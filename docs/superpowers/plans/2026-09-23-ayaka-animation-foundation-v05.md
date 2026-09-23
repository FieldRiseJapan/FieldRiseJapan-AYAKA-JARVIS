# AYAKA JARVIS v0.5 Animation Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a renderer-neutral animation controller and safe static-image adapter without altering the official AYAKA PNG or changing the proven v0.4 voice, HUD, and monitor behavior.

**Architecture:** A pure `ayaka.ui.animation` domain module converts JARVIS states and deterministic timing inputs into immutable animation frames. `LeftDisplay` owns a static-image provider that may apply only a configurable 0–2 pixel whole-character breathing offset; blink and mouth signals remain available for future layered-PNG or Live2D providers but do not modify pixels today. `JarvisUiApp` schedules animation independently from the existing 500 ms UI refresh so CENTER CORE timing and layout stay unchanged.

**Tech Stack:** Python 3.13, dataclasses, enums, typing protocols, Tkinter, Pillow, unittest

**Spec:** `docs/superpowers/specs/2026-09-23-ayaka-animation-foundation-v05-design.md`

## Global Constraints

- Do not edit, overwrite, regenerate, crop, paint over, or infer facial regions from `assets/characters/ayaka/ayaka_left_official.png`.
- Preserve official-image SHA-256 `CACD63C36D37FB1F6A0C7DCE3AB3EF7F6EC14601EEC36D9F2B609681547EB030`.
- Preserve CENTER CORE dimensions, CENTER/RIGHT placement, Win32 work-area handling, MOMOKA mode, recognition aliases, VAD/STT, and the v0.4 HUD state flow.
- Breathing is disabled by default and cannot move the character more than 2 pixels.
- No generated character assets, secrets, or new files larger than 10 MB.
- Blinking and lip sync must not be rendered until aligned differential assets or a Live2D model exist.

## Review Focus

- A configuration amplitude above 2 pixels must be clamped to 2; a negative amplitude must be clamped to 0.
- Repeated `SPEAKING` frames without audio levels must remain closed/static rather than inventing facial motion.
- Leaving `SPEAKING`, including a direct transition to `LISTENING`, must clear the speaking flag and mouth level immediately.
- MOMOKA mode or fallback rendering must reset any AYAKA offset to zero and never leave the image displaced.
- A provider exception must be contained by the animation update path so the existing voice/UI refresh can continue.

---

### Task 1: Animation Configuration and Pure State Controller

**Files:**
- Create: `ayaka/ui/animation.py`
- Modify: `ayaka/config.py`
- Modify: `ayaka/main.py`
- Modify: `config.example.json`
- Test: `tests/test_animation.py`
- Modify: `tests/test_core.py`

**Interfaces:**
- Consumes: `JarvisState` from `ayaka.ui.state`; `load_config(path: Path | None) -> AppConfig` from `ayaka.main`.
- Produces: `AnimationConfig`, `BlinkPhase`, `AnimationFrame`, `CharacterAnimationProvider`, and `AnimationController.update(state: JarvisState, *, now: float | None = None) -> AnimationFrame`; `AnimationController.set_speaking_level(level: float) -> None`.

- [ ] **Step 1: Write failing configuration tests**

Add tests proving `AnimationConfig().breathing_enabled is False`, its effective amplitude is safe, legacy JSON without `animation` still loads, and JSON containing `animation` is parsed. Use a temporary JSON file with `{"animation":{"breathing_enabled":true,"breathing_amplitude_px":2,"breathing_period_seconds":4.0,"frame_interval_ms":100}}` and assert those exact values.

- [ ] **Step 2: Run configuration tests and verify RED**

Run: `python -m unittest tests.test_core.ConfigTests -v`

Expected: FAIL because `AnimationConfig` and `AppConfig.animation` do not exist.

- [ ] **Step 3: Add minimal configuration implementation**

Add this immutable configuration to `ayaka/config.py` and add it to `AppConfig`:

```python
@dataclass(frozen=True)
class AnimationConfig:
    breathing_enabled: bool = False
    breathing_amplitude_px: int = 1
    breathing_period_seconds: float = 4.0
    frame_interval_ms: int = 100

    @property
    def safe_breathing_amplitude_px(self) -> int:
        return min(2, max(0, self.breathing_amplitude_px))
```

Update `load_config()` to construct `AnimationConfig(**raw.get("animation", {}))`. Add the same four conservative values under an `animation` object in `config.example.json`.

- [ ] **Step 4: Run configuration tests and verify GREEN**

Run: `python -m unittest tests.test_core.ConfigTests -v`

Expected: all `ConfigTests` pass.

- [ ] **Step 5: Write failing controller tests**

Create `tests/test_animation.py` with deterministic tests using an injected clock and interval source. Cover:

