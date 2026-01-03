# Ruby Style Guide

> [Doctrine](../../README.md) > [Languages](../README.md) > Ruby

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

**Target Version**: Ruby 4.0

Based on the [community Ruby Style Guide](https://rubystyle.guide/).

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Lint | StandardRB[^1] | `bundle exec standardrb` |
| Format | StandardRB[^1] | `bundle exec standardrb --fix` |
| Type check | Sorbet[^2] | `bundle exec srb tc` |
| Semantic | Reek[^3] | `bundle exec reek` |
| Dead code | debride[^4] | `bundle exec debride .` |
| Coverage | SimpleCov[^5] | via test suite |
| Complexity | Flog[^6] | `bundle exec flog lib/` |
| Fuzz | - | - |
| Test perf | parallel_tests[^7] | `bundle exec parallel_rspec` |

## Linting & Formatting: StandardRB

Projects **MUST** use StandardRB[^1] for linting and formatting. StandardRB
provides zero-config linting built on RuboCop[^8] and eliminates bikeshedding
debates with sensible defaults.

### Why StandardRB?

StandardRB was chosen over direct RuboCop configuration because it:

- **Eliminates configuration bikeshedding**: Zero-config approach means no team
  debates about style preferences
- **Provides consistency**: Same code style across all Ruby projects in the organization
- **Stays current**: Monthly updates automatically track new RuboCop rules and Ruby best practices
- **Reduces maintenance**: No need to maintain custom RuboCop configuration files
- **Enables team mobility**: Developers can switch between projects without learning new style rules

```bash
# Check
bundle exec standardrb

# Auto-fix
bundle exec standardrb --fix

# Generate todo file for legacy code
bundle exec standardrb --generate-todo
```

### Using RuboCop with StandardRB Base

Teams **MAY** use RuboCop with StandardRB as a base configuration if custom rules are required:

```yaml
# .rubocop.yml
inherit_gem:
  standard: config/base.yml

# Your customizations here
AllCops:
  TargetRubyVersion: 4.0
```

## Type Checking: Sorbet

Projects **SHOULD** use Sorbet[^2] for gradual static typing. Sorbet provides
gradual static typing for Ruby.

### Why Sorbet?

Sorbet was chosen as the type checking solution because it:

- **Gradual adoption**: Can be added incrementally to existing codebases with
  typed levels (false, true, strict, strong)
- **Fast feedback**: Provides near-instant type checking feedback during development
- **Runtime safety**: `sorbet-runtime` catches type errors at runtime when static checks aren't sufficient
- **IDE integration**: Powers autocomplete and navigation in modern editors
- **Battle-tested**: Used in production at Stripe and other large Ruby codebases
- **Active ecosystem**: Tapioca[^9] gem generates RBI files automatically for gems without type signatures

```bash
# Install
bundle add sorbet sorbet-runtime

# Initialize
bundle exec srb init

# Type check
bundle exec srb tc

# Auto-generate RBI files
bundle exec tapioca init
bundle exec tapioca gems
bundle exec tapioca dsl
```

### StandardRB + Sorbet Integration

Projects using Sorbet **MUST** use standard-sorbet[^10] to lint Sorbet signatures with StandardRB:

```ruby
# Gemfile
gem "standard"
gem "standard-sorbet"
gem "sorbet"
gem "sorbet-runtime"
```

```yaml
# .standard.yml
plugins:
  - standard-sorbet
```

This adds RuboCop rules specific to Sorbet signatures, ensuring consistent
formatting of `sig` blocks and proper usage of Sorbet types.

```ruby
# typed: strict
class User
  extend T::Sig

  sig { params(name: String, age: Integer).void }
  def initialize(name, age)
    @name = name
    @age = age
  end

  sig { returns(String) }
  def greeting
    "Hello, #{@name}!"
  end
end
```

## Ruby 4.0 Language Features

### The `it` Keyword (Ruby 3.4+)

Ruby 3.4 introduced the `it` keyword as the default block parameter, providing
a more readable alternative to numbered parameters (`_1`) and explicit block
parameters.

#### Why `it`?

The `it` keyword was introduced because it:

- **Improves readability**: More intuitive than `_1`, especially for developers from other languages
- **Reduces boilerplate**: Eliminates the need for explicit `|param|` syntax in simple blocks
- **Maintains clarity**: Makes the code intention clearer than numbered parameters
- **Language consistency**: Aligns Ruby with modern functional programming conventions

```ruby
# Ruby 4.0+ recommended style
users.map { it.name }
numbers.select { it > 10 }
posts.filter { it.published? }
items.sort_by { it.priority }

# Still valid but less idiomatic now
users.map { _1.name }
users.map { |user| user.name }

# Use explicit parameters when you need multiple or clearer naming
users.each_with_index { |user, index| puts "#{index}: #{user.name}" }
pairs.map { |key, value| "#{key}=#{value}" }
```

Projects **SHOULD** prefer `it` over `_1` for single-parameter blocks in Ruby
4.0+. Explicit parameters **MAY** still be used when parameter naming adds
clarity or when multiple parameters are needed.

### Data Class for Immutable Value Objects (Ruby 3.2+)

The `Data` class provides a lightweight way to create immutable value objects with named attributes.

#### Why Data?

Data classes were introduced because they:

- **Enforce immutability**: All instances are frozen by default, preventing accidental mutations
- **Reduce boilerplate**: Automatic attribute readers, equality, and pattern matching
- **Value semantics**: Equality based on attribute values, not object identity
- **Performance**: More memory-efficient than Struct for immutable data
- **Type safety**: Works seamlessly with pattern matching and deconstruction

```ruby
# Define immutable value object
Point = Data.define(:x, :y)

point = Point.new(1, 2)
point.x  # => 1
point.y  # => 2

# Create modified copy with #with
point2 = point.with(x: 3)  # => Point(x: 3, y: 2)

# Pattern matching support
case point
in Point(x: 0, y: 0)
  puts "Origin"
in Point(x:, y:)
  puts "Point at #{x}, #{y}"
end

# Value equality
Point.new(1, 2) == Point.new(1, 2)  # => true

# Multiple attributes
User = Data.define(:id, :name, :email)
user = User.new(1, "Alice", "alice@example.com")
updated = user.with(email: "newemail@example.com")
```

Projects **SHOULD** use `Data.define` for immutable value objects instead of
`Struct` when immutability is desired. Use `Struct` only when you need mutable
objects.

### Frozen String Literals by Default (Ruby 4.0)

Ruby 4.0 makes frozen string literals the default behavior. All string
literals are now frozen by default, improving performance and preventing
accidental mutations.

#### Why Frozen by Default?

Frozen string literals became the default because they:

- **Improve performance**: Identical frozen strings can share memory
- **Prevent bugs**: Eliminates accidental string mutations
- **Thread safety**: Frozen strings are inherently thread-safe
- **Reduce memory**: String deduplication works automatically
- **Modern best practice**: Aligns with immutability principles

```ruby
# Ruby 4.0: All string literals are frozen by default
name = "Alice"
name.frozen?  # => true

# No longer need magic comment
# frozen_string_literal: true  # Not needed in Ruby 4.0+

# Create mutable strings when needed
mutable_name = String.new("Alice")
mutable_name.frozen?  # => false

# Or use unary plus operator
mutable_name = +"Alice"
mutable_name.frozen?  # => false
mutable_name << " Smith"  # Works

# Concatenation creates new frozen strings
greeting = "Hello, " + name  # => "Hello, Alice" (frozen)

# String interpolation creates frozen strings
message = "User: #{name}"
message.frozen?  # => true
```

Projects **MUST** remove `# frozen_string_literal: true` magic comments in Ruby
4.0+. When mutable strings are needed, **MUST** use `String.new` or the unary
plus operator `+`.

### Set as Core Class (Ruby 3.2+)

The `Set` class is now built into Ruby core, eliminating the need to `require 'set'`.

```ruby
# Ruby 3.2+: Set is built-in, no require needed
set = Set[1, 2, 3]
set.add(4)
set.include?(2)  # => true

# Set operations
set1 = Set[1, 2, 3]
set2 = Set[2, 3, 4]
set1 | set2  # => Set[1, 2, 3, 4] (union)
set1 & set2  # => Set[2, 3] (intersection)
set1 - set2  # => Set[1] (difference)
```

Projects **MUST NOT** use `require 'set'` in Ruby 3.2+, as `Set` is now a core class.

### Pathname as Core Class (Ruby 4.0)

The `Pathname` class is now built into Ruby core, eliminating the need to `require 'pathname'`.

```ruby
# Ruby 4.0: Pathname is built-in, no require needed
path = Pathname.new("/usr/local/bin")
path.directory?     # => true
path.children       # => [Pathname:/usr/local/bin/ruby, ...]

# Path manipulation
config = Pathname.new("/app") / "config" / "database.yml"
config.to_s         # => "/app/config/database.yml"
config.basename     # => Pathname:database.yml
config.dirname      # => Pathname:/app/config
config.extname      # => ".yml"

# Reading and writing
path.read           # Read file contents
path.write("data")  # Write to file
path.exist?         # Check existence
```

Projects **MUST NOT** use `require 'pathname'` in Ruby 4.0+, as `Pathname` is now a core class.

### Array#find and Array#rfind (Ruby 4.0)

Ruby 4.0 adds `Array#find` and `Array#rfind` as optimized alternatives to `Enumerable#find` and `Enumerable#reverse_each.find`.

#### Why Array#find?

These methods were added because they:

- **Improve performance**: Native Array implementation is faster than Enumerable
- **Provide symmetry**: `rfind` searches from the end without creating a reversed copy
- **Reduce allocations**: No intermediate enumerator objects needed

```ruby
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Find first match (searches from beginning)
numbers.find { it > 5 }   # => 6

# Find last match (searches from end)
numbers.rfind { it < 5 }  # => 4

# With default value
numbers.find(0) { it > 100 }   # => 0
numbers.rfind(0) { it > 100 }  # => 0

# Practical example: find most recent valid record
logs = [log1, log2, log3, log4]
logs.rfind { it.valid? }  # Efficiently finds last valid log
```

Projects **SHOULD** prefer `Array#find` and `Array#rfind` over
`Enumerable#find` when working with arrays in Ruby 4.0+.

### String#strip with Selectors (Ruby 4.0)

Ruby 4.0 extends `String#strip`, `#lstrip`, and `#rstrip` to accept selector
arguments for custom character stripping.

```ruby
# Default behavior (whitespace)
"  hello  ".strip     # => "hello"

# Strip specific characters
"###hello###".strip("#")           # => "hello"
"...hello...".strip(".")           # => "hello"
"##--hello--##".strip("#", "-")    # => "hello"

# Left and right variants
"###hello".lstrip("#")             # => "hello"
"hello###".rstrip("#")             # => "hello"

# Strip character classes
"123hello456".strip("0-9")         # => "hello"
"AAAhelloBBB".strip("A-Z")         # => "hello"

# Combine with other operations
csv_value = "  \"hello\"  "
csv_value.strip.strip("\"")        # => "hello"
```

Projects **MAY** use the selector arguments to `strip`, `lstrip`, and `rstrip`
when custom character removal is needed.

### Prism Parser (Ruby 3.4+)

Prism is the new default parser in Ruby 3.4+, replacing the legacy Ripper parser.

#### Why Prism?

Prism was introduced because it:

- **Faster parsing**: Significantly improved parsing performance
- **Better error messages**: More helpful syntax error diagnostics
- **Consistent AST**: Unified abstract syntax tree representation
- **Portable**: Pure Ruby implementation works across platforms
- **Maintainable**: Cleaner codebase for future Ruby development

Projects using Ruby 3.4+ automatically benefit from Prism. No configuration changes are needed.

### YJIT Performance (Ruby 3.3+)

YJIT (Yet another Ruby JIT) is enabled by default in Ruby 3.3+, providing significant performance improvements.

#### Why YJIT?

YJIT provides:

- **20-40% performance improvement**: Real-world Rails applications see significant speedups
- **Low memory overhead**: Minimal memory cost compared to performance gains
- **Production-ready**: Stable and tested in production at Shopify
- **Zero configuration**: Enabled by default, works transparently

```bash
# YJIT is enabled by default in Ruby 3.3+
ruby --yjit script.rb  # Explicitly enable (redundant in 3.3+)

# Check YJIT stats
ruby --yjit-stats script.rb

# Disable YJIT if needed
ruby --disable-yjit script.rb
```

#### ZJIT Experimental (Ruby 4.0)

Ruby 4.0 introduces ZJIT as an experimental alternative JIT compiler.

```bash
# Enable experimental ZJIT
ruby --zjit script.rb

# ZJIT with aggressive optimizations
ruby --zjit --zjit-max-versions=10 script.rb
```

Projects **SHOULD** use default YJIT in production. ZJIT **MAY** be evaluated
for specific performance-critical workloads but is not recommended for general
use.

### Ractor Improvements (Ruby 4.0)

Ruby 4.0 introduces significant changes to the Ractor API for better actor-based concurrency.

#### Ractor::Port for Message Passing

The new `Ractor::Port` class provides a cleaner synchronization mechanism:

```ruby
# Ruby 4.0: Using Ractor::Port
port = Ractor::Port.new

worker = Ractor.new(port) do |p|
  result = expensive_computation
  p.send(result)
end

# Receive from port
result = port.receive

# Close when done
port.close
```

#### Ractor#join and Ractor#value

New methods for waiting on Ractor completion:

```ruby
# Wait for Ractor to terminate
worker = Ractor.new { compute_something }
worker.join  # Blocks until completion

# Get the return value
worker = Ractor.new { 42 }
worker.value  # => 42 (blocks until complete, returns result)

# Practical pattern: parallel computation
ractors = data_chunks.map do |chunk|
  Ractor.new(chunk) { |c| process(c) }
end

results = ractors.map(&:value)  # Collect all results
```

#### Removed Ractor Methods

The following methods were **removed** in Ruby 4.0:

- `Ractor.yield` - Use `Ractor::Port#send` instead
- `Ractor#take` - Use `Ractor#value` or `Ractor::Port#receive` instead
- `Ractor#close_incoming` - Use `Ractor::Port#close` instead
- `Ractor#close_outgoing` - Use `Ractor::Port#close` instead

```ruby
# Ruby 3.x (deprecated)
r = Ractor.new { Ractor.yield(42) }
r.take  # => 42

# Ruby 4.0 (recommended)
port = Ractor::Port.new
r = Ractor.new(port) { |p| p.send(42) }
port.receive  # => 42
```

Projects using Ractors **MUST** migrate from the removed methods to the new
`Ractor::Port` API.

## Ruby 4.0 Breaking Changes

### Removed Features

Ruby 4.0 removes several deprecated features. Projects **MUST** update code
using these features before upgrading.

| Removed | Migration |
| ------- | --------- |
| `--rjit` option | Use `--yjit` (default) or experimental `--zjit` |
| `CGI` library (most of it) | Only `cgi/escape` retained; use `Rack` or `rack-utils` for CGI functionality |
| `SortedSet` autoload | Add `gem 'sorted_set'` to Gemfile |
| `Process::Status#&` | Use `Process::Status#to_i & value` |
| `Process::Status#>>` | Use `Process::Status#to_i >> value` |
| `ObjectSpace._id2ref` | Deprecated; avoid relying on object IDs |

### Changed Behaviors

```ruby
# *nil no longer calls nil.to_a (aligns with **nil)
# Ruby 3.x: *nil => []
# Ruby 4.0: *nil => raises TypeError

# Use explicit conversion if needed
values = nil
args = values&.to_a || []

# Binding#local_variables excludes numbered parameters
binding.local_variables  # No longer includes _1, _2, etc.

# Proc#parameters shows anonymous optionals differently
proc { |a = 1| }.parameters
# Ruby 3.x: [[:opt, nil]]
# Ruby 4.0: [[:opt]]
```

### Unicode 17.0.0

Ruby 4.0 updates to Unicode 17.0.0. This may affect:

- String comparison and sorting
- Regular expression character classes
- Case conversion methods

Projects handling internationalized text **SHOULD** test Unicode-dependent
functionality after upgrading.

## Time Zone Handling

Projects **MUST** use time zone-aware methods when working with dates and
times. Using `Time.now` instead of `Time.zone.now` is a common source of
production bugs.

### Why Time Zones Matter

- **Silent failures**: `Time.now` uses system time zone, not application time zone
- **Inconsistent data**: Database stores UTC, but queries use local time
- **User confusion**: Timestamps display incorrectly across time zones
- **Testing brittleness**: Tests pass locally but fail in CI (different time zones)

### Time Zone Rules

```ruby
# BAD: Ignores configured time zone
Time.now
Date.today
DateTime.now

# GOOD: Uses application time zone
Time.current          # or Time.zone.now
Date.current          # or Time.zone.today
DateTime.current

# BAD: Parses in system time zone
Time.parse("2024-01-15 10:00:00")

# GOOD: Parses in application time zone
Time.zone.parse("2024-01-15 10:00:00")
```

### Database Queries

```ruby
# BAD: Uses system time, may miss records
User.where("created_at > ?", Time.now - 1.day)

# GOOD: Uses application time zone
User.where("created_at > ?", 1.day.ago)
User.where(created_at: 1.day.ago..)

# GOOD: For date ranges
User.where(created_at: Date.current.all_day)
User.where(created_at: Date.current.beginning_of_day..Date.current.end_of_day)
```

### Configuration

```ruby
# config/application.rb
config.time_zone = "America/New_York"

# Store all times in UTC in the database (default, recommended)
config.active_record.default_timezone = :utc
```

### Testing Time-Dependent Code

```ruby
RSpec.describe Subscription do
  it "expires after 30 days" do
    # Use travel_to for deterministic time tests
    travel_to Time.zone.parse("2024-01-15 12:00:00") do
      subscription = Subscription.create!

      travel 29.days
      expect(subscription).not_to be_expired

      travel 2.days
      expect(subscription).to be_expired
    end
  end
end
```

## Semantic Analysis: Reek

Projects **SHOULD** use Reek[^3] for semantic analysis and code smell detection.

```bash
bundle exec reek lib/
```

```yaml
# .reek.yml
detectors:
  TooManyStatements:
    max_statements: 10
  UtilityFunction:
    enabled: false
```

## Dead Code Detection: debride

Projects **MAY** use debride[^4] to detect unused methods and dead code.

```bash
# Install
gem install debride

# Find unused methods
debride .
debride lib/ app/

# With Rails
debride-rails .
```

## Code Coverage: SimpleCov

Projects **MUST** use SimpleCov[^5] for code coverage tracking.

```ruby
# spec/spec_helper.rb or test/test_helper.rb
require 'simplecov'
SimpleCov.start do
  add_filter '/spec/'
  add_filter '/test/'
  minimum_coverage 80  # Projects SHOULD maintain at least 80% coverage
  enable_coverage :branch  # Branch coverage MUST be enabled
end
```

```bash
# Run tests to generate coverage
bundle exec rspec
# Coverage report in coverage/index.html
```

RSpec[^17] is the recommended testing framework for Ruby projects.

## Cyclomatic Complexity: Flog

Projects **SHOULD** use Flog[^6] to measure and control code complexity (higher
scores indicate more complex code).

```bash
bundle exec flog lib/

# Show only methods above threshold
bundle exec flog -a lib/ | head -20

# Fail if average exceeds threshold
bundle exec flog -a lib/ -t 10
```

Guidelines:

- 0-10: Ideal
- 11-20: Might need refactoring
- 21-40: Consider refactoring
- 40+: Definitely refactor

## Test Performance: parallel_tests

Projects **SHOULD** use parallel_tests[^7] to speed up test suite execution.

```bash
# Install
bundle add parallel_tests --group development, test

# RSpec
bundle exec parallel_rspec spec/

# Minitest[^29]
bundle exec parallel_test test/

# With specific count
bundle exec parallel_rspec -n 4 spec/
```

### Database Setup for Parallel Tests

```ruby
# config/database.yml
test:
  database: myapp_test<%= ENV['TEST_ENV_NUMBER'] %>
```

```bash
# Create parallel databases
bundle exec rake parallel:create
bundle exec rake parallel:prepare
```

### Spring (Preloader)

```bash
# Gemfile
gem 'spring', group: :development
gem 'spring-commands-rspec', group: :development

# Use spring
bundle exec spring rspec spec/
```

Projects **MAY** use Spring[^18] to preload the application and speed up development.

## Pre-commit Configuration

Projects **SHOULD** configure pre-commit hooks to catch issues before commit.

```yaml
repos:
  - repo: https://github.com/standardrb/standard
    rev: v1.43.0
    hooks:
      - id: standardrb

  - repo: local
    hooks:
      - id: reek
        name: Reek
        entry: bundle exec reek
        language: system
        types: [ruby]
```

## CI Pipeline

Projects **MUST** include linting and testing in their CI pipeline.

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ruby/setup-ruby@v1
        with:
          bundler-cache: true
      - run: bundle exec standardrb

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ruby/setup-ruby@v1[^26]
        with:
          bundler-cache: true
      - run: bundle exec parallel_rspec
      - uses: codecov/codecov-action@v4[^27]
```

## Dependencies & Package Management

Projects **MUST** use Bundler[^11] for dependency management. Bundler manages
Ruby dependencies and ensures consistent environments.

```bash
# Install dependencies
bundle install

# Update all gems
bundle update

# Update specific gem
bundle update rails

# Check for vulnerabilities
bundle audit check --update
```

### Gemfile.lock

Projects **MUST** commit `Gemfile.lock` to version control. It ensures
identical gem versions across environments.

### Version Constraints

```ruby
# Gemfile
gem "rails", "~> 7.1.0"      # >= 7.1.0 and < 7.2.0
gem "rspec", ">= 3.12"       # Any version >= 3.12
gem "pg", "1.5.4"            # Exact version
gem "puma", "~> 6.0"         # >= 6.0 and < 7.0
```

### Vulnerability Scanning

Projects **MUST** use bundler-audit[^12] for vulnerability scanning.

```bash
# Install bundler-audit
gem install bundler-audit

# Update vulnerability database
bundle audit update

# Check for vulnerabilities
bundle audit check
```

### Dependabot Configuration

Projects **SHOULD** configure Dependabot[^13] for automated dependency updates.

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "bundler"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    groups:
      development-dependencies:
        dependency-type: "development"
```

## E2E & Acceptance Testing

### Capybara for Browser Testing

Projects with web interfaces **SHOULD** use Capybara[^14] for browser-based acceptance testing.

```ruby
# Gemfile
gem "capybara", group: :test
gem "selenium-webdriver", group: :test[^28]

# spec/spec_helper.rb
require "capybara/rspec"

Capybara.default_driver = :selenium_chrome_headless
```

```ruby
# spec/features/user_login_spec.rb
RSpec.feature "User login" do
  scenario "successful login" do
    visit "/login"
    fill_in "Email", with: "user@example.com"
    fill_in "Password", with: "password"
    click_button "Log in"

    expect(page).to have_content("Welcome back")
  end
end
```

### Cucumber for BDD Acceptance Tests

Projects **MAY** use Cucumber[^15] for behavior-driven development acceptance
tests when business stakeholders need readable specifications.

```ruby
# Gemfile
gem "cucumber-rails", group: :test

# features/login.feature
Feature: User Login
  Scenario: Successful login
    Given I am on the login page
    When I enter valid credentials
    Then I should see the dashboard
```

```ruby
# features/step_definitions/login_steps.rb
Given("I am on the login page") do
  visit login_path
end

When("I enter valid credentials") do
  fill_in "Email", with: "user@example.com"
  fill_in "Password", with: "password"
  click_button "Log in"
end

Then("I should see the dashboard") do
  expect(page).to have_current_path(dashboard_path)
end
```

### Page Object Pattern

Projects with complex UI test suites **SHOULD** use the Page Object pattern to improve maintainability.

```ruby
# spec/support/pages/login_page.rb
class LoginPage
  include Capybara::DSL

  def visit_page
    visit "/login"
  end

  def login(email, password)
    fill_in "Email", with: email
    fill_in "Password", with: password
    click_button "Log in"
  end

  def error_message
    find(".error").text
  end
end

# spec/features/login_spec.rb
RSpec.feature "Login" do
  let(:page_object) { LoginPage.new }

  scenario "with invalid credentials" do
    page_object.visit_page
    page_object.login("wrong@example.com", "wrong")
    expect(page_object.error_message).to eq("Invalid credentials")
  end
end
```

## Thread Safety Testing

### Testing with Threads

```ruby
RSpec.describe Counter do
  it "increments safely across threads" do
    counter = Counter.new
    threads = 100.times.map do
      Thread.new { 100.times { counter.increment } }
    end
    threads.each(&:join)

    expect(counter.value).to eq(10_000)
  end
end
```

### Mutex and Synchronization Testing

```ruby
class ThreadSafeCache
  def initialize
    @cache = {}
    @mutex = Mutex.new
  end

  def fetch(key)
    @mutex.synchronize { @cache[key] }
  end

  def set(key, value)
    @mutex.synchronize { @cache[key] = value }
  end
end

RSpec.describe ThreadSafeCache do
  it "handles concurrent writes" do
    cache = ThreadSafeCache.new
    threads = 10.times.map do |i|
      Thread.new { cache.set("key#{i}", i) }
    end
    threads.each(&:join)

    expect(cache.fetch("key5")).to eq(5)
  end
end
```

### parallel_tests Considerations

Projects **MAY** use DatabaseCleaner[^25] for managing database state in tests.

```ruby
# spec/spec_helper.rb
RSpec.configure do |config|
  # Isolate database transactions per thread
  config.use_transactional_fixtures = true

  # Ensure thread safety in shared resources
  config.before(:suite) do
    DatabaseCleaner.strategy = :transaction
  end
end
```

## Idempotence Testing

### Testing Retry-Safe Operations

```ruby
RSpec.describe PaymentProcessor do
  it "processes payment only once despite retries" do
    processor = PaymentProcessor.new
    payment_id = "pay_123"

    # First attempt
    result1 = processor.process(payment_id, amount: 100)
    expect(result1).to be_success

    # Retry with same ID should be idempotent
    result2 = processor.process(payment_id, amount: 100)
    expect(result2).to be_success
    expect(Payment.where(id: payment_id).count).to eq(1)
  end
end
```

### Sidekiq Job Idempotence

Projects **SHOULD** use Sidekiq[^24] for background job processing.

```ruby
class SendEmailJob
  include Sidekiq::Job

  sidekiq_options retry: 3

  def perform(user_id, email_type)
    # Use idempotency key to prevent duplicate sends
    key = "email:#{user_id}:#{email_type}"
    return if Rails.cache.read(key)

    send_email(user_id, email_type)
    Rails.cache.write(key, true, expires_in: 1.hour)
  end
end

RSpec.describe SendEmailJob do
  it "sends email only once when retried" do
    expect {
      3.times { SendEmailJob.new.perform(1, "welcome") }
    }.to change { ActionMailer::Base.deliveries.count }.by(1)
  end
end
```

## Reliability & Resilience Testing

### Toxiproxy for Fault Injection

Projects **MAY** use Toxiproxy[^19] for fault injection testing to simulate network failures and latency.

```ruby
# Gemfile
gem "toxiproxy", group: :test

# spec/spec_helper.rb
require "toxiproxy"

RSpec.configure do |config|
  config.before(:suite) do
    Toxiproxy.populate([
      {
        name: "redis",
        listen: "127.0.0.1:22222",
        upstream: "127.0.0.1:6379"
      }
    ])
  end
end
```

```ruby
RSpec.describe CacheService do
  it "handles redis timeout gracefully" do
    Toxiproxy[:redis].downstream(:timeout, timeout: 100).apply do
      result = CacheService.fetch("key")
      expect(result).to be_nil  # Graceful degradation
    end
  end

  it "retries on network latency" do
    Toxiproxy[:redis].downstream(:latency, latency: 500).apply do
      expect { CacheService.fetch("key") }.not_to raise_error
    end
  end
end
```

### Testing Circuit Breakers (Semian)

Projects **MAY** use Semian[^20] for circuit breaker and bulkhead patterns.

```ruby
# Gemfile
gem "semian"

class ApiClient
  include Semian::Resource

  semian_configuration(
    name: :api_client,
    tickets: 10,
    error_threshold: 3,
    error_timeout: 10,
    success_threshold: 2
  )
end

RSpec.describe ApiClient do
  it "opens circuit after threshold failures" do
    client = ApiClient.new

    # Trigger failures
    3.times { expect { client.fetch }.to raise_error(ApiError) }

    # Circuit should be open
    expect { client.fetch }.to raise_error(Semian::OpenCircuitError)
  end

  it "closes circuit after successful requests" do
    client = ApiClient.new

    # Open circuit, wait for timeout, then succeed
    3.times { client.fetch rescue nil }
    sleep 11
    2.times { client.fetch }  # Success threshold

    expect { client.fetch }.not_to raise_error(Semian::OpenCircuitError)
  end
end
```

## Compatibility Testing

### Testing Across Ruby Versions with CI Matrix

```yaml
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        ruby: ["3.3", "3.4", "4.0"]
    steps:
      - uses: actions/checkout@v4
      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: ${{ matrix.ruby }}
          bundler-cache: true
      - run: bundle exec rspec
```

### Appraisal Gem for Gem Version Testing

Projects **MAY** use Appraisal[^21] to test against multiple gem versions.

```ruby
# Gemfile
gem "appraisal", group: :development

# Appraisals file
appraise "rails-7.0" do
  gem "rails", "~> 7.0.0"
end

appraise "rails-7.1" do
  gem "rails", "~> 7.1.0"
end
```

```bash
# Generate gemfiles
bundle exec appraisal install

# Test against all versions
bundle exec appraisal rspec

# Test specific version
bundle exec appraisal rails-7.0 rspec
```

## Internationalization Testing

### UTF-8 String Handling

```ruby
RSpec.describe TextProcessor do
  it "handles UTF-8 characters correctly" do
    text = "Hello 世界 🌍"
    result = TextProcessor.truncate(text, length: 10)

    expect(result.encoding).to eq(Encoding::UTF_8)
    expect(result.length).to be <= 10
  end

  it "normalizes unicode strings" do
    # é can be represented as e + combining accent or single character
    str1 = "café"  # Single character é
    str2 = "café"  # e + combining accent

    expect(TextProcessor.normalize(str1)).to eq(TextProcessor.normalize(str2))
  end
end
```

### I18n Gem Testing

Projects **SHOULD** use the I18n gem[^22] for internationalization.

```ruby
# config/locales/en.yml
en:
  greeting: "Hello, %{name}!"

# config/locales/es.yml
es:
  greeting: "¡Hola, %{name}!"
```

```ruby
RSpec.describe Greeter do
  it "translates greetings" do
    I18n.with_locale(:en) do
      expect(Greeter.greet("Alice")).to eq("Hello, Alice!")
    end

    I18n.with_locale(:es) do
      expect(Greeter.greet("Alice")).to eq("¡Hola, Alice!")
    end
  end
end
```

### Locale Switching Tests

```ruby
RSpec.describe LocaleMiddleware do
  it "switches locale based on header" do
    get "/", headers: { "Accept-Language" => "es" }
    expect(response.body).to include("¡Hola!")

    get "/", headers: { "Accept-Language" => "en" }
    expect(response.body).to include("Hello!")
  end

  it "falls back to default locale" do
    get "/", headers: { "Accept-Language" => "invalid" }
    expect(I18n.locale).to eq(I18n.default_locale)
  end
end
```

## Data Integrity Testing

### ActiveRecord Validation Testing

Projects using Rails **SHOULD** use ActiveRecord[^23] for database interactions and validations.

```ruby
RSpec.describe User do
  it "validates presence of email" do
    user = User.new(email: nil)
    expect(user).not_to be_valid
    expect(user.errors[:email]).to include("can't be blank")
  end

  it "validates uniqueness of email" do
    User.create!(email: "test@example.com", name: "Test")
    duplicate = User.new(email: "test@example.com", name: "Duplicate")

    expect(duplicate).not_to be_valid
    expect(duplicate.errors[:email]).to include("has already been taken")
  end

  it "validates custom business rules" do
    user = User.new(age: 15, can_vote: true)
    expect(user).not_to be_valid
    expect(user.errors[:can_vote]).to include("requires age 18+")
  end
end
```

### Migration Testing

```ruby
# spec/migrations/add_email_to_users_spec.rb
require "rails_helper"
require_relative "../../db/migrate/20250101000000_add_email_to_users"

RSpec.describe AddEmailToUsers do
  let(:migration) { described_class.new }

  it "adds email column" do
    migration.migrate(:up)
    expect(User.column_names).to include("email")
  end

  it "is reversible" do
    migration.migrate(:up)
    migration.migrate(:down)
    expect(User.column_names).not_to include("email")
  end

  it "migrates existing data" do
    # Create legacy data
    user = User.create!(username: "test")

    migration.migrate(:up)
    user.reload

    expect(user.email).to eq("test@example.com")
  end
end
```

## A/B Testing & Feature Flags

### Flipper Gem

Projects **SHOULD** use Flipper[^16] for feature flags and A/B testing.

```ruby
# Gemfile
gem "flipper"
gem "flipper-active_record"
gem "flipper-ui"

# config/initializers/flipper.rb
require "flipper/adapters/active_record"

Flipper.configure do |config|
  config.adapter { Flipper::Adapters::ActiveRecord.new }
end
```

```ruby
# Enable feature for percentage of users
Flipper[:new_dashboard].enable_percentage_of_actors(25)

# Enable for specific users
Flipper[:beta_features].enable_actor(user)

# Enable for groups
Flipper.register(:admins) { |actor| actor.admin? }
Flipper[:admin_panel].enable_group(:admins)
```

### Testing Both Flag States

Feature flag tests **MUST** verify behavior in both enabled and disabled states.

```ruby
RSpec.describe DashboardController do
  describe "GET #index" do
    context "with new_dashboard enabled" do
      before { Flipper[:new_dashboard].enable }

      it "renders new dashboard" do
        get :index
        expect(response).to render_template("dashboard/new")
      end
    end

    context "with new_dashboard disabled" do
      before { Flipper[:new_dashboard].disable }

      it "renders old dashboard" do
        get :index
        expect(response).to render_template("dashboard/old")
      end
    end
  end
end
```

```ruby
RSpec.describe User do
  describe "#can_access_beta?" do
    let(:user) { User.create!(email: "test@example.com") }

    it "returns true when enabled for user" do
      Flipper[:beta_features].enable_actor(user)
      expect(user.can_access_beta?).to be true
    end

    it "returns false when disabled" do
      Flipper[:beta_features].disable
      expect(user.can_access_beta?).to be false
    end

    it "returns true for percentage rollout" do
      Flipper[:beta_features].enable_percentage_of_actors(100)
      expect(user.can_access_beta?).to be true
    end
  end
end
```

## References

[^1]: [StandardRB](https://github.com/standardrb/standard) - Ruby style guide, linter, and formatter
[^2]: [Sorbet](https://sorbet.org/) - A fast, powerful type checker designed for Ruby
[^3]: [Reek](https://github.com/troessner/reek) - Code smell detector for Ruby
[^4]: [debride](https://github.com/seattlerb/debride) - Analyze code for potentially uncalled / dead methods
[^5]: [SimpleCov](https://github.com/simplecov-ruby/simplecov) - Code coverage analysis tool for Ruby
[^6]: [Flog](https://github.com/seattlerb/flog) - Reports the most tortured code in an easy to read pain report
[^7]: [parallel_tests](https://github.com/grosser/parallel_tests) - Speedup Test::Unit + RSpec + Cucumber by running parallel on multiple CPU cores
[^8]: [RuboCop](https://rubocop.org/) - A Ruby static code analyzer and formatter
[^9]: [Tapioca](https://github.com/Shopify/tapioca) - The swiss army knife of RBI generation
[^10]: [standard-sorbet](https://github.com/standardrb/standard-sorbet) - Sorbet rules for Standard Ruby
[^11]: [Bundler](https://bundler.io/) - The best way to manage a Ruby application's gems
[^12]: [bundler-audit](https://github.com/rubysec/bundler-audit) - Patch-level verification for Bundler
[^13]: [Dependabot](https://github.com/dependabot) - Automated dependency updates
[^14]: [Capybara](https://github.com/teamcapybara/capybara) - Acceptance test framework for web applications
[^15]: [Cucumber](https://cucumber.io/) - BDD tool for Ruby
[^16]: [Flipper](https://github.com/flippercloud/flipper) - Feature flags for Ruby
[^17]: [RSpec](https://rspec.info/) - Behaviour Driven Development for Ruby
[^18]: [Spring](https://github.com/rails/spring) - Application preloader for Rails
[^19]: [Toxiproxy](https://github.com/Shopify/toxiproxy) - A TCP proxy to simulate network and system conditions for chaos and resiliency testing
[^20]: [Semian](https://github.com/Shopify/semian) - Resiliency toolkit for Ruby
[^21]: [Appraisal](https://github.com/thoughtbot/appraisal) - A library for testing your library against different versions of dependencies
[^22]: [I18n](https://guides.rubyonrails.org/i18n.html) - Ruby Internationalization and localization solution
[^23]: [ActiveRecord](https://guides.rubyonrails.org/active_record_basics.html) - Object-Relational Mapping (ORM) in Rails
[^24]: [Sidekiq](https://sidekiq.org/) - Simple, efficient background processing for Ruby
[^25]: [DatabaseCleaner](https://github.com/DatabaseCleaner/database_cleaner) - Strategies for cleaning databases in Ruby
[^26]: [ruby/setup-ruby](https://github.com/ruby/setup-ruby) - GitHub Action to set up Ruby, JRuby, and TruffleRuby
[^27]: [Codecov](https://about.codecov.io/) - Code coverage reporting and analytics
[^28]: [Selenium WebDriver](https://www.selenium.dev/documentation/webdriver/) - Browser automation framework
[^29]: [Minitest](https://github.com/minitest/minitest) - A complete suite of testing facilities supporting TDD, BDD, mocking, and benchmarking

## See Also

- [Rails Guide](../frameworks/rails.md) - Ruby on Rails specific conventions and tooling
- [Sinatra Guide](../frameworks/sinatra.md) - Lightweight DSL for simple APIs and microservices
- [Hanami Guide](../frameworks/hanami.md) - Clean architecture web framework
- [Testing Guide](../process/testing.md) - General testing practices and strategies
- [CI Guide](../process/ci.md) - Continuous integration setup and best practices
