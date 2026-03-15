---
name: spring-cloud-patterns
description: Spring Cloud microservices patterns including service discovery, distributed configuration, circuit breakers, gateway routing, and distributed tracing. Use for building resilient, observable distributed systems.
origin: ECC
---

# Spring Cloud Microservices Patterns

Spring Cloud patterns for building resilient, observable, and maintainable distributed systems.

## When to Activate

- Building microservices with service discovery (Eureka, Consul)
- Implementing API Gateway routing and rate limiting
- Setting up distributed configuration (Spring Cloud Config)
- Adding circuit breakers with Resilience4j
- Implementing service-to-service communication (OpenFeign, RestClient, WebClient)
- Setting up distributed tracing with Micrometer/Zipkin/Jaeger
- Building event-driven systems with Spring Cloud Stream (Kafka, RabbitMQ)
- Debugging issues in distributed systems (latency, cascading failures, timeouts)

## Version Compatibility

| Spring Boot | Spring Cloud Train | Notes |
|-------------|-------------------|-------|
| 4.0.x | 2026.x (pending GA) | Verify availability before migrating |
| 3.5.x | 2025.1.x (Oakwood) | Current stable train |
| 3.4.x | 2024.0.x | |
| 3.3.x | 2023.0.x (Leyton) | |

> Teams migrating to Spring Boot 4.0 should confirm Spring Cloud 2026.x GA availability before upgrading.

## Service Discovery with Eureka

Register services and enable client-side load balancing.

### Service Registration

```java
// pom.xml
<dependency>
  <groupId>org.springframework.cloud</groupId>
  <artifactId>spring-cloud-starter-netflix-eureka-client</artifactId>
</dependency>

// application.yml
spring:
  application:
    name: order-service
  cloud:
    client:
      hostname: localhost
eureka:
  client:
    service-url:
      defaultZone: http://eureka-server:8761/eureka
  instance:
    prefer-ip-address: true
    instance-id: ${spring.application.name}:${spring.application.instance_id:${random.value}}
```

### Service Discovery Client

```java
@RestController
@RequestMapping("/api/orders")
public class OrderController {
  private final DiscoveryClient discoveryClient;
  private final RestTemplate restTemplate;

  public OrderController(DiscoveryClient discoveryClient) {
    this.discoveryClient = discoveryClient;
    this.restTemplate = new RestTemplate();
  }

  @GetMapping("/{id}/details")
  public ResponseEntity<OrderDetail> getDetails(@PathVariable Long id) {
    // Discover payment service instance
    List<ServiceInstance> instances = discoveryClient.getInstances("payment-service");
    if (instances.isEmpty()) {
      throw new ServiceUnavailableException("payment-service not available");
    }

    ServiceInstance instance = instances.get(0); // Client-side load balancing
    String url = String.format("http://%s:%d/api/payments/%d",
        instance.getHost(), instance.getPort(), id);

    PaymentResponse payment = restTemplate.getForObject(url, PaymentResponse.class);
    return ResponseEntity.ok(new OrderDetail(id, payment));
  }
}

@Configuration
public class RestTemplateConfig {
  @Bean
  public RestTemplate restTemplate(RestTemplateBuilder builder) {
    return builder.setConnectTimeout(Duration.ofSeconds(5))
        .setReadTimeout(Duration.ofSeconds(10))
        .build();
  }
}
```

### Eureka Server Setup

```java
@SpringBootApplication
@EnableEurekaServer
public class EurekaServerApplication {
  public static void main(String[] args) {
    SpringApplication.run(EurekaServerApplication.class, args);
  }
}

// application.yml
eureka:
  server:
    enable-self-preservation: false
  instance:
    hostname: localhost
  client:
    register-with-eureka: false
    fetch-registry: false
    service-url:
      defaultZone: http://${eureka.instance.hostname}:${server.port}/eureka/
server:
  port: 8761
```

## Spring Cloud Gateway

API Gateway for routing, filtering, and rate limiting.

### Basic Routing Configuration

