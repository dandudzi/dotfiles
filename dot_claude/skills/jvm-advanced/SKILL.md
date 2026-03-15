---
name: jvm-advanced
description: >
  JVM internals: GC tuning (G1GC, ZGC), memory management, profiling with
  async-profiler and JFR, container-awareness flags, GraalVM native-image
  compilation, reflection configuration, and Spring Boot AOT strategies.
---

# JVM Advanced

## When to Activate

- Tuning GC pause times or throughput for Spring Boot / Kotlin applications
- Diagnosing out-of-memory errors or heap pressure
- Profiling CPU and allocation hotspots
- Configuring containerized JVM workloads for Kubernetes
- Optimizing Java Flight Recorder (JFR) and async-profiler analysis
- Analyzing thread dumps or memory leaks
- Compiling Java applications to standalone native binaries (no JVM required)
- Reducing application startup time (50-100ms vs 1-2s JVM)
- Reducing memory footprint (10-50MB vs 200-500MB heap)
- Building lightweight Docker images for cloud deployment
- Deploying to AWS Lambda, serverless platforms, or resource-constrained environments
- Migrating Spring Boot 4.x applications to AOT (Ahead-Of-Time) compilation
- Debugging reflection, proxy, or serialization failures in native builds

## Part 1: JVM Performance Tuning

Advanced JVM configuration, garbage collection strategy, memory analysis, and production optimization.

### JVM Memory Model

The JVM divides heap memory into regions:

- **Young Generation** (25–40% of heap): short-lived objects, fast collection via minor GC
- **Old Generation** (60–75% of heap): long-lived objects, slower but less frequent collection
- **Metaspace** (native memory, not on heap): class metadata, bytecode, JIT code
- **Code Cache** (native memory): compiled JIT code, default 240 MB (tune with `-XX:ReservedCodeCacheSize`)

Object lifecycle:
1. Object allocated in Young Gen (Eden space)
2. Survives minor GC → moves to Survivor spaces
3. After N minor GCs → promoted to Old Gen
4. Full GC (all regions) when Old Gen pressure rises

### GC Selection Matrix

| Scenario | GC | Flags | Notes |
|----------|----|----- |-------|
| **Latency-sensitive** (real-time trading, dashboards) | ZGC | `-XX:+UseZGC` | Sub-millisecond pauses, Java 15+ |
| **Batch/throughput** (data processing, ETL) | ParallelGC | `-XX:+UseParallelGC` | High throughput, longer pauses acceptable |
| **General purpose** (Spring Boot, microservices) | G1GC | `-XX:+UseG1GC` (default Java 9+) | Balanced latency/throughput, predictable pauses |
| **Ultra-low latency** (financial systems) | Shenandoah | `-XX:+UseShenandoahGC` (experimental) | Concurrent, ~10ms pauses |

### G1GC Tuning (Default, Recommended)

```bash
# Basic G1GC configuration for Spring Boot
java -XX:+UseG1GC \
  -Xms4g -Xmx4g \
  -XX:MaxGCPauseMillis=200 \
  -XX:G1HeapRegionSize=16M \
  -XX:InitiatingHeapOccupancyPercent=35 \
  -XX:+UseStringDeduplication \
  -XX:+ParallelRefProcEnabled \
  -jar app.jar
```

**Key flags:**
- `-Xms` / `-Xmx`: Must be equal in production (avoid resizing overhead). Size to 75% of container memory limit.
- `-XX:MaxGCPauseMillis`: Target pause time (default 200 ms). Lower values → more frequent GCs; higher values → longer pauses.
- `-XX:G1HeapRegionSize`: Region size in bytes. Default auto-tuned; set to 16M for heaps 4–8 GB, 32M for 16+ GB.
- `-XX:InitiatingHeapOccupancyPercent`: Trigger concurrent marking (default 45%). Lower = earlier collection, less pause risk.
- `-XX:+UseStringDeduplication`: Dedup identical string objects (reduces memory 5–10%).
- `-XX:+ParallelRefProcEnabled`: Parallel weak/soft reference processing (lower pause times).

