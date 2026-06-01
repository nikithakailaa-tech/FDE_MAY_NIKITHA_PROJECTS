from .base import BaseAgent


class SalesAnalysisAgent(BaseAgent):
    def __init__(self, client, model="gpt-4o-mini"):
        super().__init__(client, "Sales Analysis Agent", "Sales Performance Analyst", model)

    def analyze(self, shared_context: dict) -> str:
        data = shared_context["data"]
        summary = data.get("summary", {})

        system_prompt = (
            "You are an expert Sales Performance Analyst. Analyze sales data and produce a "
            "detailed, data-driven report in markdown. Include specific numbers, percentages, "
            "and trends. Be precise and business-focused."
        )

        user_prompt = f"""Analyze the following sales data and write a comprehensive Sales Analysis Report.

## KEY METRICS
{self._fmt_summary(summary)}

## PRODUCT PERFORMANCE
{data.get('product_stats_text', '')}

## REGION PERFORMANCE
{data.get('region_stats_text', '')}

## MONTHLY TRENDS
{data.get('monthly_trends_text', '')}

## CATEGORY PERFORMANCE
{data.get('category_stats_text', '')}

Write a detailed Sales Analysis Report with these sections:

### 1. Revenue & Profit Overview
Summarize total performance. Identify the top 3 revenue drivers and top 3 profit contributors.

### 2. Product Performance Deep Dive
For each product, assess: revenue contribution, profit margin, marketing ROI, and trend. Rank by overall performance.

### 3. Regional Analysis
Which regions are over/under performing? Identify regional opportunities and risks.

### 4. Category Analysis
Compare category-level performance. Which category has the best margin? Best growth?

### 5. Monthly Trend Analysis
Identify month-over-month growth patterns. Any acceleration or deceleration? Seasonal signals?

### 6. Marketing Efficiency
Which products have the best and worst marketing ROI? Where should budget be reallocated?

### 7. Revenue at Risk
Identify products with high return rates or declining trends that put revenue at risk.

### 8. Growth Opportunities (Top 5)
Specific opportunities to increase revenue or improve margins. Reference actual data.

Use markdown formatting with clear headers, bullet points, and specific numbers.
{self._fmt_additional(data)}"""

        return self.call_llm(system_prompt, user_prompt, max_tokens=3000)
