# core/utils/ranges.py
from datetime import datetime, timedelta, date
import calendar
from django.utils import timezone

def get_period_range(period: str, base_date_str: str):
    """Devuelve (start_dt, end_dt_exclusive) timezone-aware."""
    base_date = datetime.strptime(base_date_str, "%Y-%m-%d").date()
    tz = timezone.get_current_timezone()

    if period == 'weekly':
        # Lunes como inicio (isoweekday: 1=Mon ... 7=Sun)
        start = base_date - timedelta(days=base_date.isoweekday() - 1)
        end = start + timedelta(days=7)
    elif period == 'monthly':
        start = base_date.replace(day=1)
        last_day = calendar.monthrange(base_date.year, base_date.month)[1]
        end = date(base_date.year, base_date.month, last_day) + timedelta(days=1)
    else:  # daily
        start = base_date
        end = start + timedelta(days=1)

    start_dt = timezone.make_aware(datetime.combine(start, datetime.min.time()), tz)
    end_dt = timezone.make_aware(datetime.combine(end, datetime.min.time()), tz)
    return start_dt, end_dt

def ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    return f"{n}{ {1:'st',2:'nd',3:'rd'}.get(n % 10, 'th') }"

def build_filename(period: str, start_dt, end_dt):
    # Nombre al estilo: Daily report Monday July 7th
    months = start_dt.strftime("%B")
    day_name = start_dt.strftime("%A")
    day_number = ordinal(start_dt.day)

    if period == 'daily':
        prefix = "Daily report"
        return f"{prefix} {day_name} {months} {day_number}.pdf"
    elif period == 'weekly':
        prefix = "Weekly report"
        s = f"{start_dt.strftime('%a %b')} {ordinal(start_dt.day)}"
        e = f"{(end_dt - timedelta(days=1)).strftime('%a %b')} {ordinal((end_dt - timedelta(days=1)).day)}"
        return f"{prefix} {s} - {e}.pdf"
    else:  # monthly
        prefix = "Monthly report"
        return f"{prefix} {start_dt.strftime('%B %Y')}.pdf"
