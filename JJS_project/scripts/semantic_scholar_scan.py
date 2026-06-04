#!/usr/bin/env python3
"""Semantic Scholar Graph API scan for the JJS confined-water literature.

The script reads an optional API key from S2_API_KEY and sends it only as an
HTTP header. It never writes the key to disk or prints it.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_QUERIES = [
    "AFM capillary bridge water meniscus pull-off force humidity",
    '"Nanometer-Sized Water Bridge and Pull-Off Force in AFM"',
    '"capillary liquid bridges" "atomic force microscopy" formation rupture hysteresis',
    '"Direct measurement of the capillary condensation time" water nanobridge',
    '"nucleation growth adhesion water bridges" "sliding nano-contacts"',
    '"Nonlinear Viscoelastic Dynamics" nanoconfined water AFM',
    '"Dynamic Solidification" "Nanoconfined Water Films"',
    '"Squeeze-out dynamics of nanoconfined water"',
    '"In Situ Atomic-Scale Imaging" "3D Nanoscale Confinement" water AFM',
    '"covalent organic framework" "AFM" "nanoindentation" freestanding film',
    '"freestanding 2D covalent organic framework nanofilms" mechanical',
    '"suspended" "COF" membrane AFM force curve humidity',
]

DEFAULT_FIELDS = ",".join(
    [
        "title",
        "year",
        "authors",
        "venue",
        "citationCount",
        "externalIds",
        "url",
        "abstract",
        "openAccessPdf",
    ]
)


def make_search_url(query: str, limit: int, fields: str) -> str:
    params = urllib.parse.urlencode(
        {
            "query": query,
            "limit": str(limit),
            "fields": fields,
        }
    )
    return f"https://api.semanticscholar.org/graph/v1/paper/search?{params}"


def fetch_json(url: str, api_key: str | None, timeout: float) -> dict[str, Any]:
    headers = {"User-Agent": "JJS-literature-scan/1.0"}
    if api_key:
        headers["x-api-key"] = api_key

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        retry_after = exc.headers.get("Retry-After")
        return {
            "error": {
                "status": exc.code,
                "reason": exc.reason,
                "retry_after": retry_after,
                "body": body,
            }
        }


def normalize_paper(query: str, rank: int, paper: dict[str, Any]) -> dict[str, Any]:
    external_ids = paper.get("externalIds") or {}
    authors = paper.get("authors") or []
    return {
        "query": query,
        "rank": rank,
        "year": paper.get("year"),
        "citation_count": paper.get("citationCount"),
        "title": paper.get("title") or "",
        "venue": paper.get("venue") or "",
        "doi": external_ids.get("DOI") or "",
        "url": paper.get("url") or "",
        "open_access_pdf": (paper.get("openAccessPdf") or {}).get("url") or "",
        "authors": "; ".join(author.get("name", "") for author in authors),
        "abstract": paper.get("abstract") or "",
    }


def flatten_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        query = result["query"]
        data = result.get("response", {}).get("data") or []
        for rank, paper in enumerate(data, start=1):
            rows.append(normalize_paper(query, rank, paper))
    return rows


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "query",
        "rank",
        "year",
        "citation_count",
        "title",
        "venue",
        "doi",
        "url",
        "open_access_pdf",
        "authors",
        "abstract",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search Semantic Scholar for AFM confined-water and COF membrane literature."
    )
    parser.add_argument(
        "--query",
        action="append",
        dest="queries",
        help="Query string. Repeat for multiple queries. Defaults to the JJS literature scan set.",
    )
    parser.add_argument("--limit", type=int, default=20, help="Papers per query.")
    parser.add_argument(
        "--delay",
        type=float,
        default=1.25,
        help="Seconds to wait between requests. Keep >=1.0 for a 1 request/s key.",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/literature/semantic_scholar"),
        help="Directory for JSON and CSV outputs.",
    )
    parser.add_argument(
        "--fields",
        default=DEFAULT_FIELDS,
        help="Semantic Scholar fields to request.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="HTTP timeout per request in seconds.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned queries and URLs without making network requests.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    queries = args.queries or DEFAULT_QUERIES
    api_key = os.environ.get("S2_API_KEY")

    if args.delay < 1.0:
        print("Refusing to run with --delay < 1.0 because the approved key is limited to 1 request/s.", file=sys.stderr)
        return 2

    if args.dry_run:
        for query in queries:
            print(make_search_url(query, args.limit, args.fields))
        return 0

    if not api_key:
        print("S2_API_KEY is not set; continuing anonymously, which may hit lower rate limits.", file=sys.stderr)

    args.outdir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for index, query in enumerate(queries, start=1):
        url = make_search_url(query, args.limit, args.fields)
        print(f"[{index}/{len(queries)}] {query}", file=sys.stderr)
        response = fetch_json(url, api_key, args.timeout)
        results.append({"query": query, "url": url, "response": response})
        if index < len(queries):
            time.sleep(args.delay)

    json_path = args.outdir / "s2_results.json"
    csv_path = args.outdir / "s2_results.csv"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(flatten_results(results), csv_path)
    print(f"Wrote {json_path}")
    print(f"Wrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
