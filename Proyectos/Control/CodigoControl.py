#!/usr/bin/env python3
# -- coding: utf-8 --

import serial
import time
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque


# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
PUERTO      = "COM7"
BAUDRATE    = 115200
VENTANA_SEG = 10.0

ADC_MAX = 823
VOLTAJE_MAX_ADC = 7.803

TS_CONTROL = 0.001

# Zona física de trabajo
ENTRADA_PLANTA_MIN = 5.0
ENTRADA_PLANTA_MAX = 8.5

global PUNTODE_EQUILIBRIO 
PUNTODE_EQUILIBRIO = 6.75


global SALIDA_EQUILIBRIO
SALIDA_EQUILIBRIO = 0.0

# PID
KP = 2.9
KI = 25.1
KD = 0.0152

# Seguidor por realimentación de estados con integrador
KX_SEGUIDOR = 2.037
KI_SEGUIDOR = 19.67


DEBUG_SERIAL = False


tabla_voltajes = [
    0.0070, 0.0186, 0.0302, 0.0418, 0.0534, 0.0650, 0.0820, 0.0990,
    0.1160, 0.1330, 0.1500, 0.1680, 0.1860, 0.2040, 0.2220, 0.2400,
    0.2580, 0.2760, 0.2940, 0.3120, 0.3300, 0.3480, 0.3660, 0.3840,
    0.4020, 0.4200, 0.4400, 0.4600, 0.4800, 0.5000, 0.5200, 0.5400,
    0.5600, 0.5800, 0.6000, 0.6200, 0.6360, 0.6520, 0.6680, 0.6840,
    0.7000, 0.7160, 0.7320, 0.7480, 0.7640, 0.7800, 0.7940, 0.8080,
    0.8220, 0.8360, 0.8500, 0.8680, 0.8860, 0.9040, 0.9220, 0.9400,
    0.9680, 0.9960, 1.0240, 1.0520, 1.0800, 1.1040, 1.1280, 1.1520,
    1.1760, 1.2000, 1.4400, 1.6800, 1.9200, 2.1600, 2.4000, 2.5260,
    2.6520, 2.7780, 2.9040, 3.0300, 3.0880, 3.1460, 3.2040, 3.2620,
    3.3200, 3.4580, 3.5960, 3.7340, 3.8720, 4.0100, 4.0840, 4.1580,
    4.2320, 4.3060, 4.3800, 4.4560, 4.5320, 4.6080, 4.6840, 4.7600,
    4.8280, 4.8960, 4.9640, 5.0320, 5.1000, 5.1600, 5.2200, 5.2800,
    5.3400, 5.4000, 5.4600, 5.5200, 5.5800, 5.6400, 5.7000, 5.7620,
    5.8240, 5.8860, 5.9480, 6.0100, 6.0600, 6.1100, 6.1600, 6.2100,
    6.2600, 6.3000, 6.3400, 6.3800, 6.4200, 6.4600, 6.5080, 6.5560,
    6.6040, 6.6520, 6.7000, 6.7360, 6.7720, 6.8080, 6.8440, 6.8800,
    6.9020, 6.9240, 6.9460, 6.9680, 6.9900, 7.0060, 7.0220, 7.0380,
    7.0540, 7.0700, 7.0980, 7.1260, 7.1540, 7.1820, 7.2100, 7.2600,
    7.3100, 7.3600, 7.4100, 7.4600, 7.4920, 7.5240, 7.5560, 7.5880,
    7.6200, 7.6500, 7.6800, 7.7100, 7.7400, 7.7700, 7.7960, 7.8220,
    7.8480, 7.8740, 7.9000, 7.9280, 7.9560, 7.9840, 8.0120, 8.0400,
    8.0680, 8.0960, 8.1240, 8.1520, 8.1800, 8.2040, 8.2280, 8.2520,
    8.2760, 8.3000, 8.3220, 8.3440, 8.3660, 8.3880, 8.4100, 8.4340,
    8.4580, 8.4820, 8.5060, 8.5300, 8.5480, 8.5660, 8.5840, 8.6020,
    8.6200, 8.6380, 8.6560, 8.6740, 8.6920, 8.7100, 8.7280, 8.7460,
    8.7640, 8.7820, 8.8000, 8.8200, 8.8400, 8.8600, 8.8800, 8.9000,
    8.9160, 8.9320, 8.9480, 8.9640, 8.9800, 8.9970, 9.0140, 9.0310,
    9.0480, 9.0650, 9.0786, 9.0922, 9.1058, 9.1194, 9.1330, 9.1504,
    9.1678, 9.1852, 9.2026, 9.2200, 9.2370, 9.2540, 9.2710, 9.2880,
    9.3050, 9.3300, 9.3550, 9.3800, 9.4050, 9.4300, 9.4780, 9.5260,
    9.5740, 9.6220, 9.6700, 9.7190, 9.7680, 9.8170, 9.8660, 9.9150
]


