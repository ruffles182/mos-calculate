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
    - nombre_archivo: Ruta del archivo creado
    """
    # Generar nombre del archivo con fecha y hora actual
    fecha_hora = datetime.now().strftime("%Y%m%d-%H%M%S")
    nombre_archivo = f"pings/ping-{ip}-{fecha_hora}.txt"
    
    # Detectar sistema operativo
    sistema = platform.system().lower()
    
    try:
        # Construir comando según el sistema operativo
        if sistema == "windows":
            comando = ["ping", "-n", str(cantidad), ip]
        else:  # Linux, macOS
            comando = ["ping", "-c", str(cantidad), ip]
        
        print(f"Realizando {cantidad} pings a {ip}...")
        
        # Ejecutar ping
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=cantidad * 2  # timeout dinámico
        )
        
        # Guardar resultado en archivo
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(f"Ping a {ip} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            f.write(resultado.stdout)
            if resultado.stderr:
                f.write("\nErrores:\n")
                f.write(resultado.stderr)
        
        print(f"✓ Resultados guardados en: {nombre_archivo}")
        return nombre_archivo
        
    except subprocess.TimeoutExpired:
        print(f"✗ Error: Timeout al hacer ping a {ip}")
        return None
    except Exception as e:
        print(f"✗ Error al ejecutar ping: {e}")
        return None


def calcular_latencia_promedio(archivo):
    """
    Calcula la latencia promedio desde un archivo de ping.
    
    Parámetros:
    - archivo: Ruta del archivo con resultados de ping
    
    Retorna:
    - latencia_promedio: Latencia promedio en ms
    """
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Patrones para diferentes sistemas operativos
        # Windows: tiempo=XXms o time=XXms
        # Linux/macOS: time=XX.X ms
        patrones = [
            r'tiempo[=<](\d+\.?\d*)\s*ms',  # Windows español
            r'time[=<](\d+\.?\d*)\s*ms',    # Windows inglés / Linux / macOS
        ]
        
        latencias = []
        for patron in patrones:
            matches = re.findall(patron, contenido, re.IGNORECASE)
            if matches:
                latencias.extend([float(m) for m in matches])
        
        if not latencias:
            print("✗ No se encontraron datos de latencia en el archivo")
            return None
        
        latencia_promedio = statistics.mean(latencias)
        print(f"✓ Latencia promedio: {latencia_promedio:.2f} ms")
        print(f"  Pings analizados: {len(latencias)}")
        
        return latencia_promedio
        
    except FileNotFoundError:
        print(f"✗ Error: No se encontró el archivo {archivo}")
        return None
    except Exception as e:
        print(f"✗ Error al leer archivo: {e}")
        return None


def calcular_jitter(archivo):
    """
    Calcula el jitter (variación de latencia) desde un archivo de ping.
    
    Parámetros:
    - archivo: Ruta del archivo con resultados de ping
    
    Retorna:
    - jitter: Jitter en ms (desviación estándar de latencias)
    """
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Extraer latencias
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
            print("✗ No hay suficientes datos para calcular jitter")
            return None
        
        # Calcular jitter como desviación estándar
        jitter = statistics.stdev(latencias)
        print(f"✓ Jitter: {jitter:.2f} ms")
        print(f"  Latencia mín: {min(latencias):.2f} ms")
        print(f"  Latencia máx: {max(latencias):.2f} ms")
        
        return jitter
        
    except FileNotFoundError:
        print(f"✗ Error: No se encontró el archivo {archivo}")
        return None
    except Exception as e:
        print(f"✗ Error al calcular jitter: {e}")
        return None


def calcular_paquetes_perdidos(archivo):
    """
    Calcula el porcentaje de paquetes perdidos desde un archivo de ping.
    
    Parámetros:
    - archivo: Ruta del archivo con resultados de ping
    
    Retorna:
    - porcentaje_perdida: Porcentaje de paquetes perdidos (0-100)
    """
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Patrones para diferentes sistemas operativos
        # Windows: "Paquetes: enviados = X, recibidos = Y, perdidos = Z (W% perdidos)"
        # Linux/macOS: "X packets transmitted, Y received, Z% packet loss"
        
        # Intentar patrón Windows español
        match = re.search(r'enviados\s*=\s*(\d+).*?recibidos\s*=\s*(\d+)', contenido, re.IGNORECASE)
        if match:
            enviados = int(match.group(1))
            recibidos = int(match.group(2))
            perdidos = enviados - recibidos
            porcentaje = (perdidos / enviados) * 100 if enviados > 0 else 0
        else:
            # Intentar patrón Linux/macOS o Windows inglés
            match = re.search(r'(\d+)\s+packets?\s+transmitted.*?(\d+)\s+received.*?(\d+\.?\d*)%\s+packet\s+loss', contenido, re.IGNORECASE)
            if match:
                porcentaje = float(match.group(3))
            else:
                # Intentar extraer directamente el porcentaje
                match = re.search(r'(\d+\.?\d*)%\s+(perdidos|loss)', contenido, re.IGNORECASE)
                if match:
                    porcentaje = float(match.group(1))
                else:
                    print("✗ No se encontraron datos de pérdida de paquetes")
                    return None
        
        print(f"✓ Paquetes perdidos: {porcentaje:.2f}%")
        return porcentaje
        
    except FileNotFoundError:
        print(f"✗ Error: No se encontró el archivo {archivo}")
        return None
    except Exception as e:
        print(f"✗ Error al calcular pérdida de paquetes: {e}")
        return None


def calcular_mos(latencia_promedio, jitter, perdida_paquetes):
    """
    Calcula el MOS (Mean Opinion Score) para llamadas VoIP.
    
    Parámetros:
    - latencia_promedio: Latencia promedio en ms
    - jitter: Jitter en ms
    - perdida_paquetes: Porcentaje de pérdida de paquetes (0-100)
    
    Retorna:
    - MOS: Valor entre 1 y 5 (mayor es mejor)
    - R: Valor R-Factor
    - latencia_efectiva: Latencia efectiva calculada
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
    """Clasifica la calidad de la llamada según el valor MOS"""
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


