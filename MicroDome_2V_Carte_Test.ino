//Programme de carte de test.
//Lorsqu'on pose une tuile, la carte de test
#include <microdome.h>

#include <Adafruit_NeoPixel.h>

#define led_r 3
#define led_g 5
#define led_b 6
#define runbutton 2
#define test 8
#define data_out 9
#define tile_in 7


uint8_t nbtiles = 2;

bool toggle = true;
int delayblink = 2000;
long previousmillis = 0;

Adafruit_NeoPixel pixels(nbtiles, tile_in, NEO_GRB + NEO_KHZ800);
//MicroDome mc(nbtiles, tile_in);

void setup() {

  pinMode(led_r, OUTPUT);
  pinMode(led_g, OUTPUT);
  pinMode(led_b, OUTPUT);
  // pinMode(data_out, INPUT);
  pinMode(tile_in, OUTPUT);
  pinMode(test, INPUT);
  pinMode(runbutton, INPUT);
  //mc.clear();
  flash();
  pixels.begin(); // INITIALIZE NeoPixel strip object (REQUIRED)

  pixels.setPixelColor(0, pixels.Color(0, 0, 0));
  pixels.setPixelColor(1, pixels.Color(0, 0, 0));
}

void loop() {

  while (!digitalRead(runbutton)) {
    digitalWrite(led_b, 0);
    digitalWrite(led_g, 0);
    digitalWrite(led_r, 1);

    pixels.setPixelColor(0, pixels.Color(255, 255, 255));
    pixels.setPixelColor(1, pixels.Color(255, 255, 255));
    pixels.show();
    delay(50);
    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
    pixels.setPixelColor(1, pixels.Color(0, 0, 0));
    pixels.show();
    /*
      for (int i = 0; i < nbtiles * 3; i++) {
      mc.setLed(i, 255);
      mc.update();
      delay(100);
      }
      mc.clear();*/
  }
  while (!digitalRead(test)) {
    // mc.clear();
    digitalWrite(led_r, 0);
    digitalWrite(led_g, 1);
    pixels.setPixelColor(1, pixels.Color(0, 75, 0));
    for (int i = 0; i < 3 ; i++) {
      pixels.setPixelColor(0, pixels.Color(75, 0, 0));
      pixels.show();   // Send the updated pixel colors to the hardware.
      delay(150);
      pixels.setPixelColor(0, pixels.Color(0, 75, 0));
      pixels.show();   // Send the updated pixel colors to the hardware.
      delay(150);
      pixels.setPixelColor(0, pixels.Color(0, 0, 75));
      pixels.show();   // Send the updated pixel colors to the hardware.
      delay(150);
    }
    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
    pixels.show();
    delay(200);
    pixels.setPixelColor(1, pixels.Color(75, 75, 75));
    for (int j = 0; j < 255; j++) {
      pixels.setPixelColor(0, j, j, j);
      pixels.show();
      delay(2);
    }
    for (int j = 255; j > 0; j--) {
      pixels.setPixelColor(0, j, j, j);
      pixels.show();
      delay(2);
    }
    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
    pixels.setPixelColor(1, pixels.Color(0, 0, 0));
    pixels.show();
    delay(200);
    /*
      /*
      for (int i = 0; i < nbtiles * 3; i++) {
       mc.setLed(i, 255);
       mc.update();
      delay(100);
      }
      mc.clear();*/
  }
  ledRGBupdate();
}

void ledRGBupdate() {
  digitalWrite(led_g, 0);
  digitalWrite(led_r, 0);
  digitalWrite(led_b, 0);
  if ((millis() - previousmillis) > delayblink) {
    flash();
    previousmillis = millis();
    /*
      pixels.setPixelColor(0, pixels.Color(0, 0, 0));
      pixels.show();   // Send the updated pixel colors to the hardware.
      toggle = !toggle;
      digitalWrite(led_b, toggle);
    */
  }
}

void flash() {
  for (int i = 0; i < 3 ; i++) {
    digitalWrite(led_b, 1);
    delay(50);
    digitalWrite(led_b, 0);
    delay(50);
  }

}
