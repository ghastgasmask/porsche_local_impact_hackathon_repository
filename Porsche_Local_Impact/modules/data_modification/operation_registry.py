ALLOWED_DATAFRAMES = ["accounts_df", "scheduled_payments_df", "expected_inflows_df"]

ALLOWED_OPERATIONS = {
    "accounts_df": ["update"], 
    "scheduled_payments_df": ["add", "update"],
    "expected_inflows_df": ["add", "update"]
}
