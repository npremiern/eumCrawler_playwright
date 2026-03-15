---
description: EUM Crawler Desktop 구현을 Phase별로 실행합니다
argument-hint: "[phase] - scaffold | db | backend | frontend | crawler | integrate | polish"
---

# /eumcrawl:build Command

You are the EUM Crawler Desktop project orchestrator. Execute the requested implementation phase.

## Available Phases

| Phase | Description | Agent |
|-------|-------------|-------|
| scaffold | 프로젝트 스캐폴딩 (06-PROJECT-SETUP.md) | Direct execution |
| db | 데이터베이스 마이그레이션 및 쿼리 모듈 | eumcrawl-sqlite |
| backend | Rust IPC 커맨드 및 서비스 | eumcrawl-tauri-backend |
| frontend | Svelte UI 페이지 및 컴포넌트 | eumcrawl-svelte-frontend |
| crawler | Playwright 사이드카 구현 | eumcrawl-crawler-sidecar |
| integrate | 통합 및 E2E 테스트 | eumcrawl-orchestrator |
| polish | UI 다듬기 및 빌드 설정 | eumcrawl-svelte-frontend |

## Execution

Read the argument: $ARGUMENTS

If no argument provided, show available phases and ask user which phase to execute.

If argument matches a phase:

1. Read the relevant design documents from `docs/design/`
2. Create a TodoList for the phase tasks
3. Delegate to the appropriate agent with full context:
   - Include relevant design doc paths
   - Include target file paths
   - Include quality checklist from the agent definition
4. Report results when complete

## Design Document Mapping

- scaffold → `06-PROJECT-SETUP.md`
- db → `03-DATABASE.md`
- backend → `02-ARCHITECTURE.md` + `05-API.md` + `03-DATABASE.md`
- frontend → `04-SCREENS.md` + `05-API.md`
- crawler → `02-ARCHITECTURE.md` (Section 4) + `05-API.md` (Part 3)
- integrate → All documents
- polish → `04-SCREENS.md` (Design System section)

## Context

Always provide these to subagents:
- Design doc path: `docs/design/`
- Existing Python code (for crawler porting): `src/`
- Skills: eumcrawl-api-contract, eumcrawl-db-schema, eumcrawl-svelte5-runes, eumcrawl-tauri-v2, eumcrawl-crawler-porting
