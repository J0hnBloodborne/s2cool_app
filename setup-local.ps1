$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt -r requirements-models.txt
if ($LASTEXITCODE -ne 0) { throw 'Could not install the app packages.' }
& '.\.venv\Scripts\python.exe' -m pip install -r requirements-lstm.txt
if ($LASTEXITCODE -ne 0) { throw 'Could not install CPU PyTorch.' }
Write-Host 'Ready. Start with: .\.venv\Scripts\python.exe run.py'
