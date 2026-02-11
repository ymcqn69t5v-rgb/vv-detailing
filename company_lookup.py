#!/usr/bin/env python3
"""Vyhledání firem dle města + filtr telefonů mimo O2.

Backend logika pro CLI i webovou aplikaci.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any

ARES_SEARCH_URL = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty"
ARES_DETAIL_URL = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico}"
DUCKDUCKGO_HTML_URL = "https://duckduckgo.com/html/"
DEFAULT_O2_CHECK_URL = "https://www.o2.cz/podpora/volani-z-mobilu/overte-si-operatora"

PHONE_REGEX = re.compile(r"(?:\+420\s*)?(\d[\d\s-]{7,}\d)")

O2_RESULT_TOKENS = {
    "telefonní číslo je v síti o2",
    "telefonni cislo je v siti o2",
    "číslo je v síti o2",
    "cislo je v siti o2",
}
NON_O2_TOKENS = {
    "vodafone",
    "t-mobile",
    "mobil.cz",
    "nejste v síti o2",
    "nejste v siti o2",
    "není v síti o2",
    "neni v siti o2",
    "není v síti od o2",
    "neni v siti od o2",
}

WHITELISTED_PHONE_DOMAINS = (
    "zivefirmy.cz",
    "firmy.cz",
    "najisto.centrum.cz",
    "edb.cz",
)


@dataclass
class CompanySeed:
    ico: str
    name: str


@dataclass
class CompanyResult:
    ico: str
    name: str
    executive: str
    phone: str
    source: str
    operator_check: str


DEMO_ROWS = [
    CompanyResult(
        ico="27123456",
        name="Demo Firma Brno s.r.o.",
        executive="Jan Novák",
        phone="+420 777 123 456",
        source="zivefirmy.cz",
        operator_check="confirmed_non_o2",
    ),
    CompanyResult(
        ico="28987654",
        name="Ukázková Společnost a.s.",
        executive="Petra Svobodová",
        phone="+420 775 987 654",
        source="ares",
        operator_check="confirmed_non_o2",
    ),
]


def fetch_text(
    url: str,
    params: dict[str, Any] | None = None,
    method: str = "GET",
    data: dict[str, str] | None = None,
) -> str:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    body = None
    headers = {
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        "User-Agent": "company-lookup-ui/1.0",
    }
    if data is not None:
        body = urllib.parse.urlencode(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    req = urllib.request.Request(url, headers=headers, data=body, method=method)
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Nepodařilo se stáhnout URL: {url}\n{exc}") from exc


def fetch_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    text = fetch_text(url, params=params)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Neplatná JSON odpověď z URL: {url}\n{exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Neočekávaný formát JSON odpovědi z URL: {url}")
    return payload


def walk_json(node: Any):
    if isinstance(node, dict):
        for key, value in node.items():
            yield key, value
            yield from walk_json(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk_json(item)


def normalize_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("420") and len(digits) >= 12:
        digits = digits[-9:]
    if len(digits) == 9:
        return f"+420 {digits[:3]} {digits[3:6]} {digits[6:9]}"
    return raw.strip()


def extract_phones_from_text(text: str) -> set[str]:
    phones: set[str] = set()
    for match in PHONE_REGEX.finditer(text):
        normalized = normalize_phone(match.group(0))
        digits = re.sub(r"\D", "", normalized)
        if len(digits) == 12 and digits.startswith("420"):
            phones.add(normalized)
        elif len(digits) == 9:
            phones.add(f"+420 {digits[:3]} {digits[3:6]} {digits[6:9]}")
    return phones


def find_first_string(payload: dict[str, Any], key_candidates: set[str]) -> str | None:
    for key, value in walk_json(payload):
        if key.lower() in key_candidates and isinstance(value, str) and value.strip():
            return value.strip()
    return None


def parse_ares_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("ekonomickeSubjekty", "items", "vysledky", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
    return []


def parse_ico(item: dict[str, Any]) -> str | None:
    for key in ("ico", "ic", "id"):
        value = item.get(key)
        if isinstance(value, str):
            digits = re.sub(r"\D", "", value)
            if digits:
                return digits
        if isinstance(value, int):
            return str(value)
    return None


def search_companies_in_city(city: str, limit: int) -> list[CompanySeed]:
    payload = fetch_json(
        ARES_SEARCH_URL,
        params={"obec": city, "strankovani": "true", "pocet": limit, "start": 0},
    )

    seeds: list[CompanySeed] = []
    for item in parse_ares_items(payload):
        ico = parse_ico(item)
        if not ico:
            continue
        name = item.get("obchodniJmeno") or item.get("nazev") or f"IČO {ico}"
        seeds.append(CompanySeed(ico=ico, name=str(name).strip()))
    return seeds


def read_ares_detail(ico: str) -> tuple[str, set[str]]:
    payload = fetch_json(ARES_DETAIL_URL.format(ico=ico))
    executive = (
        find_first_string(payload, {"jmenojednatele", "jednatel", "nazevosoby", "statutarniorgan"})
        or "Nedostupné"
    )

    phones: set[str] = set()
    for _, value in walk_json(payload):
        if isinstance(value, str):
            phones.update(extract_phones_from_text(value))
    return executive, phones


def ddg_search_urls(query: str, max_results: int) -> list[str]:
    html_doc = fetch_text(DUCKDUCKGO_HTML_URL, params={"q": query})
    links = re.findall(r'<a[^>]+class="[^\"]*result__a[^\"]*"[^>]+href="([^"]+)"', html_doc)

    urls: list[str] = []
    for link in links:
        link = html.unescape(link)
        if link.startswith("//"):
            link = f"https:{link}"
        parsed = urllib.parse.urlparse(link)
        hostname = (parsed.hostname or "").lower()
        if parsed.scheme in {"http", "https"} and any(hostname.endswith(d) for d in WHITELISTED_PHONE_DOMAINS):
            urls.append(link)
        if len(urls) >= max_results:
            break
    return urls


def scrape_external_phone_sources(ico: str, name: str, city: str, max_pages: int) -> dict[str, set[str]]:
    query = f"{ico} {name} {city} telefon"
    urls = ddg_search_urls(query, max_pages)

    out: dict[str, set[str]] = {}
    for url in urls:
        hostname = urllib.parse.urlparse(url).hostname or "unknown"
        try:
            page = fetch_text(url)
        except RuntimeError:
            continue
        phones = extract_phones_from_text(page)
        if phones:
            out.setdefault(hostname, set()).update(phones)
    return out


def strip_html_for_match(text: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text)).strip().lower()


def verify_operator_with_o2(phone: str, verify_url: str) -> str:
    """Vrací: 'o2' | 'non_o2' | 'unknown'."""
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("420"):
        digits = digits[-9:]

    payloads = [
        {"phone": digits},
        {"telefon": digits},
        {"msisdn": digits},
        {"number": digits},
    ]

    for payload in payloads:
        try:
            body = fetch_text(verify_url, method="POST", data=payload)
        except RuntimeError:
            continue

        plain = strip_html_for_match(body)
        if any(token in plain for token in O2_RESULT_TOKENS):
            return "o2"
        if any(token in plain for token in NON_O2_TOKENS):
            return "non_o2"

    return "unknown"


def build_table(rows: list[CompanyResult]) -> str:
    headers = ("IČO", "Jméno firmy", "Jméno jednatele", "Kontaktní telefon", "Zdroj", "Ověření")
    table = [headers] + [
        (r.ico, r.name, r.executive, r.phone, r.source, r.operator_check) for r in rows
    ]
    widths = [max(len(str(row[i])) for row in table) for i in range(len(headers))]

    def line(values: tuple[str, str, str, str, str, str]) -> str:
        return " | ".join(str(values[i]).ljust(widths[i]) for i in range(len(headers)))

    sep = "-+-".join("-" * w for w in widths)
    return "\n".join([line(headers), sep] + [line(row) for row in table[1:]])


def run_search(
    city: str,
    limit: int,
    verify_url: str,
    strict: bool,
    max_source_pages: int,
) -> list[CompanyResult]:
    seeds = search_companies_in_city(city, limit)
    results: list[CompanyResult] = []

    for seed in seeds:
        executive, phones = read_ares_detail(seed.ico)
        phone_sources: dict[str, set[str]] = {"ares": set(phones)}

        for src, src_phones in scrape_external_phone_sources(seed.ico, seed.name, city, max_source_pages).items():
            phones.update(src_phones)
            phone_sources.setdefault(src, set()).update(src_phones)

        for phone in sorted(phones):
            operator = verify_operator_with_o2(phone, verify_url)
            if operator == "o2":
                continue
            if operator == "unknown" and strict:
                continue

            chosen_source = "ares"
            for src, src_phones in phone_sources.items():
                if phone in src_phones:
                    chosen_source = src
                    break

            results.append(
                CompanyResult(
                    ico=seed.ico,
                    name=seed.name,
                    executive=executive,
                    phone=phone,
                    source=chosen_source,
                    operator_check=("confirmed_non_o2" if operator == "non_o2" else "unverified_non_o2"),
                )
            )
            break

    return results


def run_demo() -> list[CompanyResult]:
    return list(DEMO_ROWS)


def rows_to_dicts(rows: list[CompanyResult]) -> list[dict[str, str]]:
    return [asdict(r) for r in rows]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vyhledání firem dle města s filtrem mimo O2.")
    parser.add_argument("city", help="Město, např. Brno")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--o2-check-url", default=DEFAULT_O2_CHECK_URL)
    parser.add_argument("--max-source-pages", type=int, default=5)
    parser.add_argument("--non-strict", action="store_true", help="Povolí i čísla, kde operátor nešel ověřit.")
    parser.add_argument("--demo", action="store_true", help="Ukázkový běh bez internetu")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.limit <= 0 or args.max_source_pages <= 0:
        print("--limit a --max-source-pages musí být kladné číslo", file=sys.stderr)
        return 2

    try:
        rows = run_demo() if args.demo else run_search(
            city=args.city,
            limit=args.limit,
            verify_url=args.o2_check_url,
            strict=not args.non_strict,
            max_source_pages=args.max_source_pages,
        )
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1

    if not rows:
        print("Nebyly nalezeny firmy splňující filtr.")
        return 0

    print(build_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
