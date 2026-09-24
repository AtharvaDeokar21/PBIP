# PBIP Database

Supabase PostgreSQL is the shared transactional database.

## Domain groups

- Identity: users, customers
- Banking: accounts, transactions, payees, transfers, billers, bill_payments
- Products: loan_products, loan_applications, investment_products, customer_investments, insurance_products
- Intelligence: behaviour_events, customer_risk_profiles, recommendations
- Fraud: fraud_events, fraud_alerts, fraud_investigations
- Platform: notifications, audit_logs, security_events
- AI: ai_conversations, ai_messages

The SQLAlchemy models under `backend/app/models` are the current schema source. Alembic migrations must be committed with schema changes.
