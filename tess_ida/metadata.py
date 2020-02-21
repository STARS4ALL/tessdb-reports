
# GENERATE IDA-FORMAT OBSERVATIONS FILE

# ----------------------------------------------------------------------
# Copyright (c) 2017 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import os
import os.path
import sys
import sqlite3
import datetime
import time
import logging

#--------------
# other imports
# -------------

#--------------
# local imports
# -------------

from . import __version__, MONTH_FORMAT, TSTAMP_FORMAT, UNKNOWN, EXPIRED, CURRENT

# ----------------
# Module constants
# ----------------


# Hack while there is no observer SQL table
observer_data = {}

# ------------------
# AUXILIAR FUNCTIONS
# ------------------

def get_mac_valid_period(connection, name, mac):
    logging.debug("getting valid period for ({0},{1}) association".format(name,mac))
    cursor = connection.cursor()
    row = {'name': name, 'mac': mac}
    cursor.execute(
        '''
        SELECT valid_since,valid_until,valid_state
        FROM name_to_mac_t
        WHERE mac_address == :mac
        AND name  == :name
        ''', row)
    result =  cursor.fetchone()
    return {
        'value': mac, 
        'valid_since': result[0],
        'valid_until': result[1],
        'valid_state': result[2]
    }


def single_instrument(name, tess):
    mac_address = {'changed': False, 'current': {'value': tess[1]}}
    zero_point  = {'changed': False, 'current': {'value': tess[2], 'valid_since': tess[11], 'valid_until':tess[12], 'valid_state': tess[13] }}
    filters     = {'changed': False, 'current': {'value': tess[3], 'valid_since': tess[11], 'valid_until':tess[12], 'valid_state': tess[13] }}
    azimuth     = {'changed': False, 'current': {'value': tess[4], 'valid_since': tess[11], 'valid_until':tess[12], 'valid_state': tess[13] }}
    altitude    = {'changed': False, 'current': {'value': tess[5], 'valid_since': tess[11], 'valid_until':tess[12], 'valid_state': tess[13] }}
    return {
        'name':         name,
        'mac_address':  mac_address,
        'zero_point':   zero_point,
        'filter':       filters,
        'azimuth':      azimuth,
        'altitude':     altitude,
        'model':        tess[6],
        'firmware':     tess[7],
        'fov':          tess[8],
        'cover_offset': tess[9],
        'channel':      tess[10],
    }

def if_changed(tess_list, index):
    var1 = {
        'value':        tess_list[0][index], 
        'valid_since':  tess_list[0][11], 
        'valid_until':  tess_list[0][12], 
        'valid_state':  tess_list[0][13] 
    }
    var2 = {
        'value':        tess_list[1][index], 
        'valid_since':  tess_list[1][11], 
        'valid_until':  tess_list[1][12], 
        'valid_state':  tess_list[1][13] 
    }
    changed = (tess_list[0][index] != tess_list[1][index])
    return var1, var2, changed

def maybe_swap(var1, var2):
    if var2['valid_state'] == EXPIRED:
        return var1, var2
    else:
        return var2, var1

def multiple_instruments(name, tess_list, connection):
    
    mac_address = {'changed': False}
    zero_point  = {}
    filters     = {}
    azimuth     = {}
    altitude    = {}
    mac1 = tess_list[0][1]
    mac2 = tess_list[1][1]

    # Even in the case of the change of MAC, there is almost 100% that the
    # zero point will change
    zp1, zp2, zero_point['changed']      = if_changed(tess_list, 2)
    filter1, filter2, filters['changed'] = if_changed(tess_list, 3)
    az1, az2, azimuth['changed']         = if_changed(tess_list, 4)
    alt1, alt2, altitude['changed']      = if_changed(tess_list, 5)

    mac_record1 = get_mac_valid_period(connection, name, mac1)
    if mac1 != mac2 :
        # Change of MAC means also change of ZP with almost 100% probab.
        mac_address['changed']  = True
        mac_record2 = get_mac_valid_period(connection, name, mac2)
        if mac_record2['valid_state'] == EXPIRED:
            mac_address['current']  = mac_record1
            mac_address['previous'] = mac_record2
            zero_point['current']  = zp1
            zero_point['previous'] = zp2
            filters['current']  = filter1
            filters['previous'] = filter2
            azimuth['current']  = az1
            azimuth['previous'] = az2
            altitude['current']  = alt1
            altitude['previous'] = alt2
        else:
            mac_address['current']  = mac_record2
            mac_address['previous'] = mac_record1
            zero_point['current']  = zp2
            zero_point['previous'] = zp1
            filters['current']  = filter2
            filters['previous'] = filter1
            azimuth['current']  = az2
            azimuth['previous'] = az1
            altitude['current']  = alt2
            altitude['previous'] = alt1
    else:
        # No change of MAC means change of ZP, filter, azimuth or altitude.
        mac_address['current'] = mac_record1
        zero_point['current'], zero_point['previous'] = maybe_swap(zp1, zp2)
        filters['current'],    filters['previous']    = maybe_swap(filter1, filter2)
        azimuth['current'],    azimuth['previous']    = maybe_swap(az1, az2)
        altitude['current'],   altitude['previous']   = maybe_swap(alt1, alt2)

    return {
        'name':         name,
        'mac_address':  mac_address,
        'zero_point':   zero_point,
        'filter':       filters,
        'azimuth':      azimuth,
        'altitude':     altitude,
        'model':        tess_list[0][6],
        'firmware':     tess_list[0][7],
        'fov':          tess_list[0][8],
        'cover_offset': tess_list[0][9],
        'channel':      tess_list[0][10],
    }


