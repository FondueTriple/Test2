# Gestion de cave Ã  vins

Cette application simple permet de gÃ©rer votre cave Ã  vins en ligne de commande.

## FonctionnalitÃ©s
- Ajouter une bouteille avec son millÃ©sime
- Supprimer une bouteille
- Ajouter des commentaires sur une bouteille
- Lien automatique vers la recherche Vivino pour voir les notes

Les donnÃ©es sont stockÃ©es dans un fichier `cellar.json`.

## Utilisation

```bash
python wine_cli.py add "Chateau Margaux" 2015
python wine_cli.py list
python wine_cli.py comment 1 "TrÃ¨s bon"
python wine_cli.py remove 1
```

## Tests

ExÃ©cuter les tests avec:

```bash
pytest
```

## Interface utilisateur

Un petit menu interactif est disponible pour gÃ©rer la cave directement depuis le terminal:

```bash
python wine_ui.py
```

## Interface web

Cette version utilise un frontend React (Vite) et une API Flask.

Backend (Flask API):

```bash
pip install -r requirements.txt
python app_flask.py
```

L'API est servie sous `http://127.0.0.1:5000/api/...`.

Frontend (React + Vite):

```bash
cd frontend
npm install
npm run dev
```

Ouvrir `http://127.0.0.1:5173`. Le proxy Vite redirige `/api` vers `http://127.0.0.1:5000`.

Build de production et service par Flask:

```bash
cd frontend && npm run build && cd ..
python app_flask.py
```

Quand `frontend/dist` existe, Flask sert automatiquement l'app React à `/`.
