---
name: test-writer-java
description: "JUnit 5, Mockito, AssertJ, Spring Boot testing patterns"
model: sonnet
---

# Test Writer: Java Module

> [Test Writer Agent](../test-writer.md) > Java

Java-specific guidance for test generation.

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Run tests | Maven | `mvn test` |
| Run tests | Gradle | `./gradlew test` |
| Coverage | JaCoCo | `mvn jacoco:report` |
| Single test | Maven | `mvn test -Dtest=TestClass#testMethod` |

## Framework Detection

Detect testing framework from project files:

| Indicator | Framework |
| --------- | --------- |
| `junit-jupiter` dependency | JUnit 5 |
| `junit:junit:4.x` dependency | JUnit 4 |
| `org.testng` dependency | TestNG |
| No indicators | Default to JUnit 5 |

## JUnit 5 Patterns

### Basic Test Structure

```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;

class CalculatorTest {

    @Test
    @DisplayName("Add returns sum of two positive numbers")
    void add_withPositiveNumbers_returnsSum() {
        Calculator calc = new Calculator();

        int result = calc.add(2, 3);

        assertEquals(5, result);
    }

    @Test
    @DisplayName("Divide by zero throws ArithmeticException")
    void divide_byZero_throwsException() {
        Calculator calc = new Calculator();

        assertThrows(ArithmeticException.class, () -> calc.divide(10, 0));
    }
}
```

### Setup and Teardown

```java
import org.junit.jupiter.api.*;

class UserServiceTest {

    private UserService service;
    private UserRepository mockRepo;

    @BeforeAll
    static void setUpAll() {
        // Runs once before all tests
    }

    @BeforeEach
    void setUp() {
        mockRepo = mock(UserRepository.class);
        service = new UserService(mockRepo);
    }

    @AfterEach
    void tearDown() {
        // Clean up after each test
    }

    @AfterAll
    static void tearDownAll() {
        // Runs once after all tests
    }
}
```

### Parameterized Tests

```java
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.*;

class ValidationTest {

    @ParameterizedTest
    @ValueSource(strings = {"", " ", "   "})
    @DisplayName("Blank strings are invalid")
    void isValid_withBlankString_returnsFalse(String input) {
        assertFalse(Validator.isValid(input));
    }

    @ParameterizedTest
    @CsvSource({
        "1, 1, 2",
        "2, 3, 5",
        "-1, 1, 0",
        "0, 0, 0"
    })
    @DisplayName("Add returns correct sum for various inputs")
    void add_withVariousInputs_returnsCorrectSum(int a, int b, int expected) {
        assertEquals(expected, Calculator.add(a, b));
    }

    @ParameterizedTest
    @MethodSource("provideStringsForIsBlank")
    void isBlank_withVariousStrings_returnsExpected(String input, boolean expected) {
        assertEquals(expected, StringUtils.isBlank(input));
    }

    static Stream<Arguments> provideStringsForIsBlank() {
        return Stream.of(
            Arguments.of(null, true),
            Arguments.of("", true),
            Arguments.of("  ", true),
            Arguments.of("not blank", false)
        );
    }
}
```

### Nested Tests

```java
import org.junit.jupiter.api.Nested;

class UserServiceTest {

    @Nested
    @DisplayName("When user exists")
    class WhenUserExists {

        @Test
        @DisplayName("Returns user by ID")
        void getUser_returnsUser() {
            // test
        }

        @Test
        @DisplayName("Updates user successfully")
        void updateUser_succeeds() {
            // test
        }
    }

    @Nested
    @DisplayName("When user does not exist")
    class WhenUserDoesNotExist {

        @Test
        @DisplayName("Returns empty optional")
        void getUser_returnsEmpty() {
            // test
        }
    }
}
```

## Mockito Patterns

### Basic Mocking

```java
import static org.mockito.Mockito.*;
import static org.mockito.ArgumentMatchers.*;

class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    void getUser_existingId_returnsUser() {
        User expectedUser = new User(1L, "Test User");
        when(userRepository.findById(1L)).thenReturn(Optional.of(expectedUser));

        Optional<User> result = userService.getUser(1L);

        assertTrue(result.isPresent());
        assertEquals("Test User", result.get().getName());
        verify(userRepository).findById(1L);
    }

    @Test
    void saveUser_validUser_callsRepository() {
        User user = new User(null, "New User");

        userService.saveUser(user);

        verify(userRepository).save(argThat(u ->
            u.getName().equals("New User")
        ));
    }
}
```