def available(name, month, location_id, connection):
    '''Return a a list of TESS for the given month and a given location_id'''
    row = {'name': name, 'location_id': location_id, 'from_date': month.strftime(TSTAMP_FORMAT)}
    cursor = connection.cursor()
    cursor.execute(
        '''
        SELECT DISTINCT i.tess_id, i.mac_address, i.zero_point, i.filter, i.azimuth, i.altitude, 
                        i.model, i.firmware, i.fov, i.cover_offset, i.channel, 
                        i.valid_since, i.valid_until, i.valid_state
        FROM tess_readings_t AS r
        JOIN date_t          AS d USING (date_id)
        JOIN time_t          AS t USING (time_id)
        JOIN tess_t          AS i USING (tess_id)
        WHERE i.mac_address IN (SELECT mac_address FROM name_to_mac_t WHERE name == :name)
        AND   r.location_id == :location_id
        AND     datetime(d.sql_date || 'T' || t.time || '.000') 
        BETWEEN datetime(:from_date) 
        AND     datetime(:from_date, '+1 month')
        ORDER BY i.valid_state ASC -- 'Current' before 'Expired'
        ''', row)
    tess_list = cursor.fetchall()
    logging.debug("{0}: tess_list = {1}".format(name, tess_list)) 
    l = len(tess_list)
    if l == 1:
        logging.debug("{0}: Only 1 tess_id for this location id {1} and month {2}".format(name,location_id, month.strftime(MONTH_FORMAT)))
    elif l == 2:
        logging.info("{0}: 2 tess_id ({3},{4}) for this location id {1} and month {2}".format(name, location_id, month.strftime(MONTH_FORMAT),tess_list[0][0], tess_list[1][0] ))
    elif l > 2:
        logging.warning("{0}: Oh no! {3} tess_id for this location id {1} and month {2}".format(name, location_id, month.strftime(MONTH_FORMAT)), l)
    else:
        logging.error("{0}: THIS SHOULD NOT HAPPEN No data for location id {1} in month {2}".format(name, location_id, month.strftime(MONTH_FORMAT)))
    return tess_list, (l == 1)




# --------------
# MAIN FUNCTIONS
# --------------

def instrument(name, month, location_id, connection):
    context = {}
    tess_list, single = available(name, month, location_id, connection)
    if single:
        return single_instrument(name, tess_list[0])
    else:
        return multiple_instruments(name, tess_list, connection)


def location(location_id, connection):
    global observer_data
    cursor = connection.cursor()
    row = {'location_id': location_id}
    cursor.execute(
            '''
            SELECT contact_name, organization,
                   site, longitude, latitude, elevation, location, province, country, timezone
            FROM location_t
            WHERE location_id == :location_id
            ''', row)
    result = cursor.fetchone()

    # Hack while there is no observer SQL table
    observer_data['name']         = result[0]
    observer_data['organization'] = result[1]

    return {
        'site'           : result[2],
        'longitude'      : result[3],
        'latitude'       : result[4],
        'elevation'      : result[5],
        'location'       : result[6],
        'province'       : result[7],
        'country'        : result[8],
        'timezone'       : result[9],
    }

def observer(month, connection):
    global observer_data     # Hack while there is no observer SQL table
    return observer_data

