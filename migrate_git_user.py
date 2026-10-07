#!/data/data/com.termux/files/usr/bin/env python
"""Create a Termux-compatible Python 3.12 script (shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that automates migrating a developer's local Git/SSH identity from an old GitHub account to a new one on an Android/Termux environment.

The script should define constants at the top for:
- OLD_USERNAME, OLD_EMAIL (the account being replaced)
- NEW_USERNAME, NEW_EMAIL (the account to switch to)
- Paths: HOME (user home directory), SSH_DIR (`~/.ssh`), GIT_CONFIG (`~/.gitconfig`), SSH_KEY_NAME ("id_ed25519"), SSH_KEY_PATH (full path to the key)
- A list of target filenames/glob patterns to scan/update in project files (e.g. "setup.py", "pyproject.toml", "setup.cfg", "package.json", "*.cfg", "*.ini", "*.toml", "*.md", "*.txt", "*.yml", "*.yaml")
- A set of directory names to exclude from any recursive file search (e.g. ".git", "node_modules", "venv", ".venv", "__pycache__", "site-packages", ".cache", ".local", ".npm", ".cargo")

Implement the following functionality using `os`, `re`, `subprocess`, `shutil`, and `pathlib.Path`:

1. A helper `run(cmd, check=True, capture_output=False, input_text=None)` that wraps `subprocess.run`, auto-detecting whether `cmd` is a string (use `shell=True`) or a list (use `shell=False`), always returning text output, and supporting optional stdin input and output capture.

2. `update_git_global_config()` — sets the global git `user.name` and `user.email` to the new username/email using `git config --global`.

3. `remove_old_ssh_keys()` — if the `.ssh` directory exists, iterates over its contents and deletes any file whose name starts with `id_` or equals `known_hosts`, silently ignoring deletion errors.

4. `generate_new_ssh_key()` — ensures the `.ssh` directory exists with permissions `0700`, generates a new ed25519 SSH key pair via `ssh-keygen -t ed25519 -C <new_email> -f <key_path> -N ""` (no passphrase), then sets the private key file permissions to `0600` and the public key file (`<key_path>.pub`) permissions to `0644`.

The script should be structured so these functions can be called in sequence (and likely extended with additional functions, e.g., for scanning/replacing old username/email occurrences in project files matching the target filename patterns, and re-adding the new SSH key to the ssh-agent or displaying it for upload to GitHub) to fully automate switching the machine's git identity and SSH credentials from the old account to the new one, while avoiding scanning irrelevant directories like dependency/cache folders.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/hjAki4EWVgtcN8yNz4jc7x"""

import os
import re
import subprocess
import shutil
from pathlib import Path

OLD_USERNAME = "iho147"
OLD_EMAIL = "isaacaunegh@gmail.com"
NEW_USERNAME = "i4147"
NEW_EMAIL = "yesnacoc@gmail.com"
HOME = Path.home()
SSH_DIR = HOME / ".ssh"
GIT_CONFIG = HOME / ".gitconfig"
SSH_KEY_NAME = "id_ed25519"
SSH_KEY_PATH = SSH_DIR / SSH_KEY_NAME
TARGET_FILENAMES = [
    "setup.py",
    "pyproject.toml",
    "setup.cfg",
    "package.json",
    "*.cfg",
    "*.ini",
    "*.toml",
    "*.md",
    "*.txt",
    "*.yml",
    "*.yaml",
]
EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "site-packages",
    ".cache",
    ".local",
    ".npm",
    ".cargo",
}


def run(cmd, check=True, capture_output=False, input_text=None):
    return subprocess.run(
        cmd, shell=isinstance(cmd, str), check=check, capture_output=capture_output, text=True, input=input_text
    )


def update_git_global_config():
    run(["git", "config", "--global", "user.name", NEW_USERNAME])
    run(["git", "config", "--global", "user.email", NEW_EMAIL])


def remove_old_ssh_keys():
    if SSH_DIR.exists():
        for f in SSH_DIR.iterdir():
            if f.name.startswith("id_") or f.name == "known_hosts":
                try:
                    f.unlink()
                except Exception:
                    pass


def generate_new_ssh_key():
    SSH_DIR.mkdir(mode=0o700, exist_ok=True)
    run(["ssh-keygen", "-t", "ed25519", "-C", NEW_EMAIL, "-f", str(SSH_KEY_PATH), "-N", ""])
    os.chmod(SSH_KEY_PATH, 0o600)
    os.chmod(f"{SSH_KEY_PATH}.pub", 0o644)


def configure_ssh_agent():
    run(["eval", "$(ssh-agent -s)"], check=False)
    agent_out = run(["ssh-agent", "-s"], capture_output=True)
    for line in agent_out.stdout.splitlines():
        if "=" in line and ";" in line:
            key, val = line.split(";")[0].split("=")
            os.environ[key] = val
    run(["ssh-add", str(SSH_KEY_PATH)], check=False)


