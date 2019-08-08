# tessdb-reports (overview)

Command line tool and SQL scripts to generate reports from tessdb database

tessdb is a Linux service to collect measurements pubished by TESS Sky Quality Meter via MQTT. TESS stands for [Cristobal Garcia's Telescope Encoder and Sky Sensor](http://www.observatorioremoto.com/TESS.pdf)

**tessdb** is being used as part of the [STARS4ALL Project](http://www.stars4all.eu/).

# INSTALLATION
    
## Linux installation

## Requirements

The following components are needed and should be installed first:

 * python 2.7.x (tested on Ubuntu Python 2.7.6) or python 3.6

**Note:** It is foreseen a Python 3 migration in the future, retaining Python 2.7.x compatibility.

### Installation

Installation is done from GitHub:

    git clone https://github.com/astrorafael/tessdb-reports.git
    cd tessdb-reports
    sudo python setup.py install

**Note:** Installation from PyPi is now obsolete. Do not use the package uploaded in PyPi.

* All executables are copied to `/usr/local/bin`
* The following required PIP packages will be automatically installed:
    - tabulate
    - pytz (for IDA reports generation)
    - jinja2 (for IDA reports generation)
    
