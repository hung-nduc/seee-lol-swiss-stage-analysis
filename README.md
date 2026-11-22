# SEEE LoL Championship 2026 — Swiss Stage analysis

This repo analyses the Swiss Stage of the student League of Legends tournament (SEEE Esport Championship, HUST School of Electrical & Electronic Engineering, 16–22 Nov 2026): 16 teams, 5 rounds, 33 matches.

**Reports** — live at **https://hung-nduc.github.io/seee-lol-swiss-stage-analysis/** (or open the files locally):

| Report | What it covers |
|---|---|
| [`docs/index.html`](docs/index.html) | Overview, final standings, data files, method, data gaps |
| [`docs/a-team-scouting.html`](docs/a-team-scouting.html) | **A. Team scouting**: each team's average Solo/Duo, Flex and Ranked 5s rank; ranked games in 2026; whether the team practises in Flex; rank spread; every roster |
| [`docs/b-swiss-evaluation.html`](docs/b-swiss-evaluation.html) | **B. Swiss Stage evaluation**: standings, round by round, results against rank, the most surprising result, sides, game length, ban & pick by position, which position carries the damage |
| [`docs/c-team-evaluation.html`](docs/c-team-evaluation.html) | **C. Team evaluation**: game time, total gold, gold per minute, gold difference and KDA per game; player leaderboards; every game per team |

## Repository layout

```
data/
  raw/                         original sources, unchanged
    records/                     33 match records (biên bản) — NOT in the public repo
    screenshots/                 28 post-game scoreboards (LSxx.png) — NOT in the public repo
    screenshot_name_map.csv      original screenshot name -> match code
    schedule/swiss_schedule.xlsx Swiss & knockout schedule (final authority for teams/sides)
    opgg_ranks_2026-11-22.csv    op.gg VN snapshot of every player (season 2026)
    remarks.txt                  organiser remarks
  interim/
    records.json                 parsed records (scripts/parse_records.py)
    scoreboards/LSxx.json        scoreboard transcriptions, one per played game
  processed/                   analysis tables (CSV, UTF-8) — see below
docs/                          HTML reports (generated)
scripts/
  parse_records.py             PDF + Excel -> data/interim/records.json
  build.py                     interim + raw -> data/processed/*.csv and docs/*.html
  report.py                    HTML/SVG report templates (no external libraries)
  data_issues.json             list of data gaps and how each was handled
```

## Processed tables (`data/processed/`)

| File | One row per |
|---|---|
| `matches.csv` | match: round, pool, sides, winner, result type (played / forfeit / ruling), game time, rank gap, upset flag |
| `standings.csv` | team: record, Buchholz, rank seed, finish |
| `team_games.csv` | team × played game: K/D/A, gold, gold per minute, gold difference |
| `player_games.csv` | player × played game: position, champion, K/D/A, damage, gold, shares |
| `drafts.csv` | ban or pick: raw name from the record and cleaned name |
| `player_ranks.csv` | player: op.gg Solo/Duo, Flex and Ranked 5s for 2026, Swiss games, champions |
| `team_scouting.csv` | team: average ranks, ranked activity, Flex share |
| `champions.csv` | champion: picks, bans, presence, win rate, positions |
| `role_stats.csv` | position: damage and gold share, damage per minute, top-damage count |
| `team_stats.csv`, `player_stats.csv`, `side_stats.csv` | aggregates |
| `data_issues.csv` | every gap found in the data and how it was handled |

## Rebuild

```bash
pip install -r requirements.txt   # pdfplumber, openpyxl (only for parse_records.py)
python scripts/parse_records.py   # optional: needs the private record PDFs; records.json is committed
python scripts/build.py           # writes data/processed/*.csv and docs/*.html
```

## Method in short

- **Results** come from the match records. The Excel schedule decides teams and sides.
- **Game stats** were transcribed from the scoreboard screenshots. Each team's kills, deaths, assists and gold were checked against the scoreboard header totals.
- **Ranks** were read from op.gg (VN) on 22 Nov 2026 for season 2026 (tier, LP, wins + losses per queue). This is a snapshot after the stage, not before it.
- **Team rank** is the average of the players who actually played, weighted by Swiss games. Ladder values: Iron 4 = 0, Gold 4 = 12, Diamond 1 = 27, Master = 28 + LP/100.
- **Upset** means a played game won by the lineup with the lower average Solo/Duo rank.

## Known data gaps

The full list is in `data/processed/data_issues.csv` and at the bottom of the overview page.

- **5 matches had no game.** 4 were forfeits (LS37, LS38, LS44, LS46) and LS21 was a ruling. They count in the standings but are left out of all game stats.
- **LS13 and LS33** screenshots have no damage column.
- **LS33** has no bans recorded.
- **LS15** has only part of its draft.
- **GLT's substitute in LS34** ("phong"/"Phomai") could not be found on op.gg.
- **YSL's top laner** is listed as `bimiuchiratnhieu#1808` in the records; the real tag is `#1005`.

## Publishing with GitHub Pages

Pages is served from `main` / **root**: The root `index.html` redirects to `docs/index.html`. Publishing from the root keeps the report's links to `data/processed/*.csv` working.

> **Privacy.** The match records and scoreboard screenshots contain students' real names, so they are kept out of this public repo
> (see `.gitignore`). Everything here uses in-game Riot IDs only; `parse_records.py` does not store real names, and redacts them
> from pause notes. `matches.csv` still lists the screenshot path for each game; those files are only in the organisers' private copy.