### ZGC Configuration (Ultra-Low Latency)

```bash
# ZGC for latency-sensitive workloads
java -XX:+UseZGC \
  -Xms8g -Xmx8g \
  -XX:SoftMaxHeapSize=7g \
  -XX:+ZGenerational \
  -XX:+UnlockDiagnosticVMOptions \
  -XX:ZCollectionInterval=120 \
  -jar app.jar
```

**Key flags:**
- `-XX:+UseZGC`: Enable ZGC (Java 15+).
- `-XX:SoftMaxHeapSize`: Soft limit; ZGC triggers collection before hitting this. Set 87–88% of `-Xmx`.
- `-XX:+ZGenerational`: Generational mode (Java 21+), improves young object collection.
- `-XX:ZCollectionInterval`: Force full collection every N seconds if not triggered naturally (seconds).
- **Heap sizing**: ZGC needs 20–30% overhead for concurrent collection; allocate at least 1.5x the peak live set size.

### JVM Flags for Production

```bash
java \
  # Memory & GC
  -Xms4g -Xmx4g \
  -XX:+UseG1GC \
  -XX:MaxGCPauseMillis=200 \

  # Container awareness (Java 11+)
  -XX:+UseContainerSupport \
  -XX:MaxRAMPercentage=75.0 \

  # OOM handling
  -XX:+HeapDumpOnOutOfMemoryError \
  -XX:HeapDumpPath=/var/log/heap-dumps \
  # SECURITY: Heap dumps contain credentials, JWTs, and DB connection strings
  # NEVER write to /tmp (world-readable) in production
  # At startup: mkdir -p /var/log/app/heapdumps && chmod 700 /var/log/app/heapdumps
  # For sensitive environments: encrypt heap dump files at rest
  -XX:+ExitOnOutOfMemoryError \
  -XX:OnOutOfMemoryError="kill -9 %p" \

  # GC logging
  -Xlog:gc*:file=/var/log/gc.log:time,uptime:filecount=5,filesize=20m \

  # String dedup & refs
  -XX:+UseStringDeduplication \
  -XX:+ParallelRefProcEnabled \

  # JIT tuning
  -XX:+TieredCompilation \
  -XX:ReservedCodeCacheSize=512m \

  -jar app.jar
```

### GC Logging

Enable structured GC logging for analysis:

```bash
-Xlog:gc*:file=/var/log/gc.log:time,uptime,level,tags:filecount=5,filesize=20m
```

Analyze with tools:
- **GCeasy.io**: Upload `.log`, get visual timeline + recommendations
- **JClarity Censum**: Detailed analysis dashboard
- **Universal GC Log Analyzer**: Free, offline analysis

### Profiling Tools

#### async-profiler (Recommended)

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

#### Java Flight Recorder (JFR)

```bash
# Record 60 seconds
jcmd <pid> JFR.start duration=60s filename=/tmp/recording.jfr

# Analyze (opens in JDK Mission Control or IntelliJ)
jcmd <pid> JFR.dump filename=/tmp/recording.jfr
```

#### VisualVM

```bash
# Launch (JDK 8–16)
jvisualvm

# For JDK 17+, use JDK Mission Control:
jmc
```

### Memory Leak Detection

#### Heap Dump Analysis

```bash
# Capture heap dump
jcmd <pid> GC.heap_dump /tmp/heap.hprof

# Analyze in Eclipse MAT or JProfiler:
# 1. Search "Dominator Tree" → retained heap by object
# 2. Check GC Roots → "Shortest Paths to GC Roots"
# 3. Identify circular references or accidental caches
```

#### Spring Boot Actuator Endpoint

```bash
# GET /actuator/heapdump (downloads .hprof)
curl http://localhost:8080/actuator/heapdump -o heap.hprof
```

### Thread Analysis

