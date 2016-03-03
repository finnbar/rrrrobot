#!/usr/bin/python2.7

import atexit
import ev3dev as ev3

STORAGE_LENGTH = 20
WALL_DODGE_DISTANCE = 200

ir = ev3.sensor('in1:i2c8')
steer = [ev3.large_motor('outA'),ev3.large_motor('outB')]
hold = ev3.large_motor('outD')
lefteye = ev3.sensor('in4')
righteye = ev3.sensor('in3')

vals = [5 for i in range(STORAGE_LENGTH)]
c = 0

def mean(t):
	return sum(t)/float(len(t))

def move(angle):
        if angle > 0:
                ls = 100 - 100*angle
                rs = 100
        elif angle < 0:
                ls = 100
                rs = 100 + 100*angle
        else:
                ls = 100
                rs = 100
        steer[0].run_forever(duty_cycle_sp=int(ls))
        steer[1].run_forever(duty_cycle_sp=int(rs))
        print angle,rs,ls

def exit_handler():
	steer[0].stop()
	steer[1].stop()
	hold.stop()

if __name__ == '__main__':
	print "GO!"
	assert steer[0].connected and steer[1].connected and hold.connected
	while True:
		if ev3.button.back.pressed:
			exit()
		q = ir.value()
		ldist = lefteye.value()
		rdist = righteye.value()
		print min(ldist,rdist)
		if min(rdist,ldist) > WALL_DODGE_DISTANCE:
			print 'clear'
			move(0)
#			if q != 0:
#				vals[c] = q
#				c+=1
#				if c>=STORAGE_LENGTH:
#					c = 0
#				s = mean(vals)
#				angle = (s-5)*0.25
#				move(angle)
#				hold.run_forever(duty_cycle_sp=50)
#			else:
#				if mean(vals) > 5:
#					move(1)
#				else:
#					move(-1)
#				hold.run_forever(duty_cycle_sp=-50)
		elif ldist <= WALL_DODGE_DISTANCE:
			move(-1)
		else:
			move(1)
