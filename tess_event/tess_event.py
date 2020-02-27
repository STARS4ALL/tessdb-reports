
# GENERATE IDA-FORMAT OBSERVATIONS FILE

# ----------------------------------------------------------------------
# Copyright (c) 2017 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import glob
import re
import logging
import sys
import argparse
import sqlite3
import os
import os.path

import datetime



#--------------
# other imports
# -------------


#--------------
# local imports
# -------------

from . import __version__, TSTAMP_FORMAT


# ----------------
# Module constants
# ----------------

DEFAULT_DBASE  = "/var/dbase/tess.db"
DEFAULT_LOGDIR = "/var/log"

# ---------------------
# Module global classes
# ---------------------


# -----------------------
# Module global functions
# -----------------------

def createParser():
    # create the top-level parser
    name = os.path.split(os.path.dirname(sys.argv[0]))[-1]
    parser = argparse.ArgumentParser(prog=name, description="TESS Event log file parser " + __version__)
    parser.add_argument('-d', '--dbase',   default=DEFAULT_DBASE, help='SQLite database full file path')
    parser.add_argument('-t', '--testing', action='store_true', help='Testing environment.')
    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('-v', '--verbose', action='store_true', help='Verbose output.')
    group2.add_argument('-q', '--quiet',   action='store_true', help='Quiet output.')
    return parser

# -------------------
# AUXILIARY FUNCTIONS
# -------------------


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

def create_table(connection):
    logging.debug("creating event_log_t table")
    cursor = connection.cursor()
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS event_log_t
        (
            tstamp        TEXT NOT NULL,    -- ISO timestamp
            event         TEXT NOT NULL,    -- Event key ('started,'stopped', etc)
            environment   TEXT NOT NULL,    -- Database where it takes place: 'production', 'testing'
            source        TEXT NOT NULL,    -- Who produces the event, 'script', 'tessdb'
            scope         TEXT NOT NULL,    -- Which scope: 'global', 'stars1', etc.
            method        TEXT NOT NULL,    -- How it was produced: 'cron job', 'manual'
            comment TEXT,              -- i.e. "tessdb 2.5.3, Twisted 10.10.0"
            PRIMARY KEY(tstamp, event, environment)
        );
        ''')
    connection.commit()

def process_line(line, connection):
    pass
    
# -------------
# MAIN FUNCTION
# -------------

'''
2020-02-04T12:21:47+0000 [tessdb#info] starting tessdb 2.5.3 on Python 3.6 using Twisted 19.10.0
'''
# Unsolicited Responses Patterns
EVENTS_ = (
    {
        'name'    : 'startes',
        'pattern' : r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})[+-]\d{4} \[.+\] starting tessdb ',       
    },
    {
        'name'    : 'stopped',
        'pattern' : '^<fm (\d{5})><tA ([+-]\d{4})><tO ([+-]\d{4})><mZ ([+-]\d{4})>',       
    },
    
)


UNSOLICITED_PATTERNS = [ re.compile(ur['pattern']) for ur in UNSOLICITED_RESPONSES ]



def main():
    '''
    Main entry point
    '''
    try:
        options = createParser().parse_args(sys.argv[1:])
        configureLogging(options)
        connection = open_database(options.dbase)
        create_table(connection)
        for logfile_path in sorted(glob.glob("/var/log/tessdb*")):
            with open(logfile_path,'r') as fd:
                logging.debug("processing file {0}".format(logfile_path))
                for line in fd:
                    process_line(line, connection)

    except KeyboardInterrupt:
        logging.exception('{0}: Interrupted by user ^C'.format(name))
    except Exception as e:
        logging.exception("Error => {0}".format(e))