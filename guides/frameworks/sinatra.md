# Sinatra Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > Sinatra

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119][rfc2119].

[rfc2119]: https://datatracker.ietf.org/doc/html/rfc2119

Extends [Ruby style guide](../languages/ruby.md) with Sinatra-specific conventions.

**Target Version**: Sinatra 4.x with Ruby 4.0

## Quick Reference

All Ruby tooling applies. Additional considerations:

| Task | Tool | Command |
| ---- | ---- | ------- |
| Lint | StandardRB[^1] | `bundle exec standardrb` |
| Test | RSpec + rack-test[^2] | `bundle exec rspec` |
| Coverage | SimpleCov[^3] | via test suite |

## Why Sinatra?

Sinatra[^4] is ideal for lightweight web development because it:

- **Minimalist design**: Focuses on simplicity with a clean DSL for routing and request handling
- **Low overhead**: Minimal abstraction layer results in fast startup times and low memory footprint
- **Flexible architecture**: No enforced structure allows custom organization for different use cases
- **Perfect for microservices**: Ideal for single-purpose services, APIs, and serverless functions
- **Easy learning curve**: Simple enough to learn in minutes, but powerful enough for production use
- **Rack foundation**: Built on Rack, making it compatible with middleware and easy to test

Use Sinatra when you need a simple API, webhook handler, microservice, or prototype. Choose Rails
when you need a full-featured MVC framework with conventions and scaffolding.

## Project Structure

Projects **SHOULD** use modular Sinatra style for anything beyond trivial
applications:

```text
my_app/
├── app/
│   ├── controllers/
│   │   ├── application_controller.rb
│   │   ├── users_controller.rb
│   │   └── api/
│   │       └── v1_controller.rb
│   ├── models/
│   │   └── user.rb
│   ├── services/
│   │   └── user_service.rb
│   └── helpers/
│       └── application_helper.rb
├── config/
│   ├── database.yml
│   └── environment.rb
├── db/
│   └── migrations/
├── spec/
│   ├── controllers/
│   ├── models/
│   └── spec_helper.rb
├── config.ru
├── Gemfile
└── Rakefile
```

## Modular vs Classic Style

Projects **MUST** use modular style (inheriting from `Sinatra::Base`) for production applications.
Classic style **MAY** only be used for simple scripts or prototypes.

### Modular Style (Recommended)

```ruby
# app/controllers/application_controller.rb
require "sinatra/base"

class ApplicationController < Sinatra::Base
  configure do
    set :show_exceptions, :after_handler
    enable :sessions
  end

  helpers do
    def current_user
      @current_user ||= User.find_by(id: session[:user_id])
    end
  end

  error 404 do
    json error: "Not found"
  end

  error StandardError do
    json error: "Internal server error"
  end

  private

  def json(data, status: 200)
    content_type :json
    halt status, data.to_json
  end
end
```

```ruby
# app/controllers/users_controller.rb
class UsersController < ApplicationController
  get "/users" do
    users = User.all
    json users: users.map(&:to_h)
  end

  get "/users/:id" do
    user = User.find_by(id: params[:id])
    halt 404 unless user
    json user: user.to_h
  end

  post "/users" do
    user = User.new(user_params)
    if user.save
      json user: user.to_h, status: 201
    else
      json errors: user.errors.full_messages, status: 422
    end
  end

  private

  def user_params
    JSON.parse(request.body.read).slice("name", "email")
  end
end
```

```ruby
# config.ru
require_relative "config/environment"

map("/") { run ApplicationController }
map("/") { run UsersController }
```

### Classic Style (Avoid in Production)

```ruby
# app.rb - ONLY for prototypes/scripts
require "sinatra"

get "/" do
  "Hello, World!"
end

post "/webhook" do
  # Handle webhook
  status 200
end
```

**Why modular?** Modular style provides:

- Better testability through isolated controller classes
- Explicit configuration per controller
- Ability to mount multiple applications
- Cleaner namespace management
- Easier refactoring to Rails if needed

## Routing Patterns

Routes **SHOULD** follow RESTful conventions where applicable.

