
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

# ----------------
# Other librarires
# ----------------

from dateutil.relativedelta import relativedelta

#--------------
# local imports
# -------------


# ----------------
# Module constants
# ----------------

TSTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.000"
CURRENT = "Current"
EXPIRED = "Expired"


def get_mac_intervals(connection, options):
    cursor = connection.cursor()
    row = {'name': options.name}
    cursor.execute(
        '''
        SELECT mac_address,valid_since,valid_until,valid_state
        FROM name_to_mac_t
        WHERE name == :name
        ORDER BY valid_state DESC;
        ''', row)
    return [ {'start':datetime.datetime.strptime(item[1], "%Y-%m-%dT%H:%M:%S"), 
               'end' :datetime.datetime.strptime(item[2], "%Y-%m-%dT%H:%M:%S"), 
               'mac': item[0] } for item in cursor.fetchall()]

def mac_for(interval_list, month):
    for interval in interval_list:
        if interval['start'] <= month <= interval['end']:
            return interval['mac']
     return None

def change_of_mac(interval_list, month):
    for interval in interval_list:
        if month <= interval['end'] <= month + relativedelta(months = +1):
            return list.index(interval)
     return None

def do_it_all(connection, options, month):
    result = []
    interval_list = get_mac_intervals(connection, options)
    i = change_of_mac(interval_list, month)
    if i is None:
        result.append(mac_for(interval_list, month))
    else:
        result.append(interval_list[i]['mac'])
        result.append(interval_list[i+1]['mac'])
    return result


# -----------------------
# Module global functions
# -----------------------


def analyze_latest(connection, options, mac):
    '''From start of month at midnight UTC
    Return a list of tuples (count, location_id, date_id)'''
    row = {'name': options.name, 'mac': mac}
    cursor = connection.cursor()
    cursor.execute(
        '''
        SELECT COUNT (*), r.location_id, MIN(r.date_id)
        FROM tess_readings_t as r
        JOIN date_t     as d USING (date_id)
        JOIN time_t     as t USING (time_id)
        JOIN tess_t     as i USING (tess_id)
        WHERE i.mac_address == :mac
        AND datetime(d.sql_date || 'T' || t.time || '.000') 
        BETWEEN datetime('now', 'start of month' ) AND datetime('now')
        GROUP BY r.location_id
        ORDER BY MIN(r.date_id) ASC;
        ''', row)
    return cursor.fetchall()


def analyze_previous(connection, options, mac):
    '''From start of previous month at midnight UTC
    Return a list of tuples (count, location_id, date_id)
    '''
    row = {'mac': mac}
    cursor = connection.cursor()
    cursor.execute(
        '''
        SELECT COUNT (*), r.location_id, MIN(r.date_id)
        FROM tess_readings_t as r
        JOIN date_t     as d USING (date_id)
        JOIN time_t     as t USING (time_id)
        JOIN tess_t     as i USING (tess_id)
        WHERE i.mac_address == :mac
        AND datetime(d.sql_date || 'T' || t.time || '.000') 
        BETWEEN datetime('now', 'start of month', '-1 month' ) 
        AND     datetime('now', 'start of month')
        GROUP BY r.location_id
        ORDER BY MIN(r.date_id) ASC;
        ''', row)
    return cursor.fetchall()


def analyze_for_month(connection, options, mac):
    '''From start of month at midday UTC
        Return a list of tuples (count, location_id, date_id)'''
    row = {'mac': mac, 'from_date': options.for_month.strftime(TSTAMP_FORMAT)}
    cursor = connection.cursor()
    cursor.execute(
        '''
        SELECT COUNT (*), r.location_id, MIN(r.date_id)
        FROM tess_readings_t as r
        JOIN date_t     as d USING (date_id)
        JOIN time_t     as t USING (time_id)
        JOIN tess_t     as i USING (tess_id)
        WHERE i.mac_address == :mac
        AND datetime(d.sql_date || 'T' || t.time || '.000') 
        BETWEEN datetime(:from_date) 
        AND     datetime(:from_date, '+1 month')
        GROUP BY r.location_id
        ORDER BY MIN(r.date_id) ASC;
        ''', row)
    return cursor.fetchall()



def fetch_latest(connection, options, location_id):
    '''From start of month at midnight UTC'''
    row = {'name': options.name, 'location_id': location_id}
    cursor = connection.cursor()
    cursor.execute(
        '''
        SELECT (d.sql_date || 'T' || t.time || '.000') AS timestamp, r.ambient_temperature, r.sky_temperature, r.frequency, r.magnitude, i.zero_point
        FROM tess_readings_t as r
        JOIN date_t     as d USING (date_id)
        JOIN time_t     as t USING (time_id)
        JOIN tess_t     as i USING (tess_id)
        WHERE i.name == :name
        AND r.location_id == :location_id
        AND datetime(timestamp) BETWEEN datetime('now', 'start of month') 
                                AND     datetime('now')
        ORDER BY r.date_id ASC, r.time_id ASC
        ''', row)
    return cursor


def fetch_previous(connection, options, location_id):
    '''From start of previous month at midnight UTC'''
    row = {'name': options.name, 'location_id': location_id}
    cursor = connection.cursor()
    cursor.execute(
        '''
        SELECT (d.sql_date || 'T' || t.time || '.000') AS timestamp, r.ambient_temperature, r.sky_temperature, r.frequency, r.magnitude, i.zero_point
        FROM tess_readings_t as r
        JOIN date_t     as d USING (date_id)
        JOIN time_t     as t USING (time_id)
        JOIN tess_t     as i USING (tess_id)
        WHERE i.name == :name
        AND r.location_id == :location_id
        AND datetime(timestamp) BETWEEN datetime('now', 'start of month', '-1 month') 
                                AND     datetime('now', 'start of month')
        ORDER BY r.date_id ASC, r.time_id ASC
        ''', row)
    return cursor


def fetch_for_month(connection, options, location_id):
    '''From start of month at midday UTC'''
    row = {'name': options.name, 'location_id': location_id, 'from_date': options.for_month.strftime(TSTAMP_FORMAT)}
    cursor = connection.cursor()
    cursor.execute(
        '''
        SELECT (d.sql_date || 'T' || t.time || '.000') AS timestamp, r.ambient_temperature, r.sky_temperature, r.frequency, r.magnitude, i.zero_point
        FROM tess_readings_t as r
        JOIN date_t     as d USING (date_id)
        JOIN time_t     as t USING (time_id)
        JOIN tess_t     as i USING (tess_id)
        WHERE i.name == :name
        AND r.location_id == :location_id
        AND datetime(timestamp) BETWEEN datetime(:from_date) 
                                AND     datetime(:from_date, '+1 month')
        ORDER BY r.date_id ASC, r.time_id ASC
        ''', row)
    return cursor
    