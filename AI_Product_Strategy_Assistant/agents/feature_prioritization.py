from .base import BaseAgent


class FeaturePrioritizationAgent(BaseAgent):
    def __init__(self, client, model="gpt-4o-mini"):
        super().__init__(client, "Feature Prioritization Agent", "Product Manager & Prioritization Specialist", model)

    def analyze(self, shared_context: dict) -> str:
        data = shared_context["data"]
        prior = shared_context.get("results", {})
        summary = data.get("summary", {})

        customer_insights = prior.get("Customer Feedback Agent", "")
        sales_insights = prior.get("Sales Analysis Agent", "")
        swot_insights = prior.get("SWOT Analysis Agent", "")

        system_prompt = (
            "You are an expert Product Manager specializing in feature prioritization using "
            "frameworks like RICE, ICE, and MoSCoW. You use data from customer feedback, sales "
            "performance, and strategic analysis to prioritize product improvements and features. "
            "Produce structured, scored recommendations in markdown."
        )

        user_prompt = f"""Using all available data and insights, produce a comprehensive Feature Prioritization Report.

## BUSINESS METRICS
{self._fmt_summary(summary)}

## CUSTOMER PAIN POINTS & FEEDBACK
{customer_insights[:1200] if customer_insights else data.get('reviews_text', '')[:800]}

## SALES PERFORMANCE DATA
{sales_insights[:1200] if sales_insights else data.get('product_stats_text', '')[:800]}

## STRATEGIC CONTEXT (SWOT)
{swot_insights[:800] if swot_insights else ''}

## PRODUCT & REGION DATA
{data.get('product_stats_text', '')}

Write a comprehensive Feature Prioritization Report with these sections:

### 1. Prioritization Framework
Briefly explain the scoring approach (use RICE: Reach, Impact, Confidence, Effort).

### 2. Product Investment Priority Matrix
For each product, assign a priority score (1-10) and categorize as:
- **Invest & Scale**: High performers to accelerate
- **Fix & Improve**: Underperformers with potential
- **Maintain**: Steady performers
- **Review & Decide**: Questionable ROI

For each, include: Current Score, Priority Score (1-10), Key Action Needed.

### 3. Top Feature Improvement Recommendations
List the top 8 specific improvements/features ranked by priority. For each include:
- Feature/Improvement name
- Target product(s)
- Business justification (reference data)
- RICE Score: Reach | Impact | Confidence | Effort
- Expected outcome

### 4. Quick Wins (High Impact, Low Effort)
List 3-4 improvements that can be done quickly for immediate gains.

### 5. Strategic Investments (High Impact, High Effort)
List 2-3 major investments worth prioritizing for long-term growth.

### 6. Deprioritized Items
What should NOT be prioritized right now and why?

### 7. 30-60-90 Day Priority Roadmap
Organize the top priorities into a 30/60/90-day action plan.

Use markdown with clear headers, bullet points, and specific metrics.
{self._fmt_additional(data)}"""

        return self.call_llm(system_prompt, user_prompt, max_tokens=3500)
