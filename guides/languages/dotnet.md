# .NET Style Guide

> [Doctrine](../../README.md) > [Languages](../README.md) > .NET

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Extends [C# Style Guide](csharp.md) for language-level style. This guide focuses
on .NET-specific concerns including SDK, runtime, frameworks, and tooling.

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| New project | .NET CLI[^1] | `dotnet new webapi -n MyApi` |
| Build | .NET CLI[^1] | `dotnet build` |
| Test | .NET CLI[^1] | `dotnet test` |
| Publish | .NET CLI[^1] | `dotnet publish -c Release` |
| Package | .NET CLI[^1] | `dotnet pack` |
| Run | .NET CLI[^1] | `dotnet run` |
| Watch | .NET CLI[^1] | `dotnet watch` |
| EF migrations | dotnet-ef[^2] | `dotnet ef migrations add Initial` |
| Global tools | .NET CLI[^1] | `dotnet tool install -g <tool>` |
| Format | dotnet-format[^3] | `dotnet format` |
| Security scan | .NET CLI[^1] | `dotnet list package --vulnerable` |

## .NET CLI and SDK

### Installation

You MUST use the latest LTS or STS (Standard Term Support) version of .NET for
new projects.

```bash
# Install .NET SDK (latest LTS)
# Download from https://dot.net

# Verify installation
dotnet --version
dotnet --list-sdks
dotnet --list-runtimes

# Install specific SDK version side-by-side
# .NET supports multiple SDKs installed simultaneously
```

### global.json

You SHOULD pin SDK version per solution using `global.json`:

```json
{
  "sdk": {
    "version": "10.0.100",
    "rollForward": "latestPatch"
  }
}
```

**Do:**

```bash
# Create global.json at solution root
dotnet new globaljson --sdk-version 10.0.100
```

**Don't:**

```bash
# Don't omit global.json - leads to build inconsistencies
```

### Project Templates

You MUST use `dotnet new` for creating projects:

```bash
# List available templates
dotnet new list

# Common templates
dotnet new console -n MyApp                    # Console application
dotnet new classlib -n MyLibrary              # Class library
dotnet new webapi -n MyApi                    # ASP.NET Core Web API[^4]
dotnet new mvc -n MyWebApp                    # ASP.NET Core MVC[^4]
dotnet new blazorserver -n MyBlazorApp        # Blazor Server[^5]
dotnet new blazorwasm -n MyBlazorWasm         # Blazor WebAssembly[^5]
dotnet new worker -n MyWorker                 # Worker Service[^6]
dotnet new xunit -n MyTests                   # xUnit test project[^7]
dotnet new nunit -n MyTests                   # NUnit test project[^8]
dotnet new mstest -n MyTests                  # MSTest test project[^9]

# With framework targeting
dotnet new webapi -n MyApi -f net10.0

# Create solution
dotnet new sln -n MySolution

# Add projects to solution
dotnet sln add src/MyApi/MyApi.csproj
dotnet sln add tests/MyApi.Tests/MyApi.Tests.csproj
```

### Custom Templates

You MAY create custom templates for team consistency:

```bash
# Install template from NuGet or local folder
dotnet new install MyCompany.Templates

# Uninstall template
dotnet new uninstall MyCompany.Templates
```

### Building and Running

```bash
# Restore dependencies
dotnet restore

# Build
dotnet build

# Build with specific configuration
dotnet build -c Release

# Build without restore (faster in CI)
dotnet build --no-restore

# Run project
dotnet run

# Run with specific configuration
dotnet run -c Release

# Run with arguments
dotnet run -- --environment Production

# Watch mode (auto-rebuild on changes)
dotnet watch run

# Watch with hot reload
dotnet watch
```

### Testing

```bash
# Run all tests
dotnet test

# Run with coverage
dotnet test --collect:"XPlat Code Coverage"

# Run with filter
dotnet test --filter "FullyQualifiedName~MyNamespace"
dotnet test --filter "Category=Integration"

# Run in parallel
dotnet test --parallel

# Verbose output
dotnet test --logger "console;verbosity=detailed"

# Run specific test project
dotnet test tests/MyApi.Tests/MyApi.Tests.csproj

# Set environment variable
dotnet test -e ASPNETCORE_ENVIRONMENT=Testing
```

### Publishing

```bash
# Publish for deployment
dotnet publish -c Release -o ./publish

# Self-contained deployment (includes runtime)
dotnet publish -c Release -r linux-x64 --self-contained

# Framework-dependent deployment (smaller, requires runtime installed)
dotnet publish -c Release -r linux-x64 --self-contained false

# Single-file deployment
dotnet publish -c Release -r linux-x64 \
  --self-contained \
  -p:PublishSingleFile=true

# Trimmed deployment (smaller size, experimental)
dotnet publish -c Release -r linux-x64 \
  --self-contained \
  -p:PublishTrimmed=true

# ReadyToRun (faster startup)
dotnet publish -c Release \
  -p:PublishReadyToRun=true
```

**Do:**

```xml
<!-- MyApi.csproj - Configure publish settings -->
<PropertyGroup>
  <PublishReadyToRun>true</PublishReadyToRun>
  <PublishSingleFile>false</PublishSingleFile>
  <PublishTrimmed>false</PublishTrimmed>
  <RuntimeIdentifier>linux-x64</RuntimeIdentifier>
</PropertyGroup>
```

**Don't:**

```bash
# Don't use PublishTrimmed without extensive testing
# It can break reflection-heavy code
dotnet publish -p:PublishTrimmed=true  # Risky without testing
```

### Global Tools

You SHOULD use global tools for developer productivity:

```bash
# Install global tool
dotnet tool install -g dotnet-ef
dotnet tool install -g dotnet-format
dotnet tool install -g dotnet-outdated-tool
dotnet tool install -g dotnet-stryker

# List installed tools
dotnet tool list -g

# Update tool
dotnet tool update -g dotnet-ef

# Uninstall tool
dotnet tool uninstall -g dotnet-ef
```

### Local Tools (Recommended)

You SHOULD prefer local tools (per-repository) for reproducibility:

```bash
# Create tool manifest
dotnet new tool-manifest

# Install local tool
dotnet tool install dotnet-ef
dotnet tool install dotnet-format

# Restore tools (run by team members)
dotnet tool restore

# Run local tool
dotnet tool run dotnet-ef -- migrations add Initial
dotnet ef migrations add Initial  # Shorthand
```

**.config/dotnet-tools.json:**

```json
{
  "version": 1,
  "isRoot": true,
  "tools": {
    "dotnet-ef": {
      "version": "10.0.0",
      "commands": ["dotnet-ef"]
    },
    "dotnet-format": {
      "version": "5.1.250801",
      "commands": ["dotnet-format"]
    }
  }
}
```

## Project Structure and Organization

### Solution Structure

You MUST organize solutions with clear separation of concerns:

```text
MySolution/
├── .editorconfig                  # Code style configuration
├── .gitignore                     # Git ignore rules
├── global.json                    # SDK version pinning
├── Directory.Build.props          # Shared MSBuild properties
├── Directory.Build.targets        # Shared MSBuild targets
├── Directory.Packages.props       # Central Package Management
├── MySolution.sln                 # Solution file
├── README.md                      # Documentation
├── src/                           # Source projects
│   ├── MySolution.Api/            # Web API project
│   │   ├── Controllers/
│   │   ├── Models/
│   │   ├── Services/
│   │   ├── appsettings.json
│   │   ├── appsettings.Development.json
│   │   ├── Program.cs
│   │   └── MySolution.Api.csproj
│   ├── MySolution.Core/           # Domain/business logic
│   │   ├── Entities/
│   │   ├── Interfaces/
│   │   └── MySolution.Core.csproj
│   └── MySolution.Infrastructure/ # Data access, external services
│       ├── Data/
│       ├── Repositories/
│       └── MySolution.Infrastructure.csproj
├── tests/                         # Test projects
│   ├── MySolution.Api.Tests/      # API tests
│   ├── MySolution.Core.Tests/     # Unit tests
│   └── MySolution.Integration.Tests/ # Integration tests
├── tools/                         # Build scripts, utilities
└── docs/                          # Documentation
```

### Directory.Build.props

You SHOULD use `Directory.Build.props` for shared MSBuild properties:

```xml
<Project>
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <LangVersion>14</LangVersion>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
    <EnableNETAnalyzers>true</EnableNETAnalyzers>
    <AnalysisLevel>latest-all</AnalysisLevel>
  </PropertyGroup>

  <!-- Common package references for all projects -->
  <ItemGroup>
    <PackageReference Include="Roslynator.Analyzers" Version="4.12.0">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
    </PackageReference>
  </ItemGroup>

  <!-- Source project specific settings -->
  <PropertyGroup Condition="'$(IsTestProject)' != 'true'">
    <GenerateDocumentationFile>true</GenerateDocumentationFile>
  </PropertyGroup>

  <!-- Test project specific settings -->
  <PropertyGroup Condition="'$(IsTestProject)' == 'true'">
    <IsPackable>false</IsPackable>
  </PropertyGroup>
</Project>
```

### Project References

You MUST use project references for internal dependencies:

```xml
<ItemGroup>
  <ProjectReference Include="..\MySolution.Core\MySolution.Core.csproj" />
  <ProjectReference Include="..\MySolution.Infrastructure\MySolution.Infrastructure.csproj" />
</ItemGroup>
```

**Do:**

```bash
# Add project reference via CLI
dotnet add reference ../MySolution.Core/MySolution.Core.csproj
```

**Don't:**

```xml
<!-- Don't reference projects as packages -->
<PackageReference Include="MySolution.Core" Version="1.0.0" />
```

### Implicit Usings

You SHOULD enable implicit usings for cleaner code:

```xml
<PropertyGroup>
  <ImplicitUsings>enable</ImplicitUsings>
</PropertyGroup>
```

You MAY customize implicit usings:

```xml
<ItemGroup>
  <!-- Remove default usings -->
  <Using Remove="System.Net.Http" />

  <!-- Add custom global usings -->
  <Using Include="MySolution.Core.Models" />
  <Using Include="Serilog" Alias="Log" />
</ItemGroup>
```

Or in code:

```csharp
// GlobalUsings.cs
global using MySolution.Core.Models;
global using MySolution.Core.Interfaces;
global using Microsoft.Extensions.Logging;
```

## NuGet Package Management

### Adding Packages

```bash
# Add package to project
dotnet add package Serilog

# Add specific version
dotnet add package Serilog --version 3.1.1

# Add prerelease
dotnet add package Microsoft.AspNetCore.OpenApi --prerelease

# Add to specific project
dotnet add src/MyApi/MyApi.csproj package Serilog
```

### Central Package Management (CPM)

You SHOULD use Central Package Management for solutions with multiple projects:

**Directory.Packages.props:**

```xml
<Project>
  <PropertyGroup>
    <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
    <CentralPackageTransitivePinningEnabled>true</CentralPackageTransitivePinningEnabled>
  </PropertyGroup>

  <ItemGroup>
    <!-- Package versions defined once -->
    <PackageVersion Include="Serilog" Version="3.1.1" />
    <PackageVersion Include="Serilog.Sinks.Console" Version="5.0.1" />
    <PackageVersion Include="Microsoft.EntityFrameworkCore" Version="10.0.0" />
    <PackageVersion Include="Microsoft.EntityFrameworkCore.SqlServer" Version="10.0.0" />
    <PackageVersion Include="xUnit" Version="2.6.6" />
    <PackageVersion Include="Moq" Version="4.20.70" />
  </ItemGroup>
</Project>
```

**Project files:**

```xml
<ItemGroup>
  <!-- No version specified - comes from Directory.Packages.props -->
  <PackageReference Include="Serilog" />
  <PackageReference Include="Serilog.Sinks.Console" />
</ItemGroup>
```

### Package Lock Files

You MUST use package lock files for reproducible builds:

```xml
<!-- MyProject.csproj -->
<PropertyGroup>
  <RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>
  <RestoreLockedMode Condition="'$(CI)' == 'true'">true</RestoreLockedMode>
</PropertyGroup>
```

```bash
# Generate lock file
dotnet restore

# Force regenerate
dotnet restore --force-evaluate

# Locked mode (CI)
dotnet restore --locked-mode
```

### Vulnerability Scanning

You MUST regularly scan for vulnerable packages:

```bash
# Check for vulnerable packages
dotnet list package --vulnerable

# Include transitive dependencies
dotnet list package --vulnerable --include-transitive

# Check for outdated packages
dotnet list package --outdated
```

### NuGet Configuration

**nuget.config:**

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <packageSources>
    <clear />
    <add key="nuget.org" value="https://api.nuget.org/v3/index.json" protocolVersion="3" />
    <add key="mycompany" value="https://pkgs.dev.azure.com/mycompany/_packaging/myfeed/nuget/v3/index.json" />
  </packageSources>

  <packageSourceMapping>
    <packageSource key="nuget.org">
      <package pattern="*" />
    </packageSource>
    <packageSource key="mycompany">
      <package pattern="MyCompany.*" />
    </packageSource>
  </packageSourceMapping>
</configuration>
```

## ASP.NET Core

### Minimal APIs vs Controllers

You SHOULD use Minimal APIs[^4] for simple services and Controllers for complex APIs.

**Minimal APIs (Do):**

```csharp
// Program.cs
var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

// Simple CRUD endpoints
app.MapGet("/api/users", async (IUserRepository repo) =>
{
    var users = await repo.GetAllAsync();
    return Results.Ok(users);
});

app.MapGet("/api/users/{id}", async (int id, IUserRepository repo) =>
{
    var user = await repo.GetByIdAsync(id);
    return user is not null ? Results.Ok(user) : Results.NotFound();
});

app.MapPost("/api/users", async (CreateUserRequest request, IUserRepository repo) =>
{
    var user = await repo.CreateAsync(request);
    return Results.Created($"/api/users/{user.Id}", user);
});

app.Run();
```

**Controllers (Do):**

```csharp
// For complex APIs with many endpoints, attributes, filters
[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    private readonly IUserRepository _repository;
    private readonly ILogger<UsersController> _logger;

    public UsersController(IUserRepository repository, ILogger<UsersController> logger)
    {
        _repository = repository;
        _logger = logger;
    }

    [HttpGet]
    [ProducesResponseType(typeof(IEnumerable<User>), StatusCodes.Status200OK)]
    public async Task<ActionResult<IEnumerable<User>>> GetUsers(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 10)
    {
        var users = await _repository.GetPagedAsync(page, pageSize);
        return Ok(users);
    }

    [HttpGet("{id}")]
    [ProducesResponseType(typeof(User), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<User>> GetUser(int id)
    {
        var user = await _repository.GetByIdAsync(id);
        return user is not null ? Ok(user) : NotFound();
    }

    [HttpPost]
    [ProducesResponseType(typeof(User), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<User>> CreateUser(CreateUserRequest request)
    {
        var user = await _repository.CreateAsync(request);
        return CreatedAtAction(nameof(GetUser), new { id = user.Id }, user);
    }
}
```

### Middleware Pipeline

You MUST order middleware correctly:

```csharp
var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

// 1. Exception handling MUST be first
if (app.Environment.IsDevelopment())
{
    app.UseDeveloperExceptionPage();
}
else
{
    app.UseExceptionHandler("/error");
    app.UseHsts();
}

// 2. HTTPS redirection
app.UseHttpsRedirection();

// 3. Static files (before routing)
app.UseStaticFiles();

// 4. Routing
app.UseRouting();

// 5. CORS (after routing, before auth)
app.UseCors("MyPolicy");

// 6. Authentication
app.UseAuthentication();

// 7. Authorization
app.UseAuthorization();

// 8. Custom middleware
app.UseMiddleware<RequestLoggingMiddleware>();

// 9. Endpoints MUST be last
app.MapControllers();

app.Run();
```

### Custom Middleware

**Do:**

```csharp
// Middleware/RequestLoggingMiddleware.cs
public class RequestLoggingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<RequestLoggingMiddleware> _logger;

    public RequestLoggingMiddleware(RequestDelegate next, ILogger<RequestLoggingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var startTime = DateTime.UtcNow;

        await _next(context);

        var duration = DateTime.UtcNow - startTime;
        _logger.LogInformation(
            "Request {Method} {Path} completed in {Duration}ms with status {StatusCode}",
            context.Request.Method,
            context.Request.Path,
            duration.TotalMilliseconds,
            context.Response.StatusCode);
    }
}

// Extension method
public static class RequestLoggingMiddlewareExtensions
{
    public static IApplicationBuilder UseRequestLogging(this IApplicationBuilder builder)
    {
        return builder.UseMiddleware<RequestLoggingMiddleware>();
    }
}
```

**Don't:**

```csharp
// Don't use inline middleware for complex logic
app.Use(async (context, next) =>
{
    // Too much logic here - create a proper middleware class
    var startTime = DateTime.UtcNow;
    // ... lots of code
    await next();
    // ... more code
});
```

### Dependency Injection

You MUST use constructor injection:

**Do:**

```csharp
// Program.cs
builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddScoped<IUserService, UserService>();
builder.Services.AddSingleton<IEmailService, EmailService>();
builder.Services.AddTransient<INotificationService, NotificationService>();

// Service with dependencies
public class UserService : IUserService
{
    private readonly IUserRepository _repository;
    private readonly ILogger<UserService> _logger;
    private readonly IEmailService _emailService;

    public UserService(
        IUserRepository repository,
        ILogger<UserService> logger,
        IEmailService emailService)
    {
        _repository = repository;
        _logger = logger;
        _emailService = emailService;
    }

    public async Task<User> CreateUserAsync(CreateUserRequest request)
    {
        var user = await _repository.CreateAsync(request);
        await _emailService.SendWelcomeEmailAsync(user.Email);
        return user;
    }
}
```

**Don't:**

```csharp
// Don't use service locator pattern
public class UserService
{
    private readonly IServiceProvider _serviceProvider;

    public UserService(IServiceProvider serviceProvider)
    {
        _serviceProvider = serviceProvider;
    }

    public async Task<User> CreateUserAsync(CreateUserRequest request)
    {
        // Bad: resolving at runtime
        var repository = _serviceProvider.GetRequiredService<IUserRepository>();
        return await repository.CreateAsync(request);
    }
}
```

### Service Lifetimes

- **Singleton**: Created once, shared across application lifetime
  - Use for: Stateless services, caches, configuration
- **Scoped**: Created once per request
  - Use for: DbContext, repositories, request-specific services
- **Transient**: Created each time requested
  - Use for: Lightweight stateless services

**Do:**

```csharp
// Scoped - DbContext per request
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer[^10](builder.Configuration.GetConnectionString("DefaultConnection")));

// Singleton - configuration, caching
builder.Services.AddSingleton<IMemoryCache, MemoryCache>();

// Transient - lightweight stateless services
builder.Services.AddTransient<IEmailSender, EmailSender>();
```

### Configuration

You MUST use the Options pattern:

**appsettings.json:**

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "ConnectionStrings": {
    "DefaultConnection": "Server=(localdb)\\mssqllocaldb;Database=MyDb;Trusted_Connection=true"
  },
  "Email": {
    "SmtpServer": "smtp.gmail.com",
    "SmtpPort": 587,
    "FromAddress": "noreply@example.com",
    "FromName": "My Application"
  },
  "Features": {
    "EnableNewCheckout": false,
    "MaxUploadSizeMB": 10
  }
}
```

**appsettings.Development.json:**

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Debug"
    }
  },
  "ConnectionStrings": {
    "DefaultConnection": "Server=(localdb)\\mssqllocaldb;Database=MyDb_Dev;Trusted_Connection=true"
  },
  "Email": {
    "SmtpServer": "localhost",
    "SmtpPort": 25
  }
}
```

**Options classes:**

```csharp
// Options/EmailOptions.cs
public class EmailOptions
{
    public const string Section = "Email";