```ruby
class ArticlesController < Sinatra::Base
  # Index
  get "/articles" do
    @articles = Article.all
    json articles: @articles
  end

  # Show
  get "/articles/:id" do
    @article = Article.find(params[:id])
    json article: @article
  end

  # Create
  post "/articles" do
    @article = Article.create(article_params)
    status 201
    json article: @article
  end

  # Update
  patch "/articles/:id" do
    @article = Article.find(params[:id])
    @article.update(article_params)
    json article: @article
  end

  # Delete
  delete "/articles/:id" do
    Article.find(params[:id]).destroy
    status 204
  end

  private

  def article_params
    JSON.parse(request.body.read).slice("title", "body")
  end
end
```

### Route Patterns and Constraints

```ruby
class ApiController < Sinatra::Base
  # Named parameters
  get "/users/:id" do
    params[:id]  # Captures anything except /
  end

  # Wildcard
  get "/files/*" do
    params[:splat].first  # Captures entire path
  end

  # Regular expressions
  get %r{/posts/(\d+)} do
    params[:captures].first  # Only numeric IDs
  end

  # Optional parameters
  get "/search/?:query?" do
    params[:query] || "default"
  end
end
```

## Configuration

Projects **MUST** separate configuration by environment.

```ruby
# config/environment.rb
require "bundler/setup"
Bundler.require(:default, ENV.fetch("RACK_ENV", "development"))

require_relative "../app/controllers/application_controller"
require_relative "../app/controllers/users_controller"

# Load models
Dir[File.join(__dir__, "../app/models/*.rb")].each { |file| require file }
```

```ruby
# app/controllers/application_controller.rb
class ApplicationController < Sinatra::Base
  configure :development do
    enable :logging
    set :show_exceptions, true
  end

  configure :production do
    enable :logging
    set :show_exceptions, false
    set :dump_errors, false
  end

  configure :test do
    set :show_exceptions, true
  end

  configure do
    set :root, File.expand_path("../..", __dir__)
    set :public_folder, -> { File.join(root, "public") }
    set :views, -> { File.join(root, "app/views") }

    enable :sessions
    set :session_secret, ENV.fetch("SESSION_SECRET", SecureRandom.hex(32))
  end
end
```

## Testing with rack-test

Projects **MUST** use rack-test[^2] for testing Sinatra applications.

```ruby
# Gemfile
gem "rack-test", group: :test
gem "rspec", group: :test
```

```ruby
# spec/spec_helper.rb
ENV["RACK_ENV"] = "test"

require_relative "../config/environment"
require "rack/test"
require "rspec"

RSpec.configure do |config|
  config.include Rack::Test::Methods

  config.before(:suite) do
    DatabaseCleaner.strategy = :transaction
  end

  config.around(:each) do |example|
    DatabaseCleaner.cleaning do
      example.run
    end
  end
end
```

```ruby
# spec/controllers/users_controller_spec.rb
require "spec_helper"

RSpec.describe UsersController do
  def app
    UsersController
  end

  describe "GET /users" do
    it "returns all users" do
      User.create!(name: "Alice", email: "alice@example.com")
      User.create!(name: "Bob", email: "bob@example.com")

      get "/users"

      expect(last_response).to be_ok
      expect(last_response.content_type).to include("application/json")

      body = JSON.parse(last_response.body)
      expect(body["users"].size).to eq(2)
    end
  end

  describe "POST /users" do
    it "creates a new user" do
      post "/users", { name: "Charlie", email: "charlie@example.com" }.to_json,
        "CONTENT_TYPE" => "application/json"

      expect(last_response.status).to eq(201)

      body = JSON.parse(last_response.body)
      expect(body["user"]["name"]).to eq("Charlie")
    end

    it "returns errors for invalid data" do
      post "/users", { name: "" }.to_json,
        "CONTENT_TYPE" => "application/json"

      expect(last_response.status).to eq(422)

      body = JSON.parse(last_response.body)
      expect(body["errors"]).not_to be_empty
    end
  end
end
```

### Testing with Headers and Sessions

```ruby
RSpec.describe ApiController do
  def app
    ApiController
  end

  it "requires authentication" do
    get "/protected"
    expect(last_response.status).to eq(401)
  end

  it "accepts valid API key" do
    get "/protected", {}, { "HTTP_AUTHORIZATION" => "Bearer valid_token" }
    expect(last_response).to be_ok
  end

  it "maintains session state" do
    post "/login", { username: "test", password: "pass" }.to_json
    expect(last_response).to be_ok

    # Session persists across requests in tests
    get "/dashboard"
    expect(last_response).to be_ok
  end
end
```

