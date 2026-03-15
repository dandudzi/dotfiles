---
name: springboot-security
description: Spring Security best practices for authn/authz, validation, CSRF, secrets, headers, rate limiting, and dependency security in Java Spring Boot services.
origin: ECC
---

# Spring Boot Security Review

**Baseline: Spring Boot 4.0.x · Spring Security 7.x · Java 21 LTS** (3.5.x / Security 6.3.x still supported as LTS branch)

Use when adding auth, handling input, creating endpoints, or dealing with secrets.

## When to Activate

- Adding authentication (JWT, OAuth2, session-based)
- Implementing authorization (@PreAuthorize, role-based access)
- Validating user input (Bean Validation, custom validators)
- Configuring CORS, CSRF, or security headers
- Managing secrets (Vault, environment variables)
- Adding rate limiting or brute-force protection
- Scanning dependencies for CVEs

## Authentication

- Prefer stateless JWT or opaque tokens with revocation list
- Use `httpOnly`, `Secure`, `SameSite=Strict` cookies for sessions
- Validate tokens with `OncePerRequestFilter` or resource server

```java
@Component
public class JwtAuthFilter extends OncePerRequestFilter {
  private final JwtService jwtService;

  public JwtAuthFilter(JwtService jwtService) {
    this.jwtService = jwtService;
  }

  @Override
  protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
      FilterChain chain) throws ServletException, IOException {
    String header = request.getHeader(HttpHeaders.AUTHORIZATION);
    if (header != null && header.startsWith("Bearer ")) {
      String token = header.substring(7);
      Authentication auth = jwtService.authenticate(token);
      SecurityContextHolder.getContext().setAuthentication(auth);
    }
    chain.doFilter(request, response);
  }
}
```

## Authorization

- Enable method security: `@EnableMethodSecurity`
- Use `@PreAuthorize("hasRole('ADMIN')")` or `@PreAuthorize("@authz.canEdit(#id)")`
- Deny by default; expose only required scopes

```java
@RestController
@RequestMapping("/api/admin")
public class AdminController {

  @PreAuthorize("hasRole('ADMIN')")
  @GetMapping("/users")
  public List<UserDto> listUsers() {
    return userService.findAll();
  }

  @PreAuthorize("@authz.isOwner(#id, authentication)")
  @DeleteMapping("/users/{id}")
  public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
    userService.delete(id);
    return ResponseEntity.noContent().build();
  }
}
```

## Input Validation

- Use Bean Validation with `@Valid` on controllers
- Apply constraints on DTOs: `@NotBlank`, `@Email`, `@Size`, custom validators
- Sanitize any HTML with a whitelist before rendering

```java
// BAD: No validation
@PostMapping("/users")
public User createUser(@RequestBody UserDto dto) {
  return userService.create(dto);
}

// GOOD: Validated DTO
public record CreateUserDto(
    @NotBlank @Size(max = 100) String name,
    @NotBlank @Email String email,
    @NotNull @Min(0) @Max(150) Integer age
) {}

@PostMapping("/users")
public ResponseEntity<UserDto> createUser(@Valid @RequestBody CreateUserDto dto) {
  return ResponseEntity.status(HttpStatus.CREATED)
      .body(userService.create(dto));
}
```

## SQL Injection Prevention

- Use Spring Data repositories or parameterized queries
- For native queries, use `:param` bindings; never concatenate strings

```java
// BAD: String concatenation in native query
@Query(value = "SELECT * FROM users WHERE name = '" + name + "'", nativeQuery = true)

// GOOD: Parameterized native query
@Query(value = "SELECT * FROM users WHERE name = :name", nativeQuery = true)
List<User> findByName(@Param("name") String name);

// GOOD: Spring Data derived query (auto-parameterized)
List<User> findByEmailAndActiveTrue(String email);
```

## Password Encoding

- Always hash passwords with BCrypt or Argon2 — never store plaintext
- Use `PasswordEncoder` bean, not manual hashing

```java
@Bean
public PasswordEncoder passwordEncoder() {
  return new BCryptPasswordEncoder(12); // cost factor 12
}

// In service
public User register(CreateUserDto dto) {
  String hashedPassword = passwordEncoder.encode(dto.password());
  return userRepository.save(new User(dto.email(), hashedPassword));
}
```

## CSRF Protection

- For browser session apps, keep CSRF enabled; include token in forms/headers
- For pure APIs with Bearer tokens, disable CSRF and rely on stateless auth

```java
http
  .csrf(csrf -> csrf.disable())
  .sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS));
```

