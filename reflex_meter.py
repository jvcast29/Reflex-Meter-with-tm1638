from machine import Pin
import time
import random
from TM1638 import TM1638

# Configuración de Hardware
stb_pin = 4    
clk_pin = 16   
dio_pin = 17   

tm1638 = TM1638(stb_pin, clk_pin, dio_pin)
tm1638.init()

# Variables Globales de Estado
estado_juego = "INICIO"
numero_cuenta = 3
tiempo_paso_cuenta = 0
tiempo_inicio_espera = 0
tiempo_aleatorio_objetivo = 0
tiempo_senal_go = 0
tiempo_jugador = 0
tiempo_ultimo_rebote = 0
tecla_anterior = 0
tiempo_llegada_fin = 0

print("Sistema de control HMI iniciado.")

while True:
    tiempo_actual = time.ticks_ms()
    keys_crudas = tm1638.readKeys()
    evento_tecla = 0 
    
    # Capa de Abstracción de Hardware (Filtro Antirebote)
    if keys_crudas != 0 and tecla_anterior == 0:
        if time.ticks_diff(tiempo_actual, tiempo_ultimo_rebote) > 150:
            evento_tecla = keys_crudas 
            tiempo_ultimo_rebote = tiempo_actual 
            
    tecla_anterior = keys_crudas

    # ---------------------------------------------------------
    # MÁQUINA DE ESTADOS FINITOS (FSM)
    # ---------------------------------------------------------
    if estado_juego == "INICIO":
        tm1638.clearDisplay()
        tm1638.setBrightness(7)
        tiempo_jugador = 0
        numero_cuenta = 3
        tm1638.displayDigit(7, numero_cuenta)
        tiempo_paso_cuenta = time.ticks_ms()
        estado_juego = "CUENTA_REGRESIVA"
        
    elif estado_juego == "CUENTA_REGRESIVA":
        # Evaluamos si ya pasó exactamente 1 segundo (1000 ms)
        if time.ticks_diff(tiempo_actual, tiempo_paso_cuenta) > 1000:
            numero_cuenta -= 1 # Restamos 1 al contador
            tiempo_paso_cuenta = time.ticks_ms() # Reiniciamos el reloj para el siguiente número
            
            if numero_cuenta > 0:
                # Muestra el '2' y luego el '1' en cada ciclo respectivo
                tm1638.displayDigit(7, numero_cuenta)
            else:
                # La cuenta llegó a cero, preparamos la señal aleatoria
                tm1638.clearDisplay()
                tiempo_aleatorio_objetivo = random.randint(2000, 5000)
                tiempo_inicio_espera = time.ticks_ms()
                estado_juego = "ESPERA_ALEATORIA"

    elif estado_juego == "ESPERA_ALEATORIA":
        # 1. Detección de trampa (Anticipación)
        if evento_tecla != 0:
            tm1638.clearDisplay()
            tm1638.sendData(0 << 1, 0x71) # 'F'
            tm1638.sendData(1 << 1, 0x77) # 'A'
            tm1638.sendData(2 << 1, 0x06) # 'I'
            tm1638.sendData(3 << 1, 0x38) # 'L'
            
            tiempo_llegada_fin = time.ticks_ms()
            estado_juego = "FIN"
            
        # 2. Transición por cumplimiento de tiempo
        elif time.ticks_diff(tiempo_actual, tiempo_inicio_espera) > tiempo_aleatorio_objetivo:
            tm1638.clearDisplay()
            for i in range(8):
                tm1638.displayLed(i, True)
                
            tiempo_senal_go = time.ticks_ms()
            estado_juego = "MEDICION"
            
    elif estado_juego == "MEDICION":
        # Cronómetro en tiempo real
        tiempo_en_vivo = time.ticks_diff(tiempo_actual, tiempo_senal_go)   
        tm1638.displayNumber(tiempo_en_vivo)

        
        # Captura de reacción del operador
        if evento_tecla != 0:
            tiempo_jugador = tiempo_en_vivo 
            tiempo_llegada_fin = time.ticks_ms() 
            estado_juego = "FIN"
        
    elif estado_juego == "FIN":
        # Protegemos el mensaje 'FAIL' de ser sobrescrito por un '0'
        if tiempo_jugador != 0:
            tm1638.clearLeds()
            tm1638.displayNumber(tiempo_jugador)
            #tm1638.sendData(0 << 1, 0x3D) # 'G'
            #tm1638.sendData(1 << 1, 0x3F) # 'O'
        # Enclavamiento visual y reinicio del sistema
        if evento_tecla != 0 and time.ticks_diff(tiempo_actual, tiempo_llegada_fin) > 1500:
            estado_juego = "INICIO"
        
    time.sleep_ms(10) # Watchdog y estabilización del bus SPI