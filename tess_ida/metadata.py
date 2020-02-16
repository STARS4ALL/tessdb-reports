
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

def single_instrument(name, tess):
    return {
        'name':         name,
        'mac_address':  tess[0],
        'zero_point':   tess[1],
        'filter':       tess[2],
        'azimuth':      tess[3],
        'altitude':     tess[4],
        'model':        tess[5],
        'firmware':     tess[6],
        'fov':          tess[7],
        'cover_offset': tess[8],
        'channel':      tess[9],
    }

def multiple_instruments(name, tess_list):
    
    # Convert to unque set values
    mac_set    = {item[0] for item in tess_list}
    zp_set     = {item[1] for item in tess_list}
    filter_set = {item[2] for item in tess_list}
    az_set     = {item[3] for item in tess_list}
    alt_set    = {item[4] for item in tess_list}
    model_set  = {item[5] for item in tess_list}
    firm_set   = {item[6] for item in tess_list}
    fov_set    = {item[7] for item in tess_list}
    cov_set    = {item[8] for item in tess_list}
    chan_set   = {item[9] for item in tess_list}

    return {
        'name':         name,
        'mac_address':  list(mac_set),
        'zero_point':   list(zp_set),
        'filter':       list(filter_set),
        'azimuth':      list(az_set),
        'altitude':     list(alt_set),
        'model':        model_set.pop(),
        'firmware':     firm_set.pop(),
        'fov':          fov_set.pop(),
        'cover_offset': cov_set.pop(),
        'channel':      chan_set.pop(),
    }


def available(name, month, location_id, connection):
    '''Return a list of tess_id for the given month and a given location_id'''
    row = {'name': name, 'location_id': location_id, 'from_date': month.strftime(TSTAMP_FORMAT)}
    cursor = connection.cursor()
    cursor.execute(
        '''
        SELECT DISTINCT i.mac_address, i.zero_point, i.filter, i.azimuth, i.altitude, 
                        i.model, i.firmware, i.fov, i.cover_offset, i.channel, i.tess_id
        FROM tess_readings_t AS r
        JOIN date_t          AS d USING (date_id)
        JOIN time_t          AS t USING (time_id)
        JOIN tess_t          AS i USING (tess_id)
        WHERE i.mac_address IN (SELECT mac_address FROM name_to_mac_t WHERE name == :name)
        AND   r.location_id == :location_id
        AND     datetime(d.sql_date || 'T' || t.time || '.000') 
        BETWEEN datetime(:from_date) 
        AND     datetime(:from_date, '+1 month')
        ORDER BY i.tess_id ASC
        ''', row)
    return cursor.fetchall()

# --------------
# MAIN FUNCTIONS
# --------------

def instrument(name, month, location_id, connection):
    context = {}
    tess_list = available(name, month, location_id, connection)
    l = len(tess_list)
    if l == 0:
        logging.error("{0}: THIS SHOULD NOT HAPPEN No data for location id {1} in month {2}".format(name, location_id, month.strftime(MONTH_FORMAT)))
    elif l == 1:
        logging.info("{0}: Only 1 tess_id for this location id {1} and month {2}".format(name,location_id, month.strftime(MONTH_FORMAT)))
        return single_instrument(name, tess_list[0])
    else:
        logging.info("{0}: Several tess_id for this location id {1} and month {2}".format(name, location_id, month.strftime(MONTH_FORMAT)))
        return multiple_instruments(name, tess_list)

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

