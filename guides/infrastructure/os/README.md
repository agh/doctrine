# Operating System Fundamentals

> [Doctrine](../../../README.md) > [Infrastructure](../README.md) > Operating Systems

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Overview

This guide covers cross-platform operating system concepts. Platform-specific
details are in dedicated guides:

| Platform | Guide | Primary Use |
| -------- | ----- | ----------- |
| Linux (Debian) | [linux.md](linux.md) | Servers, containers, workstations |
| macOS | *Coming soon* | Development workstations |
| Windows | *Coming soon* | Enterprise, .NET, gaming |

---

## Quick Reference

| Concept | Linux (systemd) | macOS | Windows |
| ------- | --------------- | ----- | ------- |
| Service manager | `systemctl` | `launchctl` | `sc.exe`, Services MMC |
| Package manager | `apt`, `dnf` | `brew` | `winget`, `choco` |
| Firewall | `nftables`, `ufw` | `pf` | Windows Firewall |
| Init system | systemd | launchd | SCM |
| Privilege escalation | `sudo` | `sudo` | UAC, `runas` |
| Shell | bash, zsh | zsh | PowerShell, cmd |
| Filesystem root | `/` | `/` | `C:\` |

---

## Table of Contents

1. [Users and Groups](#users-and-groups)
2. [Permissions](#permissions)
3. [Service Management](#service-management)
4. [Package Management](#package-management)
5. [Filesystem Layout](#filesystem-layout)
6. [Environment Variables](#environment-variables)
7. [Process Management](#process-management)
8. [Choosing an OS](#choosing-an-os)

---

## Users and Groups

### Concepts

All modern operating systems use users and groups to control access:

| Concept | Description |
| ------- | ----------- |
| **User** | Identity that owns processes and files |
| **Group** | Collection of users for shared permissions |
| **Primary group** | Default group for new files |
| **Supplementary groups** | Additional group memberships |
| **Service account** | Non-interactive user for running services |

### Cross-Platform Comparison

| Task | Linux | macOS | Windows |
| ---- | ----- | ----- | ------- |
| Current user | `whoami` | `whoami` | `whoami` |
| List users | `getent passwd` | `dscl . list /Users` | `Get-LocalUser` |
| Create user | `useradd` | `sysadminctl -addUser` | `New-LocalUser` |
| Add to group | `usermod -aG group user` | `dseditgroup -o edit -a user -t user group` | `Add-LocalGroupMember` |
| Service accounts | `useradd --system` | N/A (use `_name`) | `New-LocalUser` + deny logon |

### Best Practices

- **MUST** use dedicated service accounts for each service
- **MUST NOT** run services as root/Administrator unless required
- **SHOULD** use descriptive names (`_prometheus`, `svc_webapp`)
- **SHOULD** disable shell access for service accounts

```bash
# Linux: Create service account
useradd --system --shell /usr/sbin/nologin --home-dir /nonexistent prometheus

# Verify no shell access
getent passwd prometheus
# prometheus:x:998:998::/nonexistent:/usr/sbin/nologin
```

---

## Permissions

### POSIX Permissions (Linux/macOS)

```text
-rwxr-xr-- 1 owner group 4096 Jan 1 12:00 file.txt
│└┬┘└┬┘└┬┘
│ │  │  └── Other: read only
│ │  └───── Group: read + execute
│ └──────── Owner: read + write + execute
└────────── File type (- = file, d = directory, l = symlink)
```

| Permission | Files | Directories |
| ---------- | ----- | ----------- |
| Read (r/4) | View contents | List contents |
| Write (w/2) | Modify contents | Create/delete files |
| Execute (x/1) | Run as program | Enter directory |

### Special Permissions

| Permission | Octal | Effect |
| ---------- | ----- | ------ |
| setuid | 4000 | Run as file owner |
| setgid | 2000 | Run as file group / inherit group in dirs |
| sticky | 1000 | Only owner can delete (used on /tmp) |

### Standard Permission Patterns

| Use Case | Octal | Symbolic | Example |
| -------- | ----- | -------- | ------- |
| Private file | 0600 | `rw-------` | SSH private keys |
| Private directory | 0700 | `rwx------` | `~/.ssh` |
| Config file | 0644 | `rw-r--r--` | `/etc/app.conf` |
| Executable | 0755 | `rwxr-xr-x` | `/usr/bin/app` |
| Shared directory | 2775 | `rwxrwsr-x` | `/var/www` (setgid) |
| Temp directory | 1777 | `rwxrwxrwt` | `/tmp` (sticky) |

### Windows Permissions

Windows uses Access Control Lists (ACLs) with more granular permissions:

| Permission | Description |
| ---------- | ----------- |
| Full Control | All permissions including changing ownership |
| Modify | Read, write, execute, delete |
| Read & Execute | View and run |
| Read | View only |
| Write | Create and modify |

```powershell
# View permissions
Get-Acl C:\path\file.txt | Format-List

