"""
Gestor centralizado de efectos de sonido para máquinas.
"""

import os
from pathlib import Path
import pygame

from asset_manager import resource_path

# Tipos de eventos de sonido
EVENT_MACHINE_PLACED = "machine_placed"
EVENT_MACHINE_DELETED = "machine_deleted"

# Máquinas
MACHINE_CONVEYOR = "CONVEYOR"
MACHINE_DRILL = "DRILL"
MACHINE_CHEST = "CHEST"


class SoundManager:
    """Gestiona la reproducción de efectos de sonido para máquinas."""
    
    def __init__(self, assets_dir="assets"):
        """
        Inicializa el gestor de sonidos.
        
        Args:
            assets_dir: Directorio base de assets (por defecto "assets")
        """
        assets_path = Path(assets_dir)
        if not assets_path.is_absolute():
            assets_path = Path(resource_path(str(assets_path)))

        self.sounds_dir = assets_path / "SOUNDS"
        self.sounds = {}
        self.enabled = True
        self.master_volume = 1.0
        
        # Crear directorio de sonidos si no existe
        self.sounds_dir.mkdir(parents=True, exist_ok=True)
        
        # Cargar sonidos disponibles
        self._load_sounds()
    
    def _load_sounds(self):
        """Carga todos los archivos de sonido del directorio SOUNDS."""
        if not self.sounds_dir.exists():
            print(f"⚠️ Directorio de sonidos no encontrado: {self.sounds_dir}")
            return
        
        # Buscar archivos de sonido
        for file in self.sounds_dir.glob("*.wav"):
            try:
                sound = pygame.mixer.Sound(str(file))
                sound_name = file.stem
                self.sounds[sound_name] = sound
                print(f"✓ Sonido cargado: {sound_name}")
            except pygame.error as e:
                print(f"✗ Error al cargar {file.name}: {e}")
        
        for file in self.sounds_dir.glob("*.ogg"):
            try:
                sound = pygame.mixer.Sound(str(file))
                sound_name = file.stem
                self.sounds[sound_name] = sound
                print(f"✓ Sonido cargado: {sound_name}")
            except pygame.error as e:
                print(f"✗ Error al cargar {file.name}: {e}")
    
    def play_machine_sound(self, machine_type, event_type, pitch=1.0):
        """
        Reproduce el sonido de una máquina.
        
        Args:
            machine_type: Tipo de máquina ("CONVEYOR", "DRILL", "CHEST", etc.)
            event_type: Tipo de evento ("machine_placed", "machine_deleted")
            pitch: Factor de pitch (1.0 = pitch normal, 0.5-2.0 rango típico)
        """
        if not self.enabled or not self.sounds:
            return False
        
        # Construir nombre del sonido
        sound_name = f"{machine_type.lower()}_{event_type}"
        
        # Si el sonido específico no existe, intentar fallback genérico
        if sound_name not in self.sounds:
            # Fallback: sonido genérico del evento
            generic_name = event_type
            if generic_name not in self.sounds:
                return False
            sound_name = generic_name
        
        sound = self.sounds[sound_name]
        
        # Aplicar volumen maestro
        sound.set_volume(self.master_volume)
        
        # Aplicar pitch si pygame lo soporta (versiones recientes)
        # Para versiones más viejas, usar playback speed con pygame-mixer
        try:
            # pygame 2.1+ soporta pitch, pero es complicado
            # Por ahora, reproducir el sonido normalmente
            # El pitch se puede controlar alterando la frecuencia del mixer
            sound.play()
            return True
        except Exception as e:
            print(f"Error al reproducir {sound_name}: {e}")
            return False
    
    def play_place_sound(self, machine_type):
        """Reproduce el sonido de colocación de máquina."""
        return self.play_machine_sound(machine_type, "place")
    
    def play_delete_sound(self, machine_type, pitch=0.7):
        """Reproduce el sonido de eliminación de máquina."""
        # El pitch bajo (0.7) da efecto de desinstalación
        return self.play_machine_sound(machine_type, "delete", pitch=pitch)
    
    def set_master_volume(self, volume):
        """Establece el volumen maestro (0.0-1.0)."""
        self.master_volume = max(0.0, min(1.0, volume))
    
    def toggle_sound(self, enabled=None):
        """Activa/desactiva los sonidos."""
        if enabled is None:
            self.enabled = not self.enabled
        else:
            self.enabled = enabled
        return self.enabled
    
    def get_available_sounds(self):
        """Devuelve una lista de sonidos disponibles."""
        return list(self.sounds.keys())
    
    def preload_sound(self, sound_name):
        """Precarga un sonido específico para reproducción más rápida."""
        if sound_name not in self.sounds:
            sound_file = self.sounds_dir / f"{sound_name}.wav"
            if not sound_file.exists():
                sound_file = self.sounds_dir / f"{sound_name}.ogg"
            
            if sound_file.exists():
                try:
                    sound = pygame.mixer.Sound(str(sound_file))
                    self.sounds[sound_name] = sound
                    return True
                except pygame.error as e:
                    print(f"Error al precarga {sound_name}: {e}")
        return sound_name in self.sounds


# Instancia global del gestor de sonidos
_sound_manager = None


def get_sound_manager(assets_dir="assets"):
    """Obtiene la instancia global del gestor de sonidos."""
    global _sound_manager
    if _sound_manager is None:
        _sound_manager = SoundManager(assets_dir)
    return _sound_manager


def play_place_sound(machine_type):
    """Conveniencia: reproduce sonido de colocación."""
    sm = get_sound_manager()
    return sm.play_place_sound(machine_type)


def play_delete_sound(machine_type):
    """Conveniencia: reproduce sonido de eliminación."""
    sm = get_sound_manager()
    return sm.play_delete_sound(machine_type)
