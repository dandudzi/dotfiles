---
name: jvm-profiling-graalvm
description: >
  JVM profiling (async-profiler, JFR, VisualVM), memory leak detection, thread
  analysis, remote debugging, JIT tuning, GraalVM native-image compilation,
  reflection configuration, closed-world assumptions, Spring Boot AOT strategies,
  and native image testing.
model: sonnet
---

# JVM Profiling & GraalVM

## When to Activate

- Profiling CPU and allocation hotspots
- Diagnosing memory leaks and thread contention
- Compiling Java applications to standalone native binaries
- Reducing startup time (50-100ms vs 1-2s JVM) and memory (10-50MB vs 200-500MB)
- Deploying to AWS Lambda, serverless, or resource-constrained environments
- Migrating Spring Boot 3.x+ applications to AOT compilation

## Profiling Tools

### async-profiler (Recommended)

```bash
# Install (macOS)
brew install async-profiler

# CPU profile (flame graph)
async-profiler -d 30 -f flamegraph.html -o jfr jps

# Allocation profile
async-profiler -d 30 -e alloc -f flamegraph.html -o jfr jps

# Lock contention
async-profiler -d 30 -e lock -f flamegraph.html -o jfr jps
```

### Java Flight Recorder (JFR)

```bash
# Record 60 seconds
jcmd <pid> JFR.start duration=60s filename=/tmp/recording.jfr

# Analyze (opens in JDK Mission Control or IntelliJ)
jcmd <pid> JFR.dump filename=/tmp/recording.jfr
```

### VisualVM

```bash
# JDK 8–16
jvisualvm

# JDK 17+ use JDK Mission Control
jmc
```

## Memory Leak Detection

### Heap Dump Analysis

```bash
# Capture heap dump
jcmd <pid> GC.heap_dump /tmp/heap.hprof
```

Analyze in Eclipse MAT or JProfiler:
1. Search "Dominator Tree" → retained heap by object
2. Check GC Roots → "Shortest Paths to GC Roots"
3. Identify circular references or accidental caches

### Spring Boot Actuator Endpoint

```bash
curl http://localhost:8080/actuator/heapdump -o heap.hprof
```

## Thread Analysis

```bash
# Thread dump
jstack <pid> > threads.dump

# Inspect for:
# - Blocked threads (BLOCKED state, waiting on lock)
# - Deadlocks (reported at end of dump)
# - Thread pool exhaustion (all threads busy)
```

Programmatic detection:
```java
ThreadMXBean bean = ManagementFactory.getThreadMXBean();
long[] deadlockedThreads = bean.findDeadlockedThreads();
```

## Remote Debugging

**WARNING — NEVER enable debug ports in production.** `-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005` allows unauthenticated RCE. Use only in local dev. Use JFR for production profiling.

## JIT Compilation Tuning

```bash
# View JIT activity
-XX:+PrintCompilation \
-XX:+LogCompilation \
-XX:LogFile=/var/log/jit.log

# Code cache sizing (default 240 MB)
-XX:ReservedCodeCacheSize=512m

# Tiered compilation (default on for server JVM)
-XX:+TieredCompilation \
-XX:TieredStopAtLevel=4
```

---

# GraalVM Native Image

## Core Concept: Build-Time vs Runtime Reflection

**JVM Reflection**: Java bytecode is introspectable at runtime. Any class, method, or field can be accessed via reflection.

**Native Image**: The native binary is compiled ahead-of-time with a "closed-world assumption": code not reachable at compile time is eliminated.

### Problem: Reflection Is Not Visible to Native Image Compiler

```java
// Works fine on JVM
String className = "com.example.MyClass";  // Dynamic at runtime
Class<?> clazz = Class.forName(className);  // Compiler can't analyze → ClassNotFoundException
```

### Solution 1: Reflect-Config.json

Create `src/main/resources/META-INF/native-image/reflect-config.json`:

```json
[
  {
    "name": "com.example.MyClass",
    "allDeclaredConstructors": true,
    "allPublicMethods": true,
    "allDeclaredFields": true
  },
  {
    "name": "com.example.Config",
    "methods": [
      {"name": "<init>", "parameterTypes": []},
      {"name": "getValue", "parameterTypes": ["java.lang.String"]}
    ]
  }
]
```

Or build flag: `native-image -H:ReflectionConfigurationFiles=reflect-config.json MyApp`

### Solution 2: Spring Boot RuntimeHints (3.x+)

