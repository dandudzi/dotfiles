---
name: springboot-patterns
description: Spring Boot architecture patterns, REST API design, layered services, data access, caching, async processing, and logging. Use for Java Spring Boot backend work.
origin: ECC
---

# Spring Boot Development Patterns

Spring Boot architecture and API patterns for scalable, production-grade services.

## Spring Boot Version Guide

| Version | Status | Key Additions |
|---------|--------|--------------|
| 3.3.x | Stable (min) | CDS (Class Data Sharing), `/actuator/sbom` endpoint, SSL bundle reloading |
| 3.4.x | Stable | Structured JSON logging (`spring.logging.structured.format.console=ecs\|logstash`), RestClient enhancements, `@Fallback` beans |
| 3.5.x | Stable (recommended) | `ProcessInfo.VirtualThreadsInfo` metrics, Docker Compose enhancements, OTLP tracing improvements |
| 4.0.x | Stable (latest) | Jakarta EE 11, Spring Framework 7, JSpecify null-safety, API versioning |

Java minimum: **21 LTS**. Java 24+ strongly recommended when using virtual threads.

## When to Activate

- Building REST APIs with Spring MVC or WebFlux
- Structuring controller → service → repository layers
- Configuring Spring Data JPA, caching, or async processing
- Adding validation, exception handling, or pagination
- Setting up profiles for dev/staging/production environments
- Implementing event-driven patterns with Spring Events or Kafka

## REST API Structure

**Security Requirement**: All public endpoints MUST have rate limiting to prevent abuse, brute force, and DDoS. Use Resilience4j or custom filters.

```java
@RestController
@RequestMapping("/api/markets")
@Validated
class MarketController {
  private final MarketService marketService;

  MarketController(MarketService marketService) {
    this.marketService = marketService;
  }

  @GetMapping
  ResponseEntity<Page<MarketResponse>> list(
      @RequestParam(defaultValue = "0") int page,
      @RequestParam(defaultValue = "20") int size) {
    Page<Market> markets = marketService.list(PageRequest.of(page, size));
    return ResponseEntity.ok(markets.map(MarketResponse::from));
  }

  @PostMapping
  ResponseEntity<MarketResponse> create(@Valid @RequestBody CreateMarketRequest request) {
    Market market = marketService.create(request);
    return ResponseEntity.status(HttpStatus.CREATED).body(MarketResponse.from(market));
  }
}

// Minimal Resilience4j rate limiting example (pom.xml: io.github.resilience4j:resilience4j-spring-boot3)
@Configuration
public class RateLimitConfig {
  @Bean
  public RateLimiter publicEndpointLimiter() {
    RateLimiterConfig config = RateLimiterConfig.custom()
        .limitRefreshPeriod(Duration.ofMinutes(1))
        .limitForPeriod(100)  // 100 requests per minute per user
        .timeoutDuration(Duration.ofMillis(25))
        .build();
    return RateLimiter.of("public-endpoints", config);
  }
}

// Apply at controller level or use @RateLimiter("publicEndpointLimiter") on individual endpoints
```

## Repository Pattern (Spring Data JPA)

```java
public interface MarketRepository extends JpaRepository<MarketEntity, Long> {
  @Query("select m from MarketEntity m where m.status = :status order by m.volume desc")
  List<MarketEntity> findActive(@Param("status") MarketStatus status, Pageable pageable);
}
```

## Service Layer with Transactions

**Security Requirement**: Protect data mutations with @PreAuthorize to enforce authorization at the service layer, not just the controller.

```java
@Service
public class MarketService {
  private final MarketRepository repo;

  public MarketService(MarketRepository repo) {
    this.repo = repo;
  }

  @Transactional
  @PreAuthorize("hasRole('ADMIN') or hasPermission(#request, 'CREATE')")
  public Market create(CreateMarketRequest request) {
    MarketEntity entity = MarketEntity.from(request);
    MarketEntity saved = repo.save(entity);
    return Market.from(saved);
  }

  @Transactional(readOnly = true)
  public Market getById(Long id) {
    // Read operations are typically public or protected by data-level filters
    return repo.findById(id)
        .map(Market::from)
        .orElseThrow(() -> new EntityNotFoundException("Market not found"));
  }

  @Transactional
  @PreAuthorize("hasRole('ADMIN') or @marketService.isOwner(authentication.principal, #id)")
  public void delete(Long id) {
    repo.deleteById(id);
  }
}
```

