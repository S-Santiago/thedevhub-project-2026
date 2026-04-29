# The Dev Hub — Tycoon

Requisitos
- Python 3.8+
- pip

Instalación
```bash
python -m pip install -r requirements.txt
```

Ejecución
```bash
python app.pyw
```

Controles de construccion (actual)
- `W/A/S/D`: mover camara
- `1`: seleccionar `CONVEYOR`
- `2`: seleccionar `DRILL`
- `0`: deseleccionar maquina
- `R`: rotar direccion de colocacion
- Clic izquierdo: colocar maquina seleccionada en el tile bajo el cursor

Gameplay actual
- `DRILL` solo se puede colocar sobre tiles con mineral.
- El `DRILL` extrae automaticamente y expulsa el recurso hacia la casilla frontal (segun direccion).
- Si hay una `CONVEYOR` libre delante, el item se inserta y se mueve por la cinta.
