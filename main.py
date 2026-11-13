from http.server import HTTPServer, BaseHTTPRequestHandler
import sqlite3, json
import os

PUERTO = int(os.environ.get("PORT", 9011))
COMISION_PORCENTAJE = 20
TU_CLABE = "012010015243130140"

def init_db():
    c = sqlite3.connect('plataforma.db')
    c.execute('''CREATE TABLE IF NOT EXISTS viajes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pasajero_nombre TEXT,
        pasajero_tel TEXT,
        conductor_nombre TEXT DEFAULT '',
        conductor_tel TEXT DEFAULT '',
        origen TEXT,
        destino TEXT,
        monto_total REAL,
        comision REAL,
        estado TEXT DEFAULT 'DISPONIBLE',
        fecha TEXT DEFAULT (datetime('now','localtime'))
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS finanzas(
        id INTEGER PRIMARY KEY,
        viajes_completados INTEGER DEFAULT 0,
        total_comisiones REAL DEFAULT 0
    )''')
    if not c.execute('SELECT 1 FROM finanzas WHERE id=1').fetchone():
        c.execute('INSERT INTO finanzas(id) VALUES(1)')
    c.commit()
    c.close()

class Manejador(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.end_headers()
            c = sqlite3.connect('plataforma.db')
            viajes = c.execute("SELECT * FROM viajes WHERE estado='DISPONIBLE' OR estado='ASIGNADO' ORDER BY id DESC LIMIT 30").fetchall()
            fin = c.execute("SELECT * FROM finanzas WHERE id=1").fetchone()
            c.close()
            
            html = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🚗 Conecta Viajes</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,-apple-system,sans-serif;}}
