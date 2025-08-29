# Gestion de cave à vins

Cette application simple permet de gérer votre cave à vins en ligne de commande.

## Fonctionnalités
- Ajouter une bouteille avec son millésime
- Supprimer une bouteille
- Ajouter des commentaires sur une bouteille
- Lien automatique vers la recherche Vivino pour voir les notes

Les données sont stockées dans un fichier `cellar.json`.

## Utilisation

```bash
python wine_cli.py add "Chateau Margaux" 2015
python wine_cli.py list
python wine_cli.py comment 1 "Très bon"
python wine_cli.py remove 1
```

## Tests

Exécuter les tests avec:

```bash
pytest
```

## Interface utilisateur

Un petit menu interactif est disponible pour gérer la cave directement depuis le terminal:

```bash
python wine_ui.py
```

## Interface web

Deux options sont disponibles:

- Sans dépendances (WSGI simple): `python wine_web.py` → ouvrir `http://127.0.0.1:8000`
- Version Flask (recommandée): instructions ci‑dessous

### Version Flask

Installation des dépendances (dans votre venv):

```bash
pip install -r requirements.txt
```

Lancer le serveur de développement:

```bash
python app_flask.py
```

Puis ouvrir `http://127.0.0.1:5000` dans votre navigateur pour lister, ajouter, éditer, commenter et supprimer des bouteilles.
