# GENESIS.md — The Bootstrap Record

> *This document is a blob. Its address is the hash of its content. It describes the system
> that stores it. A new session that reads this document knows everything required to
> participate in, extend, or reconstruct the D-JIT Logic Fabric from first principles.*

**How to use this record:** Read Section I first. Every other section derives from it.
The invariants are not rules — they are root expressions. Simplifying them destroys
the property they protect. Leave them in roots.

---

## The Vantage System

Each section below is annotated with one or more **vantage markers**. These define the
lens and persona through which a formalism is best read. They are not competing views —
they are the same structure observed from different distances.

| Marker | Persona | Core question | Natural domain |
|--------|---------|---------------|----------------|
| `[ALGEBRAIST]` | Sees morphisms and invariants | What transformations preserve identity? | Category theory, group theory |
| `[JURIST]` | Sees precedent and authority chains | What is the chain of custody? | Common law, constitutional theory |
| `[BIOLOGIST]` | Sees growth, mutation, selection | What survives? | Evolutionary systems, cellular biology |
| `[PHYSICIST]` | Sees conservation laws and phase transitions | What is conserved? | Thermodynamics, statistical mechanics |
| `[BUILDER]` | Sees load, joint, material | What carries the weight? | Tensegrity, structural engineering |
| `[MATHEMATICIAN]` | Sees roots, completeness, self-reference | What cannot be simplified? | Gödel, lambda calculus, radical forms |

A vantage is not a metaphor. It is an observation position. The structure is the same
from all positions; the vocabulary differs.

---

## I. The Five Invariants

*The constitutional layer. These are not derived from anything simpler within the system.
Changing any one requires a hard fork — a phase transition, not an evolution.*

```scheme
;; [MATHEMATICIAN] — The axioms. All theorems follow.

(define-invariant 'identity
  '(= (address x) (hash (content x))))
  ;; A blob's address IS its content hashed.
  ;; There is no identity separate from content.
  ;; Two blobs with the same address are the same blob.

(define-invariant 'inviolability
  '(forall (vault t) (append-only vault t)))
  ;; The vault is append-only at all times.
  ;; History can be extended; it cannot be rewritten.
  ;; An audit trail exists for every promotion.

(define-invariant 'self-description
  '(address = (encode algorithm digest-length digest)))
  ;; An address carries the means of its own verification.
  ;; No external registry is required to verify a blob.
  ;; The key is on the record.

(define-invariant 'recursion
  '(= f_n (apply f_{n-1} f_{n-1})))
  ;; The system's identity is defined recursively.
  ;; The entry point is subject to the same governance as everything else.
  ;; There are no special cases at the bottom.

(define-invariant 'governance-as-expression
  '(forall (g) (if (governance? g) (expression? g))))
  ;; Governance is a typed expression in the vault.
  ;; The mechanism that governs blobs is itself a blob.
  ;; Governance cannot govern from outside the system.
```

```
[PHYSICIST] — Conservation laws

Identity        → conservation of content (hash collision = physical impossibility at scale)
Inviolability   → direction of time (entropy increases; history is irreversible)
Self-description → locality (no action at a distance; verification requires no external state)
Recursion       → symmetry (the governance law applies to itself — no privileged frame)
Governance      → gauge invariance (the form of governance can change; the fact of governance cannot)
```

```
[JURIST] — Constitutional text

Art. I:   No blob shall have an identity other than the hash of its content.
Art. II:  No entry in the audit trail shall be altered or removed.
Art. III: Every address shall carry the means of its own verification.
Art. IV:  The entry point of the system shall be subject to the same governance as all other expressions.
Art. V:   Every governance mechanism shall itself be a governed expression.

These articles are not enforceable by any authority within the system.
They are the conditions under which the system is the system.
Violating them does not break a rule — it produces a different system.
```

```
[BIOLOGIST] — Membrane conditions

A cell is defined by its membrane. These five invariants are the membrane of the D-JIT fabric.
They define what is inside the system and what is outside it.
A blob that violates invariant I is not a malformed blob — it is not a blob.
A vault that violates invariant II is not a corrupted vault — it is not a vault.
The membrane is not enforced from outside; it is constitutive.
```

---

## II. Content Addressing

