# Rails Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > Rails

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.txt).

Extends [Ruby style guide](ruby.md) with Rails-specific conventions from
[Rails Style Guide](https://rails.rubystyle.guide/).

**Target Version**: Rails 8.1+ with Ruby 3.4

## Quick Reference

All Ruby tooling applies. Additional tools are **REQUIRED**:

| Task | Tool | Command |
|------|------|---------|
| Lint | StandardRB[^1] + standard-rails[^2] | `bundle exec standardrb` |
| Security | Brakeman[^3] | `bundle exec brakeman` |
| Test | RSpec Rails[^4] | `bundle exec rspec` |
| Coverage | SimpleCov[^5] | via test suite |

## StandardRB for Rails

Rails projects **MUST** use StandardRB[^1] with the standard-rails[^2] plugin for linting.

```ruby
# Gemfile
group :development, :test do
  gem "standard"
  gem "standard-rails"
  gem "standard-sorbet"  # If using Sorbet
end
```

```yaml
# .standard.yml
plugins:
  - standard-rails
  - standard-sorbet  # If using Sorbet
```

The standard-rails[^2] plugin adds
Rails-specific RuboCop rules. You **SHOULD** add
standard-sorbet[^6] if your Rails
app uses Sorbet[^7] for type checking.

**Why StandardRB?** StandardRB eliminates style debates with zero configuration. The standard-rails plugin extends this philosophy to Rails idioms, catching common anti-patterns like N+1 queries and improper use of callbacks while maintaining zero-config simplicity.

## Project Structure

Rails projects **SHOULD** organize code using this structure:

```
app/
├── controllers/
├── models/
├── views/
├── services/          # Business logic
├── queries/           # Complex queries
├── serializers/       # JSON serialization
└── validators/        # Custom validators
```

Service objects **SHOULD** be used for complex business logic. Query objects **MAY** be used for complex database queries that don't belong in models.

## Models

### Field Order

Model declarations **MUST** follow this order:

```ruby
class User < ApplicationRecord
  # 1. Associations
  belongs_to :organization
  has_many :posts, dependent: :destroy
  has_one :profile, dependent: :destroy

  # 2. Validations
  validates :email, presence: true, uniqueness: true
  validates :name, presence: true, length: {maximum: 255}

  # 3. Callbacks (use sparingly)
  before_save :normalize_email

  # 4. Scopes
  scope :active, -> { where(active: true) }
  scope :recent, -> { order(created_at: :desc) }

  # 5. Class methods
  def self.find_by_email(email)
    find_by(email: email.downcase)
  end

  # 6. Instance methods
  def full_name
    "#{first_name} #{last_name}"
  end

  private

  def normalize_email
    self.email = email.downcase.strip
  end
end
```

### Associations

```ruby
# You MUST always specify dependent option for has_many/has_one
has_many :posts, dependent: :destroy
has_one :profile, dependent: :destroy

# You SHOULD use inverse_of for bi-directional associations
has_many :comments, inverse_of: :post
belongs_to :post, inverse_of: :comments
```

### Validations

```ruby
# You MUST use validates with hash syntax
validates :email, presence: true, uniqueness: {case_sensitive: false}

# You MUST validate boolean columns
validates :active, inclusion: {in: [true, false]}

# You MUST use database constraints for NOT NULL, unique indexes
```

## Controllers

### Thin Controllers

Controllers **MUST** be thin. Business logic **MUST** be extracted to service objects.

```ruby
# BAD
class OrdersController < ApplicationController
  def create
    @order = Order.new(order_params)
    @order.user = current_user
    @order.calculate_total
    @order.apply_discount(params[:discount_code])
    if @order.save
      OrderMailer.confirmation(@order).deliver_later
      redirect_to @order
    else
      render :new
    end
  end
end

# GOOD
class OrdersController < ApplicationController
  def create
    @order = Orders::CreateService.call(
      user: current_user,
      params: order_params,
      discount_code: params[:discount_code]
    )
    redirect_to @order
  rescue Orders::CreateService::Error => e
    @order = e.order
    flash.now[:error] = e.message
    render :new, status: :unprocessable_entity
  end
end
```

**Why Service Objects?** Thin controllers improve testability by isolating business logic from HTTP concerns. Service objects are easier to test in isolation and can be reused across controllers, jobs, and rake tasks.

### Strong Parameters

Controllers **MUST** use strong parameters to prevent mass assignment vulnerabilities.

```ruby
private

def order_params
  params.require(:order).permit(:product_id, :quantity, :notes)
end
```

## Services

```ruby
# app/services/orders/create_service.rb
module Orders
  class CreateService
    class Error < StandardError
      attr_reader :order
      def initialize(message, order:)
        super(message)
        @order = order
      end
    end

    def self.call(...)
      new(...).call
    end

    def initialize(user:, params:, discount_code: nil)
      @user = user
      @params = params
      @discount_code = discount_code
    end

    def call
      order = build_order
      apply_discount(order)
      save_order!(order)
      send_confirmation(order)
      order
    end

    private

    attr_reader :user, :params, :discount_code

    def build_order
      Order.new(params.merge(user: user))
    end

    def apply_discount(order)
      return unless discount_code
      order.apply_discount(discount_code)
    end

    def save_order!(order)
      return if order.save
      raise Error.new(order.errors.full_messages.join(", "), order: order)
    end

    def send_confirmation(order)
      OrderMailer.confirmation(order).deliver_later
    end
  end
end
```

## Authentication (Rails 8+)

Projects **SHOULD** use the built-in authentication generator for new applications:

```bash
bin/rails generate authentication
```

This generates:
- `User` model with `has_secure_password`
- `Session` model for session tracking
- `SessionsController` for login/logout
- Password reset flow with secure tokens
- Current session helpers

```ruby
# Generated authentication provides:
class User < ApplicationRecord
  has_secure_password
  has_many :sessions, dependent: :destroy

  normalizes :email_address, with: ->(e) { e.strip.downcase }
end

# In controllers:
class ApplicationController < ActionController::Base
  include Authentication
end

# Usage in views:
<% if authenticated? %>
  Logged in as <%= Current.user.email_address %>
<% end %>
```

**Why**: Rails 8's authentication generator provides secure defaults including session tracking, password resets, and rate limiting without third-party gems like Devise.

## Background Jobs: Solid Queue (Rails 8+)

Projects **SHOULD** use Solid Queue[^21] instead of Sidekiq for most background job processing:

```ruby
# Gemfile (included by default in Rails 8+)
gem "solid_queue"

# config/database.yml
production:
  primary:
    <<: *default
    database: myapp_production
  queue:
    <<: *default
    database: myapp_queue
    migrations_paths: db/queue_migrate
```

```ruby
# app/jobs/order_notification_job.rb
class OrderNotificationJob < ApplicationJob
  queue_as :default

  def perform(order_id)
    order = Order.find(order_id)
    OrderMailer.confirmation(order).deliver_now
  end
end

# Enqueue
OrderNotificationJob.perform_later(order.id)
```

**Why Solid Queue over Sidekiq?**

| Feature | Solid Queue | Sidekiq |
|---------|-------------|---------|
| Redis required | No | Yes |
| Database backend | PostgreSQL, MySQL, SQLite | Redis only |
| Concurrency controls | Built-in | Requires sidekiq-unique-jobs |
| Recurring jobs | Built-in | Requires sidekiq-cron |
| Infrastructure | Simpler | Requires Redis |

**When to use Sidekiq**: High-throughput applications (10,000+ jobs/minute) or when Redis is already in the stack.

### Job Continuations (Rails 8.1+)

Long-running jobs **SHOULD** use continuations for graceful shutdown:

```ruby
class DataExportJob < ApplicationJob
  include ActiveJob::Continuations

  def perform(export_id)
    export = Export.find(export_id)

    step :fetch_records do
      @records = export.user.records.to_a
    end

    step :process_records do
      @records.each_with_index do |record, i|
        export.process_record(record)
        checkpoint! if i % 100 == 0  # Allow graceful interruption
      end
    end

    step :finalize do
      export.complete!
      ExportMailer.ready(export).deliver_later
    end
  end
end
```

**Why**: Job continuations allow jobs to resume from the last checkpoint after deployment restarts, preventing work loss during Kamal's 30-second shutdown window.

## Caching: Solid Cache (Rails 8+)

Projects **SHOULD** use Solid Cache[^22] instead of Redis/Memcached for caching:

```ruby
# config/environments/production.rb
config.cache_store = :solid_cache_store

# config/cache.yml
production:
  database: cache
  max_size: 256.megabytes
  max_age: 1.week
```

**Why**: Solid Cache uses disk storage, enabling much larger caches than memory-based solutions. It supports encryption for privacy compliance and requires no additional infrastructure.

## WebSockets: Solid Cable (Rails 8+)

Projects using Action Cable **SHOULD** use Solid Cable[^23] instead of Redis:

```ruby
# config/cable.yml
production:
  adapter: solid_cable
  polling_interval: 0.1.seconds
  message_retention: 1.day
```

**Why**: Solid Cable eliminates Redis dependency for Action Cable while retaining messages for debugging.

## Security: Brakeman

All Rails projects **MUST** use Brakeman[^3] for static security analysis.

```bash
# Install
bundle add brakeman --group development

# Run
bundle exec brakeman

# CI with exit code
bundle exec brakeman --exit-on-warn --no-pager
```

**Why Brakeman?** Brakeman performs static analysis to detect common Rails security vulnerabilities including SQL injection, XSS, CSRF, and mass assignment. It runs without executing code, making it safe for CI and pre-commit hooks.

## Migrations

Migrations **MUST** include NOT NULL constraints and indexes where appropriate.

```ruby
class CreateUsers < ActiveRecord::Migration[8.1]
  def change
    create_table :users do |t|
      t.string :email, null: false
      t.string :name, null: false, limit: 255
      t.boolean :active, null: false, default: true
      t.timestamps
    end

    add_index :users, :email, unique: true
  end
end
```

### Safe Migration Patterns

Production migrations **MUST** use the strong_migrations[^8] gem to prevent zero-downtime deployment issues:

```ruby
# Gemfile
gem "strong_migrations"
```

```ruby
# Safe: add column with default
add_column :users, :status, :string, default: "active"

# Safe: add index concurrently
disable_ddl_transaction!
add_index :users, :email, algorithm: :concurrently
```

**Why strong_migrations?** The gem catches dangerous migrations that can cause downtime or lock tables during deployment, such as adding columns with defaults, removing columns still in use, or creating indexes on large tables without concurrency.

## Testing with RSpec

Rails projects **MUST** use RSpec[^9] for testing with RSpec Rails[^4] extensions.

```ruby
# spec/rails_helper.rb
RSpec.configure do |config|
  config.use_transactional_fixtures = true
  config.infer_spec_type_from_file_location!
end
```

```ruby
# spec/models/user_spec.rb
RSpec.describe User do
  describe "validations" do
    it { is_expected.to validate_presence_of(:email) }
    it { is_expected.to validate_uniqueness_of(:email).case_insensitive }
  end

  describe "#full_name" do
    subject(:user) { build(:user, first_name: "John", last_name: "Doe") }

    it "returns first and last name" do
      expect(user.full_name).to eq("John Doe")
    end
  end
end
```

**Why RSpec Rails?** RSpec Rails provides Rails-specific matchers and helpers that make testing models, controllers, and system tests more expressive and maintainable. It integrates seamlessly with fixtures, factories, and database cleaners.

## CI Pipeline

Rails projects **MUST** run linting, security checks, and tests in CI.

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
      - run: bundle exec brakeman --exit-on-warn

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:18
        env:
          POSTGRES_PASSWORD: postgres
    steps:
      - uses: actions/checkout@v4
      - uses: ruby/setup-ruby@v1
        with:
          bundler-cache: true
      - run: bundle exec rails db:setup
      - run: bundle exec rspec
```

## E2E & Acceptance Testing

Projects with user-facing interfaces **SHOULD** include end-to-end tests using Capybara[^10]. Cucumber[^11] **MAY** be used for BDD-style acceptance tests.

```ruby
# Gemfile
group :test do
  gem "capybara"
  gem "selenium-webdriver"
  gem "cucumber-rails", require: false
  gem "site_prism"  # Page Object Model library
end
```

```ruby
# spec/system/orders_spec.rb
RSpec.describe "Order creation", type: :system do
  it "creates order with valid data" do
    visit new_order_path
    fill_in "Product", with: "Widget"
    fill_in "Quantity", with: "5"
    click_button "Create Order"

    expect(page).to have_content("Order created successfully")
    expect(Order.last.quantity).to eq(5)
  end
end
```

```ruby
# features/step_definitions/order_steps.rb
Given("I am on the new order page") do
  visit new_order_path
end

When("I create an order for {int} widgets") do |quantity|
  fill_in "Product", with: "Widget"
  fill_in "Quantity", with: quantity
  click_button "Create Order"
end

Then("I should see a success message") do
  expect(page).to have_content("Order created successfully")
end
```

```ruby
# spec/support/pages/order_page.rb
class OrderPage < SitePrism::Page  # Using SitePrism for Page Object Model[^12]
  set_url "/orders/new"
  element :product_field, "#order_product"
  element :quantity_field, "#order_quantity"
  element :submit_button, "input[type='submit']"

  def create_order(product:, quantity:)
    product_field.set(product)
    quantity_field.set(quantity)
    submit_button.click
  end
end
```

## Thread Safety Testing

Applications using multi-threading (Puma[^13], Sidekiq[^14]) **SHOULD** include thread safety tests.

```ruby
# spec/jobs/order_processor_job_spec.rb
RSpec.describe OrderProcessorJob do
  it "processes orders concurrently" do
    orders = create_list(:order, 5)

    threads = orders.map do |order|
      Thread.new { described_class.perform_now(order.id) }
    end
    threads.each(&:join)

    orders.each do |order|
      expect(order.reload.status).to eq("processed")
    end
  end
end
```

```ruby
# spec/support/connection_pool_spec.rb
RSpec.describe "Connection pool" do
  it "handles concurrent requests" do
    pool_size = ActiveRecord::Base.connection_pool.size

    threads = pool_size.times.map do
      Thread.new { User.count }
    end

    expect { threads.each(&:join) }.not_to raise_error
  end
end
```

```ruby
# spec/requests/concurrent_requests_spec.rb
RSpec.describe "Concurrent requests" do
  it "handles parallel API calls safely" do
    user = create(:user, balance: 100)

    threads = 5.times.map do
      Thread.new do
        post api_v1_debit_path, params: {user_id: user.id, amount: 10}
      end
    end
    threads.each(&:join)

    expect(user.reload.balance).to eq(50)
  end
end
```

## Idempotence Testing

Background jobs and API endpoints **SHOULD** be idempotent. Critical operations **MUST** be tested for idempotence.

```ruby
# Gemfile
gem "sidekiq-unique-jobs"  # Ensure job idempotence[^15]
```

```ruby
# app/jobs/order_notification_job.rb
class OrderNotificationJob < ApplicationJob
  include Sidekiq::Worker
  sidekiq_options lock: :until_executed, on_conflict: :log

  def perform(order_id)
    order = Order.find(order_id)
    OrderMailer.confirmation(order).deliver_now
  end
end
```

```ruby
# spec/jobs/order_notification_job_spec.rb
RSpec.describe OrderNotificationJob do
  it "executes only once for duplicate jobs" do
    order = create(:order)

    expect {
      2.times { described_class.perform_async(order.id) }
      described_class.drain
    }.to change { ActionMailer::Base.deliveries.count }.by(1)
  end
end
```

```ruby
# app/controllers/api/v1/orders_controller.rb
class Api::V1::OrdersController < Api::V1::BaseController
  def create
    idempotency_key = request.headers["Idempotency-Key"]

    if idempotency_key
      existing = IdempotentRequest.find_by(key: idempotency_key)
      return render json: existing.response if existing
    end

    order = Orders::CreateService.call(params: order_params)
    IdempotentRequest.create!(key: idempotency_key, response: order) if idempotency_key

    render json: order, status: :created
  end
end
```

```ruby
# spec/models/user_spec.rb
RSpec.describe User do
  it "upserts idempotently" do
    user_data = {email: "test@example.com", name: "Test User"}

    2.times do
      User.upsert(user_data, unique_by: :email)
    end

    expect(User.where(email: "test@example.com").count).to eq(1)
  end
end
```

## Reliability & Resilience Testing

Applications with external dependencies **SHOULD** test failure scenarios using chaos engineering tools like Toxiproxy[^16].

```ruby
# Gemfile
group :test do
  gem "toxiproxy"
end
```

```ruby
# spec/support/toxiproxy.rb
RSpec.configure do |config|
  config.before(:suite) do
    Toxiproxy.populate([
      {
        name: "postgres",
        listen: "127.0.0.1:5433",
        upstream: "127.0.0.1:5432"
      }
    ])
  end
end
```

```ruby
# spec/integration/payment_resilience_spec.rb
RSpec.describe "Payment gateway resilience" do
  it "handles network latency" do
    Toxiproxy[:payment_gateway].downstream(:latency, latency: 2000).apply do
      expect {
        PaymentService.charge(amount: 100)
      }.to raise_error(PaymentService::TimeoutError)
    end
  end

  it "handles connection failures" do
    Toxiproxy[:payment_gateway].down do
      expect {
        PaymentService.charge(amount: 100)
      }.to raise_error(PaymentService::ConnectionError)
    end
  end
end
```

```ruby
# Gemfile
gem "semian"  # Circuit breaker for Ruby[^17]
```

```ruby
# config/initializers/semian.rb
Semian::NetHTTP.semian_configuration = proc do |host, port|
  {
    name: "#{host}:#{port}",
    tickets: 10,
    error_threshold: 3,
    error_timeout: 10,
    success_threshold: 2
  }
end
```

```ruby
# spec/jobs/order_processor_job_spec.rb
RSpec.describe OrderProcessorJob do
  it "retries on transient failures" do
    order = create(:order)
    allow(PaymentService).to receive(:charge).and_raise(Net::ReadTimeout).twice
    allow(PaymentService).to receive(:charge).and_return(true)

    described_class.perform_now(order.id)

    expect(order.reload.status).to eq("paid")
  end
end
```

## Compatibility Testing

Gems and libraries **SHOULD** test compatibility across supported Rails and Ruby versions using Appraisal[^18].

```ruby
# Gemfile
group :development, :test do
  gem "appraisal"
end
```

```ruby
# Appraisals
appraise "rails-8.0" do
  gem "rails", "~> 8.0.0"
end

appraise "rails-8.1" do
  gem "rails", "~> 8.1.0"
end
```

```bash
# Generate gemfiles
bundle exec appraisal install

# Run tests across versions
bundle exec appraisal rspec
```

```yaml
# .github/workflows/test.yml
strategy:
  matrix:
    ruby: ["3.4", "4.0"]
    rails: ["8.0", "8.1"]
steps:
  - uses: ruby/setup-ruby@v1
    with:
      ruby-version: ${{ matrix.ruby }}
  - run: bundle exec appraisal rails-${{ matrix.rails }} rspec
```

## Internationalization Testing

Applications supporting multiple locales **MUST** test localization and character encoding.

```ruby
# spec/support/i18n.rb
RSpec.configure do |config|
  config.around(:each, locale: true) do |example|
    original_locale = I18n.locale
    I18n.locale = example.metadata[:locale]
    example.run
    I18n.locale = original_locale
  end
end
```

```ruby
# spec/models/product_spec.rb
RSpec.describe Product do
  describe "#localized_name", locale: :es do
    it "returns Spanish translation" do
      product = create(:product)
      expect(product.localized_name).to eq("Producto de Prueba")
    end
  end
end
```

```ruby
# spec/system/localization_spec.rb
RSpec.describe "Localization" do
  it "displays content in user's locale" do
    I18n.available_locales.each do |locale|
      visit root_path(locale: locale)
      expect(page).to have_content(I18n.t("welcome.title", locale: locale))
    end
  end
end
```

```ruby
# spec/i18n_spec.rb
RSpec.describe "Translation coverage" do
  it "has translations for all locales" do
    I18n.available_locales.each do |locale|
      missing = I18n.t(".", locale: locale).select { |k, v| v.is_a?(String) && v.start_with?("translation missing") }
      expect(missing).to be_empty, "Missing translations in #{locale}: #{missing.keys}"
    end
  end
end
```

```ruby
# spec/models/user_spec.rb
RSpec.describe User do
  it "handles UTF-8 characters" do
    user = create(:user, name: "José María 中文 🎉")
    expect(user.reload.name).to eq("José María 中文 🎉")
  end
end
```

## Data Integrity Testing

Database constraints and migrations **MUST** be tested to ensure data integrity.

```ruby
# Gemfile
gem "strong_migrations"
```

```ruby
# spec/migrations/add_user_status_spec.rb
RSpec.describe AddUserStatus, type: :migration do
  it "adds status column with default" do
    migrate!

    User.reset_column_information
    user = User.create!(email: "test@example.com")

    expect(user.status).to eq("active")
  end
end
```

```ruby
# spec/models/order_spec.rb
RSpec.describe Order do
  describe "foreign key constraints" do
    it "prevents orphaned orders" do
      user = create(:user)
      order = create(:order, user: user)

      expect { user.destroy }.to raise_error(ActiveRecord::InvalidForeignKey)
    end
  end

  describe "check constraints" do
    it "enforces positive quantity" do
      order = build(:order, quantity: -1)
      expect(order.save).to be(false)
      expect(order.errors[:quantity]).to include("must be greater than 0")
    end
  end
end
```

```ruby
# spec/support/transactional_fixtures.rb
RSpec.configure do |config|
  config.use_transactional_fixtures = true

  config.around(:each, no_transaction: true) do |example|
    original = config.use_transactional_fixtures
    config.use_transactional_fixtures = false
    example.run
    config.use_transactional_fixtures = original
  end
end
```

```ruby
# spec/features/checkout_spec.rb
RSpec.describe "Checkout process", no_transaction: true do
  it "rolls back on payment failure" do
    initial_count = Order.count

    visit checkout_path
    # Payment fails...

    expect(Order.count).to eq(initial_count)
  end
end
```

## A/B Testing & Feature Flags

Applications using feature flags or A/B tests **MUST** test both enabled and disabled states using tools like Flipper[^19] and Split[^20].

```ruby
# Gemfile
gem "flipper"
gem "flipper-active_record"
gem "split"
```

```ruby
# config/initializers/flipper.rb
Flipper.configure do |config|
  config.default do
    adapter = Flipper::Adapters::ActiveRecord.new
    Flipper.new(adapter)
  end
end
```

```ruby
# spec/features/feature_flags_spec.rb
RSpec.describe "Feature flags" do
  it "shows new UI when enabled" do
    Flipper.enable(:new_dashboard, user)

    visit dashboard_path
    expect(page).to have_css(".new-dashboard")
  end

  it "shows old UI when disabled" do
    Flipper.disable(:new_dashboard)

    visit dashboard_path
    expect(page).to have_css(".old-dashboard")
  end
end
```

```ruby
# spec/controllers/experiments_controller_spec.rb
RSpec.describe ExperimentsController do
  describe "A/B test variants" do
    it "assigns users to control group" do
      allow(Split::Helper).to receive(:ab_test).with("checkout_flow").and_return("control")

      get :show
      expect(response).to render_template("checkout/standard")
    end

    it "assigns users to experiment group" do
      allow(Split::Helper).to receive(:ab_test).with("checkout_flow").and_return("simplified")

      get :show
      expect(response).to render_template("checkout/simplified")
    end
  end
end
```

```ruby
# spec/models/user_spec.rb
RSpec.describe User do
  describe "feature gate behavior" do
    it "accesses premium features when enabled" do
      user = create(:user)
      Flipper.enable(:premium_features, user)

      expect(user.can_access_premium?).to be(true)
    end

    it "denies access when feature disabled" do
      user = create(:user)
      Flipper.disable(:premium_features)

      expect(user.can_access_premium?).to be(false)
    end
  end
end
```

## See Also

- [Ruby Style Guide](../ruby.md) - Base Ruby conventions that apply to Rails
- [Testing Guide](../testing.md) - General testing principles and patterns
- [CI Guide](../ci.md) - Continuous integration best practices

## References

[^1]: **StandardRB** - Ruby style guide, linter, and formatter. Zero-config solution for consistent Ruby code style. [https://github.com/standardrb/standard](https://github.com/standardrb/standard)

[^2]: **standard-rails** - Rails-specific StandardRB plugin with additional RuboCop rules for Rails best practices. [https://github.com/standardrb/standard-rails](https://github.com/standardrb/standard-rails)

[^3]: **Brakeman** - Static analysis security scanner for Ruby on Rails applications. Detects common vulnerabilities without executing code. [https://brakemanscanner.org/](https://brakemanscanner.org/) | [GitHub](https://github.com/presidentbeef/brakeman)

[^4]: **RSpec Rails** - RSpec testing framework extensions for Ruby on Rails. Provides Rails-specific matchers and helpers. [https://rspec.info/](https://rspec.info/) | [GitHub](https://github.com/rspec/rspec-rails)

[^5]: **SimpleCov** - Code coverage analysis tool for Ruby. Generates coverage reports during test execution. [https://github.com/simplecov-ruby/simplecov](https://github.com/simplecov-ruby/simplecov)

[^6]: **standard-sorbet** - Sorbet-specific StandardRB plugin for type checking integration. [https://github.com/standardrb/standard-sorbet](https://github.com/standardrb/standard-sorbet)

[^7]: **Sorbet** - Fast, powerful type checker designed for Ruby. [https://sorbet.org/](https://sorbet.org/) | [GitHub](https://github.com/sorbet/sorbet)

[^8]: **strong_migrations** - Catches unsafe migrations in development to prevent production downtime and table locks. [https://github.com/ankane/strong_migrations](https://github.com/ankane/strong_migrations)

[^9]: **RSpec** - Behavior-driven development framework for Ruby. Provides expressive DSL for writing tests. [https://rspec.info/](https://rspec.info/) | [GitHub](https://github.com/rspec/rspec)

[^10]: **Capybara** - Web-based acceptance test framework for Ruby. Simulates user interactions with web applications. [https://github.com/teamcapybara/capybara](https://github.com/teamcapybara/capybara)

[^11]: **Cucumber** - BDD framework for writing human-readable acceptance tests using Gherkin syntax. [https://cucumber.io/](https://cucumber.io/) | [GitHub](https://github.com/cucumber/cucumber-ruby)

[^12]: **SitePrism** - Page Object Model DSL for Capybara. Provides organized structure for page interactions. [https://github.com/site-prism/site_prism](https://github.com/site-prism/site_prism)

[^13]: **Puma** - Modern, concurrent web server for Ruby/Rack applications. Multi-threaded for high performance. [https://puma.io/](https://puma.io/) | [GitHub](https://github.com/puma/puma)

[^14]: **Sidekiq** - Background job processor for Ruby using multi-threading. Efficient alternative to single-threaded solutions. [https://sidekiq.org/](https://sidekiq.org/) | [GitHub](https://github.com/sidekiq/sidekiq)

[^15]: **sidekiq-unique-jobs** - Ensures uniqueness of Sidekiq jobs to prevent duplicate processing. [https://github.com/mhenrixon/sidekiq-unique-jobs](https://github.com/mhenrixon/sidekiq-unique-jobs)

[^16]: **Toxiproxy** - Framework for simulating network conditions and failures. Chaos engineering tool for testing resilience. [https://github.com/Shopify/toxiproxy](https://github.com/Shopify/toxiproxy)

[^17]: **Semian** - Resiliency toolkit for Ruby. Implements circuit breaker pattern for external service dependencies. [https://github.com/Shopify/semian](https://github.com/Shopify/semian)

[^18]: **Appraisal** - Library for testing gems against multiple versions of dependencies. [https://github.com/thoughtbot/appraisal](https://github.com/thoughtbot/appraisal)

[^19]: **Flipper** - Feature flag library for Ruby applications. Supports various backends and rollout strategies. [https://www.flippercloud.io/](https://www.flippercloud.io/) | [GitHub](https://github.com/flippercloud/flipper)

[^20]: **Split** - Rack-based A/B testing framework for Ruby. Enables experimentation and conversion tracking. [https://github.com/splitrb/split](https://github.com/splitrb/split)

[^21]: **Solid Queue** - Database-backed Active Job backend. Replaces Redis/Sidekiq for most use cases in Rails 8+. [https://github.com/rails/solid_queue](https://github.com/rails/solid_queue)

[^22]: **Solid Cache** - Database-backed Rails cache store. Replaces Redis/Memcached with disk-based caching. [https://github.com/rails/solid_cache](https://github.com/rails/solid_cache)

[^23]: **Solid Cable** - Database-backed Action Cable adapter. Replaces Redis for WebSocket pubsub in Rails 8+. [https://github.com/rails/solid_cable](https://github.com/rails/solid_cable)
