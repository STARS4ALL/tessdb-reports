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
    


# OPERATION & MAINTENANCE

## The `tess` utility

`tess` is a command line utility to perform some common operations on the database without having to write SQL statements. As this utility modifies the database, it is necessary to invoke it within using `sudo`. Also, you should ensure that the database is not being written by `tessdb` to avoid *database is locked* exceptions, either by using it at daytime or by pausing the `tessdb` service.

It has several subcommands. You can find the all by typing `tess --help`
```
pi@rb-tess:~ $ tess --help
usage: /usr/local/bin/tess [-h] {instrument,location,readings} ...

positional arguments:
  {instrument,location,readings}
    instrument          instrument commands
    location            location commands
    readings            readings commands

optional arguments:
  -h, --help            show this help message and exit
```

Each subcommand has its own help that you may display by issuing `tess <subcommand> --help`

Example:
```
pi@rb-tess:~ $ tess location list --help
usage: /usr/local/bin/tess location list [-h] [-p PAGE_SIZE] [-d DBASE]

optional arguments:
  -h, --help            show this help message and exit
  -p PAGE_SIZE, --page-size PAGE_SIZE
                        list page size
  -d DBASE, --dbase DBASE
                        SQLite database full file path
```



### Listing locations
`tess location list`
```
+-----------------------------------------+-------------+------------+-------------+
| Name                                    |   Longitude |   Latitude |   Elevation |
+=========================================+=============+============+=============+
| Laboratorio de Cristobal                |    -nn.nnnn |    nn.nnnn |         nnn |
+-----------------------------------------+-------------+------------+-------------+
| Centro de Recursos Asociativos El Cerro |    -3.5515  |    40.4186 |         650 |
+-----------------------------------------+-------------+------------+-------------+
```

### Renaming locations
`tess location rename <old site name> <new site name>`

### Listing TESS instruments
`tess instrument list`

```
+---------+---------+-------------+------------+-------------+
| TESS    | Site    | Longitude   | Latitude   | Elevation   |
+=========+=========+=============+============+=============+
| pruebas | Unknown | Unknown     | Unknown    | Unknown     |
+---------+---------+-------------+------------+-------------+
| stars1  | Unknown | Unknown     | Unknown    | Unknown     |
+---------+---------+-------------+------------+-------------+
```


### Assign a location to an instrument
The most important use of the tess utility is to assign an existing location to an instrument, since brand new registered instruments are assigned to a default *Unknown* location. This must be issued with `sudo`, since it requires a DB write.

`sudo tess assign pruebas "Laboratorio de Cristobal"`

```
+---------+--------------------------+-------------+------------+-------------+
| TESS    | Site                     |   Longitude |   Latitude |   Elevation |
+=========+==========================+=============+============+=============+
| pruebas | Laboratorio de Cristobal |    -n.nnnnn |    nn.nnnn |         nnn |
+---------+--------------------------+-------------+------------+-------------+
```

`tess instrument list`

```
+---------+--------------------------+-------------+------------+-------------+
| TESS    | Site                     | Longitude   | Latitude   | Elevation   |
+=========+==========================+=============+============+=============+
| pruebas | Laboratorio de Cristobal | -nn.nnnnnnn | nn.nnnnnnn | nnn.n       |
+---------+--------------------------+-------------+------------+-------------+
| stars1  | Unknown                  | Unknown     | Unknown    | Unknown     |
+---------+--------------------------+-------------+------------+-------------+
```

### Create a brand new TESS instrument
If automatic registration fails, this command allows manual creation of a TESS instrument in the database

`tess instrument create {name} {mac} {zero point} {filter}`

### Enabling/Disabling a TESS instrument
In order for a TESS to have its readings stored in the databae, it need to be enabled (authorised). In previous releases of tessdb this happened automatically when the TESS was assigned to a known location, when the daylingth filter was active. Now this is a separate but important procedure

`tess instrument enable stars1`

