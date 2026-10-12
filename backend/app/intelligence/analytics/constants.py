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

def get_risk_label(score: float | None) -> str | None:
    if score is None:
        return None
    if score < 30:
        return "Low"
    if score < 60:
        return "Medium"
    if score < 80:
        return "High"
    return "Critical"


def get_risk_code(score: float | None) -> str | None:
    if score is None:
        return None
    if score < 30:
        return "LOW"
    if score < 60:
        return "MEDIUM"
    if score < 80:
        return "HIGH"
    return "CRITICAL"