## Secrets Management

- No secrets in source; load from env or vault
- Keep `application.yml` free of credentials; use placeholders
- Rotate tokens and DB credentials regularly

```yaml
# BAD: Hardcoded in application.yml
spring:
  datasource:
    password: mySecretPassword123

# GOOD: Environment variable placeholder
spring:
  datasource:
    password: ${DB_PASSWORD}

# GOOD: Spring Cloud Vault integration
spring:
  cloud:
    vault:
      uri: https://vault.example.com
      token: ${VAULT_TOKEN}
```

## Security Headers

```java
http
  .headers(headers -> headers
    .contentSecurityPolicy(csp -> csp
      .policyDirectives("default-src 'self'"))
    .frameOptions(HeadersConfigurer.FrameOptionsConfig::sameOrigin)
    .xssProtection(Customizer.withDefaults())
    .referrerPolicy(rp -> rp.policy(ReferrerPolicyHeaderWriter.ReferrerPolicy.NO_REFERRER)));
```

## CORS Configuration

- Configure CORS at the security filter level, not per-controller
- Restrict allowed origins — never use `*` in production

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

// In SecurityFilterChain:
http.cors(cors -> cors.configurationSource(corsConfigurationSource()));
```

## Rate Limiting

- Apply Bucket4j or gateway-level limits on expensive endpoints
- Log and alert on bursts; return 429 with retry hints

```java
// Using Bucket4j for per-endpoint rate limiting
@Component
public class RateLimitFilter extends OncePerRequestFilter {
  private final Map<String, Bucket> buckets = new ConcurrentHashMap<>();

  private Bucket createBucket() {
    return Bucket.builder()
        .addLimit(Bandwidth.classic(100, Refill.intervally(100, Duration.ofMinutes(1))))
        .build();
  }

  @Override
  protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
      FilterChain chain) throws ServletException, IOException {
    String clientIp = request.getRemoteAddr();
    Bucket bucket = buckets.computeIfAbsent(clientIp, k -> createBucket());

    if (bucket.tryConsume(1)) {
      chain.doFilter(request, response);
    } else {
      response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
      response.getWriter().write("{\"error\": \"Rate limit exceeded\"}");
    }
  }
}
```

## Dependency Security

- Run OWASP Dependency Check / Snyk in CI
- Keep Spring Boot and Spring Security on supported versions
- Fail builds on known CVEs

## Logging and PII

- Never log secrets, tokens, passwords, or full PAN data
- Redact sensitive fields; use structured JSON logging

## File Uploads

- Validate size, content type, and extension
- Store outside web root; scan if required

## Checklist Before Release

- [ ] Auth tokens validated and expired correctly
- [ ] Authorization guards on every sensitive path
- [ ] All inputs validated and sanitized
- [ ] No string-concatenated SQL
- [ ] CSRF posture correct for app type
- [ ] Secrets externalized; none committed
- [ ] Security headers configured
- [ ] Rate limiting on APIs
- [ ] Dependencies scanned and up to date
- [ ] Logs free of sensitive data

**Remember**: Deny by default, validate inputs, least privilege, and secure-by-configuration first.

## OAuth2/OIDC Resource Server

Spring Security's resource server validates JWT tokens from an OAuth2/OIDC provider without requiring session state.

**Dependencies:**
```xml
<dependency>
  <groupId>org.springframework.security</groupId>
  <artifactId>spring-security-oauth2-resource-server</artifactId>
</dependency>
<dependency>
  <groupId>org.springframework.security</groupId>
  <artifactId>spring-security-oauth2-jose</artifactId>
</dependency>
```

**Configuration:**
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

  @Bean
  public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    http
      .authorizeHttpRequests(authz -> authz
        .requestMatchers("/actuator/**").permitAll()
        .requestMatchers("/health").permitAll()
        .anyRequest().authenticated())
      .oauth2ResourceServer(oauth2 -> oauth2
        .jwt(jwt -> jwt.decoder(jwtDecoder())));
    return http.build();
  }

  @Bean
  public JwtDecoder jwtDecoder() {
    return NimbusJwtDecoder.withJwkSetUri("https://auth.example.com/.well-known/jwks.json")
        .build();
  }
}
```

