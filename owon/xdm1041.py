import serial
import time

# Abre el puerto serie (ajusta el puerto y la velocidad de baudios según sea necesario)
ser = serial.Serial('COM4', 115200, timeout=1)  # Reemplaza COM3 con tu puerto serial

# # Envía el comando *IDN? para obtener la identificación del dispositivo
# #ser.write(b'*IDN?\n')
# ser.write(b'MEASURE:VDC?\n')


# # Lee la respuesta del multímetro
# respuesta = ser.readline().decode('utf-8').strip()

# # Muestra la respuesta
# print('Respuesta del multímetro:', respuesta)

# Envía el comando SCPI para leer el voltaje DC
ser.write(b'MEASURE:VDC?\n')

# Lee la respuesta del multímetro
voltaje_dc = ser.readline().decode('utf-8').strip()

# Muestra el voltaje leído
print(f'Voltaje DC: {voltaje_dc} V')



# Cerrar el puerto
ser.close()