# ─── ESTADO COMPARTIDO ────────────────────────────────────────────────────────
ser = serial.Serial(PUERTO, BAUDRATE, timeout=0.2)
time.sleep(2)
ser.reset_input_buffer()

lock_datos = threading.Lock()
lock_serial = threading.Lock()

tiempos = deque()
valores = deque()
referencias = deque()

tiempo_inicio = time.perf_counter()
detener = threading.Event()

estado_medicion = {"texto": "Iniciando control...", "activo": True}
eventos_tau = []

estado_control = {
    "entrada_pid": 0.0,
    "entrada_aplicada": 0.0,
    "pwm": 0,
    "adc": 0
}

#------------------ Variables internas del seguidor de referencia ----------------

# ─── VARIABLES INTERNAS DEL SEGUIDOR ──────────────────────────────────────────

seguidor_integral_error = 0.0
seguidor_t_anterior = None

# ─── VARIABLES INTERNAS DEL PID ───────────────────────────────────────────────
pid_integral = 0.0
pid_error_anterior = 0.0
pid_t_anterior = None
pid_derivada_filtrada = 0.0


# ─── FUNCIONES GENERALES ──────────────────────────────────────────────────────

def saturar(valor, minimo, maximo):
    return max(minimo, min(maximo, valor))


def adc_a_voltaje(adc):
    return float(adc) * VOLTAJE_MAX_ADC / ADC_MAX


def voltaje_a_pwm(voltaje):
    voltaje = saturar(voltaje, tabla_voltajes[0], tabla_voltajes[-1])

    mejor_pwm = 0
    menor_error = abs(tabla_voltajes[0] - voltaje)

    for pwm in range(256):
        error = abs(tabla_voltajes[pwm] - voltaje)
        

        if error < menor_error:
            menor_error = error
            mejor_pwm = pwm

    return mejor_pwm


def referencia(t):
    # PID con referencia fija de 5 V
    return 5.5

    periodo = 4.0
    valor_bajo = 5.0
    valor_alto = 7.0

    if (t % periodo) < periodo / 2:
        return valor_alto
    else:
        return valor_bajo



# ─── COMUNICACIÓN CON PLANTA ──────────────────────────────────────────────────

def enviar_pwm(pwm):
    pwm = int(saturar(pwm, 0, 255))
    ser.write(f"{pwm}\n".encode())
    ser.flush()


def leer_adc():
    linea = ser.readline().decode("utf-8", errors="ignore").strip()

    if not linea:
        return None

    if DEBUG_SERIAL:
        print(f"RX: '{linea}'")

    # Acepta "V:513" o "513"
    if linea.startswith("V:"):
        linea = linea[2:]

    try:
        return int(linea)
    except ValueError:
        return None


def aplicar_entrada_planta(entrada_planta):
    """
    Interfaz física:
    voltaje calculado -> límite físico -> PWM -> Arduino.
    """

    pwm = voltaje_a_pwm(entrada_planta)
    enviar_pwm(pwm)

    estado_control["entrada_pid"] = entrada_planta
    estado_control["entrada_aplicada"] = entrada_planta
    estado_control["pwm"] = pwm

    return pwm


def leer_salida_planta():
    adc = leer_adc()

    if adc is None:
        return None

    estado_control["adc"] = adc
    return adc_a_voltaje(adc)


# ─── CAJA NEGRA PID ───────────────────────────────────────────────────────────

def bloque_control_pid(error_control):
    global pid_integral
    global pid_error_anterior
    global pid_t_anterior
    global pid_derivada_filtrada

    t_actual = time.perf_counter()

    if pid_t_anterior is None:
        dt = TS_CONTROL
        derivada = 0.0
    else:
        dt = t_actual - pid_t_anterior
        if dt <= 0:
            dt = TS_CONTROL
        derivada = (error_control - pid_error_anterior) / dt

    # Filtro simple para la derivada
    alpha = 0.8
    pid_derivada_filtrada = (
        alpha * pid_derivada_filtrada
        + (1 - alpha) * derivada
    )

    proporcional = KP * error_control
    pid_integral += KI * error_control * dt
    derivativo = KD * pid_derivada_filtrada

    salida_pid = proporcional + pid_integral + derivativo

    salida_pid = saturar(
        salida_pid,
        ENTRADA_PLANTA_MIN,
        ENTRADA_PLANTA_MAX
    )

    pid_error_anterior = error_control
    pid_t_anterior = t_actual

    with lock_serial:
        aplicar_entrada_planta(salida_pid)
        salida_planta = leer_salida_planta()

    return salida_planta

#-------------Seguidor de referencia----------------

