from .base import BaseAgent


class CustomerFeedbackAgent(BaseAgent):
    def __init__(self, client, model="gpt-4o-mini"):
        super().__init__(client, "Customer Feedback Agent", "Customer Insights Specialist", model)

    def analyze(self, shared_context: dict) -> str:
        data = shared_context["data"]
        summary = data.get("summary", {})

        system_prompt = (
            "You are an expert Customer Insights Specialist. Analyze customer feedback data "
            "and produce a detailed, structured report in markdown. Use specific numbers and "
            "product names from the data provided. Be actionable and specific."
        )

        user_prompt = f"""Analyze the following customer data and write a comprehensive Customer Insights Report.

## KEY METRICS
{self._fmt_summary(summary)}

## PRODUCT PERFORMANCE
{data.get('product_stats_text', '')}

## CUSTOMER REVIEWS
{data.get('reviews_text', '')}

Write a detailed Customer Insights Report with these sections:

### 1. Overall Sentiment Summary
Categorize overall sentiment (positive/neutral/negative split) and explain what drives it.

### 2. Product Satisfaction Ranking
Rank all products from highest to lowest customer satisfaction. Include ratings and key differentiators.

### 3. Top Customer Pain Points
List the top 5 recurring complaints with which products are most affected.

### 4. Customer Delight Factors
What are customers praising? List the top 5 positive themes.

### 5. Return Rate Risk Analysis
Identify products with concerning return rates. Explain probable root causes based on reviews.

### 6. Segment Insights
Are there patterns by product category (Wearables, Electronics, etc.)?

### 7. Actionable Recommendations (Top 5)
Specific, prioritized actions to improve customer satisfaction scores. Each recommendation must reference specific products and data.

Use markdown formatting with clear headers and bullet points.
{self._fmt_additional(data)}"""

        return self.call_llm(system_prompt, user_prompt, max_tokens=3000)
