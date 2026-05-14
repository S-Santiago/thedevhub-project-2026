from typing import Optional      # permite indicar que un valor puede ser de un tipo o None
from logic.inventory import MACHINE_INVENTORY
from enums import Direction


def _direction_name(direction) -> str:
    if direction is None:
        return ""
    return getattr(direction, "name", str(direction)).upper()


def _opposite_direction(direction):
    if direction is None:
        return None

    opposite_map = {
        Direction.UP: Direction.DOWN,
        Direction.DOWN: Direction.UP,
        Direction.LEFT: Direction.RIGHT,
        Direction.RIGHT: Direction.LEFT,
    }
    return opposite_map.get(direction, None)


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
        if direction is None:
            direction = Direction.RIGHT
        self.direction                = direction  # direccion a la que apunta (enum Direction) -> salida
        # incoming_direction: si otra cinta apunta a esta celda, la guardamos para poder dibujar curvas
        self.incoming_direction       = incoming_direction
        self.in_direction             = incoming_direction  # alias mantenido por compatibilidad interna
        self.speed     : float        = speed      # velocidad de transporte (1.0 = 1 segundo por celda)
        self.item      : Optional[MaterialsMov] = None       # material que lleva ahora mismo, None si esta vacia
        self.is_empty  : bool         = True       # True si no lleva ningun material
        # Variant almacena una clave opcional para assets tipo "CONVEYOR_FROM-TO"
        # ejemplo: "CONVEYOR_RIGHT-DOWN". Si es None se usará el asset por dirección.
        self.variant: Optional[str] = None

    def set_incoming_direction(self, incoming_direction: Optional[Direction]) -> None:
        self.incoming_direction = incoming_direction
        self.in_direction = incoming_direction

    def entrance_direction(self):
        """Devuelve el lado visual de entrada de la cinta."""
        return _opposite_direction(self.incoming_direction)

    def is_corner(self) -> bool:
        entrance = self.entrance_direction()
        return entrance is not None and entrance != self.direction

    def is_straight(self) -> bool:
        entrance = self.entrance_direction()
        return entrance is None or entrance == self.direction

    def asset_key(self) -> str:
        """Devuelve la clave exacta del asset que representa esta cinta."""
        out_name = _direction_name(self.direction)
        if not out_name:
            return "CONVEYOR"

        if self.is_corner():
            entrance = self.entrance_direction()
            if entrance is not None:
                return f"CONVEYOR_{_direction_name(entrance)}-{out_name}"

        return f"CONVEYOR_{out_name}"

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
        if self.direction is None:
            self.direction = Direction.RIGHT
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

        if self.direction is None:
            self.direction = Direction.RIGHT

        dx, dy   = self.direction.value  # desplazamiento de la direccion
        progress = self.item.progress    # cuanto ha avanzado el material en esta celda (0.0 a 1.0)

        # interpola la posicion en pixeles entre la celda actual y la siguiente
        # esto produce el movimiento suave en pygame
        px = int((self.x + dx * progress) * tile_size)
        py = int((self.y + dy * progress) * tile_size)
        return (px, py)

    def __repr__(self) -> str:
        in_dir = getattr(self.incoming_direction, "name", None)
        dir_name = getattr(self.direction, "name", None)
        return (
            f"ConveyorBelt(pos=({self.x},{self.y}), "
            f"dir={dir_name}, in={in_dir}, "
            f"item={self.item})"
        )

    def asset_candidates(self):
        """Devuelve una lista ordenada de claves de asset a probar para dibujar esta cinta.

        Prioridad: asset exacto de curva -> asset recto -> fallback genérico.
        """
        candidates = [self.asset_key()]
        if self.is_corner():
            candidates.append(f"CONVEYOR_{_direction_name(self.direction)}")
        candidates.append("CONVEYOR")
        return candidates


