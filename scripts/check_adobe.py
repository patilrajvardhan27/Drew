"""Checks the Adobe credentials in .env by requesting an access token. Spends no transactions.

Usage: python -m scripts.check_adobe
"""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request

from api.core.config import ROOT, get_settings

TOKEN_URL = "https://pdf-services.adobe.io/token"


def main() -> int:
    settings = get_settings()
    if not (settings.adobe_client_id and settings.adobe_client_secret):
        print(f"No credentials found. Add them to {ROOT / '.env'} (see .env.example).")
        return 1

    body = urllib.parse.urlencode(
        {"client_id": settings.adobe_client_id, "client_secret": settings.adobe_client_secret}
    ).encode()
    request = urllib.request.Request(TOKEN_URL, data=body, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            token = json.load(response)
    except urllib.error.HTTPError as exc:
        print(f"Adobe refused the credentials ({exc.code}). Check the client ID and secret.")
        return 1
    except urllib.error.URLError as exc:
        print(f"Could not reach Adobe: {exc.reason}")
        return 1

    hours = int(token.get("expires_in", 0)) // 3600
    print(f"Credentials work. Token issued for about {hours} hours.")
    if settings.adobe_mode != "live":
        print("Set REDRAFT_ADOBE_MODE=live in .env to use them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