```python
controller = AnimationController(AnimationConfig(), clock=lambda: 10.0, blink_interval=lambda: 4.0)
frame = controller.update(JarvisState.SPEAKING, now=10.0)
self.assertTrue(frame.speaking)
self.assertEqual(frame.mouth_open, 0.0)
controller.set_speaking_level(1.5)
self.assertEqual(controller.update(JarvisState.SPEAKING, now=10.1).mouth_open, 1.0)
self.assertFalse(controller.update(JarvisState.LISTENING, now=10.2).speaking)
self.assertEqual(controller.update(JarvisState.LISTENING, now=10.2).mouth_open, 0.0)
```

Also assert disabled breathing always yields zero, enabled breathing stays within `-2..2` even when configured as `99`, negative amplitude yields zero, and blink timing progresses `OPEN -> HALF -> CLOSED -> HALF -> OPEN` without changing image data.

- [ ] **Step 6: Run controller tests and verify RED**

Run: `python -m unittest tests.test_animation -v`

Expected: FAIL because `ayaka.ui.animation` does not exist.

- [ ] **Step 7: Implement the pure animation domain**

Create:

```python
class BlinkPhase(str, Enum):
    OPEN = "OPEN"
    HALF = "HALF"
    CLOSED = "CLOSED"

@dataclass(frozen=True)
class AnimationFrame:
    state: JarvisState
    vertical_offset_px: int = 0
    blink_phase: BlinkPhase = BlinkPhase.OPEN
    mouth_open: float = 0.0
    speaking: bool = False

class CharacterAnimationProvider(Protocol):
    def apply(self, frame: AnimationFrame) -> None: ...
    def reset(self) -> None: ...
```

Implement `AnimationController` with injected `clock: Callable[[], float]` and `blink_interval: Callable[[], float]`. Initialize the first blink deadline from the interval source. Use fixed 80 ms half-close, 120 ms closed, and 80 ms half-open phases. Compute breathing with a sine wave using `safe_breathing_amplitude_px` and round to an integer. Clamp speaking levels to `0.0..1.0`; expose them only while state is `SPEAKING`, clearing the effective mouth value immediately on any other state.

- [ ] **Step 8: Run controller and full tests**

Run: `python -m unittest tests.test_animation -v`

Expected: all animation tests pass.

Run: `python -m unittest discover -s tests -v`

Expected: all existing and new tests pass.

- [ ] **Step 9: Commit Task 1**

```powershell
git add ayaka/ui/animation.py ayaka/config.py ayaka/main.py config.example.json tests/test_animation.py tests/test_core.py
git commit -m "feat: add AYAKA animation state controller"
```

### Task 2: Safe Static-Image Provider and UI Scheduling

**Files:**
- Modify: `ayaka/ui/left_display.py`
- Modify: `ayaka/ui/app.py`
- Modify: `ayaka/ui/integrated.py`
- Modify: `tests/test_animation.py`
- Modify: `tests/test_left_display.py`
- Modify: `tests/test_ui.py`

**Interfaces:**
- Consumes: `AnimationConfig`, `AnimationController`, `AnimationFrame`, and `CharacterAnimationProvider` from Task 1.
- Produces: `StaticImageAnimationProvider.apply(frame)`, `StaticImageAnimationProvider.reset()`, `LeftDisplay.animate(state)`, and `JarvisUiApp(..., animation_config: AnimationConfig | None = None)`.

- [ ] **Step 1: Write failing provider tests**

Use a fake label whose `place_configure(**kwargs)` records calls. Assert an enabled frame with `vertical_offset_px=2` produces only `{"y": 2}`, `reset()` produces `{"y": 0}`, and blink/mouth values do not trigger image pixel operations. Use a raising provider to assert `LeftDisplay.animate()` catches provider exceptions and resets safely.

- [ ] **Step 2: Run provider tests and verify RED**

Run: `python -m unittest tests.test_left_display -v`

Expected: FAIL because `StaticImageAnimationProvider` and `LeftDisplay.animate` do not exist.

- [ ] **Step 3: Implement the safe provider adapter**

Add `StaticImageAnimationProvider` to `left_display.py`. It receives the existing Tk image label and applies only `place_configure(y=frame.vertical_offset_px)`. It must not open, crop, composite, save, or otherwise touch image pixels. Add an `AnimationController` and provider to `LeftDisplay`; `animate(state)` generates one frame and applies it inside a narrow exception boundary. `show_fallback()` and error handling call `reset()` so offsets cannot leak into MOMOKA/fallback mode.

- [ ] **Step 4: Run provider tests and verify GREEN**

Run: `python -m unittest tests.test_left_display -v`

Expected: all left-display tests pass.

- [ ] **Step 5: Write failing scheduling and state-flow tests**

Add tests proving `JarvisUiApp` accepts an animation configuration without changing `CENTER_CORE_SIZE`, the existing `refresh()` interval remains 500 ms, `_refresh_animation()` schedules itself with `frame_interval_ms`, AYAKA mode calls `left_display.animate(current_state)`, and MOMOKA mode calls the display reset/fallback path. Retain the existing voice-flow sequence assertion for `LISTENING -> THINKING -> EXECUTING -> SPEAKING -> LISTENING`.

