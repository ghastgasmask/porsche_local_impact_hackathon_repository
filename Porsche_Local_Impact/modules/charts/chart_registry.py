# Rinat сделал
# Регистрия для графиков
# Дает все возможные данные для создания графиков
# ЛЛМка юзает это чтобы понять какие данные есть, что можно юзать
# Потом валдиатор смотрит что можно что незя


# Какие можно сделать новые
ALLOWED_CHART_TYPES = ["bar", "line", "pie", "scatter"]

# Какие аггрегиационные функции. Если чо аггрегация это математика простая, которая комбинирует несколько чисел
ALLOWED_AGGREGATIONS = ["sum", "mean", "count", "min", "max", "median", "none"]

# Чтобы можно было понимать имена, не понял как работает
DATAFRAME_MAP = {
    "accounts_df": "accounts_df",
    "transactions_df": "transactions_df",
    "scheduled_payments_df": "scheduled_payments_df",
    "expected_inflows_df": "expected_inflows_df",
    "holidays_df": "holidays_df",
}

# Полный реестр наборов данных с столбцами
DATASET_REGISTRY = {
    "accounts_df": {
        "description": "Account balances across all banks and currencies",
        "columns": {
            "account_id":       {"type": "string",  "description": "Unique account identifier (e.g. ACC001)"},
            "currency":         {"type": "string",  "description": "Currency code (KZT, USD, EUR, GBP, RUB)"},
            "current_balance":  {"type": "float",   "description": "Current balance amount"},
            "bank_name":        {"type": "string",  "description": "Bank name (JP Morgan, Kaspi Bank, etc.)"},
            "account_type":     {"type": "string",  "description": "Account type (reserve, settlement, operational, nostro)"},
            "iban":             {"type": "string",  "description": "IBAN number"},
            "swift_code":       {"type": "string",  "description": "SWIFT/BIC code"},
            "last_updated":     {"type": "datetime","description": "Timestamp of last update"},
            "minimum_balance":  {"type": "float",   "description": "Minimum required balance"},
            "optimal_balance":  {"type": "float",   "description": "Target optimal balance"},
        }
    },
    "transactions_df": {
        "description": "Historical transactions including inflows and outflows",
        "columns": {
            "transaction_id":   {"type": "string",  "description": "Unique transaction identifier"},
            "datetime":         {"type": "datetime","description": "Transaction date and time"},
            "type":             {"type": "string",  "description": "Transaction type (withdrawal, deposit, partner_payment, etc.)"},
            "amount":           {"type": "float",   "description": "Transaction amount"},
            "currency":         {"type": "string",  "description": "Currency code"},
            "account_id":       {"type": "string",  "description": "Related account ID"},
            "payment_system":   {"type": "string",  "description": "Payment system used (SWIFT, ACH, INSTANT, etc.)"},
            "delay_days":       {"type": "int",     "description": "Processing delay in days"},
            "category":         {"type": "string",  "description": "Transaction category (merchant_payment, client_transfer, etc.)"},
            "status":           {"type": "string",  "description": "Transaction status (completed, pending, failed)"},
            "direction":        {"type": "string",  "description": "Flow direction (inflow, outflow)"},
            "counterparty":     {"type": "string",  "description": "Counterparty name"},
            "description":      {"type": "string",  "description": "Transaction description"},
        }
    },
    "scheduled_payments_df": {
        "description": "Upcoming scheduled payments and obligations",
        "columns": {
            "payment_id":       {"type": "string",  "description": "Unique payment identifier"},
            "due_date":         {"type": "datetime","description": "Payment due date"},
            "amount":           {"type": "float",   "description": "Payment amount"},
            "currency":         {"type": "string",  "description": "Currency code"},
            "recipient":        {"type": "string",  "description": "Payment recipient"},
            "priority":         {"type": "string",  "description": "Priority level (critical, normal, low)"},
            "category":         {"type": "string",  "description": "Payment category (merchant_payout, bill_payment, etc.)"},
            "account_from":     {"type": "string",  "description": "Source account ID"},
            "description":      {"type": "string",  "description": "Payment description"},
            "can_be_delayed":   {"type": "string",  "description": "Whether payment can be delayed (True/False)"},
        }
    },
    "expected_inflows_df": {
        "description": "Expected incoming cash flows",
        "columns": {
            "inflow_id":            {"type": "string",  "description": "Unique inflow identifier"},
            "sent_date":            {"type": "datetime","description": "Date the payment was sent"},
            "payment_system":       {"type": "string",  "description": "Payment system used"},
            "amount":               {"type": "float",   "description": "Inflow amount"},
            "currency":             {"type": "string",  "description": "Currency code"},
            "expected_arrival_date": {"type": "datetime","description": "Expected arrival date"},
            "actual_delay_days":    {"type": "int",     "description": "Actual delay in days"},
            "from_partner":         {"type": "string",  "description": "Sending partner name"},
            "to_account":           {"type": "string",  "description": "Destination account ID"},
            "status":               {"type": "string",  "description": "Inflow status (in_transit, received, delayed)"},
        }
    },
    "holidays_df": {
        "description": "Banking holidays calendar",
        "columns": {
            "date":             {"type": "datetime","description": "Holiday date"},
            "country":          {"type": "string",  "description": "Country (Global, US, UK, KZ, etc.)"},
            "holiday_name":     {"type": "string",  "description": "Name of the holiday"},
            "is_banking_day":   {"type": "string",  "description": "Whether it is a banking day (True/False)"},
        }
    },
}


def get_registry_summary_for_llm():
    # Для ЛЛМки делает краткое описание всех датафреймов и столбцов
    # чтобы вставить в систем промпт
    # Тоже странно работает!!!
    
    lines = ["AVAILABLE DATASETS AND COLUMNS:"]
    lines.append("=" * 50)
    for df_name, info in DATASET_REGISTRY.items():
        lines.append(f"\n{df_name} — {info['description']}")
        lines.append("   Columns:")
        for col_name, col_info in info["columns"].items():
            lines.append(f"   • {col_name} ({col_info['type']}): {col_info['description']}")
    return "\n".join(lines)
