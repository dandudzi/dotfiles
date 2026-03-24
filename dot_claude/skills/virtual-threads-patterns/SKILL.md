---
name: virtual-threads-patterns
description: Project Loom virtual threads, structured concurrency, carrier thread pinning avoidance, and I/O-bound workload patterns for Java 21+.
origin: ECC
model: sonnet
---

# Virtual Threads Patterns (Java 21+ LTS, stable since Sept 2023)

## When to Activate

- Building I/O-heavy applications (10,000+ concurrent requests)
- Migrating from fixed thread pools to unlimited concurrency
- Optimizing Spring Boot 3.2+ with structured concurrency

**Minimum JVM**: Java 21 LTS. Java 23+ recommended for finalized StructuredTaskScope.

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

Use for: REST APIs, microservices, database/file/network I/O. **Not** for CPU-bound algorithms or code heavily reliant on ThreadLocal.

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

## Core Concept 3: Structured Concurrency with StructuredTaskScope

Structured concurrency ensures all spawned threads complete before a scope exits. Prevents resource leaks and orphaned threads.

**API Status**: Stable in Java 21 LTS. Finalized in Java 23+.

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

### Anti-Pattern: Synchronized Blocks Pin Carrier Threads

Synchronized methods block the carrier thread while holding the monitor. Use `ReentrantLock` instead.

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

## Anti-Patterns to Avoid

**CPU-bound work**: Virtual threads provide no benefit for heavy computation — use platform threads or ForkJoinPool instead.

**Synchronized blocks**: Pin carrier threads. Use `ReentrantLock` instead (released during I/O waits).

**Heavy ThreadLocal**: Millions of virtual threads + ThreadLocal = memory leak. Use `ScopedValue` for auto-cleanup per scope.

**Unbounded thread creation**: `for (int i = 0; i < 1_000_000; i++) Thread.ofVirtual().start(...)` causes memory exhaustion. Use executors with bounded queues.

**Blocking JNI**: Native calls pin carrier threads. Isolate blocking JNI in a dedicated `newFixedThreadPool(10)` instead.

## Monitoring and Debugging

Enable JVM flags to detect pinning:
```java
System.setProperty("jdk.tracePinnedThreads", "short");
System.setProperty("jdk.traceVirtualThreadEvents", "true");
```

## Compatibility

| Java Version | Virtual Threads | StructuredTaskScope | Scoped Values |
|---|---|---|---|
| Java 21 LTS | ✓ stable | ✓ stable | ✓ stable |
| Java 23+ | ✓ stable | ✓ finalized | ✓ finalized |

**Recommendation**: Target Java 21 LTS for production.

## Related Skills

- **springboot-patterns** — Virtual thread configuration
- **springboot-reactive** — Spring WebFlux and non-blocking I/O
