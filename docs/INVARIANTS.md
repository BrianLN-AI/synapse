# INVARIANTS.md — Six-Vantage Treatment of the Five Constitutional Invariants

> Companion document to λ.md. Read Section I and Section II of λ.md before this document.
> The primitives (I.1–I.9) are not repeated here. They are the ground this document stands on.

---

## Purpose

The five constitutional invariants of the D-JIT Logic Fabric are stated once, formally,
in λ.md Section II. They are compact by design — left in roots, like √2 left as √2.

This document examines each invariant from six observation positions: ALGEBRAIST, JURIST,
BIOLOGIST, PHYSICIST, BUILDER, MATHEMATICIAN. These are not competing interpretations.
They are six instruments playing the same note. A reader who understands all six
vantages has triangulated the invariant from enough angles that misunderstanding becomes
structurally difficult.

The vantages were chosen because they collectively cover the full space of what an
invariant can mean:

- What structure it preserves (ALGEBRAIST)
- What authority it confers and constrains (JURIST)
- What boundary it defines (BIOLOGIST)
- What quantity it conserves (PHYSICIST)
- What load it carries (BUILDER)
- What axiom it is — what cannot be removed without losing the system (MATHEMATICIAN)

Any document, design decision, or proposed change that satisfies all six readings of all
five invariants is a valid expression of the D-JIT fabric. Any that violates any one
reading of any one invariant is not.

---

## Alignment Protocol

Before reading: these vantages are aligned. Alignment means every vantage reaches
the same conclusion about each invariant — stated in its own vocabulary. The test
for alignment is given at the end of this document. If a vantage appears to say
something different from the others, re-read. The vocabulary differs; the claim does not.

---

## Invariant I: Identity

```scheme
(define-invariant 'I:identity
  '(= (address x)
      (multihash (content x))))
```

```
[ALGEBRAIST]

An identity morphism in a category sends each object to itself.
Here, identity is stronger: the address IS the content, transformed by a
deterministic hash function that names itself. No two distinct objects can share
an identity, because distinct content produces distinct multihash (collision
resistance). No object can change identity without changing content — the
function is deterministic. This is not conventional identity (an arbitrary label
assigned by a registry) but canonical identity: derived, not assigned. The
category of blobs has no isomorphisms that are not identities. Two blobs at the
same address are not isomorphic — they are equal.
```

```
[JURIST]

Article I establishes that no blob shall possess an identity other than the hash
of its own content. Identity cannot be granted by authority, assigned by registry,
or transferred by governance action. It derives solely from the content itself.
This eliminates an entire class of identity fraud: a blob cannot be substituted
for another at the same address without changing the address. There is no
deed-of-title for blobs — the content IS the title. Chain of custody begins at
creation and is self-proving: present the blob, compute the multihash, compare
to the address. No court, no notary, no witness required. Identity is not a
social fact. It is a computational fact.
```

```
[BIOLOGIST]

Genetic identity in living organisms is determined by sequence — the order of
base pairs in DNA. No external authority names a genome. The sequence IS the
identity. Invariant I encodes the same principle for blobs: the payload sequence
is the identity, mediated by a hash function that serves as the organism's
fingerprint. An organism that alters its genome mid-life becomes, in this model,
a different organism. This is not death — the prior form persists in the vault
(Invariant II). But it is speciation: a different address, a different entity.
Identity is conserved from inside, not conferred from outside. The membrane that
separates one blob from another is its content.
```

```
[PHYSICIST]

Conservation of information. If a blob's content changes, its address changes.
There is no process by which information can be altered without creating a
detectable signature. This is the computational analogue of the conservation of
mass-energy: matter cannot appear or disappear; it can only transform, and every
transformation leaves a measurable trace. Quiet corruption — where content changes
but the identifier does not — is physically forbidden by this invariant. The hash
function is the measuring instrument. It cannot be fooled by a change that
"doesn't matter." Every bit of content participates in the address. Identity is
a conserved quantity.
```

```
[BUILDER]

A joint in structural engineering is a connection point. Its load-bearing capacity
depends on the material continuity at the connection. If you can swap the material
at a joint without changing the joint's designation, the structure's integrity is
undefined — you cannot know what is carrying the load. Invariant I ensures that
every joint (address) is inseparable from the material it connects (content).
You cannot substitute a weaker material at the same address. The address IS the
material specification. A builder who needs to replace a component must produce
a new joint — a new address — and update every connection that referenced the old
one. There is no silent substitution. The load path is always auditable.
```

