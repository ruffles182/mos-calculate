from mos_functions import obtener_traceroute

resultado = obtener_traceroute("8.8.8.8")
for salto in resultado:
    hostname = salto['hostname'] if salto['hostname'] else ''
    print(f"Salto {salto['hop']}: {salto['ip']} {hostname} - {salto['latency_ms']} ms")