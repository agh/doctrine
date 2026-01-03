# Hanami Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > Hanami

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119][rfc2119].

[rfc2119]: https://datatracker.ietf.org/doc/html/rfc2119

Extends [Ruby style guide](../languages/ruby.md) with Hanami-specific conventions.

**Target Version**: Hanami 2.2+ with Ruby 4.0

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
│   ├── actions/           # Cross-slice actions (if needed)
│   └── views/             # Cross-slice views
├── slices/
│   ├── admin/
│   │   ├── actions/       # Admin-specific actions
│   │   │   └── users/
│   │   │       ├── index.rb
│   │   │       ├── show.rb
│   │   │       └── create.rb
│   │   ├── views/         # Admin views
│   │   ├── repositories/  # Data access
│   │   └── entities/      # Domain objects
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
│       └── templates/
├── config/
│   ├── app.rb             # Application configuration
│   ├── routes.rb          # Route definitions
│   ├── providers/         # Dependency injection providers
│   └── settings.rb        # Environment settings
├── lib/
│   └── my_app/
│       ├── entities/      # Shared entities
│       ├── repositories/  # Shared repositories
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
        include Deps[repo: "repositories.posts"]

        def handle(request, response)
          posts = repo.all
          response.render view, posts: posts
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
            repo: "repositories.posts",
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

```ruby
module Web
  module Actions
    module Admin
      class Index < Web::Action
        before :authenticate!
        before :authorize!

        def handle(request, response)
          # Action logic here
        end

        private

        def authenticate!(request, response)
          halt 401 unless request.session[:user_id]
        end

        def authorize!(request, response)
          user = users_repo.find(request.session[:user_id])
          halt 403 unless user.admin?
        end
      end
    end
  end
end
```

### Views and Templates

Views **SHOULD** contain presentation logic only, never business logic.

```ruby
# slices/web/views/posts/index.rb
module Web
  module Views
    module Posts
      class Index < Web::View
        expose :posts do |posts|
          posts.map { |post| PostPresenter.new(post) }
        end

        expose :page_title do
          "All Posts"
        end
      end
    end
  end
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

```ruby
# slices/web/views/presenters/post_presenter.rb
module Web
  module Views
    class PostPresenter
      def initialize(post)
        @post = post
      end

      def title = @post.title
      def excerpt = @post.body.truncate(200)
      def published_at_formatted = @post.created_at.strftime("%B %d, %Y")
    end
  end
end
```

## Repositories and Relations (ROM-based Persistence)

Hanami uses ROM (Ruby Object Mapper)[^3] for data persistence. Repositories **MUST** encapsulate
all data access. Relations **SHOULD** define queries and transformations.

### Entities

Entities **SHOULD** be simple data objects with no persistence logic.

```ruby
# lib/my_app/entities/post.rb
module MyApp
  module Entities
    class Post < Hanami::Entity
      attributes do
        attribute :id, Types::Integer
        attribute :title, Types::String
        attribute :body, Types::String
        attribute :published, Types::Bool
        attribute :author_id, Types::Integer
        attribute :created_at, Types::DateTime
        attribute :updated_at, Types::DateTime
      end
    end
  end
end
```

### Relations

```ruby
# lib/my_app/relations/posts.rb
module MyApp
  module Relations
    class Posts < Hanami::DB::Relation
      schema :posts, infer: true

      auto_struct true

      def published
        where(published: true).order { created_at.desc }
      end

      def by_author(author_id)
        where(author_id: author_id)
      end

      def recent(limit = 10)
        order { created_at.desc }.limit(limit)
      end
    end
  end
end
```

### Repositories

Repositories **MUST** provide a clean interface for data operations.

```ruby
# lib/my_app/repositories/posts.rb
module MyApp
  module Repositories
    class Posts < Hanami::DB::Repository
      def all = posts.to_a
      def published = posts.published.to_a
      def find(id) = posts.by_pk(id).one!
      def recent(limit: 10) = posts.recent(limit).to_a
      def by_author(author_id) = posts.by_author(author_id).to_a

      def create(attributes) = posts.create(attributes)
      def update(id, attributes) = posts.by_pk(id).update(attributes)
      def delete(id) = posts.by_pk(id).delete

      # Complex queries with joins
      def with_author(id)
        posts
          .join(:authors)
          .where(posts[:id] => id)
          .one!
      end
    end
  end
