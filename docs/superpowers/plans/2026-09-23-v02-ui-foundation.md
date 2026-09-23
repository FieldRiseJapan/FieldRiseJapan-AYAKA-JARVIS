# AYAKA JARVIS v0.2 UI Foundation Implementation Plan

> **For agentic workers:** This plan covers the first independently testable v0.2 slice.

**Goal:** Add a Windows-capable three-monitor manager and three independent AYAKA-themed UI windows without changing the proven v0.1 audio/STT/VAD path.

**Architecture:** Keep monitor discovery and assignment hardware-independent at the data layer. Use Windows `ctypes` only inside the discovery adapter, then render three Tkinter windows through a UI application that consumes the assigned layout and a small UI state model. The audio loop remains untouched; later voice commands can call the state model and UI methods.

**Tech Stack:** Python standard library (`ctypes`, `tkinter`, `dataclasses`) and existing project dependencies only.

**Spec:** User-provided `pasted_content_4.txt`, PHASE 1–2 sections.

## Global Constraints

- Preserve the proven Jabra → WASAPI → sounddevice → RMS VAD → whisper.cpp → Wake Word → TTS path.
- Do not add OpenAI, paid APIs, cloud services, or large dependencies.
- Do not commit vendor files, whisper models, tokens, secrets, or personal data.
- Use placeholder character panels; no Live2D/3D asset work in this slice.
- Windows three-monitor integration must be verified on the user's Windows PC; Linux validation is unit/static only.

### Task 1: Monitor layout model

- Create `ayaka/ui/monitors.py` with `MonitorInfo`, `MonitorLayout`, `assign_monitors`, and `discover_monitors`.
- Test `assign_monitors` with one, two, and three synthetic monitors; primary maps to LEFT and non-primary monitors map deterministically to CENTER/RIGHT by x-position.
- Implement Windows enumeration through `ctypes.windll.user32`; use a safe single-monitor fallback elsewhere.

### Task 2: UI state model

- Create `ayaka/ui/state.py` with AYAKA/MOMOKA modes, system states, dashboard pages, and navigation history.
- Test mode switching and HOME/SNS/SOUNDON/GITHUB navigation with `戻って` behavior.
- Keep this layer independent from Tkinter and audio.

### Task 3: Three-window renderer

- Create `ayaka/ui/app.py` with LEFT, CENTER, and RIGHT windows, dark navy base, cyan/blue AYAKA theme, placeholder character panel, CORE pulse, dashboard fields, and developer panel.
- Place each window from `MonitorLayout`, not hard-coded coordinates.
- Create `ayaka/ui/launcher.py` and a documented one-command Windows launcher.
- Add UI tests for layout inputs; do not require a graphical display in Linux tests.

### Task 4: Documentation and delivery

- Update README with Phase 1–2 scope, Windows launch command, display mapping, and known limitations.
- Run all unit tests, compilation, CLI help, diff/secret/large-file checks.
- Commit and push to `feature/ayaka-ear-v0.1`.
