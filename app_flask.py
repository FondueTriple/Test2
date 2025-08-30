from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
from typing import Any, Dict
from wine_cellar import WineCellar, Bottle
import re
import urllib.request
import urllib.error
import socket


app = Flask(__name__, static_folder=None)
cellar = WineCellar()


###############################################
# JSON API for React frontend                 #
###############################################

def bottle_to_dict(b: Bottle) -> Dict[str, Any]:
    return {
        "id": b.id,
        "name": b.name,
        "year": b.year,
        "comments": list(b.comments),
        "vivino_url": b.vivino_url,
        "vivino_rating": getattr(b, "vivino_rating", 0.0),
        "pos_row": b.pos_row,
        "pos_col": b.pos_col,
        "color": getattr(b, "color", "white"),
    }


@app.get("/api/bottles")
def api_list_bottles():
    bottles = sorted(cellar.list_bottles(), key=lambda b: (b.year, b.name))
    return jsonify([bottle_to_dict(b) for b in bottles])


@app.post("/api/bottles")
def api_add_bottle():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    year = data.get("year")
    color = (data.get("color") or "white").strip().lower()
    if not name:
        return jsonify({"error": "name is required"}), 400
    try:
        year_i = int(year)
    except Exception:
        return jsonify({"error": "year must be an integer"}), 400
    b = cellar.add_bottle(name, year_i, color=color)
    return jsonify(bottle_to_dict(b)), 201


@app.put("/api/bottles/<int:bid>")
def api_edit_bottle(bid: int):
    if bid not in cellar.bottles:
        return jsonify({"error": "not found"}), 404
    data = request.get_json(silent=True) or {}
    kwargs: Dict[str, Any] = {}
    if "name" in data:
        kwargs["name"] = (data.get("name") or "").strip()
    if "year" in data:
        try:
            kwargs["year"] = int(data.get("year"))
        except Exception:
            return jsonify({"error": "year must be an integer"}), 400
    if "vivino_rating" in data:
        try:
            kwargs["vivino_rating"] = float(data.get("vivino_rating"))
        except Exception:
            return jsonify({"error": "vivino_rating must be a number"}), 400
    if "pos_row" in data or "pos_col" in data:
        pr = data.get("pos_row")
        pc = data.get("pos_col")
        kwargs["pos_row"] = int(pr) if pr is not None and pr != "" else None
        kwargs["pos_col"] = int(pc) if pc is not None and pc != "" else None
    if "color" in data:
        kwargs["color"] = (data.get("color") or "").strip().lower()
    cellar.edit_bottle(bid, **kwargs)
    return jsonify(bottle_to_dict(cellar.bottles[bid]))


@app.delete("/api/bottles/<int:bid>")
def api_delete_bottle(bid: int):
    ok = cellar.remove_bottle(bid)
    if not ok:
        return jsonify({"error": "not found"}), 404
    return ("", 204)


@app.post("/api/bottles/<int:bid>/comments")
def api_add_comment(bid: int):
    if bid not in cellar.bottles:
        return jsonify({"error": "not found"}), 404
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text is required"}), 400
    cellar.add_comment(bid, text)
    return jsonify(bottle_to_dict(cellar.bottles[bid]))


# ---- Vivino rating fetcher (best-effort, HTML heuristics) ----
def _http_get(url: str, timeout: float = 6.0) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.8,en-US;q=0.6,en;q=0.4",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}") from e
    except urllib.error.URLError as e:
        if isinstance(e.reason, socket.timeout):
            raise RuntimeError("timeout") from e
        raise RuntimeError(str(e.reason)) from e


