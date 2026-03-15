# 기술 아키텍처 설계 (Technical Architecture Design)

**프로젝트명**: eumcrawl-desktop
**상태**: 설계 문서
**작성일**: 2025-03-10
**버전**: 1.0
**대상**: 개발자 & 아키텍트

---

## 개요 (Overview)

eumcrawl-desktop은 Python Tkinter 기반의 부동산 정보 크롤러를 현대적인 스택으로 마이그레이션하는 프로젝트입니다. Svelte 5, Tauri v2, Rust, Bun, SQLite를 활용하여 고성능의 크로스플랫폼 데스크톱 애플리케이션을 구축합니다.

### 핵심 특징

- **현대적 UI**: Svelte 5 기반의 반응형 사용자 인터페이스
- **네이티브 성능**: Tauri v2를 통한 Rust 기반 백엔드
- **빠른 빌드**: Bun 패키지 매니저 및 런타임
- **스크래핑 엔진**: Playwright를 별도 프로세스로 실행하는 사이드카 아키텍처
- **데이터 관리**: SQLite 데이터베이스 (로컬 저장)
- **효율적 상태관리**: Svelte 5 runes을 활용한 리액티브 상태관리

---

## 1. 시스템 아키텍처 개요

### 1.1 고수준 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                    Desktop Application (eumcrawl)               │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Frontend Layer (Svelte 5 + SvelteKit)                    │   │
│  │  - Dashboard, Address Management, Job Monitor            │   │
│  │  - Results Display, Settings, Export                      │   │
│  │  - Real-time Status Updates via WebSocket Events          │   │
│  └───────────────────┬──────────────────────────────────────┘   │
│                      │                                            │
│                      │ IPC Commands & Events                      │
│                      ▼                                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Tauri Application Window (Rust Bridge)                  │   │
│  │  - IPC Command Handler                                    │   │
│  │  - Event Emitter                                          │   │
│  │  - File System Bridge                                     │   │
│  └───────────────┬──────────────────┬───────────────────────┘   │
│                  │                  │                            │
│        ┌─────────▼─────────┐  ┌─────▼──────────┐               │
│        │ Command Handlers  │  │ Event System   │               │
│        │ (Rust commands)   │  │ (Real-time)    │               │
│        └─────────┬─────────┘  └─────┬──────────┘               │
│                  │                  │                            │
│  ┌───────────────▼──────────────────▼──────────────────────┐   │
│  │  Application Services (Rust)                             │   │
│  │  ┌─────────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │  │ DB Service  │  │ Crawler  │  │ File     │           │   │
│  │  │ (SQLite)    │  │ Manager  │  │ Service  │           │   │
│  │  └─────────────┘  └──────────┘  └──────────┘           │   │
│  └───────────────┬──────────────────┬───────────────────────┘   │
│                  │                  │                            │
│        ┌─────────▼─────────┐  ┌─────▼──────────────────┐       │
│        │ SQLite Database   │  │ Crawler Sidecar (Bun) │       │
│        │ - Addresses       │  │ - Playwright Engine   │       │
│        │ - Results         │  │ - Scraper Logic       │       │
│        │ - Jobs            │  │ - Image Downloader    │       │
│        │ - Cache           │  │ - PDF Generator       │       │
│        └───────────────────┘  └───────────────────────┘       │
│                                                                │
│        External                       External                 │
│        ┌────────────────┐              ┌──────────────┐        │
│        │ File System    │              │ eum.go.kr    │        │
│        │ - Excel Files  │              │ (웹사이트)   │        │
│        │ - Images       │              │              │        │
│        │ - PDFs         │              │              │        │
│        └────────────────┘              └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 컴포넌트 관계

| 컴포넌트 | 역할 | 통신 방식 | 의존성 |
|---------|------|---------|--------|
| Svelte Frontend | UI 렌더링, 사용자 상호작용 | IPC Commands | Tauri Bridge |
| Tauri Rust Backend | 시스템 통합, 커맨드 처리 | Command handlers | Database, Sidecar |
| SQLite Database | 데이터 영속성 | SQL queries | Rust native drivers |
| Crawler Sidecar | Playwright 스크래핑 | stdin/stdout JSON | Playwright, File I/O |
| File System | 파일 저장/읽기 | Direct I/O | OS APIs |

### 1.3 데이터 흐름 개요

```
User Input (UI)
    ↓
Svelte Component
    ↓
IPC Command (invoke())
    ↓
Tauri Rust Handler
    ↓
Application Service
    ↓
[If crawling]
    ├→ Start Crawler Sidecar (Bun)
    │  ├→ Playwright Browser
    │  ├→ eum.go.kr Navigation
    │  └→ Data Extraction
    │      ↓
    │  → Save to Database
    │  → Emit Progress Events
    │  → Download Resources
    │
[If database]
    ├→ Query SQLite
    ├→ Format Results
    └→ Return to Frontend
        ↓
    Frontend State Update ($state)
        ↓
    UI Re-render (Svelte reactivity)
        ↓
    User Sees Results
```

---

## 2. 프론트엔드 아키텍처 (Svelte 5 + SvelteKit)

### 2.1 디렉토리 구조

```
src/
├── app.html                           # HTML 진입점
├── app.css                            # 글로벌 스타일
│
├── lib/
│   ├── components/
│   │   ├── ui/                        # Base UI 컴포넌트
│   │   │   ├── Button.svelte
│   │   │   ├── Input.svelte
│   │   │   ├── Table.svelte
│   │   │   ├── Modal.svelte
│   │   │   ├── Card.svelte
│   │   │   ├── Badge.svelte
│   │   │   ├── ProgressBar.svelte
│   │   │   ├── Toast.svelte
│   │   │   ├── Tabs.svelte
│   │   │   └── Dialog.svelte
│   │   │
│   │   ├── address/                   # 주소 관련 컴포넌트
│   │   │   ├── AddressInput.svelte     # 주소 입력 폼
│   │   │   ├── AddressList.svelte      # 주소 목록 표시
│   │   │   ├── AddressImportModal.svelte # Excel 가져오기
│   │   │   └── AddressDeleteConfirm.svelte
│   │   │
│   │   ├── result/                    # 결과 표시 컴포넌트
│   │   │   ├── ResultTable.svelte      # 결과 테이블
│   │   │   ├── ResultDetail.svelte     # 상세 정보 모달
│   │   │   ├── ResultPreview.svelte    # 이미지 미리보기
│   │   │   ├── ResultSearch.svelte     # 결과 검색 필터
│   │   │   └── ResultExportDialog.svelte
│   │   │
│   │   ├── job/                       # 작업 관리 컴포넌트
│   │   │   ├── JobMonitor.svelte       # 진행 상황 모니터
│   │   │   ├── JobProgress.svelte      # 진행률 표시
│   │   │   ├── JobLog.svelte           # 로그 출력
│   │   │   ├── JobControls.svelte      # 시작/일시정지/중지 버튼
│   │   │   └── JobStatus.svelte        # 상태 표시
│   │   │
│   │   └── layout/                    # 레이아웃 컴포넌트
│   │       ├── Sidebar.svelte         # 사이드바 네비게이션
│   │       ├── Header.svelte          # 헤더 & 제목
│   │       ├── Footer.svelte          # 푸터
│   │       └── AppLayout.svelte       # 전체 레이아웃
│   │
│   ├── stores/                        # Svelte Stores (상태관리)
│   │   ├── addresses.ts               # 주소 저장소
│   │   │   export: $state, loadAddresses(), addAddress(),
│   │   │            deleteAddress(), importFromExcel()
│   │   │
│   │   ├── results.ts                 # 결과 저장소
│   │   │   export: $state, loadResults(), getResult(),
│   │   │            deleteResult(), searchResults()
│   │   │
│   │   ├── jobs.ts                    # 작업 저장소
│   │   │   export: $state, startJob(), pauseJob(),
│   │   │            resumeJob(), stopJob(), getJobStatus()
│   │   │
│   │   ├── settings.ts                # 설정 저장소
│   │   │   export: $state, loadSettings(), updateSetting()
│   │   │
│   │   ├── cache.ts                   # 캐시 저장소
│   │   │   export: $state, getCachedAddress(),
│   │   │            clearCache()
│   │   │
│   │   └── ui.ts                      # UI 상태 저장소
│   │       export: $state, showToast(), hideToast()
│   │
│   ├── services/                      # Tauri IPC 래퍼
│   │   ├── db.ts                      # 데이터베이스 서비스
│   │   │   export: getAddresses(), addAddress(),
│   │   │            getResults(), searchResults()
│   │   │
│   │   ├── crawler.ts                 # 크롤러 제어 서비스
│   │   │   export: startCrawlJob(), pauseJob(),
│   │   │            resumeJob(), stopJob()
│   │   │
│   │   ├── file.ts                    # 파일 작업 서비스
│   │   │   export: importExcel(), selectFile(),
│   │   │            openFolder()
│   │   │
│   │   ├── export.ts                  # 내보내기 서비스
│   │   │   export: exportToExcel(), exportToCSV(),
│   │   │            exportToPDF()
│   │   │
│   │   └── ipc.ts                     # 낮은 수준 IPC 유틸
│   │       export: invoke(), listen(), once()
│   │
│   ├── types/                         # TypeScript 타입 정의
│   │   ├── address.ts
│   │   │   export: Address, AddressImportOptions
│   │   │
│   │   ├── result.ts
│   │   │   export: Result, ResultSearchFilter
│   │   │
│   │   ├── job.ts
│   │   │   export: Job, JobStatus, JobProgress
│   │   │
│   │   ├── settings.ts
│   │   │   export: Settings, Theme, CrawlerConfig
│   │   │
│   │   └── api.ts
│   │       export: 모든 IPC 커맨드 & 이벤트 타입
│   │
│   └── utils/                         # 유틸리티 함수
│       ├── formatters.ts              # 데이터 포맷팅
│       ├── validators.ts              # 입력 검증
│       ├── date.ts                    # 날짜 처리
│       ├── file.ts                    # 파일 경로 처리
│       └── constants.ts               # 상수 정의
│
├── routes/                            # SvelteKit 페이지
│   ├── +layout.svelte                 # 루트 레이아웃 (Sidebar + Header)
│   ├── +layout.ts                     # 레이아웃 로드 함수
│   ├── +page.svelte                   # 대시보드 페이지
│   ├── +page.ts                       # 대시보드 로드 함수
│   │
│   ├── addresses/
│   │   ├── +page.svelte               # 주소 관리 페이지
│   │   ├── +page.ts                   # 로드 함수
│   │   ├── [id]/
│   │   │   ├── +page.svelte           # 주소 상세 페이지 (선택사항)
│   │   │   └── +page.ts
│   │   └── import/
│   │       ├── +page.svelte           # 주소 가져오기 페이지
│   │       └── +page.ts
│   │
│   ├── jobs/
│   │   ├── +page.svelte               # 작업 모니터 페이지
│   │   ├── +page.ts
│   │   ├── [id]/
│   │   │   ├── +page.svelte           # 작업 상세 페이지
│   │   │   └── +page.ts
│   │   └── new/
│   │       ├── +page.svelte           # 새 작업 생성 페이지
│   │       └── +page.ts
│   │
│   ├── results/
│   │   ├── +page.svelte               # 결과 검색 & 표시 페이지
│   │   ├── +page.ts
│   │   ├── [id]/
│   │   │   ├── +page.svelte           # 결과 상세 페이지
│   │   │   └── +page.ts
│   │   └── export/
│   │       ├── +page.svelte           # 내보내기 페이지
│   │       └── +page.ts
│   │
│   ├── settings/
│   │   ├── +page.svelte               # 설정 페이지
│   │   ├── +page.ts
│   │   ├── crawler/
│   │   │   ├── +page.svelte           # 크롤러 설정
│   │   │   └── +page.ts
│   │   └── appearance/
│   │       ├── +page.svelte           # 외관 설정
│   │       └── +page.ts
│   │
│   └── +error.svelte                  # 에러 페이지

tailwind.config.ts                      # Tailwind CSS 설정
svelte.config.js                        # SvelteKit 설정
tsconfig.json                           # TypeScript 설정
vite.config.ts                          # Vite 빌드 설정
```