    public string SmtpServer { get; set; } = string.Empty;
    public int SmtpPort { get; set; }
    public string FromAddress { get; set; } = string.Empty;
    public string FromName { get; set; } = string.Empty;
}

// Options/FeaturesOptions.cs
public class FeaturesOptions
{
    public const string Section = "Features";

    public bool EnableNewCheckout { get; set; }
    public int MaxUploadSizeMB { get; set; }
}
```

**Registration:**

```csharp
// Program.cs
builder.Services.Configure<EmailOptions>(
    builder.Configuration.GetSection(EmailOptions.Section));

builder.Services.Configure<FeaturesOptions>(
    builder.Configuration.GetSection(FeaturesOptions.Section));
```

**Usage:**

```csharp
public class EmailService : IEmailService
{
    private readonly EmailOptions _options;
    private readonly ILogger<EmailService> _logger;

    public EmailService(
        IOptions<EmailOptions> options,
        ILogger<EmailService> logger)
    {
        _options = options.Value;
        _logger = logger;
    }

    public async Task SendAsync(string to, string subject, string body)
    {
        using var client = new SmtpClient(_options.SmtpServer, _options.SmtpPort);
        // ...
    }
}
```

### User Secrets (Development)

You MUST NOT commit secrets to source control. Use User Secrets for development:

```bash
# Initialize user secrets
dotnet user-secrets init

