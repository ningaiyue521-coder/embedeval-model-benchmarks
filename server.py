"""Loopback-only UI for manual EmbedEval submissions."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from bench import ROOT, SCOPE, Store, catalog, normalize_model


def public_catalog(manifest):
    public = {k: v for k, v in manifest.items() if k != "cases"}
    hidden = {"caseDir", "rulesHash", "buggyHash", "referenceHash"}
    public["cases"] = [{k: v for k, v in item.items() if k not in hidden} for item in manifest["cases"]]
    return public


def make_server(port=8766, db_path=None):
    manifest = catalog()
    store = Store(Path(db_path) if db_path else ROOT / "answers.sqlite3", manifest)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            print(fmt % args, flush=True)

        def respond(self, status, value, kind="application/json; charset=utf-8", download=None):
            if isinstance(value, (dict, list)):
                payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
            elif isinstance(value, str):
                payload = value.encode("utf-8")
            else:
                payload = value
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; connect-src 'self'")
            if download:
                self.send_header("Content-Disposition", f'attachment; filename="{download}"')
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            query = urlparse(self.path)
            params = parse_qs(query.query)
            try:
                if query.path == "/":
                    return self.respond(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
                if query.path == "/api/health":
                    return self.respond(200, {"app": "embedeval-manual", "revision": manifest["revision"], "scope": SCOPE})
                if query.path == "/api/catalog":
                    return self.respond(200, public_catalog(manifest))
                if query.path == "/api/leaderboard":
                    return self.respond(200, store.leaderboard())
                if query.path in {"/api/results", "/api/report"}:
                    model = params.get("model", [""])[0]
                    results = store.results(model, include_answers=True)
                    if query.path == "/api/results":
                        return self.respond(200, results)
                    _, model_key = normalize_model(model)
                    summary = next((row for row in store.leaderboard()
                                    if normalize_model(row["model"])[1] == model_key), None)
                    return self.respond(200, {"model": model, "revision": manifest["revision"],
                                              "scope": SCOPE, "summary": summary,
                                              "results": results}, download="embedeval-first-answers-report.json")
                return self.respond(404, {"error": "Not found"})
            except ValueError as exc:
                return self.respond(400, {"error": str(exc)})
            except Exception as exc:
                return self.respond(500, {"error": str(exc)})

        def do_POST(self):
            if self.path != "/api/submit":
                return self.respond(404, {"error": "Not found"})
            origin = self.headers.get("Origin")
            if origin and origin not in {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}:
                return self.respond(403, {"error": "只接受本地评分页面的提交"})
            if not self.headers.get("Content-Type", "").startswith("application/json"):
                return self.respond(415, {"error": "Expected JSON"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 2_000_000:
                    return self.respond(413, {"error": "提交大小不合法"})
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict) or any(not isinstance(data.get(k), str) for k in ["model", "caseKey", "answer"]):
                    raise ValueError("缺少模型名称、题目或首次答案")
                result, created = store.submit(data["model"], data["caseKey"], data["answer"])
                return self.respond(201 if created else 200, result)
            except FileExistsError as exc:
                return self.respond(409, {"error": str(exc)})
            except (ValueError, json.JSONDecodeError) as exc:
                return self.respond(400, {"error": str(exc)})
            except Exception as exc:
                return self.respond(500, {"error": str(exc)})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--db", default=None)
    args = parser.parse_args()
    server = make_server(args.port, args.db)
    print(f"EmbedEval manual UI: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
