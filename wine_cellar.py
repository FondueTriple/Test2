from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
import json
import urllib.parse


@dataclass
class Bottle:
    id: int
    name: str
    year: int
    comments: List[str] = field(default_factory=list)
    vivino_url: str = ""
    vivino_rating: float = 0.0
    pos_row: Optional[int] = None  # 1..6
    pos_col: Optional[int] = None  # 1..4


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

    def edit_bottle(
        self,
        bottle_id: int,
        name: Optional[str] = None,
        year: Optional[int] = None,
        vivino_rating: Optional[float] = None,
        pos_row: Optional[int] = None,
        pos_col: Optional[int] = None,
    ) -> bool:
        """Edit the name and/or year of an existing bottle.

        Returns True if the bottle was found and updated, False otherwise.
        """
        bottle = self.bottles.get(bottle_id)
        if bottle is None:
            return False
        if name is not None:
            bottle.name = name
        if year is not None:
            bottle.year = year
        changed = False
        if vivino_rating is not None:
            # Clamp rating between 0 and 5
            bottle.vivino_rating = max(0.0, min(5.0, float(vivino_rating)))
            changed = True
        # Handle position updates: if both provided, set; if one is None -> clear both
        if pos_row is not None or pos_col is not None:
            if pos_row is None or pos_col is None:
                # Clear position
                if bottle.pos_row is not None or bottle.pos_col is not None:
                    bottle.pos_row = None
                    bottle.pos_col = None
                    changed = True
            else:
                # Validate ranges (1..6 rows, 1..4 cols)
                if not (1 <= int(pos_row) <= 6 and 1 <= int(pos_col) <= 4):
                    # Ignore invalid position silently
                    pass
                else:
                    r = int(pos_row)
                    c = int(pos_col)
                    # Ensure uniqueness: clear any other bottle occupying (r,c)
                    for other in self.bottles.values():
                        if other.id != bottle.id and other.pos_row == r and other.pos_col == c:
                            other.pos_row = None
                            other.pos_col = None
                            changed = True
                    bottle.pos_row = r
                    bottle.pos_col = c
                    changed = True
        if name is not None:
            bottle.vivino_url = generate_vivino_url(bottle.name, bottle.year)
            changed = True
        if year is not None:
            changed = True
        if name is not None or year is not None:
            bottle.vivino_url = generate_vivino_url(bottle.name, bottle.year)
        if changed:
            self.save()
        return True

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
