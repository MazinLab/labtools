/*
This code is for interfacing between the control PC
(the DARKNESS computer) and the wavecal box 

arduino pin      laser diode PCB controller pin 
---------------------------------------
5V                5V
GND               GND
4                 808nm
5                 904nm
6                 980nm
3                 1120nm
2                 1310nm

7                 Mirror flip control
*/


#include <SPI.h>         // needed for Arduino versions later than 0018
#include <Ethernet.h>
#include <EthernetUdp.h>         // UDP library from: bjoern@cs.stanford.edu 12/30/2008

// Enter a MAC address and IP address for your controller below.
// The IP address will be dependent on your local network:
byte mac[] = { 0x90, 0xA2, 0xDA, 0x10, 0x40, 0x1F };                //MEC arduino
//IPAddress ip(10, 0, 0, 55); // old 10 10 10 12 
//IPAddress ip(10, 10, 10, 12);
//byte dnss[] = { 0xDE, 0xAD, 0xBE, 0xEF };
//byte subnet[] = {255,255,255,0};
//IPAddress gateway(10, 10, 10, 1); // old 10 10 10 1

// palomar
IPAddress ip(10, 200, 130, 7);
byte dnss[] = { 0xDE, 0xAD, 0xBE, 0xEF };
byte subnet[] = {255,255,0,0};
IPAddress gateway(10, 200, 1, 129); // old 10 10 10 1

unsigned int localPort = 8888;      // local port to listen on

// buffers for receiving and sending data
char packetBuffer[UDP_TX_PACKET_MAX_SIZE]; //buffer to hold incoming packet, 
char ReplyBuffer[] = "Arduino received switch signal";       // a string to send back

// An EthernetUDP instance to let us send and receive packets over UDP
EthernetUDP Udp;

char incomingByte = 0;   // for incoming serial data
int pin_mirror = 7;
int pin808 = 4; // pin 4 and 6 are swapped since location of 808 and 980 LDs were switched
int pin904 = 5;
int pin980 = 6;
int pin1120 =3;
int pin1310 =8;

int names[] = {
  pin_mirror, 808, 904, 980, 1120, 1310
};

int pins[] = {
  7, 4,5,6,3,8
};

int udpDelay = 50;  // ms

void setup() {
  // put your setup code here, to run once:
  Ethernet.begin(mac, ip, dnss, gateway, subnet);
  Udp.begin(localPort);
  
  pinMode(pin_mirror, OUTPUT);
  pinMode(pin808, OUTPUT);  
  pinMode(pin904, OUTPUT); 
  pinMode(pin980, OUTPUT);  
  pinMode(pin1120, OUTPUT); 
  pinMode(pin1310, OUTPUT);  
  
  Serial.begin(9600);
}

void loop() {
    /*digitalWrite(pins[0], HIGH);   // turn the LED on (HIGH is the voltage level)
    delay(500);              // wait for a second
    digitalWrite(pins[0], LOW);    // turn the LED off by making the voltage LOW
    delay(500);              // wait for a second
    
    digitalWrite(pins[1], HIGH);   // turn the LED on (HIGH is the voltage level)
    delay(500);              // wait for a second
    digitalWrite(pins[1], LOW);    // turn the LED off by making the voltage LOW
    delay(500);              // wait for a second
    
    digitalWrite(pins[2], HIGH);   // turn the LED on (HIGH is the voltage level)
    delay(500);              // wait for a second
    digitalWrite(pins[2], LOW);    // turn the LED off by making the voltage LOW
    delay(500);              // wait for a second
    */
  
  // put your main code here, to run repeatedly:
  int packetSize = Udp.parsePacket();
  if (packetSize)
  {
    Serial.print("Received packet of size ");
    Serial.println(packetSize);
    Serial.print("From ");
    IPAddress remote = Udp.remoteIP();
    for (int i = 0; i < 4; i++)
    {
      Serial.print(remote[i], DEC);
      if (i < 3)
      {
        Serial.print(".");
      }
    }
    Serial.print(", port ");
    Serial.println(Udp.remotePort());
  
        //clear packetBuffer
    packetBuffer[0] = '\0';
    // read the packet into packetBufffer
    Udp.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);
    Serial.println("Contents: ");
    
    // read the incoming byte:
    incomingByte = packetBuffer[0]; //packetBuffer is a char*, or an array of chars

    // send a reply, to the IP address and port that sent us the packet we received
    //Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
    //Udp.write(ReplyBuffer);
    //Udp.endPacket();
    
    Serial.print(packetBuffer);
    Serial.print("\n");
    
    for (int i = 0; i < 6; i++)
    {
      if (packetBuffer[i]=='1'){
        char HighBuffer[20];
        sprintf(HighBuffer,"setting %i pin high", names[i]);
        Serial.println(HighBuffer);
        //Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
        //Udp.write("1 hello");
        //Udp.endPacket();
        digitalWrite(pins[i],HIGH);
        delay(50);
      }
      else {
        char LowBuffer[20];
        sprintf(LowBuffer,"setting %i pin low", names[i]);
        Serial.println(LowBuffer);
        //Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
        //Udp.write("0 lol");
        //Udp.endPacket();
        digitalWrite(pins[i],LOW);
        delay(50);
      } 
    } 
    Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
    Serial.print("writing packetBuffer to UDP\n");
    Serial.print(packetBuffer); 
    Serial.print("\n\n\n");   
    Udp.write(packetBuffer);
    Udp.endPacket();
  }
  delay(10);
}
