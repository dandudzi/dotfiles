---
name: java-coding-standards
description: "Java coding standards for Spring Boot services: naming, immutability, Optional usage, streams, exceptions, generics, and project layout."
---

# Java Coding Standards

Standards for readable, maintainable Java (17+) code in Spring Boot services.

## When to Activate

- Writing or reviewing Java code in Spring Boot projects
- Enforcing naming, immutability, or exception handling conventions
- Working with records, sealed classes, or pattern matching (Java 17+)
- Reviewing use of Optional, streams, or generics
- Structuring packages and project layout

## Core Principles

- Prefer clarity over cleverness
- Immutable by default; minimize shared mutable state
- Fail fast with meaningful exceptions
- Consistent naming and package structure

## Naming

```java
// ✅ Classes/Records: PascalCase
public class MarketService {}
public record Money(BigDecimal amount, Currency currency) {}

// ✅ Methods/fields: camelCase
private final MarketRepository marketRepository;
public Market findBySlug(String slug) {}

// ✅ Constants: UPPER_SNAKE_CASE
private static final int MAX_PAGE_SIZE = 100;
```

## Immutability

```java
// ✅ Favor records and final fields
public record MarketDto(Long id, String name, MarketStatus status) {}

public class Market {
  private final Long id;
  private final String name;
  // getters only, no setters
}
```

## Optional Usage

```java
// ✅ Return Optional from find* methods
Optional<Market> market = marketRepository.findBySlug(slug);

// ✅ Map/flatMap instead of get()
return market
    .map(MarketResponse::from)
    .orElseThrow(() -> new EntityNotFoundException("Market not found"));
```

## Streams Best Practices

```java
// ✅ Use streams for transformations, keep pipelines short
List<String> names = markets.stream()
    .map(Market::name)
    .filter(Objects::nonNull)
    .toList();

// ❌ Avoid complex nested streams; prefer loops for clarity
```

## Exceptions

- Use unchecked exceptions for domain errors; wrap technical exceptions with context
- Create domain-specific exceptions (e.g., `MarketNotFoundException`)
- Avoid broad `catch (Exception ex)` unless rethrowing/logging centrally

```java
throw new MarketNotFoundException(slug);
```

## Generics and Type Safety

- Avoid raw types; declare generic parameters
- Prefer bounded generics for reusable utilities

```java
public <T extends Identifiable> Map<Long, T> indexById(Collection<T> items) { ... }
```

## Formatting and Style

- Use 2 or 4 spaces consistently (project standard)
- One public top-level type per file
- Keep methods short and focused; extract helpers
- Order members: constants, fields, constructors, public methods, protected, private

## Code Smells to Avoid

- Long parameter lists → use DTO/builders
- Deep nesting → early returns
- Magic numbers → named constants
- Static mutable state → prefer dependency injection
- Silent catch blocks → log and act or rethrow

## Logging

```java
private static final Logger log = LoggerFactory.getLogger(MarketService.class);
log.info("fetch_market slug={}", slug);
log.error("failed_fetch_market slug={}", slug, ex);
```

## Null Handling

- Accept `@Nullable` only when unavoidable; otherwise use `@NonNull`
- Use Bean Validation (`@NotNull`, `@NotBlank`) on inputs

## Testing Expectations

- JUnit 5 + AssertJ for fluent assertions
- Mockito for mocking; avoid partial mocks where possible
- Favor deterministic tests; no hidden sleeps

### Test Naming Convention

Use a unified naming pattern: `should_<expectedBehavior>_when_<condition>`

```java
// ✅ Consistent test naming
@Test
void should_returnMarket_when_slugExists() {}

@Test
void should_throwNotFoundException_when_slugIsUnknown() {}

@Test
void should_returnEmptyList_when_noMarketsMatch() {}

@Test
void should_persistMarket_when_inputIsValid() {}

// ❌ Avoid inconsistent or vague names
@Test
void testFindMarket() {}        // no intent or condition

@Test
void itWorks() {}               // meaningless

@Test
void findBySlug_success() {}    // no "should/when" structure
```

- `should_` describes the expected outcome
- `when_` describes the precondition or trigger
- Use camelCase within each segment
- Keep names concise but descriptive enough to understand without reading the test body

### Test Body Structure (Given/When/Then)

Structure every test body with `// given`, `// when`, `// then` comments:

```java
@Test
void should_returnMarket_when_slugExists() {
    // given
    var slug = "my-market";
    var market = new Market(1L, "My Market", slug);
    when(marketRepository.findBySlug(slug)).thenReturn(Optional.of(market));

    // when
    var result = marketService.findBySlug(slug);

    // then
    assertThat(result.id()).isEqualTo(1L);
    assertThat(result.name()).isEqualTo("My Market");
}

@Test
void should_throwNotFoundException_when_slugIsUnknown() {
    // given
    var slug = "unknown";
    when(marketRepository.findBySlug(slug)).thenReturn(Optional.empty());

    // when & then
    assertThatThrownBy(() -> marketService.findBySlug(slug))
        .isInstanceOf(MarketNotFoundException.class);
}
```

- **given** — set up test data and mock behavior
- **when** — execute the action under test
- **then** — assert the expected outcome
- Use `// when & then` when the action and assertion are combined (e.g., `assertThatThrownBy`)

**Remember**: Keep code intentional, typed, and observable. Optimize for maintainability over micro-optimizations unless proven necessary.
