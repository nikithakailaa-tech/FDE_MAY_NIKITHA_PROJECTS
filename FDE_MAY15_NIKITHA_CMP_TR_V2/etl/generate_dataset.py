import csv
import random
from datetime import datetime, timedelta

categories = ["Billing", "Technical", "Delivery", "Product Quality", "Customer Service", "Account", "Refund", "Installation"]
priorities = ["low", "medium", "high", "critical"]
statuses = ["open", "in_progress", "resolved", "closed", "escalated", "pending"]
agents = ["Alice Johnson", "Bob Smith", "Carol White", "David Brown", "Eve Davis", "Frank Miller"]

sla_hours = {"low": 72, "medium": 48, "high": 24, "critical": 8}

random.seed(42)

records = []
base_date = datetime(2024, 1, 1)

for i in range(1, 251):
    category = random.choice(categories)
    priority = random.choice(priorities)
    status = random.choice(statuses)
    agent = random.choice(agents)

    created_at = base_date + timedelta(days=random.randint(0, 500), hours=random.randint(0, 23))
    sla_limit = sla_hours[priority]

    if status in ["resolved", "closed"]:
        resolution_hours = random.randint(1, sla_limit * 2)
        resolved_at = created_at + timedelta(hours=resolution_hours)
        sla_breached = resolution_hours > sla_limit
    else:
        resolution_hours = None
        resolved_at = None
        elapsed = (datetime(2025, 6, 1) - created_at).total_seconds() / 3600
        sla_breached = elapsed > sla_limit

    records.append({
        "complaint_id": i,
        "title": f"Complaint #{i} - {category} Issue",
        "category": category,
        "priority": priority,
        "status": status,
        "agent": agent,
        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "resolved_at": resolved_at.strftime("%Y-%m-%d %H:%M:%S") if resolved_at else "",
        "resolution_hours": round(resolution_hours, 2) if resolution_hours else "",
        "sla_limit_hours": sla_limit,
        "sla_breached": sla_breached
    })

with open("dataset/complaints_dataset.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=records[0].keys())
    writer.writeheader()
    writer.writerows(records)

print(f"Generated {len(records)} records -> dataset/complaints_dataset.csv")
