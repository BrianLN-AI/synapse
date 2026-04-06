# Synapse Knowledge Graph Schema (v0.1)

This schema formalizes the "Information Model" for all vantage probes. Every agent output must conform to this schema to allow for graph-based analysis (convergences, conflicts, and invariants).

```json
{
  "schema_version": "0.1",
  "metadata": {
    "artifact_id": "string",
    "vantage_id": "string",
    "timestamp": "ISO8601"
  },
  "nodes": [
    {
      "id": "string",
      "type": "Fact | Axiom | Measurement | Conflict",
      "content": "string",
      "justification": "string",
      "provenance": "UNTRAINED | TRAINED | EXPERT-VALIDATED"
    }
  ],
  "edges": [
    {
      "source": "string",
      "target": "string",
      "relation": "conflicts_with | supports | refines | entails"
    }
  ],
  "logic": {
    "axioms_applied": ["string"],
    "diagnostic_findings": ["string"]
  }
}
```

---

## Node Taxonomy

| Type | Definition |
|------|------------|
| **Fact** | An empirical observation from the artifact (e.g., "The governance gate is a blob.") |
| **Axiom** | The first-principles rule applied (e.g., "Incentives drive rational actor behavior.") |
| **Measurement** | A quantitative metric (e.g., "14-day promotion latency.") |
| **Conflict** | A logical or incentive-based contradiction (e.g., "Security vs. Economist mapping.") |

---

## Deployment Strategy

1. **Agent Output:** Council agents are now instructed to output valid JSON conforming to this schema.
2. **Graph Ingestion:** We will create an automated parser that ingests these JSON blobs into our `/ug` graph storage.
3. **Graph Analysis:** We use graph queries (e.g., "Find all nodes with `type: Conflict`") to automatically map the "Systemic Mismatch" across the entire Synapse architecture.

This transforms our research from **"Reading Docs"** to **"Querying the System Model."**
