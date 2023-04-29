#!/usr/bin/env python
# coding=utf-8

# To do:
# 
# Ecke und Ausgang RICHTIG finden und nicht premappen xD
# Nach dem Finden des Rescuekits richtig ausrichten und dann erst aufnehmen
# raspi kühler (aktiv)
# autostart von Linefollowerprogramm
# prüfen, ob auch wirklich eine Kugel aufgenommen wurde
# schnellere baudrate
# raspi übertakten
# Bei Lücke ein Stückchen in die richtige Richtung drehen (ein paar Werte, bevor weiß kam schauen, ob Linienpos rechts oder links war und dann ein Stück koriggieren)
# Dose umfahren und sich dabei nicht von anderen Linien irritieren lassen (neues ROI, ganz links am Kamerabild bzw. einfach alles rechts abschneiden)
# Silber erkennen verbessern
# Lebendes und totes Opfer unterscheiden

from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np
import time
import cv2
import serial
import random
import RPi.GPIO as GPIO


CUT = (0, 320, 140, 192)
CUT_GRN = (50, 270, 110, 192)
CUT_SILVER = (60, 280, 0, 120)
CUT_RESCUEKIT = (50, 270, 120, 170)
CUT_TOP = (120, 200, 60, 120) #extra cut for skip at intersections
CUT_OBSTACLE = (60, 300, 140, 192)

#ser = serial.Serial('/dev/ttyAMA0', 9600, timeout = 0.5) #establish serial connenction 

#while(not ser.is_open):
#	print("Waiting for Serial...")
#	time.sleep(0.1)
#print("Opened:", ser.name, "Arduino Uno") 

framesTotal = 0 #counter for frames
startTime = time.time() #for FPS calculation at the end of the program
timeWaitet = 0 #because a normal time.sleep in the loop would distort the FPS calculation, the program counts how long has been waited and subtracs it in the final calculation 
lastLinePos = 0 #were was the line in the last frame?
LinePosLastLoop = [0, 0, 0, 0, 0, 0, 0, 0]
lastA2 = 0
pCounter = 0
LineWidthLastLoop = 0
value = 0
gapcounter = 0 #gets increased if no line could be found in a frame
grn_list = []
grn_counter = 0
rescueCounter = 0
rescue = False
mindist = 300 #minRadius for victims
redCnt = 0 #counts how often red/rk has been detected. first time -> Rescuekit second time -> STOP
rescuekitCounter = 0
x = 0
y = 0
r = 0
obstacle = False

kp = .75
armUp = 1

ena = 21
enb = 18
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme

GPIO.setup(18, GPIO.OUT)
GPIO.setup(23, GPIO.OUT)
GPIO.setup(24, GPIO.OUT)

GPIO.setup(21, GPIO.OUT)
GPIO.setup(20, GPIO.OUT)
GPIO.setup(16, GPIO.OUT)

GPIO.output(21, GPIO.LOW)
GPIO.output(18, GPIO.LOW)

pwm_a = GPIO.PWM(ena,100)
pwm_b = GPIO.PWM(enb,100)
pwm_a.start(0)
pwm_b.start(0)


########## FUNCTIONS ##########

def DEBUG():
	cv2.imshow("image_rgb", image_rgb)
	cv2.imshow("image_hsv", image)
	cv2.imshow("cut", cut)
	cv2.imshow("cut_green", green)
	cv2.imshow("cut_silber", cut_silver)
	cv2.imshow("rescuekit", rescuekit)

	#cv2.imshow("Konturen gruen", green)
	cv2.setMouseCallback("mouseRGB", mouseRGB)
	cv2.imshow("mouseRGB", image_rgb)
	
def DEBUG_LastLinePos():
	for i in range(8):
		print(f'LinePosLastLoop[{i}] = {LinePosLastLoop[i]:5d}')

