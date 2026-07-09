# Big Brother Fantasy Draft

This project hosts tools and a static site for a Big Brother fantasy draft.

The latest version of the site is deployed at:

https://rclavey.github.io/big_brother

If you are unable to reach the site, ensure that the URL starts with `https://` only once (e.g. avoid typos like `https://https//...`).

## Data layout

Work from the project folder:

```bash
cd /Users/richie/big_brother
```

Current-season Big Brother 28 data entry uses season-specific files in `data/`:

```text
data/picks_bb28.csv
data/winners_bb28.csv
```

Generated Big Brother 28 outputs also live in `data/`:

```text
data/points_bb28.csv
data/log_bb28.csv
data/descriptive_statistics_bb28.txt
```

Completed seasons live in `data/archived_data/` with the same naming pattern:

```text
data/archived_data/picks_bb27.csv
data/archived_data/winners_bb27.csv
data/archived_data/points_bb27.csv
data/archived_data/log_bb27.csv
data/archived_data/descriptive_statistics_bb27.txt
```

Do not edit archived files during normal BB28 updates unless you are intentionally correcting old data.

## Data entry

Most current-season updates should start by editing:

```text
data/picks_bb28.csv
data/winners_bb28.csv
```

In `winners_bb28.csv`:

- `hoh_winners` and `veto_winners` are listed in order by week.
- `off_block`, `other_comp_winners`, and `buy_back` use week/value pairs.
- Week numbers are zero-based in the data: `0` means Week 1, `1` means Week 2, etc.
- `evictions` is the eviction order.
- `americas_favorite` gets one value when known.

## Script workflow

### `generate_static_site.py`

This is the main website and GitHub Pages build script.

Run:

```bash
python3 generate_static_site.py
```

It:

1. Reads the BB28 files in `data/`.
2. Recalculates `data/points_bb28.csv` and `data/log_bb28.csv` when BB28 has picks and scoring data.
3. Loads archived seasons from `data/archived_data/`.
4. Builds the interactive static dashboard.
5. Writes the deployable site to `docs/index.html`.

This is the script to run before deploying the website.

### `pick_analysis.py`

This creates the descriptive stats file for the current BB28 picks.

Run:

```bash
python3 pick_analysis.py
```

It:

1. Reads `data/picks_bb28.csv`.
2. Calculates contestant ranking stats.
3. Writes `data/descriptive_statistics_bb28.txt`.
4. Writes `rankings_plot.png`.

Run this after updating `picks_bb28.csv` if you want the descriptive statistics refreshed.

### `website.py`

This is the older local Flask version.

Run:

```bash
python3 website.py
```

It:

1. Reads BB28 files.
2. Calculates BB28 points.
3. Writes `data/points_bb28.csv` and `data/log_bb28.csv`.
4. Starts a local Flask server on port `5001`.

The polished dashboard and deployed website use `generate_static_site.py`, not this Flask app.

### `calc_points_send_email.py`

This is an older scoring and email helper.

Run:

```bash
python3 calc_points_send_email.py
```

It:

1. Reads `data/picks_bb28.csv` and `data/winners_bb28.csv`.
2. Calculates points.
3. Writes `data/points_bb28.csv`.
4. Generates old-style chart PNGs in the repo root:
   - `total_scores.png`
   - `cumulative_scores.png`

The email section is currently commented out. This script is not needed for the deployed website because `generate_static_site.py` recalculates current-season points.

## Create descriptive stats

After editing BB28 picks, run:

```bash
cd /Users/richie/big_brother
python3 pick_analysis.py
```

This updates:

```text
data/descriptive_statistics_bb28.txt
```

## Preview the website locally

Regenerate the static site:

```bash
cd /Users/richie/big_brother
python3 generate_static_site.py
```

Start a local static server:

```bash
python3 -m http.server 8000 --directory docs
```

Open:

```text
http://127.0.0.1:8000/
```

Stop the server with `Ctrl-C` in the terminal.

## Deploy the website

After editing data and regenerating the static site:

```bash
cd /Users/richie/big_brother
python3 generate_static_site.py
git status
git add -A
git commit -m "Update BB28 data"
git push origin main
```

GitHub Pages serves the generated files under `docs/`, so `python3 generate_static_site.py` must be run before committing whenever the site data changes.
