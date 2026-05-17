#!/usr/bin/env sh
set -eu

MOODLE_DB_HOST="${MOODLE_DATABASE_HOST:-postgres}"
MOODLE_DB_PORT="${MOODLE_DATABASE_PORT_NUMBER:-5432}"
MOODLE_DB_NAME="${MOODLE_DATABASE_NAME:-moodle}"
MOODLE_DB_USER="${MOODLE_DATABASE_USER:-moodle}"
MOODLE_DB_PASSWORD="${MOODLE_DATABASE_PASSWORD:?Set MOODLE_DATABASE_PASSWORD}"
MOODLE_DATA_ROOT="${MOODLE_DATA_ROOT:-/var/moodledata}"
MOODLE_PUBLIC_HOST="${MOODLE_PUBLIC_HOST:-localhost}"
MOODLE_PUBLIC_SCHEME="${MOODLE_PUBLIC_SCHEME:-http}"
MOODLE_SSLPROXY="${MOODLE_SSLPROXY:-no}"

mkdir -p "$MOODLE_DATA_ROOT"
chown -R www-data:www-data "$MOODLE_DATA_ROOT" /var/www/html

if [ ! -f /var/www/html/config.php ]; then
  cat > /var/www/html/config.php <<PHP
<?php
unset(\$CFG);
global \$CFG;
\$CFG = new stdClass();

\$CFG->dbtype    = 'pgsql';
\$CFG->dblibrary = 'native';
\$CFG->dbhost    = '${MOODLE_DB_HOST}';
\$CFG->dbname    = '${MOODLE_DB_NAME}';
\$CFG->dbuser    = '${MOODLE_DB_USER}';
\$CFG->dbpass    = '${MOODLE_DB_PASSWORD}';
\$CFG->prefix    = 'mdl_';
\$CFG->dboptions = array(
  'dbpersist' => 0,
  'dbport' => '${MOODLE_DB_PORT}',
  'dbsocket' => '',
);

\$CFG->wwwroot   = '${MOODLE_PUBLIC_SCHEME}://${MOODLE_PUBLIC_HOST}';
\$CFG->dataroot  = '${MOODLE_DATA_ROOT}';
\$CFG->admin     = 'admin';

\$CFG->directorypermissions = 02777;
PHP

  if [ "$MOODLE_SSLPROXY" = "yes" ]; then
    cat >> /var/www/html/config.php <<'PHP'
$CFG->sslproxy = true;
PHP
  fi

  cat >> /var/www/html/config.php <<'PHP'

require_once(__DIR__ . '/lib/setup.php');
PHP
  chown www-data:www-data /var/www/html/config.php
fi

exec "$@"
