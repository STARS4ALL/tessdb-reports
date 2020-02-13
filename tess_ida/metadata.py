
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

#--------------
# other imports
# -------------

# ----------------
# Module constants
# ----------------

def instrument(connection, options):
    cursor = connection.cursor()
    row = {'name': options.name}
    cursor.execute(
            '''
            SELECT name, channel, model, firmware, mac_address,
                    zero_point, cover_offset, filter, fov, azimuth, altitude
            FROM tess_v
            WHERE valid_state == "Current"
            AND   name == :name
            ''', row)
    # Solo para instrumentos TESS monocanal
    result = cursor.fetchone()
    return {
        'name':         result[0],
        'channel':      result[1],
        'model':        result[2],
        'firmware':     result[3],
        'mac_address':  result[4],
        'zero_point':   result[5],
        'cover_offset': result[6],
        'filter':       result[7],
        'fov':          result[8],
        'azimuth':      result[9],
        'altitude':     result[10],
    }


def location(connection, options, location_id):
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
    return {
        'contact_name'   : result[0],
        'organization'   : result[1],
        'site'           : result[2],
        'longitude'      : result[3],
        'latitude'       : result[4],
        'elevation'      : result[5],
        'location'       : result[6],
        'province'       : result[7],
        'country'        : result[8],
        'timezone'       : result[9],
        
    }

def get_metadata(connection, options, location_id):
    ins = instrument(connection, options)
    loc = location(connection, options, location_id)
    obs = None
    return inst, loc, obs
