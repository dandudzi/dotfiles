---
name: virtual-threads-patterns
description: Project Loom virtual threads, structured concurrency, carrier thread pinning avoidance, and I/O-bound workload patterns for Java 21+.
origin: ECC
---

# Virtual Threads Patterns (Java 21+ LTS, stable since Sept 2023)

## When to Activate

- Building I/O-heavy applications (web servers, microservices handling thousands of concurrent requests)
- Migrating from thread pool executors to virtual thread executors
- Designing structured concurrency with `StructuredTaskScope` (Java 21+, finalized in Java 23)
- Optimizing Spring Boot 3.2+ applications for high throughput
- Avoiding carrier thread pinning issues in blocking JNI or synchronized blocks
- Measuring virtual thread performance vs traditional platform threads

**Minimum JVM**: Java 21 LTS (Sept 2023). Java 23+ recommended for finalized StructuredTaskScope APIs.

## Core Concept 1: Virtual Threads vs Platform Threads

**Platform threads** (traditional Java threads):
- 1:1 mapping to OS kernel threads
- ~2 MB stack memory per thread
- Context switching overhead; OS manages scheduling
- Limited concurrency: ~thousands of threads max
- Good for CPU-bound work

**Virtual threads** (Project Loom, Java 21+):
- Lightweight, user-space threads managed by JVM scheduler
- ~1-10 KB stack memory per thread
- Can suspend/resume at I/O boundaries without OS context switch
- Supports millions of concurrent virtual threads
- Excellent for I/O-bound work (network, database, files)

### When to Use Virtual Threads
- REST APIs handling 10,000+ concurrent requests
- Microservices awaiting external API responses
- Database connection handling
- File system operations (reading/writing)
- Network I/O (HTTP clients)

### When NOT to Use Virtual Threads
- CPU-bound algorithms (heavy computation)
- Real-time systems with strict latency guarantees
- Code heavily reliant on ThreadLocal variables
- JNI code that blocks (pins carrier threads)

## Core Concept 2: Creating and Running Virtual Threads

### Pattern 1: Basic Virtual Thread Creation

```java
// Java 21+
public class VirtualThreadExample {
    public static void main(String[] args) throws InterruptedException {
        // Create a single virtual thread
        Thread vthread = Thread.ofVirtual()
            .name("virtual-worker")
            .start(() -> {
                System.out.println("Running in virtual thread");
                // Simulate I/O work
                try {
                    Thread.sleep(1000);  // Virtual thread yields; carrier thread free
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
                System.out.println("Virtual thread complete");
            });

        vthread.join();
    }
}
```

### Pattern 2: Virtual Thread Per Task Executor

Use `Executors.newVirtualThreadPerTaskExecutor()` for concurrent workloads:

```java
import java.util.concurrent.*;

public class VirtualThreadExecutorExample {
    public static void main(String[] args) throws InterruptedException {
        // Create executor that spawns a virtual thread per task
        try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {

            for (int i = 0; i < 10000; i++) {
                final int taskId = i;
                executor.submit(() -> {
                    try {
                        // Simulate I/O work (HTTP request, database query)
                        Thread.sleep(100);
                        System.out.println("Task " + taskId + " completed");
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                    }
                });
            }

            // Wait for all tasks
            executor.shutdown();
            executor.awaitTermination(10, TimeUnit.MINUTES);
        }
    }
}
```

### Pattern 3: Named Virtual Threads for Debugging

```java
public class NamedVirtualThreads {
    public static void main(String[] args) throws InterruptedException {
        // Virtual threads with custom names aid debugging
        ThreadFactory factory = Thread.ofVirtual()
            .name("io-worker-", 0)  // Generates "io-worker-0", "io-worker-1", etc.
            .factory();

        try (ExecutorService executor = Executors.newThreadPerTaskExecutor(factory)) {
            for (int i = 0; i < 5; i++) {
                executor.submit(() -> {
                    System.out.println("Running in " + Thread.currentThread().getName());
                });
            }

            executor.shutdown();
            executor.awaitTermination(5, TimeUnit.SECONDS);
        }
    }
}
```

