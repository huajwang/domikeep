def format_cad(cents: int) -> str:
    amount = int(cents or 0)
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    return f"{sign}${amount // 100:,}.{amount % 100:02d}"
