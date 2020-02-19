
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
import logging
# Access IDA template withing the package
from pkg_resources import resource_filename

from dateutil.relativedelta import relativedelta

#--------------
# other imports
# -------------

import jinja2
import pytz

#--------------
# local imports
# -------------

from . import __version__, MONTH_FORMAT, TSTAMP_FORMAT, UNKNOWN

from . import readings, metadata

# ----------------
# Module constants
# ----------------

DEFAULT_DBASE = "/var/dbase/tess.db"
DEFAULT_DIR   = "/var/dbase/reports/IDA"

# ---------------------
# Module global classes
# ---------------------

class MonthIterator(object):

    def __init__(self, start_month, end_month):
        self.__month = start_month
        self.__end = end_month + relativedelta(months = +1)

    def __iter__(self):
        '''Make this this class an iterable'''
        return self

    def __next__(self):
        '''Make this this class an iterator'''
        m = self.__month
        if self.__month == self.__end:
            raise StopIteration  
        self.__month += relativedelta(months = +1)
        return m

    def next(self):
        '''Puython 2.7 compatibility'''
        return self.__next__()


# -----------------------
# Module global functions
# -----------------------

def createParser():
    # create the top-level parser
    name = os.path.split(os.path.dirname(sys.argv[0]))[-1]
    parser = argparse.ArgumentParser(prog=name, description="TESS IDA file generator " + __version__)
    parser.add_argument('name', metavar='<name>', help='TESS instrument name')
    parser.add_argument('-d', '--dbase',   default=DEFAULT_DBASE, help='SQLite database full file path')
    parser.add_argument('-o', '--out_dir', default=DEFAULT_DIR, help='Output directory to dump record')
    group1 = parser.add_mutually_exclusive_group(required=True)
    group1.add_argument('-m', '--for-month',  type=mkmonth, metavar='<YYYY-MM>', help='Given year & month. Defaults to current.')
    group1.add_argument('-f', '--from-month', type=mkmonth, metavar='<YYYY-MM>', help='Starting year & month')
    group1.add_argument('-l', '--latest-month', action='store_true', help='Latest month only.')
    group1.add_argument('-p', '--previous-month', action='store_true', help='previous month only.')
    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('-v', '--verbose', action='store_true', help='Verbose output.')
    group2.add_argument('-q', '--quiet',   action='store_true', help='Quiet output.')
    return parser

# -------------------
# AUXILIARY FUNCTIONS
# -------------------


def now_month():
    return datetime.datetime.utcnow().replace(day=1,hour=0,minute=0,second=0,microsecond=0)

def mkmonth(datestr):
    return datetime.datetime.strptime(datestr, MONTH_FORMAT)

def result_generator(cursor, arraysize=500):
    'An iterator that uses fetchmany to keep memory usage down'
    while True:
        results = cursor.fetchmany(arraysize)
        if not results:
            break
        for result in results:
            yield result

def createMonthList(options):
    if options.latest_month:
        start_month  = now_month()
        end_month   = start_month
    elif options.previous_month:
        start_month  = now_month() + relativedelta(months = -1)
        end_month    = start_month
    elif options.for_month:
        start_month = options.for_month
        end_month   = start_month
    else:
        start_month  = options.from_month
        end_month    = now_month()
    return MonthIterator(start_month, end_month)

def configureLogging(options):
    if options.verbose:
        level = logging.DEBUG
    elif options.quiet:
        level = logging.WARN
    else:
        level = logging.INFO
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=level)

def open_database(dbase_path):
    if not os.path.exists(dbase_path):
       raise IOError("No SQLite3 Database file found at {0}. Exiting ...".format(dbase_path))
    logging.info("Opening database {0}".format(dbase_path))
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
    return "%(utc)s;%(local)s;%(tamb).1f;%(tsky).1f;%(freq).3f;%(mag).2f;%(zp).2f" % record

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

def write_IDA_header_file(header, file_path):
    '''Writes the IDA header file after contained in result'''
    if sys.version_info[0] > 2:
        header = header.decode('utf-8')
    with open(file_path, 'w') as outfile:
        outfile.write(header)

def write_IDA_body_file(name, month, cursor, timezone, file_path):
    with open(file_path, 'a') as outfile:
        for reading in result_generator(cursor):
            body_line = render_readings_line(reading, timezone)
            outfile.write(body_line)
            outfile.write('\n')

# -------------
# MAIN FUNCTION
# -------------

def write_IDA_file(name, month, location_id, connection, options, single):
    
    # Render one IDA file per location 
    # in case the TESS nstrument has changed location during the given month
    context = {}
    template_path = resource_filename(__name__, 'templates/IDA-template.j2')
    create_directories(name, options.out_dir)
    logging.debug("{0}: Fetching location metadata from the database".format(name))
    context['location']   = metadata.location(location_id, connection)
    logging.debug("{0}: Fetching instrument metadata from the database".format(name))
    context['instrument'] = metadata.instrument(name, month, location_id, connection)
    logging.debug("{0}: Fetching observer metadata from the database".format(name))
    context['observer']   = metadata.observer(month, connection)
    timezone = context['location']['timezone']
    header = render(template_path, context).encode('utf-8')
    suffix = '_' + str(location_id) if not single else ''
    file_name = name + "_" + month.strftime(MONTH_FORMAT) + suffix + ".dat"
    file_path = os.path.join(options.out_dir, name, file_name)
    logging.debug("{0}: Fetching readings from the database".format(name))
    cursor = readings.fetch(name, month, location_id, connection)
    logging.info("{0}: saving on to file {1}".format(name, file_name))
    write_IDA_header_file(header, file_path)
    write_IDA_body_file(name, month, cursor, timezone, file_path)


def main():
    '''
    Main entry point
    '''
    try:
        options = createParser().parse_args(sys.argv[1:])
        configureLogging(options)
        connection = open_database(options.dbase)
        name = options.name        
        month_list = createMonthList(options)
        for month in month_list:
            date = month.strftime(MONTH_FORMAT) # For printing purposes
            logging.debug("{0}: Counting available data on {1}".format(name, date))
            per_location_list = readings.available(name, month, connection)
            nlocations = len(per_location_list)
            if nlocations > 0:
                single = nlocations == 1
                for location in per_location_list:
                    count       = location[0]
                    location_id = location[1]
                    site        = location[2]
                    logging.info("{0}: Generating {2} monthly IDA file with {1} samples for location '{3}'".format(name, count, date, site.encode('utf-8')))
                    write_IDA_file(name, month, location_id, connection, options, single)
            else:
                logging.info("{0}: No data for month {1}: skipping subdirs creation and IDA file generation".format(name, date))
    except KeyboardInterrupt:
        logging.exception('{0}: Interrupted by user ^C'.format(name))
    except Exception as e:
        logging.exception("Error => {0}".format(e))