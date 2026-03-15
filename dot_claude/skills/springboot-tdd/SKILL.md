---
name: springboot-tdd
description: Test-driven development for Spring Boot using JUnit 5, Mockito, MockMvc, Testcontainers, and JaCoCo. Use when adding features, fixing bugs, or refactoring.
origin: ECC
---

# Spring Boot TDD Workflow

TDD guidance for Spring Boot services with 80%+ coverage (unit + integration).

## When to Use

- New features or endpoints
- Bug fixes or refactors
- Adding data access logic or security rules

## Workflow

1) Write tests first (they should fail)
2) Implement minimal code to pass
3) Refactor with tests green
4) Enforce coverage (JaCoCo)

## Unit Tests (JUnit 5 + Mockito)

```java
@ExtendWith(MockitoExtension.class)
class MarketServiceTest {
  @Mock MarketRepository repo;
  @InjectMocks MarketService service;

  @Test
  void createsMarket() {
    CreateMarketRequest req = new CreateMarketRequest("name", "desc", Instant.now(), List.of("cat"));
    when(repo.save(any())).thenAnswer(inv -> inv.getArgument(0));

    Market result = service.create(req);

    assertThat(result.name()).isEqualTo("name");
    verify(repo).save(any());
  }
}
```

Patterns:
- Arrange-Act-Assert
- Avoid partial mocks; prefer explicit stubbing
- Use `@ParameterizedTest` for variants

## Web Layer Tests (MockMvc)

```java
@WebMvcTest(MarketController.class)
class MarketControllerTest {
  @Autowired MockMvc mockMvc;
  @MockBean MarketService marketService;

  @Test
  void returnsMarkets() throws Exception {
    when(marketService.list(any())).thenReturn(Page.empty());

    mockMvc.perform(get("/api/markets"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.content").isArray());
  }
}
```

## Integration Tests (SpringBootTest)

```java
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class MarketIntegrationTest {
  @Autowired MockMvc mockMvc;

  @Test
  void createsMarket() throws Exception {
    mockMvc.perform(post("/api/markets")
        .contentType(MediaType.APPLICATION_JSON)
        .content("""
          {"name":"Test","description":"Desc","endDate":"2030-01-01T00:00:00Z","categories":["general"]}
        """))
      .andExpect(status().isCreated());
  }
}
```

## Persistence Tests (DataJpaTest)

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Import(TestContainersConfig.class)
class MarketRepositoryTest {
  @Autowired MarketRepository repo;

  @Test
  void savesAndFinds() {
    MarketEntity entity = new MarketEntity();
    entity.setName("Test");
    repo.save(entity);

    Optional<MarketEntity> found = repo.findByName("Test");
    assertThat(found).isPresent();
  }
}
```

## Testcontainers

- Use reusable containers for Postgres/Redis to mirror production
- **Spring Boot 3.1+:** Prefer `@ServiceConnection` over `@DynamicPropertySource` — auto-wires container URL into Spring context:

```java
@SpringBootTest
@Testcontainers
class MarketRepositoryTest {
  @Container
  @ServiceConnection  // Spring Boot 3.1+ — replaces @DynamicPropertySource
  static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16");

  @Autowired MarketRepository repo;

  @Test
  void savesAndFinds() {
    // Container URL auto-configured — no manual property injection needed
    repo.save(new MarketEntity("Test"));
    assertThat(repo.findByName("Test")).isPresent();
  }
}
```

- `@DynamicPropertySource` still works for custom containers without `@ServiceConnection` support

## Coverage (JaCoCo)

Maven snippet:
```xml
<plugin>
  <groupId>org.jacoco</groupId>
  <artifactId>jacoco-maven-plugin</artifactId>
  <version>0.8.14</version>
  <executions>
    <execution>
      <goals><goal>prepare-agent</goal></goals>
    </execution>
    <execution>
      <id>report</id>
      <phase>verify</phase>
      <goals><goal>report</goal></goals>
    </execution>
  </executions>
</plugin>
```

## Assertions

- Prefer AssertJ (`assertThat`) for readability
- For JSON responses, use `jsonPath`
- For exceptions: `assertThatThrownBy(...)`

## Test Data Builders

```java
class MarketBuilder {
  private String name = "Test";
  MarketBuilder withName(String name) { this.name = name; return this; }
  Market build() { return new Market(null, name, MarketStatus.ACTIVE); }
}
```

## CI Commands

- Maven: `mvn -T 4 test` or `mvn verify`
- Gradle: `./gradlew test jacocoTestReport`

**Remember**: Keep tests fast, isolated, and deterministic. Test behavior, not implementation details.

## Contract Testing with Spring Cloud Contract

Spring Cloud Contract enables provider-side contract definition and automatic consumer stub generation for microservices.

**Provider Contract (Groovy DSL):**
```groovy
// src/test/resources/contracts/marketplace/shouldReturnMarkets.groovy
Contract.make {
  request {
    method GET()
    url "/api/markets"
    headers { contentType applicationJson() }
  }
  response {
    status OK()
    headers { contentType applicationJson() }
    body([
      [id: 1, name: "Market 1"],
      [id: 2, name: "Market 2"]
    ])
  }
}
```

**Producer Verification Test:**
```java
@SpringBootTest
@AutoConfigureMessageVerifier
class MarketContractTest {
  @Autowired RestTemplate restTemplate;

