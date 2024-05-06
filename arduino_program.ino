#include <Wire.h> 
/*  #include <Wire.h>: Mendeklarasikan penggunaan pustaka Wire, yang digunakan untuk komunikasi melalui 
protokol I2C (Inter-Integrated Circuit). Pustaka ini umumnya digunakan untuk berkomunikasi antar 
mikrokontroler dan perangkat I2C, seperti sensor, modul, atau tampilan.*/

#include <Servo.h>
/*  #include <Servo.h>: Mendeklarasikan penggunaan pustaka Servo, yang memudahkan pengendalian 
motor servo pada Arduino. Pustaka ini memberikan fungsi-fungsi yang mempermudah dalam menggerakkan 
motor servo ke posisi tertentu.*/

#include <LiquidCrystal_I2C.h>
/*  #include <LiquidCrystal_I2C.h>: Mendeklarasikan penggunaan pustaka LiquidCrystal_I2C, 
yang digunakan untuk mengendalikan tampilan LCD berbasis I2C. Pustaka ini menyederhanakan penggunaan 
LCD pada proyek Arduino dengan menggunakan komunikasi I2C.*/

#define buzzer 13
/*7.  #define buzzer 13: Membuat alias dengan nama buzzer yang setara dengan nilai 13. Ini digunakan 
 * untuk memberi nama yang lebih deskriptif terhadap nomor pin yang digunakan untuk mengendalikan buzzer.
 * 
*/
#define startServoPin 5
#define sortirServoPin 3
#define plusMotor 2
#define minMotor 4
#define irPin 10

LiquidCrystal_I2C lcd(0x27, 16, 2);
Servo startServo;
Servo sortirServo;

const int conveyorDelay = 2000;
const int servoOpenDelay = 220;

int all_count;
int damaged_count, old_count, ripe_count, unripe_count = 0;
int starts[] = {0, 90}; //servo pendorong
int angles[] = {55, 85, 145, 175};  //servo pemilah
int lcd_count;  //mengatur penggantian informasi dari lcd
unsigned long lcd_times, ir_times;  //Pergantian waktu tampilan lcd
bool dbg_mode = 0;

unsigned long classification_times;
bool classification_state = 0;

void setup() {
  Serial.begin(115200);
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Memulai program");

  pinMode(buzzer, OUTPUT);
  pinMode(plusMotor, OUTPUT);
  pinMode(minMotor, OUTPUT);
  pinMode(irPin, INPUT_PULLUP);

  startServo.attach(startServoPin);
  sortirServo.attach(sortirServoPin);

  digitalWrite(plusMotor, 0);
  digitalWrite(minMotor, 0);
  startServo.write(starts[1]);
  sortirServo.write(angles[1]);
  delay(1000);
  lcd.clear();
  lcd.print("-Pemisah Tomat-");
  if (dbg_mode) {
    Serial.println("program ready to use");
  }
  beep(2, 100, 100);
}

void loop() {
  serialReading();
  if (!digitalRead(irPin)) {
    ir_times = millis();
    while (millis() - ir_times < 2000UL) {
      delay(10);
    }
    if (!classification_state) {
      classification_times = millis();
      classification_state = 1;
      if (!digitalRead(irPin)) {
        beep(2, 100, 100);
        Serial.println("detected#");
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("TOMATO DETECTED");
        delay(1000);
      }
    }
  }

  if (classification_state) {
    if (millis() -  classification_times >= 120000UL) {
      timeout();
    }
  }

  if (millis() - lcd_times > 3000UL) {
    lcd_times = millis();
    lcd_count++;
    if (lcd_count > 4) {
      lcd_count = 0;
    }
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("-Pemisah Tomat-");
  }

  if (lcd_count == 0) {
    lcd.setCursor(0, 1);
    lcd.print("All Count:");
    lcd.print(all_count);
  } else if (lcd_count == 1) {
    lcd.setCursor(0, 1);
    lcd.print("Damaged:");
    lcd.print(damaged_count);
  } else if (lcd_count == 2) {
    lcd.setCursor(0, 1);
    lcd.print("Old:");
    lcd.print(old_count);
  } else if (lcd_count == 3) {
    lcd.setCursor(0, 1);
    lcd.print("Ripe:");
    lcd.print(ripe_count);
  } else if (lcd_count == 4) {
    lcd.setCursor(0, 1);
    lcd.print("Unripe:");
    lcd.print(unripe_count);
  }
}
