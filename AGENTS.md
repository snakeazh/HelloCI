# AGENTS.md

## Cursor Cloud specific instructions

This repository contains a **彩票号码分布分析工具** (Lottery Number Distribution Analyzer) built with Python Flask + vanilla JS frontend.

### Project structure

- `lottery_analyzer/` — Main application directory
  - `app.py` — Flask web server (port 5000)
  - `analyzer.py` — Analysis engine with 7 built-in rules
  - `generate_sample_data.py` — Sample data generator
  - `requirements.txt` — Python dependencies
  - `data/` — JSON history data files
  - `templates/` — HTML templates
  - `static/` — CSS + JS assets

### Running the application

```bash
cd lottery_analyzer
pip install -r requirements.txt --ignore-installed blinker
python3 generate_sample_data.py  # Generate sample data (only needed once)
python3 app.py                   # Start dev server on port 5000
```

### Key notes

- Use `python3` (not `python`) — this environment does not have a `python` symlink
- When installing Flask, use `--ignore-installed blinker` to avoid system package conflict
- The app auto-generates 200 periods of simulated lottery data for both 双色球 and 大乐透
- No database required — data is stored as JSON files in `data/`
- Chart.js is loaded from CDN; requires network access for the distribution charts