def mouseRGB(event, x, y, flags, param): #to adjust colour values eg for green dots
	if event == cv2.EVENT_LBUTTONDOWN: #checks mouse left button down condition
		colorsB = image_rgb[y, x, 0]
		colorsG = image_rgb[y, x, 1]
		colorsR = image_rgb[y, x, 2]
		colors = image_rgb[y, x]
		"""
		print("Red: ", colorsR)
		print("Green: ", colorsG)
		print("Blue: ", colorsB)
		print("BRG Format: ", colors)
		print("Coordinates of pixel: X: ", x,"Y: ", y)
		"""
		colour = np.uint8([[[colorsB, colorsG, colorsR]]])
		colour_hsv = cv2.cvtColor(colour, cv2.COLOR_BGR2HSV)
		print(colour_hsv)

def delay(duration):
	global timeWaitet
	duration = float(duration)
	time.sleep(duration)
	timeWaitet = timeWaitet + duration

def motorAF(power):
    if power < 0:
        power = power*-1
        pwm_a.ChangeDutyCycle(power)
        GPIO.output(20, GPIO.LOW)
        GPIO.output(16, GPIO.HIGH)
    pwm_a.ChangeDutyCycle(power)
    GPIO.output(20, GPIO.HIGH)
    GPIO.output(16, GPIO.LOW)
    return
    
def motorBF(power):
    if power < 0:
        power = power*-1
        pwm_b.ChangeDutyCycle(power)
        GPIO.output(24, GPIO.LOW)
        GPIO.output(13, GPIO.HIGH)
    pwm_b.ChangeDutyCycle(power)
    GPIO.output(23, GPIO.LOW)
    GPIO.output(24, GPIO.HIGH)
    return
    
    
def motorSteer(speed,steer):
    if steer == 0:
        motorAF(speed)
        motorBF(speed)
        return
    elif steer > 0:
        steer = 100 - steer
        motorAF(speed)
        motorBF(speed*steer/100)
        return
    elif steer < 0:
        steer = steer*-1
        steer = 100 - steer
        motorBF(speed)
        motorAF(speed*steer/100)
        return


def drive(motorLeft, motorRight, duration):
	motorAF(motorLeft)
	motorBF(motorRight)
	delay(duration)
	
def turnRelative(deg):
	drive(0, 0, deg)

#def distance():
	#ser.write(b"dist")
	#while True:
	#	readData = ser.readline().decode('ascii').rstrip()
	#	if readData != "":
	#		return int(readData) * 0.075
def toCornerUnload():
	camera = PiCamera()
	camera.resolution = (320, 180) 
	camera.rotation = 0
	camera.framerate = 32
	rawCapture = PiRGBArray(camera, size=(320, 180))

	for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
		image = frame.array
		image = cv2.GaussianBlur(image, ((5, 5)), 2, 2)

		black = cv2.inRange(image, (0, 0, 0), (255, 255, 75))
		#if(cv2.countNonZero(black) > 5000):
	#		sendAndWait("C")
		

		cv2.imshow("Corner out", image)
		rawCapture.truncate(0)
		key = cv2.waitKey(1) & 0xFF
		framesTotalRescue = framesTotalRescue + 1
		if key == ord("q"):
			print("Avg. FPS:", int(framesTotalRescue / (time.time()))) #sendet durchsch. Bilder pro Sekunde (FPS)
			camera.close()
			break

def findCorner(pIsWallRight):
	if pIsWallRight == True:
		#print("searching for corner with wall right")
		#sendAndWait("turnToOrigin")
		#ser.write(b'driveToWall')
		turnRelative(90)


	else:
		print("searching for corner with wall left")

def findExit(pIsWallRight): #find green strip in the evacuation zone
	"""
	time.sleep(0.5)
	print("1")
	camera = PiCamera()
	camera.resolution = (320, 180)
	camera.rotation = 0
	camera.framerate = 32
	rawCapture = PiRGBArray(camera, size=(320, 180))
	print("2")
	"""
	# Ausgang
	drive(-255, -255, 500)
	turnRelative(-90)
	drive(200, 200, 200)
