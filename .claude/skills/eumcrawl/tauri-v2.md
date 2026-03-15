---
name: eumcrawl-tauri-v2
description: >
  Tauri v2 patterns and best practices for EUM Crawler Desktop.
  IPC command registration, plugin configuration, sidecar management,
  event system, and Rust backend patterns.
user-invocable: false
metadata:
  version: "1.0.0"
  category: "platform"
  status: "active"
  updated: "2026-03-10"
  tags: "tauri, v2, rust, ipc, sidecar, plugin, desktop"

progressive_disclosure:
  enabled: true
  level1_tokens: 100
  level2_tokens: 5000

triggers:
  keywords: ["tauri", "ipc", "command", "sidecar", "plugin", "tauri.conf", "cargo"]
  agents: ["eumcrawl-tauri-backend", "eumcrawl-orchestrator"]
---

# Tauri v2 Patterns for EUM Crawler Desktop

## Architecture Overview

```
Svelte Frontend (WebView)
    │
    ├── invoke('command_name', params)  →  Rust IPC Handler
    │                                        │
    ├── listen('event://name')          ←  emit('event://name')
    │                                        │
    └── (no direct DB/FS access)             ├── SQLite (rusqlite)
                                             ├── File System (std::fs)
                                             └── Sidecar (tauri-plugin-shell)
```

## IPC Command Registration

### lib.rs - Command Registration
```rust
use tauri::Manager;

mod commands;
mod db;
mod error;
mod models;
mod services;
mod sidecar;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .setup(|app| {
            // Initialize database
            let db_path = app.path().app_data_dir()?.join("eumcrawl.db");
            let database = db::Database::new(db_path.to_str().unwrap())?;
            database.run_migrations()?;
            app.manage(database);

            // Initialize crawler sidecar manager
            let crawler = services::CrawlerManager::new();
            app.manage(crawler);

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            // Address commands
            commands::address::get_addresses,
            commands::address::add_address,
            commands::address::update_address,
            commands::address::delete_addresses,
            commands::address::import_addresses_from_excel,
            commands::address::get_address_groups,
            // Job commands
            commands::job::create_crawl_job,
            commands::job::start_crawl_job,
            commands::job::pause_crawl_job,
            commands::job::resume_crawl_job,
            commands::job::stop_crawl_job,
            commands::job::get_crawl_jobs,
            commands::job::get_crawl_job,
            commands::job::delete_crawl_job,
            commands::job::get_job_items,
            // Result commands
            commands::result::get_results,
            commands::result::get_result,
            commands::result::get_result_history,
            commands::result::delete_results,
            commands::result::recrawl_results,
            commands::result::check_cache,
            // Export commands
            commands::export::export_to_excel,
            commands::export::export_to_csv,
            // Settings commands
            commands::settings::get_settings,
            commands::settings::get_setting,
            commands::settings::update_setting,
            commands::settings::update_settings,
            commands::settings::reset_settings,
            // System commands
            commands::system::open_file,
            commands::system::open_folder,
            commands::system::backup_database,
            commands::system::restore_database,
            commands::system::clear_all_cache,
            commands::system::get_dashboard_stats,
            commands::system::get_crawl_logs,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

## Tauri Event System

### Emitting Events from Rust
```rust
use tauri::{AppHandle, Emitter};

pub fn emit_crawl_progress(app: &AppHandle, payload: CrawlProgress) {
    app.emit("crawl://progress", payload).ok();
}

pub fn emit_crawl_log(app: &AppHandle, payload: CrawlLog) {
    app.emit("crawl://log", payload).ok();
}

pub fn emit_job_status(app: &AppHandle, payload: JobStatus) {
    app.emit("crawl://job-status", payload).ok();
}

pub fn emit_complete(app: &AppHandle, payload: CrawlComplete) {
    app.emit("crawl://complete", payload).ok();
}
```

### Listening in Svelte
```typescript
import { listen, type UnlistenFn } from '@tauri-apps/api/event';
import { onMount, onDestroy } from 'svelte';

let unlisten: UnlistenFn;

onMount(async () => {
  unlisten = await listen<CrawlProgress>('crawl://progress', (event) => {
    console.log('Progress:', event.payload);
  });
});

onDestroy(() => {
  unlisten?.();
});
```

## Sidecar Configuration

### tauri.conf.json
```json
{
  "bundle": {
    "externalBin": [
      "binaries/eumcrawl-crawler"
    ]
  },
  "plugins": {
    "shell": {
      "sidecar": true,
      "scope": [
        {
          "name": "binaries/eumcrawl-crawler",
          "sidecar": true,
          "args": true
        }
      ]
    }
  }
}
```

### Spawning Sidecar from Rust
```rust
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::CommandEvent;

pub async fn spawn_crawler(app: &AppHandle) -> Result<SidecarHandle, AppError> {
    let (mut rx, child) = app.shell()
        .sidecar("eumcrawl-crawler")
        .map_err(|e| AppError::Sidecar(e.to_string()))?
        .spawn()
        .map_err(|e| AppError::Sidecar(e.to_string()))?;

    // Wait for READY message
    while let Some(event) = rx.recv().await {
        match event {
            CommandEvent::Stdout(line) => {
                let msg: SidecarMessage = serde_json::from_str(&String::from_utf8_lossy(&line))?;
                if msg.msg_type == "READY" {
                    return Ok(SidecarHandle { child, rx });
                }
            }
            CommandEvent::Error(err) => {
                return Err(AppError::Sidecar(err));
            }
            _ => {}
        }
    }

    Err(AppError::Sidecar("Sidecar failed to start".into()))
}
```

## Error Handling Pattern

```rust
use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct AppError {
    pub code: String,
    pub message: String,
}

// Make AppError compatible with Tauri commands
impl From<rusqlite::Error> for AppError {
    fn from(e: rusqlite::Error) -> Self {
        AppError { code: "DB_ERROR".into(), message: e.to_string() }
    }
}

// Tauri requires IntoResponse for command return types
impl std::fmt::Display for AppError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}: {}", self.code, self.message)
    }
}
```

## Key Cargo.toml Dependencies

```toml
[dependencies]
tauri = { version = "2", features = [] }
tauri-plugin-shell = "2"
tauri-plugin-dialog = "2"
tauri-plugin-fs = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
rusqlite = { version = "0.31", features = ["bundled"] }
tokio = { version = "1", features = ["full"] }
thiserror = "1"
chrono = { version = "0.4", features = ["serde"] }
calamine = "0.24"
rust_xlsxwriter = "0.64"

[build-dependencies]
tauri-build = { version = "2", features = [] }
```

## Window Configuration

```json
{
  "app": {
    "windows": [
      {
        "title": "EUM Crawler Desktop",
        "width": 1280,
        "height": 800,
        "minWidth": 1024,
        "minHeight": 768,
        "center": true,
        "decorations": true
      }
    ]
  }
}
```
