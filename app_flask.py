from flask import Flask, render_template, request, redirect, url_for
from wine_cellar import WineCellar


app = Flask(__name__)
cellar = WineCellar()


@app.get("/")
def index():
    bottles = sorted(cellar.list_bottles(), key=lambda b: (b.year, b.name))
    return render_template("index.html", bottles=bottles)


@app.post("/add")
def add():
    name = (request.form.get("name") or "").strip()
    year_raw = (request.form.get("year") or "").strip()
    try:
        year = int(year_raw)
    except ValueError:
        return render_template("error.html", message="Millésime invalide"), 400
    if not name:
        return render_template("error.html", message="Nom requis"), 400
    cellar.add_bottle(name, year)
    return redirect(url_for("index"))


@app.get("/edit/<int:bid>")
def edit_view(bid: int):
    bottle = cellar.bottles.get(bid)
    if not bottle:
        return render_template("error.html", message="Bouteille introuvable"), 404
    return render_template("edit.html", b=bottle)


@app.post("/edit/<int:bid>")
def edit_save(bid: int):
    bottle = cellar.bottles.get(bid)
    if not bottle:
        return render_template("error.html", message="Bouteille introuvable"), 404
    name = (request.form.get("name") or "").strip()
    year_raw = (request.form.get("year") or "").strip()
    try:
        year = int(year_raw)
    except ValueError:
        return render_template("error.html", message="Millésime invalide"), 400
    cellar.edit_bottle(bid, name=name, year=year)
    return redirect(url_for("edit_view", bid=bid))


@app.post("/delete/<int:bid>")
def delete(bid: int):
    cellar.remove_bottle(bid)
    return redirect(url_for("index"))


@app.post("/comment/<int:bid>")
def comment(bid: int):
    text = (request.form.get("text") or "").strip()
    if text:
        try:
            cellar.add_comment(bid, text)
        except KeyError:
            return render_template("error.html", message="Bouteille introuvable"), 404
    return redirect(url_for("edit_view", bid=bid))


if __name__ == "__main__":
    # Runs the development server (Flask built-in)
    app.run(debug=True)

