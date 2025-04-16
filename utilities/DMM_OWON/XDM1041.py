import serial
import time

'''1. Identificación del dispositivo:
Comando: *IDN?
Descripción: Obtiene la identificación del dispositivo (marca, modelo, número de serie, etc.)
ser.write(b'*IDN?\n')
respuesta = ser.readline().decode('utf-8').strip()
print('Identificación del multímetro:', respuesta)

2. Medición de voltaje (DC):
Comando: MEASURE:VDC?
Descripción: Solicita la medición de voltaje en corriente continua (DC).
ser.write(b'MEASURE:VDC?\n')
voltaje_dc = ser.readline().decode('utf-8').strip()
print('Voltaje DC:', voltaje_dc)

3. Medición de voltaje (AC):
Comando: MEASURE:VAC?
Descripción: Solicita la medición de voltaje en corriente alterna (AC).
ser.write(b'MEASURE:VAC?\n')
voltaje_ac = ser.readline().decode('utf-8').strip()
print('Voltaje AC:', voltaje_ac)

4. Medición de corriente (DC):
Comando: MEASURE:IDC?
Descripción: Solicita la medición de corriente en corriente continua (DC).
ser.write(b'MEASURE:IDC?\n')
corriente_dc = ser.readline().decode('utf-8').strip()
print('Corriente DC:', corriente_dc)

5. Medición de corriente (AC):
Comando: MEASURE:IAC?
Descripción: Solicita la medición de corriente en corriente alterna (AC).
ser.write(b'MEASURE:IAC?\n')
corriente_ac = ser.readline().decode('utf-8').strip()
print('Corriente AC:', corriente_ac)

6. Medición de resistencia:
Comando: MEASURE:RES?
Descripción: Solicita la medición de resistencia.


7. Configurar el rango de medición:
Comando: RANGE:<tipo> <valor>
Ejemplo para voltaje DC:
Comando: RANGE:VDC 10
Descripción: Configura el rango de medición de voltaje DC a 10 V.
ser.write(b'RANGE:VDC 10\n')  # Establece el rango de voltaje DC a 10 V

8. Encender y apagar el dispositivo (Control de encendido):
Comando: SYSTEM:POWER ON o SYSTEM:POWER OFF
Descripción: Controla el encendido del dispositivo.
ser.write(b'SYSTEM:POWER ON\n')  # Enciende el multímetro
# o
ser.write(b'SYSTEM:POWER OFF\n')  # Apaga el multímetro

9. Configuración de la resolución de medición:
Comando: VOLUME:RESOLUTION <valor>
Por ejemplo, puedes configurar la resolución de la medición a 3 decimales.
Ejemplo: VOLUME:RESOLUTION 3
Ejemplo en código:
ser.write(b'VOLUME:RESOLUTION 3\n')  # Configura la resolución a 3 decimales

10. Borrar memoria o restablecer el dispositivo:
Comando: *RST
Descripción: Restablece el dispositivo a su configuración predeterminada.
ser.write(b'*RST\n')  # Restablece el multímetro

11. Leer el estado de la medición en curso:
Comando: MEASURE:STATUS?
Descripción: Devuelve el estado actual de la medición.
ser.write(b'MEASURE:STATUS?\n')'''


class XDM1041:

    def __init__(self,port:str,timeout=1):
        self.port=port
        self.bauds=115200
        self.timeout=timeout
        self.connection=None

    def connect(self):
        
        try:
            self.connection=serial.Serial(self.port, self.bauds, timeout=self.timeout) 
            return True
        except Exception as e:
            print(f"Error con la conexion:{e}")
            return False
        
    def send_command(self,command:str):

        try:
            if isinstance(command, str):
                command = command.encode('utf-8')
            self.connection.write(command)
            return self.connection.readline().decode('utf-8').strip()
        except Exception as e:
            print(f"Error al enviar el comando: {e}")
            return None

        # try:
        #     self.connection.write(command)
        #     return self.connection.readline().decode('utf-8').strip()
        # except Exception as e:
        #     print(f"Error al enviar el comando:{e}")
        #     return None

    def readline(self):

        try:
            if self.connection:
                return self.connection.readline().decode('utf-8').strip()
            else:
                raise Exception("No existe una conexion")
        except Exception as e:
            print(f"Error al leer el dispositivo{e} ")
            return None

    def close(self):
        try:
            self.connection.close()

        except Exception as e:
            print(f"Error al cerrar el dispositivo: {e}")

if __name__ =="__main__":
    port='COM6'
    bauds=115200

    multimeter=XDM1041(port)
    multimeter.connect()
    dc_voltaje=b'MEASURE:VDC?\n'
    try:

        resultado=multimeter.send_command(dc_voltaje)
   
        #estado = multimeter.readline()
        print('Estado de medición:', resultado)
    except Exception as e:
        print("Ocurrio un error")