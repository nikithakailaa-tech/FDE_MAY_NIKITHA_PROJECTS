from openai import OpenAI
from agents.customer_feedback import CustomerFeedbackAgent
from agents.sales_analysis import SalesAnalysisAgent
from agents.market_research import MarketResearchAgent
from agents.competitor_analysis import CompetitorAnalysisAgent
from agents.swot import SWOTAgent
from agents.feature_prioritization import FeaturePrioritizationAgent
from agents.opportunity_analysis import OpportunityAnalysisAgent
from agents.strategy import StrategyAgent
from agents.executive_report import ExecutiveReportAgent


class Orchestrator:
    """Coordinates all 9 AI agents sequentially, passing shared context between them."""

    def __init__(self, client: OpenAI, model: str = "gpt-4o-mini"):
        self.client = client
        self.model = model
        self._agents = [
            CustomerFeedbackAgent(client, model),
            SalesAnalysisAgent(client, model),
            MarketResearchAgent(client, model),
            CompetitorAnalysisAgent(client, model),
            SWOTAgent(client, model),
            FeaturePrioritizationAgent(client, model),
            OpportunityAnalysisAgent(client, model),
            StrategyAgent(client, model),
            ExecutiveReportAgent(client, model),
        ]

    def get_agents(self):
        return self._agents

    def run(self, data_context: dict, progress_callback=None) -> dict:
        """
        Run all agents sequentially. Each agent receives the full data context
        plus all prior agents' results, enabling true agent collaboration.
        """
        results = {}
        shared_context = {"data": data_context, "results": results}

        for i, agent in enumerate(self._agents):
            if progress_callback:
                progress_callback(i, len(self._agents), agent.name)
            try:
                result = agent.analyze(shared_context)
            except Exception as e:
                result = f"⚠️ {agent.name} encountered an error: {str(e)}"
            results[agent.name] = result

        return results

    def chat(self, question: str, results: dict, history: list) -> str:
        """Answer user questions using all agent outputs as context."""
        context_parts = [
            f"## {name}\n{content}"
            for name, content in results.items()
            if content and not content.startswith("⚠️")
        ]
        full_context = "\n\n---\n\n".join(context_parts)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI Product Strategy Assistant with access to a comprehensive "
                    "9-agent product strategy analysis. Answer user questions based on this analysis. "
                    "Be specific — reference actual product names, numbers, and data. "
                    "Provide actionable, business-focused insights.\n\n"
                    f"FULL ANALYSIS CONTEXT:\n{full_context[:12000]}"
                ),
            }
        ]

        # Include last 8 conversation turns for context
        for msg in history[-8:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": question})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1500,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"⚠️ Error: {str(e)}"
