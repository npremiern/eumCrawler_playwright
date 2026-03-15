---
name: eumcrawl-db-schema
description: >
  SQLite database schema quick reference for EUM Crawler Desktop.
  Tables, indexes, cache logic, and key queries in compact form.
user-invocable: false
metadata:
  version: "1.0.0"
  category: "domain"
  status: "active"
  updated: "2026-03-10"
  tags: "sqlite, database, schema, cache, query, migration"

progressive_disclosure:
  enabled: true
  level1_tokens: 100
  level2_tokens: 4000

triggers:
  keywords: ["database", "schema", "table", "query", "cache", "migration", "sqlite", "db"]
  agents: ["eumcrawl-sqlite", "eumcrawl-tauri-backend"]
---

# EUM Crawler Database Schema Reference

Full specification: `docs/design/03-DATABASE.md`

## Tables Summary

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| addresses | Input addresses | id, address, pnu, group_name, tags |
| crawl_results | Scraped data | id, address_id, pnu, jiga, status, expires_at |
| crawl_jobs | Batch jobs | id, name, status, total/completed/failed_count |
| job_items | Items in a job | id, job_id, address_id, result_id, status |
| settings | App config | key, value, type |
| crawl_logs | Operation logs | id, job_id, level, message |

## Core Schema

```sql
CREATE TABLE addresses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  address TEXT NOT NULL UNIQUE,
  normalized_address TEXT,
  pnu TEXT,
  group_name TEXT,
  tags TEXT DEFAULT '[]',
  memo TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE crawl_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  address_id INTEGER NOT NULL REFERENCES addresses(id) ON DELETE CASCADE,
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
  pdf_path TEXT,
  scale TEXT DEFAULT '1200',
  status TEXT NOT NULL CHECK(status IN ('success','failed','partial')),
  error_message TEXT,
  source TEXT DEFAULT 'crawl' CHECK(source IN ('crawl','cache')),
  crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME
);

CREATE TABLE crawl_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK(status IN ('pending','running','paused','completed','failed','cancelled')),
  total_count INTEGER DEFAULT 0,
  completed_count INTEGER DEFAULT 0,
  failed_count INTEGER DEFAULT 0,
  cached_count INTEGER DEFAULT 0,
  scale TEXT DEFAULT '1200',
  save_pdf BOOLEAN DEFAULT 1,
  use_cache BOOLEAN DEFAULT 1,
  cache_expiry_days INTEGER DEFAULT 30,
  settings_snapshot TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  started_at DATETIME,
  paused_at DATETIME,
  finished_at DATETIME
);

CREATE TABLE job_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL REFERENCES crawl_jobs(id) ON DELETE CASCADE,
  address_id INTEGER NOT NULL REFERENCES addresses(id) ON DELETE CASCADE,
  result_id INTEGER REFERENCES crawl_results(id),
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK(status IN ('pending','running','success','failed','skipped','cached')),
  sort_order INTEGER NOT NULL,
  error_message TEXT,
  started_at DATETIME,
  finished_at DATETIME,
  UNIQUE(job_id, address_id)
);

CREATE TABLE settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  type TEXT NOT NULL CHECK(type IN ('string','number','boolean','json')),
  description TEXT,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE crawl_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER REFERENCES crawl_jobs(id) ON DELETE CASCADE,
  job_item_id INTEGER REFERENCES job_items(id) ON DELETE CASCADE,
  level TEXT NOT NULL CHECK(level IN ('info','warn','error','debug')),
  message TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Indexes

```sql
CREATE INDEX idx_results_address_id ON crawl_results(address_id);
CREATE INDEX idx_results_status ON crawl_results(status);
CREATE INDEX idx_results_crawled_at ON crawl_results(crawled_at);
CREATE INDEX idx_results_expires_at ON crawl_results(expires_at);
CREATE INDEX idx_jobs_status ON crawl_jobs(status);
CREATE INDEX idx_jobs_created_at ON crawl_jobs(created_at);
CREATE INDEX idx_job_items_job_id ON job_items(job_id);
CREATE INDEX idx_job_items_status ON job_items(status);
CREATE INDEX idx_logs_job_id ON crawl_logs(job_id);
CREATE INDEX idx_addresses_group ON addresses(group_name);
```

## Cache Check Query

```sql
-- Check if valid cached data exists for an address
SELECT * FROM crawl_results
WHERE address_id = ?
  AND status = 'success'
  AND (expires_at IS NULL OR expires_at > datetime('now'))
ORDER BY crawled_at DESC
LIMIT 1;
```

## Cache Insert with Expiry

```sql
INSERT INTO crawl_results (
  address_id, pnu, present_addr, present_class, present_area,
  jiga, jiga_year, present_mark1, present_mark2, present_mark3,
  image_path, pdf_path, scale, status, source, expires_at
) VALUES (
  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'success', 'crawl',
  datetime('now', '+' || ? || ' days')
);
```

## Dashboard Stats Query

```sql
SELECT
  (SELECT COUNT(*) FROM addresses) as total_addresses,
  (SELECT COUNT(*) FROM crawl_results WHERE status = 'success') as success_count,
  (SELECT COUNT(*) FROM crawl_results WHERE status = 'failed') as failed_count,
  (SELECT COUNT(*) FROM crawl_results WHERE source = 'cache') as cached_count,
  (SELECT COUNT(*) FROM crawl_results
   WHERE crawled_at >= date('now')) as today_count;
```

## Default Settings

```sql
INSERT INTO settings (key, value, type, description) VALUES
  ('cache_expiry_days', '30', 'number', 'Cache validity period in days'),
  ('default_scale', '1200', 'string', 'Default map scale'),
  ('wait_time', '5', 'number', 'Wait time between requests (seconds)'),
  ('headless_mode', 'true', 'boolean', 'Run browser in headless mode'),
  ('images_dir', 'images', 'string', 'Image storage directory'),
  ('pdfs_dir', 'pdfs', 'string', 'PDF storage directory'),
  ('auto_save_interval', '5', 'number', 'Auto-save interval (rows)'),
  ('max_retries', '3', 'number', 'Maximum retry attempts'),
  ('page_load_timeout', '30000', 'number', 'Page load timeout (ms)');
```

## PRAGMAs (Required)

```sql
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;
PRAGMA synchronous = NORMAL;
```
