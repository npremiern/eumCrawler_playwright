---
name: eumcrawl-crawler-porting
description: >
  Python-to-TypeScript porting guide for EUM Crawler.
  Maps existing scraper.py, config.py, and crawler.py logic
  to TypeScript/Bun/Playwright equivalents.
user-invocable: false
metadata:
  version: "1.0.0"
  category: "workflow"
  status: "active"
  updated: "2026-03-10"
  tags: "crawler, porting, python, typescript, playwright, scraper, eum"

progressive_disclosure:
  enabled: true
  level1_tokens: 100
  level2_tokens: 5000

triggers:
  keywords: ["crawler", "scraper", "porting", "playwright", "sidecar", "eum.go.kr"]
  agents: ["eumcrawl-crawler-sidecar"]
---

# Python to TypeScript Porting Guide

## Source Files

Read these existing Python files before porting:
- `src/config.py` - All constants and selectors
- `src/scraper.py` - Core scraping logic
- `src/crawler.py` - Two-phase orchestration

## Complete Selector Map

```typescript
// src-crawler/src/constants.ts

export const BASE_URL = 'https://www.eum.go.kr/';

export const AJAX_URL = 'https://www.eum.go.kr/web/am/mp/mpSearchAddrAjaxXml.jsp';

export const SELECTORS = {
  // Search
  SEARCH_INPUT: '#recent > input',

  // Result fields
  PRESENT_ADDR: '#present_addr',
  PRESENT_CLASS: '#present_class',
  PRESENT_AREA: '#present_area',
  JIGA: '#jiga',
  PRESENT_MARK1: '#present_mark1',
  PRESENT_MARK2: '#present_mark2',
  PRESENT_MARK3: '#present_mark3',

  // Image
  MAIN_IMAGE: '#appoint > div:nth-child(4) > table > tbody > tr:nth-child(1) > td.m_pd0.vtop > div > div > img',
  POPUP_IMAGE: 'body > form > div > div.big_aC > img',

  // Print/PDF
  PRINT_BUTTON: '#printBtn',  // Verify from existing code
} as const;

export const TIMING = {
  DEFAULT_WAIT: 5000,
  PAGE_TIMEOUT: 30000,
  MAX_RETRIES: 3,
  PDF_RENDER_WAIT: 3000,
} as const;

export const SCALES = ['1', '500', '600', '1000', '1200', '2400', '3000', '6000', '12000'] as const;
```

## Phase 1: Address Validation (AJAX)

### Python (existing)
```python
def check_address_count(self, address, verbose=False):
    response = self.page.request.post(
        "https://www.eum.go.kr/web/am/mp/mpSearchAddrAjaxXml.jsp",
        data={"search_addr": address}
    )
    # Parse XML response, extract count and PNU
```

### TypeScript (new)
```typescript
// src-crawler/src/validator.ts
import type { Page } from 'playwright';

export interface ValidationResult {
  success: boolean;
  count: number;
  pnu: string | null;
  error?: string;
}

export async function validateAddress(
  page: Page,
  address: string
): Promise<ValidationResult> {
  try {
    const response = await page.request.post(AJAX_URL, {
      form: { search_addr: address },
    });

    const text = await response.text();

    // Parse XML response
    // Note: Response may be EUC-KR encoded
    // Use DOMParser or simple regex to extract count and PNU
    const countMatch = text.match(/<count>(\d+)<\/count>/);
    const pnuMatch = text.match(/<pnu>([^<]+)<\/pnu>/);

    const count = countMatch ? parseInt(countMatch[1], 10) : 0;
    const pnu = pnuMatch ? pnuMatch[1] : null;

    return { success: count > 0, count, pnu };
  } catch (error) {
    return { success: false, count: -1, pnu: null, error: String(error) };
  }
}
```

## Phase 2: Search and Extract

### Python (existing)
```python
def search_address(self, address, pnu, scale="1200"):
    self.page.goto(BASE_URL)  # Refresh to prevent stale data
    self.page.fill('#recent > input', address)
    # Set scale via JavaScript
    self.page.evaluate(f"document.querySelector('#scaleFlag').value = '{scale}'")
    self.page.press('#recent > input', 'Enter')
    self.page.wait_for_selector('#jiga', timeout=30000)
```

