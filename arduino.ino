/*********************************************************************
 * Slave arduino : Testing LED blinking in Grand DOME
 * With a Serial communication I2C
 * ____________
 * |            |                    _________
 * |            |    -----SDA-----  | Arduino |
 * |   RASP     |    -----SCL-----  |pro mini |
 * |            |
 * --------------
 */

#include <Wire.h>
#include <microdome.h>


// ----- Parameters -----
int dataReceived, receivedParameters, dataSent;

#define PIN_DS_DATA A0
#define PIN_STCP_LATCH 7
#define PIN_SHCP_CLOCK 8

#define ledDim 10
#define OE 6
#define clrIo 4

// OUTPUTs tools xD
#define LED_R A1
#define LED_G A2
#define LED_B A3
#define LED_1 5
#define Buzzer 9

//// MicroDome
#define dataIn A0
int intensity = 255;
#define numbOfTiles 35
int nb_led_per_tile = 3;
int num_LEDs = numbOfTiles * nb_led_per_tile;
MicroDome dome(numbOfTiles, dataIn, RUL);

void setup() {

  pinMode(PIN_DS_DATA, OUTPUT);
  pinMode(PIN_STCP_LATCH, OUTPUT);
  pinMode(PIN_SHCP_CLOCK, OUTPUT);

  pinMode(clrIo, OUTPUT);
  pinMode(ledDim, OUTPUT);
  pinMode(OE, OUTPUT);

  pinMode(LED_R, OUTPUT);
  pinMode(LED_G, OUTPUT);
  pinMode(LED_B, OUTPUT);
  pinMode(LED_1, OUTPUT);
  pinMode(Buzzer, OUTPUT);

  dome.begin();

  Wire.begin(0x44); // Adress of Device !
  Wire.onReceive(receiveLong);
  Wire.onRequest(sendLong); 
  
  analogWrite(ledDim, 75);   // Turn LEDs ON with 75/255 ~ 30%
  digitalWrite(OE, 0);
  all_off();
  turnAllOff(); 

  triColor(500); 
  buzzer(2000); 
  delay(50);
  noBuzzer();
}

void loop() {
  delay(10);
}

//-------------------------------------------------------------------------

void receiveLong(int) {

  int bytes[sizeof(int)];
  int pbytes[sizeof(int)]; // pbytes refers to parameters


  while (Wire.available()) {

    dataReceived = Wire.read();
    receivedParameters = Wire.read();

    if (dataReceived == 1) {

      digitalWrite(PIN_STCP_LATCH, 0);
      all_off();
      digitalWrite(PIN_STCP_LATCH, 1);

      turnAllOff(); 

    }

    ////// Using OutPut Enable
    if (dataReceived == 2) {

      digitalWrite(PIN_STCP_LATCH, 0);
      brightness_with_ledDim(receivedParameters);
      delay(50);
      all_on();
      digitalWrite(PIN_STCP_LATCH, 1);
      int md_intens = receivedParameters;
      int intens_map = map(md_intens, 0, 35, 0, 20);
      allOn_md(intens_map);

    }

    ////// For micro Dome :: Turn Tile ON
    if (dataReceived == 6) {
       turn_tile_on(receivedParameters, 150);
    }


    if (dataReceived == 3) {
      int gd_indx = receivedParameters;
      int md_indx = receivedParameters;
      allumer_led_x_md(md_indx);
      allume_led_x(gd_indx);
    }

    if (dataReceived == 5) {
      clrIO();
    }

    if (dataReceived == 8) {
      buzzer(receivedParameters);
    }
    if (dataReceived == 80) {
      noBuzzer();
    }

    if (dataReceived == 9) {
      triColor(receivedParameters);
    }

    if (dataReceived == 10) {
      led_1_On(receivedParameters); //  
    }

    if (dataReceived == 0) {
      external_off(); //  OFF
    }

    if (dataReceived == 11){ // rouge
      displayColor(1, 0, 0);
    }
    
    if (dataReceived == 12){ // Vert
      displayColor(0, 1, 0);
    }

    if (dataReceived == 13){ // Blue
      displayColor(0, 0, 1);
    }

 
  }

}

void sendLong() {
  /*
  int pinFrom = RTC; 
  byte dataToSend; 
  dataToSend = digitalRead(pinFrom);
  dataSent = pinFrom; */ 
  dataSent = dataReceived ;// return what was recieved --- just to test !!
  byte bytes[sizeof(long)];

  for (int j = 0; j < sizeof(long); ++j)
    bytes[j] = dataSent >> 8 * j;
  Wire.write(bytes, sizeof(long));


}

//--------------------------------------------------------------

