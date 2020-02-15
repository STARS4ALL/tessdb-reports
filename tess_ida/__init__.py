# ----------------------------------------------------------------------
# Copyright (c) 2014 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

# ---------------
# Twisted imports
# ---------------

#--------------
# local imports
# -------------

from ._version import get_versions

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

__version__ = get_versions()['version']


TSTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.000"
MONTH_FORMAT  =  "%Y-%m"
CURRENT       = "Current"
EXPIRED       = "Expired"
UNKNOWN       = "Unknown"


del get_versions