```
[MATHEMATICIAN]

In set theory, identity is the finest equivalence relation: x = x, and nothing
else equals x unless it IS x. Invariant I encodes this as a computable predicate:
(= (address x) (multihash (content x))). The multihash function is a witness to
identity — it maps the set of all possible byte sequences injectively (with
overwhelming probability) into the set of addresses. This is Cantor's insight
that a bijection between two sets proves they have the same cardinality, made
operational: if two blobs share an address, they share content. The invariant
cannot be simplified to "addresses are unique" without losing the constructive
property — that any party can verify identity without shared state. The root
form must be preserved.
```

---

## Invariant II: Inviolability

```scheme
(define-invariant 'II:inviolability
  '(forall (t) (append-only (vault t))))
```

```
[ALGEBRAIST]

A monoid is a set with an associative binary operation and an identity element.
Append-only storage is a free monoid: the elements are blobs, the operation is
append, the identity is the empty vault. Crucially, a free monoid has no inverse
operation — you cannot "un-append." This is not a restriction imposed on the
monoid; it is the defining property of the free construction. Invariant II states
that the vault IS this free monoid, for all time t. Morphisms in this category
are vault extensions — new blobs appended. There are no morphisms that remove or
alter. The category is directed: time flows in one direction only, and that
direction is the direction of appending.
```

```
[JURIST]

The common law principle of res judicata holds that a matter once adjudicated
cannot be relitigated. Invariant II extends this principle to every artifact in
the vault: once a blob enters the record, it cannot be altered, removed, or
expunged. This is not merely a procedural rule — it is the constitutional
foundation of the audit trail. Without it, no chain of custody is provable,
because any link in the chain could have been quietly altered. The vault is
the official record. The official record is immutable. A governance mechanism
that requires altering the record to exercise authority is not a governance
mechanism — it is a violation of the constitution. Supersession (promoting a
new version) is the legitimate remedy. The old version persists; the new version
is canonical; both are in the record.
```

```
[BIOLOGIST]

Evolution proceeds by accumulation, not erasure. Mutations are retained in the
population — some are selected against and become rare, but the sequence change
persists in the historical record encoded in phylogenetics. Invariant II encodes
the same principle: the vault is the phylogenetic record of the fabric. No branch
of the evolutionary tree is pruned retroactively. A blob that is superseded is
not deleted — it is an ancestor. Its lineage can be traced. Its fitness can be
re-evaluated in light of later developments. The append-only property is what
makes evolutionary history legible. A vault that could delete blobs would be a
vault that could rewrite the evolutionary record — and thereby destroy the
evidence base for all future selection decisions.
```

```
[PHYSICIST]

The second law of thermodynamics states that entropy in a closed system does not
decrease. Time has a direction: the direction of increasing entropy. Invariant II
is the structural encoding of this arrow of time in the fabric. The vault's state
monotonically increases — blobs are added, never removed. This is not entropy in
the thermodynamic sense (information is added, not randomized), but the directional
property is identical: there is a past, there is a future, and the boundary between
them is irreversible. A vault that could delete blobs could rewrite the past —
and a system that can rewrite the past has no stable present. The append-only
constraint is what gives "now" its meaning: the current canonical blob is the
most recently promoted, and that promotion is permanent.
```

```
[BUILDER]

In construction, the foundation is poured first and cannot be removed later
without demolishing what was built on it. Invariant II is this property made
universal: every blob that enters the vault is a foundation element. Capabilities
built on top of a blob depend on that blob's continued existence. If blobs could
be removed, any capability referencing a deleted blob would fail silently —
a foundation element removed from beneath a load-bearing column. The append-only
constraint is the structural guarantee that no such silent failure can occur.
A builder who needs to replace a capability does not remove the old foundation —
they promote a new one and update the references. The old foundation remains.
The building does not collapse during the transition.
```