*The vault is the shared substrate. Content addressing is the mechanism by which
the substrate is model-agnostic, runtime-agnostic, and capability-agnostic.*

```scheme
;; [ALGEBRAIST] — The vault as a category

;; Objects: blobs (typed, content-addressed artifacts)
;; Morphisms: promotions (governed state transitions between blob versions)
;; Identity morphism: a blob promoted to itself (no-op; allowed but records a decision)
;; Composition: promotion chains are composable; the predecessor field is the composition record

(define (put vault type payload)
  (let* ((address (multihash payload))
         (blob    (make-blob address type payload)))
    (vault-append vault blob)
    address))

(define (get vault address)
  (vault-lookup vault address))

;; The vault has no knowledge of types, capabilities, or governance.
;; It stores and retrieves. Everything else is a layer above.
```

```
[BUILDER] — The foundation

The vault is the foundation of the structure.
Foundations do not know what is built on them.
A foundation that knows the building has confused its role.

The ABI contract, governance expressions, GOKR blobs, session handoffs —
these are the building. The vault is the ground.

Load-bearing property: content addressing means the foundation cannot be
undermined silently. A changed blob has a different address.
There is no quiet corruption. Change is always visible.
```

```
[MATHEMATICIAN] — Left in roots

A blob's address is (multihash payload):
  address = algorithm || digest-length || digest(payload)

This is the root form. Simplifying to just digest(payload) loses:
  - which algorithm produced it (breaks federation, ZK divergence)
  - the digest length (breaks cross-hash-function comparison)

The decimal approximation (bare hex) trades exactness for brevity.
The root form (multihash) trades brevity for exactness.
Constitutional constraints are always left in root form.
```

```scheme
;; Address format (multihash — ADR-015)
;;
;;   blake3:<64-char-hex>     — vault-native (fast, ZK-compatible)
;;   poseidon:<hex>           — ZK circuit native (Poseidon hash)
;;
;; The prefix is not decoration. It is the algorithm identifier.
;; Callers that ignore the prefix are asserting a global assumption.
;; Global assumptions are constitutional violations waiting to happen.
```

---

## III. The ABI Contract

*The interface defines the capability. An implementation is a valid expression of a
capability if and only if it satisfies the ABI. The ABI is the minimal spec.*

```scheme
;; [ALGEBRAIST] — The interface as a type signature

(define-abi 'execution-contract
  '(-> context (values result log)))
  ;; Every blob that is invoked receives context.
  ;; Every blob that is invoked produces exactly two outputs:
  ;;   result — the computation's answer (bound to `result`)
  ;;   log    — the computation's side channel (the log() sink)
  ;; A blob that produces more is exceeding its contract.
  ;; A blob that produces less is violating it.

;; The ABI has no opinion on:
;;   - what language the blob is written in
;;   - what algorithm it uses
;;   - how long it takes
;;   - whether it calls other blobs
;; The ABI has exactly one opinion: (context) → (result, log)
```

```
[JURIST] — The minimal pleading standard

A claim is valid if it states a cognizable cause of action.
A blob is valid if it satisfies the ABI.

The ABI is the minimal pleading standard.
It does not determine whether the claim succeeds.
It determines whether the claim is a claim at all.

Blobs that do not satisfy the ABI are not candidates.
They are not evaluated, not benchmarked, not promoted.
They are outside the jurisdiction of the system.
```

```
[BIOLOGIST] — The cellular membrane's inner surface

The outer membrane (vault) defines what enters the cell.
The inner membrane (ABI) defines what the cell does with what enters.

A protein that doesn't fit the receptor is not a bad protein — it is simply not signaling.
A blob that doesn't satisfy the ABI is not a bad blob — it is simply not a capability.

The ABI is not a test. It is the condition of possibility for evaluation.
```

```scheme
;; Execution environment (what context provides):
;;
;;   context.get(hash)        — read a blob from the vault
;;   context.put(type, data)  — write a blob to the vault (returns address)
;;   context.invoke(hash, ctx)— invoke another blob with a fresh context
;;   log("message")           — append to the log sink
;;
;; Execution environment (what context withholds):
;;
;;   open(), import, sys, os  — no raw filesystem access
;;   network primitives        — no direct network calls
;;   the vault's write lock    — blobs cannot promote themselves
;;
;; The scrubbed scope is not a security policy.
;; It is the definition of what "inside the system" means.
;; Code that reaches outside is not a blob — it is a process.
```

