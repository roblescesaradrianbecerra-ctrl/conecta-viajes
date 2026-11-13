from http.server import HTTPServer, BaseHTTPRequestHandler
import sqlite3, json, os
from datetime import datetime

PUERTO = int(os.environ.get("PORT", 9011))
COMISION_PORCENTAJE = 20
TU_CLABE = "012010015243130140"

def init_db():
    c = sqlite3.connect('plataforma.db')
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        telefono TEXT UNIQUE,
        tipo TEXT,
        foto TEXT DEFAULT '👤',
        calificacion REAL DEFAULT 5.0,
        reseñas INTEGER DEFAULT 0,
        creado TEXT DEFAULT (datetime('now','localtime'))
    )''')
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

init_db()

class Manejador(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.end_headers()
            c = sqlite3.connect('plataforma.db')
            viajes = c.execute("SELECT * FROM viajes WHERE estado!='COMPLETADO' ORDER BY id DESC LIMIT 20").fetchall()
            fin = c.execute("SELECT * FROM finanzas WHERE id=1").fetchone()
            c.close()
            
            html = '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Conecta Viajes</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,sans-serif;}
:root{--p:#2563eb;--e:#22c55e;--a:#f59e0b;--f:#f8fafc;--t:#1e293b;--g:#64748b;}
body{background:var(--f);color:var(--t);padding-bottom:70px;}
.cabecera{background:linear-gradient(135deg,#2563eb,#1d4ed8);color:white;padding:18px;text-align:center;position:sticky;top:0;}
.cabecera h1{font-size:20px;}
.barra{background:white;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 1px 3px rgba(0,0,0,.05);}
.saldo{background:linear-gradient(135deg,#10b981,#059669);color:white;padding:8px 14px;border-radius:20px;font-weight:bold;font-size:14px;}
.tabs{position:fixed;bottom:0;left:0;right:0;background:white;display:flex;box-shadow:0 -2px 10px rgba(0,0,0,.08);}
.tab{flex:1;padding:10px;text-align:center;font-size:11px;cursor:pointer;border-top:3px solid transparent;color:var(--g);}
.tab.activa{border-top-color:var(--p);color:var(--p);font-weight:bold;}
.tab span{font-size:18px;display:block;margin-bottom:2px;}
.cont{padding:16px;max-width:520px;margin:0 auto;}
.seccion{display:none;}
.seccion.activa{display:block;}
.tarjeta{background:white;border-radius:12px;padding:16px;margin-bottom:16px;box-shadow:0 2px 6px rgba(0,0,0,.04);}
.tarjeta h2{font-size:16px;margin-bottom:12px;}
label{display:block;font-size:13px;color:var(--g);margin-bottom:4px;}
input{width:100%;padding:11px;border:1px solid #e2e8f0;border-radius:8px;font-size:15px;margin-bottom:10px;}
button{width:100%;padding:13px;border:none;border-radius:8px;font-size:15px;font-weight:bold;cursor:pointer;}
.btn-p{background:var(--p);color:white;}
.btn-e{background:var(--e);color:white;}
.etapa{display:inline-block;padding:4px 10px;border-radius:12px;font-size:12px;font-weight:bold;margin-bottom:8px;}
.disp{background:#dbeafe;color:#1e40af;}
.asig{background:#dcfce7;color:#166534;}
.resumen{background:linear-gradient(135deg,#1e40af,#3b82f6);color:white;padding:16px;border-radius:12px;margin-bottom:16px;}
.numero{font-size:26px;font-weight:bold;}
.aviso{background:#eff6ff;border-left:4px solid var(--p);padding:12px;border-radius:6px;margin-bottom:16px;font-size:14px;}
</style>
</head>
<body>

<div class="cabecera"><h1>Conecta Viajes</h1></div>
<div class="barra">
<span style="font-weight:bold;">Aguascalientes</span>
<div class="saldo">$'''+str(round(fin[2],2))+'''</div>
</div>

<div class="cont">
<div id="inicio" class="seccion activa">
<div class="resumen">
<h3>Comisiones acumuladas</h3>
<div class="numero">$'''+str(round(fin[2],2))+'''</div>
<small>'''+str(fin[1])+''' viajes - Comision: 20%</small><br>
<small>CLABE BBVA: 012010015243130140</small>
</div>
<div class="tarjeta">
<h2>Viajes Recientes</h2>
'''
            if not viajes:
                html += '<p style="text-align:center;color:var(--g);padding:20px;">No hay viajes publicados aun</p>'
            else:
                for v in viajes[:5]:
                    estado_clase = 'disp' if v[9]=='DISPONIBLE' else 'asig'
                    html += '<div style="padding:10px 0;border-bottom:1px solid #eee;">'
                    html += '<span class="etapa '+estado_clase+'">'+v[9]+'</span>'
                    html += '<p><strong>'+str(v[4])+'</strong> -> <strong>'+str(v[5])+'</strong></p>'
                    html += '<p style="font-size:14px;color:var(--g);">$'+str(v[7])+' - Comision: $'+str(round(v[7]*0.2,2))+'</p>'
                    html += '</div>'
            html += '</div></div>'

