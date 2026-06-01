from .base import BaseAgent


class OpportunityAnalysisAgent(BaseAgent):
    def __init__(self, client, model="gpt-4o-mini"):
        super().__init__(client, "Opportunity Analysis Agent", "Product Opportunity Analyst", model)

    def analyze(self, shared_context: dict) -> str:
        data = shared_context["data"]
        prior = shared_context.get("results", {})
        summary = data.get("summary", {})

        market_insights = prior.get("Market Research Agent", "")
        competitor_insights = prior.get("Competitor Analysis Agent", "")
        customer_insights = prior.get("Customer Feedback Agent", "")
        swot_insights = prior.get("SWOT Analysis Agent", "")

        system_prompt = (
            "You are a Product Opportunity Analyst specializing in identifying, scoring, and "
            "prioritizing business opportunities. You use a rigorous scoring methodology to "
            "objectively rank opportunities. Produce structured, scored output in markdown."
        )

        user_prompt = f"""Using all available analysis, produce a comprehensive Product Opportunity Assessment with numeric scoring.

## BUSINESS METRICS
{self._fmt_summary(summary)}

## PRODUCT & MARKET DATA
{data.get('product_stats_text', '')}

## MARKET RESEARCH CONTEXT
{market_insights[:800] if market_insights else ''}

## COMPETITOR CONTEXT
{competitor_insights[:800] if competitor_insights else ''}

## CUSTOMER INSIGHTS
{customer_insights[:600] if customer_insights else ''}

## SWOT CONTEXT
{swot_insights[:600] if swot_insights else ''}

{self._fmt_additional(data)}

Write a Product Opportunity Assessment with these sections:

### 1. Opportunity Scoring Methodology
Explain the scoring formula used:
- **Market Size Score** (1-10): Based on current revenue + growth potential
- **Profitability Score** (1-10): Based on margin and ROI
- **Customer Demand Score** (1-10): Based on ratings, new customers, and sentiment
- **Competitive Advantage Score** (1-10): Based on differentiation potential
- **Feasibility Score** (1-10): Based on current capabilities and data

**Opportunity Score = (Market Size × 0.25) + (Profitability × 0.25) + (Customer Demand × 0.20) + (Competitive Advantage × 0.15) + (Feasibility × 0.15)**

### 2. Product Opportunity Scores
For each product, compute and display the opportunity score:

| Product | Market Size | Profitability | Cust. Demand | Comp. Advantage | Feasibility | **Total Score** | Priority |
|---------|------------|---------------|--------------|-----------------|-------------|-----------------|----------|

Rank from highest to lowest opportunity score.

### 3. Top 5 Product Opportunities
For each of the top 5 opportunities:
- **Opportunity**: What specifically
- **Score**: Numeric score
- **Evidence**: Data points supporting this opportunity
- **Revenue Potential**: Estimated impact
- **Time to Capture**: Short/Medium/Long term

### 4. Category Opportunities
Identify 3 category-level opportunities (e.g., expand Smart Home lineup, double down on Electronics).

### 5. Regional Expansion Opportunities
Which product+region combinations are underexploited? Score 3 specific expansion opportunities.

### 6. Customer Segment Opportunities
Based on new customer acquisition data and ratings, identify 3 customer segment opportunities.

### 7. Quick Win Opportunities (90-day)
List 3 opportunities that can be captured within 90 days with minimal investment.

### 8. Strategic Bets (12-month)
List 2 high-stakes opportunities worth significant investment for long-term advantage.

### 9. Opportunity Priority Roadmap
Organize all opportunities into a prioritized roadmap:
- **Immediate (0-3 months)**: Quick wins
- **Near-term (3-6 months)**: Medium effort opportunities
- **Strategic (6-12 months)**: Big bets

Use markdown with tables, specific scores, and data references throughout."""

        return self.call_llm(system_prompt, user_prompt, max_tokens=3500)