**Validate Specific Claims in Endpoints:**
```java
@RestController
@RequestMapping("/api/markets")
public class MarketController {

  @GetMapping("/{id}")
  @PreAuthorize("hasAuthority('SCOPE_market:read')")
  public Market getMarket(@PathVariable Long id, @AuthenticationPrincipal Jwt jwt) {
    // Access JWT claims
    String subject = jwt.getSubject();
    String issuer = jwt.getIssuer().toString();
    List<String> scopes = jwt.getClaimAsStringList("scope");

    return marketService.findById(id);
  }

  @PostMapping
  @PreAuthorize("hasAuthority('SCOPE_market:write') && @authz.isAdmin(#jwt)")
  public ResponseEntity<Market> createMarket(
      @Valid @RequestBody CreateMarketRequest req,
      @AuthenticationPrincipal Jwt jwt) {
    String userId = jwt.getClaimAsString("sub");
    Market market = marketService.create(req, userId);
    return ResponseEntity.status(HttpStatus.CREATED).body(market);
  }
}
```

**Authorization Component for SpEL:**
```java
@Component("authz")
public class AuthorizationService {
  public boolean isAdmin(Jwt jwt) {
    List<String> roles = jwt.getClaimAsStringList("roles");
    return roles != null && roles.contains("admin");
  }

  public boolean isOwner(Long marketId, Jwt jwt) {
    String userId = jwt.getClaimAsString("sub");
    return marketService.isOwner(marketId, userId);
  }
}
```

**Opaque Token Introspection (for non-JWT tokens):**
```java
@Bean
public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
  http
    .oauth2ResourceServer(oauth2 -> oauth2
      .opaqueToken(opaque -> opaque
        .introspectionUri("https://auth.example.com/oauth/introspect")
        .introspectionClientCredentials("client-id", "client-secret")));
  return http.build();
}
```

**Multi-Tenant OIDC (Validate Multiple Issuers):**
```java
@Configuration
public class MultiTenantSecurityConfig {

  @Bean
  public JwtDecoder jwtDecoder() {
    List<String> trustedIssuers = List.of(
      "https://auth1.example.com",
      "https://auth2.example.com"
    );

    return new DelegatingJwtDecoder(
      trustedIssuers.stream()
        .map(NimbusJwtDecoder::withJwkSetUri)
        .map(builder -> (JwtDecoder) builder.build())
        .toList()
    );
  }
}
```

**PKCE Flow (OAuth2 Authorization Code):**
```java
@Configuration
@EnableWebSecurity
public class OAuthClientConfig {

  @Bean
  public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    http
      .oauth2Login(oauth2 -> oauth2
        .authorizationEndpoint(auth -> auth.baseUri("/oauth2/authorize"))
        .tokenEndpoint(token -> token.baseUri("/oauth2/token"))
        .userInfoEndpoint(userinfo -> userinfo.userService(customUserService())))
      .logout(logout -> logout.logoutSuccessUrl("/"));
    return http.build();
  }

  @Bean
  public OAuth2UserService<OidcUserRequest, OidcUser> customUserService() {
    return userRequest -> {
      OidcUser oidcUser = new OidcUserService().loadUser(userRequest);
      // Map OIDC claims to application roles
      return new DefaultOidcUser(
        oidcUser.getAuthorities(),
        oidcUser.getIdToken(),
        "sub"
      );
    };
  }
}
```

---

## JWT Trade-offs

JWT tokens are stateless but require careful design for revocation and expiration.

**Stateless vs Stateful Sessions:**

| Aspect | JWT (Stateless) | Session Cookies (Stateful) |
|--------|-----------------|---------------------------|
| Server Load | Low (no storage) | Higher (session store) |
| Scalability | ✓ Horizontal | ✓ Requires sticky sessions or store |
| Revocation | Slow (token alive until expiry) | Instant (delete session) |
| Client Storage | Safe if signed + sealed | Browser-managed (httpOnly) |
| Cross-Origin | ✓ CORS friendly | ⚠ CSRF-prone |
| Mobile/SPA | ✓ Ideal | Works but less common |
| Same-Origin Web | ⚠ Overkill | ✓ Better security |

**JWT Revocation Strategy 1: Short-Lived + Refresh Tokens**
```java
@Service
public class TokenService {
  public JwtResponse authenticate(String username, String password) {
    // Authenticate user
    User user = userService.findByUsername(username);

    // Issue short-lived access token (15 min)
    String accessToken = createJwt(user, Duration.ofMinutes(15));

    // Issue long-lived refresh token (7 days), store in secure cookie
    String refreshToken = createJwt(user, Duration.ofDays(7));
    refreshTokenRepository.save(new RefreshToken(user.getId(), refreshToken, Instant.now().plus(Duration.ofDays(7))));

    return new JwtResponse(accessToken, refreshToken);
  }

  public String refreshAccessToken(String refreshToken) {
    RefreshToken stored = refreshTokenRepository.findByToken(refreshToken)
      .orElseThrow(() -> new JwtException("Invalid refresh token"));

    if (stored.isExpired()) {
      throw new JwtException("Refresh token expired");
    }

    String newAccessToken = createJwt(stored.getUser(), Duration.ofMinutes(15));
    return newAccessToken;
  }
}
```