# Set secret
dotnet user-secrets set "Email:SmtpPassword" "my-password"
dotnet user-secrets set "ConnectionStrings:DefaultConnection" "Server=...;Password=secret"

# List secrets
dotnet user-secrets list

# Remove secret
dotnet user-secrets remove "Email:SmtpPassword"

# Clear all secrets
dotnet user-secrets clear
```

**Project file:**

```xml
<PropertyGroup>
  <UserSecretsId>aspnet-MyApi-12345678</UserSecretsId>
</PropertyGroup>
```

**Access in code:**

```csharp
// Automatically loaded in Development environment
var smtpPassword = builder.Configuration["Email:SmtpPassword"];
```

### Environment Variables

You SHOULD use environment variables for production secrets:

```bash
# Linux/macOS
export Email__SmtpPassword="production-password"
export ConnectionStrings__DefaultConnection="Server=prod;..."

# Windows
set Email__SmtpPassword=production-password
set ConnectionStrings__DefaultConnection=Server=prod;...
```

**Do:**

```csharp
// Configuration hierarchy (later overrides earlier):
// 1. appsettings.json
// 2. appsettings.{Environment}.json
// 3. User Secrets (Development only)
// 4. Environment variables
// 5. Command line arguments

var builder = WebApplication.CreateBuilder(args);
// All sources automatically configured
```

### Health Checks

You SHOULD implement health checks:

```csharp
// Program.cs
builder.Services.AddHealthChecks()
    .AddDbContextCheck<ApplicationDbContext>()
    .AddSqlServer(
        connectionString: builder.Configuration.GetConnectionString("DefaultConnection"),
        name: "sql-server")
    .AddUrlGroup(new Uri("https://api.external.com/health"), name: "external-api");

var app = builder.Build();

app.MapHealthChecks("/health");
app.MapHealthChecks("/health/ready", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("ready")
});
app.MapHealthChecks("/health/live", new HealthCheckOptions
{
    Predicate = _ => false // Just check if app is running
});
```

**Custom health check:**

```csharp
public class DatabaseHealthCheck : IHealthCheck
{
    private readonly ApplicationDbContext _context;

