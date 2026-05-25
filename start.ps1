# KDP Builder - standalone bootstrap + run (Windows PowerShell)
# Pierwsze uruchomienie: tworzy venv + instaluje requirements + .env
# Kolejne: od razu odpala serwer na http://localhost:5001

# Uwaga: NIE ustawiamy $ErrorActionPreference="Stop" - PowerShell 5.1
# traktuje warningi pipa pisane na stderr jako bledy terminujace skrypt.
Set-Location -Path $PSScriptRoot

if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "[setup] Tworze venv..." -ForegroundColor Cyan
    python -m venv venv
}

$py = ".\venv\Scripts\python.exe"

& $py -m pip install --upgrade pip 1>$null
Write-Host "[setup] Instaluje zaleznosci (jesli brak)..." -ForegroundColor Cyan
& $py -m pip install -q -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[setup] Utworzono .env z .env.example. Uzupelnij klucze jesli potrzeba." -ForegroundColor Yellow
}

$env:PYTHONUTF8 = "1"
Write-Host ""
Write-Host "Uruchamiam KDP Builder na http://localhost:5001" -ForegroundColor Green
Write-Host "Ctrl+C zatrzymuje serwer." -ForegroundColor DarkGray
Write-Host ""
& $py app.py
