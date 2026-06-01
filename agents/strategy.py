from .base import BaseAgent


class StrategyAgent(BaseAgent):
    def __init__(self, client, model="gpt-4o-mini"):
        super().__init__(client, "Strategy Recommendation Agent", "Product Strategy Consultant", model)

    def analyze(self, shared_context: dict) -> str:
        data = shared_context["data"]
        prior = shared_context.get("results", {})
        summary = data.get("summary", {})

        customer_insights = prior.get("Customer Feedback Agent", "")
        sales_insights = prior.get("Sales Analysis Agent", "")
        swot_insights = prior.get("SWOT Analysis Agent", "")
        priority_insights = prior.get("Feature Prioritization Agent", "")

        system_prompt = (
            "You are a senior Product Strategy Consultant with deep expertise in product-led growth, "
            "go-to-market strategy, and competitive positioning. Synthesize all available analysis "
            "into a comprehensive, actionable strategic plan. Be specific, data-driven, and "
            "business-focused. Use markdown formatting."
        )

        user_prompt = f"""You have access to comprehensive analysis from multiple specialist agents.
Synthesize everything into a complete Strategic Recommendations Report.

## BUSINESS METRICS
{self._fmt_summary(summary)}

## CUSTOMER INSIGHTS SUMMARY
{customer_insights[:1000] if customer_insights else ''}

## SALES ANALYSIS SUMMARY
{sales_insights[:1000] if sales_insights else ''}

## SWOT ANALYSIS SUMMARY
{swot_insights[:800] if swot_insights else ''}

## FEATURE PRIORITIZATION SUMMARY
{priority_insights[:800] if priority_insights else ''}

## RAW DATA
{data.get('product_stats_text', '')}
{data.get('monthly_trends_text', '')}

Write a comprehensive Strategic Recommendations Report with these sections:

### 1. Strategic Situation Assessment
2-3 paragraph executive-level assessment of the current business situation, key challenges, and opportunities.

### 2. Strategic Objectives (Next 12 Months)
Define 3-5 clear, measurable strategic objectives with target metrics.

### 3. Growth Strategy
**Product Strategy**: Which products to grow, maintain, or sunset and why.
**Market Strategy**: Which regions to prioritize and how to expand.
**Customer Strategy**: How to improve acquisition, satisfaction, and retention.

### 4. Revenue Optimization Plan
Specific tactics to improve revenue and margins. Include pricing strategy, marketing reallocation, and cost optimization opportunities.

### 5. Risk Mitigation Plan
Top 3 business risks and specific mitigation strategies for each.

### 6. Competitive Positioning
Recommended positioning strategy based on product strengths and market data.

### 7. Strategic Action Plan
A prioritized list of 10 specific actions with:
- Action item
- Owner (role)
- Timeline
- Expected impact
- Success metric

### 8. Key Performance Indicators (KPIs)
Define 8-10 KPIs to track strategic progress. Include current baseline and 12-month targets.

### 9. Investment Recommendations
Where to increase and decrease investment based on the data.

Use markdown with clear headers, bullet points, tables where helpful, and specific numbers.
{self._fmt_additional(data)}"""

        return self.call_llm(system_prompt, user_prompt, max_tokens=3500)
