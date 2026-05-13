# The Dev Hub — Tycoon

Juego de automatizacion y gestion de recursos inspirado en titulos industriales, desarrollado como proyecto educativo para la comunidad tecnologica de la Universidad Europea de Andalucia.

---

## ✨ Caracteristicas Principales

### 🎮 Gameplay
- Taladros (`DRILL`) que extraen recursos desde tiles minerales.
- Cintas transportadoras deterministas (`CONVEYOR`) para mover items con flujo predecible.
- Gestion de recursos orientada a planificacion, eficiencia y expansion del sistema.

### 🧠 Excelencia Tecnica
- Sistema de actualizacion en dos fases para evitar race conditions y estados inconsistentes.
- Renderizado con culling espacial para mejorar rendimiento en escenas grandes.
- Cache de assets escalados para reducir operaciones de transformacion en tiempo real.
- Arquitectura desacoplada para facilitar mantenimiento, pruebas y evolucion del proyecto.

---

## 🚀 Instalacion y Uso

### Requisitos
- Python 3.8 o superior
- pip

### Instalacion
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Ejecucion
```bash
python app.pyw
```

> [!IMPORTANT]
> El archivo principal del juego es **app.pyw**. En Windows, esta extension evita abrir una consola adicional y ofrece una experiencia de ejecucion mas limpia para aplicaciones graficas.

---

## 🎮 Controles y Mecanicas

| Control | Accion |
| --- | --- |
| `W` / `A` / `S` / `D` | Mover la camara por el mapa |
| `1` | Seleccionar `CONVEYOR` |
| `2` | Seleccionar `DRILL` |
| `0` | Deseleccionar maquina actual |
| `R` | Rotar la direccion de colocacion |
| Clic izquierdo | Colocar la maquina seleccionada en el tile bajo el cursor |

> [!TIP]
> Las cintas se conectan automaticamente detectando la direccion de entrada, lo que permite formar curvas y redes de transporte de forma fluida.

---

## 🛠️ Arquitectura del Proyecto

Estructura principal:
- `logic/`: logica de simulacion, sistemas de produccion y comportamiento de maquinaria.
- `assets/`: sprites, materiales visuales y recursos graficos del juego.
- `tests/`: pruebas unitarias para validar mecanicas clave y estabilidad del sistema.

> [!NOTE]
> El proyecto sigue principios de Clean Code y DRY, por lo que es una base ideal para aprender buenas practicas de desarrollo de videojuegos en Python.

---

## 🤝 Contribucion (The Dev Hub)

Este es un proyecto abierto a los miembros de The Dev Hub. Si formas parte del club, puedes proponer mejoras de gameplay, optimizaciones tecnicas y nuevas mecanicas para enriquecer la experiencia.

> [!WARNING]
> Antes de subir cambios, ejecuta siempre los tests unitarios:
> ```bash
> pytest
> ```

---

## 📜 Licencia y Creditos

Proyecto impulsado por **The Dev Hub** en colaboracion con la **Universidad Europea de Andalucia**.

Gracias a la comunidad estudiantil por construir, iterar y compartir conocimiento a traves del desarrollo de videojuegos con enfoque profesional.