## Core Concept 3: Structured Concurrency with StructuredTaskScope\n\nStructured concurrency ensures all spawned threads complete before a scope exits. Prevents resource leaks and orphaned threads.

**API Status**: Preview in Java 19-20, finalized in Java 21 LTS. Full stable API (no --enable-preview) in Java 23+.\n\n**API Status**: Preview in Java 19-20, finalized in Java 21 LTS. Full stable API (no --enable-preview) in Java 23+.\n\n## Placeholder

Structured concurrency ensures all spawned threads complete before a scope exits. Prevents resource leaks and orphaned threads.

**API Status**: Preview in Java 19-20, finalized in Java 21 LTS. Full stable API (no --enable-preview) in Java 23+.

### Pattern 4: Fork-Join with Structured Task Scope

```java
import java.util.concurrent.*;

public class StructuredConcurrencyExample {

    public static String fetchUserData(int userId) throws Exception {
        // Simulate API call
        Thread.sleep(100);
        return "User-" + userId;
    }

    public static String fetchUserPreferences(int userId) throws Exception {
        // Simulate API call
        Thread.sleep(150);
        return "Prefs-" + userId;
    }

    public static String getUserProfile(int userId) throws Exception {
        // StructuredTaskScope ensures both tasks complete before returning
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {

            Callable<String> userTask = scope.fork(() -> fetchUserData(userId));
            Callable<String> prefTask = scope.fork(() -> fetchUserPreferences(userId));

            scope.joinUntilComplete();  // Wait for both tasks
            scope.throwIfFailed();       // Propagate exceptions

            String userData = userTask.resultNow();
            String prefs = prefTask.resultNow();

            return userData + " | " + prefs;
        }
    }

    public static void main(String[] args) throws Exception {
        String profile = getUserProfile(123);
        System.out.println(profile);  // Output: User-123 | Prefs-123
    }
}
```

### Pattern 5: Error Handling with StructuredTaskScope

```java
import java.util.concurrent.*;

public class StructuredErrorHandling {

    public static class Result {
        public final String value;
        public final Exception error;

        public Result(String value, Exception error) {
            this.value = value;
            this.error = error;
        }
    }

    public static void main(String[] args) throws Exception {
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {

            Callable<String> task1 = scope.fork(() -> {
                Thread.sleep(100);
                return "Success";
            });

            Callable<String> task2 = scope.fork(() -> {
                Thread.sleep(150);
                throw new RuntimeException("Simulated failure");
            });

            // ShutdownOnFailure cancels other tasks and propagates exception
            try {
                scope.joinUntilComplete();
                scope.throwIfFailed();
            } catch (Exception e) {
                System.out.println("One or more tasks failed: " + e.getMessage());
                // Handle gracefully
            }
        }
    }
}
```

## Core Concept 4: Carrier Thread Pinning

When a virtual thread blocks inside a `synchronized` block or blocking JNI call, it **pins** its carrier thread. This prevents the JVM scheduler from moving other virtual threads to that carrier, reducing throughput.

### Anti-Pattern 1: Synchronized Blocks Pin Carrier Threads

```java
// BAD: Synchronized methods pin carrier threads
public class PinnedThreadExample {

    private int counter = 0;

    // This blocks the carrier thread while holding monitor
    public synchronized void increment() {
        counter++;
        try {
            Thread.sleep(100);  // PINS carrier thread; no other virtual threads run
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    // Virtual thread calling this will pin its carrier
    public void badConcurrency() throws InterruptedException {
        Thread vthread = Thread.ofVirtual()
            .start(this::increment);
        vthread.join();
    }
}
```

### Pattern 6: ReentrantLock Instead of Synchronized