### 2.2 상태관리 패턴 (Svelte 5 Runes)

#### 2.2.1 기본 Store 예시 (addresses.ts)

```typescript
import { invoke } from '@tauri-apps/api/core';
import type { Address } from '../types/address';

// 상태 정의
let addresses = $state<Address[]>([]);
let isLoading = $state(false);
let error = $state<string | null>(null);

// 파생 상태 (derived state)
let totalAddresses = $derived(addresses.length);
let processedAddresses = $derived(
  addresses.filter(a => a.result_id !== null)
);
let pendingAddresses = $derived(
  addresses.filter(a => a.result_id === null)
);

// 효과 (side effects)
$effect(() => {
  if (error) {
    const timer = setTimeout(() => {
      error = null;
    }, 5000);
    return () => clearTimeout(timer);
  }
});

// 액션 함수들
export async function loadAddresses() {
  isLoading = true;
  error = null;
  try {
    addresses = await invoke('get_addresses');
  } catch (err) {
    error = `주소 로드 실패: ${err}`;
  } finally {
    isLoading = false;
  }
}

export async function addAddress(address: Omit<Address, 'id'>) {
  try {
    const newAddress = await invoke('add_address', { address });
    addresses.push(newAddress);
  } catch (err) {
    error = `주소 추가 실패: ${err}`;
    throw err;
  }
}

export async function deleteAddress(id: number) {
  try {
    await invoke('delete_address', { id });
    addresses = addresses.filter(a => a.id !== id);
  } catch (err) {
    error = `주소 삭제 실패: ${err}`;
    throw err;
  }
}

export async function importFromExcel(filePath: string) {
  isLoading = true;
  error = null;
  try {
    const newAddresses = await invoke('import_from_excel', { filePath });
    addresses.push(...newAddresses);
  } catch (err) {
    error = `Excel 가져오기 실패: ${err}`;
  } finally {
    isLoading = false;
  }
}

// Export를 위한 Svelte Store 반환
export function getAddressesStore() {
  return {
    get addresses() { return addresses; },
    get isLoading() { return isLoading; },
    get error() { return error; },
    get totalAddresses() { return totalAddresses; },
    get processedAddresses() { return processedAddresses; },
    get pendingAddresses() { return pendingAddresses; },
    loadAddresses,
    addAddress,
    deleteAddress,
    importFromExcel
  };
}
```

#### 2.2.2 Jobs Store with Real-time Events (jobs.ts)

```typescript
import { invoke, listen } from '@tauri-apps/api/core';
import type { Job, JobProgress } from '../types/job';

let jobs = $state<Job[]>([]);
let currentJob = $state<Job | null>(null);
let progress = $state<JobProgress>({
  total: 0,
  completed: 0,
  failed: 0,
  current_address: '',
  percentage: 0,
  status: 'idle'
});

// 이벤트 리스너 설정
let unlistenProgressFn: (() => void) | null = null;
let unlistenCompleteFn: (() => void) | null = null;

$effect(() => {
  // 컴포넌트 마운트 시 리스너 등록
  setupListeners();

  return () => {
    // 언마운트 시 리스너 제거
    unlistenProgressFn?.();
    unlistenCompleteFn?.();
  };
});

async function setupListeners() {
  unlistenProgressFn = await listen('crawl://progress', (event) => {
    const data = event.payload as JobProgress;
    progress = data;
  });

  unlistenCompleteFn = await listen('crawl://complete', (event) => {
    const data = event.payload as Job;
    if (currentJob) {
      currentJob.status = 'completed';
    }
  });
}

export async function startCrawlJob(jobConfig: unknown) {
  try {
    const job = await invoke('start_crawl_job', { config: jobConfig });
    currentJob = job;
    jobs.push(job);
  } catch (err) {
    throw err;
  }
}

export async function pauseJob(jobId: number) {
  await invoke('pause_job', { job_id: jobId });
  if (currentJob?.id === jobId) {
    currentJob.status = 'paused';
  }
}

export async function resumeJob(jobId: number) {
  await invoke('resume_job', { job_id: jobId });
  if (currentJob?.id === jobId) {
    currentJob.status = 'running';
  }
}

export async function stopJob(jobId: number) {
  await invoke('stop_job', { job_id: jobId });
  if (currentJob?.id === jobId) {
    currentJob.status = 'stopped';
  }
}

export function getJobsStore() {
  return {
    get jobs() { return jobs; },
    get currentJob() { return currentJob; },
    get progress() { return progress; },
    startCrawlJob,
    pauseJob,
    resumeJob,
    stopJob
  };
}
```

### 2.3 주요 컴포넌트 디자인

#### 2.3.1 페이지 컴포넌트 (Dashboard: routes/+page.svelte)

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { getAddressesStore } from '$lib/stores/addresses';
  import { getJobsStore } from '$lib/stores/jobs';
  import AddressInput from '$lib/components/address/AddressInput.svelte';
  import JobMonitor from '$lib/components/job/JobMonitor.svelte';
  import ResultTable from '$lib/components/result/ResultTable.svelte';
  import Card from '$lib/components/ui/Card.svelte';

  const addressStore = getAddressesStore();
  const jobStore = getJobsStore();

  onMount(async () => {
    await addressStore.loadAddresses();
  });

  async function handleStartJob() {
    await jobStore.startCrawlJob({
      addresses: addressStore.pendingAddresses.map(a => a.id)
    });
  }
