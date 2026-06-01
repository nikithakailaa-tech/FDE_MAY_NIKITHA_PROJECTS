from .base import BaseAgent


class CompetitorAnalysisAgent(BaseAgent):
    def __init__(self, client, model="gpt-4o-mini"):
        super().__init__(client, "Competitor Analysis Agent", "Competitive Intelligence Specialist", model)

    def analyze(self, shared_context: dict) -> str:
        data = shared_context["data"]
        prior = shared_context.get("results", {})
        summary = data.get("summary", {})

        market_insights = prior.get("Market Research Agent", "")
        customer_insights = prior.get("Customer Feedback Agent", "")

        system_prompt = (
            "You are a Competitive Intelligence Specialist. Analyze product performance data "
            "to assess competitive positioning, identify competitive gaps, and recommend "
            "differentiation strategies. When competitor documents are uploaded, use them. "
            "Otherwise, derive competitive insights from internal performance data and customer feedback. "
            "Use markdown formatting."
        )

        user_prompt = f"""Produce a comprehensive Competitor Analysis Report using all available data.

## BUSINESS METRICS
{self._fmt_summary(summary)}

## PRODUCT PERFORMANCE (Internal Competitive Baseline)
{data.get('product_stats_text', '')}

## CUSTOMER FEEDBACK (Competitive Signals)
{data.get('reviews_text', '')[:1500]}

## MARKET RESEARCH CONTEXT
{market_insights[:800] if market_insights else ''}

## CUSTOMER INSIGHTS CONTEXT
{customer_insights[:800] if customer_insights else ''}

{self._fmt_additional(data)}

Write a comprehensive Competitor Analysis Report with these sections:

### 1. Competitive Landscape Overview
Describe the competitive environment for each product category (Wearables, Electronics, Accessories, Audio, Smart Home). Use internal performance data as benchmarks and any uploaded competitor information.

### 2. Product-Level Competitive Assessment
For each product, assess:
- **Competitive Strength**: Based on rating, margin, return rate, and customer sentiment
- **Competitive Vulnerability**: Areas where competitors could win
- **Differentiation Factor**: What makes this product stand out

### 3. Customer Sentiment vs. Competitor Signals
Analyze what customer reviews reveal about competitive gaps:
- Pain points that competitors could exploit
- Features customers praise that are competitive advantages

### 4. Price-Value Competitive Analysis
Based on revenue per unit and profit margins, assess pricing competitiveness:
- Which products appear premium-positioned?
- Which are value-positioned?
- Where is pricing pressure likely highest?

### 5. Feature Gap Analysis
Based on customer feedback themes, identify:
- Features customers want that appear missing
- Quality gaps competitors could address
- Support/service gaps mentioned in reviews

### 6. Regional Competitive Dynamics
Which regions show competitive pressure signals (high returns, low ratings, low new customer acquisition)?

### 7. Competitive Positioning Matrix
Create a 2x2 positioning assessment:
- **Market Leaders**: High revenue + high satisfaction
- **Stars**: Growing fast but lower margins
- **Cash Cows**: High margin but slower growth
- **At Risk**: Low satisfaction + high returns

### 8. Strategic Competitive Recommendations
Top 5 actions to strengthen competitive position, with specific product and data references.

Use markdown with clear headers, bullet points, and specific data."""

        return self.call_llm(system_prompt, user_prompt, max_tokens=3000)
