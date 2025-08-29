from wsgiref.simple_server import make_server
from urllib.parse import parse_qs
from html import escape
from typing import Dict, Tuple

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


def response(start, status: str, body: str, headers: Tuple[Tuple[str, str], ...] = ()):
    b = body.encode("utf-8")
    start(status, (("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(b)))) + headers)
    return [b]


def redirect(start, location: str):
    start("303 See Other", (("Location", location),))
    return [b""]


def page(title: str, body: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang=\"fr\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{escape(title)}</title>
    <style>
      body {{ font-family: system-ui, Arial, sans-serif; margin: 2rem; }}
      h1 {{ margin-bottom: 1rem; }}
      table {{ border-collapse: collapse; width: 100%; max-width: 1000px; }}
      th, td {{ padding: .5rem .75rem; border-bottom: 1px solid #eee; text-align: left; }}
      form.inline {{ display: inline; margin: 0; }}
      .row {{ margin: .5rem 0; }}
      .btn {{ padding: .35rem .6rem; border: 1px solid #888; border-radius: .3rem; background: #fafafa; cursor: pointer; }}
      .btn.danger {{ border-color: #c33; color: #c33; }}
      .muted {{ color: #666; }}
      .container {{ max-width: 1000px; }}
      input[type=text], input[type=number] {{ padding: .35rem .5rem; border: 1px solid #ccc; border-radius: .25rem; }}
      .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
      @media (max-width: 720px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    </style>
  </head>
  <body>
    <div class=\"container\">
      <h1>{escape(title)}</h1>
      <p><a href=\"/\">Liste des bouteilles</a> · <a href=\"/add\">Ajouter</a></p>
      {body}
    </div>
  </body>
</html>
"""


def list_view():
    rows = []
    for b in sorted(cellar.list_bottles(), key=lambda x: (x.year, x.name)):
        comments = "".join(f"<div class=\"muted\">• {escape(c)}</div>" for c in b.comments)
        rows.append(
            f"""
            <tr>
              <td>{b.id}</td>
              <td><strong>{escape(b.name)}</strong><br><span class=\"muted\">{b.vivino_url and f'<a href=\"{escape(b.vivino_url)}\" target=\"_blank\" rel=\"noopener\">Vivino</a>' or ''}</span></td>
              <td>{b.year}</td>
              <td>{comments or '<span class=\"muted\">(aucun)</span>'}</td>
              <td>
                <form class=\"inline\" method=\"get\" action=\"/edit\">
                  <input type=\"hidden\" name=\"id\" value=\"{b.id}\" />
                  <button class=\"btn\" type=\"submit\">Éditer</button>
                </form>
                <form class=\"inline\" method=\"post\" action=\"/delete\" onsubmit=\"return confirm('Supprimer cette bouteille ?');\">
                  <input type=\"hidden\" name=\"id\" value=\"{b.id}\" />
                  <button class=\"btn danger\" type=\"submit\">Supprimer</button>
                </form>
              </td>
            </tr>
            """
        )
    body = f"""
      <table>
        <thead>
          <tr><th>ID</th><th>Nom</th><th>Millésime</th><th>Commentaires</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {''.join(rows) or '<tr><td colspan=5 class=\'muted\'>Aucune bouteille</td></tr>'}
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
        <div class=\"row\"><button class=\"btn\" type=\"submit\">Enregistrer</button></div>
      </form>
      <h3>Commentaires</h3>
      <ul>{comments}</ul>
      <form method=\"post\" action=\"/comment\" class=\"row\">
        <input type=\"hidden\" name=\"id\" value=\"{b.id}\" />
        <input type=\"text\" name=\"text\" placeholder=\"Ajouter un commentaire\" required />
        <button class=\"btn\" type=\"submit\">Ajouter</button>
      </form>
    """
    return page(f"Éditer: {b.name}", body)


def app(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/") or "/"

    # ROUTES
    if method == "GET" and path == "/":
        return response(start_response, "200 OK", list_view())

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
        cellar.add_bottle(name, year)
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
        try:
            year = int(year_raw)
        except ValueError:
            return response(start_response, "400 Bad Request", page("Erreur", "<p>Millésime invalide.</p>"))
        cellar.edit_bottle(bid, name=name, year=year)
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

    return response(start_response, "404 Not Found", page("404", "<p>Page introuvable.</p>"))


def main(host: str = "127.0.0.1", port: int = 8000):
    with make_server(host, port, app) as httpd:
        print(f"Serving on http://{host}:{port} …")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server…")


if __name__ == "__main__":
    main()