```bash
# Thread dump
jstack <pid> > threads.dump

# Inspect for:
# - Blocked threads (BLOCKED state, waiting on lock)
# - Deadlocks (reported at end of dump)
# - Thread pool exhaustion (all threads busy)

# Thread MBean programmatically
ThreadMXBean bean = ManagementFactory.getThreadMXBean();
long[] deadlockedThreads = bean.findDeadlockedThreads();
```

### Remote Debugging (Development Only)

> **WARNING — NEVER enable debug ports in production**
>
> ```
> -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005
> ```
>
> This allows **unauthenticated RCE** on any machine that can reach port 5005.
>
> Use only in local dev. Use JFR (Java Flight Recorder) for production profiling.

### JIT Compilation Tuning

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

### Container Awareness (Kubernetes)

```dockerfile
FROM eclipse-temurin:21-jdk-jammy

# Auto-detect container limits (Java 11+)
ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0"

ENTRYPOINT ["java", "-jar", "app.jar"]
```

**In Kubernetes:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: jvm-app
spec:
  containers:
  - name: app
    image: jvm-app:latest
    resources:
      requests:
        memory: "2Gi"
        cpu: "500m"
      limits:
        memory: "4Gi"
        cpu: "1000m"
    env:
    - name: JAVA_OPTS
      value: "-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0 -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -XX:+ExitOnOutOfMemoryError -XX:+HeapDumpOnOutOfMemoryError"
```

**Container OOM kill handling:**
```yaml
resources:
  limits:
    memory: "2Gi"  # Set -Xmx to ~75% of this
# JVM container flags (Java 17+)
-XX:MaxRAMPercentage=75.0
-XX:+ExitOnOutOfMemoryError   # Exit cleanly instead of limping
-XX:+HeapDumpOnOutOfMemoryError
```

### Spring Boot Optimization

#### Lazy Initialization

```properties
# Defer bean initialization until first use
spring.main.lazy-initialization=true

# Enable class path indexing (faster startup)
spring.classpath.index.enabled=true
```

#### Actuator Heap Dump

```yaml
# application.yml
management:
  endpoints:
    web:
      exposure:
        include: heapdump,threaddump,metrics
  endpoint:
    heapdump:
      cache:
        time-to-live: 0
```

### Anti-Patterns in JVM Tuning

#### ❌ WRONG: Mismatched heap settings
```bash
java -Xms1g -Xmx8g -jar app.jar
```
**Why:** Heap resizing causes GC overhead and unpredictable pause times.

#### ✓ CORRECT: Equal min/max in production
```bash
java -Xms8g -Xmx8g -XX:+UseG1GC -jar app.jar
```

---

#### ❌ WRONG: Explicit GC calls
```java
System.gc();  // Triggers full stop-the-world GC
```
**Why:** Unpredictable pauses, undermines tuning strategy.

#### ✓ CORRECT: Let GC decide
```java
// Trust the GC algorithm, profile instead of guessing
```

---

#### ❌ WRONG: Finalizers
```java
class Resource {
  protected void finalize() { close(); }
}
```
**Why:** Finalizers delay reclamation, create GC pressure.

#### ✓ CORRECT: Try-with-resources
```java
try (Resource r = new Resource()) {
  // use r
}  // auto-closed
```

---

#### ❌ WRONG: Tuning before profiling
```bash
# Random flags without data
java -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=4m -jar app.jar
```

#### ✓ CORRECT: Profile first, tune second
```bash
# Capture GC events, analyze with GCeasy.io, then adjust
java -Xlog:gc*:file=gc.log -jar app.jar
# Review output → adjust MaxGCPauseMillis only if pauses exceed SLA
```

## Part 2: GraalVM Native Images

GraalVM native-image compilation, reflection configuration, closed-world assumptions, Spring Boot AOT, and native image build/test strategies.

### Core Concept 1: Build-Time vs Runtime Reflection

**JVM Reflection**: Java bytecode is introspectable at runtime. Any class, method, or field can be accessed via reflection.

**Native Image**: The native binary is compiled ahead-of-time with a "closed-world assumption": code not reachable at compile time is eliminated.

#### Problem: Reflection Is Not Visible to Native Image Compiler

```java
// This works fine on JVM
public class ReflectionExample {
    public static void main(String[] args) throws Exception {
        String className = "com.example.MyClass";  // Dynamic at runtime
        Class<?> clazz = Class.forName(className);  // Compiler can't analyze
        Object instance = clazz.getDeclaredConstructor().newInstance();
    }
}

