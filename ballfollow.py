#!/usr/bin/python2.7
import atexit
from ev3dev.auto import *
from time import sleep

STORAGE_LENGTH = 15 # No of values in the mean
TURNINESS = 150 # Sharpness of turn
HOLD_SR_LEN = 20 # Length of shift register for holding
CLOSENESS_THRESHOLD = 10 # (in cm) Distance before going "that's too close"
SPINNING_SPEED = 50 # Speed that it spins at.

ir = Sensor('in1:i2c8') # It's an old sensor, so it needs i2c8
gyro = GyroSensor('in2')
steer = [LargeMotor('outA'),LargeMotor('outB')]
hold = LargeMotor('outD')
# [ev3.UltrasonicSensor("in4"),"in3"]
ultra = [UltrasonicSensor('in4'),UltrasonicSensor('in3')]

# a.run_to_rel_pos(position_sp=720,duty_cycle_sp=-100) is the command for doing certain length rotationy stuff

vals = [5 for i in range(STORAGE_LENGTH)]
c = 0
gyroValue = 0
calibrateGyro = 0

def updateGyro(dt):
	# Update the gyro, given delta time
	gyroValue += (gyro.value()*dt) - calibrateGyro
	gyroValue = ((gyroValue + 180) % 360) - 180
	# gyroValue takes values of -180 to +180, as you'd expect.

def mean(t):
	return sum(t)/float(len(t))

def move(angle):
	# Turn with a sharpness of TURNINESS (+TURNINESS => +angle)
	if angle > 0:
		ls = 100 - TURNINESS*angle
		rs = 100
	elif angle < 0:
		ls = 100
		rs = 100 + TURNINESS*angle # Finnbar, angle will be less than zero so this is legit code. Don't worry yourself!
	else:
		ls = 100
		rs = 100
	steer[0].run_forever(duty_cycle_sp=int(ls))
	steer[1].run_forever(duty_cycle_sp=int(rs))

def spin(direction):
	steer[0].run_forever(duty_cycle_sp=SPINNING_SPEED*direction)
	steer[1].run_forever(duty_cycle_sp=-SPINNING_SPEED*direction)

def objectDetection():
	# Return a [Bool, Bool] detailing which ultrasonics detect something as too close.
	return [ultra[0].value() < CLOSENESS_THRESHOLD, ultra[1].value < CLOSENESS_THRESHOLD]

# def move(a): pass # uncomment this line for tabletop tests, to stop it moving

def exit_handler(): # This stops the motors, which is a good idea.
	steer[0].stop()
	steer[1].stop()
	hold.stop()

if __name__ == '__main__':
	print "GO!"
	holding_sr=[] # This is our general shift register, I'll explain later.
	assert steer[0].connected and steer[1].connected and hold.connected # Basic assert, just in case
	hold.run_forever(duty_cycle_sp=50) # This is our dribbler motor
	hold_threshold = 0
	gyro.mode = "GYRO-RATE"
	sleep(1)
	for _ in range(20): # Check the dribbler speed to work out when the ball is in the way
		holding_sr.append(hold.speed)
	hold_threshold=sum(holding_sr)/21.0
	holding_sr = []
	for _ in range(20):
		holding_sr.append(gyro.value())
	print hold_threshold
	calibrateGyro = sum(holding_sr)/20.0
	oldTime = time.time()
	while True:
		updateGyro(time.time() - oldTime)
		closeThings = objectDetection()
		q = ir.value() # Angle from 1 - 9 units (very left to very right)
		del(holding_sr[0])
		holding_sr.append(hold.speed)
		if sum(holding_sr)/HOLD_SR_LEN <= hold_threshold:
			# WE HAVE THE BALL, SO:
			if closeThings[0] and closeThings[1] and abs(gyroValue) < 5:
				# We are in front of the goal, and want to score
				# So let's just push the ball already
				move(0)
				hold.run_forever(duty_cycle_sp=-100)
				sleep(0.5)
			else:
				# Move towards the goal
				if abs(gyroValue) < 45:
					move(gyroValue/360.0)
				else:
					spin(gyroValue/abs(gyroValue))
		elif q != 0: # We see the ball!
			# WE DON'T HAVE THE BALL, SO:
			vals[c] = q
			c+=1
			if c>=STORAGE_LENGTH:
				c = 0
			s = mean(vals) # Get the mean of the last STORAGE_LENGTH readings
			angle = (s-5)*0.25
			move(angle)
			hold.run_forever(duty_cycle_sp=50)
		else: # Angle is 0, or failed to find ball
			if mean(vals) > 5: # If it was already going right,
				move(1)    # Go right!
			else:
				move(-1)   # Else, go left!
			hold.run_forever(duty_cycle_sp=50)
		oldTime = time.time()
