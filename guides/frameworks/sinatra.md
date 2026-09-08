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

Response helpers **MUST** take the payload as a positional argument, and every
code path **MUST** call `halt` at most once. Base controllers **MUST** parse
request bodies through a helper that checks the media type, caps the body size
and maps parse failures to a 4xx response.

```ruby
# app/controllers/application_controller.rb
require "json"
require "sinatra/base"

class ApplicationController < Sinatra::Base
  # Largest request body the API will read, in bytes.
  MAX_BODY_BYTES = 1_048_576

  configure do
    set :show_exceptions, :after_handler
    enable :sessions
  end

  helpers do
    def current_user
      @current_user ||= User.find_by(id: session[:user_id])
    end

    # The payload is positional and the status is a keyword, so the helper
    # cannot swallow the caller's payload into its own keyword arguments.
    def respond_json(payload, status: 200)
      content_type :json
      halt status, payload.to_json
    end

    # RFC 9457 problem details. This helper halts, so callers MUST NOT nest
    # it inside another halt.
    def problem(status, title, detail: nil, **members)
      content_type "application/problem+json"
      document = { type: "about:blank", title: title, status: status }
      document[:detail] = detail if detail
      halt status, document.merge(members).to_json
    end

    # Reads, size-caps and parses the request body. Returns a Hash or halts.
    def json_body
      unless request.media_type == "application/json"
        problem(415, "Unsupported media type",
          detail: "Send the body as application/json.")
      end

      raw = request.body.read(MAX_BODY_BYTES + 1).to_s
      if raw.bytesize > MAX_BODY_BYTES
        problem(413, "Payload too large",
          detail: "The body limit is #{MAX_BODY_BYTES} bytes.")
      end

      document = JSON.parse(raw)
      return document if document.is_a?(Hash)

      problem(400, "Malformed request body",
        detail: "The body must be a JSON object.")
    rescue JSON::ParserError => e
      problem(400, "Malformed request body", detail: e.message)
    end
  end

  # Keyed on the exception, not on the status, so that a route's own
  # `problem(404, ...)` response is not overwritten by this handler.
  error Sinatra::NotFound do
    problem(404, "Not found")
  end

  error StandardError do
    problem(500, "Internal server error")
  end
end
```

**Why a positional payload?** Ruby 3 separates positional and keyword
arguments. Given `def json(data, status: 200)`, the call `json error: "Not
found"` binds nothing to `data` and raises
`ArgumentError: wrong number of arguments (given 0, expected 1)`.

**Why one `halt`?** `halt` unwinds the request immediately by throwing
`:halt`. In `halt 401, respond_json({ error: "Unauthorized" })` the argument
is evaluated first, so the inner `halt 200` wins and the client receives
`200 {"error":"Unauthorized"}`. Pass the status to the helper instead.

**Why `error Sinatra::NotFound` rather than `error 404`?** A status-keyed
handler also fires for a deliberate `halt 404` from a route and replaces its
body, discarding the specific message. The exception-keyed handler only
covers unmatched routes.

Records **MUST NOT** be serialised with `to_h`: `ActiveRecord::Base` does not
define it. Models **MUST** expose an explicit allowlist instead.

```ruby
# app/models/user.rb
class User < ActiveRecord::Base
  PUBLIC_FIELDS = %w[id name email created_at].freeze

  validates :name, presence: true
  validates :email, presence: true

  # ActiveRecord::Base has no #to_h. Serialise an explicit allowlist so a new
  # column such as password_digest can never reach a response body.
  def public_attributes
    serializable_hash(only: PUBLIC_FIELDS)
  end
end
```

```ruby
# app/controllers/users_controller.rb
class UsersController < ApplicationController
  get "/users" do
    respond_json({ users: User.all.map(&:public_attributes) })
  end

  get "/users/:id" do
    user = User.find_by(id: params[:id])
    problem(404, "User not found") unless user
    respond_json({ user: user.public_attributes })
  end

  post "/users" do
    user = User.new(user_params)
    unless user.save
      problem(422, "Validation failed", errors: user.errors.full_messages)
    end
    respond_json({ user: user.public_attributes }, status: 201)
  end

  private

  def user_params
    json_body.slice("name", "email")
  end
end
```

