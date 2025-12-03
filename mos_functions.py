"""
mos_functions.py
Funciones core para cálculo de MOS en VoIP
"""

import subprocess
import re
import statistics
from datetime import datetime
import platform


def hacer_ping(ip, cantidad=10):
    """
    Realiza ping a una IP y guarda los resultados en un archivo.
    
    Parámetros:
    - ip: Dirección IP a hacer ping
    - cantidad: Número de pings a realizar (default: 10)
    
    Retorna:
    - nombre_archivo: Ruta del archivo creado o None si hay error
    """
    fecha_hora = datetime.now().strftime("%Y%m%d-%H%M%S")
    nombre_archivo = f"pings/ping-{ip}-{fecha_hora}.txt"
    
    sistema = platform.system().lower()
    
    try:
        if sistema == "windows":
            comando = ["ping", "-n", str(cantidad), ip]
        else:  # Linux, macOS
            comando = ["ping", "-c", str(cantidad), ip]
        
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=cantidad * 2
        )
        
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(f"Ping a {ip} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            f.write(resultado.stdout)
            if resultado.stderr:
                f.write("\nErrores:\n")
                f.write(resultado.stderr)
        
        return nombre_archivo
        
    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
        return None


def calcular_latencia_promedio(archivo):
    """
    Calcula la latencia promedio desde un archivo de ping.
    
    Parámetros:
    - archivo: Ruta del archivo con resultados de ping
    
    Retorna:
    - latencia_promedio: Latencia promedio en ms o None si hay error
    """
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        patrones = [
            r'tiempo[=<](\d+\.?\d*)\s*ms',
            r'time[=<](\d+\.?\d*)\s*ms',
        ]
        
        latencias = []
        for patron in patrones:
            matches = re.findall(patron, contenido, re.IGNORECASE)
            if matches:
                latencias.extend([float(m) for m in matches])
        
        if not latencias:
            return None
        
        return statistics.mean(latencias)
        
    except FileNotFoundError:
        return None
    except Exception as e:
        return None


def calcular_jitter(archivo):
    """
    Calcula el jitter (variación de latencia) desde un archivo de ping.
    
    Parámetros:
    - archivo: Ruta del archivo con resultados de ping
    
    Retorna:
    - jitter: Jitter en ms (desviación estándar) o None si hay error
    """
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        patrones = [
            r'tiempo[=<](\d+\.?\d*)\s*ms',
            r'time[=<](\d+\.?\d*)\s*ms',
        ]
        
        latencias = []
        for patron in patrones:
            matches = re.findall(patron, contenido, re.IGNORECASE)
            if matches:
                latencias.extend([float(m) for m in matches])
        
        if len(latencias) < 2:
            return None
        
        return statistics.stdev(latencias)
        
    except FileNotFoundError:
        return None
    except Exception as e:
        return None


def calcular_paquetes_perdidos(archivo):
    """
    Calcula el porcentaje de paquetes perdidos desde un archivo de ping.
    
    Parámetros:
    - archivo: Ruta del archivo con resultados de ping
    
    Retorna:
    - porcentaje_perdida: Porcentaje de paquetes perdidos (0-100) o None si hay error
    """
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Windows español
        match = re.search(r'enviados\s*=\s*(\d+).*?recibidos\s*=\s*(\d+)', contenido, re.IGNORECASE)
        if match:
            enviados = int(match.group(1))
            recibidos = int(match.group(2))
            perdidos = enviados - recibidos
            porcentaje = (perdidos / enviados) * 100 if enviados > 0 else 0
        else:
            # Linux/macOS o Windows inglés
            match = re.search(r'(\d+)\s+packets?\s+transmitted.*?(\d+)\s+received.*?(\d+\.?\d*)%\s+packet\s+loss', contenido, re.IGNORECASE)
            if match:
                porcentaje = float(match.group(3))
            else:
                match = re.search(r'(\d+\.?\d*)%\s+(perdidos|loss)', contenido, re.IGNORECASE)
                if match:
                    porcentaje = float(match.group(1))
                else:
                    return None
        
        return porcentaje
        
    except FileNotFoundError:
        return None
    except Exception as e:
        return None


def calcular_mos(latencia_promedio, jitter, perdida_paquetes):
    """
    Calcula el MOS (Mean Opinion Score) para llamadas VoIP.
    
    Parámetros:
    - latencia_promedio: Latencia promedio en ms
    - jitter: Jitter en ms
    - perdida_paquetes: Porcentaje de pérdida de paquetes (0-100)
    
    Retorna:
    - tupla: (MOS, R-Factor, latencia_efectiva)
    """
    latencia_efectiva = latencia_promedio + (jitter * 2) + 10
    
    if latencia_efectiva < 160:
        R = 93.2 - (latencia_efectiva / 40)
    else:
        R = 93.2 - ((latencia_efectiva - 120) / 10)
    
    R = R - (perdida_paquetes * 2.5)
    
    MOS = 1 + (0.035 * R) + (0.000007 * R * (R - 60) * (100 - R))
    
    return MOS, R, latencia_efectiva


def clasificar_mos(mos):
    """
    Clasifica la calidad de la llamada según el valor MOS.
    
    Parámetros:
    - mos: Valor MOS (1-5)
    
    Retorna:
    - calidad: String con la clasificación
    """
    if mos >= 4.3:
        return "Excelente"
    elif mos >= 4.0:
        return "Buena"
    elif mos >= 3.6:
        return "Aceptable"
    elif mos >= 3.1:
        return "Pobre"
    else:
        return "Mala"


def analizar_ip(ip, cantidad_pings):
    """
    Realiza análisis completo de una IP: ping y cálculo de métricas.
    
    Parámetros:
    - ip: Dirección IP a analizar
    - cantidad_pings: Cantidad de pings a realizar
    
    Retorna:
    - dict con resultados o dict con error
    """
    try:
        # Realizar ping
        archivo = hacer_ping(ip, cantidad_pings)
        if not archivo:
            return {'error': True, 'mensaje': 'No se pudo hacer ping a la IP'}
        
        # Calcular métricas
        latencia = calcular_latencia_promedio(archivo)
        jitter = calcular_jitter(archivo)
        perdida = calcular_paquetes_perdidos(archivo)
        
        # Verificar que tenemos todos los datos
        if latencia is None:
            return {'error': True, 'mensaje': 'No se pudo calcular la latencia'}
        if jitter is None:
            return {'error': True, 'mensaje': 'No se pudo calcular el jitter'}
        if perdida is None:
            return {'error': True, 'mensaje': 'No se pudo calcular la pérdida de paquetes'}
        
        # Calcular MOS
        mos, r_factor, lat_efectiva = calcular_mos(latencia, jitter, perdida)
        calidad = clasificar_mos(mos)
        
        return {
            'ip': ip,
            'latencia': latencia,
            'jitter': jitter,
            'perdida': perdida,
            'mos': mos,
            'r_factor': r_factor,
            'latencia_efectiva': lat_efectiva,
            'calidad': calidad,
            'archivo': archivo,
            'error': False
        }
    except Exception as e:
        return {'error': True, 'mensaje': f'Error inesperado: {str(e)}'}