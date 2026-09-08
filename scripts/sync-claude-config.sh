#!/usr/bin/env bash
# Install Doctrine's Claude Code configuration into a project's .claude directory.
#
# Ownership: Doctrine owns the component directories (agents, commands, skills,
# infrastructure) and replaces each one on every sync. The project owns
# .claude/settings.json, which is installed only when it is missing unless
# --overwrite-settings is passed.
#
# Usage: scripts/sync-claude-config.sh [--overwrite-settings] [project-dir]
#
# The result is identical whether .claude already exists or not, on both GNU and
# BSD cp, because every source and destination path is named explicitly.
set -euo pipefail

components=(agents commands skills infrastructure)
verify_paths=(settings.json agents/code/reviewer.md commands/code.md skills/README.md)

overwrite_settings=false
if [ "${1-}" = "--overwrite-settings" ]; then
  overwrite_settings=true
  shift
fi

fail() {
  printf 'sync-claude-config: %s\n' "$1" >&2
  exit 1
}

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source_dir=$(cd -- "$script_dir/.." && pwd)/configs/claude
[ -f "$source_dir/settings.json" ] || fail "missing source settings: $source_dir/settings.json"

project_dir=$(cd -- "${1-.}" && pwd) || fail "project directory not found: ${1-.}"
dest=$project_dir/.claude

for component in "${components[@]}"; do
  [ -d "$source_dir/$component" ] || fail "missing source component: $source_dir/$component"
done

mkdir -p "$dest"

for component in "${components[@]}"; do
  # -L dereferences configs/claude/agents and configs/claude/commands, which are
  # symlinks inside the Doctrine checkout; copying them verbatim installs links
  # that dangle in the target project.
  rm -rf "${dest:?}/$component"
  mkdir -p "$dest/$component"
  cp -RL "$source_dir/$component/." "$dest/$component/"
done

if [ -e "$dest/settings.json" ] && [ "$overwrite_settings" = false ]; then
  printf 'sync-claude-config: kept project settings at %s\n' "$dest/settings.json"
else
  cp -f "$source_dir/settings.json" "$dest/settings.json"
fi

for path in "${verify_paths[@]}"; do
  if [ -L "$dest/$path" ] || [ ! -f "$dest/$path" ]; then
    fail "verification failed: $dest/$path is not a regular file"
  fi
done

printf 'sync-claude-config: installed %s\n' "$dest"
