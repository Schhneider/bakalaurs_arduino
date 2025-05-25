import serial
import time

SERIAL_PORT = '/dev/ttyUSB0' #Seriālā porta adrese (var atšķirties uz citām operētājsistēmām)
BAUD_RATE = 9600             #Datu pārraides ātrums
TIMEOUT = 1                  #Laika limits

# Funkcija kas pārveido datus no analogā uz procentu.
# Sausā vērtība tika iegūta gaisā, mitrā vērtība tika iegūta ūdens glāzē
def mitrums_uz_procentiem(dati):
    sauss = 517 # Kalibrētā vērtība sausai zemei
    mitrs = 206 # Kalibrētā vērtība mitrai zemei

    if dati > sauss:
        return -1
    if dati < mitrs:
        return 100.00

    procents = (sauss - dati) / (sauss - mitrs) * 100
    return round(procents, 2)

# Funkcija kas nolasa augsnes mitruma vērtību no augsnes mitruma sensora
def get_augsnes_mitrums() -> int:
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
            start_time = time.time()
            ser.flush()

            while time.time() - start_time < 2:
                if ser.in_waiting:
                    line = ser.readline().decode('utf-8').strip()
                    if "AM:" in line:
                        try:
                            raw = int(line.split(":")[1].strip())
                            return mitrums_uz_procentiem(raw)
                        except ValueError:
                            continue
        return -1
    except Exception as e:
        print(f"Kļūda nolasot mitrumu: {e}")
        return -1

# Iegūst temperatūru un mitrumu no DHT22 sensora
def get_dht22():
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
            ser.flush()
            start_time = time.time()
            temperatura = None
            mitrums = None

            while time.time() - start_time < 2:
                if ser.in_waiting:
                    line = ser.readline().decode('utf-8').strip()
                    if "GT:" in line:
                        try:
                            temperatura = float(line.split(":")[1].strip())
                        except ValueError:
                            continue
                    elif "GM:" in line:
                        try:
                            mitrums = float(line.split(":")[1].strip())
                        except ValueError:
                            continue

                    if temperatura is not None and mitrums is not None:
                        break

            return {"GT": temperatura, "GM": mitrums}
    except Exception as e:
        print(f"Kļūda nolasot DHT22: {e}")
        return {"GT": None, "GM": None}

# Funkcija pumpja ieslēgšanai un izslēgšanai
def ieslegt_pumpi(on: bool):
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
            time.sleep(2)
            ser.flush()
            command = "P_ON\n" if on else "P_OFF\n"
            ser.write(command.encode('utf-8'))
            print(f"Izsūtīta komanda: {command.strip()}")
    except Exception as e:
        print(f"Pumpja kontroles kļūda: {e}")

