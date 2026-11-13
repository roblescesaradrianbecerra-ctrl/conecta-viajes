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
        ubicacion_lat REAL,
        ubicacion_lng REAL,
        creado TEXT DEFAULT (datetime('now','localtime'))
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS viajes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pasajero_id INTEGER,
        pasajero_nombre TEXT,
        pasajero_tel TEXT,
        conductor_id INTEGER DEFAULT 0,
        conductor_nombre TEXT DEFAULT '',
        conductor_tel TEXT DEFAULT '',
        origen TEXT,
        origen_lat REAL,
        origen_lng REAL,
        destino TEXT,
        destino_lat REAL,
        destino_lng REAL,
        distancia REAL DEFAULT 0,
        monto_total REAL,
        comision REAL,
        estado TEXT DEFAULT 'DISPONIBLE',
        pasajero_calificacion INTEGER DEFAULT 0,
        conductor_calificacion INTEGER DEFAULT 0,
        fecha TEXT DEFAULT (datetime('now','localtime'))
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS mensajes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        viaje_id INTEGER,
        remitente_nombre TEXT,
        texto TEXT,
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
            viajes = c.execute("SELECT * FROM viajes WHERE estado!='COMPLETADO' ORDER BY id DESC LIMIT 20").fetchall()
            fin = c.execute("SELECT * FROM finanzas WHERE id=1").fetchone()
            c.close()
            
            html = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🚗 Conecta Viajes</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',system-ui,sans-serif;}}
