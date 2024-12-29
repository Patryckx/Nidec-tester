import serial

# Configuración del puerto RS485
ser = serial.Serial(
    port='COM3',          # Cambia por el puerto COM correspondiente
    baudrate=9600,        # Ajusta el baudrate según el dispositivo
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

# Mensaje para activar Production Test Mode
message = bytes([0x51, 0x01, 0x01])  

# Enviar el mensaje
ser.write(message)
print("Mensaje enviado para activar Production Test Mode")

# Leer la respuesta del HMI (opcional)
response = ser.read(10)  # Leer hasta 10 bytes
print(f"Respuesta del HMI: {response}")

# Cerrar el puerto
ser.close()
