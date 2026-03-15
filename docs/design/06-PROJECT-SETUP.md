# 프로젝트 설정 및 스캐폴드 구성 (Project Setup & Scaffold Configuration)

**프로젝트명**: eumcrawl-desktop
**문서 유형**: 설정 가이드
**작성일**: 2025-03-10
**버전**: 1.0
**대상**: 개발자 & 시스템 엔지니어

---

## 개요

이 문서는 eumcrawl-desktop 프로젝트를 **완전히 처음부터 구축**하기 위한 단계별 가이드입니다. 제공된 모든 명령어와 설정은 **복사-붙여넣기**로 즉시 실행 가능하도록 작성되었습니다. 숙련된 개발자라면 이 문서를 따라 **약 30분 안에 작동하는 프로젝트 스켈레톤**을 완성할 수 있습니다.

**스택 요약**:
- **프론트엔드**: Svelte 5 + SvelteKit + TypeScript
- **데스크톱**: Tauri v2 (Rust)
- **런타임/패키지 관리자**: Bun
- **크롤러**: Playwright (Bun 사이드카)
- **데이터베이스**: SQLite
- **스타일링**: Tailwind CSS v4 + shadcn-svelte
- **아이콘**: Lucide Svelte

---

## 1. 사전 요구사항 (Prerequisites)

### 1.1 필수 도구 설치

#### Windows/macOS/Linux 공통

**Bun 설치** (최신 버전)

```bash
curl -fsSL https://bun.sh/install | bash
```

검증:
```bash
bun --version
# 예상 출력: bun 1.0.0+
```

**Rust 설치** (최신 stable)

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

설치 후:
```bash
rustup update
rustc --version
cargo --version
```

#### Windows 특화 요구사항

1. **Microsoft C++ Build Tools** 설치
   - Visual Studio Build Tools 다운로드: https://visualstudio.microsoft.com/downloads/
   - "Desktop development with C++" 워크로드 선택 & 설치

2. **WebView2 Runtime** 설치
   - 다운로드: https://developer.microsoft.com/en-us/microsoft-edge/webview2/
   - 또는 Windows 10/11에 이미 포함되어 있을 수 있음
   - 확인: `winget install Microsoft.WebView2Runtime`

3. **Git 설치** (옵션이지만 권장)
   ```bash
   winget install Git.Git
   ```

#### macOS 특화 요구사항

Xcode Command Line Tools 설치:
```bash
xcode-select --install
```

#### Linux 특화 요구사항 (Ubuntu/Debian 예시)

```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    pkg-config \
    libssl-dev \
    libgtk-3-dev \
    libwebkit2gtk-4.0-dev \
    libappindicator3-dev \
    librsvg2-dev \
    patchelf
```

### 1.2 선택 도구

**Node.js** (특정 도구용, Bun이 기본)
```bash
bun install -g node  # Bun 경유로 설치 가능
```

**Visual Studio Code** (권장 에디터)
- 다운로드: https://code.visualstudio.com/

### 1.3 Playwright 브라우저 설치

프로젝트 생성 후 설치할 예정이지만, 미리 설치 가능:

```bash
bunx playwright install chromium
```

### 1.4 환경 변수 확인

```bash
# 터미널에서 다음 명령어 실행:
bun --version
rustc --version
cargo --version

# 모두 버전 정보를 반환하면 설치 완료
```

---

## 2. 프로젝트 초기화 (Project Initialization)

### 2.1 SvelteKit 프로젝트 생성

작업 디렉토리 선택 후:

```bash
bun create svelte@latest eumcrawl-desktop
```

프롬프트에서 다음과 같이 선택:

```
Which Svelte app template?
> Skeleton project
  > SvelteKit demo app
  > Library project

선택: Skeleton project

Add type checking with TypeScript?
> Yes, using TypeScript syntax
  > Yes, using JSDoc syntax
  > No

선택: Yes, using TypeScript syntax

Select additional options (use arrow keys/spacebar)
> Add ESLint for code linting
> Add Prettier for code formatting
> Add Vitest for unit testing
> Add Playwright for end-to-end testing

선택: ESLint와 Prettier 체크 (엔터로 선택)
```

### 2.2 프로젝트 디렉토리 이동

```bash
cd eumcrawl-desktop
```

### 2.3 기본 의존성 설치

```bash
bun install
```

### 2.4 Tauri v2 추가

```bash
bun add -D @tauri-apps/cli@latest
```

Tauri 초기화:

```bash
bunx tauri init
```

다음 프롬프트에 답변:

