# Production Readiness

This project is production-oriented once these controls are enabled in deployment.

## Identity And Authorization

- Keep `ALLOW_USER_ID_OVERRIDE=false` outside local development.
- Configure `MOODLE_CREATOR_USER_IDS` with the Moodle user ids allowed to use creator tools.
- The API resolves the effective Moodle user from `core_webservice_get_site_info` unless overrides are explicitly enabled.
- ADK Moodle tools inject the resolved role and user id into every MCP call; the model does not choose those arguments.

## Required Environment

Agents deployments should set:

- `AGENT_RUNTIME=adk`
- `MCP_SERVER_URL`
- `MCP_CLIENT_TRANSPORT`
- `MOODLE_BASE_URL`
- `MOODLE_TOKEN`
- `MOODLE_CREATOR_USER_IDS`
- `LITELLM_BASE_URL`
- `LITELLM_API_KEY`
- `LITELLM_PROVIDER`
- `LITELLM_MODEL`

## Current Production Tool Surface

- Identity: current Web Services user and user lookup by id, username, or email.
- Course creation: create course shells.
- Content creation: URL resources and page resources.
- Student reads: enrolled courses, course contents, activity completion status.

## Remaining Gaps

- Per-user authentication should replace service-token user simulation for multi-user production.
- Creator detection should eventually use Moodle capability checks instead of `MOODLE_CREATOR_USER_IDS`.
- Enrollment writes, assignments, quizzes, files, grades, and reports are still future tool surfaces.
- ADK sessions are in memory; use persistent session storage before scaling multiple agent replicas.