// Native image compiler sees:
// 1. Class.forName(String) is called
// 2. But className is dynamic (not a string literal)
// 3. Compiler can't determine which classes to include
// 4. Result: ClassNotFoundException at runtime
```

#### Solution 1: Reflect-Config.json

Create `reflect-config.json` to declare reflective access:

```json
[
  {
    "name": "com.example.MyClass",
    "allDeclaredConstructors": true,
    "allPublicConstructors": true,
    "allDeclaredMethods": true,
    "allPublicMethods": true,
    "allDeclaredFields": true,
    "allPublicFields": true
  },
  {
    "name": "com.example.Config",
    "methods": [
      {"name": "<init>", "parameterTypes": [] },
      {"name": "getValue", "parameterTypes": ["java.lang.String"] }
    ],
    "fields": [
      {"name": "timeout"}
    ]
  }
]
```

Place in: `src/main/resources/META-INF/native-image/reflect-config.json`

Or specify via build flag:
```bash
native-image -H:ReflectionConfigurationFiles=reflect-config.json MyApp
```

#### Solution 2: RegisterReflectionForBinding

Programmatically register reflection (Spring Boot 3.x):

```java
import org.springframework.aot.hint.RuntimeHints;
import org.springframework.aot.hint.RuntimeHintsRegistrar;

public class MyReflectionHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        // Register entire class for reflection
        hints.reflection().registerType(MyClass.class);

        // Register specific constructor
        hints.reflection().registerConstructor(
            MyClass.class.getConstructor(String.class, int.class),
            ExecutableMode.INVOKE
        );

        // Register specific method
        hints.reflection().registerMethod(
            MyClass.class.getMethod("getValue", String.class),
            ExecutableMode.INVOKE
        );
    }
}
```

### Core Concept 2: Proxy Configuration

Dynamic proxy creation (`java.lang.reflect.Proxy`) requires compile-time configuration.

#### Problem: Proxies Not Visible to Compiler

```java
// This fails in native image
public interface DataService {
    String fetch(String id);
}

public class ProxyExample {
    public static void main(String[] args) throws Exception {
        // Create proxy at runtime
        DataService proxy = (DataService) Proxy.newProxyInstance(
            DataService.class.getClassLoader(),
            new Class[]{DataService.class},
            (p, method, args) -> {
                System.out.println("Intercepted: " + method.getName());
                return null;
            }
        );
    }
}

// Error: Cannot create proxy (interfaces not known at compile time)
```

#### Solution: Proxy-Config.json

```json
[
  {
    "interfaces": [
      "com.example.DataService",
      "java.io.Serializable"
    ]
  },
  {
    "interfaces": [
      "java.util.List",
      "java.util.RandomAccess"
    ]
  }
]
```

Or register programmatically:

```java
import org.springframework.aot.hint.RuntimeHints;

public class ProxyHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        hints.proxies()
            .registerJdkProxy(DataService.class, Serializable.class);
    }
}
```

### Core Concept 3: Serialization Configuration

Java serialization requires class metadata at compile time.

#### Problem: Serialization Not Available in Native Image

```java
public class User implements Serializable {
    private String name;
    private int age;

    // This fails in native image
    public User deserialize(byte[] data) throws Exception {
        ByteArrayInputStream bais = new ByteArrayInputStream(data);
        ObjectInputStream ois = new ObjectInputStream(bais);
        return (User) ois.readObject();  // User class not in native image metadata
    }
}
```

#### Solution: Serialization-Config.json

```json
[
  {
    "name": "com.example.User",
    "customizationType": "java.io.Serializable"
  },
  {
    "name": "com.example.Order",
    "customizationType": "java.io.Serializable"
  }
]
```

Or register with Spring:

```java
import org.springframework.aot.hint.RuntimeHints;

