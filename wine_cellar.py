from dataclasses import dataclass, field, asdict
from typing import List, Dict
import json
import urllib.parse


@dataclass
class Bottle:
    id: int
    name: str
    year: int
    comments: List[str] = field(default_factory=list)
    vivino_url: str = ""


class WineCellar:
    """Simple wine cellar manager with JSON persistence."""

    def __init__(self, filepath: str = "cellar.json"):
        self.filepath = filepath
        self.bottles: Dict[int, Bottle] = {}
        self._next_id = 1
        self.load()

    def load(self) -> None:
        """Load cellar information from JSON file."""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.bottles = {int(b["id"]): Bottle(**b) for b in data.get("bottles", [])}
            self._next_id = data.get("next_id", max(self.bottles.keys(), default=0) + 1)
        except FileNotFoundError:
            self.bottles = {}
            self._next_id = 1

    def save(self) -> None:
        """Persist current cellar to JSON file."""
        data = {
            "next_id": self._next_id,
            "bottles": [asdict(b) for b in self.bottles.values()],
        }
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def add_bottle(self, name: str, year: int) -> Bottle:
        bottle = Bottle(
            id=self._next_id,
            name=name,
            year=year,
            vivino_url=generate_vivino_url(name, year),
        )
        self.bottles[bottle.id] = bottle
        self._next_id += 1
        self.save()
        return bottle

    def remove_bottle(self, bottle_id: int) -> bool:
        if bottle_id in self.bottles:
            del self.bottles[bottle_id]
            self.save()
            return True
        return False

    def add_comment(self, bottle_id: int, comment: str) -> None:
        bottle = self.bottles.get(bottle_id)
        if bottle is None:
            raise KeyError(f"Bottle {bottle_id} not found")
        bottle.comments.append(comment)
        self.save()

    def list_bottles(self) -> List[Bottle]:
        return list(self.bottles.values())


def generate_vivino_url(name: str, year: int) -> str:
    """Return a Vivino search URL for the given wine."""
    query = urllib.parse.quote_plus(f"{name} {year}")
    return f"https://www.vivino.com/search/wines?q={query}"