## DTOs and Validation

```java
public record CreateMarketRequest(
    @NotBlank @Size(max = 200) String name,
    @NotBlank @Size(max = 2000) String description,
    @NotNull @FutureOrPresent Instant endDate,
    @NotEmpty List<@NotBlank String> categories) {}

public record MarketResponse(Long id, String name, MarketStatus status) {
  static MarketResponse from(Market market) {
    return new MarketResponse(market.id(), market.name(), market.status());
  }
}
```

## Exception Handling

**Security Note**: Error messages MUST NOT leak API schema, field names, or database details to clients. Use opaque error codes with server-side correlation IDs for support.

```java
@ControllerAdvice
class GlobalExceptionHandler {
  private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

  @ExceptionHandler(MethodArgumentNotValidException.class)
  ResponseEntity<ApiError> handleValidation(MethodArgumentNotValidException ex) {
    String correlationId = UUID.randomUUID().toString();

    // INSECURE: logs validation details to client (leaks schema)
    // String message = ex.getBindingResult().getFieldErrors().stream()
    //     .map(e -> e.getField() + ": " + e.getDefaultMessage())
    //     .collect(Collectors.joining(", "));

    // SECURE: opaque message, details logged server-side with correlation ID
    log.warn("validation_error correlationId={} errors={}", correlationId,
        ex.getBindingResult().getFieldErrors());

    return ResponseEntity.badRequest()
        .body(new ApiError("VALIDATION_ERROR", correlationId, "Invalid request"));
  }

  @ExceptionHandler(AccessDeniedException.class)
  ResponseEntity<ApiError> handleAccessDenied() {
    return ResponseEntity.status(HttpStatus.FORBIDDEN)
        .body(ApiError.of("Forbidden"));
  }

  @ExceptionHandler(Exception.class)
  ResponseEntity<ApiError> handleGeneric(Exception ex) {
    String correlationId = UUID.randomUUID().toString();
    // Log unexpected errors with stack traces SERVER-SIDE only
    log.error("unhandled_exception correlationId={}", correlationId, ex);

    // Return opaque error to client
    return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
        .body(new ApiError("INTERNAL_ERROR", correlationId, "Internal server error"));
  }
}

// Secure error response format
record ApiError(String errorCode, String correlationId, String message) {
  static ApiError of(String message) {
    return new ApiError("ERROR", UUID.randomUUID().toString(), message);
  }
}
```

## Caching

Requires `@EnableCaching` on a configuration class.

```java
@Service
public class MarketCacheService {
  private final MarketRepository repo;

  public MarketCacheService(MarketRepository repo) {
    this.repo = repo;
  }

  @Cacheable(value = "market", key = "#id")
  public Market getById(Long id) {
    return repo.findById(id)
        .map(Market::from)
        .orElseThrow(() -> new EntityNotFoundException("Market not found"));
  }

  @CacheEvict(value = "market", key = "#id")
  public void evict(Long id) {}
}
```

## Async Processing

Requires `@EnableAsync` on a configuration class.

```java
@Service
public class NotificationService {
  @Async
  public CompletableFuture<Void> sendAsync(Notification notification) {
    // send email/SMS
    return CompletableFuture.completedFuture(null);
  }
}
```

## Logging (SLF4J)

```java
@Service
public class ReportService {
  private static final Logger log = LoggerFactory.getLogger(ReportService.class);

  public Report generate(Long marketId) {
    log.info("generate_report marketId={}", marketId);
    try {
      // logic
    } catch (Exception ex) {
      log.error("generate_report_failed marketId={}", marketId, ex);
      throw ex;
    }
    return new Report();
  }
}
```

## Middleware / Filters

