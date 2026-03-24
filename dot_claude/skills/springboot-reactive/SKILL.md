---
name: springboot-reactive
description: Spring WebFlux reactive patterns, Project Loom virtual threads, and non-blocking I/O for Java Spring Boot. Use for high-concurrency, reactive workloads.
origin: ECC
model: sonnet
---

# Spring Boot Reactive Patterns

Reactive and non-blocking architecture for handling high-concurrency I/O-bound workloads.

## When to Activate

- Reactive/non-blocking workloads with many concurrent connections (10,000+)
- High-concurrency I/O-bound operations (3+ external service calls per request)
- Existing R2DBC or WebFlux codebases
- Real-time features (WebSockets, Server-Sent Events)

## WebFlux Reactive Patterns

Non-blocking, async request handling with Mono and Flux for high-concurrency scenarios.

### Reactive REST Controller

```java
@RestController
@RequestMapping("/api/orders")
public class ReactiveOrderController {
  private final ReactiveOrderService orderService;

  public ReactiveOrderController(ReactiveOrderService orderService) {
    this.orderService = orderService;
  }

  @GetMapping("/{id}")
  public Mono<ResponseEntity<OrderResponse>> getOrder(@PathVariable Long id) {
    return orderService.findById(id)
        .map(order -> ResponseEntity.ok(OrderResponse.from(order)))
        .defaultIfEmpty(ResponseEntity.notFound().build());
  }

  @GetMapping
  public Flux<OrderResponse> listOrders(
      @RequestParam(defaultValue = "0") int page,
      @RequestParam(defaultValue = "20") int size) {
    return orderService.list(page, size)
        .map(OrderResponse::from)
        .doOnError(ex -> LoggerFactory.getLogger(getClass())
            .error("list_orders_failed", ex));
  }

  @PostMapping
  public Mono<ResponseEntity<OrderResponse>> create(
      @Valid @RequestBody CreateOrderRequest request) {
    return orderService.create(request)
        .map(order -> ResponseEntity.status(HttpStatus.CREATED)
            .body(OrderResponse.from(order)));
  }
}

@Service
public class ReactiveOrderService {
  private final ReactiveOrderRepository orderRepository;
  private static final Logger log = LoggerFactory.getLogger(ReactiveOrderService.class);

  public Mono<Order> findById(Long id) {
    return orderRepository.findById(id)
        .doOnSuccess(order -> log.info("find_order_success id={}", id))
        .doOnError(ex -> log.error("find_order_failed id={}", id, ex));
  }

  public Flux<Order> list(int page, int size) {
    return orderRepository.findAll()
        .skip((long) page * size)
        .take(size);
  }

  public Mono<Order> create(CreateOrderRequest request) {
    Order order = Order.from(request);
    return orderRepository.save(order)
        .doOnSuccess(saved -> log.info("order_created id={}", saved.id()));
  }
}

@Repository
public interface ReactiveOrderRepository extends ReactiveCrudRepository<OrderEntity, Long> {
  Flux<OrderEntity> findByUserId(String userId);
}
```

### R2DBC for Reactive Database Access

```java
// pom.xml dependencies
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-data-r2dbc</artifactId>
</dependency>
<dependency>
  <groupId>org.postgresql</groupId>
  <artifactId>r2dbc-postgresql</artifactId>
</dependency>

// application.yml
spring:
  r2dbc:
    url: r2dbc:postgresql://localhost:5432/orders_db
    pool:
      initial-size: 10
      max-size: 20
      max-idle-time: 30m

// Entity
@Table("orders")
public record OrderEntity(
    @Id Long id,
    String userId,
    BigDecimal total,
    OrderStatus status,
    Instant createdAt) {}

// Reactive repository with custom queries
@Repository
public interface OrderRepository extends ReactiveCrudRepository<OrderEntity, Long> {
  @Query("select * from orders where user_id = $1 order by created_at desc")
  Flux<OrderEntity> findByUserIdOrdered(String userId);

  Mono<Long> countByUserId(String userId);
}

// Service using reactive queries
@Service
public class OrderStatsService {
  private final OrderRepository orderRepository;

  public Mono<OrderStats> getStats(String userId) {
    return Mono.zip(
        orderRepository.countByUserId(userId),
        orderRepository.findByUserIdOrdered(userId)
            .map(OrderEntity::total)
            .reduce(BigDecimal.ZERO, BigDecimal::add)
    ).map(tuple -> new OrderStats(tuple.getT1(), tuple.getT2()));
  }
}
```

### WebClient with Retry and Timeout