```
✔ Project name (eumcrawl-desktop) · eumcrawl-desktop
✔ Window title (eumcrawl-desktop) · EUM Crawler Desktop
✔ Run dev server command (npm run dev) · bun run dev
✔ Build frontend when running tauri dev (true) · true
✔ Frontend dev URL (http://localhost:5173) · http://localhost:5173
✔ Frontend dist dir (.../build) · ../build

✔ Create src-tauri? (Y/n) · Y
```

결과: `src-tauri/` 디렉토리 자동 생성

### 2.5 Tauri API 플러그인 추가

```bash
bun add @tauri-apps/api@latest
bun add -D @tauri-apps/cli@latest
bun add @tauri-apps/plugin-shell@latest
bun add @tauri-apps/plugin-dialog@latest
bun add @tauri-apps/plugin-fs@latest
bun add @tauri-apps/plugin-sql@latest
bun add @tauri-apps/plugin-process@latest
bun add @tauri-apps/plugin-http@latest
```

### 2.6 Tailwind CSS v4 설치

```bash
bun add -D tailwindcss @tailwindcss/vite postcss autoprefixer
```

Tailwind 초기화:

```bash
bunx tailwindcss init -p
```

### 2.7 shadcn-svelte 설치

```bash
bunx shadcn-svelte@latest init
```

프롬프트:

```
✔ Which style would you like to use? · Default
✔ Which color would you like as the base color? · Slate
✔ Do you want to use CSS variables for colors? (Y/n) · yes
```

### 2.8 추가 UI 및 유틸리티 라이브러리

```bash
bun add lucide-svelte
bun add clsx tailwind-merge
bun add bits-ui
bun add mode-watcher
```

### 2.9 사이드카 프로젝트 생성

```bash
mkdir src-crawler
cd src-crawler
bun init
cd ..
```

사이드카 의존성:

```bash
cd src-crawler
bun add playwright
bun add sharp
cd ..
```

이제 기본 프로젝트 구조가 완성되었습니다.

---

## 3. 디렉토리 구조 (전체 레이아웃)

프로젝트 루트에서 다음 명령어로 확인:

```bash
tree -L 2 -a
```

예상 결과:

```
eumcrawl-desktop/
├── src/                              # Svelte 프론트엔드
│   ├── app.html                      # HTML 진입점
│   ├── app.css                       # 전역 스타일
│   ├── app.d.ts                      # 타입 정의
│   ├── lib/
│   │   ├── components/               # UI 컴포넌트
│   │   ├── stores/                   # Svelte 스토어 (상태관리)
│   │   ├── services/                 # Tauri IPC 래퍼
│   │   ├── types/                    # TypeScript 타입
│   │   └── utils/                    # 유틸리티 함수
│   └── routes/
│       ├── +layout.svelte            # 루트 레이아웃
│       ├── +page.svelte              # 대시보드
│       ├── addresses/
│       ├── jobs/
│       ├── results/
│       ├── export/
│       └── settings/
│
├── src-tauri/                        # Rust 백엔드
│   ├── src/
│   │   ├── main.rs                   # 진입점
│   │   ├── lib.rs                    # 라이브러리 루트
│   │   ├── commands/                 # IPC 커맨드
│   │   ├── db/                       # 데이터베이스
│   │   ├── models/                   # 데이터 모델
│   │   ├── services/                 # 비즈니스 로직
│   │   ├── events.rs                 # 이벤트 타입
│   │   ├── errors.rs                 # 에러 타입
│   │   └── state.rs                  # 앱 상태
│   ├── migrations/                   # SQLite 마이그레이션
│   ├── Cargo.toml                    # Rust 의존성
│   ├── tauri.conf.json               # Tauri 설정
│   └── build.rs                      # 빌드 스크립트
│
├── src-crawler/                      # Playwright 사이드카
│   ├── index.ts                      # 진입점
│   ├── scraper.ts                    # 스크래핑 로직
│   ├── image-downloader.ts           # 이미지 다운로더
│   ├── types.ts                      # 타입 정의
│   ├── package.json                  # 의존성
│   └── tsconfig.json                 # TypeScript 설정
│
├── static/                           # 정적 자산
│   └── fonts/                        # 폰트
│
├── package.json                      # 프로젝트 루트 설정
├── svelte.config.js                  # Svelte 설정
├── vite.config.ts                    # Vite 설정
├── tailwind.config.ts                # Tailwind 설정
├── tsconfig.json                     # TypeScript 설정
├── components.json                   # shadcn-svelte 설정
└── README.md                         # 프로젝트 문서
```

---

## 4. 핵심 설정 파일 (Configuration Files)

### 4.1 package.json (프로젝트 루트)

생성된 파일을 다음과 같이 수정:

