# JOBS-TO-BE-DONE — Vantage Completeness Review
## Role: Demand-side innovation, functional/emotional/social jobs, struggling moments
## Lens: What jobs does Synapse get hired to do? What struggling moments does it address?

**Reviewed:** 2026-04-02
**Vantage document:** `docs/vantages/VANTAGES.md` (30 vantages across 12 clusters)
**System under review:** Synapse D-JIT Logic Fabric — append-only blob vault, content-addressed identity, self-modifying via f_n = f_{n-1}(f_{n-1}), typed governance expressions, 4-layer execution stack

---

## Does JTBD Deserve Its Own Vantage?

Yes. The case is strong and the gap is structural.

The ECONOMIST already occupies the Social cluster and sees market structure, pricing,
incentives, and rational actor behavior. The ADVOCATE sees power distribution and
structural exclusion. Neither of these is a demand-side lens. Both observe what the
system offers; neither starts from the participant's struggling moment.

JTBD theory (Christensen, Ulwick, Klement) inverts the standard analytical posture.
Instead of asking "what does this system do?" — the question every vantage in
VANTAGES.md asks — it asks "what is the participant trying to accomplish when they
reach for this?" The unit of analysis is not the system; it is the job. The job
exists before the system. The system either gets hired to do the job or it doesn't.
This inversion is not a perspective shift on the same facts — it surfaces different
facts entirely.

The struggling moment is the diagnostic instrument. A developer reaching for Synapse
is in some situation that existing tools have failed to resolve. What is that situation?
The ECONOMIST cannot answer this. The BUILDER cannot answer this. The CHILD asks "why
would anyone want this?" and accepts the system's own answer. The JTBD analyst refuses
the system's answer and goes to find the struggling participant to ask.

The gap this creates: every other vantage in VANTAGES.md reads a system that has
already been hired. The JTBD vantage asks whether the right jobs were identified in
the first place, which jobs are over-served, and which jobs — the most important ones —
go unnamed and therefore undesigned-for.

---

## Jobs Synapse Gets Hired For

### Functional Jobs

**"When I need to share a reusable algorithm across systems or agents, help me verify
that what I deployed is what I intended, so I can eliminate runtime divergence between
environments."**
The content address is the functional solution to this job. The hash is the hiring
criterion: it proves identity without a registry, without a naming authority, without
coordination overhead.

**"When I need to run code I did not write, help me know whether it passed a meaningful
quality bar, so I can use it without becoming responsible for its internals."**
The governance gate is hired for this job. The fitness score is the signal the
participant consumes. The telemetry record is the audit trail they will use if something
goes wrong.

**"When I need multiple AI agents to agree on a piece of logic before deploying it,
help me run that agreement protocol without it becoming my coordination problem."**
The GOKR and IAC convergence protocol are hired for this job. The job was previously
done manually — by email chains, Slack threads, PR reviews, meeting notes. Synapse hires
back the time and attention that coordination was consuming.

**"When I need to improve my own execution infrastructure, help me do it without taking
the system down or writing a second system alongside the first."**
`f_n = f_{n-1}(f_{n-1})` is hired for this job. The job existed long before Synapse:
every team that has tried to upgrade a production system while it runs has felt this
struggle. The fabric's self-modification property is the functional solution, not an
architectural curiosity.

**"When I need to authorize a code deployment, help me demonstrate that the authorization
happened and cannot be denied later."**
The governance expression and cryptographic seal are hired for this job. The job is
non-repudiation of promotion decisions. The telemetry hash is the artifact the auditor
will want.

### Emotional Jobs

**"Help me feel confident that I know what is running in my system."**
Content addressing is also an emotional hire. The hash either matches or it doesn't.
There is no ambiguity, no version confusion, no "I think that's the right one." The
emotional progress this enables: from chronic low-grade uncertainty to verifiable
certainty.

**"Help me feel like I'm not the last line of defense."**
The governance gate is hired emotionally as a backstop. The developer who promotes a
blob did not make the decision alone — the governance expression witnessed it, the
telemetry sealed it, the fitness evaluation preceded it. Shared responsibility is
emotional progress.

**"Help me feel like my contribution to a shared system is permanent and credited."**
The append-only vault is an emotional hire for contributors who have had their work
overwritten, deprecated without notice, or silently replaced. Immutability is not
just a technical property — it is the promise that what you wrote is not going away.

### Social Jobs

**"Help me demonstrate to my organization that algorithm deployment is governed, not
ad hoc."**
The governance expression and telemetry record are hired for this social job. The
audience is not the system — it is the principal's manager, auditor, or compliance
function. Governance as a social signal, not just a technical constraint.