```java
@Component
public class RequestLoggingFilter extends OncePerRequestFilter {
  private static final Logger log = LoggerFactory.getLogger(RequestLoggingFilter.class);

  @Override
  protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
      FilterChain filterChain) throws ServletException, IOException {
    long start = System.currentTimeMillis();
    try {
      filterChain.doFilter(request, response);
    } finally {
      long duration = System.currentTimeMillis() - start;
      log.info("req method={} uri={} status={} durationMs={}",
          request.getMethod(), request.getRequestURI(), response.getStatus(), duration);
    }
  }
}
```

## Pagination and Sorting

```java
PageRequest page = PageRequest.of(pageNumber, pageSize, Sort.by("createdAt").descending());
Page<Market> results = marketService.list(page);
```

## Error-Resilient External Calls

```java
public <T> T withRetry(Supplier<T> supplier, int maxRetries) {
  int attempts = 0;
  while (true) {
    try {
      return supplier.get();
    } catch (Exception ex) {
      attempts++;
      if (attempts >= maxRetries) {
        throw ex;
      }
      try {
        Thread.sleep((long) Math.pow(2, attempts) * 100L);
      } catch (InterruptedException ie) {
        Thread.currentThread().interrupt();
        throw ex;
      }
    }
  }
}
```

## Rate Limiting (Filter + Bucket4j)

**Security Note**: The `X-Forwarded-For` header is untrusted by default because clients can spoof it.
Only use forwarded headers when:
1. Your app is behind a trusted reverse proxy (nginx, AWS ALB, etc.)
2. You have registered `ForwardedHeaderFilter` as a bean
3. You have configured `server.forward-headers-strategy=NATIVE` or `FRAMEWORK` in application properties
4. Your proxy is configured to overwrite (not append to) the `X-Forwarded-For` header

### Startup Validation for Forwarded Headers

**CRITICAL**: Misconfigured forwarded headers expose rate limiting and authentication bypasses. Add this startup validator:

```java
@Component
public class ForwardHeadersStrategyValidator implements ApplicationRunner {
    @Value("${server.forward-headers-strategy:NONE}")
    private String forwardHeadersStrategy;

    @Override
    public void run(ApplicationArguments args) throws Exception {
        if ("NONE".equalsIgnoreCase(forwardHeadersStrategy)) {
            throw new IllegalStateException(
                "server.forward-headers-strategy must be NATIVE or FRAMEWORK " +
                "to prevent X-Forwarded-For spoofing and rate limit bypass. " +
                "Add to application.yml: server.forward-headers-strategy: NATIVE"
            );
        }
    }
}
```

This bean throws at startup if forwarded headers are misconfigured, preventing silent security failures in production.

When `ForwardedHeaderFilter` is properly configured, `request.getRemoteAddr()` will automatically
return the correct client IP from the forwarded headers. Without this configuration, use
`request.getRemoteAddr()` directly—it returns the immediate connection IP, which is the only
trustworthy value.

```java
@Component
public class RateLimitFilter extends OncePerRequestFilter {
  private final Map<String, Bucket> buckets = new ConcurrentHashMap<>();

  /*
   * SECURITY: This filter uses request.getRemoteAddr() to identify clients for rate limiting.
   *
   * If your application is behind a reverse proxy (nginx, AWS ALB, etc.), you MUST configure
   * Spring to handle forwarded headers properly for accurate client IP detection:
   *
   * 1. Set server.forward-headers-strategy=NATIVE (for cloud platforms) or FRAMEWORK in
   *    application.properties/yaml
   * 2. If using FRAMEWORK strategy, register ForwardedHeaderFilter:
   *
   *    @Bean
   *    ForwardedHeaderFilter forwardedHeaderFilter() {
   *        return new ForwardedHeaderFilter();
   *    }
   *
   * 3. Ensure your proxy overwrites (not appends) the X-Forwarded-For header to prevent spoofing
   * 4. Configure server.tomcat.remoteip.trusted-proxies or equivalent for your container
   *
   * Without this configuration, request.getRemoteAddr() returns the proxy IP, not the client IP.
   * Do NOT read X-Forwarded-For directly—it is trivially spoofable without trusted proxy handling.
   */
  @Override
  protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
      FilterChain filterChain) throws ServletException, IOException {
    // Use getRemoteAddr() which returns the correct client IP when ForwardedHeaderFilter
    // is configured, or the direct connection IP otherwise. Never trust X-Forwarded-For
    // headers directly without proper proxy configuration.
    String clientIp = request.getRemoteAddr();

    Bucket bucket = buckets.computeIfAbsent(clientIp,
        k -> Bucket.builder()
            .addLimit(Bandwidth.classic(100, Refill.greedy(100, Duration.ofMinutes(1))))
            .build());

    if (bucket.tryConsume(1)) {
      filterChain.doFilter(request, response);
    } else {
      response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
    }
  }
}
```