end
```

## Dependency Injection Container

Hanami's dependency injection container **SHOULD** be used for managing dependencies. This
improves testability and makes dependencies explicit.

### Providers

Providers **SHOULD** define how dependencies are created and configured.

```ruby
# config/providers/mailer.rb
Hanami.app.register_provider :mailer do
  prepare do
    require "mail"
  end

  start do
    Mail.defaults do
      delivery_method :smtp, {
        address: target["settings"].smtp_host,
        port: target["settings"].smtp_port,
        user_name: target["settings"].smtp_username,
        password: target["settings"].smtp_password,
        authentication: :plain
      }
    end

    register "mailer", Mail
  end
end
```

### Using Dependencies

```ruby
# slices/web/actions/posts/create.rb
module Web
  module Actions
    module Posts
      class Create < Web::Action
        include Deps[
          repo: "repositories.posts",
          logger: "logger",
          mailer: "mailer"
        ]

        def handle(request, response)
          post = repo.create(request.params[:post])
          logger.info "Post created: #{post.id}"
          response.redirect_to routes.path(:posts_show, id: post.id)
        end
      end
    end
  end
end
```

### Testing with Dependency Injection

```ruby
# spec/slices/web/actions/posts/create_spec.rb
RSpec.describe Web::Actions::Posts::Create do
  let(:repo) { instance_double("MyApp::Repositories::Posts") }
  let(:logger) { instance_double("Logger", info: nil) }
  let(:action) { described_class.new(repo: repo, logger: logger) }

  it "creates a post and logs" do
    post = MyApp::Entities::Post.new(id: 1, title: "Test")
    allow(repo).to receive(:create).and_return(post)

    response = action.call(post: { title: "Test", body: "Body" })

    expect(repo).to have_received(:create)
    expect(logger).to have_received(:info).with("Post created: 1")
  end
end
```

## Configuration and Settings

Projects **MUST** use environment-specific settings. Settings **SHOULD** be type-safe using Dry::Types.

```ruby
# config/settings.rb
module MyApp
  class Settings < Hanami::Settings
    setting :database_url, constructor: Types::String
    setting :port, default: 2300, constructor: Types::Integer
    setting :host, default: "0.0.0.0", constructor: Types::String
    setting :enable_api, default: true, constructor: Types::Bool
    setting :session_secret, constructor: Types::String
  end
end
```

```ruby
# .env (for development)
DATABASE_URL=postgres://localhost/myapp_development
SESSION_SECRET=development_secret_change_in_production
```

## Routing

Routes **MUST** be defined in `config/routes.rb`. Routes **SHOULD** be organized by slice.

```ruby
# config/routes.rb
module MyApp
  class Routes < Hanami::Routes
    root to: "web.actions.home.index"

    slice :web, at: "/" do
      get "/posts", to: "actions.posts.index"
      get "/posts/:id", to: "actions.posts.show"
    end

    slice :admin, at: "/admin" do
      get "/", to: "actions.dashboard.index"
      resources :users, only: [:index, :show, :create]
    end

    slice :api, at: "/api" do
      scope "/v1" do
        resources :posts, only: [:index, :show, :create, :update, :destroy]
      end
    end

    get "/health", to: ->(env) { [200, {}, ["OK"]] }
  end
end
```

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

```ruby
RSpec.describe Web::Actions::Posts::Create do
  let(:repo) { instance_double("MyApp::Repositories::Posts") }
  let(:validator) { instance_double("MyApp::Validators::Post") }
  let(:action) { described_class.new(repo: repo, validator: validator) }

  describe "with valid params" do
    it "creates a post and redirects" do
      post = MyApp::Entities::Post.new(id: 1, title: "Test")
      result = double(success?: true, to_h: { title: "Test", body: "Body" })

      allow(validator).to receive(:call).and_return(result)
      allow(repo).to receive(:create).and_return(post)

      response = action.call(post: { title: "Test", body: "Body" })

      expect(response).to be_redirect
      expect(repo).to have_received(:create)
    end
  end
end
```

### Testing Repositories

```ruby
RSpec.describe MyApp::Repositories::Posts do
  let(:repo) { described_class.new }

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
RSpec.describe "Posts", type: :request do
  let(:app) { Hanami.app }

  describe "GET /posts" do
    it "lists all posts" do
      MyApp::Repositories::Posts.new.create(
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
