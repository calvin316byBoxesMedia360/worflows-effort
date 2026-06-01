"""Servidor web del restaurante.

Tiene dos "caras":
  /        -> Vista para la TV (Firestick): muestra los especiales activos (fotos y videos),
              rota solo según la duración de cada plato, con transición suave.
  /admin   -> Dashboard de gestión: agregar, editar (nombre/precio/duración),
              activar/ocultar, eliminar, y controlar si se muestra nombre y/o precio.

Uso (desde la raíz del proyecto):
  python -m pip install -r restaurante-especiales/requirements.txt   (solo la primera vez)
  python restaurante-especiales/servidor.py
Luego:
  TV (Firestick):  http://<IP-de-tu-PC>:5000/
  Dashboard:       http://<IP-de-tu-PC>:5000/admin
"""
import json
import os
from datetime import date

from flask import Flask, request, redirect, send_from_directory
from werkzeug.utils import secure_filename

# Reutilizamos la lógica de la "base de datos" que ya vive en gestion.py
from gestion import cargar, guardar, nuevo_id

CARPETA = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(CARPETA, "media")


app = Flask(__name__)


# ---------------------------------------------------------------------------
# VISTA TV  (/)  — lo que ven los clientes en el televisor
# ---------------------------------------------------------------------------
@app.route("/")
def pantalla():
    activos = [e for e in cargar()["especiales"] if e.get("activo")]
    return TV_HTML.replace("__DATOS__", json.dumps(activos, ensure_ascii=False))


@app.route("/media/<path:archivo>")
def media(archivo):
    return send_from_directory(MEDIA, archivo)


# ---------------------------------------------------------------------------
# DASHBOARD  (/admin)  — lo que usa el personal del restaurante
# ---------------------------------------------------------------------------
@app.route("/admin")
def admin():
    datos = cargar()
    forms_edit = ""
    filas = ""
    for e in datos["especiales"]:
        eid = e["id"]
        activo = e.get("activo")
        m_nombre = e.get("mostrar_nombre", True)
        m_precio = e.get("mostrar_precio", True)
        dur = e.get("duracion", 8)

        badge = "<span class='badge on'>Activo</span>" if activo else "<span class='badge off'>Oculto</span>"
        if e.get("video"):
            media_cell = "<span class='media-ico' title='Video'>🎬</span>"
        elif e.get("imagen"):
            media_cell = f"<img src='/media/{e['imagen']}' class='thumb'>"
        else:
            media_cell = "—"
        estado_lbl = "Ocultar" if activo else "Activar"
        nombre_cls, nombre_lbl = ("on", "Nombre ✅") if m_nombre else ("off", "Nombre ⬜")
        precio_cls, precio_lbl = ("on", "Precio ✅") if m_precio else ("off", "Precio ⬜")

        # Formulario (vacío) de edición, asociado por el atributo form= a los inputs de la fila
        forms_edit += f"<form id='ed{eid}' method='post' action='/admin/editar/{eid}'></form>"

        filas += f"""
        <tr>
          <td>#{eid}</td>
          <td class='th'>{media_cell}</td>
          <td><input class='edit' form='ed{eid}' name='nombre' value="{e['nombre']}"></td>
          <td><input class='edit precio' form='ed{eid}' name='precio' type='number' step='0.01' value="{e['precio']}"></td>
          <td><input class='edit dur' form='ed{eid}' name='duracion' type='number' step='1' min='1' value="{dur}"> s</td>
          <td>
            <form method='post' action='/admin/toggle-campo/{eid}/nombre' class='inline'><button class='btn tiny {nombre_cls}'>{nombre_lbl}</button></form>
            <form method='post' action='/admin/toggle-campo/{eid}/precio' class='inline'><button class='btn tiny {precio_cls}'>{precio_lbl}</button></form>
          </td>
          <td>
            {badge}
            <form method='post' action='/admin/toggle/{eid}' class='inline'><button class='btn'>{estado_lbl}</button></form>
          </td>
          <td>
            <button class='btn save' form='ed{eid}' type='submit'>💾 Guardar</button>
            <form method='post' action='/admin/eliminar/{eid}' class='inline' onsubmit="return confirm('¿Eliminar {e['nombre']}?')"><button class='btn del'>Eliminar</button></form>
          </td>
        </tr>"""

    if not filas:
        filas = "<tr><td colspan='8' class='vacio'>No hay especiales todavía. Agrega el primero abajo 👇</td></tr>"

    return ADMIN_HTML.replace("__FORMS__", forms_edit).replace("__FILAS__", filas)


def _guardar_archivo(campo):
    """Guarda un archivo subido (imagen o video) en media/ y devuelve su nombre."""
    archivo = request.files.get(campo)
    if archivo and archivo.filename:
        nombre = secure_filename(archivo.filename)
        os.makedirs(MEDIA, exist_ok=True)
        archivo.save(os.path.join(MEDIA, nombre))
        return nombre
    return ""