    public DatabaseHealthCheck(ApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await _context.Database.CanConnectAsync(cancellationToken);
            return HealthCheckResult.Healthy("Database is reachable");
        }
        catch (Exception ex)
        {
            return HealthCheckResult.Unhealthy("Database is unreachable", ex);
        }
    }
}
```

## Entity Framework Core

### DbContext Configuration

Entity Framework Core[^10] is the recommended ORM for .NET applications.

**Do:**

```csharp
// Data/ApplicationDbContext.cs
public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    public DbSet<User> Users => Set<User>();
    public DbSet<Order> Orders => Set<Order>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Apply all configurations from assembly
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(ApplicationDbContext).Assembly);
    }
}

// Data/Configurations/UserConfiguration.cs
public class UserConfiguration : IEntityTypeConfiguration<User>
{
    public void Configure(EntityTypeBuilder<User> builder)
    {
        builder.HasKey(u => u.Id);

        builder.Property(u => u.Email)
            .IsRequired()
            .HasMaxLength(256);

        builder.HasIndex(u => u.Email)
            .IsUnique();

        builder.Property(u => u.CreatedAt)
            .IsRequired()
            .HasDefaultValueSql("GETUTCDATE()");
    }
}
```

**Don't:**

```csharp
// Don't configure entities in OnModelCreating - use IEntityTypeConfiguration
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    modelBuilder.Entity<User>(entity =>
    {
        entity.HasKey(u => u.Id);
        entity.Property(u => u.Email).IsRequired().HasMaxLength(256);
        // ... many more entities
    });
}
```

### Migrations

You MUST use code-first migrations:

```bash
# Add migration
dotnet ef migrations add InitialCreate

# Add migration with specific context
dotnet ef migrations add InitialCreate --context ApplicationDbContext

# Update database
dotnet ef database update

# Update to specific migration
dotnet ef database update AddUserTable

# Rollback to previous migration
dotnet ef database update PreviousMigration

# Remove last migration (not applied)
dotnet ef migrations remove

# Generate SQL script
dotnet ef migrations script

# Generate script from specific migration
dotnet ef migrations script AddUserTable AddOrderTable

# List migrations
dotnet ef migrations list

# Drop database
dotnet ef database drop
```

**Migration design:**

```csharp
public partial class InitialCreate : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.CreateTable(
            name: "Users",
            columns: table => new
            {
                Id = table.Column<int>(nullable: false)
                    .Annotation("SqlServer:Identity", "1, 1"),
                Email = table.Column<string>(maxLength: 256, nullable: false),
                CreatedAt = table.Column<DateTime>(nullable: false,
                    defaultValueSql: "GETUTCDATE()")
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_Users", x => x.Id);
            });

        migrationBuilder.CreateIndex(
            name: "IX_Users_Email",
            table: "Users",
            column: "Email",
            unique: true);
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropTable(name: "Users");
    }
}
```

### Database Initialization

**Do:**

```csharp
// Program.cs
var app = builder.Build();

// Apply migrations on startup (development only)
if (app.Environment.IsDevelopment())
{
    using var scope = app.Services.CreateScope();
    var context = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
    await context.Database.MigrateAsync();
}

app.Run();
```

**Production:**

```bash
# Run migrations separately in production
dotnet ef database update --connection "Server=prod;..."

# Or use SQL script
dotnet ef migrations script -o migration.sql
# Review and run SQL script manually
```

### Query Optimization

**Do:**

```csharp
// Use AsNoTracking for read-only queries
var users = await _context.Users
    .AsNoTracking()
    .Where(u => u.IsActive)
    .ToListAsync();

// Eager loading with Include
var orders = await _context.Orders
    .Include(o => o.User)
    .Include(o => o.Items)
        .ThenInclude(i => i.Product)
    .Where(o => o.Status == OrderStatus.Pending)
    .ToListAsync();

// Projection to avoid loading unnecessary data
var userDtos = await _context.Users
    .Select(u => new UserDto
    {
        Id = u.Id,
        Email = u.Email,
        Name = u.Name
    })
    .ToListAsync();

// Pagination
var pagedUsers = await _context.Users
    .OrderBy(u => u.CreatedAt)
    .Skip((page - 1) * pageSize)
    .Take(pageSize)
    .ToListAsync();

// Split queries for multiple collections
var orders = await _context.Orders
    .Include(o => o.Items)
    .Include(o => o.Payments)
    .AsSplitQuery()
    .ToListAsync();
```

**Don't:**

```csharp
// Don't use ToList() before filtering
var users = _context.Users.ToList() // Loads all users into memory!
    .Where(u => u.IsActive)
    .ToList();

// Don't use N+1 queries
var orders = await _context.Orders.ToListAsync();
foreach (var order in orders)
{
    // N+1: separate query for each order
    var user = await _context.Users.FindAsync(order.UserId);
}

// Don't track entities for read-only operations
var users = await _context.Users // Tracking overhead
    .Where(u => u.IsActive)
    .ToListAsync();
```

### Repository Pattern

You MAY use Repository pattern for complex data access:

```csharp
// Repositories/IUserRepository.cs
public interface IUserRepository
{
    Task<User?> GetByIdAsync(int id, CancellationToken cancellationToken = default);
    Task<User?> GetByEmailAsync(string email, CancellationToken cancellationToken = default);
    Task<IEnumerable<User>> GetAllAsync(CancellationToken cancellationToken = default);
    Task<User> AddAsync(User user, CancellationToken cancellationToken = default);
    Task UpdateAsync(User user, CancellationToken cancellationToken = default);
    Task DeleteAsync(int id, CancellationToken cancellationToken = default);
}

// Repositories/UserRepository.cs
public class UserRepository : IUserRepository
{
    private readonly ApplicationDbContext _context;

    public UserRepository(ApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<User?> GetByIdAsync(int id, CancellationToken cancellationToken = default)
    {
        return await _context.Users
            .AsNoTracking()
            .FirstOrDefaultAsync(u => u.Id == id, cancellationToken);
    }

    public async Task<User?> GetByEmailAsync(string email, CancellationToken cancellationToken = default)
    {
        return await _context.Users
            .AsNoTracking()
            .FirstOrDefaultAsync(u => u.Email == email, cancellationToken);
    }

    public async Task<IEnumerable<User>> GetAllAsync(CancellationToken cancellationToken = default)
    {
        return await _context.Users
            .AsNoTracking()
            .ToListAsync(cancellationToken);
    }

    public async Task<User> AddAsync(User user, CancellationToken cancellationToken = default)
    {
        _context.Users.Add(user);
        await _context.SaveChangesAsync(cancellationToken);
        return user;
    }

    public async Task UpdateAsync(User user, CancellationToken cancellationToken = default)
    {
        _context.Users.Update(user);
        await _context.SaveChangesAsync(cancellationToken);
    }

    public async Task DeleteAsync(int id, CancellationToken cancellationToken = default)
    {
        var user = await _context.Users.FindAsync(new object[] { id }, cancellationToken);
        if (user is not null)
        {
            _context.Users.Remove(user);
            await _context.SaveChangesAsync(cancellationToken);
        }
    }
}
```

## Testing

### xUnit Test Structure

You MUST follow AAA pattern (Arrange, Act, Assert) when writing tests with xUnit[^7]:

```csharp
public class UserServiceTests
{
    private readonly Mock<IUserRepository> _mockRepository;
    private readonly Mock<ILogger<UserService>> _mockLogger;
    private readonly UserService _service;

    public UserServiceTests()
    {
        _mockRepository = new Mock<IUserRepository>();
        _mockLogger = new Mock<ILogger<UserService>>();
        _service = new UserService(_mockRepository.Object, _mockLogger.Object);
    }

    [Fact]
    public async Task CreateUserAsync_WithValidRequest_ReturnsUser()
    {
        // Arrange
        var request = new CreateUserRequest
        {
            Email = "test@example.com",
            Name = "Test User"
        };

        var expectedUser = new User
        {
            Id = 1,
            Email = request.Email,
            Name = request.Name
        };

        _mockRepository
            .Setup(r => r.AddAsync(It.IsAny<User>(), default))
            .ReturnsAsync(expectedUser);

        // Act
        var result = await _service.CreateUserAsync(request);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(expectedUser.Email, result.Email);
        Assert.Equal(expectedUser.Name, result.Name);

        _mockRepository.Verify(
            r => r.AddAsync(It.IsAny<User>(), default),
            Times.Once);
    }

