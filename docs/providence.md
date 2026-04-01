# Synapse: Provenance & Providence Model

This document defines the **provenance model** (origin and chain of custody) used in Synapse's agentic development, and the **providence tree** (the tree of agent decisions that shape the lineage). It also documents key terms and tagging/branching conventions.

---

## Key Terms

**Provenance (noun)**  
The origin and chain of custody of a piece of logic. In Synapse, every blob, branch, and tag is traceable to its origin commit(s). The git history *is* the provenance record.

**Providence tree**  
The tree of derivations across branches and agents. A "providence tree" node is a commit (or tag) at which an agent made a decision that branched or collapsed potential into a new form. The tree is visible in git history and branch/tag topology.

**Collapse**  
The moment when potential (an `undefined` or experimental state) becomes a stable, named form. Collapses are marked with tags. The term comes from quantum mechanics: a wavefunction of possibilities resolves to one measured state.

**Self-modification cycle**  
When a version of the fabric (`f_n`) is used to produce a better version of itself (`f_{n+1} = f_n(f_n)`). Each council release after `v1.0.0` is one such cycle.

**Blob**  
A content-addressed unit of logic (stored by SHA-256 hash). Implementation detail — see branch docs.

**Council**  
A governance layer that approves changes before they are promoted. Defined in `COUNCIL.md` on the council lineage branches.

**Agentic development**  
Development performed by AI agents (in this repo, Claude Sonnet 4.6 and Brian Lloyd-Newberry as human principal). The agents' identities are visible in commit author/co-author metadata.

---

## The Provenance Tree

Synapse's git history encodes the full provenance tree:

```
[tag: unknown]  2d22e7f  — root of everything
      ↓
[tag: undefined]  f65f4a7  — shared base, both lineages diverge from here
      ↓                        ↓
Non-council lineage        Council lineage
(solo agent)               (governed, multi-agent)
f_* tags                   v1.* annotated tags
```

This structure means:
- Every experiment traces back to `unknown` and `undefined`.
- The two lineages are parallel; neither feeds the other (no cross-merges yet).
- `main` holds stable docs and pointers only — no experiment code lives here.
- When the experiments are ready to converge, the merges will be deliberate and documented.

---

## Tagging Conventions

### Non-council lineage — lightweight tags

Lightweight tags point directly at a commit SHA (no tag object, no message).

| Tag | Purpose |
| :--- | :--- |
| `unknown` | Repo genesis (concept before form) |
| `undefined` | Seed potential (before first implementation) |
| `f_0` | First stable collapse of the non-council experiment |
| `f_1` | Second iteration |
| `f_2` | Third iteration |

**When to cut a lightweight tag:** at the moment of a named collapse — when a phase sequence reaches its intended stable form and the commit message declares the collapse (e.g., "The Wavefunction Collapse: f(undefined) → f_0").

**Tag message:** none (lightweight). The commit message on the tagged commit carries the narrative.

### Council lineage — annotated tags

Annotated tags are tag objects: they have a tagger identity, a timestamp, and a message. This is intentional — council releases are signed-off milestones with an explicit record.

```bash
git tag -a v1.x.0 -m "f_n: <short summary>"
```

**Format of annotated tag message:**

```
f_n: <short human-readable summary>

[optional: identity line — f_n = f_(n-1)(f_(n-1))]
[optional: co-authorship note]
```

**When to cut an annotated tag:** after a council-approved promotion cycle completes and the manifest is updated to the new version.

#### Examples

```
v1.0.0  "f_0 defined: self-hosting + closed feedback loop"
v1.1.0  "f_1: first self-modification cycle complete"
v1.2.0  "f_2 = f_1(f_1): p95 + integrity signals end-to-end"
v1.3.0  "f_3 = f_2(f_2): persistent bytecode cache; dynamic tolerance"
v1.4.0  "f_4 = f_3(f_3): governed feedback loop"
```

---

## Branch Naming Conventions

| Pattern | Lineage | Meaning |
| :--- | :--- | :--- |
| `f_<n>` | Non-council | The nth iteration of the non-council experiment |
| `council/f_<n>` | Council | The nth iteration of the council experiment |
| `main` | — | Stable docs and pointers only |

> **Important:** `council/f_0` is a **branch name** — the `/` is part of the name, not a directory separator. Git allows `/` in branch names; GitHub renders them as a path-like hierarchy, but they are flat refs.

### Branch lifecycle

1. A new branch (`f_n` or `council/f_n`) diverges from the previous stable collapse.
2. Experimental work proceeds on the branch.
3. When stable, the branch head is tagged (lightweight or annotated, per lineage convention).
4. The next branch (`f_{n+1}`) diverges from the tagged commit.
5. **No merges back to `main` until explicitly ready** — `main` is deliberately kept clean.

---

## Self-Modification Identity

For the council lineage, each cycle produces a new version of the fabric using the previous version:

```
f_1 = f_0(f_0)   — f_0 rewrites itself, producing f_1
f_2 = f_1(f_1)   — f_1 rewrites itself, producing f_2
f_3 = f_2(f_2)
f_4 = f_3(f_3)
...
f_n = f_{n-1}(f_{n-1})
```

This identity is tracked in the annotated tag message (when present) and in the commit message of the council branch head.

---

## Agentic Development

Development in this repository is **agentic**: AI agents and human principals collaborate to evolve the fabric. Agent identity is visible in:

- Commit `author` and `committer` fields
- `Co-Authored-By:` trailers in commit messages (e.g., `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`)
- Annotated tag `tagger` fields

The provenance tree preserves a full audit trail of which agent made which decision at which point in the lineage.

---

## No Merges to `main` (Current Status)

As of the current state of the repo, **no experiment branch has been merged back to `main`**. This is intentional:

- The experiments are still evolving.
- Convergence requires deliberate review, not an automatic merge.
- `main` serves as the stable, always-readable entry point to the project.

When a lineage is ready to converge, the merge will be accompanied by a clear commit message documenting the convergence decision and which version is being promoted.

---

*See also: [experiments.md](experiments.md) for the detailed lineage histories and tag notes.*
