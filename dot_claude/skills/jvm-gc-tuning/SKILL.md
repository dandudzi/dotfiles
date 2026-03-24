---
name: jvm-gc-tuning
description: >
  GC tuning (G1GC, ZGC, ParallelGC), heap sizing, container-aware JVM flags,
  GC logging, Kubernetes deployment, memory anti-patterns, and production
  optimization for Spring Boot and microservices.
model: sonnet
---

# JVM GC Tuning

## When to Activate

- Tuning GC pause times or throughput for Spring Boot applications
- Diagnosing out-of-memory errors or heap pressure
- Configuring containerized JVM workloads for Kubernetes
- Optimizing GC logging analysis

## JVM Memory Model

The JVM divides heap memory into regions:

- **Young Generation** (25–40% of heap): short-lived objects, fast collection via minor GC
- **Old Generation** (60–75% of heap): long-lived objects, slower but less frequent collection
- **Metaspace** (native memory): class metadata, bytecode, JIT code
- **Code Cache** (native memory): compiled JIT code, tune with `-XX:ReservedCodeCacheSize`

Object lifecycle:
1. Object allocated in Young Gen (Eden space)
2. Survives minor GC → moves to Survivor spaces
3. After N minor GCs → promoted to Old Gen
4. Full GC triggers when Old Gen pressure rises

## GC Selection Matrix

| Scenario | GC | Flags | Notes |
|----------|----|----- |-------|
| **Latency-sensitive** (trading, dashboards) | ZGC | `-XX:+UseZGC` | Sub-millisecond pauses, Java 15+ |
| **Batch/throughput** (ETL, data processing) | ParallelGC | `-XX:+UseParallelGC` | High throughput, longer pauses acceptable |
| **General purpose** (Spring Boot, microservices) | G1GC | `-XX:+UseG1GC` | Balanced latency/throughput, predictable pauses |
| **Ultra-low latency** (financial systems) | Shenandoah | `-XX:+UseShenandoahGC` | Concurrent, ~10ms pauses, experimental |

## G1GC Tuning (Default, Recommended)

```bash
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
- `-XX:MaxGCPauseMillis`: Target pause time (default 200 ms). Lower = more frequent GCs; higher = longer pauses.
- `-XX:G1HeapRegionSize`: Region size. Default auto-tuned; set to 16M for 4–8 GB heaps, 32M for 16+ GB.
- `-XX:InitiatingHeapOccupancyPercent`: Trigger concurrent marking (default 45%). Lower = earlier collection, less pause risk.
- `-XX:+UseStringDeduplication`: Dedup identical string objects (5–10% memory savings).
- `-XX:+ParallelRefProcEnabled`: Parallel weak/soft reference processing (lower pause times).

## ZGC Configuration (Ultra-Low Latency)

```bash
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
- `-XX:ZCollectionInterval`: Force full collection every N seconds (default: natural triggering).
- **Heap sizing**: ZGC needs 20–30% overhead; allocate at least 1.5x peak live set size.

## JVM Flags for Production

```bash
java \
  -Xms4g -Xmx4g \
  -XX:+UseG1GC \
  -XX:MaxGCPauseMillis=200 \
  -XX:+UseContainerSupport \
  -XX:MaxRAMPercentage=75.0 \
  -XX:+HeapDumpOnOutOfMemoryError \
  -XX:HeapDumpPath=/var/log/app/heapdumps \
  -XX:+ExitOnOutOfMemoryError \
  -XX:OnOutOfMemoryError="kill -9 %p" \
  -Xlog:gc*:file=/var/log/gc.log:time,uptime:filecount=5,filesize=20m \
  -XX:+UseStringDeduplication \
  -XX:+ParallelRefProcEnabled \
  -XX:+TieredCompilation \
  -XX:ReservedCodeCacheSize=512m \
  -jar app.jar
```

**SECURITY**: Heap dumps contain credentials, JWTs, and DB strings. Never write to `/tmp` (world-readable). Pre-create `/var/log/app/heapdumps` with `chmod 700`. Encrypt heap dumps at rest in sensitive environments.

## GC Logging

Enable structured GC logging for analysis:

```bash
-Xlog:gc*:file=/var/log/gc.log:time,uptime,level,tags:filecount=5,filesize=20m
```

Analyze with:
- **GCeasy.io**: Upload `.log`, get visual timeline + recommendations
- **JClarity Censum**: Detailed analysis dashboard
- **Universal GC Log Analyzer**: Free, offline analysis

## Container Awareness (Kubernetes)

```dockerfile
FROM eclipse-temurin:21-jdk-jammy

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
      value: "-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0 -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -XX:+ExitOnOutOfMemoryError"
```

Set `-Xmx` to ~75% of memory limit. Use `-XX:+ExitOnOutOfMemoryError` to exit cleanly instead of limping.

## Anti-Patterns

**Mismatched heap settings** — Heap resizing causes GC overhead and unpredictable pauses.
```bash
# WRONG
java -Xms1g -Xmx8g -jar app.jar

# CORRECT — Equal min/max in production
java -Xms8g -Xmx8g -XX:+UseG1GC -jar app.jar
```

**Explicit GC calls** — `System.gc()` triggers full stop-the-world GC, unpredictable pauses. Let GC decide.

**Finalizers** — Delay reclamation, create GC pressure. Use try-with-resources instead:
```java
try (Resource r = new Resource()) {
  // use r
}  // auto-closed
```

**Tuning before profiling** — Adjust only after capturing GC events and analyzing with GCeasy.io. Random flags waste time.

## Spring Boot Optimization

**Lazy initialization** — Defer bean creation until first use:
```properties
spring.main.lazy-initialization=true
spring.classpath.index.enabled=true
```

**Actuator heap dump** (application.yml):
```yaml
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

Capture with: `curl http://localhost:8080/actuator/heapdump -o heap.hprof`

## Agent Support

- **java-architect** — GraalVM native image, Java 21+ features
- **docker-expert** — Multi-stage builds, container optimization
- **performance-expert** — GC benchmarking
