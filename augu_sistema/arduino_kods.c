#include <DHT.h>

#define DHTPIN 2          // DHT22 datu savienojums
#define DHTTYPE DHT22     // DHT 22 (AM2302)
#define MOISTURE_PIN A0   // Augsnes sensora savienojums
#define PUMP_PIN 8        // 5v pumpis

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  dht.begin();

  pinMode(PUMP_PIN, OUTPUT);
  digitalWrite(PUMP_PIN, LOW);
}

void loop() {
  if (Serial.available() > 0) {
    String komanda = Serial.readStringUntil('\n');
    komanda.trim();

    if (komanda == "P_ON") {
      digitalWrite(PUMP_PIN, HIGH);
    } else if (komanda == "P_OFF") {
      digitalWrite(PUMP_PIN, LOW);
    }
  }
  
  int augsnesMitrums = analogRead(MOISTURE_PIN); // Nolasa augsnes mitruma sensora vērtību

  float gaisaTemperatura = dht.readTemperature(); // Nolasa DHT22 vērtības, izmantojot dht bibliotēku
  float gaisaMitrums = dht.readHumidity();

  Serial.print("AM:"); // Augsnes mitrums
  Serial.println(augsnesMitrums);

  Serial.print("GT:"); // Gaisa temperatūra
  Serial.println(gaisaTemperatura);

  Serial.print("GM:"); // Gaisa mitrums
  Serial.println(gaisaMitrums);


  delay(1000); // vienas sekundes pauze
}
