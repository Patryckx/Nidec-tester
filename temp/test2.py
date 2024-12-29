import serial
import time

def send_command(ser, command):
    """
    Envía un comando en formato hexadecimal a través del puerto serial.
    
    :param ser: Objeto serial (conexión abierta)
    :param command: Comando en formato hexadecimal (lista de bytes)
    """
    # Enviar el comando
    ser.write(command)
    print(f"Comando enviado: {command.hex().upper()}")
    
    # Esperar una respuesta del dispositivo
    time.sleep(1)  # Tiempo de espera para la respuesta
    
    # Leer la respuesta (hasta 100 bytes en este caso)
    response = ser.read(100)
    print(f"Respuesta recibida: {response.hex().upper()}")
    return response

def main():
    # Configuración del puerto serial
    port = 'COM3'  # Cambia esto al puerto correcto
    baudrate = 9600
    timeout = 1

    # Abriendo la conexión serial
    ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout, 
                        parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)

    if ser.is_open:
        print(f"Conexión serial abierta en {port} a {baudrate} bps.")
    else:
        print(f"No se pudo abrir el puerto {port}.")
        return

    # Comando en formato hexadecimal: 'Command Mode' (0x51 0x01 0x00 para Monitor Mode)
    command = bytes([0x51, 0x01, 0x00])  # Cambia 0x00 a 0x01 para Production Test Mode

    # Enviar el comando y recibir la respuesta
    response = send_command(ser, command)

    # Cerrar la conexión serial
    ser.close()
    print("Conexión serial cerrada.")

if __name__ == "__main__":
    main()
