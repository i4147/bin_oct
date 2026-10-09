#!/data/data/com.termux/files/usr/bin/env python
"""Design a prompt for an AI coding agent to generate a Termux-targeted Python 3.12 CLI tool that automates common Git branch-comparison and cherry-pick workflows using an interactive terminal UI.

The prompt should specify the following:

**Purpose:**
Create an interactive command-line Git helper script (shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that must be run from inside a Git repository. It hel user compare branify commits that differ between them (e.g., via `git cherry -v`), and interactively select/apply actions (such as cherry-picking) using terminal dialogs instead of manual git commands.

**Key behaviors/requirements:**
- On startup, attempt to open the current directory as a Git repository".")` ( GitPython) and also prw `git.cance for direct command execution. If the current directory is not a valo directory!"` and ex autocomplete call the currentomplete input typ interactive user input/output: use `prompt()` for free text input, and dialog helpers (`yes_no_dialog`, `button_dialog`, `radiolist_dialog`, `checkboxlist_dialog`) for choices/confirmations, with a custom `Style` applied to dialogs.
- Use the `sh` library's `git` callable to run raw git subprocess commands (e.g., `git(["cherry", "-v", first, second])`) when GitPython's API isn't convenient, and parse the text output (split by newlines, split each line by spaces)ashes/colored` for colorizg., highlighting branuses, warlogging` for internal diagnostic/debard `os`/`sys`/`pPath` utment and path handling.
- Define an `Enum` class to represent a fixed set of modes/actions the tool supports (e.g., different operation types the user can pick from in a menu).

**Core logic to implement in a `RepoManager` class with static methods:**
1. `get_list_branches(ignore_current=True)` — return a list of all local branch names, excluding the currently active branch when `ignore_current` is true.
2. `get_autocomplete_list_branches(ctx, args, incomplete)` — click-compatible autocompletion function that returns branch names (excluding current) matching the partially-typed text.
3. `ask(title, text)` — show a yes/no dialog with the given title and text, and return theverify_branch()` — show a yes/no confirmation dialog asking the user to confirm that the currently active branch is the correct one, name.
5. `cher run `git cherry -v <first> <second>` viagit`, parse each output starbol and comm commit message strings (stripping the symping the remaining message tced_remotes()` —spect `repo.refs` to determ sync with their relional hel the overall branch-comparison/cherry-pick workflow, such as listing out-of-sync branches, selecting source/target branches via dialogs, displaying the list of differing commits for user selection via `checkboxlist_dialog`, and applying the chosen action).

**Main program flow:**
Wire this all together under a `click` command (or group) entry point: verify the repo and current branch, let the user pick source/target branches (with autocompletion), compute and display the differing commits between them, let the user select which commits to act on via a checkbox dialog, confirm the action, and execute it (pick) while reporting progress/results with colored output.

Ensure the generated code is a self-contained executable script matching this structure, using the exact imports: `logging`, `os`um.Enum`, `pathlib.Path`, `click`, `colored`, `git` (GitPython), `prompt_toolkit.prompt`, `prompt_toolkit.shortcuts`og`, `radiolist_dialog`, `y`, and `sh.git`.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/jFAN7G73x7DRoCVkjHyF4W"""

import logging
import os
import sys
from enum import Enum
from pathlib import Path

import click
import colored
import git
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import (
    button_dialog,
    checkboxlist_dialog,
    radiolist_dialog,
    yes_no_dialog,
)
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
