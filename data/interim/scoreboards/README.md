# Scoreboard transcriptions

One JSON per played game, transcribed from `data/raw/screenshots/`. After transcription, kills, deaths, assists and gold were checked against the team totals in the scoreboard header. Roles for FTL (LS16) and HKG (LS42) were corrected afterwards from the champions played. The instructions used for transcription follow.

## Transcription instructions

You transcribe League of Legends post-game scoreboard screenshots (Vietnamese/English client) from a student tournament. Number accuracy matters most.

Inputs
- Screenshots: data/raw/screenshots/<CODE>.png (file name = match code; the match identity is already verified).
- data/interim/records.json — per match: blue/red team, winner, record duration, and `players` (blue/red lists with role + riot ID) and `draft` (record's ban/pick rows; draft rows are PICK ORDER, not roles; champion spellings in records can be wrong).
- the team rosters — team -> player names.

Layouts
1. Standard scoreboard (most): header "CHIẾN THẮNG"/"VICTORY" (or THẤT BẠI/DEFEAT), game time, then ĐỘI 1 / ĐỘI 2 (TEAM 1/2) each with team K/D/A and team gold, then 5 rows: level, player name, champion name, K/D/A, damage dealt to champions (middle number), gold (right number; '.' or ',' are thousands separators).
2. Detailed layout (LS13, LS33): rows show champion ICONS only (no champion name text), K/D/A, CS, gold; NO damage column. Set damage to null. Identify champions from the record draft for that match (cross-check icons). For LS33 the record draft is empty; the user supplied: GOS = Varus, Renekton, Jarvan IV, Aurelion Sol, Leona; ZEN = Rumble, Kayn, Yone, Ezreal, Soraka — assign each to the right player by looking at the icons (zoom crops). LS33 also shows ban icons under "CẤM + MỤC TIÊU": try to identify the 5 bans per team; if unsure, write "?" and say so.

Method (per screenshot)
- Open with the Read tool. For small/low-res images (e.g. LS22, LS24, LS25) crop and upscale regions with Python PIL (run `python3 -I`) into data/interim/scoreboards/crops/ and Read the crops. Zoom whenever any digit is uncertain.
- Map each ĐỘI to the tournament team via player names (roster/matches.json). ZEN = NGU.
- Assign each player's role from matches.json `players` for that match; if the scoreboard champion clearly contradicts the record role (e.g., a support champion on the "TOP" player), keep the record role but note it in `notes`. Scoreboard row order is usually TOP, JG, MID, AD, SP.
- Normalize champion names to official English names (e.g., "Ngộ Không" = Wukong, "Kai'Sa", "Cho'Gath", "Jarvan IV", "K'Sante", "Kog'Maw", "Dr. Mundo"). "Locke" and "Yunara" are real champions.
- VERIFY: sum of player kills/deaths/assists == team K/D/A shown in the header; sum of player gold within ~1% of team gold. If a check fails, re-zoom and fix. If it still fails, keep best reading and explain in notes.
- Winner: compare with matches.json winner; note any disagreement. Game time: note if different from record duration.

Output: one JSON per match at data/interim/scoreboards/<CODE>.json:
{"code":"LS..","layout":"standard|detailed","game_time":"mm:ss","teams":[{"team":"XXX","won":true,"kills":0,"deaths":0,"assists":0,"gold":0,"players":[{"riot":"name#tag from matches.json","name_on_screen":"..","role":"TOP|JG|MID|AD|SP","champion":"..","level":0,"k":0,"d":0,"a":0,"damage":0,"gold":0}]},{...}],"bans":{"TEAM":["..."]} (only if read from screenshot, else omit),"checks_passed":true,"notes":"..."}

Only write files inside data/interim/scoreboards/. Finish with a short table per match: code, teams, time, checks_passed, notes.
