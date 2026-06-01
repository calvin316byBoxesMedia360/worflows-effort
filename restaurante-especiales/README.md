# 🍽️ Restaurante — Especiales del día

App para gestionar los especiales del día (imágenes y videos) y mostrarlos en una TV
a través del navegador de un Firestick.

## Estructura

```
restaurante-especiales/
├── gestion.py          # Agregar / listar / activar / eliminar especiales (la "DB")
├── servidor.py         # Servidor web que muestra los especiales en la TV
├── especiales.json     # El catálogo (base de datos en JSON)
├── requirements.txt    # Dependencias (Flask)
└── media/              # Imágenes y videos editados
```

## Uso rápido (desde la raíz del proyecto)

```powershell
# 1. Gestionar especiales
python restaurante-especiales/gestion.py add "Lomo Saltado" --precio 35 --desc "Clasico" --imagen lomo.jpg
python restaurante-especiales/gestion.py list

# 2. Instalar Flask (solo la primera vez)
python -m pip install -r restaurante-especiales/requirements.txt

# 3. Levantar el servidor
python restaurante-especiales/servidor.py
```

Luego, en el Firestick, abre `http://<IP-de-tu-PC>:5000/` (mismo WiFi que el PC).

> 💡 También puedes usar el workflow `/especial-del-dia` dentro de Claude Code para
> que te guíe en todo esto sin recordar los comandos.
