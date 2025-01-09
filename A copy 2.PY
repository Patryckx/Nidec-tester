import serial
# Configuración del puerto serial
ser = serial.Serial(
    port='COM5',        # Cambia al puerto correcto
    baudrate=9600,      # Velocidad de comunicación (verifica con tu dispositivo)
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

command = bytes.fromhex('FF00FFA50060100D04D05101010249')
ser.write(command)

# Leer la respuesta
response = ser.read(256)
print(response)

command = bytes.fromhex('FF00FFA50060100D04D05C01320285')
ser.write(command)

# Leer la respuesta
response = ser.read(256)
print(response)

command = bytes.fromhex('FF00FFA50060100D05D05B0200000254')
ser.write(command)

# Leer la respuesta
response = ser.read(256)
print(response)


# command = bytes.fromhex('FF00FFA50060100D05D05B0202000256')
# ser.write(command)

# # Leer la respuesta
# response = ser.read(256)
# print(response)


# command = bytes.fromhex('FF00FFA50060100D05D05D0402000256')
# ser.write(command)

# # Leer la respuesta
# response = ser.read(256)
# print(response)


# command = bytes.fromhex('FF00FFA50060100D07D05D0400000000025A')
# ser.write(command)

# # Leer la respuesta
# response = ser.read(256)
# print(response)


# command = bytes.fromhex('FF00FFA50060100D05D05B0203FF0356')
# ser.write(command)

# # Leer la respuesta
# response = ser.read(256)
# print(response)


# command = bytes.fromhex('FF00FFA50060100D07D05D04 48 4F 4C 41 037E')
# ser.write(command)

# # Leer la respuesta
# response = ser.read(256)
# print(response)

# Cerrar puerto serial
ser.close()