## Background Jobs

Use Spring’s `@Scheduled` or integrate with queues (e.g., Kafka, SQS, RabbitMQ). Keep handlers idempotent and observable.

## Observability

- Structured logging (JSON) via Logback encoder
- Metrics: Micrometer + Prometheus/OTel
- Tracing: Micrometer Tracing with OpenTelemetry or Brave backend

## Production Defaults

- Prefer constructor injection, avoid field injection
- Enable `spring.mvc.problemdetails.enabled=true` for RFC 7807 errors (Spring Boot 3+)
- Configure HikariCP pool sizes for workload, set timeouts
- Use `@Transactional(readOnly = true)` for queries
- Enforce null-safety via `@NonNull` and `Optional` where appropriate

**Remember**: Keep controllers thin, services focused, repositories simple, and errors handled centrally. Optimize for maintainability and testability.

## WebFlux Reactive Patterns

Non-blocking, async request handling with Mono and Flux for high-concurrency scenarios.

### Reactive REST Controller

```java
// pom.xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-webflux</artifactId>
</dependency>

// Reactive controller
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
        .onErrorResume(EntityNotFoundException.class, ex ->
            Mono.just(ResponseEntity.notFound().build()))
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

// Reactive service
@Service
public class ReactiveOrderService {
  private final ReactiveOrderRepository orderRepository;
  private static final Logger log = LoggerFactory.getLogger(ReactiveOrderService.class);

  public ReactiveOrderService(ReactiveOrderRepository orderRepository) {
    this.orderRepository = orderRepository;
  }

  public Mono<Order> findById(Long id) {
    return orderRepository.findById(id)
        .doOnSubscribe(sub -> log.info("find_order_start id={}", id))
        .doOnSuccess(order -> log.info("find_order_success id={}", id))
        .doOnError(ex -> log.error("find_order_failed id={}", id, ex));
  }

  public Flux<Order> list(int page, int size) {
    return orderRepository.findAll()
        .skip((long) page * size)
        .take(size)
        .doOnError(ex -> log.error("list_orders_failed", ex));
  }

  public Mono<Order> create(CreateOrderRequest request) {
    Order order = Order.from(request);
    return orderRepository.save(order)
        .doOnSuccess(saved -> log.info("order_created id={}", saved.id()));
  }
}

// Reactive repository
@Repository
public interface ReactiveOrderRepository extends ReactiveCrudRepository<OrderEntity, Long> {
  Flux<OrderEntity> findByUserId(String userId);
}
```

### R2DBC for Reactive Database Access

```java
// pom.xml
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
    username: app
    password: ${DB_PASSWORD}
    pool:
      initial-size: 10
      max-size: 20
      max-idle-time: 30m

// Entity with @Query for reactive queries
@Table("orders")
public record OrderEntity(
    @Id Long id,
    String userId,
    BigDecimal total,
    OrderStatus status,
    Instant createdAt) {}

// Reactive CRUD + custom queries
@Repository
public interface OrderRepository extends ReactiveCrudRepository<OrderEntity, Long> {
  @Query("select * from orders where user_id = $1 order by created_at desc")
  Flux<OrderEntity> findByUserIdOrdered(String userId);

  @Query("select * from orders where status = $1 and created_at > $2")
  Flux<OrderEntity> findRecentByStatus(OrderStatus status, Instant since);

  Mono<Long> countByUserId(String userId);
}

// Service using R2DBC
@Service
public class OrderStatsService {
  private final OrderRepository orderRepository;

  public OrderStatsService(OrderRepository orderRepository) {
    this.orderRepository = orderRepository;
  }

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

### When Reactive is Worth the Complexity

Reactive patterns excel when:
- Handling 10,000+ concurrent connections with limited threads (e.g., API gateway)
- Making multiple non-blocking I/O calls per request (3+ external service calls)
- Building real-time features (WebSocket streams, Server-Sent Events)
- Processing high-volume message streams (Kafka consumers)

**Avoid reactive if:**
- CPU-bound work dominates (complex calculations)
- Average request involves 1-2 database queries
- Team lacks reactive experience (learning curve is steep)
- Debugging reactive code requires specialized tools and expertise

## Event-Driven Patterns

Domain events for loose coupling and scalable systems.

### Spring Events (In-Process)

```java
// Domain event
public record OrderCreatedEvent(Long orderId, String userId, BigDecimal total) {}