# Set permissions
$acl = Get-Acl C:\path
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "Users", "ReadAndExecute", "Allow")
$acl.SetAccessRule($rule)
Set-Acl C:\path $acl
```

### Best Practices

- **MUST** use 0600 for private keys and credentials
- **MUST** use 0700 for directories containing secrets
- **MUST NOT** use 0777 (world-writable) for any file
- **SHOULD** use setgid on shared directories for consistent group ownership

---

## Service Management

### systemd (Linux)

Modern Linux distributions use systemd for service management:

```bash
# Service lifecycle
systemctl start nginx          # Start service
systemctl stop nginx           # Stop service
systemctl restart nginx        # Stop then start
systemctl reload nginx         # Reload config (if supported)
systemctl status nginx         # View status

# Enable/disable on boot
systemctl enable nginx         # Start on boot
systemctl disable nginx        # Don't start on boot
systemctl enable --now nginx   # Enable and start immediately

# View logs
journalctl -u nginx            # All logs for service
journalctl -u nginx -f         # Follow logs
journalctl -u nginx --since "1 hour ago"
```

### launchd (macOS)

macOS uses launchd with plist configuration:

```bash
# Service lifecycle
launchctl load /Library/LaunchDaemons/com.example.app.plist
launchctl unload /Library/LaunchDaemons/com.example.app.plist
launchctl start com.example.app
launchctl stop com.example.app
launchctl list | grep example

# Locations
# /Library/LaunchDaemons/     - System-wide daemons (root)
# /Library/LaunchAgents/      - System-wide agents (user session)
# ~/Library/LaunchAgents/     - Per-user agents
```

### Windows Services

```powershell
# Service lifecycle
Start-Service -Name "nginx"
Stop-Service -Name "nginx"
Restart-Service -Name "nginx"
Get-Service -Name "nginx"

# Enable/disable
Set-Service -Name "nginx" -StartupType Automatic
Set-Service -Name "nginx" -StartupType Disabled

# Create service
New-Service -Name "MyApp" -BinaryPathName "C:\app\myapp.exe" `
    -StartupType Automatic -Description "My Application"
```

### Best Practices

- **MUST** use the native service manager (not cron/Task Scheduler for services)
- **MUST** configure service dependencies correctly
- **SHOULD** use socket activation where available (systemd)
- **SHOULD** configure automatic restart on failure

---

## Package Management

### Comparison

| Feature | apt (Debian) | dnf (Fedora) | brew (macOS) | winget (Windows) |
| ------- | ------------ | ------------ | ------------ | ---------------- |
| Update index | `apt update` | `dnf check-update` | `brew update` | `winget upgrade` |
| Upgrade all | `apt upgrade` | `dnf upgrade` | `brew upgrade` | `winget upgrade --all` |
| Install | `apt install pkg` | `dnf install pkg` | `brew install pkg` | `winget install pkg` |
| Remove | `apt remove pkg` | `dnf remove pkg` | `brew uninstall pkg` | `winget uninstall pkg` |
| Search | `apt search pkg` | `dnf search pkg` | `brew search pkg` | `winget search pkg` |
| Info | `apt show pkg` | `dnf info pkg` | `brew info pkg` | `winget show pkg` |
| List installed | `apt list --installed` | `dnf list installed` | `brew list` | `winget list` |

### Best Practices

- **MUST** update package index before installing
- **MUST** pin versions in automation scripts
- **SHOULD** use unattended-upgrades (Linux) for security updates
- **SHOULD** avoid mixing package managers (apt + snap + pip)

```bash
# Linux: Pin package version
apt install nginx=1.24.0-1

# macOS: Pin formula
brew pin nginx

# Windows: Specify version
winget install nginx --version 1.24.0
```

---

## Filesystem Layout

### Linux (FHS)

```text
/
├── bin/          # Essential user binaries (often → /usr/bin)
├── boot/         # Bootloader files
├── dev/          # Device files
├── etc/          # System configuration
├── home/         # User home directories
├── lib/          # Essential libraries (often → /usr/lib)
├── mnt/          # Temporary mount points
├── opt/          # Optional/third-party software
├── proc/         # Process information (virtual)
├── root/         # Root user's home
├── run/          # Runtime data (tmpfs)
├── srv/          # Service data (web, ftp)
├── sys/          # Kernel/hardware info (virtual)
├── tmp/          # Temporary files
├── usr/          # User programs and data
│   ├── bin/      # User binaries
│   ├── lib/      # Libraries
│   ├── local/    # Locally installed software
│   └── share/    # Architecture-independent data
└── var/          # Variable data
    ├── cache/    # Application cache
    ├── lib/      # State information
    ├── log/      # Log files
    └── run/      # → /run
```

### macOS

