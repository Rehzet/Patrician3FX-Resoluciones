"""
reemplazo_hex_especifico.py

Script para modificar la resolución del juego:
- Fase 1: modificar el EXE
- Fase 2: modificar los archivos ini y redimensionar las imágenes
Todos los resultados se guardan en una carpeta 'output-<resolucion>'.
"""

import sys
import os
import mmap
from shutil import copy2, copytree, rmtree
from PIL import Image

# ---------------------------
# FASE 1 - Modificación del EXE
# ---------------------------

FIRST_GROUP = [
    "C7 44 24 18 00 04 00 00 C7 44 24 1C 00 03 00 00",
    "C7 44 24 3C 00 04 00 00 C7 44 24 40 00 03 00 00",
    "C7 44 24 48 00 04 00 00 C7 44 24 4C 00 03 00 00",
    "C7 44 24 24 00 04 00 00 C7 44 24 28 00 03 00 00",
]

SECOND_GROUP = [
    "0F 84 AF 00 00 00 3D 00 05 00 00",
    "3D 00 04 00 00 74 1E 3D 00 05 00 00",
]

def int_to_le_bytes(value):
    return value.to_bytes(4, byteorder='little')

def backup(path):
    bak = path + '.bak'
    copy2(path, bak)
    return bak

def find_all_offsets(data, subseq):
    offsets = []
    start = 0
    while True:
        idx = data.find(subseq, start)
        if idx == -1:
            break
        offsets.append(idx)
        start = idx + 1
    return offsets

def replace_in_place_at_offsets(path, offsets_and_pairs):
    with open(path, 'r+b') as f:
        mm = mmap.mmap(f.fileno(), 0)
        try:
            for off, orig, new in offsets_and_pairs:
                if mm[off:off+len(orig)] != orig:
                    raise RuntimeError(f'Valor distinto en offset {off}: esperado {orig.hex()} pero encontrado {mm[off:off+len(orig)].hex()}')
                mm[off:off+len(orig)] = new
            mm.flush()
        finally:
            mm.close()

def process_group(data, sequences, replacements):
    offsets_and_pairs = []
    found_any = False

    for seq_hex in sequences:
        seq_bytes = bytes.fromhex(seq_hex.replace(' ', ''))
        occs = find_all_offsets(data, seq_bytes)
        for occ in occs:
            found_any = True
            for orig, new in replacements.items():
                rel_start = 0
                while True:
                    rel = seq_bytes.find(orig, rel_start)
                    if rel == -1:
                        break
                    abs_off = occ + rel
                    offsets_and_pairs.append((abs_off, orig, new))
                    rel_start = rel + 1
    return found_any, offsets_and_pairs

# ---------------------------
# FASE 2 - Modificación de archivos y redimensionado de imágenes
# ---------------------------

def update_ini_file(path, replacements):
    with open(path, 'r', encoding='latin1') as f:
        content = f.read()
    for old, new in replacements.items():
        content = content.replace(old, new)
    with open(path, 'w', encoding='latin1') as f:
        f.write(content)

def resize_image(path, new_width=None, new_height=None):
    img = Image.open(path)
    width, height = img.size
    if new_width is None:
        new_width = width
    if new_height is None:
        new_height = height
    img_resized = img.resize((new_width, new_height), Image.LANCZOS)
    img_resized.save(path)

def fase2_update_files(output_base, width, height):
    scripts_path = os.path.join(output_base, 'scripts')
    images_path = os.path.join(output_base, 'images')

    update_ini_file(os.path.join(scripts_path, 'accelMap.ini'), {'1280 1024': f'{width} {height}'})
    width_adj = width - 284
    height_adj = height - 600
    update_ini_file(os.path.join(scripts_path, 'screenGame.ini'), {
        '740': str(width_adj),
        '996': str(width_adj),
        '424': str(height_adj)
    })
    update_ini_file(os.path.join(scripts_path, 'textures.ini'), {'1280 1024': f'{width} {height}'})

    resize_image(os.path.join(images_path, 'Vollansichtskarte1280.bmp'), new_width=width, new_height=height)
    resize_image(os.path.join(images_path, 'HauptscreenE1280.bmp'), new_height=height-600)

# ---------------------------
# MAIN
# ---------------------------

def main():
    if len(sys.argv) != 4:
        print('Uso: python reemplazo_hex_especifico.py archivo.exe ancho alto')
        sys.exit(1)

    path = sys.argv[1]
    try:
        width = int(sys.argv[2])
        height = int(sys.argv[3])
    except ValueError:
        print('Error: ancho y alto deben ser números enteros.')
        sys.exit(1)

    if width <= 0 or height <= 0 or width > 16384 or height > 16384:
        print('Error: valores de resolución inválidos.')
        sys.exit(1)

    if not os.path.isfile(path):
        print('Error: no existe el archivo especificado:', path)
        sys.exit(1)

    base_dir = os.path.dirname(os.path.abspath(path))
    output_dir = os.path.join(base_dir, f'output-{width}x{height}')

    if os.path.exists(output_dir):
        rmtree(output_dir)
    os.makedirs(output_dir)

    # Copiar EXE, scripts e images a output antes de modificar
    exe_output_path = os.path.join(output_dir, os.path.basename(path))
    copy2(path, exe_output_path)
    copytree(os.path.join(base_dir, 'scripts'), os.path.join(output_dir, 'scripts'))
    copytree(os.path.join(base_dir, 'images'), os.path.join(output_dir, 'images'))

    # ---------------------------
    # FASE 1: modificar EXE en output
    # ---------------------------
    print(f'FASE 1: modificando {exe_output_path} a resolución {width}x{height}')
    width_bytes = int_to_le_bytes(width)[:2]
    height_bytes = int_to_le_bytes(height)[:2]

    FIRST_GROUP_REPLACEMENTS = {
        bytes.fromhex('00 04'): width_bytes,
        bytes.fromhex('00 03'): height_bytes,
    }
    SECOND_GROUP_REPLACEMENTS = {
        bytes.fromhex('00 05'): width_bytes,
    }

    print('Creando backup...')
    bak = backup(exe_output_path)
    print('Backup guardado en', bak)

    with open(exe_output_path, 'rb') as f:
        data = f.read()

    all_offsets = []
    found1, offsets1 = process_group(data, FIRST_GROUP, FIRST_GROUP_REPLACEMENTS)
    found2, offsets2 = process_group(data, SECOND_GROUP, SECOND_GROUP_REPLACEMENTS)
    if found1 or found2:
        all_offsets.extend(offsets1)
        all_offsets.extend(offsets2)

    if not all_offsets:
        print('No se encontraron secuencias en el EXE. Fase 1 no realizó cambios.')
    else:
        replace_in_place_at_offsets(exe_output_path, all_offsets)
        print('FASE 1 completada: EXE modificado exitosamente.')

    # ---------------------------
    # FASE 2: modificar archivos de configuración y redimensionar imágenes en output
    # ---------------------------
    fase2_update_files(output_dir, width, height)
    print('FASE 2 completada: archivos modificados y imágenes redimensionadas automáticamente.')
    print(f'Todo el resultado está en: {output_dir}')

if __name__ == '__main__':
    main()
