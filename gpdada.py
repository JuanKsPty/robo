import RPi.GPIO as GPIO
import time
ena = 21
enb = 18
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme

GPIO.setup(18, GPIO.OUT)
GPIO.setup(23, GPIO.OUT)
GPIO.setup(24, GPIO.OUT)

GPIO.setup(21, GPIO.OUT)
GPIO.setup(20, GPIO.OUT)
GPIO.setup(16, GPIO.OUT)

# Initial state for LEDs:
print("Testing RF out, Press CTRL+C to exit")
GPIO.output(21, GPIO.LOW)
GPIO.output(18, GPIO.LOW)

pwm_a = GPIO.PWM(ena,100)
pwm_b = GPIO.PWM(enb,100)
pwm_a.start(0)
pwm_b.start(0)

def motorAF(power):
    pwm_a.ChangeDutyCycle(power)
    GPIO.output(20, GPIO.HIGH)
    GPIO.output(16, GPIO.LOW)
def motorAB(power,duration):
    pwm_a.ChangeDutyCycle(power)
    GPIO.output(20, GPIO.LOW)
    GPIO.output(16, GPIO.HIGH)
    time.sleep(duration)
def motorBF(power):
    pwm_b.ChangeDutyCycle(power)
    GPIO.output(20, GPIO.LOW)
    GPIO.output(16, GPIO.HIGH)
def motorBB(power,duration):
    pwm_b.ChangeDutyCycle(power)
    
    
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
        steer =*-1
        motorBF(speed)
        motorAF(speed*steer/100)
        return
            
    GPIO.output(20, GPIO.LOW)
    GPIO.output(16, GPIO.HIGH)
    time.sleep(duration)
try:
     print("set GIOP high")
     motorAF(50,4)
     motorAF(50,4)
     GPIO.output(21, GPIO.HIGH)
     GPIO.output(16, GPIO.HIGH)
     GPIO.output(20, GPIO.LOW)
     time.sleep(1)
     GPIO.output(21, GPIO.LOW)
     time.sleep(1)
     GPIO.output(18, GPIO.HIGH)
     GPIO.output(23, GPIO.HIGH)  
     GPIO.output(24, GPIO.LOW)
     time.sleep(3)
     GPIO.output(18, GPIO.HIGH)
     GPIO.output(24, GPIO.HIGH)
     GPIO.output(23, GPIO.LOW)
     time.sleep(3)
except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
   print("Keyboard interrupt")

except:
   print("some error") 

finally:
    GPIO.output(21, GPIO.LOW)
    GPIO.output(18, GPIO.LOW)
    print("clean up") 
    GPIO.cleanup() # cleanup all GPIO 