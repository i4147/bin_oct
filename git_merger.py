#!/data/data/com.termux/files/usr/bin/env python
"""Build a self-contained prompt that tells an AI coding agent how to recreate a Python command-line utility for interactive Git branch and commit management in a local repository, based on the behavior described below.

Create a Python 3 command-line script that acts as an interactive Git repository helper, intended to run from the root of a local Git repository (targeting the Termux environment on Android, so the shebang should point to the Termux Python path: /data/data/com.termux/files/usr/bin/env python).

**Startup and repository check**
- On launch, attempt to open the Git repository in the current working directory and create a Git command handle for it.
- If the current directory is not a Git repository, print the message "Not in a repo directory!" and exit immediately. Use a broad exception handler for this check.
- Keep the repository and command handle as module-level variables available to all helper code.

**Dependencies**
- Use the `click` library for command-line option and subcommand definitions, including shell-completion callbacks for branch names.
- Use the `colored` library for colored terminal output.
- Use GitPython (`git` package) for repository access, branches, and active-branch lookup.
- Use the `sh` library for invoking Git subcommands and capturing their output as strings.
- Use `prompt_toolkit` for interactive UI: a single-line `prompt`, and the shortcuts `yes_no_dialog`, `button_dialog`, `radiolist_dialog`, and `checkboxlist_dialog`, styled with `prompt_toolkit.styles.Style`.
- Standard library modules: `logging`, `os`, `sys`, `enum.Enum`, and `pathlib.Path`.

**RepoManager helper class (all static methods)**
- `get_list_branches`: returns the names of all local branches except the currently active branch.
- `get_autocomplete_list_branches(ctx, args, incomplete)`: returns branch names (excluding the active branch) that contain the partial text `incomplete`, for click autocompletion.
- `ask(title, text)`: shows a yes/no dialog and returns the user's boolean answer.
- `verify_branch`: asks the user to confirm the current active branch name via a yes/no dialog.
- `cherry(first, second)`: runs `git cherry -v <first> <second>` through `sh`, splits the output by newline, and parses each line into a commit collection (the parsing logic and the returned structure should be a list of commit entries representing commits present in `second` but not in `first`, each carrying its marker and identifying info). Handle empty output gracefully by returning an empty list.

**Enumerations**
- Define an `Enum` for cherry-pick/commit status markers (for example, a "to apply" state and an "already applied" state), used to classify commits from `git cherry` output (`+` means not yet applied, `-` means already applied in the target).

**Behavior expectations**
- The tool is an interactive workflow: it lists candidate branches, asks the user to verify the current branch, displays commits that differ between two branches, lets the user select which commits to cherry-pick (via a checkbox or radio dialog), and performs the chosen Git operations, reporting results with colored output.
- Use `prompt_toolkit` dialogs for all user choices; use `click` to expose the top-level command and its options/arguments with branch-name autocompletion.
- Logging should be configured through the standard `logging` module for debug/info messages about Git operations.
- Handle the case where there are no other branches to choose from, and the case where `git cherry` returns no output, without crashing.
- Handle user cancellation of dialogs (a `None` result) by aborting the current action cleanly.
- Handle Git command failures (from `sh` exceptions) by reporting the error in colored output and exiting or returning without a traceback.
- Exit with a non-zero status on fatal errors and zero on successful completion or user cancellation.

**Execution**
- Run it as an executable script from inside a Git repository: `python <script> [options]`, with options and branch arguments provided through click.
- Intended to be run in Termux on Android; no network access is required, only local Git operations.

**Output requirements for the reproduction**
- Produce one complete, runnable Python file with a `main` entry point guarded by `if __name__ == "__main__":`, using click's command decorator to start the program.
- Include concise comments only where they clarify non-obvious logic, matching a plain, idiomatic style with 4-space indentation.
---"""

import logging
import os
import sys
from enum import Enum
from pathlib import Path