# Ejemplo de uso completo
if __name__ == "__main__":
    print("=" * 60)
    print("ANÁLISIS COMPLETO DE CALIDAD VoIP")
    print("=" * 60)
    
    # 1. Realizar ping
    ip = "200.94.158.82"  # Google DNS - puedes cambiar esta IP
    cantidad_pings = 20
    
    archivo = hacer_ping(ip, cantidad_pings)
    
    if archivo:
        print("\n" + "-" * 60)
        
        # 2. Calcular latencia promedio
        latencia = calcular_latencia_promedio(archivo)
        
        # 3. Calcular jitter
        jitter = calcular_jitter(archivo)
        
        # 4. Calcular paquetes perdidos
        perdida = calcular_paquetes_perdidos(archivo)
        
        # Calcular MOS si tenemos todos los datos
        if latencia is not None and jitter is not None and perdida is not None:
            print("\n" + "=" * 60)
            print("CÁLCULO DE MOS")
            print("=" * 60)
            
            mos, r_factor, lat_efectiva = calcular_mos(latencia, jitter, perdida)
            
            print(f"\nParámetros:")
            print(f"  Latencia promedio: {latencia:.2f} ms")
            print(f"  Jitter: {jitter:.2f} ms")
            print(f"  Pérdida de paquetes: {perdida:.2f}%")
            print(f"\nResultados:")
            print(f"  Latencia efectiva: {lat_efectiva:.2f} ms")
            print(f"  R-Factor: {r_factor:.2f}")
            print(f"  MOS: {mos:.2f}")
            print(f"  Calidad: {clasificar_mos(mos)}")
            print("=" * 60)