```java
import java.util.concurrent.locks.*;

public class NonPinningExample {

    private int counter = 0;
    private final ReentrantLock lock = new ReentrantLock();

    // GOOD: ReentrantLock releases carrier thread while waiting
    public void increment() {
        lock.lock();
        try {
            counter++;
            try {
                Thread.sleep(100);  // Does NOT pin carrier thread
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        } finally {
            lock.unlock();
        }
    }

    public void goodConcurrency() throws InterruptedException {
        try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < 1000; i++) {
                executor.submit(this::increment);
            }
            executor.shutdown();
            executor.awaitTermination(5, TimeUnit.SECONDS);
        }
    }
}
```

### Pattern 7: Avoiding JNI Blocking

```java
public class JNIBlocking {

    private native void nativeBlockingCall();  // This blocks carrier thread

    // WRONG: Don't call blocking JNI from virtual thread
    public void badNativeCall() {
        nativeBlockingCall();  // Pins carrier thread
    }

    // BETTER: Use dedicated platform thread pool for blocking JNI
    private static final ExecutorService nativeExecutor =
        Executors.newFixedThreadPool(10);  // Platform threads only

    public void goodNativeCall() throws Exception {
        Future<Void> result = nativeExecutor.submit(() -> {
            nativeBlockingCall();  // Runs on platform thread, doesn't pin virtual
            return null;
        });
        result.get();
    }
}
```

## Core Concept 5: Spring Boot 3.2+ Virtual Thread Integration

Spring Boot 3.2+ auto-detects `newVirtualThreadPerTaskExecutor()` and uses it if available.

### Pattern 8: Spring Boot Virtual Thread Configuration

```java
import org.springframework.boot.autoconfigure.web.servlet.ServletWebServerFactoryCustomizer;
import org.springframework.boot.web.embedded.tomcat.TomcatServletWebServerFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class VirtualThreadConfig {

    /**
     * Enable virtual threads for Tomcat (Spring Boot 3.2+)
     * Alternative: Set application.properties:
     *   server.tomcat.threads.virtual-enabled=true
     */
    @Bean
    public ServletWebServerFactoryCustomizer<TomcatServletWebServerFactory>
    tomcatCustomizer() {
        return factory -> {
            factory.setProtocol("org.apache.coyote.http11.Http11NioProtocol");
            // Virtual threads enabled automatically if on Java 21+
        };
    }
}
```

Or in `application.properties`:
```properties
server.tomcat.threads.virtual-enabled=true
```

### Pattern 9: Spring MVC with Virtual Threads

```java
import org.springframework.web.bind.annotation.*;
import java.net.http.*;

@RestController
@RequestMapping("/api")
public class VirtualThreadController {

    private static final HttpClient httpClient = HttpClient.newBuilder()
        .version(HttpClient.Version.HTTP_2)
        .build();

    /**
     * Each request runs on a virtual thread.
     * I/O operations (HTTP calls, DB queries) free the carrier thread.
     */
    @GetMapping("/data/{id}")
    public DataResponse getData(@PathVariable int id) throws Exception {
        // Simulate fetching from multiple services
        HttpRequest request = HttpRequest.newBuilder()
            .uri(new java.net.URI("https://api.example.com/user/" + id))
            .GET()
            .build();

        HttpResponse<String> response = httpClient.send(request,
            HttpResponse.BodyHandlers.ofString());

        return new DataResponse(id, response.body());
    }

    @GetMapping("/concurrent/{id}")
    public CombinedResponse getConcurrent(@PathVariable int id) throws Exception {
        try (var scope = new java.util.concurrent.StructuredTaskScope.ShutdownOnFailure()) {

            var userTask = scope.fork(() -> fetchUser(id));
            var prefsTask = scope.fork(() -> fetchPrefs(id));

            scope.joinUntilComplete();
            scope.throwIfFailed();

            return new CombinedResponse(
                userTask.resultNow(),
                prefsTask.resultNow()
            );
        }
    }

    private String fetchUser(int id) throws Exception {
        // HTTP call yields carrier thread
        return "User-" + id;
    }

    private String fetchPrefs(int id) throws Exception {
        // HTTP call yields carrier thread
        return "Prefs-" + id;
    }
}

record DataResponse(int id, String data) {}
record CombinedResponse(String user, String prefs) {}
```

