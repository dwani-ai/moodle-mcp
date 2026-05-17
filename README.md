# Moodle MCP Agent

This project installs Moodle and runs separate MCP and ADK/API agent services that work with Moodle through Moodle Web Services.

The first version supports two Moodle-backed user flows:

- Creator: create courses and add basic URL resources.
- Student: list and consume enrolled Moodle courses.

## Architecture

- Moodle, PostgreSQL, and Moodle cron can run on their own VM from `services/moodle/docker-compose.yml`.
- The MCP tools can run on a separate VM from `services/mcp/docker-compose.yml`.
- The ADK/API agents and chat UI can run on a separate VM from `services/agents/docker-compose.yml`.
- The root `docker-compose.yml` remains a local all-in-one developer stack with the same service boundaries.
- The FastAPI app serves a simple web chat UI and calls an OpenAI-compatible LLM endpoint.
- Google ADK agent construction uses LiteLLM, so `LLM_PROVIDER=openai` and `LLM_MODEL=gpt-4o-mini` become `openai/gpt-4o-mini`.
- Google ADK also exposes an education orchestrator with specialist sub-agents and reusable education skills.
- Set `AGENT_RUNTIME=adk` to make `/api/chat` call the ADK education orchestrator; set `AGENT_RUNTIME=legacy` to use the original direct OpenAI-compatible tool loop.
- Moodle operations are implemented as narrow Python tool functions and exposed through the MCP server.
- Moodle users and roles remain the source of truth for permissions.

### System Diagram

```mermaid
flowchart LR
  userBrowser["Browser / Educator / Student"] --> agentsProxy["Agents VM Caddy Proxy"]
  agentsProxy --> agentsApi["FastAPI Agents App"]
  agentsApi -->|"POST /api/chat"| adkRuntime["AdkChatRuntime"]
  adkRuntime --> adkRunner["Google ADK Runner"]
  adkRunner --> orchestrator["education_orchestrator"]
  orchestrator --> courseCreator["course_creator_agent"]
  orchestrator --> assessmentBuilder["assessment_builder_agent"]
  orchestrator --> studentTutor["student_tutor_agent"]
  orchestrator --> adminEnrollment["admin_enrollment_agent"]
  orchestrator --> progressMonitor["progress_monitor_agent"]
  orchestrator --> contentCurator["content_curator_agent"]
  orchestrator -->|"ADK McpToolset"| mcpProxy["MCP VM Caddy Proxy"]
  courseCreator -->|"ADK McpToolset"| mcpProxy
  assessmentBuilder -->|"ADK McpToolset"| mcpProxy
  studentTutor -->|"ADK McpToolset"| mcpProxy
  adminEnrollment -->|"ADK McpToolset"| mcpProxy
  progressMonitor -->|"ADK McpToolset"| mcpProxy
  contentCurator -->|"ADK McpToolset"| mcpProxy
  mcpProxy --> mcpServer["Moodle MCP Server"]
  mcpServer -->|"Moodle REST Web Services"| moodleProxy["Moodle VM Caddy Proxy"]
  moodleProxy --> moodleApp["Moodle PHP / Apache"]
  moodleApp --> postgresDb["PostgreSQL"]
  moodleCron["Moodle Cron"] --> moodleApp
  moodleApp --> moodleData["moodledata Volume"]
```

### Sequence Diagram: ADK Chat Request

```mermaid
sequenceDiagram
  actor User
  participant Browser as Browser UI
  participant API as FastAPI /api/chat
  participant Runtime as AdkChatRuntime
  participant Runner as Google ADK Runner
  participant Orchestrator as education_orchestrator
  participant Specialist as Specialist ADK Agent
  participant Toolset as ADK McpToolset
  participant MCP as Moodle MCP Server
  participant Moodle as Moodle Web Services
  participant DB as PostgreSQL

  User->>Browser: Submit education request
  Browser->>API: POST /api/chat with message, role, user_id
  API->>Runtime: chat(role, message, user_id)
  Runtime->>Runner: run_async(new_message)
  Runner->>Orchestrator: Invoke root agent
  Orchestrator->>Specialist: Delegate to relevant education sub-agent
  Specialist->>Toolset: Request Moodle tool when Moodle data or changes are needed
  Toolset->>MCP: call_tool(name, arguments)
  MCP->>Moodle: REST request to /webservice/rest/server.php
  Moodle->>DB: Read or write Moodle state
  DB-->>Moodle: Query result
  Moodle-->>MCP: Web Services response
  MCP-->>Toolset: MCP tool result
  Toolset-->>Specialist: Tool output
  Specialist-->>Orchestrator: Draft final answer
  Orchestrator-->>Runner: Final ADK event
  Runner-->>Runtime: Stream events
  Runtime-->>API: ChatResult answer and event summaries
  API-->>Browser: JSON response
  Browser-->>User: Render agent response
```

