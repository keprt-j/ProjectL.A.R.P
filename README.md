# Project L.A.R.P.

Daily cron bot that rolls 1–100, appends text to `chronicle.txt`, and pushes commits.

## Rules

| Roll | Behavior |
|------|----------|
| **1–80** | Append that many lines; commit `floor(n/2)` times (at least once), lines split evenly |
| **81–99** | Append one line in one commit |
| **100** | Append the full Declaration of Independence across **5** commits |

## How it runs

GitHub Actions workflow [`.github/workflows/daily.yml`](.github/workflows/daily.yml) runs **daily at 14:00 UTC**, and can also be triggered manually via **Actions → Daily LARP Chronicle → Run workflow**.

## Manual run

```bash
python3 bot.py              # roll, commit, push
python3 bot.py --dry-run    # preview only
python3 bot.py --roll 100   # force a roll
python3 bot.py --no-push    # commit locally only
```

This is just to boost the number of commits I have because having a blank commit graph is cringe and i just cant stand for that