**Why an allowlist?** `user.to_h` raises
`NoMethodError: undefined method 'to_h' for an instance of User` on
ActiveRecord 8.1. The obvious replacements, `as_json` and `serializable_hash`
with no arguments, return *every* column, so adding `password_digest` or
`token` to the table silently publishes it. Naming the fields makes the
response contract explicit and lets a test assert that secrets are absent.

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

Routes **SHOULD** follow RESTful conventions where applicable. Routes **MUST
NOT** report an outcome that did not happen: a missing record **MUST** return
404, and a route **MUST** branch on the result of `save` or `update` before
answering with a success status. Request bodies **MUST** be validated against
an explicit schema before they reach the model.

```ruby
# app/controllers/articles_controller.rb
require "json_schemer"

class ArticlesController < ApplicationController
  ARTICLE_SCHEMA = JSONSchemer.schema({
    "type" => "object",
    "additionalProperties" => false,
    "required" => ["title"],
    "properties" => {
      "title" => { "type" => "string", "minLength" => 1, "maxLength" => 200 },
      "body" => { "type" => "string", "maxLength" => 50_000 }
    }
  })

  # Index
  get "/articles" do
    respond_json({ articles: Article.all.map(&:public_attributes) })
  end

  # Show
  get "/articles/:id" do
    article = find_article!
    respond_json({ article: article.public_attributes })
  end

  # Create
  post "/articles" do
    article = Article.new(article_params)
    unless article.save
      problem(422, "Validation failed", errors: article.errors.full_messages)
    end
    respond_json({ article: article.public_attributes }, status: 201)
  end

  # Update
  patch "/articles/:id" do
    article = find_article!
    unless article.update(article_params)
      problem(422, "Validation failed", errors: article.errors.full_messages)
    end
    respond_json({ article: article.public_attributes })
  end

  # Delete
  delete "/articles/:id" do
    find_article!.destroy
    status 204
  end

  private

  def find_article!
    Article.find_by(id: params[:id]) || problem(404, "Article not found")
  end

  def article_params
    payload = json_body
    errors = ARTICLE_SCHEMA.validate(payload).map { |error| error.fetch("error") }
    problem(422, "Validation failed", errors: errors) if errors.any?
    payload.slice("title", "body")
  end
end
```

**Why check every outcome?** The unchecked variant of this controller answers
`201 {"article":{"id":null,...}}` for input that failed validation, `200` for
an update that was rejected, and `500` for both a missing record and a
malformed body, because `Article.find` raises `ActiveRecord::RecordNotFound`
and `JSON.parse` raises `JSON::ParserError` with nothing to catch them. A
client cannot distinguish "created" from "silently discarded".

`Article` defines `public_attributes` the same way as `User` above.

**Why `find_by` rather than a rescue?** `Article.find_by(id:)` returns `nil`
for a missing row, so the route decides the status itself. A blanket
`rescue ActiveRecord::RecordNotFound` around the whole route also swallows
not-found errors raised deeper in the call stack and reports them as a client
error.

Don't:

```ruby
post "/articles" do
  @article = Article.create(article_params)  # Returns an unsaved record
  status 201                                 # ...and claims success anyway
  json article: @article
end
```

Do:

```ruby
post "/articles" do
  article = Article.new(article_params)
  unless article.save
    problem(422, "Validation failed", errors: article.errors.full_messages)
  end
  respond_json({ article: article.public_attributes }, status: 201)
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

## JSON Requests and Error Responses

APIs **MUST** apply the following request policy before any handler touches a
model, and **MUST** use a single error representation across every failure.

| Condition | Status | Enforced by |
| --------- | ------ | ----------- |
| Media type is not `application/json` | 415 | `json_body` |
| Body exceeds `MAX_BODY_BYTES` | 413 | `json_body` |
| Body is not well-formed JSON | 400 | `json_body` |
| Body is well-formed but not an object | 400 | `json_body` |
| Body fails the route schema | 422 | `JSONSchemer` |
| Record does not exist | 404 | route |
| Persistence fails | 422 | route |

Applications **MUST** choose exactly one JSON parsing path, and **SHOULD**
serve errors as RFC 9457[^5] problem details with the
`application/problem+json` media type.

**Why one parser?** Stacking `Rack::JSONBodyParser`[^6] in front of an
in-route parser makes the request contract ambiguous, and the middleware
writes whatever it parsed into `rack.request.form_hash`. A well-formed
top-level array such as `[1, 2, 3]` therefore replaces the params hash, and
Sinatra fails with `TypeError: no implicit conversion of Array into Hash`,
producing a 500 for a malformed *request*. The middleware also answers with
its own `{"error": ...}` shape, which will not match the rest of the API.

**Why a size cap?** Without one, a single request can force the process to
buffer an unbounded body; OWASP tracks this as API4:2023 Unrestricted
Resource Consumption[^7]. `request.body.read(MAX_BODY_BYTES + 1)` reads one
byte past the limit, which is enough to detect an overrun without holding the
whole payload.

**Why reject non-object bodies?** `JSON.parse("[1,2,3]")` succeeds, so a
`rescue JSON::ParserError` alone does not protect the route: `payload.slice`
then fails with `NoMethodError` and the client sees a 500 instead of a 400.

Don't:

```ruby
def article_params
  JSON.parse(request.body.read).slice("title", "body")
end
```

Do:

```ruby
def article_params
  payload = json_body  # 415, 413 or 400 before this returns
  errors = ARTICLE_SCHEMA.validate(payload).map { |error| error.fetch("error") }
  problem(422, "Validation failed", errors: errors) if errors.any?
  payload.slice("title", "body")
end
```

A problem document from the `problem` helper looks like this:

```json
{
  "type": "about:blank",
  "title": "Validation failed",
  "status": 422,
  "errors": ["string length at `/title` is less than: 1"]
}
```

Tests **MUST** cover every branch of the table above:

```ruby
# spec/controllers/users_controller_spec.rb
it "returns 415 for a non-JSON media type" do
  post "/users", "name=Charlie",
    "CONTENT_TYPE" => "application/x-www-form-urlencoded"

  expect(last_response.status).to eq(415)
end

it "returns 400 for malformed JSON" do
  post "/users", "{oops", "CONTENT_TYPE" => "application/json"

  expect(last_response.status).to eq(400)
end

it "returns 400 for a non-object body" do
  post "/users", "[1, 2, 3]", "CONTENT_TYPE" => "application/json"

  expect(last_response.status).to eq(400)
end

it "returns 413 for an oversized body" do
  oversized = { name: "a" * (ApplicationController::MAX_BODY_BYTES + 1) }

  post "/users", oversized.to_json, "CONTENT_TYPE" => "application/json"

  expect(last_response.status).to eq(413)
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

Projects **MUST** use rack-test[^2] for testing Sinatra applications. Every
constant a test helper references **MUST** be declared as a pinned dependency
and required before use.

```ruby
# Gemfile
group :test do
  gem "database_cleaner-active_record", "~> 2.2.2"
  gem "rack-test", "~> 2.2.0"
  gem "rspec", "~> 3.13.2"
end
```

```ruby
# spec/spec_helper.rb
ENV["RACK_ENV"] = "test"

require_relative "../config/environment"
require "database_cleaner/active_record"
require "rack/test"
require "rspec"

RSpec.configure do |config|
  config.include Rack::Test::Methods

  config.before(:suite) do
    DatabaseCleaner[:active_record].strategy = :transaction
  end

  config.around(:each) do |example|
    DatabaseCleaner[:active_record].cleaning do
      example.run
    end
  end
end
```

