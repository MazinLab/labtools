#include <genieArduino.h>
#include <Wire.h>
#include <Adafruit_ADS1015.h>

Adafruit_ADS1115 ads1115;	// construct an ads1115 at address 0x49

Genie genie;
#define RESETLINE 4  // Change this if you are not using an Arduino Adaptor Shield Version 2 (see code below)
int ledPin = 13;                 // LED connected to digital pin 13
int screenOnOffPin = 23;

// the setup routine runs once when you press reset:
void setup() {

  pinMode(ledPin, OUTPUT);      // sets the digital pin as output
  pinMode(46, OUTPUT);       //These are apparently VERY necessary!
  pinMode(47, OUTPUT);       //This shit tripped me up for the 
  pinMode(48, OUTPUT);       //better part of a day. 
  pinMode(49, OUTPUT);
  pinMode(50, OUTPUT);
  pinMode(51, OUTPUT);
  pinMode(51, OUTPUT);
  pinMode(53, OUTPUT);
  
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  Serial1.begin(9600);
  genie.Begin(Serial1);
  genie.AttachEventHandler(myGenieEventHandler); // Attach the user function Event Handler for processing events
  
  ads1115.begin();  // Initialize ads1115
  
  //Serial.println("Started Genie.");
  
  // Reset the Display (change D4 to D2 if you have original 4D Arduino Adaptor)
  // THIS IS IMPORTANT AND CAN PREVENT OUT OF SYNC ISSUES, SLOW SPEED RESPONSE ETC
  // If NOT using a 4D Arduino Adaptor, digitalWrites must be reversed as Display Reset is Active Low, and
  // the 4D Arduino Adaptors invert this signal so must be Active High.  
  pinMode(RESETLINE, OUTPUT);  // Set D4 on Arduino to Output (4D Arduino Adaptor V2 - Display Reset)
  digitalWrite(RESETLINE, 0);  // Reset the Display via D4
  delay(100);
  digitalWrite(RESETLINE, 1);  // unReset the Display via D4
  //Serial.println("Reset Display.");

  delay (3500); //let the display start up after the reset (This is important)
  
  //Turn the Display on (Contrast) - (Not needed but illustrates how)
  genie.WriteContrast(12); // 1 = Display ON, 0 = Display OFF.
  //Serial.println("Set Contrasts.");
  //For uLCD43, uLCD-70DT, and uLCD-35DT, use 0-15 for Brightness Control, where 0 = Display OFF, though to 15 = Max Brightness ON.
  unsigned int screenOn = 1;
  pinMode(screenOnOffPin, INPUT);




   //Write a string to the Display to show the version of the library used
  //genie.WriteStr(0, GENIE_VERSION);
  
  // set analog reference to external 2.048 V reference
  //analogReference(INTERNAL2V56); // use keyword EXTERNAL for external ref
  analogReference(EXTERNAL); // use keyword EXTERNAL for external ref

}

