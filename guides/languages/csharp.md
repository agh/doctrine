# C# Style Guide

> [Doctrine](../../README.md) > [Languages](../README.md) > C#

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in
[RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Extends [Google C# Style Guide](google/csharp.md) and
[Microsoft C# Coding Conventions](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions).

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Lint | Roslynator[^1] | via NuGet |
| Format | dotnet format[^2] | `dotnet format` |
| Type check | built-in | `dotnet build` |
| Semantic | SonarAnalyzer[^3] | via NuGet |
| Dead code | built-in | IDE0051, IDE0052 |
| Coverage | coverlet[^4] | `dotnet test --collect:"XPlat Code Coverage"` |
| Complexity | - | via Roslynator[^1] |
| Fuzz | SharpFuzz[^5] | `sharpfuzz` |
| Test perf | dotnet test | `dotnet test -- RunConfiguration.MaxCpuCount=0` |

## C# 14 Features

Projects targeting .NET 10 **SHOULD** adopt C# 14 features where they
improve clarity and reduce boilerplate.

### Extension Members

C# 14 introduces extension blocks that allow defining properties, static
members, and operators on existing types:

**Do:**

```csharp
// Extension properties and methods in a single block
extension(IEnumerable<T> source) where T : struct
{
    public bool IsEmpty => !source.Any();
    public int SafeCount => source?.Count() ?? 0;

    public static IEnumerable<T> Empty => Enumerable.Empty<T>();
}

// Usage
var numbers = new[] { 1, 2, 3 };
if (!numbers.IsEmpty)
{
    Console.WriteLine($"Count: {numbers.SafeCount}");
}
```

**Don't:**

```csharp
// Don't use extension blocks for single simple methods
// - use traditional extension methods instead
extension(string s)
{
    public bool IsNullOrEmpty => string.IsNullOrEmpty(s);
}

// Better as traditional extension method
public static bool IsNullOrEmpty(this string s) => string.IsNullOrEmpty(s);
```

### Field Keyword

The `field` keyword provides direct access to auto-property backing fields:

**Do:**

```csharp
public class User
{
    // Validate on set while keeping auto-property syntax
    public string Email
    {
        get;
        set => field = value?.ToLowerInvariant()
            ?? throw new ArgumentNullException(nameof(value));
    }

    // Lazy initialization with backing field
    public DateTime CreatedAt
    {
        get => field ??= DateTime.UtcNow;
    }

    // Notify on change
    public string Name
    {
        get;
        set
        {
            if (field != value)
            {
                field = value;
                OnPropertyChanged();
            }
        }
    }
}
```

**Don't:**

```csharp
// Don't use field keyword for simple validation that can use init
public string Id
{
    get;
    set => field = value ?? throw new ArgumentNullException(nameof(value));
}

// Better: use init accessor
public required string Id { get; init; }
```

### Null-Conditional Assignment

The `?.=` operator assigns only if the left side is non-null:

**Do:**

```csharp
public class OrderProcessor
{
    public void UpdateOrder(Order? order, string status)
    {
        // Only assigns if order is not null
        order?.Status = status;
        order?.UpdatedAt = DateTime.UtcNow;

        // Equivalent to:
        // if (order is not null) { order.Status = status; }
    }

    public void ConfigureOptions(Options? options)
    {
        options?.Timeout = TimeSpan.FromSeconds(30);
        options?.RetryCount = 3;
    }
}
```

### Partial Constructors and Events

Partial classes can now split constructor and event definitions:

**Do:**

```csharp
// Generated code (e.g., source generator)
public partial class ViewModel
{
    public partial event PropertyChangedEventHandler? PropertyChanged;

    public partial ViewModel(ILogger logger);
}

// Hand-written implementation
public partial class ViewModel
{
    private readonly ILogger _logger;

    public partial ViewModel(ILogger logger)
    {
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    public partial event PropertyChangedEventHandler? PropertyChanged
    {
        add => _propertyChanged += value;
        remove => _propertyChanged -= value;
    }
    private PropertyChangedEventHandler? _propertyChanged;
}
```

### nameof with Unbound Generics

`nameof` now works with unbound generic types:

**Do:**

```csharp
// Get type name without specifying type argument
public void LogGenericUsage<T>()
{
    _logger.LogDebug("Using {TypeName}", nameof(List<>));      // "List"
    _logger.LogDebug("Using {TypeName}", nameof(Dictionary<,>)); // "Dictionary"
}

// Useful for attributes and reflection
[TypeConverter(typeof(GenericConverter<>))]
public class MyType { }
```

### Simple Lambda Parameters with Modifiers

Lambda parameters can now have modifiers without explicit types:

**Do:**

```csharp
// ref, out, in modifiers on lambda parameters
Span<int> numbers = stackalloc int[] { 1, 2, 3 };
numbers.Sort((ref x, ref y) => x.CompareTo(y));

// scoped modifier
ReadOnlySpan<char> Process(ReadOnlySpan<char> input) =>
    Transform(input, (scoped text) => text.Trim());

// params modifier
var sum = Aggregate((params values) => values.Sum());
```

## Linting: Roslynator + SonarAnalyzer

C# projects **MUST** use Roslynator[^1] and SonarAnalyzer[^3] for static analysis.

### Why Roslynator + SonarAnalyzer

- **Roslynator[^1]**: Provides 500+ analyzers and refactorings built on
  Roslyn, covering code quality, performance, and style issues
- **SonarAnalyzer[^3]**: Adds security vulnerability detection and code
  smell identification that complement Roslynator's coverage
- Both integrate seamlessly with the .NET build process and IDEs
- Native NuGet packages require no separate tooling or installation

### Installation

You **MUST** add to your project or Directory.Build.props:

```xml
<ItemGroup>
  <PackageReference Include="Roslynator.Analyzers" Version="4.12.0">
    <PrivateAssets>all</PrivateAssets>
    <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
  </PackageReference>
  <PackageReference Include="SonarAnalyzer.CSharp" Version="9.32.0">
    <PrivateAssets>all</PrivateAssets>
    <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
  </PackageReference>
</ItemGroup>
```

### Solution-Wide (Directory.Build.props)

Projects **SHOULD** configure analyzers solution-wide using `Directory.Build.props`:

```xml
<Project>
  <PropertyGroup>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
    <EnableNETAnalyzers>true</EnableNETAnalyzers>
    <AnalysisLevel>latest-all</AnalysisLevel>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Roslynator.Analyzers" Version="4.12.0" />
    <PackageReference Include="SonarAnalyzer.CSharp" Version="9.32.0" />
  </ItemGroup>
</Project>
```

## Formatting: dotnet format

C# projects **MUST** use `dotnet format`[^2] for code formatting.

### Why dotnet format

- Built into the .NET SDK (no separate installation required)
- Reads rules from `.editorconfig` for consistent configuration
- Supports both formatting and style rule enforcement
- Fast and reliable with official Microsoft support
- Integrates seamlessly with CI/CD pipelines

`dotnet format`[^2] reads rules from `.editorconfig`.

```bash
# Format entire solution
dotnet format

# Check only (for CI)
dotnet format --verify-no-changes

# Format specific project
dotnet format ./src/MyProject/MyProject.csproj
```

### EditorConfig (.editorconfig)

```ini
root = true

[*.cs]
# Indentation
indent_style = space
indent_size = 4

# New lines
end_of_line = lf
insert_final_newline = true

# Naming
dotnet_naming_rule.private_fields_should_be_camel_case.severity = warning
dotnet_naming_rule.private_fields_should_be_camel_case.symbols = private_fields
dotnet_naming_rule.private_fields_should_be_camel_case.style = camel_case_underscore

dotnet_naming_symbols.private_fields.applicable_kinds = field
dotnet_naming_symbols.private_fields.applicable_accessibilities = private

dotnet_naming_style.camel_case_underscore.required_prefix = _
dotnet_naming_style.camel_case_underscore.capitalization = camel_case

# Code style
csharp_style_var_for_built_in_types = false:warning
csharp_style_var_when_type_is_apparent = true:warning
csharp_style_expression_bodied_methods = when_on_single_line:suggestion
csharp_style_namespace_declarations = file_scoped:warning

# Analyzer severity
dotnet_diagnostic.CA1062.severity = warning
dotnet_diagnostic.CA2007.severity = warning
```

## Code Coverage: coverlet

C# projects **MUST** use coverlet[^4] for code coverage measurement.

### Why coverlet

- Cross-platform coverage tool built for .NET Core and .NET 5+
- Integrates natively with `dotnet test` command
- Supports multiple output formats (Cobertura, OpenCover, lcov)
- Works with all major CI systems and coverage reporting tools
- Built-in support for excluding generated code and test assemblies

```bash
# Run tests with coverage
dotnet test --collect:"XPlat Code Coverage"

# With threshold
dotnet test /p:CollectCoverage=true /p:Threshold=80

# Generate report
dotnet tool install -g dotnet-reportgenerator-globaltool
reportgenerator -reports:coverage.cobertura.xml -targetdir:coverage
```

ReportGenerator[^6] is used to generate human-readable coverage reports.

### Configuration

```xml
<!-- coverlet.runsettings -->
<?xml version="1.0" encoding="utf-8" ?>
<RunSettings>
  <DataCollectionRunSettings>
    <DataCollectors>
      <DataCollector friendlyName="XPlat Code Coverage">
        <Configuration>
          <Format>cobertura</Format>
          <Exclude>[*]*.Migrations.*</Exclude>
          <ExcludeByAttribute>GeneratedCodeAttribute</ExcludeByAttribute>
        </Configuration>
      </DataCollector>
    </DataCollectors>
  </DataCollectionRunSettings>
</RunSettings>
```

## Fuzzing: SharpFuzz

```bash
# Install
dotnet tool install --global SharpFuzz.CommandLine

# Instrument assembly
sharpfuzz path/to/MyLibrary.dll
```

```csharp
using SharpFuzz;[^5]

public class Program
{
    public static void Main(string[] args)
    {
        Fuzzer.Run(stream =>
        {
            try
            {
                MyParser.Parse(stream);
            }
            catch (FormatException) { }
        });
    }
}
```

## Test Performance

```bash
# Parallel execution (0 = use all cores)
dotnet test -- RunConfiguration.MaxCpuCount=0

# Parallel per assembly
dotnet test -- RunConfiguration.DisableParallelization=false

# Blame mode for hanging tests
dotnet test --blame-hang-timeout 60s
```

### xUnit Parallelization

```csharp
// Assembly level
[assembly: CollectionBehavior(DisableTestParallelization = false)]

// Or per collection
[CollectionDefinition("Sequential", DisableParallelization = true)]
public class SequentialCollection { }
```

xUnit[^7] is the recommended testing framework for .NET projects.

## CI Pipeline

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '10.0.x'

      - run: dotnet restore
      - run: dotnet build --no-restore /p:TreatWarningsAsErrors=true
      - run: dotnet format --verify-no-changes

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '10.0.x'

      - run: dotnet test --collect:"XPlat Code Coverage"
      - uses: codecov/codecov-action@v4
```

## Dependencies & Package Management

C# projects **MUST** use NuGet[^8] for package management and **SHOULD**
enable lock files in CI environments.

```bash
# Add package
dotnet add package Newtonsoft.Json

# Enable lock file
dotnet restore --use-lock-file

# Update and lock
dotnet restore --force-evaluate
```

### packages.lock.json

Projects **SHOULD** enable lock files and **MUST** use locked mode in CI:

```xml
<!-- MyProject.csproj -->
<PropertyGroup>
  <RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>
  <RestoreLockedMode Condition="'$(CI)' == 'true'">true</RestoreLockedMode>
</PropertyGroup>
```

### Version Constraints

```xml
<!-- exact -->
<PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
<!-- range -->
<PackageReference Include="Serilog" Version="[3.0.0,4.0.0)" />
<!-- floating -->
<PackageReference Include="Polly" Version="8.*" />
```

### Vulnerability Scanning

Projects **MUST** check for vulnerable packages regularly:

```bash
# Check for vulnerable packages
dotnet list package --vulnerable

# Include transitive
dotnet list package --vulnerable --include-transitive
```

### Dependabot Config

Projects **SHOULD** configure Dependabot[^9] for automated dependency updates:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "nuget"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

## E2E & Acceptance Testing

Web applications **SHOULD** use Playwright[^10] for end-to-end testing.
BDD projects **MAY** use SpecFlow[^11].

### Playwright for .NET

```csharp
using Microsoft.Playwright;[^10]

[Test]
public async Task UserCanLogin()
{
    await using var playwright = await Playwright.CreateAsync();
    await using var browser = await playwright.Chromium.LaunchAsync();
    var page = await browser.NewPageAsync();

    await page.GotoAsync("https://example.com/login");
    await page.FillAsync("#username", "user@test.com");
    await page.FillAsync("#password", "password");
    await page.ClickAsync("button[type=submit]");

    await Expect(page).ToHaveURLAsync("https://example.com/dashboard");
}
```

### SpecFlow for BDD

```gherkin
# Features/Login.feature
Feature: User Login
  Scenario: Successful login
    Given I am on the login page
    When I enter valid credentials
    Then I should see the dashboard
```

```csharp
[Binding]
public class LoginSteps(WebApplicationFactory<Program> factory)
{
    private HttpClient _client = factory.CreateClient();
    private HttpResponseMessage _response;

    [Given(@"I am on the login page")]
    public void GivenIAmOnLoginPage() { }

    [When(@"I enter valid credentials")]
    public async Task WhenIEnterValidCredentials()
    {
        _response = await _client.PostAsJsonAsync("/api/login",
            new { Username = "user", Password = "pass" });
    }

    [Then(@"I should see the dashboard")]
    public void ThenIShouldSeeDashboard()
    {
        _response.StatusCode.Should().Be(HttpStatusCode.OK);
    }
}
```

### WebApplicationFactory

ASP.NET Core applications **SHOULD** use `WebApplicationFactory`[^12] for
integration testing:

```csharp
public class ApiTests(WebApplicationFactory<Program> factory)
    : IClassFixture<WebApplicationFactory<Program>>
{
    [Fact]
    public async Task GetUsers_ReturnsOk()
    {
        var client = factory.CreateClient();
        var response = await client.GetAsync("/api/users");

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var users = await response.Content.ReadFromJsonAsync<List<User>>();
        users.Should().NotBeEmpty();
    }
}
```

This example uses FluentAssertions[^13] for readable assertions.

## Thread Safety Testing

Concurrent code **MUST** include thread safety tests:

```csharp
[Fact]
public async Task ConcurrentAccess_IsSafe()
{
    var counter = new ThreadSafeCounter();
    var tasks = Enumerable.Range(0, 1000)
        .Select(_ => Task.Run(() => counter.Increment()));

    await Task.WhenAll(tasks);

    counter.Value.Should().Be(1000);
}

// Implementation
public class ThreadSafeCounter
{
    private int _value;

    public void Increment() => Interlocked.Increment(ref _value);
    public int Value => Interlocked.CompareExchange(ref _value, 0, 0);
}
```

### Lock Testing

```csharp
[Fact]
public async Task Lock_PreventsConcurrentModification()
{
    var resource = new LockedResource();
    var results = new ConcurrentBag<int>();

    var tasks = Enumerable.Range(0, 100)
        .Select(i => Task.Run(() => results.Add(resource.IncrementAndGet())));

    await Task.WhenAll(tasks);

    results.Should().OnlyHaveUniqueItems();
    results.Should().HaveCount(100);
}
```

### Thread-Safe Collections

```csharp
[Fact]
public void ConcurrentDictionary_HandlesConcurrentWrites()
{
    var dict = new ConcurrentDictionary<int, string>();

    Parallel.For(0, 1000, i =>
    {
        dict.TryAdd(i, $"Value{i}");
    });

    dict.Count.Should().Be(1000);
}
```

## Idempotence Testing

Operations that can be called multiple times **SHOULD** be tested for idempotence:

```csharp
[Fact]
public async Task CreateUser_IsIdempotent()
{
    var request = new CreateUserRequest { Email = "test@example.com" };

    var result1 = await _service.CreateUserAsync(request);
    var result2 = await _service.CreateUserAsync(request);

    result1.Id.Should().Be(result2.Id);
    var users = await _repository.GetByEmailAsync(request.Email);
    users.Should().ContainSingle();
}
```

### Polly Retry Testing

```csharp
[Fact]
public async Task RetryPolicy_HandlesTransientFailures()
{
    var attempts = 0;
    var policy = Policy[^14]
        .Handle<HttpRequestException>()
        .WaitAndRetryAsync(3, _ => TimeSpan.FromMilliseconds(100));

    await policy.ExecuteAsync(async () =>
    {
        attempts++;
        if (attempts < 3) throw new HttpRequestException();
        return await Task.FromResult("success");
    });

    attempts.Should().Be(3);
}
```

## Reliability & Resilience Testing

Applications with external dependencies **SHOULD** implement and test
resilience patterns using Polly[^14].

### Polly Resilience Patterns

```csharp
[Fact]
public async Task CircuitBreaker_OpensAfterFailures()
{
    var breaker = Policy[^14]
        .Handle<Exception>()
        .CircuitBreakerAsync(2, TimeSpan.FromSeconds(30));

    await breaker.Invoking(p => p.ExecuteAsync(() => throw new Exception()))
        .Should().ThrowAsync<Exception>();
    await breaker.Invoking(p => p.ExecuteAsync(() => throw new Exception()))
        .Should().ThrowAsync<Exception>();

    await breaker.Invoking(p => p.ExecuteAsync(() => Task.CompletedTask))
        .Should().ThrowAsync<BrokenCircuitException>();
}
```

### Simmy Chaos Engineering

Simmy[^15] enables chaos engineering testing:

```csharp
[Fact]
public async Task Service_HandlesLatency()
{
    var latencyPolicy = MonkeyPolicy.InjectLatencyAsync(
        injectionRate: 0.5,
        latency: TimeSpan.FromSeconds(2));

    var stopwatch = Stopwatch.StartNew();
    await latencyPolicy.ExecuteAsync(async () =>
        await _service.GetDataAsync());
    stopwatch.Stop();

    // Should handle added latency gracefully
    stopwatch.ElapsedMilliseconds.Should().BeLessThan(5000);
}
```

### Timeout Testing

```csharp
[Fact]
public async Task Operation_RespectsTimeout()
{
    var timeout = Policy.TimeoutAsync(TimeSpan.FromMilliseconds(100));

    await timeout.Invoking(p => p.ExecuteAsync(async () =>
    {
        await Task.Delay(1000);
    })).Should().ThrowAsync<TimeoutRejectedException>();
}
```

## Compatibility Testing

Libraries **SHOULD** test against multiple .NET versions using multi-targeting.

### Multi-Targeting

```xml
<!-- MyLibrary.csproj -->
<PropertyGroup>
  <TargetFrameworks>net8.0;net9.0;net10.0</TargetFrameworks>
</PropertyGroup>

<ItemGroup Condition="'$(TargetFramework)' == 'net8.0'">
  <PackageReference Include="System.Text.Json" Version="8.0.0" />
</ItemGroup>
```

### CI Matrix

```yaml
jobs:
  test:
    strategy:
      matrix:
        dotnet: ['8.0.x', '9.0.x', '10.0.x']
        os: [ubuntu-latest, windows-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: ${{ matrix.dotnet }}
      - run: dotnet test
```

## Internationalization Testing

Applications with international users **MUST** test localization and UTF-8 handling:

```csharp
[Theory]
[InlineData("en-US", "Hello")]
[InlineData("es-ES", "Hola")]
[InlineData("ja-JP", "こんにちは")]
public void Greeting_LocalizesToCulture(string culture, string expected)
{
    var currentCulture = CultureInfo.CurrentCulture;
    try
    {
        CultureInfo.CurrentCulture = new CultureInfo(culture);
        var greeting = _localizer["Greeting"];
        greeting.Should().Be(expected);
    }
    finally
    {
        CultureInfo.CurrentCulture = currentCulture;
    }
}
```

### UTF-8 Handling

```csharp
[Fact]
public void Parser_HandlesUtf8()
{
    var input = "Hello 世界 🌍";
    var bytes = Encoding.UTF8.GetBytes(input);

    var result = Parser.Parse(bytes);

    result.Should().Be(input);
}
```

### Resource Files

```csharp
[Fact]
public void ResourceManager_LoadsCorrectCulture()
{
    var rm = new ResourceManager("MyApp.Resources", Assembly.GetExecutingAssembly());

    var english = rm.GetString("Welcome", new CultureInfo("en"));
    var french = rm.GetString("Welcome", new CultureInfo("fr"));

    english.Should().Be("Welcome");
    french.Should().Be("Bienvenue");
}
```

## Data Integrity Testing

Applications using databases **MUST** test migrations and transactions.

### EF Core Migration Testing

Entity Framework Core[^16] migrations should be tested:

```csharp
[Fact]
public async Task Migrations_ApplyCleanly()
{
    await using var context = CreateContext();
    await context.Database.MigrateAsync();

    var pendingMigrations = await context.Database.GetPendingMigrationsAsync();
    pendingMigrations.Should().BeEmpty();
}

[Fact]
public async Task Migration_PreservesExistingData()
{
    await using var context = CreateContext();
    context.Users.Add(new User { Name = "Test" });
    await context.SaveChangesAsync();

    await context.Database.MigrateAsync();

    var user = await context.Users.FirstAsync();
    user.Name.Should().Be("Test");
}
```

### Transaction Testing

```csharp
[Fact]
public async Task Transaction_RollsBackOnError()
{
    await using var context = CreateContext();
    await using var transaction = await context.Database.BeginTransactionAsync();

    try
    {
        context.Users.Add(new User { Name = "Test" });
        await context.SaveChangesAsync();
        throw new Exception("Simulated error");
    }
    catch
    {
        await transaction.RollbackAsync();
    }

    context.Users.Should().BeEmpty();
}
```

## A/B Testing & Feature Flags

Applications implementing feature flags **SHOULD** use Microsoft.FeatureManagement[^17].

### Microsoft.FeatureManagement

```csharp
// Configuration
services.AddFeatureManagement()[^17]
    .AddFeatureFilter<PercentageFilter>()
    .AddFeatureFilter<TimeWindowFilter>();
```

```json
{
  "FeatureManagement": {
    "NewCheckout": {
      "EnabledFor": [
        {
          "Name": "Percentage",
          "Parameters": { "Value": 50 }
        }
      ]
    }
  }
}
```

### Testing Feature Filters

```csharp
[Fact]
public async Task FeatureFilter_RespectsPercentage()
{
    var config = new ConfigurationBuilder()
        .AddInMemoryCollection(new Dictionary<string, string>
        {
            ["FeatureManagement:NewCheckout:EnabledFor:0:Name"] = "Percentage",
            ["FeatureManagement:NewCheckout:EnabledFor:0:Parameters:Value"] = "50"
        })
        .Build();

    var services = new ServiceCollection();
    services.AddSingleton<IConfiguration>(config);
    services.AddFeatureManagement();

    var provider = services.BuildServiceProvider();
    var featureManager = provider.GetRequiredService<IFeatureManager>();

    var enabled = await featureManager.IsEnabledAsync("NewCheckout");
    enabled.Should().BeOneOf(true, false); // Non-deterministic at 50%
}

[Fact]
public async Task Feature_IsDisabledByDefault()
{
    var featureManager = CreateFeatureManager(new Dictionary<string, bool>());

    var enabled = await featureManager.IsEnabledAsync("UnknownFeature");

    enabled.Should().BeFalse();
}
```

## References

[^1]: [Roslynator](https://github.com/dotnet/roslynator) - A collection of 500+ analyzers, refactorings and fixes for C#
[^2]: [dotnet format](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-format) - Code formatter for .NET
[^3]: [SonarAnalyzer.CSharp](https://github.com/SonarSource/sonar-dotnet) - Static code analyzer for C# code quality and security
[^4]: [coverlet](https://github.com/coverlet-coverage/coverlet) - Cross platform code coverage framework for .NET
[^5]: [SharpFuzz](https://github.com/Metalnem/sharpfuzz) - AFL-based fuzz testing for .NET
[^6]: [ReportGenerator](https://github.com/danielpalme/ReportGenerator) - Converts coverage reports into human readable formats
[^7]: [xUnit.net](https://xunit.net/) - Free, open source, community-focused unit testing tool for .NET
[^8]: [NuGet](https://www.nuget.org/) - Package manager for .NET
[^9]: [Dependabot](https://docs.github.com/en/code-security/dependabot) - Automated dependency updates for GitHub repositories
[^10]: [Playwright for .NET](https://playwright.dev/dotnet/) - Cross-browser end-to-end testing library
[^11]: [SpecFlow](https://specflow.org/) - BDD framework for .NET
[^12]: [WebApplicationFactory](https://learn.microsoft.com/en-us/aspnet/core/test/integration-tests) - ASP.NET Core integration testing
[^13]: [FluentAssertions](https://fluentassertions.com/) - Fluent API for asserting the results of unit tests
[^14]: [Polly](https://github.com/App-vNext/Polly) - .NET resilience and transient-fault-handling library
[^15]: [Simmy](https://github.com/Polly-Contrib/Simmy) - Chaos engineering library for .NET
[^16]: [Entity Framework Core](https://learn.microsoft.com/en-us/ef/core/) - Modern object-database mapper for .NET
[^17]: [Microsoft.FeatureManagement](https://github.com/microsoft/FeatureManagement-Dotnet) - Feature flag library for .NET

## See Also

- [Testing Guide](../testing.md) - General testing practices and patterns
- [CI Guide](../ci.md) - Continuous integration best practices
- [EditorConfig Guide](../editorconfig.md) - Editor configuration standards
