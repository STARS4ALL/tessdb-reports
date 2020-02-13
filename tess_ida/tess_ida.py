
# GENERATE IDA-FORMAT OBSERVATIONS FILE

# ----------------------------------------------------------------------
# Copyright (c) 2017 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------
from __future__ import generators    # needs to be at the top of your module

import os
import os.path
import sys
import argparse
import sqlite3
import datetime
import time

#--------------
# other imports
# -------------

from . import __version__

import jinja2
import pytz

# ----------------
# Module constants
# ----------------

UNKNOWN = "Unknown"

DEFAULT_DBASE = "/var/dbase/tess.db"
DEFAULT_TMPLT = "/etc/tessdb/IDA-template.j2"
DEFAULT_DIR   = "/var/dbase/reports/IDA"
DEFAULT_MONTH = datetime.datetime.utcnow().strftime("%Y-%m")

TSTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.000"

# -----------------------
# Module global functions
# -----------------------

def createParser():
    # create the top-level parser
    parser = argparse.ArgumentParser(prog=sys.argv[0], description="TESS IDA file generator " + __version__)
    parser.add_argument('name', metavar='<name>', help='TESS instrument name')
    parser.add_argument('-d', '--dbase', default=DEFAULT_DBASE, help='SQLite database full file path')
    parser.add_argument('-t', '--template', default=DEFAULT_TMPLT, help='Jinja2 template file path')
    parser.add_argument('-o', '--out_dir', default=DEFAULT_DIR, help='Output directory to dump record')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-m', '--for-month', type=mkmonth, metavar='<YYYY-MM>', help='Given year & month. Defaults to current.')
    group.add_argument('-f', '--from-month', type=mkmonth, metavar='<YYYY-MM>', help='Starting year & month')
    group.add_argument('-l', '--latest-month', action='store_true', help='Latest month only.')
    group.add_argument('-p', '--previous-month', action='store_true', help='previous month only.')
    return parser

# -------------------
# AUXILIARY FUNCTIONS
# -------------------


def mkmonth(datestr):
    return datetime.datetime.strptime(datestr, '%Y-%m')


def month_generator(start_month):
    '''start_month is a datetime object represeting the start of month'''
    end_month = datetime.datetime.utcnow().replace(day=1, hour=0, minute=0, second=0,microsecond=0)
    one_month = datetime.timedelta(days=28)
    one_day   = datetime.timedelta(days=1)
    month     = start_month
    if start_month <= end_month:
        while month <= end_month:
            yield month
            next_month = month + one_month
            while next_month.month == month.month:
                next_month += one_day
            month = next_month


def result_generator(cursor, arraysize=500):
    'An iterator that uses fetchmany to keep memory usage down'
    while True:
        results = cursor.fetchmany(arraysize)
        if not results:
            break
        for result in results:
            yield result


def open_database(dbase_path):
    if not os.path.exists(dbase_path):
       raise IOError("No SQLite3 Database file found at {0}. Exiting ...".format(dbase_path))
    print("Opening database {0}".format(dbase_path))
    return sqlite3.connect(dbase_path)


def render_readings_line(dbreading, timezone):
    tzobj = pytz.timezone(timezone)
    dt = datetime.datetime.strptime(dbreading[0], TSTAMP_FORMAT).replace(tzinfo=pytz.utc)
    record = {
            'utc':  dbreading[0], 
            'local': dt.astimezone(tzobj).strftime(TSTAMP_FORMAT),
            'tamb': dbreading[1], 
            'tsky': dbreading[2], 
            'freq': dbreading[3], 
            'mag':  dbreading[4],
            'zp':   dbreading[5],
        }
    return "%(utc)s;%(local)s;%(tamb)s;%(tsky)s;%(freq)s;%(mag)s;%(zp)s" % record



def render(template_path, context):
    if not os.path.exists(template_path):
        raise IOError("No Jinja2 template file found at {0}. Exiting ...".format(template_path))
    path, filename = os.path.split(template_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)


def create_directories(instrument_name, out_dir, year=None):
    sub_dir = os.path.join(out_dir, instrument_name)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    if not os.path.exists(sub_dir):
        os.makedirs(sub_dir)
   
# -------------------
# IDA FILE Generation
# -------------------

def write_IDA_header_file(header, instrument_name, out_dir, timestamp, suffix):
    '''Writes the IDA header file after contained in result'''
    file_name = instrument_name + timestamp.strftime("_%Y-%m") + suffix + ".dat"
    full_name = os.path.join(out_dir, instrument_name, file_name)
    if sys.version_info[0] > 2:
        result = result.decode('utf-8')
    with open(full_name, 'w') as outfile:
        outfile.write(header)


def write_IDA_body_file(cursor, timezone, instrument_name, out_dir, timestamp, suffix):
    file_name = instrument_name + timestamp.strftime("_%Y-%m") + suffix + ".dat"
    full_name = os.path.join(out_dir, instrument_name, file_name)
    with open(full_name, 'a') as outfile:
        for reading in result_generator(cursor):
            body_line = render_readings_line(reading, timezone)
            outfile.write(body_line)
            outfile.write('\n')

# -------------
# MAIN FUNCTION
# -------------

def do_one_pass(connection, resultset, options):
    empty = len(resultset) == 0
    if not empty:
            # Render one IDA file per diferent location in case the TESS nstrument
            # has changed location during the given month
        for idx, result in enumerate(resultset):
            count = result[0]
            location_id = result[1]
            start_date_id = result[2]
            print("Generating monthly IDA file for {0} with {1} samples starting from {2} for location id {3}".format(options.name, count, start_date_id, location_id))
            create_directories(options.name, options.out_dir)
            if options.latest_month:
                timestamp  = datetime.datetime.utcnow()
                cursor = readings.fetch_latest(connection, options, location_id)
            elif options.previous_month:
                # back to last day of previous month
                timestamp = datetime.datetime.utcnow().replace(day=1,hour=0,minute=0,second=0,microsecond=0)
                timestamp -= datetime.timedelta(days=1)
                cursor = readings.fetch_previous(connection, options, location_id)
            else:
                timestamp  = options.for_month
                cursor = readings.fetch_for_month(connection, options, location_id)
            # render IDA header file from Jinja2 template
            context = {}
            context['instrument'], context['location'], context['observer'] = metadata.get_metadata(connection, options, location_id)
            timezone = context['location']['timezone']
            header = render(options.template, context).encode('utf-8')
            suffix = '' if idx == 0 else '_x' + str(idx)
            write_IDA_header_file(header, options.name, options.out_dir, timestamp, suffix)
            write_IDA_body_file(cursor, timezone, options.name, options.out_dir, timestamp, suffix)
    else:
        print("No data: skipping subdirs creation and IDA file generation")
  

def main():
    '''
    Utility entry point
    '''
    try:
        options = createParser().parse_args(sys.argv[1:])
        connection = open_database(options.dbase)
        if options.latest_month:
            resultset = readings.analyze_latest(connection, options)
            do_one_pass(connection, resultset, options)
        if options.previous_month:
            resultset = readings.analyze_previous(connection, options)
            do_one_pass(connection, resultset, options)
        elif options.for_month:
            resultset = readings.analyze_for_month(connection, options)
            do_one_pass(connection, resultset, options)
        else:
            for month in month_generator(options.from_month):
                options.for_month = month   # This is a hack
                resultset = readings.analyze_for_month(connection, options)
                do_one_pass(connection, resultset, options)
    except KeyboardInterrupt:
        print('Interrupted by user ^C')
    #except Exception as e:
        print("Error => {0}".format(e))