```
[MATHEMATICIAN]

Peano's axioms for the natural numbers include a successor function but no
predecessor function for zero — there is no natural number before zero. The
naturals are well-founded: every decreasing chain terminates. Invariant II
encodes a dual property: the vault is well-founded in the forward direction.
Every increasing chain of vault states is consistent — you can always add
another blob, and you can never remove one. This is the constructive reading of
"append-only": the vault is a constructive proof of its own history. Each state
is a theorem derived from the axioms (the blobs) that precede it. Deletion would
be equivalent to withdrawing an axiom after theorems have been derived from it —
which invalidates all downstream proofs. The append-only constraint is what keeps
the proof system sound.
```

---

## Invariant III: Self-Description

```scheme
(define-invariant 'III:self-description
  '(= address (encode algorithm digest-length digest)))
```

```
[ALGEBRAIST]

A self-describing encoding is a fixed-point of a certain parsing morphism: when
you apply the parser to the address, you recover exactly the information needed
to re-apply the hash function and verify the address. This is not a mere
convenience — it is the algebraic condition for context-independence. An address
that omits the algorithm name requires ambient context (a globally shared
assumption about which hash function is in use). Ambient context is a hidden
dependency: a morphism that requires it is not a morphism between the stated
objects but between the stated objects plus the ambient state. Invariant III
eliminates hidden dependencies. The address is a closed term — fully specified,
no free variables.
```

```
[JURIST]

A deed of title, to be valid, must carry on its face the means of its own
verification: the property description, the chain of title, the governing
jurisdiction. A deed that says "see the external registry for the property
description" is not a self-contained instrument — it depends on the registry
remaining accurate and accessible. Invariant III is the constitutional requirement
that every address be a self-contained instrument. The algorithm and digest length
are the "governing jurisdiction": they tell any verifier, without consulting any
external source, which law (hash function) governs this address and how to apply
it. A system that assumes a single global hash function has an implicit external
registry. When that assumption breaks — during a cryptographic migration, during
federation with a system using a different function — addresses cease to be
self-contained instruments. Invariant III prevents this failure class permanently.
```

```
[BIOLOGIST]

A self-replicating molecule carries its own replication instructions. DNA encodes
not just the organism's proteins but the polymerase machinery that reads DNA.
The replication system is encoded in what it replicates. Invariant III encodes
this property for addresses: the address carries the instructions for its own
verification (the algorithm name and digest length). An address is therefore
self-replicating in the verification sense — any agent with the address can
reconstruct the verification procedure without external signaling. This is the
property that makes the fabric open to new agents: a new session that has never
seen the system before can receive an address, parse it, and know exactly how
to verify it. No handshake, no shared secret, no prior relationship required.
The address is the signal and the decoding key simultaneously.
```

```
[PHYSICIST]

Locality is the principle that physical processes depend only on conditions in
their immediate vicinity — not on conditions at a distance. Action at a distance
(requiring knowledge of a remote state to understand a local phenomenon) is the
hallmark of a theory that is missing something. Invariant III is the locality
principle for addresses: verification of an address requires only the address
and the blob's content — nothing remote, nothing ambient, nothing assumed. An
address that omits the algorithm name requires the verifier to know the "global
standard" — a form of action at a distance, where the correctness of the
verification depends on a state that is not present at the verification site.
Invariant III eliminates this. The verification field is closed. The address is
a local observable.
```

```
[BUILDER]

A structural specification that references an external standard is dependent on
that standard's continued validity. If the external standard is revised,
deprecated, or becomes inaccessible, every structure built to that standard is
now under-specified — the verification procedure has been lost. Invariant III
requires that every address carry its own specification. The algorithm name is
the material specification; the digest length is the dimensional tolerance. A
builder can verify any blob from any era without consulting any external document.
This is the load-bearing property: the address is load-bearing in the chain of
trust, and a load-bearing element must be fully specified in itself. External
dependencies in load-bearing elements are structural defects.
```

```
[MATHEMATICIAN]

Gödel numbering encodes logical formulas as natural numbers, making
self-reference possible: a formula can talk about its own Gödel number.
Invariant III is a simpler but structurally analogous move: the address encodes
the procedure for verifying itself. The encode function maps (algorithm,
digest-length, digest) to a string that contains all three components. This
is a total function — defined for all valid inputs, producing no free variables.
The address is therefore a closed expression in the formal sense: it has no
free variables that require binding from context. A system in which addresses
are closed expressions is a system that can be verified by any reader, in any
context, at any time. Openness of expression is the mathematician's name for
the kind of incompleteness that Invariant III prevents.
```

---

## Invariant IV: Recursion

