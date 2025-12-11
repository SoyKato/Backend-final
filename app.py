from flask import Flask, render_template, jsonify, request
import sqlite3
import math

app = Flask(__name__)

# Calcula la distancia en metros entre dos coordenadas usando la fórmula de Haversine
def calcular_distancia(lat1, lon1, lat2, lon2):

    R = 6371000
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2) * math.sin(delta_lat/2) + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * \
        math.sin(delta_lon/2) * math.sin(delta_lon/2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distancia = R * c
    return distancia

# Crea la base de datos y carga los datos del CSV
def inicializar_db():
    conn = sqlite3.connect('oxxos.db')
    cursor = conn.cursor()
    

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS oxxos (
            id INTEGER PRIMARY KEY,
            nombre TEXT,
            latitud REAL,
            longitud REAL
        )
    ''')
    

    cursor.execute('SELECT COUNT(*) FROM oxxos')
    if cursor.fetchone()[0] == 0:

        import csv
        with open('Oxxos_normalizado.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cursor.execute('''
                    INSERT INTO oxxos (id, nombre, latitud, longitud)
                    VALUES (?, ?, ?, ?)
                ''', (row['id'], row['nombre'], float(row['latitud']), float(row['longitud'])))
        
        conn.commit()
        print("Base de datos inicializada con los datos del CSV")
    
    conn.close()

@app.route('/')
# Renderizar pagina principal
def index():
    return render_template('index.html')

@app.route('/api/oxxos-cercanos')

# API que devuelve los Oxxos cercanos en una ubicacion
def oxxos_cercanos():

    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        radio = float(request.args.get('radio', 60))
        
        conn = sqlite3.connect('oxxos.db')
        cursor = conn.cursor()
        

        cursor.execute('SELECT id, nombre, latitud, longitud FROM oxxos')
        todos_oxxos = cursor.fetchall()
        

        oxxos_cercanos = []
        for oxxo in todos_oxxos:
            oxxo_id, nombre, lat_oxxo, lon_oxxo = oxxo
            distancia = calcular_distancia(lat, lon, lat_oxxo, lon_oxxo)
            
            if distancia <= radio:
                oxxos_cercanos.append({
                    'id': oxxo_id,
                    'nombre': nombre,
                    'latitud': lat_oxxo,
                    'longitud': lon_oxxo,
                    'distancia': round(distancia, 2)
                })
        
        conn.close()
        

        oxxos_cercanos.sort(key=lambda x: x['distancia'])
        
        return jsonify({
            'success': True,
            'total': len(oxxos_cercanos),
            'oxxos': oxxos_cercanos
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/todos-oxxos')

# API que devuelve todos los Oxxos
def todos_oxxos():
    try:
        conn = sqlite3.connect('oxxos.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, nombre, latitud, longitud FROM oxxos')
        oxxos = cursor.fetchall()
        
        conn.close()
        
        oxxos_list = []
        for oxxo in oxxos:
            oxxos_list.append({
                'id': oxxo[0],
                'nombre': oxxo[1],
                'latitud': oxxo[2],
                'longitud': oxxo[3]
            })
        
        return jsonify({
            'success': True,
            'total': len(oxxos_list),
            'oxxos': oxxos_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

if __name__ == '__main__':

    inicializar_db()
    
    print("Servidor Flask iniciado en http://localhost:5000")
    app.run(debug=True, port=5000)
