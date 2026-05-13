#!/usr/bin/env python3

import logging
import sys
from dataclasses import dataclass

import requests


BASE_URL = "https://tools-httpstatus.pickup-services.com"


@dataclass(frozen=True)
class HttpCheck:
    status_code: int
    url: str


class HttpStatusError(Exception):
    pass


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def fetch_status(check: HttpCheck) -> None:
    logging.info("Requesting %s", check.url)

    response = requests.get(check.url, timeout=10, allow_redirects=False)

    if 100 <= response.status_code <= 399:
        logging.info(
            "Successful response | status_code=%s | body=%s",
            response.status_code,
            response.text.strip(),
        )
        return

    if 400 <= response.status_code <= 599:
        raise HttpStatusError(
            f"HTTP error response | status_code={response.status_code} | body={response.text.strip()}"
        )

    raise HttpStatusError(f"Unexpected status code: {response.status_code}")


def main() -> int:
    setup_logging()

    checks = [
        HttpCheck(200, f"{BASE_URL}/200"),
        HttpCheck(201, f"{BASE_URL}/201"),
        HttpCheck(301, f"{BASE_URL}/301"),
        HttpCheck(404, f"{BASE_URL}/404"),
        HttpCheck(500, f"{BASE_URL}/500"),
    ]

    for check in checks:
        try:
            fetch_status(check)
        except HttpStatusError as error:
            logging.error("Handled HTTP exception: %s", error)
        except requests.RequestException as error:
            logging.error("Handled network exception: %s", error)

    logging.info("All requests were processed")
    return 0


if __name__ == "__main__":
    sys.exit(main())