
#include <Wire.h>
#include <VL53L0X.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>
#include <AFMotor.h>

AF_DCMotor motorA(4)
AF_DCMotor motorB(3)

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


int xy = 0;
boolean rescueFlag = false;
int MOTORSPEED = 70;
int SENSITIVITY = 60;

int obstacleCnt = 0;
float origin; //save absolute orientation in which the robot is aligned with the walls in the rescue area
String readString;

void setup() {
	Serial.begin(9600);
	if (!bno.begin())  {
		Serial.print("Ooops, no BNO055 detected ... Check your wiring or I2C ADDR!");
		//while (1);
		beep(1000);
	}

}

void turnGreen(bool left) {
	turnRelative(left ? -10 : 10);
	int angle = 0;
	while(true) {
		if(angle >= 60) return;
		while(Serial.available() > 0) {
			char c = Serial.read();
			if(c == 'G') {
				beep(100);
				turnRelative(left ? -30 : 30);
				break;
			}
		}
		angle += 5;
		turnRelative(left ? -5 : 5);
		delay(100);
	}
}

void loop() {
	readString = "";

	while (Serial.available()) { //receive data from raspi
		delay(4);
		if (Serial.available() > 0) {
			char c = Serial2.read();
			readString += c;
		}
	}

	if (readString != "") {
		Serial.println(readString);
		if (readString == "R") {
			led(0, 0, 0);
			drive(255, 255, 800);
			turnGreen(false);
			drive(-255, -255, 250);
			drive(255, 255, 1);
			led(0, 0, 0);
		} if (readString == "L") {
			led(1, 0, 0);
			drive(255, 255, 800);
			//turnRelative(-75);
			turnGreen(true);
			drive(-255, -255, 250);
			drive(255, 255, 1);
			led(0, 0, 0);   
		} if (readString == "A") {
			drive(0, 0, 0);
			drive(0, 0, 0);
			beep(100);
			turnRelative(-15);
			turnRelative(180);
			drive(-255, -255, 50);
			drive(0, 0, 0);
			armDown();
			armUp();
			turnRelative(180);
			turnRelative(20);
		} if (readString.indexOf("E") != -1) {
			drive(0, 0, 0);
			beep(100);
			turnRelative(-70);
			drive(150, 150, 200);
			drive(0, 0, 0);
		} if (readString.indexOf("RK") != -1) {
			drive(0, 0, 0);
			beep(1000);
			String incomingString = "";
			while (true) {
				if (Serial2.available() > 0) {
					incomingString = Serial2.readString();
					//incomingString.trim();
					String xval = getValue(incomingString, ':', 0);
					String yval = getValue(incomingString, ':', 1);
					String zval = getValue(incomingString, ':', 2);
					int motorleft = xval.toInt();
					int motorright = yval.toInt();
					int duration = zval.toInt();   
					pln(incomingString);

					if(incomingString == "grabRescueKit") {
						turnRelative(180);
						drive(-200, -200, 50);
						drive(0, 0, 0);
						armDown();
						armUp();
						drive(200, 200, 100);
						drive(0, 0, 0);
						turnRelative(180);
						drive(-200, -200, 100);
						drive(0, 0, 0);
						break;
					} else if (incomingString == "armUp") {
						drive(0, 0, 0);
						armUp();
						Serial2.println(1);
					} else if (incomingString == "armDown") {
						drive(0, 0, 0);
						armDown();
						Serial2.println(1);
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
								turnRelative(duration);
								Serial2.println(1);
							}
						} else {
							drive(motorleft, motorright, duration);
							drive(0, 0, 0);
							Serial2.println(1);
						}
					}
				}
			}

		} if (readString == "I") {
			drive(255, 255, 550);
		} if (readString == "IR") {
			drive(0, 0, 0);
			led(1, 0, 0);
			drive(255, -255, 100);
			drive(255, 255, 550);
		} if (readString == "IL") {
			drive(0, 0, 0);
			led(0, 0, 1);
			drive(-255, 255, 100);
			drive(255, 255, 550);
		} if (readString == "D") {
			led(1, 1, 1);
			drive(255, 255, 300);
			turnRelative(180);      
			drive(-255, -255, 500);
			drive(255, 255, 1);
		} if (readString.indexOf("STOP") != -1) {
			drive(255, 255, 200);
			servoString.write(180); //loose rope
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
			led(1, 0, 1);
			if (rescueFlag == false && distanceAvg() < 2000 && distanceAvg() > 500) { //checks if distance fits
				drive(0, 0, 0);
				led(1, 0, 0);
				Serial2.println("8"); //sends a 8 to the raspi to verify the entrance of the evacuation zone
				rescue();
			} else {
				drive(0, 0, 0);
				led(0, 0, 1);
				Serial2.println(6); //sends a 6 because there can't be the rescue area
			}
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

				if (getYOrientation() > 15.00) {   
					drive(motorSpeedL * 1.5, motorSpeedR * 1.5, 0); 
				} else if (getYOrientation() < -15.00) {
					drive(motorSpeedL * 0.5, motorSpeedR * 0.5, 0);
				} else {
					drive(motorSpeedL, motorSpeedR, 0);					
				}
			}
		}
	}
	obstacle3();
	//obstacle();
}

