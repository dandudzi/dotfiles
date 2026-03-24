---
name: springboot-security
description: Spring Security best practices for authn/authz, validation, CSRF, secrets, headers, rate limiting, and dependency security in Java Spring Boot services.
origin: ECC
model: sonnet
---

# Spring Boot Security Review

**Baseline: Spring Boot 4.0.x · Spring Security 7.x · Java 21 LTS**

Activate for authentication, authorization, input validation, CORS/CSRF, secrets management, rate limiting, or CVE scanning.

## Authentication & Authorization

**Auth:** Prefer stateless JWT or opaque tokens with revocation. For sessions, use `httpOnly`, `Secure`, `SameSite=Strict` cookies. Validate tokens with `OncePerRequestFilter`.

**Authz:** Enable `@EnableMethodSecurity` with `@PreAuthorize("hasRole('ADMIN')")` or custom SpEL. Deny by default.

```java
@Component
public class JwtAuthFilter extends OncePerRequestFilter {
  @Override
  protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain) throws ServletException, IOException {
    String header = req.getHeader("Authorization");
    if (header != null && header.startsWith("Bearer ")) {
      String token = header.substring(7);
      SecurityContextHolder.getContext().setAuthentication(jwtService.authenticate(token));
    }
    chain.doFilter(req, res);
  }
}

@RestController
@RequestMapping("/api/admin")
public class AdminController {
  @PreAuthorize("hasRole('ADMIN')")
  @GetMapping("/users")
  public List<User> listUsers() { return userService.findAll(); }

  @PreAuthorize("@authz.isOwner(#id, authentication)")
  @DeleteMapping("/users/{id}")
  public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
    userService.delete(id);
    return ResponseEntity.noContent().build();
  }
}
```

## Input Validation

Use Bean Validation (`@Valid`) with DTOs: `@NotBlank`, `@Email`, `@Size`. Sanitize HTML with whitelist.

```java
public record CreateUserDto(
    @NotBlank @Size(max = 100) String name,
    @NotBlank @Email String email,
    @NotNull @Min(0) @Max(150) Integer age
) {}

@PostMapping("/users")
public ResponseEntity<User> createUser(@Valid @RequestBody CreateUserDto dto) {
  return ResponseEntity.status(HttpStatus.CREATED).body(userService.create(dto));
}
```

## SQL Injection Prevention

Use Spring Data repos or parameterized queries; never concatenate strings.

```java
@Query(value = "SELECT * FROM users WHERE name = :name", nativeQuery = true)
List<User> findByName(@Param("name") String name);

List<User> findByEmailAndActiveTrue(String email);  // auto-parameterized
```

## Password Encoding

Hash passwords with BCrypt (cost 12) or Argon2; never store plaintext.

```java
@Bean
public PasswordEncoder passwordEncoder() { return new BCryptPasswordEncoder(12); }

public User register(CreateUserDto dto) {
  return userRepository.save(new User(dto.email(), passwordEncoder.encode(dto.password())));
}
```

## CSRF Protection

For session apps, enable CSRF with token in forms. For stateless APIs with Bearer tokens, disable.

```java
http.csrf(csrf -> csrf.disable())
  .sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS));
```

## Secrets Management

No secrets in source; load from env or vault. Use placeholders in `application.yml`.

```yaml
spring:
  datasource:
    password: ${DB_PASSWORD}  # Environment variable
  cloud:
    vault:
      uri: https://vault.example.com
      token: ${VAULT_TOKEN}
```

## Security Headers

```java
http.headers(headers -> headers
  .contentSecurityPolicy(csp -> csp.policyDirectives("default-src 'self'"))
  .frameOptions(HeadersConfigurer.FrameOptionsConfig::sameOrigin)
  .xssProtection(Customizer.withDefaults())
  .referrerPolicy(rp -> rp.policy(ReferrerPolicyHeaderWriter.ReferrerPolicy.NO_REFERRER)));
```

## CORS Configuration

Configure CORS at security filter level (not per-controller). Restrict origins; never use `*`.

