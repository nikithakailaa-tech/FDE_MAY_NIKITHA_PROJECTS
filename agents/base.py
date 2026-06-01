from openai import OpenAI


class BaseAgent:
    def __init__(self, client: OpenAI, name: str, role: str, model: str = "gpt-4o-mini"):
        self.client = client
        self.name = name
        self.role = role
        self.model = model

    def call_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 2500) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"⚠️ Error in {self.name}: {str(e)}"

    def analyze(self, shared_context: dict) -> str:
        raise NotImplementedError(f"{self.name} must implement analyze()")

    def _fmt_additional(self, data: dict) -> str:
        txt = data.get("additional_text", "").strip()
        if not txt:
            return ""
        return f"\n\n## ADDITIONAL UPLOADED DOCUMENTS (PDFs / Text Files)\n{txt[:3000]}\n"

    def _fmt_summary(self, summary: dict) -> str:
        return (
            f"- Period: {summary.get('date_range', 'N/A')}\n"
            f"- Products: {', '.join(summary.get('products', []))}\n"
            f"- Categories: {', '.join(summary.get('categories', []))}\n"
            f"- Regions: {', '.join(summary.get('regions', []))}\n"
            f"- Total Revenue: ${summary.get('total_revenue_usd', 0):,.2f}\n"
            f"- Total Profit: ${summary.get('total_profit_usd', 0):,.2f}\n"
            f"- Profit Margin: {summary.get('overall_profit_margin_pct', 0):.1f}%\n"
            f"- Total Units Sold: {summary.get('total_units_sold', 0):,}\n"
            f"- Avg Customer Rating: {summary.get('avg_customer_rating', 0):.1f}/5.0\n"
            f"- Total Returns: {summary.get('total_returns', 0):,} ({summary.get('return_rate_pct', 0):.1f}% rate)\n"
            f"- Marketing Spend: ${summary.get('total_marketing_spend_usd', 0):,.2f}\n"
            f"- New Customers: {summary.get('total_new_customers', 0):,}"
        )