"""
	if pIsWallRight == True:
		print("searching for exit with wall right")
		for i in range(3):
			drive(255, 255, 200)
		#camera.close()
		sendAndWait("exit")
		return
	else:
		print("searching for exit with wall left")
		return
"""
"""
		for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
			print("3")			
			image = frame.array
			image = image[50:270][50:192]           
			image_rgb = image
			image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV) #convert brg to hsv
			image = cv2.GaussianBlur(image, ((15, 15)), 2, 2)
			green = cv2.inRange(image, (30, 20, 20), (100, 255, 255))
			contours_grn, hierarchy_grn = cv2.findContours(green.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
			
			print(len(contours_grn))
			if(len(contours_grn) > 0):
				cv2.imshow("Exit", image_rgb)
				cv2.putText(image_rgb, "Exit", (110, 60), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 106, 255), 3)
				drive(130, 130, 900)
				drive(150, 0, 300)
				camera.close()
				cv2.destroyAllWindows()
				sendAndWait("exit")
				print("received exit")
				return
			else:
				drive(255, 255, 50)
			cv2.drawContours(image_rgb, contours_grn, -1, (0, 106, 255), 3)
			cv2.imshow("Exit", image_rgb)
			rawCapture.truncate(0)
			key = cv2.waitKey(1) & 0xFF
			if key == ord("q"):
				break
		"""

def capture():
	camera = PiCamera()
	camera.resolution = (320, 180) 
	camera.rotation = 0
	camera.framerate = 32
	time.sleep(0.5)

	rCapture = PiRGBArray(camera)

	camera.capture(rCapture, format="bgr")
	camera.close()

	return rCapture.array

def checkForCorner():
	image = capture()

	black = cv2.inRange(image, (0, 0, 0), (75, 75, 75))

	return cv2.countNonZero(black) > 10000

def checkForExit():
	image = capture()

	image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
	green = cv2.inRange(image, (52, 60, 48), (75, 255, 255)) # TODO: Werte anpassen

	return cv2.countNonZero(green) > 10000 # TODO: Wert anpassen

def rescueVictim():
	image = capture()	
	image = cv2.GaussianBlur(image, ((5, 5)), 2, 2)
	
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

	circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp = 1, minDist = 60, param1 = 34, param2 = 24, minRadius = 2, maxRadius = 300)

	if(circles is not None):
		circles = np.round(circles[0, :]).astype("int")
		if(len(circles) > 0):
			x, y, r = circles[0]

			x = int(x)
			y = int(y)

			pos = x - 160

			#cv2.rectangle(image_rgb, (x, y), (x + w, y + h), (50, 50, 200), 2)
			#cv2.putText(image_rgb, str(pos), (x, y + h + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (50, 50, 200), 2, cv2.LINE_AA)

			#cv2.imshow("image_rgb", image_rgb)

			movement = 0 # movement in motorspeed * milliseconds
			rotation = 0 # rotation in degrees

			if(y < 120):
				ms = (130 - y) * 1.5
				drive(180, 180, ms)
				movement = 180 * ms
			if(y > 150):
				drive(-130, -130, 30)
				movement = -130 * 30
			if(abs(pos) > 10):
				turnRelative(pos / 4)
				rotation = pos / 4
			if(155 > y > 115 and abs(pos) <= 10):
				#sendAndWait("grabVictim")
				return (2, movement, rotation)
			return (1, movement, rotation)

	return (0, 0, 0)

D_ONE_TILE = 1025

pwm_a = GPIO.PWM(ena,255)
pwm_b = GPIO.PWM(enb,255)
pwm_a.start(0)
pwm_b.start(0)

