import serial
import time

# Abre el puerto serie (ajusta el puerto y la velocidad de baudios según sea necesario)
ser = serial.Serial('COM3', 9600, timeout=1)  # Reemplaza COM3 con tu puerto serial

# Envía el comando *IDN? para obtener la identificación del dispositivo
ser.write(b'*IDN?\n')

#ser.write(b'MEASURE:VDC?\n')
# ser.write(b'MEASURE:VAC?\n')
# ser.write(b'MEASURE:IDC?\n')
# ser.write(b'MEASURE:IAC?\n')
# ser.write(b'MEASURE:RES?\n')

# ser.write(b'RANGE:VDC 10\n')  # Establece el rango de voltaje DC a 10 V


# ser.write(b'SYSTEM:POWER ON\n')  # Enciende el multímetro
# # o
# ser.write(b'SYSTEM:POWER OFF\n')  # Apaga el multímetro

# # Lee la respuesta del multímetro
# respuesta = ser.readline().decode('utf-8').strip()

# ser.write(b'VOLUME:RESOLUTION 3\n')  # Configura la resolución a 3 decimales


# ser.write(b'*RST\n')  # Restablece el multímetro


#ser.write(b'MEASURE:STATUS?\n')
estado = ser.readline().decode('utf-8').strip()
print('Estado de medición:', estado)


# Muestra la respuesta
print('Respuesta del multímetro:', estado)

# Cerrar el puerto
ser.close()