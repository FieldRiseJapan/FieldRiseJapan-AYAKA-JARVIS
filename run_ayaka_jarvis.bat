@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command "py -3 -m ayaka.ui.integrated --config config.json --work-dir runtime"