파일 경로: `eumcrawl-desktop/package.json`

```json
{
  "name": "eumcrawl-desktop",
  "version": "1.0.0",
  "description": "EUM Real Estate Crawler Desktop Application",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite dev",
    "build": "vite build",
    "preview": "vite preview",
    "tauri": "tauri",
    "tauri:dev": "tauri dev",
    "tauri:build": "tauri build",
    "sidecar:build": "cd src-crawler && bun build.ts && cd ..",
    "lint": "eslint .",
    "format": "prettier --write .",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "svelte": "^5.0.0",
    "@sveltejs/kit": "^2.0.0",
    "@tauri-apps/api": "^2.0.0",
    "@tauri-apps/plugin-shell": "^2.0.0",
    "@tauri-apps/plugin-dialog": "^2.0.0",
    "@tauri-apps/plugin-fs": "^2.0.0",
    "@tauri-apps/plugin-http": "^2.0.0",
    "tailwindcss": "^3.3.0",
    "lucide-svelte": "^0.263.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0",
    "bits-ui": "^0.19.0",
    "mode-watcher": "^0.2.0"
  },
  "devDependencies": {
    "@sveltejs/adapter-auto": "^2.1.0",
    "@sveltejs/vite-plugin-svelte": "^2.4.0",
    "@tauri-apps/cli": "^2.0.0",
    "vite": "^5.0.0",
    "typescript": "^5.3.0",
    "@types/node": "^20.0.0",
    "tailwindcss": "^3.3.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "prettier": "^3.0.0",
    "prettier-plugin-svelte": "^3.0.0",
    "eslint": "^8.0.0",
    "eslint-plugin-svelte": "^2.0.0",
    "svelte": "^5.0.0"
  }
}
```

### 4.2 svelte.config.js

파일 경로: `eumcrawl-desktop/svelte.config.js`

```javascript
import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		adapter: adapter(),
		alias: {
			'$lib': 'src/lib'
		}
	}
};

export default config;
```

### 4.3 vite.config.ts

파일 경로: `eumcrawl-desktop/vite.config.ts`

```typescript
import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import tailwindcss from 'tailwindcss';
import autoprefixer from 'autoprefixer';

export default defineConfig({
	plugins: [svelte()],
	css: {
		postcss: {
			plugins: [tailwindcss, autoprefixer]
		}
	},
	optimizeDeps: {
		exclude: ['eumcrawl-tauri']
	}
});
```

### 4.4 tailwind.config.ts

파일 경로: `eumcrawl-desktop/tailwind.config.ts`

```typescript
import type { Config } from 'tailwindcss';
import defaultTheme from 'tailwindcss/defaultTheme';

const config: Config = {
	darkMode: ['class'],
	content: [
		'./src/**/*.{html,js,svelte,ts}',
		'./node_modules/bits-ui/dist/**/*.{html,js,svelte,ts}'
	],
	theme: {
		extend: {
			fontFamily: {
				sans: ['Pretendard', ...defaultTheme.fontFamily.sans],
				mono: [...defaultTheme.fontFamily.mono]
			},
			colors: {
				primary: {
					50: '#f0f7ff',
					100: '#e0efff',
					200: '#bae6ff',
					300: '#7dd3fc',
					400: '#38bdf8',
					500: '#0ea5e9',
					600: '#0284c7',
					700: '#0369a1',
					800: '#075985',
					900: '#0c3d66',
					950: '#051e3e'
				}
			}
		}
	},
	plugins: []
};

export default config;
```

### 4.5 tsconfig.json

파일 경로: `eumcrawl-desktop/tsconfig.json`

```json
{
	"compilerOptions": {
		"moduleResolution": "bundler",
		"allowImportingTsExtensions": true,
		"resolveJsonModule": true,
		"lib": ["ES2020", "DOM", "DOM.Iterable"],
		"target": "ES2020",
		"module": "ESNext",
		"strict": true,
		"esModuleInterop": true,
		"skipLibCheck": true,
		"forceConsistentCasingInFileNames": true,
		"baseUrl": ".",
		"paths": {
			"$lib": ["src/lib"],
			"$lib/*": ["src/lib/*"]
		}
	},
	"include": ["src/**/*.ts", "src/**/*.svelte", "src-tauri/**/*.ts"],
	"exclude": ["node_modules", "dist", "build", "src-tauri/target"]
}
```

### 4.6 src-tauri/Cargo.toml

파일 경로: `eumcrawl-desktop/src-tauri/Cargo.toml`

생성된 파일의 `[dependencies]` 섹션을 다음과 같이 업데이트:

```toml
[package]
name = "eumcrawl-tauri"
version = "1.0.0"
edition = "2021"

[dependencies]
tauri = { version = "2", features = ["shell-open", "fs-all", "dialog-all"] }
tauri-plugin-shell = "2"
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

[target.'cfg(windows)'.dependencies]
windows = { version = "0.55", features = ["Win32_Foundation"] }

[profile.release]
panic = "crash"
codegen-units = 1
lto = true
```

### 4.7 src-tauri/tauri.conf.json

파일 경로: `eumcrawl-desktop/src-tauri/tauri.conf.json`

```json
{
  "productName": "EUM Crawler",
  "version": "1.0.0",
  "identifier": "com.eumcrawl.desktop",
  "build": {
    "beforeBuildCommand": "bun run build",
    "beforeDevCommand": "bun run dev",
    "devUrl": "http://localhost:5173",
    "frontendDist": "../build"
  },
  "app": {
    "windows": [
      {
        "title": "EUM Crawler Desktop",
        "width": 1400,
        "height": 900,
        "minWidth": 900,
        "minHeight": 700,
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
    "targets": [
      "msi",
      "nsis"
    ],
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

### 4.8 src-crawler/package.json

파일 경로: `eumcrawl-desktop/src-crawler/package.json`

```json
{
  "name": "eumcrawl-crawler-sidecar",
  "version": "1.0.0",
  "description": "Playwright-based crawling sidecar",
  "type": "module",
  "scripts": {
    "start": "bun src/index.ts",
    "dev": "bun --watch src/index.ts",
    "build": "bun build src/index.ts --outfile ../dist/sidecar.js --minify"
  },
  "dependencies": {
    "playwright": "^1.40.0",
    "sharp": "^0.33.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/node": "^20.0.0",
    "bun-types": "latest"
  }
}
```

### 4.9 src-crawler/tsconfig.json

파일 경로: `eumcrawl-desktop/src-crawler/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ES2020",
    "lib": ["ES2020"],
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src/**/*.ts"],
  "exclude": ["node_modules", "dist"]
}
```

---

## 5. 핵심 보일러플레이트 파일 (Essential Files)

### 5.1 src/app.html

파일 경로: `eumcrawl-desktop/src/app.html`

```html
<!doctype html>
<html lang="ko" class="light">
	<head>
		<meta charset="utf-8" />
		<link rel="icon" href="%sveltekit.assets%/favicon.png" />
		<meta name="viewport" content="width=device-width, initial-scale=1" />
		<meta name="description" content="EUM Real Estate Crawler Desktop" />
		<title>EUM Crawler Desktop</title>
		%sveltekit.head%
	</head>
	<body data-sveltekit-preload-data="hover">
		<div style="display: contents">%sveltekit.body%</div>
	</body>
</html>
```

### 5.2 src/app.css

파일 경로: `eumcrawl-desktop/src/app.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');

:root {
	color-scheme: light;
	--background: #ffffff;
	--foreground: #000000;
	--primary: #0ea5e9;
	--primary-foreground: #ffffff;
	--secondary: #f1f5f9;
	--secondary-foreground: #000000;
	--accent: #0284c7;
	--accent-foreground: #ffffff;
	--destructive: #dc2626;
	--destructive-foreground: #ffffff;
	--muted: #f1f5f9;
	--muted-foreground: #64748b;
	--card: #ffffff;
	--card-foreground: #000000;
	--border: #e2e8f0;
	--input: #e2e8f0;
	--radius: 0.5rem;
}

html.dark {
	color-scheme: dark;
	--background: #0f172a;
	--foreground: #f1f5f9;
	--primary: #0ea5e9;
	--primary-foreground: #000000;
	--secondary: #1e293b;
	--secondary-foreground: #f1f5f9;
	--accent: #0284c7;
	--accent-foreground: #f1f5f9;
	--destructive: #ef4444;
	--destructive-foreground: #000000;
	--muted: #1e293b;
	--muted-foreground: #94a3b8;
	--card: #1e293b;
	--card-foreground: #f1f5f9;
	--border: #334155;
	--input: #334155;
}

* {
	@apply border-border;
}

body {
	@apply bg-background text-foreground;
}

html {
	scroll-behavior: smooth;
}

/* 폰트 설정 */
body {
	font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* 텍스트 선택 스타일 */
::selection {
	@apply bg-primary text-primary-foreground;
}
```

### 5.3 src/lib/utils/cn.ts

파일 경로: `eumcrawl-desktop/src/lib/utils/cn.ts`

```typescript
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * clsx와 tailwind-merge를 조합하여 Tailwind 클래스를 안전하게 병합
 */
export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}
```

### 5.4 src/routes/+layout.svelte (루트 레이아웃)

파일 경로: `eumcrawl-desktop/src/routes/+layout.svelte`

```svelte
<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';

	let mounted = false;

	onMount(() => {
		mounted = true;
	});