// Publisher (uses ApplicationEventPublisher)
@Service
public class OrderService {
  private final OrderRepository orderRepository;
  private final ApplicationEventPublisher eventPublisher;
  private static final Logger log = LoggerFactory.getLogger(OrderService.class);

  public OrderService(OrderRepository orderRepository, ApplicationEventPublisher eventPublisher) {
    this.orderRepository = orderRepository;
    this.eventPublisher = eventPublisher;
  }

  @Transactional
  public Order create(CreateOrderRequest request) {
    Order order = Order.from(request);
    Order saved = orderRepository.save(order);
    log.info("order_created id={}", saved.id());

    // Publish event after transaction commits
    eventPublisher.publishEvent(
        new OrderCreatedEvent(saved.id(), saved.userId(), saved.total()));

    return saved;
  }
}

// Consumer with @EventListener
@Component
public class OrderEventListeners {
  private static final Logger log = LoggerFactory.getLogger(OrderEventListeners.class);

  @EventListener
  @Async  // Non-blocking listener
  public void onOrderCreated(OrderCreatedEvent event) {
    log.info("send_notification orderId={}", event.orderId());
    // Send email, update cache, trigger workflow, etc.
  }

  @EventListener
  @Async
  public void onOrderCreatedAnalytics(OrderCreatedEvent event) {
    log.info("record_analytics orderId={}", event.orderId());
    // Update metrics, analytics pipeline
  }
}

// Configuration
@Configuration
public class EventConfig {
  @Bean
  public Executor taskExecutor() {
    return Executors.newVirtualThreadPerTaskExecutor();  // Java 21+
  }
}
```

### Transactional Outbox Pattern

Ensures event publishing reliability by writing events and entities transactionally.

```java
// Outbox table entity
@Table("order_events")
public record OrderEventOutbox(
    @Id Long id,
    String eventType,
    String payload,
    Instant createdAt,
    Instant publishedAt) {}

// Repository
@Repository
public interface OrderEventOutboxRepository extends JpaRepository<OrderEventOutbox, Long> {
  List<OrderEventOutbox> findByPublishedAtIsNull();
}

// Service: write order + event in same transaction
@Service
public class OrderServiceWithOutbox {
  private final OrderRepository orderRepository;
  private final OrderEventOutboxRepository outboxRepository;
  private static final Logger log = LoggerFactory.getLogger(OrderServiceWithOutbox.class);

  public OrderServiceWithOutbox(OrderRepository orderRepository,
                                 OrderEventOutboxRepository outboxRepository) {
    this.orderRepository = orderRepository;
    this.outboxRepository = outboxRepository;
  }

  @Transactional
  public Order create(CreateOrderRequest request) {
    Order order = Order.from(request);
    Order saved = orderRepository.save(order);
    log.info("order_saved id={}", saved.id());

    // Write event to outbox in same transaction
    OrderCreatedEvent event = new OrderCreatedEvent(
        saved.id(), saved.userId(), saved.total());
    OrderEventOutbox outbox = new OrderEventOutbox(
        null,
        "order.created",
        jsonSerialize(event),
        Instant.now(),
        null  // publishedAt null until sent
    );
    outboxRepository.save(outbox);

    return saved;
  }

  private String jsonSerialize(Object event) {
    // Use Jackson or similar
    return "";
  }
}

// Background job: poll and publish
@Service
public class OutboxPoller {
  private final OrderEventOutboxRepository outboxRepository;
  private final StreamBridge streamBridge;
  private static final Logger log = LoggerFactory.getLogger(OutboxPoller.class);