public class SerializationHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        hints.serialization().registerType(User.class);
        hints.serialization().registerType(Order.class);
    }
}
```

### Core Concept 4: Spring Boot 4.x Ahead-Of-Time (AOT) Compilation

Spring Boot 4.x provides native-image support via `@ImportRuntimeHints`.

#### Pattern 1: Spring Boot Native Application

```java
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class NativeApp {
    public static void main(String[] args) {
        SpringApplication.run(NativeApp.class, args);
    }
}
```

Build with Maven:
```bash
mvn spring-boot:build-image -DskipTests
```

Or Gradle:
```bash
./gradlew bootBuildImage
```

This produces a containerized native image automatically.

#### Pattern 2: Custom RuntimeHints for Spring Beans

```java
import org.springframework.aot.hint.RuntimeHints;
import org.springframework.aot.hint.RuntimeHintsRegistrar;
import org.springframework.stereotype.Component;

// Custom class needing reflection
public class DynamicServiceLoader {
    public static Object loadService(String className) throws Exception {
        return Class.forName(className).getDeclaredConstructor().newInstance();
    }
}

// Register hints
@Component
public class DynamicServiceHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        // Register service classes for reflection
        hints.reflection().registerType(com.example.ServiceA.class);
        hints.reflection().registerType(com.example.ServiceB.class);

        // Register default constructors
        try {
            hints.reflection().registerConstructor(
                com.example.ServiceA.class.getConstructor()
            );
            hints.reflection().registerConstructor(
                com.example.ServiceB.class.getConstructor()
            );
        } catch (NoSuchMethodException e) {
            throw new RuntimeException(e);
        }
    }
}

// Mark config to include hints
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.ImportRuntimeHints;

@Configuration
@ImportRuntimeHints(DynamicServiceHints.class)
public class AppConfig {
}
```

#### Pattern 3: Conditional Reflection Hints

```java
import org.springframework.aot.hint.RuntimeHints;
import org.springframework.aot.hint.RuntimeHintsRegistrar;
import java.util.List;

public class ConditionalHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        // Register different classes based on conditions
        String env = System.getenv("APP_ENV");

        if ("production".equals(env)) {
            hints.reflection().registerType(com.example.ProductionConfig.class);
        } else {
            hints.reflection().registerType(com.example.DevConfig.class);
        }

        // Register multiple classes
        List.of(
            com.example.UserService.class,
            com.example.OrderService.class,
            com.example.PaymentService.class
        ).forEach(clazz -> hints.reflection().registerType(clazz));
    }
}
```

### Core Concept 5: Common Native Image Failures and Fixes

#### Failure 1: ClassNotFoundException (Reflection)

**Error**:
```
Exception in thread "main" java.lang.ClassNotFoundException:
    com.example.MyClass
```

**Root Cause**: Class accessed via `Class.forName()` or similar, not visible at compile time.

**Fix**:
```java
// reflect-config.json
{
  "name": "com.example.MyClass",
  "allDeclaredConstructors": true,
  "allPublicMethods": true
}

