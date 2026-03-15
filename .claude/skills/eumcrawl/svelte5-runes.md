---
name: eumcrawl-svelte5-runes
description: >
  Svelte 5 Runes patterns for EUM Crawler Desktop.
  $state, $derived, $effect, $props, $bindable, class-based stores,
  and migration patterns from Svelte 4 legacy stores.
user-invocable: false
metadata:
  version: "1.0.0"
  category: "language"
  status: "active"
  updated: "2026-03-10"
  tags: "svelte, svelte5, runes, state, derived, effect, props, store"

progressive_disclosure:
  enabled: true
  level1_tokens: 100
  level2_tokens: 5000

triggers:
  keywords: ["svelte", "runes", "$state", "$derived", "$effect", "store", "component", "svelte5"]
  agents: ["eumcrawl-svelte-frontend"]
---

# Svelte 5 Runes Patterns

## Core Runes Reference

### $state - Reactive State
```svelte
<script lang="ts">
  // Primitive state
  let count = $state(0);
  let name = $state('');

  // Object state (deeply reactive)
  let user = $state({ name: 'Kim', age: 30 });

  // Array state (deeply reactive)
  let items = $state<string[]>([]);

  // Set/Map state
  let selectedIds = $state(new Set<number>());
</script>
```

### $derived - Computed Values
```svelte
<script lang="ts">
  let items = $state<Item[]>([]);
  let filter = $state('all');

  // Simple derived
  let count = $derived(items.length);

  // Complex derived
  let filteredItems = $derived(
    filter === 'all' ? items : items.filter(i => i.status === filter)
  );

  // Derived from multiple sources
  let summary = $derived(`${filteredItems.length} / ${items.length} items`);
</script>
```

### $effect - Side Effects
```svelte
<script lang="ts">
  let searchQuery = $state('');

  // Auto-tracks dependencies
  $effect(() => {
    if (searchQuery.length >= 2) {
      loadResults(searchQuery);
    }
  });

  // Cleanup pattern
  $effect(() => {
    const timer = setInterval(() => tick(), 1000);
    return () => clearInterval(timer);
  });

  // One-time initialization
  $effect(() => {
    untrack(() => {
      initializeApp();
    });
  });
</script>
```

### $props - Component Props
```svelte
<script lang="ts">
  // Typed props with defaults
  let {
    title,
    count = 0,
    onSelect,
    items = [],
    class: className = '',
  }: {
    title: string;
    count?: number;
    onSelect?: (id: number) => void;
    items?: Item[];
    class?: string;
  } = $props();
</script>
```

### $bindable - Two-way Binding
```svelte
<!-- Parent -->
<SearchInput bind:value={searchQuery} />

<!-- SearchInput.svelte -->
<script lang="ts">
  let { value = $bindable('') }: { value?: string } = $props();
</script>
<input bind:value />
```

## Class-Based Store Pattern (Recommended for EUM Crawler)

### Store Definition
```typescript
// src/lib/stores/addresses.svelte.ts
import { addressService } from '$lib/services/address.service';
import type { Address, PaginatedResult } from '$lib/types';

class AddressStore {
  // Reactive state
  addresses = $state<Address[]>([]);
  total = $state(0);
  page = $state(1);
  perPage = $state(20);
  search = $state('');
  group = $state<string | null>(null);
  loading = $state(false);
  error = $state<string | null>(null);

  // Selection state
  selectedIds = $state<Set<number>>(new Set());

  // Derived values
  hasSelection = $derived(this.selectedIds.size > 0);
  selectedCount = $derived(this.selectedIds.size);
  totalPages = $derived(Math.ceil(this.total / this.perPage));
  isEmpty = $derived(this.addresses.length === 0 && !this.loading);

  // Actions
  async load() {
    this.loading = true;
    this.error = null;
    try {
      const result = await addressService.getAll({
        page: this.page,
        per_page: this.perPage,
        search: this.search || undefined,
        group: this.group || undefined,
      });
      this.addresses = result.data;
      this.total = result.total;
    } catch (e) {
      this.error = e instanceof Error ? e.message : String(e);
    } finally {
      this.loading = false;
    }
  }

  async add(data: CreateAddressInput) {
    const address = await addressService.add(data);
    await this.load(); // Refresh list
    return address;
  }

  async deleteSelected() {
    if (this.selectedIds.size === 0) return;
    await addressService.delete([...this.selectedIds]);
    this.selectedIds.clear();
    await this.load();
  }

  toggleSelect(id: number) {
    if (this.selectedIds.has(id)) {
      this.selectedIds.delete(id);
    } else {
      this.selectedIds.add(id);
    }
  }

  selectAll() {
    this.addresses.forEach(a => this.selectedIds.add(a.id));
  }

  clearSelection() {
    this.selectedIds.clear();
  }

  setPage(page: number) {
    this.page = page;
    this.load();
  }

  setSearch(query: string) {
    this.search = query;
    this.page = 1;
    this.load();
  }
}

export const addressStore = new AddressStore();
```