  public OutboxPoller(OrderEventOutboxRepository outboxRepository, StreamBridge streamBridge) {
    this.outboxRepository = outboxRepository;
    this.streamBridge = streamBridge;
  }

  @Scheduled(fixedDelay = 5000)  // Poll every 5 seconds
  public void publishOutboxEvents() {
    List<OrderEventOutbox> unpublished = outboxRepository.findByPublishedAtIsNull();
    for (OrderEventOutbox event : unpublished) {
      try {
        boolean sent = streamBridge.send("orders-out-0", event.payload());
        if (sent) {
          event = event.withPublishedAt(Instant.now());
          outboxRepository.save(event);
          log.info("outbox_published eventId={}", event.id());
        }
      } catch (Exception ex) {
        log.error("outbox_publish_failed eventId={}", event.id(), ex);
      }
    }
  }
}
```

## CQRS with Spring

Separate read and write models for optimized queries and scalability.

### Command Service (Write Model)

```java
// Command DTOs
public record CreateOrderCommand(String userId, List<OrderItem> items) {}
public record ApproveOrderCommand(Long orderId, String approverUserId) {}

// Command handler service
@Service
@Transactional
public class OrderCommandService {
  private final OrderRepository orderRepository;
  private final OrderEventPublisher eventPublisher;
  private static final Logger log = LoggerFactory.getLogger(OrderCommandService.class);

  public OrderCommandService(OrderRepository orderRepository, OrderEventPublisher eventPublisher) {
    this.orderRepository = orderRepository;
    this.eventPublisher = eventPublisher;
  }

  public Order handle(CreateOrderCommand cmd) {
    log.info("handle_create_order userId={}", cmd.userId());
    Order order = new Order(
        null, cmd.userId(), cmd.items(),
        OrderStatus.PENDING, Instant.now());
    Order saved = orderRepository.save(order);

    eventPublisher.publishOrderCreated(
        new OrderCreatedEvent(saved.id(), saved.userId(), saved.total()));

    return saved;
  }

  public Order handle(ApproveOrderCommand cmd) {
    log.info("handle_approve_order orderId={}", cmd.orderId());
    Order order = orderRepository.findById(cmd.orderId())
        .orElseThrow(() -> new EntityNotFoundException("Order not found"));

    order = order.withStatus(OrderStatus.APPROVED)
        .withApprovedBy(cmd.approverUserId())
        .withApprovedAt(Instant.now());
    Order saved = orderRepository.save(order);

    eventPublisher.publishOrderApproved(new OrderApprovedEvent(saved.id()));
    return saved;
  }
}

// Command controller (write API)
@RestController
@RequestMapping("/api/orders/commands")
public class OrderCommandController {
  private final OrderCommandService commandService;

  public OrderCommandController(OrderCommandService commandService) {
    this.commandService = commandService;
  }

  @PostMapping
  public ResponseEntity<OrderResponse> createOrder(@Valid @RequestBody CreateOrderCommand cmd) {
    Order order = commandService.handle(cmd);
    return ResponseEntity.status(HttpStatus.CREATED).body(OrderResponse.from(order));
  }

  @PostMapping("/{id}/approve")
  public ResponseEntity<OrderResponse> approveOrder(
      @PathVariable Long id,
      @RequestParam String approverUserId) {
    Order order = commandService.handle(new ApproveOrderCommand(id, approverUserId));
    return ResponseEntity.ok(OrderResponse.from(order));
  }
}
```

### Query Service (Read Model)

```java
// Read model entity (denormalized, optimized for queries)
@Table("order_view")
public record OrderView(
    @Id Long id,
    String userId,
    BigDecimal total,
    OrderStatus status,
    int itemCount,
    String approverName,
    Instant createdAt,
    Instant approvedAt) {}

// Read-only repository
@Repository
public interface OrderViewRepository extends JpaRepository<OrderView, Long> {
  List<OrderView> findByUserId(String userId);

  @Query("select * from order_view where status = :status and approved_at is not null order by approved_at desc")
  Page<OrderView> findApprovedOrders(@Param("status") OrderStatus status, Pageable pageable);