```java
@Bean
public CorsConfigurationSource corsConfigurationSource() {
  CorsConfiguration config = new CorsConfiguration();
  config.setAllowedOrigins(List.of("https://app.example.com"));
  config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));
  config.setAllowedHeaders(List.of("Authorization", "Content-Type"));
  config.setAllowCredentials(true);
  config.setMaxAge(3600L);
  UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
  source.registerCorsConfiguration("/api/**", config);
  return source;
}
http.cors(cors -> cors.configurationSource(corsConfigurationSource()));
```

## Rate Limiting

Use Bucket4j or gateway-level limits. Return 429 on limit exceeded.

```java
@Component
public class RateLimitFilter extends OncePerRequestFilter {
  private final Map<String, Bucket> buckets = new ConcurrentHashMap<>();

  @Override
  protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain) throws ServletException, IOException {
    Bucket bucket = buckets.computeIfAbsent(req.getRemoteAddr(), k ->
      Bucket.builder().addLimit(Bandwidth.classic(100, Refill.intervally(100, Duration.ofMinutes(1)))).build());

    if (bucket.tryConsume(1)) {
      chain.doFilter(req, res);
    } else {
      res.setStatus(429);
      res.getWriter().write("{\"error\": \"Rate limit exceeded\"}");
    }
  }
}
```

## Dependency Security

Run OWASP Dependency Check in CI; fail builds on CVEs ≥7. Keep Spring Boot/Security updated.

## Logging & PII

Never log secrets, tokens, or passwords. Redact sensitive fields; use JSON logging.

## File Uploads

Validate size, content type, extension. Store outside web root.

## Pre-Release Checklist

- [ ] Auth tokens validated and expired
- [ ] Authorization guards on sensitive paths
- [ ] Inputs validated and sanitized
- [ ] No string-concatenated SQL
- [ ] CSRF correct for app type
- [ ] Secrets externalized
- [ ] Security headers configured
- [ ] Rate limiting on APIs
- [ ] Dependencies scanned, updated
- [ ] No sensitive data in logs

**Deny by default. Validate inputs. Least privilege. Secure-by-config first.**

## OAuth2/OIDC Resource Server

Validate JWT from OAuth2/OIDC provider; use JwtDecoder with `@AuthenticationPrincipal Jwt jwt` to access claims.

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
  @Bean
  public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    http.authorizeHttpRequests(authz -> authz
      .requestMatchers("/actuator/**", "/health").permitAll()
      .anyRequest().authenticated())
    .oauth2ResourceServer(oauth2 -> oauth2.jwt(jwt -> jwt.decoder(jwtDecoder())));
    return http.build();
  }

  @Bean
  public JwtDecoder jwtDecoder() {
    return NimbusJwtDecoder.withJwkSetUri("https://auth.example.com/.well-known/jwks.json").build();
  }
}

@RestController
@RequestMapping("/api/markets")
public class MarketController {
  @GetMapping("/{id}")
  @PreAuthorize("hasAuthority('SCOPE_market:read')")
  public Market getMarket(@PathVariable Long id, @AuthenticationPrincipal Jwt jwt) {
    String userId = jwt.getClaimAsString("sub");
    return marketService.findById(id);
  }

  @PostMapping
  @PreAuthorize("@authz.isAdmin(#jwt)")
  public ResponseEntity<Market> createMarket(@Valid @RequestBody CreateMarketRequest req, @AuthenticationPrincipal Jwt jwt) {
    return ResponseEntity.status(HttpStatus.CREATED).body(marketService.create(req, jwt.getClaimAsString("sub")));
  }
}

@Component("authz")
public class AuthorizationService {
  public boolean isAdmin(Jwt jwt) {
    List<String> roles = jwt.getClaimAsStringList("roles");
    return roles != null && roles.contains("admin");
  }
}
```

For multi-tenant OIDC, validate multiple issuers:
```java
@Bean
public JwtDecoder jwtDecoder() {
  return new DelegatingJwtDecoder(
    List.of("https://auth1.example.com", "https://auth2.example.com").stream()
      .map(NimbusJwtDecoder::withJwkSetUri)
      .map(builder -> (JwtDecoder) builder.build())
      .toList()
  );
}
```

## JWT vs Sessions

**JWT (stateless):** Low server load, horizontal scalability, CORS-friendly. Slow revocation (token alive until expiry).

**Sessions (stateful):** Instant revocation, simpler CSRF handling. Higher server load, requires sticky sessions.

Use JWT for mobile/SPA. Use sessions for same-origin server-rendered apps.

**Short-Lived Access + Refresh Tokens:**
```java
@Service
public class TokenService {
  public JwtResponse authenticate(String username, String password) {
    User user = userService.findByUsername(username);
    String accessToken = createJwt(user, Duration.ofMinutes(15));
    String refreshToken = createJwt(user, Duration.ofDays(7));
    refreshTokenRepository.save(new RefreshToken(user.getId(), refreshToken, Instant.now().plus(Duration.ofDays(7))));
    return new JwtResponse(accessToken, refreshToken);
  }