</script>

{#if mounted}
	<main class="min-h-screen bg-background text-foreground">
		<!-- 헤더 -->
		<header class="border-b border-border bg-card shadow-sm">
			<div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
				<h1 class="text-2xl font-bold text-primary">EUM Crawler</h1>
				<nav class="flex gap-4">
					<a href="/" class="text-sm text-muted-foreground hover:text-foreground">
						대시보드
					</a>
					<a href="/addresses" class="text-sm text-muted-foreground hover:text-foreground">
						주소
					</a>
					<a href="/jobs" class="text-sm text-muted-foreground hover:text-foreground">
						작업
					</a>
					<a href="/results" class="text-sm text-muted-foreground hover:text-foreground">
						결과
					</a>
					<a href="/settings" class="text-sm text-muted-foreground hover:text-foreground">
						설정
					</a>
				</nav>
			</div>
		</header>

		<!-- 메인 콘텐츠 -->
		<div class="mx-auto max-w-7xl px-4 py-8">
			<slot />
		</div>
	</main>
{/if}

<style>
	:global(html) {
		scroll-behavior: smooth;
	}
</style>
```

### 5.5 src/routes/+page.svelte (대시보드)

파일 경로: `eumcrawl-desktop/src/routes/+page.svelte`

```svelte
<script lang="ts">
	import { onMount } from 'svelte';

	let stats = {
		totalAddresses: 0,
		processedAddresses: 0,
		totalJobs: 0,
		runningJobs: 0
	};

	onMount(() => {
		// IPC 명령어로 통계 로드 (추후 구현)
		// loadStats();
	});
</script>

<div class="space-y-6">
	<h2 class="text-3xl font-bold">대시보드</h2>

	<!-- 통계 카드 -->
	<div class="grid grid-cols-4 gap-4">
		<div class="rounded-lg border border-border bg-card p-6 shadow-sm">
			<div class="text-sm text-muted-foreground">전체 주소</div>
			<div class="text-3xl font-bold">{stats.totalAddresses}</div>
		</div>

		<div class="rounded-lg border border-border bg-card p-6 shadow-sm">
			<div class="text-sm text-muted-foreground">처리된 주소</div>
			<div class="text-3xl font-bold text-green-600">{stats.processedAddresses}</div>
		</div>

		<div class="rounded-lg border border-border bg-card p-6 shadow-sm">
			<div class="text-sm text-muted-foreground">전체 작업</div>
			<div class="text-3xl font-bold">{stats.totalJobs}</div>
		</div>

		<div class="rounded-lg border border-border bg-card p-6 shadow-sm">
			<div class="text-sm text-muted-foreground">실행 중인 작업</div>
			<div class="text-3xl font-bold text-blue-600">{stats.runningJobs}</div>
		</div>
	</div>

	<!-- 최근 활동 -->
	<div class="rounded-lg border border-border bg-card p-6 shadow-sm">
		<h3 class="text-lg font-semibold">최근 작업</h3>
		<p class="mt-4 text-sm text-muted-foreground">실행 중인 작업이 없습니다.</p>
	</div>
</div>
```

### 5.6 src-tauri/src/main.rs

파일 경로: `eumcrawl-desktop/src-tauri/src/main.rs`

```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;

mod commands;
mod db;
mod models;
mod services;
mod events;
mod errors;
mod state;

use crate::state::AppState;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
	tauri::Builder::default()
		.setup(|app| {
			let app_dir = app.path_resolver()
				.app_config_dir()
				.expect("Failed to resolve app config directory");

			std::fs::create_dir_all(&app_dir)?;

			let db_path = app_dir.join("eumcrawl.db");
			let state = AppState::new(db_path.to_str().unwrap())
				.expect("Failed to initialize app state");

			app.manage(state);
			Ok(())
		})
		.invoke_handler(tauri::generate_handler![
			// 주소 관련 커맨드
			commands::get_addresses,
			commands::add_address,
			commands::delete_address,

			// 작업 관련 커맨드
			commands::start_crawl_job,
			commands::pause_job,
			commands::resume_job,
			commands::stop_job,

			// 결과 관련 커맨드
			commands::get_results,
			commands::search_results,
			commands::delete_result,

			// 설정 관련 커맨드
			commands::get_settings,
			commands::update_setting,
		])
		.run(tauri::generate_context!())
		.expect("error while running tauri application");
}
```

### 5.7 src-tauri/src/lib.rs

파일 경로: `eumcrawl-desktop/src-tauri/src/lib.rs`

```rust
pub mod commands;
pub mod db;
pub mod models;
pub mod services;
pub mod events;
pub mod errors;
pub mod state;
```

### 5.8 src-tauri/migrations/001_initial.sql

파일 경로: `eumcrawl-desktop/src-tauri/migrations/001_initial.sql`

```sql
-- Addresses 테이블
CREATE TABLE IF NOT EXISTS addresses (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	address TEXT NOT NULL UNIQUE,
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Results 테이블
CREATE TABLE IF NOT EXISTS results (
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
CREATE TABLE IF NOT EXISTS jobs (
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
CREATE TABLE IF NOT EXISTS job_addresses (
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
CREATE TABLE IF NOT EXISTS settings (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	key TEXT UNIQUE NOT NULL,
	value TEXT,
	type TEXT DEFAULT 'string',
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Cache 테이블
CREATE TABLE IF NOT EXISTS cache (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	address TEXT UNIQUE NOT NULL,
	result_data JSON,
	expires_at DATETIME,
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_addresses_address ON addresses(address);
CREATE INDEX IF NOT EXISTS idx_results_address_id ON results(address_id);
CREATE INDEX IF NOT EXISTS idx_results_crawled_at ON results(crawled_at);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_job_addresses_job_id ON job_addresses(job_id);
CREATE INDEX IF NOT EXISTS idx_cache_address ON cache(address);
CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache(expires_at);
```

### 5.9 src-crawler/src/index.ts

파일 경로: `eumcrawl-desktop/src-crawler/src/index.ts`

```typescript
import * as readline from 'readline';

interface SidecarMessage {
	type: 'START_CRAWL' | 'PAUSE' | 'RESUME' | 'STOP' | 'PING';
	job_id: number;
	addresses?: string[];
	config?: Record<string, unknown>;
}

interface SidecarResponse {
	type: 'PROGRESS' | 'RESULT' | 'ERROR' | 'COMPLETE' | 'LOG' | 'PONG';
	job_id: number;
	progress?: Record<string, unknown>;
	result?: Record<string, unknown>;
	error?: Record<string, unknown>;
	complete?: Record<string, unknown>;
	log?: Record<string, unknown>;
	timestamp?: string;
}

const rl = readline.createInterface({
	input: process.stdin,
	output: process.stdout,
	terminal: false
});

let isRunning = false;
let isPaused = false;

function sendResponse(response: SidecarResponse) {
	console.log(JSON.stringify(response));
}

function log(level: string, message: string, jobId: number = 0) {
	sendResponse({
		type: 'LOG',
		job_id: jobId,
		log: {
			level,
			message
		},
		timestamp: new Date().toISOString()
	});
}

rl.on('line', async (line) => {
	try {
		const message = JSON.parse(line) as SidecarMessage;

		switch (message.type) {
			case 'START_CRAWL':
				await handleStartCrawl(message);
				break;

			case 'PAUSE':
				isPaused = true;
				log('info', `Job ${message.job_id} paused`, message.job_id);
				break;

			case 'RESUME':
				isPaused = false;
				log('info', `Job ${message.job_id} resumed`, message.job_id);
				break;

			case 'STOP':
				isRunning = false;
				log('info', `Job ${message.job_id} stopped`, message.job_id);
				break;

			case 'PING':
				sendResponse({
					type: 'PONG',
					job_id: message.job_id
				});
				break;

			default:
				log('error', `Unknown message type: ${message.type}`, message.job_id);
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
	if (!message.addresses) {
		log('error', 'No addresses provided', message.job_id);
		return;
	}

	isRunning = true;
	isPaused = false;

	try {
		const total = message.addresses.length;

		for (let i = 0; i < total && isRunning; i++) {
			// 일시정지 체크
			while (isPaused && isRunning) {
				await new Promise(resolve => setTimeout(resolve, 100));
			}

			if (!isRunning) break;

			const address = message.addresses[i];

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

			// 더미 결과 (실제 구현 필요)
			sendResponse({
				type: 'RESULT',
				job_id: message.job_id,
				result: {
					address,
					present_addr: `Result for ${address}`,
					crawled_at: new Date().toISOString()
				}
			});
		}

		// 완료
		sendResponse({
			type: 'COMPLETE',
			job_id: message.job_id,
			complete: {
				total,
				successful: total,
				failed: 0,
				duration_seconds: 0
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
		isRunning = false;
	}
}

log('info', 'Crawler sidecar started');
```

---

## 6. 필수 디렉토리 생성

프로젝트 루트에서:

```bash
# Frontend 구조
mkdir -p src/lib/components/ui
mkdir -p src/lib/components/address
mkdir -p src/lib/components/job
mkdir -p src/lib/components/result
mkdir -p src/lib/components/layout
mkdir -p src/lib/stores
mkdir -p src/lib/services
mkdir -p src/lib/types
mkdir -p src/lib/utils

# Backend 구조
mkdir -p src-tauri/src/commands
mkdir -p src-tauri/src/db
mkdir -p src-tauri/src/models
mkdir -p src-tauri/src/services
mkdir -p src-tauri/migrations

# Crawler 구조
mkdir -p src-crawler/src

# 정적 자산
mkdir -p static/fonts
```

---

## 7. 개발 워크플로우 (Development Workflow)

### 7.1 개발 서버 시작

```bash
# 프로젝트 루트에서:
cd eumcrawl-desktop

# Tauri + Svelte 개발 서버 실행
bun run tauri:dev
```

예상 출력:
```
   Running your Vite app in development mode...

   ➜  Browser: http://localhost:5173
   ➜  Local:   http://localhost:5173
   ➜  Press 'q' to quit
```

### 7.2 Playwright 브라우저 설치

```bash
cd src-crawler
bunx playwright install chromium
cd ..
```

### 7.3 Eslint & Prettier 실행

```bash
# 코드 검사
bun run lint

# 코드 포맷팅
bun run format
```

### 7.4 TypeScript 체크

```bash
bun run type-check
```

### 7.5 사이드카 테스트

```bash
cd src-crawler
bun run dev
# 터미널에 JSON 입력:
# {"type":"PING","job_id":1}
cd ..
```

---

## 8. 빌드 및 배포 (Build & Distribution)

### 8.1 프로덕션 빌드

```bash
# 전체 빌드 (Svelte + Tauri)
bun run tauri:build
```

빌드 결과:
- Windows: `src-tauri/target/release/bundle/msi/` 또는 `nsis/`
- macOS: `src-tauri/target/release/bundle/dmg/`
- Linux: `src-tauri/target/release/bundle/deb/` 또는 `appimage/`

### 8.2 빌드 체크리스트

```
- [ ] 모든 TypeScript 타입 체크 성공
- [ ] ESLint 경고 없음
- [ ] 테스트 통과
- [ ] Playwright 브라우저 번들 확인
- [ ] version 번호 업데이트 (package.json, tauri.conf.json)
- [ ] CHANGELOG.md 업데이트
- [ ] 배포 준비 완료
```

### 8.3 Windows MSI 빌드 최적화

`src-tauri/Cargo.toml`에서:
```toml
[profile.release]
panic = "crash"
codegen-units = 1
lto = true
```

---

## 9. 문제 해결 (Troubleshooting)

### 9.1 "WebView2 not found" (Windows)

해결책:
```bash
# WebView2 런타임 설치
winget install Microsoft.WebView2Runtime

# 또는 수동으로 설치:
# https://developer.microsoft.com/en-us/microsoft-edge/webview2/
```

### 9.2 "Rust compilation error"

해결책:
```bash
# Rust 업데이트
rustup update

# 클린 빌드
cargo clean
cargo build
```

### 9.3 "Playwright browser not found"

해결책:
```bash
cd src-crawler
bunx playwright install chromium
cd ..
```

### 9.4 "Tauri CLI not found"

해결책:
```bash
bun add -D @tauri-apps/cli@latest
bunx tauri --version
```

### 9.5 포트 5173 이미 사용 중

해결책:
```bash
# 포트 변경 (vite.config.ts):
export default defineConfig({
  server: {
    port: 5174
  }
});

# 그리고 tauri.conf.json에서:
"devUrl": "http://localhost:5174"
```

### 9.6 SQLite 잠금 오류

해결책:
- SQLite는 단일 연결만 지원
- Rust에서 `Mutex<Connection>` 사용으로 해결
- 동시 쿼리는 큐에 입력됨

---

## 10. 마이그레이션 체크리스트 (Python → Svelte/Tauri)

| 기능 | Python 위치 | 새 위치 | 상태 |
|------|----------|--------|------|
| 메인 CLI | crawler.py | src-tauri/src/commands | ❌ |
| 크롤링 로직 | scraper.py | src-crawler/src/scraper.ts | ❌ |
| Excel 처리 | excel_handler.py | src-tauri/src/services | ❌ |
| 설정 | config.py | src/lib/utils/constants.ts | ❌ |
| GUI | tkinter | Svelte 5 | ❌ |

---

## 11. 다음 단계 (Next Steps)

### Phase 1: 기본 구조 완성 (현재)
- ✅ 프로젝트 초기화
- ✅ 의존성 설치
- ✅ 설정 파일 작성
- ⏳ 기본 컴포넌트 구현

### Phase 2: 백엔드 기능
- IPC 커맨드 구현 (주소, 작업, 결과)
- SQLite 스키마 및 쿼리
- Tauri 이벤트 시스템

### Phase 3: 프론트엔드 페이지
- 주소 관리 페이지
- 작업 모니터 페이지
- 결과 검색 페이지

### Phase 4: 사이드카 통합
- Playwright 스크래핑 로직
- 메시지 프로토콜 구현
- 실시간 진행률 전송

### Phase 5: 테스트 & 배포
- 유닛 테스트
- E2E 테스트
- 프로덕션 빌드 및 배포

---

## 12. 빠른 참조 (Quick Reference)

### 주요 명령어

```bash
# 의존성 설치
bun install

# 개발 서버 시작
bun run tauri:dev

# 프로덕션 빌드
bun run tauri:build

# 코드 포맷팅
bun run format

# 타입 체크
bun run type-check

# Playwright 브라우저 설치
cd src-crawler && bunx playwright install chromium && cd ..
```

### 파일 경로

```
Frontend components:     src/lib/components/
Frontend stores:         src/lib/stores/
Frontend services:       src/lib/services/
Backend commands:        src-tauri/src/commands/
Backend models:          src-tauri/src/models/
Database schema:         src-tauri/migrations/
Crawler logic:           src-crawler/src/
```

### 포트 및 URL

```
Svelte Dev:    http://localhost:5173
Tauri Window:  Auto-generated (frameless window)
Database:      ~/.eumcrawl/eumcrawl.db
```

---

## 부록 A: 환경 변수 (Optional)

`.env.local` 파일 생성 (프로젝트 루트):

```env
# Vite 환경
VITE_API_URL=http://localhost:5173

# Tauri 환경
TAURI_PRIVATE_KEY=...  # 업데이트용 (선택사항)

# 크롤러 설정
PLAYWRIGHT_TIMEOUT=30000
CRAWLER_HEADLESS=true
```

---

## 부록 B: 추천 VS Code 확장

```json
{
  "recommendations": [
    "svelte.svelte-vscode",
    "rust-lang.rust-analyzer",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "bradlc.vscode-tailwindcss",
    "denoland.vscode-deno"
  ]
}
```

`.vscode/extensions.json`에 저장:

```bash
mkdir -p .vscode
echo '{"recommendations": ["svelte.svelte-vscode", "rust-lang.rust-analyzer", "esbenp.prettier-vscode", "dbaeumer.vscode-eslint", "bradlc.vscode-tailwindcss"]}' > .vscode/extensions.json
```

---

## 부록 C: Bun vs npm/yarn 비교

| 기능 | Bun | npm | 차이 |
|------|-----|-----|------|
| 설치 속도 | 매우 빠름 | 느림 | ~3배 빠름 |
| 캐시 | 자동 | 수동 | Bun이 더 효율적 |
| TypeScript | 네이티브 | 필요 | Bun이 즉시 실행 |
| 런타임 | Node.js 호환 | - | Bun이 더 빠름 |

**권장**: Bun 사용 (프로젝트 전체에서 일관된 성능)

---

## 완료 확인 체크리스트

프로젝트를 모두 완료하면 다음을 확인하세요:

```
[ ] bun --version 출력됨
[ ] rustc --version 출력됨
[ ] eumcrawl-desktop 디렉토리 생성됨
[ ] node_modules 설치됨
[ ] src-tauri/target 빌드됨
[ ] src/routes/+page.svelte 렌더링됨
[ ] bun run tauri:dev 성공
[ ] SQLite 데이터베이스 파일 생성됨
[ ] 브라우저에서 http://localhost:5173 접속 가능
```

모든 항목이 완료되면 **프로젝트 스켈레톤이 정상 작동**하는 것입니다!

---

## 추가 리소스

- **Tauri 공식 문서**: https://tauri.app
- **SvelteKit 공식 문서**: https://kit.svelte.dev
- **Svelte 5 문서**: https://svelte.dev
- **Bun 공식 문서**: https://bun.sh
- **Tailwind CSS 문서**: https://tailwindcss.com
- **shadcn-svelte**: https://www.shadcn-svelte.com

---

**문서 정보**
- 작성일: 2025-03-10
- 버전: 1.0
- 대상 독자: 풀스택 개발자
- 최종 검증일: 2025-03-10
- 예상 완료 시간: 30분 (경험 있는 개발자)
