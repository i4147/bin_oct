#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that sets up an encrypted dotfiles repository for a user's home directory, so that sensitive files are transparently encrypted before being committed to version control while everything else is Verify that the required command-line encryption and version control tools are installed on the system, and report clearly which ones are missing if any are absent. It should also handle the case where the tools are installed in a non-standard location common on mobile Linux environments.
- Generate a new encryption keypair for the user if one does not already exist, storing the private key securely in the user's configuration directory and making the public key available for reuse. Never overwrite an existing key without explicit confirmation.
- Install a git clean/smudge filter that encrypts files on staging and decrypts them on checkout, so that encryption happens automatically and transparently during normal version control use.
- Configure the user's home-level git attributes so that files matching defined secret patterns (such as secrets directories, `.env` files, `*.secret`, and `*.token` files) are routed through the encryption filter.
- Configure a that irrelevant orbut-unencrypted paths (such as the key directory itself, the b, cache directories, and stor from tracking.
- Initialize a bare git repository for the home directory that uses the home directory as its working tree, and is configured to respect the attributes and ignore rulesear, user-friendly console each step, including progress messages, success confirmations, and actionable error messages that explain what went wrong and how to fix it.
- Handle failures gracefully: abort cleanly on unrecoverable errors, avoid leaving the system in a half-configured state where possible, and never print or log private key material.
- Be safe to re-run: detect existing setup pieces and skip or verify them rather than duplicating or destroying them.
- Print a short summary at the end describing what was configured and the basic next steps the user should take (such as adding files and committing).
---"""

from __future__ import annotations
import os
import shutil
import subprocess
import sys
import textwrap

HOME = os.path.expanduser("~")
AGE_DIR = os.path.join(HOME, ".config", "age")
AGE_KEY = os.path.join(AGE_DIR, "keys.txt")
AGE_PUB = os.path.join(AGE_DIR, "public.key")
FILTER_PATH = os.path.join(HOME, ".local", "bin", "git-age-filter")
REPO_DIR = os.path.join(HOME, "dotfiles.git")
GITATTRIBUTES = os.path.join(HOME, ".gitattributes")
GITIGNORE = os.path.join(HOME, ".gitignore")
SECRET_PATTERNS = [
    "secrets/**",
    "*.secret",
    ".env",
    "*.token",
]
IGNORE_PATTERNS = [
    ".config/age/",
    "dotfiles.git/",
    "storage/",
    "*.log",
    ".cache/",
]


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kw)


def which(binary: str) -> str | None:
    return shutil.which(binary) or (
        os.path.exists(f"/data/data/com.termux/files/usr/bin/{binary}")
        and f"/data/data/com.termux/files/usr/bin/{binary}"
    )


def ensure_tools() -> None:
    missing = [b for b in ("age", "age-keygen", "git") if not which(b)]
    if missing:
        print(f"Missing tools: {', '.join(missing)}")
        print("Install with:  pkg install age git")
        sys.exit(1)


def ensure_age_key() -> str:
    os.makedirs(AGE_DIR, mode=0o700, exist_ok=True)
    if not os.path.exists(AGE_KEY):
        print("Generating age keypair...")
        out = subprocess.run(
            [which("age-keygen") or "age-keygen", "-o", AGE_KEY],
            capture_output=True,
        )
        if out.returncode != 0:
            print(out.stderr.decode(), file=sys.stderr)
            sys.exit(1)
        os.chmod(AGE_KEY, 0o600)
    pubkey = None
    with open(AGE_KEY) as f:
        for line in f:
            if line.startswith("# public key:"):
                pubkey = line.split(":", 1)[1].strip()
                break
    if not pubkey:
        print("Could not find public key in keys.txt", file=sys.stderr)
        sys.exit(1)
    with open(AGE_PUB, "w") as f:
        f.write(pubkey + "\n")
    os.chmod(AGE_PUB, 0o644)
    print(f"age public key: {pubkey}")
    return pubkey


FILTER_SOURCE = r'''#!/data/data/com.termux/files/usr/bin/python
"""Git clean/smudge filter using age. Managed by setup_dotfiles.py."""
import os, subprocess, sys
AGE_BIN = "age"
AGE_KEY_FILE = os.path.expanduser("~/.config/age/keys.txt")
AGE_PUBKEY_FILE = os.path.expanduser("~/.config/age/public.key")
def die(msg, code=1):
    print(f"git-age-filter: {msg}", file=sys.stderr)
    sys.exit(code)
def clean():
    if not os.path.exists(AGE_PUBKEY_FILE):
        die(f"missing public key: {AGE_PUBKEY_FILE}")
    pubkey = open(AGE_PUBKEY_FILE).read().strip()
    p = subprocess.run([AGE_BIN, "-r", pubkey, "-a"],
                       input=sys.stdin.buffer.read(),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        die(f"encrypt failed: {p.stderr.decode(errors='replace')}")
    sys.stdout.buffer.write(p.stdout)
def smudge():
    data = sys.stdin.buffer.read()
    if not data.lstrip().startswith(b"-----BEGIN AGE ENCRYPTED FILE-----"):
        sys.stdout.buffer.write(data); return
    if not os.path.exists(AGE_KEY_FILE):
        print("git-age-filter: no private key; leaving ciphertext", file=sys.stderr)
        sys.stdout.buffer.write(data); return
    p = subprocess.run([AGE_BIN, "-d", "-i", AGE_KEY_FILE],
                       input=data,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        die(f"decrypt failed: {p.stderr.decode(errors='replace')}")
    sys.stdout.buffer.write(p.stdout)
if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("clean", "smudge"):
        die("usage: git-age-filter {clean|smudge}")
    (clean if sys.argv[1] == "clean" else smudge)()
'''


def write_filter() -> None:
    os.makedirs(os.path.dirname(FILTER_PATH), exist_ok=True)
    with open(FILTER_PATH, "w") as f:
        f.write(FILTER_SOURCE)
    os.chmod(FILTER_PATH, 0o755)
    print(f"wrote filter: {FILTER_PATH}")


def write_gitattributes() -> None:
    lines = ["# Managed by setup_dotfiles.py — encrypted via age filter"]
    lines += [f"{p} filter=age diff=age" for p in SECRET_PATTERNS]
    with open(GITATTRIBUTES, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote: {GITATTRIBUTES}")


def write_gitignore() -> None:
    existing = ""
    if os.path.exists(GITIGNORE):
        existing = open(GITIGNORE).read()
    lines = ["# Managed by setup_dotfiles.py"]
    lines += [p for p in IGNORE_PATTERNS if p not in existing]
    mode = "a" if existing else "w"
    with open(GITIGNORE, mode) as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write("\n".join(lines) + "\n")
    print(f"updated: {GITIGNORE}")


def git(*args: str, cwd: str | None = None) -> None:
    cmd = ["git", f"--git-dir={REPO_DIR}", f"--work-tree={HOME}", *args]
    subprocess.run(cmd, check=True, cwd=cwd)


def init_repo() -> None:
    if not os.path.isdir(REPO_DIR):
        run(["git", "init", "--bare", REPO_DIR])
        print(f"initialized bare repo: {REPO_DIR}")
    git("config", "filter.age.clean", FILTER_PATH + " clean")
    git("config", "filter.age.smudge", FILTER_PATH + " smudge")
    git("config", "filter.age.required", "true")
    git("config", "diff.age.textconv", FILTER_PATH + " smudge")
    git("config", "status.showUntrackedFiles", "no")
    git("config", "core.excludesfile", GITIGNORE)
    print("registered age clean/smudge filters")


def main() -> None:
    ensure_tools()
    ensure_age_key()
    write_filter()
    write_gitattributes()
    write_gitignore()
    init_repo()
    print(
        textwrap.dedent(f"""
    ✅ Setup complete.
    Your repo is a bare repo at:
        {REPO_DIR}
    with work-tree = {HOME}
    Add this alias to ~/.bashrc (or ~/.zshrc):
        alias dot='git --git-dir=$HOME/dotfiles.git --work-tree=$HOME'
    Then:
        dot add .gitattributes .gitignore
        dot add .bashrc .zshrc .config/nvim secrets/api-keys.env
        dot commit -m "initial dotfiles (encrypted secrets)"
        dot remote add origin <your-repo-url>
        dot push -u origin main
    Verify a secret is encrypted before pushing:
        dot show HEAD:secrets/api-keys.env
        # should print -----BEGIN AGE ENCRYPTED FILE-----
    🔑 BACK UP {AGE_KEY} somewhere safe (password manager).
    Lose it and the encrypted files are unrecoverable.
    """)
    )


if __name__ == "__main__":
    main()
