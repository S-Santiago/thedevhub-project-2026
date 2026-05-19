"""
Sistema de Audio Culling para máquinas basado en frustum de cámara.

Previene que cientos de máquinas produzcan sonidos simultáneamente
al fuera del viewport de la cámara, mejorando rendimiento y game feel.
"""

from typing import Dict, Tuple, Set


class AudioCullingManager:
    """
    Gestiona qué máquinas deben reproducir audio basándose en su posición
    relativa al viewport actual de la cámara.
    
    El frustum se calcula una sola vez por frame para máxima eficiencia.
    """
    
    def __init__(self, margin: int = 1):
        """
        Inicializa el manager de audio culling.
        
        Args:
            margin: Número de tiles extra alrededor del viewport para pre-cargar audio.
                    Evita clicks/pops cuando el usuario hace pan rápidamente.
        """
        self.margin = margin
        self._frustum_left = 0
        self._frustum_right = 0
        self._frustum_top = 0
        self._frustum_bottom = 0
        self._last_audible: Set[Tuple[int, int]] = set()
        self._currently_audible: Set[Tuple[int, int]] = set()
    
    def update_frustum(self, offset_x: float, offset_y: float, tile_size: int,
                       window_width: int, window_height: int) -> None:
        """
        Actualiza el frustum de la cámara (viewport) una sola vez por frame.
        
        Args:
            offset_x: Desplazamiento X de la cámara en píxeles
            offset_y: Desplazamiento Y de la cámara en píxeles
            tile_size: Tamaño de cada tile en píxeles
            window_width: Ancho de la ventana en píxeles
            window_height: Alto de la ventana en píxeles
        """
        # Convertir pixels a tiles
        left = -offset_x / tile_size - self.margin
        top = -offset_y / tile_size - self.margin
        right = left + (window_width / tile_size) + self.margin
        bottom = top + (window_height / tile_size) + self.margin
        
        self._frustum_left = int(left)
        self._frustum_right = int(right) + 1
        self._frustum_top = int(top)
        self._frustum_bottom = int(bottom) + 1
    
    def is_audible(self, tile_x: int, tile_y: int) -> bool:
        """
        Comprueba si una máquina en la posición dada debe reproducir audio.
        
        Args:
            tile_x: Coordenada X en tiles
            tile_y: Coordenada Y en tiles
            
        Returns:
            True si la máquina está dentro del viewport (+ margin), False si está fuera.
        """
        return (self._frustum_left <= tile_x <= self._frustum_right and
                self._frustum_top <= tile_y <= self._frustum_bottom)
    
    def get_audible_positions(self, positions: list) -> Set[Tuple[int, int]]:
        """
        Filtra una lista de posiciones para retornar solo las audibles.
        
        Útil para búsquedas en batch (ej: todos los drills).
        
        Args:
            positions: Lista de tuplas (x, y) a filtrar
            
        Returns:
            Set de posiciones audibles
        """
        return {(x, y) for x, y in positions if self.is_audible(x, y)}
    
    def get_changed_audibility(self, current_positions: Set[Tuple[int, int]]) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
        """
        Detecta qué máquinas entraron y salieron del viewport desde la última actualización.
        
        Útil para eventos o callbacks.
        
        Args:
            current_positions: Set de posiciones actualmente audibles
            
        Returns:
            Tupla (entered, exited) con posiciones que entraron/salieron de audibilidad
        """
        entered = current_positions - self._last_audible
        exited = self._last_audible - current_positions
        self._last_audible = current_positions.copy()
        return entered, exited


# Instancia global para facilitar uso
_audio_culling = None


def get_audio_culling_manager(margin: int = 1) -> AudioCullingManager:
    """
    Obtiene la instancia global del Audio Culling Manager.
    
    Args:
        margin: Margen de tiles alrededor del viewport
        
    Returns:
        Instancia del AudioCullingManager
    """
    global _audio_culling
    if _audio_culling is None:
        _audio_culling = AudioCullingManager(margin=margin)
    return _audio_culling
