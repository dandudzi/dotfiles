---
name: typescript-scaffold
description: >
  TypeScript project scaffolding: project-type detection, directory structure
  templates, tsconfig configuration, environment patterns, and tooling setup
  for Next.js, Node.js API, library, and CLI projects using pnpm and
  TypeScript 5.5+ (6.0 RC as of March 2026).
model: sonnet
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

---

## React Props

- Define component props with a named `interface` or `type`
- Type callback props explicitly
- Do not use `React.FC` unless there is a specific reason to do so

```typescript
interface UserCardProps {
  user: User
  onSelect: (id: string) => void
}

function UserCard({ user, onSelect }: UserCardProps) {
  return <button onClick={() => onSelect(user.id)}>{user.email}</button>
}
```

## JSDoc for JavaScript Files

In `.js` and `.jsx` files, use JSDoc when types improve clarity and a TypeScript migration is not practical:

```javascript
/**
 * @param {{ firstName: string, lastName: string }} user
 * @returns {string}
 */
export function formatUser(user) {
  return `${user.firstName} ${user.lastName}`
}
```

## Immutability

Use spread operator for object/array updates. Use `Readonly<T>` for immutable type contracts:

```typescript
const updated = { ...user, name: 'new' }
```

## Error Handling

Use try-catch with `catch (error: unknown)` and type narrowing:

```typescript
async function loadUser(userId: string): Promise<User> {
  try {
    return await riskyOperation(userId)
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'Unexpected error'
    logger.error('Operation failed', message)
    throw new Error(message)
  }
}
```

## Input Validation

Use Zod for schema-based validation and infer types from the schema:

```typescript
const userSchema = z.object({ email: z.email(), age: z.number().int().min(0) })
type User = z.infer<typeof userSchema>
const user = userSchema.parse(input)
```

## Logging

Never use `console.log()` in production — use a structured logger:
- Prefer `pino` (fastest) or `winston` for Node.js services
- Output JSON in production, human-readable in development
- Include `level`, `timestamp`, `message`, and structured context fields

## Formatting

Use Prettier for all formatting:
- Configuration: 2-space indent, single quotes, semicolons required
- Run `prettier --check` in CI — fail on unformatted files
- Use ESLint for linting (separate concern from formatting)

## TypeScript Code Quality Checklist

- [ ] No `any` types — use `unknown` or generics
- [ ] No `console.log()` — use structured logger
- [ ] Strict mode enabled in tsconfig
- [ ] All public API exports have explicit types
