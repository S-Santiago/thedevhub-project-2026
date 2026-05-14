# Guía para generar el `.exe` de The Dev Hub (Windows)
Este documento explica cómo crear el ejecutable de Windows (`.exe`) para este proyecto hecho con Pygame.

## 1) Requisitos
- Windows 10/11
- Python 3.8 o superior
- `pip` disponible en terminal

## 2) Preparar el proyecto
Abre PowerShell o CMD dentro de la carpeta del proyecto y ejecuta:

```bash
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

## 3) Crear el `.exe` (recomendado: carpeta distribuible)
Ejecuta este comando:

```bash
py -m PyInstaller --noconfirm --clean --windowed --name "TheDevHub" --workpath "%LOCALAPPDATA%\TheDevHub\pyinstaller-build" --add-data "assets;assets" app.pyw
```

## 4) Dónde queda el ejecutable
Al terminar, encontrarás:

- Ejecutable: `dist/TheDevHub/TheDevHub.exe`
- Carpeta completa para compartir: `dist/TheDevHub/`

Para que el juego funcione correctamente, comparte **toda** la carpeta `TheDevHub`, no solo el `.exe`.

## 5) Opción alternativa: un único archivo `.exe`
Si prefieres un solo archivo:

```bash
py -m PyInstaller --noconfirm --clean --onefile --windowed --name "TheDevHub" --workpath "%LOCALAPPDATA%\TheDevHub\pyinstaller-build" --icon="assets/icon.ico" --add-data "assets;assets" --collect-binaries numpy --hidden-import numpy --hidden-import numpy._core._multiarray_umath app.pyw
```

Resultado esperado:
- `dist/TheDevHub.exe`

Nota: en modo `--onefile` el inicio puede tardar un poco más.

Nota: para que el icono de Windows del ejecutable se incruste correctamente, usa un archivo `.ico` (por ejemplo `assets/icon.ico`).

## 6) Errores comunes
### No encuentra `pygame`
Reinstala dependencias:

```bash
py -m pip install -r requirements.txt
```

### Error con rutas o assets que faltan
Verifica que existe la carpeta `assets` en la raíz del proyecto y que usas exactamente:

```bash
--add-data "assets;assets"
```

### PermissionError en `build\TheDevHub\localpycs`
Esto suele pasar si el proyecto está dentro de OneDrive, el EXE está abierto, o Windows Defender/antivirus bloquea la carpeta de trabajo. Usa un `--workpath` fuera del proyecto, como en los comandos anteriores, y vuelve a compilar tras cerrar cualquier `TheDevHub.exe` abierto.

### El ejecutable se abre y se cierra
Prueba quitando `--windowed` temporalmente para ver errores en consola:

```bash
py -m PyInstaller --noconfirm --clean --name "TheDevHub" --workpath "%LOCALAPPDATA%\TheDevHub\pyinstaller-build" --add-data "assets;assets" app.pyw
```
