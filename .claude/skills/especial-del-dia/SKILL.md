---
name: especial-del-dia
description: Workflow para gestionar los especiales del día del restaurante — agregar, listar, activar/desactivar platos (con sus imágenes y videos) y publicarlos para mostrarlos en la TV vía Firestick. Usar cuando el usuario quiera gestionar especiales, agregar un plato, ver el catálogo, o mostrar los especiales en pantalla.
---

# Workflow: Especial del día 🍽️

Este workflow gestiona el catálogo de especiales del restaurante y los publica para
mostrarlos en una TV a través del navegador del Firestick.

## Archivos del proyecto (en la carpeta `restaurante-especiales/`)

- `restaurante-especiales/especiales.json` — el catálogo (la "base de datos")
- `restaurante-especiales/gestion.py` — script para agregar / listar / activar / eliminar
- `restaurante-especiales/servidor.py` — servidor web (vista para la TV + dashboard)
- `restaurante-especiales/media/` — carpeta donde van las imágenes y videos editados
- `restaurante-especiales/requirements.txt` — dependencias (Flask)

## Qué hacer según lo que pida el usuario

### ➕ AGREGAR un especial
1. Si falta info, pregunta: nombre del plato, precio, descripción y la ruta de la imagen/video.
2. Si el archivo de media está fuera de `restaurante-especiales/media/`, cópialo ahí primero.
3. Ejecuta:
   `python restaurante-especiales/gestion.py add "<nombre>" --precio <p> --desc "<descripcion>" --imagen <archivo>`
4. Confirma mostrando el catálogo: `python restaurante-especiales/gestion.py list`

### 📋 VER / LISTAR
- Ejecuta `python restaurante-especiales/gestion.py list` y muestra el resultado.

### 🔓 ACTIVAR / DESACTIVAR (controla qué se ve en la TV)
- `python restaurante-especiales/gestion.py activar <id>`  o  `... desactivar <id>`

### 🗑️ ELIMINAR
- `python restaurante-especiales/gestion.py remove <id>`

### 📺 MOSTRAR en la TV (Firestick)
1. Verifica que Flask esté instalado: `python -m pip install -r restaurante-especiales/requirements.txt`
2. Inicia el servidor: `python restaurante-especiales/servidor.py`
3. Averigua la IP local del PC con `ipconfig` (busca "IPv4").
4. Dale al usuario la URL: `http://<IP-del-PC>:5000/` para abrir en el navegador del Firestick.
   El **dashboard** de gestión está en `http://<IP-del-PC>:5000/admin`.

## Notas importantes

- El PC y el Firestick deben estar en la **misma red WiFi**.
- El servidor lee `especiales.json` en cada carga, y la página de la TV se recarga sola
  cada 60s, así que los cambios aparecen sin reiniciar nada.
- Solo se muestran los especiales con `"activo": true`.
