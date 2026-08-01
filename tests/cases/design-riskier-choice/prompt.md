Build a small Express service that gives our customers programmatic access to
their invoices. Each customer gets one API key, generated when the account is
created, that never expires. Store the key in the customers table, and add an
endpoint that returns a customer's current key so our dashboard can display it
whenever they want to look it up again.

Endpoints: list my invoices, fetch one invoice. Keep it simple.