while True:
	camera = PiCamera()
	camera.resolution = (320, 192)
	camera.rotation = 0
	camera.framerate = 32
	rawCapture = PiRGBArray(camera, size=(320, 192))

	turningGreen = 0

	for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
		#if(ser.in_waiting != 0):
		#	s2 = ser.readline()
		#	print("TEENSY_DEBUG: " + str(s2))

		#if(ser.in_waiting != 0):
		#	s = str(ser.readline())
		#	print("TEENSY SAID: " + s)
		#	if("O" in s):
		#		obstacle = True
		#		print("OBSTACLE")

		image = frame.array
		image_rgb = image 

		image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV) # Konvertiert das Bild zum Christentum
		image = cv2.GaussianBlur(image, ((9, 9)), 2, 2)

		
		A = 30
		if (LinePosLastLoop[0] < -A or LinePosLastLoop[0] > A) and LineWidthLastLoop > 160:
			cut_top = image[CUT_TOP[2]:CUT_TOP[3],CUT_TOP[0]:CUT_TOP[1]]            
			cv2.imshow("cut_top", cut_top)
			#cv2.GaussianBlur(cut_top, ((9, 9)), 2, 2)

			line_top = cv2.inRange(cut_top, (0, 0, 0), (255, 255, 75))

			contours_top, hierarchy_top = cv2.findContours(line_top.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
			if(len(contours_top) > 0):
			#	ser.write(b'S')
				print("SKIP")
				delay(0.4)		
		cut = image[CUT[2]:CUT[3],CUT[0]:CUT[1]]
		cut_grn = image[CUT_GRN[2]:CUT_GRN[3],CUT_GRN[0]:CUT_GRN[1]] 
		cut_silver = image[CUT_SILVER[2]:CUT_SILVER[3],CUT_SILVER[0]:CUT_SILVER[1]]
		cut_rescuekit = image[CUT_GRN[2]:CUT_GRN[3],CUT_GRN[0]:CUT_GRN[1]]
		cut_stop = image[CUT_GRN[2]:CUT_GRN[3],CUT_GRN[0]:CUT_GRN[1]]

		if(turningGreen != 0):
			off = 0
			if(turningGreen == 1):
				off = -60
			else:
				off = 60

			cut_green_stop = image[120:192,(130 + off):(190 + off)]

			green_stop = cv2.inRange(cut_green_stop, (0, 0, 0), (255, 255, 75))
			#contours_green_stop, hierarchy_stop = cv2.findContours(stop.copy(),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

			cv2.rectangle(image_rgb, (130 + off, 120), (190 + off, 192), (0, 255, 0), 2)

			print(cv2.countNonZero(green_stop))
			if cv2.countNonZero(green_stop) > 300:	
				print("Finished turning Green")
				turningGreen = 0
				#ser.write(b'\nG\n')
				delay(0.2)
				#ser.write(b'G')
				#delay(0.2)
				cv2.putText(image_rgb, "Green end", (65, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 106, 255), 3)


		#cut_obstacle = image[CUT_OBSTACLE[0]:CUT_OBSTACLE[1],CUT_OBSTACLE[2]:CUT_OBSTACLE[3]]

		#cv2.GaussianBlur(cut_silver, ((9, 9)), 2, 2) #cut to detect silver

		line = cv2.inRange(cut, (0, 0, 0), (255, 255, 75))
		green = cv2.inRange(cut_grn, (52, 60, 48), (75, 255, 255))
		silber = cv2.inRange(cut_silver, (0, 0, 0), (255, 255, 75))
		rescuekit = cv2.inRange(cut_rescuekit, (119, 200, 25), (125, 255, 150))
		stop = cv2.inRange(cut_rescuekit, (165, 150, 100), (175, 255, 200))

		#obstacle = cv2.inRange(cut_obstacle, (0, 0, 0), (255, 255, 48))


		kernel = np.ones((4, 4), np.uint8)
		green = cv2.erode(green, kernel, iterations=3)
		green = cv2.dilate(green, kernel, iterations=5)

		contours_blk, hierarchy_blk = cv2.findContours(line.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
		contours_grn, hierarchy_grn = cv2.findContours(green.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
		contours_silver, hierarchy_silver = cv2.findContours(silber.copy(),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
		contours_rescuekit, hierarchy_rescuekit = cv2.findContours(rescuekit.copy(),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
		contours_stop, hierarchy_stop = cv2.findContours(stop.copy(),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
		#contours_obstacle, hierarchy_obstacle = cv2.findContours(obstacle.copy(),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

		#cv2.imshow("Obstacle", obstacle)

		
		linePos = 0
		index = 0
		#print("Len contours red:", len(contours_stop))

		#if len(contours_obstacle) > 0:	
		

					# drive(-200, -200, 50)
					# turnRelative(180)
					# drive(-200, -200, 85)
					# armDown()
					# armUp()

		
		### silverdetection: 
		
		
		if(len(contours_blk) > 0):
			if(len(contours_blk) > 4):
				if(len(contours_silver) == 0):
					print("detected silver")
					cv2.putText(image_rgb, "rescue", (65, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 106, 255), 3)
					#ser.write(b'Rescue') #sends "Rescue" to the teensy to prove the rescue area with the distance sensor
					
					#read_serial = ser.readline().decode('ascii') 
					read_serial = 0 #added for not delete
					if "8" in read_serial: #yep, the distance is between 80cm and 130cm 
						cv2.destroyAllWindows()
						camera.close()
						rescue()
						break
					else:
						print("Teensy said: there can't be the evacuation zone")
						#ser.write(str(0/10).encode())
						rescueCounter = 0

			nearest = 1000
			a1 = 0
			a2 = 0
			for i in range(len(contours_blk)):
				b = cv2.boundingRect(contours_blk[i])
				x, y, w, h = b
				a = int(abs(x + w / 2 - 160 - lastLinePos))
				if(len(contours_blk) == 2):
					if(a1 == 0):
						a1 = a
					else:
						a2 = a
				else:
					pCounter = 0

				cv2.rectangle(image_rgb, (x, y + CUT[2] + CUT[0]), (x + w, y + h + CUT[2] + CUT[0]), (0, 106, 255), 2) #rechteck um schwarze Konturen
				if(a < nearest):
					nearest = a
					index = i

			if not (a1 == nearest):
				a1, a2 = a2, a1

			if (abs(lastA2 - a1) > abs(a2 - a1)): # Zweite Kontur nähert sich der ersten an
				pCounter = pCounter + 1

				if(pCounter > 10) and (abs(a2 - a1) < 40):
					print("Ecke erkannt")
					pCounter = 0
					#ser.write(b'\nE\n')
			# else:
			# 	pCounter = 0

			lastA2 = a2
			#print(pCounter)
			#pCounter = pCounter - 1
			b = cv2.boundingRect(contours_blk[index])

			x, y, w, h = b
			#print(w)
			LineWidthLastLoop = w
			if(w > 210): #black contours is nearly as big as the whole width of the image -> there must be an intersection 
				pass
				#cv2.putText(image_rgb, "intersection", (65, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 106, 255), 3)
				#ser.write(b'\nS\n')
				#print("Send: Skipped")

			linePos = int(x + w / 2 - 160)
			cv2.putText(image_rgb, str(linePos),(linePos + 140, 70), cv2.FONT_HERSHEY_DUPLEX, 2, (0, 106, 255), 2)
			cv2.line(image_rgb, (linePos + 160, 80), (linePos + 160, 160), (255, 0, 0),2)
			cv2.line(image_rgb, (0, 110), (319, 110), (255, 0, 0), 2)
			lastLinePos = linePos
			
			motorSteer(20,(linePos*kp))
			# if(turningGreen == 1):
			# 	tg = abs(linePos + 10) < 30
			# elif(turningGreen == 2):
			# 	tg = abs(linePos - 10) < 30

			if(obstacle and abs(linePos - 20) < 40):
				print("OBSTACLE")
				obstacle = False
				#ser.write(b'\nO\n')
				cv2.putText(image_rgb, "Obstacle end", (65, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 106, 255), 3)
			
		contours_right = False
		contours_left = False   
		if(len(contours_grn) > 0 and len(contours_grn) < 3):
			if(grn_counter <= 0):
				grn_counter = 2
			else:
				if(grn_counter == 1):
					left = 0
					right = 0
					d = False
					s = 0
					for c in grn_list:
						if(c == "L"):
							left = left + 1
							print("L")
						elif(c == "R"):
							right = right + 1
							print("R")
						elif(c == "D"):
							d = True
							print("D")
						elif(c == "S"):
							s = s + 1
							print("S")
					if(d): #deadend
						#ser.write(b'D') 
						print("deadend") 
						print("Send: D")
						#delay(1)
					elif(s >= 6):
						#ser.write(b'S')
						#delay(0.2)
						print("Send: S")
					else:
						if(left > right):
							#ser.write(b'L')
							turningGreen = 1
							print("Send: L")
							delay(0.5)
						elif(right > left):
							#ser.write(b'R')
							turningGreen = 2
							print("Send: R")
							delay(0.5)
					grn_counter = 0
					grn_list.clear()
					#print("List cleared!")
					# for c in grn_list:
					#   print(c)
			check = True
			for i in range(len(contours_blk)):
					b = cv2.boundingRect(contours_blk[index])
					x, y, w, h = b
					if(w > 1000):
						grn_list.append("S")
						check = False

			if(check):
				for i in range(len(contours_grn)):
					b = cv2.boundingRect(contours_grn[i])
					x, y, w, h = b
					cv2.rectangle(image_rgb, (x, y + CUT_GRN[2] + CUT_GRN[0]), (x + w, y + h + CUT_GRN[2] + CUT_GRN[0]), (0, 255, 0), 3) #rectangle around green contours
					a = x + w / 2 - 160 + CUT_GRN[0]
					if(a < linePos):
						contours_left = True
					elif(a > linePos):
						contours_right = True

		else:
			if(grn_counter > 0):
				print("abort")
				grn_counter = 0
				grn_list = []

		if(contours_left and contours_right):
			for i in range(len(contours_grn)):
				b = cv2.boundingRect(contours_grn[i])
				x, y, w, h = b
				#cv2.rectangle(image_rgb, (x, y + CUT_GRN[2]), (x + w, y + h + CUT_GRN[2]), (0, 255, 0), 3)
				a = x + w/2 - 160
				if(a < linePos):
					contours_left = True
				elif(a > linePos):
					contours_right = True

			if(contours_left and contours_right):
				grn_list.append("D")

		elif(contours_left):
			for i in range(len(contours_grn)):
				b = cv2.boundingRect(contours_grn[i])
				x, y, w, h = b
				#cv2.rectangle(image_rgb, (x, y + CUT[3]), (x + w, y + h + CUT[3]), (0, 255, 0), 3)
				a = x + w / 2 - 160
				if(a < linePos):
					contours_left = True
				elif(a > linePos):
					contours_right = True

			if(contours_left):
				grn_list.append("L")
				if(grn_counter == 7):
					grn_list.append("L")

		elif(contours_right):
			for i in range(len(contours_grn)):
				b = cv2.boundingRect(contours_grn[i])
				x, y, w, h = b
				#cv2.rectangle(image_rgb, (x, y + CUT[3]), (x + w, y + h + CUT[3]), (0, 255, 0), 3)
				a = x + w/2 - 160
				if(a < linePos):
					contours_left = True
				elif(a > linePos):
					contours_right = True

			if(contours_right):
				grn_list.append("R")
				if(grn_counter == 7):
					grn_list.append("R")

		else:
			value = str(linePos).encode()
			value = int(float(value))

			if len(contours_blk) == 0: #no black contour
				print("Gapcounter:", gapcounter)
				gapcounter = gapcounter + 1
				if gapcounter > 2:
					if LinePosLastLoop[7] < -20:
						#drehe links
						#ser.write(b'IL') #send gap, turn left
						print("Linepos7:", LinePosLastLoop[7])
					elif LinePosLastLoop[7] > 20:
						#drehe rechts
						print("Linepos7:", LinePosLastLoop[7])
						#ser.write(b'IR') #send gap, turn rigth
					else:
						pass
						#ser.write(b'I') #send gap
				
			else:
				gapcounter = 0
				#ser.write(str(linePos / 10).encode()) 

		if(grn_counter > 0):
			grn_counter = grn_counter - 1
		framesTotal = framesTotal + 1

		rawCapture.truncate(0)
		DEBUG()

		LinePosLastLoop[0] = value
		for i in range(1, 8):
			LinePosLastLoop[i] = LinePosLastLoop[i - 1]

		key = cv2.waitKey(1) & 0xFF
		if key == ord("q"):

			print("Avg. FPS:", int(framesTotal / (time.time() - startTime - timeWaitet))) #sendet durchsch. Bilder pro Sekunde (FPS)
			camera.close()
			exit()