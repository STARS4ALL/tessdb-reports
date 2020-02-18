
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

from . import __version__, MONTH_FORMAT, TSTAMP_FORMAT, UNKNOWN

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
    return {
        'name':         name,
        'mac_address':  mac_address,
        'zero_point':   zero_point,
        'filter':       tess[3],
        'azimuth':      tess[4],
        'altitude':     tess[5],
        'model':        tess[6],
        'firmware':     tess[7],
        'fov':          tess[8],
        'cover_offset': tess[9],
        'channel':      tess[10],
    }

def multiple_instruments(name, tess_list, connection):
    
    mac_address = {'changed': False}
    zero_point  = {'changed': True}
    mac1 = tess_list[0][1]
    mac2 = tess_list[1][1]

    # Even in the case of the change of MAC, there is almost 100% that the
    # zero point will change
    zero_point['changed'] = True
    zero_point['current'] = {
        'value':        tess_list[0][2], 
        'valid_since':  tess_list[0][11], 
        'valid_until':  tess_list[0][12], 
        'valid_state':  tess_list[0][13] 
    }
    zero_point['previous'] = {
        'value':        tess_list[1][2], 
        'valid_since':  tess_list[1][11], 
        'valid_until':  tess_list[1][12], 
        'valid_state':  tess_list[1][13] 
    }

    mac_address['current']  = get_mac_valid_period(connection, name, mac1)
    if mac1 != mac2 :
        mac_address['changed']  = True
        mac_address['previous'] = get_mac_valid_period(connection, name, mac2)

    # Convert to unque set values   
   
    filter_set = {(item[3],item[0]) for item in tess_list}
    az_set     = {(item[4],item[0]) for item in tess_list}
    alt_set    = {(item[5],item[0]) for item in tess_list}
    model_set  = {item[6] for item in tess_list}
    firm_set   = {item[7] for item in tess_list}
    fov_set    = {item[8] for item in tess_list}
    cov_set    = {item[9] for item in tess_list}
    chan_set   = {item[10] for item in tess_list}

    return {
        'name':         name,
        'mac_address':  mac_address,
        'zero_point':   zero_point,
        'filter':       filter_set.pop()[0],
        'azimuth':      az_set.pop()[0],
        'altitude':     alt_set.pop()[0],
        'model':        model_set.pop(),
        'firmware':     firm_set.pop(),
        'fov':          fov_set.pop(),
        'cover_offset': cov_set.pop(),
        'channel':      chan_set.pop(),
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
    l = len(tess_list)
    if l == 1:
        logging.debug("{0}: Only 1 tess_id for this location id {1} and month {2}".format(name,location_id, month.strftime(MONTH_FORMAT)))
    elif l == 2:
        logging.debug("{0}: 2 tess_id for this location id {1} and month {2}".format(name, location_id, month.strftime(MONTH_FORMAT)))
    elif l > 2:
        logging.debug("{0}: Oh no! {3} tess_id for this location id {1} and month {2}".format(name, location_id, month.strftime(MONTH_FORMAT)), l)
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

