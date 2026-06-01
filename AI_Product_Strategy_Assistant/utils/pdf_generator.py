import re
from datetime import datetime
from fpdf import FPDF


def _clean(text: str) -> str:
    """Strip markdown and non-ASCII chars for PDF output."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"#{1,6}\s+", "", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    text = re.sub(r"---+", "-" * 40, text)
    replacements = {
        "’": "'", "‘": "'", "“": '"', "”": '"',
        "–": "-", "—": "--", "•": "*", "…": "...",
        " ": " ", "♥": "*", "●": "*",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("ascii", errors="ignore").decode("ascii")


class _PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "AI-Powered Product Strategy Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()} | Confidential", align="C")


SECTION_TITLES = {
    "Customer Feedback Agent": "1. Customer Insights Report",
    "Sales Analysis Agent": "2. Sales Performance Analysis",
    "SWOT Analysis Agent": "3. SWOT Analysis",
    "Feature Prioritization Agent": "4. Feature Prioritization",
    "Strategy Recommendation Agent": "5. Strategic Recommendations",
    "Executive Report Agent": "6. Executive Summary",
}


def generate_pdf(results: dict, summary: dict) -> bytes:
    pdf = _PDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Cover Page
    pdf.add_page()
    pdf.set_fill_color(40, 40, 80)
    pdf.rect(0, 0, 210, 297, "F")

    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 28)
    pdf.ln(50)
    pdf.multi_cell(0, 14, "AI-Powered Product\nStrategy Report", align="C")

    pdf.ln(8)
    pdf.set_font("Helvetica", size=14)
    pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%B %d, %Y')}", align="C", new_x="LMARGIN", new_y="NEXT")

    if summary:
        pdf.ln(12)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "BUSINESS OVERVIEW", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        pdf.set_font("Helvetica", size=11)
        metrics = [
            f"Period: {summary.get('date_range', 'N/A')}",
            f"Total Revenue: ${summary.get('total_revenue_usd', 0):,.2f}",
            f"Total Profit: ${summary.get('total_profit_usd', 0):,.2f}  |  Margin: {summary.get('overall_profit_margin_pct', 0):.1f}%",
            f"Total Units Sold: {summary.get('total_units_sold', 0):,}",
            f"Avg Customer Rating: {summary.get('avg_customer_rating', 0):.1f} / 5.0",
            f"Total Returns: {summary.get('total_returns', 0):,}  ({summary.get('return_rate_pct', 0):.1f}% rate)",
            f"Marketing Spend: ${summary.get('total_marketing_spend_usd', 0):,.2f}",
        ]
        for m in metrics:
            pdf.cell(0, 7, _clean(m), align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(180, 180, 220)
    pdf.set_font("Helvetica", "I", 10)
    pdf.ln(20)
    products = summary.get("products", [])
    pdf.multi_cell(0, 7, _clean(f"Products: {', '.join(products)}"), align="C")

    # Section pages
    for agent_name, content in results.items():
        if not content:
            continue
        title = SECTION_TITLES.get(agent_name, agent_name)

        pdf.add_page()
        pdf.set_text_color(40, 40, 80)
        pdf.set_fill_color(240, 242, 255)
        pdf.rect(0, 25, 210, 18, "F")
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_y(28)
        pdf.cell(0, 12, _clean(title), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        pdf.set_text_color(50, 50, 50)
        pdf.set_font("Helvetica", size=9)

        for line in _clean(content).splitlines():
            stripped = line.strip()
            if not stripped:
                pdf.ln(2)
                continue
            # Detect headers (lines starting with numbers or all caps)
            if re.match(r"^(\d+\.|#{1,3}|[A-Z][A-Z\s]{4,}:?$)", stripped):
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(40, 40, 100)
                pdf.multi_cell(0, 6, stripped)
                pdf.set_font("Helvetica", size=9)
                pdf.set_text_color(50, 50, 50)
            elif stripped.startswith(("- ", "* ", "+ ")):
                pdf.set_x(18)
                pdf.multi_cell(0, 5, stripped)
            else:
                pdf.multi_cell(0, 5, stripped)

    return bytes(pdf.output())