def bloque_control_seguidor(error_control):
    global seguidor_integral_error
    global seguidor_t_anterior

    t_actual = time.perf_counter()

    if seguidor_t_anterior is None:
        dt = TS_CONTROL
    else:
        dt = t_actual - seguidor_t_anterior
        if dt <= 0:
            dt = TS_CONTROL

    seguidor_t_anterior = t_actual

    # xi = integral(r - y)
    seguidor_integral_error += error_control * dt

    # u_dev = kx(r-y) + kI*xi
    u_dev = (
        KX_SEGUIDOR * error_control
        + KI_SEGUIDOR * seguidor_integral_error
    )

    entrada_motor = PUNTODE_EQUILIBRIO + u_dev

    entrada_motor_saturada = saturar(
        entrada_motor,
        ENTRADA_PLANTA_MIN,
        ENTRADA_PLANTA_MAX
    )

    # Anti-windup simple: si saturó, deshace la integración de este ciclo
    if entrada_motor != entrada_motor_saturada:
        seguidor_integral_error -= error_control * dt
        entrada_motor = entrada_motor_saturada
    else:
        entrada_motor = entrada_motor_saturada

    with lock_serial:
        aplicar_entrada_planta(entrada_motor)
        salida_motor_medida = leer_salida_planta()

    return salida_motor_medida

# ─── HILO DE CONTROL ──────────────────────────────────────────────────────────
MODO_CONTROL = "PID"      # Elegir: "PID" o "SEGUIDOR"


def hilo_control():
    global seguidor_integral_error
    global seguidor_t_anterior

    global pid_integral
    global pid_error_anterior
    global pid_t_anterior
    global pid_derivada_filtrada

    with lock_serial:
        aplicar_entrada_planta(0.0)
        time.sleep(2.0)
        salida_inicial = leer_salida_planta()

    if salida_inicial is None:
        salida_inicial = 0.0

    if MODO_CONTROL == "PID":

        salida_control = salida_inicial

        pid_integral = 0.0
        pid_error_anterior = 0.0
        pid_t_anterior = None
        pid_derivada_filtrada = 0.0

    elif MODO_CONTROL == "SEGUIDOR":

        seguidor_integral_error = 0.0

        seguidor_t_anterior = None
        salida_control = salida_inicial

    else:
        raise ValueError("MODO_CONTROL debe ser 'PID' o 'SEGUIDOR'")

    while not detener.is_set():

        t_ciclo = time.perf_counter()
        t = t_ciclo - tiempo_inicio

        referencia_actual = referencia(t)

        if MODO_CONTROL == "PID":
            error_control = referencia_actual - salida_control
            salida_nueva = bloque_control_pid(error_control)

        else:
            error_control = referencia_actual - salida_control
            salida_nueva = bloque_control_seguidor(error_control)

        if salida_nueva is not None:
            salida_control = salida_nueva

            with lock_datos:
                tiempos.append(t)

                if MODO_CONTROL == "PID":
                    valores.append(salida_control)
                    salida_para_texto = salida_control
                else:
                    valores.append(salida_control)
                    salida_para_texto = salida_control

                referencias.append(referencia_actual)

                estado_medicion["texto"] = (
                    f"Modo={MODO_CONTROL} | "
                    f"Ref={referencia_actual:.2f} V | "
                    f"Salida={salida_para_texto:.2f} V | "
                    f"Error={error_control:.2f} | "
                    f"Entrada={estado_control['entrada_pid']:.2f} V | "
                    f"PWM={estado_control['pwm']}"
                )

        restante = TS_CONTROL - (time.perf_counter() - t_ciclo)

        if restante > 0:
            time.sleep(restante)

# ─── OSCILOSCOPIO ─────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(20, 5))
linea_señal, = ax.plot([], [], color="lime", linewidth=0.8, zorder=3)
linea_referencia, = ax.plot([], [], color="red", linewidth=1.0, linestyle="--", zorder=2)

ax.set_facecolor("#0a0a0a")
fig.patch.set_facecolor("#0a0a0a")
ax.set_ylim(-0.1, 10.1)
ax.set_ylabel("Voltaje (V)", color="white")
ax.set_xlabel("Tiempo (segundos)", color="white")
ax.set_title("Osciloscopio + Control — Motor DC", color="white")
ax.tick_params(colors="white")
ax.grid(True, color="#222222")

for sp in ax.spines.values():
    sp.set_edgecolor("#333333")

txt_info = ax.text(
    0.01, 0.97, "",
    transform=ax.transAxes,
    color="yellow",
    fontsize=8,
    va="top",
    family="monospace"
)

txt_estado = ax.text(
    0.01, 0.88, "",
    transform=ax.transAxes,
    color="cyan",
    fontsize=8,
    va="top",
    family="monospace"
)

