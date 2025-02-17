import serial

## Configuración del puerto serial
ser = serial.Serial(
    port='COM7',        # Cambia al puerto correcto
    baudrate=9600,      # Velocidad de comunicación (verifica con tu dispositivo)
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)



# command = bytes.fromhex('FF00FFA50060100D04D05001010249')
# ser.write(command)

# # Leer la respuesta
# response = ser.read(256)
# print(response)


#while True:
command = bytes.fromhex('FF00FFA50060100D04D05101010249')
ser.write(command)

# Leer la respuesta
response = ser.read(256)
#print(response)

# Convertir la respuesta a formato hexadecimal legible
formatted_response = response.hex().upper()

# Imprimir la respuesta en formato legible
print(formatted_response)

command = bytes.fromhex('FF00FFA50060100D05D05B0203FF0356')
ser.write(command)
#FF00FFA50060100D04D05E011F0274
# Leer la respuesta
response = ser.read(256)
print(response)

# Convertir la respuesta a formato hexadecimal legible
formatted_response = response.hex().upper()

# Imprimir la respuesta en formato legible
print(formatted_response)

# command = bytes.fromhex('FF00FFA50060100D04D05E011F0274')
# ser.write(command)

# # Leer la respuesta
# response = ser.read(256)
# #print(response)

# # Convertir la respuesta a formato hexadecimal legible
# formatted_response = response.hex().upper()

# # Imprimir la respuesta en formato legible
# print(formatted_response)


# command = bytes.fromhex('FF00FFA50060100D07D05D0408080808027A')
# ser.write(command)

# # Leer la respuesta
# response = ser.read(256)
# #print(response)

# # Convertir la respuesta a formato hexadecimal legible
# formatted_response = response.hex().upper()

# # Imprimir la respuesta en formato legible
# print(formatted_response)




# command = bytes.fromhex('FF00FFA50060100D04D05C01320285')
# ser.write(command)

# # Leer la respuesta
# response = ser.read(256)
# print(response)

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


# command = bytes.fromhex('FF00FFA50060100D07D05D04484F4C41037E')
# ser.write(command)

# # Leer la respuesta
# response = ser.read(256)
# print(response)


# Cerrar puerto serial
ser.close()
