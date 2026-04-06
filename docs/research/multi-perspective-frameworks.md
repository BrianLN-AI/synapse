# Research: Multi-Perspective Systems Modeling

**Date:** 2026-04-06
**Purpose:** Find existing bodies of work on multi-perspective systems modeling to validate/inform our vantage framework

---

## Status

- [x] Rozanski & Woods Viewpoints/Perspectives — fetched, readable
- [x] Cognitive Dimensions (Wikipedia + theory) — fetched, readable  
- [x] Soft Systems Methodology — web search, surface info
- [x] Finkelstein Viewpoints (1992) — **FETCHED AND PARSED**
  - PDF: `docs/research/papers/finkelstein-viewpoints-1992.pdf`
  - Text: `docs/research/papers/finkelstein-viewpoints-1992.txt` (1334 lines)
  - Source: https://openaccess.city.ac.uk/id/eprint/26496/
- [x] Cognitive Dimensions tutorial (Green & Blackwell) — **FETCHED AND PARSED**
  - PDF: `docs/research/papers/green-cognitive-dimensions-tutorial.pdf`
  - Text: `docs/research/papers/green-cognitive-dimensions-tutorial.txt` (3076 lines)
  - Source: http://www.cl.cam.ac.uk/~afb21/CognitiveDimensions/CDtutorial.pdf
- [ ] TRIZ — web search, surface info
- [ ] Alexander Pattern Language — web search, surface info

---

## Existing Frameworks Found

### 1. Cognitive Dimensions (Green & Petre)

**Source:** Thomas R.G. Green, Marian Petre (1996)
**What:** 14 formal dimensions for evaluating notations/UI/programming languages

| Dimension | Measures |
|-----------|----------|
| Abstraction gradient | Min/max abstraction levels |
| Closeness of mapping | Notation ↔ problem domain |
| Consistency | Can you guess the rest? |
| Diffuseness/terseness | Verbosity |
| Error-proneness | Likelihood of mistakes |
| Hard mental operations | Processing burden |
| Hidden dependencies | Coupling visibility |
| Juxtaposability | Side-by-side comparison |
| Premature commitment | Order constraints |
| Progressive evaluation | Feedback on incomplete work |
| Role-expressiveness | Role clarity |
| Secondary notation | Escape from formalism |
| Viscosity | Resistance to change |
| Visibility | Findability |

**Key insight:** Dimensions are pairwise independent but trade off. Design maneuver in one usually affects another.

**Reference:** https://en.wikipedia.org/wiki/Cognitive_dimensions_of_notations

---

### 2. Rozanski & Woods Viewpoints + Perspectives

**Source:** "Software Systems Architecture" (Rozanski & Woods, 2011)
**What:** Viewpoints partition architecture; Perspectives apply across viewpoints

**Viewpoints:**
- Functional, Information, Deployment, Development, Operational, etc.

**Perspectives (cut across all viewpoints):**
- Accessibility, Availability & Resilience, Development Resource, Evolution, Internationalization, Location, Performance & Scalability, Regulation, Security, Usability

**Key insight:** Some concerns (security) don't fit a single viewpoint — they need perspectives that apply across.

**Reference:** https://www.viewpoints-and-perspectives.info/home/perspectives/

---

### 3. Finkelstein Viewpoints (1992)

**Source:** Finkelstein, Kramer, Nuseibeh, Goedicke — "Viewpoints: A Framework for Integrating Multiple Perspectives in System Development"
**What:** Academic framework for requirements engineering with multiple stakeholders

**Status:** PDF did not render — needs re-fetch or alternative source

---

### 4. Soft Systems Methodology (Checkland)

**Source:** Peter Checkland, Lancaster University (1980s)
**What:** Multiple "world views" for complex organizational problems

**Key concept:** Different stakeholders have different "world views" — the methodology structures finding and resolving these.

---

### 5. Alexander Pattern Language

**Source:** Christopher Alexander — "A Pattern Language" (1977)
**What:** Recurring solutions with context

**Key concept:** Patterns are form-language pairs that solve recurring problems in context.

---

## What This Means for Our Vantage Framework

| Existing Framework | What we could use | Gap |
|-------------------|-------------------|-----|
| Cognitive Dimensions | Formal, testable, well-established | Too notation-focused |
| Rozanski & Woods | Viewpoint/perspective distinction | Practitioner, not formal |
| Finkelstein Viewpoints | Academic foundation | Unknown (can't read PDF) |
| Soft Systems | World views concept | Complex, organizational focus |
| Alexander Pattern | Reusable patterns with context | Patterns vs perspectives |

---

## Our Potential Contribution

We're applying **disciplinary perspectives** (economist, biologist, physicist) to systems — not:
- Concern-based views (Cognitive Dimensions)
- Stakeholder-based viewpoints (Rozanski)
- Notation-focused dimensions (Green & Petre)

**What we'd add:**
1. Domain-based perspectives
2. Transformation rules between perspectives
3. Conflict detection

**What we lack:**
1. Formal definitions
2. Proven utility
3. Validation against real systems

---

## Action Items

- [x] Fetch Finkelstein PDF (via curl + pdftotext)
- [x] Fetch Cognitive Dimensions tutorial PDF (via curl + pdftotext)
- [ ] Read Soft Systems Methodology paper
- [ ] Read Alexander Pattern Language
- [ ] Read Finkelstein extracted text (1334 lines)
- [ ] Read Cognitive Dimensions tutorial extracted text (3076 lines)
- [ ] Validate our vantage framework against these sources
- [ ] Consider adopting Cognitive Dimensions as formal vocabulary
- [ ] Compare our vantage framework to Finkelstein's Viewpoints framework
