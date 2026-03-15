# API/IPC 인터페이스 설계 문서

**프로젝트명**: eumCrawler v2.0 (부동산공시가격 크롤러)
**작성일**: 2026-03-10
**버전**: 1.0.0
**상태**: 최종 검토 대기

---

## 목차

1. [개요](#개요)
2. [Part 1: Tauri IPC 커맨드](#part-1-tauri-ipc-커맨드)
3. [Part 2: Tauri 실시간 이벤트](#part-2-tauri-실시간-이벤트)
4. [Part 3: 크롤러 사이드카 프로토콜](#part-3-크롤러-사이드카-프로토콜)
5. [Part 4: TypeScript 타입 정의](#part-4-typescript-타입-정의)
6. [Part 5: 프론트엔드 서비스 레이어](#part-5-프론트엔드-서비스-레이어)
7. [Part 6: 에러 처리 계약](#part-6-에러-처리-계약)
8. [Part 7: 시퀀스 다이어그램](#part-7-시퀀스-다이어그램)

---

## 개요

### 아키텍처 개요

```
┌─────────────────────────┐
│  Svelte 5 Frontend      │
│  (TypeScript)           │
└────────┬────────────────┘
         │
         │ IPC Commands & Events
         │
┌────────▼────────────────┐
│  Tauri v2 Backend       │
│  (Rust)                 │
├────────────────────────┤
│ - Command Handlers      │
│ - Event Emitter         │
│ - DB Operations         │
└────────┬────────────────┘
         │
    ┌────┴─────────────────┬──────────────────┐
    │                      │                  │
┌───▼──────────┐  ┌────────▼───┐  ┌─────────▼──────┐
│ SQLite DB    │  │Crawler Side │  │ File System    │
│ (로컬)       │  │ car (Bun)   │  │ (Images/PDFs)  │
└──────────────┘  │ Playwright  │  └────────────────┘
                  └─────┬───────┘
                        │
                        │ stdin/stdout JSON
                        │
                  ┌─────▼───────────┐
                  │ eum.go.kr       │
                  │ (웹사이트)      │
                  └─────────────────┘
```

### 통신 계층

| 계층 | 방향 | 프로토콜 | 담당 |
|-----|------|---------|------|
| Frontend ↔ Tauri | 양방향 | IPC (invoke/listen) | Tauri Framework |
| Tauri ↔ Sidecar | 양방향 | stdin/stdout JSON | 구현 필요 |
| Tauri ↔ Database | 편방향 | SQL (rusqlite) | Rust 백엔드 |

---

# Part 1: Tauri IPC 커맨드

Tauri 커맨드는 프론트엔드에서 백엔드로 호출하는 RPC 메서드입니다. 모든 커맨드는 `async` 함수이며, 결과 또는 에러를 반환합니다.

## 1.1 주소 관리 커맨드

### get_addresses
주소 목록을 조회합니다. 페이지네이션, 필터링, 정렬을 지원합니다.

**호출**
```typescript
invoke<PaginatedResult<Address>>('get_addresses', {
  page: 1,
  per_page: 50,
  search?: 'keyword',
  group?: 'group_name',
  sort_by?: 'created_at',
  sort_order?: 'desc'
})
```

**매개변수**
- `page`: number - 페이지 번호 (1부터 시작)
- `per_page`: number - 페이지당 항목 수 (기본: 50)
- `search?`: string - 검색어 (주소명 부분일치)
- `group?`: string - 그룹명 필터
- `sort_by?`: string - 정렬 기준 ('created_at', 'address', 'updated_at')
- `sort_order?`: string - 정렬 순서 ('asc' | 'desc', 기본: 'desc')

**반환값**
```typescript
interface PaginatedResult<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

interface Address {
  id: number;
  address: string;
  normalized_address: string | null;
  pnu: string | null;
  group_name: string | null;
  tags: string[];
  memo: string | null;
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}
```

**에러**
- `400`: 유효하지 않은 페이지 번호
- `404`: 주소 없음
- `500`: 데이터베이스 오류

**SQL 참조**
```sql
SELECT * FROM addresses
WHERE (address LIKE '%' || ?1 || '%' OR normalized_address LIKE '%' || ?1 || '%')
  AND (group_name = ?2 OR ?2 IS NULL)
ORDER BY ?3 ?4
LIMIT ?5 OFFSET (?6 - 1) * ?5;
```

---

### add_address
새로운 주소를 추가합니다. 중복 주소는 거부됩니다.

**호출**
```typescript
invoke<Address>('add_address', {
  address: '서울시 강남구 역삼동 123-45',
  group_name?: '2024-03-강남구-조사',
  tags?: ['강남구', '주택'],
  memo?: '신축 건물'
})
```

**매개변수**
- `address`: string - 주소 (필수, UNIQUE)
- `group_name?`: string - 그룹명
- `tags?`: string[] - 태그 배열 (최대 5개)
- `memo?`: string - 메모

**반환값**
```typescript
interface Address {
  id: number;
  address: string;
  normalized_address: string | null;
  pnu: string | null;
  group_name: string | null;
  tags: string[];
  memo: string | null;
  created_at: string;
  updated_at: string;
}
```

**에러**
- `400`: 빈 주소, 이미 존재하는 주소
- `409`: 중복 주소
- `500`: 데이터베이스 오류

**SQL 참조**
```sql
INSERT INTO addresses (address, normalized_address, group_name, tags, memo, created_at, updated_at)
VALUES (?1, ?2, ?3, json(?4), ?5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
```

---

### update_address
기존 주소의 정보를 수정합니다.

**호출**
```typescript
invoke<Address>('update_address', {
  id: 1,
  address?: '서울시 강남구 역삼동 123-46',
  group_name?: '2024-03-강남구-조사',
  tags?: ['강남구', '상업용'],
  memo?: '수정됨'
})
```

**매개변수**
- `id`: number - 주소 ID (필수)
- `address?`: string - 새 주소
- `group_name?`: string - 새 그룹명
- `tags?`: string[] - 새 태그 배열
- `memo?`: string - 새 메모

**반환값**
```typescript
interface Address { /* 위와 동일 */ }
```

**에러**
- `400`: 필수 필드 누락
- `404`: 주소 없음
- `409`: 중복 주소
- `500`: 데이터베이스 오류

---

### delete_addresses
하나 이상의 주소를 삭제합니다. 관련 크롤링 결과도 함께 삭제될 수 있습니다.

**호출**
```typescript
invoke<{ deleted: number }>('delete_addresses', {
  ids: [1, 2, 3],
  delete_results?: false
})
```

**매개변수**
- `ids`: number[] - 삭제할 주소 ID 배열
- `delete_results?`: boolean - 관련 결과도 삭제할지 여부 (기본: false)

**반환값**
```typescript
interface DeleteResult {
  deleted: number; // 삭제된 주소 수
}
```

**에러**
- `400`: 빈 ID 배열
- `404`: 주소 없음
- `500`: 데이터베이스 오류

---

### import_addresses_from_excel
Excel 파일에서 주소를 일괄 가져옵니다.

**호출**
```typescript
invoke<ImportResult>('import_addresses_from_excel', {
  file_path: '/path/to/file.xlsx',
  start_row: 2,
  address_column: 'B',
  group_name?: '2024-03-강남구',
  duplicate_strategy: 'skip' // 'skip' | 'overwrite'
})
```

**매개변수**
- `file_path`: string - Excel 파일 경로 (필수)
- `start_row`: number - 시작 행 (헤더 제외, 기본: 2)
- `address_column`: string - 주소 컬럼 (기본: 'B')
- `group_name?`: string - 일괄 그룹명
- `duplicate_strategy`: string - 중복 처리 ('skip' | 'overwrite', 기본: 'skip')

**반환값**
```typescript
interface ImportResult {
  success: boolean;
  total_read: number; // 읽은 행 수
  imported: number; // 새로 추가된 주소 수
  skipped: number; // 중복으로 건너뛴 수
  errors: string[]; // 오류 메시지 배열
  message: string; // 사용자용 메시지
}
```

**에러**
- `400`: 파일 경로 없음
- `404`: 파일 없음
- `422`: 유효하지 않은 Excel 파일
- `500`: 파일 읽기 오류

---

### get_address_groups
모든 주소 그룹을 조회합니다.

**호출**
```typescript
invoke<string[]>('get_address_groups')
```

**반환값**
```typescript
string[] // ['2024-03-강남구', '2024-03-서초구', ...]
```

---

## 1.2 크롤링 작업 커맨드

### create_crawl_job
새로운 크롤링 작업을 생성합니다.

**호출**
```typescript
invoke<CrawlJob>('create_crawl_job', {
  name: '2024-03-강남구-001',
  address_ids: [1, 2, 3, 4, 5],
  scale: '1200',
  save_pdf: true,
  use_cache: true,
  cache_expiry_days: 30,
  headless: true,
  wait_time: 5,
  auto_start: true
})
```

**매개변수**
- `name`: string - 작업명 (필수)
- `address_ids`: number[] - 주소 ID 배열 (필수)
- `scale?`: string - 지도 축척 ('1200', '1500', '2000', '3000', 기본: '1200')
- `save_pdf?`: boolean - PDF 저장 여부 (기본: true)
- `use_cache?`: boolean - 캐시 사용 여부 (기본: true)
- `cache_expiry_days?`: number - 캐시 만료 기간 (일, 기본: 30)
- `headless?`: boolean - 헤드리스 모드 (기본: true)
- `wait_time?`: number - 대기 시간 (초, 기본: 3)
- `auto_start?`: boolean - 자동 시작 여부 (기본: false)

**반환값**
```typescript
interface CrawlJob {
  id: number;
  name: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  total_count: number;
  completed_count: number;
  failed_count: number;
  cached_count: number;
  scale: string;
  save_pdf: boolean;
  use_cache: boolean;
  cache_expiry_days: number;
  created_at: string;
  started_at: string | null;
  paused_at: string | null;
  finished_at: string | null;
}
```

**에러**
- `400`: 필수 필드 누락, 빈 address_ids
- `404`: 일부 주소 없음
- `500`: 데이터베이스 오류

---

### start_crawl_job
대기 중인 크롤링 작업을 시작합니다. 이미 실행 중인 작업이 있으면 대기열에 추가됩니다.

**호출**
```typescript
invoke<void>('start_crawl_job', {
  job_id: 1,
  priority?: 'high' // 'high' | 'normal' | 'low'
})
```

**매개변수**
- `job_id`: number - 작업 ID (필수)
- `priority?`: string - 우선순위 (기본: 'normal')

**에러**
- `404`: 작업 없음
- `400`: 이미 실행 중인 상태
- `500`: 크롤러 시작 실패

---

### pause_crawl_job
실행 중인 크롤링 작업을 일시정지합니다. 현재 처리 중인 항목은 완료됩니다.

**호출**
```typescript
invoke<void>('pause_crawl_job', {
  job_id: 1
})
```

**에러**
- `404`: 작업 없음
- `400`: 실행 중이 아닌 상태

---

### resume_crawl_job
일시정지된 작업을 재개합니다.

**호출**
```typescript
invoke<void>('resume_crawl_job', {
  job_id: 1
})
```

**에러**
- `404`: 작업 없음
- `400`: 일시정지 상태가 아님

---

### stop_crawl_job
실행 중인 작업을 즉시 중지합니다.

**호출**
```typescript
invoke<void>('stop_crawl_job', {
  job_id: 1,
  force?: false
})
```

**매개변수**
- `job_id`: number - 작업 ID
- `force?`: boolean - 강제 중지 (기본: false)

**에러**
- `404`: 작업 없음
- `400`: 중지 불가능한 상태

---

### get_crawl_jobs
작업 목록을 조회합니다.

**호출**
```typescript
invoke<PaginatedResult<CrawlJob>>('get_crawl_jobs', {
  page: 1,
  per_page: 20,
  status?: 'running'
})
```

**반환값**
```typescript
interface PaginatedResult<CrawlJob> {
  data: CrawlJob[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
```

---

### get_crawl_job
특정 작업의 상세 정보를 조회합니다.

**호출**
```typescript
invoke<CrawlJobDetail>('get_crawl_job', {
  job_id: 1
})
```

**반환값**
```typescript
interface CrawlJobDetail extends CrawlJob {
  settings_snapshot: Record<string, unknown>; // JSON
  progress_percent: number;
  cache_hit_rate: number;
  failure_rate: number;
  duration_minutes?: number;
  items_status: {
    pending: number;
    running: number;
    success: number;
    failed: number;
    cached: number;
    skipped: number;
  };
}
```

---

### delete_crawl_job
완료된 작업을 삭제합니다. 관련 결과는 유지됩니다.

**호출**
```typescript
invoke<void>('delete_crawl_job', {
  job_id: 1
})
```

---

### get_job_items
특정 작업의 개별 항목 목록을 조회합니다.

**호출**
```typescript
invoke<PaginatedResult<JobItem>>('get_job_items', {
  job_id: 1,
  page: 1,
  per_page: 50,
  status?: 'failed'
})
```

**반환값**
```typescript
interface JobItem {
  id: number;
  job_id: number;
  address_id: number;
  address: string;
  result_id: number | null;
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped' | 'cached';
  sort_order: number;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
}
```

---

## 1.3 결과 조회 커맨드

### get_results
크롤링 결과를 조회합니다. 검색, 필터링, 정렬을 지원합니다.

**호출**
```typescript
invoke<PaginatedResult<CrawlResult>>('get_results', {
  page: 1,
  per_page: 50,
  search?: '역삼동',
  date_from?: '2024-03-01',
  date_to?: '2024-03-10',
  status?: 'success',
  source?: 'crawl', // 'crawl' | 'cache' | 'manual'
  scale?: '1200',
  sort_by?: 'crawled_at',
  sort_order?: 'desc'
})
```

**반환값**
```typescript
interface CrawlResult {
  id: number;
  address_id: number;
  address: string;
  pnu: string | null;
  present_addr: string | null;
  present_class: string | null;
  present_area: string | null;
  jiga: string | null;
  jiga_year: string | null;
  present_mark1: string | null;
  present_mark2: string | null;
  present_mark3: string | null;
  image_path: string | null;
  pdf_path: string | null;
  scale: string;
  status: 'success' | 'partial' | 'failed';
  source: 'crawl' | 'cache' | 'manual';
  error_message: string | null;
  crawled_at: string;
  expires_at: string | null;
  parsing_duration_ms: number | null;
}
```

---

### get_result
특정 결과의 상세 정보를 조회합니다.

**호출**
```typescript
invoke<CrawlResultDetail>('get_result', {
  id: 1
})
```

**반환값**
```typescript
interface CrawlResultDetail extends CrawlResult {
  is_cached: boolean;
  cache_expires_in_days?: number;
  related_job?: CrawlJob;
}
```

---

### get_result_history
특정 주소의 크롤링 이력을 조회합니다.

**호출**
```typescript
invoke<CrawlResult[]>('get_result_history', {
  address_id: 1,
  limit?: 10
})
```

**반환값**
```typescript
interface CrawlResult[] // 최신순 정렬
```

---

### delete_results
하나 이상의 결과를 삭제합니다.

**호출**
```typescript
invoke<{ deleted: number }>('delete_results', {
  ids: [1, 2, 3],
  delete_files?: true // 이미지/PDF도 함께 삭제
})
```

---

### recrawl_results
선택한 결과를 강제로 재크롤링합니다.

**호출**
```typescript
invoke<CrawlJob>('recrawl_results', {
  ids: [1, 2, 3],
  scale?: '2400',
  use_cache?: false
})
```

**반환값**
```typescript
interface CrawlJob { /* 새로 생성된 작업 */ }
```

---

### check_cache
특정 주소의 캐시 상태를 확인합니다.

**호출**
```typescript
invoke<CacheStatus>('check_cache', {
  address_id: 1
})
```

**반환값**
```typescript
interface CacheStatus {
  has_cache: boolean;
  is_valid: boolean;
  result?: CrawlResult;
  expires_at?: string;
  expires_in_days?: number;
}
```

---

## 1.4 내보내기 커맨드

### export_to_excel
결과를 Excel 파일로 내보냅니다.

**호출**
```typescript
invoke<string>('export_to_excel', {
  result_ids?: [1, 2, 3], // 없으면 전체
  columns: ['address', 'present_addr', 'jiga', 'image_path'],
  include_images?: false,
  output_path: '/path/to/export.xlsx'
})
```

**반환값**
```typescript
string // 저장된 파일 경로
```

---

### export_to_csv
결과를 CSV 파일로 내보냅니다.

**호출**
```typescript
invoke<string>('export_to_csv', {
  result_ids?: [1, 2, 3],
  columns: ['address', 'present_addr', 'jiga'],
  output_path: '/path/to/export.csv'
})
```

---

## 1.5 설정 커맨드

### get_settings
모든 설정을 조회합니다.

**호출**
```typescript
invoke<Settings>('get_settings')
```

**반환값**
```typescript
interface Settings {
  cache_expiry_days: number;
  cache_mode: 'never' | 'always' | 'smart';
  default_scale: string;
  wait_time: number;
  headless_mode: boolean;
  max_retries: number;
  page_load_timeout: number;
  images_dir: string;
  pdfs_dir: string;
  theme: 'light' | 'dark' | 'auto';
  language: 'ko' | 'en';
  window_width: number;
  window_height: number;
  enable_telemetry: boolean;
  app_version: string;
  last_backup_at?: string;
}
```

---

### get_setting
특정 설정값을 조회합니다.

**호출**
```typescript
invoke<string | number | boolean>('get_setting', {
  key: 'cache_expiry_days'
})
```

---

### update_setting
특정 설정값을 업데이트합니다.

**호출**
```typescript
invoke<void>('update_setting', {
  key: 'cache_expiry_days',
  value: '60'
})
```

---

### update_settings
여러 설정값을 일괄 업데이트합니다.

**호출**
```typescript
invoke<void>('update_settings', {
  cache_expiry_days: '60',
  headless_mode: 'false',
  theme: 'dark'
})
```

---

### reset_settings
모든 설정을 기본값으로 복원합니다.

**호출**
```typescript
invoke<void>('reset_settings')
```

---

## 1.6 파일/시스템 커맨드

### open_file
파일을 기본 애플리케이션으로 엽니다.

**호출**
```typescript
invoke<void>('open_file', {
  file_path: '/path/to/image.jpg'
})
```

---

### open_folder
폴더를 탐색기에서 엽니다.

**호출**
```typescript
invoke<void>('open_folder', {
  folder_path: '/path/to/images'
})
```

---

### select_file
파일 선택 대화상자를 열고 선택된 경로를 반환합니다.

**호출**
```typescript
invoke<string | null>('select_file', {
  filters: [
    { name: 'Excel', extensions: ['xlsx', 'xls'] },
    { name: 'All Files', extensions: ['*'] }
  ]
})
```

---

### select_folder
폴더 선택 대화상자를 열고 선택된 경로를 반환합니다.

**호출**
```typescript
invoke<string | null>('select_folder')
```

---

### backup_database
데이터베이스를 수동으로 백업합니다.

**호출**
```typescript
invoke<void>('backup_database', {
  output_path: '/path/to/backup.db'
})
```

---

### restore_database
백업 파일에서 데이터베이스를 복원합니다.

**호출**
```typescript
invoke<void>('restore_database', {
  backup_path: '/path/to/backup.db'
})
```

---

### clear_all_cache
모든 캐시를 삭제합니다.

**호출**
```typescript
invoke<{ deleted: number }>('clear_all_cache')
```

---

### get_dashboard_stats
대시보드 통계를 조회합니다.

**호출**
```typescript
invoke<DashboardStats>('get_dashboard_stats')
```

**반환값**
```typescript
interface DashboardStats {
  total_addresses: number;
  total_results: number;
  success_count: number;
  failed_count: number;
  cached_count: number;
  today_count: number;
  success_rate: number;
  cache_hit_rate: number;
  storage_size_mb: number;
  images_count: number;
  pdfs_count: number;
  active_jobs: number;
  last_crawl_at?: string;
}
```

---

### get_crawl_logs
크롤링 로그를 조회합니다.

**호출**
```typescript
invoke<CrawlLog[]>('get_crawl_logs', {
  job_id?: 1,
  level?: 'error', // 'debug' | 'info' | 'warn' | 'error'
  limit?: 100
})
```

**반환값**
```typescript
interface CrawlLog {
  id: number;
  job_id: number | null;
  job_item_id: number | null;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  created_at: string;
}
```

---

# Part 2: Tauri 실시간 이벤트

프론트엔드에서 백엔드의 실시간 이벤트를 수신합니다. `listen()` 함수로 구독할 수 있습니다.

## 2.1 크롤링 진행 이벤트

### crawl://progress
크롤링 진행 상황을 실시간으로 전송합니다.

**수신**
```typescript
listen<CrawlProgress>('crawl://progress', (event) => {
  console.log(event.payload);
})
```

**페이로드**
```typescript
interface CrawlProgress {
  job_id: number;
  item_id: number;
  address: string;
  status: 'running' | 'success' | 'failed' | 'cached';
  message: string;
  progress: {
    completed: number;
    total: number;
    percentage: number;
  };
  estimated_remaining_minutes?: number;
  speed_items_per_minute?: number;
}
```

**예시**
```typescript
// 진행률 표시
progress.percentage // 45.5
progress.address // "서울시 강남구 역삼동 123"
progress.status // "success"
```

---

## 2.2 크롤링 로그 이벤트

### crawl://log
크롤링 로그 메시지를 전송합니다.

**수신**
```typescript
listen<CrawlLog>('crawl://log', (event) => {
  console.log(event.payload);
})
```

**페이로드**
```typescript
interface CrawlLog {
  job_id: number;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  timestamp: string;
}
```

---

## 2.3 작업 상태 이벤트

### crawl://job-status
작업 상태가 변경되면 전송합니다.

**수신**
```typescript
listen<JobStatusChange>('crawl://job-status', (event) => {
  console.log(event.payload);
})
```

**페이로드**
```typescript
interface JobStatusChange {
  job_id: number;
  status: 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  stats: {
    completed: number;
    failed: number;
    cached: number;
    total: number;
  };
  timestamp: string;
}
```

---

## 2.4 작업 완료 이벤트

### crawl://complete
크롤링 작업이 완료되면 전송합니다.

**수신**
```typescript
listen<CrawlComplete>('crawl://complete', (event) => {
  console.log(event.payload);
})
```

**페이로드**
```typescript
interface CrawlComplete {
  job_id: number;
  name: string;
  total_addresses: number;
  successful: number;
  failed: number;
  cached: number;
  duration_seconds: number;
  elapsed_time_formatted: string; // "15분 30초"
  average_time_per_item_ms: number;
  cache_hit_rate: number;
  timestamp: string;
}
```

---

# Part 3: 크롤러 사이드카 프로토콜

Tauri 백엔드와 크롤러 사이드카(Bun + Playwright)는 stdin/stdout 기반 JSON 메시지로 통신합니다. 한 줄에 하나의 JSON 객체가 전송됩니다.

## 3.1 메시지 형식

### 기본 구조
```typescript
interface SidecarMessage {
  type: 'START_CRAWL' | 'PAUSE' | 'RESUME' | 'STOP' | 'PING';
  job_id: number;
  payload?: unknown;
  timestamp?: string;
}

interface SidecarResponse {
  type: 'READY' | 'ITEM_START' | 'VALIDATION_RESULT' | 'DATA_RESULT'
       | 'IMAGE_RESULT' | 'PDF_RESULT' | 'ITEM_COMPLETE' | 'ITEM_FAILED'
       | 'LOG' | 'COMPLETE' | 'ERROR' | 'PONG';
  job_id: number;
  payload?: unknown;
  timestamp?: string;
}
```

---

## 3.2 Rust → Sidecar 메시지

### START_CRAWL
크롤링을 시작합니다.

```json
{
  "type": "START_CRAWL",
  "job_id": 1,
  "payload": {
    "items": [
      {
        "item_id": 1,
        "address_id": 10,
        "address": "서울시 강남구 역삼동 123-45",
        "pnu": "1135010400110010045"
      },
      {
        "item_id": 2,
        "address_id": 11,
        "address": "서울시 강남구 역삼동 123-46",
        "pnu": "1135010400110010046"
      }
    ],
    "settings": {
      "scale": "1200",
      "wait_time": 5,
      "headless": true,
      "save_pdf": true,
      "max_retries": 3,
      "timeout": 30000
    }
  }
}
```

---

### PAUSE
크롤링을 일시정지합니다.

```json
{
  "type": "PAUSE",
  "job_id": 1
}
```

---

### RESUME
크롤링을 재개합니다.

```json
{
  "type": "RESUME",
  "job_id": 1
}
```

---

### STOP
크롤링을 중지합니다.

```json
{
  "type": "STOP",
  "job_id": 1
}
```

---

### PING
사이드카의 상태를 확인합니다.

```json
{
  "type": "PING",
  "job_id": 1
}
```

---

## 3.3 Sidecar → Rust 메시지

### READY
사이드카가 준비 완료 상태입니다.

```json
{
  "type": "READY",
  "job_id": 0,
  "payload": {
    "version": "1.0.0",
    "browser": "chromium"
  }
}
```

---

### ITEM_START
항목 처리를 시작합니다.

```json
{
  "type": "ITEM_START",
  "job_id": 1,
  "payload": {
    "item_id": 1,
    "address": "서울시 강남구 역삼동 123-45"
  }
}
```

---

### VALIDATION_RESULT
주소 검증 결과입니다.

```json
{
  "type": "VALIDATION_RESULT",
  "job_id": 1,
  "payload": {
    "item_id": 1,
    "success": true,
    "pnu": "1135010400110010045",
    "found_count": 1,
    "message": "검색 완료"
  }
}
```

---

### DATA_RESULT
데이터 추출 결과입니다.

```json
{
  "type": "DATA_RESULT",
  "job_id": 1,
  "payload": {
    "item_id": 1,
    "data": {
      "present_addr": "서울시 강남구 역삼동 123",
      "present_class": "토지",
      "present_area": "1234.56",
      "jiga": "5600000",
      "jiga_year": "2024",
      "present_mark1": "도시지역",
      "present_mark2": null,
      "present_mark3": null
    }
  }
}
```

---

### IMAGE_RESULT
이미지 다운로드 결과입니다.

```json
{
  "type": "IMAGE_RESULT",
  "job_id": 1,
  "payload": {
    "item_id": 1,
    "success": true,
    "image_path": "images/2024/03/1135010400110010045_20240310.jpg",
    "image_filename": "1135010400110010045_20240310.jpg",
    "image_size_bytes": 125000
  }
}
```

---

### PDF_RESULT
PDF 생성 결과입니다.

```json
{
  "type": "PDF_RESULT",
  "job_id": 1,
  "payload": {
    "item_id": 1,
    "success": true,
    "pdf_path": "pdfs/2024/03/1135010400110010045_토지이용계획_20240310.pdf",
    "pdf_filename": "1135010400110010045_토지이용계획_20240310.pdf",
    "pdf_size_bytes": 250000
  }
}
```

---

### ITEM_COMPLETE
항목 처리가 완료되었습니다.

```json
{
  "type": "ITEM_COMPLETE",
  "job_id": 1,
  "payload": {
    "item_id": 1,
    "status": "success",
    "result": {
      "address": "서울시 강남구 역삼동 123-45",
      "pnu": "1135010400110010045",
      "present_addr": "서울시 강남구 역삼동 123",
      "present_class": "토지",
      "present_area": "1234.56",
      "jiga": "5600000",
      "jiga_year": "2024",
      "present_mark1": "도시지역",
      "present_mark2": null,
      "present_mark3": null,
      "image_path": "images/2024/03/1135010400110010045_20240310.jpg",
      "pdf_path": "pdfs/2024/03/1135010400110010045_토지이용계획_20240310.pdf",
      "scale": "1200",
      "source": "crawl",
      "parsing_duration_ms": 2500
    }
  }
}
```

---

### ITEM_FAILED
항목 처리에 실패했습니다.

```json
{
  "type": "ITEM_FAILED",
  "job_id": 1,
  "payload": {
    "item_id": 1,
    "error": "검색 결과 없음",
    "error_code": "NOT_FOUND",
    "retries_left": 2
  }
}
```

---

### LOG
로그 메시지입니다.

```json
{
  "type": "LOG",
  "job_id": 1,
  "payload": {
    "level": "info",
    "message": "항목 1/50 처리 중: 서울시 강남구 역삼동 123-45"
  }
}
```

---

### COMPLETE
모든 항목 처리가 완료되었습니다.

```json
{
  "type": "COMPLETE",
  "job_id": 1,
  "payload": {
    "total": 50,
    "success": 45,
    "failed": 5,
    "elapsed_ms": 450000
  }
}
```

---

### ERROR
치명적 오류가 발생했습니다.

```json
{
  "type": "ERROR",
  "job_id": 1,
  "payload": {
    "message": "브라우저 충돌",
    "code": "BROWSER_CRASH",
    "fatal": true
  }
}
```

---

### PONG
PING에 대한 응답입니다.

```json
{
  "type": "PONG",
  "job_id": 1,
  "payload": {
    "uptime_ms": 123456
  }
}
```

---

# Part 4: TypeScript 타입 정의

프론트엔드와 백엔드에서 공유되는 TypeScript 타입 정의입니다. `src/lib/types/` 디렉토리에 저장합니다.

## 4.1 공통 타입 (types/common.ts)

```typescript
// 페이지네이션
export interface PaginatedResult<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// API 응답
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

// 에러 응답
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

// 파일 필터
export interface FileFilter {
  name: string;
  extensions: string[];
}
```

## 4.2 주소 타입 (types/address.ts)

```typescript
export interface Address {
  id: number;
  address: string;
  normalized_address: string | null;
  pnu: string | null;
  group_name: string | null;
  tags: string[];
  memo: string | null;
  created_at: string;
  updated_at: string;
}

export interface AddressInput {
  address: string;
  group_name?: string;
  tags?: string[];
  memo?: string;
}

export interface ImportResult {
  success: boolean;
  total_read: number;
  imported: number;
  skipped: number;
  errors: string[];
  message: string;
}
```

## 4.3 결과 타입 (types/result.ts)

```typescript
export interface CrawlResult {
  id: number;
  address_id: number;
  address: string;
  pnu: string | null;
  present_addr: string | null;
  present_class: string | null;
  present_area: string | null;
  jiga: string | null;
  jiga_year: string | null;
  present_mark1: string | null;
  present_mark2: string | null;
  present_mark3: string | null;
  image_path: string | null;
  pdf_path: string | null;
  scale: string;
  status: 'success' | 'partial' | 'failed';
  source: 'crawl' | 'cache' | 'manual';
  error_message: string | null;
  crawled_at: string;
  expires_at: string | null;
  parsing_duration_ms: number | null;
}

export interface ResultSearchParams {
  page?: number;
  per_page?: number;
  search?: string;
  date_from?: string;
  date_to?: string;
  status?: string;
  source?: string;
  scale?: string;
  sort_by?: string;
  sort_order?: string;
}

export interface CacheStatus {
  has_cache: boolean;
  is_valid: boolean;
  result?: CrawlResult;
  expires_at?: string;
  expires_in_days?: number;
}
```

## 4.4 작업 타입 (types/job.ts)

```typescript
export interface CrawlJob {
  id: number;
  name: string;
  status: JobStatus;
  total_count: number;
  completed_count: number;
  failed_count: number;
  cached_count: number;
  scale: string;
  save_pdf: boolean;
  use_cache: boolean;
  cache_expiry_days: number;
  created_at: string;
  started_at: string | null;
  paused_at: string | null;
  finished_at: string | null;
}

export type JobStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';

export interface CrawlJobDetail extends CrawlJob {
  settings_snapshot: Record<string, unknown>;
  progress_percent: number;
  cache_hit_rate: number;
  failure_rate: number;
  duration_minutes?: number;
  items_status: {
    pending: number;
    running: number;
    success: number;
    failed: number;
    cached: number;
    skipped: number;
  };
}

export interface JobItem {
  id: number;
  job_id: number;
  address_id: number;
  address: string;
  result_id: number | null;
  status: JobItemStatus;
  sort_order: number;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
}

export type JobItemStatus = 'pending' | 'running' | 'success' | 'failed' | 'skipped' | 'cached';

export interface CrawlProgress {
  job_id: number;
  item_id: number;
  address: string;
  status: 'running' | 'success' | 'failed' | 'cached';
  message: string;
  progress: {
    completed: number;
    total: number;
    percentage: number;
  };
  estimated_remaining_minutes?: number;
  speed_items_per_minute?: number;
}
```

## 4.5 로그 타입 (types/log.ts)

```typescript
export interface CrawlLog {
  id: number;
  job_id: number | null;
  job_item_id: number | null;
  level: LogLevel;
  message: string;
  created_at: string;
}

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface DashboardStats {
  total_addresses: number;
  total_results: number;
  success_count: number;
  failed_count: number;
  cached_count: number;
  today_count: number;
  success_rate: number;
  cache_hit_rate: number;
  storage_size_mb: number;
  images_count: number;
  pdfs_count: number;
  active_jobs: number;
  last_crawl_at?: string;
}
```

---

# Part 5: 프론트엔드 서비스 레이어

Tauri IPC 호출을 추상화하는 서비스 계층을 구현합니다. `src/lib/services/` 디렉토리에 저장합니다.

## 5.1 데이터베이스 서비스 (services/db.ts)

```typescript
import { invoke } from '@tauri-apps/api/core';
import type {
  Address,
  CrawlResult,
  CrawlJob,
  DashboardStats,
  PaginatedResult
} from '$lib/types';

export const addressService = {
  getAll: (page: number, perPage: number, search?: string) =>
    invoke<PaginatedResult<Address>>('get_addresses', {
      page,
      per_page: perPage,
      search
    }),

  add: (address: string, groupName?: string, tags?: string[], memo?: string) =>
    invoke<Address>('add_address', {
      address,
      group_name: groupName,
      tags,
      memo
    }),

  update: (id: number, data: Partial<Address>) =>
    invoke<Address>('update_address', { id, ...data }),

  delete: (ids: number[], deleteResults?: boolean) =>
    invoke<{ deleted: number }>('delete_addresses', {
      ids,
      delete_results: deleteResults
    }),

  importFromExcel: (
    filePath: string,
    startRow: number = 2,
    addressColumn: string = 'B',
    groupName?: string,
    duplicateStrategy: 'skip' | 'overwrite' = 'skip'
  ) =>
    invoke('import_addresses_from_excel', {
      file_path: filePath,
      start_row: startRow,
      address_column: addressColumn,
      group_name: groupName,
      duplicate_strategy: duplicateStrategy
    }),

  getGroups: () =>
    invoke<string[]>('get_address_groups')
};

export const resultService = {
  getAll: (
    page: number,
    perPage: number,
    search?: string,
    status?: string,
    dateFrom?: string,
    dateTo?: string
  ) =>
    invoke<PaginatedResult<CrawlResult>>('get_results', {
      page,
      per_page: perPage,
      search,
      status,
      date_from: dateFrom,
      date_to: dateTo
    }),

  getDetail: (id: number) =>
    invoke('get_result', { id }),

  getHistory: (addressId: number, limit?: number) =>
    invoke<CrawlResult[]>('get_result_history', {
      address_id: addressId,
      limit
    }),

  delete: (ids: number[], deleteFiles?: boolean) =>
    invoke('delete_results', { ids, delete_files: deleteFiles }),

  recrawl: (ids: number[], scale?: string, useCache?: boolean) =>
    invoke<CrawlJob>('recrawl_results', { ids, scale, use_cache: useCache })
};

export const jobService = {
  create: (
    name: string,
    addressIds: number[],
    scale?: string,
    useCacheahoo?: boolean
  ) =>
    invoke<CrawlJob>('create_crawl_job', {
      name,
      address_ids: addressIds,
      scale,
      use_cache: useCache
    }),

  start: (jobId: number, priority?: string) =>
    invoke('start_crawl_job', { job_id: jobId, priority }),

  pause: (jobId: number) =>
    invoke('pause_crawl_job', { job_id: jobId }),

  resume: (jobId: number) =>
    invoke('resume_crawl_job', { job_id: jobId }),

  stop: (jobId: number, force?: boolean) =>
    invoke('stop_crawl_job', { job_id: jobId, force }),

  getAll: (page: number, perPage: number, status?: string) =>
    invoke<PaginatedResult<CrawlJob>>('get_crawl_jobs', {
      page,
      per_page: perPage,
      status
    }),

  getDetail: (jobId: number) =>
    invoke('get_crawl_job', { job_id: jobId }),

  getItems: (jobId: number, page: number, perPage: number, status?: string) =>
    invoke('get_job_items', {
      job_id: jobId,
      page,
      per_page: perPage,
      status
    })
};
```

## 5.2 크롤러 서비스 (services/crawler.ts)

```typescript
import { invoke, listen } from '@tauri-apps/api/core';
import type {
  CrawlJob,
  CrawlProgress,
  CrawlLog
} from '$lib/types';

export const crawlerService = {
  create: (name: string, addressIds: number[], autoStart: boolean = false) =>
    invoke<CrawlJob>('create_crawl_job', {
      name,
      address_ids: addressIds,
      auto_start: autoStart
    }),

  start: (jobId: number) =>
    invoke('start_crawl_job', { job_id: jobId }),

  pause: (jobId: number) =>
    invoke('pause_crawl_job', { job_id: jobId }),

  resume: (jobId: number) =>
    invoke('resume_crawl_job', { job_id: jobId }),

  stop: (jobId: number) =>
    invoke('stop_crawl_job', { job_id: jobId }),

  onProgress: (callback: (progress: CrawlProgress) => void) =>
    listen('crawl://progress', (event) => {
      callback(event.payload as CrawlProgress);
    }),

  onLog: (callback: (log: CrawlLog) => void) =>
    listen('crawl://log', (event) => {
      callback(event.payload as CrawlLog);
    }),

  onComplete: (callback: (data: any) => void) =>
    listen('crawl://complete', (event) => {
      callback(event.payload);
    }),

  onJobStatus: (callback: (status: any) => void) =>
    listen('crawl://job-status', (event) => {
      callback(event.payload);
    })
};
```

## 5.3 설정 서비스 (services/settings.ts)

```typescript
import { invoke } from '@tauri-apps/api/core';

export const settingsService = {
  getAll: () =>
    invoke('get_settings'),

  get: (key: string) =>
    invoke('get_setting', { key }),

  update: (key: string, value: string) =>
    invoke('update_setting', { key, value }),

  updateMultiple: (settings: Record<string, string>) =>
    invoke('update_settings', settings),

  reset: () =>
    invoke('reset_settings')
};
```

## 5.4 파일 서비스 (services/file.ts)

```typescript
import { invoke } from '@tauri-apps/api/core';

export const fileService = {
  openFile: (filePath: string) =>
    invoke('open_file', { file_path: filePath }),

  openFolder: (folderPath: string) =>
    invoke('open_folder', { folder_path: folderPath }),

  selectFile: (filters?: Array<{ name: string; extensions: string[] }>) =>
    invoke<string | null>('select_file', { filters }),

  selectFolder: () =>
    invoke<string | null>('select_folder'),

  exportToExcel: (
    resultIds?: number[],
    columns?: string[],
    outputPath?: string
  ) =>
    invoke<string>('export_to_excel', {
      result_ids: resultIds,
      columns,
      output_path: outputPath
    }),

  exportToCsv: (
    resultIds?: number[],
    columns?: string[],
    outputPath?: string
  ) =>
    invoke<string>('export_to_csv', {
      result_ids: resultIds,
      columns,
      output_path: outputPath
    }),

  backupDatabase: (outputPath: string) =>
    invoke('backup_database', { output_path: outputPath }),

  restoreDatabase: (backupPath: string) =>
    invoke('restore_database', { backup_path: backupPath })
};
```

## 5.5 시스템 서비스 (services/system.ts)

```typescript
import { invoke } from '@tauri-apps/api/core';
import type { DashboardStats, CrawlLog } from '$lib/types';

export const systemService = {
  getDashboardStats: () =>
    invoke<DashboardStats>('get_dashboard_stats'),

  getCrawlLogs: (jobId?: number, level?: string, limit?: number) =>
    invoke<CrawlLog[]>('get_crawl_logs', {
      job_id: jobId,
      level,
      limit
    }),

  clearAllCache: () =>
    invoke<{ deleted: number }>('clear_all_cache'),

  checkCache: (addressId: number) =>
    invoke('check_cache', { address_id: addressId })
};
```

---

# Part 6: 에러 처리 계약

## 6.1 HTTP 상태 코드

| 코드 | 의미 | 사용 사례 |
|------|------|---------|
| 200 | OK | 성공적인 요청 |
| 400 | Bad Request | 유효하지 않은 입력 |
| 404 | Not Found | 리소스 없음 |
| 409 | Conflict | 중복 데이터 |
| 422 | Unprocessable Entity | 파일 형식 오류 |
| 500 | Internal Server Error | 데이터베이스 오류 |

## 6.2 에러 응답 형식

```typescript
interface ErrorResponse {
  code: string; // 'DUPLICATE_ADDRESS', 'NOT_FOUND', etc.
  message: string; // 사용자 친화적 메시지 (한국어)
  details?: {
    field?: string; // 어떤 필드에서 오류 발생
    value?: unknown; // 문제가 된 값
    constraint?: string; // 위반된 제약조건
  };
}
```

## 6.3 사용자 정의 에러 코드

| 코드 | 메시지 | 원인 |
|-----|--------|------|
| `DUPLICATE_ADDRESS` | "이미 존재하는 주소입니다" | 중복 주소 추가 |
| `EMPTY_ADDRESS` | "주소를 입력해주세요" | 빈 주소 필드 |
| `ADDRESS_NOT_FOUND` | "주소를 찾을 수 없습니다" | ID로 주소 조회 실패 |
| `JOB_NOT_FOUND` | "작업을 찾을 수 없습니다" | ID로 작업 조회 실패 |
| `JOB_ALREADY_RUNNING` | "이미 실행 중인 작업입니다" | 중복 시작 |
| `INVALID_EXCEL_FILE` | "올바른 Excel 파일이 아닙니다" | 파일 형식 오류 |
| `DATABASE_ERROR` | "데이터베이스 오류가 발생했습니다" | DB 연결/쿼리 오류 |
| `FILE_NOT_FOUND` | "파일을 찾을 수 없습니다" | 경로 오류 |

## 6.4 프론트엔드 에러 처리 패턴

```typescript
try {
  const result = await invoke('add_address', { address: '...' });
} catch (error: unknown) {
  const err = error as { code: string; message: string };

  switch (err.code) {
    case 'DUPLICATE_ADDRESS':
      showToast('error', '이미 존재하는 주소입니다');
      break;
    case 'EMPTY_ADDRESS':
      showToast('error', '주소를 입력해주세요');
      break;
    case 'DATABASE_ERROR':
      showToast('error', '데이터베이스 오류가 발생했습니다. 잠시 후 다시 시도해주세요');
      break;
    default:
      showToast('error', err.message);
  }
}
```

---

# Part 7: 시퀀스 다이어그램

## 7.1 Excel 주소 가져오기 흐름

```
사용자
  │
  └─> UI: "Excel 가져오기" 클릭
        │
        └─> 파일 선택 대화상자
              │
              └─> 파일 선택: example.xlsx
                    │
                    └─> invoke('import_addresses_from_excel')
                          │
                          ├─> Tauri Backend
                          │     │
                          │     ├─> Excel 파일 읽기
                          │     ├─> 주소 추출 (B 컬럼)
                          │     ├─> 중복 검사
                          │     └─> addresses 테이블 INSERT
                          │
                          └─> ImportResult 반환
                                │
                                └─> UI 업데이트
                                      │
                                      └─> "50개 주소 추가됨"
```

## 7.2 크롤링 작업 실행 흐름

```
사용자
  │
  └─> UI: "크롤링 시작" 클릭
        │
        └─> invoke('create_crawl_job', { address_ids: [1,2,3,...] })
              │
              ├─> Tauri Backend
              │     │
              │     ├─> crawl_jobs 테이블에 INSERT
              │     ├─> job_items 테이블에 항목 추가
              │     │
              │     └─> Sidecar 프로세스 시작
              │           │
              │           ├─> Playwright 브라우저 시작
              │           │
              │           └─> 루프: 각 주소마다
              │                 │
              │                 ├─> eum.go.kr 접속
              │                 ├─> 주소 검색
              │                 ├─> 데이터 추출
              │                 ├─> 이미지 다운로드
              │                 │
              │                 └─> ITEM_COMPLETE 메시지 (stdout)
              │                       │
              │                       └─> Tauri가 수신
              │                             │
              │                             ├─> crawl_results 저장
              │                             ├─> 이벤트 발행: crawl://progress
              │                             │
              │                             └─> Frontend 수신
              │                                   │
              │                                   └─> UI 업데이트 (진행률)
              │
              └─> CrawlJob 반환
                    │
                    └─> 모든 항목 완료
                          │
                          └─> 이벤트 발행: crawl://complete
                                │
                                └─> Frontend 수신
                                      │
                                      └─> 완료 알림 표시
```

## 7.3 캐시 확인 흐름

```
크롤링 시작
  │
  └─> 각 주소마다
        │
        ├─> Tauri: check_cache(address_id)
        │     │
        │     └─> SELECT FROM crawl_results
        │           WHERE address_id = ?
        │           AND status = 'success'
        │           AND expires_at > NOW()
        │
        ├─> 캐시 있음?
        │     │
        │     YES─> 캐시된 결과 반환 (소스: 'cache')
        │     │
        │     NO──> Sidecar에 지시: START_CRAWL
        │           │
        │           └─> 웹 크롤링 수행
        │                 │
        │                 └─> 결과 저장 (소스: 'crawl')
        │                       │
        │                       └─> expires_at 설정
        │
        └─> 결과 반환
```

## 7.4 데이터 내보내기 흐름

```
사용자
  │
  └─> UI: "Excel 내보내기" 클릭
        │
        └─> 내보내기 옵션 설정
              │
              ├─> 컬럼 선택
              ├─> 이미지 포함 여부
              └─> 저장 경로 선택
                    │
                    └─> invoke('export_to_excel', { result_ids, ... })
                          │
                          ├─> Tauri Backend
                          │     │
                          │     ├─> crawl_results 조회
                          │     ├─> Excel 워크북 생성
                          │     ├─> 각 행에 데이터 입력
                          │     │
                          │     ├─> 이미지 포함?
                          │     │     │
                          │     │     YES─> 이미지 파일에서 읽어서 삽입
                          │     │
                          │     └─> 파일 저장
                          │
                          └─> 파일 경로 반환
                                │
                                └─> invoke('open_file')
                                      │
                                      └─> 사용자의 Excel에서 자동으로 열기
```

---

## 문서 정보

- **작성일**: 2026-03-10
- **버전**: 1.0.0
- **상태**: 최종 검토 대기
- **대상 독자**: 프론트엔드 개발자, 백엔드 개발자
- **참조 문서**: 01-PRD.md, 02-ARCHITECTURE.md, 03-DATABASE.md

---

## 변경 이력

| 버전 | 날짜 | 변경 사항 | 작성자 |
|------|------|---------|--------|
| 1.0.0 | 2026-03-10 | 초안 작성 | Claude |

---

**이 문서는 기밀 문서입니다. 무단 배포를 금합니다.**