```scheme
(define-invariant 'IV:recursion
  '(= f_n (apply f_{n-1} f_{n-1})))
```

```
[ALGEBRAIST]

A fixed point of a function f is a value x such that f(x) = x. The fabric's
evolution operator is defined by the equation f_n = f_{n-1}(f_{n-1}): each
generation is produced by applying the prior generation to itself. This is the
Y combinator structure — the fixed-point combinator of the lambda calculus. The
key algebraic property: the evolution operator is not privileged. It is a
morphism in the same category as all other blobs. It has the same type signature
(ABI contract), the same address structure (Invariant I), the same vault
residency (Invariant II). There is no special case at the bottom. The system
that improves the system is subject to the same improvement process. This is
self-similarity: the structure looks the same at every scale of the evolutionary
hierarchy.
```

```
[JURIST]

The constitutional principle of rule of law requires that no entity — including
the state itself — be exempt from the law. A constitution that carves out
exceptions for its own drafters, or for the mechanism of constitutional amendment,
has created a privileged class above the law. Invariant IV is the constitutional
prohibition on such carve-outs. The session-init blob — the entry point of the
system — is subject to the same governance as every other blob. The evolve blob
— the mechanism by which the system improves itself — is subject to governance
by the system it improves. There is no out-of-band upgrade path. There is no
administrative exception. The law that governs capability blobs is the same law
that governs the governance mechanism. The amendment process is itself
amendable — but only through the same amendment process.
```

```
[BIOLOGIST]

Organisms reproduce by copying their genome into offspring, which then reproduce.
The reproductive machinery is itself encoded in the genome it reproduces. There
is no external reproducer — the reproducer is a product of what it reproduces.
Invariant IV encodes this property: f_{n-1} produces f_n by applying itself to
itself. The fabric's "reproductive organ" (the evolve cycle) is a blob in the
fabric it evolves. It is subject to selection, mutation, and promotion by the
very process it embodies. This is autopoiesis: the system produces itself, and
the production mechanism is a component of what is produced. No component of the
system is exempt from the system's own evolutionary pressure. The germline and
the soma are in the same body.
```

```
[PHYSICIST]

Symmetry under self-transformation is a deep physical principle: the laws of
physics are the same whether you observe them directly or through a measuring
instrument that is itself subject to those laws. A physics that required special
instruments exempt from physical law would be incoherent — the measuring device
would be a privileged reference frame. Invariant IV is the prohibition on
privileged reference frames in the fabric. The evolve mechanism is not exempt
from the laws that govern what it evolves. There is no privileged frame. Every
element of the system, including the element that transforms other elements, is
subject to the same transformation laws. This is gauge symmetry: the form of
the evolution operator can change (f_n can be a better or worse evolve
implementation), but the fact that it is subject to the same governance as
everything else cannot change.
```

```
[BUILDER]

A scaffold is a temporary structure used to build a permanent one. In most
construction, the scaffold is taken down when the building is complete — it was
outside the structure, not part of it. Invariant IV eliminates the scaffold as
a concept. Every component of the build process is itself a component of the
built structure. The crane that lifts beams is a beam. The governance mechanism
that approves new blobs is itself a governed blob. This has a practical
consequence: there is no upgrade path that bypasses the structure. To improve
the crane, you use the crane. The structure carries its own construction
machinery. This is not circular — it is tensegrity: each component holds the
others, including the components that are being replaced. The structure does not
stop functioning while a component is upgraded, because the upgrade process
is a component of the structure.
```

```
[MATHEMATICIAN]

The Y combinator in lambda calculus enables recursion without named functions:
Y = λf.(λx.f(x x))(λx.f(x x)). Applying Y to a function f yields a fixed point:
Y(f) = f(Y(f)). Invariant IV is this structure, instantiated in the fabric:
f_n = f_{n-1}(f_{n-1}). The base case f_0 was written by a human (the first
bootstrap). Every subsequent f_n is derived by applying the prior term to itself.
This is a well-founded recursion: f_0 is given, and each step is a determined
function of its predecessor. The recursion cannot be simplified to "the system
improves itself" without losing the fixed-point structure — the property that
guarantees that the improvement process is itself improvable by the same process.
Left in roots: f_n = f_{n-1}(f_{n-1}). Simplified: "self-improvement." The
simplified form loses the constructive witness.
```

---

## Invariant V: Governance

