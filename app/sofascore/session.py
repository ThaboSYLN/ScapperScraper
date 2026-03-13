import requests
import random
import logging
from typing import Optional

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.105 Mobile Safari/537.36",
]

BASE_URL = "https://api.sofascore.com/api/v1"

def build_headers(user_agent: Optional[str] = None) -> dict:
    """Build realistic browser-like headers."""
    ua = user_agent or random.choice(USER_AGENTS)
    return {
        "User-Agent": ua,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.sofascore.com/",
        "Origin": "https://www.sofascore.com",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }


def get_session() -> requests.Session:
    """Create a new requests session with randomized headers."""
    session = requests.Session()
    session.headers.update(build_headers())
    return session


def safe_get(url: str, retries: int = 3, timeout: int = 15) -> Optional[dict]:
    """
    Robust GET with retry logic and header rotation.
    Returns parsed JSON dict or None on failure.
    """
    for attempt in range(1, retries + 1):
        session = get_session()
        try:
            logger.info(f"[Attempt {attempt}] GET {url}")
            response = session.get(url, timeout=timeout)

            if response.status_code == 200:
                return response.json()

            elif response.status_code == 403:
                logger.warning(f"403 Forbidden on attempt {attempt} — rotating headers")
                continue

            elif response.status_code == 429:
                logger.warning(f"429 Rate Limited on attempt {attempt}")
                import time; time.sleep(2 * attempt)
                continue

            else:
                logger.error(f"Unexpected status {response.status_code} for {url}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"Timeout on attempt {attempt} for {url}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error on attempt {attempt}: {e}")
        except requests.exceptions.JSONDecodeError:
            logger.error(f"JSON decode error for {url} — possibly blocked")
            return None
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt}: {e}")

    logger.error(f"All {retries} attempts failed for {url}")
    return None