#!/bin/bash
# Orphaned names when renaming

# ------------------------------------------------------------------------------
#                             AUXILIARY FUNCTIONS
# ------------------------------------------------------------------------------

orphaned_names() {
dbase=$1
sqlite3 -csv -header ${dbase} <<EOF
.separator ;
SELECT name as label, max(valid_until) as expiration_date
FROM name_to_mac_t
WHERE name IN
    (SELECT name
    FROM name_to_mac_t
    EXCEPT
    SELECT name as label
    FROM name_to_mac_t
    WHERE valid_state = "Current")
GROUP BY NAME
ORDER BY name ASC;
EOF
}

names_history() {
dbase=$1
sqlite3 -csv -header ${dbase} <<EOF
.separator ;
SELECT name as label, mac_address, valid_since, valid_until, valid_state as state
FROM name_to_mac_t
ORDER BY CAST(substr(name, 6) as decimal) ASC;
EOF
}


# ------------------------------------------------------------------------------

# may be we need it ..
TODAY=$(date +%Y%m%d)

DEFAULT_DATABASE="/var/dbase/tess.db"
DEFAULT_REPORTS_DIR="/var/dbase/reports"

# Arguments from the command line & default values

# Either the default or the rotated tess.db-* database
dbase="${1:-$DEFAULT_DATABASE}"
# wildcard expansion ...
dbase="$(ls -1 $dbase)"

out_dir="${2:-$DEFAULT_REPORTS_DIR}"

# get the name from the script name without extensions
name=$(basename ${0%.sh})

if  [[ ! -f $dbase || ! -r $dbase ]]; then
        echo "Database file $dbase does not exists or is not readable."
        echo "Exiting"
        exit 1
fi

dbname=$(basename $dbase)
oper_dbname=$(basename $DEFAULT_DATABASE)

if [[ "$dbname" = "$oper_dbname" ]]; then
    operational_dbase="yes"
else
    operational_dbase="no"
fi

# Stops background database I/O when using the operational database
if  [[ operational_dbase="yes" ]]; then
        echo "Pausing tessdb service."
    	/usr/local/bin/tessdb_pause 
		/bin/sleep 2
else
	echo "Using backup database, no need to pause tessdb service."
fi

names_history  ${dbase} > ${out_dir}/${name}.csv
orphaned_names ${dbase} > ${out_dir}/${name}_orphaned.csv

# Resume background database I/O
if  [[ operational_dbase="yes" ]]; then
        echo "Resuming tessdb service."
    	/usr/local/bin/tessdb_resume 
else
	echo "Using backup database, no need to resume tessdb service."
fi