```java
// application.yml
spring:
  cloud:
    gateway:
      routes:
        - id: order-service
          uri: lb://order-service
          predicates:
            - Path=/orders/**
          filters:
            - RewritePath=/orders/(?<segment>.*), /api/orders/$\{segment}
            - name: CircuitBreaker
              args:
                name: orderBreaker
                fallbackUri: forward:/fallback/orders

        - id: payment-service
          uri: lb://payment-service
          predicates:
            - Path=/payments/**
          filters:
            - StripPrefix=0
            - name: RequestRateLimiter
              args:
                redis-rate-limiter.replenish-rate: 10
                redis-rate-limiter.burst-capacity: 20
                key-resolver: "#{@userKeyResolver}"

      default-filters:
        - name: Retry
          args:
            retries: 3
            series: SERVER_ERROR
            methods: GET,POST
            backoff:
              delay: 100
              max-delay: 1000
              multiplier: 2

server:
  port: 8080
```

### Custom Gateway Filters

```java
@Component
public class LoggingGatewayFilterFactory extends AbstractGatewayFilterFactory<LoggingGatewayFilterFactory.Config> {
  private static final Logger log = LoggerFactory.getLogger(LoggingGatewayFilterFactory.class);

  public LoggingGatewayFilterFactory() {
    super(Config.class);
  }

  @Override
  public GatewayFilter apply(Config config) {
    return (exchange, chain) -> {
      ServerHttpRequest request = exchange.getRequest();
      log.info("gateway_request method={} path={} requestId={}",
          request.getMethod(), request.getPath(),
          request.getHeaders().getFirst("X-Request-ID"));

      long start = System.currentTimeMillis();
      return chain.filter(exchange).doFinally(signal -> {
        long duration = System.currentTimeMillis() - start;
        log.info("gateway_response path={} status={} durationMs={}",
            request.getPath(),
            exchange.getResponse().getStatusCode(),
            duration);
      });
    };
  }

  public static class Config {
    // Add custom configuration if needed
  }
}

@Component("userKeyResolver")
public class UserKeyResolver implements KeyResolver {
  @Override
  public Mono<String> resolve(ServerWebExchange exchange) {
    return exchange.getPrincipal()
        .map(Principal::getName)
        .defaultIfEmpty("anonymous");
  }
}
```

## Distributed Configuration with Spring Cloud Config

Externalize configuration to a Git repository.

### Config Server Setup

```java
@SpringBootApplication
@EnableConfigServer
public class ConfigServerApplication {
  public static void main(String[] args) {
    SpringApplication.run(ConfigServerApplication.class, args);
  }
}

// application.yml
spring:
  cloud:
    config:
      server:
        git:
          uri: https://github.com/mycompany/config-repo
          username: ${GIT_USERNAME}
          password: ${GIT_PASSWORD}
          clone-on-start: true
          search-paths: '{application}/{profile}'

server:
  port: 8888
```

### Config Client Setup

```java
// pom.xml
<dependency>
  <groupId>org.springframework.cloud</groupId>
  <artifactId>spring-cloud-starter-config</artifactId>
</dependency>

// bootstrap.yml (or spring.config.import in application.yml)
spring:
  cloud:
    config:
      uri: http://config-server:8888
      fail-fast: true
      retry:
        initial-interval: 1000
        max-interval: 10000
        multiplier: 1.1
        max-attempts: 3
  application:
    name: order-service

// Properties refresh on POST /actuator/refresh
@Component
@RefreshScope
public class FeatureToggleService {
  @Value("${features.new-checkout:false}")
  private boolean newCheckoutEnabled;

  public boolean isNewCheckoutEnabled() {
    return newCheckoutEnabled;
  }
}

// Actuator endpoint to trigger refresh
@RestController
public class RefreshController {
  private final ContextRefresher contextRefresher;

  public RefreshController(ContextRefresher contextRefresher) {
    this.contextRefresher = contextRefresher;
  }

  @PostMapping("/actuator/refresh")
  public Set<String> refresh() {
    return contextRefresher.refresh();
  }
}
```

## Circuit Breakers with Resilience4j

Protect services from cascading failures.

### Resilience4j Configuration

