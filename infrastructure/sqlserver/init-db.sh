#!/bin/bash
set -euo pipefail
: "${SA_PASSWORD:?SA_PASSWORD must be supplied}"
export SQLCMDPASSWORD="$SA_PASSWORD"
SQLCMD=/opt/mssql-tools18/bin/sqlcmd
SERVER="${DB_INIT_SERVER:-sqlserver}"
for service in hotel user room booking payment notification; do
    database="${service}_service"
    exists="$($SQLCMD -S "$SERVER" -U sa -C -b -h -1 -W -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM sys.databases WHERE name=N'$database'")"
    if [[ "$exists" == *1* ]]; then
        echo "Preserving existing database: $database (no automatic migration or reseed)."
        continue
    fi
    script="/usr/config/${service}_database_init.sql"
    if [[ "$service" == hotel ]]; then script=/usr/config/database_update.sql; fi
    echo "Initializing new database: $database"
    "$SQLCMD" -S "$SERVER" -U sa -C -I -b -i "$script"
    if [[ "$service" == user && "${SEED_DEMO_DATA:-0}" == 1 ]]; then
        "$SQLCMD" -S "$SERVER" -U sa -C -I -b -i /usr/config/user_database_demo_seed.sql
    fi
done
echo "Database initialization completed. Existing databases require explicit migrations."