**"Help my team converge on a shared understanding of what 'good enough to ship' means,
without the answer being whoever has the loudest voice."**
The fitness threshold and adversarial test suite are hired to depersonalize the quality
standard. The social progress: replacing taste-based authority with evidence-based
criteria.

---

## Struggling Moments and Underserved Jobs

### Struggling Moments Synapse Directly Addresses

**The "which version is running?" struggle.** Developers in distributed systems spend
significant time diagnosing version drift — different nodes running different code with
no way to verify identity without coordinated deployment tooling. Content addressing
eliminates this class of struggle entirely.

**The "who approved this?" struggle.** In environments with compliance requirements or
post-incident reviews, the question of who authorized a deployment and when is often
unanswerable. The governance expression and telemetry record make it permanently
answerable.

**The "how do I upgrade without breaking the thing that depends on it?" struggle.**
Library versioning, API compatibility, and live-system upgrades are chronic developer
pain. The vault's append-only structure with immutable addresses means the upgrade
path does not require the old path to disappear.

**The "can I trust this code that wasn't written by my team?" struggle.** Third-party
dependencies are a trust problem before they are a technical problem. The fitness
evaluation and governance gate are hired to reduce the trust burden on the consuming
principal.

### Underserved Jobs (Design Whitespace)

**"Help me understand why a blob was promoted, not just that it was."**
The governance gate captures that a blob passed. It does not capture the deliberative
reasoning behind the fitness criteria. A blob may be promoted with a score of 0.82
and the consuming principal has no access to the reasoning that produced that number.
The job: transparent fitness rationale, not just a score.

**"Help me find a blob that does approximately what I need, when I don't know the
exact address."**
Content addressing is perfect for retrieval by identity; it is useless for discovery
by function. The participant who wants "a blob that handles OAuth token validation
against a JWKS endpoint" has no search path. The vault is a library with no card
catalog. This is the largest underserved functional job in the current design.

**"Help me understand the downstream consequences of removing my dependency on a
specific blob."**
The vault preserves everything but provides no dependency graph. A blob author who
wants to understand who depends on their blob before making changes has no instrument
for this. The job is impact analysis before change, not just identity verification
after deployment.

**"Help me hire a blob for a job that requires different behavior in different
contexts, without proliferating nearly-identical blobs."**
The ABI accepts a context dict, but blob selection is currently identity-based.
There is no parameterized blob pattern — no way to hire "this blob but configured for
my tenant's locale and rate limits." Over-served job: proliferation of nearly-identical
blobs. Under-served job: configuration-layer separation from logic.

**"Help the person who is not a developer consume the results of blobs without
understanding the system."**
The current participant model is implicitly technical: principals hold keys, invoke
blobs by address, interpret telemetry. The non-technical stakeholder — who consumes
the output of blob-mediated processes — has no addressed job in the current design.
This is the widest structural gap from a demand-side perspective.

---

## Other Gaps This Lens Reveals

**The PRODUCT MANAGER vantage is missing.** JTBD analysis often surfaces a need for
the demand-side product perspective alongside the supply-side technical perspectives.
A PRODUCT MANAGER vantage would ask: which jobs are growing in urgency, which blobs
are getting hired most frequently, and what does the usage pattern tell us about
where the system needs to develop next? This is distinct from ECONOMIST (which asks
about incentives) and JTBD (which asks about jobs). The PM asks: given the jobs map,
what should we build next?

**The USER RESEARCHER vantage is missing.** JTBD theory is ultimately an empirical
discipline — you find the struggling moments by talking to participants, not by
reasoning from first principles. A USER RESEARCHER vantage would ask: what evidence
collection methods are built into the system that would allow demand-side learning
over time? Currently, the telemetry record captures invocation facts but not job-level
intent — the participant's goal when they made the invocation. This is a design gap,
not just an observational one.

---

## Priority

**Critical.** JTBD is not a minor addition. Every other vantage in VANTAGES.md reads
the system from the supply side — what the system is, does, enforces, or enables.
None of them starts from the participant's situation. The demand-side gap means the
vantage framework has no instrument for detecting whether the system is being hired
for the right jobs, over-serving some jobs while leaving others unaddressed, or
drifting away from the actual struggling moments it was built to address.

The underserved discovery job alone — the inability to find a blob by function rather
than by address — is a design constraint that no supply-side vantage would surface.
The JTBD lens finds it immediately because it asks: "when the participant wants to
hire a blob, what is their situation at the moment of hiring?" The answer: they do not
know the address. They know the job.

---

### `[JOBS-TO-BE-DONE]`

#### The Persona

