# Patrician3FX-Resoluciones
Nuevas resoluciones para Patrician III 1.13, versión de FX en español.

1. Descomprimir el .zip de la resolución elegida en la carpeta de Patrician 3. Se sobreescribirá el archivo Patrician3.exe.
2. Dentro del juego hay que seleccionar la resolución 1024x768, que en realidad contendrá la resolución que hayamos descargado. Esta no se aplicará hasta que no iniciemos una partida.

Para crear nuevas resoluciones, seguir esta guía de Steam: 

## Nuevas resoluciones

Antiguamente utilizaba esta guía de Steam y seguía los pasos a mano https://steamcommunity.com/sharedfiles/filedetails/?id=382413909

Ahora he creado un script de Python para crear automáticamente cualquier resolución. Lo único que hay que hacer es descargar el contenido de la carpeta p3_hex_replace y ejecutar en una terminal:

```bash
python p3_hex_replace.py ./Patrician3.exe 2560 1440
```
Se puede sustituir `2560 1440` por la resolución deseada.