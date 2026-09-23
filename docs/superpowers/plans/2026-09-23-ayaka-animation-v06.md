# v0.6 implementation plan

1. Preserve the v0.5 baseline and document renderer and asset boundaries.
2. Add deterministic tests for blink phases, non-speaking closed mouth, independent flags, reset, provider failures and two-pixel breathing bound.
3. Extend configuration and controller, retaining existing frame fields and provider protocol.
4. Harden LEFT image loading and provider reset. Keep CORE, monitor placement, HUD, commands and VAD/STT implementation untouched.
5. Run full unittest discovery, compile and CLI help; inspect changes for secrets and large files. Verify official image SHA-256 where the binary is available. Commit and push only changed source, docs and tests on the specified feature branch.

## Plan review

The CI environment is Linux/headless and cannot validate live Windows monitor detection or Jabra/TTS output. Existing tests cover monitor work-area placement and voice state transitions; owner must do the final Windows check. The repository's official PNG must be present for the SHA test; lack of binary access is a blocker to declaring full regression green.
