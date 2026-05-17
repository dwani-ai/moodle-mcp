# Deployment Notes

The supported deployment shape is a single GCP VM running Docker Compose.

## VM Checklist

- Ubuntu LTS or Debian.
- Docker Engine and Docker Compose plugin installed.
- DNS records for the app hostname and Moodle hostname.
- Firewall allows inbound `80/tcp` and `443/tcp` only.
- `.env` created from `.env.example` with production secrets.

## Start

```bash
docker compose up -d --build
```

## Logs

```bash
docker compose logs -f app
docker compose logs -f moodle
docker compose logs -f moodle-cron
```

## Backup

Back up PostgreSQL:

```bash
docker compose exec postgres pg_dump -U "$MOODLE_DB_USER" "$MOODLE_DB_NAME" > moodle.sql
```

Back up Moodle data volumes using your VM backup tooling or a volume backup container. Keep database and file backups from the same time window.

## Restore

Restore the database first, then restore `moodle-data` and `moodledata` volumes before starting Moodle.