  @Query("select count(*) from order_view where user_id = :userId")
  long countByUserId(@Param("userId") String userId);
}

// Query service
@Service
public class OrderQueryService {
  private final OrderViewRepository viewRepository;
  private static final Logger log = LoggerFactory.getLogger(OrderQueryService.class);

  public OrderQueryService(OrderViewRepository viewRepository) {
    this.viewRepository = viewRepository;
  }

  @Transactional(readOnly = true)
  public OrderView getOrder(Long id) {
    log.info("query_order id={}", id);
    return viewRepository.findById(id)
        .orElseThrow(() -> new EntityNotFoundException("Order not found"));
  }

  @Transactional(readOnly = true)
  public Page<OrderView> getUserOrders(String userId, int page, int size) {
    log.info("query_user_orders userId={}", userId);
    return viewRepository.findByUserId(userId);  // Simplified; normally paged
  }

  @Transactional(readOnly = true)
  public Page<OrderView> getApprovedOrders(OrderStatus status, int page, int size) {
    return viewRepository.findApprovedOrders(status,
        PageRequest.of(page, size, Sort.by("approvedAt").descending()));
  }
}

// Query controller (read API)
@RestController
@RequestMapping("/api/orders/queries")
public class OrderQueryController {
  private final OrderQueryService queryService;

  public OrderQueryController(OrderQueryService queryService) {
    this.queryService = queryService;
  }

  @GetMapping("/{id}")
  public ResponseEntity<OrderView> getOrder(@PathVariable Long id) {
    OrderView view = queryService.getOrder(id);
    return ResponseEntity.ok(view);
  }

  @GetMapping("/user/{userId}")
  public ResponseEntity<List<OrderView>> getUserOrders(
      @PathVariable String userId,
      @RequestParam(defaultValue = "0") int page,
      @RequestParam(defaultValue = "20") int size) {
    Page<OrderView> orders = queryService.getUserOrders(userId, page, size);
    return ResponseEntity.ok(orders.getContent());
  }

  @GetMapping("/approved")
  public ResponseEntity<Page<OrderView>> getApprovedOrders(
      @RequestParam OrderStatus status,
      @RequestParam(defaultValue = "0") int page,
      @RequestParam(defaultValue = "20") int size) {
    Page<OrderView> orders = queryService.getApprovedOrders(status, page, size);
    return ResponseEntity.ok(orders);
  }
}

// Event handler to update read model
@Component
public class OrderViewUpdater {
  private final OrderViewRepository viewRepository;
  private static final Logger log = LoggerFactory.getLogger(OrderViewUpdater.class);

  public OrderViewUpdater(OrderViewRepository viewRepository) {
    this.viewRepository = viewRepository;
  }

  @EventListener
  @Transactional
  public void onOrderCreated(OrderCreatedEvent event) {
    log.info("update_view_on_created orderId={}", event.orderId());
    // Create or update denormalized read model based on event
    OrderView view = new OrderView(
        event.orderId(), event.userId(), event.total(),
        OrderStatus.PENDING, 0, null, Instant.now(), null);
    viewRepository.save(view);
  }

