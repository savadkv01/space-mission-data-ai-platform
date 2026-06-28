# 10 Interview Questions

## Executive Summary

This document prepares the project owner to explain the business-analysis phase during technical interviews, portfolio reviews, or architecture discussions. The questions focus on judgment, scope control, business value, and trade-off quality rather than implementation specifics.

## Interview Questions and Answers

### 1. Why did you start with business analysis instead of building pipelines immediately?

A business-first phase prevents premature architecture decisions. In a space and AI platform, the wrong scope can create an impressive technical stack that solves low-value problems. This phase establishes which business decisions matter, who the users are, which use cases are realistic with accessible data, and how success should be measured.

### 2. Why is Earth observation intelligence the recommended MVP instead of satellite telemetry or launch analytics?

Earth observation intelligence provides the best balance of business value, public-sector relevance, open-data access, and AI richness. Telemetry and launch analytics are important, but they depend heavily on proprietary, sparse, or safety-critical datasets that are difficult to represent credibly in a public capstone.

### 3. How did you decide which use cases to rank highest?

I used a weighted scoring model across business value, implementation feasibility, data availability, AI potential, portfolio value, and interview value. That made the selection explicit and defensible rather than driven by prestige or intuition alone.

### 4. Why include metadata quality and cataloging in a business analysis for an AI platform?

Because a platform only creates value if analysts can discover and trust the data. Metadata quality is a business productivity problem, not just a technical housekeeping task. Poor discoverability slows response time, increases duplicate work, and weakens confidence in downstream analytics.

### 5. What makes this project still feel aerospace-focused if the MVP centers on Earth observation and maritime monitoring?

Earth observation is a core aerospace business domain. The MVP still depends on space-derived data, mission-oriented monitoring, and downstream operational decisions. It also leaves a clear roadmap into telemetry, space weather, and mission operations once a credible data and decision foundation exists.

### 6. Why did some high-profile aerospace use cases rank lower than disaster or maritime use cases?

Not because they lack value, but because they are less realistic for this constraint set. High-profile domains such as collision avoidance, launch analytics, and spacecraft anomaly detection have strong strategic importance, but public datasets, validation realism, and safe demonstration quality are weaker.

### 7. How would you explain the business value of the MVP to an executive?

It reduces the time between raw space-derived data and an actionable decision. In practice, that means earlier wildfire alerts, faster flood impact awareness, more efficient maritime enforcement, and less analyst time wasted searching for reliable imagery.

### 8. What are the main risks in your recommended scope?

The main risks are data quality gaps, false positives or false negatives in alerting, metadata inconsistency, scope drift, and overclaiming beyond what open datasets can support. I addressed those by selecting use cases with visible evidence chains and by framing analytics as decision support.

### 9. Why did you include interview value as a scoring criterion?

Because this project is also a portfolio asset. A strong capstone should demonstrate technical judgment and business prioritization in a way that creates meaningful conversation during hiring. Interview value should not dominate the ranking, but it is a legitimate secondary consideration.

### 10. How would this phase influence later architecture choices?

It narrows the architecture problem. Once the business scope is clear, later phases can design storage, pipelines, APIs, and AI workflows around specific decision windows, user journeys, KPI targets, and data domains instead of generic platform ambitions.

### 11. What did you deliberately avoid in this phase?

I avoided infrastructure design, implementation detail, schema design, code generation, and premature tool selection. The goal here was to define the business problems and the value logic, not the technical solution.

### 12. If you had more resources, would you still keep the same MVP?

Possibly not. With access to proprietary telemetry, operations data, and larger compute, a mission-operations-first MVP could become viable. Under the current constraints, though, the selected scope is the most defensible balance of realism and impact.

### 13. How does the roadmap avoid becoming a random backlog of AI ideas?

Each roadmap stage expands from the business logic of the prior one. Version 1.0 proves EO monitoring value. Later versions broaden into additional environmental domains, then maritime and climate intelligence, then mission-support scenarios, and only later move into telemetry-heavy operations.

### 14. What is the strongest business insight from this phase?

The strongest insight is that the platform should be judged by the decisions it improves, not by the volume of data it can store or the sophistication of individual models.

### 15. What would you say if an interviewer argued that telemetry anomaly detection is the only truly aerospace use case?

I would challenge that framing. Earth observation, disaster intelligence, and maritime monitoring are also core aerospace value chains because they rely on spaceborne assets and mission-derived data products. Aerospace value is not limited to spacecraft housekeeping; it also includes the operational services enabled by those assets.

## Cross References

- The ranking logic is documented in [04-use-case-ranking.md](./04-use-case-ranking.md).
- The recommended MVP is documented in [05-mvp-definition.md](./05-mvp-definition.md).
- The roadmap context is documented in [06-roadmap.md](./06-roadmap.md).
