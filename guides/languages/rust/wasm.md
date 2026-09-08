# WebAssembly (WASM)

> [Doctrine](../../../README.md) > [Languages](../README.md) > [Rust](../rust.md) > WebAssembly (WASM)

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) when, and only
when, they appear in all capitals, as shown here.

This guide covers building Rust for WebAssembly: target selection, wasm-bindgen
and web-sys manifests, wasm-pack, browser testing and size control. The
toolchain, lint, formatting and pre-commit rules in the
[Rust Style Guide](../rust.md) apply and are not repeated here, and so do the
[dependency](dependencies.md) and [CI](ci.md) rules; every version quoted is
listed in the [Tested Version Matrix](versions.md#tested-version-matrix) and was
current on 8 September 2026.

Projects **MAY** compile Rust to WebAssembly for browser or edge runtime
deployment. wasm-pack[^19] **SHOULD** be used for building WASM packages.

## Why Rust for WASM

- **Performance**: Near-native speed in the browser
- **Safety**: Memory-safe without garbage collection
- **Size**: Small binary sizes with aggressive optimization
- **Interop**: Excellent JavaScript interoperability via wasm-bindgen

## Target Selection

`wasm32-unknown-unknown` and the WASI targets are not interchangeable and
**MUST** be chosen deliberately.

| Target | Use | Host API |
| ------ | --- | -------- |
| `wasm32-unknown-unknown` | Browser, bundler, wasm-bindgen | JavaScript via wasm-bindgen; no filesystem, no sockets |
| `wasm32-wasip1` | Edge and server runtimes (Wasmtime, Wasmer) | WASI preview 1: files, clocks, stdio |
| `wasm32-wasip2` | Component-model runtimes | WASI preview 2 interfaces |

**Why**: `wasm32-unknown-unknown` has no operating system behind it. `std::fs`,
`std::net` and `std::time::SystemTime::now` compile and then fail or panic at
run time, and `wasm-bindgen` is unavailable on WASI targets because there is no
JavaScript host to bind to. Code shared between the two **MUST** be gated on
`target_os`, not merely on `target_arch = "wasm32"`.

## Setup

```bash
# Install the browser target
rustup target add wasm32-unknown-unknown

# Install wasm-pack, pinned
cargo install wasm-pack --version 0.15.0 --locked

# Optional: wasm-opt for size optimisation
cargo install wasm-opt --version 0.116.1 --locked
```

## Project Structure

The manifest **MUST** list every crate and every `web-sys` feature the code
uses.

**Why**: `web-sys` gates each Web IDL interface behind a Cargo feature to keep
compile times and binary size down, so an unlisted feature is a
`error[E0432]: unresolved import 'web_sys::Document'`, not a smaller binary.
The same applies to the crates that examples reach for without declaring:
`console_error_panic_hook`, `serde` and `serde-wasm-bindgen`.

```toml
# Cargo.toml
[package]
name = "my_crate"
version = "0.1.0"
edition = "2024"
rust-version = "1.94.0"

[lib]
crate-type = ["cdylib", "rlib"]

[dependencies]
console_error_panic_hook = "0.1.7"
js-sys = "0.3.105"
serde = { version = "1.0.229", features = ["derive"] }
serde-wasm-bindgen = "0.6.5"
wasm-bindgen = "0.2.128"  # wasm-bindgen[^20]

[dependencies.web-sys]
version = "0.3.105"
features = ["Document", "Element", "Window"]  # one feature per interface used

[dev-dependencies]
wasm-bindgen-test = "0.3.78"

[profile.release]
opt-level = "z"      # Optimise for size
lto = true           # Link-time optimisation
codegen-units = 1
panic = "abort"
strip = true
```

```toml
# BAD: the code below calls web_sys::window(), sets a panic hook and
# round-trips serde values, none of which this manifest can compile.
[dependencies]
wasm-bindgen = "0.2"

[dev-dependencies]
wasm-bindgen-test = "0.3"
```

## Basic WASM Module

```rust
// src/lib.rs
use serde::{Deserialize, Serialize};
use wasm_bindgen::prelude::*;
use web_sys::Element;

#[wasm_bindgen(start)]
pub fn start() {
    console_error_panic_hook::set_once();
}

#[wasm_bindgen]
#[must_use]
pub fn greet(name: &str) -> String {
    format!("Hello, {name}!")
}

#[wasm_bindgen]
#[derive(Default)]
pub struct Counter {
    value: i32,
}

#[wasm_bindgen]
#[allow(clippy::missing_const_for_fn, reason = "#[wasm_bindgen] rejects const fn")]
impl Counter {
    #[wasm_bindgen(constructor)]
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    pub fn increment(&mut self) {
        self.value += 1;
    }

    #[must_use]
    pub fn value(&self) -> i32 {
        self.value
    }
}

/// Creates a detached element of type `tag`.
///
/// # Errors
///
/// Returns the JavaScript error when there is no window or document, or when
/// `tag` is not a valid element name.
#[wasm_bindgen]
pub fn create_element(tag: &str) -> Result<Element, JsValue> {
    let window = web_sys::window().ok_or_else(|| JsValue::from_str("no window"))?;
    let document = window.document().ok_or_else(|| JsValue::from_str("no document"))?;
    document.create_element(tag)
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Config {
    pub name: String,
    pub value: i32,
}

/// Round-trips a configuration object through Rust.
///
/// # Errors
///
/// Returns the JavaScript error when `config` does not deserialise into
/// [`Config`].
#[wasm_bindgen]
pub fn process_config(config: JsValue) -> Result<JsValue, JsValue> {
    let mut config: Config = serde_wasm_bindgen::from_value(config)?;
    config.value += 1;
    Ok(serde_wasm_bindgen::to_value(&config)?)
}
```

## Building WASM

```bash
# Build for bundlers (webpack, vite)
wasm-pack build --target bundler

# Build for Node.js
wasm-pack build --target nodejs

# Build for web (no bundler)
wasm-pack build --target web

# Build with optimizations
wasm-pack build --release --target web

# Further optimize with wasm-opt
wasm-opt -Os -o pkg/optimized.wasm pkg/app_bg.wasm
```

## Using in JavaScript

The import shape **MUST** match the `--target` the package was built with.
`--target bundler` output re-exports named bindings only and starts the module
itself; it has no default export, so `import init from './pkg/my_crate.js'`
fails to link with "SyntaxError: The requested module does not provide an
export named 'default'". Only `--target web` exports the asynchronous
initialiser as the default.[^20]

```javascript
// GOOD: `wasm-pack build --target bundler` — named exports, no init call.
// The bundler resolves and instantiates the .wasm import for you.
import { greet, Counter } from './pkg/my_crate.js';

console.log(greet('World'));

const counter = new Counter();
counter.increment();
console.log(counter.value()); // 1
```

```javascript
// GOOD: `wasm-pack build --target web` — default export is the initialiser
// and MUST be awaited before any other export is called.
import init, { greet, Counter } from './pkg/my_crate.js';

async function run() {
  await init();
  console.log(greet('World'));

  const counter = new Counter();
  counter.increment();
  console.log(counter.value()); // 1
}

run();
```

```javascript
// BAD: bundler output has no default export; this is a link-time SyntaxError.
import init, { greet } from './pkg/my_crate.js';  // built with --target bundler
```

```html
<!-- Without bundler: built with `wasm-pack build --target web` -->
<script type="module">
  import init, { greet } from './pkg/my_crate.js';

  async function run() {
    await init();
    document.body.textContent = greet('WASM');
  }

  run();
</script>
```

## WASM Testing

```rust
// tests/web.rs
#![cfg(target_arch = "wasm32")]

use wasm_bindgen_test::{wasm_bindgen_test, wasm_bindgen_test_configure};
use wasmdemo::{Counter, greet};

wasm_bindgen_test_configure!(run_in_browser);

#[wasm_bindgen_test]
fn greet_interpolates() {
    assert_eq!(greet("Test"), "Hello, Test!");
}

#[wasm_bindgen_test]
fn counter_increments() {
    let mut counter = Counter::new();
    assert_eq!(counter.value(), 0);
    counter.increment();
    assert_eq!(counter.value(), 1);
}
```

**Why `#![cfg(target_arch = "wasm32")]`**: `wasm_bindgen_test` targets a
browser or Node host. Without the gate, `cargo test` on the development machine
tries to build the file for the host target and fails on the missing
JavaScript environment.

```bash
# Run WASM tests in a headless browser
wasm-pack test --headless --firefox
wasm-pack test --headless --chrome

# Run in Node.js
wasm-pack test --node
```

## WASM Best Practices

Exported functions **MUST NOT** unwrap host lookups. `web_sys::window()`
returns `None` in a worker or in Node, and `unwrap` there aborts the module
with an unhelpful "unreachable executed" trap rather than a JavaScript
exception the caller can catch.

```rust
// GOOD: the host failure becomes a rejected promise or a thrown JsValue.
let window = web_sys::window().ok_or_else(|| JsValue::from_str("no window"))?;
```

```rust
// BAD: traps the whole module in a worker context.
let window = web_sys::window().unwrap();
```

`console_error_panic_hook::set_once()` **SHOULD** be installed from
`#[wasm_bindgen(start)]` so that any panic that does occur prints a Rust stack
trace to the browser console instead of "unreachable executed".

## WASM Size Optimisation

The release profile in [Project Structure](#project-structure) is the size
configuration; the settings **MUST** be at the workspace root when the crate is
a workspace member, because Cargo ignores `[profile]` in a non-root manifest
and says so: "profiles for the non root package will be ignored".

```bash
# Check WASM size
ls -lh pkg/*.wasm

# Analyse with twiggy
cargo install twiggy --version 0.8.0 --locked
twiggy top pkg/app_bg.wasm
twiggy paths pkg/app_bg.wasm
```

## References

[^19]: [wasm-pack](https://wasm-bindgen.github.io/wasm-pack/) - Tool for building Rust WASM packages
[^20]: [wasm-bindgen](https://github.com/wasm-bindgen/wasm-bindgen) - Facilitating high-level interactions between Wasm modules and JavaScript

## See Also

- [Rust Style Guide](../rust.md) - Toolchain, lints, formatting, dependencies and CI
- [Rust topic guides](README.md) - The other Rust topic guides