**JWT Revocation Strategy 2: Token Blocklist (for logout)**
```java
@Service
public class JwtRevocationService {
  private final StringRedisTemplate redis;

  public void revokeToken(String token) {
    Jwt decoded = jwtDecoder.decode(token);
    Instant expiresAt = decoded.getExpiresAt();
    Duration ttl = Duration.between(Instant.now(), expiresAt);

    if (ttl.isPositive()) {
      redis.opsForValue().set("revoked:" + token, "true", ttl);
    }
  }

  public boolean isRevoked(String token) {
    return redis.hasKey("revoked:" + token);
  }
}
```

**Token Rotation (Preventive):**
```java
// Rotate token on every refresh to prevent token reuse
@Component
public class JwtRotationFilter extends OncePerRequestFilter {
  @Override
  protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain) {
    String oldToken = extractToken(req);
    chain.doFilter(req, res);

    // On successful request, issue new token (refresh in background)
    if (res.getStatus() == 200) {
      String newToken = tokenService.rotateToken(oldToken);
      res.addHeader("X-New-Token", newToken);
    }
  }
}
```

**When to Use Session Cookies Instead of JWT:**
- ✓ Same-origin server-rendered apps (traditional web apps)
- ✓ Need instant token revocation (logout, permission changes)
- ✓ Low session storage burden (small user base)
- ✓ CSRF protection important (use double-submit cookie pattern with JWT)

```java
// Prefer sessions for same-origin web apps
@Configuration
public class SessionSecurityConfig {
  @Bean
  public SecurityFilterChain sessionChain(HttpSecurity http) throws Exception {
    http
      .sessionManagement(sm -> sm
        .sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED)
        .sessionFixationProtection(SessionFixationProtection.MIGRATE_SESSION)
        .maximumSessions(1))
      .csrf(csrf -> csrf.csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse()));
    return http.build();
  }
}
```

---

## Method-Level Security

Use `@EnableMethodSecurity` with annotations and SpEL for fine-grained authorization at the service layer.

**Enable Method Security:**
```java
@Configuration
@EnableMethodSecurity(
  prePostEnabled = true,  // @PreAuthorize, @PostAuthorize
  securedEnabled = true   // @Secured
)
public class MethodSecurityConfig {}
```

**Controller with Method Security:**
```java
@RestController
@RequestMapping("/api/markets")
public class MarketController {

  @GetMapping
  @PreAuthorize("hasAuthority('SCOPE_market:read')")
  public Page<Market> listMarkets(Pageable page) {
    return marketService.findAll(page);
  }

  @PostMapping
  @PreAuthorize("hasRole('MARKET_ADMIN') && @authz.canCreateMarket(authentication)")
  public ResponseEntity<Market> createMarket(@Valid @RequestBody CreateMarketRequest req) {
    return ResponseEntity.status(HttpStatus.CREATED)
        .body(marketService.create(req));
  }

  @PutMapping("/{id}")
  @PreAuthorize("@authz.isOwner(#id, authentication)")
  public ResponseEntity<Market> updateMarket(
      @PathVariable Long id,
      @Valid @RequestBody UpdateMarketRequest req) {
    return ResponseEntity.ok(marketService.update(id, req));
  }

  @DeleteMapping("/{id}")
  @PreAuthorize("hasRole('ADMIN')")
  public ResponseEntity<Void> deleteMarket(@PathVariable Long id) {
    marketService.delete(id);
    return ResponseEntity.noContent().build();
  }
}
```

**Authorization Service with SpEL:**
```java
@Component("authz")
public class AuthorizationService {

  public boolean canCreateMarket(Authentication auth) {
    return auth.isAuthenticated() &&
        auth.getAuthorities().stream()
          .anyMatch(a -> a.getAuthority().equals("ROLE_MARKET_ADMIN"));
  }

  public boolean isOwner(Long marketId, Authentication auth) {
    String userId = auth.getName();
    Market market = marketService.findById(marketId);
    return market.getOwnerId().equals(userId);
  }

  public boolean canEditMarket(Long marketId, Authentication auth) {
    return isOwner(marketId, auth) ||
        auth.getAuthorities().stream()
          .anyMatch(a -> a.getAuthority().equals("ROLE_ADMIN"));
  }
}
```