## Core Concept 6: Migration from Thread Pools

### Pattern 10: Migrating from Fixed Thread Pool

```java
// BEFORE: Fixed thread pool, limited concurrency
ExecutorService executor = Executors.newFixedThreadPool(100);

for (int i = 0; i < 10000; i++) {
    final int id = i;
    executor.submit(() -> {
        // Can handle max 100 concurrent tasks
        handleRequest(id);
    });
}
executor.shutdown();

// AFTER: Virtual thread per task, handles 10000+ concurrent
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
    for (int i = 0; i < 10000; i++) {
        final int id = i;
        executor.submit(() -> {
            // Can handle 10000+ concurrent tasks
            handleRequest(id);
        });
    }
    executor.shutdown();
    executor.awaitTermination(1, TimeUnit.HOURS);
}
```

### Pattern 11: Monitoring Virtual Thread Creation

```java
import java.util.concurrent.*;
import java.lang.management.*;

public class VirtualThreadMonitoring {

    public static void main(String[] args) throws Exception {
        ThreadMXBean threadMxBean = ManagementFactory.getThreadMXBean();

        try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < 1000; i++) {
                executor.submit(() -> {
                    try {
                        Thread.sleep(1000);
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                    }
                });
            }

            // Platform threads: few (e.g., 8 for 8-core CPU)
            // Virtual threads: 1000+
            System.out.println("Platform threads: " + threadMxBean.getThreadCount());
            System.out.println("Peak threads: " + threadMxBean.getPeakThreadCount());

            executor.shutdown();
            executor.awaitTermination(2, TimeUnit.SECONDS);
        }
    }
}
```

## Core Concept 7: ThreadLocal Considerations

Virtual threads can use ThreadLocal, but be aware of memory accumulation across millions of threads.

### Pattern 12: Scoped Values (Java 19+ Preview, finalized Java 21 LTS)

```java
import java.lang.ScopedValue;

public class ScopedValueExample {

    // Scoped value replaces ThreadLocal for virtual threads
    private static final ScopedValue<String> USER_CONTEXT =
        ScopedValue.newInstance();

    public static void main(String[] args) throws Exception {
        // Bind scoped value for this execution
        ScopedValue.callWhere(USER_CONTEXT, "user-123", () -> {
            processRequest();
        });
    }

    private static void processRequest() {
        String user = USER_CONTEXT.get();
        System.out.println("Processing for: " + user);
    }
}
```

## Anti-Patterns

### WRONG: Blocking I/O Without Virtual Threads

```java
// ANTI-PATTERN: Platform threads with blocking pool (thousands limit)
ExecutorService executor = Executors.newFixedThreadPool(100);

for (int i = 0; i < 10000; i++) {
    executor.submit(() -> {
        // Only 100 tasks run concurrently
        // Remaining 9900 queue and wait (high latency)
        makeHttpRequest();
    });
}
```

### CORRECT: Virtual Threads for I/O

```java
// CORRECT: Virtual threads (unlimited concurrency)
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
    for (int i = 0; i < 10000; i++) {
        executor.submit(() -> {
            // All 10000 tasks run concurrently (low latency)
            makeHttpRequest();
        });
    }
}
```

### WRONG: Synchronized Blocks with Virtual Threads

```java
// ANTI-PATTERN: Synchronized pinning carrier threads
public synchronized void criticalSection() {
    try {
        Thread.sleep(1000);  // Holds lock AND pins carrier (bad)
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
    }
}
```

### CORRECT: ReentrantLock with Virtual Threads

```java
// CORRECT: Lock that doesn't pin
private final ReentrantLock lock = new ReentrantLock();

public void criticalSection() {
    lock.lock();
    try {
        Thread.sleep(1000);  // Releases carrier thread while holding lock
    } finally {
        lock.unlock();
    }
}
```

### WRONG: Heavy ThreadLocal Usage

