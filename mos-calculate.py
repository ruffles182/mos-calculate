import subprocess
import re
import statistics
from datetime import datetime
import platform
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading


class MOSCalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora MOS - VoIP Quality Analyzer")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Variables
        self.archivo_ping = None
        self.latencia = None
        self.jitter = None
        self.perdida = None
        
        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        self.crear_interfaz()
    
    def crear_interfaz(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Título
        titulo = ttk.Label(main_frame, text="Analizador de Calidad VoIP", 
                          font=('Arial', 16, 'bold'))
        titulo.grid(row=0, column=0, columnspan=3, pady=10)
        
        # --- Sección 1: Parámetros de Ping ---
        frame_ping = ttk.LabelFrame(main_frame, text="1. Configuración de Ping", padding="10")
        frame_ping.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(frame_ping, text="IP/Host:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.entry_ip = ttk.Entry(frame_ping, width=30)
        self.entry_ip.insert(0, "8.8.8.8")
        self.entry_ip.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(frame_ping, text="Cantidad:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.entry_cantidad = ttk.Entry(frame_ping, width=10)
        self.entry_cantidad.insert(0, "20")
        self.entry_cantidad.grid(row=0, column=3, sticky=tk.W, pady=5, padx=5)
        
        self.btn_ping = ttk.Button(frame_ping, text="🌐 Realizar Ping", 
                                    command=self.ejecutar_ping)
        self.btn_ping.grid(row=0, column=4, pady=5, padx=10)
        
        # --- Sección 2: Resultados del Análisis ---
        frame_resultados = ttk.LabelFrame(main_frame, text="2. Resultados del Análisis", padding="10")
        frame_resultados.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        frame_resultados.columnconfigure(1, weight=1)
        
        # Botones de análisis
        self.btn_latencia = ttk.Button(frame_resultados, text="📊 Calcular Latencia", 
                                       command=self.calcular_latencia_promedio, state='disabled')
        self.btn_latencia.grid(row=0, column=0, pady=5, padx=5, sticky=tk.W)
        
        self.lbl_latencia = ttk.Label(frame_resultados, text="Latencia: -- ms", 
                                      font=('Arial', 10))
        self.lbl_latencia.grid(row=0, column=1, pady=5, padx=10, sticky=tk.W)
        
        self.btn_jitter = ttk.Button(frame_resultados, text="📈 Calcular Jitter", 
                                     command=self.calcular_jitter, state='disabled')
        self.btn_jitter.grid(row=1, column=0, pady=5, padx=5, sticky=tk.W)
        
        self.lbl_jitter = ttk.Label(frame_resultados, text="Jitter: -- ms", 
                                    font=('Arial', 10))
        self.lbl_jitter.grid(row=1, column=1, pady=5, padx=10, sticky=tk.W)
        
        self.btn_perdida = ttk.Button(frame_resultados, text="📉 Calcular Pérdida", 
                                      command=self.calcular_paquetes_perdidos, state='disabled')
        self.btn_perdida.grid(row=2, column=0, pady=5, padx=5, sticky=tk.W)
        
        self.lbl_perdida = ttk.Label(frame_resultados, text="Pérdida: -- %", 
                                     font=('Arial', 10))
        self.lbl_perdida.grid(row=2, column=1, pady=5, padx=10, sticky=tk.W)
        
        # Botón calcular todo
        self.btn_analizar_todo = ttk.Button(frame_resultados, text="⚡ Analizar Todo", 
                                            command=self.analizar_todo, state='disabled')
        self.btn_analizar_todo.grid(row=3, column=0, columnspan=2, pady=10)
        
        # --- Sección 3: Cálculo MOS ---
        frame_mos = ttk.LabelFrame(main_frame, text="3. Cálculo MOS", padding="10")
        frame_mos.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.btn_calcular_mos = ttk.Button(frame_mos, text="🎯 Calcular MOS", 
                                           command=self.calcular_mos_gui, state='disabled')
        self.btn_calcular_mos.grid(row=0, column=0, pady=10, padx=5)
        
        # Frame para resultados MOS
        self.frame_mos_resultado = ttk.Frame(frame_mos)
        self.frame_mos_resultado.grid(row=0, column=1, pady=10, padx=20, sticky=(tk.W, tk.E))
        
        self.lbl_mos = ttk.Label(self.frame_mos_resultado, text="MOS: --", 
                                font=('Arial', 14, 'bold'))
        self.lbl_mos.grid(row=0, column=0, sticky=tk.W)
        
        self.lbl_calidad = ttk.Label(self.frame_mos_resultado, text="", 
                                    font=('Arial', 12))
        self.lbl_calidad.grid(row=1, column=0, sticky=tk.W)
        
        self.lbl_r_factor = ttk.Label(self.frame_mos_resultado, text="", 
                                     font=('Arial', 9))
        self.lbl_r_factor.grid(row=2, column=0, sticky=tk.W)
        
        # --- Sección 4: Consola de Logs ---
        frame_log = ttk.LabelFrame(main_frame, text="Registro de Actividad", padding="10")
        frame_log.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(4, weight=1)
        
        self.text_log = scrolledtext.ScrolledText(frame_log, height=12, width=80, 
                                                  state='disabled', wrap=tk.WORD)
        self.text_log.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        frame_log.columnconfigure(0, weight=1)
        frame_log.rowconfigure(0, weight=1)
        
        # Botón limpiar log
        ttk.Button(frame_log, text="🗑️ Limpiar Log", 
                  command=self.limpiar_log).grid(row=1, column=0, pady=5)
        
        # Barra de estado
        self.status_bar = ttk.Label(main_frame, text="Listo", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
    
    def log(self, mensaje):
        """Agregar mensaje al log"""
        self.text_log.config(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.text_log.insert(tk.END, f"[{timestamp}] {mensaje}\n")
        self.text_log.see(tk.END)
        self.text_log.config(state='disabled')
    
    def limpiar_log(self):
        """Limpiar el log"""
        self.text_log.config(state='normal')
        self.text_log.delete(1.0, tk.END)
        self.text_log.config(state='disabled')
    
    def actualizar_estado(self, mensaje):
        """Actualizar barra de estado"""
        self.status_bar.config(text=mensaje)
    
    def ejecutar_ping(self):
        """Ejecutar ping en un hilo separado"""
        ip = self.entry_ip.get().strip()
        
        if not ip:
            messagebox.showwarning("Advertencia", "Por favor ingrese una IP o host")
            return
        
        try:
            cantidad = int(self.entry_cantidad.get())
            if cantidad < 1 or cantidad > 100:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Advertencia", "La cantidad debe ser un número entre 1 y 100")
            return
        
        # Deshabilitar botón durante ejecución
        self.btn_ping.config(state='disabled')
        self.actualizar_estado(f"Ejecutando ping a {ip}...")
        
        # Ejecutar en hilo separado
        thread = threading.Thread(target=self._hacer_ping_thread, args=(ip, cantidad))
        thread.daemon = True
        thread.start()
    
    def _hacer_ping_thread(self, ip, cantidad):
        """Thread para ejecutar ping"""
        resultado = self.hacer_ping(ip, cantidad)
        
        # Actualizar UI en el hilo principal
        self.root.after(0, self._ping_completado, resultado)
    
    def _ping_completado(self, archivo):
        """Callback cuando el ping se completa"""
        self.btn_ping.config(state='normal')
        
        if archivo:
            self.archivo_ping = archivo
            self.log(f"✓ Ping completado. Archivo: {archivo}")
            self.actualizar_estado("Ping completado")
            
            # Habilitar botones de análisis
            self.btn_latencia.config(state='normal')
            self.btn_jitter.config(state='normal')
            self.btn_perdida.config(state='normal')
            self.btn_analizar_todo.config(state='normal')
        else:
            self.log("✗ Error al ejecutar ping")
            self.actualizar_estado("Error en ping")
            messagebox.showerror("Error", "No se pudo completar el ping")
    
    def hacer_ping(self, ip, cantidad):
        """Realizar ping y guardar en archivo"""
        fecha_hora = datetime.now().strftime("%Y%m%d-%H%M%S")
        nombre_archivo = f"ping-{ip}-{fecha_hora}.txt"
        
        sistema = platform.system().lower()
        
        try:
            if sistema == "windows":
                comando = ["ping", "-n", str(cantidad), ip]
            else:
                comando = ["ping", "-c", str(cantidad), ip]
            
            self.log(f"Realizando {cantidad} pings a {ip}...")
            
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
            
        except Exception as e:
            self.log(f"✗ Error: {e}")
            return None
    
    def calcular_latencia_promedio(self):
        """Calcular latencia promedio del archivo"""
        if not self.archivo_ping:
            messagebox.showwarning("Advertencia", "Primero debe realizar un ping")
            return
        
        try:
            with open(self.archivo_ping, 'r', encoding='utf-8') as f:
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
                self.log("✗ No se encontraron datos de latencia")
                messagebox.showerror("Error", "No se encontraron datos de latencia en el archivo")
                return
            
            self.latencia = statistics.mean(latencias)
            self.lbl_latencia.config(text=f"Latencia: {self.latencia:.2f} ms")
            self.log(f"✓ Latencia promedio: {self.latencia:.2f} ms ({len(latencias)} muestras)")
            
            self._verificar_datos_completos()
            
        except Exception as e:
            self.log(f"✗ Error al calcular latencia: {e}")
            messagebox.showerror("Error", f"Error al calcular latencia: {e}")
    
    def calcular_jitter(self):
        """Calcular jitter del archivo"""
        if not self.archivo_ping:
            messagebox.showwarning("Advertencia", "Primero debe realizar un ping")
            return
        
        try:
            with open(self.archivo_ping, 'r', encoding='utf-8') as f:
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
                self.log("✗ No hay suficientes datos para calcular jitter")
                messagebox.showerror("Error", "No hay suficientes datos para calcular jitter")
                return
            
            self.jitter = statistics.stdev(latencias)
            self.lbl_jitter.config(text=f"Jitter: {self.jitter:.2f} ms")
            self.log(f"✓ Jitter: {self.jitter:.2f} ms (min: {min(latencias):.2f}, max: {max(latencias):.2f})")
            
            self._verificar_datos_completos()
            
        except Exception as e:
            self.log(f"✗ Error al calcular jitter: {e}")
            messagebox.showerror("Error", f"Error al calcular jitter: {e}")
    
    def calcular_paquetes_perdidos(self):
        """Calcular paquetes perdidos del archivo"""
        if not self.archivo_ping:
            messagebox.showwarning("Advertencia", "Primero debe realizar un ping")
            return
        
        try:
            with open(self.archivo_ping, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            match = re.search(r'enviados\s*=\s*(\d+).*?recibidos\s*=\s*(\d+)', contenido, re.IGNORECASE)
            if match:
                enviados = int(match.group(1))
                recibidos = int(match.group(2))
                perdidos = enviados - recibidos
                porcentaje = (perdidos / enviados) * 100 if enviados > 0 else 0
            else:
                match = re.search(r'(\d+)\s+packets?\s+transmitted.*?(\d+)\s+received.*?(\d+\.?\d*)%\s+packet\s+loss', contenido, re.IGNORECASE)
                if match:
                    porcentaje = float(match.group(3))
                else:
                    match = re.search(r'(\d+\.?\d*)%\s+(perdidos|loss)', contenido, re.IGNORECASE)
                    if match:
                        porcentaje = float(match.group(1))
                    else:
                        self.log("✗ No se encontraron datos de pérdida de paquetes")
                        messagebox.showerror("Error", "No se encontraron datos de pérdida de paquetes")
                        return
            
            self.perdida = porcentaje
            self.lbl_perdida.config(text=f"Pérdida: {self.perdida:.2f} %")
            self.log(f"✓ Paquetes perdidos: {self.perdida:.2f}%")
            
            self._verificar_datos_completos()
            
        except Exception as e:
            self.log(f"✗ Error al calcular pérdida: {e}")
            messagebox.showerror("Error", f"Error al calcular pérdida: {e}")
    
    def analizar_todo(self):
        """Ejecutar todos los análisis"""
        self.log("--- Iniciando análisis completo ---")
        self.calcular_latencia_promedio()
        self.calcular_jitter()
        self.calcular_paquetes_perdidos()
        self.log("--- Análisis completo finalizado ---")
    
    def _verificar_datos_completos(self):
        """Verificar si tenemos todos los datos para calcular MOS"""
        if self.latencia is not None and self.jitter is not None and self.perdida is not None:
            self.btn_calcular_mos.config(state='normal')
    
    def calcular_mos_gui(self):
        """Calcular MOS con los datos obtenidos"""
        if self.latencia is None or self.jitter is None or self.perdida is None:
            messagebox.showwarning("Advertencia", "Debe completar todos los análisis primero")
            return
        
        latencia_efectiva = self.latencia + (self.jitter * 2) + 10
        
        if latencia_efectiva < 160:
            R = 93.2 - (latencia_efectiva / 40)
        else:
            R = 93.2 - ((latencia_efectiva - 120) / 10)
        
        R = R - (self.perdida * 2.5)
        
        MOS = 1 + (0.035 * R) + (0.000007 * R * (R - 60) * (100 - R))
        
        # Clasificar calidad
        if MOS >= 4.3:
            calidad = "Excelente"
            color = "green"
        elif MOS >= 4.0:
            calidad = "Buena"
            color = "blue"
        elif MOS >= 3.6:
            calidad = "Aceptable"
            color = "orange"
        elif MOS >= 3.1:
            calidad = "Pobre"
            color = "dark orange"
        else:
            calidad = "Mala"
            color = "red"
        
        # Actualizar labels
        self.lbl_mos.config(text=f"MOS: {MOS:.2f}", foreground=color)
        self.lbl_calidad.config(text=f"Calidad: {calidad}", foreground=color)
        self.lbl_r_factor.config(text=f"R-Factor: {R:.2f} | Latencia Efectiva: {latencia_efectiva:.2f} ms")
        
        # Log detallado
        self.log("=" * 50)
        self.log("RESULTADO MOS:")
        self.log(f"  Latencia efectiva: {latencia_efectiva:.2f} ms")
        self.log(f"  R-Factor: {R:.2f}")
        self.log(f"  MOS: {MOS:.2f}")
        self.log(f"  Calidad: {calidad}")
        self.log("=" * 50)
        
        self.actualizar_estado(f"MOS calculado: {MOS:.2f} ({calidad})")


if __name__ == "__main__":
    root = tk.Tk()
    app = MOSCalculatorGUI(root)
    root.mainloop()