import click
import colored
import git
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import button_dialog, checkboxlist_dialog, radiolist_dialog, yes_no_dialog
from prompt_toolkit.styles import Style
from sh import git

repo = None
g = None

try:
    repo = git.Repo(".")
    g = git.cmd.Git()
except:
    print("Not in a repo directory!")
    exit()


class RepoManager:
    @staticmethod
    def get_list_branches(ignore_current=True):
        return [branch.name for branch in repo.branches if branch.name != repo.active_branch.name]

    @staticmethod
    def get_autocomplete_list_branches(ctx, args, incomplete):
        return [branch.name for branch in RepoManager.get_list_branches() if incomplete in branch.name]

    @staticmethod
    def ask(title, text):
        return yes_no_dialog(title=title, text=text).run()

    @staticmethod
    def verify_branch():
        return RepoManager.ask(
            "Branch Verification",
            f"Current Branch: {repo.active_branch.name} is this correct?",
        )

    @staticmethod
    def cherry(first, second):
        from sh import git

        cmd = ["cherry", "-v", first, second]
        response = git(cmd).strip().split("\n")

        commits = []

        for commit in response:
            commit = commit.split(" ")

            commits.append(" ".join(commit[2:]))

        return commits

    @staticmethod
    def fetch_synced_remotes():
        refs = repo.refs

        remotes = []

        for ref in refs:
            if isinstance(ref, git.refs.remote.RemoteReference):
                if ref.name not in ["origin/HEAD", "origin/master"]:
                    remotes.append(ref)

        return remotes

    @staticmethod
    def recent_branches(count=os.environ.get("RECENT_COUNT", 5)):
        from sh import git

        cmd = [
            "for-each-ref",
            f"--count={count}",
            "--sort=-committerdate",
            "refs/heads/",
            "--format=%(refname:short)",
        ]
        response = git(cmd)
        return response

    @staticmethod
    def choose_repos_from_list(title, message, items):
        picked = checkboxlist_dialog(
            title=title,
            text=message,
            values=[(x.name, x.name) for x in items],
        ).run()

        selected = []

        if not picked:
            return []

        for item in items:
            for pick in picked:
                if item.name == pick:
                    selected.append(item)
                    break

        return selected


class AuthorManager:
    def __init__(self):
        import json

        self.authors = None

        if os.path.exists("authors.json"):
            with open("authors.json", "r") as f:
                self.authors = json.loads(f.read())
                self.authors = self.authors["authors"]

    def ask(self):
        if self.authors:
            authors = []

            for index, author in enumerate(self.authors):
                name = f"{author['name']} <{author['email']}>"
                authors.append((name, name))

            response = radiolist_dialog(
                title="Reviewer Picker",
                text="Who reviewed this?",
                values=authors,
            ).run()

            if response != None:
                return response

        name = prompt("Whats the reviewers name?: ")
        email = prompt("Whats the reviewers email?: ")

        return f"{name} <{email}>"


