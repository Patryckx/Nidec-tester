import serial

# Configuración del puerto serial
ser = serial.Serial('COM3', 9600, timeout=1)  # COMx debe ser reemplazado por el puerto correcto

# Enviar un comando al dispositivo
ser.write(b'\xFF\x00\xFF\xA5\x00\x10\x10\x0D\x04\xD0\x51\x01\x01')

# Leer la respuesta
response = ser.read(100)
print(response)

# Cerrar puerto serial
ser.close()