```
+--------+--------------------------+--------------+
| TESS   | Site                     |   Authorised |
+========+==========================+==============+
| stars1 | Laboratorio de Cristóbal |            1 |
+--------+--------------------------+--------------+
```


If, for soem reason, we must avoid a given TESS to store its readings, we proceed and disable it.

`tess instrument disable stars1`

```
+--------+--------------------------+--------------+
| TESS   | Site                     |   Authorised |
+========+==========================+==============+
| stars1 | Laboratorio de Cristóbal |            0 |
+--------+--------------------------+--------------+
```


### Renaming a TESS instrument
If for some reason, an instrument needs to change the friendly user name, this command allows you to do so.
`tess instrument rename {old name} {new name}`

```
+---------+-------------------+---------------+----------+-------------+------------+-------------+
| TESS    | MAC Addr.         |   Zero Point | Site     |   Longitude |   Latitude |   Elevation |
+=========+===================+===============+==========+=============+============+=============+
| pruebas | 18:FE:34:9C:AD:ED |          1.61 | Pamplona |    n.nnnnn |    nn.nnnn |         nnn |
+---------+-------------------+---------------+----------+-------------+------------+-------------+
```

### Deleting a TESS instrument
**Use this option with utmost care, as it will leave orphaned readings**

This will also erase the instrument history of changes, as shown in the folowing example:

`tess instrument delete pruebas`

```
About to delete
+---------+-------------------+--------------+----------+--------------------------+-------------+------------+-------------+
| TESS    | MAC Addr.         |   Zero Point | Filter   | Site                     |   Longitude |   Latitude |   Elevation |
+=========+===================+==============+==========+==========================+=============+============+=============+
| pruebas | 18:FE:34:9C:AD:ED |         1.65 | UVIR     | Laboratorio de Cristobal |    -3.55809 |    40.4246 |         626 |
+---------+-------------------+--------------+----------+--------------------------+-------------+------------+-------------+
| pruebas | 18:FE:34:9C:AD:ED |         1.6  | UVIR     | Laboratorio de Cristobal |    -3.55809 |    40.4246 |         626 |
+---------+-------------------+--------------+----------+--------------------------+-------------+------------+-------------+
+--------+-----------------------+
| TESS   |   Acumulated Readings |
+========+=======================+
|        |                     0 |
+--------+-----------------------+

```

### Updating the zero point / filter / azimuth / altitude
If, for some reason, we need to change any of these, this command allows you to do so. Note that you must especify at least one magnitude.

Since these attributes versioned columns in the database, a new instrument entry is made with updated `valid_since`, `valid_until` and `valid_state` columns. However, If the  `--latest` flag is passed, the update command only changes the **current** TESS zero point or filter. This is useful to fix errors in the current TESS instrument definition.

`tess instrument update {name} --zero-point {new zp} --filter {new filter} --azimuth {new azimuth} --altitude {new altitude} [--latest]`

Example 1:
`tess instrument update stars3 --zero-point 23.45 --filter BG39`

Example 2:
`tess instrument update stars3 --zero-point 19.99 --filter UVIR --latest`


```
+--------+--------------+----------+---------+---------------------+---------------------+--------------------------+
| TESS   |   Zero Point | Filter   | State   | Since               | Until               | Site                     |
+========+==============+==========+=========+=====================+=====================+==========================+
| stars3 |        19.99 | DG       | Current | 2016-09-08T13:59:12 | 2999-12-31T23:59:59 | Facultad de Fisicas, UCM |
+--------+--------------+----------+---------+---------------------+---------------------+--------------------------+
```


### Listing the history changes of a single TESS instrument
`tess instrument history stars2`

