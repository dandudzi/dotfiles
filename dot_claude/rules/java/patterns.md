---
paths:
  - "**/*.java"
  - "**/*.kt"
  - "**/pom.xml"
  - "**/build.gradle*"
---
# Java/Kotlin Patterns

> This file extends [common/patterns.md](../common/patterns.md) with Java/Kotlin-specific content.

## Builder Pattern

```java
// Use for objects with many optional parameters
public class HttpRequest {
    private final String url;
    private final String method;
    private final Map<String, String> headers;
    private final Duration timeout;

    private HttpRequest(Builder builder) {
        this.url = builder.url;
        this.method = builder.method;
        this.headers = Map.copyOf(builder.headers);
        this.timeout = builder.timeout;
    }

    public static Builder builder(String url) {
        return new Builder(url);
    }

    public static class Builder {
        private final String url;
        private String method = "GET";
        private final Map<String, String> headers = new HashMap<>();
        private Duration timeout = Duration.ofSeconds(30);

        private Builder(String url) {
            this.url = Objects.requireNonNull(url);
        }

        public Builder method(String method) { this.method = method; return this; }
        public Builder header(String key, String value) { headers.put(key, value); return this; }
        public Builder timeout(Duration timeout) { this.timeout = timeout; return this; }
        public HttpRequest build() { return new HttpRequest(this); }
    }
}

// Usage
var request = HttpRequest.builder("https://api.example.com/users")
    .method("POST")
    .header("Content-Type", "application/json")
    .timeout(Duration.ofSeconds(10))
    .build();
```

## Factory Method Pattern

```java
// Sealed interface with factory methods
public sealed interface Notification permits EmailNotification, SmsNotification, PushNotification {

    String recipient();
    String message();

    static Notification email(String to, String subject, String body) {
        return new EmailNotification(to, subject, body);
    }

    static Notification sms(String phoneNumber, String text) {
        return new SmsNotification(phoneNumber, text);
    }

    static Notification push(String deviceToken, String title, String body) {
        return new PushNotification(deviceToken, title, body);
    }
}
```

## Repository Pattern

```java
// Generic repository interface
public interface Repository<T, ID> {
    Optional<T> findById(ID id);
    List<T> findAll(Specification<T> spec, Pageable pageable);
    T save(T entity);
    void deleteById(ID id);
}

// Spring Data JPA implementation (auto-generated)
public interface UserRepository extends JpaRepository<UserEntity, Long> {
    Optional<UserEntity> findByEmail(String email);

    @Query("SELECT u FROM UserEntity u WHERE u.status = :status AND u.createdAt > :since")
    List<UserEntity> findActiveUsersSince(
        @Param("status") UserStatus status,
        @Param("since") Instant since
    );
}
```

### JPA Entity Immutability

JPA entities require a no-arg constructor and mutable setters for hydration, which conflicts with immutability principles. Practical approach:

- **Domain layer:** Use immutable records/value objects for business logic
- **Persistence layer:** JPA entities may use package-private setters; keep mutation contained
- **Never expose mutable entities** to controllers — map to DTOs/records at the service boundary
- Use `@Immutable` (Hibernate) for read-only entities (e.g., views, lookup tables)

## Optional Usage

```java
// GOOD: Fluent Optional usage
public String getUserDisplayName(String userId) {
    return userRepository.findById(userId)
        .map(User::displayName)
        .orElse("Unknown User");
}

// GOOD: Optional chaining
public BigDecimal getDiscountedPrice(String productId, String couponCode) {
    return productRepository.findById(productId)
        .flatMap(product -> couponService.findValidCoupon(couponCode)
            .map(coupon -> coupon.applyTo(product.price())))
        .orElseThrow(() -> new ProductNotFoundException(productId));
}

// BAD: Anti-patterns to avoid
Optional.get();                     // Use orElseThrow()
Optional.isPresent() + get();       // Use map/flatMap/orElse
Optional as method parameter;       // Use @Nullable or overloads
Optional as field;                  // Use nullable field
```

## Stream API Patterns

```java
// Grouping and aggregation
Map<Department, List<Employee>> byDepartment = employees.stream()
    .collect(Collectors.groupingBy(Employee::department));

// Complex transformation pipeline
List<OrderSummary> summaries = orders.stream()
    .filter(order -> order.status() == OrderStatus.COMPLETED)
    .sorted(Comparator.comparing(Order::completedAt).reversed())
    .map(order -> new OrderSummary(
        order.id(),
        order.total(),
        order.items().size()
    ))
    .toList();

// Collectors.toMap with merge function
Map<String, BigDecimal> totalsByCategory = items.stream()
    .collect(Collectors.toMap(
        Item::category,
        Item::price,
        BigDecimal::add
    ));
```

## Kotlin Extension Functions

