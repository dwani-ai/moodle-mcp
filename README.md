# Moodle MCP Agent

This project installs Moodle and runs a Python Google ADK-oriented agent that uses MCP-style tools to work with Moodle through Moodle Web Services.

The first version supports two Moodle-backed user flows:

- Creator: create courses and add basic URL resources.
- Student: list and consume enrolled Moodle courses.

## Architecture

- Moodle runs on the same GCP VM as the agent stack.
- Docker Compose starts Moodle, PostgreSQL, Moodle cron, Caddy, and the FastAPI app.
- The FastAPI app serves a simple web chat UI and calls an OpenAI-compatible LLM endpoint.
- Moodle operations are implemented as narrow Python tool functions and exposed through an MCP server.
- Moodle users and roles remain the source of truth for permissions.

## Local Setup

1. Copy the environment template.

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set the Moodle admin password, database password, app secret, LLM key, and hostnames. `MOODLE_DOWNLOAD_URL` controls which Moodle release tarball is baked into the local Moodle image.

3. Start Moodle and the app stack.

   ```bash
   docker compose up -d --build
   ```

4. Open Moodle and finish the initial setup.

   ```text
   http://moodle.localhost
   ```

   After you are logged in, use `http://moodle.localhost` or `http://moodle.localhost/my/`.
   If you manually open `http://moodle.localhost/login/index.php` while already logged in,
   Moodle shows a confirmation page asking whether to log out before logging in as another user.
   Use the explicit `http://` URL for local development so it matches Moodle's configured
   `wwwroot` and avoids proxy scheme redirects.

5. Follow the Moodle Web Services setup guide in `deploy/moodle/SETUP.md`.

6. Add the generated Moodle token to `.env` as `MOODLE_TOKEN`, then restart the app.

   ```bash
   docker compose up -d app
   ```

7. Open the chat app.

   ```text
   http://app.localhost
   ```

For a pure localhost route without custom hostnames, open `http://localhost`.

## Python Development

Use Python 3.12 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,adk]"
pytest
```

Run the API locally:

```bash
uvicorn moodle_mcp.api:app --reload
```

Run the MCP server directly:

```bash
python -m moodle_mcp.mcp_server
```

## Required Moodle Web Services

The app expects Moodle REST Web Services to be enabled with these functions:

- `core_webservice_get_site_info`
- `core_course_get_categories`
- `core_course_create_courses`
- `core_course_get_contents`
- `core_enrol_get_users_courses`
- `core_user_get_users_by_field`
- `mod_url_add_instance`

The exact Moodle role capabilities still need to be configured inside Moodle. Creator users should only receive the course/category permissions they actually need.

## Deployment On GCP VM

1. Create a VM with Docker and the Docker Compose plugin installed.
2. Point DNS records for the app and Moodle hostnames at the VM.
3. Copy the project to the VM.
4. Create a production `.env` from `.env.example`.
5. Run `docker compose up -d --build`.
6. Complete the Moodle setup and Web Services token creation.
7. Configure backups for both PostgreSQL and Moodle data volumes.

Only ports 80 and 443 should be exposed publicly. Database, Moodle container ports, app ports, and MCP ports should remain on the Docker network.

## Current MVP Limits

- Course creation and URL resources are implemented first.
- File upload and richer Moodle activity creation are intentionally left behind capability checks because Moodle Web Services support varies by installation.
- The app accepts a role selector in the MVP UI. Production should derive creator/student permissions from Moodle capabilities instead of trusting the browser.