// the loop routine runs over and over again forever:
void loop() {
  // read the input on analog pin 0:
  unsigned int i = 3;
  unsigned int j = 4;
  unsigned int sensorValue[30];
  unsigned int voltage[30];
  
  
     // On the MUX, S0 is the least significant bit
   //Set up MUX1
   digitalWrite(47, HIGH && (i & B00000001));  //S0
   digitalWrite(49, HIGH && (i & B00000010));  //S1
   digitalWrite(51, HIGH && (i & B00000100));  //S2
   digitalWrite(53, HIGH && (i & B00001000));  //S3
   
   delay(50);
  
  
  
  int adc0 = 0,adc1 = 0,adc2 = 0,adc3 = 0;
  //ads1115.setGain(GAIN_ONE);     // 1x gain   +/- 4.096V  1 bit = 2mV
  ads1115.setGain(GAIN_TWO);     // 2x gain   +/- 2.048V  1 bit = 1mV
  // ads1115.setGain(GAIN_FOUR);    // 4x gain   +/- 1.024V  1 bit = 0.5mV
  // ads1115.setGain(GAIN_EIGHT);   // 8x gain   +/- 0.512V  1 bit = 0.25mV
  // ads1115.setGain(GAIN_SIXTEEN); // 16x gain  +/- 0.256V  1 bit = 0.125mV
  delay(10);
  //adc0 = ads1115.readADC_SingleEnded(0);
  delay(10);
  //adc1 = ads1115.readADC_SingleEnded(1);
  delay(10);
  //adc2 = ads1115.readADC_SingleEnded(2);
  delay(10);
  adc1 = ads1115.readADC_SingleEnded(3);
  //Serial.print("AIN0: "); 
  //Serial.println(adc3);
  //delay(100);
  //Serial.print("AIN2: "); Serial.println(adc2);
  
 
  delay(10);
  
  
  digitalWrite(47, HIGH && (j & B00000001));  //S0
  digitalWrite(49, HIGH && (j & B00000010));  //S1
  digitalWrite(51, HIGH && (j & B00000100));  //S2
  digitalWrite(53, HIGH && (j & B00001000));  //S3
   
  delay(50);
  
  
  ads1115.setGain(GAIN_ONE);     // 1x gain   +/- 4.096V  1 bit = 2mV
  //adc0 = ads1115.readADC_SingleEnded(0);
  delay(10);
  //adc1 = ads1115.readADC_SingleEnded(1);
  delay(10);
  //adc2 = ads1115.readADC_SingleEnded(2);
  delay(10);
  adc3 = ads1115.readADC_SingleEnded(3);
  //Serial.print("AIN0: "); 
  //Serial.println(adc3);
  //delay(100);
  //Serial.print("AIN2: "); Serial.println(adc2);
  
  Serial.print(adc0);
  Serial.print(",");
  Serial.print(adc1);
  Serial.print(",");
  Serial.print(adc2);
  Serial.print(",");
  Serial.println(adc3);
  
  
  for (int jj = 0;jj<30;jj++){
    voltage[jj] = 0;
    sensorValue[jj] = 0;
  }

  
  int screenOn = digitalRead(screenOnOffPin); //this is 1 or 0
  if (screenOn == 1){
    genie.WriteContrast(12); // 12 = Display ON, 0 = Display OFF.
  }
  else{
    genie.WriteContrast(0); // 12 = Display ON, 0 = Display OFF.
  }
  
 
  
 
  
  // pause for 0.2 sec
  digitalWrite(ledPin, HIGH);   // sets the LED on
  //Serial.println("LED goes HIGH"); 
  delay(100);
  //Serial.println("LED goes LOW"); 
  digitalWrite(ledPin, LOW);   // sets the LED on
}

void myGenieEventHandler(void)
{
  genieFrame Event;
  genie.DequeueEvent(&Event);

  int slider_val = 0;

  //If the cmd received is from a Reported Event (Events triggered from the Events tab of Workshop4 objects)
  if (Event.reportObject.cmd == GENIE_REPORT_EVENT)
  {
    if (Event.reportObject.object == GENIE_OBJ_SLIDER)                // If the Reported Message was from a Slider
    {
      if (Event.reportObject.index == 0)                              // If Slider0
      {
        slider_val = genie.GetEventData(&Event);                      // Receive the event data from the Slider0
        genie.WriteObject(GENIE_OBJ_LED_DIGITS, 0x00, slider_val);    // Write Slider0 value to to LED Digits 0
      }
    }
  }

  //If the cmd received is from a Reported Object, which occurs if a Read Object (genie.ReadOject) is requested in the main code, reply processed here.
  if (Event.reportObject.cmd == GENIE_REPORT_OBJ)
  {
    if (Event.reportObject.object == GENIE_OBJ_USER_LED)              // If the Reported Message was from a User LED
    {
      if (Event.reportObject.index == 0)                              // If UserLed0
      {
        bool UserLed0_val = genie.GetEventData(&Event);               // Receive the event data from the UserLed0
        UserLed0_val = !UserLed0_val;                                 // Toggle the state of the User LED Variable
        genie.WriteObject(GENIE_OBJ_USER_LED, 0x00, UserLed0_val);    // Write UserLed0_val value back to to UserLed0
      }
    }
  }

  //This can be expanded as more objects are added that need to be captured

  //Event.reportObject.cmd is used to determine the command of that event, such as an reported event
  //Event.reportObject.object is used to determine the object type, such as a Slider
  //Event.reportObject.index is used to determine the index of the object, such as Slider0
  //genie.GetEventData(&Event) us used to save the data from the Event, into a variable.
}

