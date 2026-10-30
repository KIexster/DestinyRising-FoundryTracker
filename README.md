# Foundry Tracker

Foundry Tracker shows your progress in the **Foundry challenges** of Destiny Rising (Global): the achievements that ask for 1,000 kills with 8 different weapons of a collection. Instead of checking every weapon in the game, you see all seven collections at once, how many kills each weapon has and the fastest way to finish each achievement.

## Features

- **All Foundry challenges at a glance:** Exotic Enthusiast, Riviks & Wright, Novak, Strid, Jiangshi Steelworks I & II and Eclipse Monolith, with their progress out of 8.
- **Every weapon of a collection:** kills, kills left to 1,000, a progress bar and its artwork. Click a weapon to open its details.
- **Shortest path:** the fewest kills you need to complete each achievement, and which weapons get you there.
- **Sessions:** start a session before playing, then refresh from the menu to see the kills you gained with each weapon.
- **Share card:** save a PNG of your progress, ready to post.
- **English and Spanish:** more languages can be added with a single JSON file (see *Translations*).
- **Export** your data to CSV or JSON.

## Requirements

- Windows 10 or 11, 64-bit.
- **MuMu Player 12** with **root permission enabled** (see below).
- Destiny Rising **Global**, with your character loaded in the game.
- The game build supported by your version of Foundry Tracker. When the game updates, the app tells you to download the new version.

## Getting started

1. Enable root in MuMu Player:
   1. Open MuMu Player and go to **Settings center → Other**.
   2. Turn on **Root permission**.
   3. Restart MuMu.
2. Open Destiny Rising Global in MuMu and load your character.
3. Run the Foundry Tracker `.exe`. The first read can take 20–60 seconds.
4. Pick an emblem to see its weapons. Use **Refresh from game** (F5) whenever you want new numbers.

If more than one game session is open, keep only the one you want to read.

## Privacy

- Everything stays on your PC. The app only talks to MuMu through ADB on your own machine. It does not use the internet, your login or any NetEase service.
- ADB runs from `%LOCALAPPDATA%\FoundryTracker\adb` on its own port (5041), so it does not interfere with MuMu's ADB, and it is stopped when you close the app.
- It only reads: it does not change memory, inject code, unlock anything or touch your account.
- Your read history (kills per weapon ID) is saved in `%APPDATA%\FoundryTracker\history.json`. Delete that folder to reset it.

## Translations

Interface texts live in `src/lang/<code>.json`. To add a language, copy `en.json`, rename it (for example `pt.json`), translate the `strings` and the `tracker` messages, and set `label` and `thousands`. The language selector picks it up automatically.

## Building from source

Python 3.12 with Tk. Put `adb.exe`, `AdbWinApi.dll` and `AdbWinUsbApi.dll` in `src/adb`, then run `build.ps1` (use `-Python <path>` to choose the interpreter). It creates `.venv-build` with the pinned tools from `requirements-build.txt`, runs the tests and writes the executable, its SHA-256 file and the release zip to `dist`, named after the version in `src/resources.py`. Run the app with `--demo export.json` to open the interface on a saved JSON export without the game, or with `--no-intro` to skip the opening animation.

---

## Disclaimer and Terms of Service

**Foundry Tracker is an unofficial fan project.** It is not made, endorsed or supported by NetEase, Bungie or the Destiny Rising team. Destiny Rising, Destiny, their names, emblems and weapon artwork belong to their respective owners. They are included only to identify the in-game content the app tracks.

**How it reads your data.** To read your kill counters, the app uses root access in MuMu Player to read the memory of the game while it runs. It never writes to memory or sends data anywhere. Even so, reading a game's memory with third-party software can go against the game's Terms of Service, even when nothing is changed. Before using the app, read the Terms of Service of Destiny Rising. You decide whether to use it.

**Use at your own risk.** The publisher of the game may restrict, suspend or ban accounts that use third-party tools. Neither the author nor the contributors are responsible for any action taken against your account, for data loss, or for any other consequence of using this software. Foundry Tracker is provided "as is", without warranty of any kind.

If you don't agree with these terms, don't use Foundry Tracker.
