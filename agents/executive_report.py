from .base import BaseAgent


class ExecutiveReportAgent(BaseAgent):
    def __init__(self, client, model="gpt-4o-mini"):
        super().__init__(client, "Executive Report Agent", "Executive Communications Specialist", model)

    def analyze(self, shared_context: dict) -> str:
        data = shared_context["data"]
        prior = shared_context.get("results", {})
        summary = data.get("summary", {})

        all_insights = "\n\n".join(
            f"=== {name} ===\n{content[:600]}"
            for name, content in prior.items()
            if content
        )

        system_prompt = (
            "You are an Executive Communications Specialist. Your role is to distill complex "
            "multi-agent analysis into a concise, compelling executive summary for C-suite leaders. "
            "Write with clarity, confidence, and precision. Use markdown. Focus on decisions, "
            "not analysis details."
        )

        user_prompt = f"""Create a Board-Ready Executive Summary from the following comprehensive analysis.

## BUSINESS METRICS
{self._fmt_summary(summary)}

## AGENT ANALYSIS SUMMARIES
{all_insights}

Write a concise but comprehensive Executive Summary Report:

### EXECUTIVE SUMMARY
A 3-4 paragraph board-ready summary of the business situation, key findings, and recommended path forward. Write as if presenting to the CEO and board.

### KEY FINDINGS AT A GLANCE
A bulleted list of the 8 most important findings across all analysis areas. Each finding should be a single sentence with a specific data point.

### BUSINESS PERFORMANCE SCORECARD
| Dimension | Performance | Trend | Priority |
|-----------|-------------|-------|----------|
Rate: Revenue, Profitability, Customer Satisfaction, Product Quality, Marketing Efficiency, Regional Coverage
Use: Excellent/Good/Fair/Poor for Performance; Up/Stable/Down for Trend; High/Medium/Low for Priority

### TOP 3 STRATEGIC PRIORITIES
The 3 most critical actions the leadership team must take in the next 90 days. For each:
- What: Specific action
- Why: Business impact
- How: Implementation approach
- Success Metric: How to measure

### INVESTMENT DECISIONS
Immediate investment recommendations:
- **INCREASE**: Where to invest more and expected return
- **MAINTAIN**: Where to hold current investment levels
- **REDUCE**: Where to cut back and reallocate

### PRODUCT PORTFOLIO ASSESSMENT
One-line assessment per product with recommendation (Scale / Invest / Fix / Watch / Review).

### RISKS & MITIGATION
Top 3 risks with likelihood, impact, and mitigation approach.

### 12-MONTH OUTLOOK
Revenue and growth projection narrative based on recommended actions.

Write concisely but with authority. This document will be read by executives making business decisions."""

        return self.call_llm(system_prompt, user_prompt, max_tokens=3000)
