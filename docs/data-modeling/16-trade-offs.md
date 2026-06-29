# 16 - Trade-off Analysis

> **Phase 6 - Data Modeling** · Document 16 of 18

| Decision | Chosen | Alternative | Trade-off |
| --- | --- | --- | --- |
| Star vs Data Vault | Star | Data Vault | Simplicity/speed vs auditability/scale |
| Wide vs normalized | Wide Gold marts | Normalized | Read speed vs storage/dup |
| Batch aggregates vs real-time views | Batch | Real-time | Cost/feasibility vs freshness |
| Feature store vs direct compute | Feature store | Inline | Reuse/no-leakage vs setup cost |

All choices favor laptop feasibility and reuse; full justifications in [17-adr.md](17-adr.md).
