"""
Gmail API client for fetching rejection/update emails.
Uses OAuth 2.0 with Desktop app credentials.
Gracefully falls back to empty results if credentials are unavailable.
"""

from __future__ import annotations

import os
import base64
from typing import List, Optional


def get_gmail_service():
    """
    Authenticate with Gmail API using OAuth 2.0.
    Requires credentials.json in the project root.
    Returns the Gmail API service object, or None if unavailable.
    """
    try:
        from googleapiclient.discovery import build
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials

        SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
        creds = None

        project_root = os.path.join(os.path.dirname(__file__), "..")
        token_path = os.path.join(project_root, "token.json")
        creds_path = os.path.join(project_root, "credentials.json")

        if not os.path.exists(creds_path):
            return None

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(token_path, "w") as token:
                token.write(creds.to_json())

        return build("gmail", "v1", credentials=creds)

    except Exception as e:
        print(f"Gmail API setup failed: {e}")
        return None


def fetch_rejection_emails(
    max_results: int = 10,
    sender_filter: Optional[str] = None,
) -> List[str]:
    """
    Fetch email body texts matching job application update patterns.

    Args:
        max_results: Maximum number of emails to fetch.
        sender_filter: Specific sender email to filter by.

    Returns:
        List of email body text strings. Empty list if Gmail is unavailable.
    """
    service = get_gmail_service()
    if service is None:
        return []

    try:
        # Build query
        queries = []
        if sender_filter:
            queries.append(f"from:{sender_filter}")
        else:
            queries.append(
                "(from:no-reply@greenhouse.io OR from:no-reply@lever.co "
                "OR from:notifications@hire.lever.co OR from:noreply@hired.com "
                'OR subject:"application update" OR subject:"application status" '
                'OR subject:"your application" OR subject:"regarding your application")'
            )

        query = " ".join(queries)

        results = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results,
        ).execute()

        messages = results.get("messages", [])
        email_texts = []

        for msg in messages:
            full_msg = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="full",
            ).execute()

            body_text = _extract_body(full_msg)
            if body_text:
                email_texts.append(body_text)

        return email_texts

    except Exception as e:
        print(f"Gmail fetch failed: {e}")
        return []


def _extract_body(message: dict) -> str:
    """Extract plain text body from a Gmail API message."""
    try:
        payload = message.get("payload", {})

        # Simple message
        if payload.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

        # Multipart message
        parts = payload.get("parts", [])
        for part in parts:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        # Fallback to snippet
        return message.get("snippet", "")

    except Exception:
        return message.get("snippet", "")
