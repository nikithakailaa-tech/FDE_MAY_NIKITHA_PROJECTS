from .base import BaseAgent


class MarketResearchAgent(BaseAgent):
    def __init__(self, client, model="gpt-4o-mini"):
        super().__init__(client, "Market Research Agent", "Market Intelligence Analyst", model)

    def analyze(self, shared_context: dict) -> str:
        data = shared_context["data"]
        prior = shared_context.get("results", {})
        summary = data.get("summary", {})

        sales_insights = prior.get("Sales Analysis Agent", "")

        system_prompt = (
            "You are a Market Intelligence Analyst specializing in technology product markets. "
            "Analyze available data to produce a comprehensive Market Research Summary covering "
            "market size, trends, growth opportunities, and segment analysis. "
            "Use markdown formatting. Be specific and data-driven."
        )

        user_prompt = f"""Produce a comprehensive Market Research Summary using all available data.

## BUSINESS METRICS
{self._fmt_summary(summary)}

## SALES PERFORMANCE DATA
{data.get('product_stats_text', '')}

## CATEGORY PERFORMANCE
{data.get('category_stats_text', '')}

## MONTHLY TRENDS
{data.get('monthly_trends_text', '')}

## REGIONAL DATA
{data.get('region_stats_text', '')}

## SALES ANALYSIS CONTEXT
{sales_insights[:1000] if sales_insights else ''}

{self._fmt_additional(data)}

Write a comprehensive Market Research Summary with these sections:

### 1. Market Overview
Summarize the total addressable market based on available revenue and unit data. Identify which product categories are growing fastest.

### 2. Market Segment Analysis
For each category (Wearables, Electronics, Accessories, Audio, Smart Home):
- Market size (revenue contribution)
- Growth trajectory (based on monthly trends)
- Profit profile
- Customer satisfaction signal

### 3. Demand Trends
Identify growing and declining demand signals:
- Which products are gaining traction?
- Which are showing saturation signals?
- Seasonal or monthly patterns observed

### 4. Regional Market Insights
- Which regions are the most developed markets?
- Which regions show the most growth potential?
- Regional preferences and patterns

### 5. Customer Acquisition Trends
- New customer acquisition rates by product/region
- Which products are best at acquiring new customers?
- Customer lifetime value signals

### 6. Market Opportunities
Identify 5 specific market opportunities based on data gaps, high-growth segments, or underserved regions.

### 7. Market Risks
Identify 4 market risks including saturation, return rate trends, and regional concentration.

### 8. Market Research Conclusions
Summary of the 5 most important market intelligence findings that should inform product strategy.

Use markdown with clear headers, bullet points, and reference specific data throughout."""

        return self.call_llm(system_prompt, user_prompt, max_tokens=3000)
