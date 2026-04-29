from typing import Optional      # permite indicar que un valor puede ser de un tipo o None


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
    def __init__(self, x: int, y: int, direction, speed: float = 1.0) -> None:
        self.x         : int          = x          # columna en el grid
        self.y         : int          = y          # fila en el grid
        self.direction                = direction  # direccion a la que apunta (enum Direction)
        self.speed     : float        = speed      # velocidad de transporte (1.0 = 1 segundo por celda)
        self.item      : Optional[MaterialsMov] = None       # material que lleva ahora mismo, None si esta vacia
        self.is_empty  : bool         = True       # True si no lleva ningun material

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
        return (
            f"ConveyorBelt(pos=({self.x},{self.y}), "
            f"dir={self.direction.name}, "
            f"item={self.item})"
        )


# Gestor de todas las cintas del mapa
class ConveyorSystem:
    def __init__(self) -> None:
        # diccionario que guarda todas las cintas, la clave es la posicion (x, y)
        self._grid = {}

    def add_belt(self, belt) -> None:
        # añade una cinta al grid usando su posicion como clave
        self._grid[(belt.x, belt.y)] = belt

    def remove_belt(self, x: int, y: int) -> None:
        # elimina la cinta de esa posicion, si no existe no hace nada
        self._grid.pop((x, y), None)

    def get_belt(self, x: int, y: int):
        # devuelve la cinta de esa posicion, o None si no hay ninguna
        return self._grid.get((x, y))

    def rotate_belt(self, x: int, y: int, direction) -> None:
        belt = self.get_belt(x, y)     # busca la cinta en esa posicion
        if belt:                        # si existe
            belt.direction = direction  # cambia su direccion

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

    def __repr__(self) -> str:
        # lo que se muestra al hacer print(), ej: ConveyorSystem(12 cintas)
        return f"ConveyorSystem({len(self._grid)} cintas)"
