from wine_cellar import WineCellar

COLOR_CODES = {"red": "\033[31m", "white": "\033[33m"}


def main():
    cellar = WineCellar()
    while True:
        print("\nGestion de cave à vins")
        print("1. Lister les bouteilles")
        print("2. Ajouter une bouteille")
        print("3. Éditer une bouteille")
        print("4. Supprimer une bouteille")
        print("5. Quitter")
        choice = input("Choix: ")
        if choice == "1":
            for b in cellar.list_bottles():
                color = COLOR_CODES.get(b.color, "")
                reset = "\033[0m" if color else ""
                print(f"{b.id}: {color}{b.name}{reset} ({b.year}, {b.color}) - {b.vivino_url}")
                for c in b.comments:
                    print(f"  - {c}")
        elif choice == "2":
            name = input("Nom: ")
            year = int(input("Millésime: "))
            color_in = input("Couleur (red/white) [red]: ").strip().lower() or "red"
            bottle = cellar.add_bottle(name, year, color=color_in)
            print(f"Bouteille ajoutée {bottle.id}")
        elif choice == "3":
            try:
                bottle_id = int(input("ID de la bouteille: "))
            except ValueError:
                print("ID invalide")
                continue
            bottle = cellar.bottles.get(bottle_id)
            if not bottle:
                print("Bouteille introuvable")
                continue
            new_name = input(f"Nouveau nom [{bottle.name}]: ") or bottle.name
            year_input = input(f"Nouveau millésime [{bottle.year}]: ")
            new_year = int(year_input) if year_input else bottle.year
            color_in = input(f"Nouvelle couleur [{bottle.color}]: ").strip().lower() or bottle.color
            cellar.edit_bottle(bottle_id, name=new_name, year=new_year, color=color_in)
            print("Bouteille mise à jour")
        elif choice == "4":
            try:
                bottle_id = int(input("ID de la bouteille: "))
            except ValueError:
                print("ID invalide")
                continue
            if cellar.remove_bottle(bottle_id):
                print("Bouteille supprimée")
            else:
                print("Bouteille introuvable")
        elif choice == "5":
            break
        else:
            print("Choix invalide")


if __name__ == "__main__":
    main()