```
+--------+------+-------------------+--------------+----------+---------------------+---------------------+
| TESS   |   Id | MAC Addr.         |   Zero Point | Filter   | Since               | Until               |
+========+======+===================+==============+==========+=====================+=====================+
| stars2 |    7 | 18:FE:34:D3:44:42 |        20    | UVIR     | 2016-05-14T18:23:03 | 2016-05-28T07:23:49 |
+--------+------+-------------------+--------------+----------+---------------------+---------------------+
| stars2 |    8 | 18:FE:34:D3:44:42 |        20.56 | UVIR     | 2016-05-28T07:23:49 | 2016-09-08T11:13:46 |
+--------+------+-------------------+--------------+----------+---------------------+---------------------+
| stars2 |   21 | 18:FE:34:D3:44:42 |        20.5  | UVIR     | 2016-09-08T11:13:46 | 2999-12-31T23:59:59 |
+--------+------+-------------------+--------------+----------+---------------------+---------------------+
```


### Listing TESS readings
`test readings list`
```
+--------------+--------+------------+-------------+-------------+
| Timestamp    | TESS   | Location   | Frequency   | Magnitude   |
+==============+========+============+=============+=============+
+--------------+--------+------------+-------------+-------------+
```

### Show system maintenance window
This command give the start time and duration for a safe system stop. At that time, it is guaranteed that all readings from the different photometers will be discarded due to daylight.

```tess system window
+---------------------+---------------------+----------+
| Start Time (UTC)    | End Time (UTC)      | Window   |
+=====================+=====================+==========+
| 2017-11-04 13:45:03 | 2017-11-04 14:44:35 | 0:59:32  |
+---------------------+---------------------+----------+
```

# Sample SQL Queries

The following are samples queries illustraing how to use the data model. They are actually being used by the STARS4ALL project

1. Get a daily report of readings per instrument:

```sh
#!/bin/bash
sqlite3 /var/dbase/tess.db <<EOF
.mode column
.headers on
SELECT d.sql_date, i.name, count(*) AS readings
FROM tess_readings_t AS r
JOIN tess_t AS i USING (tess_id)
JOIN date_t AS d USING (date_id)
GROUP BY r.date_id, r.tess_id
ORDER BY d.sql_date DESC;
EOF
```

2. Extract a CSV (semicolon separated) with all readings for an instrument passed as a command line argument:

```sh
#!/bin/bash
instrument_name=$1
sqlite3 -csv -header /var/dbase/tess.db <<EOF
SELECT (d.julian_day + t.day_fraction) AS julian_day, (d.sql_date || 'T' || t.time) AS timestamp, r.sequence_number, l.site, i.name, r.frequency, r.magnitude, i.zero_point, r.sky_temperature, r.ambient_temperature
FROM tess_readings_t AS r
JOIN tess_t          AS i USING (tess_id)
JOIN location_t      AS l USING (location_id)
JOIN date_t          AS d USING (date_id)
JOIN time_t          AS t USING (time_id)
WHERE i.name = "${instrument_name}"
ORDER BY r.date_id ASC, r.time_id ASC;
EOF
```

3. Show current TESS instruments. Note that we are using the `tess_v` View,so that the current location info is already included.

```sh
#!/bin/bash
sqlite3 /var/dbase/tess.db <<EOF
.mode column
.headers on
SELECT v.name AS Name, v.mac_address AS MAC, (v.latitude || ' ' || v.longitude) AS Coordinates , (v.site || ', ' || v.location || ', ' || v.province) AS Location, v.contact_email as User, v.zero_point as ZP, v.filter as Filter
FROM tess_v AS v
WHERE v.valid_state = "Current"
ORDER BY v.name ASC;
EOF
```

4. Show TESS instruments changes (zero point and/or filter)

```sh
#!/bin/bash
sqlite3 /var/dbase/tess.db <<EOF
.mode column
.headers on;
SELECT i.name AS Name, i.zero_point as ZP, i.filter as Filter, i.valid_since AS Since, i.valid_until AS Until, i.valid_state AS 'Change State'
FROM tess_t AS i
ORDER BY i.name ASC, i.valid_since ASC;
EOF
```