    [Fact]
    public async Task GetUserAsync_WhenUserNotFound_ReturnsNull()
    {
        // Arrange
        _mockRepository
            .Setup(r => r.GetByIdAsync(999, default))
            .ReturnsAsync((User?)null);

        // Act
        var result = await _service.GetUserAsync(999);

        // Assert
        Assert.Null(result);
    }

    [Theory]
    [InlineData("")]
    [InlineData(" ")]
    [InlineData(null)]
    public async Task CreateUserAsync_WithInvalidEmail_ThrowsArgumentException(string email)
    {
        // Arrange
        var request = new CreateUserRequest { Email = email, Name = "Test" };

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(() =>
            _service.CreateUserAsync(request));
    }
}
```

### Integration Testing with WebApplicationFactory

**Do:**

```csharp
// Tests/ApiTests.cs
public class UserApiTests : IClassFixture<WebApplicationFactory<Program>>[^11]
{
    private readonly WebApplicationFactory<Program> _factory;
    private readonly HttpClient _client;

    public UserApiTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory;
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task GetUsers_ReturnsSuccessAndUsers()
    {
        // Act
        var response = await _client.GetAsync("/api/users");

        // Assert
        response.EnsureSuccessStatusCode();
        var users = await response.Content.ReadFromJsonAsync<List<UserDto>>();
        Assert.NotNull(users);
    }

    [Fact]
    public async Task CreateUser_WithValidRequest_ReturnsCreated()
    {
        // Arrange
        var request = new CreateUserRequest
        {
            Email = "test@example.com",
            Name = "Test User"
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/users", request);

        // Assert
        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        var user = await response.Content.ReadFromJsonAsync<UserDto>();
        Assert.NotNull(user);
        Assert.Equal(request.Email, user.Email);
    }
}
```

### Custom WebApplicationFactory

**Do:**

```csharp
// Tests/CustomWebApplicationFactory.cs
public class CustomWebApplicationFactory : WebApplicationFactory<Program>[^11]
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
        {
            // Remove the app's ApplicationDbContext registration
            var descriptor = services.SingleOrDefault(
                d => d.ServiceType == typeof(DbContextOptions<ApplicationDbContext>));

            if (descriptor != null)
            {
                services.Remove(descriptor);
            }

            // Add ApplicationDbContext using an in-memory database for testing
            services.AddDbContext<ApplicationDbContext>(options =>
            {
                options.UseInMemoryDatabase("InMemoryDbForTesting");
            });

            // Build the service provider
            var sp = services.BuildServiceProvider();

            // Create a scope to obtain a reference to the database contexts
            using var scope = sp.CreateScope();
            var scopedServices = scope.ServiceProvider;
            var db = scopedServices.GetRequiredService<ApplicationDbContext>();

            // Ensure the database is created
            db.Database.EnsureCreated();

            // Seed test data
            SeedTestData(db);
        });
    }

    private static void SeedTestData(ApplicationDbContext context)
    {
        context.Users.AddRange(
            new User { Id = 1, Email = "user1@test.com", Name = "User 1" },
            new User { Id = 2, Email = "user2@test.com", Name = "User 2" }
        );
        context.SaveChanges();
    }
}
```

### Mocking with Moq

You SHOULD use Moq[^12] for mocking dependencies in unit tests.

**Do:**

```csharp
// Setup method return value
_mockRepository
    .Setup(r => r.GetByIdAsync(1, default))
    .ReturnsAsync(new User { Id = 1, Email = "test@example.com" });

// Setup with predicate
_mockRepository
    .Setup(r => r.GetByIdAsync(It.IsAny<int>(), default))
    .ReturnsAsync((int id, CancellationToken _) =>
        id > 0 ? new User { Id = id } : null);

// Setup to throw exception
_mockRepository
    .Setup(r => r.AddAsync(It.IsAny<User>(), default))
    .ThrowsAsync(new DbUpdateException("Database error"));

// Verify method was called
_mockRepository.Verify(
    r => r.AddAsync(It.IsAny<User>(), default),
    Times.Once);

// Verify method was never called
_mockRepository.Verify(
    r => r.DeleteAsync(It.IsAny<int>(), default),
    Times.Never);

// Verify with specific arguments
_mockRepository.Verify(
    r => r.GetByIdAsync(1, default),
    Times.Once);
```

### Test Data Builders

You SHOULD use Test Data Builders for complex objects:

```csharp
// Tests/Builders/UserBuilder.cs
public class UserBuilder
{
    private int _id = 1;
    private string _email = "test@example.com";
    private string _name = "Test User";
    private DateTime _createdAt = DateTime.UtcNow;

    public UserBuilder WithId(int id)
    {
        _id = id;
        return this;
    }

    public UserBuilder WithEmail(string email)
    {
        _email = email;
        return this;
    }

    public UserBuilder WithName(string name)
    {
        _name = name;
        return this;
    }

    public UserBuilder CreatedAt(DateTime createdAt)
    {
        _createdAt = createdAt;
        return this;
    }

    public User Build()
    {
        return new User
        {
            Id = _id,
            Email = _email,
            Name = _name,
            CreatedAt = _createdAt
        };
    }
}

// Usage in tests
[Fact]
public async Task Example()
{
    var user = new UserBuilder()
        .WithId(123)
        .WithEmail("special@example.com")
        .Build();

    // Test with user...
}
```

### Snapshot Testing

You MAY use Verify[^13] for snapshot testing:

```csharp
[Fact]
public async Task GetUsers_ReturnsExpectedJson()
{
    // Arrange
    var response = await _client.GetAsync("/api/users");
    var content = await response.Content.ReadAsStringAsync();

    // Assert - compares against Users_ReturnsExpectedJson.verified.txt
    await Verify(content);
}
```

## Performance

### Async/Await Best Practices

**Do:**

```csharp
// Use async all the way
public async Task<User> GetUserAsync(int id)
{
    return await _repository.GetByIdAsync(id);
}

// Use ConfigureAwait(false) in libraries
public async Task<User> GetUserAsync(int id)
{
    return await _repository.GetByIdAsync(id).ConfigureAwait(false);
}

// Avoid async void except for event handlers
public async void Button_Click(object sender, EventArgs e)
{
    await ProcessAsync();
}

// Return Task directly when possible
public Task<User> GetUserAsync(int id)
{
    return _repository.GetByIdAsync(id);
}

// Use ValueTask for hot paths
public ValueTask<User?> GetCachedUserAsync(int id)
{
    if (_cache.TryGetValue(id, out var user))
    {
        return ValueTask.FromResult(user);
    }

    return new ValueTask<User?>(LoadUserAsync(id));
}

// Parallel execution
var tasks = ids.Select(id => GetUserAsync(id));
var users = await Task.WhenAll(tasks);
```

**Don't:**

```csharp
// Don't use .Result or .Wait() - causes deadlocks
public User GetUser(int id)
{
    return GetUserAsync(id).Result; // Deadlock risk!
}

// Don't use async void for regular methods
public async void ProcessUser(int id) // Should return Task
{
    await _repository.UpdateAsync(id);
}

// Don't create unnecessary async methods
public async Task<int> GetValueAsync()
{
    return await Task.FromResult(42); // Just return 42!
}
```

### Memory Management

**Do:**

```csharp
// Use ArrayPool for large temporary buffers
var pool = ArrayPool<byte>.Shared;
byte[] buffer = pool.Rent(1024);
try
{
    // Use buffer
}
finally
{
    pool.Return(buffer);
}

// Use Span<T> and Memory<T> for slicing
public void ProcessData(ReadOnlySpan<byte> data)
{
    var first10 = data.Slice(0, 10);
    // No allocation for slice
}

// Use stackalloc for small buffers
Span<byte> buffer = stackalloc byte[256];

