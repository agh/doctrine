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
using System;
using System.Collections.Generic;
using System.Linq;

// Extension blocks live in a top-level, non-generic static class
public static class EnumerableExtensions
{
    // The block declares its own type parameters and constraints
    extension<T>(IEnumerable<T> source) where T : struct
    {
        public bool IsEmpty => !source.Any();
        public int SafeCount => source?.Count() ?? 0;

        public static IEnumerable<T> Empty => Enumerable.Empty<T>();
    }
}

// Usage
public static class Report
{
    public static void Print()
    {
        var numbers = new[] { 1, 2, 3 };
        if (!numbers.IsEmpty)
        {
            Console.WriteLine($"Count: {numbers.SafeCount}");
        }
    }
}
```

**Don't:**

```csharp
// Don't use extension blocks for single simple methods
// - use traditional extension methods instead
public static class StringExtensions
{
    extension(string s)
    {
        public bool IsNullOrEmpty => string.IsNullOrEmpty(s);
    }
}

// Better as traditional extension method
public static class StringHelpers
{
    public static bool IsNullOrEmpty(this string s) => string.IsNullOrEmpty(s);
}
```

### Why a containing static class and an explicit type parameter

An extension block **MUST** be declared inside a top-level, non-generic
static class, and **MUST** declare its own type parameters. A bare
`extension(...)` block is a compile error: the compiler reports CS9283
outside such a class, and CS0080 plus CS0246 when the block uses `T`
without declaring `extension<T>`. The receiver parameter does not
introduce type parameters.

### Field Keyword

The `field` keyword provides direct access to auto-property backing fields.
The backing field has the property's own type, so `field ??= ...` compiles
only when that type is nullable, and a `field`-backed non-nullable property
**MUST** be `required` or carry an initializer or the compiler reports
CS9264.

**Do:**

```csharp
using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;

public class User : INotifyPropertyChanged
{
    // Validate on set while keeping auto-property syntax
    public required string Email
    {
        get;
        set => field = value?.ToLowerInvariant()
            ?? throw new ArgumentNullException(nameof(value));
    }

    // Notify on change
    public required string Name
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

    // DateTime has no null state, so seed the backing field from an
    // initializer; `field ??= DateTime.UtcNow` does not compile
    public DateTime CreatedAt { get; init; } = DateTime.UtcNow;

    // Lazy initialization needs a nullable property so `??=` has a null to test
    public string? Slug
    {
        get => field ??= Name.ToLowerInvariant().Replace(' ', '-');
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    private void OnPropertyChanged([CallerMemberName] string? name = null) =>
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
}
```

**Don't:**

```csharp
using System;

// Don't trade a mutable property for an immutable one without saying so:
// the null check below runs on every assignment, at run time
public class MutableOrder
{
    public required string Id
    {
        get;
        set => field = value ?? throw new ArgumentNullException(nameof(value));
    }
}

// Better when the value must not change after construction: the compiler
// enforces it at every call site instead
public class ImmutableOrder
{
    public required string Id { get; init; }
}

// A member already named `field` is shadowed inside an accessor (CS9258):
// write `this.field` or `@field` to reach it
public class Legacy
{
    private readonly string field = "backing";

