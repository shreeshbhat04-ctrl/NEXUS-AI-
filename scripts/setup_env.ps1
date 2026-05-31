python -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .[dev]
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}
Write-Host "Environment ready. Activate later with: .\\.venv\\Scripts\\Activate.ps1"