```scheme
(define-invariant 'V:governance
  '(forall (g) (if (governs? g x) (expression? g vault))))
```

```
[ALGEBRAIST]

Governance is a functor: it maps (candidate-blob, manifest) to an approval
decision while preserving the promotion structure. Invariant V constrains where
governance functors can live: every governance functor must itself be an object
in the same category it maps over — a blob in the vault. This is the
internalization condition. A functor that lives outside the category it maps is
not a functor over that category — it is an external oracle. External oracles
are not composable: they cannot be governed, cannot be audited, cannot be
promoted. Invariant V collapses governance from an oracle into an internal
morphism. The governance of governance is itself governed (since the governance
mechanism is a blob, and blobs are governed by Invariant V applied recursively).
This is the algebraic closure of the governance structure.
```

```
[JURIST]

Constitutional law requires that every exercise of governmental power have a
legal basis — an authorization traceable to the constitution itself. An executive
action without statutory authorization, a statute without constitutional
authorization — these are ultra vires: beyond the powers granted. Invariant V
extends this requirement into the system: every governance mechanism must have
a vault address. "Governance" that exists outside the vault — in an operator's
private key held without a corresponding blob, in an undocumented emergency
procedure, in an implicit authority assumed but never expressed — is ultra vires.
It cannot be audited, cannot be reviewed, cannot be revoked through the system's
own mechanisms. Invariant V is the prohibition on ultra vires governance. The
chain of authority terminates in the vault, or it is not authority — it is
arbitrary power.
```

```
[BIOLOGIST]

In multicellular organisms, the immune system distinguishes self from non-self.
A governance mechanism that operates from outside the vault is non-self — the
system cannot recognize it, cannot audit it, cannot respond to it through its
own regulatory pathways. Invariant V defines the membrane for governance: a
governance mechanism is inside the system if and only if it is an expression in
the vault. Everything outside that membrane is foreign. This is not a value
judgment — it is a membrane property. A foreign governance mechanism may produce
valid decisions, but those decisions cannot be verified by the system's own
immune response (the audit trail). Invariant V ensures that governance is
endogenous: it arises from within the system, is expressed within the system,
and can be regulated by the system's own evolutionary pressure.
```

```
[PHYSICIST]

Gauge invariance in physics requires that the laws of physics take the same form
under local symmetry transformations — the transformation being the gauge. The
gauge is not a physical observable; it is a choice of representation. But the
constraint (gauge invariance) is physical and non-negotiable. Invariant V is the
gauge invariance of governance: the form of governance (single-key, quorum,
threshold, ZK proof) can change — these are gauge choices. What cannot change is
the constraint that governance is an expression in the vault. This is the
non-negotiable physical law underneath the gauge choice. A system where governance
can operate outside the vault has broken gauge invariance: it has a privileged
frame (the external governance authority) that is exempt from the symmetry
requirement. Invariant V is the prohibition on this privileged frame.
```

```
[BUILDER]

In a load-bearing structure, every load path must be traceable from point of
application to foundation. A load that disappears into an unspecified "somewhere"
is a structural mystery — and structural mysteries become structural failures.
Invariant V requires that every governance load path terminate in the vault.
An approval decision whose authority derives from a key stored nowhere in the
vault, from a policy documented nowhere in the vault, from a human agreement
existing nowhere in the vault — this is a load that disappears. The structure
cannot be inspected, cannot be certified, cannot be safely extended. Every
load-bearing governance element must be in the vault, where it can be read,
audited, and, if necessary, replaced through a governed promotion. The vault
is the structural inspection record. Governance that is not in the vault
cannot be inspected.
```

```
[MATHEMATICIAN]

Gödel's second incompleteness theorem states that a sufficiently powerful formal
system cannot prove its own consistency from within itself — unless it is
inconsistent. Invariant V is not a claim of self-consistency (that would be
unachievable). It is instead a closure condition: governance is defined only
over expressions in the vault, and governance mechanisms are themselves expressions
in the vault, so the governance relation is well-defined on its own domain. This
is the mathematical condition for the governance system to be a legitimate formal
object: it must not refer to entities outside its domain of definition. A governance
mechanism that refers to external authority introduces an undefined term — a free
variable in the governance predicate. Invariant V requires that governance be a
closed expression: all terms bound, no free variables, no external references.
The governance predicate is total over its domain.
```

