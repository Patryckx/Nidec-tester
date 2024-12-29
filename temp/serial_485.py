import serial

def calculate_checksum(packet):
    """
    Calcula el checksum como la suma de todos los bytes, truncada a 1 byte.
    """
    return sum(packet) & 0xFF

# Configuración del puerto serial
ser = serial.Serial(
    port='COM3',        # Cambia al puerto correcto
    baudrate=9600,      # Velocidad de comunicación (verifica con tu dispositivo)
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

# Construcción del paquete
packet = [
    0xFF, 0x00, 0xFF, 0xA5,  # Preamble & Sync
    0x00,                    # House
    0x10,                    # Destination
    0x10,                    # Source
    0x0D,                    # Op Code
    0x04,                    # Length
    0xD0,                    # Type
    0x51,                    # Command
    0x01,                    # Size
    0x01                     # Data
]

# Cálculo del checksum
checksum = calculate_checksum(packet)
packet.append(checksum)


# Conversión a bytes y envío (usando bytes en lugar de bytearray)
ser.write(bytes(packet))
# Conversión a bytes y envío
ser.write(bytearray(packet))

# Leer la respuesta (si es necesario)
response = ser.read(100)  # Leer hasta 100 bytes o el timeout
print("Respuesta:", response)

# Cerrar el puerto serial
ser.close()
