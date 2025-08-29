Space Invaders: Bonus Blitz Edition

A fast paced arcade shooter built with Pygame, featuring dynamic level progression, bonus rounds, and a local leaderboard. Blast your way through waves of enemies and asteroids while climbing the ranks!

* Features

- 10 progressively harder levels with increasing spawn rates
- Bonus rounds every 3 levels (Levels 3, 6, 9) with asteroid only mayhem
- Local leaderboard with name entry for top 3 scores
- Health refills at key milestones (Levels 4 & 6)
- Pause functionality (ESC key)
- Clean HUD displaying score, health, level, and bonus stats

* Controls

| Action        | Key(s)              |
|---------------|---------------------|
| Move          | Arrow keys or WASD  |
| Shoot         | Spacebar            |
| Pause/Resume  | ESC                 |
| Menu Select   | Arrow keys + Enter  |

* Requirements

- Python 3.7+
- Pygame pip install pygame


* Make sure leaderboard.json is in the same directory (it will be created automatically if missing).

* Game Progression
Levels 1–3: +350 points to advance

Levels 4–6: +550 points to advance

Levels 7–10: +650 points to advance

Bonus rounds last 25 seconds and award extra points (but don’t count toward level advancement)

* Leaderboard
After each game, if your score qualifies for the top 3, you’ll be prompted to enter your name. Scores are saved locally in leaderboard.json.
