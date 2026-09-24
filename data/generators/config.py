from dataclasses import dataclass


@dataclass
class GeneratorConfig:
    customers: int = 100
    accounts_per_customer: int = 2
    transactions_per_account: int = 50
    behaviour_events_per_customer: int = 20
    fraud_rate: float = 0.02