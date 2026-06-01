"""Gestión de los especiales del día (la base de datos del restaurante).

Ejemplos de uso (desde la raíz del proyecto):
  python restaurante-especiales/gestion.py add "Lomo Saltado" --precio 35 --desc "Clásico peruano" --imagen lomo.jpg
  python restaurante-especiales/gestion.py list
  python restaurante-especiales/gestion.py activar 1
  python restaurante-especiales/gestion.py desactivar 1
  python restaurante-especiales/gestion.py remove 1
"""
import argparse
import json
import os
from datetime import date

CARPETA = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(CARPETA, "especiales.json")


def cargar():
    if not os.path.exists(DB):
        return {"especiales": []}
    with open(DB, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar(datos):
    with open(DB, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def nuevo_id(datos):
    ids = [e["id"] for e in datos["especiales"]]
    return max(ids) + 1 if ids else 1


def cmd_add(args):
    datos = cargar()
    especial = {
        "id": nuevo_id(datos),
        "nombre": args.nombre,
        "descripcion": args.desc,
        "precio": args.precio,
        "imagen": args.imagen,
        "video": args.video,
        "activo": True,
        "mostrar_nombre": True,
        "mostrar_precio": True,
        "duracion": args.duracion,
        "fecha": date.today().isoformat(),
    }
    datos["especiales"].append(especial)
    guardar(datos)
    print(f"Agregado #{especial['id']}: {especial['nombre']}")


def cmd_list(args):
    datos = cargar()
    if not datos["especiales"]:
        print("No hay especiales todavia. Agrega uno con: python restaurante-especiales/gestion.py add \"Nombre\"")
        return
    print("Especiales:")
    for e in datos["especiales"]:
        estado = "ACTIVO" if e["activo"] else "inactivo"
        print(f"  #{e['id']} [{estado}] {e['nombre']} - ${e['precio']}  (imagen: {e['imagen'] or '-'})")


def cmd_estado(args, activo):
    datos = cargar()
    for e in datos["especiales"]:
        if e["id"] == args.id:
            e["activo"] = activo
            guardar(datos)
            print(f"#{args.id} -> {'activado' if activo else 'desactivado'}")
            return
    print(f"No existe el especial #{args.id}")


def cmd_remove(args):
    datos = cargar()
    antes = len(datos["especiales"])
    datos["especiales"] = [e for e in datos["especiales"] if e["id"] != args.id]
    if len(datos["especiales"]) < antes:
        guardar(datos)
        print(f"Eliminado #{args.id}")
    else:
        print(f"No existe el especial #{args.id}")


def main():
    parser = argparse.ArgumentParser(description="Gestión de especiales del día")
    sub = parser.add_subparsers(dest="comando", required=True)

    p_add = sub.add_parser("add", help="Agregar un especial")
    p_add.add_argument("nombre")
    p_add.add_argument("--precio", type=float, default=0)
    p_add.add_argument("--desc", default="")
    p_add.add_argument("--imagen", default="")
    p_add.add_argument("--video", default="")
    p_add.add_argument("--duracion", type=float, default=8, help="Segundos en pantalla")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="Listar especiales")
    p_list.set_defaults(func=cmd_list)

    p_on = sub.add_parser("activar", help="Activar un especial (se muestra en la TV)")
    p_on.add_argument("id", type=int)
    p_on.set_defaults(func=lambda a: cmd_estado(a, True))

    p_off = sub.add_parser("desactivar", help="Desactivar un especial (se oculta de la TV)")
    p_off.add_argument("id", type=int)
    p_off.set_defaults(func=lambda a: cmd_estado(a, False))

    p_rm = sub.add_parser("remove", help="Eliminar un especial")
    p_rm.add_argument("id", type=int)
    p_rm.set_defaults(func=cmd_remove)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
