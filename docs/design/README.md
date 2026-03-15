# EUM Crawler Desktop - 설계 문서

## 프로젝트 개요

기존 Python + Tkinter 기반 부동산 정보 크롤러(eum.go.kr)를 **Svelte 5 + Tauri v2 + Bun + Playwright** 스택으로 재구축하기 위한 종합 설계 문서입니다.

## 기술 스택

| 영역 | 기술 | 비고 |
|------|------|------|
| Frontend | Svelte 5 (Runes) + SvelteKit | UI/UX |
| Desktop | Tauri v2 (Rust) | 네이티브 래퍼 |
| Runtime | Bun | JS 런타임/패키지 매니저 |
| Crawler | Playwright | 브라우저 자동화 (Sidecar) |
| Database | SQLite | 로컬 데이터 저장 |
| Styling | Tailwind CSS + shadcn-svelte | UI 컴포넌트 |

## 핵심 기능

- 부동산 공시가격 알리미(eum.go.kr) 데이터 자동 수집
- SQLite 기반 데이터 저장 및 검색
- 캐시/재사용 (설정 가능한 유효기간)
- 일괄 크롤링 작업 관리 (대기/실행/일시정지/완료)
- Excel 가져오기/내보내기
- 이미지 및 PDF 다운로드
- 검색 이력 및 필터링

## 문서 목록

| # | 문서 | 설명 | 크기 |
|---|------|------|------|
| 01 | [PRD (제품 요구사항)](./01-PRD.md) | 기능/비기능 요구사항, 사용자 시나리오, 범위 정의 | ~51KB |
| 02 | [기술 아키텍처](./02-ARCHITECTURE.md) | 시스템 구조, 컴포넌트 설계, 통신 프로토콜, 빌드/배포 | ~75KB |
| 03 | [데이터베이스 설계](./03-DATABASE.md) | 테이블 스키마, 인덱싱, 마이그레이션, 주요 쿼리, 캐시 로직 | ~67KB |
| 04 | [화면 설계](./04-SCREENS.md) | 디자인 시스템, 8개 화면 와이어프레임, 컴포넌트 명세 | ~64KB |
| 05 | [API/IPC 인터페이스](./05-API.md) | Tauri IPC 커맨드, 이벤트, Sidecar 프로토콜, 타입 정의 | ~49KB |
| 06 | [프로젝트 설정 가이드](./06-PROJECT-SETUP.md) | 프로젝트 생성, 설정 파일, 보일러플레이트, 개발 워크플로우 | ~38KB |

## 문서 간 관계

```
01-PRD (요구사항 정의)
  ├── 02-ARCHITECTURE (기술 설계)
  │     ├── 03-DATABASE (데이터 계층)
  │     ├── 04-SCREENS (프레젠테이션 계층)
  │     └── 05-API (통신 계층)
  └── 06-PROJECT-SETUP (구현 시작점)
```

## 읽는 순서

1. **01-PRD.md** - 전체 요구사항과 범위 파악
2. **02-ARCHITECTURE.md** - 시스템 구조 이해
3. **03-DATABASE.md** - 데이터 모델 확인
4. **04-SCREENS.md** - UI 설계 확인
5. **05-API.md** - Frontend ↔ Backend 인터페이스 확인
6. **06-PROJECT-SETUP.md** - 프로젝트 생성 및 개발 시작

## 구현 순서 권장

### Phase 1: 프로젝트 기반 구축
- 06-PROJECT-SETUP.md 따라 프로젝트 스캐폴딩
- 03-DATABASE.md의 마이그레이션 스크립트 적용
- 기본 레이아웃 (사이드바, 헤더) 구현

### Phase 2: 핵심 CRUD
- 주소 관리 (추가/수정/삭제/목록)
- Excel 가져오기
- 설정 페이지

### Phase 3: 크롤링 엔진
- Playwright Sidecar 구현 (기존 Python 로직 포팅)
- Tauri ↔ Sidecar 통신
- 크롤링 작업 생성/실행/진행상황

### Phase 4: 결과 관리
- 결과 목록/상세/검색/필터
- 캐시 로직 구현
- 이미지/PDF 뷰어

### Phase 5: 내보내기 및 마무리
- Excel/CSV 내보내기
- 대시보드
- 빌드/배포 설정

## 기존 프로젝트 대비 주요 변경사항

| 항목 | 기존 (Python) | 신규 (Svelte/Tauri) |
|------|--------------|---------------------|
| UI | Tkinter | Svelte 5 + Tailwind |
| 데이터 저장 | Excel 직접 읽기/쓰기 | SQLite DB |
| 크롤러 | Python Playwright | Bun Playwright (Sidecar) |
| 배포 | PyInstaller EXE | Tauri MSI Installer |
| 캐시 | 없음 | SQLite 기반 캐시 |
| 검색/필터 | 없음 | FTS5 전문 검색 |
| 작업 관리 | 단일 작업 | 일괄 작업 큐 |

---

*작성일: 2026-03-10*
*총 문서 규모: 11,345줄, 344KB*
