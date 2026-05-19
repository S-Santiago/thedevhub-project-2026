"""
Script para generar sonidos de "Game Feel" (satisfactorios) para máquinas.
Ejecutar una vez para crear los archivos de audio.
"""

import numpy as np
import wave
from pathlib import Path


def add_fast_envelope(wave_data, sample_rate):
    """Añade un ataque ultrarrápido (2ms) para evitar chasquidos, manteniendo el 'golpe'."""
    attack_len = int(sample_rate * 0.002) 
    fade_len = int(sample_rate * 0.01)  
    
    if len(wave_data) > attack_len + fade_len:
        fade_in = np.linspace(0, 1, attack_len)
        fade_out = np.linspace(1, 0, fade_len)
        wave_data[:attack_len] = (wave_data[:attack_len] * fade_in).astype(np.int16)
        wave_data[-fade_len:] = (wave_data[-fade_len:] * fade_out).astype(np.int16)
        
    silence_padding = np.zeros(int(sample_rate * 0.15), dtype=np.int16)
    return np.concatenate((wave_data, silence_padding))


def generate_pop(start_freq, end_freq, duration=0.08, sample_rate=44100, amplitude=12000):
    """Genera un sonido de 'Burbuja' o 'Pop' muy juguetón."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Barrido de frecuencia
    frequency = start_freq * (end_freq / start_freq) ** (t / duration)
    wave_data = np.sin(2 * np.pi * frequency * t)
    
    # Envolvente percusiva (cae rápido hacia el final)
    envelope = np.exp(-12 * t / duration) 
    wave_data = (amplitude * wave_data * envelope).astype(np.int16)
    return add_fast_envelope(wave_data, sample_rate)


def generate_thump(frequency, duration=0.1, sample_rate=44100, amplitude=16000):
    """Genera un golpe seco y grave, como un bloque de madera (Woodblock)."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave_data = np.sin(2 * np.pi * frequency * t)
    
    # Envolvente percusiva más agresiva para que suene a "golpe" físico
    envelope = np.exp(-20 * t / duration)
    wave_data = (amplitude * wave_data * envelope).astype(np.int16)
    return add_fast_envelope(wave_data, sample_rate)


def generate_bell(freq1, freq2, duration=0.15, sample_rate=44100, amplitude=10000):
    """Genera un 'Ding' musical y alegre combinando dos notas (acorde)."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Mezclamos dos ondas senoidales para crear armonía
    wave_data1 = np.sin(2 * np.pi * freq1 * t)
    wave_data2 = np.sin(2 * np.pi * freq2 * t)
    wave_data = (wave_data1 + wave_data2) / 2.0
    
    # Caída suave tipo campanilla
    envelope = np.exp(-8 * t / duration)
    wave_data = (amplitude * wave_data * envelope).astype(np.int16)
    return add_fast_envelope(wave_data, sample_rate)

def generate_tick(frequency=1000, duration=0.035, sample_rate=44100, amplitude=3500):
    """
    Genera un 'tic' o 'clink' muy corto y sutil.
    Diseñado específicamente para acciones de alta repetición (como extraer minerales).
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Onda senoidal simple para un tono limpio
    wave_data = np.sin(2 * np.pi * frequency * t)
    
    # Envolvente extremadamente rápida (-40) para que sea un toque percusivo muy breve, 
    # sin "cola" que se acumule en el cerebro del jugador.
    envelope = np.exp(-40 * t / duration) 
    
    wave_data = (amplitude * wave_data * envelope).astype(np.int16)
    return add_fast_envelope(wave_data, sample_rate)

def save_wav(filename, wave_data, sample_rate=44100):
    """Guarda un array de datos de onda como archivo WAV."""
    with wave.open(str(filename), 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave_data.tobytes())
    print(f"✓ Guardado: {filename.name}")

def generate_error_buzzer(frequency=120, duration=0.15, sample_rate=44100, amplitude=8000):
    """
    Genera un zumbido de error clásico y áspero usando una onda cuadrada.
    Ideal para 'No puedes construir aquí' por colisión.
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # El truco np.sign convierte la curva suave del seno en saltos bruscos de -1 a 1 (onda cuadrada)
    wave_data = np.sign(np.sin(2 * np.pi * frequency * t))
    
    # Envolvente plana que cae rápido al final, para que suene como un timbre seco
    envelope = np.ones_like(t)
    decay_len = int(len(t) * 0.3) # El último 30% del sonido es para apagarse
    envelope[-decay_len:] = np.linspace(1, 0, decay_len)
    
    wave_data = (amplitude * wave_data * envelope).astype(np.int16)
    return add_fast_envelope(wave_data, sample_rate)

def create_sound_files():
    """Genera sonidos diseñados específicamente para dar una respuesta táctil y satisfactoria."""
    sounds_dir = Path("assets/SOUNDS")
    sounds_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generando fábrica de dopamina...\n")
    
    # === CONVEYOR (Acción súper común, debe ser sutil y rápida) ===
    # PLACE: Un "Pop" ascendente (burbuja pequeña)
    wave_data = generate_pop(300, 600, duration=0.06, amplitude=12000)
    save_wav(sounds_dir / "conveyor_place.wav", wave_data)
    
    # DELETE: Un "Pop" descendente un poco más bajo
    wave_data = generate_pop(400, 200, duration=0.06, amplitude=10000)
    save_wav(sounds_dir / "conveyor_delete.wav", wave_data)
    
    # === DRILL (Máquina pesada, requiere contundencia) ===
    # PLACE: Un "Thud" o "Toc" grave y seco
    wave_data = generate_thump(110, duration=0.08, amplitude=18000)
    save_wav(sounds_dir / "drill_place.wav", wave_data)
    
    # DELETE: Un "Thud" más sordo y bajo
    wave_data = generate_thump(75, duration=0.08, amplitude=14000)
    save_wav(sounds_dir / "drill_delete.wav", wave_data)
    
    # === CHEST (Objeto valioso/almacenamiento, sonido brillante) ===
    # PLACE: Acorde mayor (Do + Mi), sonido de éxito
    wave_data = generate_bell(523.25, 659.25, duration=0.15, amplitude=10000)
    save_wav(sounds_dir / "chest_place.wav", wave_data)
    
    # DELETE: Acorde descendente/menor (Sol + Si bemol)
    wave_data = generate_bell(466.16, 392.00, duration=0.15, amplitude=8000)
    save_wav(sounds_dir / "chest_delete.wav", wave_data)
    
    # === GENÉRICOS DE FALLBACK ===
    # PLACE genérico: Pop medio
    wave_data = generate_pop(400, 500, duration=0.08, amplitude=11000)
    save_wav(sounds_dir / "machine_placed.wav", wave_data)
    
    # DELETE genérico: Pop inverso
    wave_data = generate_pop(500, 400, duration=0.08, amplitude=9000)
    save_wav(sounds_dir / "machine_deleted.wav", wave_data)
    
    # === EXTRACTION (Acción muy repetitiva) ===
    # Mineral extraído: Un "clink" corto, agudo pero de muy bajo volumen (3500 vs los 12000 del Pop)
    wave_data = generate_tick(frequency=900, duration=0.035, amplitude=3500)
    save_wav(sounds_dir / "mineral_extracted.wav", wave_data)
    
    # === ERRORES / DENEGADO ===
    
    # Error fuerte: Zumbido áspero para colisiones o bloqueos
    wave_data = generate_error_buzzer(frequency=110, duration=0.15, amplitude=8000)
    save_wav(sounds_dir / "error_blocked.wav", wave_data)
    
    print("\n✓ ¡Listo!")

if __name__ == "__main__":
    create_sound_files()