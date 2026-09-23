# AYAKA JARVIS v0.6 design

## Baseline and invariants

Baseline is `52607fa06deca35d7bba2aae8b32ffed605239c1`. The official image remains an immutable source asset, verified against the prescribed SHA-256 on the Windows checkout. No face geometry is inferred from it. Existing HUD, Win32 work-area positioning, CENTER CORE, mode switching and voice pipeline retain their interfaces.

## Data path

`UiState` provides the existing operational state. `AnimationController` samples a clock and injected blink interval source and emits `AnimationFrame` with blink phase, discrete mouth shape, speaking flag and integer vertical displacement. `CharacterAnimationProvider` consumes the frame. The static provider uses only the whole-image offset; a differential provider can be plugged in later when independently approved, aligned transparent PNG layers exist. No differential layers are bundled in v0.6.

Flags `enabled`, `blink_enabled`, `lipsync_enabled` and `breathing_enabled` independently gate the signals. Breathing defaults OFF and is clamped to two pixels. Blink schedules variable intervals through an injected callable for repeatable tests. SPEAKING alone accepts normalized output level; all other states and reset close the mouth. A missing or invalid level closes the mouth. The audio output path currently exposes no level callbacks, so the level input remains at zero until a trustworthy TTS output meter is integrated.

Provider errors are contained in LEFT; reset returns the static official picture to zero offset. If the official file is missing or unreadable, the existing fallback panel is shown. On MOMOKA mode the AYAKA animation resets; returning to AYAKA starts from a clean controller state.

## Review

The baseline already has a blink timer, normalized mouth level and breathing clamp. Gaps: independent flags, discrete mouth shape, reset across mode transitions, PNG load error containment, and documented asset contract. A static PNG cannot show actual eyelid or mouth changes. Do not call that visual work complete until aligned assets are approved and tested on the owner's three-monitor Windows machine.