    public string Value => this.field;
}
```

### Why `required` rather than an unchecked setter

`required string Id { get; init; }` and a mutable property with a
null-rejecting setter are not interchangeable. The first is checked by the
compiler at every object initializer and cannot change afterwards; the
second throws at run time and stays writable. Projects **MUST** choose
`init` only where the value is genuinely set once.

Projects that already declare a member named `field` **MUST** migrate it or
qualify every accessor reference. In language version 14.0 the compiler
reports CS9258 and binds `field` to a synthesized backing field, so
`this.field` or `@field` is required to reach the existing member.

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

Lambda parameters can carry modifiers without explicit types, provided the
target delegate declares the same modifiers. A `params` parameter is the
exception: it **MUST** be explicitly typed.

**Do:**

```csharp
using System;
using System.Linq;

public delegate int RefComparer(ref int x, ref int y);

public delegate int SpanLength(scoped ReadOnlySpan<char> text);

public delegate int Aggregator(params int[] values);

public static class LambdaSamples
{
    public static void Run()
    {
        // ref, out and in modifiers need a delegate that declares them
        RefComparer compare = (ref x, ref y) => x.CompareTo(y);
        int left = 3, right = 7;
        Console.WriteLine(compare(ref left, ref right));

        // Span<T>.Sort takes Comparison<T>, whose parameters are by value
        Span<int> numbers = stackalloc int[] { 3, 1, 2 };
        numbers.Sort((x, y) => x.CompareTo(y));

        // scoped modifier
        SpanLength trimmedLength = (scoped text) => text.Trim().Length;
        Console.WriteLine(trimmedLength("  hello  "));

        // params modifier: the parameter type must be written out
        Aggregator sum = (params int[] values) => values.Sum();
        Console.WriteLine(sum(1, 2, 3));
    }
}
```

### Why the delegate signature decides the modifiers

A lambda parameter modifier is checked against the target delegate.
`Span<T>.Sort` takes `Comparison<T>`, which passes both operands by value,
so `(ref x, ref y) => ...` is rejected with CS1677. An implicitly typed
`params` lambda parameter is rejected outright with CS9272.

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
  <PackageReference Include="Roslynator.Analyzers" Version="5.0.0">
    <PrivateAssets>all</PrivateAssets>
    <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
  </PackageReference>
  <PackageReference Include="SonarAnalyzer.CSharp" Version="10.33.0.1635">
    <PrivateAssets>all</PrivateAssets>
    <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
  </PackageReference>
</ItemGroup>
```

Both versions **MUST** be written exactly as published. SonarAnalyzer.CSharp
uses four-part versions, so `Version="10.33.0"` resolves to the nearest
higher build with NU1603, which `TreatWarningsAsErrors` turns into a fatal
restore error.

### Migrating to Roslynator 5.0.0

Roslynator 5.0.0 (released 2026-08-21) is a breaking release. Projects
upgrading from 4.x **MUST**:

- Rename the legacy `.editorconfig` keys `roslynator.max_line_length` and
  `roslynator.prefix_field_identifier_with_underscore` to
  `roslynator_max_line_length` and
  `roslynator_prefix_field_identifier_with_underscore`, and replace
  `roslynator_suppress_unity_script_methods` with
  `roslynator_unity_code_analysis.enabled`
- Replace the analyzers removed in 5.0.0 with their successors, for example
  RCS0014 with RCS0061, RCS1035 with RCS1260, and RCS1237 with RCS1254
- Reference `Microsoft.CodeAnalysis.CSharp.Workspaces` explicitly in test
  projects that used the Roslynator testing packages, which now floor their
  Roslyn dependency at 3.8.0 instead of forcing 4.14.0
- Install the Roslynator 2026 extension for Visual Studio 2026, or stay on
  the last 4.x VSIX; the 5.0.0 extensions no longer bundle analyzers

Projects **MUST** baseline the diagnostics both upgrades introduce before
turning warnings into errors, otherwise the first build after the upgrade
fails on pre-existing code.

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
    <PackageReference Include="Roslynator.Analyzers" Version="5.0.0">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
    </PackageReference>
    <PackageReference Include="SonarAnalyzer.CSharp" Version="10.33.0.1635">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
    </PackageReference>
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
# Run tests with coverage into a known directory
dotnet test --settings coverlet.runsettings \
  --collect:"XPlat Code Coverage" \
  --results-directory ./TestResults

# With threshold
dotnet test /p:CollectCoverage=true /p:Threshold=80

# Generate report from the per-run GUID directories VSTest creates
dotnet new tool-manifest
dotnet tool install dotnet-reportgenerator-globaltool --version 5.5.11
dotnet tool run reportgenerator \
  -reports:"TestResults/**/coverage.cobertura.xml" \
  -targetdir:coverage
```

ReportGenerator[^6] is used to generate human-readable coverage reports.

### Why the glob and the local tool

The VSTest collector writes `coverage.cobertura.xml` into a freshly named
GUID directory under `TestResults`, never at the repository root, so
`-reports:coverage.cobertura.xml` fails with "No report files specified".
A recursive glob matches whichever directory the run produced. Pinning
ReportGenerator in a tool manifest **MUST** be preferred over
`dotnet tool install -g`, which gives CI an unpinned floating version.

### Configuration

The settings below belong in `coverlet.runsettings`. The XML declaration
**MUST** be the first node in the file, so the filename cannot be written as
a leading comment; `dotnet test` otherwise rejects the file with
"Unexpected XML declaration".

```xml
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

The fuzzing harness below uses SharpFuzz[^5]:

```csharp
using SharpFuzz;

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

Install the runner-specific integration package rather than the bare
library, so the base class supplies `Page` and `Expect`, and install the
browsers before the first run:

```bash
dotnet add package Microsoft.Playwright.Xunit.v3 --version 1.62.0
dotnet build
pwsh bin/Debug/net10.0/playwright.ps1 install
```

Tests then derive from `PageTest`, which opens a page per test and disposes
it. The example uses Playwright for .NET[^10]:

```csharp
using Microsoft.Playwright;
using Microsoft.Playwright.Xunit.v3;
using Xunit;

public class LoginTests : PageTest
{
    [Fact]
    public async Task UserCanLogin()
    {
        await Page.GotoAsync("https://example.com/login");
        await Page.FillAsync("#username", "user@test.com");
        await Page.FillAsync("#password", "password");
        await Page.ClickAsync("button[type=submit]");

        await Expect(Page).ToHaveURLAsync("https://example.com/dashboard");
    }
}
```

### Why the integration package

`IPlaywright` does not implement `IAsyncDisposable`, so
`await using var playwright = await Playwright.CreateAsync()` fails with
CS8417, and `Expect` is a member of the runner base class rather than a
free function, so calling it without that base class fails with CS0103.
Projects using xUnit **MUST** reference `Microsoft.Playwright.Xunit.v3` for
xUnit v3 or `Microsoft.Playwright.Xunit` for xUnit v2; NUnit attributes such
as `[Test]` **MUST NOT** be mixed into an xUnit suite.

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

The retry test below builds its policy with Polly[^14]:

```csharp
[Fact]
public async Task RetryPolicy_HandlesTransientFailures()
{
    var attempts = 0;
    var policy = Policy
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
    var breaker = Policy
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

### Chaos Engineering

Polly 8.7.0 ships chaos strategies in the box, so Simmy[^15] as a separate
package is no longer required. Injection **MUST** be made deterministic in
tests by setting `InjectionRate` to 1.0 rather than a probability:

```csharp
using System.Diagnostics;
using Polly;
using Polly.Simmy;
using Polly.Simmy.Latency;

public class ChaosTests
{
    [Fact]
    public async Task Service_HandlesLatency()
    {
        var pipeline = new ResiliencePipelineBuilder()
            .AddChaosLatency(new ChaosLatencyStrategyOptions
            {
                InjectionRate = 1.0,
                Latency = TimeSpan.FromMilliseconds(500)
            })
            .Build();

        var stopwatch = Stopwatch.StartNew();
        await pipeline.ExecuteAsync(
            async ct => await _service.GetDataAsync(ct),
            CancellationToken.None);
        stopwatch.Stop();

        stopwatch.Elapsed.Should()
            .BeGreaterThanOrEqualTo(TimeSpan.FromMilliseconds(500));
        stopwatch.Elapsed.Should().BeLessThan(TimeSpan.FromSeconds(5));
    }
}
```

### Why not `MonkeyPolicy`

`Polly.Contrib.Simmy` stopped at 0.3.0 and its `MonkeyPolicy` has no
two-argument `InjectLatencyAsync(injectionRate, latency)` overload, so the
legacy call fails with CS1501. A probabilistic `injectionRate: 0.5` also
makes the assertion pass roughly half the time for the wrong reason.

### Timeout Testing

The executed delegate **MUST** accept and forward the cancellation token
Polly supplies, otherwise an optimistic timeout has nothing to cancel:

```csharp
[Fact]
public async Task Operation_RespectsTimeout()
{
    var timeout = Policy.TimeoutAsync(TimeSpan.FromMilliseconds(100));

    await timeout.Invoking(p => p.ExecuteAsync(
            async ct => await Task.Delay(TimeSpan.FromSeconds(1), ct),
            CancellationToken.None))
        .Should().ThrowAsync<TimeoutRejectedException>();
}
```

### Why the token must be forwarded

`Policy.TimeoutAsync(TimeSpan)` uses the optimistic strategy, which cancels
the token it passes to the delegate and reports `TimeoutRejectedException`
only if the delegate observes it. A delegate that calls `Task.Delay(1000)`
without a token runs to completion, the policy throws nothing, and the test
above passes only because the assertion is never reached.

## Compatibility Testing

Libraries **SHOULD** test against multiple .NET versions using multi-targeting.

### Multi-Targeting

```xml
<!-- MyLibrary.csproj -->
<PropertyGroup>
  <TargetFrameworks>net8.0;net9.0;net10.0</TargetFrameworks>
</PropertyGroup>
```

### Why no conditional System.Text.Json reference

`System.Text.Json` ships in the shared framework for every `net8.0` and
later target, so referencing the package explicitly is redundant: NuGet
reports NU1510 and asks for the reference to be removed. Pinning it to
8.0.0 also drags in two high-severity denial-of-service advisories,
GHSA-hh2w-p6rv-4g7w and GHSA-8g4q-xg66-9fp4, which restore reports as
NU1903 and `TreatWarningsAsErrors` turns into build failures. A target that
genuinely needs the package, such as `netstandard2.0`, **MUST** pin a
serviced version — 8.0.6 is the last 8.x, and 10.0.11 is the current stable
release — and CI **MUST** fail on NU1903.

### CI Matrix

Each matrix leg **MUST** check out the repository and build a single target
framework, and the job **MUST** install every runtime the matrix exercises
alongside an SDK new enough to evaluate `net10.0`:

```yaml
jobs:
  test:
    strategy:
      matrix:
        framework: ['net8.0', 'net9.0', 'net10.0']
        os: [ubuntu-latest, windows-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: |
            8.0.x
            9.0.x
            10.0.x
      - run: dotnet test --framework ${{ matrix.framework }}
```

### Why not a matrix of SDK versions

Building `net10.0` with the .NET 8 or 9 SDK fails with NETSDK1045, so a
matrix over `dotnet-version` either fails or silently falls back to a
preinstalled newer SDK and tests nothing it claims to. Matrixing over the
target framework instead keeps one current SDK and asserts that each
target framework really builds and runs.

## Internationalization Testing

Applications with international users **MUST** test localization and UTF-8
handling. Resource lookup reads `CultureInfo.CurrentUICulture`, not
`CultureInfo.CurrentCulture`, so a localization test **MUST** set and
restore both, and **MUST** run without parallelism because culture is
ambient state:

```csharp
[Collection("Sequential")]
public class GreetingTests
{
    [Theory]
    [InlineData("en-US", "Hello")]
    [InlineData("es-ES", "Hola")]
    [InlineData("ja-JP", "こんにちは")]
    public void Greeting_LocalizesToCulture(string culture, string expected)
    {
        var originalCulture = CultureInfo.CurrentCulture;
        var originalUICulture = CultureInfo.CurrentUICulture;
        try
        {
            var target = new CultureInfo(culture);
            CultureInfo.CurrentUICulture = target;  // resource lookup
            CultureInfo.CurrentCulture = target;    // formatting and parsing

            var greeting = _localizer["Greeting"];

            greeting.Value.Should().Be(expected);
        }
        finally
        {
            CultureInfo.CurrentCulture = originalCulture;
            CultureInfo.CurrentUICulture = originalUICulture;
        }
    }
}
```

### Why both cultures

`IStringLocalizer` resolves satellite assemblies through
`CultureInfo.CurrentUICulture`. Setting only `CurrentCulture` leaves the
lookup on the neutral resources, so a correctly localized application still
returns the fallback string and the test fails. `CurrentCulture` is still
needed when the assertion covers number, date or currency formatting.
Compare `LocalizedString.Value` rather than the `LocalizedString` itself,
which does not compare equal to a `string`.

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

Register the filters with Microsoft.FeatureManagement[^17]:

```csharp
// Configuration
services.AddFeatureManagement()
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

Tests **MUST** pin the filter inputs so the outcome is decided, not
sampled:

```csharp
[Fact]
public async Task FeatureFilter_AtZeroPercent_IsDisabled()
{
    var featureManager = CreatePercentageFeatureManager(0);

    var enabled = await featureManager.IsEnabledAsync("NewCheckout");

    enabled.Should().BeFalse();
}

[Fact]
public async Task FeatureFilter_AtHundredPercent_IsEnabled()
{
    var featureManager = CreatePercentageFeatureManager(100);

    var enabled = await featureManager.IsEnabledAsync("NewCheckout");

    enabled.Should().BeTrue();
}

private static IFeatureManager CreatePercentageFeatureManager(int percentage)
{
    var config = new ConfigurationBuilder()
        .AddInMemoryCollection(new Dictionary<string, string?>
        {
            ["FeatureManagement:NewCheckout:EnabledFor:0:Name"] = "Percentage",
            ["FeatureManagement:NewCheckout:EnabledFor:0:Parameters:Value"] =
                percentage.ToString(CultureInfo.InvariantCulture)
        })
        .Build();

    var services = new ServiceCollection();
    services.AddSingleton<IConfiguration>(config);
    services.AddFeatureManagement().AddFeatureFilter<PercentageFilter>();

    return services.BuildServiceProvider().GetRequiredService<IFeatureManager>();
}

[Fact]
public async Task Feature_IsDisabledByDefault()
{
    var featureManager = CreateFeatureManager(new Dictionary<string, bool>());

    var enabled = await featureManager.IsEnabledAsync("UnknownFeature");

    enabled.Should().BeFalse();
}
```

### Why the bounds rather than the midpoint

A 50% filter is non-deterministic, so no single assertion can describe it.
`BooleanAssertions` has no `BeOneOf` member in FluentAssertions[^13] 8.10.0
either, so `enabled.Should().BeOneOf(true, false)` fails to compile with
CS1061 — and would assert nothing if it did. The 0% and 100% cases pin both
outcomes and still exercise the real `PercentageFilter`.

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