```java
@Service
public class ExternalServiceClient {
  private final WebClient webClient;
  private static final Logger log = LoggerFactory.getLogger(ExternalServiceClient.class);

  public ExternalServiceClient(WebClient.Builder builder) {
    this.webClient = builder
        .baseUrl("https://api.external.com")
        .defaultHeader(HttpHeaders.AUTHORIZATION, "Bearer ${API_KEY}")
        .build();
  }

  public Mono<ExternalData> fetchData(String id) {
    return webClient.get()
        .uri("/data/{id}", id)
        .retrieve()
        .bodyToMono(ExternalData.class)
        .timeout(Duration.ofSeconds(5))
        .retryWhen(Retry.backoff(3, Duration.ofSeconds(1))
            .filter(ex -> isRetryable(ex))
            .doBeforeRetry(signal -> log.warn("retry_fetch_data id={}", id)))
        .onErrorMap(TimeoutException.class, ex -> new ServiceException("Request timeout", ex))
        .doOnError(ex -> log.error("fetch_data_failed id={}", id, ex));
  }

  private boolean isRetryable(Throwable ex) {
    return ex instanceof TimeoutException ||
           (ex instanceof WebClientResponseException &&
            ((WebClientResponseException) ex).getStatusCode().is5xxServerError());
  }
}
```

### When Reactive Is Worth the Complexity

Reactive patterns excel when:
- Handling 10,000+ concurrent connections with limited threads
- Making 3+ non-blocking I/O calls per request
- Building real-time features (WebSocket streams, Server-Sent Events)
- Processing high-volume message streams (Kafka consumers)

**Avoid reactive if:**
- CPU-bound work dominates
- Average request involves 1-2 database queries
- Team lacks reactive experience

## Project Loom: Virtual Threads (Java 21+)

Virtual threads replace the thread-per-request model with lightweight continuations, dramatically improving throughput for I/O-bound workloads.

### Enabling Virtual Threads (Spring Boot 3.1+)

```properties
# application.properties
spring.threads.virtual.enabled=true
spring.main.keep-alive=true
```

This replaces the default Tomcat thread pool with virtual threads for all request handling. No code changes required.

> Java 21 minimum. Java 24+ strongly recommended.
> `spring.main.keep-alive=true` ensures `@Scheduled` tasks keep the JVM alive (virtual threads are daemon).

### When Virtual Threads Help

Virtual threads excel for **I/O-bound workloads**:
- Database queries (JDBC blocking I/O)
- HTTP client calls (RestTemplate, WebClient in blocking mode)
- File I/O

Rule of thumb: if threads spend >70% of time blocking on I/O, virtual threads improve throughput.

**Avoid for CPU-bound work** — virtual threads provide no benefit for computation.

### Carrier Thread Pinning — What to Avoid

Virtual threads mount on OS "carrier threads." Pinning occurs when a virtual thread cannot unmount:

```java
// WRONG: synchronized + blocking I/O pins carrier thread
synchronized (lock) {
    result = jdbcTemplate.query(...);  // PINNED
}

// CORRECT: use ReentrantLock instead
private final ReentrantLock lock = new ReentrantLock();
lock.lock();
try {
    result = jdbcTemplate.query(...);  // Virtual thread can unmount
} finally {
    lock.unlock();
}
```

Add JVM flag to detect pinning:
```
-Djdk.tracePinnedThreads=full
```

Check logs for `VirtualThread` pinning messages and address each one. Hibernate's internal synchronization usually isn't a bottleneck with HikariCP pooling — confirm via load tests.

### Structured Concurrency (Java 21 preview → stable in 24)

Run parallel subtasks with automatic cancellation on failure:

```java
import java.util.concurrent.StructuredTaskScope;

public UserProfile getProfile(UserId id) throws Exception {
    try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
        Subtask<User> user = scope.fork(() -> userService.findById(id));
        Subtask<List<Order>> orders = scope.fork(() -> orderService.findByUser(id));

        scope.join().throwIfFailed();
        return new UserProfile(user.get(), orders.get());
    }
}
```

If either subtask fails, the scope cancels all remaining subtasks automatically.

### Connection Pool Tuning with Virtual Threads

Virtual threads allow many more concurrent requests, but the database remains the bottleneck:

```properties
# Don't size pool to CPU cores — size to DB capacity
spring.datasource.hikari.maximum-pool-size=50
```

Each concurrent request needs a DB connection. Profile and tune pool size based on DB throughput, not thread count.

### Observability

Monitor virtual thread health:
```
GET /actuator/metrics/jvm.threads.live
GET /actuator/metrics/jvm.threads.daemon
```

Via JFR (Java Flight Recorder):
```bash
jcmd <pid> JFR.start duration=60s filename=recording.jfr
```

Analyze in JDK Mission Control for pinning and blocking events.

### Virtual Threads Compatibility Checklist

- [ ] `spring.threads.virtual.enabled=true` in application.properties
- [ ] `-Djdk.tracePinnedThreads=full` reviewed for pinning
- [ ] Replaced `synchronized` blocks around I/O with `ReentrantLock`
- [ ] HikariCP pool tuned to DB capacity
- [ ] Avoid `ThreadLocal`; use `ScopedValue` (Java 21+)
- [ ] Load tested: confirm throughput improvement
- [ ] Java 21+ confirmed

## Cross-References

- **Event-driven patterns** → See `event-sourcing` skill
- **Transactional Outbox pattern** → See `saga-orchestration` skill
- **CQRS patterns** → See `cqrs-implementation` skill

## Agent Support

- `java-reviewer`: Code review for reactive implementations
- `code-reviewer`: General code quality and patterns