```java
// pom.xml
<dependency>
  <groupId>io.github.resilience4j</groupId>
  <artifactId>resilience4j-spring-boot3</artifactId>
</dependency>
<dependency>
  <groupId>io.github.resilience4j</groupId>
  <artifactId>resilience4j-circuitbreaker</artifactId>
</dependency>
<dependency>
  <groupId>io.github.resilience4j</groupId>
  <artifactId>resilience4j-retry</artifactId>
</dependency>
<dependency>
  <groupId>io.github.resilience4j</groupId>
  <artifactId>resilience4j-timelimiter</artifactId>
</dependency>
<dependency>
  <groupId>io.github.resilience4j</groupId>
  <artifactId>resilience4j-bulkhead</artifactId>
</dependency>

// application.yml
resilience4j:
  circuitbreaker:
    instances:
      paymentBreaker:
        register-health-indicator: true
        sliding-window-size: 50
        failure-rate-threshold: 50
        slow-call-duration-threshold: 2s
        slow-call-rate-threshold: 50
        permitted-number-of-calls-in-half-open-state: 3
        automatic-transition-from-open-to-half-open-enabled: true
        wait-duration-in-open-state: 10s

  retry:
    instances:
      paymentRetry:
        register-health-indicator: false
        max-attempts: 3
        wait-duration: 1s
        retry-exceptions:
          - org.springframework.web.client.HttpServerErrorException
        ignore-exceptions:
          - org.springframework.web.client.HttpClientErrorException

  timelimiter:
    instances:
      paymentTimeout:
        timeout-duration: 5s
        cancel-running-future: true

  bulkhead:
    instances:
      paymentBulkhead:
        max-concurrent-calls: 10
        max-wait-duration: 1s
```

### Using Circuit Breaker Annotations

```java
@Service
public class PaymentService {
  private final PaymentClient paymentClient;
  private static final Logger log = LoggerFactory.getLogger(PaymentService.class);

  public PaymentService(PaymentClient paymentClient) {
    this.paymentClient = paymentClient;
  }

  @CircuitBreaker(name = "paymentBreaker", fallbackMethod = "processPaymentFallback")
  @Retry(name = "paymentRetry")
  @TimeLimiter(name = "paymentTimeout")
  @Bulkhead(name = "paymentBulkhead")
  public CompletableFuture<PaymentResponse> processPayment(PaymentRequest request) {
    return CompletableFuture.supplyAsync(() -> {
      log.info("process_payment orderId={}", request.orderId());
      PaymentResponse response = paymentClient.charge(request);
      log.info("payment_success orderId={} transactionId={}",
          request.orderId(), response.transactionId());
      return response;
    });
  }

  // Fallback method (must have same signature + additional exception parameter)
  public CompletableFuture<PaymentResponse> processPaymentFallback(
      PaymentRequest request, Exception ex) {
    log.warn("payment_fallback orderId={} reason={}", request.orderId(), ex.getMessage());
    // Return cached result, use default payment processor, or queue for retry
    return CompletableFuture.failedFuture(ex);
  }
}
```

## Service-to-Service Communication

### OpenFeign (Declarative HTTP Client)

```java
// pom.xml
<dependency>
  <groupId>org.springframework.cloud</groupId>
  <artifactId>spring-cloud-starter-openfeign</artifactId>
</dependency>

// application.yml
feign:
  client:
    config:
      payment-service:
        connect-timeout: 5000
        read-timeout: 10000
        logger-level: full
        error-decoder: com.example.CustomErrorDecoder

// Enable Feign
@SpringBootApplication
@EnableFeignClients
public class OrderServiceApplication {}

// Feign interface
@FeignClient(
  name = "payment-service",
  url = "${payment.service.url:http://payment-service}",
  fallback = PaymentClientFallback.class
)
public interface PaymentClient {
  @PostMapping("/api/payments")
  PaymentResponse charge(@RequestBody PaymentRequest request);

  @GetMapping("/api/payments/{id}")
  PaymentResponse getPayment(@PathVariable String id);
}

@Component
public class PaymentClientFallback implements PaymentClient {
  private static final Logger log = LoggerFactory.getLogger(PaymentClientFallback.class);

  @Override
  public PaymentResponse charge(PaymentRequest request) {
    log.warn("payment_service_unavailable orderId={}", request.orderId());
    throw new ServiceUnavailableException("Payment service temporarily unavailable");
  }

  @Override
  public PaymentResponse getPayment(String id) {
    throw new ServiceUnavailableException("Payment service temporarily unavailable");
  }
}
```

