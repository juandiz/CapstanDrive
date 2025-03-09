/**
 * ESP32-C3 ADS1230 Reader
 * 
 * This program reads data from an ADS1230 ADC board using a simple DRDY/DOUT and SCLK interface.
 * It prints the raw ADC values via serial communication.
 */

// Define the pin connections
const int DOUT_PIN = 10;  // DRDY/DOUT pin
const int SCLK_PIN = 9;  // SCLK pin
const int PDWN_PIN = 6;  // Power down pin

// Optional ADS1230 control pins (if connected)
// const int SPEED_PIN = 7; // Speed pin (10/80 SPS selection)

const int OFFSET = 7700;  // Power down pin


// Load cell calibration values
int32_t zeroOffset = 0;       // ADC reading at no load
int32_t calibrationValue = 0; // ADC reading at known weight
float knownWeight = 1.0;      // Known calibration weight in kg
bool isCalibrated = false;    // Flag to indicate if calibration has been done


void setup() {
  // Initialize serial communication at 115200 baud
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for serial port to connect
  }

  Serial.println("ADS1230 Initialize");
  
  // Configure pins
  pinMode(DOUT_PIN, INPUT);
  pinMode(SCLK_PIN, OUTPUT);
  pinMode(PDWN_PIN, OUTPUT);

  digitalWrite(PDWN_PIN, HIGH);  // Normal operation mode
  delay(10);
  digitalWrite(SCLK_PIN, LOW);  // Initial SCLK state
  digitalWrite(PDWN_PIN, LOW);  // Normal operation mode
  delay(10); 
  digitalWrite(PDWN_PIN, HIGH);  // Normal operation mode
  delay(10); 

  // Optional configuration for additional control pins
  // pinMode(SPEED_PIN, OUTPUT);
  // digitalWrite(SPEED_PIN, LOW);  // 10 SPS mode (LOW = 10 SPS, HIGH = 80 SPS)
  
 
  Serial.println("ADS1230 Reader Initialized");
  Serial.println("Read One data to clean buffer");
  int32_t adcValue = readADS1230();
  Serial.println(adcValue);
  Serial.println("Read One completed");

  delay(10);  // Short delay for setup
}

// void noloop() {
//   // Check if data is ready (DRDY is LOW when data is ready)
//   if (digitalRead(DOUT_PIN) == LOW) {
//     // Read the 24-bit value
//     int32_t adcValue = readADS1230() - OFFSET;
    
//     // Print the raw ADC value
//     // Serial.print("ADS1230 Raw Value: ");
//     // Serial.println(adcValue);

//     float weight = convertToWeight(adcValue, 1);
//     Serial.println(weight, 6);
    
//     // Optional: Convert to voltage or weight depending on your application
//     // float voltage = convertToVoltage(adcValue);
//     // Serial.print("Voltage: ");
//     // Serial.println(voltage, 6);
//   }
  
//   delay(10);  // Short delay between readings
// }

void loop() {
  // Check for serial commands
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    switch (command) {
      case 't': // Tare - set zero point
        performTare();
        break;
      case 'c': // Calibrate with known weight
        performCalibration();
        break;
      case 'r': // Reset calibration
        resetCalibration();
        break;
    }
  }
  
  // Check if data is ready (DRDY is LOW when data is ready)
  if (digitalRead(DOUT_PIN) == LOW) {
    // Read the 20-bit value
    int32_t adcValue = readADS1230();
    
    // Convert to weight
    float weight = convertToWeight(adcValue);
    
    // Print the raw ADC value and weight
    Serial.print("ADC: ");
    Serial.print(adcValue);
    
    if (isCalibrated) {
      Serial.print(", Weight: ");
      Serial.print(weight, 3);  // 3 decimal places
      Serial.println(" kg");    // Adjust unit as needed
    } else {
      Serial.print(", Uncalibrated: ");
      Serial.println(weight, 3);
      Serial.println("Please calibrate using 't' and 'c' commands");
    }
  }
  
  delay(100);  // Short delay between readings
}

