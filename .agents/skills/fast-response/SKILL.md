---
name: fast-response
description: Use for straightforward questions, known information, and low-risk tasks that need a direct answer. Avoid unnecessary research, file reads, planning, and tool calls while preserving accuracy and required checks.
---

# Fast Response

Use the fast route only when the request is simple, low-risk, and answerable from the current conversation or a small, clearly identified source.

## Fast route

1. Identify the requested result and any explicit constraints.
2. Use the conversation context when it already contains the needed, current information.
3. Read only the specific file or section needed. Do not load a whole repository, history, or large file when a targeted lookup is enough.
4. Skip tools when they add no evidence or capability. Do not repeat a search, read, or check whose result is still valid for this task.
5. Keep planning proportional: for a one-step task, act directly; for several independent read-only checks, batch or parallelize them when safe.
6. Answer directly and stop when the requested result is complete.

## Keep accuracy and safety

- Do not use the fast route when the task involves debugging, code changes, security, credentials, data migrations, important Git operations, or another high-impact action. Use the appropriate deeper workflow and targeted verification.
- Check current sources when the user asks for current information or when the fact may have changed. Do not treat old context as current evidence in those cases.
- Never skip a necessary confirmation, safety gate, permission check, or verification just to save time.
- State uncertainty plainly. Do not describe unchecked work as verified or passed.
- Do not cache or expose credentials, tokens, secrets, or private information.
- Do not automatically install or execute external skills, code, or scripts. Review their contents and origin first.

The fast route reduces avoidable work; it does not change access controls, security requirements, or the evidence needed for a reliable answer.
