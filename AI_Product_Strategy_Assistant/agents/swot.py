from .base import BaseAgent


class SWOTAgent(BaseAgent):
    def __init__(self, client, model="gpt-4o-mini"):
        super().__init__(client, "SWOT Analysis Agent", "Strategic Business Analyst", model)

    def analyze(self, shared_context: dict) -> str:
        data = shared_context["data"]
        prior = shared_context.get("results", {})
        summary = data.get("summary", {})

        customer_insights = prior.get("Customer Feedback Agent", "")
        sales_insights = prior.get("Sales Analysis Agent", "")

        system_prompt = (
            "You are a Strategic Business Analyst specializing in SWOT analysis for technology "
            "product companies. Synthesize data and prior agent insights into a precise, actionable "
            "SWOT analysis in markdown. Every point must be supported by evidence from the data."
        )

        user_prompt = f"""Synthesize the following data and insights to produce a comprehensive SWOT Analysis.

## BUSINESS METRICS
{self._fmt_summary(summary)}

## CUSTOMER INSIGHTS (from Customer Feedback Agent)
{customer_insights[:1500] if customer_insights else data.get('reviews_text', '')[:800]}

## SALES INSIGHTS (from Sales Analysis Agent)
{sales_insights[:1500] if sales_insights else data.get('product_stats_text', '')[:800]}

## PRODUCT PERFORMANCE
{data.get('product_stats_text', '')}

Write a comprehensive SWOT Analysis with these sections:

### STRENGTHS (Internal Positives)
List 6-8 specific strengths with supporting evidence. Examples: high-margin products, strong ratings, regions performing well, marketing efficiency.

### WEAKNESSES (Internal Negatives)
List 6-8 specific weaknesses with supporting evidence. Examples: high return rates, low ratings, poor marketing ROI, underperforming regions.

### OPPORTUNITIES (External Positives)
List 6-8 market opportunities. Examples: growing categories, underserved regions, products with strong ratings that could expand, customer acquisition trends.

### THREATS (External Negatives)
List 6-8 threats. Examples: high return rates signaling quality issues, customer dissatisfaction patterns, revenue concentration risks, market saturation signals.

### SWOT Summary Matrix
Create a brief 2x2 matrix summary showing the most critical point in each quadrant.

### Strategic Implications
Based on the SWOT, what are the 3 most important strategic priorities?

Use markdown formatting. Each point must reference specific products, regions, or data.
{self._fmt_additional(data)}"""

        return self.call_llm(system_prompt, user_prompt, max_tokens=3000)
