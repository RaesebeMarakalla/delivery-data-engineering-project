"""Generate business insights and export a small dashboard from processed delivery data."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROCESSED_DIR = ROOT / "data" / "processed"
DEFAULT_REPORT_DIR = ROOT / "reports"


def load_processed_data(processed_dir: Path | str = DEFAULT_PROCESSED_DIR) -> dict[str, pd.DataFrame]:
    """Load the processed CSV files used for KPI generation."""
    processed_dir = Path(processed_dir)
    tables: dict[str, pd.DataFrame] = {}
    for file_name in [
        "customers.csv",
        "products.csv",
        "orders.csv",
        "order_items.csv",
        "drivers.csv",
        "vehicles.csv",
        "deliveries.csv",
    ]:
        path = processed_dir / file_name
        if not path.exists():
            raise FileNotFoundError(f"Missing processed data file: {path}")
        tables[file_name.replace(".csv", "")] = pd.read_csv(path)
    return tables


def calculate_business_insights(tables: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Compute key business KPIs from the cleaned delivery dataset."""
    orders = tables["orders"].copy()
    customers = tables["customers"].copy()
    products = tables["products"].copy()
    order_items = tables["order_items"].copy()
    deliveries = tables["deliveries"].copy()

    for frame in (orders, customers, products, order_items, deliveries):
        for column in frame.columns:
            if "date" in column.lower():
                frame[column] = pd.to_datetime(frame[column], errors="coerce")

    revenue_by_category = (
        order_items.merge(products[["product_id", "product_name", "category", "price"]], on="product_id")
        .assign(line_revenue=lambda df: df["quantity"] * df["price"])
        .groupby("category", as_index=False)["line_revenue"]
        .sum()
        .rename(columns={"line_revenue": "category_revenue"})
        .sort_values("category_revenue", ascending=False)
    )

    total_revenue = float(revenue_by_category["category_revenue"].sum())
    avg_order_value = float(orders["total_amount"].mean()) if not orders.empty else 0.0
    total_orders = int(len(orders))
    delivered_orders = int((deliveries["status"] == "Delivered").sum())
    total_deliveries = int(len(deliveries))
    delivery_success_rate = (delivered_orders / total_deliveries * 100) if total_deliveries else 0.0

    revenue_by_city = (
        orders.merge(customers[["customer_id", "city"]], on="customer_id")
        .merge(order_items, on="order_id")
        .merge(products[["product_id", "category", "price"]], on="product_id")
        .assign(line_revenue=lambda df: df["quantity"] * df["price"])
        .groupby(["city", "category"], as_index=False)["line_revenue"]
        .sum()
        .rename(columns={"line_revenue": "revenue"})
        .sort_values(["city", "revenue"], ascending=[True, False])
    )

    customer_spend = (
        orders.merge(customers[["customer_id", "name", "city"]], on="customer_id")
        .groupby(["customer_id", "name", "city"], as_index=False)["total_amount"]
        .sum()
        .rename(columns={"total_amount": "total_spent"})
        .sort_values("total_spent", ascending=False)
    )

    delivery_per_driver = (
        deliveries.merge(tables["drivers"][["driver_id", "name"]], on="driver_id")
        .groupby(["driver_id", "name"], as_index=False)["delivery_id"]
        .count()
        .rename(columns={"delivery_id": "delivery_count"})
        .sort_values("delivery_count", ascending=False)
    )

    best_category = revenue_by_category.iloc[0].to_dict() if not revenue_by_category.empty else {}
    top_customer = customer_spend.iloc[0].to_dict() if not customer_spend.empty else {}
    top_driver = delivery_per_driver.iloc[0].to_dict() if not delivery_per_driver.empty else {}

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "avg_order_value": avg_order_value,
        "total_deliveries": total_deliveries,
        "delivered_orders": delivered_orders,
        "delivery_success_rate": delivery_success_rate,
        "revenue_by_category": revenue_by_category,
        "revenue_by_city": revenue_by_city,
        "customer_spend": customer_spend,
        "delivery_per_driver": delivery_per_driver,
        "best_category": best_category,
        "top_customer": top_customer,
        "top_driver": top_driver,
    }


def save_summary_markdown(insights: dict[str, Any], output_path: Path) -> None:
    """Write a concise markdown report for the dashboard."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    category = insights["best_category"]
    customer = insights["top_customer"]
    driver = insights["top_driver"]

    summary = f"""# Delivery Business Summary

## KPIs
- Total orders: {insights['total_orders']}
- Total revenue: $ {insights['total_revenue']:,.2f}
- Average order value: $ {insights['avg_order_value']:,.2f}
- Total deliveries: {insights['total_deliveries']}
- Delivered orders: {insights['delivered_orders']}
- Delivery success rate: {insights['delivery_success_rate']:.1f}%

## Top performers
- Top revenue category: {category.get('category', 'N/A')} ($ {category.get('category_revenue', 0):,.2f})
- Top customer: {customer.get('name', 'N/A')} from {customer.get('city', 'N/A')} ($ {customer.get('total_spent', 0):,.2f})
- Top driver by delivery count: {driver.get('name', 'N/A')} ({driver.get('delivery_count', 0)} deliveries)

## Revenue by category
| Category | Revenue |
| --- | ---: |
"""

    for _, row in insights["revenue_by_category"].iterrows():
        summary += f"| {row['category']} | $ {row['category_revenue']:,.2f} |\n"

    output_path.write_text(summary, encoding="utf-8")


def save_category_chart(revenue_by_category: pd.DataFrame, output_path: Path) -> None:
    """Generate a simple bar chart showing category revenue."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    categories = revenue_by_category["category"].tolist()
    revenue = revenue_by_category["category_revenue"].tolist()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(categories, revenue, color=["#4c78a8", "#f58518", "#54a24b", "#e45756"])
    ax.set_title("Revenue by Product Category")
    ax.set_xlabel("Category")
    ax.set_ylabel("Revenue")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=DEFAULT_PROCESSED_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    args = parser.parse_args()

    tables = load_processed_data(args.processed_dir)
    insights = calculate_business_insights(tables)
    save_summary_markdown(insights, args.report_dir / "business_summary.md")
    save_category_chart(insights["revenue_by_category"], args.report_dir / "revenue_by_category.png")

    print(f"Total orders: {insights['total_orders']}")
    print(f"Total revenue: $ {insights['total_revenue']:,.2f}")
    print(f"Average order value: $ {insights['avg_order_value']:,.2f}")
    print(f"Delivery success rate: {insights['delivery_success_rate']:.1f}%")
    print(f"Saved summary to {args.report_dir / 'business_summary.md'}")
    print(f"Saved chart to {args.report_dir / 'revenue_by_category.png'}")


if __name__ == "__main__":
    main()