### TypeScript (new)
```typescript
// src-crawler/src/scraper.ts
import { type Page, type BrowserContext, chromium } from 'playwright';

export class EumScraper {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private page: Page | null = null;

  constructor(private options: ScraperOptions) {}

  async launch(): Promise<void> {
    this.browser = await chromium.launch({
      headless: this.options.headless ?? true,
    });
    this.context = await this.browser.newContext();
    this.page = await this.context.newPage();
    this.page.setDefaultTimeout(TIMING.PAGE_TIMEOUT);
    await this.page.goto(BASE_URL);
  }

  async searchAddress(address: string, pnu: string, scale = '1200'): Promise<{ success: boolean; message: string }> {
    if (!this.page) throw new Error('Browser not launched');

    // Refresh to main page (prevents stale data)
    await this.page.goto(BASE_URL);
    await this.page.waitForLoadState('networkidle');

    // Fill search input
    await this.page.fill(SELECTORS.SEARCH_INPUT, address);

    // Set scale via JavaScript
    await this.page.evaluate((s) => {
      const el = document.querySelector('#scaleFlag') as HTMLInputElement;
      if (el) el.value = s;
    }, scale);

    // Submit search
    await this.page.press(SELECTORS.SEARCH_INPUT, 'Enter');

    // Wait for results
    try {
      await this.page.waitForSelector(SELECTORS.JIGA, { timeout: TIMING.PAGE_TIMEOUT });
      return { success: true, message: 'Search complete' };
    } catch {
      return { success: false, message: 'Search timeout - no results found' };
    }
  }

  async extractData(): Promise<Record<string, string>> {
    if (!this.page) throw new Error('Browser not launched');

    const data: Record<string, string> = {};

    const fields = [
      { key: 'present_addr', selector: SELECTORS.PRESENT_ADDR },
      { key: 'present_class', selector: SELECTORS.PRESENT_CLASS },
      { key: 'present_area', selector: SELECTORS.PRESENT_AREA },
      { key: 'jiga', selector: SELECTORS.JIGA },
      { key: 'present_mark1', selector: SELECTORS.PRESENT_MARK1 },
      { key: 'present_mark2', selector: SELECTORS.PRESENT_MARK2 },
      { key: 'present_mark3', selector: SELECTORS.PRESENT_MARK3 },
    ];

    for (const { key, selector } of fields) {
      try {
        const el = await this.page.$(selector);
        data[key] = el ? (await el.textContent() ?? '').trim() : '';
      } catch {
        data[key] = '';
      }
    }

    // Parse jiga to extract year: "50,000 (2024/01)" → jiga_year = "2024"
    const jigaMatch = data.jiga?.match(/\((\d{4})\//);
    data.jiga_year = jigaMatch ? jigaMatch[1] : '';

    // Clean present_class (remove "?" characters)
    data.present_class = data.present_class?.replace(/\?/g, '') ?? '';

    return data;
  }

  async close(): Promise<void> {
    await this.page?.close();
    await this.context?.close();
    await this.browser?.close();
    this.page = null;
    this.context = null;
    this.browser = null;
  }
}
```

## Image Download

### Python (existing)
```python
# Uses browser evaluate to fetch image with session cookies
# Converts base64 from browser, validates with PIL
```

### TypeScript (new)
```typescript
// src-crawler/src/image-downloader.ts
import { type Page } from 'playwright';
import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';

export async function downloadImage(
  page: Page,
  outputDir: string,
  filename: string,
  scale = '1200'
): Promise<string | null> {
  try {
    // Get image URL from page
    const imgUrl = await page.evaluate((sel) => {
      const img = document.querySelector(sel) as HTMLImageElement;
      return img?.src || null;
    }, SELECTORS.MAIN_IMAGE);

    if (!imgUrl) return null;

    // Download via browser context (preserves session cookies)
    const base64Data = await page.evaluate(async (url) => {
      const response = await fetch(url);
      const blob = await response.blob();
      return new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.readAsDataURL(blob);
      });
    }, imgUrl);

    // Extract base64 content
    const base64Content = base64Data.split(',')[1];
    const buffer = Buffer.from(base64Content, 'base64');

    // Save file
    await mkdir(outputDir, { recursive: true });
    const filePath = join(outputDir, `${filename}.png`);
    await writeFile(filePath, buffer);

    return filePath;
  } catch (error) {
    return null;
  }
}

export async function downloadImageFromPopup(
  context: BrowserContext,
  pnu: string,
  scale: string,
  outputDir: string,
  filename: string
): Promise<string | null> {
  const popupUrl = `https://www.eum.go.kr/web/ar/lu/luLandPop.jsp?pnu=${pnu}&scale=${scale}`;
  const popup = await context.newPage();

  try {
    await popup.goto(popupUrl);
    await popup.waitForSelector(SELECTORS.POPUP_IMAGE, { timeout: TIMING.PAGE_TIMEOUT });

    // Download image from popup
    const imgUrl = await popup.evaluate((sel) => {
      const img = document.querySelector(sel) as HTMLImageElement;
      return img?.src || null;
    }, SELECTORS.POPUP_IMAGE);

    if (!imgUrl) return null;

    // Same download logic as above...
    // ...

    return filePath;
  } finally {
    await popup.close();
  }
}
```

## PDF Generation

```typescript
// src-crawler/src/pdf-downloader.ts
export async function savePdf(
  page: Page,
  context: BrowserContext,
  outputDir: string,
  filename: string
): Promise<string | null> {
  try {
    // Click print button
    await page.click(SELECTORS.PRINT_BUTTON);

    // Wait for popup window
    const popup = await context.waitForEvent('page', { timeout: 10000 });
    await popup.waitForLoadState('networkidle');

    // Wait for map tiles to render
    await popup.waitForTimeout(TIMING.PDF_RENDER_WAIT);

    // Generate PDF
    await mkdir(outputDir, { recursive: true });
    const filePath = join(outputDir, `${filename}.pdf`);
    await popup.pdf({
      path: filePath,
      format: 'A4',
      printBackground: true,
    });

    await popup.close();
    return filePath;
  } catch {
    return null;
  }
}
```

## Retry Logic Pattern

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = TIMING.MAX_RETRIES,
  waitMs = TIMING.DEFAULT_WAIT
): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      if (attempt < maxRetries) {
        await new Promise(r => setTimeout(r, waitMs));
      }
    }
  }

  throw lastError;
}
```

## Critical Porting Notes

1. **EUC-KR Encoding**: AJAX response may use EUC-KR. Use `iconv-lite` or `TextDecoder` with fallback.
2. **Session Cookies**: Image URLs require authenticated browser session. Always download via `page.evaluate(fetch(...))`.
3. **Page Refresh**: Always navigate to BASE_URL before each search to prevent stale data.
4. **Scale Handling**: Default 1/1200 uses main page image. Other scales require popup window.
5. **PDF Headless Only**: `page.pdf()` only works in headless mode (Playwright limitation).
6. **Cleanup**: Always close browser on exit, even on errors. Use try/finally.