## Local Setup

1. Copy the environment template.

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set the Moodle admin password, database password, app secret, LLM key, and hostnames. `MOODLE_DOWNLOAD_URL` controls which Moodle release tarball is baked into the local Moodle image.

3. Start the local all-in-one stack.

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

6. Add the generated Moodle token to `.env` as `MOODLE_TOKEN`, then restart the MCP and agents services.

   ```bash
   docker compose up -d mcp agents
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
moodle-mcp-server --transport stdio
```

Run a network MCP server locally:

```bash
moodle-mcp-server --transport streamable-http --host 0.0.0.0 --port 8000
```

## Google ADK Education Skills

`build_google_adk_agent()` returns an education orchestrator backed by LiteLLM. When `AGENT_RUNTIME=adk`, the FastAPI `/api/chat` endpoint runs that orchestrator through a Google ADK `Runner`. The orchestrator delegates to specialist ADK sub-agents and connects to Moodle through ADK `McpToolset` instances pointed at `MCP_SERVER_URL`.

Call chain:

```text
Browser UI -> /api/chat -> AdkChatRuntime -> education_orchestrator -> specialist sub-agent -> Moodle MCP server -> Moodle Web Services
```

Specialist ADK agents:

- `course_creator_agent`: plans and creates course shells, lessons, and starter resources.
- `assessment_builder_agent`: drafts quizzes, rubrics, assignments, and assessment plans.
- `student_tutor_agent`: helps learners understand visible Moodle course content.
- `admin_enrollment_agent`: guides enrollment, access, role, and cohort workflows.
- `progress_monitor_agent`: reviews engagement signals and recommends support interventions.
- `content_curator_agent`: recommends and places learning resources.

Education skills:

- `course-creation-skill`: category discovery, course shell creation, section planning, URL resources.
- `lesson-planning-skill`: objectives, lesson outlines, activities, and Moodle-ready plans.
- `assessment-builder-skill`: quiz, question bank, rubric, and assignment drafts.
- `student-tutor-skill`: learner explanations, course summaries, and next study steps.
- `admin-enrollment-skill`: user access, enrollment, role, and cohort guidance.
- `progress-engagement-skill`: engagement review and at-risk learner support planning.
- `content-curator-skill`: resource recommendations and URL resource creation.
- `support-assistant-skill`: Moodle navigation, access troubleshooting, and setup support.

The current implemented Moodle tool surface supports course shells, URL resources, categories, enrolled-course listing, and course contents. Skills that need quizzes, assignments, grades, completion, files, enrollment writes, cohorts, or reports are scaffolded with explicit future tool requirements.

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

## Deployment On Separate VMs

Use one checkout of this repo per VM, then run the compose file for that VM:

1. Moodle VM: create `services/moodle/.env` from `services/moodle/.env.example`, then run `docker compose -f services/moodle/docker-compose.yml up -d --build`.
2. Complete Moodle setup and create the Web Services token from `deploy/moodle/SETUP.md`.
3. MCP VM: create `services/mcp/.env` from `services/mcp/.env.example`, set `MOODLE_BASE_URL` to the Moodle VM URL and `MOODLE_TOKEN` to the Web Services token, then run `docker compose -f services/mcp/docker-compose.yml up -d --build`.
4. Agents VM: create `services/agents/.env` from `services/agents/.env.example`, set `MCP_SERVER_URL` to the MCP VM endpoint, set LLM credentials and `LLM_PROVIDER`, then run `docker compose -f services/agents/docker-compose.yml up -d --build`.
5. Configure backups for PostgreSQL and Moodle data volumes on the Moodle VM.

Only ports 80 and 443 should be exposed publicly on each VM. Database, Moodle container ports, agents ports, and raw MCP ports should remain on the Docker network or private VM network.

## Current MVP Limits

- Course creation and URL resources are implemented first.
- File upload and richer Moodle activity creation are intentionally left behind capability checks because Moodle Web Services support varies by installation.
- The app accepts a role selector in the MVP UI. Production should derive creator/student permissions from Moodle capabilities instead of trusting the browser.
