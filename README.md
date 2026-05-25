# KDP Builder — standalone

Wyciągnięta podgrupa narzędzi z `pythonmoneyv3/dashboard` zawierająca **wyłącznie** stack KDP:

- `/kdp` — hub
- `/kdp/coloring` — Coloring Bot
- `/kdp/flashcard` — Flashcard Bot
- `/kdp/cover` — Cover Generator
- `/kdp/builder` — Book Builder (one-click)
- `/kdp/activity` — Activity Book (mazes / dots / sudoku / wordsearch)
- `/kdp/quotes/generate` — auto-cytaty (Amazon → Claude Sonnet 4.6)

Działa na **porcie 5001**, żeby nie kolidować z oryginalnym dashboardem (port 5000).

## Pierwsze uruchomienie

```powershell
cd dashboard_kdp
.\start.ps1
```

Skrypt sam zakłada `venv/`, instaluje zależności i odpala serwer. Później wystarczy ponownie `.\start.ps1`.

## Ręcznie

```powershell
cd dashboard_kdp
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # uzupełnij FLASK_SECRET_KEY (+ opcjonalnie ANTHROPIC_API_KEY, SCRAPEOPS_API_KEY)
$env:PYTHONUTF8 = "1"
python app.py
# → http://localhost:5001
```

## Smoke test

```powershell
$env:PYTHONUTF8 = "1"; .\venv\Scripts\python.exe -m pytest tests/ -v
# → 10 passed
```

## Co NIE jest wyciągnięte

Narzędzia spoza KDP zostały świadomie pominięte: Amazon Parser, Comparison Bot, Pinterest/Keywords, TikTok scraper. Jeśli ich potrzebujesz, użyj oryginalnego dashboardu (port 5000).