### RestClient (Spring 6.1+)

```java
@Service
public class PaymentService {
  private final RestClient restClient;
  private static final Logger log = LoggerFactory.getLogger(PaymentService.class);

  public PaymentService(RestClientBuilder builder) {
    this.restClient = builder
        .baseUrl("http://payment-service:8080")
        .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
        .build();
  }

  public PaymentResponse charge(PaymentRequest request) {
    try {
      log.info("charge_payment orderId={}", request.orderId());
      return restClient.post()
          .uri("/api/payments")
          .body(request)
          .retrieve()
          .onStatus(HttpStatusCode::isError, (req, res) -> {
            log.error("charge_failed orderId={} status={}", request.orderId(), res.getStatusCode());
            throw new PaymentException("Payment failed: " + res.getStatusCode());
          })
          .body(PaymentResponse.class);
    } catch (Exception ex) {
      log.error("charge_error orderId={}", request.orderId(), ex);
      throw ex;
    }
  }
}
```

### WebClient (Async/Reactive)

```java
@Service
public class ReactivPaymentService {
  private final WebClient webClient;
  private static final Logger log = LoggerFactory.getLogger(ReactivPaymentService.class);

  public ReactivPaymentService(WebClient.Builder builder) {
    this.webClient = builder
        .baseUrl("http://payment-service:8080")
        .clientConnector(new ReactorNettyClientHttpConnector(
            HttpClient.create()
                .responseTimeout(Duration.ofSeconds(10))
                .connectionTimeout(Duration.ofSeconds(5))
        ))
        .filter(ExchangeFilterFunction.ofResponseProcessor(clientResponse -> {
          if (clientResponse.getStatusCode().isError()) {
            log.warn("payment_request_failed status={}", clientResponse.getStatusCode());
          }
          return Mono.just(clientResponse);
        }))
        .build();
  }

  public Mono<PaymentResponse> chargeAsync(PaymentRequest request) {
    return webClient.post()
        .uri("/api/payments")
        .bodyValue(request)
        .retrieve()
        .bodyToMono(PaymentResponse.class)
        .timeout(Duration.ofSeconds(5))
        .doOnError(ex -> log.error("async_charge_failed orderId={}", request.orderId(), ex));
  }
}
```

## Distributed Tracing with Micrometer + Zipkin/Jaeger

Enable request tracing across microservices.

### Micrometer Tracing Configuration

```java
// pom.xml
<dependency>
  <groupId>io.micrometer</groupId>
  <artifactId>micrometer-tracing-bridge-otel</artifactId>
</dependency>
<dependency>
  <groupId>io.opentelemetry</groupId>
  <artifactId>opentelemetry-exporter-zipkin</artifactId>
</dependency>

// application.yml
management:
  tracing:
    sampling:
      probability: 1.0  # Sample 100% of requests for development; reduce in production
  zipkin:
    tracing:
      endpoint: http://zipkin:9411/api/v2/spans

logging:
  pattern:
    level: "%5p [%X{traceId},%X{spanId}]"  # Include trace IDs in logs
```

### Custom Instrumentation

```java
@Service
public class OrderService {
  private final Tracer tracer;
  private final OrderRepository orderRepository;
  private static final Logger log = LoggerFactory.getLogger(OrderService.class);

  public OrderService(Tracer tracer, OrderRepository orderRepository) {
    this.tracer = tracer;
    this.orderRepository = orderRepository;
  }

  public Order createOrder(CreateOrderRequest request) {
    // Current span is automatically captured by Spring
    log.info("create_order userId={}", request.userId());

    // Create child span for custom operation
    try (Tracer.SpanInScope scope = tracer.nextSpan()
        .name("validate_inventory")
        .tag("request.items", request.items().size())
        .start()
        .makeCurrent()) {

      validateInventory(request.items());
      log.info("inventory_valid");

    } catch (Exception ex) {
      log.error("inventory_validation_failed", ex);
      throw ex;
    }

    Order order = orderRepository.save(Order.from(request));
    log.info("order_created orderId={}", order.id());
    return order;
  }

  private void validateInventory(List<OrderItem> items) {
    // Validation logic
  }
}
```