html += '''<div id="pedir" class="seccion">
<div class="tarjeta">
<h2>Publicar Viaje</h2>
<div class="aviso">Llena los datos y presiona Publicar</div>
<label>Tu nombre</label>
<input id="p_nombre" placeholder="Tu nombre completo">
<label>Telefono</label>
<input id="p_tel" placeholder="4491234567" type="tel">
<label>Origen</label>
<input id="origen" placeholder="Desde donde sales">
<label>Destino</label>
<input id="destino" placeholder="A donde vas">
<label>Monto total ($)</label>
<input id="monto" placeholder="150" type="number" oninput="actualizarComision()">
<p style="background:#eff6ff;padding:10px;border-radius:6px;margin:10px 0;">
Conductor recibe 80%<br>
<strong>Tu recibes: <span id="comision">$0.00</span> (20%)</strong>
</p>
<button class="btn-p" onclick="publicar()">PUBLICAR VIAJE</button>
</div></div>'''

html += '''<div id="tomar" class="seccion">
<div class="tarjeta">
<h2>Viajes Disponibles</h2>
<label>Tu nombre (conductor)</label>
<input id="c_nombre" placeholder="Tu nombre">
<label>Tu telefono</label>
<input id="c_tel" placeholder="Tu numero" type="tel">
<div id="lista">'''
            disponibles = [v for v in viajes if v[9] == 'DISPONIBLE']
            if not disponibles:
                html += '<p style="text-align:center;color:var(--g);padding:20px;">No hay viajes disponibles</p>'
            else:
                for v in disponibles:
                    html += '<div style="border:1px solid #e2e8f0;padding:12px;border-radius:8px;margin-bottom:10px;">'
                    html += '<span class="etapa disp">DISPONIBLE</span>'
                    html += '<p>Origen: '+str(v[4])+'</p>'
                    html += '<p>Destino: '+str(v[5])+'</p>'
                    html += '<p>Total: $'+str(v[7])+' - Recibes: $'+str(round(v[7]*0.8,2))+'</p>'
                    html += '<button class="btn-e" onclick="tomar('+str(v[0])+')">YO LO TOMO</button>'
                    html += '</div>'
            html += '</div></div></div>'

html += '''<script>
function mostrarSeccion(id){
    document.querySelectorAll('.seccion').forEach(s=>s.classList.remove('activa'));
    document.querySelectorAll('.tab').forEach(t=>t.classList.remove('activa'));
    document.getElementById(id).classList.add('activa');
    event.target.classList.add('activa');
}
function actualizarComision(){
    const m = parseFloat(document.getElementById('monto').value)||0;
    document.getElementById('comision').textContent = '$'+(m*0.2).toFixed(2);
}
async function publicar(){
    const datos = {
        nombre: document.getElementById('p_nombre').value,
        tel: document.getElementById('p_tel').value,
        origen: document.getElementById('origen').value,
        destino: document.getElementById('destino').value,
        monto: parseFloat(document.getElementById('monto').value)
    };
    if(!datos.nombre || !datos.origen || !datos.destino || !datos.monto){
        alert('Llena todos los campos');return;
    }
    datos.comision = datos.monto * 0.2;
    const res = await fetch('/nuevo-viaje',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(datos)
    });
    if(res.ok){alert('Viaje publicado');location.reload();}
    else{alert('Error al publicar');}
}
async function tomar(id){
    const nombre = document.getElementById('c_nombre').value;
    const tel = document.getElementById('c_tel').value;
    if(!nombre || !tel){alert('Escribe tu nombre y telefono');return;}
    const res = await fetch('/tomar-viaje/'+id,{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({nombre:nombre,tel:tel})
    });
    if(res.ok){alert('Viaje tomado! Comunicate con el pasajero');location.reload();}
    else{alert('Error');}
}
</script>

<div class="tabs">
<div class="tab activa" onclick="mostrarSeccion('inicio')"><span>🏠</span>Inicio</div>
<div class="tab" onclick="mostrarSeccion('pedir')"><span>📲</span>Publicar</div>
<div class="tab" onclick="mostrarSeccion('tomar')"><span>🚘</span>Tomar</div>
</div>

</body>
</html>'''
            self.wfile.write(html.encode('utf-8'))

    def do_POST(self):
        c = sqlite3.connect('plataforma.db')
        long = int(self.headers['Content-Length'])
        cuerpo = self.rfile.read(long)
        datos = json.loads(cuerpo)
        
        if self.path == '/nuevo-viaje':
            c.execute('INSERT INTO viajes(pasajero_nombre,pasajero_tel,origen,destino,monto_total,comision) VALUES(?,?,?,?,?,?)',
                (datos['nombre'],datos['tel'],datos['origen'],datos['destino'],datos['monto'],datos['comision']))
            c.commit()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
            
        elif self.path.startswith('/tomar-viaje/'):
            id_viaje = int(self.path.split('/')[2])
            c.execute("UPDATE viajes SET conductor_nombre=?, conductor_tel=?, estado='ASIGNADO' WHERE id=?",
                (datos['nombre'],datos['tel'],id_viaje))
            c.commit()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        else:
            self.send_response(404)
            self.end_headers()
        c.close()

if __name__ == '__main__':
    init_db()
    servidor = HTTPServer(('0.0.0.0', PUERTO), Manejador)
    print("Servidor corriendo en puerto", PUERTO)
    servidor.serve_forever()
    
