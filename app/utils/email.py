"""I do not really like IMAP after creating this file. 
This is not async but does not need to be since it is only called once (potentially) on startup.
"""

import imaplib
import re
import email
import time
from typing import List, Optional
from app.utils.config import load_config


def connect_imap(host: str, user: str, password: str) -> imaplib.IMAP4_SSL:
    imap = imaplib.IMAP4_SSL(host=host, port=1143)
    imap.login(user, password)
    return imap


def get_message_ids(
    imap: imaplib.IMAP4_SSL, target_mailbox: str, sender: str, subject: str
) -> List[int]:
    status, data = imap.select(target_mailbox)
    search_criteria = f'(UNSEEN FROM "{sender}" SUBJECT "{subject}")'
    status, message_ids = imap.uid("search", None, search_criteria)
    return list(map(int, message_ids[0].split())) if status == "OK" else []


def fetch_and_process_emails(
    imap: imaplib.IMAP4_SSL, message_ids: List[int]
) -> Optional[str]:
    for i in range(1):
        try:
            message_id = message_ids[i]
        except IndexError:
            return None
        status, data = imap.uid("fetch", str(message_id).encode(), "(RFC822)")
        if status == "OK":
            raw_email = data[0][1]
            email_message = email.message_from_bytes(raw_email)
            regex = r"ml=([A-Za-z0-9-_=]+)"

            for part in email_message.walk():
                body = part.get_payload(decode=True)
                body = body.decode("utf-8")

                matches = re.findall(regex, body)
                if matches:
                    # print(matches[0])
                    return matches[0]

    return None


def fetch_magic_link(tries: int = 10, wait: int = 5) -> Optional[str]:
    """
    Fetches the magic link from the email server. If no magic link is found keep trying until it is found.

    Returns:
        Optional[str]: The magic link if found, None otherwise.
    """
    config = load_config()
    imap = connect_imap(config.imap.host, config.imap.username, config.imap.password)

    for i in range(tries):
        message_ids = get_message_ids(
            imap,
            f'"{config.imap.mailbox}"',
            "accounts@us.mcdonalds.com",
            "Use this email to",  # NOTE: What McDonalds has for magic link emails
        )

        if len(message_ids) == 0:
            print(f"Magic link not found, trying again in {wait} seconds...")
            time.sleep(wait)
            continue

        code = fetch_and_process_emails(imap, message_ids)
        if code is None:
            print(f"Magic link not found, trying again in {wait} seconds...")
            time.sleep(wait)
            continue

        return code