</script>

<div class="dashboard">
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
    <!-- 왼쪽: 주소 입력 & 목록 -->
    <div class="lg:col-span-1">
      <Card title="주소 입력">
        <AddressInput />
      </Card>

      <Card title="주소 목록" class="mt-4">
        <!-- 목록 표시 -->
        {#each addressStore.pendingAddresses as address (address.id)}
          <div class="p-2 border-b">
            {address.address}
          </div>
        {/each}
      </Card>
    </div>

    <!-- 중간/오른쪽: 작업 모니터 & 결과 -->
    <div class="lg:col-span-2">
      <Card title="작업 모니터">
        <JobMonitor
          job={jobStore.currentJob}
          progress={jobStore.progress}
          onStart={handleStartJob}
        />
      </Card>

      <Card title="결과" class="mt-4">
        <ResultTable results={addressStore.processedAddresses} />
      </Card>
    </div>
  </div>
</div>

<style>
  .dashboard {
    padding: 1rem;
  }
</style>
```

### 2.4 컴포넌트 통신 패턴

```
User Interaction (UI)
    ↓
Svelte Component (event handler)
    ↓
Call Store Action (e.g., addAddress())
    ↓
IPC Command invoke() to Tauri
    ↓
Update Local $state
    ↓
Reactive Update ($derived expressions re-run)
    ↓
Component Re-render
    ↓
User Sees Changes
```

---

## 3. Tauri 백엔드 아키텍처 (Rust)

### 3.1 Tauri 프로젝트 구조

```
src-tauri/
├── src/
│   ├── main.rs                        # 애플리케이션 진입점
│   ├── lib.rs                         # 라이브러리 루트
│   │
│   ├── commands/                      # IPC 커맨드 핸들러
│   │   ├── mod.rs
│   │   ├── address_commands.rs        # 주소 관련 커맨드
│   │   ├── crawler_commands.rs        # 크롤러 제어 커맨드
│   │   ├── result_commands.rs         # 결과 조회 커맨드
│   │   ├── settings_commands.rs       # 설정 커맨드
│   │   ├── export_commands.rs         # 내보내기 커맨드
│   │   ├── cache_commands.rs          # 캐시 관리 커맨드
│   │   └── file_commands.rs           # 파일 작업 커맨드
│   │
│   ├── db/
│   │   ├── mod.rs
│   │   ├── models.rs                  # 데이터 모델
│   │   ├── schema.rs                  # 스키마 정의
│   │   ├── migrations/
│   │   │   ├── 001_initial_schema.sql
│   │   │   ├── 002_add_cache_table.sql
│   │   │   └── 003_add_indexes.sql
│   │   └── operations.rs              # DB 쿼리 함수들
│   │
│   ├── models/
│   │   ├── mod.rs
│   │   ├── address.rs
│   │   ├── result.rs
│   │   ├── job.rs
│   │   ├── cache.rs
│   │   └── settings.rs
│   │
│   ├── services/
│   │   ├── mod.rs
│   │   ├── crawler_service.rs         # 크롤러 관리
│   │   ├── sidecar_service.rs         # 사이드카 통신
│   │   ├── file_service.rs            # 파일 처리
│   │   ├── export_service.rs          # 내보내기 로직
│   │   └── cache_service.rs           # 캐시 관리
│   │
│   ├── events.rs                      # 이벤트 정의
│   ├── errors.rs                      # 에러 타입
│   └── state.rs                       # 앱 상태
│
├── Cargo.toml                         # Rust 의존성
├── tauri.conf.json                    # Tauri 설정
└── build.rs                           # 빌드 스크립트 (선택사항)
```

### 3.2 Tauri 설정 (tauri.conf.json)

```json
{
  "build": {
    "beforeBuildCommand": "bun run build",
    "beforeDevCommand": "bun run dev",
    "devUrl": "http://localhost:5173",
    "frontendDist": "../build"
  },
  "app": {
    "windows": [
      {
        "title": "EUM Crawler",
        "width": 1200,
        "height": 800,
        "minWidth": 800,
        "minHeight": 600,
        "resizable": true,
        "fullscreen": false,
        "focus": true,
        "label": "main"
      }
    ],
    "security": {
      "csp": null
    }
  },
  "bundle": {
    "active": true,
    "targets": ["msi", "nsis"],
    "identifier": "com.eumcrawl.desktop",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ]
  }
}
```

### 3.3 Cargo.toml 의존성

```toml
[package]
name = "eumcrawl-tauri"
version = "1.0.0"
edition = "2021"

[dependencies]
tauri = { version = "2", features = ["shell-open", "fs-all", "http-client"] }
tauri-plugin-shell = "1"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tokio = { version = "1", features = ["full"] }
rusqlite = { version = "0.31", features = ["bundled", "chrono"] }
chrono = { version = "0.4", features = ["serde"] }
anyhow = "1"
thiserror = "1"
uuid = { version = "1", features = ["v4", "serde"] }
base64 = "0.22"
reqwest = { version = "0.11", features = ["json"] }
image = "0.24"
openpyxl = "0.2"  # 또는 xlsx 크레이트

[target.'cfg(windows)'.dependencies]
windows = { version = "0.55", features = ["Win32_Foundation"] }
```

### 3.4 IPC 커맨드 정의

#### 3.4.1 Address Commands (commands/address_commands.rs)

```rust
use tauri::State;
use crate::models::Address;
use crate::db::operations::*;

#[tauri::command]
pub async fn get_addresses(state: State<'_, AppState>) -> Result<Vec<Address>> {
    let db = state.db.lock().unwrap();
    get_all_addresses(&db)
}

#[tauri::command]
pub async fn get_address(
    id: i32,
    state: State<'_, AppState>
) -> Result<Address> {
    let db = state.db.lock().unwrap();
    get_address_by_id(&db, id)
}

#[tauri::command]
pub async fn add_address(
    address: String,
    state: State<'_, AppState>
) -> Result<Address> {
    let db = state.db.lock().unwrap();
    insert_address(&db, &address)
}

#[tauri::command]
pub async fn delete_address(
    id: i32,
    state: State<'_, AppState>
) -> Result<()> {
    let db = state.db.lock().unwrap();
    delete_address_by_id(&db, id)
}

#[tauri::command]
pub async fn import_from_excel(
    file_path: String,
    state: State<'_, AppState>
) -> Result<Vec<Address>> {
    // Excel 파일 읽기 로직
    // addresses 추출
    // DB에 삽입
    // 반환
}
```

#### 3.4.2 Crawler Commands (commands/crawler_commands.rs)

```rust
#[tauri::command]
pub async fn start_crawl_job(
    config: CrawlConfig,
    state: State<'_, AppState>,
    window: tauri::Window
) -> Result<Job> {
    let mut crawler = state.crawler_service.lock().unwrap();

    // Job 생성 & DB 저장
    let job = create_job(&state.db, &config)?;

    // 사이드카 프로세스 시작
    crawler.start_sidecar(
        job.id,
        &job.addresses,
        window.clone()
    ).await?;

    Ok(job)
}

#[tauri::command]
pub async fn pause_job(
    job_id: i32,
    state: State<'_, AppState>
) -> Result<()> {
    let mut crawler = state.crawler_service.lock().unwrap();
    crawler.pause_job(job_id).await
}

#[tauri::command]
pub async fn resume_job(
    job_id: i32,
    state: State<'_, AppState>
) -> Result<()> {
    let mut crawler = state.crawler_service.lock().unwrap();
    crawler.resume_job(job_id).await
}

#[tauri::command]
pub async fn stop_job(
    job_id: i32,
    state: State<'_, AppState>
) -> Result<()> {
    let mut crawler = state.crawler_service.lock().unwrap();
    crawler.stop_job(job_id).await
}

#[tauri::command]
pub async fn get_job_status(
    job_id: i32,
    state: State<'_, AppState>
) -> Result<JobStatus> {
    let db = state.db.lock().unwrap();
    get_job_by_id(&db, job_id)
}
```

#### 3.4.3 Result Commands (commands/result_commands.rs)

```rust
#[tauri::command]
pub async fn get_results(
    filter: Option<ResultFilter>,
    state: State<'_, AppState>
) -> Result<Vec<Result>> {
    let db = state.db.lock().unwrap();

    match filter {
        None => get_all_results(&db),
        Some(f) => search_results(&db, &f)
    }
}

