#include <genieArduino.h>
#include <Wire.h>
#include <Adafruit_ADS1015.h>
#include <Servo.h>

Servo hemtServo;  // Servo to control HEMTs OFF/ON/CHARGE
int pos=0;

Adafruit_ADS1115 ads1115_0(0x48);	// construct an ads1115 at address 0x48
Adafruit_ADS1115 ads1115_1(0x49);  // construct an ads1115 at address 0x49
int adc00, adc02;
int adc1_val=0;

Genie genie;
#define RESETLINE 4  // Change this if you are not using an Arduino Adaptor Shield Version 2 (see code below)
int ledPin = 13;                 // LED connected to digital pin 13
int screenOnOffPin = 23;

unsigned int j;
unsigned int nValues = 30;
float adcToVolt = 0.580;
int incomingByte = 0;
int hemtBiases[32];
int muxIndex = -1;
boolean muxEnabled=false;
boolean relaySet = true;
boolean readHEMTs = true;
boolean screenOn = false;
boolean oldScreenOnValue = false;

String s="";


// the setup routine runs once when you press reset:
void setup() {

  pinMode(ledPin, OUTPUT);      // sets the digital pin as output
  pinMode(33, OUTPUT);   //relay 1 set
  pinMode(35, OUTPUT);   //relay 1 reset
  pinMode(37, OUTPUT);   //relay 2 set 
  pinMode(39, OUTPUT);   //relay 2 reset
  pinMode(41, OUTPUT);   //relay 3 set
  pinMode(43, OUTPUT);   //relay 3 reset
  pinMode(47, OUTPUT);   //S2 of MUX
  pinMode(49, OUTPUT);   //S1 of MUX
  pinMode(51, OUTPUT);   //S0 of MUX
  pinMode(53, OUTPUT);   //EN of MUX
  
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);   //Computer communication over USB
  Serial.println("Starting MEC HEMT Power Supply Arduino Software. v0.7");
  Serial1.begin(9600);  //Front screen communication
  genie.Begin(Serial1);
  genie.AttachEventHandler(myGenieEventHandler); // Attach the user function Event Handler for processing events
  
  ads1115_0.begin();  // Initialize ads1115
  ads1115_1.begin();

  //hemtServo.attach(9);  // attaches the servo on pin 9 to the servo object
  
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
  pinMode(screenOnOffPin, INPUT);
  screenOn = digitalRead(screenOnOffPin);
  // 12 = Display ON, 0 = Display OFF.
  if (screenOn){genie.WriteContrast(12);}
  else {genie.WriteContrast(0);}
  oldScreenOnValue=screenOn;
  Serial.println("Set Contrasts.");
  //For uLCD43, uLCD-70DT, and uLCD-35DT, use 0-15 for Brightness Control, where 0 = Display OFF, though to 15 = Max Brightness ON.
  




   //Write a string to the Display to show the version of the library used
  //genie.WriteStr(0, GENIE_VERSION);
  
  // set analog reference to external 2.048 V reference
  //analogReference(INTERNAL2V56); // use keyword EXTERNAL for external ref
  analogReference(EXTERNAL); // use keyword EXTERNAL for external ref

  ads1115_1.setGain(GAIN_TWOTHIRDS);  // 2/3x gain +/- 6.144V  1 bit = 3mV (default)
  //ads1115_1.setGain(GAIN_ONE);     // 1x gain   +/- 4.096V  1 bit = 2mV
  //ads1115_1.setGain(GAIN_TWO);     // 2x gain   +/- 2.048V  1 bit = 1mV
  // ads1015.setGain(GAIN_FOUR);    // 4x gain   +/- 1.024V  1 bit = 0.5mV
  // ads1015.setGain(GAIN_EIGHT);   // 8x gain   +/- 0.512V  1 bit = 0.25mV
  // ads1015.setGain(GAIN_SIXTEEN); // 16x gain  +/- 0.256V  1 bit = 0.125mV


  ads1115_0.setGain(GAIN_SIXTEEN); // 16x gain  +/- 0.256V  1 bit = 0.125mV


  relaySet = true;
  resetRelay();    //Initialize with relays on mux board open

  Serial.println("Done Setup!");
  
}


void setRelay() {
  //return;
  //Closes the relays on the MUX board
  //This connects the grounds which may cause extra noise on the HEMTs
  if(!relaySet){
    digitalWrite(35,1);
    delay(50);
    digitalWrite(35,0);
    
    digitalWrite(39,1);
    delay(50);
    digitalWrite(39,0);
    
    digitalWrite(43,1);
    delay(50);
    digitalWrite(43,0);
    
    delay(1);
    relaySet=true;
  }
}
void resetRelay() {
  //return;
  //Open relays on the MUX board
  //This dissconnects HEMT bias boards from the Arduino ground (less noise?)
  //Can't read accurate hemt biases if the the grounds are floating
  if(relaySet){
    digitalWrite(33,1);
    delay(50);
    digitalWrite(33,0);
    
    digitalWrite(37,1);
    delay(50);
    digitalWrite(37,0);
    
    digitalWrite(41,1);
    delay(50);
    digitalWrite(41,0);

    delay(1);
    relaySet=false;
  }
}