**Why the explicit require and adapter?** `database_cleaner` is a family of
gems; the `DatabaseCleaner` constant arrives with an adapter, not with
Sinatra, ActiveRecord or rack-test. Without
`gem "database_cleaner-active_record"` and its require, the `before(:suite)`
hook above raises `NameError: uninitialized constant DatabaseCleaner` and no
example in the suite runs. Selecting the cleaner with
`DatabaseCleaner[:active_record]` also keeps the setting explicit when a
second adapter (Redis, Mongoid) is added later.

**Why not always `:transaction`?** The transaction strategy simply rolls the
work back, which is the fastest option, but it only covers the connection the
test itself uses. Tests whose application runs in a different process — a
Capybara system test against a booted server, or a background worker — do not
share that transaction and **MUST** use `:truncation` or `:deletion`
instead.[^9]

```ruby
# spec/controllers/users_controller_spec.rb
require "spec_helper"

RSpec.describe UsersController do
  def app
    UsersController
  end

  describe "GET /users" do
    it "returns all users without sensitive columns" do
      User.create!(name: "Alice", email: "alice@example.com",
        password_digest: "secret")
      User.create!(name: "Bob", email: "bob@example.com")

      get "/users"

      expect(last_response).to be_ok
      expect(last_response.content_type).to include("application/json")

      body = JSON.parse(last_response.body)
      expect(body["users"].size).to eq(2)
      expect(body["users"].first.keys)
        .to contain_exactly("id", "name", "email", "created_at")
    end
  end

  describe "GET /users/:id" do
    it "returns 404 for a missing user" do
      get "/users/999"

      expect(last_response.status).to eq(404)
      expect(last_response.content_type).to include("application/problem+json")
      expect(JSON.parse(last_response.body)["title"]).to eq("User not found")
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

    it "returns errors for invalid data and persists nothing" do
      post "/users", { name: "" }.to_json,
        "CONTENT_TYPE" => "application/json"

      expect(last_response.status).to eq(422)
      expect(User.count).to eq(0)

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
Every middleware constant a project references **MUST** come from a pinned
gem that the application requires explicitly.

```ruby
# Gemfile
source "https://rubygems.org"

gem "json_schemer", "~> 2.5.0"
gem "rack", "~> 3.2.7"
gem "rack-attack", "~> 6.8.0"
gem "rack-cors", "~> 3.0.0"
gem "sentry-ruby", "~> 7.0.0"
gem "sinatra", "~> 4.2.1"
```

```ruby
# app/controllers/application_controller.rb
require "rack/attack"
require "rack/cors"
require "rack/deflater"
require "rack/protection"
require "sentry-ruby"
require "sinatra/base"

class ApplicationController < Sinatra::Base
  # Security
  use Rack::Protection  # XSS, CSRF, etc.
  use Rack::Deflater    # Gzip compression

  # Logging
  use Rack::CommonLogger

  # Custom middleware
  use AuthenticationMiddleware
end
```

**Why explicit requires?** `Rack::Attack`, `Rack::Cors` and
`Sentry::Rack::CaptureExceptions` are not part of Rack or Sinatra; after
`require "sinatra/base"` all three constants are undefined and `use` raises
`NameError` at class-definition time. `Bundler.require` is not a substitute:
rack-cors and rack-attack ship only `lib/rack/cors.rb` and
`lib/rack/attack.rb`, so Bundler's default `require "rack-cors"` fails with
`LoadError`. Either require the entry points as above, or declare
`gem "rack-cors", "~> 3.0.0", require: "rack/cors"`.

`Rack::JSONBodyParser` is deliberately absent — see
[JSON Requests and Error Responses](#json-requests-and-error-responses) for
why the body is parsed in the route helper instead.

```ruby
# app/middleware/authentication_middleware.rb
require "json"
require "rack"