#[tauri::command]
pub async fn get_result_detail(
    result_id: i32,
    state: State<'_, AppState>
) -> Result<ResultDetail> {
    let db = state.db.lock().unwrap();

    let result = get_result_by_id(&db, result_id)?;
    let images = get_result_images(&db, result_id)?;
    let pdf_path = get_result_pdf(&db, result_id)?;

    Ok(ResultDetail {
        result,
        images,
        pdf_path
    })
}

#[tauri::command]
pub async fn search_results(
    query: String,
    filter: ResultFilter,
    state: State<'_, AppState>
) -> Result<Vec<Result>> {
    let db = state.db.lock().unwrap();
    search_results_with_query(&db, &query, &filter)
}

#[tauri::command]
pub async fn delete_result(
    result_id: i32,
    state: State<'_, AppState>
) -> Result<()> {
    let db = state.db.lock().unwrap();

    // 파일 정리
    cleanup_result_files(result_id)?;

    // DB에서 삭제
    delete_result_by_id(&db, result_id)
}
```

#### 3.4.4 Export Commands (commands/export_commands.rs)

```rust
#[tauri::command]
pub async fn export_to_excel(
    result_ids: Vec<i32>,
    output_path: String,
    state: State<'_, AppState>
) -> Result<String> {
    let db = state.db.lock().unwrap();
    let service = state.export_service.lock().unwrap();

    service.export_results_to_excel(&db, &result_ids, &output_path)
}

#[tauri::command]
pub async fn export_to_csv(
    result_ids: Vec<i32>,
    output_path: String,
    state: State<'_, AppState>
) -> Result<String> {
    let db = state.db.lock().unwrap();
    let service = state.export_service.lock().unwrap();

    service.export_results_to_csv(&db, &result_ids, &output_path)
}

#[tauri::command]
pub async fn export_to_pdf(
    result_id: i32,
    output_path: String,
    state: State<'_, AppState>
) -> Result<String> {
    let db = state.db.lock().unwrap();
    let service = state.export_service.lock().unwrap();

    service.generate_pdf(&db, result_id, &output_path)
}
```

### 3.5 이벤트 시스템

#### 3.5.1 이벤트 정의 (events.rs)

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct CrawlProgress {
    pub job_id: i32,
    pub total: i32,
    pub completed: i32,
    pub failed: i32,
    pub current_address: String,
    pub percentage: f64,
    pub status: String,
    pub message: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct CrawlLog {
    pub job_id: i32,
    pub timestamp: String,
    pub level: String,  // "info", "warn", "error"
    pub message: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct CrawlComplete {
    pub job_id: i32,
    pub total_addresses: i32,
    pub successful: i32,
    pub failed: i32,
    pub duration_seconds: i32,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct JobStatusChange {
    pub job_id: i32,
    pub status: String,  // "running", "paused", "stopped", "completed"
}
```

#### 3.5.2 이벤트 발행 (services/crawler_service.rs)

```rust
use tauri::Window;

pub struct CrawlerService {
    window: Window,
    current_job: Option<JobHandle>,
}

impl CrawlerService {
    pub async fn emit_progress(&self, progress: CrawlProgress) {
        let _ = self.window.emit("crawl://progress", &progress);
    }

    pub async fn emit_log(&self, log: CrawlLog) {
        let _ = self.window.emit("crawl://log", &log);
    }

    pub async fn emit_complete(&self, complete: CrawlComplete) {
        let _ = self.window.emit("crawl://complete", &complete);
    }
}
```

### 3.6 앱 상태 (state.rs)

```rust
use std::sync::Mutex;
use rusqlite::Connection;

pub struct AppState {
    pub db: Mutex<Connection>,
    pub crawler_service: Mutex<CrawlerService>,
    pub file_service: Mutex<FileService>,
    pub export_service: Mutex<ExportService>,
}

impl AppState {
    pub fn new(db_path: &str) -> Result<Self> {
        let db = Connection::open(db_path)?;

        // 마이그레이션 실행
        run_migrations(&db)?;

        Ok(AppState {
            db: Mutex::new(db),
            crawler_service: Mutex::new(CrawlerService::new()),
            file_service: Mutex::new(FileService::new()),
            export_service: Mutex::new(ExportService::new()),
        })
    }
}
```

### 3.7 Main.rs 설정

```rust
use tauri::Manager;
mod commands;
mod db;
mod models;
mod services;
mod events;
mod errors;
mod state;

use crate::commands::*;
use crate::state::AppState;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        // 앱 상태 초기화
        .setup(|app| {
            let app_dir = app.path_resolver()
                .app_config_dir()
                .expect("Failed to get app config dir");

            std::fs::create_dir_all(&app_dir)?;

            let db_path = app_dir.join("eumcrawl.db");
            let state = AppState::new(db_path.to_str().unwrap())?;

            app.manage(state);
            Ok(())
        })
        // IPC 커맨드 등록
        .invoke_handler(tauri::generate_handler![
            // Address Commands
            get_addresses,
            get_address,
            add_address,
            delete_address,
            import_from_excel,

            // Crawler Commands
            start_crawl_job,
            pause_job,
            resume_job,
            stop_job,
            get_job_status,

            // Result Commands
            get_results,
            get_result_detail,
            search_results,
            delete_result,

            // Export Commands
            export_to_excel,
            export_to_csv,
            export_to_pdf,

            // Settings Commands
            get_settings,
            update_setting,

            // Cache Commands
            check_cache,
            clear_cache,

            // File Commands
            open_file,
            open_folder,
        ])
        // 앱 실행
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

---

## 4. Crawler Sidecar 아키텍처 (Bun + Playwright)

### 4.1 사이드카 개요

Playwright 기반 크롤러는 독립적인 Bun 프로세스로 실행되며, Tauri 백엔드와 stdin/stdout을 통해 JSON 메시지로 통신합니다.

### 4.2 사이드카 디렉토리 구조

```
src-crawler/
├── index.ts                           # 진입점, 메시지 핸들러
├── scraper.ts                         # Playwright 스크래핑 로직
├── validator.ts                       # 주소 검증 (AJAX)
├── image-downloader.ts                # 이미지 다운로드
├── pdf-generator.ts                   # PDF 생성
├── types.ts                           # 공유 타입 정의
├── utils.ts                           # 유틸리티 함수
├── config.ts                          # 설정 상수
└── package.json
```

### 4.3 사이드카 메시지 프로토콜

#### 4.3.1 메시지 형식

```typescript
// Tauri → Sidecar
interface SidecarMessage {
  type: 'START_CRAWL' | 'PAUSE' | 'RESUME' | 'STOP' | 'PING';
  job_id: number;
  addresses?: string[];
  config?: CrawlerConfig;
}

// Sidecar → Tauri (via stdout)
interface SidecarResponse {
  type: 'PROGRESS' | 'RESULT' | 'ERROR' | 'COMPLETE' | 'LOG' | 'PONG';
  job_id: number;

  // PROGRESS
  progress?: {
    total: number;
    completed: number;
    failed: number;
    current_address: string;
    percentage: number;
  };

  // RESULT
  result?: {
    address: string;
    present_addr: string;
    present_class: string;
    present_area: string;
    jiga: string;
    image_path?: string;
    pdf_path?: string;
  };

  // ERROR
  error?: {
    address: string;
    message: string;
    code: string;
  };

  // COMPLETE
  complete?: {
    total: number;
    successful: number;
    failed: number;
    duration_seconds: number;
  };

  // LOG
  log?: {
    level: 'info' | 'warn' | 'error' | 'debug';
    message: string;
  };

  timestamp?: string;
}
```

### 4.4 사이드카 구현

#### 4.4.1 진입점 (index.ts)

```typescript
import * as readline from 'readline';
import { RealEstateScraper } from './scraper';
import { parseMessage, validateConfig } from './utils';
import type { SidecarMessage, SidecarResponse } from './types';

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

let scraper: RealEstateScraper | null = null;
let isRunning = false;
let isPaused = false;

function sendResponse(response: SidecarResponse) {
  console.log(JSON.stringify(response));
}

function log(level: string, message: string) {
  sendResponse({
    type: 'LOG',
    job_id: 0,
    log: {
      level: level as any,
      message
    },
    timestamp: new Date().toISOString()
  });
}

rl.on('line', async (line) => {
  try {
    const message = parseMessage(line) as SidecarMessage;

    switch (message.type) {
      case 'START_CRAWL':
        await handleStartCrawl(message);
        break;

      case 'PAUSE':
        isPaused = true;
        log('info', `Job ${message.job_id} paused`);
        break;

      case 'RESUME':
        isPaused = false;
        log('info', `Job ${message.job_id} resumed`);
        break;

      case 'STOP':
        await handleStopCrawl(message);
        break;

      case 'PING':
        sendResponse({
          type: 'PONG',
          job_id: message.job_id
        });
        break;
    }
  } catch (error) {
    sendResponse({
      type: 'ERROR',
      job_id: 0,
      error: {
        address: '',
        message: String(error),
        code: 'PARSE_ERROR'
      }
    });
  }
});

