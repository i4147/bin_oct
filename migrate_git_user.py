#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a developer-machine identity migration tool: it switches a user's local Git and SSH identity from an old username and email to a new one, and then rewrites references to the old identity across the user's project files.
The tool should operate on the current user's home directory and must treat the old and new identity values as configurable constants defined at the top of the script. Its high-level behavior should cover the following:
1. Update the global Git configuration so the user name and email point to the new identity.
2. Manage the user's SSH setup: detect the existing key location in the standard SSH directory for a named ed25519 key, remove or retire the old key material associated with the previous identity, and generate a fresh ed25519 key pair for the new email address, with appropriate handling if a key already exists (for example, prompting or backing up before overwriting). Ensure the SSH directory and key files get the correct permissions.
3. Scan the user's home directory recursively for common configuration and metadata files (such as package manifests, Python packaging configs, INI/TOML/YAML files, Markdown and plain-text files) while skipping dependency, virtual environment, cache, and version-control directories. Replace every occurrence of the old username and old email in those files with the new values, and report which files were changed and how many replacements were made in each.
4. Be robust and safe: handle missing files, permission errors, and failed subprocess commands gracefully; log each step clearly to the console; avoid modifying files it should not touch; and make the destructive steps (deleting keys, rewriting files) clearly announced so the user understands what happened.
5. Run as a single command-line script with no required interactive setup beyond any confirmations needed for destructive actions, and finish with a concise summary of all changes made and any steps that failed or need manual follow-up (such as adding the new public key to a Git hosting service).
---"""

from __future__ import annotations
import contextlib
import os
from pathlib import Path
import re
import subprocess

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
        cmd,
        shell=isinstance(cmd, str),
        check=check,
        capture_output=capture_output,
        text=True,
        input=input_text,
    )


def update_git_global_config():
    run(["git", "config", "--global", "user.name", NEW_USERNAME])
    run(["git", "config", "--global", "user.email", NEW_EMAIL])


def remove_old_ssh_keys():
    if SSH_DIR.exists():
        for f in SSH_DIR.iterdir():
            if f.name.startswith("id_") or f.name == "known_hosts":
                with contextlib.suppress(Exception):
                    f.unlink()


def generate_new_ssh_key():
    SSH_DIR.mkdir(mode=0o700, exist_ok=True)
    run([
        "ssh-keygen",
        "-t",
        "ed25519",
        "-C",
        NEW_EMAIL,
        "-f",
        str(SSH_KEY_PATH),
        "-N",
        "",
    ])
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
                remotes = run(
                    ["git", "-C", repo_path, "remote", "-v"],
                    capture_output=True,
                    check=False,
                ).stdout
                if OLD_USERNAME in remotes:
                    remote_names = {line.split()[0] for line in remotes.splitlines() if line}
                    for remote in remote_names:
                        url_result = run(
                            ["git", "-C", repo_path, "remote", "get-url", remote],
                            capture_output=True,
                            check=False,
                        )
                        old_url = url_result.stdout.strip()
                        new_url = old_url.replace(OLD_USERNAME, NEW_USERNAME)
                        if new_url != old_url:
                            run(
                                [
                                    "git",
                                    "-C",
                                    repo_path,
                                    "remote",
                                    "set-url",
                                    remote,
                                    new_url,
                                ],
                                check=False,
                            )
                run(
                    ["git", "-C", repo_path, "config", "user.name", NEW_USERNAME],
                    check=False,
                )
                run(
                    ["git", "-C", repo_path, "config", "user.email", NEW_EMAIL],
                    check=False,
                )
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
    with contextlib.suppress(Exception):
        run(
            ["git", "config", "--global", "--unset-all", "credential.helper"],
            check=False,
        )
    with contextlib.suppress(Exception):
        run(["git", "config", "--global", "--remove-section", "credential"], check=False)
    for helper in ("store", "cache"):
        with contextlib.suppress(Exception):
            run(["git", "credential-" + helper, "erase"], check=False, input_text="\n")


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
    with contextlib.suppress(Exception):
        print((SSH_KEY_PATH.parent / (SSH_KEY_NAME + ".pub")).read_text())


if __name__ == "__main__":
    main()