## Spring Cloud Stream (Kafka/RabbitMQ)

Publish and consume events asynchronously.

### Producer Configuration

```java
// pom.xml
<dependency>
  <groupId>org.springframework.cloud</groupId>
  <artifactId>spring-cloud-stream-binder-kafka</artifactId>
</dependency>

// application.yml
spring:
  cloud:
    stream:
      kafka:
        binder:
          brokers: kafka:9092
          default-binder-configuration:
            min-partition-count: 3
            replication-factor: 2
      bindings:
        orderCreated-out-0:
          destination: orders-created
          content-type: application/json
          producer:
            partition-key-expression: payload.userId

// Event class
public record OrderCreatedEvent(
    Long orderId,
    String userId,
    BigDecimal total,
    Instant createdAt) {}

// Producer service
@Service
public class OrderEventPublisher {
  private final StreamBridge streamBridge;
  private static final Logger log = LoggerFactory.getLogger(OrderEventPublisher.class);

  public OrderEventPublisher(StreamBridge streamBridge) {
    this.streamBridge = streamBridge;
  }

  public void publishOrderCreated(OrderCreatedEvent event) {
    log.info("publish_order_created orderId={}", event.orderId());
    boolean sent = streamBridge.send("orderCreated-out-0", event);
    if (!sent) {
      log.error("publish_failed orderId={}", event.orderId());
      throw new EventPublishException("Failed to publish order created event");
    }
  }
}

// Controller integration
@RestController
@RequestMapping("/api/orders")
public class OrderController {
  private final OrderService orderService;
  private final OrderEventPublisher eventPublisher;

  public OrderController(OrderService orderService, OrderEventPublisher eventPublisher) {
    this.orderService = orderService;
    this.eventPublisher = eventPublisher;
  }

  @PostMapping
  public ResponseEntity<OrderResponse> create(@Valid @RequestBody CreateOrderRequest request) {
    Order order = orderService.create(request);

    // Publish event after order is persisted
    eventPublisher.publishOrderCreated(new OrderCreatedEvent(
        order.id(), order.userId(), order.total(), Instant.now()));

    return ResponseEntity.status(HttpStatus.CREATED).body(OrderResponse.from(order));
  }
}
```

### Consumer Configuration with Error Handling

```java
// application.yml
spring:
  cloud:
    stream:
      bindings:
        orderCreated-in-0:
          destination: orders-created
          group: notification-service
          consumer:
            max-attempts: 3
            back-off-initial-interval: 1000
            back-off-max-interval: 10000
            back-off-multiplier: 2.0

// Consumer function (functional style)
@Configuration
public class OrderEventConsumerConfig {
  private static final Logger log = LoggerFactory.getLogger(OrderEventConsumerConfig.class);

  @Bean
  public Consumer<OrderCreatedEvent> orderCreated(NotificationService notificationService) {
    return event -> {
      try {
        log.info("consume_order_created orderId={}", event.orderId());
        notificationService.notifyOrderCreated(event);
        log.info("notification_sent orderId={}", event.orderId());
      } catch (Exception ex) {
        log.error("process_failed orderId={}", event.orderId(), ex);
        throw ex;  // Trigger retry or DLQ
      }
    };
  }
}

// Dead Letter Queue handler
@Configuration
public class DlqConfig {
  private static final Logger log = LoggerFactory.getLogger(DlqConfig.class);

  @Bean
  public Consumer<ErrorMessage> dlq(OrderEventRepository eventRepository) {
    return errorMessage -> {
      log.error("dlq_message payload={} exception={}",
          errorMessage.getPayload(),
          errorMessage.getThrowable().getMessage());

      // Store failed event for manual inspection
      eventRepository.saveFailedEvent(
          errorMessage.getPayload().toString(),
          errorMessage.getThrowable().getMessage()
      );
    };
  }
}
```