  // Spring Cloud Contract auto-generates tests that verify contracts
  // Just ensure the endpoint exists and returns correct structure
  @Test
  void verifyMarketsFetch() {
    ResponseEntity<List> response = restTemplate.getForEntity("/api/markets", List.class);
    assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
    assertThat(response.getBody()).isNotEmpty();
  }
}
```

**Maven Configuration:**
```xml
<plugin>
  <groupId>org.springframework.cloud</groupId>
  <artifactId>spring-cloud-contract-maven-plugin</artifactId>
  <version>4.1.0</version>
  <executions>
    <execution>
      <goals><goal>generateTests</goal></goals>
    </execution>
  </executions>
</plugin>
```

**Consumer Stub Dependency:**
```xml
<dependency>
  <groupId>io.marketplace</groupId>
  <artifactId>marketplace-api-stubs</artifactId>
  <version>1.0.0</version>
  <classifier>stubs</classifier>
  <scope>test</scope>
</dependency>
```

**Consumer Test with Stubs:**
```java
@SpringBootTest
@AutoConfigureWireMock(port = 8888)
class MarketClientTest {
  @Test
  void fetchesMarketsFromStub() {
    // WireMock stub automatically loads generated contract stubs
    ResponseEntity<List> response = restTemplate.getForEntity("http://localhost:8888/api/markets", List.class);
    assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
  }
}
```

**CI Integration:** Publish stubs to artifact repository; consumers fetch with classifier `:stubs`.

---

## Testcontainers for Kafka

Use `@Testcontainers` with `KafkaContainer` for testing async message flows without mocking.

**Test Configuration:**
```java
@SpringBootTest
@Testcontainers
class MarketEventIntegrationTest {
  static KafkaContainer kafka = new KafkaContainer(DockerImageName.parse("confluentinc/cp-kafka:7.5.0"));

  @DynamicPropertySource
  static void kafkaProperties(DynamicPropertyRegistry registry) {
    registry.add("spring.kafka.bootstrap-servers", kafka::getBootstrapServers);
  }

  @Autowired KafkaTemplate<String, String> kafkaTemplate;
  @Autowired private TestChannelInterceptor interceptor;

  @Test
  void consumesMarketCreatedEvent() throws InterruptedException {
    // Produce event
    kafkaTemplate.send("market-events", """
      {"eventId":"123","marketId":"456","eventType":"MarketCreated","timestamp":"2025-01-01T00:00:00Z"}
    """);

    // Wait for consumer to process (with timeout)
    boolean messageReceived = interceptor.getLatch().await(5, TimeUnit.SECONDS);
    assertThat(messageReceived).isTrue();
    assertThat(interceptor.getLastMessage()).contains("MarketCreated");
  }

  @Component
  static class TestChannelInterceptor {
    private final CountDownLatch latch = new CountDownLatch(1);
    private String lastMessage;

    @KafkaListener(topics = "market-events", groupId = "test-group")
    public void listen(String message) {
      this.lastMessage = message;
      latch.countDown();
    }

    public CountDownLatch getLatch() { return latch; }
    public String getLastMessage() { return lastMessage; }
  }
}
```

**Async Message Verification without TestChannelInterceptor:**
```java
@Test
void publishesMarketCreatedEvent() {
  ArgumentCaptor<String> topicCaptor = ArgumentCaptor.forClass(String.class);
  ArgumentCaptor<String> messageCaptor = ArgumentCaptor.forClass(String.class);

  marketService.createMarket(new CreateMarketRequest("name", "desc", Instant.now(), List.of("cat")));

  verify(kafkaTemplate).send(topicCaptor.capture(), messageCaptor.capture());
  assertThat(topicCaptor.getValue()).isEqualTo("market-events");
  assertThat(messageCaptor.getValue()).contains("MarketCreated");
}
```

---

## Testcontainers for Redis

Use `RedisContainer` for testing cache operations and eviction policies in integration tests.

**Test Setup:**
```java
@SpringBootTest
@Testcontainers
class RedisCacheIntegrationTest {
  static GenericContainer<?> redis = new GenericContainer<>(DockerImageName.parse("redis:7.2"))
      .withExposedPorts(6379);

  @DynamicPropertySource
  static void redisProperties(DynamicPropertyRegistry registry) {
    registry.add("spring.redis.host", redis::getHost);
    registry.add("spring.redis.port", redis::getFirstMappedPort);
  }

  @Autowired private StringRedisTemplate stringRedisTemplate;
  @Autowired private MarketCacheService cacheService;