class Printer:
    def _default_label_colors(self):
        return colored.fg("white")

    def _default_value_colors(self):
        return colored.fg("white")

    def _generate_label_colors(self, colors):
        if colors:
            return colors
        else:
            return self._default_label_colors()

    def _generate_value_colors(self, colors):
        if colors:
            return colors
        else:
            return self._default_value_colors()

    def autocomplete(self):
        path_folder = os.path.dirname(__file__)
        path = Path(path_folder)
        path_autocomplete = os.path.join(path)

        print(f"""{colored.fg("green")}AUTOCOMPLETE
===============
ZSH:
source {path_autocomplete}/merger-zsh-complete.sh

FISH:
source {path_autocomplete}/merger-fish-complete.sh

BASH:
source {path_autocomplete}/merger-bash-complete.sh
""")

    def banner(self, message="Merger"):
        from pyfiglet import print_figlet

        print_figlet(message, colors="LIGHT_CYAN")

    def merged(
        self,
        label_colors=colored.fg("white") + colored.bg("green"),
        value_colors=colored.fg("white") + colored.bg("green"),
    ):
        label_colors = self._generate_label_colors(label_colors)
        value_colors = self._generate_value_colors(value_colors)

        print(f"{label_colors}Merger: {value_colors} Successfully merged!")

    def branches(
        self,
        label_colors=None,
        value_colors=None,
    ):
        print(f"""{colored.fg("yellow")}Current Branch:\n===============\n{repo.active_branch.name}\n""")
        print(f"""{colored.fg("yellow")}Recent Branches ({os.environ.get("RECENT_COUNT", 5)})\n===============""")
        print(str(RepoManager.recent_branches()) + colored.fg("white"))

    def space(self):
        print("\n")

    def invalid_branch(
        self,
        branch,
        label_colors=colored.fg("white") + colored.bg("red"),
        value_colors=colored.fg("white") + colored.bg("red"),
    ):
        label_colors = self._generate_label_colors(label_colors)
        value_colors = self._generate_value_colors(value_colors)
        print(f"{label_colors}Error: {value_colors} {branch} is not correct! Please try again.")

    def error(
        self,
        label,
        error,
        label_colors=colored.fg("white") + colored.bg("red"),
        value_colors=colored.fg("white") + colored.bg("red"),
    ):
        label_colors = self._generate_label_colors(label_colors)
        value_colors = self._generate_value_colors(value_colors)
        print(f"{label_colors}{label}: {value_colors} {error}")


printer = Printer()


@click.group()
def cli():
    pass


@cli.command()
def help_stats():
    printer.banner()
    printer.branches()


@cli.command()
def help_autocomplete():
    printer.banner()
    printer.autocomplete()


@cli.command()
@click.argument(
    "branch",
    type=click.Choice(RepoManager.get_list_branches()),
    autocompletion=RepoManager.get_list_branches,
)
def merge(branch):

    if RepoManager.verify_branch():
        authorManager = AuthorManager()

        author = authorManager.ask()

        if author is None:
            printer.error("Author", "Not chosen")
            exit()

        commits = "\n".join(RepoManager.cherry(repo.active_branch, branch))

        commit_message = f"""{commits}

Reviewed By: {author}"""

        repo.git.merge("--squash", "--no-log", branch)
        repo.index.commit(commit_message)

        printer.merged()

    else:
        printer.invalid_branch(repo.active_branch.name)


@cli.group(help="Helper functions used for cleaning up")
def clean():
    pass


@clean.command(help="Process to clean up remote branches")
def remote():
    recent_branches = RepoManager.recent_branches(count=999999999)
    remote_branches = RepoManager.fetch_synced_remotes()

    if len(remote_branches) == 0:
        button_dialog(title="ERROR", text="NO REMOTE BRANCHES FOUND", buttons=[("OK", True)]).run()
        exit()

    selected = RepoManager.choose_repos_from_list(
        "BRANCH REMOTE CLEANER",
        "CHOOSE BRANCHES FROM THE LIST BELOW TO DELETE",
        remote_branches,
    )

    if len(selected) == 0:
        print("No branches selected")
        return

    question = RepoManager.ask(
        "ARE YOU SURE?",
        f"ARE YOU SURE YOU WISH TO DELETE THESE BRANCHES?: {', '.join([x.name for x in selected])}",
    )

    if question:
        for x in selected:
            name = x.name.split("/")[1:]
            repo.git.push("origin", "--delete", name)

        button_dialog(title="REMOTES DELETED", buttons=[("OK", True)]).run()
        exit()
    else:
        print("No branches deleted")


@cli.group(help="Development tools")
def tools():
    pass


@tools.command(help="Used to create test branches")
def create_test_branches(names=["1.0.0", "2.0.0", "3.0.0"]):
    origin = repo.remote()

    for x in names:
        branch = repo.create_head(x)
        branch.checkout()
        origin.push(x)

    g.checkout("master")


cli()
