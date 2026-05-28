#!/usr/bin/env bash

set -e

export GREENPLUM_PORT=${GREENPLUM_PORT:-5432}
export GREENPLUM_DB=${GREENPLUM_DB:-default}
export GREENPLUM_USER=${GREENPLUM_USER:-default}
export GREENPLUM_PASSWORD=${GREENPLUM_PASSWORD:-default}
export COORDINATOR_DATA_DIRECTORY=/greenplum/master/gp-1

# Start sshd as root
echo "Starting sshd service"
service ssh start

# Graceful shutdown handler
function greenplum_shutdown() {
    echo "Received shutdown signal. Start Greenplum stop script"
    su - gpadmin -c "yes Y | gpstop -M fast"
    exit 0
}
trap "greenplum_shutdown" SIGTERM SIGINT

# Start Greenplum cluster
su - gpadmin -c "yes Y | gpstart"

# Create database if not exists
su - gpadmin -c "psql -h $(hostname) -p ${GREENPLUM_PORT} -U gpadmin -d postgres -tc \"SELECT 1 FROM pg_database WHERE datname='${GREENPLUM_DB}';\" | grep -q 1 || psql -h $(hostname) -p ${GREENPLUM_PORT} -U gpadmin -d postgres -c \"create database \"\"${GREENPLUM_DB}\"\";\""

# Create user if not exists and grant privileges
su - gpadmin -c "psql -h $(hostname) -p ${GREENPLUM_PORT} -U gpadmin -d postgres -tc \"SELECT 1 FROM pg_roles WHERE rolname='${GREENPLUM_USER}';\" | grep -q 1 || psql -h $(hostname) -p ${GREENPLUM_PORT} -U gpadmin -d postgres -c \"create user \"\"${GREENPLUM_USER}\"\" with password '${GREENPLUM_PASSWORD}'; alter user \"\"${GREENPLUM_USER}\"\" with superuser; grant all privileges on database \"\"${GREENPLUM_DB}\"\" to \"\"${GREENPLUM_USER}\"\";\""

# Apply Data Vault SQL if present
if [ -f /docker-entrypoint-initdb.d/init_data_vault.sql ]; then
    echo "Applying Data Vault schema from /docker-entrypoint-initdb.d/init_data_vault.sql"
    su - gpadmin -c "psql -h $(hostname) -p ${GREENPLUM_PORT} -U gpadmin -d ${GREENPLUM_DB} -f /docker-entrypoint-initdb.d/init_data_vault.sql"
fi

export MASTER_LOG_DIR="/greenplum/master/gp-1/log"
export SEGMENT_LOG_DIR="/greenplum/segment1/gp0/log"

tail -f $MASTER_LOG_DIR/*.csv $SEGMENT_LOG_DIR/*.csv &
wait