void beep(int duration) {
	digitalWrite(buzzerPin, HIGH);
	delay(duration);
	digitalWrite(buzzerPin, LOW);
}

void drive(int left, int right, int duration) {

	if(duration < 0) {
		int h = left;
		left = right;
		right = h;
		duration *= -1;
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
	
	motorA.run(FORWARD)
	digitalWrite(motorA1, left < 0 ? HIGH : LOW);
	digitalWrite(motorA2, left <= 0 ? LOW : HIGH);

	digitalWrite(motorB1, right < 0 ? HIGH : LOW);
	digitalWrite(motorB2, right <= 0 ? LOW : HIGH);

	analogWrite(motorApwm, abs(left));
	analogWrite(motorBpwm, abs(right));

	delay(duration);
}

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

void turnRelative(float deg) {
	float startPos = getXOrientation();
	float endPos = startPos + deg - 2; //calculate end pos, but substrac 2 degs because the motors usually turn a bit to long


	//weird code follows to rotate the robot
	if (deg >= 0.0) {
		//p("startPos: ");
		//p(startPos);
		//p("endPos: ");
		//p(endPos);
		if (startPos >= 0.0 && startPos <=  182) {
			while (getXOrientation() < endPos) {
				drive(130, -130, 0);
			}
		} else {
			if (endPos < 359.9999) {
				while (getXOrientation() < endPos) {
					drive(130, -130, 0);
				}
			} else {
				while (getXOrientation() > 1.0) {
					drive(130, -130, 0);
				}
				endPos = endPos - 360.0;
				while (getXOrientation() < endPos) {
					drive(130, -130, 0);
				}
			}
		}
		drive(-130, 130, 40);
	} else {
		if (startPos >= 0 && startPos < 182) {
			if (endPos >= 0.0) {
				while (getXOrientation() > endPos) {
					drive(-130, 130, 0);
				}
			} else {
				while (getXOrientation() < 359.0) {
					drive(-130, 130, 0);
				}
				endPos = endPos + 360;
				while (getXOrientation() > endPos) {
					drive(-130, 130, 0);
				}
			}
		} else {
			while (getXOrientation() > endPos) {
				drive(-130, 130, 0);
			}
		}
		drive(130, -130, 40);
	}
	drive(0, 0, 0);
}


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
		Serial.print(distance());
		Serial.print("mm");
	}
}

void obstacle2() {
	if (distance() < 50) {
		if (distance() < 60) { //double check distance
			if (distance() < 60) {
				drive(0, 0, 0);
				led(1, 1, 1);
				drive(-255, -255, 200);
				turnRelative(-50);
				drive(255, 255, 200);
				for (int i = 0; i < 12; i++) {
					drive(255, 255, 80);
					turnRelative(10);
				}
				drive(0, 0, 500);
				drive(255, 255, 300);
				turnRelative(-38);
				drive(-255, -255, 200);
				drive(0, 0, 0);
				obstacleCnt++;
			}
		}
	}
}

void obstacle3() {
	int sign = 1;
	if (distance() < 50) {
		if (distance() < 60) { //double check distance
			if (distance() < 60) {
				drive(0, 0, 0);
				led(1, 1, 1);
				drive(-255, -255, 150);
				turnRelative(-50);

				if(distanceAvg() < 300) {
					turnRelative(110);
					sign *= -1;
					//drive(255, 255, 120);
				}

				drive(255, 255, 200);
				Serial2.println("O");
				while (1) {
					drive(255, 255, 50);
					drive(0, 0, 0);
					delay(200);
					//turnRelative(10 * sign);
					drive(255, -255, 90 * sign);
					drive(0, 0, 0);
					readString = "";
					while (Serial2.available() > 0) {
						//delay(4);
						char c = Serial2.read();
						readString += c;
					}

					if (readString.indexOf("O") != -1) {
						//Linie gefunden
						drive(0, 0, 0);
						beep(1000);
						drive(255, 255, 550);
						turnRelative(-50 * sign);
						drive(-255, -255, 200);
						Serial2.println("Found Line");
						return;
					}
				}
			}
		}
	}	
}

