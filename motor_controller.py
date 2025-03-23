import math
import time
import odrive
import threading

from odrive.utils import dump_errors
from odrive.utils import MotorType, AxisState, EncoderId, Protocol, InputMode, ControlMode

class MotorRequest:
    torque: float = 0.1     # Nm
    velocity: float = 30  # deg/s
    position: float = 0.0   # deg

class MotorController:

    requests: list[MotorRequest] = []
    def __init__(self) -> None:
        self.odrv0 = odrive.find_any()
        self.init_offset_pos = 0.0
        if self.odrv0.reboot_required: 
            try:
                self.odrv0.erase_configuration()
            except:
                print("Erase config and reboot") # Saving configuration makes the device reboot
            self.odrv0.clear_errors()
        else:
            print("Connecting to configured motor")

    def run(self):
        self.control_running = True
        self.request_not_processed = threading.Event()
        self.th = threading.Thread(target=self.position_control, daemon= True)
        self.th.start()

    def position_control(self):

        print("position_control START")
        while self.control_running:
            print(f"Current pos: {self.get_position()}")
            time.sleep(1)
    
    def add_request(self, request: MotorRequest):
        self.requests.append(request)
        self.request_not_processed.set()
    
    def config(self):
        odrv = self.odrv0
        odrv.config.dc_bus_overvoltage_trip_level = 30
        odrv.config.dc_bus_undervoltage_trip_level = 10.5
        odrv.config.dc_max_positive_current = 10
        odrv.config.dc_max_negative_current = -1
        odrv.config.brake_resistor0.enable = True
        odrv.config.brake_resistor0.resistance = 2
        odrv.axis0.config.motor.motor_type = MotorType.HIGH_CURRENT
        odrv.axis0.config.motor.pole_pairs = 7
        odrv.axis0.config.motor.torque_constant = 0.02506060606060606
        odrv.axis0.config.motor.current_soft_max = 40
        odrv.axis0.config.motor.current_hard_max = 60
        odrv.axis0.config.motor.calibration_current = 3
        odrv.axis0.config.motor.resistance_calib_max_voltage = 2
        odrv.axis0.config.calibration_lockin.current = 3
        odrv.axis0.motor.motor_thermistor.config.enabled = False
        odrv.axis0.controller.config.control_mode = ControlMode.POSITION_CONTROL
        odrv.axis0.controller.config.input_mode = InputMode.TRAP_TRAJ
        odrv.axis0.controller.config.vel_limit = 5
        odrv.axis0.controller.config.vel_limit_tolerance = 1.2
        odrv.axis0.controller.config.vel_ramp_rate = 10
        odrv.axis0.trap_traj.config.vel_limit = 10  # Max speed (rev/s)
        odrv.axis0.trap_traj.config.accel_limit = 2
        odrv.axis0.trap_traj.config.decel_limit = 2  # Max deceleration (rev/s^2)
        odrv.axis0.config.torque_soft_min = -math.inf
        odrv.axis0.config.torque_soft_max = math.inf
        odrv.can.config.protocol = Protocol.NONE
        odrv.axis0.config.enable_watchdog = False
        odrv.axis0.config.load_encoder = EncoderId.ONBOARD_ENCODER0
        odrv.axis0.config.commutation_encoder = EncoderId.ONBOARD_ENCODER0
        odrv.config.enable_uart_a = False
    
    def save_and_reboot(self):
        try:
            self.odrv0.save_configuration()
        except:
            print("Saving config and reboot") # Saving configuration makes the device reboot
        self.odrv0 = odrive.find_any()

    def set_home(self):
        self.odrv0.axis0.requested_state = AxisState.CLOSED_LOOP_CONTROL
        while self.odrv0.axis0.current_state != AxisState.CLOSED_LOOP_CONTROL:
            time.sleep(0.1)
        self.init_offset_pos = self.odrv0.axis0.pos_estimate
    
    def release_torque(self):
        self.odrv0.axis0.requested_state = AxisState.IDLE

    def calibrate(self):
        self.odrv0.axis0.requested_state = AxisState.FULL_CALIBRATION_SEQUENCE
        while self.odrv0.axis0.current_state != AxisState.IDLE:
            time.sleep(0.1)

    def set_pos(self, pos: float, vel: float = 50 , torque: float = 0.3):
        # self.odrv0.axis0.controller.input_torque = torque
        # self.odrv0.axis0.controller.input_vel = vel/360
        self.odrv0.axis0.controller.input_pos = (pos)/360 + self.init_offset_pos
    
    def set_velocity(self, vel: float = 0.001 , torque: float = 0.1):
        self.odrv0.axis0.controller.input_torque = torque
        self.odrv0.axis0.controller.input_vel = vel/360
    
    def get_position(self):
        return (self.odrv0.axis0.pos_estimate) * 360 - self.init_offset_pos
    
    def get_velocity(self):
        return self.odrv0.axis0.vel_estimate

    def get_torque(self):
        return self.odrv0.axis0.motor.torque_estimate
    
    def get_voltage(self):
        str(self.odrv0.vbus_voltage)

    def check_errors(self):
        dump_errors(self.odrv0)
    
    def end(self):
        if self.control_running:
            self.control_running = False
            self.th.join()
        self.odrv0.clear_errors()
        self.odrv0.reboot()
        dump_errors(self.odrv0)