# app/intelligence/analytics/constants.py

SEGMENT_LABELS = {
    "MASS_MARKET": "Standard",
    "MASS_AFFLUENT": "Premium",
    "AFFLUENT": "Premium",
    "HIGH_NET_WORTH": "High Value"
}

INCOME_BANDS = [
    (None, 74999, "Below ₹75,000"),
    (75000, 125000, "₹75,000–₹1,25,000"),
    (125001, None, "Above ₹1,25,000")
]

RISK_LEVELS = (
    (30, "Low", "LOW"),
    (60, "Medium", "MEDIUM"),
    (80, "High", "HIGH"),
    (float("inf"), "Critical", "CRITICAL"),
)


def get_risk_label(score: float | None) -> str | None:
    if score is None:
        return None
    for upper_bound, label, _ in RISK_LEVELS:
        if score < upper_bound:
            return label
    return None


def get_risk_code(score: float | None) -> str | None:
    label = get_risk_label(score)
    if label is None:
        return None
    return next(code for _, level, code in RISK_LEVELS if level == label)