### Using Store in Components
```svelte
<script lang="ts">
  import { addressStore } from '$lib/stores/addresses.svelte';
  import { onMount } from 'svelte';

  onMount(() => {
    addressStore.load();
  });
</script>

{#if addressStore.loading}
  <Skeleton />
{:else if addressStore.isEmpty}
  <EmptyState message="주소가 없습니다" />
{:else}
  {#each addressStore.addresses as address (address.id)}
    <TableRow
      selected={addressStore.selectedIds.has(address.id)}
      onclick={() => addressStore.toggleSelect(address.id)}
    >
      {address.address}
    </TableRow>
  {/each}
{/if}
```

## All EUM Crawler Stores

```typescript
// addresses.svelte.ts - Address CRUD, import, groups
// results.svelte.ts   - Result search, filter, pagination
// jobs.svelte.ts      - Job CRUD, real-time progress, logs
// settings.svelte.ts  - Settings CRUD, cache config
// ui.svelte.ts        - Sidebar collapsed, toasts, modals
// dashboard.svelte.ts - Stats, recent data
```

## Component Patterns

### Data Table with Selection
```svelte
<script lang="ts">
  import * as Table from '$lib/components/ui/table';
  import { Checkbox } from '$lib/components/ui/checkbox';

  let { items, selectedIds, onToggle, onSelectAll }:
    { items: Item[]; selectedIds: Set<number>; onToggle: (id: number) => void; onSelectAll: () => void } = $props();

  let allSelected = $derived(items.length > 0 && items.every(i => selectedIds.has(i.id)));
</script>

<Table.Root>
  <Table.Header>
    <Table.Row>
      <Table.Head class="w-12">
        <Checkbox checked={allSelected} onCheckedChange={onSelectAll} />
      </Table.Head>
      <Table.Head>Name</Table.Head>
    </Table.Row>
  </Table.Header>
  <Table.Body>
    {#each items as item (item.id)}
      <Table.Row>
        <Table.Cell>
          <Checkbox
            checked={selectedIds.has(item.id)}
            onCheckedChange={() => onToggle(item.id)}
          />
        </Table.Cell>
        <Table.Cell>{item.name}</Table.Cell>
      </Table.Row>
    {/each}
  </Table.Body>
</Table.Root>
```

### Modal Dialog Pattern
```svelte
<script lang="ts">
  import * as Dialog from '$lib/components/ui/dialog';

  let open = $state(false);
</script>

<Dialog.Root bind:open>
  <Dialog.Trigger>
    <Button>Open</Button>
  </Dialog.Trigger>
  <Dialog.Content>
    <Dialog.Header>
      <Dialog.Title>Title</Dialog.Title>
    </Dialog.Header>
    <!-- Content -->
    <Dialog.Footer>
      <Button variant="outline" onclick={() => open = false}>Cancel</Button>
      <Button onclick={handleSubmit}>Confirm</Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
```

### Toast Notification Pattern
```typescript
// src/lib/stores/ui.svelte.ts
interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

class UIStore {
  toasts = $state<Toast[]>([]);
  sidebarCollapsed = $state(false);

  addToast(type: Toast['type'], message: string, duration = 3000) {
    const id = crypto.randomUUID();
    this.toasts.push({ id, type, message, duration });
    if (duration > 0) {
      setTimeout(() => this.removeToast(id), duration);
    }
  }

  removeToast(id: string) {
    this.toasts = this.toasts.filter(t => t.id !== id);
  }

  success(msg: string) { this.addToast('success', msg); }
  error(msg: string) { this.addToast('error', msg, 0); } // persistent
  warn(msg: string) { this.addToast('warning', msg, 5000); }
  info(msg: string) { this.addToast('info', msg); }
}

export const uiStore = new UIStore();
```

## Important: DO NOT Use Legacy Patterns

```typescript
// WRONG - Svelte 4 legacy store
import { writable } from 'svelte/store';
const count = writable(0);

// CORRECT - Svelte 5 runes
let count = $state(0);
```

```svelte
<!-- WRONG - Svelte 4 reactive declaration -->
$: doubled = count * 2;

<!-- CORRECT - Svelte 5 derived -->
let doubled = $derived(count * 2);
```