```text
/
├── Applications/           # GUI applications
├── Library/               # System-wide support files
├── System/                # macOS system files (SIP protected)
├── Users/                 # User home directories
├── Volumes/               # Mounted volumes
├── bin/, etc/, usr/, var/ # BSD layer (similar to Linux)
├── opt/                   # Homebrew (Apple Silicon)
└── usr/local/             # Homebrew (Intel), local software
```

### Windows

```text
C:\
├── Program Files\         # 64-bit applications
├── Program Files (x86)\   # 32-bit applications
├── ProgramData\           # Application data (all users)
├── Users\                 # User profiles
│   └── <user>\
│       ├── AppData\
│       │   ├── Local\     # Non-roaming app data
│       │   ├── LocalLow\  # Low-integrity app data
│       │   └── Roaming\   # Roaming profiles
│       ├── Desktop\
│       └── Documents\
├── Windows\               # Operating system
│   ├── System32\         # System binaries (64-bit!)
│   └── SysWOW64\         # 32-bit compatibility
└── temp\                  # System temp
```

---

## Environment Variables

### Common Variables

| Variable | Linux/macOS | Windows | Purpose |
| -------- | ----------- | ------- | ------- |
| Home directory | `$HOME` | `%USERPROFILE%` | User's home |
| Temp directory | `$TMPDIR`, `/tmp` | `%TEMP%` | Temporary files |
| Path | `$PATH` | `%PATH%` | Executable search path |
| User | `$USER` | `%USERNAME%` | Current username |
| Shell | `$SHELL` | N/A | Default shell |
| Editor | `$EDITOR` | N/A | Default text editor |

### Setting Variables

```bash
# Linux/macOS - Session
export MY_VAR="value"

# Linux/macOS - Persistent (add to ~/.bashrc, ~/.zshrc)
echo 'export MY_VAR="value"' >> ~/.bashrc

# Linux - System-wide
echo 'MY_VAR="value"' >> /etc/environment
```

```powershell
# Windows - Session
$env:MY_VAR = "value"

# Windows - Persistent (user)
[Environment]::SetEnvironmentVariable("MY_VAR", "value", "User")

# Windows - Persistent (system)
[Environment]::SetEnvironmentVariable("MY_VAR", "value", "Machine")
```

---

## Process Management

### Cross-Platform Commands

| Task | Linux/macOS | Windows |
| ---- | ----------- | ------- |
| List processes | `ps aux` | `Get-Process` |
| Find by name | `pgrep nginx` | `Get-Process nginx` |
| Kill by PID | `kill 1234` | `Stop-Process -Id 1234` |
| Kill by name | `pkill nginx` | `Stop-Process -Name nginx` |
| Force kill | `kill -9 1234` | `Stop-Process -Id 1234 -Force` |
| Process tree | `pstree` | `Get-CimInstance Win32_Process` |
| Resource usage | `top`, `htop` | Task Manager, `Get-Process \| Sort CPU` |

### Signals (Linux/macOS)

| Signal | Number | Purpose |
| ------ | ------ | ------- |
| SIGHUP | 1 | Reload configuration |
| SIGINT | 2 | Interrupt (Ctrl+C) |
| SIGTERM | 15 | Graceful termination |
| SIGKILL | 9 | Immediate termination (cannot be caught) |
| SIGUSR1/2 | 10/12 | User-defined |

```bash
# Send specific signal
kill -HUP $(pgrep nginx)    # Reload nginx
kill -TERM 1234             # Graceful stop
kill -KILL 1234             # Force kill (last resort)
```

---

## Choosing an OS

### Decision Matrix

| Use Case | Recommended | Why |
| -------- | ----------- | --- |
| **Web servers** | Linux (Debian) | Stability, security, performance |
| **Containers** | Linux | Native container support |
| **Databases** | Linux | Performance, tooling |
| **Development** | macOS or Linux | POSIX compatibility, tooling |
| **.NET applications** | Windows or Linux | .NET Core runs on both |
| **Active Directory** | Windows Server | Native integration |
| **File server (SMB)** | Windows or Linux (Samba) | Depends on clients |
| **GPU compute** | Linux | CUDA/driver support |
| **Desktop apps** | Match target users | Native experience |

### Debian vs Ubuntu

| Aspect | Debian | Ubuntu |
| ------ | ------ | ------ |
| Release cycle | ~2 years | 6 months (LTS: 2 years) |
| Support length | ~5 years | 5 years (LTS) |
| Stability | More conservative | Newer packages |
| Use case | Servers, stability | Desktop, cloud |
| Derivatives | Ubuntu, many others | Many derivatives |

**Recommendation**: Use Debian for servers requiring maximum stability; Ubuntu
LTS for cloud deployments with newer packages.

---

## See Also

- [Linux (Debian)](linux.md) — Debian-specific configuration
- [SSH](../services/ssh.md) — SSH server hardening
- [Ansible](../ansible.md) — Automated configuration management
- [Shell Style Guide](../../languages/shell.md) — Shell scripting standards