### Argument Captors

```java
@Test
void createOrder_capturesOrderDetails() {
    ArgumentCaptor<Order> orderCaptor = ArgumentCaptor.forClass(Order.class);

    orderService.createOrder(customerId, items);

    verify(orderRepository).save(orderCaptor.capture());
    Order capturedOrder = orderCaptor.getValue();

    assertEquals(customerId, capturedOrder.getCustomerId());
    assertEquals(items.size(), capturedOrder.getItems().size());
}
```

### Mocking Static Methods

```java
import org.mockito.MockedStatic;

@Test
void testWithStaticMock() {
    try (MockedStatic<Instant> mockedStatic = mockStatic(Instant.class)) {
        Instant fixedInstant = Instant.parse("2024-01-01T00:00:00Z");
        mockedStatic.when(Instant::now).thenReturn(fixedInstant);

        // Test code that uses Instant.now()
    }
}
```

## AssertJ Assertions

```java
import static org.assertj.core.api.Assertions.*;

class AssertJExampleTest {

    @Test
    void assertJExamples() {
        // String assertions
        assertThat("Hello World")
            .startsWith("Hello")
            .endsWith("World")
            .contains("o W");

        // Collection assertions
        assertThat(users)
            .hasSize(3)
            .extracting(User::getName)
            .containsExactly("Alice", "Bob", "Charlie");

        // Exception assertions
        assertThatThrownBy(() -> service.process(null))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("cannot be null");

        // Object assertions
        assertThat(actualUser)
            .usingRecursiveComparison()
            .ignoringFields("id", "createdAt")
            .isEqualTo(expectedUser);
    }
}
```

## Spring Boot Testing

### Controller Tests

```java
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;

@WebMvcTest(UserController.class)
class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private UserService userService;

    @Test
    void getUser_existingId_returnsOk() throws Exception {
        when(userService.getUser(1L)).thenReturn(Optional.of(testUser));

        mockMvc.perform(get("/api/users/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("Test User"));
    }

    @Test
    void createUser_validPayload_returnsCreated() throws Exception {
        String payload = """
            {
                "name": "New User",
                "email": "new@example.com"
            }
            """;

        mockMvc.perform(post("/api/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(payload))
            .andExpect(status().isCreated());
    }
}
```

### Integration Tests

```java
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

@SpringBootTest
@ActiveProfiles("test")
@Transactional
class UserServiceIntegrationTest {

    @Autowired
    private UserService userService;

    @Autowired
    private UserRepository userRepository;

    @Test
    void createAndRetrieveUser() {
        User created = userService.createUser("Test User", "test@example.com");

        Optional<User> retrieved = userService.getUser(created.getId());

        assertThat(retrieved).isPresent();
        assertThat(retrieved.get().getEmail()).isEqualTo("test@example.com");
    }
}
```

## Coverage Commands

```bash
# Maven with JaCoCo
mvn clean test jacoco:report
# Report at: target/site/jacoco/index.html

# Gradle with JaCoCo
./gradlew test jacocoTestReport
# Report at: build/reports/jacoco/test/html/index.html

# Coverage threshold (Maven pom.xml)
<configuration>
    <rules>
        <rule>
            <element>BUNDLE</element>
            <limits>
                <limit>
                    <counter>LINE</counter>
                    <value>COVEREDRATIO</value>
                    <minimum>0.80</minimum>
                </limit>
            </limits>
        </rule>
    </rules>
</configuration>
```

## Coverage Report Parsing

Parse JaCoCo XML (`jacoco.xml`):

```xml
<report name="project">
  <package name="com/example">
    <class name="com/example/Calculator" sourcefilename="Calculator.java">
      <method name="add" desc="(II)I" line="10">
        <counter type="INSTRUCTION" missed="0" covered="5"/>
        <counter type="LINE" missed="0" covered="2"/>
      </method>
      <method name="divide" desc="(II)I" line="15">
        <counter type="INSTRUCTION" missed="3" covered="0"/>
        <counter type="LINE" missed="2" covered="0"/>
      </method>
    </class>
  </package>
</report>
```

## See Also

- [Java Style Guide](../../../../guides/languages/java.md)
- [Testing Guide](../../../../guides/process/testing.md)
