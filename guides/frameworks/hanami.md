# Hanami Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > Hanami

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119][rfc2119].

[rfc2119]: https://datatracker.ietf.org/doc/html/rfc2119

Extends [Ruby style guide](../languages/ruby.md) with Hanami-specific conventions.

**Target Version**: Hanami 3.0.x with Ruby 4.0 (minimum Ruby 3.3)

These examples target Hanami 3.0 and were written and run against Hanami
3.0.2[^4] with hanami-db 3.0.0, hanami-view 3.0.2 and hanami-router 3.0.0.
Projects **MUST NOT** target Hanami 2.2 while using them: the
`resource`/`resources` routing DSL used under [Routing](#routing) was added in
Hanami 2.3.0, and the persistence, view and settings APIs shown here are the
3.0 ones.

## Quick Reference

All Ruby tooling applies. Additional considerations:

| Task | Tool | Command |
| ---- | ---- | ------- |
| Lint | StandardRB[^1] | `bundle exec standardrb` |
| Test | RSpec | `bundle exec rspec` |
| Console | Hanami CLI | `bundle exec hanami console` |
| Server | Hanami CLI | `bundle exec hanami server` |

## Why Hanami?

Hanami[^2] is ideal for architecture-focused web development because it:

- **Clean architecture**: Enforces separation of concerns with distinct layers (actions, views,
  entities, repositories)
- **Explicit over implicit**: No magic; dependencies are explicit and configuration is clear
- **Testability**: Framework designed for testing with minimal setup and fast test suites
- **Modular monoliths**: Slices architecture allows organizing code into bounded contexts within
  a single application
- **ROM integration**: Uses Ruby Object Mapper (ROM) for flexible, powerful data persistence
- **Dependency injection**: Built-in container for managing dependencies and testing
- **Modern Ruby**: Built for Ruby 3.x+ with performance and developer experience in mind

Use Hanami for greenfield applications where clean architecture matters, especially
domain-driven designs and modular monoliths. Choose Rails for rapid prototyping with extensive
ecosystem, or Sinatra for simple APIs and microservices.

## Project Structure (Slices Architecture)

Projects **SHOULD** organize code using Hanami's slices architecture. Each
slice represents a bounded context or feature area.

```text
my_app/
├── app/
│   ├── actions/           # App-level actions
│   ├── views/             # App-level views
│   ├── db/                # Relation, repo and struct base classes
│   ├── relations/         # Shared relations
│   ├── repos/             # Shared repositories
│   └── structs/           # Shared structs
├── slices/
│   ├── admin/
│   │   ├── actions/       # Admin-specific actions
│   │   │   └── users/
│   │   │       ├── index.rb
│   │   │       ├── show.rb
│   │   │       └── create.rb
│   │   ├── views/         # Admin views
│   │   ├── repos/         # Admin-only data access
│   │   └── structs/       # Admin-only domain objects
│   ├── api/
│   │   ├── actions/
│   │   │   └── v1/
│   │   │       └── posts/
│   │   │           ├── index.rb
│   │   │           └── create.rb
│   │   └── serializers/
│   └── web/               # Public web interface
│       ├── actions/
│       ├── views/
│       │   └── parts/     # Presentation logic for exposed values
│       └── templates/
├── config/
│   ├── app.rb             # Application configuration
│   ├── routes.rb          # Route definitions
│   ├── db/migrate/        # Database migrations
│   ├── providers/         # Dependency injection providers
│   └── settings.rb        # Environment settings
├── lib/
│   └── my_app/
│       └── types.rb       # Custom types
└── spec/
    ├── slices/
    │   ├── admin/
    │   └── api/
    └── support/
```

**Why slices?** Slices provide:

- Clear boundaries between features
- Independent testing of each slice
- Easier refactoring and code navigation
- Natural evolution from monolith to microservices
- Shared code only where needed

## Actions and Views (Separated Concerns)

Actions **MUST** handle HTTP concerns only. Views **MUST** handle presentation logic. This
separation ensures testability and maintainability.

### Actions

```ruby
# slices/web/actions/posts/index.rb
module Web
  module Actions
    module Posts
      class Index < Web::Action
        include Deps["repos.post_repo"]

        def handle(_request, response)
          response.render view, posts: post_repo.published
        end
      end
    end
  end
end
```

```ruby
# slices/api/actions/v1/posts/create.rb
module API
  module Actions
    module V1
      module Posts
        class Create < API::Action
          include Deps[
            repo: "repos.post_repo",
            validator: "validators.post"
          ]

          def handle(request, response)
            result = validator.call(request.params[:post])

            if result.success?
              post = repo.create(result.to_h)
              response.status = 201
              response.format = :json
              response.body = { post: serialize(post) }.to_json
            else
              response.status = 422
              response.format = :json
              response.body = { errors: result.errors.to_h }.to_json
            end
          end

          private

          def serialize(post)
            {
              id: post.id,
              title: post.title,
              body: post.body,
              created_at: post.created_at.iso8601
            }
          end
        end
      end
    end
  end
end
```

### Before/After Callbacks

Sessions are disabled by default, so an action that reads `request.session`
**MUST** be backed by session configuration in the app class, and every
collaborator a callback uses **MUST** be declared through `Deps`. Callbacks
**MUST NOT** store per-request state in instance variables: Hanami memoises one
action instance per component key and reuses it across requests. Pass state
between callbacks through `response[]` instead.

**Why**: an action that reads a disabled session, calls an undeclared method or
mutates shared instance state either raises on the first request or leaks one
visitor's identity into another's.

```ruby
# config/app.rb
require "hanami"

module MyApp
  class App < Hanami::App
    config.actions.sessions = :cookie, {
      key: "my_app.session",
      secret: settings.session_secret,
      expire_after: 60 * 60 * 24 * 7,
      secure: Hanami.env?(:production),
      httponly: true,
      same_site: :lax
    }

    # Repos live in the app container; slices only receive the standard
    # components unless the app shares them explicitly.
    config.shared_app_component_keys += ["repos.post_repo", "repos.user_repo"]
  end
end
```

```ruby
# app/repos/user_repo.rb
module MyApp
  module Repos
    class UserRepo < MyApp::DB::Repo
      # `one` returns nil for an unknown id; `one!` would raise.
      def find(id) = users.by_pk(id).one
    end
  end
end
```

```ruby
# app/structs/user.rb
module MyApp
  module Structs
    class User < MyApp::DB::Struct
      # The column is `admin`; ROM structs expose it without the question mark.
      def admin? = admin
    end
  end
end
```

```ruby
# slices/admin/actions/dashboard/index.rb
module Admin
  module Actions
    module Dashboard
      class Index < Admin::Action
        include Deps["repos.user_repo"]

        before :authenticate!
        before :authorize!

        def handle(_request, response)
          response.render view
        end

        private

        # Authentication: is there a real user behind this session?
        def authenticate!(request, response)
          user_id = request.session[:user_id]
          halt 401 unless user_id

          user = user_repo.find(user_id)
          halt 401 unless user

          response[:current_user] = user
        end

        # Authorisation: is that user allowed here?
        def authorize!(_request, response)
          halt 403 unless response[:current_user].admin?
        end
      end
    end
  end
end
```

A stale `user_id` — a session cookie for a deleted account — **MUST** produce
401 rather than a `NoMethodError` on `nil`. Cover all four cases:

```ruby
# spec/requests/admin_spec.rb
RSpec.describe "Admin dashboard", :db, type: :request do
  let(:users) { Hanami.app["relations.users"] }

  def sign_in(user_id) = env("rack.session", {user_id: user_id})

  it "returns 401 without a session" do
    get "/admin"
    expect(last_response.status).to be(401)
  end

  it "returns 401 for a stale session id" do
    sign_in(12_345)
    get "/admin"
    expect(last_response.status).to be(401)
  end

  it "returns 403 for a non-admin user" do
    sign_in(users.changeset(:create, email: "a@example.com", admin: false).commit[:id])
    get "/admin"
    expect(last_response.status).to be(403)
  end

  it "renders the dashboard for an admin user" do
    sign_in(users.changeset(:create, email: "root@example.com", admin: true).commit[:id])
    get "/admin"
    expect(last_response.status).to be(200)
  end
end
```

### Views and Templates

Views **SHOULD** contain presentation logic only, never business logic.

Presentation behaviour attached to a domain object **MUST** live in a Hanami
View part rather than an ad hoc presenter class. Exposures are undecorated by
default in Hanami 3, so a view **MUST** ask for decoration explicitly with
`decorate` or `decorate: true`.

**Why**: parts are resolved by the framework from the exposure name, are bound
to the value they decorate, and can be tested in isolation. A hand-rolled
presenter has to be instantiated by hand in every exposure, and — as below — is
easy to place at a path Zeitwerk cannot load.

```ruby
# slices/web/views/posts/index.rb
module Web
  module Views
    module Posts
      class Index < Web::View
        # The action supplies `posts:`; `decorate` exposes that input and wraps
        # each element in Web::Views::Parts::Post.
        decorate :posts

        expose :page_title do
          "All Posts"
        end
      end
    end
  end
end
```

Exposure block parameters are not interchangeable. A **keyword** parameter reads
view input; a **positional** parameter names another exposure to depend on. Given
an action calling `response.render view, posts: post_repo.published`:

```ruby
# Don't: `posts` is read as a dependency on an exposure named :posts,
# which does not exist. Rendering raises KeyError: key not found: :posts.
expose :posts do |posts|
  posts
end

# Do: a keyword parameter reads the supplied input.
expose :posts, decorate: true do |posts:|
  posts
end
```

```erb
<!-- slices/web/templates/posts/index.html.erb -->
<h1><%= page_title %></h1>

<ul>
  <% posts.each do |post| %>
    <li>
      <h2><%= post.title %></h2>
      <p><%= post.excerpt %></p>
      <small>Posted <%= post.published_at_formatted %></small>
    </li>
  <% end %>
</ul>
```

Parts live under `Views::Parts` in the app or slice, and the file path **MUST**
match the constant path: Hanami autoloads with Zeitwerk, so
`slices/web/views/parts/post.rb` **MUST** define `Web::Views::Parts::Post`.
Part methods **MUST NOT** depend on undeclared core-class extensions such as
ActiveSupport's `String#truncate`.

**Why**: a file whose constant path does not match its location raises
`Zeitwerk::NameError` on eager load and `NameError` on first reference in
development. `String#truncate` is not part of Ruby or of any gem this guide
declares, so `"body".truncate(200)` raises `NoMethodError` on the first render.

```ruby
# slices/web/views/parts/post.rb
module Web
  module Views
    module Parts
      class Post < Web::Views::Part
        EXCERPT_LENGTH = 200
        ELLIPSIS = "\u2026"

        def excerpt
          text = body.to_s
          return text if text.length <= EXCERPT_LENGTH

          "#{text[0, EXCERPT_LENGTH].rstrip}#{ELLIPSIS}"
        end

        def published_at_formatted = created_at.strftime("%B %d, %Y")
      end
    end
  end
end
```

`String#[]` and `String#length` count characters, not bytes, so this truncation
is multibyte-safe. Test the boundaries:

```ruby
# spec/slices/web/views/parts/post_spec.rb
RSpec.describe Web::Views::Parts::Post do
  def part(body)
    described_class.new(value: Struct.new(:body, :created_at).new(body, Time.now))
  end

  it "returns a short body unchanged" do
    expect(part("short").excerpt).to eq("short")
  end

  it "truncates a long body" do
    expect(part("b" * 500).excerpt).to eq("#{"b" * 200}\u2026")
  end

  it "handles empty and nil bodies" do
    expect(part("").excerpt).to eq("")
    expect(part(nil).excerpt).to eq("")
  end

  it "truncates multibyte bodies by character" do
    expect(part("\u3042" * 500).excerpt.length).to eq(201)
  end
end
```

## Repositories and Relations (ROM-based Persistence)

Hanami uses ROM (Ruby Object Mapper)[^3] for data persistence. Repositories **MUST** encapsulate
all data access. Relations **SHOULD** define queries and transformations.

Hanami 3 has no `Hanami::Entity` and no `Hanami::DB::Repository`. The three
persistence base classes are `Hanami::DB::Relation`, `Hanami::DB::Repo` and
`Hanami::DB::Struct`, each subclassed once per app or slice in
`app/db/{relation,repo,struct}.rb` by `hanami new`. Concrete classes **MUST**
inherit from those local base classes and live in the generated `Relations`,
`Repos` and `Structs` namespaces.

**Why**: `Hanami::Entity` and `Hanami::DB::Repository` do not exist — referencing
either raises `NameError` before any query runs. The namespaces are the
conventional locations the generators use and the ones the container's
auto-registration and struct lookup expect (`repos.post_repo`,
`MyApp::Structs::Post`).

### Structs

Structs are the output of a repository: immutable projections of requested data,
with no persistence logic. Attribute types come from the relation schema, so a
struct class is only needed when adding behaviour.

```ruby
# app/structs/post.rb
module MyApp
  module Structs
    class Post < MyApp::DB::Struct
      def draft? = !published
    end
  end
end
```

### Relations

```ruby
# app/relations/posts.rb
module MyApp
  module Relations
    class Posts < MyApp::DB::Relation
      schema :posts, infer: true do
        associations do
          belongs_to :author
        end
      end

      def published = where(published: true).order { created_at.desc }

      def by_author(author_id) = where(author_id: author_id)

      def recent(limit = 10) = order { created_at.desc }.limit(limit)
    end
  end
end
```

### Repositories

Repositories **MUST** provide a clean interface for data operations. Writes
**MUST** go through a ROM changeset or command; relations expose no `create`,
and `update`/`delete` on a relation return affected rows rather than the
struct the caller needs.

**Why**: `posts.create(attributes)` raises `NoMethodError`. A changeset returns
the committed struct, so callers can read the generated `id` without a second
query, and `map(:add_timestamps)`/`map(:touch)` fill `created_at`/`updated_at`
without the caller supplying them.

```ruby
# app/repos/post_repo.rb
module MyApp
  module Repos
    class PostRepo < MyApp::DB::Repo
      def all = posts.to_a
      def published = posts.published.to_a
      def get!(id) = posts.by_pk(id).one!
      def recent(limit: 10) = posts.recent(limit).to_a
      def by_author(author_id) = posts.by_author(author_id).to_a

      def create(attributes)
        posts.changeset(:create, attributes).map(:add_timestamps).commit
      end

      def update(id, attributes)
        posts.by_pk(id).changeset(:update, attributes).map(:touch).commit
      end

      def delete(id) = posts.by_pk(id).changeset(:delete).commit

      # Associated data, loaded through the relation's associations
      def with_author(id) = posts.by_pk(id).combine(:author).one!
    end
  end
end
```

## Dependency Injection Container

Hanami's dependency injection container **SHOULD** be used for managing dependencies. This
improves testability and makes dependencies explicit.

### Providers

Providers **SHOULD** define how dependencies are created and configured.

A provider **MUST** resolve everything it needs from `target` into local
variables *before* entering a third-party DSL that is instance-evaluated.

**Why**: `Mail.defaults` runs its block through
`Configuration.instance.instance_eval`, so `self` inside the block is a
`Mail::Configuration`. `target` is a method on the provider source, not on that
object, and calling it there raises
`NameError: undefined local variable or method 'target'`. Local variables, by
contrast, are captured by the block's closure and remain visible.

```ruby
# config/providers/mailer.rb
Hanami.app.register_provider :mailer do
  prepare do
    require "mail"
  end

  start do
    settings = target["settings"]

    smtp_options = {
      address: settings.smtp_host,
      port: settings.smtp_port,
      user_name: settings.smtp_username,
      password: settings.smtp_password,
      authentication: :plain,
      enable_starttls_auto: true
    }

    # Never open an SMTP connection from the test suite.
    adapter, adapter_options =
      Hanami.env?(:test) ? [:test, {}] : [:smtp, smtp_options]

    Mail.defaults do
      delivery_method adapter, adapter_options
    end

    register "mailer", Mail
  end
end
```

Every setting the provider reads — `smtp_host`, `smtp_port`, `smtp_username`,
`smtp_password` — **MUST** be declared in `config/settings.rb`; see
[Configuration and Settings](#configuration-and-settings).

### Using Dependencies

Request parameters are untrusted input. An action that writes to the database
**MUST** declare a `params` schema covering only the writable fields, **MUST**
check `request.params.valid?` before persisting, and **MUST** pass the validated
result — never the raw request hash — to the repository.

**Why**: `repo.create(request.params[:post])` forwards every key the client
sent. Posting `post[id]=4321&post[author_id]=1&post[published]=true` against that
action writes all three straight into the row, letting a visitor choose primary
keys, reassign authorship and publish without review. A schema discards anything
it does not name.

```ruby
# slices/web/actions/posts/create.rb
module Web
  module Actions
    module Posts
      class Create < Web::Action
        include Deps[
          repo: "repos.post_repo",
          logger: "logger"
        ]

        params do
          required(:post).hash do
            required(:title).filled(:string, min_size?: 5)
            required(:body).filled(:string)
            optional(:published).filled(:bool)
          end
        end

        def handle(request, response)
          unless request.params.valid?
            response.status = 422
            response.render view, errors: request.params.errors
            return
          end

          post = repo.create(request.params[:post])
          logger.info "Post created: #{post.id}"
          response.redirect_to routes.path(:post, id: post.id)
        end
      end
    end
  end
end
```

Prove the allowlist rather than assuming it:

```ruby
# spec/requests/posts_spec.rb
RSpec.describe "Posts", :db, type: :request do
  let(:post_repo) { Hanami.app["repos.post_repo"] }

  it "discards params outside the allowlist" do
    post "/posts", post: {title: "Valid title", body: "Body", id: 999, author_id: 42}

    expect(last_response.status).to be(302)
    created = post_repo.all.last
    expect(created.id).not_to eq(999)
    expect(created.author_id).to be_nil
  end

  it "rejects invalid input without persisting" do
    post "/posts", post: {title: "no", body: ""}

    expect(last_response.status).to be(422)
    expect(post_repo.all).to be_empty
  end
end
```

### Testing with Dependency Injection

```ruby
# spec/slices/web/actions/posts/create_spec.rb
RSpec.describe Web::Actions::Posts::Create do
  let(:repo) { instance_double("MyApp::Repos::PostRepo", create: double("post", id: 1)) }
  let(:logger) { instance_double("Logger", info: nil) }
  let(:action) { described_class.new(repo: repo, logger: logger) }

  it "creates a post and logs" do
    action.call(post: {title: "Test title", body: "Body"})

    expect(repo).to have_received(:create)
    expect(logger).to have_received(:info).with("Post created: 1")
  end
end
```

See [Testing Actions](#testing-actions) for the full set of cases.

## Configuration and Settings

Projects **MUST** use environment-specific settings. Settings **SHOULD** be type-safe using Dry::Types.

Settings sourced from the environment **MUST** use the `Types::Params::*`
coercing constructors, not the strict `Types::*` ones. Security-sensitive
settings **SHOULD** carry a constraint.

**Why**: environment variables always arrive as strings. `PORT=2300` with
`constructor: Types::Integer` raises
`Dry::Types::ConstraintError: "2300" violates constraints`, and `ENABLE_API=false`
with `Types::Bool` fails the same way — the app refuses to boot the moment
anyone sets the variable. `Types::Params::Integer` and `Types::Params::Bool`
coerce `"2300"` to `2300` and `"false"` to `false`. Constraining
`session_secret` to Hanami's documented minimum of 32 characters stops a short,
guessable cookie-signing key reaching production.

```ruby
# config/settings.rb
module MyApp
  class Settings < Hanami::Settings
    setting :database_url, constructor: Types::String
    setting :port, default: 2300, constructor: Types::Params::Integer
    setting :host, default: "0.0.0.0", constructor: Types::String
    setting :enable_api, default: true, constructor: Types::Params::Bool
    setting :session_secret, constructor: Types::String.constrained(min_size: 32)
    setting :smtp_host, constructor: Types::String
    setting :smtp_port, default: 587, constructor: Types::Params::Integer
    setting :smtp_username, constructor: Types::String.optional
    setting :smtp_password, constructor: Types::String.optional
  end
end
```

Secrets **MUST NOT** be committed. Hanami loads `.env.{environment}.local`
before `.env.{environment}` and `.env`, so keep shared, non-secret defaults in
the tracked files and real secrets in the ignored `.local` ones:

```ini
# .env (tracked, loaded in development and test: no secrets)
DATABASE_URL=sqlite://db/my_app.sqlite
PORT=2300
ENABLE_API=false
SMTP_HOST=localhost
SMTP_PORT=1025
```

```ini
# .env.test (tracked: throwaway value, never used to sign a real session)
SESSION_SECRET=0000000000000000000000000000000000000000000000000000000000000000
```

```ini
# .env.development.local (git-ignored; development only)
SESSION_SECRET=0f2b4d6e8a0c2e4f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7
SMTP_USERNAME=mailer@example.com
SMTP_PASSWORD=replace-me
```

`.env.local` is not loaded in the test environment, which is why the test secret
lives in `.env.test`. Production **MUST** supply `SESSION_SECRET` and the SMTP
credentials from the deployment environment or a secret manager, never from a
dotenv file.

```ruby
# spec/guide/settings_spec.rb
RSpec.describe MyApp::Settings do
  it "coerces string environment values" do
    settings = described_class.new(
      database_url: "sqlite://db/x.sqlite",
      port: "2300",
      enable_api: "false",
      session_secret: "0" * 64,
      smtp_host: "localhost"
    )

    expect(settings.port).to eq(2300)
    expect(settings.enable_api).to be(false)
  end

  it "rejects a short session secret" do
    expect {
      described_class.new(
        database_url: "sqlite://db/x.sqlite",
        session_secret: "short",
        smtp_host: "localhost"
      )
    }.to raise_error(Hanami::Settings::InvalidSettingsError, /session_secret/)
  end
end
```

## Routing

Routes **MUST** be defined in `config/routes.rb`. Routes **SHOULD** be organized by slice.

A route target names an action *within* the container it is resolved against;
the resolver supplies the `actions.` prefix itself. App-level routes therefore
target `"home.index"`, and routes inside `slice :web` target `"posts.index"`.
`scope` changes only path and route-name prefixes, so a versioned resource
**MUST** name its action namespace with `to:`.

**Why**: the resolver concatenates `actions.` with the given target. Booting
`root to: "web.actions.home.index"` and requesting `/` raises
`Hanami::Routes::MissingActionError: Could not find action with key
"actions.web.actions.home.index" in MyApp::App`; `to: "actions.posts.index"`
inside a slice looks for `actions.actions.posts.index`. Likewise
`scope "/v1" { resources :posts }` generates `to: "posts.create"`, which never
reaches `API::Actions::V1::Posts::Create` — only
`resources :posts, to: "v1.posts"` produces `v1.posts.create`.

```ruby
# config/routes.rb
module MyApp
  class Routes < Hanami::Routes
    root to: "home.index"

    slice :web, at: "/" do
      get "/posts", to: "posts.index"
      get "/posts/:id", to: "posts.show", as: :post
      post "/posts", to: "posts.create"
    end

    slice :admin, at: "/admin" do
      get "/", to: "dashboard.index"
      resources :users, only: [:index, :show, :create]
    end

    slice :api, at: "/api" do
      scope "/v1" do
        resources :posts, to: "v1.posts", only: [:index, :show, :create, :update, :destroy]
      end
    end

    get "/health", to: ->(*) { [200, {}, ["OK"]] }
  end
end
```

`bundle exec hanami routes` prints the resolved target and helper name for every
route, and **SHOULD** be checked after editing this file:

```text
GET     /                    home.index          as :root
GET     /posts               posts.index
GET     /posts/:id           posts.show          as :post
POST    /posts               posts.create
GET     /admin               dashboard.index
GET     /admin/users         users.index         as :admin_users
GET     /admin/users/:id     users.show          as :admin_user
POST    /admin/users         users.create        as :admin_users
GET     /api/v1/posts        v1.posts.index      as :api_v1_posts
GET     /api/v1/posts/:id    v1.posts.show       as :api_v1_post
POST    /api/v1/posts        v1.posts.create     as :api_v1_posts
PATCH   /api/v1/posts/:id    v1.posts.update     as :api_v1_post
DELETE  /api/v1/posts/:id    v1.posts.destroy    as :api_v1_post
GET     /health              (proc)
```

Route helpers **MUST** use the names in that `as` column — `routes.path(:post,
id: post.id)` for the show route above, not an invented `:posts_show`.

The `resources` and `resource` DSL was added in Hanami 2.3.0; apps still on 2.2
have to write each route out longhand.

## Validation

Projects **MUST** use Hanami validations (based on dry-validation) for input validation.

```ruby
# lib/my_app/validators/post.rb
module MyApp
  module Validators
    class Post < Hanami::Validator
      params do
        required(:title).filled(:string)
        required(:body).filled(:string)
        optional(:published).filled(:bool)
      end

      rule(:title) do
        key.failure("must be at least 5 characters") if value.length < 5
      end
    end
  end
end
```

## Testing Patterns

Hanami applications **MUST** be tested at multiple levels: unit, integration, and system tests.

### Testing Actions

Unit action specs **MUST** inject exactly the dependencies the action declares
through `Deps`, and **MUST** assert the real status and side effects.

```ruby
# spec/slices/web/actions/posts/create_spec.rb
RSpec.describe Web::Actions::Posts::Create do
  let(:created_post) { double("post", id: 1) }
  let(:repo) { instance_double("MyApp::Repos::PostRepo", create: created_post) }
  let(:logger) { instance_double("Logger", info: nil) }
  let(:action) { described_class.new(repo: repo, logger: logger) }

  it "persists only allowlisted fields and redirects" do
    response = action.call(post: {title: "Test title", body: "Body", id: 999})

    expect(response.status).to be(302)
    expect(response.headers["Location"]).to eq("/posts/1")
    expect(repo).to have_received(:create).with(title: "Test title", body: "Body")
    expect(logger).to have_received(:info).with("Post created: 1")
  end

  it "responds 422 for invalid params without persisting" do
    response = action.call(post: {title: "no", body: ""})

    expect(response.status).to be(422)
    expect(repo).not_to have_received(:create)
  end
end
```

### Testing Repositories

Repositories are container components, so resolve them from the app rather than
calling `new`: `MyApp::DB::Repo` needs the ROM container its relations live in.

```ruby
# spec/repos/post_repo_spec.rb
RSpec.describe MyApp::Repos::PostRepo, :db do
  subject(:repo) { Hanami.app["repos.post_repo"] }

  describe "#published" do
    it "returns only published posts" do
      published = repo.create(title: "Published", body: "Body", published: true)
      repo.create(title: "Draft", body: "Body", published: false)

      posts = repo.published

      expect(posts.size).to eq(1)
      expect(posts.first.id).to eq(published.id)
    end
  end
end
```

### Integration Tests

```ruby
# spec/requests/posts_index_spec.rb
RSpec.describe "Posts", :db, type: :request do
  describe "GET /posts" do
    it "lists published posts" do
      Hanami.app["repos.post_repo"].create(
        title: "Test Post",
        body: "Body",
        published: true
      )

      get "/posts"

      expect(last_response).to be_ok
      expect(last_response.body).to include("Test Post")
    end
  end
end
```

## See Also

- [Ruby Style Guide](../languages/ruby.md) - Language-level Ruby conventions
- [Rails Style Guide](rails.md) - Full-featured MVC framework
- [Sinatra Style Guide](sinatra.md) - Lightweight DSL framework

## References

[^1]: [StandardRB](https://github.com/standardrb/standard) - Ruby style guide, linter, and formatter
[^2]: [Hanami](https://hanamirb.org/) - Modern Ruby web framework
[^3]: [ROM (Ruby Object Mapper)](https://rom-rb.org/) - Data mapping and persistence toolkit
[^4]: [Hanami CHANGELOG](https://github.com/hanami/hanami/blob/main/CHANGELOG.md) - Release
    history; `resource`/`resources` routing arrived in v2.3.0 (2025-11-12), and 3.0.2 is the
    release these examples were run against
