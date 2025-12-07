
int val = 0;
unsigned long lastSampleTime = 0;
const unsigned long SAMPLE_INTERVAL = 4000; // 4ms = 250 Hz (appropriate for EEG)

void setup() {
  Serial.begin(115200);
}

void loop() {
  unsigned long currentTime = micros();

  if (currentTime - lastSampleTime >= SAMPLE_INTERVAL) {
    lastSampleTime = currentTime;

    val = analogRead(A0);

    float seconds = millis() / 1000.0;  // Convert to seconds with decimal
    Serial.print(seconds, 3);           // Print with 3 decimal places
    Serial.print(",");
    Serial.println(val);                // Raw ADC value (0-1023) with newline
  }
}