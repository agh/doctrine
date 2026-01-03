# EditorConfig Guide

EditorConfig provides consistent coding styles across editors and IDEs. Create a
`.editorconfig` file in your project root.

## Standard Configuration

```ini
# EditorConfig - https://editorconfig.org
root = true

# Default for all files
[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space

# Python
[*.py]
indent_size = 4
max_line_length = 100

# Ruby
[*.rb]
indent_size = 2
max_line_length = 100

# Go (tabs required)
[*.go]
indent_style = tab
indent_size = 4

# Rust
[*.rs]
indent_size = 4
max_line_length = 100

# C#
[*.cs]
indent_size = 4
max_line_length = 100

# JavaScript/TypeScript
[*.{js,jsx,ts,tsx}]
indent_size = 2
max_line_length = 100

# Web (HTML, CSS)
[*.{html,css,scss,less}]
indent_size = 2

# Data formats
[*.{json,yaml,yml,toml}]
indent_size = 2

# Markdown
[*.md]
indent_size = 4
max_line_length = 80
trim_trailing_whitespace = false

# Shell scripts
[*.sh]
indent_size = 2
max_line_length = 80

# SQL
[*.sql]
indent_size = 2
max_line_length = 80

# Makefiles (tabs required)
[Makefile]
indent_style = tab

# Dockerfiles
[Dockerfile*]
indent_size = 4

# Git config
[.git*]
indent_size = 4
```

## Properties Reference

| Property | Values | Description |
| -------- | ------ | ----------- |
| `root` | `true` | Stop searching for .editorconfig |
| `indent_style` | `tab`, `space` | Hard tabs or soft tabs |
| `indent_size` | integer | Number of spaces per indent |
| `tab_width` | integer | Width of a tab character |
| `end_of_line` | `lf`, `cr`, `crlf` | Line ending style |
| `charset` | `utf-8`, `latin1`, etc. | Character encoding |
| `trim_trailing_whitespace` | `true`, `false` | Remove trailing spaces |
| `insert_final_newline` | `true`, `false` | File ends with newline |
| `max_line_length` | integer, `off` | Soft line length limit |

## Editor Support

EditorConfig is supported natively or via plugins:

| Editor | Support |
| ------ | ------- |
| VS Code | Native (settings enable) |
| JetBrains IDEs | Native |
| Vim/Neovim | Plugin: editorconfig-vim |
| Emacs | Plugin: editorconfig-emacs |
| Sublime Text | Plugin: EditorConfig |
| Atom | Plugin: editorconfig |

### VS Code Settings

Add to `.vscode/settings.json`:

```json
{
  "editor.formatOnSave": true,
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,
  "files.eol": "\n"
}
```

## Relationship with Other Tools

EditorConfig works alongside language-specific formatters:

| Tool | Purpose | EditorConfig Relationship |
| ---- | ------- | ------------------------- |
| Prettier | Formatting | Respects `.editorconfig` |
| Ruff | Python formatting | Has own config, sync manually |
| rustfmt | Rust formatting | Has own config, sync manually |
| gofmt | Go formatting | Hardcoded (tabs), no config |
| dotnet format | C# formatting | Respects `.editorconfig` |

### Syncing with Formatters

Keep EditorConfig and formatter configs in sync:

```toml
# pyproject.toml (Ruff)
[tool.ruff]
line-length = 100  # Match .editorconfig max_line_length

[tool.ruff.format]
indent-style = "space"  # Match .editorconfig indent_style
```

## Best Practices

1. **Always set `root = true`** in project root to prevent inheriting from
   parent directories.

2. **Use LF line endings** (`end_of_line = lf`) for consistency across
   platforms. Handle Windows in `.gitattributes`.

3. **Always insert final newline** - POSIX standard, prevents diff noise.

4. **Trim trailing whitespace** - except in Markdown where trailing spaces can
   mean line breaks.

5. **Match formatter configs** - EditorConfig sets editor behavior, but
   formatters enforce on save/commit.
