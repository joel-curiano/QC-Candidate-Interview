"""Validation for the single email address stored on each account."""
import re
from email.headerregistry import Address
from email.errors import HeaderParseError


def validate_email_address(value, label='Email'):
    address = str(value or '').strip()
    try:
        parsed = Address(addr_spec=address)
        if (
            not parsed.username or not parsed.domain
            or any(character.isspace() for character in address)
            or not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?', parsed.domain)
            or any(not part or part.startswith('-') or part.endswith('-') for part in parsed.domain.split('.'))
        ):
            raise ValueError
        address.encode('ascii')
    except (ValueError, IndexError, UnicodeError, HeaderParseError) as exc:
        raise ValueError(f'{label} must be a complete email address, such as name@example.com.') from exc
    return address
