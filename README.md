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