async function handleStartCrawl(message: SidecarMessage) {
  if (!message.addresses || !message.config) {
    throw new Error('Missing addresses or config');
  }

  if (!validateConfig(message.config)) {
    throw new Error('Invalid config');
  }

  isRunning = true;
  isPaused = false;

  try {
    scraper = new RealEstateScraper(message.config);

    const results = [];
    const total = message.addresses.length;

    for (let i = 0; i < message.addresses.length; i++) {
      if (!isRunning) break;

      // 일시정지 상태 체크
      while (isPaused && isRunning) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      const address = message.addresses[i];

      try {
        log('info', `Crawling address ${i + 1}/${total}: ${address}`);

        const result = await scraper.crawlAddress(address);

        // 진행률 전송
        sendResponse({
          type: 'PROGRESS',
          job_id: message.job_id,
          progress: {
            total,
            completed: i + 1,
            failed: 0,
            current_address: address,
            percentage: ((i + 1) / total) * 100
          }
        });

        // 결과 전송
        sendResponse({
          type: 'RESULT',
          job_id: message.job_id,
          result
        });

        results.push(result);
      } catch (error) {
        sendResponse({
          type: 'ERROR',
          job_id: message.job_id,
          error: {
            address,
            message: String(error),
            code: 'CRAWL_ERROR'
          }
        });
      }
    }

    // 완료
    sendResponse({
      type: 'COMPLETE',
      job_id: message.job_id,
      complete: {
        total,
        successful: results.length,
        failed: total - results.length,
        duration_seconds: Math.floor((Date.now() - Date.now()) / 1000)
      }
    });

  } catch (error) {
    sendResponse({
      type: 'ERROR',
      job_id: message.job_id,
      error: {
        address: '',
        message: String(error),
        code: 'SETUP_ERROR'
      }
    });
  } finally {
    if (scraper) {
      await scraper.close();
    }
    isRunning = false;
  }
}

async function handleStopCrawl(message: SidecarMessage) {
  isRunning = false;
  if (scraper) {
    await scraper.close();
  }
  log('info', `Job ${message.job_id} stopped`);
}
```

#### 4.4.2 Scraper 클래스 (scraper.ts)

```typescript
import { Browser, Page, chromium } from 'playwright';
import { ImageDownloader } from './image-downloader';
import { PDFGenerator } from './pdf-generator';
import type { CrawlerConfig, CrawlResult } from './types';

export class RealEstateScraper {
  private browser: Browser | null = null;
  private page: Page | null = null;
  private config: CrawlerConfig;
  private imageDownloader: ImageDownloader;
  private pdfGenerator: PDFGenerator;

  constructor(config: CrawlerConfig) {
    this.config = config;
    this.imageDownloader = new ImageDownloader();
    this.pdfGenerator = new PDFGenerator();
  }

  async init() {
    this.browser = await chromium.launch({
      headless: this.config.headless ?? true
    });

    this.page = await this.browser.newPage();
    await this.page.goto('https://www.eum.go.kr/', {
      waitUntil: 'networkidle'
    });
  }

  async crawlAddress(address: string): Promise<CrawlResult> {
    if (!this.page) {
      throw new Error('Scraper not initialized');
    }

    // 1. 주소 입력
    await this.page.fill('#recent > input', address);

    // 2. 검색 실행 (Enter 키)
    await this.page.press('#recent > input', 'Enter');

    // 3. 결과 로드 대기
    await this.page.waitForSelector('#present_addr', {
      timeout: this.config.timeout || 30000
    });

    // 4. 데이터 추출
    const result = await this.page.evaluate(() => ({
      present_addr: (document.querySelector('#present_addr') as HTMLElement)?.innerText || '',
      present_class: (document.querySelector('#present_class') as HTMLElement)?.innerText || '',
      present_area: (document.querySelector('#present_area') as HTMLElement)?.innerText || '',
      jiga: (document.querySelector('#jiga') as HTMLElement)?.innerText || '',
      present_mark1: (document.querySelector('#present_mark1') as HTMLElement)?.innerText || '',
      present_mark2: (document.querySelector('#present_mark2') as HTMLElement)?.innerText || '',
      present_mark3: (document.querySelector('#present_mark3') as HTMLElement)?.innerText || '',
    }));

    // 5. 이미지 다운로드
    let imagePath: string | undefined;
    try {
      imagePath = await this.downloadImage(address);
    } catch (err) {
      console.warn(`Failed to download image for ${address}:`, err);
    }

    // 6. PDF 생성
    let pdfPath: string | undefined;
    if (this.config.generatePdf) {
      try {
        pdfPath = await this.generatePdf(address);
      } catch (err) {
        console.warn(`Failed to generate PDF for ${address}:`, err);
      }
    }

    return {
      address,
      ...result,
      image_path: imagePath,
      pdf_path: pdfPath,
      crawled_at: new Date().toISOString()
    };
  }

  private async downloadImage(address: string): Promise<string> {
    if (!this.page) {
      throw new Error('Scraper not initialized');
    }

    // 이미지 요소 찾기
    const imageElement = await this.page.$('table img');
    if (!imageElement) {
      throw new Error('Image not found');
    }

    const imageUrl = await imageElement.evaluate((el: HTMLImageElement) => el.src);
    return await this.imageDownloader.download(imageUrl, address);
  }

  private async generatePdf(address: string): Promise<string> {
    if (!this.page) {
      throw new Error('Scraper not initialized');
    }

    return await this.pdfGenerator.generate(this.page, address);
  }

  async close() {
    if (this.page) {
      await this.page.close();
    }
    if (this.browser) {
      await this.browser.close();
    }
  }
}
```

#### 4.4.3 이미지 다운로더 (image-downloader.ts)

```typescript
import * as fs from 'fs/promises';
import * as path from 'path';
import fetch from 'node-fetch';
import sharp from 'sharp';

export class ImageDownloader {
  private tempDir = './temp_images';

  async init() {
    await fs.mkdir(this.tempDir, { recursive: true });
  }

  async download(imageUrl: string, address: string): Promise<string> {
    try {
      // 이미지 다운로드
      const response = await fetch(imageUrl);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const buffer = await response.buffer();

      // 임시 파일 저장
      const filename = `${address.replace(/[/\\]/g, '_')}_${Date.now()}.jpg`;
      const filepath = path.join(this.tempDir, filename);

      // 이미지 리사이징 (300px 너비)
      await sharp(buffer)
        .resize(300, null, { withoutEnlargement: true })
        .jpeg({ quality: 80 })
        .toFile(filepath);

      return filepath;
    } catch (err) {
      throw new Error(`Image download failed: ${err}`);
    }
  }

  async cleanup() {
    try {
      await fs.rm(this.tempDir, { recursive: true, force: true });
    } catch (err) {
      console.warn('Cleanup failed:', err);
    }
  }
}
```

#### 4.4.4 타입 정의 (types.ts)

```typescript
export interface CrawlerConfig {
  headless?: boolean;
  timeout?: number;
  waitTime?: number;
  retries?: number;
  generatePdf?: boolean;
  imageDir?: string;
}

export interface CrawlResult {
  address: string;
  present_addr: string;
  present_class: string;
  present_area: string;
  jiga: string;
  present_mark1?: string;
  present_mark2?: string;
  present_mark3?: string;
  image_path?: string;
  pdf_path?: string;
  crawled_at: string;
}

export interface SidecarMessage {
  type: string;
  job_id: number;
  addresses?: string[];
  config?: CrawlerConfig;
}

export interface SidecarResponse {
  type: string;
  job_id: number;
  progress?: any;
  result?: CrawlResult;
  error?: any;
  complete?: any;
  log?: any;
  timestamp?: string;
}
```

### 4.5 사이드카 Bun 설정 (package.json)

```json
{
  "name": "eumcrawl-crawler-sidecar",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "start": "bun src-crawler/index.ts",
    "dev": "bun --watch src-crawler/index.ts",
    "build": "bun build src-crawler/index.ts --outfile dist/sidecar.js"
  },
  "dependencies": {
    "playwright": "^1.40.0",
    "sharp": "^0.33.0",
    "node-fetch": "^3.3.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/node": "^20.0.0"
  }
}
```

---

## 5. 데이터베이스 아키텍처

### 5.1 SQLite 스키마

#### 5.1.1 초기 마이그레이션 (001_initial_schema.sql)

```sql
-- Addresses 테이블
CREATE TABLE addresses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  address TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Results 테이블
CREATE TABLE results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  address_id INTEGER NOT NULL,
  present_addr TEXT,
  present_class TEXT,
  present_area TEXT,
  jiga TEXT,
  present_mark1 TEXT,
  present_mark2 TEXT,
  present_mark3 TEXT,
  image_path TEXT,
  pdf_path TEXT,
  crawled_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (address_id) REFERENCES addresses(id) ON DELETE CASCADE
);