  @EventListener
  @Transactional
  public void onOrderApproved(OrderApprovedEvent event) {
    log.info("update_view_on_approved orderId={}", event.orderId());
    // Update read model
    OrderView view = viewRepository.findById(event.orderId())
        .orElseThrow();
    view = view.withStatus(OrderStatus.APPROVED)
        .withApprovedAt(Instant.now());
    viewRepository.save(view);
  }
}
```

## Agent Support

- **java-architect**: System design, microservices architecture, reactive patterns
- **java-reviewer**: Code review for Spring Boot implementations
- **code-reviewer**: General code quality and patterns
- **spring-expert** (if available): Deep Spring framework expertise
- **docker-expert**: Containerization and deployment patterns
- **kubernetes-architect**: Cluster design for Spring Boot microservices

## Skill References

- **spring-cloud-patterns**: Microservices, distributed configuration, circuit breakers
- **springboot-security**: Authentication, authorization, input validation
- **springboot-tdd**: Test-driven development for Spring Boot
- **springboot-verification**: Build verification and quality gates
- **architecture-patterns**: Clean architecture and domain-driven design
- **ddd-tactical-patterns**: Domain-driven design implementation
- **event-sourcing**: Event sourcing infrastructure and persistence

## Project Loom: Virtual Threads (Java 21+)

### Enabling Virtual Threads (Spring Boot 3.1+)

Add to `application.properties`:
```
spring.threads.virtual.enabled=true
# If using @Scheduled, also add:
spring.main.keep-alive=true
```

This replaces the default Tomcat thread pool with virtual threads for all request handling. No other code changes required.

> `spring.threads.virtual.enabled` available since Spring Boot 3.1+. Java 21 required; Java 24+ strongly recommended.
> `spring.main.keep-alive=true` is needed because virtual threads are daemon threads — without it, `@Scheduled` tasks won't keep the JVM alive.

### When Virtual Threads Help

Virtual threads excel for **I/O-bound workloads**:
- Database queries (JDBC blocking I/O)
- HTTP client calls (RestTemplate, WebClient in blocking mode)
- File I/O
- Any blocking wait

**Do NOT use for CPU-bound work** — virtual threads provide no benefit for computation-heavy tasks. Use `ForkJoinPool.commonPool()` or a dedicated platform thread executor for CPU work.

Rule of thumb: if threads spend >70% of time blocking on I/O, virtual threads will improve throughput.

### Carrier Thread Pinning — What to Avoid

Virtual threads are mounted on OS "carrier threads." Pinning occurs when a virtual thread cannot be unmounted:

**Avoid these patterns in I/O paths:**
- `synchronized` blocks that call blocking I/O — pins the carrier thread, defeats virtual thread benefit
- `synchronized` methods on classes used in I/O paths

**Solutions:**
```java
// WRONG: synchronized + blocking I/O pins carrier thread
synchronized (lock) {
    result = jdbcTemplate.query(...); // pins!
}

// CORRECT: use ReentrantLock instead
private final ReentrantLock lock = new ReentrantLock();
lock.lock();
try {
    result = jdbcTemplate.query(...); // virtual thread can be unmounted
} finally {
    lock.unlock();
}
```

**Detection:** Add JVM flag to log pinning events:
```
-Djdk.tracePinnedThreads=full
```
Check logs for `VirtualThread` pinning messages. Address each one.

**Hibernate note:** Hibernate's connection acquisition uses `synchronized` internally. With connection pooling (HikariCP), this usually isn't a bottleneck — but run load tests to confirm.

### Structured Concurrency (Java 21 preview → stable in 24)

Run parallel subtasks with automatic cancellation on failure:

```java
import java.util.concurrent.StructuredTaskScope;

public UserProfile getProfile(UserId id) throws Exception {
    try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
        Subtask<User> user = scope.fork(() -> userService.findById(id));
        Subtask<List<Order>> orders = scope.fork(() -> orderService.findByUser(id));

        scope.join()           // wait for all
             .throwIfFailed(); // propagate first exception

        return new UserProfile(user.get(), orders.get());
    }
}
```

If either subtask fails, the scope cancels all remaining subtasks automatically.

### Connection Pool Tuning with Virtual Threads

Virtual threads allow many more concurrent requests, but the database is still the bottleneck:

```properties
# Don't size pool to CPU cores — size to DB capacity
spring.datasource.hikari.maximum-pool-size=50
# Match your DB server's max_connections / number_of_app_instances
```

With virtual threads you can handle thousands of concurrent requests — but each still needs a DB connection. Profile and tune pool size based on DB throughput, not thread count.

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
Then analyze in JDK Mission Control for pinning and blocking events.

### Virtual Threads Compatibility Checklist

- [ ] `spring.threads.virtual.enabled=true` in application.properties
- [ ] Added `-Djdk.tracePinnedThreads=full` and reviewed output
- [ ] Replaced `synchronized` blocks around I/O with `ReentrantLock`
- [ ] HikariCP pool size tuned to DB capacity (not CPU cores)
- [ ] Avoid `ThreadLocal` for request context scoping — use `ScopedValue` (Java 21+) for virtual-thread-safe scoping
- [ ] Load tested: confirm throughput improvement for I/O-bound endpoints
- [ ] Java 21+ confirmed (`java -version`)
