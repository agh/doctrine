# Rails Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > Rails

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119][rfc2119].

[rfc2119]: https://datatracker.ietf.org/doc/html/rfc2119

Extends [Ruby style guide](ruby.md) with Rails-specific conventions from
[Rails Style Guide](https://rails.rubystyle.guide/).

**Target Version**: Rails 8.1+ with Ruby 3.4

## Quick Reference

All Ruby tooling applies. Additional tools are **REQUIRED**:

| Task | Tool | Command |
| ---- | ---- | ------- |
| Lint | StandardRB[^1] + standard-rails[^2] | `bundle exec standardrb` |
| Security | Brakeman[^3] | `bundle exec brakeman` |
| Test | RSpec Rails[^4] | `bundle exec rspec` |
| Coverage | SimpleCov[^5] | via test suite |
| N+1 Detection | Bullet[^29] | via test suite |
| Profiling | rack-mini-profiler[^28] | `?pp=flamegraph` |
| Rate Limiting | Rails built-in or Rack::Attack[^24] | via middleware |

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

**Why StandardRB?** StandardRB eliminates style debates with zero configuration. The
standard-rails plugin extends this philosophy to Rails idioms, catching common anti-patterns
like N+1 queries and improper use of callbacks while maintaining zero-config simplicity.

## Project Structure

Rails projects **SHOULD** organize code using this structure:

```text
app/
├── controllers/
├── models/
├── views/
├── services/          # Business logic
├── queries/           # Complex queries
├── serializers/       # JSON serialization
└── validators/        # Custom validators
```

Service objects **SHOULD** be used for complex business logic. Query objects **MAY** be used for
complex database queries that don't belong in models.

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

**Why Service Objects?** Thin controllers improve testability by isolating business logic from
HTTP concerns. Service objects are easier to test in isolation and can be reused across
controllers, jobs, and rake tasks.

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

**Why**: Rails 8's authentication generator provides secure defaults including session tracking,
password resets, and rate limiting without third-party gems like Devise.

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

**When to use Sidekiq**: High-throughput applications (10,000+ jobs/minute) or when Redis is
already in the stack.

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

**Why**: Job continuations allow jobs to resume from the last checkpoint after deployment
restarts, preventing work loss during Kamal's 30-second shutdown window.

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

**Why**: Solid Cache uses disk storage, enabling much larger caches than memory-based solutions.
It supports encryption for privacy compliance and requires no additional infrastructure.

## WebSockets: Solid Cable (Rails 8+)

Projects using Action Cable **SHOULD** use Solid Cable[^23] instead of Redis:

```ruby
# config/cable.yml
production:
  adapter: solid_cable
  polling_interval: 0.1.seconds
  message_retention: 1.day
```

**Why**: Solid Cable eliminates Redis dependency for Action Cable while retaining messages for
debugging.

## Hotwire: Turbo + Stimulus

Projects **SHOULD** use Hotwire[^34] for modern, interactive UIs without writing custom
JavaScript. Hotwire combines Turbo[^35] for HTML-over-the-wire updates with Stimulus[^36] for
lightweight JavaScript sprinkles.

### Why Hotwire

- **Less JavaScript**: Build reactive UIs using server-rendered HTML
- **Default in Rails 8**: Included by default, no additional gems needed
- **Progressive enhancement**: Works without JavaScript, enhanced when available
- **Simpler mental model**: Server controls application state, not client

### Turbo Drive

Turbo Drive accelerates navigation by intercepting link clicks and form submissions:

```erb
<%# Turbo Drive is enabled by default. Disable for specific links: %>
<%= link_to "External Site", "https://example.com", data: { turbo: false } %>

<%# Disable for forms that should do full page reload: %>
<%= form_with model: @user, data: { turbo: false } do |f| %>
  ...
<% end %>
```

### Turbo Frames

Turbo Frames enable partial page updates by scoping navigation to a frame:

```erb
<%# app/views/posts/index.html.erb %>
<%= turbo_frame_tag "posts" do %>
  <% @posts.each do |post| %>
    <%= render post %>
  <% end %>

  <%# Link loads only the frame, not full page %>
  <%= link_to "Load More", posts_path(page: @page + 1) %>
<% end %>

<%# Lazy-load content %>
<%= turbo_frame_tag "comments", src: post_comments_path(@post), loading: :lazy do %>
  <p>Loading comments...</p>
<% end %>
```

```ruby
# app/controllers/posts_controller.rb
class PostsController < ApplicationController
  def index
    @posts = Post.page(params[:page])
    # Turbo Frame requests only render the frame, not layout
  end
end
```

### Turbo Streams

Turbo Streams enable real-time updates via WebSocket or HTTP responses:

```ruby
# app/controllers/comments_controller.rb
class CommentsController < ApplicationController
  def create
    @comment = @post.comments.build(comment_params)

    if @comment.save
      respond_to do |format|
        format.turbo_stream  # Renders create.turbo_stream.erb
        format.html { redirect_to @post }
      end
    else
      render :new, status: :unprocessable_entity
    end
  end
end
```

```erb
<%# app/views/comments/create.turbo_stream.erb %>
<%= turbo_stream.append "comments", @comment %>
<%= turbo_stream.update "comment_form", partial: "comments/form", locals: { comment: Comment.new } %>
<%= turbo_stream.update "comment_count", @post.comments.count %>
```

### Turbo Stream Actions

| Action | Description |
|--------|-------------|
| `append` | Add content to end of target |
| `prepend` | Add content to start of target |
| `replace` | Replace entire target element |
| `update` | Replace content inside target |
| `remove` | Remove target element |
| `before` | Insert content before target |
| `after` | Insert content after target |

### Broadcasting with Action Cable

```ruby
# app/models/comment.rb
class Comment < ApplicationRecord
  belongs_to :post

  after_create_commit -> {
    broadcast_append_to post, target: "comments"
  }

  after_destroy_commit -> {
    broadcast_remove_to post
  }
end
```

```erb
<%# app/views/posts/show.html.erb %>
<%= turbo_stream_from @post %>

<div id="comments">
  <%= render @post.comments %>
</div>
```

### Stimulus Controllers

Stimulus adds lightweight JavaScript behavior to HTML:

```javascript
// app/javascript/controllers/clipboard_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["source"]
  static values = { successMessage: String }

  copy() {
    navigator.clipboard.writeText(this.sourceTarget.value)
    this.dispatch("copied", { detail: { content: this.sourceTarget.value } })
  }
}
```

```erb
<div data-controller="clipboard" data-clipboard-success-message-value="Copied!">
  <input type="text" value="Copy me!" data-clipboard-target="source">
  <button data-action="clipboard#copy">Copy</button>
</div>
```

### Stimulus Best Practices

```javascript
// GOOD: Use targets for DOM elements
static targets = ["input", "output"]

// GOOD: Use values for configuration
static values = { url: String, delay: { type: Number, default: 300 } }

// GOOD: Use classes for CSS manipulation
static classes = ["active", "loading"]

// GOOD: Small, focused controllers
// BAD: Monolithic controllers with 500+ lines

// GOOD: Use Stimulus outlets for controller communication
static outlets = ["modal"]
openModal() {
  this.modalOutlet.open()
}
```

### Testing Hotwire

```ruby
# spec/requests/comments_spec.rb
RSpec.describe "Comments", type: :request do
  describe "POST /posts/:post_id/comments" do
    it "returns turbo stream response" do
      post post_comments_path(post), params: { comment: { body: "Great!" } },
           headers: { "Accept" => "text/vnd.turbo-stream.html" }

      expect(response).to have_http_status(:success)
      expect(response.media_type).to eq("text/vnd.turbo-stream.html")
      expect(response.body).to include("turbo-stream")
    end
  end
end
```

```ruby
# spec/system/comments_spec.rb
RSpec.describe "Comments", type: :system, js: true do
  it "adds comment without page reload" do
    post = create(:post)
    visit post_path(post)

    fill_in "comment_body", with: "New comment"
    click_button "Submit"

    expect(page).to have_content("New comment")
    expect(page).not_to have_current_path(post_comments_path(post))
  end
end
```

## ViewComponent

Projects with complex views **SHOULD** use ViewComponent[^37] to encapsulate view logic in
testable, reusable components.

### Why ViewComponent

- **Testable**: Components are unit-testable Ruby objects, 10x faster than system tests
- **Encapsulated**: Components own their templates, no implicit instance variables
- **Reusable**: Components are packaged for reuse across views
- **Type-safe**: Works with Sorbet for compile-time type checking

### Installation

```ruby
# Gemfile
gem "view_component"
```

```bash
bin/rails generate component Example title
```

### Basic Component

```ruby
# app/components/alert_component.rb
class AlertComponent < ViewComponent::Base
  VARIANTS = %w[info success warning error].freeze

  def initialize(message:, variant: "info", dismissible: false)
    @message = message
    @variant = variant.to_s
    @dismissible = dismissible
  end

  def variant_classes
    case @variant
    when "success" then "bg-green-100 text-green-800"
    when "warning" then "bg-yellow-100 text-yellow-800"
    when "error" then "bg-red-100 text-red-800"
    else "bg-blue-100 text-blue-800"
    end
  end

  def render?
    @message.present?
  end
end
```

```erb
<%# app/components/alert_component.html.erb %>
<div class="alert <%= variant_classes %>" role="alert"
     data-controller="<%= 'dismissible' if @dismissible %>">
  <p><%= @message %></p>
  <% if @dismissible %>
    <button data-action="dismissible#dismiss">×</button>
  <% end %>
</div>
```

```erb
<%# Usage in views %>
<%= render AlertComponent.new(message: "Success!", variant: :success, dismissible: true) %>
```

### Components with Slots

```ruby
# app/components/card_component.rb
class CardComponent < ViewComponent::Base
  renders_one :header
  renders_one :footer
  renders_many :actions

  def initialize(title: nil)
    @title = title
  end
end
```

```erb
<%# app/components/card_component.html.erb %>
<div class="card">
  <% if header? || @title %>
    <div class="card-header">
      <%= header || @title %>
    </div>
  <% end %>

  <div class="card-body">
    <%= content %>
  </div>

  <% if actions? %>
    <div class="card-actions">
      <% actions.each do |action| %>
        <%= action %>
      <% end %>
    </div>
  <% end %>

  <% if footer? %>
    <div class="card-footer">
      <%= footer %>
    </div>
  <% end %>
</div>
```

```erb
<%# Usage %>
<%= render CardComponent.new do |card| %>
  <% card.with_header do %>
    <h2>Custom Header</h2>
  <% end %>

  <p>Card content goes here.</p>

  <% card.with_action do %>
    <%= link_to "Edit", edit_path %>
  <% end %>
  <% card.with_action do %>
    <%= button_to "Delete", delete_path, method: :delete %>
  <% end %>
<% end %>
```

### Collection Rendering

```ruby
# app/components/user_row_component.rb
class UserRowComponent < ViewComponent::Base
  with_collection_parameter :user

  def initialize(user:, user_counter: nil)
    @user = user
    @counter = user_counter
  end
end
```

```erb
<%# Render collection efficiently %>
<%= render UserRowComponent.with_collection(@users) %>
```

### Component Testing

```ruby
# spec/components/alert_component_spec.rb
RSpec.describe AlertComponent, type: :component do
  it "renders message" do
    render_inline(described_class.new(message: "Hello"))

    expect(page).to have_text("Hello")
  end

  it "applies variant classes" do
    render_inline(described_class.new(message: "Error!", variant: :error))

    expect(page).to have_css(".bg-red-100")
  end

  it "does not render when message is blank" do
    render_inline(described_class.new(message: ""))

    expect(page).not_to have_css(".alert")
  end

  context "when dismissible" do
    it "renders close button" do
      render_inline(described_class.new(message: "Dismiss me", dismissible: true))

      expect(page).to have_button("×")
    end
  end
end
```

### Component Previews

```ruby
# spec/components/previews/alert_component_preview.rb
class AlertComponentPreview < ViewComponent::Preview
  # @param message text
  # @param variant select [info, success, warning, error]
  # @param dismissible toggle
  def default(message: "This is an alert", variant: :info, dismissible: false)
    render AlertComponent.new(
      message: message,
      variant: variant,
      dismissible: dismissible
    )
  end

  def all_variants
    render_with_template
  end
end
```

```erb
<%# spec/components/previews/alert_component_preview/all_variants.html.erb %>
<% %w[info success warning error].each do |variant| %>
  <%= render AlertComponent.new(message: "#{variant.titleize} message", variant: variant) %>
<% end %>
```

Visit `/rails/view_components` to browse component previews during development.

### ViewComponent with Hotwire

```ruby
# app/components/live_counter_component.rb
class LiveCounterComponent < ViewComponent::Base
  def initialize(count:, resource:)
    @count = count
    @resource = resource
  end

  def dom_id
    "#{@resource.class.name.underscore}_#{@resource.id}_counter"
  end
end
```

```erb
<%# app/components/live_counter_component.html.erb %>
<%= turbo_stream_from @resource, :counter %>
<span id="<%= dom_id %>"><%= @count %></span>
```

```ruby
# app/models/post.rb
class Post < ApplicationRecord
  after_update_commit -> {
    broadcast_update_to self, :counter,
      target: "post_#{id}_counter",
      html: comments_count.to_s
  }
end
```

## Rate Limiting

### Built-in Rate Limiting (Rails 8+)

Rails 8 projects **SHOULD** use the built-in `rate_limit` method for simple throttling scenarios:

```ruby
# app/controllers/sessions_controller.rb
class SessionsController < ApplicationController
  rate_limit to: 10, within: 3.minutes, only: :create, with: -> {
    redirect_to new_session_url, alert: "Try again later."
  }

  def create
    # Login logic
  end
end

# app/controllers/api/v1/base_controller.rb
class Api::V1::BaseController < ApplicationController
  rate_limit to: 100, within: 1.minute, by: -> { request.remote_ip }
end
```

**Why**: Rails 8's built-in rate limiting requires no additional gems and uses your existing
cache store (Redis, Memcached, or Solid Cache). It integrates seamlessly with Action
Controller.

### Rack::Attack for Advanced Scenarios

Projects with complex rate limiting requirements **SHOULD** use Rack::Attack[^24]:

```ruby
# Gemfile
gem "rack-attack"
```

```ruby
# config/initializers/rack_attack.rb
class Rack::Attack
  # Use Redis for distributed rate limiting
  Rack::Attack.cache.store = ActiveSupport::Cache::RedisCacheStore.new(
    url: ENV["REDIS_URL"],
    db: 1  # Separate database for throttling
  )

  # Block bad actors
  blocklist("block bad IPs") do |req|
    Blocklist.exists?(ip: req.ip)
  end

  # Throttle all requests by IP (100 req/min)
  throttle("req/ip", limit: 100, period: 1.minute) do |req|
    req.ip
  end

  # Stricter limits for authentication endpoints
  throttle("logins/ip", limit: 5, period: 20.seconds) do |req|
    req.ip if req.path == "/login" && req.post?
  end

  # Throttle by email for password resets (prevent enumeration)
  throttle("password_resets/email", limit: 3, period: 1.hour) do |req|
    if req.path == "/password" && req.post?
      req.params["user"]["email"].to_s.downcase.gsub(/\s+/, "")
    end
  end

  # Exponential backoff for failed logins
  (1..5).each do |level|
    blocklist("fail2ban/login/L#{level}") do |req|
      Rack::Attack::Fail2Ban.filter(
        "login-#{req.ip}",
        maxretry: 5,
        findtime: 1.minute,
        bantime: (2**level).minutes
      ) do
        req.path == "/login" && req.post? && req.env["warden.options"]&.dig(:message) == :invalid
      end
    end
  end

  # Safelist trusted IPs
  safelist("allow localhost") do |req|
    req.ip == "127.0.0.1" || req.ip == "::1"
  end

  # Custom response for throttled requests
  self.throttled_responder = lambda do |req|
    retry_after = (req.env["rack.attack.match_data"] || {})[:period]
    [
      429,
      {
        "Content-Type" => "application/json",
        "Retry-After" => retry_after.to_s
      },
      [{ error: "Rate limit exceeded", retry_after: retry_after }.to_json]
    ]
  end
end
```

### User-Based Rate Limiting

API applications **SHOULD** implement per-user rate limiting with tiered limits:

```ruby
# config/initializers/rack_attack.rb
Rack::Attack.throttle("api/user", limit: proc { |req|
  user = User.find_by(api_key: req.env["HTTP_X_API_KEY"])
  case user&.plan
  when "enterprise" then 10_000
  when "pro" then 1_000
  else 100
  end
}, period: 1.hour) do |req|
  req.env["HTTP_X_API_KEY"] if req.path.start_with?("/api/")
end

# Include rate limit headers in responses
class Api::V1::BaseController < ApplicationController
  after_action :set_rate_limit_headers

  private

  def set_rate_limit_headers
    match_data = request.env["rack.attack.throttle_data"]&.dig("api/user")
    return unless match_data

    response.headers["X-RateLimit-Limit"] = match_data[:limit].to_s
    response.headers["X-RateLimit-Remaining"] = (match_data[:limit] - match_data[:count]).to_s
    response.headers["X-RateLimit-Reset"] = (match_data[:epoch_time] + match_data[:period]).to_s
  end
end
```

**When to use Rack::Attack over built-in rate limiting**:

| Feature | Built-in (Rails 8+) | Rack::Attack |
|---------|---------------------|--------------|
| Simple endpoint throttling | Yes | Yes |
| IP blocking/safelisting | No | Yes |
| Fail2ban patterns | No | Yes |
| Custom response format | Limited | Full control |
| Distributed (Redis) | Via cache store | Native support |
| Request inspection | Limited | Full Rack access |

**Why Rack::Attack?** Rack::Attack operates at the Rack middleware layer, blocking malicious
requests before they reach your Rails controllers. This protects against credential stuffing
attacks (often 1,000-10,000x normal traffic) and reduces load on your application stack.

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

**Why Brakeman?** Brakeman performs static analysis to detect common Rails security
vulnerabilities including SQL injection, XSS, CSRF, and mass assignment. It runs without
executing code, making it safe for CI and pre-commit hooks.

### Authentication: Devise + OmniAuth

Legacy applications or those requiring OAuth integration **MAY** use Devise[^25] with OmniAuth[^26]:

```ruby
# Gemfile
gem "devise"
gem "omniauth"
gem "omniauth-rails_csrf_protection"  # Required for OmniAuth 2.0+
gem "omniauth-google-oauth2"
```

```ruby
# config/initializers/devise.rb
Devise.setup do |config|
  config.omniauth :google_oauth2,
    ENV["GOOGLE_CLIENT_ID"],
    ENV["GOOGLE_CLIENT_SECRET"],
    scope: "email,profile"
end
```

```ruby
# app/models/user.rb
class User < ApplicationRecord
  devise :database_authenticatable, :registerable,
         :recoverable, :rememberable, :validatable,
         :omniauthable, omniauth_providers: [:google_oauth2]

  def self.from_omniauth(auth)
    find_or_create_by(provider: auth.provider, uid: auth.uid) do |user|
      user.email = auth.info.email
      user.password = Devise.friendly_token[0, 20]
    end
  end
end
```

**Why**: While Rails 8 includes built-in authentication, Devise remains the standard for
applications requiring OAuth providers, two-factor authentication, or advanced account
management features.

### Authorization: Pundit

Applications with role-based access control **SHOULD** use Pundit[^27]:

```ruby
# Gemfile
gem "pundit"
```

```ruby
# app/controllers/application_controller.rb
class ApplicationController < ActionController::Base
  include Pundit::Authorization

  after_action :verify_authorized, except: :index
  after_action :verify_policy_scoped, only: :index

  rescue_from Pundit::NotAuthorizedError do |exception|
    redirect_to root_path, alert: "You are not authorized to perform this action."
  end
end
```

```ruby
# app/policies/post_policy.rb
class PostPolicy < ApplicationPolicy
  def update?
    user.admin? || record.user == user
  end

  def destroy?
    user.admin?
  end

  class Scope < ApplicationPolicy::Scope
    def resolve
      if user.admin?
        scope.all
      else
        scope.where(published: true).or(scope.where(user: user))
      end
    end
  end
end
```

```ruby
# app/controllers/posts_controller.rb
class PostsController < ApplicationController
  def index
    @posts = policy_scope(Post)
  end

  def update
    @post = Post.find(params[:id])
    authorize @post

    if @post.update(post_params)
      redirect_to @post
    else
      render :edit
    end
  end
end
```

**Why Pundit?** Pundit encapsulates authorization logic in plain Ruby policy classes, keeping
controllers thin and making access rules testable. It enforces the principle of least privilege
by requiring explicit authorization for each action.

## Performance

### Development Profiling

Rails projects **SHOULD** use rack-mini-profiler[^28] for development profiling:

```ruby
# Gemfile
group :development do
  gem "rack-mini-profiler"
  gem "flamegraph"        # Flame graph visualization
  gem "stackprof"         # Stack profiler for flame graphs
  gem "memory_profiler"   # Memory allocation profiling
end
```

```ruby
# config/initializers/rack_profiler.rb
if defined?(Rack::MiniProfiler)
  # Position badge on left side
  Rack::MiniProfiler.config.position = "bottom-left"

  # Enable memory profiling (add ?pp=profile-memory to URL)
  Rack::MiniProfiler.config.enable_advanced_debugging_tools = true

  # Store profiling data in memory (or use Redis for persistence)
  Rack::MiniProfiler.config.storage = Rack::MiniProfiler::MemoryStore
end
```

Access profiling features by appending query parameters:

- `?pp=help` - Show all available profiling options
- `?pp=flamegraph` - Generate flame graph visualization
- `?pp=profile-memory` - Show memory allocations
- `?pp=profile-gc` - Show garbage collection stats
- `?pp=analyze-memory` - Detailed memory analysis

**Why rack-mini-profiler?** It provides real-time performance visibility with minimal overhead,
showing SQL queries, view rendering times, and memory usage directly in the browser during
development.

### N+1 Query Detection

All Rails projects **MUST** use Bullet[^29] to detect N+1 queries:

```ruby
# Gemfile
group :development, :test do
  gem "bullet"
end
```

```ruby
# config/environments/development.rb
Rails.application.configure do
  config.after_initialize do
    Bullet.enable = true
    Bullet.alert = true           # JavaScript alert in browser
    Bullet.bullet_logger = true   # Log to log/bullet.log
    Bullet.console = true         # Browser console warnings
    Bullet.rails_logger = true    # Rails logger
    Bullet.add_footer = true      # Add details to page footer

    # Raise errors in test environment
    Bullet.raise = Rails.env.test?

    # Ignore specific associations if needed
    # Bullet.add_safelist type: :n_plus_one_query, class_name: "User", association: :posts
  end
end
```

```ruby
# config/environments/test.rb
Rails.application.configure do
  config.after_initialize do
    Bullet.enable = true
    Bullet.raise = true  # Fail tests on N+1 queries
  end
end
```

**Why Bullet?** N+1 queries are the most common performance issue in Rails applications. Bullet
detects them during development and can fail tests, preventing performance regressions from
reaching production.

### Memory Profiling

Applications with memory concerns **SHOULD** use memory_profiler[^30] for detailed analysis:

```ruby
# Gemfile
group :development, :test do
  gem "memory_profiler"
end
```

```ruby
# lib/tasks/memory_profile.rake
namespace :memory do
  desc "Profile memory usage of a specific code path"
  task profile: :environment do
    report = MemoryProfiler.report do
      # Code to profile
      100.times { User.all.to_a }
    end

    report.pretty_print(
      detailed_report: true,
      scale_bytes: true,
      normalize_paths: true
    )
  end
end
```

```ruby
# spec/support/memory_profiler.rb
RSpec.configure do |config|
  config.around(:each, :profile_memory) do |example|
    report = MemoryProfiler.report { example.run }

    if report.total_allocated_memsize > 10.megabytes
      puts "WARNING: High memory allocation detected"
      report.pretty_print(to_file: "tmp/memory_#{example.description.parameterize}.txt")
    end
  end
end
```

### Production APM

Production applications **SHOULD** use an Application Performance Monitoring (APM) service:

```ruby
# Gemfile
# Choose ONE of the following based on requirements:
gem "appsignal"   # AppSignal[^31] - Ruby-focused, GDPR compliant
gem "skylight"    # Skylight[^32] - Rails-specific, simple pricing
gem "newrelic_rpm" # New Relic - Enterprise features, broader ecosystem
```

```ruby
# config/appsignal.yml (if using AppSignal)
production:
  active: true
  name: "MyApp"
  push_api_key: <%= ENV["APPSIGNAL_PUSH_API_KEY"] %>
  enable_host_metrics: true
  enable_minutely_probes: true
```

```ruby
# Custom instrumentation for business-critical code
class Orders::CreateService
  def call
    ActiveSupport::Notifications.instrument("orders.create", order_id: order.id) do
      # Business logic
    end
  end
end
```

| APM | Best For | Pricing Model |
|-----|----------|---------------|
| AppSignal[^31] | Ruby/Rails teams, GDPR requirements | Request-based ($23+/month) |
| Skylight[^32] | Rails-only, simple performance tuning | Request-based ($20+/month) |
| New Relic | Enterprise, polyglot environments | Host-based (varies) |

**Why APM in production?** Development profiling misses issues that only appear under
production load. APM tools provide continuous monitoring, alerting on performance regressions,
slow queries, and error spikes before users complain.

### Query Tracing

Applications debugging slow queries **MAY** use active_record_query_trace[^33]:

```ruby
# Gemfile
group :development do
  gem "active_record_query_trace"
end
```

```ruby
# config/initializers/query_trace.rb
if defined?(ActiveRecordQueryTrace) && Rails.env.development?
  ActiveRecordQueryTrace.enabled = true
  ActiveRecordQueryTrace.level = :app    # Only show app code, not gems
  ActiveRecordQueryTrace.lines = 5       # Number of backtrace lines
  ActiveRecordQueryTrace.colorize = true
end
```

**Why**: When Bullet identifies an N+1 query, active_record_query_trace shows exactly where in
your code the query originates, making it easier to add eager loading.

### Benchmarking

Performance-critical code **SHOULD** include benchmarks:

```ruby
# Gemfile
group :development, :test do
  gem "benchmark-ips"
  gem "derailed_benchmarks"
end
```

```ruby
# spec/benchmarks/user_search_benchmark.rb
require "benchmark/ips"

RSpec.describe "User search performance", :benchmark do
  let!(:users) { create_list(:user, 1000) }

  it "compares search implementations" do
    Benchmark.ips do |x|
      x.report("LIKE query") { User.where("name LIKE ?", "%john%").to_a }
      x.report("pg_search") { User.search_by_name("john").to_a }
      x.compare!
    end
  end
end
```

```bash
# Profile boot time and memory
bundle exec derailed bundle:mem
bundle exec derailed bundle:objects

# Profile specific request
bundle exec derailed exec perf:stackprof PATH_TO_HIT=/users
```

## Migrations

Migrations **MUST** include NOT NULL constraints and indexes where appropriate:

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

Production migrations **MUST** use the strong_migrations[^8] gem to prevent zero-downtime
deployment issues:

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

**Why strong_migrations?** The gem catches dangerous migrations that can cause downtime or lock
tables during deployment, such as adding columns with defaults, removing columns still in use,
or creating indexes on large tables without concurrency.

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

**Why RSpec Rails?** RSpec Rails provides Rails-specific matchers and helpers that make testing
models, controllers, and system tests more expressive and maintainable. It integrates
seamlessly with fixtures, factories, and database cleaners.

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

Projects with user-facing interfaces **SHOULD** include end-to-end tests using Capybara[^10].
Cucumber[^11] **MAY** be used for BDD-style acceptance tests.

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

Background jobs and API endpoints **SHOULD** be idempotent. Critical operations **MUST** be
tested for idempotence.

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

Applications with external dependencies **SHOULD** test failure scenarios using chaos
engineering tools like Toxiproxy[^16].

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

Applications using feature flags or A/B tests **MUST** test both enabled and disabled states
using tools like Flipper[^19] and Split[^20].

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

[^24]: **Rack::Attack** - Rack middleware for blocking and throttling abusive requests. Battle-tested rate limiting with 33+ million downloads. [https://github.com/rack/rack-attack](https://github.com/rack/rack-attack)

[^25]: **Devise** - Flexible authentication solution for Rails with Warden. Industry standard for complex authentication requirements. [https://github.com/heartcombo/devise](https://github.com/heartcombo/devise)

[^26]: **OmniAuth** - Flexible authentication system utilizing Rack middleware. Enables OAuth integration with third-party providers. [https://github.com/omniauth/omniauth](https://github.com/omniauth/omniauth)

[^27]: **Pundit** - Minimal authorization library using plain Ruby objects. Encapsulates access rules in testable policy classes. [https://github.com/varvet/pundit](https://github.com/varvet/pundit)

[^28]: **rack-mini-profiler** - Profiler for development and production Ruby rack apps. Shows SQL queries, view rendering times, and memory usage. [https://github.com/MiniProfiler/rack-mini-profiler](https://github.com/MiniProfiler/rack-mini-profiler)

[^29]: **Bullet** - Helps detect N+1 queries and unused eager loading. Essential for Rails performance optimization. [https://github.com/flyerhzm/bullet](https://github.com/flyerhzm/bullet)

[^30]: **memory_profiler** - Memory profiling routines for Ruby. Provides detailed allocation reports for debugging memory issues. [https://github.com/SamSaffron/memory_profiler](https://github.com/SamSaffron/memory_profiler)

[^31]: **AppSignal** - Application performance monitoring and error tracking for Ruby. GDPR compliant with request-based pricing. [https://www.appsignal.com/](https://www.appsignal.com/) | [GitHub](https://github.com/appsignal/appsignal-ruby)

[^32]: **Skylight** - Rails-focused application profiler and performance monitoring. Simple pricing with deep Rails integration. [https://www.skylight.io/](https://www.skylight.io/)

[^33]: **active_record_query_trace** - Logs backtrace of all SQL queries executed by Active Record. Helps identify query origins in large applications. [https://github.com/brunofacca/active-record-query-trace](https://github.com/brunofacca/active-record-query-trace)

[^34]: **Hotwire** - HTML over the wire. The default frontend approach in Rails 8+ combining Turbo and Stimulus for modern UIs without heavy JavaScript. [https://hotwired.dev/](https://hotwired.dev/)

[^35]: **Turbo** - Core library of Hotwire for page navigation, partial updates (frames), and real-time updates (streams). [https://turbo.hotwired.dev/](https://turbo.hotwired.dev/) | [GitHub](https://github.com/hotwired/turbo)

[^36]: **Stimulus** - Modest JavaScript framework for the HTML you already have. Adds behavior to HTML via data attributes. [https://stimulus.hotwired.dev/](https://stimulus.hotwired.dev/) | [GitHub](https://github.com/hotwired/stimulus)

[^37]: **ViewComponent** - Framework for creating reusable, testable, and encapsulated view components in Ruby on Rails. By GitHub. [https://viewcomponent.org/](https://viewcomponent.org/) | [GitHub](https://github.com/ViewComponent/view_component)