void incrementMux() {
  muxIndex=(muxIndex+1)%8;
  // On the MUX, S0 is the least significant bit
  digitalWrite(47, HIGH && (muxIndex & B00000100));  //S2
  digitalWrite(49, HIGH && (muxIndex & B00000010));  //S1
  digitalWrite(51, HIGH && (muxIndex & B00000001));  //S0
  delay(1);
}
void enableMux() {
  if(!muxEnabled){
    digitalWrite(53, HIGH);  //EN
    muxEnabled=true;
  }
}
void disableMux() {
  if(muxEnabled){ //I assume the if conditional is faster than the digitalWrite()
    digitalWrite(53, LOW);
    muxEnabled=false;
  }
}


void readHemtBiases() {
  for (j = 0;j<4;j++){
    adc1_val = ads1115_1.readADC_SingleEnded(j);
    if(adc1_val < 0){adc1_val=0;}
    hemtBiases[muxIndex*4+j]=(unsigned int) adc1_val*adcToVolt;
    if(hemtBiases[muxIndex*4+j] > 65535){hemtBiases[muxIndex*4+j]=65535;}
  }
}

void readHemtBiases2() {  //For some reason this doesn't work
  for (j = 0;j<4;j++){
    adc1_val = max(0,ads1115_1.readADC_SingleEnded(j));
    hemtBiases[muxIndex*4+j] =min( 65535, (unsigned int) adc1_val*adcToVolt);
  }
}

void outputHemtBiases() {
  //format hemtBiases and output to println
  s="";
  for (j=0; j<nValues-1; j++){
    s+=hemtBiases[(j*4+2)%31];
    s+=",";
    //Serial.print(hemtBiases[(j*4+2)%31]);
    //Serial.print(",");
  }
  s+=hemtBiases[((nValues-1)*4+2)%31];
  Serial.println(s);
  //Serial.println(hemtBiases[((nValues-1)*4+2)%31]);
}

void showHemtBiases() {
  //write to genie the hemt biases
  genie.WriteObject(GENIE_OBJ_USER_LED, 0,1);  // turn on LED to indicate loop is running
  for (j = 0; j<nValues; j++){
    genie.WriteObject(GENIE_OBJ_CUSTOM_DIGITS, j, hemtBiases[(j*4+2)%31]);
  }
  genie.WriteObject(GENIE_OBJ_USER_LED, 0,0);
}
void showFakeHemtBiases() {
  //write 333 to the screen
  // write garbage voltage values to genie so user knows
  for (j = 0; j<nValues; j++){
    genie.WriteObject(GENIE_OBJ_CUSTOM_DIGITS, j, 333);
  }
}


void servoMove(int val) {
  //Move the servo to 0=OFF, 1=ON, 2=CHARGE
  if(val==0 || val==1 || val==2){
    hemtServo.attach(9);
    delay(15);
    pos = 180-val*40;
    hemtServo.write(pos);
    delay(15);
    hemtServo.detach();
    //Serial.print("Moved to ");
    //Serial.println(pos);
  }
}

void servoMovePos() {
  pos =0;
  while(Serial.available()>0){
    incomingByte = Serial.read();
    if (incomingByte == '\n') break;
    if (incomingByte == '\r') break;
    if (incomingByte == -1) break;
    pos*= 10;
    pos = ((incomingByte - 48) + pos);
  }
  hemtServo.attach(9);
  delay(15);
  //hemtServo.writeMicroseconds(pos);
  hemtServo.write(pos);
  delay(15);
  hemtServo.detach();
  //Serial.print("Moved to ");
  //Serial.println(pos);
}



