---
name: springboot-patterns
description: Spring Boot architecture patterns, REST API design, layered services, data access, caching, async processing, and logging. Use for Java Spring Boot backend work.
origin: ECC
model: sonnet
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

- Building REST APIs with Spring MVC
- Structuring controller → service → repository layers
- Configuring Spring Data JPA, caching, or async processing
- Adding validation, exception handling, or pagination

## REST API Structure

**Security**: All public endpoints MUST have rate limiting to prevent abuse. Use Resilience4j or custom filters.

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

// Resilience4j rate limiting (pom.xml: io.github.resilience4j:resilience4j-spring-boot3)
@Configuration
public class RateLimitConfig {
  @Bean
  public RateLimiter publicEndpointLimiter() {
    RateLimiterConfig config = RateLimiterConfig.custom()
        .limitRefreshPeriod(Duration.ofMinutes(1))
        .limitForPeriod(100)
        .timeoutDuration(Duration.ofMillis(25))
        .build();
    return RateLimiter.of("public-endpoints", config);
  }
}
```

## Repository Pattern (Spring Data JPA)

```java
public interface MarketRepository extends JpaRepository<MarketEntity, Long> {
  @Query("select m from MarketEntity m where m.status = :status order by m.volume desc")
  List<MarketEntity> findActive(@Param("status") MarketStatus status, Pageable pageable);
}
```

## Service Layer with Transactions

**Security**: Protect data mutations with `@PreAuthorize` to enforce authorization at the service layer.

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
    return Market.from(repo.save(entity));
  }

  @Transactional(readOnly = true)
  public Market getById(Long id) {
    return repo.findById(id)
        .map(Market::from)
        .orElseThrow(() -> new EntityNotFoundException("Market not found"));
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

**Security**: Error messages MUST NOT leak API schema, field names, or database details. Use opaque error codes with correlation IDs for support.

```java
@ControllerAdvice
class GlobalExceptionHandler {
  private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

  @ExceptionHandler(MethodArgumentNotValidException.class)
  ResponseEntity<ApiError> handleValidation(MethodArgumentNotValidException ex) {
    String correlationId = UUID.randomUUID().toString();
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
    log.error("unhandled_exception correlationId={}", correlationId, ex);
    return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
        .body(new ApiError("INTERNAL_ERROR", correlationId, "Internal server error"));
  }
}

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
      if (++attempts >= maxRetries) throw ex;
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

**Security**: The `X-Forwarded-For` header is untrusted by default. Only use it when:
1. Your app is behind a trusted reverse proxy (nginx, AWS ALB, etc.)
2. You have registered `ForwardedHeaderFilter` as a bean
3. You have configured `server.forward-headers-strategy=NATIVE` or `FRAMEWORK`
4. Your proxy overwrites (not appends) the `X-Forwarded-For` header

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
                "to prevent X-Forwarded-For spoofing. " +
                "Add to application.yml: server.forward-headers-strategy: NATIVE"
            );
        }
    }
}
```

```java
@Component
public class RateLimitFilter extends OncePerRequestFilter {
  private final Map<String, Bucket> buckets = new ConcurrentHashMap<>();

  @Override
  protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
      FilterChain filterChain) throws ServletException, IOException {
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

## Production Defaults

- Prefer constructor injection
- Enable `spring.mvc.problemdetails.enabled=true` for RFC 7807 errors (Spring Boot 3+)
- Configure HikariCP pool sizes for workload, set timeouts
- Use `@Transactional(readOnly = true)` for queries
- Enforce null-safety via `@NonNull` and `Optional`

## CQRS Pattern

Separate read and write models for optimized queries and scalability. Implement via dedicated command/query services. See `cqrs-implementation` skill for comprehensive patterns.

```java
@Service
@Transactional
public class OrderCommandService {
  private final OrderRepository orderRepository;
  private final ApplicationEventPublisher eventPublisher;

  public Order handle(CreateOrderCommand cmd) {
    Order order = new Order(null, cmd.userId(), cmd.items(), OrderStatus.PENDING, Instant.now());
    Order saved = orderRepository.save(order);
    eventPublisher.publishEvent(new OrderCreatedEvent(saved.id(), saved.userId(), saved.total()));
    return saved;
  }
}
```

## Observability

Refer to `observability-engineer` skill for structured logging, metrics, and distributed tracing setup.

## JPA Entity Immutability

JPA entities require a no-arg constructor and mutable setters for hydration, which conflicts with immutability. Practical approach:

- **Domain layer**: Use immutable records/value objects for business logic
- **Persistence layer**: JPA entities may use package-private setters; keep mutation contained
- Never expose mutable entities to controllers — map to DTOs at the service boundary
- Use `@Immutable` (Hibernate) for read-only entities

## Optional Usage

```java
// Fluent Optional usage
public String getUserDisplayName(String userId) {
    return userRepository.findById(userId)
        .map(User::displayName)
        .orElse("Unknown User");
}

// Optional chaining
public BigDecimal getDiscountedPrice(String productId, String couponCode) {
    return productRepository.findById(productId)
        .flatMap(product -> couponService.findValidCoupon(couponCode)
            .map(coupon -> coupon.applyTo(product.price())))
        .orElseThrow(() -> new ProductNotFoundException(productId));
}
```

## Records vs Lombok Decision Matrix

| Scenario | Use | Why |
|----------|-----|-----|
| Immutable DTO / value object (Java 16+) | **Record** | Built-in, zero annotation overhead |
| Mutable domain object with builder | **Lombok `@Builder`** | Better support for mutable patterns |
| Backward compatibility with Java < 16 | **Lombok** | Records require Java 16+ |
| JPA entity (mutable) | **Lombok `@Entity` + `@Data`** | JPA hydration requires mutability |

**Rule**: Prefer Records for immutable data in Java 17+ projects. Use Lombok for mutable objects or legacy Java.