class AuthenticationMiddleware
  PUBLIC_PATHS = ["/health", "/login"].freeze

  def initialize(app)
    @app = app
  end

  def call(env)
    request = Rack::Request.new(env)

    # Skip authentication for public routes
    return @app.call(env) if PUBLIC_PATHS.include?(request.path)

    # Validate token
    token = request.get_header("HTTP_AUTHORIZATION")&.split(" ")&.last
    user = token && User.find_by(token: token)
    return unauthorized unless user

    # Add user to env
    env["current_user"] = user
    @app.call(env)
  end

  private

  # Rack 3 response header names MUST be lower case.
  def unauthorized
    document = { type: "about:blank", title: "Unauthorized", status: 401 }
    [401, { "content-type" => "application/problem+json" },
      [document.to_json]]
  end
end
```

**Why lower-case header names?** Rack 3 requires every response header name
to be lower case so that servers no longer have to normalise them.[^8]
Returning `"Content-Type"` fails validation with
`Rack::Lint::LintError: uppercase character in header name: Content-Type`,
and Sinatra 4 runs on Rack 3.

Custom middleware **MUST** be exercised through `Rack::Lint` so that an
invalid response shape fails a test rather than a deployment:

```ruby
# spec/middleware/authentication_middleware_spec.rb
require "spec_helper"
require "rack/lint"

RSpec.describe AuthenticationMiddleware do
  def app
    Rack::Lint.new(
      AuthenticationMiddleware.new(->(_env) { [200, {}, []] })
    )
  end

  it "returns a Rack 3-compliant 401 for an unauthenticated request" do
    get "/users"

    expect(last_response.status).to eq(401)
    expect(last_response.headers["content-type"])
      .to eq("application/problem+json")
  end

  it "passes public paths through" do
    get "/health"

    expect(last_response.status).to eq(200)
  end
end
```

### Common Middleware Stack

```ruby
require "rack/attack"
require "rack/cors"
require "rack/protection"
require "sentry-ruby"

class ApiController < ApplicationController
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

Projects **SHOULD** use helpers to encapsulate common functionality. A helper
that calls `halt` **MUST NOT** be used as an argument to another `halt`.

```ruby
class ApplicationController < Sinatra::Base
  helpers do
    def authenticate!
      # A single halt. `halt 401, problem(...)` would evaluate the argument
      # first, so the inner halt would answer with its own status instead.
      problem(401, "Unauthorized") unless current_user
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

Don't:

```ruby
def authenticate!
  # Two bugs. `json(error: "Unauthorized")` raises ArgumentError under Ruby 3
  # because nothing binds to the positional parameter; written positionally as
  # `json({ error: "Unauthorized" })` the inner halt wins and the client
  # receives `200 {"error":"Unauthorized"}`.
  halt 401, json(error: "Unauthorized") unless current_user
end
```

Do:

```ruby
def authenticate!
  problem(401, "Unauthorized") unless current_user
end
```

```ruby
class UsersController < ApplicationController
  before do
    authenticate! unless request.path_info == "/login"
  end

  get "/users" do
    users = paginate(User.all, page: params[:page])
    respond_json({ users: users.map(&:public_attributes) })
  end

  get "/profile" do
    respond_json({ user: current_user.public_attributes })
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
[^5]: [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) - Problem Details for HTTP APIs
[^6]: [Rack::JSONBodyParser](https://github.com/rack/rack-contrib/blob/main/lib/rack/contrib/json_body_parser.rb) - rack-contrib JSON body middleware
[^7]: [OWASP API4:2023](https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/) - Unrestricted Resource Consumption
[^8]: [Rack 3 upgrade guide](https://github.com/rack/rack/blob/main/UPGRADE-GUIDE.md) - Response headers must be lower case
[^9]: [DatabaseCleaner](https://github.com/DatabaseCleaner/database_cleaner#what-strategy-is-fastest) - Strategy trade-offs for multi-process tests
