# PROCESS.md

## Iteration Cycle

Every f_N evolution follows this sequence:

```
evaluate → mutate → review → benchmark → promote → document
```

### Step Details

**evaluate**
- Read current engine hash from manifest
- Gather fitness signals from telemetry artifacts
- Compute f(Link) for current blob

**mutate**
- Derive mutation goal from fitness signals
- Use `evolve.py --label <discovery|planning|judge|engine>`

**review**
- Triple-pass: Static Analysis → Safety Verification → Protocol Compliance
- Run `promote.py` (which runs all three passes)

**benchmark**
- Execute blob against test suite
- Record latency, success rate, memory usage

**promote**
- On pass: update manifest.json and manifest.hash
- On fail: abort, do not update

**document** (mandatory)
1. Identify key decisions
2. Write `docs/adr/ADR-NNN-<slug>.md` for each
3. Flag: `[CHERRY-PICK CANDIDATE]`, `[BRANCH-ONLY]`, or `[LESSON — do not adopt]`
4. Commit findings alongside code

---

## Worktree Protocol

### When to use a worktree

Use a worktree when testing mutations or risky changes. Keep main clean.

### Creating a worktree

```bash
# For a feature test
git worktree add ../worktrees/test-feature main

# For an evolution generation
git worktree add ../worktrees/f_N main
```

### Promoting from worktree to main

```bash
cd ../worktrees/test-feature
# ... make changes, test, commit ...
git checkout main
git merge worktrees/test-feature --no-ff -m "feat: merge test-feature"
git worktree remove ../worktrees/test-feature
```

### Emergency rollback

If a promotion breaks the fabric:

```bash
# Revert manifest.hash to last known good
cp manifest.hash.bak manifest.hash
```

Ensure `manifest.hash.bak` exists before any promotion by adding a pre-promotion backup step to your workflow.

---

## Commit Cadence

- Commit after each successful unit test
- Commit messages should describe *what* changed and *why*
- Evolution commits follow: `feat(f_N): <description>`

---

## Evolution Labels

| Label | What mutates |
|-------|-------------|
| `discovery` | Discovery layer blob |
| `planning` | Planning layer blob |
| `judge` | Judge/feedback blob |
| `engine` | Execution engine blob |
