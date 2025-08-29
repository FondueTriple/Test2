from wine_cellar import WineCellar


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
                print(f"{b.id}: {b.name} ({b.year}) - {b.vivino_url}")
                for c in b.comments:
                    print(f"  - {c}")
        elif choice == "2":
            name = input("Nom: ")
            year = int(input("Millésime: "))
            bottle = cellar.add_bottle(name, year)
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
            cellar.edit_bottle(bottle_id, name=new_name, year=new_year)
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