```kotlin
// Domain-specific extensions
fun BigDecimal.toCurrency(locale: Locale = Locale.US): String =
    NumberFormat.getCurrencyInstance(locale).format(this)

fun Instant.toReadableDate(): String =
    DateTimeFormatter.ofPattern("MMM dd, yyyy")
        .withZone(ZoneId.of("UTC"))
        .format(this)

// Collection extensions
fun <T> List<T>.secondOrNull(): T? = if (size >= 2) this[1] else null

// Scope function conventions
// let: transform nullable, introduce scoped variable
val length = name?.let { it.trim().length }

// apply: configure an object
val request = HttpRequest.newBuilder().apply {
    uri(URI.create("https://api.example.com"))
    header("Accept", "application/json")
    timeout(Duration.ofSeconds(10))
}.build()

// also: side effects (logging, validation)
fun createUser(request: CreateUserRequest): User =
    userRepository.save(request.toEntity())
        .also { log.info("Created user: ${it.id}") }
```

## Kotlin Sealed Classes

```kotlin
// Result type with exhaustive matching
sealed class ApiResult<out T> {
    data class Success<T>(val data: T) : ApiResult<T>()
    data class Error(val code: Int, val message: String) : ApiResult<Nothing>()
    data object Loading : ApiResult<Nothing>()
}

fun <T> handleResult(result: ApiResult<T>) = when (result) {
    is ApiResult.Success -> "Data: ${result.data}"
    is ApiResult.Error -> "Error ${result.code}: ${result.message}"
    is ApiResult.Loading -> "Loading..."
    // No else needed -- compiler enforces exhaustiveness
}
```

## Dependency Injection

```java
// GOOD: Constructor injection (preferred in Spring)
@Service
public class OrderService {
    private final OrderRepository orderRepository;
    private final PaymentGateway paymentGateway;
    private final EventPublisher eventPublisher;

    // Single constructor -- @Autowired not needed
    public OrderService(
            OrderRepository orderRepository,
            PaymentGateway paymentGateway,
            EventPublisher eventPublisher) {
        this.orderRepository = orderRepository;
        this.paymentGateway = paymentGateway;
        this.eventPublisher = eventPublisher;
    }
}
```

```kotlin
// Kotlin: constructor injection is natural
@Service
class OrderService(
    private val orderRepository: OrderRepository,
    private val paymentGateway: PaymentGateway,
    private val eventPublisher: EventPublisher
) {
    fun createOrder(request: CreateOrderRequest): Order {
        // ...
    }
}
```

## Exception Handling

```java
// Define a base exception hierarchy per domain
public abstract class DomainException extends RuntimeException {
    private final String code;

    protected DomainException(String code, String message) {
        super(message);
        this.code = code;
    }

    public String code() { return code; }
}

public class NotFoundException extends DomainException {
    public NotFoundException(String resource, Object id) {
        super("NOT_FOUND", resource + " not found: " + id);
    }
}

public class BusinessRuleException extends DomainException {
    public BusinessRuleException(String message) {
        super("BUSINESS_RULE", message);
    }
}
```

```java
// Spring @ControllerAdvice for centralized mapping
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(NotFoundException.class)
    ResponseEntity<ErrorResponse> handleNotFound(NotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(new ErrorResponse(ex.code(), ex.getMessage()));
    }

    @ExceptionHandler(BusinessRuleException.class)
    ResponseEntity<ErrorResponse> handleBusinessRule(BusinessRuleException ex) {
        return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY)
            .body(new ErrorResponse(ex.code(), ex.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException ex) {
        String message = ex.getBindingResult().getFieldErrors().stream()
            .map(e -> e.getField() + ": " + e.getDefaultMessage())
            .collect(Collectors.joining(", "));
        return ResponseEntity.badRequest()
            .body(new ErrorResponse("VALIDATION_ERROR", message));
    }
}

public record ErrorResponse(String code, String message) {}
```

## Records vs Lombok Decision Matrix

| Scenario | Use | Why |
|----------|-----|-----|
| Immutable DTO / value object (Java 16+) | **Record** | Built-in, zero annotation overhead, native IDE support |
| Mutable domain object with builder | **Lombok `@Builder`** | `@Builder` + `@Data` or `@Value` for mutable/builder patterns |
| Backward compatibility with Java < 16 | **Lombok** | Records require Java 16+ |
| JPA entity (mutable, needs no-arg constructor) | **Lombok `@Entity` + `@Data`** | JPA hydration requires mutability |
| Type-safe wrapper with zero overhead (Kotlin) | **`@JvmInline value class`** | No Lombok needed in Kotlin |

**Rule of thumb:** Prefer Records for immutable data transfer in Java 17+ projects. Use Lombok only for mutable objects, JPA entities, or legacy Java projects.

## Agent Support

- **java-reviewer** — Java/Kotlin-specific code review

## Skill Reference

- `java-coding-standards` skill — Java coding standards
- `springboot-patterns` skill — Spring Boot patterns
