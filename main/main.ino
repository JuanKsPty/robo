#include <AFMotor.h>

AF_DCMotor motorA(4);
AF_DCMotor motorB(3);

int motorA1 = 33;
int motorA2 = 34;
int motorApwm = 35;

int motorB1 = 38;
int motorB2 = 37;
int motorBpwm = 14;

int servoAPin = 0;
int servoBPin = 0;

int echoPin = 0;
int triggerPin = 0;

int buzzerPin = A0;

String directionLeft = "RELEASE";
String directionRight = "RELEASE";
int xy = 0;
boolean rescueFlag = false;
int MOTORSPEED = 70;
int SENSITIVITY = 60;

int directions[] = {RELEASE,FORWARD,BACKWARD};

int obstacleCnt = 0;
float origin; //save absolute orientation in which the robot is aligned with the walls in the rescue area
String readString;

String getValue(String data, char separator, int index) { //returns ints from mutliple Strings seperated by a character
	int found = 0;
	int strIndex[] = { 0, -1 };
	int maxIndex = data.length() - 1;

	for (int i = 0; i <= maxIndex && found <= index; i++) {
			if (data.charAt(i) == separator || i == maxIndex) {
					found++;
					strIndex[0] = strIndex[1] + 1;
					strIndex[1] = (i == maxIndex) ? i+1 : i;
			}
	}
	return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}

void setup() {
	Serial.begin(9600);
  
	pinMode(24, INPUT_PULLUP);
	pinMode(buzzerPin, OUTPUT);
	pinMode(13, OUTPUT);
	
	pinMode(motorA1, OUTPUT);
	pinMode(motorA2, OUTPUT);
	pinMode(motorApwm, OUTPUT);
	pinMode(motorB1, OUTPUT);
	pinMode(motorB2, OUTPUT);
	pinMode(motorBpwm, OUTPUT);



	//Gyrosensor
	
	//distance sensor
	
	

	/*
	while (distanceAvg() > 50) {
		delay(1);
	}
	*/
 //loosen rope
	delay(700);


	//while(distanceAvg() > 100) {}

}


void turnGreen(bool left) {

	int angle = 0;
	while(true) {
		if(angle >= 60) return;
		while(Serial.available() > 0) {
			char c = Serial.read();
			if(c == 'G') {
				beep(100);
			
				break;
			}
		}
		angle += 5;
		
		delay(100);
	}
}

