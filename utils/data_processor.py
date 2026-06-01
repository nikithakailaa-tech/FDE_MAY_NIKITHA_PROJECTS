import pandas as pd
from io import StringIO


def process_files(uploaded_files) -> dict:
    context = {
        "has_csv": False,
        "has_text": False,
        "summary": {},
        "product_stats_text": "",
        "region_stats_text": "",
        "monthly_trends_text": "",
        "category_stats_text": "",
        "reviews_text": "",
        "additional_text": "",
        "df": None,
    }

    for file in uploaded_files:
        name = file.name.lower()
        if name.endswith(".csv"):
            file.seek(0)
            df, summary = _process_csv(file)
            context["df"] = df
            context["summary"] = summary
            context["has_csv"] = True
            context["product_stats_text"] = _fmt_product_stats(df)
            context["region_stats_text"] = _fmt_region_stats(df)
            context["monthly_trends_text"] = _fmt_monthly_trends(df)
            context["category_stats_text"] = _fmt_category_stats(df)
            context["reviews_text"] = _fmt_reviews(df)
        elif name.endswith(".pdf"):
            text = _extract_pdf(file)
            context["additional_text"] += f"\n\n[Document: {file.name}]\n{text}"
            context["has_text"] = True
        elif name.endswith((".txt", ".md")):
            file.seek(0)
            text = file.read().decode("utf-8", errors="ignore")
            context["additional_text"] += f"\n\n[Document: {file.name}]\n{text}"
            context["has_text"] = True

    return context


def _process_csv(file) -> tuple:
    df = pd.read_csv(file)
    df["Date"] = pd.to_datetime(df["Date"])

    total_rev = df["Revenue_USD"].sum()
    total_profit = df["Profit_USD"].sum()
    total_units = df["Units_Sold"].sum()
    total_returns = df["Returns"].sum()

    summary = {
        "total_records": len(df),
        "date_range": f"{df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}",
        "products": sorted(df["Product_Name"].unique().tolist()),
        "categories": sorted(df["Category"].unique().tolist()),
        "regions": sorted(df["Region"].unique().tolist()),
        "total_revenue_usd": round(total_rev, 2),
        "total_profit_usd": round(total_profit, 2),
        "total_cost_usd": round(df["Cost_USD"].sum(), 2),
        "total_units_sold": int(total_units),
        "avg_customer_rating": round(df["Customer_Rating"].mean(), 2),
        "total_returns": int(total_returns),
        "total_new_customers": int(df["New_Customers"].sum()),
        "total_marketing_spend_usd": round(df["Marketing_Spend_USD"].sum(), 2),
        "overall_profit_margin_pct": round(total_profit / total_rev * 100, 1) if total_rev else 0,
        "return_rate_pct": round(total_returns / total_units * 100, 2) if total_units else 0,
    }

    return df, summary


def _fmt_product_stats(df: pd.DataFrame) -> str:
    agg = df.groupby("Product_Name").agg(
        Units_Sold=("Units_Sold", "sum"),
        Revenue_USD=("Revenue_USD", "sum"),
        Profit_USD=("Profit_USD", "sum"),
        Cost_USD=("Cost_USD", "sum"),
        Marketing_Spend_USD=("Marketing_Spend_USD", "sum"),
        Customer_Rating=("Customer_Rating", "mean"),
        Returns=("Returns", "sum"),
        New_Customers=("New_Customers", "sum"),
    ).round(2)

    lines = ["PRODUCT PERFORMANCE ANALYSIS:", "=" * 60]
    for product, row in agg.iterrows():
        margin = round(row["Profit_USD"] / row["Revenue_USD"] * 100, 1) if row["Revenue_USD"] else 0
        ret_rate = round(row["Returns"] / row["Units_Sold"] * 100, 1) if row["Units_Sold"] else 0
        roi = round(row["Profit_USD"] / row["Marketing_Spend_USD"] * 100, 1) if row["Marketing_Spend_USD"] else 0
        lines.append(f"\n{product} ({df[df['Product_Name']==product]['Category'].iloc[0]}):")
        lines.append(f"  Units Sold: {int(row['Units_Sold']):,}")
        lines.append(f"  Revenue: ${row['Revenue_USD']:,.2f}  |  Profit: ${row['Profit_USD']:,.2f} ({margin}% margin)")
        lines.append(f"  Marketing Spend: ${row['Marketing_Spend_USD']:,.2f}  |  Marketing ROI: {roi}%")
        lines.append(f"  Avg Rating: {row['Customer_Rating']:.1f}/5.0  |  Returns: {int(row['Returns'])} ({ret_rate}%)")
        lines.append(f"  New Customers: {int(row['New_Customers']):,}")
    return "\n".join(lines)


