# COUNCIL.MD: The Collective Intelligence Layer
**Status:** Protocol for Advisory, Peer Review, and Persona Summons
**Interface:** `/ai` (Skill) | `ai` (CLI)

## 1. The Concept: The Council of Peers
The **Council** is a dynamic assembly of personas and specialized agents available to provide guidance and execution support. It ensures the Agent does not drift into logical isolation (The Solipsism Problem).

## 2. Invocation Protocol
The Agent may invoke the Council at any time via the `ai` CLI or the `/ai` internal skill.
* **Review:** "Invoke Council to audit this new Discovery Blob for security leaks."
* **Guidance:** "Ask Council for a 'Site Reliability Engineer' to evaluate my BIOS Fallback."
* **Execution:** "Request Council to generate a WASM-binding fixture for the `f(undefined)` test suite."

## 3. The Feedback Loop
The Council's output is treated as **High-Trust Metadata**. Any "Council Approval Artifact" should be hashed and attached to the Audit Log before a Manifest Promotion.