// Use StringBuilder for string concatenation
var sb = new StringBuilder();
foreach (var item in items)
{
    sb.Append(item);
}
var result = sb.ToString();

// Dispose IDisposable properly
await using var stream = File.OpenRead("file.txt");
using var reader = new StreamReader(stream);
```

**Don't:**

```csharp
// Don't concatenate strings in loops
string result = "";
foreach (var item in items)
{
    result += item; // Creates new string each time
}

// Don't forget to dispose
var stream = File.OpenRead("file.txt"); // Leak!

// Don't use ToList() unnecessarily
var count = users.ToList().Count; // Should be users.Count()
```

### Benchmarking with BenchmarkDotNet

You SHOULD use BenchmarkDotNet[^14] for accurate performance measurements.

```csharp
using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Running;

[MemoryDiagnoser]
[SimpleJob(warmupCount: 3, iterationCount: 5)]
public class StringBenchmarks
{
    private const int Iterations = 1000;

    [Benchmark(Baseline = true)]
    public string StringConcatenation()
    {
        string result = "";
        for (int i = 0; i < Iterations; i++)
        {
            result += i.ToString();
        }
        return result;
    }

    [Benchmark]
    public string StringBuilderAppend()
    {
        var sb = new StringBuilder();
        for (int i = 0; i < Iterations; i++)
        {
            sb.Append(i);
        }
        return sb.ToString();
    }

    [Benchmark]
    public string StringCreate()
    {
        return string.Create(Iterations * 4, Iterations, (span, iterations) =>
        {
            int pos = 0;
            for (int i = 0; i < iterations; i++)
            {
                var str = i.ToString();
                str.AsSpan().CopyTo(span.Slice(pos));
                pos += str.Length;
            }
        });
    }
}

// Program.cs
public class Program
{
    public static void Main(string[] args)
    {
        BenchmarkRunner.Run<StringBenchmarks>();
    }
}
```

```bash
# Run benchmarks
dotnet run -c Release
```

### Response Caching

**Do:**

```csharp
// Program.cs
builder.Services.AddResponseCaching()[^15];

var app = builder.Build();
app.UseResponseCaching();

// Controller
[HttpGet]
[ResponseCache(Duration = 60, VaryByQueryKeys = new[] { "page" })]
public async Task<ActionResult<IEnumerable<User>>> GetUsers(int page = 1)
{
    var users = await _repository.GetPagedAsync(page, 10);
    return Ok(users);
}
```

### Output Caching (.NET 7+)

**Do:**

```csharp
// Program.cs
builder.Services.AddOutputCache[^16](options =>
{
    options.AddBasePolicy(builder => builder.Expire(TimeSpan.FromSeconds(60)));
    options.AddPolicy("Expire20", builder => builder.Expire(TimeSpan.FromSeconds(20)));
});

var app = builder.Build();
app.UseOutputCache();

// Minimal API
app.MapGet("/api/users", async (IUserRepository repo) =>
{
    return await repo.GetAllAsync();
})
.CacheOutput("Expire20");

// Controller
[HttpGet]
[OutputCache(PolicyName = "Expire20")]
public async Task<ActionResult<IEnumerable<User>>> GetUsers()
{
    var users = await _repository.GetAllAsync();
    return Ok(users);
}
```

## Security

### Authentication and Authorization

**JWT Bearer Authentication[^17]:**

```csharp
// Program.cs
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = builder.Configuration["Jwt:Issuer"],
            ValidAudience = builder.Configuration["Jwt:Audience"],
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Key"]))
        };
    });

builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("AdminOnly", policy => policy.RequireRole("Admin"));
    options.AddPolicy("UserOrAdmin", policy =>
        policy.RequireRole("User", "Admin"));
});

var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();

// Controller
[Authorize]
[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    [HttpGet]
    [Authorize(Roles = "User,Admin")]
    public async Task<ActionResult<IEnumerable<User>>> GetUsers()
    {
        // ...
    }

    [HttpDelete("{id}")]
    [Authorize(Policy = "AdminOnly")]
    public async Task<IActionResult> DeleteUser(int id)
    {
        // ...
    }
}
```

### HTTPS Enforcement

You MUST enforce HTTPS in production:

```csharp
// Program.cs
var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
    app.UseHttpsRedirection();
    app.UseHsts();
}
```

**appsettings.json:**

```json
{
  "Kestrel": {
    "Endpoints": {
      "Http": {
        "Url": "http://localhost:5000"
      },
      "Https": {
        "Url": "https://localhost:5001"
      }
    }
  }
}
```

### CORS

**Do:**

```csharp
// Program.cs
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        policy.WithOrigins("https://example.com")
            .AllowAnyMethod()
            .AllowAnyHeader()
            .AllowCredentials();
    });
});

var app = builder.Build();
app.UseCors("AllowFrontend");
```

**Don't:**

```csharp
// Don't allow all origins in production
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin() // Insecure!
            .AllowAnyMethod()
            .AllowAnyHeader();
    });
});
```

### Input Validation

**Do:**

```csharp
// Use Data Annotations
public class CreateUserRequest
{
    [Required]
    [EmailAddress]
    [MaxLength(256)]
    public string Email { get; set; } = string.Empty;

    [Required]
    [MinLength(2)]
    [MaxLength(100)]
    public string Name { get; set; } = string.Empty;

    [Range(18, 120)]
    public int Age { get; set; }
}

// FluentValidation[^18] (more powerful)
public class CreateUserRequestValidator : AbstractValidator<CreateUserRequest>
{
    public CreateUserRequestValidator()
    {
        RuleFor(x => x.Email)
            .NotEmpty()
            .EmailAddress()
            .MaximumLength(256);

        RuleFor(x => x.Name)
            .NotEmpty()
            .Length(2, 100);

        RuleFor(x => x.Age)
            .InclusiveBetween(18, 120);
    }
}

// Register FluentValidation
builder.Services.AddValidatorsFromAssemblyContaining<CreateUserRequestValidator>();
builder.Services.AddFluentValidationAutoValidation();
```

### SQL Injection Prevention

**Do:**

```csharp
// Use parameterized queries (EF Core does this automatically)
var users = await _context.Users
    .Where(u => u.Email == email)
    .ToListAsync();

// For raw SQL, use parameters
var users = await _context.Users
    .FromSqlRaw("SELECT * FROM Users WHERE Email = {0}", email)
    .ToListAsync();
```

**Don't:**

```csharp
// Never concatenate SQL strings
var users = await _context.Users
    .FromSqlRaw($"SELECT * FROM Users WHERE Email = '{email}'") // SQL injection!
    .ToListAsync();
```

### Secret Management

**Azure Key Vault[^19] (Production):**

```csharp
// Program.cs
if (!builder.Environment.IsDevelopment())
{
    var keyVaultUri = new Uri(builder.Configuration["KeyVault:Uri"]);
    builder.Configuration.AddAzureKeyVault(
        keyVaultUri,
        new DefaultAzureCredential());
}
```

**AWS Secrets Manager[^20]:**

```csharp
builder.Configuration.AddSecretsManager(configurator: options =>
{
    options.SecretFilter = entry => entry.Name.StartsWith("MyApp_");
});
```

### Rate Limiting (.NET 7+)

```csharp
// Program.cs
builder.Services.AddRateLimiter[^21](options =>
{
    options.AddFixedWindowLimiter("fixed", options =>
    {
        options.PermitLimit = 100;
        options.Window = TimeSpan.FromMinutes(1);
        options.QueueProcessingOrder = QueueProcessingOrder.OldestFirst;
        options.QueueLimit = 5;
    });

    options.AddSlidingWindowLimiter("sliding", options =>
    {
        options.PermitLimit = 100;
        options.Window = TimeSpan.FromMinutes(1);
        options.SegmentsPerWindow = 4;
    });
});

var app = builder.Build();
app.UseRateLimiter();