// Or programmatically
hints.reflection().registerType(com.example.MyClass.class);
```

#### Failure 2: NoSuchMethodException (Serialization)

**Error**:
```
java.io.InvalidClassException: com.example.User; no valid constructor
```

**Root Cause**: Serialization class not declared in native-image metadata.

**Fix**:
```json
[
  {
    "name": "com.example.User",
    "customizationType": "java.io.Serializable"
  }
]
```

#### Failure 3: UnsatisfiedLinkError (JNI)

**Error**:
```
java.lang.UnsatisfiedLinkError: no native method found
```

**Root Cause**: Native library not linked or loaded in native image.

**Fix**: Link native libraries at compile time:
```bash
native-image --link-at-build-time=com.example.Native MyApp
```

Or use configuration:
```json
// native-image.properties
BuildAtBuildTime=com.example.Native
```

#### Failure 4: IllegalAccessException (Module Encapsulation)

**Error**:
```
java.lang.IllegalAccessException: class X cannot access member of class Y
```

**Root Cause**: Sealed module preventing reflection on private members.

**Fix**: Add module opens to build:
```bash
native-image --enable-all-security-services MyApp
```

Or in `native-image.properties`:
```properties
Args=-J--add-opens=java.base/java.lang=ALL-UNNAMED
```

### Core Concept 6: Docker Multi-Stage Build for Native Images

#### Pattern 4: Multi-Stage Native Image Build

```dockerfile
# Stage 1: Build native image
FROM ghcr.io/graalvm/native-image:latest as builder

WORKDIR /app
COPY . .

# Build native executable
RUN native-image -jar app.jar app

# Stage 2: Runtime (minimal)
FROM ubuntu:latest

WORKDIR /app
COPY --from=builder /app/app .
COPY --from=builder /app/app.jar .

# No JVM needed; executable is self-contained
ENTRYPOINT ["/app/app"]
```

#### Pattern 5: Spring Boot Native Image Docker Build

```dockerfile
# Stage 1: Maven build
FROM maven:3.9-eclipse-temurin-21 as build

WORKDIR /app
COPY . .

# Build with AOT compilation (Spring Boot 3.2+)
RUN mvn native:compile -DskipTests

# Stage 2: Runtime
FROM ubuntu:latest

WORKDIR /app
COPY --from=build /app/target/myapp /app/myapp

EXPOSE 8080
ENTRYPOINT ["/app/myapp"]
```

Or using Spring Boot's built-in containerization:

```bash
# Builds Docker image with native executable
mvn spring-boot:build-image -DskipTests
```

### Core Concept 7: Startup Time and Memory Trade-Offs

#### Comparison: Native Image vs JVM

| Metric | Native Image | JVM |
|--------|--------------|-----|
| Startup | 50-100ms | 1000-2000ms |
| Memory (RSS) | 10-50MB | 200-500MB |
| Peak Memory | Lower | Higher (GC) |
| CPU Usage (startup) | Lower | Higher (JIT) |
| Long-running Performance | Slightly lower | Higher (JIT optimization) |
| Build Time | 20-60s | <1s |
| Docker Image Size | 50MB | 500MB+ |

**When to Use Native Image**:
- Serverless/Lambda (rapid startup critical)
- High-density containerized deployments (memory constrained)
- CLI tools (user experience)
- Cost-sensitive auto-scaling (rapid startup saves $)

**When to Use JVM**:
- Long-running services (JIT warm-up pays off)
- Complex reflection/dynamic behavior
- Development (fast build cycle)
- Legacy libraries with native image incompatibilities

### Core Concept 8: Native Image Testing Strategies

#### Pattern 6: Testing Native Image Locally

```java
import io.quarkus.test.junit.QuarkusTest;
import org.junit.jupiter.api.Test;

// Quarkus automatically tests against native image in CI
@QuarkusTest
public class NativeImageTest {

    @Test
    public void testEndpoint() {
        // Test runs against native executable
        given()
            .when().get("/api/users")
            .then()
            .statusCode(200);
    }
}
```

For Spring Boot:
```java
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

@SpringBootTest
@ActiveProfiles("native")  // Test native image
public class NativeImageTest {

    @Test
    public void testApplicationStartup() {
        // Test runs against native executable in CI
        assertThat(applicationContext).isNotNull();
    }
}
```

#### Pattern 7: Reflection Detection in Tests

```java
// JVM: Enable pinned thread detection before tests
System.setProperty("jdk.tracePinnedThreads", "short");

// Native image: Enable reflection tracing
System.setProperty("org.graalvm.nativeimage.trace", "true");