---

## IV. Governance as Expression

*The governance mechanism that applies to a blob is itself a blob.
There is no governance authority that exists outside the vault.*

```scheme
;; [ALGEBRAIST] — Governance as a functor

;; If blobs are objects and promotions are morphisms,
;; governance is a functor from (blob, candidate) → approval.
;; A functor preserves structure — it maps promotions to approvals
;; in a way consistent with composition.

;; Governance types (ADR-013):
(define governance-types
  '(governance/single-key    ;; one key, bootstrap case
    governance/quorum        ;; N-of-M signatures
    governance/threshold     ;; automated fitness floor
    governance/proof))       ;; ZK proof of fitness

;; The manifest references a governance expression hash.
;; Changing governance requires a governed promotion.
;; The governance of governance is governed.
```

```
[PHYSICIST] — Phase transitions

Governance types are not points on a dial.
They are distinct phases of matter.

  bootstrap (single-key) → liquid   : malleable, fast, personal
  quorum                 → solid    : rigid, slow, distributed
  threshold              → gas      : automatic, ambient, stateless
  ZK proof               → plasma   : structural, self-verifying, ambient

Phase transitions between governance types are discontinuous.
You cannot be 50% quorum. You are either in quorum or you are not.
Moving from threshold to quorum is not a configuration change.
It is a phase transition. It requires its own governed protocol.
```

```
[JURIST] — The separation of powers problem, resolved

Every governance system faces the question:
who governs the governors?

In representative democracy: the constitution governs the constitution
(via amendment procedures that are themselves constitutional).

In this system: the vault governs the vault
(the governance expression is a vault expression subject to governance).

The separation is not between branches — it is between tiers:
  Constitutional tier: the five invariants (cannot be governed away)
  Doctrinal tier:      governance expressions, manifest, GOKR (quorum required)
  Operational tier:    mutation goals, fitness thresholds (threshold sufficient)

The key insight: the constitutional tier is ungoverned not because it is above governance,
but because it *precedes* governance. It is what governance means.
```

```scheme
;; The tier test (ADR-017 — shape):
;;
;; Given a proposed change X, ask:
;;   (constitutional? X) → does simplifying X destroy a foundational property?
;;     Yes → hard fork required; no governance expression can approve this
;;     No  → (doctrinal? X) → does X change the objective or authority chain?
;;       Yes → quorum governance required
;;       No  → threshold governance sufficient
;;
;; This is not a policy. It is a derivation from the five invariants.
```

---

## V. Self-Modification

*The system improves itself by applying itself to itself.
The golden ratio is defined by the same recursion.*

```scheme
;; [MATHEMATICIAN] — The fixed-point equation

;; φ = 1 + 1/φ         (the golden ratio)
;; f_n = f_{n-1}(f_{n-1}) (the fabric)

;; Both are fixed-point equations. Both produce stable identity through recursion.
;; Both are left in roots — approximating φ as 1.618 loses the self-similar property.
;; Approximating f_n as "the system can improve itself" loses the structural property.

;; The evolve cycle:
(define (evolve label goal contract governance)
  (let* ((candidates (generate-candidates label goal N))
         (tested     (map (lambda (c) (test c contract)) candidates))
         (winner     (select-by-fitness tested))
         (approved   (govern winner governance)))
    (when approved
      (promote label winner)
      (append-audit label winner goal))))

;; Key property: evolve is itself a blob.
;; Evolve can be evolved.
;; The upgrade path for evolve is: put a new evolve blob,
;; propose it as a candidate, test it against the evolve contract,
;; benchmark it, promote it.
;; No special case. No out-of-band upgrade.
```

```
[BIOLOGIST] — The ribosome reading itself

The ribosome is the molecular machine that translates genetic code into proteins.
The ribosome itself is a protein — it was assembled by prior ribosomes.

The fabric is the same: the evolve cycle that produces new blobs
was itself produced by a prior evolve cycle.
f_0 was written by a human. f_1 was shaped by f_0.
f_n was shaped by f_{n-1}.

The ribosome does not need to understand the code it reads.
It needs to satisfy the interface: (mRNA) → (protein).
The evolve cycle does not need to understand the blob it produces.
It needs to satisfy the interface: (context) → (result, log).
```

