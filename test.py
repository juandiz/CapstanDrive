#!/usr/bin/env python3
"""
Example usage of the ODrive python library to monitor and control ODrive devices
"""

from __future__ import print_function

import odrive
from odrive.enums import *
import time
import math

# Find a connected ODrive (this will block until you connect one)
print("finding an odrive...")
my_drive = odrive.find_any()

# Find an ODrive that is connected on the serial port /dev/ttyUSB0
#my_drive = odrive.find_any("serial:/dev/ttyUSB0")
motor = my_drive.axis0.motor; axis = my_drive.axis0; ctrl = axis.controller  #variables

print("starting closed loop control...")
my_drive.axis0.requested_state = AxisState.CLOSED_LOOP_CONTROL
# while my_drive.axis0.current_state != AXIS_STATE_IDLE:
#     time.sleep(0.1)
print("moving 1000 ticks")
ctrl.move_incremental(1000,False)
time.sleep(3)


# To read a value, simply read the property
print("Bus voltage is " + str(my_drive.vbus_voltage) + "V")

# Or to change a value, just assign to the property
initial_offset = my_drive.axis0.controller.pos_setpoint
print("Position setpoint is " + str(my_drive.axis0.controller.pos_setpoint))

# And this is how function calls are done:
for i in [1,2,3,4]:
    print('voltage on GPIO{} is {} Volt'.format(i, my_drive.get_adc_voltage(i)))

# A sine wave to test
t0 = time.monotonic()
freq = 2*3.14 / 1.91 /2
c= 0
while True:
    c = c +1
    setpoint = 5000.0 * math.sin((time.monotonic() - t0)*freq)
    my_drive.axis0.controller.pos_setpoint = setpoint + initial_offset
    print("avg freq" + str(c/(time.monotonic() - t0))  + "goto " + str(int(setpoint)))


# Some more things you can try:

# Write to a read-only property:
my_drive.vbus_voltage = 11.0  # fails with `AttributeError: can't set attribute`

# Assign an incompatible value:
my_drive.motor0.pos_setpoint = "I like trains"  # fails with `ValueError: could not convert string to float`