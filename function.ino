void serialReading() {
  // Check if there is serial data available to read
  if (Serial.available() > 0) {
    // Read the incoming value from the serial port
    String data = Serial.readStringUntil('\n');
    data.trim();
    if (data == "TIMEOUT#") {
      timeout();
    } else {
      int hashIndex = data.indexOf('#');
      if (hashIndex != -1) {
        beep(2, 100, 100);
        // Extract the condition and accuracy from the data
        String condition = data.substring(0, hashIndex);
        float accuracy = data.substring(hashIndex + 1).toFloat();

        sortir(condition, accuracy);
        classification_state = 0;
      }
    }
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("-Pemisah Tomat-");
  }
} //baca data serial dari raspberry

void sortir(String condition, float accuracy) {
  // Print the parsed values for testing
  if (dbg_mode) {
    Serial.print("Condition: ");
    Serial.println(condition);
    Serial.print("Accuracy: ");
    Serial.println(accuracy);
    Serial.println();
  }
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(condition);
  lcd.setCursor(0, 1);
  lcd.print(accuracy);
  lcd.print("%");
  delay(1000);
  // Check the value and assign the corresponding state
  if (condition == "damaged") {
    all_count++;
    damaged_count++;
    if (dbg_mode) {
      Serial.println("Damaged");
    }
    sortirServo.write(angles[0]);
    delay(100);
    analogWrite(plusMotor, 130);
    digitalWrite(minMotor, 0);
    delay(1000);
    
    startServo.write(starts[0]);
    delay(servoOpenDelay);
    startServo.write(starts[1]);
    
    delay(conveyorDelay);
    digitalWrite(plusMotor, 0);
    digitalWrite(minMotor, 0);
  } else if (condition == "old") {
    all_count++;
    old_count++;
    if (dbg_mode) {
      Serial.println("Old");
    }
    sortirServo.write(angles[1]);
    delay(100);
    analogWrite(plusMotor, 130);
    digitalWrite(minMotor, 0);
    delay(1000);
    
    startServo.write(starts[0]);
    delay(servoOpenDelay);
    startServo.write(starts[1]);
    
    delay(conveyorDelay);
    digitalWrite(plusMotor, 0);
    digitalWrite(minMotor, 0);
  } else if (condition == "ripe") {
    all_count++;
    ripe_count++;
    if (dbg_mode) {
      Serial.println("Ripe");
    }
    sortirServo.write(angles[2]);
    delay(100);
    analogWrite(plusMotor, 130);
    digitalWrite(minMotor, 0);
    delay(1000);
    
    startServo.write(starts[0]);
    delay(servoOpenDelay);
    startServo.write(starts[1]);
    
    delay(conveyorDelay);
    digitalWrite(plusMotor, 0);
    digitalWrite(minMotor, 0);
  } else if (condition == "unripe") {
    all_count++;
    unripe_count++;
    if (dbg_mode) {
      Serial.println("Unripe");
    }
    sortirServo.write(angles[3]);
    delay(100);
    analogWrite(plusMotor, 130);
    digitalWrite(minMotor, 0);
    delay(1000);
    
    startServo.write(starts[0]);
    delay(servoOpenDelay);
    startServo.write(starts[1]);
    
    delay(conveyorDelay);
    digitalWrite(plusMotor, 0);
    digitalWrite(minMotor, 0);
  } else {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Data Tidak");
    lcd.setCursor(0, 1);
    lcd.print("Sesuai");
    delay(3000);
  }
} //Proses sortir

void timeout() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("----TIMEOUT----");
  beep(1, 1000, 0);
  lcd.setCursor(0, 0);
  lcd.print("  Please Check  ");
  lcd.setCursor(0, 1);
  lcd.print("  Your Server.  ");
  delay(1000);
  classification_state = 0;
} //Pengetesan raspberry apabila raspberry tidak merespon 

void beep(byte interval, int wait1, int wait2) {
  for (byte times = 0; times < interval; times++) {
    digitalWrite(buzzer, 1);
    delay(wait1);
    digitalWrite(buzzer, 0);
    delay(wait2);
  }
} //