```java
// ANTI-PATTERN: Millions of virtual threads + ThreadLocal = memory leak
ThreadLocal<ExpensiveResource> resource = new ThreadLocal<>();

try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
    for (int i = 0; i < 1_000_000; i++) {
        executor.submit(() -> {
            resource.set(new ExpensiveResource());  // Accumulates in memory
            // ... use resource
        });
    }
}
```

### CORRECT: ScopedValue or Explicit Cleanup

```java
// CORRECT: ScopedValue is auto-cleaned per scope
private static final ScopedValue<ExpensiveResource> resource =
    ScopedValue.newInstance();

try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
    for (int i = 0; i < 1_000_000; i++) {
        executor.submit(() -> {
            ScopedValue.callWhere(resource, new ExpensiveResource(), () -> {
                // ... use resource; auto-cleaned when scope exits
            });
        });
    }
}
```

## Best Practices

### Do This

```java
// GOOD: Virtual threads for I/O-bound work
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
    for (int i = 0; i < 10000; i++) {
        executor.submit(() -> performIoOperation());
    }
    executor.shutdown();
    executor.awaitTermination(1, TimeUnit.HOURS);
}

// GOOD: Structured concurrency ensures cleanup
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    var task1 = scope.fork(() -> fetchData());
    var task2 = scope.fork(() -> fetchMetadata());

    scope.joinUntilComplete();
    scope.throwIfFailed();

    return combine(task1.resultNow(), task2.resultNow());
}

// GOOD: ReentrantLock for synchronization
private final ReentrantLock lock = new ReentrantLock();

public void criticalSection() {
    lock.lock();
    try {
        // Critical work without pinning
    } finally {
        lock.unlock();
    }
}

// GOOD: Monitor virtual thread behavior
System.setProperty("jdk.tracePinnedThreads", "short");
System.setProperty("jdk.traceVirtualThreadEvents", "true");
```

### Don't Do This

```java
// BAD: CPU-bound work on virtual threads (no benefit)
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
    executor.submit(() -> performExpensiveComputation());  // Waste
}

// BAD: Synchronized blocks (pins carrier threads)
public synchronized void process() {
    try {
        Thread.sleep(1000);  // PINS
    } catch (InterruptedException e) {}
}

// BAD: Blocking JNI calls (pins carrier threads)
public void callNative() {
    nativeBlockingMethod();  // PINS
}

// BAD: Unbounded virtual thread creation
for (int i = 0; i < 1_000_000; i++) {
    Thread.ofVirtual().start(() -> {}); // Memory exhaustion
}

// BAD: Heavy ThreadLocal (memory leak risk)
ThreadLocal<byte[]> buffer = new ThreadLocal<>();
for (int i = 0; i < 1_000_000; i++) {
    executor.submit(() -> {
        buffer.set(new byte[1_000_000]);  // Accumulates
    });
}
```

## Compatibility Matrix

| Java Version | Virtual Threads | StructuredTaskScope | Scoped Values | Status |
|--------------|-----------------|---------------------|---------------|--------|
| Java 19-20   | ✓ (preview)     | ✓ (preview)        | ✓ (preview)   | Deprecated |
| Java 21 LTS  | ✓ (stable)      | ✓ (stable)         | ✓ (stable)    | **Current LTS** |
| Java 22      | ✓ (stable)      | ✓ (stable)         | ✓ (stable)    | Short-term |
| Java 23      | ✓ (stable)      | ✓ (finalized)      | ✓ (finalized) | Current |
| Java 24+     | ✓ (stable)      | ✓ (stable)         | ✓ (stable)    | Future releases |

**Recommendation**: Target Java 21 LTS for production; test against Java 23+ for latest APIs.

## Agent Support

- **java-architect** — Java 21+ architecture and patterns
- **springboot-patterns** — Spring Boot 3.2+ virtual thread integration
- **jvm-advanced** — Benchmarking and profiling virtual threads

## Skill References

- **springboot-patterns** — Virtual thread configuration in Spring Boot
- **java-locks** — ReentrantLock, ReadWriteLock, and lock-free synchronization
- **async-patterns** — Comparison with CompletableFuture and reactive streams
