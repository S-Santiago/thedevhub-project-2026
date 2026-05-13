"""Sistema de Inventarios: máquinas que almacenan materiales recibidos desde cintas.

Define `InventoryMachine` (contenedor por posición) y `InventorySystem` (registro).
"""
from typing import Dict, Tuple, Iterator, Optional


MACHINE_INVENTORY = "INVENTORY"


class InventoryMachine:
    def __init__(self, x: int, y: int, capacity: Optional[int] = None):
        self.x = x
        self.y = y
        # capacity=None = sin límite
        self.capacity = capacity
        # contents: mapping kind -> count
        self.contents: Dict[str, int] = {}

    def store(self, kind: str, amount: int = 1) -> bool:
        """Almacena `amount` unidades de `kind` en el inventario.

        Devuelve True si se almacenó, False si no hay espacio.
        """
        if amount <= 0:
            return False

        if self.capacity is not None:
            current_total = sum(self.contents.values())
            if current_total + amount > self.capacity:
                return False

        self.contents[kind] = self.contents.get(kind, 0) + amount
        return True

    def __repr__(self) -> str:
        return f"InventoryMachine(pos=({self.x},{self.y}), contents={self.contents})"


class InventorySystem:
    def __init__(self) -> None:
        # mapping (x,y) -> InventoryMachine
        self._grid: Dict[Tuple[int, int], InventoryMachine] = {}

    def create_inventory(self, x: int, y: int, capacity: Optional[int] = None) -> InventoryMachine:
        inv = InventoryMachine(x, y, capacity=capacity)
        self._grid[(x, y)] = inv
        return inv

    def add_inventory(self, inv: InventoryMachine) -> None:
        self._grid[(inv.x, inv.y)] = inv

    def get_inventory(self, x: int, y: int) -> Optional[InventoryMachine]:
        return self._grid.get((x, y))

    def remove_inventory(self, x: int, y: int) -> None:
        self._grid.pop((x, y), None)

    def store_item_at(self, x: int, y: int, kind: str, amount: int = 1) -> bool:
        inv = self.get_inventory(x, y)
        if inv is None:
            return False
        return inv.store(kind, amount)

    def iter_inventories(self) -> Iterator[Tuple[Tuple[int, int], InventoryMachine]]:
        return iter(self._grid.items())

    def __len__(self):
        return len(self._grid)

    def __repr__(self) -> str:
        return f"InventorySystem({len(self._grid)} inventories)"
