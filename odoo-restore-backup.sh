#!/bin/sh
set -e 



echo ""
echo ""
echo ""

echo "odoo-restore-backup | Starting Script"
echo $(date +%d-%m-%Y-%H:%M)


if [[ -z "$1" ]]; then
    echo "Must provide dump file path" 1>&2
    exit 1
fi

if [[ -z "$2" ]]; then
    echo "Must provide filestore zip path" 1>&2
    exit 1
fi

if [[ -z "$3" ]]; then
    echo "Must provide database original name" 1>&2
    exit 1
fi

if [[ -z "$4" ]]; then
    echo "Must provide new database name" 1>&2
    exit 1
fi

if [[ -z "$5" ]]; then
    echo "Must provide odoo conf file" 1>&2
    exit 1
fi

DUMP_FILE_PATH=$1
FILESTORE_ZIP_NAME=$2
DB_NAME=$3
NEW_DB_NAME=$4
ODOO_CONF_PATH=$5

BACKUP_DIR_PATH='' # Set your PATH eg: /Users/<user>/backups
FILESTORE_DIR_PATH='' # Set your PATH eg: /Users/<user>/odoo/filestore

if [[ -z "$BACKUP_DIR_PATH" ]]; then
    echo "Must provide a backup dir path" 1>&2
    exit 1
fi

if [[ -z "$FILESTORE_DIR_PATH" ]]; then
    echo "Must provide a filestore dir path" 1>&2
    exit 1
fi

echo "odoo-restore-backup | Parameters Script"
echo "odoo-restore-backup | Parameters DUMP_FILE_PATH: $DUMP_FILE_PATH"
echo "odoo-restore-backup | Parameters FILESTORE_ZIP_NAME: $FILESTORE_ZIP_NAME"
echo "odoo-restore-backup | Parameters DB_NAME: $DB_NAME"
echo "odoo-restore-backup | Parameters NEW_DB_NAME: $NEW_DB_NAME"
echo "odoo-restore-backup | Parameters ODOO_CONF_PATH: $ODOO_CONF_PATH"


# Executa o comando PSQL para matar as conexões do banco
PGPASSWORD="odoo" psql -U odoo -p 6432 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid() AND datname = '$DB_NAME'"
PGPASSWORD="odoo" psql -U odoo -p 6432 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid() AND datname = '$NEW_DB_NAME'"
# Executa o comando PSQL para apagar o banco
PGPASSWORD="odoo" psql -U odoo -p 6432 -c 'DROP DATABASE "'$DB_NAME'";'
# Executa o comando PSQL para criar o banco
PGPASSWORD="odoo" psql -U odoo -p 6432 -c 'CREATE DATABASE "'$DB_NAME'";'
# Executa o comando PSQL para reestaelecer o dump
PGPASSWORD="odoo" psql -U odoo -p 6432 -c 'DROP DATABASE "'$NEW_DB_NAME'";' 
# Executa o comando PSQL para criar o banco
PGPASSWORD="odoo" psql -U odoo -p 6432 -c 'CREATE DATABASE "'$NEW_DB_NAME'";'
# Executa o comando PSQL para reestaelecer o dump
PGPASSWORD="odoo" psql -U odoo -p 6432 -d "$NEW_DB_NAME" < $DUMP_FILE_PATH
# Executa o comando PSQL a limpeza do ir_cron
PGPASSWORD="odoo" psql -U odoo -p 6432 -d "$NEW_DB_NAME" -c "UPDATE public.ir_cron SET active = FALSE;"
# Executa o comando PSQL a limpeza do ir_mail_server
PGPASSWORD="odoo" psql -U odoo -p 6432 -d "$NEW_DB_NAME" -c "UPDATE public.ir_mail_server SET active = FALSE;"
# Executa o comando PSQL a limpeza do ir_mail_server
PGPASSWORD="odoo" psql -U odoo -p 6432 -d "$NEW_DB_NAME" -c 'UPDATE public.ir_config_parameter SET value = '"'"'http://localhost:8069'"'"' WHERE "key" = '"'"'web.base.url'"'"' ;'
# Seta a senha padrão como admin ()
PGPASSWORD="odoo" psql -U odoo -p 6432 -d "$NEW_DB_NAME" -c 'UPDATE public.res_users SET password = '"'"'$pbkdf2-sha512$25000$glBKydl7TwlBiPFeqzXGWA$bHNaubY8NZFR2hn6QkPk.bBHnkcCe2ceV3N56w9ObqThRpydpVFY.eptd/3TZunVKX9KwoYM3pSmAr58VVsxlg'"'"';'
# Insert Token
PGPASSWORD="odoo" psql -U odoo -p 6432 -d "$NEW_DB_NAME" -c 'INSERT INTO public.api_access_token ("token", user_id, expires, "scope", create_uid, create_date, write_uid, write_date) VALUES('"'"'access_token_4e4d28b653c2c366fbd33c56cba85bsf12312e6b'"'"', 2, '"'"'2055-04-06 15:20:40.000'"'"', '"'"'userinfo'"'"', 1, '"'"'2022-07-20 15:20:40.000'"'"', 1, '"'"'2022-07-20 15:20:40.000'"'"');'

# Insert mail_hog
PGPASSWORD="odoo" psql -U odoo -p 6432 -d "$NEW_DB_NAME" -c 'INSERT INTO public.ir_mail_server ("name", smtp_host, smtp_port, smtp_user, smtp_pass, smtp_encryption, smtp_debug, "sequence", active, create_uid, create_date, write_uid, write_date) VALUES('"'"'mailhog'"'"', '"'"'localhost'"'"', 1026, '"'"'contato@waybee.com.br'"'"', '"'"'email'"'"', '"'"'none'"'"', true, 1, true, 2, '"'"'2022-08-03'"'"', 2, '"'"'2022-08-03'"'"');'

pwd
cp $BACKUP_DIR_PATH/$FILESTORE_ZIP_NAME.zip $FILESTORE_DIR_PATH
pwd
cd $FILESTORE_DIR_PATH && unzip $FILESTORE_ZIP_NAME.zip
pwd
rm -rf $NEW_DB_NAME
mv $DB_NAME $NEW_DB_NAME

chmod -R 777 $NEW_DB_NAME

# Set the current postgresql version
brew services restart pgbouncer && brew services restart postgresql@12

echo ""
echo ""
echo ""

echo "odoo-restore-backup | New database loaded $NEW_DB_NAME"

echo ""
echo ""
echo ""