void loop() {
	readString = "";

	while (Serial.available()) { //receive data from raspi
		delay(4);
		if (Serial.available() > 0) {
			char c = Serial.read();
			readString += c;
		}
	}

	if (readString != "") {
		Serial.println(readString);
		if (readString == "R") {
		
			drive(255, 255, 800);
			turnGreen(false);
			drive(-255, -255, 250);
			drive(255, 255, 1);
		
		} if (readString == "L") {
	
			drive(255, 255, 800);
			//turnRelative(-75);
			turnGreen(true);
			drive(-255, -255, 250);
			drive(255, 255, 1);
		 
		} if (readString == "A") {
			drive(0, 0, 0);
			drive(0, 0, 0);
			beep(100);
		
			
			drive(-255, -255, 50);
			drive(0, 0, 0);
			
		
		} if (readString.indexOf("E") != -1) {
			drive(0, 0, 0);
			beep(100);
			
			drive(150, 150, 200);
			drive(0, 0, 0);
		} if (readString.indexOf("RK") != -1) {
			drive(0, 0, 0);
			beep(1000);
			String incomingString = "";
			while (true) {
				if (Serial.available() > 0) {
					incomingString = Serial.readString();
					//incomingString.trim();
          String xval = getValue(incomingString, ':', 0);
					String yval = getValue(incomingString, ':', 1);
					String zval = getValue(incomingString, ':', 2);
          
					int motorleft = xval.toInt();
					int motorright = yval.toInt();
					int duration = zval.toInt();   
					pln(incomingString);

					if(incomingString == "grabRescueKit") {
						
						drive(-200, -200, 50);
						drive(0, 0, 0);
					
						drive(200, 200, 100);
						drive(0, 0, 0);
					
						drive(-200, -200, 100);
						drive(0, 0, 0);
						break;
					} else if (incomingString == "armUp") {
						drive(0, 0, 0);
						
						Serial.println(1);
					} else if (incomingString == "armDown") {
						drive(0, 0, 0);
						
						Serial.println(1);
					} else {
						/*
						p(motorleft);
						p("  ");
						p(motorright);
						pln("");
						*/
						if (motorleft == 0 && motorright == 0) {
							if (duration == 0) { //turn to origin

							} else {
							
								Serial.println(1);
							}
						} else {
							drive(motorleft, motorright, duration);
							drive(0, 0, 0);
							Serial.println(1);
						}
					}
				}
			}

		} if (readString == "I") {
			drive(255, 255, 550);
		} if (readString == "IR") {
			drive(0, 0, 0);
			
			drive(255, -255, 100);
			drive(255, 255, 550);
		} if (readString == "IL") {
			drive(0, 0, 0);
			
			drive(-255, 255, 100);
			drive(255, 255, 550);
		} if (readString == "D") {
			
			drive(255, 255, 300);
			     
			drive(-255, -255, 500);
			drive(255, 255, 1);
		} if (readString.indexOf("STOP") != -1) {
			drive(255, 255, 200);
			//loose rope
			drive(0, 0, 100000);
		} else if (readString.indexOf("S") != -1) {
			drive(255, 255, 400);
		} if (readString == "gapR") {
			drive(0, 0, 0);
			beep(50);
			drive(255, -255, 100);
			drive(0, 0, 0);
		} if (readString == "gapL") {
			drive(0, 0, 0);
			beep(50);
			drive(-255, 255, 100);
			drive(0, 0, 0);
		} if (readString == "Rescuekit") {
			beep(2000);
		}if (readString == "Rescue") { //Raspi says: there is the rescue area because he did not see a line for 10 frames
			drive(0, 0, 0);
			
			/*if (rescueFlag == false && distanceAvg() < 2000 && distanceAvg() > 500) { //checks if distance fits
				drive(0, 0, 0);
				led(1, 0, 0);
				Serial2.println("8"); //sends a 8 to the raspi to verify the entrance of the evacuation zone
				rescue();
			} else {
				drive(0, 0, 0);
				led(0, 0, 1);
				Serial2.println(6); //sends a 6 because there can't be the rescue area
			}*/
		} else {
			String newReadString = "";
			for(int i = 0; i < readString.length(); i++) {
				char c = readString[i];
				if(c == '-' || c == '.' || c == '0' || c == '1' || 
					c == '2' || c == '3' || c == '4' || c == '5' ||
					c == '6' || c == '7' || c == '8' || c == '9') {
					newReadString += c;
				}
			}

			//Linefollowing
			int x = newReadString.toInt();

			if (x < 200 && x > -200) {

				int motorSpeedL = MOTORSPEED + x * SENSITIVITY;
				int motorSpeedR = MOTORSPEED - x * SENSITIVITY;

				
			}
		}
	}
	
	//obstacle();
}

void beep(int duration) {
	digitalWrite(buzzerPin, HIGH);
	delay(duration);
	digitalWrite(buzzerPin, LOW);
}

void drive(int left, int right, int duration) {
	int directionLeft = 0;
  int directionRight = 0;
	if(duration < 0) {
		int h = left;
		left = right;
		right = h;
		duration *= -1;
	}
	if (left > 0) {
		directionLeft = 1;
	}
	else if (left == 0) {
		directionLeft = 0;
	}
	else{
		directionLeft = 2;
	}
	if (right > 0) {
		directionRight = 1;
	}
	else if (right == 0) {
		directionRight = 0;
	}
	else{
		directionRight = 2;
	}
	if (right > 255) {
		right = 255;
	}
	if (right < -255) {
		right = -255;
	}
	if (left > 255) {
		left = 255;
	}
	if (left < -255) {
		left = -255;
	}
	
	motorA.run(directions[directionLeft]);
	motorB.run(directions[directionRight]);
	/*
	digitalWrite(motorA1, left < 0 ? HIGH : LOW);
	digitalWrite(motorA2, left <= 0 ? LOW : HIGH);

	digitalWrite(motorB1, right < 0 ? HIGH : LOW);
	digitalWrite(motorB2, right <= 0 ? LOW : HIGH);

	analogWrite(motorApwm, abs(left));
	analogWrite(motorBpwm, abs(right));
	*/
  motorA.setSpeed(abs(left));
  motorB.setSpeed(abs(right));
	
	delay(duration);
  


}

/*
void turnAbsolute(float pos) {	
	if (pos > getXOrientation()) {
		while (getXOrientation() < pos - 2.0) {
			drive(130, -130, 0);
		}
	} else {
		while (getXOrientation() > pos + 2.0) {
			drive(-130, 130, 0);
		}
	}
	drive(0, 0, 0);
}
*/



//Symbol of programmers lazyness:
inline void p(String txt) {
	Serial.print(txt);
}

inline void pln(String txt) {
	Serial.println(txt);
}


void debug(bool statement) {
	if (statement) {
		//debug everything

		//laser sensor front:
		Serial.print("Distance: ");
		
		Serial.print("mm");
	}
}

	
	



