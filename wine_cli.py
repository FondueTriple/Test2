import argparse
from wine_cellar import WineCellar


def main():
    parser = argparse.ArgumentParser(description="Manage your wine cellar")
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add", help="Add a new bottle")
    add_parser.add_argument("name", help="Name of the wine")
    add_parser.add_argument("year", type=int, help="Vintage year")

    remove_parser = subparsers.add_parser("remove", help="Remove a bottle")
    remove_parser.add_argument("id", type=int, help="ID of the bottle to remove")

    comment_parser = subparsers.add_parser("comment", help="Add comment to a bottle")
    comment_parser.add_argument("id", type=int, help="Bottle ID")
    comment_parser.add_argument("text", help="Comment text")

    subparsers.add_parser("list", help="List all bottles")

    args = parser.parse_args()
    cellar = WineCellar()

    if args.command == "add":
        bottle = cellar.add_bottle(args.name, args.year)
        print(
            f"Added bottle {bottle.id}: {bottle.name} ({bottle.year}) - {bottle.vivino_url}"
        )
    elif args.command == "remove":
        if cellar.remove_bottle(args.id):
            print("Bottle removed")
        else:
            print("Bottle not found")
    elif args.command == "comment":
        try:
            cellar.add_comment(args.id, args.text)
            print("Comment added")
        except KeyError:
            print("Bottle not found")
    elif args.command == "list":
        for b in cellar.list_bottles():
            print(f"{b.id}: {b.name} ({b.year}) - {b.vivino_url}")
            for c in b.comments:
                print(f"  - {c}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