@app.route("/admin/agregar", methods=["POST"])
def admin_agregar():
    nombre = (request.form.get("nombre") or "").strip()
    if not nombre:
        return redirect("/admin")

    datos = cargar()
    datos["especiales"].append({
        "id": nuevo_id(datos),
        "nombre": nombre,
        "descripcion": request.form.get("descripcion", ""),
        "precio": float(request.form.get("precio") or 0),
        "imagen": _guardar_archivo("imagen"),
        "video": _guardar_archivo("video"),
        "activo": True,
        "mostrar_nombre": True,
        "mostrar_precio": True,
        "duracion": float(request.form.get("duracion") or 8),
        "fecha": date.today().isoformat(),
    })
    guardar(datos)
    return redirect("/admin")


@app.route("/admin/editar/<int:especial_id>", methods=["POST"])
def admin_editar(especial_id):
    """Edita nombre, precio y duración de un especial (se sincroniza con especiales.json)."""
    datos = cargar()
    for e in datos["especiales"]:
        if e["id"] == especial_id:
            nombre = (request.form.get("nombre") or "").strip()
            if nombre:
                e["nombre"] = nombre
            try:
                e["precio"] = float(request.form.get("precio") or 0)
            except ValueError:
                pass
            try:
                e["duracion"] = max(1.0, float(request.form.get("duracion") or 8))
            except ValueError:
                pass
            break
    guardar(datos)
    return redirect("/admin")


@app.route("/admin/toggle-campo/<int:especial_id>/<campo>", methods=["POST"])
def admin_toggle_campo(especial_id, campo):
    """Activa/desactiva mostrar el nombre o el precio de un especial en la TV."""
    clave = {"nombre": "mostrar_nombre", "precio": "mostrar_precio"}.get(campo)
    if clave:
        datos = cargar()
        for e in datos["especiales"]:
            if e["id"] == especial_id:
                e[clave] = not e.get(clave, True)
                break
        guardar(datos)
    return redirect("/admin")


@app.route("/admin/toggle/<int:especial_id>", methods=["POST"])
def admin_toggle(especial_id):
    datos = cargar()
    for e in datos["especiales"]:
        if e["id"] == especial_id:
            e["activo"] = not e.get("activo")
            break
    guardar(datos)
    return redirect("/admin")


@app.route("/admin/eliminar/<int:especial_id>", methods=["POST"])
def admin_eliminar(especial_id):
    datos = cargar()
    datos["especiales"] = [e for e in datos["especiales"] if e["id"] != especial_id]
    guardar(datos)
    return redirect("/admin")


