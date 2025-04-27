/**
 * ESP32-C3 ADS1230 Reader
 * 
 * This program reads data from an ADS1230 ADC board using a simple DRDY/DOUT and SCLK interface.
 * It prints the raw ADC values via serial communication.
 */

#include "ArduinoJson.h"

// Define the pin connections
const int DOUT_PIN = 10;  // DRDY/DOUT pin
const int SCLK_PIN = 9;  // SCLK pin
const int PDWN_PIN = 6;  // Power down pin

// Optional ADS1230 control pins (if connected)
// const int SPEED_PIN = 7; // Speed pin (10/80 SPS selection)

const int OFFSET = 7700;  // Power down pin


// Load cell calibration values
int32_t zeroOffset = 0;       // ADC reading at no load
int32_t calibrationValue = 80000; // ADC reading at known weight
float knownWeight = 1.0;      // Known calibration weight in kg
bool isCalibrated = false;    // Flag to indicate if calibration has been done
int16_t sendValuesIntervalLoops = 5;
int8_t sendValuesCounter = 0;
int16_t loopDelay = 100;
bool continuousUpdate = false;

// Create a DynamicJsonDocument with a capacity of 200 bytes
DynamicJsonDocument doc(200);

void setup() {

  doc["adcValue"] = 0;
  doc["zeroOffset"] = 0;
  doc["offsetCorrected"] = 0;
  doc["isCalibrated"] = false;
  doc["knownWeight"] = 00;
  doc["calibrationValue"] = 0;
  doc["calculatedWeight"] = 0;

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

void sendCurrentValues(){
  // Serialize JSON to string and print
  serializeJson(doc, Serial);
  Serial.println();
}

void selectMode() {
  // Wait for weight input
  while (!Serial.available()) {
    delay(100);
  }
  
  // Read the known weight value
  char mode = Serial.read();
  if (mode == 'm'){
    continuousUpdate = false;
    Serial.print("Manual mode selected");
  }
  else if (mode == 'a'){
    continuousUpdate = true;
    Serial.print("Automatic mode selected");
  }
  else{
    Serial.print("Unsupported mode");
    Serial.println(mode);
  }
}

void readCommands(){
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
      case 'g':
        sendCurrentValues();
        break;
      case 'm': // mode selection
        selectMode();
        break;
    }
  }
}

void checkDataReady(){
  // Check if data is ready (DRDY is LOW when data is ready)
  if (digitalRead(DOUT_PIN) == LOW) {

    Serial.print("New value ready");
    
    // Read the 20-bit value
    int32_t adcValue = readADS1230();
    
    // Convert to weight
    float weight = convertToWeight(adcValue);
    
    // Print the raw ADC value and weight
    // Serial.print("ADC: ");
    // Serial.print(adcValue);
      doc["adcValue"] = adcValue;
      doc["isCalibrated"] = isCalibrated;
      doc["calculatedWeight"] = weight;
    
    // if (isCalibrated) {
    //   Serial.print(", Weight: ");
    //   Serial.print(weight, 3);  // 3 decimal places
    //   Serial.println(" kg");    // Adjust unit as needed
    // } else {
    //   Serial.print(", Uncalibrated: ");
    //   Serial.println(weight, 3);
    //   Serial.println("Please calibrate using 't' and 'c' commands");
    // }
    // data is rady and continius update on
    if(continuousUpdate)
      sendCurrentValues();
  }
}

void loop() {
  readCommands();
  checkDataReady();
  delay(loopDelay);  // Short delay between readings
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
  
  // Pretty print all variables
  // Serial.println("=== Debug Info ===");
  // Serial.print("ADC Value: ");
  // Serial.println(adcValue);
  // Serial.print("Zero Offset: ");
  // Serial.println(zeroOffset);
  // Serial.print("Offset Corrected: ");
  // Serial.println(offsetCorrected);
  // Serial.print("Calibration: ");
  // Serial.println(calibrationValue);
  // Serial.print("Calibration weigth: ");
  // Serial.println(knownWeight);
  // Serial.print("Is Calibrated: ");
  // Serial.println(isCalibrated ? "Yes" : "No");

  // Calculate weight based on calibration
  float val1 = ((float)offsetCorrected * (float)knownWeight);
  float val2 = ((float)calibrationValue - (float)zeroOffset);
  float weight = val1 /  val2;

  // Serial.print("val1: ");
  // Serial.println(val1);
  // Serial.print("val2: ");
  // Serial.println(val2);
  // Serial.print("weight: ");
  // Serial.println(weight);
  
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

  doc["zeroOffset"] = zeroOffset;
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

  doc["offsetCorrected"] = 0;
  doc["isCalibrated"] = isCalibrated;
  doc["knownWeight"] = knownWeight;
  doc["calibrationValue"] = calibrationValue;

  Serial.print("Using ");
  Serial.print(knownWeight);
  Serial.println(" kg as calibration weight");
}

// Reset calibration
void resetCalibration() {
  zeroOffset = 0;
  calibrationValue = 0;
  isCalibrated = false;
  // Serial.println("Calibration reset");
}


