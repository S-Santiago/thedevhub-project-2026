from typing import Optional      # permite indicar que un valor puede ser de un tipo o None
from enums import Direction


# Material que viaja sobre la cinta
class MaterialsMov:
    def __init__(self, kind: str) -> None:
        self.kind     : str   = kind  # tipo de material, ej: "IRON"
        self.progress : float = 0.0   # avance en la celda actual (0.0 = recien llegó, 1.0 = listo para saltar)

    def __repr__(self) -> str:
        # lo que se muestra al hacer print(), ej: "Material: IRON, Progress: 0.75%"
        return f"Material: {self.kind}, Progress: {self.progress * 100:.2f}%"


# Una celda de cinta transportadora en el grid
class ConveyorBelt:
    def __init__(self, x: int, y: int, direction, speed: float = 1.0, incoming_direction: Optional[Direction] = None) -> None:
        self.x         : int          = x          # columna en el grid
        self.y         : int          = y          # fila en el grid
        self.direction                = direction  # direccion a la que apunta (enum Direction) -> salida
        # incoming_direction: si otra cinta apunta a esta celda, la guardamos para poder dibujar curvas
        self.in_direction             = incoming_direction
        self.speed     : float        = speed      # velocidad de transporte (1.0 = 1 segundo por celda)
        self.item      : Optional[MaterialsMov] = None       # material que lleva ahora mismo, None si esta vacia
        self.is_empty  : bool         = True       # True si no lleva ningun material
        # Variant almacena una clave opcional para assets tipo "CONVEYOR_FROM-TO"
        # ejemplo: "CONVEYOR_RIGHT-DOWN". Si es None se usará el asset por dirección.
        self.variant: Optional[str] = None

    def update(self, delta_time: float, system) -> None:
        # si no hay material en esta celda no hay nada que actualizar
        if self.item is None:
            return

        # avanza el progreso del material segun la velocidad y el tiempo transcurrido desde el ultimo frame
        self.item.progress += self.speed * delta_time

        # si el material ha cruzado la celda entera, intenta moverlo a la siguiente
        if self.item.progress >= 1.0:
            self._try_transfer(system)

    def _try_transfer(self, system) -> None:
        # obtiene el desplazamiento de la direccion, ej: RIGHT dx=1 dy=0
        dx, dy = self.direction.value

        # busca la celda que hay en la direccion a la que apunta esta cinta
        dest = system.get_belt(self.x + dx, self.y + dy)

        if dest is not None and dest.is_empty:  # si la celda destino existe y esta libre
            self.item.progress = 0.0            # resetea el progreso para que empiece desde 0 en la nueva celda
            dest.item          = self.item      # mueve el material a la celda destino
            dest.is_empty      = False          # marca la celda destino como ocupada
            self.item          = None           # vacia la celda actual
            self.is_empty      = True           # marca la celda actual como libre
        else:
            # la celda destino no existe o esta ocupada, el material espera en el borde
            self.item.progress = 1.0

    def pixel_position(self, tile_size: int):
        # si no hay material no hay posicion que devolver
        if self.item is None:
            return None

        dx, dy   = self.direction.value  # desplazamiento de la direccion
        progress = self.item.progress    # cuanto ha avanzado el material en esta celda (0.0 a 1.0)

        # interpola la posicion en pixeles entre la celda actual y la siguiente
        # esto produce el movimiento suave en pygame
        px = int((self.x + dx * progress) * tile_size)
        py = int((self.y + dy * progress) * tile_size)
        return (px, py)

    def __repr__(self) -> str:
        in_dir = getattr(self.in_direction, "name", None)
        return (
            f"ConveyorBelt(pos=({self.x},{self.y}), "
            f"dir={self.direction.name}, in={in_dir}, "
            f"item={self.item})"
        )

    def asset_candidates(self):
        """Devuelve una lista ordenada de claves de asset a probar para dibujar esta cinta.

        Prioridad: CONVEYOR_{IN}_{OUT} -> CONVEYOR_{OUT} -> CONVEYOR
        """
        out_name = getattr(self.direction, "name", str(self.direction))
        candidates = []
        if self.in_direction is not None:
            in_name = getattr(self.in_direction, "name", str(self.in_direction))
            candidates.append(f"CONVEYOR_{in_name}_{out_name}")
            candidates.append(f"CONVEYOR_{out_name}_{in_name}")
        candidates.append(f"CONVEYOR_{out_name}")
        candidates.append("CONVEYOR")
        return candidates