# ---------------------------------------------------------------------------
# Plantillas HTML
# ---------------------------------------------------------------------------
TV_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Especiales de hoy</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:#0b0b0b; color:#fff; font-family:Arial, sans-serif; overflow:hidden; }
  /* Todas las diapositivas se apilan; la 'activa' aparece con un fundido suave */
  .slide { position:fixed; inset:0; display:flex; flex-direction:column;
           align-items:center; justify-content:center; text-align:center; padding:4vh;
           opacity:0; transition:opacity 0.8s ease; }
  .slide.activa { opacity:1; }
  .slide img, .slide video { max-width:80vw; max-height:55vh; border-radius:18px; box-shadow:0 0 40px #000; }
  h1 { font-size:5vw; margin-top:3vh; }
  p  { font-size:2.4vw; color:#ffcc66; margin-top:1.5vh; max-width:70vw; }
  .precio { font-size:4vw; color:#7CFC00; margin-top:2vh; font-weight:bold; }
  .vacio { font-size:3vw; color:#888; }
</style>
</head>
<body>
<div id="cont"></div>
<script>
  const especiales = __DATOS__;
  const cont = document.getElementById("cont");

  if (especiales.length === 0) {
    cont.innerHTML = "<div class='slide activa'><p class='vacio'>No hay especiales activos</p></div>";
    setTimeout(() => location.reload(), 15000);   // revisa si agregaron algo
  } else {
    especiales.forEach((e) => {
      const div = document.createElement("div");
      div.className = "slide";
      let html = "";
      if (e.video)        html += `<video src="/media/${e.video}" autoplay muted loop playsinline></video>`;
      else if (e.imagen)  html += `<img src="/media/${e.imagen}">`;
      if (e.mostrar_nombre !== false) html += `<h1>${e.nombre}</h1>`;
      if (e.descripcion) html += `<p>${e.descripcion}</p>`;
      if (e.precio && e.mostrar_precio !== false) html += `<div class="precio">$${e.precio}</div>`;
      div.innerHTML = html;
      cont.appendChild(div);
    });

    const slides = document.querySelectorAll(".slide");

    function mostrar(i) {
      slides.forEach(s => s.classList.remove("activa"));
      slides[i].classList.add("activa");
      // Si la diapositiva tiene video, lo reiniciamos y reproducimos
      const vid = slides[i].querySelector("video");
      if (vid) { try { vid.currentTime = 0; vid.play(); } catch (_) {} }

      const segs = Number(especiales[i].duracion) || 8;   // ⏱️ duración de ESTE plato
      setTimeout(() => {
        const sig = (i + 1) % slides.length;
        // Al completar una vuelta entera, recargamos para tomar cambios del dashboard
        if (sig === 0) location.reload();
        else mostrar(sig);
      }, segs * 1000);
    }

    mostrar(0);
  }
</script>
</body>
</html>"""

ADMIN_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dashboard — Especiales</title>
<style>
  * { box-sizing:border-box; }
  body { background:#f4f5f7; color:#222; font-family:Arial, sans-serif; margin:0; padding:24px; }
  h1 { margin:0 0 4px; }
  .sub { color:#666; margin-bottom:24px; }
  .card { background:#fff; border-radius:12px; padding:20px; box-shadow:0 2px 8px rgba(0,0,0,.08); margin-bottom:24px; }
  table { width:100%; border-collapse:collapse; }
  th, td { text-align:left; padding:10px; border-bottom:1px solid #eee; vertical-align:middle; }
  th { color:#888; font-size:13px; text-transform:uppercase; }
  .thumb { height:40px; border-radius:6px; }
  .media-ico { font-size:26px; }
  .th { width:60px; }
  .badge { padding:3px 10px; border-radius:20px; font-size:12px; font-weight:bold; }
  .badge.on { background:#e3f7e3; color:#1a7f1a; }
  .badge.off { background:#eee; color:#999; }
  .inline { display:inline; }
  input.edit { padding:7px; border:1px solid #ccc; border-radius:7px; font-size:14px; width:150px; }
  input.edit.precio { width:80px; }
  input.edit.dur { width:60px; }
  .btn { border:none; border-radius:8px; padding:7px 12px; cursor:pointer; background:#2563eb; color:#fff; font-size:13px; margin:2px; }
  .btn.del { background:#e53935; }
  .btn.save { background:#1a7f1a; }
  .btn.add { background:#1a7f1a; font-size:15px; padding:10px 18px; }
  .btn.tiny { padding:5px 9px; font-size:12px; }
  .btn.tiny.on { background:#1a7f1a; }
  .btn.tiny.off { background:#bbb; color:#444; }
  .vacio { text-align:center; color:#999; padding:24px; }
  form.add { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
  form.add input { padding:9px; border:1px solid #ccc; border-radius:8px; font-size:14px; }
  form.add input[name=nombre] { flex:1; min-width:160px; }
  form.add label { font-size:13px; color:#666; }
  a.tv { display:inline-block; margin-top:8px; color:#2563eb; text-decoration:none; font-weight:bold; }
  .hint { color:#888; font-size:12px; margin-top:6px; }
</style>
</head>
<body>
  <h1>🍽️ Dashboard — Especiales del día</h1>
  <div class="sub">Gestiona qué platos se muestran en la TV.
    <a class="tv" href="/" target="_blank">📺 Ver la pantalla de la TV →</a>
  </div>

  <div style="display:none">__FORMS__</div>

  <div class="card">
    <table>
      <thead>
        <tr><th>ID</th><th>Media</th><th>Plato</th><th>Precio</th><th>Duración</th><th>Mostrar en TV</th><th>Estado</th><th>Acciones</th></tr>
      </thead>
      <tbody>__FILAS__</tbody>
    </table>
    <div class="hint">✏️ Edita nombre, precio o duración (segundos en pantalla) y pulsa 💾 Guardar.
      Los botones "Nombre/Precio" controlan si se ven en la TV. 🎬 = tiene video.</div>
  </div>

  <div class="card">
    <h3 style="margin-top:0">➕ Agregar especial</h3>
    <form class="add" method="post" action="/admin/agregar" enctype="multipart/form-data">
      <input name="nombre" placeholder="Nombre del plato" required>
      <input name="precio" type="number" step="0.01" placeholder="Precio">
      <input name="descripcion" placeholder="Descripción">
      <input name="duracion" type="number" step="1" min="1" value="8" title="Segundos en pantalla" style="width:90px">
      <label>📷 <input name="imagen" type="file" accept="image/*"></label>
      <label>🎬 <input name="video" type="file" accept="video/*"></label>
      <button class="btn add" type="submit">Agregar</button>
    </form>
  </div>
</body>
</html>"""


if __name__ == "__main__":
    print("Servidor activo:")
    print("  TV (Firestick): http://<IP-de-tu-PC>:5000/")
    print("  Dashboard:      http://<IP-de-tu-PC>:5000/admin")
    app.run(host="0.0.0.0", port=5000)
