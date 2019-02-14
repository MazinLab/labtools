#include <genieArduino.h>

#include <genieArduino.h>
Genie genie;
#define RESETLINE 4  // Change this if you are not using an Arduino Adaptor Shield Version 2 (see code below)
int ledPin = 13;                 // LED connected to digital pin 13

// the setup routine runs once when you press reset:
void setup() {

  pinMode(ledPin, OUTPUT);      // sets the digital pin as output
  
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  Serial1.begin(9600);
  genie.Begin(Serial1);
  genie.AttachEventHandler(myGenieEventHandler); // Attach the user function Event Handler for processing events
  
  Serial.println("Started Genie.");
  
  // Reset the Display (change D4 to D2 if you have original 4D Arduino Adaptor)
  // THIS IS IMPORTANT AND CAN PREVENT OUT OF SYNC ISSUES, SLOW SPEED RESPONSE ETC
  // If NOT using a 4D Arduino Adaptor, digitalWrites must be reversed as Display Reset is Active Low, and
  // the 4D Arduino Adaptors invert this signal so must be Active High.  
  pinMode(RESETLINE, OUTPUT);  // Set D4 on Arduino to Output (4D Arduino Adaptor V2 - Display Reset)
  digitalWrite(RESETLINE, 0);  // Reset the Display via D4
  delay(100);
  digitalWrite(RESETLINE, 1);  // unReset the Display via D4
  Serial.println("Reset Display.");

  delay (3500); //let the display start up after the reset (This is important)
  
  //Turn the Display on (Contrast) - (Not needed but illustrates how)
  genie.WriteContrast(12); // 1 = Display ON, 0 = Display OFF.
  Serial.println("Set Contrasts.");
  //For uLCD43, uLCD-70DT, and uLCD-35DT, use 0-15 for Brightness Control, where 0 = Display OFF, though to 15 = Max Brightness ON.

   //Write a string to the Display to show the version of the library used
  //genie.WriteStr(0, GENIE_VERSION);
  
  // set analog reference to external 2.048 V reference
  //analogReference(INTERNAL2V56); // use keyword EXTERNAL for external ref
  analogReference(EXTERNAL); // use keyword EXTERNAL for external ref

}

// the loop routine runs over and over again forever:
void loop() {
  // read the input on analog pin 0:
  unsigned int i;
  unsigned int sensorValue[16];
  unsigned int voltage[16];
  
  // read voltages
  sensorValue[0] = analogRead(A0);
  delay(1);
  sensorValue[1] = analogRead(A1);
  delay(1);
  sensorValue[2] = analogRead(A2);
  delay(1);
  sensorValue[3] = analogRead(A3);
  delay(1);
  sensorValue[4] = analogRead(A4);
  delay(1);
  sensorValue[5] = analogRead(A5);  
  delay(1);
  sensorValue[6] = analogRead(A6);
  delay(1);
  sensorValue[7] = analogRead(A7);  
  delay(1);
  sensorValue[8] = analogRead(A8);  
  delay(1);
  sensorValue[9] = analogRead(A9);
  delay(1);
  sensorValue[10] = analogRead(A10);
  delay(1);
  sensorValue[11] = analogRead(A11);  
  delay(1);
  sensorValue[12] = analogRead(A12);
  delay(1);
  sensorValue[13] = analogRead(A13);  
  delay(1);
  sensorValue[14] = analogRead(A14);  
  delay(1);
  sensorValue[15] = analogRead(A15);  
 
  // Convert the analog reading (which goes from 0 - 1023) to a voltage (0 - 5000 mV):
  for (i=0;i<15;i++) {
    voltage[i] = (unsigned int) sensorValue[i] * 2;
    if( voltage[i] > 9999) voltage[i]=9999;
    Serial.println(voltage[i]);      
    // write new voltage values to display
    //genie.WriteObject(GENIE_OBJ_CUSTOM_DIGITS, 0x00, voltage[i]);
    genie.WriteObject(GENIE_OBJ_CUSTOM_DIGITS, i, voltage[i]);
    delay(50);
  }
  
  // pause for 0.2 sec
  digitalWrite(ledPin, HIGH);   // sets the LED on
  Serial.println("LED goes HIGH"); 
  delay(100);
  Serial.println("LED goes LOW"); 
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

