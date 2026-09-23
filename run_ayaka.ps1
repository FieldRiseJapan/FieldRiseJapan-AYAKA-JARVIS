$ErrorActionPreference = "Stop"
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -3 -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt
}
if (-not (Test-Path "config.json")) { Copy-Item config.example.json config.json }
.venv\Scripts\python.exe -m ayaka.main --config config.json --tts