## Anti-Patterns to Avoid

### Distributed Monolith

**Problem**: Services call each other synchronously in long chains, creating tight coupling and cascading failures.

```java
// WRONG: Synchronous chain
@RestController
public class OrderController {
  private final PaymentClient paymentClient;
  private final ShippingClient shippingClient;
  private final NotificationClient notificationClient;

  @PostMapping("/orders")
  public ResponseEntity<OrderResponse> create(CreateOrderRequest request) {
    Order order = saveOrder(request);

    PaymentResponse payment = paymentClient.charge(order);  // Blocks
    if (!payment.success()) {
      throw new PaymentException("Payment failed");
    }

    ShippingResponse shipping = shippingClient.ship(order);  // Blocks
    NotificationResponse notif = notificationClient.notify(order);  // Blocks

    return ResponseEntity.ok(OrderResponse.from(order));
  }
}

// CORRECT: Event-driven and async
@RestController
public class OrderController {
  private final OrderService orderService;

  @PostMapping("/orders")
  public ResponseEntity<OrderResponse> create(CreateOrderRequest request) {
    Order order = orderService.create(request);
    // Return immediately; payment, shipping, notification happen asynchronously
    return ResponseEntity.status(HttpStatus.CREATED).body(OrderResponse.from(order));
  }
}
```

### Chatty Services

**Problem**: Services make many small requests to each other, creating latency and network overhead.

```java
// WRONG: Multiple calls per request
@Service
public class OrderService {
  private final UserClient userClient;
  private final ProductClient productClient;

  public Order create(CreateOrderRequest request) {
    UserProfile user = userClient.getUser(request.userId());  // Call 1
    user = userClient.getPreferences(request.userId());  // Call 2
    user = userClient.getAddresses(request.userId());  // Call 3

    for (OrderItem item : request.items()) {
      ProductDetail product = productClient.getProduct(item.productId());  // Call N
    }
  }
}

// CORRECT: Batch operations or data enrichment at API Gateway
@Service
public class OrderService {
  private final UserClient userClient;
  private final ProductClient productClient;

  public Order create(CreateOrderRequest request) {
    // Single call with all user data
    UserDetail user = userClient.getUserFull(request.userId());

    // Batch product lookup
    List<ProductDetail> products = productClient.getProducts(
        request.items().stream().map(OrderItem::productId).toList());
  }
}
```

### Missing Timeouts

**Problem**: Services wait indefinitely for responses, leading to resource exhaustion.

```java
// WRONG: No timeout
RestTemplate restTemplate = new RestTemplate();
PaymentResponse response = restTemplate.getForObject(url, PaymentResponse.class);

// CORRECT: Timeouts on all external calls
@Configuration
public class RestTemplateConfig {
  @Bean
  public RestTemplate restTemplate(RestTemplateBuilder builder) {
    return builder
        .setConnectTimeout(Duration.ofSeconds(5))
        .setReadTimeout(Duration.ofSeconds(10))
        .interceptors((request, body, execution) -> {
          // Add timeout handling
          return execution.execute(request, body);
        })
        .build();
  }
}

// WebClient with timeout
webClient.post()
    .uri("/api/payments")
    .retrieve()
    .bodyToMono(PaymentResponse.class)
    .timeout(Duration.ofSeconds(5));  // Circuit breaker
```

## Agent Support

- **java-reviewer**: Code review for Spring Cloud implementations
- **architect**: Designing microservices architecture and resilience patterns
- **springframework-expert** (if available): Deep Spring Cloud expertise

## Skill References

- **springboot-patterns**: Foundation for Spring Boot services
- **springboot-security**: Authentication/authorization in microservices
- **microservices-patterns**: General microservices architecture
- **docker**: Containerizing microservices
- **deployment-patterns**: Kubernetes deployment of distributed systems
