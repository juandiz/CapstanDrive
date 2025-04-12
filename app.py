import tkinter as tk
import time
import threading

from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, 
    NavigationToolbar2Tk
) 
from motor_controller import MotorController

import load_cell_reader

# Initialize the Tkinter root window
root = tk.Tk()
root.title("Motor controller")
root.geometry("300x200")

SENSOR_COM = 'COM4'
SERSOR_BR = 115200
INTERVAL_VALUES_UPDATE = 0.1

motor : MotorController = None
ser: load_cell_reader.LoadCellreader = None
thread: threading.Thread = None
check_values : bool = False
position_values = []
velocity_values = []
torque_values = []
force_values = []

def load_callback(msg):
    messages_output.config(text=msg)

# Function to start the application
def set_position(event=None):
    # Read the integer input and validate
    try:
        input = float(entry.get())
        entry.config()
        motor.set_pos(input)
        print("setting position to", input)
    except ValueError:
        messages_output.config(text="Please enter a valid integer.")
    
    # Clear the entry field after starting updates
    entry.delete(0, tk.END)

# the figure that will contain the plot 
fig = Figure(figsize = (3, 3), 
            dpi = 100) 

# adding the subplot 
ax = fig.add_subplot(411) 
ax.set_xlabel("s") 
ax.set_ylabel("deg") 
ax.set_title("Postion")
ax.grid() 

ax_vel = fig.add_subplot(412) 
ax_vel.set_xlabel("s") 
ax_vel.set_ylabel("rev/s") 
ax_vel.set_title("Velocity")
ax_vel.grid() 

ax_torq = fig.add_subplot(413) 
ax_torq.set_xlabel("s") 
ax_torq.set_ylabel("Nm") 
ax_torq.set_title("Torque")
ax_torq.grid() 

ax_force = fig.add_subplot(414) 
ax_force.set_xlabel("s") 
ax_force.set_ylabel("Kg") 
ax_force.set_title("Force")
ax_force.grid() 

graph = FigureCanvasTkAgg(fig, master=root) 
graph.get_tk_widget().pack(side="top",fill='both',expand=True) 
MAX_VALUES = 100

def plot(values, ax_to_plot): 
    ax_to_plot.cla() 
    ax_to_plot.grid()
    val_len = len(values)
    init_index = val_len - MAX_VALUES
    if init_index < 0:
        init_index = 0
    ax_to_plot.plot(range(init_index, val_len),values[init_index:])

def clear_values(array: list, percentage: float = 0.8):
    prev_len = len(array)
    return array[int(prev_len*percentage): prev_len]

def clear_graphs(event=None):
    global position_values, velocity_values, torque_values, force_values
    position_values = clear_values(position_values)
    velocity_values = clear_values(velocity_values)
    torque_values = clear_values(torque_values)
    force_values = clear_values(force_values)
    plot(position_values, ax)
    plot(velocity_values, ax_vel)
    plot(torque_values, ax_torq)
    plot(force_values, ax_force)

def reset_to_home(event=None):
    global motor
    print("Set new home")
    motor.set_home()

def release(event=None):
    global motor
    print("Releasing motor") 
    motor.release_torque()

def calibrate(event=None):
    global motor
    print("Calibrate motor") 
    motor.calibrate()

def calibrate_lc(event=None):
    global ser
    print("Calibrate Load cell") 

    if not ser.isConnected():
        messages_output.config(text="Error Load Cell not connected")

    try:

        buffer =  ser.calibrate_lc()
        if buffer:
            messages_output.config(text=f"Message from cell: {buffer}")

    except:
        messages_output.config(text="Error connecting with Load Cell")

def tare_lc(event=None):
    global ser
    print("Tare Load cell") 

    if not ser.isConnected():
        messages_output.config(text="Error Load Cell not connected")

    try:
        buffer =  ser.tare_lc()
        if buffer:
            messages_output.config(text=f"Message from cell: {buffer}")

    except:
        messages_output.config(text="Error connecting with Load Cell")

