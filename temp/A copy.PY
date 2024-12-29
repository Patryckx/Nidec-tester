import serial

## Configuración del puerto serial
ser = serial.Serial(
    port='COM3',        # Cambia al puerto correcto
    baudrate=9600,      # Velocidad de comunicación (verifica con tu dispositivo)
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)


# Enviar un comando al dispositivo
ser.write(b'\xFF\x00\xFF\xA5\x00\x10\x10\x0D\x04\xD0\x51\x01\x01')

# Leer la respuesta
response = ser.read(256)
print(response)

# Cerrar puerto serial
ser.close()
