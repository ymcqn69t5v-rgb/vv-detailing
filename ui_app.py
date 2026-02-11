#!/usr/bin/env python3
"""Jednoduchá web aplikace (bez externích dependency) pro company lookup."""

from __future__ import annotations

import argparse
import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from company_lookup import run_demo, run_search, rows_to_dicts

ROOT = Path(__file__).resolve().parent


def resolve_ui_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")) / "ui"
    return ROOT / "ui"


UI_DIR = resolve_ui_dir()


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
        if self.path == "/favicon.ico":
            return self._send(204, b"", "image/x-icon")
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

            # Pokud je zapnutý strict + externí zdroje a nic se nenašlo,
            # zkusíme ne-striktní režim a vrátíme alespoň potenciální kontakty.
            if (not demo) and use_external_sources and strict and not rows:
                relaxed_rows = run_search(
                    city=city,
                    limit=limit,
                    verify_url="https://www.o2.cz/podpora/volani-z-mobilu/overte-si-operatora",
                    strict=False,
                    max_source_pages=max_source_pages,
                    use_external_sources=True,
                )
                if relaxed_rows:
                    return self._send_json(
                        200,
                        {
                            "ok": True,
                            "rows": rows_to_dicts(relaxed_rows),
                            "message": (
                                "Strict filtr nenašel žádný výsledek. "
                                "Zobrazuji ne-striktní výsledky (operátor nemusí být ověřen)."
                            ),
                        },
                    )

            return self._send_json(200, {"ok": True, "rows": rows_to_dicts(rows)})
        except RuntimeError as exc:
            # Typicky síťový problém (ARES/O2 nedostupné). Vracíme srozumitelnou zprávu bez 500.
            return self._send_json(
                200,
                {
                    "ok": False,
                    "error": (
                        "Nepodařilo se načíst živá data (ARES/O2 nebo síť). "
                        "Zkus zapnout Demo režim, nebo ověř připojení k internetu.\n"
                        f"Detail: {exc}"
                    ),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return self._send_json(500, {"ok": False, "error": f"Interní chyba serveru: {exc}"})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Spuštění lokálního UI serveru")
    parser.add_argument("--host", default="127.0.0.1", help="Host bind (výchozí: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Port serveru (výchozí: 8765)")
    parser.add_argument("--no-open-browser", action="store_true", help="Neotevírat automaticky prohlížeč")
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

    app_url = f"http://{host}:{port}"
    print(f"Server běží. Otevři v prohlížeči: {app_url}")
    print("Pokud vidíš jinou službu (např. EDB/Postgres), máš otevřený špatný port.")
    print("Ukončení: Ctrl+C")

    if not args.no_open_browser:
        threading.Timer(1.2, lambda: webbrowser.open(app_url)).start()

    server.serve_forever()


if __name__ == "__main__":
    main()