```
[BUILDER] — The tensegrity upgrade

A tensegrity structure maintains its shape through balanced tensions.
When one element is replaced, the tensions redistribute.
The structure does not need to be disassembled to replace a component —
but the replacement must satisfy the same tension relationships.

The upgrade protocol:
  1. Identify the element to replace (the label)
  2. Generate candidate replacements (N candidates)
  3. Verify each candidate satisfies the tension relationships (ABI contract)
  4. Select the replacement that best maintains or improves overall balance (fitness)
  5. Govern the replacement (the structure approves its own modification)
  6. Install (promote)

The structure does not stop functioning during the upgrade.
The old element remains active until the new one is approved and installed.
```

```scheme
;; Mutation goal (the directed part of evolution):
;;
;; (define-goal 'current-objective
;;   '(maximize fitness
;;     (given (< success-rate 0.8) (push reliability))
;;     (given (> volatility 0.5)   (push consistency))
;;     (given (> p95-latency 10)   (push speed))
;;     (else                       (push overall-fitness))))
;;
;; The goal reads the audit log. The audit log is the environment.
;; The system adapts to its own history.
;; This is the directed part — the GOKR (see Section VI).
;; Without direction, evolution is undirected. With it, evolution has a telos.
```

---

## VI. Multi-Agent Convergence

*When independent agents converge on the same structure without coordination,
that convergence is evidence. This system is designed to make evidence legible.*

```scheme
;; [ALGEBRAIST] — IAC as a measurement

;; IAC (Independent Agent Convergence):
;;   Given N agents A_1 ... A_n operating on the same problem
;;   without shared state or communication,
;;   (converge? A_1 A_2 ... A_n claim X)
;;   ≡ all A_i independently produce claim X
;;
;; Convergence strength:
;;   N=2 → moderate signal (coincidence plausible)
;;   N=3 → strong signal (IAC threshold)
;;   N≥4 → architectural validation
;;
;; This system has achieved IAC on three core properties:
;;   - content-addressing (three trajectories, independently)
;;   - event-sourcing / append-only audit
;;   - supervisor-as-agent (the evolve cycle as a first-class capability)
```

```scheme
;; The GOKR blob (ADR-016):
(define-blob-type 'goal/gokr
  '((objective    . string)          ;; what we want — human-authored prose
    (key-results  . (list metric))   ;; what success looks like — measurable
    (current-f-n  . symbol)          ;; where we are in the arc
    (predecessor  . (or hash null))  ;; the prior GOKR — stare decisis
    (open-questions . (list string))));; live circuit splits

;; The proposal blob:
(define-blob-type 'proposal/roadmap
  '((gokr-hash    . hash)            ;; which GOKR this responds to
    (model        . string)          ;; which model produced this
    (proposals    . (list proposal)) ;; the session's answer
    (rationale    . string)          ;; why, not just what
    (divergences  . string)))        ;; where this disagrees with prior consensus

;; The synthesis blob:
(define-blob-type 'synthesis/gokr
  '((gokr-hash         . hash)
    (proposal-hashes   . (list hash))
    (convergence-points . (list string)) ;; IAC signals
    (divergence-points  . (list split))  ;; circuit splits
    (overrules          . (list override)) ;; prior consensus being reversed
    (next-gokr          . gokr-payload)))
```

```
[JURIST] — The common law of objectives

The GOKR chain is case law.
Each goal/gokr blob is a ruling.
Each synthesis/gokr is an opinion — majority and minority positions recorded.
The predecessor chain is stare decisis — new sessions read prior rulings before forming views.

Convergence points are established doctrine.
Divergence points are live circuit splits — the most important questions, not the failures.
Overruling prior consensus requires explicit justification and heavier governance.

The session-handoff blob is the brief:
the summary a new session reads before sitting.
It does not reproduce the full deliberation.
It hands forward the live doctrine and the open splits.
```