**Post-Authorization Filtering (@PostFilter):**
```java
@Service
public class MarketService {

  @PostFilter("filterObject.ownerId == authentication.name || hasRole('ADMIN')")
  public List<Market> getMyMarkets() {
    return marketRepository.findAll();
  }

  @PostFilter("hasPermission(filterObject, 'READ')")
  public List<Market> getAccessibleMarkets() {
    return marketRepository.findAll();
  }
}
```

**Custom Permission Evaluator:**
```java
@Component
public class CustomPermissionEvaluator implements PermissionEvaluator {

  @Override
  public boolean hasPermission(Authentication auth, Object targetDomainObject, Object permission) {
    if (!(targetDomainObject instanceof Market market)) {
      return false;
    }
    String requiredPerm = (String) permission;

    if ("READ".equals(requiredPerm)) {
      return isOwner(market, auth) || hasRole(auth, "ADMIN");
    }
    if ("WRITE".equals(requiredPerm)) {
      return isOwner(market, auth);
    }
    return false;
  }

  private boolean isOwner(Market market, Authentication auth) {
    return market.getOwnerId().equals(auth.getName());
  }

  private boolean hasRole(Authentication auth, String role) {
    return auth.getAuthorities().stream()
        .anyMatch(a -> a.getAuthority().equals("ROLE_" + role));
  }

  @Override
  public boolean hasPermission(Authentication auth, Serializable targetId, String targetType, Object permission) {
    // For ID-based permission checks; implement as needed
    return false;
  }
}

// Usage in SpEL:
// @PostAuthorize("hasPermission(returnObject, 'READ')")
```

**Testing Method Security with @WithMockUser:**
```java
@SpringBootTest
@AutoConfigureMockMvc
class MarketSecurityTest {
  @Autowired MockMvc mockMvc;

  @Test
  @WithMockUser(username = "user1", roles = "USER")
  void userCanListMarkets() throws Exception {
    mockMvc.perform(get("/api/markets"))
        .andExpect(status().isOk());
  }

  @Test
  @WithMockUser(username = "user1", roles = "USER")
  void userCannotDeleteMarket() throws Exception {
    mockMvc.perform(delete("/api/markets/1"))
        .andExpect(status().isForbidden());
  }

  @Test
  @WithMockUser(username = "admin", roles = "ADMIN")
  void adminCanDeleteMarket() throws Exception {
    mockMvc.perform(delete("/api/markets/1"))
        .andExpect(status().isNoContent());
  }

  @Test
  @WithMockUser(username = "owner", roles = "USER")
  void ownerCanUpdateOwnMarket() throws Exception {
    mockMvc.perform(put("/api/markets/123")
        .contentType(MediaType.APPLICATION_JSON)
        .content("""
          {"name":"Updated","description":"Desc"}
        """))
        .andExpect(status().isOk());
  }

  @Test
  void unauthenticatedUserDenied() throws Exception {
    mockMvc.perform(get("/api/markets/1"))
        .andExpect(status().isUnauthorized());
  }
}
```

**Custom @WithMockUser Principal:**
```java
@Retention(RetentionPolicy.RUNTIME)
@WithMockUser(roles = "USER")
public @interface WithMarketOwner {
  String userId() default "user123";
}

@Component
public class WithMarketOwnerSecurityContextFactory implements WithSecurityContextFactory<WithMarketOwner> {
  @Override
  public SecurityContext createSecurityContext(WithMarketOwner annotation) {
    SecurityContext context = SecurityContextHolder.createEmptyContext();
    UserDetails user = User.builder()
        .username(annotation.userId())
        .password("password")
        .roles("USER")
        .build();
    context.setAuthentication(new UsernamePasswordAuthenticationToken(user, null, user.getAuthorities()));
    return context;
  }
}
```

## Agent Support

- **java-reviewer**: Spring Security code patterns and best practices
- **code-reviewer**: General security code quality
- **owasp-top10-expert**: OWASP vulnerability assessment and remediation
- **oauth-oidc-expert**: OAuth2 and OIDC integration design
- **dependency-manager**: Security vulnerability scanning and CVE management

## Skill References

- **springboot-patterns**: REST API design and layered architecture
- **springboot-tdd**: Security-focused unit and integration testing
- **springboot-verification**: Build verification and security gates
- **common/security.md**: Code-level and architectural security guidelines