```java
import org.springframework.aot.hint.RuntimeHints;
import org.springframework.aot.hint.RuntimeHintsRegistrar;

public class MyReflectionHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        hints.reflection().registerType(MyClass.class);

        hints.reflection().registerConstructor(
            MyClass.class.getConstructor(String.class, int.class),
            ExecutableMode.INVOKE
        );

        hints.reflection().registerMethod(
            MyClass.class.getMethod("getValue", String.class),
            ExecutableMode.INVOKE
        );
    }
}
```

## Proxy Configuration

Dynamic proxy creation (`java.lang.reflect.Proxy`) requires compile-time configuration.

### Problem: Proxies Not Visible to Compiler

```java
// Fails in native image
DataService proxy = (DataService) Proxy.newProxyInstance(
    DataService.class.getClassLoader(),
    new Class[]{DataService.class},
    (p, method, args) -> null
);
```

### Solution: Proxy-Config.json

```json
[
  {
    "interfaces": [
      "com.example.DataService",
      "java.io.Serializable"
    ]
  }
]
```

Or register programmatically:
```java
hints.proxies().registerJdkProxy(DataService.class, Serializable.class);
```

## Serialization Configuration

Java serialization requires class metadata at compile time.

### Solution: Serialization-Config.json

```json
[
  {
    "name": "com.example.User",
    "customizationType": "java.io.Serializable"
  }
]
```

Or with Spring:
```java
hints.serialization().registerType(User.class);
```

## Spring Boot 3.x AOT Compilation

### Pattern: Native Application

```java
@SpringBootApplication
public class NativeApp {
    public static void main(String[] args) {
        SpringApplication.run(NativeApp.class, args);
    }
}
```

Build with Maven: `mvn spring-boot:build-image -DskipTests`

Or Gradle: `./gradlew bootBuildImage`

Produces containerized native image automatically.

### Pattern: Custom RuntimeHints for Dynamic Services

```java
public class DynamicServiceLoader {
    public static Object loadService(String className) throws Exception {
        return Class.forName(className).getDeclaredConstructor().newInstance();
    }
}

@Component
public class DynamicServiceHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        hints.reflection().registerType(com.example.ServiceA.class);
        hints.reflection().registerType(com.example.ServiceB.class);

        try {
            hints.reflection().registerConstructor(
                com.example.ServiceA.class.getConstructor()
            );
        } catch (NoSuchMethodException e) {
            throw new RuntimeException(e);
        }
    }
}

@Configuration
@ImportRuntimeHints(DynamicServiceHints.class)
public class AppConfig {}
```

## Common Native Image Failures

**ClassNotFoundException** — Class accessed via `Class.forName()`, not visible at compile time.
```java
hints.reflection().registerType(com.example.MyClass.class);
```

**NoSuchMethodException** — Serialization class not declared in native-image metadata.
```json
{"name": "com.example.User", "customizationType": "java.io.Serializable"}
```

**UnsatisfiedLinkError** — Native library not linked. Link at compile time:
```bash
native-image --link-at-build-time=com.example.Native MyApp
```

**IllegalAccessException** — Sealed module preventing reflection. Add module opens:
```bash
native-image --enable-all-security-services MyApp
```

## Docker Multi-Stage Build for Native Images

```dockerfile
# Stage 1: Build native image
FROM ghcr.io/graalvm/native-image:latest as builder

WORKDIR /app
COPY . .
RUN native-image -jar app.jar app

# Stage 2: Runtime
FROM ubuntu:latest

WORKDIR /app
COPY --from=builder /app/app .
ENTRYPOINT ["/app/app"]
```

Automatic Spring Boot build: `mvn spring-boot:build-image -DskipTests`

## Startup Time and Memory Trade-Offs

| Metric | Native Image | JVM |
|--------|--------------|-----|
| Startup | 50-100ms | 1000-2000ms |
| Memory (RSS) | 10-50MB | 200-500MB |
| Peak Memory | Lower | Higher (GC) |
| Long-running Performance | Slightly lower | Higher (JIT optimization) |
| Build Time | 20-60s | <1s |
| Docker Image Size | 50MB | 500MB+ |

**Use Native Image**: Serverless/Lambda (rapid startup critical), high-density containers (memory constrained), CLI tools, cost-sensitive auto-scaling.

**Use JVM**: Long-running services (JIT warm-up pays off), complex reflection, development (fast build cycle).

## Native Image Testing Strategies

### Testing with Quarkus

```java
import io.quarkus.test.junit.QuarkusTest;
import org.junit.jupiter.api.Test;

@QuarkusTest
public class NativeImageTest {
    @Test
    public void testEndpoint() {
        given()
            .when().get("/api/users")
            .then()
            .statusCode(200);
    }
}
```

### Testing with Spring Boot

