#!/bin/sh
set -e

echo ""
echo ""
echo ""

echo "generate-db-dump | Starting Script"
echo $(date +%d-%m-%Y-%H:%M)

# Verifica se existe o banco de dados 
# echo "generate-db-dump | sd-prod exists?"
# if [ psql -lqt | cut -d \| -f 1 | grep -qw sd-prod]; then
#     # database exists
#     # $? is 0

# else
#     # ruh-roh
#     # $? is 1
#     echo "generate-db-dump | Database not found..."
#     exit
# fi

if [[ -z "$1" ]]; then
    echo "Must provide an user to connect on postgres" 1>&2
    exit 1
fi

if [[ -z "$2" ]]; then
    echo "Must provide a password to connect on postgres" 1>&2
    exit 1
fi

if [[ -z "$3" ]]; then
    echo "Must provide database name to be dump" 1>&2
    exit 1
fi

USER=$1
PASSWORD=$2
DB_NAME=$3
REMOTE_SERVER_BACKUP=$4

# stop odoo service
echo "generate-db-dump | Stopping Odoo Production..."
echo $(date +%d-%m-%Y-%H:%M)
sudo systemctl stop odoo-prod.service

# Kill any connection on database
echo "generate-db-dump | Eliminating postgres opened sessions..."
echo $(date +%d-%m-%Y-%H:%M)
sudo PGPASSWORD=$PASSWORD psql -U $USER -d $DB_NAME -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid() AND datname = 'sd-prod'"

# Generate Dump
echo "generate-db-dump | Generating dump..."
sudo pg_dump -v -U $USER $DB_NAME > /tmp/$DB_NAME.dump

# Start Odoo service again
echo "generate-db-dump | Stopping Odoo Production..."
echo $(date +%d-%m-%Y-%H:%M)
sudo systemctl start odoo-prod.service

# Replicate filestore folder
echo "generate-db-dump | Replicating filestore with $DB_NAME folder and files"
echo $(date +%d-%m-%Y-%H:%M)
cp -R /home/ubuntu/.local/share/Odoo/filestore/$DB_NAME /tmp/$DB_NAME

# Zip Filestore folder
echo "generate-db-dump | Zipping filestore..."
echo $(date +%d-%m-%Y-%H:%M)
zip -r /tmp/$DB_NAME-filestore.zip /tmp/$DB_NAME

if [ -z "$REMOTE_SERVER_BACKUP" ]; then 
    echo "Send backup to remote server is disabled"; 
else 
    # Send for new server
    echo "generate-db-dump | Sending backup-data to new server (filestore)"
    echo $(date +%d-%m-%Y-%H:%M)
    rsync -avzhe ssh /tmp/$DB_NAME-filestore.zip $REMOTE_SERVER_BACKUP/$DB_NAME-filestore.zip

    echo "generate-db-dump | Sending backup-data to new server (db)"
    echo $(date +%d-%m-%Y-%H:%M)
    rsync -avzhe ssh /tmp/$DB_NAME.dump $REMOTE_SERVER_BACKUP/$DB_NAME.dump
    ; fi