def _parse_vivino_rating(html: str):
    # 1) Try JSON-LD aggregateRating
    for m in re.finditer(r"aggregateRating[\s\S]{0,200}?ratingValue\s*[:\"]\s*([0-9]+(?:\.[0-9]+)?)", html, re.IGNORECASE):
        try:
            val = float(m.group(1))
            if 0.0 <= val <= 5.0:
                return val
        except ValueError:
            pass
    # 2) ratingsAverage key often present in embedded JSON
    m = re.search(r"ratingsAverage\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)", html)
    if m:
        try:
            val = float(m.group(1))
            if 0.0 <= val <= 5.0:
                return val
        except ValueError:
            pass
    # 3) Loose text near 'rating'/'note' with 3.0-5.0
    for m in re.finditer(r"(?i)(rating|note)[^\n]{0,40}?([3-5](?:\.[0-9])?)", html):
        try:
            val = float(m.group(2))
            if 0.0 <= val <= 5.0:
                return val
        except ValueError:
            pass
    # 4) Find standalone number with /5
    m = re.search(r"([0-5](?:\.[0-9])?)\s*/\s*5", html)
    if m:
        try:
            val = float(m.group(1))
            if 0.0 <= val <= 5.0:
                return val
        except ValueError:
            pass
    return None


def _fetch_and_update_rating(bottle_id: int):
    b = cellar.bottles.get(bottle_id)
    if not b:
        return False, "Bouteille introuvable"
    url = b.vivino_url
    if not url:
        return False, "Lien Vivino manquant"
    try:
        html = _http_get(url)
    except Exception as e:
        return False, f"Ã©chec HTTP: {e}"
    rating = _parse_vivino_rating(html)
    # If rating not found on search page, try following the first wine link (/w/<id>)
    if rating is None:
        m = re.search(r"href=\"(https?://[^\"]+?/w/\d+[^\"]*)\"", html)
        if not m:
            m2 = re.search(r"href=\"(/[^\"]+?/w/\d+[^\"]*)\"", html)
            wine_url = ("https://www.vivino.com" + m2.group(1)) if m2 else None
        else:
            wine_url = m.group(1)
        if wine_url:
            try:
                html2 = _http_get(wine_url)
                rating = _parse_vivino_rating(html2)
            except Exception:
                pass
    if rating is None:
        return False, "Note introuvable sur la page Vivino"
    cellar.edit_bottle(bottle_id, vivino_rating=rating)
    return True, f"Note mise Ã  jour: {rating:.1f}/5"


@app.post("/api/bottles/<int:bid>/fetch-rating")
def api_fetch_rating(bid: int):
    ok, msg = _fetch_and_update_rating(bid)
    if not ok:
        return jsonify({"error": msg}), 400
    return jsonify(bottle_to_dict(cellar.bottles[bid]))


@app.post("/api/bottles/fetch-all-ratings")
def api_fetch_all_ratings():
    ok = fail = 0
    for b in cellar.list_bottles():
        try:
            success, _ = _fetch_and_update_rating(b.id)
            ok += 1 if success else 0
            fail += 0 if success else 1
        except Exception:
            fail += 1
    return jsonify({"updated": ok, "failed": fail})


###############################################
# Serve React build (frontend/dist)            #
###############################################

DIST_DIR = Path(__file__).parent / "frontend" / "dist"


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path: str):
    """Serve the React single-page app build in production.

    - If frontend/dist exists, serve static files from there.
    - Otherwise, show a simple message pointing to dev instructions.
    """
    if DIST_DIR.exists():
        # Preserve API routes
        if path.startswith("api/"):
            return ("Not Found", 404)
        # Try to serve the static file
        target = DIST_DIR / path
        if path and target.exists():
            return send_from_directory(str(DIST_DIR), path)
        # Fallback to index.html for SPA routes
        return send_from_directory(str(DIST_DIR), "index.html")
    return (
        "<h1>Frontend not built</h1><p>Run the React dev server from frontend/ or build with npm run build.</p>",
        200,
        {"Content-Type": "text/html; charset=utf-8"},
    )


if __name__ == "__main__":
    # Runs the development server (Flask built-in)
    # For local development with React dev server, enable CORS via a simple header
    @app.after_request
    def add_cors_headers(resp):
        # Allow Vite dev server default port
        resp.headers.setdefault("Access-Control-Allow-Origin", "http://localhost:5173")
        resp.headers.setdefault("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        resp.headers.setdefault("Access-Control-Allow-Headers", "Content-Type")
        return resp

    app.run(debug=True)

