/*
This code is for interfacing between the control PC
(the DARKNESS computer) and the heat switch box from
HPD.

arduino pin      heat switch controller pin 
---------------------------------------
8               9
9                2
GND              11
2                scope trigger


For debugging, use labview vi "arduino_udp_test.vi" to send characters over UDP

*/


#include <SPI.h>         // needed for Arduino versions later than 0018
#include <Ethernet.h>
#include <EthernetUdp.h>         // UDP library from: bjoern@cs.stanford.edu 12/30/2008

// Enter a MAC address and IP address for your controller below.
// The IP address will be dependent on your local network:
byte mac[] = {
  0x90, 0xA2, 0xDA, 0x10, 0x40, 0x49                //DARKNESS arduino
};
//byte mac[] = {
//  0x90, 0xA2, 0xDA, 0x10, 0x40, 0x1F                  //wavecal arduino
//};
//IPAddress ip(10, 200, 130, 3);   // ip for Palomar
IPAddress ip(10, 10, 10, 11);     // ip for black lab
byte dnss[] = {
  0xDE, 0xAD, 0xBE, 0xEF
};

//byte subnet[] = {255,255,0,0};  // Palomar
byte subnet[] = {255,255,255,0};   // black lab

//IPAddress gateway(10, 200, 1, 129); // Palomar
IPAddress gateway(10, 10, 10, 1);  // black lab


unsigned int localPort = 8888;      // local port to listen on

// buffers for receiving and sending data
char packetBuffer[UDP_TX_PACKET_MAX_SIZE]; //buffer to hold incoming packet,
char  ReplyBuffer[] = "acknowledged";       // a string to send back

// An EthernetUDP instance to let us send and receive packets over UDP
EthernetUDP Udp;

char incomingByte = 0;   // for incoming serial data
int openPin = 9;
int closePin = 8;

int udpDelay = 50;  // ms

void setup() {
  
    // start the Ethernet and UDP:
  Ethernet.begin(mac, ip, dnss, gateway, subnet);
  Udp.begin(localPort);
  
  // initialize digital pin 13 as an output.

  pinMode(closePin, OUTPUT);  //close heat switch, "c"
  pinMode(openPin, OUTPUT);  //open heat switch, "o"
  Serial.begin(9600);
}

// the loop function runs over and over again forever
void loop() {
  // if there's data available, read a packet
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
    Serial.println("Contents:");
    Serial.println(packetBuffer);
    
    // read the incoming byte:
    incomingByte = packetBuffer[0]; //packetBuffer is a char*, or an array of chars

    // send a reply, to the IP address and port that sent us the packet we received
    //Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
    //Udp.write(ReplyBuffer);
    //Udp.endPacket();

  
    if (incomingByte==99){
      Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
      Udp.write("arduino received CLOSE signal");
      Udp.endPacket();
      digitalWrite(closePin,HIGH);
      delay(50);
      digitalWrite(closePin,LOW);
      delay(udpDelay);
      }
    if (incomingByte==111){
      Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
      Udp.write("arduino received OPEN signal");
      Udp.endPacket();
      digitalWrite(openPin,HIGH);
      delay(50);
      digitalWrite(openPin,LOW);
      delay(udpDelay);
      }
    if (incomingByte==73){
      Serial.write("arduino says hello world!\r\n");
      delay(udpDelay);
      Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
      Udp.write("arduino says hello world!\r\n");
      Udp.endPacket();
      }
  }
  delay(10);


}