void waitForDataReady() {
  // DRDY is active LOW, meaning it's already LOW when data is ready
  // No need to wait if it's already LOW
  if (digitalRead(DOUT_PIN) == LOW) {
    // Data is already ready, no need to wait
    return;
  }
  
  // If not ready yet, wait for DRDY to go LOW
  while (digitalRead(DOUT_PIN) == HIGH) {
    yield();  // Allow ESP32 to handle background tasks
  }
}

int32_t readADS1230() {
  int32_t adcValue = 0;
  
  // Read 20 bits
  for (int i = 0; i < 20; i++) {
    // Pulse SCLK high
    digitalWrite(SCLK_PIN, HIGH);
    delayMicroseconds(1);  // Short delay for stability
    
    // Read data bit
    adcValue = (adcValue << 1) | digitalRead(DOUT_PIN);
    
    // Pulse SCLK low
    digitalWrite(SCLK_PIN, LOW);
    delayMicroseconds(1);  // Short delay for stability
  }
  
  // Generate an additional SCLK pulse to complete the cycle
  digitalWrite(SCLK_PIN, HIGH);
  delayMicroseconds(1);
  digitalWrite(SCLK_PIN, LOW);
  
  // Handle two's complement (convert to signed)
  if (adcValue & 0x80000) {  // Check the MSB (bit 19) for sign
    adcValue |= 0xFFF00000;  // Sign extension for negative values (for 20-bit value)
  }
  
  return adcValue;
}


//// 

// Function to convert ADC value to calibrated weight
float convertToWeight(int32_t adcValue) {
  // Apply zero offset
  int32_t offsetCorrected = adcValue - zeroOffset;
  
  // If not calibrated, return raw value (scaled down for readability)
  if (!isCalibrated) {
    return offsetCorrected / 1000.0;
  }
  
  // Calculate weight based on calibration
  float weight = offsetCorrected * knownWeight / (calibrationValue - zeroOffset);
  
  return weight;
}

// Function to convert ADC value to voltage
float convertToVoltage(int32_t adcValue) {
  // Assuming ADS1230 with gain = 1 and Vref = 2.5V
  // Full scale range is ±(2^19-1) counts
  const float VREF = 2.5;
  const float FULL_SCALE = 524287.0;  // 2^19 - 1
  
  return (adcValue / FULL_SCALE) * VREF;
}



///////
// Calibration and offset

// Tare function - set the zero point
void performTare() {
  Serial.println("Place no weight on scale and wait...");
  delay(2000);  // Give time to remove weight and stabilize
  
  // Take average of multiple readings for better stability
  int32_t sum = 0;
  int samples = 10;
  
  for (int i = 0; i < samples; i++) {
    waitForDataReady();
    sum += readADS1230();
    delay(50);
  }
  
  zeroOffset = sum / samples;
  Serial.print("Zero offset set to: ");
  Serial.println(zeroOffset);
}

// Calibration function - use a known weight
void performCalibration() {
  Serial.println("Place known weight on scale and enter the weight in kg (e.g. '1.0'):");
  
  // Wait for weight input
  while (!Serial.available()) {
    delay(100);
  }
  
  // Read the known weight value
  knownWeight = Serial.parseFloat();
  Serial.print("Using ");
  Serial.print(knownWeight);
  Serial.println(" kg as calibration weight");
  
  delay(1000);  // Give time to stabilize
  
  // Take average of multiple readings for better stability
  int32_t sum = 0;
  int samples = 10;
  
  for (int i = 0; i < samples; i++) {
    waitForDataReady();
    sum += readADS1230();
    delay(50);
  }
  
  calibrationValue = sum / samples;
  isCalibrated = true;
  
  Serial.print("Calibration value set to: ");
  Serial.println(calibrationValue);
  Serial.println("Calibration complete!");
}

// Reset calibration
void resetCalibration() {
  zeroOffset = 0;
  calibrationValue = 0;
  isCalibrated = false;
  Serial.println("Calibration reset");
}


