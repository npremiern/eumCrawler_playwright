# 데이터베이스 스키마 설계 (SQLite)

## 목차
1. [개요](#개요)
2. [데이터베이스 아키텍처](#데이터베이스-아키텍처)
3. [테이블 설계](#테이블-설계)
4. [인덱싱 전략](#인덱싱-전략)
5. [마이그레이션 전략](#마이그레이션-전략)
6. [주요 쿼리](#주요-쿼리)
7. [데이터 무결성](#데이터-무결성)
8. [캐시 로직](#캐시-로직)
9. [성능 고려사항](#성능-고려사항)
10. [백업 및 복구](#백업-및-복구)
11. [ER 다이어그램](#er-다이어그램)

---

## 개요

### 목적
eumcrawl은 한국 부동산공시가격 정보(eum.go.kr)를 크롤링하고 로컬 SQLite 데이터베이스에 저장하는 Tauri v2 데스크톱 애플리케이션입니다.

### 핵심 요구사항
- **캐시/재사용**: 크롤링된 데이터를 설정 가능한 기간(7~365일 또는 무제한) 내에서 재사용
- **배치 작업 관리**: 여러 주소를 포함한 크롤링 작업 추적
- **검색/필터링**: 날짜, 지역, 상태별 히스토리 검색
- **내보내기 지원**: 효율적인 쿼리로 데이터 내보내기
- **파일 메타데이터**: 이미지 및 PDF 파일 메타데이터 추적

### 기술 스택
- **데이터베이스**: SQLite 3.43+
- **동시성**: WAL(Write-Ahead Logging) 모드
- **트랜잭션**: ACID 준수
- **마이그레이션**: 버전 기반 마이그레이션 (Rust 백엔드에서 실행)

---

## 데이터베이스 아키텍처

### 설계 원칙
1. **정규화**: 3NF 준수로 데이터 중복 최소화
2. **확장성**: 향후 기능 추가를 고려한 설계
3. **성능**: 자주 사용되는 쿼리에 최적화된 인덱싱
4. **안정성**: 외래키 제약조건으로 데이터 무결성 보장

### 데이터베이스 파일 위치
```
$APP_DATA_DIR/
├── eumcrawl.db          # 메인 데이터베이스
├── eumcrawl.db-shm      # WAL 공유 메모리
├── eumcrawl.db-wal      # WAL 로그
└── backups/             # 백업 파일
    └── eumcrawl_2024-03-10_120000.db
```

### 초기화 시퀀스
```rust
// Tauri 백엔드에서 실행
1. 데이터베이스 파일 확인
2. 스키마 버전 확인 (settings 테이블의 db_version)
3. 필요한 마이그레이션 실행
4. 기본 설정값 시드 처리
5. PRAGMA 설정 적용 (foreign_keys, journal_mode 등)
```

---

## 테이블 설계

### 1. addresses - 주소 관리

주소의 정규화된 형태와 메타데이터를 저장합니다.

```sql
CREATE TABLE addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT NOT NULL UNIQUE COLLATE NOCASE,
    normalized_address TEXT,
    pnu TEXT UNIQUE,
    group_name TEXT,
    tags TEXT,
    memo TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (length(address) > 0),
    CHECK (pnu IS NULL OR length(pnu) = 19)
);

-- 주소 그룹화를 위한 인덱스
CREATE INDEX idx_addresses_group_name ON addresses(group_name);
CREATE INDEX idx_addresses_created_at ON addresses(created_at DESC);
```

**컬럼 설명**:
- `id`: 유일한 식별자
- `address`: 원본 입력 주소 (UNIQUE: 중복 방지)
- `normalized_address`: 정규화된 주소 (예: 띄어쓰기 제거, 약자 정규화)
- `pnu`: 필지번호(19자리 숫자) - 토지 고유 식별자
- `group_name`: 배치 작업명이나 지역명으로 주소 그룹화
- `tags`: JSON 배열 형식 태그 (예: `["강남구", "주택", "검증됨"]`)
- `memo`: 사용자 메모
- `created_at`: 생성 시각
- `updated_at`: 최종 수정 시각

**데이터 예시**:
```json
{
    "id": 1,
    "address": "서울특별시 강남구 역삼동 123-45",
    "normalized_address": "서울특별시강남구역삼동123-45",
    "pnu": "1135010400110010045",
    "group_name": "2024-03-강남구-조사",
    "tags": "[\"강남구\", \"상업용\", \"검증완료\"]",
    "memo": "신축 건물, 2024년 준공"
}
```

---

### 2. crawl_results - 크롤링 결과 저장

각 주소에 대한 크롤링 결과를 저장합니다. 같은 주소에 대해 여러 번 크롤링할 수 있으므로 버전 관리를 지원합니다.

```sql
CREATE TABLE crawl_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address_id INTEGER NOT NULL,

    -- 공시정보 필드
    pnu TEXT,
    present_addr TEXT,
    present_class TEXT,
    present_area TEXT,
    jiga TEXT,
    jiga_year TEXT,
    present_mark1 TEXT,
    present_mark2 TEXT,
    present_mark3 TEXT,

    -- 파일 정보
    image_path TEXT,
    image_filename TEXT,
    image_size_bytes INTEGER,
    image_downloaded_at DATETIME,
    pdf_path TEXT,
    pdf_filename TEXT,
    pdf_size_bytes INTEGER,
    pdf_downloaded_at DATETIME,

    -- 크롤링 메타데이터
    scale TEXT NOT NULL DEFAULT '1200',
    status TEXT NOT NULL DEFAULT 'success',
    error_message TEXT,
    source TEXT NOT NULL DEFAULT 'crawl',
    crawled_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,

    -- 통계
    parsing_duration_ms INTEGER,

    FOREIGN KEY (address_id) REFERENCES addresses(id) ON DELETE CASCADE,
    CHECK (status IN ('success', 'partial', 'failed')),
    CHECK (source IN ('crawl', 'cache', 'manual')),
    CHECK (scale IN ('1200', '1500', '2000', '3000')),
    CHECK (present_area IS NULL OR CAST(present_area AS REAL) > 0),
    CHECK (jiga IS NULL OR CAST(jiga AS REAL) >= 0)
);

-- 쿼리 최적화 인덱스
CREATE INDEX idx_crawl_results_address_id ON crawl_results(address_id);
CREATE INDEX idx_crawl_results_status ON crawl_results(status);
CREATE INDEX idx_crawl_results_crawled_at ON crawl_results(crawled_at DESC);
CREATE INDEX idx_crawl_results_expires_at ON crawl_results(expires_at);

-- 복합 인덱스: 캐시 유효성 검사 최적화
CREATE INDEX idx_crawl_results_cache_check
    ON crawl_results(address_id, status, expires_at)
    WHERE status = 'success';

-- 조회용 복합 인덱스
CREATE INDEX idx_crawl_results_address_latest
    ON crawl_results(address_id, crawled_at DESC);
```

**컬럼 설명**:
- `address_id`: addresses 테이블 참조 (외래키)
- `pnu`: 필지번호 (address에서 중복, 빠른 검색용)
- `present_addr` 등: 부동산공시가격 사이트에서 크롤링한 실제 데이터
- `image_path`: 저장된 이미지 경로 (예: `images/2024/03/abc123.jpg`)
- `pdf_path`: 저장된 PDF 경로 (예: `pdfs/2024/03/abc123.pdf`)
- `scale`: 크롤링 시 사용한 지도 배율 (1200m, 1500m 등)
- `status`: 성공(success), 부분(partial), 실패(failed)
- `source`: 크롤링(crawl), 캐시(cache), 수동입력(manual)
- `crawled_at`: 크롤링 시각
- `expires_at`: 캐시 만료 시각 (NULL = 무제한 유효)
- `parsing_duration_ms`: 파싱 소요 시간 (성능 추적)

**데이터 예시**:
```json
{
    "id": 1,
    "address_id": 1,
    "pnu": "1135010400110010045",
    "present_addr": "서울시 강남구 역삼동 123-45",
    "present_class": "토지",
    "present_area": "1234.56",
    "jiga": "5600000",
    "jiga_year": "2024",
    "image_path": "images/2024/03/abc123.jpg",
    "status": "success",
    "source": "crawl",
    "crawled_at": "2024-03-10T12:34:56Z",
    "expires_at": "2024-04-09T12:34:56Z"
}
```

---

### 3. crawl_jobs - 배치 작업 관리

여러 주소를 포함한 크롤링 배치 작업을 관리합니다.

```sql
CREATE TABLE crawl_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',

    -- 진행 상황 추적
    total_count INTEGER NOT NULL DEFAULT 0,
    completed_count INTEGER NOT NULL DEFAULT 0,
    failed_count INTEGER NOT NULL DEFAULT 0,
    cached_count INTEGER NOT NULL DEFAULT 0,

    -- 설정
    scale TEXT NOT NULL DEFAULT '1200',
    save_pdf BOOLEAN NOT NULL DEFAULT 1,
    use_cache BOOLEAN NOT NULL DEFAULT 1,
    cache_expiry_days INTEGER NOT NULL DEFAULT 30,

    -- 설정 스냅샷 (작업 생성 시점의 설정 기록)
    settings_snapshot TEXT,

    -- 타임스탐프
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    paused_at DATETIME,
    finished_at DATETIME,

    CHECK (status IN ('pending', 'running', 'paused', 'completed', 'failed', 'cancelled')),
    CHECK (total_count >= 0),
    CHECK (completed_count >= 0 AND completed_count <= total_count),
    CHECK (failed_count >= 0),
    CHECK (cached_count >= 0),
    CHECK (cache_expiry_days IS NULL OR cache_expiry_days > 0 OR cache_expiry_days = -1)
);

-- 작업 상태별 조회 최적화
CREATE INDEX idx_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX idx_crawl_jobs_created_at ON crawl_jobs(created_at DESC);
CREATE INDEX idx_crawl_jobs_finished_at ON crawl_jobs(finished_at DESC);

-- 활성 작업 조회
CREATE INDEX idx_crawl_jobs_active
    ON crawl_jobs(started_at DESC)
    WHERE status IN ('running', 'paused');
```

**컬럼 설명**:
- `name`: 작업명 (예: "2024-03 강남구 조사")
- `status`: pending(대기) → running(실행) → paused(일시정지) → completed(완료) 또는 failed(실패) 또는 cancelled(취소)
- `total_count`: 총 항목 수
- `completed_count`: 완료된 항목 수
- `failed_count`: 실패한 항목 수
- `cached_count`: 캐시에서 가져온 항목 수
- `cache_expiry_days`: 캐시 유효기간 (일 수, -1 = 무제한)
- `settings_snapshot`: JSON 형식의 작업 생성 시점 설정 기록
- `started_at`: 작업 시작 시각
- `paused_at`: 마지막 일시정지 시각
- `finished_at`: 작업 완료 시각

**데이터 예시**:
```json
{
    "id": 1,
    "name": "2024-03-강남구-조사-001",
    "status": "running",
    "total_count": 50,
    "completed_count": 15,
    "failed_count": 2,
    "cached_count": 5,
    "cache_expiry_days": 30,
    "settings_snapshot": "{\"scale\": \"1200\", \"save_pdf\": true, \"headless\": true}",
    "created_at": "2024-03-10T10:00:00Z",
    "started_at": "2024-03-10T10:05:00Z"
}
```

**진행 상황 계산**:
```
완료율 = (completed_count + failed_count) / total_count * 100
캐시 적중율 = cached_count / completed_count * 100
에러율 = failed_count / total_count * 100
```

---

### 4. job_items - 작업 항목 상세

각 배치 작업에 포함된 개별 주소의 처리 상태를 추적합니다.

```sql
CREATE TABLE job_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    address_id INTEGER NOT NULL,
    result_id INTEGER,

    status TEXT NOT NULL DEFAULT 'pending',
    sort_order INTEGER NOT NULL,
    error_message TEXT,

    started_at DATETIME,
    finished_at DATETIME,

    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (address_id) REFERENCES addresses(id) ON DELETE CASCADE,
    FOREIGN KEY (result_id) REFERENCES crawl_results(id) ON DELETE SET NULL,
    CHECK (status IN ('pending', 'running', 'success', 'failed', 'skipped', 'cached')),
    UNIQUE(job_id, address_id),
    UNIQUE(job_id, sort_order)
);

-- 작업별 항목 조회 최적화
CREATE INDEX idx_job_items_job_id ON job_items(job_id);
CREATE INDEX idx_job_items_status ON job_items(job_id, status);
CREATE INDEX idx_job_items_sort_order ON job_items(job_id, sort_order);
CREATE INDEX idx_job_items_address_id ON job_items(address_id);
```

**컬럼 설명**:
- `job_id`: 소속 크롤링 작업
- `address_id`: 크롤링할 주소
- `result_id`: 크롤링 결과 (크롤링 후에 할당)
- `status`: pending(대기) → running(실행 중) → success/failed/cached/skipped
- `sort_order`: 작업 내 처리 순서 (1부터 시작)
- `error_message`: 실패 시 에러 메시지
- `started_at`, `finished_at`: 해당 항목의 처리 시각

**데이터 예시**:
```json
{
    "id": 1,
    "job_id": 1,
    "address_id": 1,
    "result_id": 1,
    "status": "success",
    "sort_order": 1,
    "started_at": "2024-03-10T10:05:30Z",
    "finished_at": "2024-03-10T10:15:45Z"
}
```

---

### 5. settings - 애플리케이션 설정

사용자 설정 및 애플리케이션 상태를 저장합니다.

```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (type IN ('string', 'number', 'boolean', 'json'))
);

-- 설정 값 인덱스
CREATE INDEX idx_settings_type ON settings(type);
```

**기본 설정값 (초기 설정)**:

```sql
INSERT INTO settings (key, value, type, description) VALUES
-- 캐시 설정
('cache_expiry_days', '30', 'number', '기본 캐시 유효기간 (일 수)'),
('cache_mode', 'smart', 'string', '캐시 모드: never, always, smart'),

-- 크롤러 설정
('default_scale', '1200', 'string', '기본 지도 축척 (m)'),
('wait_time', '5', 'number', '페이지 로드 대기 시간 (초)'),
('headless_mode', 'true', 'boolean', '헤드리스 모드 사용 여부'),
('max_retries', '3', 'number', '실패 시 재시도 최대 횟수'),
('page_load_timeout', '30000', 'number', '페이지 로드 타임아웃 (밀리초)'),

-- 파일 설정
('images_dir', 'images', 'string', '이미지 저장 디렉토리'),
('pdfs_dir', 'pdfs', 'string', 'PDF 저장 디렉토리'),
('auto_save_interval', '5', 'number', '자동 저장 간격 (초)'),
('max_image_size_mb', '10', 'number', '이미지 최대 크기 (MB)'),

-- UI 설정
('theme', 'light', 'string', '테마: light, dark, auto'),
('language', 'ko', 'string', '언어 코드: ko, en'),
('window_width', '1200', 'number', '기본 창 너비 (픽셀)'),
('window_height', '800', 'number', '기본 창 높이 (픽셀)'),

-- 시스템 설정
('db_version', '1', 'number', '데이터베이스 스키마 버전'),
('app_version', '1.0.0', 'string', '애플리케이션 버전'),
('last_backup_at', NULL, 'string', '마지막 백업 시각 (ISO 8601)'),
('enable_telemetry', 'false', 'boolean', '사용량 통계 수집 여부');
```

**컬럼 설명**:
- `key`: 설정 키 (기본값 소문자, 언더스코어 분리)
- `value`: 설정 값 (TEXT로 저장, type으로 구분)
- `type`: 데이터 타입 (string, number, boolean, json)
- `description`: 설정 설명
- `updated_at`: 마지막 수정 시각

**설정 읽기 Rust 코드 예시**:
```rust
fn get_setting<T: FromStr>(db: &Connection, key: &str) -> Result<T> {
    let (value, setting_type): (String, String) =
        db.query_row(
            "SELECT value, type FROM settings WHERE key = ?1",
            [key],
            |row| Ok((row.get(0)?, row.get(1)?))
        )?;

    match setting_type.as_str() {
        "number" => value.parse().map_err(|_| "Invalid number"),
        "boolean" => match value.as_str() {
            "true" | "1" => Ok(true),
            "false" | "0" => Ok(false),
            _ => Err("Invalid boolean")
        },
        _ => Ok(value)
    }
}
```

---

### 6. crawl_logs - 크롤링 로그

디버깅 및 감시용 상세 로그를 저장합니다.

```sql
CREATE TABLE crawl_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    job_item_id INTEGER,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (job_item_id) REFERENCES job_items(id) ON DELETE CASCADE,
    CHECK (level IN ('debug', 'info', 'warn', 'error'))
);

-- 로그 조회 최적화
CREATE INDEX idx_crawl_logs_job_id ON crawl_logs(job_id);
CREATE INDEX idx_crawl_logs_job_item_id ON crawl_logs(job_item_id);
CREATE INDEX idx_crawl_logs_level ON crawl_logs(level);
CREATE INDEX idx_crawl_logs_created_at ON crawl_logs(created_at DESC);

-- 최근 로그 조회
CREATE INDEX idx_crawl_logs_recent
    ON crawl_logs(created_at DESC)
    WHERE level IN ('warn', 'error');
```

**로그 수준 가이드**:
- `debug`: 개발자 디버깅 정보 (선택적 저장)
- `info`: 일반 정보 (크롤링 시작, 완료 등)
- `warn`: 경고 (이미지 다운로드 실패, 일부 필드 누락 등)
- `error`: 에러 (주소 검색 실패, 타임아웃 등)

**데이터 예시**:
```json
{
    "id": 1,
    "job_id": 1,
    "job_item_id": 1,
    "level": "info",
    "message": "주소 크롤링 시작: 서울시 강남구 역삼동 123-45",
    "created_at": "2024-03-10T10:15:30Z"
}
```

**로그 테이션 (자동 정리)**:
```sql
-- 90일 이상 된 DEBUG 로그 삭제
DELETE FROM crawl_logs
WHERE level = 'debug'
  AND created_at < datetime('now', '-90 days');

-- 1년 이상 된 모든 로그 삭제
DELETE FROM crawl_logs
WHERE created_at < datetime('now', '-1 year');
```

---

## 인덱싱 전략

### 인덱스 분류

#### 1. 기본 인덱스 (Primary Key & Unique)
- 모든 테이블의 PRIMARY KEY는 자동으로 인덱싱
- UNIQUE 제약조건도 자동으로 인덱싱

#### 2. 조회 최적화 인덱스

| 테이블 | 인덱스 | 사용 쿼리 | 설명 |
|--------|--------|----------|------|
| addresses | (group_name) | 그룹별 주소 조회 | 배치 작업별 주소 그룹화 |
| addresses | (created_at DESC) | 최근 추가 주소 | 타임라인 보기 |
| crawl_results | (address_id) | 주소별 결과 조회 | 많은 조회에서 사용 |
| crawl_results | (status) | 상태별 결과 필터링 | 진행 상황 조회 |
| crawl_results | (crawled_at DESC) | 최신 크롤링 결과 | 타임라인 보기 |
| crawl_results | (expires_at) | 만료된 캐시 정리 | 캐시 유효성 검사 |

#### 3. 복합 인덱스 (성능 최적화)

**캐시 유효성 검사 최적화**:
```sql
CREATE INDEX idx_crawl_results_cache_check
    ON crawl_results(address_id, status, expires_at)
    WHERE status = 'success';
```
- 쿼리: 특정 주소의 유효한 캐시 찾기
- 이유: WHERE 절 조건 순서대로 인덱스 구성

**작업 항목 조회 최적화**:
```sql
CREATE INDEX idx_job_items_status
    ON job_items(job_id, status);
```
- 쿼리: 특정 작업의 상태별 항목 집계
- 이유: 작업별 진행 상황 추적에 자주 사용

#### 4. Partial 인덱스 (조건부)

**활성 작업만 인덱싱**:
```sql
CREATE INDEX idx_crawl_jobs_active
    ON crawl_jobs(started_at DESC)
    WHERE status IN ('running', 'paused');
```
- 이점: 활성 작업 조회만 최적화, 인덱스 크기 감소

**최근 에러 로그만 인덱싱**:
```sql
CREATE INDEX idx_crawl_logs_recent
    ON crawl_logs(created_at DESC)
    WHERE level IN ('warn', 'error');
```
- 이점: 에러 조회 빠르게, 로그 크기 관리

### 인덱스 유지보수

```sql
-- SQLite 인덱스 통계 업데이트 (쿼리 최적화)
ANALYZE;

-- 인덱스 상태 확인
SELECT * FROM sqlite_stat1;

-- 비효율적인 인덱스 찾기 (사용되지 않는 인덱스)
SELECT name FROM sqlite_master
WHERE type = 'index'
  AND name LIKE 'idx_%';
```

---

## 마이그레이션 전략

### 버전 관리

데이터베이스 스키마는 `settings` 테이블의 `db_version` 으로 관리합니다.

```
v1: 초기 스키마 (addresses, crawl_results, crawl_jobs, job_items, settings, crawl_logs)
v2: [미래 업데이트 예정] 예: search_history 테이블 추가
v3: [미래 업데이트 예정]
```

### 마이그레이션 파일 구조

```
migrations/
├── 001_initial_schema.sql      # v0 → v1: 초기 스키마 생성
├── 002_add_feature_x.sql       # v1 → v2: 새 기능 추가
└── README.md                   # 마이그레이션 가이드
```

### 001_initial_schema.sql - 초기 마이그레이션

```sql
-- SQLite 호환성 설정
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ===== addresses 테이블 =====
CREATE TABLE IF NOT EXISTS addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT NOT NULL UNIQUE COLLATE NOCASE,
    normalized_address TEXT,
    pnu TEXT UNIQUE,
    group_name TEXT,
    tags TEXT,
    memo TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (length(address) > 0),
    CHECK (pnu IS NULL OR length(pnu) = 19)
);

CREATE INDEX IF NOT EXISTS idx_addresses_group_name ON addresses(group_name);
CREATE INDEX IF NOT EXISTS idx_addresses_created_at ON addresses(created_at DESC);

-- ===== crawl_results 테이블 =====
CREATE TABLE IF NOT EXISTS crawl_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address_id INTEGER NOT NULL,
    pnu TEXT,
    present_addr TEXT,
    present_class TEXT,
    present_area TEXT,
    jiga TEXT,
    jiga_year TEXT,
    present_mark1 TEXT,
    present_mark2 TEXT,
    present_mark3 TEXT,
    image_path TEXT,
    image_filename TEXT,
    image_size_bytes INTEGER,
    image_downloaded_at DATETIME,
    pdf_path TEXT,
    pdf_filename TEXT,
    pdf_size_bytes INTEGER,
    pdf_downloaded_at DATETIME,
    scale TEXT NOT NULL DEFAULT '1200',
    status TEXT NOT NULL DEFAULT 'success',
    error_message TEXT,
    source TEXT NOT NULL DEFAULT 'crawl',
    crawled_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    parsing_duration_ms INTEGER,

    FOREIGN KEY (address_id) REFERENCES addresses(id) ON DELETE CASCADE,
    CHECK (status IN ('success', 'partial', 'failed')),
    CHECK (source IN ('crawl', 'cache', 'manual')),
    CHECK (scale IN ('1200', '1500', '2000', '3000')),
    CHECK (present_area IS NULL OR CAST(present_area AS REAL) > 0),
    CHECK (jiga IS NULL OR CAST(jiga AS REAL) >= 0)
);

CREATE INDEX IF NOT EXISTS idx_crawl_results_address_id ON crawl_results(address_id);
CREATE INDEX IF NOT EXISTS idx_crawl_results_status ON crawl_results(status);
CREATE INDEX IF NOT EXISTS idx_crawl_results_crawled_at ON crawl_results(crawled_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_results_expires_at ON crawl_results(expires_at);
CREATE INDEX IF NOT EXISTS idx_crawl_results_cache_check
    ON crawl_results(address_id, status, expires_at)
    WHERE status = 'success';
CREATE INDEX IF NOT EXISTS idx_crawl_results_address_latest
    ON crawl_results(address_id, crawled_at DESC);

-- ===== crawl_jobs 테이블 =====
CREATE TABLE IF NOT EXISTS crawl_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    total_count INTEGER NOT NULL DEFAULT 0,
    completed_count INTEGER NOT NULL DEFAULT 0,
    failed_count INTEGER NOT NULL DEFAULT 0,
    cached_count INTEGER NOT NULL DEFAULT 0,
    scale TEXT NOT NULL DEFAULT '1200',
    save_pdf BOOLEAN NOT NULL DEFAULT 1,
    use_cache BOOLEAN NOT NULL DEFAULT 1,
    cache_expiry_days INTEGER NOT NULL DEFAULT 30,
    settings_snapshot TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    paused_at DATETIME,
    finished_at DATETIME,

    CHECK (status IN ('pending', 'running', 'paused', 'completed', 'failed', 'cancelled')),
    CHECK (total_count >= 0),
    CHECK (completed_count >= 0 AND completed_count <= total_count),
    CHECK (failed_count >= 0),
    CHECK (cached_count >= 0),
    CHECK (cache_expiry_days IS NULL OR cache_expiry_days > 0 OR cache_expiry_days = -1)
);

CREATE INDEX IF NOT EXISTS idx_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_created_at ON crawl_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_finished_at ON crawl_jobs(finished_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_active
    ON crawl_jobs(started_at DESC)
    WHERE status IN ('running', 'paused');

-- ===== job_items 테이블 =====
CREATE TABLE IF NOT EXISTS job_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    address_id INTEGER NOT NULL,
    result_id INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',
    sort_order INTEGER NOT NULL,
    error_message TEXT,
    started_at DATETIME,
    finished_at DATETIME,

    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (address_id) REFERENCES addresses(id) ON DELETE CASCADE,
    FOREIGN KEY (result_id) REFERENCES crawl_results(id) ON DELETE SET NULL,
    CHECK (status IN ('pending', 'running', 'success', 'failed', 'skipped', 'cached')),
    UNIQUE(job_id, address_id),
    UNIQUE(job_id, sort_order)
);

CREATE INDEX IF NOT EXISTS idx_job_items_job_id ON job_items(job_id);
CREATE INDEX IF NOT EXISTS idx_job_items_status ON job_items(job_id, status);
CREATE INDEX IF NOT EXISTS idx_job_items_sort_order ON job_items(job_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_job_items_address_id ON job_items(address_id);

-- ===== settings 테이블 =====
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (type IN ('string', 'number', 'boolean', 'json'))
);

CREATE INDEX IF NOT EXISTS idx_settings_type ON settings(type);

-- 기본 설정값 초기화
INSERT OR IGNORE INTO settings (key, value, type, description) VALUES
('cache_expiry_days', '30', 'number', '기본 캐시 유효기간 (일 수)'),
('cache_mode', 'smart', 'string', '캐시 모드: never, always, smart'),
('default_scale', '1200', 'string', '기본 지도 축척 (m)'),
('wait_time', '5', 'number', '페이지 로드 대기 시간 (초)'),
('headless_mode', 'true', 'boolean', '헤드리스 모드 사용 여부'),
('max_retries', '3', 'number', '실패 시 재시도 최대 횟수'),
('page_load_timeout', '30000', 'number', '페이지 로드 타임아웃 (밀리초)'),
('images_dir', 'images', 'string', '이미지 저장 디렉토리'),
('pdfs_dir', 'pdfs', 'string', 'PDF 저장 디렉토리'),
('auto_save_interval', '5', 'number', '자동 저장 간격 (초)'),
('max_image_size_mb', '10', 'number', '이미지 최대 크기 (MB)'),
('theme', 'light', 'string', '테마: light, dark, auto'),
('language', 'ko', 'string', '언어 코드: ko, en'),
('window_width', '1200', 'number', '기본 창 너비 (픽셀)'),
('window_height', '800', 'number', '기본 창 높이 (픽셀)'),
('db_version', '1', 'number', '데이터베이스 스키마 버전'),
('app_version', '1.0.0', 'string', '애플리케이션 버전'),
('enable_telemetry', 'false', 'boolean', '사용량 통계 수집 여부');

-- ===== crawl_logs 테이블 =====
CREATE TABLE IF NOT EXISTS crawl_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    job_item_id INTEGER,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (job_item_id) REFERENCES job_items(id) ON DELETE CASCADE,
    CHECK (level IN ('debug', 'info', 'warn', 'error'))
);

CREATE INDEX IF NOT EXISTS idx_crawl_logs_job_id ON crawl_logs(job_id);
CREATE INDEX IF NOT EXISTS idx_crawl_logs_job_item_id ON crawl_logs(job_item_id);
CREATE INDEX IF NOT EXISTS idx_crawl_logs_level ON crawl_logs(level);
CREATE INDEX IF NOT EXISTS idx_crawl_logs_created_at ON crawl_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_logs_recent
    ON crawl_logs(created_at DESC)
    WHERE level IN ('warn', 'error');

-- 마이그레이션 완료 표시
UPDATE settings SET value = '1', updated_at = CURRENT_TIMESTAMP WHERE key = 'db_version';
```

### 마이그레이션 실행 (Rust 백엔드)

```rust
use rusqlite::{Connection, Result, TransactionBehavior};
use std::path::Path;

pub fn run_migrations(db_path: &Path) -> Result<()> {
    let mut conn = Connection::open(db_path)?;

    // 현재 버전 확인
    let current_version: i32 = conn.query_row(
        "SELECT COALESCE((SELECT value FROM settings WHERE key = 'db_version'), '0')",
        [],
        |row| Ok(row.get::<_, String>(0)?.parse().unwrap_or(0))
    )?;

    // 필요한 마이그레이션 실행
    if current_version < 1 {
        run_migration_001(&mut conn)?;
    }
    // if current_version < 2 {
    //     run_migration_002(&mut conn)?;
    // }

    Ok(())
}

fn run_migration_001(conn: &mut Connection) -> Result<()> {
    let tx = conn.transaction_with_behavior(TransactionBehavior::Deferred)?;

    // 001_initial_schema.sql 내용 실행
    let sql = include_str!("../../migrations/001_initial_schema.sql");
    tx.execute_batch(sql)?;

    tx.commit()?;
    println!("Migration 001 completed: Initial schema created");
    Ok(())
}
```

### 롤백 전략

SQLite는 자동 롤백을 지원하므로 마이그레이션 실패 시 자동으로 이전 상태로 복구됩니다.

```rust
fn run_migration_with_rollback(conn: &mut Connection) -> Result<()> {
    let tx = conn.transaction()?;

    // 마이그레이션 실행
    match execute_migration(&tx) {
        Ok(_) => tx.commit()?,
        Err(e) => {
            tx.rollback()?;  // 자동 롤백
            return Err(e);
        }
    }

    Ok(())
}
```

---

## 주요 쿼리

### 1. 캐시 유효성 검사 (가장 중요)

주소에 대한 유효한 캐시된 결과를 가져옵니다. `expires_at`이 현재 시간보다 늦은 경우만 반환합니다.

```sql
-- 단일 주소의 최신 유효한 캐시 확인
SELECT cr.* FROM crawl_results cr
WHERE cr.address_id = ?1
  AND cr.status = 'success'
  AND (cr.expires_at IS NULL OR cr.expires_at > datetime('now'))
ORDER BY cr.crawled_at DESC
LIMIT 1;
```

**매개변수**: `?1` = address_id

**반환**: 캐시된 결과 또는 NULL (캐시 없음)

**성능**: `idx_crawl_results_cache_check` 인덱스 사용

```rust
pub fn get_cached_result(conn: &Connection, address_id: i64) -> Result<Option<CrawlResult>> {
    conn.query_row(
        "SELECT cr.* FROM crawl_results cr
         WHERE cr.address_id = ?1
           AND cr.status = 'success'
           AND (cr.expires_at IS NULL OR cr.expires_at > datetime('now'))
         ORDER BY cr.crawled_at DESC
         LIMIT 1",
        [address_id],
        |row| {
            Ok(CrawlResult {
                id: row.get(0)?,
                address_id: row.get(1)?,
                // ... 나머지 필드
            })
        }
    ).optional()
}
```

---

### 2. 캐시 만료 시간 계산

캐시 유효기간을 기반으로 만료 시간을 계산합니다.

```sql
-- 캐시 만료 시간 계산
SELECT datetime('now', '+' || ?1 || ' days')
-- 또는
SELECT datetime(CURRENT_TIMESTAMP, '+' || ?1 || ' days')
```

**매개변수**: `?1` = cache_expiry_days (30, 60, 365, 또는 NULL)

**NULL 처리**: `cache_expiry_days = -1`일 경우 `expires_at = NULL` (무제한 유효)

```rust
pub fn calculate_expiry_datetime(cache_days: Option<i32>) -> Option<String> {
    match cache_days {
        Some(-1) | None => None,  // 무제한
        Some(days) => {
            let now = chrono::Local::now();
            let expiry = now + chrono::Duration::days(days as i64);
            Some(expiry.to_rfc3339())
        },
        _ => None
    }
}
```

---

### 3. 결과 검색 및 필터링

여러 조건으로 크롤링 결과를 검색합니다.

```sql
-- 기본 검색: 주소명 포함, 날짜 범위, 상태별
SELECT cr.*, a.address, a.group_name
FROM crawl_results cr
JOIN addresses a ON cr.address_id = a.id
WHERE 1=1
  AND (a.address LIKE '%' || ?1 || '%' OR a.normalized_address LIKE '%' || ?1 || '%')
  AND (cr.crawled_at >= datetime(?2) AND cr.crawled_at < datetime(?3, '+1 day'))
  AND (cr.status IN ('success', 'partial') OR ?4 IS NULL)
ORDER BY cr.crawled_at DESC
LIMIT ?5 OFFSET ?6;
```

**매개변수**:
- `?1` = 검색어 (주소)
- `?2` = 시작 날짜 (YYYY-MM-DD)
- `?3` = 종료 날짜 (YYYY-MM-DD)
- `?4` = 상태 필터 (선택사항)
- `?5` = 페이지 크기
- `?6` = 오프셋

**집계 쿼리** (페이지네이션용):

```sql
SELECT COUNT(*) as total
FROM crawl_results cr
JOIN addresses a ON cr.address_id = a.id
WHERE a.address LIKE '%' || ?1 || '%'
  AND cr.crawled_at >= datetime(?2)
  AND cr.crawled_at < datetime(?3, '+1 day');
```

```rust
pub struct SearchParams {
    pub keyword: String,
    pub start_date: String,  // YYYY-MM-DD
    pub end_date: String,
    pub status_filter: Option<String>,
    pub page: usize,
    pub page_size: usize,
}

pub fn search_results(
    conn: &Connection,
    params: &SearchParams
) -> Result<Vec<CrawlResult>> {
    let offset = (params.page - 1) * params.page_size;

    let mut stmt = conn.prepare(
        "SELECT cr.*, a.address FROM crawl_results cr
         JOIN addresses a ON cr.address_id = a.id
         WHERE a.address LIKE ?1
           AND cr.crawled_at >= datetime(?2)
           AND cr.crawled_at < datetime(?3, '+1 day')
         ORDER BY cr.crawled_at DESC
         LIMIT ?4 OFFSET ?5"
    )?;

    let results = stmt.query_map(
        rusqlite::params![
            format!("%{}%", params.keyword),
            params.start_date,
            params.end_date,
            params.page_size,
            offset
        ],
        |row| { /* ... */ }
    )?;

    Ok(results.collect::<Result<Vec<_>>>()?)
}
```

---

### 4. 작업 진행 상황 조회

특정 크롤링 작업의 진행 상황을 상세히 조회합니다.

```sql
-- 작업 전체 진행 상황
SELECT
    cj.id,
    cj.name,
    cj.status,
    cj.total_count,
    cj.completed_count,
    cj.failed_count,
    cj.cached_count,
    ROUND(100.0 * (cj.completed_count + cj.failed_count) / NULLIF(cj.total_count, 0), 1) as progress_percent,
    ROUND(100.0 * cj.cached_count / NULLIF(cj.completed_count, 0), 1) as cache_hit_rate,
    ROUND(100.0 * cj.failed_count / NULLIF(cj.total_count, 0), 1) as failure_rate,
    cj.created_at,
    cj.started_at,
    cj.finished_at,
    CAST((julianday(cj.finished_at) - julianday(cj.started_at)) * 24 * 60 AS INTEGER) as duration_minutes
FROM crawl_jobs cj
WHERE cj.id = ?1;
```

**매개변수**: `?1` = job_id

**상태별 항목 집계**:

```sql
-- 상태별 항목 수 집계
SELECT
    status,
    COUNT(*) as count
FROM job_items
WHERE job_id = ?1
GROUP BY status;
```

**응답 예시**:
```json
{
    "id": 1,
    "name": "2024-03-강남구-001",
    "status": "running",
    "total_count": 100,
    "completed_count": 45,
    "failed_count": 5,
    "cached_count": 20,
    "progress_percent": 50.0,
    "cache_hit_rate": 44.4,
    "failure_rate": 5.0,
    "duration_minutes": 32
}
```

---

### 5. 대시보드 통계

애플리케이션 전체 통계를 조회합니다.

```sql
-- 대시보드 통계
SELECT
    (SELECT COUNT(*) FROM addresses) as total_addresses,
    (SELECT COUNT(*) FROM crawl_results WHERE status = 'success') as successful_results,
    (SELECT COUNT(*) FROM crawl_results WHERE status = 'failed') as failed_results,
    (SELECT COUNT(*) FROM crawl_results WHERE status = 'success') * 100.0 /
        NULLIF((SELECT COUNT(*) FROM crawl_results), 0) as success_rate,
    (SELECT COUNT(*) FROM crawl_jobs WHERE status = 'completed') as completed_jobs,
    (SELECT COUNT(*) FROM crawl_jobs WHERE status IN ('running', 'paused')) as active_jobs,
    (SELECT AVG(parsing_duration_ms) FROM crawl_results) as avg_parsing_duration_ms,
    (SELECT SUM(CAST(image_size_bytes AS REAL)) / 1024 / 1024) as total_images_mb,
    (SELECT SUM(CAST(pdf_size_bytes AS REAL)) / 1024 / 1024) as total_pdfs_mb,
    (SELECT MAX(crawled_at) FROM crawl_results) as last_crawl_time;
```

**응답 예시**:
```json
{
    "total_addresses": 512,
    "successful_results": 489,
    "failed_results": 23,
    "success_rate": 95.5,
    "completed_jobs": 8,
    "active_jobs": 1,
    "avg_parsing_duration_ms": 2345,
    "total_images_mb": 1234.5,
    "total_pdfs_mb": 567.8,
    "last_crawl_time": "2024-03-10T12:45:30Z"
}
```

---

### 6. 데이터 내보내기 (Export)

모든 크롤링 결과를 CSV/JSON으로 내보낼 수 있도록 쿼리합니다.

```sql
-- 완전한 데이터 내보내기 (모든 필드 포함)
SELECT
    a.id as address_id,
    a.address,
    a.normalized_address,
    a.pnu,
    a.group_name,
    cr.id as result_id,
    cr.present_addr,
    cr.present_class,
    cr.present_area,
    cr.jiga,
    cr.jiga_year,
    cr.present_mark1,
    cr.present_mark2,
    cr.present_mark3,
    cr.image_path,
    cr.pdf_path,
    cr.scale,
    cr.status,
    cr.source,
    cr.crawled_at,
    cr.expires_at
FROM addresses a
LEFT JOIN crawl_results cr ON a.id = cr.address_id
WHERE cr.status = 'success' OR cr.id IS NULL
ORDER BY a.id, cr.crawled_at DESC;
```

**특정 날짜 범위 내보내기**:

```sql
SELECT
    a.address,
    a.pnu,
    cr.present_addr,
    cr.present_class,
    cr.present_area,
    cr.jiga,
    cr.crawled_at
FROM crawl_results cr
JOIN addresses a ON cr.address_id = a.id
WHERE cr.crawled_at >= datetime(?1)
  AND cr.crawled_at < datetime(?2, '+1 day')
  AND cr.status = 'success'
ORDER BY cr.crawled_at DESC;
```

---

### 7. 재크롤링 필요 주소 찾기

최근 결과가 없거나 캐시가 만료된 주소를 찾습니다.

```sql
-- 캐시가 만료되었거나 결과가 없는 주소
SELECT DISTINCT a.id, a.address
FROM addresses a
LEFT JOIN (
    SELECT address_id
    FROM crawl_results
    WHERE status = 'success'
      AND (expires_at IS NULL OR expires_at > datetime('now'))
) valid_cache ON a.id = valid_cache.address_id
WHERE valid_cache.address_id IS NULL
ORDER BY a.created_at;
```

**특정 그룹의 만료된 캐시 찾기**:

```sql
-- 그룹별 만료된 캐시 주소
SELECT a.id, a.address, MAX(cr.crawled_at) as last_crawl
FROM addresses a
LEFT JOIN crawl_results cr ON a.id = cr.address_id
WHERE a.group_name = ?1
  AND (cr.expires_at IS NULL OR cr.expires_at <= datetime('now'))
GROUP BY a.id
ORDER BY last_crawl ASC NULLS FIRST;
```

---

### 8. 페이지네이션 쿼리

대량의 데이터를 페이지 단위로 조회합니다.

```sql
-- 페이지네이션: 크롤링 결과 목록
SELECT
    cr.id,
    a.address,
    cr.present_addr,
    cr.present_class,
    cr.jiga,
    cr.status,
    cr.crawled_at,
    cr.source
FROM crawl_results cr
JOIN addresses a ON cr.address_id = a.id
ORDER BY cr.crawled_at DESC
LIMIT ?1 OFFSET ?2;
```

**매개변수**:
- `?1` = 페이지 크기 (예: 20)
- `?2` = 오프셋 (예: 페이지 1 = 0, 페이지 2 = 20)

**총 결과 수 조회**:

```sql
SELECT COUNT(*) as total FROM crawl_results;
```

---

### 9. 로그 쿼리

로그를 조회하고 관리합니다.

```sql
-- 특정 작업의 최근 로그
SELECT level, message, created_at
FROM crawl_logs
WHERE job_id = ?1
ORDER BY created_at DESC
LIMIT 100;
```

**에러 로그만 조회**:

```sql
-- 최근 에러 로그
SELECT job_id, job_item_id, message, created_at
FROM crawl_logs
WHERE level = 'error'
ORDER BY created_at DESC
LIMIT 50;
```

**로그 정리 (자동 실행)**:

```sql
-- 90일 이상 된 DEBUG 로그 삭제
DELETE FROM crawl_logs
WHERE level = 'debug'
  AND created_at < datetime('now', '-90 days');

-- 1년 이상 된 모든 로그 삭제
DELETE FROM crawl_logs
WHERE created_at < datetime('now', '-1 year');
```

---

## 데이터 무결성

### 외래키 제약조건 활성화

SQLite에서 외래키는 기본으로 비활성화되어 있으므로 명시적으로 활성화해야 합니다.

```sql
-- 데이터베이스 연결 직후 실행 (필수!)
PRAGMA foreign_keys = ON;
```

**Rust 초기화 코드**:

```rust
fn init_database(db_path: &Path) -> Result<Connection> {
    let conn = Connection::open(db_path)?;

    // 외래키 제약조건 활성화
    conn.execute("PRAGMA foreign_keys = ON", [])?;

    // WAL 모드 활성화 (동시성 개선)
    conn.execute("PRAGMA journal_mode = WAL", [])?;

    // 동기화 모드 설정 (NORMAL = 충돌 방지, 충돌 시 성능)
    conn.execute("PRAGMA synchronous = NORMAL", [])?;

    // 캐시 크기 설정 (성능 최적화)
    conn.execute("PRAGMA cache_size = -64000", [])?;  // 64MB

    // 자동 진공 활성화 (데이터베이스 크기 최적화)
    conn.execute("PRAGMA auto_vacuum = INCREMENTAL", [])?;
    conn.execute("PRAGMA incremental_vacuum(1000)", [])?;

    Ok(conn)
}
```

### 트랜잭션 패턴

배치 작업이나 다중 행 작업에는 트랜잭션을 사용합니다.

```rust
// 배치 주소 삽입
fn insert_batch_addresses(
    conn: &Connection,
    addresses: &[&str],
    group_name: &str
) -> Result<()> {
    let tx = conn.transaction()?;

    {
        let mut stmt = tx.prepare(
            "INSERT INTO addresses (address, group_name) VALUES (?1, ?2)"
        )?;

        for address in addresses {
            stmt.execute([address, &group_name])?;
        }
    }

    tx.commit()?;
    Ok(())
}
```

**트랜잭션 롤백** (에러 발생 시):

```rust
fn create_job_with_items(
    conn: &Connection,
    job_name: &str,
    address_ids: &[i64]
) -> Result<i64> {
    let tx = conn.transaction()?;

    // 작업 생성
    tx.execute(
        "INSERT INTO crawl_jobs (name, total_count) VALUES (?1, ?2)",
        [job_name, address_ids.len().to_string().as_str()]
    )?;

    let job_id: i64 = tx.last_insert_rowid();

    // 작업 항목 추가
    for (idx, addr_id) in address_ids.iter().enumerate() {
        match tx.execute(
            "INSERT INTO job_items (job_id, address_id, sort_order) VALUES (?1, ?2, ?3)",
            [job_id.to_string().as_str(), addr_id.to_string().as_str(), (idx+1).to_string().as_str()]
        ) {
            Ok(_) => {},
            Err(e) => {
                tx.rollback()?;  // 실패 시 모든 변경사항 롤백
                return Err(e);
            }
        }
    }

    tx.commit()?;
    Ok(job_id)
}
```

### 데이터 검증 규칙

**주소**:
- 길이: 1자 이상
- PNU: NULL 또는 정확히 19자리

**크롤 결과**:
- 면적(present_area): NULL 또는 > 0의 실수
- 지가(jiga): NULL 또는 >= 0의 실수

**작업**:
- `completed_count <= total_count`
- `failed_count <= total_count`
- `cache_expiry_days > 0` 또는 `-1` (무제한)

---

## 캐시 로직

### 캐시 전략

```
┌─────────────────────────┐
│  새로운 크롤링 요청     │
└────────────┬────────────┘
             │
        ┌────▼────┐
        │캐시 활성화?│
        └────┬────┘
       YES   │   NO
            │        └─────────────────┐
            │                          │
    ┌───────▼────────┐       ┌────────▼──────────┐
    │유효한 캐시 있음?│       │ 웹 크롤링 수행    │
    └───────┬────────┘       └────────┬──────────┘
       YES  │  NO                     │
            │    └──────────────┐     │
            │                  │     │
    ┌───────▼──────┐    ┌──────▼────────┐
    │캐시 반환     │    │결과 저장      │
    │(source=cache)│    │(source=crawl) │
    └──────────────┘    └──────┬────────┘
                               │
                        ┌──────▼──────────┐
                        │expires_at 계산  │
                        └─────────────────┘
```

### 캐시 확인 로직 (Rust)

```rust
pub async fn get_or_crawl_address(
    db: &Connection,
    address: &str,
    use_cache: bool,
    cache_expiry_days: Option<i32>
) -> Result<CrawlResult> {
    // 1. 주소 ID 조회 또는 생성
    let address_id = get_or_create_address(db, address)?;

    // 2. 캐시 확인
    if use_cache {
        if let Some(cached) = get_cached_result(db, address_id)? {
            log::info!("캐시 사용: {}", address);
            return Ok(cached);
        }
    }

    // 3. 웹 크롤링
    log::info!("웹 크롤링 시작: {}", address);
    let crawl_result = perform_web_crawl(address).await?;

    // 4. 만료 시간 계산
    let expires_at = calculate_expiry_datetime(cache_expiry_days);

    // 5. 결과 저장
    save_crawl_result(db, address_id, crawl_result, expires_at)?;

    Ok(crawl_result)
}

fn calculate_expiry_datetime(cache_expiry_days: Option<i32>) -> Option<String> {
    match cache_expiry_days {
        Some(-1) => None,  // 무제한
        Some(days) => {
            let expiry = chrono::Local::now() + chrono::Duration::days(days as i64);
            Some(expiry.format("%Y-%m-%d %H:%M:%S").to_string())
        },
        None => None
    }
}
```

### 캐시 모드

`settings` 테이블의 `cache_mode` 값:

| 모드 | 동작 | 사용 사례 |
|------|------|---------|
| `never` | 캐시 미사용, 항상 웹 크롤링 | 최신 정보 필요 |
| `always` | 캐시 사용, 유효하면 웹 크롤링 안 함 | 빠른 처리, 오래된 데이터 용인 |
| `smart` | 캐시 사용, 실패 시 웹 크롤링 | 기본 모드 |

```rust
pub async fn get_result_smart_cache(
    db: &Connection,
    address: &str,
    cache_mode: &str
) -> Result<CrawlResult> {
    match cache_mode {
        "never" => perform_web_crawl(address).await,
        "always" => {
            if let Some(cached) = get_cached_result(db, get_address_id(db, address)?)? {
                Ok(cached)
            } else {
                perform_web_crawl(address).await
            }
        },
        "smart" => {
            match get_cached_result(db, get_address_id(db, address)?)? {
                Some(cached) => Ok(cached),
                None => perform_web_crawl(address).await
            }
        },
        _ => Err("Unknown cache mode".into())
    }
}
```

### 캐시 유효성 검사 SQL

```sql
-- 만료된 캐시 확인
SELECT COUNT(*) as expired_count
FROM crawl_results
WHERE status = 'success'
  AND expires_at IS NOT NULL
  AND expires_at <= datetime('now');
```

**캐시 만료 처리 (배치)**:

```sql
-- 만료된 캐시 상태 업데이트
UPDATE crawl_results
SET status = 'expired', source = 'cache'
WHERE expires_at <= datetime('now')
  AND status = 'success';
```

---

## 성능 고려사항

### 1. 인덱스 최적화

**자주 사용되는 쿼리 예**:

```rust
// 캐시 확인 (매우 자주)
SELECT * FROM crawl_results
WHERE address_id = ? AND status = 'success' AND expires_at > NOW()

// 인덱스: idx_crawl_results_cache_check
// 효과: O(log n) → O(1) 근처

// 작업 진행 상황 (자주)
SELECT COUNT(*) FROM job_items
WHERE job_id = ? AND status = ?

// 인덱스: idx_job_items_status
```

### 2. 쿼리 최적화

**EXPLAIN QUERY PLAN**을 사용하여 쿼리 계획 확인:

```sql
EXPLAIN QUERY PLAN
SELECT cr.* FROM crawl_results cr
WHERE cr.address_id = 1
  AND cr.status = 'success'
  AND (cr.expires_at IS NULL OR cr.expires_at > datetime('now'));
```

**좋은 쿼리 계획**: SEARCH crawl_results USING idx_crawl_results_cache_check

**나쁜 쿼리 계획**: SCAN crawl_results (테이블 전체 스캔)

### 3. 데이터베이스 크기 관리

```sql
-- 데이터베이스 크기 확인
SELECT page_count * page_size as size_bytes FROM pragma_page_count(), pragma_page_size();

-- 테이블별 크기
SELECT
    name,
    (SELECT COUNT(*) * 8 FROM crawl_results) as approx_size_kb
FROM sqlite_master
WHERE type = 'table';

-- 자동 진공 실행 (여유 공간 회수)
VACUUM;

-- WAL 체크포인트 (WAL 파일 크기 최소화)
PRAGMA wal_checkpoint(TRUNCATE);
```

### 4. 동시 접근 처리

SQLite는 기본적으로 한 번에 하나의 쓰기 트랜잭션만 허용합니다. WAL 모드로 읽기/쓰기 동시성을 개선합니다.

```sql
-- WAL 모드 활성화 (Tauri 백엔드 초기화 시)
PRAGMA journal_mode = WAL;
PRAGMA wal_autocheckpoint = 1000;  -- 1000개 페이지마다 자동 체크포인트
```

**동시성 처리 (Rust)**:

```rust
use std::sync::Mutex;

// 데이터베이스 연결을 Mutex로 보호
let db = Mutex::new(Connection::open("eumcrawl.db")?);

// 크롤링 작업
tauri::async_runtime::spawn(async move {
    let conn = db.lock().unwrap();
    // 데이터베이스 작업 수행
});
```

### 5. 배치 작업 성능

대량 데이터 삽입:

```rust
// 느린 방법 (1000회 INSERT)
for address in addresses {
    conn.execute(
        "INSERT INTO addresses (address) VALUES (?1)",
        [address]
    )?;
}

// 빠른 방법 (1회 트랜잭션)
let tx = conn.transaction()?;
{
    let mut stmt = tx.prepare("INSERT INTO addresses (address) VALUES (?1)")?;
    for address in addresses {
        stmt.execute([address])?;
    }
}
tx.commit()?;
```

성능 개선: **10배 이상** (1000개 항목 기준)

---

## 백업 및 복구

### 자동 백업

매일 자정에 자동 백업을 생성합니다.

```rust
use chrono::Local;
use std::fs;

pub fn auto_backup(db_path: &Path, backup_dir: &Path) -> Result<()> {
    // 백업 디렉토리 생성
    fs::create_dir_all(backup_dir)?;

    // 백업 파일명: eumcrawl_YYYY-MM-DD_HHMMSS.db
    let timestamp = Local::now().format("%Y-%m-%d_%H%M%S");
    let backup_path = backup_dir.join(format!("eumcrawl_{}.db", timestamp));

    // 데이터베이스 백업
    let conn = Connection::open(db_path)?;
    let backup_conn = Connection::open(&backup_path)?;

    conn.backup(
        rusqlite::backup::DatabaseName::Main,
        &backup_conn,
        rusqlite::backup::DatabaseName::Main
    )?;

    println!("백업 완료: {}", backup_path.display());

    // 오래된 백업 삭제 (30일 이상)
    cleanup_old_backups(backup_dir, 30)?;

    Ok(())
}

fn cleanup_old_backups(backup_dir: &Path, days: u64) -> Result<()> {
    let cutoff = chrono::Local::now() - chrono::Duration::days(days as i64);

    for entry in fs::read_dir(backup_dir)? {
        let entry = entry?;
        let path = entry.path();

        if path.extension().map_or(false, |ext| ext == "db") {
            if let Ok(metadata) = fs::metadata(&path) {
                if let Ok(modified) = metadata.modified() {
                    if modified < cutoff.into() {
                        fs::remove_file(&path)?;
                        println!("오래된 백업 삭제: {}", path.display());
                    }
                }
            }
        }
    }

    Ok(())
}
```

### 수동 백업

사용자가 언제든지 수동 백업을 생성할 수 있습니다.

```rust
// Tauri 커맨드
#[tauri::command]
pub fn backup_database(db_path: String, backup_path: String) -> Result<String> {
    let from = Path::new(&db_path);
    let to = Path::new(&backup_path);

    fs::copy(from, to)?;

    Ok(format!("백업 완료: {}", backup_path))
}
```

### 복구

손상된 데이터베이스를 백업에서 복구합니다.

```rust
pub fn restore_from_backup(backup_path: &Path, target_path: &Path) -> Result<()> {
    if !backup_path.exists() {
        return Err("백업 파일을 찾을 수 없습니다".into());
    }

    // 기존 데이터베이스 백업
    let current_backup = target_path.with_extension("db.corrupted");
    fs::rename(target_path, &current_backup)?;

    // 백업에서 복구
    fs::copy(backup_path, target_path)?;

    println!("복구 완료: {} → {}", backup_path.display(), target_path.display());
    println!("손상된 데이터베이스 백업: {}", current_backup.display());

    Ok(())
}
```

### 무결성 검사

데이터베이스 무결성을 주기적으로 확인합니다.

```sql
-- 데이터베이스 무결성 검사
PRAGMA integrity_check;

-- 상세 검사 (시간 소요)
PRAGMA integrity_check(10000);

-- 검사 결과: 'ok' 또는 에러 메시지
```

**Rust 래퍼**:

```rust
pub fn check_database_integrity(conn: &Connection) -> Result<bool> {
    let result: String = conn.query_row(
        "PRAGMA integrity_check",
        [],
        |row| row.get(0)
    )?;

    if result == "ok" {
        println!("데이터베이스 무결성 확인: OK");
        Ok(true)
    } else {
        eprintln!("데이터베이스 무결성 문제: {}", result);
        Ok(false)
    }
}
```

---

## ER 다이어그램

### 텍스트 기반 ER 다이어그램

```
┌──────────────────────┐
│      addresses       │
├──────────────────────┤
│ PK  id               │
│     address (UQ)     │
│     normalized_addr  │
│     pnu (UQ)         │
│     group_name       │
│     tags (JSON)      │
│     memo             │
│     created_at       │
│     updated_at       │
└──────────────────────┘
         │
         │ FK (1:N)
         │
    ┌────▼─────────────────────────────────────┐
    │         crawl_results                     │
    ├─────────────────────────────────────────┤
    │ PK  id                                   │
    │ FK  address_id → addresses(id)           │
    │     pnu                                  │
    │     present_addr, present_class, etc.   │
    │     image_path, pdf_path                │
    │     status (success/partial/failed)     │
    │     source (crawl/cache/manual)         │
    │     crawled_at, expires_at              │
    └────▲──────────────────────────────────┘
         │
         │ FK (1:1)
         │
┌──────┴─────────────────────────────────────┐
│         job_items                          │
├────────────────────────────────────────────┤
│ PK  id                                     │
│ FK  job_id → crawl_jobs(id)               │
│ FK  address_id → addresses(id)            │
│ FK  result_id → crawl_results(id)         │
│     status (pending/running/success...)   │
│     sort_order                            │
│     started_at, finished_at               │
└────▲──────────────────────────────────────┘
     │
     │ FK (1:N)
     │
┌────┴──────────────────────┐
│    crawl_jobs             │
├───────────────────────────┤
│ PK  id                    │
│     name                  │
│     status                │
│     total_count           │
│     completed_count       │
│     failed_count          │
│     cached_count          │
│     cache_expiry_days     │
│     settings_snapshot     │
│     created_at            │
│     started_at            │
│     finished_at           │
└───────────────────────────┘


┌─────────────────────────────┐
│      crawl_logs             │
├─────────────────────────────┤
│ PK  id                      │
│ FK  job_id (nullable)       │
│ FK  job_item_id (nullable)  │
│     level                   │
│     message                 │
│     created_at              │
└─────────────────────────────┘


┌──────────────────────────┐
│      settings            │
├──────────────────────────┤
│ PK  key                  │
│     value                │
│     type                 │
│     description          │
│     updated_at           │
└──────────────────────────┘
```

### 관계 요약

| 관계 | 타입 | 참고 |
|------|------|------|
| addresses ← crawl_results | 1:N | 한 주소는 여러 크롤링 결과를 가짐 |
| crawl_jobs ← job_items | 1:N | 한 작업은 여러 항목을 포함 |
| addresses ← job_items | 1:N | 한 주소는 여러 작업에서 사용 가능 |
| crawl_results ← job_items | 1:1 | 작업 항목은 최대 1개의 결과를 가짐 |
| crawl_jobs ← crawl_logs | 1:N | 한 작업은 여러 로그 항목을 가짐 |
| job_items ← crawl_logs | 1:N | 한 작업 항목은 여러 로그를 가짐 |

---

## 부록: SQL 초기화 스크립트 전체 코드

### init_db.sql (완전한 초기화)

```sql
-- SQLite 호환성 설정
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;
PRAGMA auto_vacuum = INCREMENTAL;

-- ===== addresses 테이블 =====
CREATE TABLE IF NOT EXISTS addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT NOT NULL UNIQUE COLLATE NOCASE,
    normalized_address TEXT,
    pnu TEXT UNIQUE,
    group_name TEXT,
    tags TEXT,
    memo TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (length(address) > 0),
    CHECK (pnu IS NULL OR length(pnu) = 19)
);

CREATE INDEX IF NOT EXISTS idx_addresses_group_name ON addresses(group_name);
CREATE INDEX IF NOT EXISTS idx_addresses_created_at ON addresses(created_at DESC);

-- ===== crawl_results 테이블 =====
CREATE TABLE IF NOT EXISTS crawl_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address_id INTEGER NOT NULL,
    pnu TEXT,
    present_addr TEXT,
    present_class TEXT,
    present_area TEXT,
    jiga TEXT,
    jiga_year TEXT,
    present_mark1 TEXT,
    present_mark2 TEXT,
    present_mark3 TEXT,
    image_path TEXT,
    image_filename TEXT,
    image_size_bytes INTEGER,
    image_downloaded_at DATETIME,
    pdf_path TEXT,
    pdf_filename TEXT,
    pdf_size_bytes INTEGER,
    pdf_downloaded_at DATETIME,
    scale TEXT NOT NULL DEFAULT '1200',
    status TEXT NOT NULL DEFAULT 'success',
    error_message TEXT,
    source TEXT NOT NULL DEFAULT 'crawl',
    crawled_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    parsing_duration_ms INTEGER,

    FOREIGN KEY (address_id) REFERENCES addresses(id) ON DELETE CASCADE,
    CHECK (status IN ('success', 'partial', 'failed')),
    CHECK (source IN ('crawl', 'cache', 'manual')),
    CHECK (scale IN ('1200', '1500', '2000', '3000')),
    CHECK (present_area IS NULL OR CAST(present_area AS REAL) > 0),
    CHECK (jiga IS NULL OR CAST(jiga AS REAL) >= 0)
);

CREATE INDEX IF NOT EXISTS idx_crawl_results_address_id ON crawl_results(address_id);
CREATE INDEX IF NOT EXISTS idx_crawl_results_status ON crawl_results(status);
CREATE INDEX IF NOT EXISTS idx_crawl_results_crawled_at ON crawl_results(crawled_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_results_expires_at ON crawl_results(expires_at);
CREATE INDEX IF NOT EXISTS idx_crawl_results_cache_check
    ON crawl_results(address_id, status, expires_at)
    WHERE status = 'success';
CREATE INDEX IF NOT EXISTS idx_crawl_results_address_latest
    ON crawl_results(address_id, crawled_at DESC);

-- ===== crawl_jobs 테이블 =====
CREATE TABLE IF NOT EXISTS crawl_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    total_count INTEGER NOT NULL DEFAULT 0,
    completed_count INTEGER NOT NULL DEFAULT 0,
    failed_count INTEGER NOT NULL DEFAULT 0,
    cached_count INTEGER NOT NULL DEFAULT 0,
    scale TEXT NOT NULL DEFAULT '1200',
    save_pdf BOOLEAN NOT NULL DEFAULT 1,
    use_cache BOOLEAN NOT NULL DEFAULT 1,
    cache_expiry_days INTEGER NOT NULL DEFAULT 30,
    settings_snapshot TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    paused_at DATETIME,
    finished_at DATETIME,

    CHECK (status IN ('pending', 'running', 'paused', 'completed', 'failed', 'cancelled')),
    CHECK (total_count >= 0),
    CHECK (completed_count >= 0 AND completed_count <= total_count),
    CHECK (failed_count >= 0),
    CHECK (cached_count >= 0),
    CHECK (cache_expiry_days IS NULL OR cache_expiry_days > 0 OR cache_expiry_days = -1)
);

CREATE INDEX IF NOT EXISTS idx_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_created_at ON crawl_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_finished_at ON crawl_jobs(finished_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_active
    ON crawl_jobs(started_at DESC)
    WHERE status IN ('running', 'paused');

-- ===== job_items 테이블 =====
CREATE TABLE IF NOT EXISTS job_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    address_id INTEGER NOT NULL,
    result_id INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',
    sort_order INTEGER NOT NULL,
    error_message TEXT,
    started_at DATETIME,
    finished_at DATETIME,

    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (address_id) REFERENCES addresses(id) ON DELETE CASCADE,
    FOREIGN KEY (result_id) REFERENCES crawl_results(id) ON DELETE SET NULL,
    CHECK (status IN ('pending', 'running', 'success', 'failed', 'skipped', 'cached')),
    UNIQUE(job_id, address_id),
    UNIQUE(job_id, sort_order)
);

CREATE INDEX IF NOT EXISTS idx_job_items_job_id ON job_items(job_id);
CREATE INDEX IF NOT EXISTS idx_job_items_status ON job_items(job_id, status);
CREATE INDEX IF NOT EXISTS idx_job_items_sort_order ON job_items(job_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_job_items_address_id ON job_items(address_id);

-- ===== settings 테이블 =====
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (type IN ('string', 'number', 'boolean', 'json'))
);

CREATE INDEX IF NOT EXISTS idx_settings_type ON settings(type);

-- 기본 설정값 초기화
INSERT OR IGNORE INTO settings (key, value, type, description) VALUES
('cache_expiry_days', '30', 'number', '기본 캐시 유효기간 (일 수)'),
('cache_mode', 'smart', 'string', '캐시 모드: never, always, smart'),
('default_scale', '1200', 'string', '기본 지도 축척 (m)'),
('wait_time', '5', 'number', '페이지 로드 대기 시간 (초)'),
('headless_mode', 'true', 'boolean', '헤드리스 모드 사용 여부'),
('max_retries', '3', 'number', '실패 시 재시도 최대 횟수'),
('page_load_timeout', '30000', 'number', '페이지 로드 타임아웃 (밀리초)'),
('images_dir', 'images', 'string', '이미지 저장 디렉토리'),
('pdfs_dir', 'pdfs', 'string', 'PDF 저장 디렉토리'),
('auto_save_interval', '5', 'number', '자동 저장 간격 (초)'),
('max_image_size_mb', '10', 'number', '이미지 최대 크기 (MB)'),
('theme', 'light', 'string', '테마: light, dark, auto'),
('language', 'ko', 'string', '언어 코드: ko, en'),
('window_width', '1200', 'number', '기본 창 너비 (픽셀)'),
('window_height', '800', 'number', '기본 창 높이 (픽셀)'),
('db_version', '1', 'number', '데이터베이스 스키마 버전'),
('app_version', '1.0.0', 'string', '애플리케이션 버전'),
('enable_telemetry', 'false', 'boolean', '사용량 통계 수집 여부');

-- ===== crawl_logs 테이블 =====
CREATE TABLE IF NOT EXISTS crawl_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    job_item_id INTEGER,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (job_item_id) REFERENCES job_items(id) ON DELETE CASCADE,
    CHECK (level IN ('debug', 'info', 'warn', 'error'))
);

CREATE INDEX IF NOT EXISTS idx_crawl_logs_job_id ON crawl_logs(job_id);
CREATE INDEX IF NOT EXISTS idx_crawl_logs_job_item_id ON crawl_logs(job_item_id);
CREATE INDEX IF NOT EXISTS idx_crawl_logs_level ON crawl_logs(level);
CREATE INDEX IF NOT EXISTS idx_crawl_logs_created_at ON crawl_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_logs_recent
    ON crawl_logs(created_at DESC)
    WHERE level IN ('warn', 'error');
```

---

## 결론

이 데이터베이스 설계는 다음 특성을 갖습니다:

✅ **정규화**: 3NF 준수로 데이터 중복 최소화
✅ **성능**: 자주 사용되는 쿼리에 최적화된 인덱싱
✅ **확장성**: 향후 기능 추가를 고려한 유연한 스키마
✅ **안정성**: 외래키 제약조건과 트랜잭션으로 데이터 무결성 보장
✅ **캐시 관리**: 효율적인 캐시 유효성 검사 및 만료 처리
✅ **감시**: 상세한 로깅과 통계 추적

이 설계를 기반으로 Tauri v2 데스크톱 애플리케이션을 구현할 수 있습니다.