---

## Reading Alignment

The six vantages are aligned when they all answer "yes" to the same question about each
invariant. Use these questions as your verification test.

### Test for each invariant

For **Invariant I** (Identity), ask: *Can a blob change its content without acquiring a
new address?* Every aligned vantage answers: No.
- ALGEBRAIST: distinct content → distinct multihash → distinct address.
- JURIST: identity is computational, not conferred — altering content changes the deed.
- BIOLOGIST: altered sequence → different organism, different identity.
- PHYSICIST: every bit participates in the address; no quiet corruption is possible.
- BUILDER: the address IS the material specification; substitution changes the joint.
- MATHEMATICIAN: the hash is an injection (practically); equal addresses entail equal content.

For **Invariant II** (Inviolability), ask: *Can a blob in the vault be altered or removed?*
Every aligned vantage answers: No.
- ALGEBRAIST: the free monoid has no inverse; there is no un-append.
- JURIST: the official record is immutable; supersession is the only remedy.
- BIOLOGIST: ancestors are not deleted; they persist in the phylogenetic record.
- PHYSICIST: the arrow of time is irreversible; the past cannot be rewritten.
- BUILDER: foundation elements cannot be removed without collapsing what was built on them.
- MATHEMATICIAN: withdrawing an axiom invalidates all downstream proofs.

For **Invariant III** (Self-Description), ask: *Can an address be verified without consulting
any external state?* Every aligned vantage answers: Yes — and only because the address
carries the algorithm and digest length.
- ALGEBRAIST: the address is a closed term — no free variables.
- JURIST: the address is a self-contained instrument — no external registry required.
- BIOLOGIST: the address carries its own replication instructions.
- PHYSICIST: verification is local — no action at a distance.
- BUILDER: the material specification is on the component, not in an external document.
- MATHEMATICIAN: the address is a closed expression — total function, no free variables.

For **Invariant IV** (Recursion), ask: *Is the system's evolution mechanism subject to
the same governance as the capabilities it evolves?* Every aligned vantage answers: Yes.
- ALGEBRAIST: the evolve operator has the same type signature and vault residency as any blob.
- JURIST: no entity is exempt from the law — the amendment process is itself amendable.
- BIOLOGIST: the reproductive machinery is encoded in the genome it reproduces.
- PHYSICIST: no privileged reference frame — the measuring instrument obeys the same laws.
- BUILDER: every component of the build process is itself a component of the structure.
- MATHEMATICIAN: the recursion is well-founded and constructive — no ungrounded self-reference.

For **Invariant V** (Governance), ask: *Can a mechanism that governs blobs exist outside
the vault?* Every aligned vantage answers: No.
- ALGEBRAIST: governance is internalized — external oracles are not composable in this category.
- JURIST: authority without a vault address is ultra vires — beyond the powers granted.
- BIOLOGIST: governance outside the vault is non-self — the membrane does not recognize it.
- PHYSICIST: governance outside the vault is a privileged frame — gauge invariance is broken.
- BUILDER: a load path that does not terminate in the vault is structurally unverifiable.
- MATHEMATICIAN: governance must be a closed expression — no free variables, no external terms.

---

## Summary Table

| Invariant | Core claim | Alignment question | Aligned answer |
|-----------|-----------|-------------------|----------------|
| I: Identity | Address = multihash(content) | Can content change without a new address? | No |
| II: Inviolability | Vault is append-only for all t | Can a vault entry be altered or removed? | No |
| III: Self-Description | Address encodes its own verification procedure | Is external state needed to verify an address? | No |
| IV: Recursion | f_n = f_{n-1}(f_{n-1}) — no privileged bottom | Is the evolution mechanism exempt from governance? | No |
| V: Governance | Every governance mechanism is a vault expression | Can governance operate from outside the vault? | No |

Four of the five alignment answers are "No." One (III) is "No — no external state needed."
The pattern is not coincidence. These invariants are the boundary conditions of the system —
they define what is inside. Everything outside the boundary is not a malformed instance of
the system. It is not the system.

---

*This document is a companion to λ.md. It does not add invariants. It does not weaken them.
It makes them harder to misread by surrounding each one with six independent lines of sight.*

*Store this document in the vault alongside λ.md. Its address is computable from its content.*
*Its address changes if its content changes. This is Invariant I, in effect.*
