import time
import threading

from motor_controller import MotorController, MotorRequest


check_pos = True

def check_position():
    global check_pos
    while check_pos:
        time.sleep(1)
        print("Pos:", motor.get_position()) 

if __name__ == "__main__":

    motor = MotorController()
    motor.config()
    motor.save_and_reboot()
    motor.calibrate()
    # motor.set_home()
    motor.run()

    while True:
        val = input()
        if val == 'q':
            break
        else:
            try:
                if val == 'h':
                    motor.set_home()
                elif val == 'r':
                    motor.release_torque()
                else:
                    motor.set_pos(float(val))
            except:
                print("Input must be a float")

    motor.end()