import serial
import time

# Configuración del puerto RS-485
ser = serial.Serial('COM3', baudrate=9600, timeout=1)  # Ajusta 'COMx' al puerto que uses

# Paquete de datos (excluyendo los bytes de preámbulo y checksum calculado)
packet = [
    0xFF, 0x00, 0xFF, 0xA5,  # Preambulo y sincronización
    0x00, 0x60, 0x10, 0x0D,  # Dirección de la casa, destino, origen y código de operación
    0x04, 0xD0, 0x51, 0x01, 0x01  # Comando Command Mode y datos
]

# Cálculo del checksum (puedes adaptarlo si tu sistema tiene un método específico)
checksum = sum(packet[4:]) & 0xFFFF  # Sumar los bytes y obtener los 16 bits más bajos
checksum_high = (checksum >> 8) & 0xFF  # 8 bits más altos
checksum_low = checksum & 0xFF  # 8 bits más bajos

# Agregar el checksum al paquete
packet.append(checksum_high)
packet.append(checksum_low)

# Enviar el paquete
ser.write(bytearray(packet))

# Esperar un tiempo para que el dispositivo responda
time.sleep(1)  # Ajusta el tiempo de espera según el dispositivo

# Leer la respuesta del dispositivo
response = ser.read(ser.in_waiting)  # Lee todos los datos disponibles

# Verificar si se recibió alguna respuesta
if response:
    print(f"Respuesta recibida: {response.hex()}")
else:
    print("No se recibió respuesta.")

# Cerrar el puerto serial
ser.close()
