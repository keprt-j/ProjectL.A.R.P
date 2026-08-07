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

# Famous quotes from movies, TV, books, games, etc. (picked at random).
LINE_POOL = [
    "May the Force be with you.",
    "I'll be back.",
    "Here's looking at you, kid.",
    "You talking to me?",
    "There's no place like home.",
    "I'm going to make him an offer he can't refuse.",
    "You can't handle the truth!",
    "Houston, we have a problem.",
    "Say hello to my little friend!",
    "Life is like a box of chocolates.",
    "Why so serious?",
    "I am your father.",
    "To infinity and beyond!",
    "Just keep swimming.",
    "I see dead people.",
    "You're gonna need a bigger boat.",
    "My precious.",
    "Keep your friends close, but your enemies closer.",
    "I feel the need—the need for speed!",
    "Nobody puts Baby in a corner.",
    "Roads? Where we're going, we don't need roads.",
    "I'm the king of the world!",
    "Hakuna Matata.",
    "With great power comes great responsibility.",
    "Get to the chopper!",
    "Hasta la vista, baby.",
    "Carpe diem. Seize the day.",
    "Show me the money!",
    "You had me at hello.",
    "I solemnly swear that I am up to no good.",
    "Winter is coming.",
    "This is the way.",
    "Frankly, my dear, I don't give a damn.",
    "Go ahead, make my day.",
    "The first rule of Fight Club is: you do not talk about Fight Club.",
    "You shall not pass!",
    "Do or do not. There is no try.",
    "Here's Johnny!",
    "Elementary, my dear Watson.",
    "All that is gold does not glitter.",
    "Not all those who wander are lost.",
    "We didn't know we were making memories, we just knew we were having fun.",
    "Let us go on and take the adventure that shall fall to us.",
    "So it goes.",
    "It was the best of times, it was the worst of times.",
    "Call me Ishmael.",
    "In a hole in the ground there lived a hobbit.",
    "The cake is a lie.",
    "War. War never changes.",
    "It's dangerous to go alone! Take this.",
    "Would you kindly?",
    "A man chooses. A slave obeys.",
    "Nothing is true, everything is permitted.",
    "The spice must flow.",
    "Fear is the mind-killer.",
    "One does not simply walk into Mordor.",
    "Valar morghulis.",
    "I drink and I know things.",
    "How you doin'?",
    "We were on a break!",
    "That's what she said.",
    "I am the one who knocks.",
    "Say my name.",
    "Clear eyes, full hearts, can't lose.",
    "Live long and prosper.",
    "Make it so.",
    "Resistance is futile.",
    "The truth is out there.",
    "I want to believe.",
    "All your base are belong to us.",
    "Finish him!",
    "It's a-me, Mario!",
    "Do a barrel roll!",
    "Stay awhile and listen.",
    "You died.",
    "Praise the Sun!",
    "I used to be an adventurer like you. Then I took an arrow in the knee.",
    "Snakes. Why did it have to be snakes?",
    "I am Iron Man.",
    "Avengers, assemble!",
    "I can do this all day.",
    "Great Scott!",
    "There's a snake in my boots!",
    "To boldly go where no one has gone before.",
    "Space: the final frontier.",
    "The name's Bond. James Bond.",
    "Shaken, not stirred.",
    "I'll get you, my pretty, and your little dog too!",
    "Pay no attention to that man behind the curtain.",
    "That is so fetch.",
    "On Wednesdays we wear pink.",
    "I drink your milkshake!",
    "After all, tomorrow is another day!",
    "It's alive! It's alive!",
    "Toto, I've a feeling we're not in Kansas anymore.",
    "I'll have what she's having.",
    "That'll do, pig. That'll do.",
    "Bazinga!",
    "Engage.",
    "Hadouken!",
    "We rob banks.",
    "Excelsior!",
]


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, check=check, text=True, capture_output=True)


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], check=check)


def ensure_git_identity() -> None:
    name = git("config", "user.name", check=False)
    email = git("config", "user.email", check=False)
    if name.returncode != 0 or not name.stdout.strip():
        git("config", "user.name", os.environ.get("GIT_AUTHOR_NAME", "keprt-j"))
    if email.returncode != 0 or not email.stdout.strip():
        git(
            "config",
            "user.email",
            os.environ.get(
                "GIT_AUTHOR_EMAIL",
                "181767491+keprt-j@users.noreply.github.com",
            ),
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