def _fmt_region_stats(df: pd.DataFrame) -> str:
    agg = df.groupby("Region").agg(
        Units_Sold=("Units_Sold", "sum"),
        Revenue_USD=("Revenue_USD", "sum"),
        Profit_USD=("Profit_USD", "sum"),
        Customer_Rating=("Customer_Rating", "mean"),
        Returns=("Returns", "sum"),
        New_Customers=("New_Customers", "sum"),
    ).round(2)

    lines = ["\nREGION PERFORMANCE ANALYSIS:", "=" * 60]
    for region, row in agg.iterrows():
        margin = round(row["Profit_USD"] / row["Revenue_USD"] * 100, 1) if row["Revenue_USD"] else 0
        lines.append(f"\n{region} Region:")
        lines.append(f"  Revenue: ${row['Revenue_USD']:,.2f}  |  Profit: ${row['Profit_USD']:,.2f} ({margin}% margin)")
        lines.append(f"  Units Sold: {int(row['Units_Sold']):,}  |  Avg Rating: {row['Customer_Rating']:.1f}/5.0")
        lines.append(f"  Returns: {int(row['Returns'])}  |  New Customers: {int(row['New_Customers']):,}")
    return "\n".join(lines)


def _fmt_monthly_trends(df: pd.DataFrame) -> str:
    df = df.copy()
    df["Month"] = df["Date"].dt.to_period("M")
    monthly = df.groupby("Month").agg(
        Revenue_USD=("Revenue_USD", "sum"),
        Profit_USD=("Profit_USD", "sum"),
        Units_Sold=("Units_Sold", "sum"),
        Customer_Rating=("Customer_Rating", "mean"),
        Returns=("Returns", "sum"),
    ).round(2)

    lines = ["\nMONTHLY SALES TRENDS:", "=" * 60]
    prev_rev = None
    for month, row in monthly.iterrows():
        margin = round(row["Profit_USD"] / row["Revenue_USD"] * 100, 1) if row["Revenue_USD"] else 0
        growth = ""
        if prev_rev and prev_rev > 0:
            pct = round((row["Revenue_USD"] - prev_rev) / prev_rev * 100, 1)
            growth = f" ({'+' if pct >= 0 else ''}{pct}% MoM)"
        lines.append(f"\n{month}{growth}:")
        lines.append(f"  Revenue: ${row['Revenue_USD']:,.2f}  |  Profit: ${row['Profit_USD']:,.2f} ({margin}% margin)")
        lines.append(f"  Units Sold: {int(row['Units_Sold']):,}  |  Avg Rating: {row['Customer_Rating']:.1f}/5.0  |  Returns: {int(row['Returns'])}")
        prev_rev = row["Revenue_USD"]
    return "\n".join(lines)


def _fmt_category_stats(df: pd.DataFrame) -> str:
    agg = df.groupby("Category").agg(
        Units_Sold=("Units_Sold", "sum"),
        Revenue_USD=("Revenue_USD", "sum"),
        Profit_USD=("Profit_USD", "sum"),
        Customer_Rating=("Customer_Rating", "mean"),
        Marketing_Spend_USD=("Marketing_Spend_USD", "sum"),
    ).round(2)

    lines = ["\nCATEGORY PERFORMANCE:", "=" * 60]
    for cat, row in agg.iterrows():
        margin = round(row["Profit_USD"] / row["Revenue_USD"] * 100, 1) if row["Revenue_USD"] else 0
        rev_share = round(row["Revenue_USD"] / df["Revenue_USD"].sum() * 100, 1)
        lines.append(f"\n{cat}:")
        lines.append(f"  Revenue: ${row['Revenue_USD']:,.2f} ({rev_share}% of total)  |  Margin: {margin}%")
        lines.append(f"  Units Sold: {int(row['Units_Sold']):,}  |  Avg Rating: {row['Customer_Rating']:.1f}/5.0")
        lines.append(f"  Marketing Spend: ${row['Marketing_Spend_USD']:,.2f}")
    return "\n".join(lines)


def _fmt_reviews(df: pd.DataFrame) -> str:
    lines = ["\nCUSTOMER REVIEWS BY PRODUCT:", "=" * 60]
    for product in df["Product_Name"].unique():
        pdf = df[df["Product_Name"] == product][["Customer_Rating", "Review"]].head(6)
        avg_rating = pdf["Customer_Rating"].mean()
        lines.append(f"\n{product} (avg {avg_rating:.1f}/5.0):")
        for _, row in pdf.iterrows():
            lines.append(f"  [{row['Customer_Rating']}] {row['Review']}")
    return "\n".join(lines)


def _extract_pdf(file) -> str:
    try:
        import PyPDF2
        file.seek(0)
        reader = PyPDF2.PdfReader(file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        return f"[Could not extract PDF text: {e}]"