// Run tests to detect reflection issues early
@Test
public void testReflectionUsage() {
    // Any reflection not in native-image metadata will fail here
    Class<?> clazz = Class.forName("com.example.MyClass");
}
```

#### Pattern 8: Native Image Plugin for Maven

```xml
<plugin>
    <groupId>org.graalvm.buildtools</groupId>
    <artifactId>native-maven-plugin</artifactId>
    <version>0.11.1</version>

    <configuration>
        <imageName>myapp</imageName>
        <mainClass>com.example.Main</mainClass>

        <!-- Enable strict build (fail on missing metadata) -->
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

### Core Concept 9: Closed-World Assumption Limitations

The native image compiler assumes:
1. **No dynamic class loading** beyond declared classes
2. **No unknown reflection** at compile time
3. **All JNI libraries** must be linked
4. **No new code generation** at runtime

#### Unsupported Patterns

```java
// NOT SUPPORTED: Dynamic bytecode generation
import javassist.ClassPool;

public class DynamicClassGeneration {
    public static void main(String[] args) throws Exception {
        ClassPool pool = ClassPool.getDefault();
        CtClass cc = pool.makeClass("GeneratedClass");  // Fails in native image
        // Cannot generate bytecode in native image
    }
}

// NOT SUPPORTED: Arbitrary reflection
public class DynamicInvocation {
    public void callUnknownMethod(String methodName) throws Exception {
        // Method name is dynamic; compiler can't analyze
        Object obj = new MyClass();
        Method method = obj.getClass().getMethod(methodName);  // Fails
        method.invoke(obj);
    }
}

// NOT SUPPORTED: ClassLoader isolation
public class CustomClassLoading {
    public void loadCustom() throws Exception {
        // Creating new class loaders not supported
        URLClassLoader loader = new URLClassLoader(new URL[] {...});
        Class<?> clazz = loader.loadClass("unknown.Class");  // Fails
    }
}

// SUPPORTED: Declared reflection with static method names
public class StaticReflection {
    public void callKnownMethod() throws Exception {
        // Method name is static (compile-time constant)
        Object obj = new MyClass();
        Method method = obj.getClass().getMethod("knownMethod");  // OK
        method.invoke(obj);
    }
}
```

### Core Concept 10: Quarkus vs Micronaut vs Spring Boot Native

#### Comparison

| Framework | Native Support | Reflection Config | AOT Maturity |
|-----------|----------------|------------------|-------------|
| Quarkus | Excellent | Automatic | Production-ready |
| Micronaut | Excellent | Automatic | Production-ready |
| Spring Boot 4.x | Excellent | Spring AOT (auto, improved) | Production-ready |
| Spring Boot 3.x | Good | Spring AOT (auto) | Production-ready |
| Spring Boot <3.x | Manual | Manual config | Not recommended |

**Quarkus Example** (least config):
```java
@Path("/api")
public class UserResource {
    @GET
    @Path("/{id}")
    public User getUser(@PathParam int id) {
        return new User(id);
    }
}

// Build native: mvn clean package -Pnative
// No additional metadata needed
```

**Micronaut Example** (minimal config):
```java
@Controller("/api")
public class UserController {
    @Get("/{id}")
    public User getUser(int id) {
        return new User(id);
    }
}

// Build native: mn create-app && mn build --lang=java --build=native
```

**Spring Boot Example** (some config):
```java
@RestController
@RequestMapping("/api")
public class UserController {

    @GetMapping("/{id}")
    public User getUser(@PathVariable int id) {
        return new User(id);
    }
}

// Build native: mvn spring-boot:build-image -DskipTests
// Spring AOT handles most reflection automatically
```

### Anti-Patterns in Native Images

#### WRONG: Unbounded Reflection

```java
// ANTI-PATTERN: Reflection on unknown classes
public void loadService(String serviceName) throws Exception {
    Class<?> clazz = Class.forName(serviceName);  // Dynamic; compiler can't see
    Object service = clazz.getDeclaredConstructor().newInstance();
}

// This works on JVM but fails in native image
```