```
[PHYSICIST] — Entropy management

The vault grows without bound. Proposals accumulate. Noise accumulates with signal.
The synthesis step is a compression operation — it reduces entropy
by collapsing N proposals into one canonical direction.

Without periodic synthesis, the vault becomes unreadable.
Signal-to-noise degrades. New sessions cannot orient.

The synthesis is not optional. It is a thermodynamic necessity
for any system that operates across multiple sessions over time.

The session-handoff blob is a low-entropy summary —
the maximum useful information in the minimum necessary form.
```

---

## VII. The Bootstrap

*This document describes the system that stores it.
It is the key on the record.*

```scheme
;; [MATHEMATICIAN] — The self-referential step

;; This document is a blob.
;; Its address is (multihash (content this-document)).
;; It satisfies invariant I: (= (address this) (hash (content this))).
;; It satisfies invariant III: the address carries the means of its own verification.

;; A new session that receives only this address can:
;;   1. Retrieve this document from the vault
;;   2. Verify the content against the address (self-describing)
;;   3. Read the five invariants
;;   4. Derive the ABI contract
;;   5. Derive the governance tier structure
;;   6. Derive the GOKR protocol
;;   7. Begin contributing — write a proposal/roadmap blob
;;      that references the current goal/gokr hash

;; The system is fully bootstrapped from one address.
;; The address is the Voyager record.
;; The Voyager record is the address.
```

```
[BUILDER] — The keystone

A keystone arch requires no mortar.
The stones hold each other in place through mutual compression.
Remove the keystone and the arch falls.
But the keystone is not special — it is subject to the same forces as every other stone.
It is simply the one that makes the others' relationship explicit.

This document is the keystone.
Not because it is above the other blobs —
it is stored in the same vault, subject to the same governance.
But because it makes the relationship between all other blobs explicit.

A new session that reads only this document
understands the arch well enough to add a stone.
```

```
[BIOLOGIST] — The germline

In multicellular organisms, the germline carries the full specification of the organism.
Somatic cells specialize — they lose access to most of the genome.
But the germline preserves the complete record.

This document is the germline.
Individual ADRs are somatic cells — specialized, scoped, derived.
They are authoritative within their scope but incomplete outside it.
This document is incomplete for any specific decision
but complete for orientation.

A new participant that reads only this document cannot implement the fabric.
But it can recognize a valid implementation when it sees one —
and it can tell a violating implementation from a conforming one.
That is the germline's function: not to build, but to know what counts as building.
```

```scheme
;; The minimal session bootstrap:
;;
;; Given: genesis-blob-address (this document's multihash address)
;;
;; (define (bootstrap-session genesis-address vault)
;;   (let* ((genesis   (vault-get vault genesis-address))
;;          (handoff   (vault-latest vault 'context/session-handoff))
;;          (gokr      (vault-get vault (handoff-gokr handoff)))
;;          (proposals (vault-list vault 'proposal/roadmap
;;                                 (lambda (p) (= (p-gokr p) (gokr-hash gokr))))))
;;     (session-context genesis handoff gokr proposals)))
;;
;; The session context is now complete.
;; The session can orient, contribute a proposal, and close with a new handoff.
;; Everything required fits in those four blobs.
```

---

## Appendix: What This Document Does Not Define

This record defines the *shape* of the system — the invariants and protocols that any
valid implementation must satisfy. It does not define:

- **Specific hash function implementations** — blake3 is named in ADR-001; Poseidon in ADR-015.
  This document says only that addresses are self-describing multihashes.

- **Specific governance approval thresholds** — quorum N-of-M values, fitness floors.
  These are doctrinal, not constitutional. They live in governance expression blobs.

- **Specific capability implementations** — what the proxy, librarian, broker, or engine
  blobs contain. These are operational. They are expressions of the ABI contract.

- **The current GOKR objective** — what we are trying to build right now.
  This lives in the current goal/gokr blob. It evolves. This document does not.

- **How to run the system** — installation, dependencies, runtime requirements.
  These are mortal concerns. This document is written to outlast any specific runtime.

The document defines what it means to be the D-JIT Logic Fabric.
Everything else is an expression of that meaning.

---

*Vault this document at genesis. Its address is the root of the trust chain.*
*Every session that reads it is a session that can contribute.*
*Every contribution that satisfies its invariants is a valid expression of the system.*