  @Test
  void cachesMissingMarket() {
    cacheService.cacheMarket("market-1", new Market(1L, "Test", MarketStatus.ACTIVE));

    String cached = stringRedisTemplate.opsForValue().get("market:market-1");
    assertThat(cached).isNotNull().contains("Test");
  }

  @Test
  void evictsCacheOnMarketUpdate() {
    cacheService.cacheMarket("market-1", new Market(1L, "Test", MarketStatus.ACTIVE));
    cacheService.invalidateMarket("market-1");

    String cached = stringRedisTemplate.opsForValue().get("market:market-1");
    assertThat(cached).isNull();
  }

  @Test
  void respectsTTLExpiration() throws InterruptedException {
    stringRedisTemplate.opsForValue().set("temp-key", "value", Duration.ofMillis(500));

    Thread.sleep(600);
    String expired = stringRedisTemplate.opsForValue().get("temp-key");
    assertThat(expired).isNull();
  }
}
```

**Cache Service Implementation:**
```java
@Service
public class MarketCacheService {
  private final StringRedisTemplate redisTemplate;
  private final ObjectMapper mapper;

  public void cacheMarket(String id, Market market) {
    try {
      String json = mapper.writeValueAsString(market);
      redisTemplate.opsForValue().set("market:" + id, json, Duration.ofHours(1));
    } catch (JsonProcessingException e) {
      log.error("Failed to cache market", e);
    }
  }

  public void invalidateMarket(String id) {
    redisTemplate.delete("market:" + id);
  }
}
```

---

## Mutation Testing with PIT

Mutation testing verifies test quality by injecting code mutations and ensuring tests catch them.

**Maven Configuration:**
```xml
<plugin>
  <groupId>org.pitest</groupId>
  <artifactId>pitest-maven</artifactId>
  <version>1.14.4</version>
  <configuration>
    <targetClasses>
      <param>io.marketplace.service.*</param>
      <param>io.marketplace.domain.*</param>
    </targetClasses>
    <targetTests>
      <param>io.marketplace.service.*Test</param>
    </targetTests>
    <mutators>
      <mutator>DEFAULTS</mutator>
      <mutator>STRONGER</mutator>
    </mutators>
    <mutationThreshold>60</mutationThreshold>
    <outputFormats>
      <format>HTML</format>
      <format>XML</format>
    </outputFormats>
  </configuration>
</plugin>
```

**Gradle Configuration:**
```gradle
plugins {
  id "info.solidsoft.pitest" version "1.7.2"
}

pitest {
  pitestVersion = "1.14.4"
  targetClasses = ["io.marketplace.service.*", "io.marketplace.domain.*"]
  targetTests = ["io.marketplace.service.*Test"]
  mutators = ["DEFAULTS", "STRONGER"]
  mutationThreshold = 60
  outputFormats = ["HTML", "XML"]
}
```

**Example: Test Catching Boundary Mutations:**
```java
@ExtendWith(MockitoExtension.class)
class PriceCalculatorTest {
  @InjectMocks PriceCalculator calculator;

  @Test
  void rejectsZeroPrice() {
    assertThatThrownBy(() -> calculator.validate(0))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessage("Price must be > 0");
  }

  @Test
  void rejectsNegativePrice() {
    assertThatThrownBy(() -> calculator.validate(-10))
        .isInstanceOf(IllegalArgumentException.class);
  }

  @Test
  void acceptsPositivePrice() {
    assertThatCode(() -> calculator.validate(99.99))
        .doesNotThrowAnyException();
  }

  @Test
  void appliesDiscountCorrectly() {
    double discounted = calculator.applyDiscount(100.0, 0.10);
    assertThat(discounted).isEqualTo(90.0);
  }

  @Test
  void appliesZeroDiscount() {
    double result = calculator.applyDiscount(100.0, 0.0);
    assertThat(result).isEqualTo(100.0);
  }
}
```

**Understanding Surviving Mutants:**
- **Boundary mutations:** `>` → `>=`, `==` → `!=` — ensure edge cases are tested
- **Constant mutations:** `0.10` → `0.11` — verify calculated values, not just types
- **Return mutations:** Replace return with hardcoded value — if test still passes, coverage is insufficient

**CI Integration:**
```bash
# Maven
mvn test pitest:mutationCoverage

# Gradle
./gradlew pitest

# Fail CI if mutation threshold not met:
# Check exit code and fail build
```

View HTML report: `target/pit-reports/index.html`

---

## Agent Support

- **tdd-guide**: Test-driven development workflow enforcement (RED → GREEN → REFACTOR)
- **java-reviewer**: Code review for Spring Boot tests
- **code-reviewer**: General test quality and patterns
- **vitest-expert** (for JavaScript Spring Boot FE): Frontend test patterns
- **playwright-expert**: E2E testing against Spring Boot services

## Skill References

- **springboot-patterns**: Service layer, repositories, and API design to test
- **springboot-security**: Authentication/authorization testing patterns
- **springboot-verification**: Coverage gates and test quality metrics
- **tdd-workflow**: TDD discipline rules, exemptions, and coverage requirements
