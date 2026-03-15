---
name: typescript-scaffold
description: >
  TypeScript project scaffolding: project-type detection, directory structure
  templates, tsconfig configuration, environment patterns, and tooling setup
  for Next.js, Node.js API, library, and CLI projects using pnpm and
  TypeScript 5.5+ (6.0 RC as of March 2026).
---

# TypeScript 5.5+ Project Scaffolding

## When to Activate

Trigger on phrases like:
- "scaffold a TypeScript project", "set up TypeScript"
- "new Next.js project", "new Node.js API", "create a library"
- "TypeScript project structure", "tsconfig setup"
- "pnpm workspace", "monorepo TypeScript setup"
- "CLI project TypeScript", "npm package TypeScript"

## Project Type Detection

Identify project type from context before scaffolding:

| Indicator | Project Type |
|-----------|-------------|
| "Next.js", "App Router", "RSC" | Next.js app (see **nextjs-expert** and **react-expert** agents) |
| "REST API", "Express", "Fastify", "Hono" | Node.js API |
| "npm package", "publish to npm", "library" | TypeScript library |
| "CLI tool", "command-line", "bin" | CLI project |
| Multiple apps, shared packages | pnpm monorepo |

## Directory Structures

### Next.js App (App Router)

```
my-app/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── (routes)/
│   ├── components/
│   │   ├── ui/
│   │   └── features/
│   ├── lib/
│   │   ├── db.ts
│   │   └── auth.ts
│   ├── hooks/
│   ├── types/
│   └── env.ts
├── public/
├── package.json
├── tsconfig.json
└── next.config.ts
```

### Node.js API

```
my-api/
├── src/
│   ├── index.ts
│   ├── app.ts
│   ├── routes/
│   ├── services/
│   ├── repositories/
│   ├── middleware/
│   ├── types/
│   └── config.ts
├── tests/
│   ├── unit/
│   └── integration/
├── package.json
└── tsconfig.json
```

### TypeScript Library

```
my-lib/
├── src/
│   ├── index.ts
│   ├── types.ts
│   └── internal/
├── tests/
├── dist/
├── package.json
└── tsconfig.json
```

### CLI Project

```
my-cli/
├── src/
│   ├── index.ts
│   ├── commands/
│   ├── utils/
│   └── types.ts
├── bin/
│   └── my-cli
├── package.json
└── tsconfig.json
```

## tsconfig Templates

### Base (strict, for all projects)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

### Next.js addition

```json
{
  "extends": "./tsconfig.base.json",
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "ES2022"],
    "jsx": "preserve",
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  }
}
```

### Library (emit declarations)

```json
{
  "extends": "./tsconfig.base.json",
  "compilerOptions": {
    "declaration": true,
    "declarationMap": true,
    "outDir": "dist",
    "rootDir": "src"
  }
}
```

## Type-Safe Environment Pattern

```typescript
// src/env.ts
import { z } from "zod";

const schema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]),
  DATABASE_URL: z.string().url(),
  API_KEY: z.string().min(1),
});

export const env = schema.parse(process.env);
// Throws at startup if env vars are missing or invalid
```

## Library package.json Essentials

```json
{
  "name": "my-lib",
  "version": "0.1.0",
  "type": "module",
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "types": "./dist/index.d.ts"
    }
  },
  "files": ["dist"],
  "scripts": {
    "build": "tsc",
    "test": "vitest run",
    "typecheck": "tsc --noEmit"
  }
}
```

## pnpm Workspace (Monorepo)

```yaml
# pnpm-workspace.yaml
packages:
  - "apps/*"
  - "packages/*"
```

## pnpm-workspace.yaml

Example workspace root configuration:

```yaml
packages:
  - "apps/web"
  - "apps/api"
  - "packages/ui"
  - "packages/shared"
  - "packages/utils"
```

## Tooling Checklist

- [ ] TypeScript 5.5+ (6.0 when stable)
- [ ] `strict: true` + `noUncheckedIndexedAccess`
- [ ] ESLint with `@typescript-eslint/recommended-type-checked`
- [ ] Prettier for formatting
- [ ] Vitest for testing
- [ ] Type-safe env validation at startup
- [ ] `"type": "module"` in package.json
- [ ] `.gitignore` includes `dist/`, `node_modules/`, `.env`
- [ ] Source maps enabled for production debugging
- [ ] SWC or esbuild for faster builds

## Build and Development

### Dev Mode
```bash
# Watch mode with type checking
pnpm run dev

# Type checking without emit
pnpm run typecheck
```

### Production Build
```bash
# Type-check and emit
pnpm run build

# Verify outputs
ls dist/
```

## Agent Support
- **typescript-expert** — Type system design and complex generics
- **nextjs-expert** — Next.js project structure and configuration
- **nodejs-expert** — Node.js API and library scaffolding

## Skill References
- **typescript-advanced-types** — Advanced type patterns for complex scenarios
- **modern-javascript** — ES2022+ features and patterns