-- Jobs 테이블
CREATE TABLE jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  total_addresses INTEGER DEFAULT 0,
  successful_count INTEGER DEFAULT 0,
  failed_count INTEGER DEFAULT 0,
  started_at DATETIME,
  completed_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Job_Addresses 연결 테이블
CREATE TABLE job_addresses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL,
  address_id INTEGER NOT NULL,
  status TEXT DEFAULT 'pending',
  result_id INTEGER,
  error_message TEXT,
  FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
  FOREIGN KEY (address_id) REFERENCES addresses(id),
  FOREIGN KEY (result_id) REFERENCES results(id)
);

-- Settings 테이블
CREATE TABLE settings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  key TEXT UNIQUE NOT NULL,
  value TEXT,
  type TEXT DEFAULT 'string',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Cache 테이블
CREATE TABLE cache (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  address TEXT UNIQUE NOT NULL,
  result_data JSON,
  expires_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_addresses_address ON addresses(address);
CREATE INDEX idx_results_address_id ON results(address_id);
CREATE INDEX idx_results_crawled_at ON results(crawled_at);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_job_addresses_job_id ON job_addresses(job_id);
CREATE INDEX idx_cache_address ON cache(address);
CREATE INDEX idx_cache_expires_at ON cache(expires_at);
```

#### 5.1.2 캐시 테이블 마이그레이션 (002_add_cache_table.sql)

```sql
-- 이미 위의 001 마이그레이션에 포함됨
-- 필요시 선택적 추가 필드를 위한 ALTER TABLE 가능
ALTER TABLE results ADD COLUMN cached_at DATETIME;
```

### 5.2 데이터 모델

#### 5.2.1 Address 모델 (models/address.rs)

```rust
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Address {
    pub id: i32,
    pub address: String,
    pub result_id: Option<i32>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct NewAddress {
    pub address: String,
}
```

#### 5.2.2 Result 모델 (models/result.rs)

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Result {
    pub id: i32,
    pub address_id: i32,
    pub present_addr: Option<String>,
    pub present_class: Option<String>,
    pub present_area: Option<String>,
    pub jiga: Option<String>,
    pub present_mark1: Option<String>,
    pub present_mark2: Option<String>,
    pub present_mark3: Option<String>,
    pub image_path: Option<String>,
    pub pdf_path: Option<String>,
    pub crawled_at: Option<DateTime<Utc>>,
}
```

#### 5.2.3 Job 모델 (models/job.rs)

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Job {
    pub id: i32,
    pub name: String,
    pub status: JobStatus,
    pub total_addresses: i32,
    pub successful_count: i32,
    pub failed_count: i32,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum JobStatus {
    Pending,
    Running,
    Paused,
    Completed,
    Failed,
    Stopped,
}
```

### 5.3 DB 작업 함수 (db/operations.rs)

```rust
use rusqlite::{Connection, Result as SqlResult, params};
use crate::models::*;

pub fn get_all_addresses(db: &Connection) -> SqlResult<Vec<Address>> {
    let mut stmt = db.prepare(
        "SELECT id, address, created_at, updated_at FROM addresses ORDER BY id DESC"
    )?;

    let addresses = stmt.query_map([], |row| {
        Ok(Address {
            id: row.get(0)?,
            address: row.get(1)?,
            result_id: None,
            created_at: row.get(2)?,
            updated_at: row.get(3)?,
        })
    })?
        .collect::<SqlResult<Vec<_>>>()?;

    Ok(addresses)
}

pub fn insert_address(db: &Connection, address: &str) -> SqlResult<Address> {
    let now = chrono::Utc::now();

    db.execute(
        "INSERT INTO addresses (address, created_at, updated_at) VALUES (?1, ?2, ?3)",
        params![address, now, now],
    )?;

    let id = db.last_insert_rowid() as i32;

    Ok(Address {
        id,
        address: address.to_string(),
        result_id: None,
        created_at: now,
        updated_at: now,
    })
}

pub fn delete_address_by_id(db: &Connection, id: i32) -> SqlResult<()> {
    db.execute("DELETE FROM addresses WHERE id = ?1", params![id])?;
    Ok(())
}

pub fn save_result(db: &Connection, address_id: i32, result: &CrawlResult) -> SqlResult<i32> {
    let now = chrono::Utc::now();

    db.execute(
        "INSERT INTO results (
            address_id, present_addr, present_class, present_area, jiga,
            present_mark1, present_mark2, present_mark3, image_path, pdf_path,
            crawled_at, created_at
        ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12)",
        params![
            address_id,
            &result.present_addr,
            &result.present_class,
            &result.present_area,
            &result.jiga,
            &result.present_mark1,
            &result.present_mark2,
            &result.present_mark3,
            &result.image_path,
            &result.pdf_path,
            &result.crawled_at,
            now
        ],
    )?;

    Ok(db.last_insert_rowid() as i32)
}
```

---

## 6. 통신 프로토콜

### 6.1 Frontend ↔ Tauri Rust (IPC)

#### 6.1.1 커맨드 호출 (Frontend에서 Rust로)

```typescript
import { invoke } from '@tauri-apps/api/core';

// 주소 가져오기
const addresses = await invoke('get_addresses');

// 크롤링 작업 시작
const job = await invoke('start_crawl_job', {
  config: {
    addresses: [1, 2, 3],
    headless: true,
    timeout: 30000
  }
});

// 작업 일시정지
await invoke('pause_job', { job_id: 1 });

// 결과 내보내기
const path = await invoke('export_to_excel', {
  result_ids: [1, 2, 3],
  output_path: '/path/to/file.xlsx'
});
```

#### 6.1.2 이벤트 수신 (Rust에서 Frontend로)

```typescript
import { listen } from '@tauri-apps/api/core';

// 크롤링 진행률 수신
const unlistenProgress = await listen('crawl://progress', (event) => {
  console.log('Progress:', event.payload);
  // { total: 100, completed: 25, ... }
});

// 크롤링 로그 수신
const unlistenLog = await listen('crawl://log', (event) => {
  console.log('Log:', event.payload);
  // { level: 'info', message: '...' }
});

// 크롤링 완료
const unlistenComplete = await listen('crawl://complete', (event) => {
  console.log('Complete:', event.payload);
  // { successful: 99, failed: 1, ... }
});

// 정리
unlistenProgress();
unlistenLog();
unlistenComplete();
```

### 6.2 Tauri Rust ↔ Crawler Sidecar (stdin/stdout JSON)

#### 6.2.1 Sidecar 통신 서비스 (services/sidecar_service.rs)

```rust
use tauri::{Command, Window};
use std::process::{Command as ProcessCommand, Stdio};
use std::io::{BufReader, BufRead, Write};

pub struct SidecarCommunicator {
    window: Window,
}

impl SidecarCommunicator {
    pub async fn start_crawl(
        &self,
        job_id: i32,
        addresses: Vec<String>,
        config: CrawlerConfig
    ) -> Result<()> {
        let mut child = ProcessCommand::new("bun")
            .arg("src-crawler/index.ts")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .spawn()?;

        // stdin으로 메시지 전송
        let message = serde_json::json!({
            "type": "START_CRAWL",
            "job_id": job_id,
            "addresses": addresses,
            "config": config
        });

        if let Some(mut stdin) = child.stdin.take() {
            stdin.write_all(message.to_string().as_bytes())?;
            stdin.write_all(b"\n")?;
        }

        // stdout에서 메시지 수신
        if let Some(stdout) = child.stdout.take() {
            let reader = BufReader::new(stdout);

            for line in reader.lines() {
                if let Ok(line) = line {
                    if let Ok(response) = serde_json::from_str::<SidecarResponse>(&line) {
                        self.handle_response(response).await;
                    }
                }
            }
        }

        Ok(())
    }

    async fn handle_response(&self, response: SidecarResponse) {
        match response.typ.as_str() {
            "PROGRESS" => {
                let _ = self.window.emit("crawl://progress", &response.progress);
            }
            "RESULT" => {
                let _ = self.window.emit("crawl://result", &response.result);
            }
            "LOG" => {
                let _ = self.window.emit("crawl://log", &response.log);
            }
            "COMPLETE" => {
                let _ = self.window.emit("crawl://complete", &response.complete);
            }
            "ERROR" => {
                let _ = self.window.emit("crawl://error", &response.error);
            }
            _ => {}
        }
    }
}
```

### 6.3 에러 처리 프로토콜

#### 6.3.1 에러 타입 정의 (errors.rs)

```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum AppError {
    #[error("Database error: {0}")]
    DatabaseError(String),

    #[error("Crawler error: {0}")]
    CrawlerError(String),

    #[error("File error: {0}")]
    FileError(#[from] std::io::Error),

    #[error("Invalid input: {0}")]
    ValidationError(String),

    #[error("Export error: {0}")]
    ExportError(String),
}

impl serde::Serialize for AppError {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        serializer.serialize_str(&self.to_string())
    }
}
```

#### 6.3.2 Result 타입

```rust
pub type Result<T> = std::result::Result<T, AppError>;
```

---

## 7. 데이터 흐름 다이어그램

### 7.1 주소 가져오기 흐름

```
User clicks "Import Excel"
    ↓
AddressImportModal.svelte
    ↓
invoke('import_from_excel', { filePath })
    ↓
Tauri: import_from_excel command
    ↓
Read Excel file
    ↓
Extract addresses
    ↓
For each address:
  └→ INSERT INTO addresses
    ↓
Return: Vec<Address>
    ↓
Frontend: addressStore.addresses = [...]
    ↓
$derived updates all connected components
    ↓
AddressList.svelte re-renders
    ↓
User sees addresses in table
```

### 7.2 크롤링 작업 실행 흐름

```
User clicks "Start Crawl"
    ↓
JobMonitor component
    ↓
invoke('start_crawl_job', { config })
    ↓
Tauri: start_crawl_job command
    ├→ CREATE Job record in DB
    ├→ Spawn sidecar process (bun)
    └→ Start listening to sidecar output
        ↓
Sidecar: Playwright browser opens
    ↓
For each address:
    ├→ Navigate to eum.go.kr
    ├→ Search address
    ├→ Extract data
    ├→ Download image
    ├→ Send PROGRESS to stdout
    │   ↓
    │   Tauri receives and emits 'crawl://progress'
    │   ↓
    │   Frontend listens and updates jobStore.progress
    │   ↓
    │   JobMonitor.svelte re-renders (real-time progress)
    │
    └→ Send RESULT to stdout
        ↓
        Tauri receives and saves to DB
        ↓
        Frontend refreshes results
    ↓
All addresses processed
    ↓
Send COMPLETE
    ↓
Sidecar closes
    ↓
Tauri updates Job status to 'completed'
    ↓
Frontend emits 'crawl://complete'
    ↓
ResultTable.svelte loads new results
    ↓
User sees complete results
```

### 7.3 캐시 확인 흐름

```
Before crawling address:
    ↓
invoke('check_cache', { address })
    ↓
Tauri: SELECT FROM cache WHERE address = ? AND expires_at > NOW()
    ↓
Found?
├→ Yes: Return cached result
│   ↓
│   Skip sidecar crawl
│   ↓
│   Emit result directly from DB
│
└→ No: Continue with crawl
    ↓
Sidecar crawls
    ↓
INSERT INTO cache (address, result_data, expires_at)
```

### 7.4 내보내기 흐름

```
User clicks "Export to Excel"
    ↓
ResultExportDialog.svelte
    ↓
invoke('export_to_excel', { result_ids, output_path })
    ↓
Tauri: export_to_excel command
    ├→ Query DB for results
    ├→ Create Excel workbook
    ├→ For each result:
    │   ├→ Write data to row
    │   └→ Insert image from disk
    ├→ Save file
    └→ Return file path
        ↓
Frontend receives path
    ↓
Invoke 'open_file' to open in user's Excel
    ↓
User sees data in Excel
```

---

## 8. 설정 및 관리

### 8.1 애플리케이션 설정 (Settings Store)

```typescript
// stores/settings.ts
interface Settings {
  // Crawler settings
  crawlerTimeout: number;              // ms
  crawlerRetries: number;
  crawlerHeadless: boolean;
  crawlerCacheExpiry: number;          // hours
  crawlerGeneratePdf: boolean;
  crawlerImageWidth: number;           // pixels

  // UI settings
  theme: 'light' | 'dark';
  language: 'ko' | 'en';
  fontSize: number;

  // Export settings
  defaultExportPath: string;
  exportFormat: 'excel' | 'csv' | 'pdf';

  // Advanced settings
  enableLogging: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  maxCacheSize: number;                // MB
}
```

### 8.2 데이터베이스 초기화 및 마이그레이션

```rust
pub fn run_migrations(db: &Connection) -> Result<()> {
    // 001_initial_schema.sql 실행
    db.execute_batch(include_str!("migrations/001_initial_schema.sql"))?;

    // 002_add_cache_table.sql 실행
    db.execute_batch(include_str!("migrations/002_add_cache_table.sql"))?;

    // 003_add_indexes.sql 실행
    db.execute_batch(include_str!("migrations/003_add_indexes.sql"))?;

    Ok(())
}
```

---

## 9. 빌드 및 배포

### 9.1 개발 모드 실행

```bash
# 프로젝트 루트에서:
cd eumcrawl-desktop

# 의존성 설치
bun install

# 개발 서버 + Tauri 시작
bun run tauri dev
```

### 9.2 프로덕션 빌드

```bash
# Svelte 빌드 + Tauri 빌드
bun run tauri build

# 출력: src-tauri/target/release/bundle/
#   └── msi/
#   │   └── eumcrawl-desktop_1.0.0_x64_en-US.msi
#   └── nsis/
#       └── eumcrawl-desktop_1.0.0_x64-setup.exe
```

### 9.3 배포 체크리스트

- [ ] 모든 테스트 통과 (`bun run test`)
- [ ] 빌드 성공 (`bun run tauri build`)
- [ ] 설치 프로그램 테스트
- [ ] Playwright 브라우저 번들 확인 (~200MB)
- [ ] 버전 번호 업데이트 (package.json, tauri.conf.json, CHANGELOG.md)
- [ ] GitHub Releases에 업로드
- [ ] 사용자 공지

### 9.4 Playwright 브라우저 번들

```javascript
// vite.config.ts에서 playwright를 외부 번들로 처리할 수도 있지만,
// 일반적으로는 Playwright가 자동으로 필요한 브라우저를 다운로드하도록 함.

// package.json에서:
{
  "scripts": {
    "postinstall": "playwright install chromium"
  }
}
```

---

## 10. 오류 처리 전략

### 10.1 Frontend 오류 처리

```svelte
<script lang="ts">
  import { getAddressesStore } from '$lib/stores/addresses';
  import Toast from '$lib/components/ui/Toast.svelte';

  const { error, loadAddresses } = getAddressesStore();

  $effect(() => {
    if (error) {
      // 에러 토스트 표시
      showToast({
        type: 'error',
        message: error,
        duration: 5000
      });
    }
  });
</script>

<div>
  {#if error}
    <Toast type="error" message={error} />
  {/if}
</div>
```

### 10.2 Tauri 오류 처리

```rust
#[tauri::command]
pub async fn start_crawl_job(
    config: CrawlConfig,
    state: State<'_, AppState>
) -> Result<Job, String> {
    match create_and_start_job(&state, config).await {
        Ok(job) => Ok(job),
        Err(err) => {
            eprintln!("Crawler error: {}", err);
            Err(err.to_string())
        }
    }
}
```

### 10.3 Sidecar 오류 복구

```typescript
// 사이드카 프로세스 충돌 시 자동 재시작
class CrawlerService {
  async startCrawl(jobId: number) {
    let retries = 3;

    while (retries > 0) {
      try {
        await this.launchSidecar(jobId);
        break;
      } catch (err) {
        retries--;
        if (retries > 0) {
          await sleep(2000);  // 2초 대기 후 재시도
        } else {
          throw new Error(`Failed to start crawler after 3 attempts: ${err}`);
        }
      }
    }
  }
}
```

---

## 11. 성능 최적화

### 11.1 프론트엔드 최적화

- **코드 분할**: SvelteKit 자동 코드 분할 (라우트별)
- **이미지 최적화**: WebP 포맷, lazy loading
- **상태 최적화**: Svelte 5 runes는 자동으로 가장 최소 범위로 업데이트
- **가상 스크롤**: 큰 주소/결과 목록에 virtual-scroll 라이브러리 사용

### 11.2 백엔드 최적화

- **인덱스**: addresses, results, jobs, cache 테이블에 인덱스
- **배치 작업**: 여러 주소 한번에 처리 시 배치 INSERT
- **연결 풀**: SQLite는 단일 연결, Mutex로 동시 접근 제어
- **캐싱**: 최근 크롤링 결과 1시간 캐시

### 11.3 사이드카 최적화

- **브라우저 재사용**: 단일 브라우저 인스턴스에서 여러 페이지
- **병렬 처리**: 여러 페이지 동시에 로드 (Playwright workers)
- **메모리 관리**: 각 페이지 처리 후 정리

---

## 12. 테스트 전략

### 12.1 유닛 테스트 (Rust)

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_insert_address() {
        let db = Connection::open_in_memory().unwrap();
        run_migrations(&db).unwrap();

        let addr = insert_address(&db, "서울시 강남구").unwrap();
        assert_eq!(addr.address, "서울시 강남구");
    }
}
```

### 12.2 통합 테스트 (Svelte)

```typescript
import { render, screen } from '@testing-library/svelte';
import AddressInput from '$lib/components/address/AddressInput.svelte';

test('주소 입력 컴포넌트 렌더링', () => {
  render(AddressInput);
  const input = screen.getByPlaceholderText('주소 입력');
  expect(input).toBeInTheDocument();
});
```

### 12.3 E2E 테스트 (Playwright)

```typescript
import { test, expect } from '@playwright/test';

test('주소 추가 및 크롤링', async ({ page }) => {
  await page.goto('http://localhost:5173');

  // 주소 입력
  await page.fill('input[placeholder="주소 입력"]', '서울시 강남구 테헤란로 123');
  await page.click('button:has-text("추가")');

  // 크롤링 시작
  await page.click('button:has-text("크롤링 시작")');

  // 진행률 확인
  await expect(page.locator('.progress-bar')).toBeVisible();

  // 완료 대기
  await page.waitForTimeout(30000);

  // 결과 확인
  await expect(page.locator('table tbody tr')).toHaveCount(1);
});
```

---

## 13. 배포 후 운영

### 13.1 사용자 가이드 제공

- README.md: 설치, 기본 사용법
- 온라인 문서: https://eumcrawl-docs.example.com
- 비디오 튜토리얼: YouTube 링크

### 13.2 피드백 수집

- 인앱 피드백 버튼 (Settings → Feedback)
- GitHub Issues
- 사용자 포럼

### 13.3 모니터링 및 로깅

```rust
// 자동 로깅 설정
pub fn setup_logging() {
    let log_path = get_app_log_dir().join("eumcrawl.log");

    // 최근 7일 로그 유지
    // 로그 레벨: INFO (기본), DEBUG (개발)
}
```

### 13.4 자동 업데이트

```rust
// tauri-plugin-updater 사용
pub async fn check_updates(window: Window) {
    if let Ok(update) = tauri::updater::builder(window)
        .check()
        .await
    {
        if update.is_update_available() {
            update.download_and_install().await.ok();
        }
    }
}
```

---

## 부록 A: 의존성 버전 명시

### A.1 프론트엔드 (package.json)

```json
{
  "dependencies": {
    "svelte": "^5.0.0",
    "@sveltejs/kit": "^2.0.0",
    "@tauri-apps/api": "^2.0.0",
    "tailwindcss": "^3.3.0",
    "daisyui": "^3.9.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "typescript": "^5.3.0",
    "@sveltejs/vite-plugin-svelte": "^3.0.0"
  }
}
```

### A.2 백엔드 (Cargo.toml)

```toml
[dependencies]
tauri = "2.0"
serde = "1.0"
serde_json = "1.0"
tokio = "1.0"
rusqlite = "0.31"
chrono = "0.4"
anyhow = "1.0"
uuid = "1.0"
```

### A.3 사이드카 (src-crawler/package.json)

```json
{
  "dependencies": {
    "playwright": "^1.40.0",
    "sharp": "^0.33.0"
  }
}
```

---

## 부록 B: 파일 레이아웃 체크리스트

```
eumcrawl-desktop/
├── src/                           # Svelte 프론트엔드
│   ├── lib/components/            # ✓ 컴포넌트
│   ├── lib/stores/                # ✓ 상태관리
│   ├── lib/services/              # ✓ IPC 래퍼
│   ├── lib/types/                 # ✓ TypeScript 타입
│   ├── routes/                    # ✓ SvelteKit 페이지
│   └── app.html                   # ✓ HTML 진입점
│
├── src-tauri/                     # Rust 백엔드
│   ├── src/
│   │   ├── commands/              # ✓ IPC 커맨드
│   │   ├── db/                    # ✓ DB 작업
│   │   ├── models/                # ✓ 데이터 모델
│   │   ├── services/              # ✓ 비즈니스 로직
│   │   ├── main.rs                # ✓ 진입점
│   │   └── events.rs              # ✓ 이벤트
│   ├── tauri.conf.json            # ✓ Tauri 설정
│   └── Cargo.toml                 # ✓ Rust 의존성
│
├── src-crawler/                   # Bun 사이드카
│   ├── index.ts                   # ✓ 진입점
│   ├── scraper.ts                 # ✓ 스크래핑
│   ├── types.ts                   # ✓ 타입
│   └── package.json               # ✓ 의존성
│
├── package.json                   # ✓ 프로젝트 루트 설정
├── svelte.config.js               # ✓ Svelte 설정
├── vite.config.ts                 # ✓ Vite 설정
├── tailwind.config.ts             # ✓ Tailwind 설정
├── tsconfig.json                  # ✓ TypeScript 설정
└── docs/design/                   # ✓ 설계 문서
    └── 02-ARCHITECTURE.md         # ✓ 이 문서
```

---

## 부록 C: 마이그레이션 체크리스트 (Python → Svelte/Tauri)

### C.1 기능 매핑

| Python 기능 | 새로운 위치 | 상태 |
|-----------|-----------|------|
| crawler.py | src-crawler/index.ts | 구현 예정 |
| scraper.py | src-crawler/scraper.ts | 구현 예정 |
| excel_handler.py | src-tauri/src/services/export_service.rs | 구현 예정 |
| config.py | svelte.config.js + Rust settings | 구현 예정 |
| GUI (Tkinter) | Svelte 5 + SvelteKit | 구현 예정 |

### C.2 테스트 계획

- [ ] 각 Rust 커맨드 유닛 테스트
- [ ] 각 Svelte 컴포넌트 렌더링 테스트
- [ ] Sidecar 메시지 프로토콜 테스트
- [ ] 전체 크롤링 흐름 E2E 테스트
- [ ] 내보내기 기능 테스트 (Excel, CSV, PDF)
- [ ] 캐시 메커니즘 테스트

### C.3 마이그레이션 일정 (제안)

1. **Phase 1 (1주)**: 프로젝트 구조 & 환경 설정
   - [ ] Tauri 프로젝트 초기화
   - [ ] SvelteKit 프로젝트 설정
   - [ ] 데이터베이스 스키마 생성

2. **Phase 2 (2주)**: 백엔드 핵심 기능
   - [ ] 주소 관리 커맨드 구현
   - [ ] 작업 관리 커맨드 구현
   - [ ] 결과 저장 로직 구현

3. **Phase 3 (2주)**: 사이드카 크롤러
   - [ ] Playwright 스크래핑 로직 포팅
   - [ ] 메시지 프로토콜 구현
   - [ ] 실시간 진행률 전송

4. **Phase 4 (1.5주)**: 프론트엔드 UI
   - [ ] 기본 레이아웃 & 네비게이션
   - [ ] 주소 입력 & 관리 페이지
   - [ ] 작업 모니터 & 실시간 진행률

5. **Phase 5 (1주)**: 내보내기 & 설정
   - [ ] Excel/CSV/PDF 내보내기
   - [ ] 설정 페이지
   - [ ] 캐시 관리

6. **Phase 6 (1주)**: 테스트 & 최적화
   - [ ] E2E 테스트
   - [ ] 성능 최적화
   - [ ] 빌드 & 패키징

---

## 결론

이 아키텍처 설계 문서는 eumcrawl-desktop의 모든 계층을 상세히 정의합니다. 개발자는 이 문서를 기반으로 다음 작업을 진행할 수 있습니다:

1. **프로젝트 초기화**: Tauri + SvelteKit 프로젝트 설정
2. **API 정의**: IPC 커맨드 및 이벤트 계약 확정
3. **데이터베이스**: SQLite 스키마 생성 및 마이그레이션
4. **기능 구현**: 백엔드 커맨드, 프론트엔드 UI 개발
5. **테스트**: 각 계층별 테스트 작성
6. **배포**: 빌드 및 릴리스 프로세스 실행

각 섹션은 충분한 구현 세부사항과 예제 코드를 포함하여, 경험 있는 개발자라면 이 문서만으로 전체 시스템을 구축할 수 있도록 설계되었습니다.

---

**문서 정보**
- 작성일: 2025-03-10
- 버전: 1.0
- 대상 독자: 풀스택 개발자, 시스템 아키텍트
- 참조: ../CLAUDE.md, ../docs/*.md
