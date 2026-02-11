#!/usr/bin/env python3
"""Jednoduchá web aplikace (bez externích dependency) pro company lookup."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from company_lookup import run_demo, run_search, rows_to_dicts

ROOT = Path(__file__).resolve().parent
UI_DIR = ROOT / "ui"


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload: dict) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            return self._serve_file(UI_DIR / "index.html", "text/html; charset=utf-8")
        if self.path == "/app.css":
            return self._serve_file(UI_DIR / "app.css", "text/css; charset=utf-8")
        if self.path == "/app.js":
            return self._serve_file(UI_DIR / "app.js", "application/javascript; charset=utf-8")
        if self.path == "/api/health":
            return self._send_json(200, {"ok": True})
        return self._send_json(404, {"ok": False, "error": "Not found"})

    def _serve_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self._send_json(404, {"ok": False, "error": f"Missing file: {path.name}"})
            return
        self._send(200, path.read_bytes(), content_type)

    def do_POST(self) -> None:
        if self.path != "/api/search":
            return self._send_json(404, {"ok": False, "error": "Not found"})

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            city = str(payload.get("city", "")).strip()
            if not city:
                return self._send_json(400, {"ok": False, "error": "Město je povinné."})

            limit = int(payload.get("limit", 20))
            max_source_pages = int(payload.get("max_source_pages", 4))
            strict = bool(payload.get("strict", True))
            demo = bool(payload.get("demo", False))
            use_external_sources = bool(payload.get("use_external_sources", False))

            if limit <= 0 or max_source_pages <= 0:
                return self._send_json(400, {"ok": False, "error": "limit a max_source_pages musí být > 0"})

            rows = run_demo() if demo else run_search(
                city=city,
                limit=limit,
                verify_url="https://www.o2.cz/podpora/volani-z-mobilu/overte-si-operatora",
                strict=strict,
                max_source_pages=max_source_pages,
                use_external_sources=use_external_sources,
            )

            return self._send_json(200, {"ok": True, "rows": rows_to_dicts(rows)})
        except Exception as exc:  # noqa: BLE001
            return self._send_json(500, {"ok": False, "error": str(exc)})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Spuštění lokálního UI serveru")
    parser.add_argument("--host", default="127.0.0.1", help="Host bind (výchozí: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Port serveru (výchozí: 8765)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.port <= 0 or args.port > 65535:
        raise SystemExit("Port musí být v rozsahu 1-65535.")

    host, port = args.host, args.port
    try:
        server = ThreadingHTTPServer((host, port), Handler)
    except OSError as exc:
        raise SystemExit(
            f"Nepodařilo se spustit server na {host}:{port}. "
            f"Port je pravděpodobně obsazený. Zkus třeba: python ui_app.py --port 8877\n{exc}"
        ) from exc

    print(f"Server běží. Otevři v prohlížeči: http://{host}:{port}")
    print("Pokud vidíš jinou službu (např. EDB/Postgres), máš otevřený špatný port.")
    print("Ukončení: Ctrl+C")
    server.serve_forever()


if __name__ == "__main__":
    main()
