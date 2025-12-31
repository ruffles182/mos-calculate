"""
main.py
Sistema de Monitoreo MOS para VoIP
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
from mos_functions import analizar_ip, clasificar_mos


class MonitorMOS:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor MOS - VoIP")
        self.root.resizable(True, True)
        
        self.config = None
        self.resultados = []
        
        # Cargar configuración
        if not self.cargar_configuracion():
            messagebox.showerror("Error", "No se pudo cargar config.json")
            root.destroy()
            return
        
        self.crear_pantalla_inicial()
    
    def cargar_configuracion(self):
        """Cargar configuración desde config.json"""
        try:
            with open('config.json', 'r', encoding='utf-8-sig') as f:
                contenido = f.read().strip()
                if not contenido:
                    raise ValueError("Archivo vacío")
                self.config = json.loads(contenido)
            return True
        except FileNotFoundError:
            # Crear archivo de ejemplo si no existe
            config_ejemplo = {
                "cantidad_pings": 20,
                "ips": [
                    {"ip": "8.8.8.8", "nombre": "Google DNS"},
                    {"ip": "1.1.1.1", "nombre": "Cloudflare DNS"}
                ]
            }
            try:
                with open('config.json', 'w', encoding='utf-8') as f:
                    json.dump(config_ejemplo, f, indent=4)
                messagebox.showinfo("Información", 
                    "Se ha creado config.json con valores de ejemplo.\n" +
                    "Puede modificarlo y reiniciar la aplicación.")
                self.config = config_ejemplo
                return True
            except:
                return False
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer config.json: {e}")
            return False
    
    def crear_pantalla_inicial(self):
        """Crear pantalla inicial con botón de inicio"""
        # Limpiar ventana
        for widget in self.root.winfo_children():
            widget.destroy()

        # Ajustar tamaño de ventana inicial
        self.root.geometry("")  # Resetear geometría

        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Forzar actualización para calcular tamaño necesario
        self.root.update_idletasks()

        # Establecer tamaño mínimo razonable
        self.root.minsize(500, 400)
        
        # Título
        ttk.Label(main_frame, text="Monitor MOS - VoIP", 
                 font=('Arial', 18, 'bold')).pack(pady=20)
        
        # Información de configuración
        info_frame = ttk.LabelFrame(main_frame, text="Configuración Actual", padding="15")
        info_frame.pack(pady=20, fill=tk.X)
        
        ttk.Label(info_frame, text=f"Cantidad de pings: {self.config['cantidad_pings']}", 
                 font=('Arial', 10)).pack(anchor=tk.W, pady=5)
        
        ttk.Label(info_frame, text=f"IPs a monitorear: {len(self.config['ips'])}", 
                 font=('Arial', 10)).pack(anchor=tk.W, pady=5)
        
        # Lista de IPs
        ips_text = "\n".join([f"  • {item['nombre']} ({item['ip']})" 
                              for item in self.config['ips']])
        ttk.Label(info_frame, text=ips_text, 
                 font=('Arial', 9), foreground='gray').pack(anchor=tk.W, pady=5)
        
        # Botón de inicio (más grande y visible)
        btn_iniciar = tk.Button(main_frame, 
                               text="▶ Iniciar Monitoreo", 
                               command=self.iniciar_monitoreo,
                               font=('Arial', 14, 'bold'),
                               bg='#4CAF50',
                               fg='white',
                               padx=30,
                               pady=15,
                               cursor='hand2')
        btn_iniciar.pack(pady=30)
    
    def crear_pantalla_cargando(self):
        """Crear pantalla de carga"""
        # Limpiar ventana
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        # Mensaje de carga
        ttk.Label(main_frame, text="Cargando: Espere un momento...", 
                 font=('Arial', 14)).pack(pady=30)
        
        # Barra de progreso
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=300)
        self.progress.pack(pady=20)
        self.progress.start(10)
        
        # Label de estado
        self.lbl_estado = ttk.Label(main_frame, text="Iniciando análisis...", 
                                    font=('Arial', 10), foreground='gray')
        self.lbl_estado.pack(pady=10)
    
    def iniciar_monitoreo(self):
        """Iniciar el proceso de monitoreo"""
        self.crear_pantalla_cargando()
        
        # Ejecutar análisis en thread separado
        thread = threading.Thread(target=self.ejecutar_analisis)
        thread.daemon = True
        thread.start()
    
    def ejecutar_analisis(self):
        """Ejecutar análisis de todas las IPs"""
        self.resultados = []
        total = len(self.config['ips'])
        
        for i, item in enumerate(self.config['ips'], 1):
            ip = item['ip']
            nombre = item['nombre']
            
            # Actualizar estado
            self.root.after(0, self.actualizar_estado, 
                          f"Analizando {nombre} ({ip})... [{i}/{total}]")
            
            # Realizar análisis
            resultado = analizar_ip(ip, self.config['cantidad_pings'])
            
            if resultado and not resultado.get('error'):
                resultado['nombre'] = nombre
                self.resultados.append(resultado)
            else:
                mensaje_error = resultado.get('mensaje', 'Error desconocido') if resultado else 'Sin respuesta'
                self.resultados.append({
                    'ip': ip,
                    'nombre': nombre,
                    'error': True,
                    'mensaje': mensaje_error
                })
        
        # Mostrar resultados
        self.root.after(0, self.mostrar_resultados)
    
    def actualizar_estado(self, texto):
        """Actualizar texto de estado"""
        self.lbl_estado.config(text=texto)
    
    def mostrar_resultados(self):
        """Mostrar pantalla de resultados"""
        # Limpiar ventana
        for widget in self.root.winfo_children():
            widget.destroy()

        # Calcular ancho necesario basado en número de tarjetas
        num_tarjetas = len(self.resultados)
        # Ancho por tarjeta (300) + padding (20) + margen extra
        ancho_ventana = min(num_tarjetas * 320 + 60, 1600)
        ancho_ventana = max(ancho_ventana, 600)  # Mínimo 600px
        alto_ventana = 550

        self.root.geometry(f"{ancho_ventana}x{alto_ventana}")
        
        # Frame principal con scroll horizontal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text="Resultados del Monitoreo", 
                 font=('Arial', 16, 'bold')).pack(pady=15)
        
        # Frame para canvas con scroll horizontal
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # Canvas y scrollbar horizontal
        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
        scrollable_frame = ttk.Frame(canvas)
        
        def actualizar_scroll(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Centrar el contenido si es más pequeño que el canvas
            canvas_width = canvas.winfo_width()
            frame_width = scrollable_frame.winfo_reqwidth()
            if frame_width < canvas_width:
                x_pos = (canvas_width - frame_width) // 2
                canvas.coords(canvas_window, x_pos, 0)
            else:
                canvas.coords(canvas_window, 0, 0)

        scrollable_frame.bind("<Configure>", actualizar_scroll)

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(xscrollcommand=scrollbar.set)

        # También actualizar al redimensionar el canvas
        canvas.bind("<Configure>", actualizar_scroll)

        # Frame para las tarjetas en horizontal
        tarjetas_frame = ttk.Frame(scrollable_frame)
        tarjetas_frame.pack(padx=10, pady=10)
        
        # Mostrar cada resultado horizontalmente
        for i, resultado in enumerate(self.resultados):
            self.crear_tarjeta_resultado(tarjetas_frame, resultado, i)
        
        # Empaquetar canvas y scrollbar
        canvas.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="bottom", fill="x")
        
        # Botón volver
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)
        
        ttk.Button(btn_frame, text="⟲ Volver a Inicio", 
                  command=self.crear_pantalla_inicial).pack()
    
    def crear_tarjeta_resultado(self, parent, resultado, columna):
        """Crear tarjeta con resultado de una IP"""
        # Frame para la tarjeta (columna)
        card = ttk.LabelFrame(parent, text=f"{resultado['nombre']}\n({resultado['ip']})", 
                             padding="15", width=280)
        card.grid(row=0, column=columna, padx=10, pady=10, sticky=(tk.N, tk.S))
        card.grid_propagate(False)  # Mantener tamaño fijo
        
        if resultado.get('error'):
            error_msg = resultado.get('mensaje', 'Error desconocido')
            ttk.Label(card, text=f"❌ {error_msg}", 
                     font=('Arial', 9), foreground='red', wraplength=250).pack(pady=20)
            return
        
        # Métricas básicas
        metricas_frame = ttk.Frame(card)
        metricas_frame.pack(fill=tk.X, pady=5)
        
        self.agregar_metrica(metricas_frame, "Latencia:", f"{resultado['latencia']:.2f} ms")
        self.agregar_metrica(metricas_frame, "Jitter:", f"{resultado['jitter']:.2f} ms")
        self.agregar_metrica(metricas_frame, "Pérdida:", f"{resultado['perdida']:.2f}%")
        
        # Separador
        ttk.Separator(card, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Frame de resultados MOS
        mos_frame = ttk.Frame(card)
        mos_frame.pack(fill=tk.X, pady=5)
        
        # Determinar color según calidad
        mos = resultado['mos']
        if mos >= 4.3:
            color = "green"
        elif mos >= 4.0:
            color = "blue"
        elif mos >= 3.6:
            color = "orange"
        elif mos >= 3.1:
            color = "dark orange"
        else:
            color = "red"
        
        # MOS y Calidad
        ttk.Label(mos_frame, text=f"MOS: {resultado['mos']:.2f}", 
                 font=('Arial', 14, 'bold'), foreground=color).pack()
        
        ttk.Label(mos_frame, text=f"Calidad: {resultado['calidad']}", 
                 font=('Arial', 11), foreground=color).pack()
        
        ttk.Label(mos_frame, text=f"Lat. Efectiva:\n{resultado['latencia_efectiva']:.2f} ms", 
                 font=('Arial', 9), foreground='gray').pack(pady=5)
    
    def agregar_metrica(self, parent, label, valor):
        """Agregar una métrica al frame"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame, text=label, font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Label(frame, text=valor, font=('Arial', 10)).pack(side=tk.LEFT, padx=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = MonitorMOS(root)
    root.mainloop()