linea_arranque = ax.axvline(
    x=0,
    color="#ff6600",
    linewidth=1.2,
    linestyle="--",
    alpha=0,
    zorder=4
)

linea_umbral_t = ax.axvline(
    x=0,
    color="#00cfff",
    linewidth=1.2,
    linestyle="--",
    alpha=0,
    zorder=4
)

linea_umbral_v = ax.axhline(
    y=0,
    color="#00cfff",
    linewidth=0.8,
    linestyle=":",
    alpha=0,
    zorder=4
)

txt_tau = ax.text(
    0,
    0,
    "",
    color="#00cfff",
    fontsize=8,
    family="monospace",
    zorder=5
)

_fs_actual = [0.0]


def actualizar(frame):
    with lock_datos:
        if not tiempos:
            return linea_señal, txt_info, txt_estado, \
                   linea_arranque, linea_umbral_t, linea_umbral_v, txt_tau

        t_arr = list(tiempos)
        v_arr = list(valores)
        r_arr = list(referencias)
        evs = list(eventos_tau)

    t_fin = t_arr[-1]
    t_ini = max(0.0, t_fin - VENTANA_SEG)

    pares = [
    (t, v, r)
    for t, v, r in zip(t_arr, v_arr, r_arr)
    if t >= t_ini
]

    if len(pares) < 2:
        return linea_señal, txt_info, txt_estado, \
               linea_arranque, linea_umbral_t, linea_umbral_v, txt_tau

    ts, vs, rs = zip(*pares)

    duracion = ts[-1] - ts[0]

    if duracion > 0:
        _fs_actual[0] = (len(ts) - 1) / duracion

    N_SMOOTH = max(1, int(_fs_actual[0] * 0.05))

    vs_lista = list(vs)
    vs_suave = []

    for i in range(len(vs_lista)):
        inicio = max(0, i - N_SMOOTH + 1)
        vs_suave.append(sum(vs_lista[inicio:i+1]) / (i - inicio + 1))

    umbral_flancos = (max(vs_suave) + min(vs_suave)) / 2

    flancos = [
        i for i in range(1, len(vs_suave))
        if vs_suave[i - 1] < umbral_flancos <= vs_suave[i]
    ]

    if len(flancos) >= 2:
        periodos = [
            ts[flancos[k + 1]] - ts[flancos[k]]
            for k in range(len(flancos) - 1)
        ]

        periodo_medio = sum(periodos) / len(periodos)
        freq_señal = 1.0 / periodo_medio if periodo_medio > 0 else 0
    else:
        freq_señal = 0

    limite_borrado = t_ini - VENTANA_SEG * 2

    with lock_datos:
        while tiempos and tiempos[0] < limite_borrado:
            tiempos.popleft()
            valores.popleft()

    linea_señal.set_data(ts, vs_suave)
    linea_referencia.set_data(ts, rs)
    ax.set_xlim(t_ini, t_fin)

    txt_info.set_text(
        f"fs ≈ {_fs_actual[0]:.0f} Hz   |   "
        f"f_señal ≈ {freq_señal:.1f} Hz   |   "
        f"puntos: {len(ts)}"
    )

    txt_estado.set_text(f"Estado: {estado_medicion['texto']}")

    ev_visible = [e for e in evs if e["t_umbral"] >= t_ini]

    if ev_visible:
        ev = ev_visible[-1]
        ta = ev["t_arranque"]
        tu = ev["t_umbral"]

        linea_arranque.set_xdata([ta, ta])
        linea_arranque.set_alpha(0.8)

        linea_umbral_t.set_xdata([tu, tu])
        linea_umbral_t.set_alpha(0.8)

        linea_umbral_v.set_ydata([ev["umbral"], ev["umbral"]])
        linea_umbral_v.set_alpha(0.6)

        txt_tau.set_position((tu + 0.02, ev["umbral"] + 0.1))
        txt_tau.set_text(
            f"τ={ev['tau']:.3f}s\n"
            f"V={ev['voltaje']}V\n"
            f"obj={ev['objetivo']:.2f}"
        )
    else:
        linea_arranque.set_alpha(0)
        linea_umbral_t.set_alpha(0)
        linea_umbral_v.set_alpha(0)
        txt_tau.set_text("")

    return linea_señal, linea_referencia, txt_info, txt_estado, \
       linea_arranque, linea_umbral_t, linea_umbral_v, txt_tau


# ─── ARRANQUE ─────────────────────────────────────────────────────────────────

hilo = threading.Thread(target=hilo_control, daemon=True)
hilo.start()

try:
    ani = animation.FuncAnimation(fig, actualizar, interval=30, blit=True)
    plt.tight_layout()
    plt.show()

finally:
    detener.set()
    time.sleep(0.2)

    try:
        with lock_serial:
            enviar_pwm(0)
    except Exception:
        pass

    ser.close()
    print("Puerto cerrado.")