class ConveyorCurve(ConveyorBelt):
    """Representa una cinta curva (cambio de sentido) desde `in_direction` hacia `direction`.

    Es una subclase ligera de `ConveyorBelt` que marca la cinta como curva
    y reutiliza `asset_candidates()` para preferir assets `CONVEYOR_<IN>_<OUT>`.
    """
    def __init__(self, x: int, y: int, out_direction, in_direction, speed: float = 1.0):
        super().__init__(x, y, out_direction, speed, incoming_direction=in_direction)
        self.is_curve = True

    def __repr__(self) -> str:
        in_dir = getattr(self.in_direction, "name", None)
        return (
            f"ConveyorCurve(pos=({self.x},{self.y}), out={self.direction.name}, in={in_dir}, item={self.item})"
        )


# Gestor de todas las cintas del mapa
class ConveyorSystem:
    def __init__(self) -> None:
        # diccionario que guarda todas las cintas, la clave es la posicion (x, y)
        self._grid = {}

    def add_belt(self, belt) -> None:
        # añade una cinta al grid usando su posicion como clave
        self._grid[(belt.x, belt.y)] = belt
        # actualizar conexiones entrantes/salientes alrededor de la celda añadida
        self._refresh_connections(belt.x, belt.y)

    def remove_belt(self, x: int, y: int) -> None:
        # elimina la cinta de esa posicion, si no existe no hace nada
        self._grid.pop((x, y), None)
        # actualizar vecinos ya que pueden perder su entrada
        self._refresh_connections(x, y)

    def get_belt(self, x: int, y: int):
        # devuelve la cinta de esa posicion, o None si no hay ninguna
        return self._grid.get((x, y))

    def rotate_belt(self, x: int, y: int, direction) -> None:
        belt = self.get_belt(x, y)     # busca la cinta en esa posicion
        if belt:                        # si existe
            belt.direction = direction  # cambia su direccion
            # refrescar conexiones locales
            self._refresh_connections(x, y)

    def place_material(self, x: int, y: int, kind: str) -> bool:
        belt = self.get_belt(x, y)          # busca la cinta en esa posicion
        if belt and belt.is_empty:          # si existe y esta vacia
            belt.item     = MaterialsMov(kind)  # crea el material y lo coloca en la cinta
            belt.is_empty = False               # marca la cinta como ocupada
            return True                         # exito
        return False  # la celda no existe o ya tiene un material

    def update(self, delta_time: float) -> None:
        # list() hace una copia del grid para evitar problemas si se modifica durante el bucle
        for belt in list(self._grid.values()):
            belt.update(delta_time, self)  # actualiza cada cinta

    def _compute_incoming(self, x: int, y: int):
        """Busca una cinta adyacente que apunte a (x,y) y devuelve su Direction si existe."""
        for d in Direction:
            dx, dy = d.value
            nb = self.get_belt(x - dx, y - dy)
            if nb is not None and getattr(nb, "direction", None) == d:
                return d
        return None

    def _refresh_connections(self, x: int, y: int):
        """Refresca el campo `in_direction` para la celda (x,y) y sus vecinos inmediatos."""
        positions = [(x, y), (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        for px, py in positions:
            belt = self.get_belt(px, py)
            if belt is not None:
                belt.in_direction = self._compute_incoming(px, py)

    def __repr__(self) -> str:
        # lo que se muestra al hacer print(), ej: ConveyorSystem(12 cintas)
        return f"ConveyorSystem({len(self._grid)} cintas)"
