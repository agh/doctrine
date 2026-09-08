# Unsafe Rust

> [Doctrine](../../../README.md) > [Languages](../README.md) > [Rust](../rust.md) > Unsafe Rust

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) when, and only
when, they appear in all capitals, as shown here.

This guide covers when `unsafe` is justified, the invariants every unsafe block
**MUST** document, Edition 2024 rules for `extern` and unsafe attributes, FFI,
and checking with Miri. The toolchain, lint, formatting, dependency and CI rules
in the [Rust Style Guide](../rust.md) apply and are not repeated here; every
version quoted is listed in its [Tested Version
Matrix](../rust.md#tested-version-matrix) and was current on 8 September 2026.

Projects **SHOULD** minimize usage of `unsafe`. When `unsafe` is required, it
**MUST** be carefully documented and isolated.

## Why Minimize Unsafe

- **Compiler guarantees**: Safe Rust provides memory safety guarantees that `unsafe` bypasses
- **Bug surface**: Unsafe code is where memory bugs hide
- **Review burden**: Unsafe code requires more careful review
- **Soundness**: Incorrect unsafe code can cause undefined behavior

## When Unsafe is Necessary

| Use Case | Example |
| -------- | ------- |
| FFI (Foreign Function Interface) | Calling C libraries |
| Raw pointer manipulation | Custom data structures |
| Performance-critical code | SIMD, avoiding bounds checks |
| Hardware access | Memory-mapped I/O |
| Implementing low-level abstractions | `Arc`, `Mutex` internals |

## Unsafe Best Practices

A function that cannot uphold an unsafe operation's preconditions itself
**MUST** be declared `unsafe fn` with a `# Safety` section. A `// SAFETY:`
comment **MUST NOT** be used to push an obligation onto callers of a safe
function.

**Why**: safety is part of the signature, not of a comment. A safe
`get_unchecked` can be called from entirely safe code with any index; under
Miri, `get_unchecked(&[], 0)` aborts with "unsafe precondition(s) violated:
slice::get_unchecked requires that the index is within the slice".[^26]

```rust
// GOOD: bounds-checked, safe to call with any index
#[must_use]
pub fn get(slice: &[u8], index: usize) -> Option<u8> {
    slice.get(index).copied()
}

// GOOD: the obligation is in the signature and documented
/// Reads `slice[index]` without a bounds check.
///
/// # Safety
///
/// `index` must be strictly less than `slice.len()`. Violating this reads out
/// of bounds, which is undefined behaviour.
#[must_use]
pub unsafe fn get_unchecked(slice: &[u8], index: usize) -> u8 {
    debug_assert!(index < slice.len());
    // SAFETY: the caller guarantees `index < slice.len()`.
    unsafe { *slice.get_unchecked(index) }
}
```

```rust
// BAD: safe fn, unchecked index. The comment transfers nothing; safe callers
// can pass any index and cause undefined behaviour.
pub fn get_unchecked(slice: &[u8], index: usize) -> u8 {
    // SAFETY: Caller must ensure index < slice.len()
    unsafe { *slice.get_unchecked(index) }
}
```

An abstraction over a raw allocation **MUST** handle allocation failure,
initialise memory before it is read, and free the allocation in `Drop`.

**Why**: `std::alloc::alloc` returns uninitialised memory and a null pointer on
failure, and it never frees anything. Reading such a byte through a safe method
is undefined behaviour even when the allocation succeeds: on the `SafeBuffer`
shown below, Miri reports "Undefined Behavior: reading memory ..., but memory is
uninitialized ..., and this operation requires initialized memory" for
`SafeBuffer::new(1).get(0)`.[^26]
`alloc_zeroed` initialises the whole block, `handle_alloc_error` reports failure
without producing a dangling `NonNull`, and `Drop` returns the memory.

```rust
// GOOD: Encapsulate unsafe in a safe API with a complete set of invariants
use std::alloc::{Layout, alloc_zeroed, dealloc, handle_alloc_error};
use std::ptr::NonNull;

pub struct ZeroedBuffer {
    ptr: NonNull<u8>,
    layout: Layout,
}

impl ZeroedBuffer {
    /// Allocates `len` zeroed bytes. Returns `None` for `len == 0`, which is
    /// not a valid allocation size.
    #[must_use]
    pub fn new(len: usize) -> Option<Self> {
        if len == 0 {
            return None;
        }
        let layout = Layout::array::<u8>(len).ok()?;

        // SAFETY: `layout` has non-zero size because `len > 0`.
        let ptr = unsafe { alloc_zeroed(layout) };

        // The allocator returns null on failure; it must never be
        // dereferenced or wrapped in `NonNull`.
        let Some(ptr) = NonNull::new(ptr) else {
            handle_alloc_error(layout)
        };
        Some(Self { ptr, layout })
    }

    #[must_use]
    pub const fn len(&self) -> usize {
        self.layout.size()
    }

    #[must_use]
    pub const fn is_empty(&self) -> bool {
        false
    }

    #[must_use]
    pub const fn get(&self, index: usize) -> Option<u8> {
        if index >= self.len() {
            return None;
        }
        // SAFETY: `index < self.len()`, so the offset stays inside the
        // allocation, and `alloc_zeroed` initialised every byte of it.
        Some(unsafe { self.ptr.as_ptr().add(index).read() })
    }

    pub const fn set(&mut self, index: usize, value: u8) -> bool {
        if index >= self.len() {
            return false;
        }
        // SAFETY: `index < self.len()` and `&mut self` rules out aliasing.
        unsafe { self.ptr.as_ptr().add(index).write(value) };
        true
    }
}

impl Drop for ZeroedBuffer {
    fn drop(&mut self) {
        // SAFETY: `ptr` came from `alloc_zeroed` with exactly `self.layout`
        // and has not been freed; `Drop` runs at most once.
        unsafe { dealloc(self.ptr.as_ptr(), self.layout) };
    }
}
```

```rust
// BAD: unwraps the layout, ignores allocation failure, reads uninitialised
// bytes through a safe method, and leaks the allocation.
pub struct SafeBuffer {
    ptr: *mut u8,
    len: usize,
}

impl SafeBuffer {
    pub fn new(size: usize) -> Self {
        let ptr = unsafe {
            // SAFETY: size is non-zero, layout is valid   <- neither is checked
            std::alloc::alloc(std::alloc::Layout::array::<u8>(size).unwrap())
        };
        Self { ptr, len: size }
    }

    pub fn get(&self, index: usize) -> Option<u8> {
        if index < self.len {
            // SAFETY: index is bounds-checked   <- but the byte is uninitialised
            Some(unsafe { *self.ptr.add(index) })
        } else {
            None
        }
    }
}
// No `Drop`: every SafeBuffer leaks its allocation.
```

Prefer a safe owner where one exists. `vec![0u8; len]` gives the same
guarantees with no `unsafe` at all; reach for raw allocation only when the
layout or ownership cannot be expressed with `Vec` or `Box`.

```rust
// GOOD: no unsafe needed for a zeroed byte buffer
let buffer = vec![0u8; 100];
assert_eq!(buffer.get(100), None);
```

```rust
// GOOD: Document invariants
/// A non-null pointer to a valid T.
///
/// # Safety
///
/// The pointer must:
/// - Be properly aligned for T
/// - Point to a valid, initialized T
/// - Not be aliased by any mutable reference
pub struct NonNullPtr<T> {
    ptr: *const T,
}
```

## SAFETY Comments

All `unsafe` blocks **MUST** include a `// SAFETY:` comment explaining why the code is sound:

```rust
// GOOD: Explains why this is safe
let value = unsafe {
    // SAFETY: We verified ptr is non-null and properly aligned above.
    // The lifetime is tied to 'a, ensuring the reference remains valid.
    &*ptr
};

// BAD: No safety justification
let value = unsafe { &*ptr };

// BAD: Insufficient explanation
let value = unsafe {
    // SAFETY: It's fine
    &*ptr
};
```

## FFI Guidelines

In Edition 2024 an `extern` block is itself unsafe and **MUST** be written
`unsafe extern "C"`. Attributes that affect linkage — `no_mangle`,
`link_section`, `export_name` — **MUST** be written in the `unsafe(...)` form.

**Why**: nothing checks that a declaration matches the library actually linked.
Declaring `fn strlen(s: *const c_char) -> usize` with the wrong signature is
undefined behaviour at every call site, and before Edition 2024 the declaration
itself needed no `unsafe`. Plain `extern "C" { ... }` in an Edition 2024 crate
fails with "error: extern blocks must be unsafe", and `#[no_mangle]` with
"error: unsafe attribute used without unsafe".[^36]

A wrapper **MUST NOT** hide a failure mode behind `expect`. `CString::new`
fails on an interior null byte, which is ordinary caller input.

```rust
use std::ffi::{CStr, CString, NulError};
use std::os::raw::c_char;

// Edition 2024: the extern block is unsafe, because nothing checks that these
// declarations match the library that is linked in.
unsafe extern "C" {
    fn strlen(s: *const c_char) -> usize;
    fn malloc(size: usize) -> *mut u8;
    fn free(ptr: *mut u8);
}

// GOOD: safe wrapper; the interior-null case is a Result, not a panic.
/// # Errors
///
/// Returns [`NulError`] when `s` contains an interior null byte and therefore
/// has no C string representation.
pub fn safe_strlen(s: &str) -> Result<usize, NulError> {
    let c_string = CString::new(s)?;
    // SAFETY: `c_string` is a valid, null-terminated C string that outlives
    // the call.
    Ok(unsafe { strlen(c_string.as_ptr()) })
}

// GOOD: RAII wrapper for C resources
pub struct CBuffer {
    ptr: *mut u8,
    len: usize,
}

impl CBuffer {
    pub fn new(size: usize) -> Option<Self> {
        // SAFETY: malloc returns null on failure, checked below
        let ptr = unsafe { malloc(size) };
        if ptr.is_null() {
            None
        } else {
            Some(Self { ptr, len: size })
        }
    }
}

impl Drop for CBuffer {
    fn drop(&mut self) {
        // SAFETY: ptr was allocated by malloc and has not been freed
        unsafe { free(self.ptr) };
    }
}

// GOOD: Edition 2024 form for a symbol exported to C
#[unsafe(no_mangle)]
pub extern "C" fn my_crate_version() -> u32 {
    env!("CARGO_PKG_VERSION_MAJOR").parse().unwrap_or(0)
}
```

```rust
// BAD: Edition 2024 rejects both of these.
//   error: extern blocks must be unsafe
//   error: unsafe attribute used without unsafe
extern "C" {
    fn strlen(s: *const c_char) -> usize;
}

#[no_mangle]
pub extern "C" fn my_crate_version() -> u32 { 1 }
```

## Testing Unsafe Code

```rust
#[cfg(test)]
#[allow(clippy::unwrap_used, clippy::expect_used, reason = "test-only allowance")]
mod tests {
    use super::*;

    #[test]
    fn checked_access() {
        let data = [1_u8, 2, 3];
        assert_eq!(get(&data, 0), Some(1));
        assert_eq!(get(&data, 3), None);

        // SAFETY: 2 < data.len().
        assert_eq!(unsafe { get_unchecked(&data, 2) }, 3);
    }

    #[test]
    fn safe_wrapper() {
        let buffer = ZeroedBuffer::new(100).expect("100 > 0");
        assert_eq!(buffer.get(0), Some(0));
        assert_eq!(buffer.get(99), Some(0));
        assert_eq!(buffer.get(100), None);
    }

    #[test]
    fn edge_cases() {
        assert!(ZeroedBuffer::new(0).is_none());

        let mut buffer = ZeroedBuffer::new(1).expect("1 > 0");
        assert_eq!(buffer.get(0), Some(0));
        assert!(buffer.set(0, 42));
        assert_eq!(buffer.get(0), Some(42));
        assert_eq!(buffer.get(1), None);
        assert!(!buffer.set(1, 42));
    }

    #[test]
    #[cfg_attr(miri, ignore = "calls into C")]
    fn ffi_wrapper_reports_interior_nul() {
        assert_eq!(safe_strlen("abc"), Ok(3));
        assert!(safe_strlen("a\0b").is_err());
    }
}
```

Tests over `unsafe` code **MUST** assert on values, not merely on
`is_some()`. `assert!(buffer.get(0).is_some())` passes just as happily when the
byte behind it is uninitialised, so it cannot distinguish a sound
implementation from an unsound one; only Miri or a value assertion can.

## Miri for Undefined Behaviour Detection

Projects with `unsafe` code **SHOULD** run Miri[^26] to detect undefined
behaviour. The nightly toolchain **MUST** be pinned by date, exactly as for
fuzzing.

**Why**: Miri ships only on nightly and is occasionally missing from a given
night's build, so an unpinned `+nightly` job fails intermittently for reasons
unrelated to the code. `rustup component add miri --toolchain <date>` fails
loudly when the component is absent, which is the failure you want.

```bash
rustup toolchain install nightly-2026-09-01 --component miri

# Run the whole suite under Miri
cargo +nightly-2026-09-01 miri test

# Run one test
cargo +nightly-2026-09-01 miri test safe_wrapper

# Stricter aliasing model, and check for leaks
MIRIFLAGS="-Zmiri-tree-borrows -Zmiri-strict-provenance" \
  cargo +nightly-2026-09-01 miri test
```

Miri interprets Rust; it **MUST NOT** be expected to run tests that call into
C. A test that reaches an `extern "C"` function aborts with "unsupported
operation: can't call foreign function". FFI wrappers **SHOULD** therefore be
tested under Miri with the foreign call behind `#[cfg(not(miri))]`, leaving the
pure-Rust invariants covered.

```rust
#[test]
#[cfg_attr(miri, ignore = "calls into C")]
fn ffi_wrapper_reports_interior_nul() {
    assert_eq!(safe_strlen("abc"), Ok(3));
}
```

Miri is slow — typically 10× to 100× native — so it **SHOULD** run on a
schedule or on changes to `unsafe` code rather than on every push.

## Unsafe Antipatterns

```rust
// BAD: Unnecessary unsafe
let x: i32 = unsafe { 5 };  // Nothing unsafe here!

// BAD: Unsafe impl without necessity
unsafe impl Send for MyType {}  // Only if truly needed

// BAD: Transmute for type conversion
let x: u32 = unsafe { std::mem::transmute(1.0f32) };
// GOOD: Use to_bits() instead
let x: u32 = 1.0f32.to_bits();

// BAD: Unchecked indexing without bounds verification
let value = unsafe { *slice.get_unchecked(user_input) };
// GOOD: Bounds check first
if user_input < slice.len() {
    let value = unsafe { *slice.get_unchecked(user_input) };
}
```

## Unsafe Trait Implementations

```rust
// Manually implementing Send/Sync requires careful thought
struct MyWrapper<T> {
    data: *mut T,
}

// SAFETY: MyWrapper can be sent across threads because:
// 1. The pointer is not shared (unique ownership)
// 2. T itself is Send
unsafe impl<T: Send> Send for MyWrapper<T> {}

// SAFETY: MyWrapper can be shared across threads because:
// 1. All access to data is synchronized (not shown)
// 2. T itself is Sync
unsafe impl<T: Sync> Sync for MyWrapper<T> {}
```

## References

[^26]: [Miri](https://github.com/rust-lang/miri) - Experimental interpreter for Rust's mid-level intermediate representation
[^36]: [Announcing Rust 1.85.0 and Rust 2024](https://blog.rust-lang.org/2025/02/20/Rust-1.85.0/) - Edition 2024 stabilisation, 20 February 2025; see the [Edition Guide](https://doc.rust-lang.org/edition-guide/rust-2024/index.html)

## See Also

- [Rust Style Guide](../rust.md) - Toolchain, lints, formatting, dependencies and CI
- [Rust topic guides](README.md) - The other Rust topic guides
