---
name: react-19-patterns
description: React 19 features, form handling, compiler optimizations, and Server Component performance patterns. Use when building with React 19+ or optimizing RSC applications.
model: sonnet
---

# React 19 Patterns

## When to Activate

- Building or upgrading to React 19+ applications
- Using `use()`, `useActionState`, `useFormStatus`, or React Compiler features
- Optimizing Server Component performance or RSC streaming patterns

## use() Hook

Unwraps promises and context values for cleaner async component patterns:

```typescript
import { use } from 'react';

// Unwrap promises in Server/Client Components
export function DataComponent({ dataPromise }: { dataPromise: Promise<any> }) {
  const data = use(dataPromise);
  return <div>{data.title}</div>;
}

// Read context without Consumer wrapper
const ThemeContext = createContext('light');

export function ThemedButton() {
  const theme = use(ThemeContext); // Cleaner than useContext
  return <button className={theme}>Click</button>;
}
```

## Form Actions and useActionState

Server Actions with built-in form state management:

```typescript
// Server Action
async function submitForm(prevState: any, formData: FormData) {
  const email = formData.get('email');
  const result = await saveEmail(email);
  return result.success ? { message: 'Saved!' } : { error: result.error };
}

// Client Component using useActionState
import { useActionState } from 'react';

export function EmailForm() {
  const [state, formAction, isPending] = useActionState(submitForm, null);

  return (
    <form action={formAction}>
      <input name="email" type="email" required />
      <button disabled={isPending}>
        {isPending ? 'Saving...' : 'Save'}
      </button>
      {state?.error && <p className="error">{state.error}</p>}
      {state?.message && <p className="success">{state.message}</p>}
    </form>
  );
}
```

## useFormStatus Hook

Monitor form submission state without prop drilling:

```typescript
import { useFormStatus } from 'react-dom';

export function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button disabled={pending} type="submit">
      {pending ? 'Loading...' : 'Submit'}
    </button>
  );
}

// Use in the same form without passing state down
export function MyForm() {
  return (
    <form action={serverAction}>
      <input name="name" />
      <SubmitButton /> {/* Accesses form state automatically */}
    </form>
  );
}
```

## Compiler Optimizations (Stable RC)

React 19 compiler automatically memoizes components:

```typescript
// The React Compiler automatically memoizes this — no React.memo needed
export function SlowComponent({ data }: { data: { items: string[] } }) {
  const count = data.items.length;
  return (
    <div>
      {data.items.map((item) => (
        <Item key={item} name={item} />
      ))}
      <Counter count={count} />
    </div>
  );
}
```

## Performance Patterns

### Server Components for Data
Fetch data in Server Components to eliminate client-side waterfalls:

```typescript
// app/posts/page.tsx
export default async function PostsPage() {
  const posts = await fetch('https://api.example.com/posts', {
    next: { revalidate: 3600 } // ISR
  }).then(r => r.json());
  return <PostsList posts={posts} />;
}
```

### Selective Client Interactivity
Isolate interactive features to small client components:

```typescript
// Server Component
export default async function ProductPage() {
  const product = await getProduct();
  return (
    <div>
      <h1>{product.name}</h1>
      <p>{product.description}</p>
      <AddToCartButton product={product} /> {/* Only this is "use client" */}
    </div>
  );
}

// Client Component
'use client';
export function AddToCartButton({ product }: { product: Product }) {
  const [quantity, setQuantity] = useState(1);
  return (
    <button onClick={() => addToCart(product.id, quantity)}>
      Add to Cart
    </button>
  );
}
```

### Suspense for Progressive Rendering
Stream non-critical content independently:

```typescript
export default async function Dashboard() {
  return (
    <div>
      <h1>Dashboard</h1>
      <UserProfile /> {/* Critical: renders immediately */}
      <Suspense fallback={<LoadingSpinner />}>
        <RecommendedProducts /> {/* Streams separately */}
      </Suspense>
      <Suspense fallback={<LoadingSkeleton />}>
        <Analytics />
      </Suspense>
    </div>
  );
}
```

### Memoization (Only When Necessary)
Profile before memoizing; React 19 compiler handles many cases automatically:

```typescript
// Use React.memo only for expensive pure components
export const MemoizedList = React.memo(function List({ items }: { items: string[] }) {
  return <ul>{items.map(item => <li key={item}>{item}</li>)}</ul>;
});

// useCallback for callbacks passed to memoized children
export function Parent({ onUpdate }: { onUpdate: (x: string) => void }) {
  const handleUpdate = useCallback((value: string) => {
    onUpdate(value);
  }, [onUpdate]);
  return <MemoizedChild onUpdate={handleUpdate} />;
}
```

### Bundle Size Optimization
Use dynamic imports and code splitting:

```typescript
import dynamic from 'next/dynamic';

const HeavyChart = dynamic(() => import('./Chart'), {
  loading: () => <p>Loading chart...</p>,
  ssr: false
});
```
