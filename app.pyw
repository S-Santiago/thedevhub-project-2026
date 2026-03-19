# main.py
import pygame
from settings import MAP_SIZE, MIN_TILE_SIZE, USER_OPTIONS
from map_generator import generate_map
from asset_manager import load_images

def main():            
    pygame.init()
    pygame.display.set_caption("The Dev Hub")
    
    # 1. Configuración de pantalla
    screens = pygame.display.get_desktop_sizes()
    selected_screen = USER_OPTIONS["screen"]
    
    # Prevención de errores si solo hay un monitor
    display_idx = 0
    if selected_screen <= len(screens):
        display_idx = selected_screen - 1

    window_width, window_height = screens[display_idx]
    
    # Calculamos el tamaño del tile para que el mapa ocupe todo el ALTO de la ventana
    tile_size = window_height // MAP_SIZE
    map_pixel_size = tile_size * MAP_SIZE
    
    # Calculamos el centro de la pantalla
    offset_x = (window_width - map_pixel_size) // 2
    offset_y = (window_height - map_pixel_size) // 2
          
    screen = pygame.display.set_mode(
        (window_width, window_height), 
        pygame.NOFRAME,
        display=display_idx
    )
    
    clock = pygame.time.Clock()
    
    # Carga de datos
    tiles = generate_map()
    imagenes = load_images(tile_size)
    
    # Bucle Principal
    running = True
    while running:
        # Gestión de Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Salir rápido con ESC
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
                
        # Lógica
                
        # Dibujado
        screen.fill((0, 0, 0))
        
        for (x, y), data in tiles.items():
            # Aplicamos el offset para que todo se dibuje centrado
            pos_x = offset_x + (x * tile_size)
            pos_y = offset_y + (y * tile_size)
            
            # Dibujar terreno
            terrain = data["terrain"]
            if terrain in imagenes:
                screen.blit(imagenes[terrain], (pos_x, pos_y))
            
            # Dibujar mineral
            mineral = data["mineral"]
            if mineral and mineral in imagenes:
                screen.blit(imagenes[mineral], (pos_x, pos_y))

        pygame.display.flip()
        clock.tick(USER_OPTIONS["fps"])

    pygame.quit()
        
if __name__ == "__main__":
    main()