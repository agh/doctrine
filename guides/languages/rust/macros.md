# Procedural Macros

> [Doctrine](../../../README.md) > [Languages](../README.md) > [Rust](../rust.md) > Procedural Macros

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) when, and only
when, they appear in all capitals, as shown here.

This guide covers derive, attribute and function-like procedural macros: crate
layout, parsing with syn, code generation with quote, spanned errors and
compile-fail testing with trybuild. The toolchain, lint, formatting and
pre-commit rules in the [Rust Style Guide](../rust.md) apply and are not
repeated here, and so do the [dependency](dependencies.md) and [CI](ci.md)
rules; every version quoted is listed in the
[Tested Version Matrix](versions.md#tested-version-matrix) and was current on 8
September 2026.

Projects **MAY** create procedural macros to reduce boilerplate. Procedural
macros **MUST** be defined in a separate crate with `proc-macro = true`.

## Why Procedural Macros

- **Code generation**: Generate boilerplate at compile time
- **Custom derives**: Implement traits automatically
- **DSLs**: Create domain-specific languages
- **Validation**: Enforce invariants at compile time

## Types of Procedural Macros

| Type | Syntax | Use Case |
| ---- | ------ | -------- |
| Derive macros | `#[derive(MyTrait)]` | Auto-implement traits |
| Attribute macros | `#[my_attr]` | Transform items |
| Function-like macros | `my_macro!(...)` | Custom syntax |

## Project Structure

```text
my_project/
├── Cargo.toml
├── src/
│   └── lib.rs
└── my_macro/           # Separate crate for proc-macro
    ├── Cargo.toml
    └── src/
        └── lib.rs
```

```toml
# my_macro/Cargo.toml
[package]
name = "my_macro"
version = "0.1.0"
edition = "2024"        # REQUIRED: an omitted edition defaults to 2015
rust-version = "1.94.0"

[lib]
proc-macro = true

[dependencies]
syn = { version = "3.0.5", features = ["full"] }     # syn[^21]
quote = "1.0.47"                                      # quote[^22]
proc-macro2 = "1.0.107"                               # proc-macro2[^23]
```

Every crate manifest **MUST** declare `package.edition`.

**Why**: Cargo defaults an omitted `edition` to 2015, where `use quote::quote;`
and `use syn::...;` do not resolve without an `extern crate` declaration. The
macro crate above fails to compile with "error[E0432]: unresolved import
quote" until the edition is declared.[^27]

## Migrating from syn 2 to syn 3

New macro crates **MUST** use syn 3. syn 3.0.0 reshaped the syntax tree to
absorb three years of language evolution: `Type::BareFn` became `Type::FnPtr`,
`Signature::unsafety` became a three-way `Safety` enum, `Arm::guard` moved to a
`Pat::Guard` variant, and ten new non-exhaustive `*Modifiers` structs were
added to reserve room for future syntax.[^42]

Macros **MUST** round-trip parsed items rather than reassembling them field by
field.

**Why**: field-by-field reassembly drops whatever the macro does not name, and
breaks outright when a syntax tree node gains a field. Destructuring
`syn::ItemFn` exhaustively against syn 3 fails with
"error[E0027]: pattern does not mention field `modifiers`"; the same code
written against syn 2 compiled, and silently discarded any modifier syntax the
node did not yet model.

```rust
// GOOD: mutate the parsed item and print it back. Attributes, visibility,
// generics, `async`, `const`, `unsafe` and modifiers all survive untouched.
let mut func = parse_macro_input!(item as ItemFn);
let body = &func.block;
let wrapped: Block = parse_quote! {{ /* ... */ #body }};
*func.block = wrapped;
quote! { #func }
```

```rust
// BAD: names four of the five fields. Rejected by syn 3, and lossy under
// syn 2.
let ItemFn { attrs, vis, sig, block } = parse_macro_input!(item as ItemFn);
quote! { #(#attrs)* #vis #sig { /* ... */ #block } }
```

Where a macro must reject syntax it does not understand, call
`.require_empty()` on the relevant `*Modifiers` value: it returns a spanned
error naming the unsupported construct instead of silently ignoring it.[^42]

## Derive Macro Example

A derive macro **MUST** handle every shape of the item it accepts — named,
tuple and unit structs, and generics — or reject the rest with a spanned
error. It **MUST NOT** `panic!`.

**Why**: `panic!` in a proc macro surfaces as
"error: proc-macro derive panicked" pointing at the derive attribute, with the
message relegated to a note and no span for the offending item. A returned
`syn::Error` points at the token that is wrong. Ignoring tuple and unit structs
is worse than rejecting them: `#[derive(Builder)]` on a tuple struct silently
generates a builder whose `build()` cannot name any field, and the failure
appears deep inside the expansion.

```rust
// my_macro/src/lib.rs
use proc_macro::TokenStream;
use proc_macro2::Span;
use quote::{format_ident, quote};
use syn::spanned::Spanned;
use syn::{
    Block, Data, DeriveInput, Error, Fields, Ident, ItemFn, Result, Type, parse_macro_input,
    parse_quote,
};

#[proc_macro_derive(Builder)]
pub fn derive_builder(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    expand_builder(&input)
        .unwrap_or_else(Error::into_compile_error)
        .into()
}

struct Field {
    /// `None` for a tuple struct: the accessor is positional.
    ident: Option<Ident>,
    setter: Ident,
    ty: Type,
}

fn collect_fields(data: &Data) -> Result<Vec<Field>> {
    let fields = match data {
        Data::Struct(s) => &s.fields,
        Data::Enum(e) => {
            return Err(Error::new(e.enum_token.span, "Builder supports structs only"));
        }
        Data::Union(u) => {
            return Err(Error::new(u.union_token.span, "Builder supports structs only"));
        }
    };
    let out = match fields {
        Fields::Named(named) => named
            .named
            .iter()
            .map(|f| {
                let ident = f.ident.clone().ok_or_else(|| {
                    Error::new(f.span(), "named field without an identifier")
                })?;
                Ok(Field { setter: ident.clone(), ident: Some(ident), ty: f.ty.clone() })
            })
            .collect::<Result<Vec<_>>>()?,
        Fields::Unnamed(unnamed) => unnamed
            .unnamed
            .iter()
            .enumerate()
            .map(|(i, f)| Field {
                ident: None,
                setter: format_ident!("field_{i}", span = f.span()),
                ty: f.ty.clone(),
            })
            .collect(),
        Fields::Unit => Vec::new(),
    };
    Ok(out)
}

fn expand_builder(input: &DeriveInput) -> Result<proc_macro2::TokenStream> {
    let name = &input.ident;
    let builder = format_ident!("{name}Builder");
    let error = format_ident!("{name}BuilderError");
    let fields = collect_fields(&input.data)?;
    let (impl_generics, ty_generics, where_clause) = input.generics.split_for_impl();

    let decls = fields.iter().map(|f| {
        let (setter, ty) = (&f.setter, &f.ty);
        quote! { #setter: ::core::option::Option<#ty> }
    });
    let inits = fields.iter().map(|f| {
        let setter = &f.setter;
        quote! { #setter: ::core::option::Option::None }
    });
    let setters = fields.iter().map(|f| {
        let (setter, ty) = (&f.setter, &f.ty);
        quote! {
            pub fn #setter(mut self, value: #ty) -> Self {
                self.#setter = ::core::option::Option::Some(value);
                self
            }
        }
    });
    let takes = fields.iter().map(|f| {
        let setter = &f.setter;
        let label = setter.to_string();
        let value = quote! {
            self.#setter.ok_or(#error { field: #label })?
        };
        match &f.ident {
            Some(ident) => quote! { #ident: #value },
            None => value,
        }
    });
    let ctor = match fields.first().map(|f| f.ident.is_some()) {
        Some(true) => quote! { #name { #(#takes,)* } },
        Some(false) => quote! { #name(#(#takes,)*) },
        None => quote! { #name },
    };

    Ok(quote! {
        /// Error returned when a required field was never set.
        #[derive(Debug, Clone, Copy, PartialEq, Eq)]
        pub struct #error {
            /// Name of the field that was left unset.
            pub field: &'static str,
        }

        impl ::core::fmt::Display for #error {
            fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::fmt::Result {
                ::core::write!(f, "missing field: {}", self.field)
            }
        }

        impl ::core::error::Error for #error {}

        pub struct #builder #impl_generics #where_clause {
            #(#decls,)*
        }

        impl #impl_generics #builder #ty_generics #where_clause {
            #[must_use]
            pub fn new() -> Self {
                Self { #(#inits,)* }
            }

            #(#setters)*

            pub fn build(self) -> ::core::result::Result<#name #ty_generics, #error> {
                ::core::result::Result::Ok(#ctor)
            }
        }

        impl #impl_generics ::core::default::Default for #builder #ty_generics #where_clause {
            fn default() -> Self {
                Self::new()
            }
        }

        impl #impl_generics #name #ty_generics #where_clause {
            #[must_use]
            pub fn builder() -> #builder #ty_generics {
                #builder::new()
            }
        }
    })
}
```

## Attribute Macro Example

An attribute macro **MUST** preserve the item it decorates: attributes,
visibility, generics, `async` and `where` clauses. Wrapping a body in a
closure **MUST NOT** be used.

**Why**: `let result = (|| { #body })();` changes the meaning of the function.
`?` and `return` inside the body then leave the closure rather than the
function, `.await` is rejected because the closure is not `async`, and the
closure captures `self` by inference. Assigning the block back onto the parsed
`ItemFn` keeps the original control flow, and a `Drop` guard logs the exit on
every path including `?` and early `return`.

```rust
// my_macro/src/lib.rs
#[proc_macro_attribute]
pub fn log_calls(attr: TokenStream, item: TokenStream) -> TokenStream {
    if !attr.is_empty() {
        let span = proc_macro2::TokenStream::from(attr).span();
        return Error::new(span, "log_calls takes no arguments")
            .into_compile_error()
            .into();
    }
    // Mutate the parsed item and print it back. Reassembling the pieces by
    // hand silently drops anything the macro does not name.
    let mut func = parse_macro_input!(item as ItemFn);
    let name = func.sig.ident.to_string();
    let body = &func.block;
    let wrapped: Block = parse_quote! {{
        struct __LogExit(&'static str);
        impl ::core::ops::Drop for __LogExit {
            fn drop(&mut self) {
                ::std::println!("[EXIT] {}", self.0);
            }
        }
        let __log_exit = __LogExit(#name);
        ::std::println!("[ENTER] {}", #name);
        #body
    }};
    *func.block = wrapped;
    quote! { #func }.into()
}
```

## Function-like Macro Example

A macro **MUST** validate only what its documentation and its error message
claim. A prefix check is a prefix check, not SQL validation.

**Why**: naming a macro `sql!` and checking `starts_with("SELECT")` promises
compile-time SQL checking and delivers none: `sql!(SELECT nonexistent FROM
missing)` is accepted. If compile-time SQL verification is the goal, use SQLx's
checked macros against a real schema; see
[Data Integrity Testing](testing-scenarios.md#sqlx-compile-time-checked-queries).

```rust
// my_macro/src/lib.rs
#[proc_macro]
pub fn select(input: TokenStream) -> TokenStream {
    let tokens = proc_macro2::TokenStream::from(input);
    let leading = tokens.clone().into_iter().next();
    let ok = matches!(
        &leading,
        Some(proc_macro2::TokenTree::Ident(i)) if i.to_string().eq_ignore_ascii_case("select")
    );
    if !ok {
        let span = leading.map_or_else(Span::call_site, |t| t.span());
        return Error::new(span, "select! accepts SELECT statements only")
            .into_compile_error()
            .into();
    }
    let text = tokens.to_string();
    quote! { #text }.into()
}
```

## Using the Macros

```rust
// src/lib.rs — the consumer crate
pub use my_macro::{Builder, log_calls, select};

#[derive(Builder, Debug, PartialEq, Eq)]
pub struct Config {
    pub host: String,
    pub port: u16,
}

#[derive(Builder, Debug, PartialEq, Eq)]
pub struct Pair<T>(pub T, pub T)
where
    T: Clone;

#[derive(Builder, Debug, PartialEq, Eq)]
pub struct Marker;

#[log_calls]
pub fn double(x: i32) -> i32 {
    x * 2
}

#[log_calls]
pub async fn fetch(id: u64) -> Result<u64, ConfigBuilderError> {
    if id == 0 {
        return Err(ConfigBuilderError { field: "id" });
    }
    Ok(id)
}

pub const QUERY: &str = select!(SELECT * FROM users WHERE id = 1);
```

## Testing Procedural Macros

```rust
// tests/builder.rs
#![allow(clippy::unwrap_used, clippy::expect_used, clippy::panic)]

use macro_user::{Config, Marker, Pair};

#[test]
fn named_struct_builds() {
    let config = Config::builder()
        .host("localhost".into())
        .port(8080)
        .build()
        .expect("all fields set");
    assert_eq!(config.host, "localhost");
    assert_eq!(config.port, 8080);
}

#[test]
fn missing_field_names_itself() {
    let err = Config::builder().host("localhost".into()).build().unwrap_err();
    assert_eq!(err.field, "port");
}

#[test]
fn tuple_struct_builds_positionally() {
    let pair = Pair::builder().field_0(1u8).field_1(2u8).build().expect("both set");
    assert_eq!(pair, Pair(1, 2));
}

#[test]
fn unit_struct_builds() {
    assert_eq!(Marker::builder().build().expect("no fields"), Marker);
}

#[test]
fn attribute_macro_preserves_async_and_early_return() {
    let rt = std::thread::spawn(|| {
        futures_lite::future::block_on(async { macro_user::fetch(7).await })
    })
    .join()
    .expect("thread");
    assert_eq!(rt.expect("id 7 is accepted"), 7);
    assert_eq!(macro_user::double(21), 42);
    assert_eq!(macro_user::QUERY, "SELECT * FROM users WHERE id = 1");
}
```

## Compile-fail Tests with trybuild

Compile-fail fixtures **MUST** ship the expected `.stderr`.

**Why**: without a golden file, `trybuild` records whatever the macro currently
prints and passes. The test then asserts only that compilation failed, not that
it failed for the stated reason, so a macro that starts rejecting valid input
still passes. Generate the goldens once with `TRYBUILD=overwrite cargo test`
and review them like any other source.

```toml
[dev-dependencies]
trybuild = "1.0.121"  # trybuild[^24]
```

```rust
// tests/compile_fail.rs
#[test]
fn compile_fail_tests() {
    let t = trybuild::TestCases::new();
    t.compile_fail("tests/compile-fail/*.rs");
}
```

```rust
// tests/compile-fail/builder_on_enum.rs
use macro_user::Builder;

#[derive(Builder)]
enum Invalid {
    A,
    B,
}

fn main() {}
```

```text
// tests/compile-fail/builder_on_enum.stderr
error: Builder supports structs only
 --> tests/compile-fail/builder_on_enum.rs:4:1
  |
4 | enum Invalid {
  | ^^^^
```

```rust
// tests/compile-fail/select_rejects_insert.rs
use macro_user::select;

fn main() {
    let _ = select!(INSERT INTO users VALUES (1));
}
```

```text
// tests/compile-fail/select_rejects_insert.stderr
error: select! accepts SELECT statements only
 --> tests/compile-fail/select_rejects_insert.rs:4:21
  |
4 |     let _ = select!(INSERT INTO users VALUES (1));
  |                     ^^^^^^
```

## Proc Macro Best Practices

Errors **MUST** be returned as `syn::Error` with the narrowest useful span:

```rust
// GOOD: the diagnostic points at the `enum` keyword.
Data::Enum(e) => {
    return Err(Error::new(e.enum_token.span, "Builder supports structs only"));
}
```

```rust
// BAD: no span, and the message is buried under
// "error: proc-macro derive panicked".
_ => panic!("Builder only works on structs"),
```

Attribute parsing **SHOULD** use darling[^25] rather than hand-written
`Meta` walking:

```toml
[dependencies]
darling = "0.24.1"  # darling[^25]
```

**Why**: darling derives the parser from a struct definition, so unknown keys,
missing required keys and wrong value types all produce spanned errors for
free. Hand-written `Meta` traversal typically accumulates one `if` per key and
degrades to ignoring anything unrecognised.

## References

[^21]: [syn](https://github.com/dtolnay/syn) - Parser for Rust source code
[^22]: [quote](https://github.com/dtolnay/quote) - Rust quasi-quoting for code generation
[^23]: [proc-macro2](https://github.com/dtolnay/proc-macro2) - Wrapper around the proc-macro API
[^24]: [trybuild](https://github.com/dtolnay/trybuild) - Test harness for ui tests of compiler diagnostics
[^25]: [darling](https://github.com/TedDriggs/darling) - Declarative attribute parser for Rust proc macros
[^27]: [The `edition` field](https://doc.rust-lang.org/cargo/reference/manifest.html#the-edition-field) - Cargo manifest reference
[^42]: [syn 3.0.0 release notes](https://github.com/dtolnay/syn/releases/tag/3.0.0) - Breaking syntax-tree changes and the `*Modifiers` structs

## See Also

- [Rust Style Guide](../rust.md) - Toolchain, lints, formatting, dependencies and CI
- [Rust topic guides](README.md) - The other Rust topic guides