void allume_led_x(int x) {
  
  analogWrite(ledDim, 75);
  int tabled[] = {
    1, 2, 4, 8, 16, 32, 64, 128  };
  digitalWrite(PIN_STCP_LATCH, LOW);
  int bras = x / 8; // shift register
  for (int k = bras + 1; k < 20; k++)
  {
    shiftOut(PIN_DS_DATA, PIN_SHCP_CLOCK, MSBFIRST, B00000000);
  }
  int led = tabled[x % 8];
  shiftOut(PIN_DS_DATA, PIN_SHCP_CLOCK, MSBFIRST, led);

  for (int j = 0; j < bras; j++)
  {
    shiftOut(PIN_DS_DATA, PIN_SHCP_CLOCK, MSBFIRST, B00000000);
  }
  digitalWrite(PIN_STCP_LATCH, HIGH);
}

void all_on() {

  //digitalWrite(ledDim, 1);
  digitalWrite(clrIo, 1);
  for (int k = 0; k < 20; k++) {
    shiftOut(PIN_DS_DATA, PIN_SHCP_CLOCK, MSBFIRST, 0xFF);
  }
}

void all_off() {

  digitalWrite(ledDim, 0);
  digitalWrite(clrIo, 1);
  for (int k = 0; k < 20; k++) {
    shiftOut(PIN_DS_DATA, PIN_SHCP_CLOCK, MSBFIRST, 0b00000000);
  }

}

void brightness(int brightness) {
  // digitalWrite(ledDim, 0);
  // analogWrite(OE, brightness);
  digitalWrite(OE, 1);
}

void brightness_with_ledDim(int brightness) {
  digitalWrite(OE, 0);
  if (brightness > 150)
  {
    analogWrite(ledDim, 150);
  }
  else{
    analogWrite(ledDim, brightness);
  }

}

void clrIO() {
  digitalWrite(clrIo, 0);
}


void buzzer(int sound){
  tone(Buzzer, sound, 100); 
}

void noBuzzer(){
  noTone(Buzzer);
}


void displayColor(byte r, byte g, byte b) {
  digitalWrite(LED_R, r);
  digitalWrite(LED_G, g);
  digitalWrite(LED_B, b);
}

void triColor(int freq){
  displayColor(1, 0, 0);
  delay(freq);
  displayColor(0, 1, 0);
  delay(freq);
  displayColor(0, 0, 1);
  delay(freq);
  displayColor(0, 0, 0);
}

void clignoter(){
  for (int i=0; i<10; i++){
  displayColor(0, 0, 1);
  delay(200);
  }
}

void external_off(){
  displayColor(0, 0, 0);
  led_1_On(0);
}

void led_1_On(int state){
  if (state == 0){
  digitalWrite(LED_1, LOW);
  }
  if (state == 1){
  digitalWrite(LED_1, HIGH);
  }
}


////////////////// MICRO DOME /////////////////
///////// Allumer toutes les LEDs ///////
void allOn_md(int intens) {
       dome.clear();
  if (intens < 100) {
    for (int i = 0; i <= numbOfTiles; i++) {
      dome.setTile(i, dome.setLedLevels(intens, intens, intens));
      dome.show();
    }
  }
  else {
    for (int i = 0; i <= numbOfTiles; i++) {
      dome.setTile(i, dome.setLedLevels(75, 75, 75));
      dome.show();
    }
  }
  dome.clear();

}


///////////////// Allumer une LEDs par tuile ! //////
void led_by_tile() {
  dome.clear();
  for (int i = 0; i <= numbOfTiles; i++) {
    dome.setTile(i, dome.setLedLevels(0, intensity, 0));
    dome.show();
  }
  dome.clear();
}


void turn_tile_on(int tile, int intens) {
  dome.clear();
  dome.setTile(tile, dome.setLedLevels(intens, intens, intens));
  dome.show();
  dome.clear();
}


void turnAllOff() {
  dome.clear();
  dome.setLedLevels(0, 0, 0);
  for (int i = 0; i <= numbOfTiles; i++) {
    dome.setTile(i, dome.setLedLevels(0, 0, 0));
    dome.show();
  }
  dome.clear();
}


void allumer_led_x_md(int x) {
  dome.clear();
  dome.setLedLevels(0, 0, 0);
  if (x % 3 == 0) {
    dome.setTile((int)(x / nb_led_per_tile), dome.setLedLevels(intensity, 0, 0));
  }
  if (x % 3 == 1) {
    dome.setTile((int)(x / nb_led_per_tile), dome.setLedLevels(0, intensity, 0));
  }
  if (x % 3 == 2) {
    dome.setTile((int)(x / nb_led_per_tile), dome.setLedLevels(0, 0, intensity));
  }
  dome.show();
  dome.clear();
}