body{{background:#f5f7fa;padding:16px;max-width:520px;margin:0 auto;}}
h1{{color:#2563eb;text-align:center;margin-bottom:16px;font-size:22px;}}
.tarjeta{{background:white;border-radius:12px;padding:16px;margin-bottom:12px;box-shadow:0 2px 6px rgba(0,0,0,0.06);}}
h2{{font-size:16px;margin-bottom:10px;color:#333;}}
input{{width:100%;padding:11px;margin:6px 0 10px;border:1px solid #ddd;border-radius:6px;font-size:15px;}}
button{{width:100%;padding:12px;border:none;border-radius:6px;font-size:15px;font-weight:bold;cursor:pointer;}}
.btn-azul{{background:#2563eb;color:white;}}
.btn-verde{{background:#22c55e;color:white;}}
.btn-naranja{{background:#f97316;color:white;}}
.etapa{{display:inline-block;padding:4px 10px;border-radius:12px;font-size:13px;font-weight:bold;margin-bottom:8px;}}
.disponible{{background:#dbeafe;color:#1e40af;}}
.asignado{{background:#dcfce7;color:#166534;}}
.tabs{{display:flex;gap:8px;margin-bottom:16px;}}
.tab{{flex:1;padding:10px;background:#eee;border-radius:6px;text-align:center;font-size:14px;cursor:pointer;}}
.tab.activa{{background:#2563eb;color:white;}}
.seccion{{display:none;}}
.seccion.activa{{display:block;}}
.resumen{{background:#fef3c7;border-left:4px solid #f59e0b;padding:12px;border-radius:6px;margin-bottom:16px;}}
</style>
</head>
<body>
<h1>🚗 Conecta Viajes</h1>

<div class="resumen">
<strong>💰 Tus Comisiones:</strong> {fin[1]} viajes completados<br>
<strong>Total acumulado:</strong> ${round(fin[2],2)} MXN<br>
<small>CLABE BBVA: <code>{TU_CLABE}</code> — Comisión: {COMISION_PORCENTAJE}%</small>
</div>

<div class="tabs">
<div class="tab activa" onclick="mostrar('pedir')">👤 Pido Viaje</div>
<div class="tab" onclick="mostrar('tomar')">🚘 Tomo Viaje</div>
<div class="tab" onclick="mostrar('mis')">📋 Mis Viajes</div>
</div>

<div id="pedir" class="seccion activa">
<div class="tarjeta">
<h2>📍 Publicar un viaje</h2>
<input id="p_nombre" placeholder="Tu nombre completo">
<input id="p_tel" placeholder="Tu teléfono" type="tel">
<input id="origen" placeholder="¿De dónde sales?">
<input id="destino" placeholder="¿A dónde vas?">
<input id="monto" placeholder="¿Cuánto pagas? $" type="number">
<button class="btn-azul" onclick="publicar()">🚀 PUBLICAR VIAJE</button>
</div>
</div>

<div id="tomar" class="seccion">
<div class="tarjeta">
<h2>🚘 Viajes disponibles</h2>
<input id="c_nombre" placeholder="Tu nombre (conductor)">
<input id="c_tel" placeholder="Tu teléfono" type="tel">
'''
            for v in viajes:
                if v[9] == 'DISPONIBLE':
                    html += f'''<div style="border-bottom:1px solid #eee;padding:12px 0;">
<span class="etapa disponible">DISPONIBLE</span>
<p><strong>📍 {v[4]}</strong> → <strong>{v[5]}</strong></p>
<p>💲 ${v[6]} — Tú recibes: ${round(v[6]*0.8,2)}</p>
<button class="btn-verde" onclick="tomar({v[0]})">✅ YO LO TOMO</button>
</div>'''
            if not any(v[9] == 'DISPONIBLE' for v in viajes):
                html += '<p style="text-align:center;color:#888;padding:20px;">Sin viajes disponibles por ahora.</p>'
            html += '</div></div>'

            html += '<div id="mis" class="seccion"><div class="tarjeta"><h2>🤝 Viajes asignados</h2>'
            for v in viajes:
                if v[9] == 'ASIGNADO':
                    html += f'''<div style="border-bottom:1px solid #eee;padding:12px 0;">
<span class="etapa asignado">ASIGNADO</span>
<p><strong>📍 {v[4]}</strong> → <strong>{v[5]}</strong></p>
<p>👤 Pasajero: {v[1]} — {v[2]}</p>
<p>🚘 Conductor: {v[6] if len(v)>6 else v[5]} — {v[7] if len(v)>7 else v[6]}</p>
<p>💲 Total: ${v[6]} — Tu comisión: ${round(v[6]*0.2,2)}</p>
<button class="btn-naranja" onclick="terminar({v[0]})">✅ VIAJE TERMINADO</button>
</div>'''
            if not any(v[9] == 'ASIGNADO' for v in viajes):
                html += '<p style="text-align:center;color:#888;padding:20px;">Sin viajes asignados.</p>'
            html += '</div></div>'

            html += '''<script>
function mostrar(s){
document.querySelectorAll('.seccion').forEach(x=>x.classList.remove('activa'));
document.querySelectorAll('.tab').forEach(x=>x.classList.remove('activa'));
document.getElementById(s).classList.add('activa');
event.target.classList.add('activa');
}
async function publicar(){
const datos = {
nombre: document.getElementById('p_nombre').value,
telefono: document.getElementById('p_tel').value,
origen: document.getElementById('origen').value,
destino: document.getElementById('destino').value,
monto_total: parseFloat(document.getElementById('monto').value),
comision: parseFloat(document.getElementById('monto').value)*0.2
};
if(!datos.nombre || !datos.telefono || !datos.origen || !datos.destino || !datos.monto_total){
alert('Llena todos los datos');return;
}
await fetch('/publicar-viaje', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(datos)});
alert('✅ ¡Publicado! Espera a que un conductor lo tome');location.reload();
}
async function tomar(id){
const nombre = document.getElementById('c_nombre').value;
const tel = document.getElementById('c_tel').value;
if(!nombre || !tel){alert('Escribe tu nombre y teléfono primero');return;}
await fetch('/tomar-viaje', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({viaje_id:id,nombre,telefono:tel})});
alert('✅ ¡Viaje tuyo! Ve a "Mis Viajes" para ver los datos del pasajero');location.reload();
}
async function terminar(id){
if(confirm('¿Viaje terminado y comisión entregada?')){
await fetch('/completar-viaje', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({viaje_id:id})});
alert('✅ ¡Listo! Comisión registrada');location.reload();
}
}
</script>
</body></html>'''
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        c = sqlite3.connect('plataforma.db')
        longitud = int(self.headers.get('Content-Length'))
        cuerpo = self.rfile.read(longitud)
        datos = json.loads(cuerpo.decode('utf-8'))
        
        if self.path == '/publicar-viaje':
            c.execute('INSERT INTO viajes(pasajero_nombre,pasajero_tel,origen,destino,monto_total,comision) VALUES(?,?,?,?,?,?)',
                (datos['nombre'], datos['telefono'], datos['origen'], datos['destino'], datos['monto_total'], datos['comision']))
            c.commit()
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok":True}).encode())
        
        elif self.path == '/tomar-viaje':
            c.execute('UPDATE viajes SET estado="ASIGNADO", conductor_nombre=?, conductor_tel=? WHERE id=? AND estado="DISPONIBLE"',
                (datos['nombre'], datos['telefono'], datos['viaje_id']))
            c.commit()
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok":True}).encode())
        
        elif self.path == '/completar-viaje':
            viaje = c.execute('SELECT * FROM viajes WHERE id=?', (datos['viaje_id'],)).fetchone()
            c.execute('UPDATE viajes SET estado="COMPLETADO" WHERE id=?', (datos['viaje_id'],))
            c.execute('UPDATE finanzas SET viajes_completados=viajes_completados+1, total_comisiones=total_comisiones+? WHERE id=1', (viaje[8],))
            c.commit()
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok":True}).encode())
        
        c.close()

if __name__ == "__main__":
    init_db()
    print("✅ Servidor corriendo en el puerto", PUERTO)
    HTTPServer(("0.0.0.0", PUERTO), Manejador).serve_forever()
          