/*Description of what this software is doing.
 * There are two ADCs. 
 *  ADC0 is reading out the magnet current and the flow meter
 *  ADC1 is reading out the HEMT voltages, of which there are 30.
 *  
 * Each ADC has four inputs, so when we measure a voltage with ADC0 input 0, we call it adc00, and a 
 *  voltage measured with ADC1 input 2 is called adc12. 
 *  
 * There are 10 HEMTs, each with 3 voltages: Vdrain, Vgate, and Idrain
 *  (I say that Idrain is a voltage because the ADC measures a voltage, and then we turn it into a current)
 *  We label the HEMTS with letters and numbers. There are 5 "A" HEMTs and 5 "B" HEMTs. The A HEMTs are on the 
 *  A cable, and the B HEMTs are on the B cable (see the MEC rack). 
 * 
 * Because there are 30 HEMT voltages to read out and only 4 ADC inputs, we also use some 8 channel multiplexers.
 * The MUXs have 4 control pins, which we call EN, SO, S1, and S2. (EN stands for enable which turns the MUX connection
 * on/off, and SO S1 and S2 are the 3 bits you need to switch between 8 channels. )
 * 
 * For convenience, I've illustrated the numbering scheme for voltage array with an indication of what HEMT each value 
 * corresponds to, and also what adc channel is reading out that particular voltage. 
 * 
 * index =   [ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]
 * voltage = [vd, id, vg, vd, id, vg, vd, id, vg, vd, id, vg, vd, id, vg, vd, id, vg, vd, id, vg, vd, id, vg, vd, id, vg, vd, id, vg]
 * adc#  =   [12, 12, 12, 12, 12, 12, 12, 12, 13, 13, 13, 13, 13, 13, 13, 10, 10, 10, 10, 10, 10, 10, 10, 11, 11, 11, 11, 11, 11, 11]
 * HEMT  =    |    A1    |    A2     |    A3     |    A4     |    A5     |    B1     |    B2     |    B3     |    B4     |    B5     |
 * MUX ctrl =[ 0,  1,  2,  3,  4,  5,  6,  7,  0,  1,  2,  3,  4,  5,  6,  0,  1,  2,  3,  4,  5,  6,  7,  0,  1,  2,  3,  4,  5,  6]
 * 
 * MUX ctrl = (index%15)%8
 *

 * Commands sent from LabView GUI:
 * 65="A" - Read HEMT biases from the ADC. Only updates the current 4 values the MUX is currently set to. 
 *          The next time this is called, it will update the next 4 bias values.
 * 118="v" - The read all HEMT values button on the GUI was clicked
 * 114="r" - We want the HEMT ground to be floating to improve noise 
 *           This is called automatically when the ramp down completes
 *           It's also called when the MUX relay is manually set to OPEN (on the GUI)
 * 115="s" - This is called when the MUX relay is manually set to CLOSED (on the GUI)
 *       If the screen is on, we'll start reading out the HEMT biases again and displaying them
 * 99="c" - gets the coolant flow rate and magnet current
 * 105="i" - Turn HEMT servo to OFF
 * 106="j" - Turn HEMT servo to ON
 * 107="k" - Turn HEMT servo to Charge
 */

// the loop routine runs over and over again forever:
void loop() {
  unsigned int i;
  //First Handle the inputs
  if(Serial.available()>0){incomingByte = Serial.read();}
  else{incomingByte = -1;}
  screenOn = digitalRead(screenOnOffPin);

  if(incomingByte==115){readHEMTs=true;}  //'s' Set relay command
  else if(incomingByte==114){             //'r' reset relay command. Also, ramping down indicator
    readHEMTs=false;
    if(screenOn){showFakeHemtBiases();}
    disableMux();
    resetRelay();
  }
  
  //If we've just flipped the screen on, then force the bias voltage to readout onto the screen
  if(screenOn && !oldScreenOnValue){readHEMTs=true;}
  
  //We need to grab hemt biases if screen is on, incomingByte is 65, or incomingByte is 118. 
  if(incomingByte==65 || incomingByte==118 || (screenOn && readHEMTs)) {
    setRelay();
    
    enableMux();
    readHemtBiases();
    
    if(incomingByte==65){outputHemtBiases();}    //short circuit here to make this command as fast as possible
    if(incomingByte==118 || readHEMTs){
      for (i = 0; i<8-1; i++){                  //loop through the other 7 MUX states and read the biases in
        incrementMux();
        readHemtBiases();
      }
      incrementMux();                           //the 8th incrementMux() sets it back to the original state
    }
    
    if(!readHEMTs){
      disableMux();
      resetRelay();
    }
    if(incomingByte==118){outputHemtBiases();}
    
    if(screenOn){showHemtBiases();}
    incrementMux();                              //Do this now so we're ready for next time a 65 command comes in
  }
  
  //If we've toggled the screen turn it on/off
  if (screenOn!=oldScreenOnValue){
    // 12 = Display ON, 0 = Display OFF.
    if (screenOn){genie.WriteContrast(12);}
    else{genie.WriteContrast(0);}
    oldScreenOnValue = screenOn;
  }

  if (incomingByte == 99){ //c
    //Read the magnet current and flow meter
    adc00 = ads1115_0.readADC_SingleEnded(0);
    adc02 = ads1115_0.readADC_SingleEnded(2);
    
    //print the magnet current and flow meter values
    s="";
    s+=adc00;
    s+=",";
    s+=adc02;
    Serial.println(s);
    //Serial.print(adc00);
    //Serial.print(",");
    //Serial.println(adc02);
  }
  else if(incomingByte==105 || incomingByte==106 || incomingByte==107){servoMove(incomingByte-105);}
  else if(incomingByte==108){servoMovePos();}
  
  // flash the onboard LED to show that loop is running. 
  digitalWrite(ledPin, HIGH);   // sets the LED on
  delay(10);
  digitalWrite(ledPin, LOW);   // sets the LED off
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

