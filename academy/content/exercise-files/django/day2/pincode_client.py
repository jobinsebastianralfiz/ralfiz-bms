"""Real-world: address autofill from an Indian PIN code (used in booking/checkout forms)."""
from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)
API = "https://api.postalpincode.in/pincode/{pin}"


@dataclass(frozen=True)
class PostOffice:
    name: str
    district: str
    state: str


class PincodeNotFound(Exception):
    pass


@contextmanager
def timer(label: str):
    """Context manager: `with timer("lookup"):` logs how long the block took."""
    start = perf_counter()
    try:
        yield
    finally:
        logger.info("%s: %.0f ms", label, (perf_counter() - start) * 1000)


def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504), allowed_methods=("GET",))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"Accept": "application/json", "User-Agent": "bookit/1.0"})
    return session


def lookup(pin: str, session: requests.Session | None = None) -> list[PostOffice]:
    if not (pin.isdigit() and len(pin) == 6):
        raise ValueError("PIN code must be 6 digits")
    session = session or build_session()
    with timer(f"pincode {pin}"):
        resp = session.get(API.format(pin=pin), timeout=(3, 10))  # ALWAYS set a timeout
    resp.raise_for_status()
    payload = resp.json()[0]
    if payload.get("Status") != "Success" or not payload.get("PostOffice"):
        raise PincodeNotFound(pin)
    return [PostOffice(p["Name"], p["District"], p["State"]) for p in payload["PostOffice"]]


def read_in_batches(path: str, size: int = 1000):
    """Generator: process a 2 GB log/CSV without loading it into memory."""
    batch = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            batch.append(line.rstrip("\n"))
            if len(batch) == size:
                yield batch
                batch = []
    if batch:
        yield batch


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for office in lookup("679322"):
        print(office)
