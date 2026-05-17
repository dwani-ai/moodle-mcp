# Architecture Diagrams

These diagrams describe the split Moodle, MCP, and ADK agents deployment.

## System Diagram

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
  orchestrator -->|"Bound ADK Moodle tools"| mcpProxy["MCP VM Caddy Proxy"]
  courseCreator -->|"Bound ADK Moodle tools"| mcpProxy
  assessmentBuilder -->|"Bound ADK Moodle tools"| mcpProxy
  studentTutor -->|"Bound ADK Moodle tools"| mcpProxy
  adminEnrollment -->|"Bound ADK Moodle tools"| mcpProxy
  progressMonitor -->|"Bound ADK Moodle tools"| mcpProxy
  contentCurator -->|"Bound ADK Moodle tools"| mcpProxy
  mcpProxy --> mcpServer["Moodle MCP Server"]
  mcpServer -->|"Moodle REST Web Services"| moodleProxy["Moodle VM Caddy Proxy"]
  moodleProxy --> moodleApp["Moodle PHP / Apache"]
  moodleApp --> postgresDb["PostgreSQL"]
  moodleCron["Moodle Cron"] --> moodleApp
  moodleApp --> moodleData["moodledata Volume"]
```

## Sequence Diagram: ADK Chat Request

```mermaid
sequenceDiagram
  actor User
  participant Browser as Browser UI
  participant API as FastAPI /api/chat
  participant Runtime as AdkChatRuntime
  participant Runner as Google ADK Runner
  participant Orchestrator as education_orchestrator
  participant Specialist as Specialist ADK Agent
  participant Toolset as Bound ADK Moodle Tools
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

## Sequence Diagram: Service Startup And Readiness

```mermaid
sequenceDiagram
  participant Operator
  participant MoodleStack as Moodle VM Compose
  participant MCPStack as MCP VM Compose
  participant AgentsStack as Agents VM Compose
  participant Moodle as Moodle
  participant MCP as Moodle MCP Server
  participant Agents as FastAPI Agents App

  Operator->>MoodleStack: docker compose up -d
  MoodleStack->>Moodle: Start Postgres, Moodle, Moodle cron, proxy
  Moodle-->>Operator: Complete setup and create Web Services token
  Operator->>MCPStack: Configure MOODLE_BASE_URL and MOODLE_TOKEN
  Operator->>MCPStack: docker compose up -d
  MCPStack->>MCP: Start streamable HTTP MCP server
  MCP->>Moodle: Validate Moodle Web Services calls
  Operator->>AgentsStack: Configure MCP_SERVER_URL, LLM settings, AGENT_RUNTIME=adk
  Operator->>AgentsStack: docker compose up -d
  AgentsStack->>Agents: Start FastAPI app
  Agents->>MCP: /readyz calls get_current_user through MCP
  MCP->>Moodle: REST Web Services readiness probe
  Moodle-->>MCP: Current user response
  MCP-->>Agents: MCP tool response
  Agents-->>Operator: ready
```
