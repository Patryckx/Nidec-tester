import serial
import time


def calculate_checksum(packet):
    """Calcula el checksum para el paquete."""
    checksum = sum(packet[3:])  # Sumar desde el byte 4 hasta el final
    high_byte = (checksum >> 8) & 0xFF  # Parte alta del checksum
    low_byte = checksum & 0xFF  # Parte baja del checksum
    return high_byte, low_byte

def build_packet(command_id, message_data=None):
    """Construye un paquete Pentair para el comando especificado."""
    # Paquete base
    packet = [
        0xFF, 0x00, 0xFF,  # Preamble
        0xA5,              # Sync Byte
        0x00,              # House Address
        0x60,              # Destination Address (HMI)
        0x10,              # Source Address
        command_id,        # Op Code
    ]
    
    # Si hay datos, agregar longitud y datos
    if message_data:
        packet.append(len(message_data))  # Longitud de los datos
        packet.extend(message_data)      # Datos adicionales
    else:
        packet.append(0x00)  # Longitud = 0 si no hay datos
    
    # Calcular checksum y agregarlo al paquete
    high_byte, low_byte = calculate_checksum(packet)
    packet.extend([high_byte, low_byte])
    return bytes(packet)

def send_command(serial_port, command_id, message_data=None):
    """Envía un comando al dispositivo y verifica la respuesta."""
    packet = build_packet(command_id, message_data)
    serial_port.write(packet)
    print(f"Enviado: {packet.hex().upper()}")
    
    # Leer la respuesta (ajustar el tamaño según sea necesario)
    response = serial_port.read(32)  # Leer hasta 32 bytes, puedes ajustar este valor
    print(f"Respuesta: {response.hex().upper()}")
    return response

def split_16bit(value):
    """Divide un valor de 16 bits en dos bytes."""
    high_byte = (value >> 8) & 0xFF
    low_byte = value & 0xFF
    return high_byte, low_byte


def main():
    # Configuración de conexión serial
    port = "COM5"  # Cambiar por el puerto correcto
    baudrate = 9600  # Ajustar según especificaciones del HMI
    timeout = 1
    
    try:
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            print("Conexión establecida con el dispositivo.")
            
            # # Enviar comando para activar modo de comandos
            print("Enviando comando para activar modo de comandos...")
            send_command(ser, 0x0D, [0xD0, 0x51, 0x01, 0x01])
            time.sleep(1)  # Esperar para recibir respuesta
            
            # # Enviar comando de consulta de versión de firmware
            print("Enviando comando de consulta de versión de firmware...")
            response = send_command(ser, 0x0D, [0xD0, 0x56, 0x00] )
            print(f"Respuesta recibida: {response.hex().upper()}")

            
            # # Ejemplo de uso
            # led_high, led_low = split_16bit(0x200)

             # Enviar comando de consulta de versión de firmware
            print("Enviando comando apagar leds ...")
            response = send_command(ser, 0x0D, [0xD0, 0x5B,0x02,  0x00, 0x00] )
            
            print(f"Respuesta recibida: {response.hex().upper()}")

            # # Enviar comando de consulta de versión de firmware
            # '''print("Enviando comando de control de LEDS...")
            # response = send_command(ser, 0x0D, [0xD0, 0x5B,0x02, 0x01,0x00] )
            # print(f"Respuesta recibida: {response.hex().upper()}")'''


             # Enviar comando de consulta de versión de firmware
            print("Enviando comando Control intensidad pantalla...")
            response = send_command(ser, 0x0D, [0xD0, 0x5C,0x01, 0x00] )
            print(f"Respuesta recibida: {response.hex().upper()}")

             # Enviar comando de consulta de versión de firmware
            print("Enviando comando Control intensidad pantalla...")
            response = send_command(ser, 0x0D, [0xD0, 0x5C,0x01, 0x64] )
            print(f"Respuesta recibida: {response.hex().upper()}")

            #  # Enviar comando de consulta de versión de firmware
            # print("Enviando comando Esribir pantalla LCD...")
            # response = send_command(ser, 0x0D, [0xD0, 0x5D,0x04, 0x48, 0x4f, 0x4c, 0x41] )
            # print(f"Respuesta recibida: {response.hex().upper()}")

            #  # Enviar comando de consulta de versión de firmware
            # print("Enviando comando iconos LCD...")
            # response = send_command(ser, 0x0D, [0xD0, 0x5E,0x01, 0x01,0X001] )
            # print(f"Respuesta recibida: {response.hex().upper()}")

    
    except serial.SerialException as e:
        print(f"Error en la conexión serial: {e}")
    except KeyboardInterrupt:
        print("Conexión cerrada por el usuario.")

if __name__ == "__main__":
    main()
