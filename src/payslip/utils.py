from datetime import date, datetime
from fastapi import HTTPException


def parse_month(month_str: str) -> date:
    """Convert YYYY-MM to a date object representing first day of the month."""
    try:
        d = datetime.strptime(month_str, "%Y-%m")
        return date(d.year, d.month, 1)
    except:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")


def calculate_period(mode: str, start: str | None, end: str | None):
    today = date.today()
    current_month = date(today.year, today.month, 1)

    if mode == "3_months":
        months = 3
    elif mode == "6_months":
        months = 6
    else:  # manual mode
        if not start or not end:
            raise HTTPException(400, "start_month and end_month required")
        start_date = parse_month(start)
        end_date = parse_month(end)

        if end_date > current_month:
            raise HTTPException(400, "Cannot request future payslips")
        if start_date > end_date:
            raise HTTPException(400, "start_month cannot be after end_month")

        return start_date, end_date

    # Auto period
    end_date = current_month
    year = end_date.year
    mon = end_date.month - (months - 1)

    while mon <= 0:
        mon += 12
        year -= 1

    start_date = date(year, mon, 1)
    return start_date, end_date


def validate_join_date(join_date_str: str, period_start: date):
    """User cannot request payslips earlier than join date"""
    try:
        join = datetime.strptime(join_date_str, "%Y-%m-%d").date()
        join_month = join.replace(day=1)
    except:
        raise HTTPException(500, "Invalid join_date format in DB")

    if period_start < join_month:
        raise HTTPException(400, "You cannot request payslips before your joining date")