#### CORRECT: Declared Reflection

```java
// CORRECT: Known classes declared at compile time
public static final Set<Class<?>> KNOWN_SERVICES = Set.of(
    ServiceA.class, ServiceB.class, ServiceC.class
);

public void loadService(String serviceName) throws Exception {
    Class<?> clazz = KNOWN_SERVICES.stream()
        .filter(c -> c.getSimpleName().equals(serviceName))
        .findFirst()
        .orElseThrow();
    Object service = clazz.getDeclaredConstructor().newInstance();
}
```

#### WRONG: Dynamic JNI Loading

```java
// ANTI-PATTERN: Runtime JNI library loading
public class NativeLib {
    static {
        System.load("/path/to/native/" + getOsName() + "/lib.so");  // Dynamic
    }

    private native void nativeCall();
}
```

#### CORRECT: Statically Linked JNI

```java
// CORRECT: Static linking at build time
public class NativeLib {
    static {
        System.loadLibrary("mylib");  // Linked at native-image build
    }

    private native void nativeCall();
}

// Build: native-image --link-at-build-time=com.example.NativeLib MyApp
```

#### WRONG: Unbounded ThreadLocal

```java
// ANTI-PATTERN: ThreadLocal in native image
ThreadLocal<ExpensiveResource> resource = new ThreadLocal<>();

public void process() {
    resource.set(new ExpensiveResource());  // No GC of ThreadLocal in native
    // Memory leak risk
}
```

#### CORRECT: Scoped Values (Preview in Java 21)

```java
// CORRECT: Scoped values auto-clean
private static final ScopedValue<ExpensiveResource> resource =
    ScopedValue.newInstance();

public void process() {
    ScopedValue.callWhere(resource, new ExpensiveResource(), () -> {
        // Auto-cleaned when scope exits
    });
}
```

### Best Practices

#### Do This

```java
// GOOD: Explicit reflection hints
public class MyHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        hints.reflection().registerType(MyService.class);
    }
}

// GOOD: Use Spring Boot 3.2+ native support
@SpringBootApplication
public class App {
    public static void main(String[] args) {
        SpringApplication.run(App.class, args);
    }
}
// Build: mvn spring-boot:build-image

// GOOD: Static method names (known at compile time)
public void callMethod(Object obj) throws Exception {
    Method m = obj.getClass().getMethod("knownMethod");
    m.invoke(obj);
}

// GOOD: Docker multi-stage build
// Stage 1: build native
// Stage 2: small runtime image

// GOOD: Test native image in CI
// Run integration tests against compiled native executable
```

#### Don't Do This

```java
// BAD: Reflection on unknown classes
Class<?> clazz = Class.forName(dynamicClassName);  // Fails in native

// BAD: Generating bytecode at runtime
ClassPool pool = ClassPool.getDefault();
CtClass cc = pool.makeClass("Generated");  // Not supported

// BAD: Dynamic JNI loading
System.load("/path/to/" + osName + "/lib.so");  // Must link statically

// BAD: Arbitrary proxy creation (without hints)
Proxy.newProxyInstance(loader, interfaces, handler);  // Fails without config

// BAD: Unbounded reflection in loops
for (String className : classes) {
    Class.forName(className);  // Each must be pre-declared
}

// BAD: Relying on JIT optimization for performance
// Native image performs poorly on CPU-bound code
```

## Agent Support

This skill pairs with:
- **java-architect** — Java 21+ native image features, GraalVM configuration
- **spring-expert** — Spring Boot 3.x AOT and native image support
- **docker-expert** — Multi-stage builds and container optimization
- **nodejs-expert** — JVM runtime concepts
- **sql-expert** — Query tuning affecting memory
- **performance-expert** — Benchmarking native vs JVM performance

## Skill References

- **docker**: Container heap sizing, volume mounts for gc logs, multi-stage builds for native binaries
- **tdd-workflow**: Load testing to validate GC tuning changes, native image integration testing
