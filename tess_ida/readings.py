
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
import logging

# ----------------
# Other librarires
# ----------------

from dateutil.relativedelta import relativedelta

#--------------
# local imports
# -------------

from . import MONTH_FORMAT, TSTAMP_FORMAT, CURRENT, EXPIRED

# ----------------
# Module constants
# ----------------


# -----------------------
# Module global functions
# -----------------------
    

def available(name, month, connection):
    '''Return a count of readings related to this name, 
    grouped by location'''
    row = {'name': name, 'from_date': month.strftime(TSTAMP_FORMAT)}
    cursor = connection.cursor()
    cursor.execute(
        '''
        SELECT COUNT (*), r.location_id, l.site
        FROM tess_readings_t AS r
        JOIN date_t          AS d USING (date_id)
        JOIN time_t          AS t USING (time_id)
        JOIN tess_t          AS i USING (tess_id)
        JOIN location_t      AS l USING(location_id)
        WHERE i.mac_address IN (SELECT mac_address FROM name_to_mac_t WHERE name == :name)
        AND     datetime(d.sql_date || 'T' || t.time || '.000') 
        BETWEEN datetime(:from_date) 
        AND     datetime(:from_date, '+1 month')
        GROUP BY r.location_id
        ''', row)
    logging.debug("{0}: Fetched counted readings grouped by location id".format(name))
    return cursor.fetchall()


def fetch(name, month, location_id, connection):
    '''From start of month at midday UTC'''
    row = {'name': name, 'location_id': location_id, 'from_date': month.strftime(TSTAMP_FORMAT)}
    cursor = connection.cursor()
    cursor.execute(
        '''
        SELECT (d.sql_date || 'T' || t.time || '.000') AS timestamp, r.ambient_temperature, r.sky_temperature, r.frequency, r.magnitude, i.zero_point
        FROM tess_readings_t as r
        JOIN date_t     as d USING (date_id)
        JOIN time_t     as t USING (time_id)
        JOIN tess_t     as i USING (tess_id)
        WHERE i.mac_address IN (SELECT mac_address FROM name_to_mac_t WHERE name == :name)
        AND r.location_id == :location_id
        AND datetime(timestamp) BETWEEN datetime(:from_date) 
                                AND     datetime(:from_date, '+1 month')
        ORDER BY r.date_id ASC, r.time_id ASC
        ''', row)
    return cursor