## Middleware Usage

Projects **SHOULD** use Rack middleware to implement cross-cutting concerns.

```ruby
# app/controllers/application_controller.rb
class ApplicationController < Sinatra::Base
  # Request parsing
  use Rack::JSONBodyParser  # Parse JSON request bodies

  # Security
  use Rack::Protection  # XSS, CSRF, etc.
  use Rack::Deflater    # Gzip compression

  # Logging
  use Rack::CommonLogger

  # Custom middleware
  use AuthenticationMiddleware
end
```

```ruby
# app/middleware/authentication_middleware.rb
class AuthenticationMiddleware
  def initialize(app)
    @app = app
  end

  def call(env)
    request = Rack::Request.new(env)

    # Skip authentication for public routes
    return @app.call(env) if public_route?(request.path)

    # Validate token
    token = request.env["HTTP_AUTHORIZATION"]&.split(" ")&.last
    unless valid_token?(token)
      return [401, { "Content-Type" => "application/json" },
        [{ error: "Unauthorized" }.to_json]]
    end

    # Add user to env
    env["current_user"] = User.find_by_token(token)
    @app.call(env)
  end

  private

  def public_route?(path)
    ["/health", "/login"].include?(path)
  end

  def valid_token?(token)
    token && User.exists?(token: token)
  end
end
```

### Common Middleware Stack

```ruby
class ApplicationController < Sinatra::Base
  # Parse request bodies
  use Rack::JSONBodyParser

  # CORS for APIs
  use Rack::Cors do
    allow do
      origins "*"
      resource "/api/*", headers: :any, methods: [:get, :post, :patch, :delete]
    end
  end

  # Rate limiting
  use Rack::Attack

  # Security headers
  use Rack::Protection, except: [:json_csrf]
  use Rack::Protection::StrictTransport  # HSTS

  # Logging and monitoring
  use Rack::CommonLogger
  use Rack::Runtime  # X-Runtime header

  # Error tracking (e.g., Sentry)
  use Sentry::Rack::CaptureExceptions if ENV["SENTRY_DSN"]
end
```

## Helpers and Extensions

Projects **SHOULD** use helpers to encapsulate common functionality.

```ruby
class ApplicationController < Sinatra::Base
  helpers do
    def json(data, status: 200)
      content_type :json
      halt status, data.to_json
    end

    def authenticate!
      halt 401, json(error: "Unauthorized") unless current_user
    end

    def current_user
      @current_user ||= User.find_by(id: session[:user_id])
    end

    def paginate(collection, page: 1, per_page: 25)
      page = [page.to_i, 1].max
      offset = (page - 1) * per_page
      collection.limit(per_page).offset(offset)
    end
  end
end
```

```ruby
class UsersController < ApplicationController
  before do
    authenticate! unless request.path_info == "/login"
  end

  get "/users" do
    users = paginate(User.all, page: params[:page])
    json users: users.map(&:to_h)
  end

  get "/profile" do
    json user: current_user.to_h
  end
end
```

### Extensions and Gems

Common Sinatra extensions **MAY** be used for additional functionality:

```ruby
# Gemfile
gem "sinatra-contrib"  # Common extensions
gem "sinatra-activerecord"  # ActiveRecord integration
gem "sinatra-flash"  # Flash messages

# app/controllers/application_controller.rb
require "sinatra/json"
require "sinatra/namespace"
require "sinatra/config_file"

class ApplicationController < Sinatra::Base
  register Sinatra::Namespace
  register Sinatra::ConfigFile

  config_file "config/settings.yml"

  namespace "/api/v1" do
    get "/status" do
      json status: "ok", version: "1.0.0"
    end
  end
end
```

## See Also

- [Ruby Style Guide](../languages/ruby.md) - Language-level Ruby conventions
- [Rails Style Guide](rails.md) - Full-featured MVC framework

## References

[^1]: [StandardRB](https://github.com/standardrb/standard) - Ruby style guide, linter, and formatter
[^2]: [rack-test](https://github.com/rack/rack-test) - Small, simple testing API for Rack apps
[^3]: [SimpleCov](https://github.com/simplecov-ruby/simplecov) - Code coverage analysis tool for Ruby
[^4]: [Sinatra](https://sinatrarb.com/) - DSL for quickly creating web applications in Ruby