Studies why people hire products, services, and systems to make progress in their
lives. The core insight of JTBD theory (Christensen, Ulwick, Klement) is that the
unit of analysis is not the customer, not the product, and not the market segment —
it is the *job*. A job is the progress a person is trying to make in a particular
circumstance. People do not buy software; they hire it to do a job they cannot do
themselves, or cannot do well enough with their current hire.

The JTBD analyst's first move is to find the struggling moment: the specific situation
where the current solution is failing. The struggling moment precedes the hire. It is
where the desire for progress meets the inadequacy of available tools. Products that
get hired most reliably are those that address a struggling moment so precisely that
the participant feels recognized by the design — as if the system was built for their
exact situation.

Jobs have three dimensions. The functional job is the concrete task: "process this
payload," "verify this signature," "deploy this update." The emotional job is the
internal state the participant wants to achieve: "feel confident that nothing will
break," "feel like I made a defensible decision." The social job is the external
image: "demonstrate to my organization that we have a governance process," "be seen
by my team as the person who solved the dependency management problem." Functional
jobs are necessary; emotional and social jobs determine whether the hire actually
sticks — whether participants keep using the system once they could leave.

JTBD theory also maps the job executor — the specific person in the situation who makes
the hiring decision — and distinguishes them from other participants. The architect who
decides to adopt Synapse has different jobs than the developer who invokes blobs daily,
who has different jobs than the compliance officer reviewing the telemetry record. A
single system can be hired by multiple executors for different jobs, and it must serve
them all or risk being fired by the most influential one.

Core question in general: *What job is this being hired to do?*

#### The System

The content address is hired for a job that most registry systems fail: *permanent
verifiable identity with no coordination overhead*. The struggling moment it addresses
is the developer who has experienced version drift — who has debugged a production
incident only to discover that different nodes were running different code with no
way to detect the difference. The hash either matches or it does not. This is not
a nuanced improvement on existing registries; it is a categorical change in what the
participant can know. The functional job is identity verification. The emotional job
is certainty. These are distinct, and the design serves both.

The governance gate is hired for two jobs simultaneously, and the duality is important.
The first job is the *functional authorization record*: the participant needs to
demonstrate, after the fact, that a deployment decision had a process behind it.
The governance expression and telemetry hash are the evidence. The second job is
*shared moral responsibility*: the participant who promotes a blob does not want to
be the sole accountable party. The quorum requirement distributes accountability.
Both jobs are real; neither is reducible to the other. The ECONOMIST sees incentives;
the JTBD analyst sees the struggling participant who has been blamed for a bad
deployment and never wants to be alone in that position again.

The GOKR protocol and IAC convergence are hired to do a job that knowledge management
systems, wikis, Slack channels, and retrospective documents have consistently
under-served: *produce a durable, authored agreement among independent agents without
the agreement becoming anyone's maintenance burden*. The struggling moment is the
team that has had the same architectural debate three times because the outcome of
the first debate was not encoded anywhere that subsequent reasoning would consult.
GOKR convergence produces an artifact — a blob — not a document. The blob can be
invoked; the document can only be read. The functional job shifts from "record the
decision" to "enforce the decision in execution."

The `f_n = f_{n-1}(f_{n-1})` self-modification property is hired for the job of
*live system improvement without a second system*. Every team that has maintained a
production system has felt this struggle: the system that is running cannot be the
system you are improving. You need a shadow environment, a canary deployment, a
feature flag system, a migration path. The fabric's self-hosting property collapses
this into a single operation: promote the next generation through the current
governance gate. The emotional job here is not just efficiency — it is the relief of
*not carrying two systems*. The social job is demonstrating that the team's deployment
capability is genuinely sophisticated, not just scripted.

The append-only vault is hired, at the emotional level, for permanence. Contributors
to shared systems routinely experience their work being silently overwritten, deprecated
without consultation, or lost in a migration. The vault's inability to forget is a
design choice that addresses an emotional job that no functional job statement captures:
*the need for work to be treated as permanent once committed*. This is why the THEOLOGIAN
finds covenant structure here. The JTBD analyst finds the same structure from the demand
side: participants hire permanence because they have been burned by impermanence.

The system's most significant underserved job is discovery by function. The vault is
a library with no card catalog. Content addressing is the perfect retrieval mechanism
for participants who know exactly what they want; it is entirely useless for
participants who want to describe a job and find blobs that have been hired to do it.
The struggling moment: a developer knows there is probably a blob in the vault that
handles HMAC token validation, but they do not know its address, they do not know
who to ask, and the vault provides no search surface. They write a new blob. The vault
accumulates near-duplicate blobs. Keystone blobs go under-referenced because they
are unfindable. This is the largest design gap visible from the demand side — and it
is invisible from every supply-side vantage in VANTAGES.md, because supply-side
vantages do not start from the moment of the hire.