```java
@SpringBootTest
@ActiveProfiles("native")  // Test native image
public class NativeImageTest {
    @Test
    public void testApplicationStartup() {
        assertThat(applicationContext).isNotNull();
    }
}
```

### Reflection Detection in Tests

```java
System.setProperty("org.graalvm.nativeimage.trace", "true");

@Test
public void testReflectionUsage() {
    Class<?> clazz = Class.forName("com.example.MyClass");
    // Any reflection not in metadata will fail here
}
```

### Native Image Maven Plugin

```xml
<plugin>
    <groupId>org.graalvm.buildtools</groupId>
    <artifactId>native-maven-plugin</artifactId>
    <version>0.11.1</version>

    <configuration>
        <imageName>myapp</imageName>
        <mainClass>com.example.Main</mainClass>
        <buildArgs>
            <buildArg>--strict-image-heap</buildArg>
            <buildArg>-H:+ReportExceptionStackTraces</buildArg>
        </buildArgs>
    </configuration>

    <executions>
        <execution>
            <goals>
                <goal>native-compile</goal>
            </goals>
        </execution>
    </executions>
</plugin>
```

Build with: `mvn native:compile`

## Closed-World Assumption Limitations

The native image compiler assumes:
1. No dynamic class loading beyond declared classes
2. No unknown reflection at compile time
3. All JNI libraries must be linked
4. No new code generation at runtime

### Unsupported Patterns

**Dynamic bytecode generation** — Cannot generate bytecode in native image:
```java
ClassPool pool = ClassPool.getDefault();
CtClass cc = pool.makeClass("GeneratedClass");  // Fails
```

**Arbitrary reflection** — Method name must be compile-time constant:
```java
Method method = obj.getClass().getMethod(methodName);  // Dynamic fails
Method method = obj.getClass().getMethod("knownMethod");  // OK
```

**CustomClassLoading** — Creating new class loaders not supported:
```java
URLClassLoader loader = new URLClassLoader(new URL[] {...});
Class<?> clazz = loader.loadClass("unknown.Class");  // Fails
```

## Anti-Patterns

**Unbounded reflection** — Fails; compiler can't determine classes:
```java
// WRONG
Class<?> clazz = Class.forName(serviceName);

// CORRECT — Declare known classes
public static final Set<Class<?>> KNOWN_SERVICES = Set.of(
    ServiceA.class, ServiceB.class, ServiceC.class
);
```

**Dynamic JNI loading** — Cannot load libraries at runtime:
```java
// WRONG
System.load("/path/to/" + getOsName() + "/lib.so");

// CORRECT — Static linking at build time
System.loadLibrary("mylib");
// Build: native-image --link-at-build-time=com.example.NativeLib MyApp
```

**Unbounded ThreadLocal** — No GC of ThreadLocal in native, memory leak risk:
```java
// WRONG
ThreadLocal<ExpensiveResource> resource = new ThreadLocal<>();

// CORRECT — Scoped values (Java 21)
private static final ScopedValue<ExpensiveResource> resource =
    ScopedValue.newInstance();

ScopedValue.callWhere(resource, new ExpensiveResource(), () -> {
    // Auto-cleaned when scope exits
});
```

## Framework Comparison

| Framework | Native Support | Reflection Config | AOT Maturity |
|-----------|----------------|------------------|-------------|
| Quarkus | Excellent | Automatic | Production-ready |
| Micronaut | Excellent | Automatic | Production-ready |
| Spring Boot 4.x | Excellent | Spring AOT (auto, improved) | Production-ready |
| Spring Boot 3.x | Good | Spring AOT (auto) | Production-ready |

**Quarkus** (least config):
```java
@Path("/api")
public class UserResource {
    @GET
    @Path("/{id}")
    public User getUser(@PathParam int id) {
        return new User(id);
    }
}
// Build: mvn clean package -Pnative
```

## Best Practices

✓ Use Spring Boot 3.2+ native support with `mvn spring-boot:build-image`
✓ Explicitly register reflection hints via `RuntimeHintsRegistrar`
✓ Use static method names (known at compile time)
✓ Test native image in CI (run integration tests against compiled executable)
✓ Docker multi-stage build (build stage + small runtime image)

✗ Reflection on unknown classes — fails in native
✗ Generating bytecode at runtime — not supported
✗ Dynamic JNI loading — must link statically
✗ Arbitrary proxy creation without hints — fails
✗ Unbounded reflection in loops — each must be pre-declared

## Agent Support

- **java-architect** — GraalVM native image, Java 21+ features
- **spring-expert** — Spring Boot 3.x AOT and native image support
- **docker-expert** — Multi-stage builds