:root{{--primario:#2563eb;--exito:#22c55e;--alerta:#f59e0b;--peligro:#ef4444;--fondo:#f8fafc;--tarjeta:#fff;--texto:#1e293b;--claro:#64748b;}}
body{{background:var(--fondo);color:var(--texto);min-height:100vh;padding-bottom:80px;}}
.cabecera{{background:linear-gradient(135deg,#2563eb,#1d4ed8);color:white;padding:20px;text-align:center;position:sticky;top:0;z-index:100;box-shadow:0 2px 10px rgba(0,0,0,.1);}}
.cabecera h1{{font-size:22px;display:flex;align-items:center;justify-content:center;gap:8px;}}
.barra-superior{{background:white;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 1px 3px rgba(0,0,0,.05);}}
.saldo{{background:linear-gradient(135deg,#10b981,#059669);color:white;padding:10px 16px;border-radius:20px;font-weight:bold;font-size:14px;}}
.tabs{{position:fixed;bottom:0;left:0;right:0;background:white;display:flex;box-shadow:0 -2px 10px rgba(0,0,0,.08);z-index:100;}}
.tab{{flex:1;padding:12px;text-align:center;font-size:12px;cursor:pointer;border-top:3px solid transparent;color:var(--claro);transition:.2s;}}
.tab.activa{{border-top-color:var(--primario);color:var(--primario);font-weight:bold;}}
.tab span{{font-size:20px;display:block;margin-bottom:2px;}}
.contenido{{padding:16px;max-width:520px;margin:0 auto;}}
.seccion{{display:none;}}
.seccion.activa{{display:block;animation:aparece .3s ease;}}
@keyframes aparece{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}
.tarjeta{{background:white;border-radius:16px;padding:16px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,.04);border:1px solid #f1f5f9;}}
.tarjeta h2{{font-size:17px;margin-bottom:14px;color:var(--texto);display:flex;align-items:center;gap:6px;}}
.grupo-input{{margin-bottom:12px;}}
label{{display:block;font-size:13px;color:var(--claro);margin-bottom:4px;font-weight:500;}}
input, select{{width:100%;padding:12px;border:1px solid #e2e8f0;border-radius:8px;font-size:15px;background:#fafafa;}}
input:focus, select:focus{{outline:none;border-color:var(--primario);background:white;}}
button{{width:100%;padding:14px;border:none;border-radius:10px;font-size:15px;font-weight:bold;cursor:pointer;transition:.2s;}}
.btn-primario{{background:var(--primario);color:white;}}
.btn-primario:hover{{background:#1d4ed8;}}
.btn-exito{{background:var(--exito);color:white;}}
.btn-alerta{{background:var(--alerta);color:white;}}
.btn-peligro{{background:var(--peligro);color:white;}}
.btn-outline{{background:transparent;border:2px solid var(--primario);color:var(--primario);}}
.etapa{{display:inline-block;padding:4px 12px;border-radius:12px;font-size:12px;font-weight:bold;margin-bottom:10px;}}
.disponible{{background:#dbeafe;color:#1e40af;}}
.asignado{{background:#dcfce7;color:#166534;}}
.completado{{background:#f1f5f9;color:#475569;}}
.mapa{{height:200px;border-radius:10px;margin:10px 0;z-index:1;}}
.fila{{display:flex;gap:10px;flex-wrap:wrap;}}
.fila button{{flex:1;min-width:140px;}}
.datos-viaje{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0;}}
.dato{{background:#f8fafc;padding:10px;border-radius:8px;}}
.dato small{{color:var(--claro);font-size:12px;}}
.dato strong{{font-size:16px;color:var(--texto);}}
.chat{{max-height:250px;overflow-y:auto;margin:10px 0;border:1px solid #eee;border-radius:8px;padding:10px;background:#fafafa;}}
.mensaje{{margin-bottom:8px;padding:8px 12px;border-radius:16px;max-width:80%;font-size:14px;}}
.mensaje.tuyo{{background:var(--primario);color:white;margin-left:auto;border-bottom-right-radius:4px;}}
.mensaje.suyo{{background:#e2e8f0;color:var(--texto);margin-right:auto;border-bottom-left-radius:4px;}}
.estadisticas{{display:grid;grid-template-columns:1fr 1fr;gap:12px;}}
.est{{background:white;padding:16px;border-radius:12px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,.03);}}
.est-num{{font-size:28px;font-weight:bold;color:var(--primario);}}
.est-etq{{font-size:12px;color:var(--claro);margin-top:4px;}}
.oculto{{display:none !important;}}
.aviso{{background:#eff6ff;border-left:4px solid var(--primario);padding:12px;border-radius:6px;margin-bottom:16px;font-size:14px;}}
.resumen-superior{{background:linear-gradient(135deg,#1e40af,#3b82f6);color:white;padding:16px;border-radius:12px;margin-bottom:16px;}}
.resumen-superior h3{{font-size:14px;opacity:.8;margin-bottom:4px;}}
.resumen-superior .numero{{font-size:24px;font-weight:bold;}}
.estrella{{color:#f59e0b;font-size:18px;}}
</style>
</head>
<body>

<div class="cabecera">
<h1>🚗 Conecta Viajes</h1>
</div>

<div class="barra-superior">
<span style="font-weight:bold;font-size:15px;">📍 Aguascalientes, Ags.</span>
<div class="saldo">💰 ${round(fin[2],2)} MXN</div>
</div>

<div class="contenido">

<!-- PANEL INICIO -->
<div id="inicio" class="seccion activa">
<div class="resumen-superior">
<h3>Comisiones acumuladas</h3>
<div class="numero">${round(fin[2],2)} <small style="font-size:14px;opacity:.8">MXN</small></div>
<small>{fin[1]} viajes completados · Comisión: {COMISION_PORCENTAJE}%</small><br>
<small>CLABE BBVA: {TU_CLABE}</small>
</div>

<div class="estadisticas">
<div class="est"><div class="est-num">{fin[1]}</div><div class="est-etq">Viajes</div></div>
<div class="est"><div class="est-num">{COMISION_PORCENTAJE}%</div><div class="est-etq">Comisión</div></div>
<div class="est"><div class="est-num">24/7</div><div class="est-etq">Activo</div></div>
<div class="est"><div class="est-num">0</div><div class="est-etq">Usuarios</div></div>
</div>

<div style="margin-top:20px;">
<h2 style="font-size:18px;margin-bottom:12px;">📊 Viajes Recientes</h2>
'''
            if not viajes:
                html += '<p style="text-align:center;color:var(--claro);padding:30px;">No hay viajes publicados aún. ¡Sé el primero en publicar uno!</p>'
            else:
                for v in viajes[:5]:
                    estado_clase = 'disponible' if v[9]=='DISPONIBLE' else 'asignado' if v[9]=='ASIGNADO' else 'completado'
                    html += f'''<div class="tarjeta" style="margin-bottom:12px;">
<span class="etapa {estado_clase}">{v[9]}</span>
<p><strong>📍 {v[4]}</strong> → <strong>{v[6]}</strong></p>
<p style="font-size:14px;color:var(--claro);">💲 ${v[8]} · Tu comisión: ${round(v[8]*0.2,2)}</p>
</div>'''
            html += '''</div></div>

<!-- PUBLICAR VIAJE -->
<div id="pedir" class="seccion">
<div class="tarjeta">
<h2>📲 Publicar un viaje</h2>
<div class="aviso">Llena los datos y presiona "Publicar". Los conductores cercanos lo verán al instante.</div>
<div class="grupo-input">
<label>Tu nombre completo</label>
<input id="p_nombre" placeholder="ej. Juan Pérez">
</div>
<div class="grupo-input">
<label>Tu teléfono</label>
<input id="p_tel" placeholder="ej. 4491234567" type="tel">
</div>
<div class="grupo-input">
<label>📍 Punto de partida</label>
<input id="origen" placeholder="¿Desde dónde sales?">
</div>
<div class="grupo-input">
<label>🎯 Destino</label>
<input id="destino" placeholder="¿A dónde vas?">
</div>
<div class="grupo-input">
<label>💰 Monto total a pagar ($ MXN)</label>
<input id="monto" placeholder="ej. 150" type="number">
</div>
<div class="dato" style="background:#eff6ff;border:1px solid #bfdbfe;">
<small>Conductor recibe el 80%</small><br>
<strong>Tú recibes: <span id="comision_muestra">$0.00</span> ({COMISION_PORCENTAJE}%)</strong>
</div>
<button class="btn-primario" style="margin-top:16px;" onclick="publicarViaje()">🚀 PUBLICAR VIAJE</button>
</div>
</div>

<!-- TOMAR VIAJE -->
<div id="tomar" class="seccion">
<div class="tarjeta">
<h2>🚘 Viajes Disponibles</h2>
<div class="grupo-input">
<label>Tu nombre (conductor)</label>
<input id="c_nombre" placeholder="Tu nombre completo">
</div>
<div class="grupo-input">
<label>Tu teléfono</label>
<input id="c_tel" placeholder="Tu número" type="tel">
</div>
<div id="lista-viajes">
'''
            disponibles = [v for v in viajes if v[9] == 'DISPONIBLE']
            if not disponibles:
                html += '<p style="text-align:center;color:var(--claro);padding:30px;">🔍 No hay viajes disponibles ahora mismo.<br>Revisa más tarde o comparte la app.</p>'
            else:
                for v in disponibles:
                    html += f'''<div class="tarjeta" style="border:1px solid #e2e8f0;">
<span class="etapa disponible">DISPONIBLE</span>
<p style="font-size:15px;"><strong>📍 Origen:</strong> {v[4]}</p>
<p style="font-size:15px;"><strong>🎯 Destino:</strong> {v[6]}</p>
<p style="font-size:16px;margin:8px 0;"><strong>💲 ${v[8]}</strong> · Recibes: <span style="color:var(--exito);font-weight:bold;">${round(v[8]*0.8,2)}</span></p>
<button class="btn-exito" onclick="tomarViaje({v[0]})">✅ YO LO TOMO</button>
</div>'''
            html += '</div></div></div>'

<!-- MIS VIAJES -->
<div id="mis" class="seccion">
<h2 style="margin-bottom:16px;">📋 Mis Viajes</h2>
<div id="mis_contenido">'
            asignados = [v for v in viajes if v[9] == 'ASIGNADO']
            if not asignados:
                html += '<p style="text-align:center;color:var(--claro);padding:30px;">No tienes viajes asignados aún.<br>Ve a "Tomar Viaje" para ver los disponibles.</p>'
            else:
                for v in asignados:
                    html += f'''<div class="tarjeta">
<span class="etapa asignado">ASIGNADO</span>
<div class="datos-viaje">
<div class="dato"><small>De</small><br><strong>{v[4]}</strong></div>
<div class="dato"><small>Hasta</small><br><strong>{v[6]}</strong></div>
</div>
<div class="datos-viaje">
<div class="dato"><small>Pasajero</small><br><strong>{v[1]}</strong><br><a href="tel:{v[2]}" style="color:var(--primario);text-decoration:none;">📞 Llamar</a></div>
<div class="dato"><small>Conductor</small><br><strong>{v[5]}</strong><br><a href="tel:{v[3]}" style="color:var(--primario);text-decoration:none;">📞 Llamar</a></div>
</div>
<div class="dato" style="background:#fef3c7;border:1px solid #fcd34d;">
<small>💰 Total: ${v[8]} · Tu comisión: ${round(v[8]*0.2,2)}</small>
</div>
<div class="fila" style="margin-top:10px;">
<button class="btn-alerta" onclick="abrirChat({v[0]})">💬 CHAT</button>
<button class="btn-exito" onclick="terminarViaje({v[0]})">✅ COMPLETAR</button>
</div>
<div id="chat_{v[0]}" class="oculto" style="margin-top:12px;">
<div class="chat" id="caja_{v[0]}">
<p style="text-align:center;color:var(--claro);font-size:13px;">— Inicia la conversación —</p>
</div>
<div style="display:flex;gap:8px;margin-top:8px;">
<input type="text" id="msg_{v[0]}" placeholder="Escribe un mensaje..." style="flex:1;">
<button class="btn-primario" style="width:auto;padding:10px 14px;" onclick="enviarMensaje({v[0]})">➤</button>
</div>
</div>
</div>'''
            html += '</div></div>'

<!-- PERFIL -->
<div id="perfil" class="seccion">
<div class="tarjeta">
<h2>👤 Tu Perfil</h2>
<div style="text-align:center;padding:20px 0;">
<div style="font-size:60px;">🚗</div>
<h3 style="font-size:20px;margin-top:10px;">Conecta Viajes</h3>
<p style="color:var(--claro);">Plataforma de viajes local</p>
<div style="margin-top:12px;">
<span class="estrella">⭐⭐⭐⭐⭐</span>
<p style="font-weight:bold;">5.0 · 0 reseñas</p>
</div>
</div>
</div>
<div class="tarjeta">
<h2>📊 Resumen</h2>
<div class="datos-viaje">
<div class="dato"><small>Viajes</small><br><strong>{fin[1]}</strong></div>
<div class="dato"><small>Comisión %</small><br><strong>{COMISION_PORCENTAJE}%</strong></div>
<div class="dato"><small>Ganancia</small><br><strong>${round(fin[2],2)}</strong></div>
<div class="dato"><small>Estado</small><br><strong style="color:var(--exito);">Activo ✅</strong></div>
</div>
</div>
<div class="tarjeta">
<h2>💳 Datos de Cobro</h2>
<p><strong>CLABE BBVA:</strong><br><code style="background:#f1f5f9;padding:6px 10px;border-radius:4px;font-family:monospace;">{TU_CLABE}</code></p>
<p style="margin-top:8px;font-size:13px;color:var(--claro);">El conductor te entrega el 20% en efectivo al completar el viaje.</p>
</div>
<div class="tarjeta">
<h2>ℹ️ Ayuda</h2>
<p style="font-size:14px;line-height:1.6;">• <strong>Publicar:</strong> Ingresa tus datos y el origen/dest
