"""
Calendar Export — Generates .ics (iCalendar) files for interview events.
Works with Google Calendar, Outlook, Apple Calendar, and any other .ics-compatible app.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional


def generate_ics(interview: dict) -> str:
    """
    Generate a valid .ics (iCalendar) string from an interview event dict.
    
    Args:
        interview: Dict with keys: company, role, interview_date (YYYY-MM-DD),
                   interview_time (HH:MM), duration_minutes, interview_type, notes
    
    Returns:
        A complete iCalendar string ready for file download.
    """
    company = interview.get("company", "Company")
    role = interview.get("role", "Role")
    date_str = interview.get("interview_date", "")
    time_str = interview.get("interview_time", "09:00")
    duration = interview.get("duration_minutes", 45)
    interview_type = interview.get("interview_type", "Video")
    notes = interview.get("notes", "")
    event_id = interview.get("event_id", "jobhunter-event")

    # Parse date and time
    try:
        dt_start = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        dt_start = datetime.now() + timedelta(days=1)
        dt_start = dt_start.replace(hour=9, minute=0, second=0, microsecond=0)

    dt_end = dt_start + timedelta(minutes=duration)

    # Format for iCalendar (UTC-naive local time)
    fmt = "%Y%m%dT%H%M%S"
    dtstart = dt_start.strftime(fmt)
    dtend = dt_end.strftime(fmt)
    dtstamp = datetime.utcnow().strftime(fmt) + "Z"

    # Build description
    description_lines = [
        f"Interview Type: {interview_type}",
        f"Company: {company}",
        f"Role: {role}",
        f"Duration: {duration} minutes",
    ]
    if notes:
        description_lines.append(f"\\nNotes: {notes}")
    
    description = "\\n".join(description_lines)

    # Build the .ics content
    ics = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//JobHunter//Interview Tracker//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{event_id}@jobhunter\r\n"
        f"DTSTAMP:{dtstamp}\r\n"
        f"DTSTART:{dtstart}\r\n"
        f"DTEND:{dtend}\r\n"
        f"SUMMARY:{interview_type} Interview — {role} at {company}\r\n"
        f"DESCRIPTION:{description}\r\n"
        "STATUS:CONFIRMED\r\n"
        "BEGIN:VALARM\r\n"
        "TRIGGER:-PT30M\r\n"
        "ACTION:DISPLAY\r\n"
        f"DESCRIPTION:Interview reminder: {role} at {company} in 30 minutes\r\n"
        "END:VALARM\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )

    return ics


def get_ics_filename(interview: dict) -> str:
    """Generate a clean filename for the .ics download."""
    company = interview.get("company", "company").replace(" ", "_")
    date_str = interview.get("interview_date", "date")
    return f"interview_{company}_{date_str}.ics"
