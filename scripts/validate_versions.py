#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_FILE = PROJECT_ROOT / "configs/pre-commit/.pre-commit-config.yaml"
GUIDES_DIR = PROJECT_ROOT / "guides"

def normalize_repo_url(url: str) -> str:
    """Extract user/repo from a URL."""
    # Remove .git suffix
    url = url.strip().replace('.git', '')
    # Handle ssh or http
    if 'github.com/' in url:
        return url.split('github.com/')[-1]
    return url.split('/')[-1]

def parse_pre_commit_config(file_path: Path) -> Dict[str, str]:
    """Extract repo URLs and revs from pre-commit config, including commented ones."""
    if not file_path.exists():
        print(f"Error: Config file not found at {file_path}")
        sys.exit(1)
        
    content = file_path.read_text()
    tools = {}
    
    # Matches:
    #   - repo: https://github.com/user/repo
    #     rev: v1.2.3
    # Also matches commented out versions:
    #   # - repo: ...
    #   #   rev: ...
    # Capture group 1: repo url, Capture group 2: rev
    
    # We'll iterate line by line to handle the YAML structure simply but robustly enough for this task
    lines = content.splitlines()
    current_repo = None
    
    for line in lines:
        line = line.strip()
        # Check for repo line
        repo_match = re.search(r'repo:\s+(.+)$', line)
        if repo_match:
            current_repo = normalize_repo_url(repo_match.group(1))
            continue
            
        # Check for rev line if we have a repo
        if current_repo:
            rev_match = re.search(r'rev:\s+([^\s]+)', line)
            if rev_match:
                tools[current_repo] = rev_match.group(1)
                current_repo = None # Reset
                
    return tools

def scan_markdown_files(root_dir: Path) -> List[Tuple[Path, str, str]]:
    """Find tool versions mentioned in markdown files."""
    matches = []
    
    # Regex to find: 
    #   repo: https://github.com/user/repo
    #   rev: v1.2.3
    # Captures the full version string including suffixes (e.g., v1.2.3-alpha)
    
    block_pattern = re.compile(r'repo:\s+(.+?)\s*\n\s*rev:\s+([^\s]+)', re.MULTILINE)

    for md_file in root_dir.glob('**/*.md'):
        content = md_file.read_text()
        
        for match in block_pattern.finditer(content):
            repo_url = match.group(1).strip()
            rev = match.group(2).strip()
            repo_key = normalize_repo_url(repo_url)
            matches.append((md_file, repo_key, rev))
            
    return matches

def main():
    print(f"Validating versions against {CONFIG_FILE.relative_to(PROJECT_ROOT)}...")
    
    canonical_versions = parse_pre_commit_config(CONFIG_FILE)
    if not canonical_versions:
        print("No versions found in config file.")
        sys.exit(1)
        
    print(f"Loaded {len(canonical_versions)} canonical tool versions.")
    
    usage_matches = scan_markdown_files(GUIDES_DIR)
    print(f"Found {len(usage_matches)} version references in guides.")
    
    errors = 0
    warnings = 0
    
    for file_path, repo_key, rev in usage_matches:
        canonical_rev = canonical_versions.get(repo_key)
        
        if canonical_rev:
            if rev != canonical_rev:
                print(f"MISMATCH in {file_path.relative_to(PROJECT_ROOT)}:")
                print(f"  Tool: {repo_key}")
                print(f"  Guide says:  {rev}")
                print(f"  Config has:  {canonical_rev}")
                errors += 1
        else:
            # Try to find if the repo key is just a substring (e.g. tool name vs full path)
            # This handles cases where maybe normalization failed or different URL formats
            possible_match = None
            for c_repo in canonical_versions:
                if repo_key.endswith(c_repo) or c_repo.endswith(repo_key):
                    possible_match = c_repo
                    break
            
            if possible_match:
                c_rev = canonical_versions[possible_match]
                if rev != c_rev:
                    print(f"MISMATCH (fuzzy match) in {file_path.relative_to(PROJECT_ROOT)}:")
                    print(f"  Tool: {repo_key} (~= {possible_match})")
                    print(f"  Guide says:  {rev}")
                    print(f"  Config has:  {c_rev}")
                    errors += 1
            else:
                # Tool in guide not found in main config at all
                # print(f"WARNING: Tool {repo_key} not found in config (referenced in {file_path.relative_to(PROJECT_ROOT)})")
                warnings += 1

    if errors == 0:
        print("\nSUCCESS: All guide versions match the canonical configuration.")
        if warnings > 0:
            print(f"(Ignored {warnings} tools present in guides but not in config)")
    else:
        print(f"\nFAILURE: Found {errors} version mismatches.")
        sys.exit(1)

if __name__ == "__main__":
    main()