import serial
import time

def calculate_checksum(packet):
    """Calcula el checksum para el paquete."""
    checksum = sum(packet[3:])  # Sumar desde el byte 4 hasta el final
    high_byte = (checksum >> 8) & 0xFF  # Parte alta del checksum
    low_byte = checksum & 0xFF  # Parte baja del checksum
    return high_byte, low_byte

def build_packet(command_mode):
    """Construye un paquete Pentair para activar el modo de comandos."""
    # Paquete base
    packet = [
        0xFF, 0x00, 0xFF,  # Preamble
        0xA5,              # Sync Byte
        0x00,              # House Address
        0x60,              # Destination Address (VS drive)
        0x10,              # Source Address (Pool control system)
        0x0D,              # Op Code
        0x04,              # Length (N = 4)
        0xD0,              # Packet Type
        0x51,              # Command Message Number
        0x01,              # Size of Message Data Bytes
        command_mode       # Command mode (0x00 = Monitor, 0x01 = Production Test)
    ]
    
    # Calcular checksum y agregarlo al paquete
    high_byte, low_byte = calculate_checksum(packet)
    packet.extend([high_byte, low_byte])
    return bytes(packet)

def send_command(serial_port, command_mode):
    """Envía un comando al dispositivo y verifica la respuesta."""
    packet = build_packet(command_mode)
    serial_port.write(packet)
    print(f"Enviado: {packet.hex().upper()}")
    
    # Leer la respuesta
    response = serial_port.read(16)  # Leer hasta 16 bytes (ajustar si necesario)
    print(f"Respuesta: {response.hex().upper()}")
    return response

def main():
    # Configuración de conexión serial
    port = "COM4"  # Cambiar por el puerto correcto
    baudrate = 9600  # Ajustar según especificaciones del HMI
    timeout = 1
    
    try:
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            print("Conexión establecida con el dispositivo.")
            
            # Enviar comando para activar modo de producción
            response = send_command(ser, 0x01)
            
            # Validar la respuesta (puedes implementar lógica adicional aquí)
            if response:
                print("Comando enviado y respuesta recibida.")
            else:
                print("No se recibió respuesta del dispositivo.")
            
            # Mantener el modo de producción con comandos periódicos
            while True:
                time.sleep(25)  # Enviar comando cada 25 segundos
                send_command(ser, 0x01)
    
    except serial.SerialException as e:
        print(f"Error en la conexión serial: {e}")
    except KeyboardInterrupt:
        print("Conexión cerrada por el usuario.")

if __name__ == "__main__":
    main()
