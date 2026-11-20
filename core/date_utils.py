"""Shared date, week-boundary, and festivity resolution utilities."""

import logging
from datetime import date, datetime, timedelta
from typing import Any


def parse_first_day_of_week(val: int | str | None) -> int:
    """Normalizes a weekday name or index into 0..6 (0=Monday, 5=Saturday, 6=Sunday)."""
    if val is None:
        return 0
    if isinstance(val, int) and 0 <= val <= 6:
        return val
    s = str(val).strip().lower()
    mapping = {
        "monday": 0, "mon": 0, "lunedi": 0, "lunedì": 0, "0": 0,
        "tuesday": 1, "tue": 1, "martedi": 1, "martedì": 1, "1": 1,
        "wednesday": 2, "wed": 2, "mercoledi": 2, "mercoledì": 2, "2": 2,
        "thursday": 3, "thu": 3, "giovedi": 3, "giovedì": 3, "3": 3,
        "friday": 4, "fri": 4, "venerdi": 4, "veneredì": 4, "4": 4,
        "saturday": 5, "sat": 5, "sabato": 5, "5": 5,
        "sunday": 6, "sun": 6, "domenica": 6, "6": 6,
    }
    return mapping.get(s, 0)


def get_easter_date(year: int) -> date:
    """Calculates Easter Sunday using the Anonymous Gregorian algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def get_italian_holidays(year: int) -> dict[date, str]:
    """Returns a dict mapping date -> holiday name for national Italian holidays in the given year."""
    holidays = {
        date(year, 1, 1): "Capodanno",
        date(year, 1, 6): "Epifania",
        date(year, 4, 25): "Liberazione",
        date(year, 5, 1): "Festa del Lavoro",
        date(year, 6, 2): "Festa della Repubblica",
        date(year, 8, 15): "Ferragosto",
        date(year, 11, 1): "Ognissanti",
        date(year, 12, 8): "Immacolata",
        date(year, 12, 25): "Natale",
        date(year, 12, 26): "Santo Stefano",
    }
    easter = get_easter_date(year)
    holidays[easter + timedelta(days=1)] = "Pasquetta"
    return holidays


def get_week_start_date(week_number: int, year: int = 2025, first_day_of_week: int | str = 0) -> date:
    """Calculates the start date for a given week number in a year given first_day_of_week."""
    start_dow = parse_first_day_of_week(first_day_of_week)
    jan1 = date(year, 1, 1)
    if start_dow == 0:
        if jan1.weekday() != 0:
            jan1 += timedelta(days=(7 - jan1.weekday()))
        return jan1 + timedelta(weeks=week_number - 1)

    if jan1.weekday() == start_dow:
        return jan1 + timedelta(weeks=week_number - 1)

    diff = (start_dow - jan1.weekday()) % 7
    first_full_start = jan1 + timedelta(days=diff)
    if week_number == 1:
        return jan1
    return first_full_start + timedelta(weeks=week_number - 2)


def get_week_monday(week_number: int, year: int = 2025) -> date:
    """Calculates the Monday date for a given week number in a year."""
    return get_week_start_date(week_number, year, 0)


def get_week_date(week_number: int, year: int = 2025, first_day_of_week: int | str = 0) -> str:
    """Returns the ISO YYYY-MM-DD start date string for a week number."""
    return get_week_start_date(week_number, year, first_day_of_week).strftime("%Y-%m-%d")


def get_week_number_for_date(d: date, year: int = 2025, first_day_of_week: int | str = 0) -> int:
    """Finds which schedule week number a date belongs to."""
    start_dow = parse_first_day_of_week(first_day_of_week)
    jan1 = date(year, 1, 1)
    if start_dow == 0:
        first_monday = get_week_start_date(1, year, 0)
        delta_days = (d - first_monday).days
        if delta_days < 0:
            return 1
        return (delta_days // 7) + 1

    if jan1.weekday() == start_dow:
        delta_days = (d - jan1).days
        if delta_days < 0:
            return 1
        return (delta_days // 7) + 1

    diff = (start_dow - jan1.weekday()) % 7
    first_full_start = jan1 + timedelta(days=diff)
    if d < first_full_start:
        return 1
    return 2 + ((d - first_full_start).days // 7)


def get_summer_weeks(year: int, first_day_of_week: int | str = 0) -> tuple[int, int]:
    """Calculates the dynamic summer week range (start_week, end_week) for June 15 - Sept 15."""
    sum_start_w = get_week_number_for_date(date(year, 6, 15), year, first_day_of_week)
    sum_end_w = get_week_number_for_date(date(year, 9, 15), year, first_day_of_week)
    return sum_start_w, sum_end_w


def get_days_in_week(week_number: int, year: int = 2025, first_day_of_week: int | str = 0) -> list[date]:
    """Calculates the exact dates belonging to a specific week within the target year."""
    start_date = get_week_start_date(week_number, year, first_day_of_week)

    if week_number == 1:
        next_week_start = get_week_start_date(2, year, first_day_of_week)
        days = (next_week_start - start_date).days
    else:
        days = 7

    valid_dates = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        if d.year == year:
            valid_dates.append(d)
    return valid_dates


def parse_custom_date(raw_date: str | None, year: int) -> date | None:
    """Parses 'DD/MM', 'DD/MM/YYYY', or 'YYYY-MM-DD' into a date object for the given year."""
    if not raw_date:
        return None
    d_str = raw_date.strip()
    if not d_str:
        return None

    if "/" in d_str:
        parts = d_str.split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid date format '{d_str}'.")
        day = int(parts[0])
        month = int(parts[1])
        target_year = int(parts[2]) if len(parts) >= 3 and parts[2] else year
        return date(target_year, month, day)

    if "-" in d_str:
        return datetime.strptime(d_str, "%Y-%m-%d").date()

    raise ValueError(f"Unsupported date format '{d_str}'.")


def resolve_festivities_dict(
    year: int,
    auto_festivities: bool = True,
    custom_festivities: list[Any] | None = None,
    strict: bool = False,
) -> dict[date, str]:
    """Builds a date -> festivity name mapping from Italian holidays and custom festivities."""
    festivities_dict: dict[date, str] = {}
    if auto_festivities:
        festivities_dict.update(get_italian_holidays(year))

    for cust_fest in custom_festivities or []:
        name = (
            cust_fest.name
            if hasattr(cust_fest, "name")
            else (cust_fest.get("name", "") if isinstance(cust_fest, dict) else str(cust_fest))
        )
        raw_d = (
            cust_fest.date
            if hasattr(cust_fest, "date")
            else (cust_fest.get("date", "") if isinstance(cust_fest, dict) else "")
        )
        d_str = raw_d.strip() if raw_d else ""

        if not d_str:
            if strict:
                raise ValueError(
                    f"Cannot generate schedule: Festivity '{name}' is missing a date while auto festivities is disabled."
                )
            continue

        try:
            d_obj = parse_custom_date(d_str, year)
            if d_obj is not None:
                festivities_dict[d_obj] = name
        except Exception as exc:
            if strict:
                raise ValueError(
                    f"Cannot generate schedule: Festivity '{name}' has invalid date format '{d_str}' while auto festivities is disabled."
                ) from exc
            logging.warning(f"Skipping invalid custom festivity date '{d_str}': {exc}")

    return festivities_dict