  public String refreshAccessToken(String refreshToken) {
    RefreshToken stored = refreshTokenRepository.findByToken(refreshToken)
      .orElseThrow(() -> new JwtException("Invalid"));
    if (stored.isExpired()) throw new JwtException("Expired");
    return createJwt(stored.getUser(), Duration.ofMinutes(15));
  }
}
```

**Revocation via Redis Blocklist:**
```java
@Service
public class JwtRevocationService {
  public void revokeToken(String token) {
    Jwt decoded = jwtDecoder.decode(token);
    Duration ttl = Duration.between(Instant.now(), decoded.getExpiresAt());
    if (ttl.isPositive()) redis.opsForValue().set("revoked:" + token, "true", ttl);
  }
  public boolean isRevoked(String token) { return redis.hasKey("revoked:" + token); }
}
```

## Advanced Authorization

Enable method security with `@PreAuthorize` and SpEL:
```java
@Configuration
@EnableMethodSecurity(prePostEnabled = true)
public class MethodSecurityConfig {}

@Service
public class MarketService {
  @PostFilter("filterObject.ownerId == authentication.name || hasRole('ADMIN')")
  public List<Market> getMyMarkets() { return marketRepository.findAll(); }
}
```

Custom `PermissionEvaluator` for object-level access control:
```java
@Component
public class CustomPermissionEvaluator implements PermissionEvaluator {
  public boolean hasPermission(Authentication auth, Object target, Object permission) {
    if (!(target instanceof Market market)) return false;
    String perm = (String) permission;
    if ("READ".equals(perm)) return isOwner(market, auth) || hasRole(auth, "ADMIN");
    if ("WRITE".equals(perm)) return isOwner(market, auth);
    return false;
  }
  public boolean hasPermission(Authentication auth, Serializable id, String type, Object perm) { return false; }
  private boolean isOwner(Market market, Authentication auth) { return market.getOwnerId().equals(auth.getName()); }
}
```

Test with `@WithMockUser`:
```java
@SpringBootTest
@AutoConfigureMockMvc
class MarketSecurityTest {
  @Autowired MockMvc mockMvc;
  @Test
  @WithMockUser(username = "user1", roles = "USER")
  void userCanListMarkets() throws Exception {
    mockMvc.perform(get("/api/markets")).andExpect(status().isOk());
  }
  @Test
  @WithMockUser(username = "admin", roles = "ADMIN")
  void adminCanDelete() throws Exception {
    mockMvc.perform(delete("/api/markets/1")).andExpect(status().isNoContent());
  }
}
```

## XXE Prevention, JNDI, Deserialization

**XXE:** Disable external entities in XML parsers.
```java
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
dbf.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
dbf.setFeature("http://xml.org/sax/features/external-general-entities", false);
```

**JNDI:** Validate allowlist JNDI names before lookup. Update Log4j ≥2.17.1.

**Deserialization:** Use Jackson with `@JsonTypeInfo` allowlist; never use `ObjectInputStream` on untrusted data.
```java
@JsonTypeInfo(use = JsonTypeInfo.Id.NAME)
@JsonSubTypes({
    @JsonSubTypes.Type(value = Cat.class, name = "cat"),
    @JsonSubTypes.Type(value = Dog.class, name = "dog")
})
public abstract class Animal {}
```

## Dependency Scanning & SBOM

Configure OWASP Dependency-Check (Maven/Gradle) to fail builds on CVE ≥7:
```bash
mvn dependency-check:check  # Maven
gradle dependencyCheckAnalyze  # Gradle
```

Generate CycloneDX SBOM:
```bash
mvn cyclonedx:makeAggregateBom  # Maven
gradle cyclonedxBom  # Gradle
```
