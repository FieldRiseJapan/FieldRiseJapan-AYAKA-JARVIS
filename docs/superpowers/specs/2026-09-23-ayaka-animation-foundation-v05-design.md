# AYAKA JARVIS v0.5 Animation Foundation Design

## Purpose

Add a safe character-animation state layer that can later drive layered PNG assets or Live2D without modifying the official AYAKA image or regressing the v0.4 voice/UI flow.

## Constraints

- Do not edit, overwrite, regenerate, crop, paint over, or infer facial regions from `assets/characters/ayaka/ayaka_left_official.png`.
- Preserve its SHA-256: `CACD63C36D37FB1F6A0C7DCE3AB3EF7F6EC14601EEC36D9F2B609681547EB030`.
- Preserve CENTER CORE dimensions, CENTER/RIGHT placement, Win32 work-area handling, MOMOKA mode, recognition aliases, VAD/STT, and the v0.4 HUD state flow.
- Any motion that could harm the appearance must be disabled by default and configurable.
- Do not add generated character assets, secrets, or files larger than 10 MB.

## Architecture

Create an animation domain layer independent of Tk rendering:

- `AnimationController` receives JARVIS state transitions, tracks animation timing, and produces immutable animation frames.
- `AnimationFrame` carries renderer-neutral values: vertical breathing offset, blink phase, mouth phase, and speaking status.
- `CharacterAnimationProvider` is the adapter boundary for current and future rendering implementations.
- `StaticImageAnimationProvider` safely applies only supported whole-character motion and otherwise preserves the current static display.

The controller depends on an injected clock and random source so timing behavior is deterministic in tests. Rendering remains owned by `LeftDisplay`; the controller never reads or writes image pixels.

## State and Data Flow

`UiState.set_system_state()` remains the source of truth. The existing UI refresh observes that state and passes it to `AnimationController`. Entering `SPEAKING` starts the speaking signal; leaving it stops the signal. All operational states remain accepted: `STANDBY`, `LISTENING`, `THINKING`, `EXECUTING`, and `SPEAKING`.

The provider receives generated frames on the Tk event loop. Future providers may map blink and mouth phases to closed-eye, half-eye, closed-mouth, open-mouth, or Live2D parameters without changing voice-flow code.

## Safe v0.5 Visual Behavior

- Breathing is a slow whole-character vertical translation capped at 2 pixels.
- Breathing is disabled by default and controlled through configuration.
- HUD pulse timing may be driven from the animation frame while retaining the v0.4 geometry and state labels.
- The official PNG is loaded read-only through the existing Pillow path and is never saved.
- MOMOKA and fallback displays do not apply AYAKA character motion.

## Deferred Behavior and Required Assets

Natural blinking and lip sync are controller/provider capabilities only in v0.5. They are not rendered against the single official PNG.

Natural blinking requires transparent, consistently aligned full-character layers for open, half-closed, and closed eyes, or a rigged Live2D model. Lip sync requires aligned closed/open mouth shapes (preferably additional phoneme shapes) or Live2D mouth parameters. Audio-amplitude input can later drive the existing speaking/mouth interface.

## Error Handling

- Missing optional animation assets cause a static-image fallback, not startup failure.
- Invalid timing or motion settings are rejected or clamped to safe bounds.
- Animation scheduling stops cleanly when the UI closes.
- Rendering exceptions must not stop VAD/STT or state transitions.

## Configuration

Add an animation configuration section with conservative defaults. Breathing is off by default, and its amplitude cannot exceed 2 pixels. Timing values remain independent from voice-pipeline settings.

## Testing and Verification

Use test-driven development for:

- state-to-animation synchronization, including SPEAKING start and stop;
- deterministic timing and safe frame values;
- provider substitution and static fallback;
- breathing disabled by default and capped at 2 pixels;
- no rendered blink or mouth mutation without supporting assets;
- official asset path and exact SHA-256;
- preservation of v0.4 state/HUD behavior and monitor work-area behavior.

Before completion, run the full existing test suite, new regression tests, Python compile checks, CLI help/startup-safe checks, and monitor-discovery checks. Inspect the commit for secrets and newly added files larger than 10 MB. Commit only intended tracked changes and push `feature/ayaka-ear-v0.1` to its configured GitHub remote.