// Apply to endpoint
app.MapGet("/api/users", async (IUserRepository repo) =>
{
    return await repo.GetAllAsync();
})
.RequireRateLimiting("fixed");
```

## CI/CD

### GitHub Actions for .NET

You SHOULD use GitHub Actions[^22] for CI/CD pipelines.

**.github/workflows/dotnet.yml:**

```yaml
name: .NET CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  DOTNET_VERSION: '10.0.x'

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Setup .NET
      uses: actions/setup-dotnet@v4
      with:
        dotnet-version: ${{ env.DOTNET_VERSION }}

    - name: Restore dependencies
      run: dotnet restore

    - name: Build
      run: dotnet build --no-restore --configuration Release

    - name: Run tests
      run: dotnet test --no-build --configuration Release --verbosity normal --collect:"XPlat Code Coverage"

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.cobertura.xml

  format:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Setup .NET
      uses: actions/setup-dotnet@v4
      with:
        dotnet-version: ${{ env.DOTNET_VERSION }}

    - name: Restore dotnet tools
      run: dotnet tool restore

    - name: Check formatting
      run: dotnet format --verify-no-changes

  publish:
    runs-on: ubuntu-latest
    needs: [build, format]
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v4

    - name: Setup .NET
      uses: actions/setup-dotnet@v4
      with:
        dotnet-version: ${{ env.DOTNET_VERSION }}

    - name: Publish
      run: dotnet publish src/MyApi/MyApi.csproj -c Release -o ./publish

    - name: Upload artifact
      uses: actions/upload-artifact@v4
      with:
        name: published-app
        path: ./publish
```

### Multi-stage Docker Build

You SHOULD use multi-stage Docker builds[^23] for optimal image size and security.

**Dockerfile:**

```dockerfile
# Stage 1: Build
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Copy csproj and restore dependencies (cached layer)
COPY ["src/MyApi/MyApi.csproj", "src/MyApi/"]
COPY ["src/MyApi.Core/MyApi.Core.csproj", "src/MyApi.Core/"]
RUN dotnet restore "src/MyApi/MyApi.csproj"

# Copy everything else and build
COPY . .
WORKDIR "/src/src/MyApi"
RUN dotnet build "MyApi.csproj" -c Release -o /app/build

# Stage 2: Publish
FROM build AS publish
RUN dotnet publish "MyApi.csproj" -c Release -o /app/publish /p:UseAppHost=false

# Stage 3: Runtime
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app

# Create non-root user
RUN addgroup --gid 1000 appuser && \
    adduser --uid 1000 --gid 1000 --disabled-password --gecos "" appuser

# Copy published app
COPY --from=publish /app/publish .

# Switch to non-root user
USER appuser

EXPOSE 8080

ENTRYPOINT ["dotnet", "MyApi.dll"]
```

**.dockerignore:**

```text
**/.git
**/.gitignore
**/.vs
**/.vscode
**/bin
**/obj
**/*.user
**/node_modules
**/coverage
**/TestResults
```

**Build and run:**

```bash
# Build image
docker build -t myapi:latest .

# Run container
docker run -d -p 8080:8080 \
  -e ASPNETCORE_ENVIRONMENT=Production \
  -e ConnectionStrings__DefaultConnection="Server=db;..." \
  myapi:latest
```

### Docker Compose

You MAY use Docker Compose[^24] for local development and testing.

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - ASPNETCORE_ENVIRONMENT=Production
      - ConnectionStrings__DefaultConnection=Server=db;Database=MyDb;User Id=sa;Password=YourStrong@Passw0rd;TrustServerCertificate=True
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: mcr.microsoft.com/mssql/server:2022-latest
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=YourStrong@Passw0rd
    ports:
      - "1433:1433"
    volumes:
      - sqldata:/var/opt/mssql
    restart: unless-stopped

volumes:
  sqldata:
```

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Versioning

You SHOULD use Semantic Versioning and embed version in assemblies:

**Directory.Build.props:**

```xml
<PropertyGroup>
  <Version>1.2.3</Version>
  <AssemblyVersion>1.2.3.0</AssemblyVersion>
  <FileVersion>1.2.3.0</FileVersion>
  <InformationalVersion>1.2.3+$(SourceRevisionId)</InformationalVersion>
</PropertyGroup>
```

**From Git (MinVer[^25]):**

```xml
<ItemGroup>
  <PackageReference Include="MinVer" Version="5.0.0">
    <PrivateAssets>all</PrivateAssets>
    <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
  </PackageReference>
</ItemGroup>
```

```bash
# Version from git tags
git tag v1.2.3
dotnet build
# Version: 1.2.3
```

### NuGet Package Publishing

You SHOULD publish reusable libraries to NuGet[^26].

```bash
# Pack
dotnet pack -c Release

# Pack with version
dotnet pack -c Release /p:Version=1.2.3

# Publish to NuGet.org
dotnet nuget push bin/Release/MyLibrary.1.2.3.nupkg \
  --api-key $NUGET_API_KEY \
  --source https://api.nuget.org/v3/index.json

# Publish to private feed
dotnet nuget push bin/Release/MyLibrary.1.2.3.nupkg \
  --api-key $FEED_API_KEY \
  --source https://pkgs.dev.azure.com/myorg/_packaging/myfeed/nuget/v3/index.json
```

**Package metadata:**

```xml
<PropertyGroup>
  <PackageId>MyCompany.MyLibrary</PackageId>
  <Version>1.2.3</Version>
  <Authors>My Company</Authors>
  <Company>My Company</Company>
  <Product>My Library</Product>
  <Description>A library for doing amazing things</Description>
  <PackageLicenseExpression>MIT</PackageLicenseExpression>
  <PackageProjectUrl>https://github.com/mycompany/mylibrary</PackageProjectUrl>
  <RepositoryUrl>https://github.com/mycompany/mylibrary</RepositoryUrl>
  <RepositoryType>git</RepositoryType>
  <PackageTags>library;dotnet;csharp</PackageTags>
  <PackageReadmeFile>README.md</PackageReadmeFile>
</PropertyGroup>

<ItemGroup>
  <None Include="README.md" Pack="true" PackagePath="\" />
</ItemGroup>
```

## Logging

### Structured Logging with Serilog

You SHOULD use Serilog[^27] for structured logging:

```csharp
// Program.cs
using Serilog;

var builder = WebApplication.CreateBuilder(args);

// Configure Serilog
Log.Logger = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration)
    .Enrich.FromLogContext()
    .Enrich.WithMachineName()
    .Enrich.WithEnvironmentName()
    .WriteTo.Console(
        outputTemplate: "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj} {Properties:j}{NewLine}{Exception}")
    .WriteTo.File(
        path: "logs/log-.txt",
        rollingInterval: RollingInterval.Day,
        retainedFileCountLimit: 7)
    .CreateLogger();

builder.Host.UseSerilog();

var app = builder.Build();

// Log application startup
app.Logger.LogInformation("Starting application...");

try
{
    app.Run();
}
catch (Exception ex)
{
    Log.Fatal(ex, "Application terminated unexpectedly");
}
finally
{
    Log.CloseAndFlush();
}
```

**appsettings.json:**

```json
{
  "Serilog": {
    "MinimumLevel": {
      "Default": "Information",
      "Override": {
        "Microsoft": "Warning",
        "Microsoft.AspNetCore": "Warning",
        "System": "Warning"
      }
    },
    "WriteTo": [
      {
        "Name": "Console"
      },
      {
        "Name": "File",
        "Args": {
          "path": "logs/log-.txt",
          "rollingInterval": "Day"
        }
      },
      {
        "Name": "Seq",
        "Args": {
          "serverUrl": "http://localhost:5341"
        }
      }
    ],
    "Enrich": [ "FromLogContext", "WithMachineName", "WithThreadId" ]
  }
}
```

**Structured logging usage:**