def write_ssh_config():
    ssh_config_path = SSH_DIR / "config"
    config_block = f"""Host github.com
    HostName github.com
    User git
    IdentityFile {SSH_KEY_PATH}
    IdentitiesOnly yes
"""
    with open(ssh_config_path, "w") as f:
        f.write(config_block)
    os.chmod(ssh_config_path, 0o600)


def should_skip_dir(dirpath):
    parts = Path(dirpath).parts
    return any(p in EXCLUDE_DIRS for p in parts)


def find_target_files():
    matched = set()
    for root, dirs, files in os.walk(HOME):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".git")]
        if should_skip_dir(root):
            continue
        for pattern in TARGET_FILENAMES:
            for f in files:
                if Path(f).match(pattern):
                    matched.add(os.path.join(root, f))
    return matched


def replace_in_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return
    original = content
    content = re.sub(re.escape(OLD_EMAIL), NEW_EMAIL, content)
    content = re.sub(re.escape(OLD_USERNAME), NEW_USERNAME, content)
    if content != original:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass


def scan_and_replace_all():
    files = find_target_files()
    for filepath in files:
        replace_in_file(filepath)


def update_git_remotes_in_repos():
    for root, dirs, files in os.walk(HOME):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        if should_skip_dir(root):
            continue
        if ".git" in dirs:
            repo_path = root
            try:
                remotes = run(["git", "-C", repo_path, "remote", "-v"], capture_output=True, check=False).stdout
                if OLD_USERNAME in remotes:
                    remote_names = set(line.split()[0] for line in remotes.splitlines() if line)
                    for remote in remote_names:
                        url_result = run(
                            ["git", "-C", repo_path, "remote", "get-url", remote], capture_output=True, check=False
                        )
                        old_url = url_result.stdout.strip()
                        new_url = old_url.replace(OLD_USERNAME, NEW_USERNAME)
                        if new_url != old_url:
                            run(["git", "-C", repo_path, "remote", "set-url", remote, new_url], check=False)
                run(["git", "-C", repo_path, "config", "user.name", NEW_USERNAME], check=False)
                run(["git", "-C", repo_path, "config", "user.email", NEW_EMAIL], check=False)
            except Exception:
                pass


def fix_git_config_files():
    for root, dirs, files in os.walk(HOME):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        if should_skip_dir(root):
            continue
        if ".git" in dirs:
            cfg_path = os.path.join(root, ".git", "config")
            if os.path.isfile(cfg_path):
                replace_in_file(cfg_path)


def clear_git_credential():
    credential_paths = [
        HOME / ".git-credentials",
        HOME / ".gitcredentials",
    ]
    for p in credential_paths:
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass
    try:
        run(["git", "config", "--global", "--unset-all", "credential.helper"], check=False)
    except Exception:
        pass
    try:
        run(["git", "config", "--global", "--remove-section", "credential"], check=False)
    except Exception:
        pass
    for helper in ("store", "cache"):
        try:
            run(["git", "credential-" + helper, "erase"], check=False, input_text="\n")
        except Exception:
            pass


def purge_gitconfig_old_identity():
    if not GIT_CONFIG.exists():
        return
    try:
        with open(GIT_CONFIG, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return
    new_content = re.sub(re.escape(OLD_EMAIL), NEW_EMAIL, content)
    new_content = re.sub(re.escape(OLD_USERNAME), NEW_USERNAME, new_content)
    if new_content != content:
        try:
            with open(GIT_CONFIG, "w", encoding="utf-8") as f:
                f.write(new_content)
        except Exception:
            pass


def main():
    print("[1/8] Updating git global config ...")
    update_git_global_config()
    print("[2/8] Purging old identity from ~/.gitconfig ...")
    purge_gitconfig_old_identity()
    print("[3/8] Removing old SSH keys ...")
    remove_old_ssh_keys()
    print("[4/8] Generating new SSH key ...")
    generate_new_ssh_key()
    print("[5/8] Writing ~/.ssh/config ...")
    write_ssh_config()
    print("[6/8] Loading key into ssh-agent ...")
    configure_ssh_agent()
    print("[7/8] Scanning files (setup.py, pyproject.toml, ...) for old identity ...")
    scan_and_replace_all()
    print("[8/8] Fixing git repos (.git/config, remotes, local user) ...")
    update_git_remotes_in_repos()
    fix_git_config_files()
    print("[+] Clearing stored git credentials ...")
    clear_git_credential()
    print("\nDone.")
    print(f"  new username : {NEW_USERNAME}")
    print(f"  new email    : {NEW_EMAIL}")
    print(f"  public key   : {SSH_KEY_PATH}.pub")
    print("\nAdd the following public key to GitHub:")
    try:
        print((SSH_KEY_PATH.parent / (SSH_KEY_NAME + ".pub")).read_text())
    except Exception:
        pass


if __name__ == "__main__":
    main()