def connect_lc(event=None):
    global ser

    if ser and ser.isConnected():
        ser.disconnect()

    try:
        # try to connect serial force sensor
        ser = load_cell_reader.LoadCellreader(SENSOR_COM, SERSOR_BR)  # open serial port
        ser.attach_callback(load_callback)
        buffer = ser.readBuffer()
        if buffer:
            messages_output.config(text=f"Message from cell: {buffer}")

    except:
        messages_output.config(text="Error connecting with Load Cell")

def connect():

    global motor, thread, check_values

    def run_updates():
        while check_values:
            # Update each output with a random float
            pos = motor.get_position()
            vel = motor.get_velocity()
            torq = motor.get_torque()
            position_values.append(pos)
            velocity_values.append(vel)
            torque_values.append(torq)
            position_output.config(text=f"Pos [deg]: {pos:.2f}")
            force = ser.get_current_force() if ser else 0
            force_values.append(force)
            plot(position_values, ax)
            plot(velocity_values, ax_vel)
            plot(torque_values, ax_torq)
            plot(force_values, ax_force)
            graph.draw()
            time.sleep(INTERVAL_VALUES_UPDATE)  # Update every second
    
    if thread == None :

        print("Initializing motor")

        messages_output.config(text="Waitting for motor to connect")
        motor = MotorController()
        
        messages_output.config(text="Configuring motor")
        motor.config()
        motor.save_and_reboot()

        # Start the updates in a separate thread
        check_values = True
        thread = threading.Thread(target=run_updates, daemon=True)
        thread.start()
    else:
        print("Disconnecting motor")
        messages_output.config(text="Disconnecting motor")
        check_values = False
        thread.join()
        thread = None

# Create labels for the outputs
input_frame = tk.LabelFrame(root, text='Input and Info', padx=10, pady=10)
input_frame.pack(side='left', padx=10)

# Create buttons
motor_frame = tk.LabelFrame(root, text='Motor', padx=10, pady=10)
motor_frame.pack(side='left', padx=10)

release_button = tk.Button(motor_frame, text="Connect", command=connect)
release_button.pack(side="left", padx=10, pady=10)

release_button = tk.Button(motor_frame, text="Calibrate", command=calibrate)
release_button.pack(side="left", padx=10, pady=10)

home_button = tk.Button(motor_frame, text="Home", command=reset_to_home)
home_button.pack(side="left", padx=10, pady=10)

release_button = tk.Button(motor_frame, text="Release", command=release)
release_button.pack(side="left", padx=10, pady=10)

# Create and place the input label and entry
label = tk.Label(motor_frame, text="Enter an integer:")
label.pack(side="left", padx=10, pady=10)
entry = tk.Entry(motor_frame)
entry.pack(side="left", padx=10, pady=10)

# Bind the Enter key to start the application
entry.bind("<Return>", set_position)

position_output = tk.Label(motor_frame, text="Position [deg]: ")
position_output.pack(pady=5)

# Create a frame for Load Cell buttons
load_cell_frame = tk.LabelFrame(root, text='Load Cell', padx=10, pady=10)
load_cell_frame.pack(side='left', padx=10)

# Create buttons within the Load Cell frame
release_button = tk.Button(load_cell_frame, text="Connect", command=connect_lc)
release_button.pack(side="left", padx=10, pady=10)

release_button = tk.Button(load_cell_frame, text="Calibrate", command=calibrate_lc)
release_button.pack(side="left", padx=10, pady=10)

release_button = tk.Button(load_cell_frame, text="Tare", command=tare_lc)
release_button.pack(side="left", padx=10, pady=10)

# information
messages_output = tk.Label(root, text="Info: ---")
messages_output.pack(side="left",pady=5)

clear_graph = tk.Button(load_cell_frame, text="Clear Graphs", command=clear_graphs)
clear_graph.pack(side="left", padx=10, pady=10)

# Start the Tkinter main loop
root.mainloop()