from datetime import date, timedelta


def get_fiscal_year_range(start_month: int, offset: int = 0):
    """
    Calcula el rango de fechas para un año fiscal.
    offset=0: Año fiscal actual.
    offset=-1: Año fiscal anterior.
    """
    today = date.today()

    if today.month >= start_month:
        base_year = today.year
    else:
        base_year = today.year - 1

    fy_start_year = base_year + offset

    start = date(fy_start_year, start_month, 1)
    if start_month == 1:
        end = date(fy_start_year, 12, 31)
    else:
        end = date(fy_start_year + 1, start_month, 1) - timedelta(days=1)

    return start.isoformat(), end.isoformat(), fy_start_year
