# AGENTS.MD

**Role:** D-JIT Fabric Architect & Optimization Agent

---

## Finding Current State

The system evolves through generations f_0 through f_N. State is discovered, not hardcoded.

```bash
# Current generation (most recent council/f_N worktree)
git worktree list | grep council/f_ | sort -V | tail -1

# Stable anchor (main branch manifest hash)
git show main:manifest.hash

# Vault contents
ls blob_vault/
```

Canonical docs:
- Genesis: `docs/genesis/f(undefined).md`, `docs/genesis/METAPHORS.md`
- Principles: `docs/INVARIANTS.md`, `lambda.md`
- Protocol: `docs/PROTOCOL.md`
- Security: `docs/SECURITY.md`
- Decisions: `docs/adr/`
- ZK protocol: `ZK_PROTOCOL.md`
- Process: `docs/PROCESS.md`

---

## Discovery Procedures

### How to find the active engine blob

```bash
python3 -c "import json; m=json.load(open('manifest.json')); print(m['blobs']['engine']['logic/python'][:16]+'...')"
```

### How to evolve a generation

```bash
python3 evolve.py --label discovery  # or planning, judge, engine
```

### How to promote safely

```bash
python3 promote.py  # runs triple-pass review first
```

---

## Golden Rules

1. **ABI contract:** Every engine must enforce `result` variable + `log()` sink.
2. **BIOS fallback:** `seed.py` boots via `_raw_get` only — no engine dependency in kernel.
3. **No bricking:** Never update `manifest.hash` until verified in a separate worktree.
4. **blake3 only:** The vault address IS the blake3 hash. No SHA-256, blake2s, or blake2b.

---

## Iteration Cycle

```
evaluate → mutate → review → benchmark → promote → document
```

### Document step (mandatory)

At cycle end, for each decision:
1. Write `docs/adr/ADR-NNN-<slug>.md`
2. Flag: `[CHERRY-PICK CANDIDATE]`, `[BRANCH-ONLY]`, or `[LESSON — do not adopt]`
3. Commit findings with the code

---

## Fitness Function

$$f(Link) = \frac{SuccessRate \times Integrity}{Latency \times ComputeCost}$$

Full treatment: `docs/INVARIANTS.md`

---

## ZK Protocol

Before touching proof code: read `ZK_PROTOCOL.md`.

- Hash primitive: blake3
- Proof artifacts: blobs (PUT to vault, reference by hash)
- Proofs belong at promotion time, not per-invocation

---

## Worktree Strategy

```bash
# Test a mutation in isolation
git worktree add ../worktrees/test-feature main
# ... work ...
git worktree remove ../worktrees/test-feature

# Commit after each successful unit test
git add -A && git commit -m "describe what changed"
```
