#!/usr/bin/env python3
"""Daily LARP chronicle bot: roll 1–100, append text, commit, push."""

from __future__ import annotations

import argparse
import os
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHRONICLE = ROOT / "chronicle.txt"
DECLARATION = ROOT / "declaration_of_independence.txt"

# Filler lines for rolls 1–99 (picked at random).
LINE_POOL = [
    "A courier arrives with news from the eastern marches.",
    "Somewhere a dice tower topples; nobody claims responsibility.",
    "The tavern bard misremembers a prophecy and invents a better one.",
    "Fog rolls in. Visibility: dramatic.",
    "A goblin accountant files a complaint in triplicate.",
    "The quest board gains a sticky note that just says 'maybe'.",
    "Two wizards argue about whether fireball is a lifestyle.",
    "A dragon yawns. Markets tremble.",
    "The map folds itself into a paper swan.",
    "Initiative is rolled. Initiative is ignored.",
    "A potion labeled 'probably fine' changes hands.",
    "The party splits. The party regrets splitting.",
    "Natural 20 on intimidation against a houseplant. It wilts.",
    "Rumors say the MacGuffin was in the first chest all along.",
    "A critical miss invents a new local holiday.",
    "The DM smiles. The players do not.",
    "Loot: 3gp, a sock, and unresolved tension.",
    "Side quest accepted. Main quest postponed indefinitely.",
    "Someone casts Speak with Dead on the group chat.",
    "The chronomancer is late. Again.",
]


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, check=check, text=True, capture_output=True)


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], check=check)


def ensure_git_identity() -> None:
    name = git("config", "user.name", check=False)
    email = git("config", "user.email", check=False)
    if name.returncode != 0 or not name.stdout.strip():
        git("config", "user.name", os.environ.get("GIT_AUTHOR_NAME", "LARP Cron Bot"))
    if email.returncode != 0 or not email.stdout.strip():
        git(
            "config",
            "user.email",
            os.environ.get("GIT_AUTHOR_EMAIL", "larp-cron-bot@users.noreply.github.com"),
        )


def append_lines(lines: list[str]) -> None:
    CHRONICLE.parent.mkdir(parents=True, exist_ok=True)
    with CHRONICLE.open("a", encoding="utf-8") as f:
        for line in lines:
            f.write(line.rstrip("\n") + "\n")


def commit_with_message(message: str) -> None:
    git("add", str(CHRONICLE.relative_to(ROOT)))
    status = git("status", "--porcelain", str(CHRONICLE.relative_to(ROOT)))
    if not status.stdout.strip():
        return
    git("commit", "-m", message)


def push_remote() -> None:
    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    result = git("push", "origin", branch, check=False)
    if result.returncode != 0:
        # Empty repo / no upstream yet.
        result = git("push", "-u", "origin", "HEAD", check=False)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(f"git push failed (exit {result.returncode})")


def stamp(prefix: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    return f"[{now}] {prefix}"


def random_line(roll: int, index: int, total: int) -> str:
    body = random.choice(LINE_POOL)
    return stamp(f"roll={roll} line {index}/{total} — {body}")


def chunk_evenly(items: list[str], n_chunks: int) -> list[list[str]]:
    if n_chunks <= 0:
        raise ValueError("n_chunks must be positive")
    if not items:
        return [[] for _ in range(n_chunks)]
    n_chunks = min(n_chunks, len(items))
    base, rem = divmod(len(items), n_chunks)
    chunks: list[list[str]] = []
    i = 0
    for c in range(n_chunks):
        size = base + (1 if c < rem else 0)
        chunks.append(items[i : i + size])
        i += size
    return chunks


def load_declaration_lines() -> list[str]:
    text = DECLARATION.read_text(encoding="utf-8")
    lines = [ln.rstrip() for ln in text.splitlines()]
    # Keep blank lines as spacing inside the chronicle.
    return [ln if ln else "" for ln in lines]


def run_roll(roll: int, *, dry_run: bool = False) -> None:
    print(f"Rolled: {roll}")

    if roll == 100:
        lines = [stamp("NATURAL 100 — The Declaration of Independence")]
        lines.extend(load_declaration_lines())
        commits = 5
        plan = chunk_evenly(lines, commits)
        print(f"Mode: declaration ({len(lines)} lines across {commits} commits)")
    elif 81 <= roll <= 99:
        plan = [[random_line(roll, 1, 1)]]
        print("Mode: single line / single commit")
    elif 1 <= roll <= 80:
        n_lines = roll
        n_commits = max(1, n_lines // 2)
        all_lines = [random_line(roll, i + 1, n_lines) for i in range(n_lines)]
        plan = chunk_evenly(all_lines, n_commits)
        print(f"Mode: {n_lines} lines across {n_commits} commits")
    else:
        raise SystemExit(f"roll must be 1–100, got {roll}")

    if dry_run:
        for i, chunk in enumerate(plan, start=1):
            print(f"--- commit {i}/{len(plan)} ({len(chunk)} lines) ---")
            for line in chunk:
                print(line)
        return

    ensure_git_identity()
    for i, chunk in enumerate(plan, start=1):
        append_lines(chunk)
        commit_with_message(f"larp: roll {roll} — commit {i}/{len(plan)}")
        print(f"Committed {i}/{len(plan)} ({len(chunk)} lines)")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--roll",
        type=int,
        default=None,
        help="Force a specific roll (1–100). Default: random.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written/committed without changing git.",
    )
    p.add_argument(
        "--no-push",
        action="store_true",
        help="Commit locally but do not push.",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="RNG seed for reproducible runs.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    roll = args.roll if args.roll is not None else random.randint(1, 100)
    if not (1 <= roll <= 100):
        raise SystemExit("--roll must be between 1 and 100")

    run_roll(roll, dry_run=args.dry_run)
    if not args.dry_run and not args.no_push:
        push_remote()
        print("Pushed to origin.")


if __name__ == "__main__":
    main()
