from wsgiref.simple_server import make_server
from wsgiref.validate import validator
from urllib.parse import parse_qs, quote_plus
from html import escape
from typing import Dict, Iterable, Tuple, Optional
import re
import urllib.request
import urllib.error
import socket

from wine_cellar import WineCellar


cellar = WineCellar()


def read_post(environ) -> Dict[str, str]:
    try:
        size = int(environ.get("CONTENT_LENGTH", 0))
    except (TypeError, ValueError):
        size = 0
    data = environ["wsgi.input"].read(size) if size > 0 else b""
    fields = {}
    for k, v in parse_qs(data.decode("utf-8"), keep_blank_values=True).items():
        fields[k] = v[0]
    return fields


def response(start, status: str, body: str, headers: Optional[Iterable[Tuple[str, str]]] = None):
    b = body.encode("utf-8")
    base = [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(b)))]
    extra = list(headers) if headers is not None else []
    start(status, base + extra)
    return [b]


def redirect(start, location: str):
    # Ensure Content-Length is set by using response helper
    return response(start, "303 See Other", "", headers=[("Location", location)])


def page(title: str, body: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang=\"fr\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{escape(title)}</title>
    <style>
      :root {{
        --bg: #0f0b0a;
        --panel: #1b1513;
        --panel-2: #231b18;
        --text: #f2ece6;
        --muted: #a39286;
        --line: #2a211e;
        --accent: #c9a227;
        --accent-2: #8b6a2b;
        --danger: #c05858;
      }}
      html, body {{ height: 100%; }}
      body {{
        margin: 0;
        font-family: Georgia, 'Times New Roman', serif;
        color: var(--text);
        background:
          radial-gradient(1200px 800px at 10% -20%, #241915 0%, transparent 65%),
          radial-gradient(1200px 800px at 110% 120%, #271d19 0%, transparent 65%),
          linear-gradient(180deg, #100c0a 0%, #0b0908 100%);
      }}
      a {{ color: var(--accent); text-decoration: none; }}
      a:hover {{ text-decoration: underline; }}
      .container {{
        max-width: 1100px;
        margin: 2rem auto;
        padding: 2rem;
        background: linear-gradient(180deg, var(--panel) 0%, var(--panel-2) 100%);
        border: 1px solid var(--line);
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,.4), inset 0 1px 0 rgba(255,255,255,.04);
      }}
      h1 {{
        margin: 0 0 1.25rem 0;
        font-weight: 600;
        letter-spacing: .5px;
      }}
      .subnav {{ margin-bottom: 1rem; color: var(--muted); }}
      .subnav a {{ color: var(--muted); }}
      .subnav a.active {{ color: var(--accent); font-weight: 600; }}

      table {{ border-collapse: collapse; width: 100%; }}
      thead th {{
        font-weight: 600;
        color: var(--text);
        text-align: left;
        border-bottom: 2px solid var(--line);
        padding: .75rem .75rem;
        background: rgba(255,255,255,0.02);
      }}
      tbody td {{
        padding: .6rem .75rem;
        border-bottom: 1px solid var(--line);
        vertical-align: top;
      }}
      .muted {{ color: var(--muted); }}
      .cell-name small {{ display: inline-block; margin-top: .25rem; }}
      .actions {{ white-space: nowrap; }}

      .btn {{
        padding: .45rem .7rem;
        border: 1px solid var(--accent-2);
        background: linear-gradient(180deg, rgba(201,162,39,.15), rgba(201,162,39,.05));
        color: var(--text);
        border-radius: 8px;
        cursor: pointer;
      }}
      .btn:hover {{ filter: brightness(1.05); }}
      .btn.danger {{ border-color: var(--danger); color: #ffd9d9; background: linear-gradient(180deg, rgba(192,88,88,.18), rgba(192,88,88,.06)); }}

      form.inline {{ display: inline; margin: 0; }}
      .row {{ margin: .75rem 0; }}
      input[type=text], input[type=number] {{
        width: 100%;
        padding: .5rem .6rem;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #120e0c;
        color: var(--text);
      }}
      label {{ font-size: .95rem; color: var(--muted); }}
      .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
      @media (max-width: 720px) {{ .grid {{ grid-template-columns: 1fr; }} }}

      /* Star rating (fractional) */
      .stars {{ position: relative; display: inline-block; line-height: 1; }}
      .stars .base, .stars .fill {{
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
        letter-spacing: 2px;
        font-size: 1rem;
      }}
      .stars .base {{ color: #4b3f39; }}
      .stars .fill {{
        position: absolute; left: 0; top: 0; overflow: hidden; white-space: nowrap;
        color: var(--accent);
        text-shadow: 0 0 6px rgba(201,162,39,.25);
      }}
    </style>
  </head>
  <body>
    <div class=\"container\">
      <h1>{escape(title)}</h1>
      <p class=\"subnav\"><a class=\"active\" href=\"/\">Liste des bouteilles</a> · <a href=\"/add\">Ajouter</a></p>
      {body}
    </div>
  </body>
</html>
"""


def list_view(info: str = ""):
    rows = []
    for b in sorted(cellar.list_bottles(), key=lambda x: (x.year, x.name)):
        comments = "".join(f"<div class=\"muted\">• {escape(c)}</div>" for c in b.comments)
        rating = getattr(b, 'vivino_rating', 0.0) or 0.0
        pct = max(0, min(5.0, float(rating))) / 5.0 * 100.0
        stars = (
            f"<span class=\"stars\" aria-label=\"Note Vivino: {rating:.1f}/5\">"
            f"<span class=\"base\">★★★★★</span>"
            f"<span class=\"fill\" style=\"width: {pct:.0f}%\">★★★★★</span>"
            f"</span>"
        )
        rows.append(
            f"""
            <tr>
              <td>{b.id}</td>
              <td class=\"cell-name\"><strong>{escape(b.name)}</strong><br><small class=\"muted\">{b.vivino_url and f'<a href=\"{escape(b.vivino_url)}\" target=\"_blank\" rel=\"noopener\">Vivino</a>' or ''}</small></td>
              <td>{b.year}</td>
              <td>{stars} <span class=\"muted\">{(rating and f'{rating:.1f}') or ''}</span></td>
              <td>{comments or '<span class=\"muted\">(aucun)</span>'}</td>
              <td class=\"actions\">
                <form class=\"inline\" method=\"post\" action=\"/fetch_rating\">\n                  <input type=\"hidden\" name=\"id\" value=\"{b.id}\" />\n                  <button class=\"btn\" type=\"submit\" title=\"Mettre à jour la note automatiquement\">↻ Note</button>\n                </form>
                <form class=\"inline\" method=\"get\" action=\"/edit\">\n                  <input type=\"hidden\" name=\"id\" value=\"{b.id}\" />\n                  <button class=\"btn\" type=\"submit\">Éditer</button>\n                </form>
                <form class=\"inline\" method=\"post\" action=\"/delete\" onsubmit=\"return confirm('Supprimer cette bouteille ?');\">\n                  <input type=\"hidden\" name=\"id\" value=\"{b.id}\" />\n                  <button class=\"btn danger\" type=\"submit\">Supprimer</button>\n                </form>
              </td>
            </tr>
            """
        )
    flash = f"<p class=\"muted\">{escape(info)}</p>" if info else ""
    body = f"""
      {flash}
      <div class=\"row\">
        <form method=\"post\" action=\"/fetch_all_ratings\" class=\"inline\">
          <button class=\"btn\" type=\"submit\">↻ Mettre à jour toutes les notes</button>
        </form>
      </div>
      <table>
        <thead>
          <tr><th>ID</th><th>Nom</th><th>Millésime</th><th>Note</th><th>Commentaires</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {''.join(rows) or '<tr><td colspan=6 class=\'muted\'>Aucune bouteille</td></tr>'}
        </tbody>
      </table>
      <h2>Ajouter une bouteille</h2>
      <form method=\"post\" action=\"/add\" class=\"grid\">
        <label>Nom<br><input type=\"text\" name=\"name\" required /></label>
        <label>Millésime<br><input type=\"number\" name=\"year\" min=\"1900\" max=\"2100\" required /></label>
        <div class=\"row\"><button class=\"btn\" type=\"submit\">Ajouter</button></div>
      </form>
    """
    return page("Cave à vins", body)


def edit_view(bottle_id: int):
    b = cellar.bottles.get(bottle_id)
    if not b:
        return page("Introuvable", "<p>Bouteille introuvable.</p>")
    comments = "".join(f"<li>{escape(c)}</li>" for c in b.comments) or "<li class=\"muted\">(aucun)</li>"
    body = f"""
      <h2>Éditer</h2>
      <form method=\"post\" action=\"/edit\" class=\"grid\">
        <input type=\"hidden\" name=\"id\" value=\"{b.id}\" />
        <label>Nom<br><input type=\"text\" name=\"name\" value=\"{escape(b.name)}\" required /></label>
        <label>Millésime<br><input type=\"number\" name=\"year\" value=\"{b.year}\" min=\"1900\" max=\"2100\" required /></label>
        <label>Note Vivino (0–5)<br><input type=\"number\" name=\"vivino_rating\" step=\"0.1\" min=\"0\" max=\"5\" value=\"{getattr(b, 'vivino_rating', 0.0):.1f}\" /></label>
        <div class=\"row\"><button class=\"btn\" type=\"submit\">Enregistrer</button>
          <form class=\"inline\" method=\"post\" action=\"/fetch_rating\">\n            <input type=\"hidden\" name=\"id\" value=\"{b.id}\" />\n            <button class=\"btn\" type=\"submit\">↻ Mettre à jour automatiquement</button>\n          </form>
        </div>
      </form>
      <h3>Commentaires</h3>
      <ul>{comments}</ul>
      <form method=\"post\" action=\"/comment\" class=\"row\">\n        <input type=\"hidden\" name=\"id\" value=\"{b.id}\" />\n        <input type=\"text\" name=\"text\" placeholder=\"Ajouter un commentaire\" required />\n        <button class=\"btn\" type=\"submit\">Ajouter</button>\n      </form>
    """
    return page(f"Éditer: {b.name}", body)


def app(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/") or "/"

    # ROUTES
    if method == "GET" and path == "/":
        qs = parse_qs(environ.get("QUERY_STRING", ""))
        info = (qs.get("info") or [""])[0]
        return response(start_response, "200 OK", list_view(info))

    if method == "GET" and path == "/add":
        return response(start_response, "200 OK", list_view())

    if method == "POST" and path == "/add":
        form = read_post(environ)
        name = (form.get("name") or "").strip()
        year_raw = (form.get("year") or "").strip()
        try:
            year = int(year_raw)
        except ValueError:
            return response(start_response, "400 Bad Request", page("Erreur", "<p>Millésime invalide.</p>"))
        if not name:
            return response(start_response, "400 Bad Request", page("Erreur", "<p>Nom requis.</p>"))
        bottle = cellar.add_bottle(name, year)
        # Attempt immediate rating fetch (best-effort)
        try:
            fetch_and_update_rating(bottle.id)
        except Exception:
            pass
        return redirect(start_response, "/")

    if method == "GET" and path == "/edit":
        qs = parse_qs(environ.get("QUERY_STRING", ""))
        try:
            bid = int((qs.get("id") or [""])[0])
        except ValueError:
            return response(start_response, "400 Bad Request", page("Erreur", "<p>ID invalide.</p>"))
        return response(start_response, "200 OK", edit_view(bid))

    if method == "POST" and path == "/edit":
        form = read_post(environ)
        try:
            bid = int(form.get("id", ""))
        except ValueError:
            return response(start_response, "400 Bad Request", page("Erreur", "<p>ID invalide.</p>"))
        name = (form.get("name") or "").strip()
        year_raw = (form.get("year") or "").strip()
        rating_raw = (form.get("vivino_rating") or "").strip()
        try:
            year = int(year_raw)
        except ValueError:
            return response(start_response, "400 Bad Request", page("Erreur", "<p>Millésime invalide.</p>"))
        rating: Optional[float]
        if rating_raw == "":
            rating = None
        else:
            try:
                rating = float(rating_raw)
            except ValueError:
                return response(start_response, "400 Bad Request", page("Erreur", "<p>Note Vivino invalide.</p>"))
        cellar.edit_bottle(bid, name=name, year=year, vivino_rating=rating)
        return redirect(start_response, f"/edit?id={bid}")

    if method == "POST" and path == "/delete":
        form = read_post(environ)
        try:
            bid = int(form.get("id", ""))
        except ValueError:
            return response(start_response, "400 Bad Request", page("Erreur", "<p>ID invalide.</p>"))
        cellar.remove_bottle(bid)
        return redirect(start_response, "/")

    if method == "POST" and path == "/comment":
        form = read_post(environ)
        try:
            bid = int(form.get("id", ""))
        except ValueError:
            return response(start_response, "400 Bad Request", page("Erreur", "<p>ID invalide.</p>"))
        text = (form.get("text") or "").strip()
        if text:
            try:
                cellar.add_comment(bid, text)
            except KeyError:
                pass
        return redirect(start_response, f"/edit?id={bid}")

    if method == "POST" and path == "/fetch_all_ratings":
        ok, fail = fetch_all_and_counts()
        msg = f"Notes mises à jour: {ok} succès, {fail} échecs"
        return redirect(start_response, f"/?info={quote_plus(msg)}")

    if method == "POST" and path == "/fetch_rating":
        form = read_post(environ)
        try:
            bid = int(form.get("id", ""))
        except ValueError:
            return response(start_response, "400 Bad Request", page("Erreur", "<p>ID invalide.</p>"))
        # Try to fetch and update rating; ignore details in UI, redirect back
        try:
            fetch_and_update_rating(bid)
        except Exception:
            pass
        return redirect(start_response, f"/edit?id={bid}")

    return response(start_response, "404 Not Found", page("404", "<p>Page introuvable.</p>"))


# ---- Vivino rating fetcher (best-effort, HTML heuristics) ----
def fetch_and_update_rating(bottle_id: int) -> Tuple[bool, str]:
    b = cellar.bottles.get(bottle_id)
    if not b:
        return False, "Bouteille introuvable"
    url = b.vivino_url
    if not url:
        return False, "Lien Vivino manquant"
    try:
        html = http_get(url)
    except Exception as e:
        return False, f"Échec HTTP: {e}"
    rating = parse_vivino_rating(html)
    # If rating not found on search page, try following the first wine link (/w/<id>)
    if rating is None:
        m = re.search(r"href=\"(https?://[^\"]+?/w/\d+[^\"]*)\"", html)
        if not m:
            m = re.search(r"href=\"(/[^\"]+?/w/\d+[^\"]*)\"", html)
            base = "https://www.vivino.com"
            wine_url = base + m.group(1) if m else None
        else:
            wine_url = m.group(1)
        if wine_url:
            try:
                html2 = http_get(wine_url)
                rating = parse_vivino_rating(html2)
            except Exception:
                pass
    if rating is None:
        return False, "Note introuvable sur la page Vivino"
    cellar.edit_bottle(bottle_id, vivino_rating=rating)
    return True, f"Note mise à jour: {rating:.1f}/5"


def http_get(url: str, timeout: float = 6.0) -> str:
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


def parse_vivino_rating(html: str) -> Optional[float]:
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


def fetch_all_and_counts() -> Tuple[int, int]:
    ok = fail = 0
    for b in cellar.list_bottles():
        try:
            success, _ = fetch_and_update_rating(b.id)
            if success:
                ok += 1
            else:
                fail += 1
        except Exception:
            fail += 1
    return ok, fail


def main(host: str = "127.0.0.1", port: int = 8000):
    with make_server(host, port, validator(app)) as httpd:
        print(f"Serving on http://{host}:{port} …")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server…")


if __name__ == "__main__":
    main()
