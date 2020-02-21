import os
import os.path

from setuptools import setup, Extension
import versioneer

# Default description in markdown
long_description = open('README.md').read()
 

PKG_NAME     = 'tessdb-reports'
AUTHOR       = 'Rafael Gonzalez'
AUTHOR_EMAIL = 'astrorafael@yahoo.es'
DESCRIPTION  = 'Command line tool and SQL scripts to generate reports from tessdb database',
LICENSE      = 'MIT'
KEYWORDS     = 'Astronomy Python RaspberryPi'
URL          = 'http://github.com/stars4all/tessdb-reports/'
PACKAGES     = ["tess_ida"]
DEPENDENCIES = [
                  'python-dateutil',
                  'tabulate', 
                  'pytz',
                  'jinja2'
]

CLASSIFIERS  = [
    'Environment :: No Input/Output (Daemon)',
    'Intended Audience :: Science/Research',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: POSIX :: Linux',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: SQL',
    'Topic :: Scientific/Engineering :: Astronomy',
    'Topic :: Scientific/Engineering :: Atmospheric Science',
    'Development Status :: 4 - Beta',
]

# Additional data inside the package
PACKAGE_DATA = {
    'tess_ida': ['templates/IDA-template.j2'],
}
                                
DATA_FILES  = [ 
  ('/usr/local/bin',         [
                              'files/usr/local/bin/tessdb_index.sh',
                              'files/usr/local/bin/tess_ida',
                              'files/usr/local/bin/tess_bulk_dump.sh', 
                              'files/usr/local/bin/tess_daily_summary.sh', 
                              'files/usr/local/bin/tess_life_span.sh', 
                              'files/usr/local/bin/tess_readings_unassigned.sh', 
                              'files/usr/local/bin/tess_ida_bulk_dump.sh',
                              'files/usr/local/bin/tess_ida_bulk_dump_all.sh',
                              ]),
]

if os.name == "posix":
  

  setup(name             = PKG_NAME,
        version          = versioneer.get_version(),
        cmdclass         = versioneer.get_cmdclass(),
        author           = AUTHOR,
        author_email     = AUTHOR_EMAIL,
        description      = DESCRIPTION,
        long_description_content_type = "text/markdown",
        long_description = long_description,
        license          = LICENSE,
        keywords         = KEYWORDS,
        url              = URL,
        classifiers      = CLASSIFIERS,
        packages         = PACKAGES,
        install_requires = DEPENDENCIES,
        data_files       = DATA_FILES,
        package_data     = PACKAGE_DATA
        )
 
else:

   print("Not supported OS")
