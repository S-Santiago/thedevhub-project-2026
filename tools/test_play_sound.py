import time
import sys
from pathlib import Path
import pygame

# Añadir la raíz del repo al path para permitir imports desde `tools/`
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sound_manager import SoundManager

print("Iniciando prueba de audio...")
try:
    # Inicializar sólo el mixer para no abrir ventana
    pygame.mixer.init()
    print("mixer init OK", pygame.mixer.get_init())
except Exception as e:
    print("Error inicializando mixer:", e)

sm = SoundManager(assets_dir="assets")
print("Sonidos disponibles:", sm.get_available_sounds())
res = sm.play_place_sound("CONVEYOR")
print("play_place_sound ->", res)
res2 = sm.play_place_sound("INVENTORY")
print("play_place_sound(INVENTORY) ->", res2)
# Esperar para permitir reproducción breve
time.sleep(0.6)
try:
    pygame.mixer.quit()
except Exception:
    pass
print("Prueba finalizada.")
