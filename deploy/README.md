# Deployment Notes

The supported production deployment shape is three VM-scoped Docker Compose stacks:

- Moodle VM: PostgreSQL, Moodle, Moodle cron, and a Moodle proxy.
- MCP VM: Moodle MCP tool server and optional proxy.
- Agents VM: ADK/API agent web app and optional proxy.

The root compose file remains available for local all-in-one development.

## VM Checklist

- Ubuntu LTS or Debian.
- Docker Engine and Docker Compose plugin installed.
- DNS records for the relevant VM hostname: Moodle, MCP, or app.
- Firewall allows inbound `80/tcp` and `443/tcp` only.
- `.env` created from the service-specific `.env.example` with production secrets.

## Start

Start the Moodle VM first:

```bash
docker compose -f services/moodle/docker-compose.yml up -d --build
```

After Moodle is configured and a Web Services token exists, start the MCP VM:

```bash
docker compose -f services/mcp/docker-compose.yml up -d --build
```

Start the agents VM last:

```bash
docker compose -f services/agents/docker-compose.yml up -d --build
```

## Logs

```bash
docker compose -f services/moodle/docker-compose.yml logs -f moodle moodle-cron
docker compose -f services/mcp/docker-compose.yml logs -f mcp
docker compose -f services/agents/docker-compose.yml logs -f agents
```

## Backup

Back up PostgreSQL:

```bash
docker compose -f services/moodle/docker-compose.yml exec postgres pg_dump -U "$MOODLE_DB_USER" "$MOODLE_DB_NAME" > moodle.sql
```

Back up Moodle data volumes on the Moodle VM using your VM backup tooling or a volume backup container. Keep database and file backups from the same time window.

## Restore

Restore the database first, then restore the `moodledata` volume before starting Moodle.