void obstacle() {
	if (distance() < 50) {
		if (distance() < 60) { //double check distance
			if (distance() < 60) {
				drive(0, 0, 0);
				led(1, 1, 1);
				beep(50);
				drive(-150, -150, 120);
				turnRelative(-55);
				drive(255, 255, 50);
				int x = 200;
				Serial2.flush();
				beep(50);
				drive(0, 0, 0);
				delay(1000);
				led(0, 0, 0);
				/*while (Serial2.available()) { //hängt sich in dieser loop auf Fehlercode: jdhjkdfhg
					delay(4);
					Serial.read();
					digitalWrite(ledRedPin, HIGH);
					}*/
				digitalWrite(ledRedPin, LOW);

				bool a = false;

				while (abs(x) == 0 || abs(x) > 3) {
					readString = "";

					Serial2.flush();
					delay(5);

					while (Serial2.available()) {
						delay(4);
						if (Serial2.available() > 0) {
							char c = Serial2.read();
							readString += c;
						}
					}

					if (readString != "") {
						x = readString.toInt();
					} else {
						x = 0;
					}
					//drive(255, 30, 0);
					turnRelative(15);
					drive(150, 255, 10);
					a = -a;
				}
				led(0, 1, 0);
				drive(255, 255, 300);
				//drive(-255, 255, 500);
				turnRelative(-50);
				drive(-255, -255, 200);
				drive(0, 0, 0);
				beep(50);
			}
			led(0, 0, 0);
		}
	}
}
/*
//following fuction does the same as turnToOrigin, but using the laser distance sensor -> no longer used because inaccurate
void ausrichten() {
	bool ungerade = true;
	int last = distanceAvg();
	drive(150, -150, 200);
	drive(0, 0, 0);
	int current = distanceAvg();
	if (current < last) {
		while (ungerade) {
			led(1, 1, 1);
			last = distanceAvg();
			drive(150, -150, 50);
			drive(0, 0, 0);
			current = distanceAvg();
			delay(100);
			Serial.print("last: ");
			Serial.print(last);
			Serial.print("  ");
			Serial.print("current: ");
			Serial.print(current);
			Serial.print("  ");
			if (current > last) {
				beep(50);
				drive(0, 0, 0);
				led(0, 0, 0);
				drive(-255, -255, 3000);
				drive(0, 0, 0);
				delay(100000);
				//ungerade = false;
				//break;
			}
		}
	}
}
*/
void rescue() {
	drive(0, 0, 0);
	beep(20);
	boolean rescue = true;
	while (rescue) {
		if (Serial2.available() > 0) {
			String incomingString = Serial2.readString();
			//incomingString.trim();
			String xval = getValue(incomingString, ':', 0);
			String yval = getValue(incomingString, ':', 1);
			String zval = getValue(incomingString, ':', 2);
			int motorleft = xval.toInt();
			int motorright = yval.toInt();
			int duration = zval.toInt();   
			pln(incomingString);

			if(incomingString == "dist") {
				int di = distanceAvg();
				Serial2.println(String(di));
			} else if (incomingString == "drop") {
				drive(0, 0, 0);
				drop();
				Serial2.println(1);
			} else if (incomingString == "grabVictim") {
				turnRelative(180);
				drive(-200, -200, 50);
				drive(0, 0, 0);
				armDown();
				armUp();
				drive(200, 200, 100);
				drive(0, 0, 0);
				turnRelative(180);
				drive(-200, -200, 100);
				drive(0, 0, 0);
				Serial2.println(1);
			} else if (incomingString == "armUp") {
				drive(0, 0, 0);
				armUp();
				Serial2.println(1);
			} else if (incomingString == "armDown") {
				drive(0, 0, 0);
				armDown();
				Serial2.println(1);
			} else if (incomingString == "setOrigin") {
				origin = getXOrientation();
				beep(50);
				p("origin set to: ");
				p(origin);
				pln("");
				Serial2.println(1);
			} else if (incomingString == "turnToOrigin") {
				turnAbsolute(origin);
				Serial2.println(1);
			} else if(incomingString == "driveToWall") {
				drive(255, 255, 0);
				while(distanceAvg() > 100) {
					if (Serial2.available() > 0) {
						String incomingString = Serial2.readString();

						if(incomingString == "C") {
							break;
						}
						led(0, 1, 0);
					}
				}

				drive(0, 0, 0);
				delay(100);
				Serial2.println(1);
				beep(500);
			} else if (incomingString == "exit") {
				drive(0, 0, 10);
				Serial2.println(1);
				return;
			} else if (incomingString == "driveToBlackCornerAndSaveVictim") {
				turnRelative(90);
				while (distanceAvg() > 170) {
					drive(255, 255, 0);
					led(0, 0, 1);
				}
				turnRelative(90);
				while (distanceAvg() > 400) {
					drive(255, 255, 0);
					led(0, 0, 1);
				}
				turnRelative(45);
				drive(255, 255, 400);
				turnRelative(90);
				drive(-255, -255, 500);
				drive(0, 0, 0);
				armHalfDown();
				armUp();
				drive(255, 255, 1000);

				turnAbsolute(origin);
				Serial2.println(1);
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
						turnRelative(duration);
						Serial2.println(1);
					}
				} else {
					drive(motorleft, motorright, duration);
					drive(0, 0, 0);
					Serial2.println(1);
				}
			}
		}
	}
}

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

void led(int green, int yellow, int red) {
	digitalWrite(ledGreenPin, constrain(green, 0, 1));
	digitalWrite(ledYellowPin, constrain(yellow, 0, 1));
	digitalWrite(ledRedPin, constrain(red, 0, 1));
}