```csharp
public class UserService
{
    private readonly ILogger<UserService> _logger;

    public UserService(ILogger<UserService> logger)
    {
        _logger = logger;
    }

    public async Task<User> CreateUserAsync(CreateUserRequest request)
    {
        _logger.LogInformation(
            "Creating user with email {Email}",
            request.Email); // Structured property

        try
        {
            var user = await _repository.CreateAsync(request);

            _logger.LogInformation(
                "User {UserId} created successfully with email {Email}",
                user.Id,
                user.Email);

            return user;
        }
        catch (Exception ex)
        {
            _logger.LogError(
                ex,
                "Failed to create user with email {Email}",
                request.Email);
            throw;
        }
    }
}
```

## Observability

### OpenTelemetry

You SHOULD use OpenTelemetry[^28] for distributed tracing and metrics.

```csharp
// Program.cs
builder.Services.AddOpenTelemetry()
    .WithTracing(tracing => tracing
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddEntityFrameworkCoreInstrumentation()
        .AddOtlpExporter())
    .WithMetrics(metrics => metrics
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddRuntimeInstrumentation()
        .AddOtlpExporter());
```

### Application Insights

You MAY use Application Insights[^29] for Azure-hosted applications.

```csharp
// Program.cs
builder.Services.AddApplicationInsightsTelemetry(options =>
{
    options.ConnectionString = builder.Configuration["ApplicationInsights:ConnectionString"];
});

// Custom metrics
public class OrderService
{
    private readonly TelemetryClient _telemetryClient;

    public async Task ProcessOrderAsync(Order order)
    {
        var stopwatch = Stopwatch.StartNew();

        try
        {
            await _repository.SaveAsync(order);

            _telemetryClient.TrackMetric("OrderProcessingTime", stopwatch.ElapsedMilliseconds);
            _telemetryClient.TrackEvent("OrderProcessed", new Dictionary<string, string>
            {
                ["OrderId"] = order.Id.ToString(),
                ["Amount"] = order.Total.ToString()
            });
        }
        catch (Exception ex)
        {
            _telemetryClient.TrackException(ex);
            throw;
        }
    }
}
```

## .NET Aspire

You **SHOULD** use .NET Aspire[^30] for cloud-native distributed applications.

### Why .NET Aspire

- Opinionated stack for building observable, production-ready distributed apps
- Built-in service discovery, health checks, and telemetry
- Simplified local development with orchestration
- First-class support for containers and cloud deployment

### Getting Started

```bash
# Install Aspire workload
dotnet workload install aspire

# Create new Aspire project
dotnet new aspire-starter -n MyApp
```

### AppHost Configuration

```csharp
// MyApp.AppHost/Program.cs
var builder = DistributedApplication.CreateBuilder(args);

// Add PostgreSQL container
var postgres = builder.AddPostgres("postgres")
    .WithPgAdmin();

var db = postgres.AddDatabase("mydb");

// Add Redis for caching
var redis = builder.AddRedis("redis")
    .WithRedisCommander();

// Add API project with dependencies
var api = builder.AddProject<Projects.MyApp_Api>("api")
    .WithReference(db)
    .WithReference(redis);

// Add web frontend
builder.AddProject<Projects.MyApp_Web>("web")
    .WithReference(api);

builder.Build().Run();
```

### Service Defaults

```csharp
// MyApp.ServiceDefaults/Extensions.cs
public static class Extensions
{
    public static IHostApplicationBuilder AddServiceDefaults(this IHostApplicationBuilder builder)
    {
        builder.ConfigureOpenTelemetry();
        builder.AddDefaultHealthChecks();
        builder.Services.AddServiceDiscovery();
        builder.Services.ConfigureHttpClientDefaults(http =>
        {
            http.AddStandardResilienceHandler();
            http.AddServiceDiscovery();
        });

        return builder;
    }
}

// Usage in API project
var builder = WebApplication.CreateBuilder(args);
builder.AddServiceDefaults();
builder.AddNpgsqlDbContext<AppDbContext>("mydb");
builder.AddRedisClient("redis");
```

## Cross-References

See [C# Style Guide](csharp.md) for:

- Language-level style (naming, formatting, code organization)
- Roslynator and SonarAnalyzer configuration
- Code coverage and testing patterns
- Advanced C# features (records, pattern matching, etc.)

See [EditorConfig Guide](../configs/editorconfig.md) for:

- Code style configuration
- File formatting rules

See [GitHub Actions Guide](../workflows/github-actions.md) for:

- CI/CD pipeline patterns
- Workflow best practices

See [Docker Guide](../infrastructure/docker.md) for:

- Container best practices
- Multi-stage build optimization

## References

[^1]: [.NET CLI Documentation](https://learn.microsoft.com/en-us/dotnet/core/tools/) - Command-line interface for .NET SDK
[^2]: [Entity Framework Core Tools](https://learn.microsoft.com/en-us/ef/core/cli/dotnet) - dotnet-ef command-line tool for EF Core migrations
[^3]: [dotnet format](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-format) - Code formatter for .NET
[^4]: [ASP.NET Core Documentation](https://learn.microsoft.com/en-us/aspnet/core/) - Web framework for building modern applications
[^5]: [Blazor Documentation](https://learn.microsoft.com/en-us/aspnet/core/blazor/) - Framework for building interactive web UIs with C#
[^6]: [Worker Services](https://learn.microsoft.com/en-us/dotnet/core/extensions/workers) - Background service framework
[^7]: [xUnit.net](https://xunit.net/) - Free, open source testing tool for .NET
[^8]: [NUnit Documentation](https://docs.nunit.org/) - Unit testing framework for .NET
[^9]: [MSTest Documentation](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-with-mstest) - Microsoft's testing framework
[^10]: [Entity Framework Core Documentation](https://learn.microsoft.com/en-us/ef/core/) - Modern object-relational mapper for .NET
[^11]: [WebApplicationFactory](https://learn.microsoft.com/en-us/aspnet/core/test/integration-tests) - Integration testing with ASP.NET Core
[^12]: [Moq Documentation](https://github.com/moq/moq4) - Popular mocking framework for .NET
[^13]: [Verify](https://github.com/VerifyTests/Verify) - Snapshot testing for .NET
[^14]: [BenchmarkDotNet](https://benchmarkdotnet.org/) - Powerful .NET library for benchmarking
[^15]: [Response Caching Middleware](https://learn.microsoft.com/en-us/aspnet/core/performance/caching/middleware) - HTTP response caching in ASP.NET Core
[^16]: [Output Caching](https://learn.microsoft.com/en-us/aspnet/core/performance/caching/output) - Output caching middleware (.NET 7+)
[^17]: [JWT Bearer Authentication](https://learn.microsoft.com/en-us/aspnet/core/security/authentication/) - Authentication and authorization in ASP.NET Core
[^18]: [FluentValidation](https://docs.fluentvalidation.net/) - Popular validation library for .NET
[^19]: [Azure Key Vault](https://learn.microsoft.com/en-us/azure/key-vault/general/overview) - Cloud service for securely storing secrets
[^20]: [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/) - AWS service for managing secrets
[^21]: [Rate Limiting](https://learn.microsoft.com/en-us/aspnet/core/performance/rate-limit) - Rate limiting middleware (.NET 7+)
[^22]: [GitHub Actions](https://docs.github.com/en/actions) - CI/CD platform by GitHub
[^23]: [Docker Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/) - Optimizing Docker images
[^24]: [Docker Compose](https://docs.docker.com/compose/) - Tool for defining multi-container Docker applications
[^25]: [MinVer](https://github.com/adamralph/minver) - Minimalist versioning using Git tags
[^26]: [NuGet Documentation](https://learn.microsoft.com/en-us/nuget/) - Package manager for .NET
[^27]: [Serilog](https://serilog.net/) - Structured logging library for .NET
[^28]: [OpenTelemetry for .NET](https://opentelemetry.io/docs/languages/net/) - Observability framework
[^29]: [Application Insights](https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview) - Application performance management service
[^30]: [.NET Aspire](https://learn.microsoft.com/en-us/dotnet/aspire/) - Cloud-native stack for building distributed applications
