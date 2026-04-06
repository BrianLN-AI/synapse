# Principle: Minimalist Documentation (The Living-State Mandate)

## Definition
Documentation is not an archive of our "process"; it is a **Living-State Sensor**. We prioritize current system invariants over historical proposals.

## The Principles
1.  **Documentation as Interface, Not History**: If documentation does not define a current `Invariant`, an active `Sensor`, or a `Vantage` for future auditors, it is dead weight.
2.  **The Git-is-Archive Axiom**: We do not store "proposals," "drafts," or "failed synthesis data" in the working tree. Git is our archive; the working tree is our **Current-State Truth**. 
3.  **Delete as Evolution**: If a protocol or ADR is superseded by a newer implementation, the old document is deleted from the working tree. We maintain the "System-as-it-Exists," not the "System-as-it-Was."
4.  **No Dead-Weight Documentation**: We reject the "paper trail" fallacy. If it's not needed to audit the current invariants, it is removed. 

## How this changes our work:
*   **The Repository is the System**: When someone (human or agent) clones this repo, they see *what the system is*, not a museum of everything we tried.
*   **No "Archiving" Folder**: We don't "move to archive" files; we delete them. If we need them, we checkout the commit.
*   **The Living Record**: We only keep documentation that *governs* the present.