- [ ] **Step 6: Run scheduling tests and verify RED**

Run: `python -m unittest tests.test_ui -v`

Expected: FAIL because `JarvisUiApp` has no animation configuration or independent animation refresh.

- [ ] **Step 7: Connect animation without changing existing refresh timing**

Extend `JarvisUiApp.__init__` with optional `animation_config`, pass it into `LeftDisplay`, and add `_refresh_animation()` that animates only in AYAKA mode and reschedules itself through `root.after(animation_config.frame_interval_ms, self._refresh_animation)`. Start this loop from `run()` alongside the unchanged `refresh()` method. In `integrated.run()`, pass `config.animation` to `JarvisUiApp`. Do not alter `STATE_HOLD_MS`, `VoiceUiFlow`, CENTER CORE constants, monitor geometry, or HUD bounds.

- [ ] **Step 8: Run focused and full regression tests**

Run: `python -m unittest tests.test_ui tests.test_left_display tests.test_animation -v`

Expected: all focused tests pass.

Run: `python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 9: Commit Task 2**

```powershell
git add ayaka/ui/left_display.py ayaka/ui/app.py ayaka/ui/integrated.py tests/test_animation.py tests/test_left_display.py tests/test_ui.py
git commit -m "feat: connect safe AYAKA animation provider"
```

### Task 3: Asset Integrity, Documentation, and Release Verification

**Files:**
- Modify: `tests/test_left_display.py`
- Modify: `README.md`
- Verify unchanged: `assets/characters/ayaka/ayaka_left_official.png`

**Interfaces:**
- Consumes: official asset resolver and animation configuration/provider behavior from Tasks 1–2.
- Produces: permanent SHA-256 regression guard and operator documentation for v0.5.

- [ ] **Step 1: Write the failing asset-integrity regression test**

Add a test that streams the official file into `hashlib.sha256()` and asserts the lowercase digest equals `cacd63c36d37fb1f6a0c7dce3ab3ef7f6ec14601eec36d9f2b609681547eb030`. Temporarily use a deliberately wrong expected digest, run it once, and confirm the observed digest is the approved one; then replace the expectation with the approved digest.

- [ ] **Step 2: Run the integrity test and verify RED then GREEN**

Run with the wrong digest: `python -m unittest tests.test_left_display.LeftDisplayAssetTests.test_official_asset_sha256_is_unchanged -v`

Expected: FAIL showing the approved digest.

Run after restoring the approved digest: the same command.

Expected: PASS.

- [ ] **Step 3: Document v0.5 behavior and deferred assets**

Add a README section stating that the controller/provider foundation is implemented, breathing is optional and off by default, and the original PNG is unchanged. Explicitly state that visible blinking requires aligned open/half/closed-eye transparent layers or Live2D, while visible lip sync requires aligned mouth shapes or Live2D mouth parameters; neither is faked from the single PNG.

- [ ] **Step 4: Run fresh compile, CLI, monitor, and full-suite checks**

Run:

```powershell
python -m compileall -q ayaka tests
python -m ayaka.ui.launcher --help
python -m ayaka.ui.launcher --print-layout
python -m ayaka.ui.integrated --help
python -m unittest discover -s tests -v
```

Expected: every command exits 0; layout prints LEFT, CENTER, and RIGHT roles; the full suite reports zero failures and zero errors.

- [ ] **Step 5: Verify protected behavior and repository hygiene**

Run:

```powershell
Get-FileHash assets/characters/ayaka/ayaka_left_official.png -Algorithm SHA256
git diff --check
git status --short
git diff --name-only cae3024 --
git diff --numstat cae3024 --
git ls-files -o --exclude-standard
```

Confirm the official hash is exactly `CACD63C36D37FB1F6A0C7DCE3AB3EF7F6EC14601EEC36D9F2B609681547EB030`; CENTER/RIGHT, monitor, MOMOKA, alias, VAD/STT, and HUD test files pass unchanged except for intentional regression assertions; no intended added file exceeds 10 MB. Search only intended tracked additions for common secret signatures such as `api_key`, `secret`, `token`, `password`, `AKIA`, and private-key headers, and confirm no credential value was added. Exclude the pre-existing untracked `python_test.txt`, `transcript_test.txt`, and `vendor/` from every commit.

- [ ] **Step 6: Commit documentation and integrity guard**

```powershell
git add README.md tests/test_left_display.py
git commit -m "test: protect AYAKA v0.5 visual integrity"
```

- [ ] **Step 7: Request whole-branch code review and fix all Critical/Important findings**

Review the diff from `cae3024` through `HEAD` against the design spec and this plan. Re-run the affected focused tests after every fix and the full test suite after the final fix.

- [ ] **Step 8: Perform final fresh verification and push**

Repeat Steps 4–5 after review fixes. Then run:

```powershell
git push origin feature/ayaka-ear-v0.1
```

Expected: push succeeds and reports the final implementation commit on `origin/feature/ayaka-ear-v0.1`.
