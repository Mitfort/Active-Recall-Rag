from datetime import datetime, timedelta
from src.scheduler import calculate_retrievability

last_review = datetime.now() - timedelta(days=5)

r = calculate_retrievability(
    last_review=last_review,
    stability_days=10
)

print(r)