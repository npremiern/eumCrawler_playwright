---
name: eumcrawl-api-contract
description: >
  API/IPC contract quick reference for EUM Crawler Desktop.
  Tauri IPC command signatures, event types, sidecar protocol,
  and TypeScript type definitions in compact form.
user-invocable: false
metadata:
  version: "1.0.0"
  category: "domain"
  status: "active"
  updated: "2026-03-10"
  tags: "api, ipc, tauri, contract, types, events, sidecar, protocol"

progressive_disclosure:
  enabled: true
  level1_tokens: 100
  level2_tokens: 5000

triggers:
  keywords: ["api", "ipc", "command", "invoke", "event", "contract", "type", "interface"]
  agents: ["eumcrawl-tauri-backend", "eumcrawl-svelte-frontend", "eumcrawl-orchestrator"]
---

# API/IPC Contract Quick Reference

Full specification: `docs/design/05-API.md`

## TypeScript Types

```typescript
// Common
interface PaginatedResult<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Address
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

// Crawl Result
interface CrawlResult {
  id: number;
  address_id: number;
  address: string;  // joined from addresses table
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
  status: 'success' | 'failed' | 'partial';
  error_message: string | null;
  source: 'crawl' | 'cache';
  crawled_at: string;
  expires_at: string | null;
}

// Crawl Job
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

// Job Item
interface JobItem {
  id: number;
  job_id: number;
  address_id: number;
  address: string;  // joined
  result_id: number | null;
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped' | 'cached';
  sort_order: number;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
}

// Dashboard
interface DashboardStats {
  total_addresses: number;
  total_results: number;
  success_count: number;
  failed_count: number;
  cached_count: number;
  today_count: number;
  success_rate: number;
}

// Settings
type SettingValue = { key: string; value: string; type: 'string' | 'number' | 'boolean' | 'json' };

// Import
interface ImportResult {
  imported: number;
  skipped: number;
  errors: string[];
}

// Cache
interface CacheStatus {
  has_cache: boolean;
  result: CrawlResult | null;
  expires_at: string | null;
}
```

## IPC Commands (invoke name → return type)

### Address
| Command | Params | Returns |
|---------|--------|---------|
| `get_addresses` | page, per_page, search?, group?, sort_by?, sort_order? | `PaginatedResult<Address>` |
| `add_address` | address, group_name?, tags?, memo? | `Address` |
| `update_address` | id, data | `Address` |
| `delete_addresses` | ids: number[] | `{ deleted: number }` |
| `import_addresses_from_excel` | file_path, start_row, address_column, group_name?, duplicate_strategy | `ImportResult` |
| `get_address_groups` | (none) | `string[]` |

### Job
| Command | Params | Returns |
|---------|--------|---------|
| `create_crawl_job` | name, address_ids, scale, save_pdf, use_cache, cache_expiry_days | `CrawlJob` |
| `start_crawl_job` | job_id | `void` |
| `pause_crawl_job` | job_id | `void` |
| `resume_crawl_job` | job_id | `void` |
| `stop_crawl_job` | job_id | `void` |
| `get_crawl_jobs` | page, per_page, status? | `PaginatedResult<CrawlJob>` |
| `get_crawl_job` | job_id | `CrawlJob` |
| `delete_crawl_job` | job_id | `void` |
| `get_job_items` | job_id, page, per_page, status? | `PaginatedResult<JobItem>` |

### Result
| Command | Params | Returns |
|---------|--------|---------|
| `get_results` | page, per_page, search?, date_from?, date_to?, status?, source?, scale? | `PaginatedResult<CrawlResult>` |
| `get_result` | id | `CrawlResult` |
| `get_result_history` | address_id | `CrawlResult[]` |
| `delete_results` | ids: number[] | `{ deleted: number }` |
| `recrawl_results` | ids: number[] | `CrawlJob` |
| `check_cache` | address_id | `CacheStatus` |

### Export
| Command | Params | Returns |
|---------|--------|---------|
| `export_to_excel` | result_ids?, filters?, columns, include_images, output_path | `string` (path) |
| `export_to_csv` | result_ids?, filters?, columns, output_path | `string` (path) |

### Settings
| Command | Params | Returns |
|---------|--------|---------|
| `get_settings` | (none) | `Record<string, SettingValue>` |
| `get_setting` | key | `SettingValue` |
| `update_setting` | key, value | `void` |
| `update_settings` | settings: Record<string, string> | `void` |
| `reset_settings` | (none) | `void` |

### System
| Command | Params | Returns |
|---------|--------|---------|
| `open_file` | file_path | `void` |
| `open_folder` | folder_path | `void` |
| `backup_database` | output_path | `void` |
| `restore_database` | backup_path | `void` |
| `clear_all_cache` | (none) | `{ deleted: number }` |
| `get_dashboard_stats` | (none) | `DashboardStats` |
| `get_crawl_logs` | job_id, level?, limit? | `CrawlLog[]` |

## Tauri Events

| Event | Payload | Direction |
|-------|---------|-----------|
| `crawl://progress` | `{ job_id, item_id, address, status, message, progress: { completed, total, percentage }, result? }` | Backend → Frontend |
| `crawl://log` | `{ job_id, level, message, timestamp }` | Backend → Frontend |
| `crawl://job-status` | `{ job_id, status, stats: { completed, failed, cached, total } }` | Backend → Frontend |
| `crawl://complete` | `{ job_id, stats, elapsed_time }` | Backend → Frontend |

## Sidecar Protocol (stdin/stdout JSON)

### Inbound (Rust → Sidecar)
| Type | Payload |
|------|---------|
| `START_CRAWL` | `{ job_id, items: [{item_id, address, pnu, address_id}], settings: {scale, wait_time, headless, save_pdf, max_retries, timeout} }` |
| `PAUSE` | (none) |
| `RESUME` | (none) |
| `STOP` | (none) |
| `PING` | (none) |

### Outbound (Sidecar → Rust)
| Type | Payload |
|------|---------|
| `READY` | (none) |
| `ITEM_START` | `{ item_id, address }` |
| `VALIDATION_RESULT` | `{ item_id, success, pnu, count }` |
| `DATA_RESULT` | `{ item_id, data: { present_class, present_area, jiga, ... } }` |
| `IMAGE_RESULT` | `{ item_id, success, image_path }` |
| `PDF_RESULT` | `{ item_id, success, pdf_path }` |
| `ITEM_COMPLETE` | `{ item_id, status, result: { ... } }` |
| `ITEM_FAILED` | `{ item_id, error, retries_left }` |
| `LOG` | `{ level, message }` |
| `COMPLETE` | `{ total, success, failed, elapsed_ms }` |
| `ERROR` | `{ message, fatal }` |
| `PONG` | (none) |