class ConveyorCurve(ConveyorBelt):
    """Representa una cinta curva (cambio de sentido) desde `in_direction` hacia `direction`.

    Es una subclase ligera de `ConveyorBelt` que marca la cinta como curva
    y reutiliza `asset_key()` para preferir assets `CONVEYOR_<ENTRADA>-<SALIDA>`.
    """
    def __init__(self, x: int, y: int, out_direction, in_direction, speed: float = 1.0):
        super().__init__(x, y, out_direction, speed, incoming_direction=in_direction)
        self.is_curve = True

    def __repr__(self) -> str:
        in_dir = getattr(self.incoming_direction, "name", None)
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

    def update(self, delta_time: float, map_manager=None, inventory_system=None) -> None:
        """Actualizar sistema de cintas en dos fases:

        1) Calcular el progreso proyectado de cada material y registrar intenciones
           de transferencia cuando el progreso supera 1.0.
        2) Resolver conflictos de destino y aplicar las transferencias de forma
           atómica para evitar condiciones de carrera y pérdidas de ítems.
        """
        # Paso 1: calcular next_progress y determinar qué cintas intentan mover
        next_progress = {}
        will_move_out = set()
        for belt in list(self._grid.values()):
            if belt.item is None:
                continue
            projected = belt.item.progress + belt.speed * delta_time
            next_progress[(belt.x, belt.y)] = projected
            if projected >= 1.0:
                will_move_out.add((belt.x, belt.y))

        # Paso 2: construir intenciones (dst_pos -> (src_pos, item)) respetando
        # que el destino sea válido (exista) y vaya a quedar libre o ya esté libre.
        intents = {}
        # Para depósitos a máquinas (p.ej. cofres) que no son cintas
        deposit_intents = {}
        for belt in list(self._grid.values()):
            src = (belt.x, belt.y)
            if belt.item is None:
                # nada que hacer, pero actualizar progreso si no se mueve
                continue

            projected = next_progress.get(src, belt.item.progress + belt.speed * delta_time)
            if projected < 1.0:
                # avanzamos el progreso y no intentamos transferir
                belt.item.progress = projected
                continue

            dx, dy = belt.direction.value
            dst = (belt.x + dx, belt.y + dy)
            dest_belt = self.get_belt(dst[0], dst[1])

            # Si no hay una cinta destino, quizá hay una máquina (p.ej. un cofre)
            if dest_belt is None:
                machine_name = None
                try:
                    if map_manager is not None:
                        md = map_manager.get_machine_data(dst[0], dst[1])
                        if isinstance(md, dict):
                            machine_name = md.get("machine")
                        else:
                            machine_name = md
                except Exception:
                    machine_name = None

                # Soportar depósito en INVENTORY
                if machine_name == MACHINE_INVENTORY or machine_name == "INVENTORY":
                    # Conflicto de depósitos: si ya hay intención la cancelamos
                    if dst in deposit_intents:
                        prev_src, prev_item = deposit_intents.pop(dst)
                        s = self.get_belt(prev_src[0], prev_src[1])
                        if s and s.item:
                            s.item.progress = 1.0
                        belt.item.progress = 1.0
                        continue

                    deposit_intents[dst] = (src, belt.item)
                    continue

                # Destino inexistente y no es máquina receptora: queda en la frontera
                belt.item.progress = 1.0
                continue

            # Considerar destino libre si ahora está vacío o si va a moverse fuera
            dest_has_item = dest_belt.item is not None
            dest_will_move = dst in will_move_out

            # Evitar caso de swap directo: si el destino planea moverse a src, cancelar
            swap = False
            if dest_will_move:
                ddx, ddy = dest_belt.direction.value
                dest_target = (dest_belt.x + ddx, dest_belt.y + ddy)
                if dest_target == src:
                    swap = True

            if dest_has_item and not dest_will_move:
                # destino ocupado y no acaba de vaciarse: esperar
                belt.item.progress = 1.0
                continue

            if swap:
                # cancelar ambos: dejar en frontera
                belt.item.progress = 1.0
                dest_belt.item.progress = 1.0
                # no registrar intención
                continue

            # registrar intención si no hay conflicto previo
            if dst in intents:
                # conflicto: dos fuentes quieren el mismo destino -> cancelar
                prev_src, prev_item = intents.pop(dst)
                # dejar ambos en frontera
                s = self.get_belt(prev_src[0], prev_src[1])
                if s and s.item:
                    s.item.progress = 1.0
                belt.item.progress = 1.0
                continue

            # Si ya existe una intención de depósito hacia la misma posición, cancelar también
            if dst in deposit_intents:
                prev_src, prev_item = deposit_intents.pop(dst)
                s = self.get_belt(prev_src[0], prev_src[1])
                if s and s.item:
                    s.item.progress = 1.0
                belt.item.progress = 1.0
                continue

            intents[dst] = (src, belt.item)

        # Paso 3: aplicar transferencias válidas
        for dst_pos, (src_pos, item) in intents.items():
            src_belt = self.get_belt(src_pos[0], src_pos[1])
            dst_belt = self.get_belt(dst_pos[0], dst_pos[1])
            if src_belt is None or dst_belt is None:
                continue
            # mover item y actualizar banderas de ocupación
            src_belt.item = None
            src_belt.is_empty = True
            dst_belt.item = item
            dst_belt.is_empty = False
            dst_belt.item.progress = 0.0

        # Aplicar depósitos a máquinas (p.ej. cofres)
        for dst_pos, (src_pos, item) in deposit_intents.items():
            src_belt = self.get_belt(src_pos[0], src_pos[1])
            if src_belt is None or item is None:
                continue

            stored = False
            try:
                if inventory_system is not None:
                    stored = inventory_system.store_item_at(dst_pos[0], dst_pos[1], item.kind, 1)
            except Exception:
                stored = False

            if stored:
                # consumir el item de la cinta origen
                src_belt.item = None
                src_belt.is_empty = True
            else:
                # no se pudo almacenar: dejar en frontera
                src_belt.item.progress = 1.0

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
                belt.set_incoming_direction(self._compute_incoming(px, py))

    def iter_belts(self):
        """Iterador público sobre las cintas: devuelve ((x,y), belt)."""
        return iter(self._grid.items())

    def __len__(self):
        return len(self._grid)

    def __repr__(self) -> str:
        # lo que se muestra al hacer print(), ej: ConveyorSystem(12 cintas)
        return f"ConveyorSystem({len(self._grid)} cintas)"
