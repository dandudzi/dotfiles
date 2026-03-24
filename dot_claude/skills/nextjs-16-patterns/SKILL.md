---
name: nextjs-16-patterns
description: Next.js 16 breaking changes, async request APIs, caching defaults, cacheComponents, and Pages Router migration patterns. Use when upgrading to Next.js 16 or migrating from Pages Router.
model: sonnet
---

# Next.js 16 Patterns

## When to Activate

- Upgrading from Next.js 15 to Next.js 16
- Migrating synchronous `cookies()`, `headers()`, `params`, or `searchParams` to async
- Configuring Next.js 16 caching defaults or `cacheComponents`
- Migrating from Pages Router to App Router

## Breaking Changes

### Async Request APIs (Mandatory)

Synchronous access to `cookies`, `headers`, `draftMode`, `params`, and `searchParams` is **fully removed** in Next.js 16 — all must be awaited:

```typescript
// Next.js 16 — params and cookies are now Promises
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;          // REQUIRED: await params
  const cookieStore = await cookies();  // REQUIRED: await cookies()
  const headersList = await headers();  // REQUIRED: await headers()
  // ...
}
```

### Caching Defaults Changed

`fetch()` is **no longer cached by default**. Explicit opt-in required:

```typescript
// Next.js 16 — no default caching
const a = await fetch('https://api.example.com/data');                        // NOT cached
const b = await fetch('https://api.example.com/data', { cache: 'force-cache' }); // cached
const c = await fetch('https://api.example.com/data', { next: { revalidate: 60 } }); // ISR
```

### cacheComponents Flag (replaces experimental.dynamicIO)

```js
// next.config.js — enables Partial Pre-Rendering (PPR)
module.exports = {
  cacheComponents: true,  // replaces experimental: { dynamicIO: true }
}
```

### Routing Performance (No Code Changes Needed)

- **Layout deduplication**: shared layouts downloaded once across prefetched URLs
- **Incremental prefetching**: only prefetches parts of a page not already in cache

## Pages Router Migration

**CRITICAL:** Pages Router (`pages/` directory) is deprecated in Next.js 13+. Migrate to App Router (`app/` directory).

### Key Changes

- `pages/api/` -> Route Handlers in `app/api/route.ts` (export `GET`, `POST`, etc.)
- `getStaticProps`, `getServerSideProps` -> Server Components with `fetch()` caching
- `_app.tsx`, `_document.tsx` -> `app/layout.tsx` (Shared layout wrapper)
- `next/router` -> `next/navigation` (useRouter, usePathname, useSearchParams)
- API middleware -> `middleware.ts` at project root

### Example Pages Router -> App Router

```typescript
// Pages Router (DEPRECATED)
// pages/posts/[id].tsx
export async function getStaticProps({ params }) {
  const post = await fetch(`/api/posts/${params.id}`).then(r => r.json());
  return { props: { post }, revalidate: 60 };
}

export default function PostPage({ post }) {
  return <h1>{post.title}</h1>;
}

// App Router (RECOMMENDED)
// app/posts/[id]/page.tsx
export default async function PostPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const post = await fetch(`https://api.example.com/posts/${id}`, {
    next: { revalidate: 60 } // ISR
  }).then(r => r.json());
  return <h1>{post.title}</h1>;
}
```
