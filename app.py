import tkinter as tk
import time
import threading
import csv
import datetime

from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, 
    NavigationToolbar2Tk
) 
from motor_controller import MotorController, LoopFlowData

import load_cell_reader
# CSV file with date and time in file name
csv_name = f"captan_drive_test_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
csvfile = open(csv_name, 'w', newline='')
fieldnames = ['timestamp', 'position', 'torque', 'velocity', 'force']
writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
writer.writeheader()

# Initialize the Tkinter root window
root = tk.Tk()
root.title("Motor controller")
root.geometry("300x200")

SENSOR_COM = 'COM4'
SERSOR_BR = 115200
INTERVAL_VALUES_UPDATE = 0.1
MAX_VALUES = 1000
init_time = 0

motor : MotorController = None
ser: load_cell_reader.LoadCellreader = None
thread: threading.Thread = None
check_values : bool = False
position_values = []
velocity_values = []
torque_values = []
force_values = []
timestamps = []

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

def plot(values, val_y,  ax_to_plot): 
    ax_to_plot.cla() 
    ax_to_plot.grid()
    val_len = len(values)
    ax_to_plot.plot(range(0, val_len), values)

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

def update_csv_file(data: list[dict]):
    writer.writerows(data)

def limit_data_len(data: list):
    val_len = len(data)
    if val_len > MAX_VALUES:
        data = data[-MAX_VALUES:]
        val_len = MAX_VALUES
    return data

def load_cell_cb(data: load_cell_reader.LoadCellData):

    global position_values, velocity_values, torque_values, force_values

    ts = datetime.datetime.now().timestamp()
    timestamps.append(ts)
    
    # get values
    pos = motor.get_position() if motor else 0.0
    vel = motor.get_velocity() if motor else 0.0
    torq = motor.get_torque() if motor else 0.0
    force = data.calculatedWeight if data else 0.0

    # update lists
    position_values.append(pos)
    velocity_values.append(vel)
    torque_values.append(torq)
    force_values.append(force)

    # limit list
    position_values = limit_data_len(position_values)
    velocity_values = limit_data_len(velocity_values)
    torque_values = limit_data_len(torque_values)
    force_values = limit_data_len(force_values)

    # update interface
    position_output.config(text=f"Pos [deg]: {pos:.2f}")

    # save information
    data = {
        'timestamp': ts, 
        'position': pos, 
        'torque': torq, 
        'velocity': vel, 
        'force': force
    }
    update_csv_file([data])

def connect_lc(event=None):
    global ser

    if ser and ser.isConnected():
        ser.disconnect()

    try:
        # try to connect serial force sensor
        ser = load_cell_reader.LoadCellreader(SENSOR_COM, SERSOR_BR)  # open serial port
        ser.start(load_cell_cb)
        buffer = ser.readBuffer()
        if buffer:
            messages_output.config(text=f"Message from cell: {buffer}")

    except:
        messages_output.config(text="Error connecting with Load Cell")

def run_updates():
    global timestamps
    while check_values:

        ts_len = len(timestamps)    
        if ts_len > MAX_VALUES:
            timestamps = timestamps[-MAX_VALUES:]

        # Update each output with a random float
        plot(position_values, timestamps, ax)
        plot(velocity_values, timestamps,ax_vel)
        plot(torque_values, timestamps, ax_torq)
        plot(force_values, timestamps, ax_force)
        graph.draw()
        time.sleep(INTERVAL_VALUES_UPDATE)  # Update every second

def connect():

    global motor, thread, check_values
    
    # if thread == None :

    print("Initializing motor")

    messages_output.config(text="Waitting for motor to connect")
    motor = MotorController()
    
    messages_output.config(text="Configuring motor")
    motor.config()
    motor.save_and_reboot()

def run_step_loop():
    global motor
    steps = []
    steps.append(LoopFlowData(position=300, delay_ms= 2000))
    steps.append(LoopFlowData(position=400, delay_ms= 1000))
    steps.append(LoopFlowData(position=500, delay_ms= 2000))
    steps.append(LoopFlowData(position=300, delay_ms= 2000))
    steps.append(LoopFlowData(position=700, delay_ms= 5000))
    steps.append(LoopFlowData(position=400, delay_ms= 2000))
    steps.append(LoopFlowData(position=800, delay_ms= 3000))
    steps.append(LoopFlowData(position=500, delay_ms= 1000))
    motor.set_loop_flow(steps)

def stop_step_loop():
    global motor
    motor.stop_steps_loop()

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

release_button = tk.Button(motor_frame, text="Run Steps", command=run_step_loop)
release_button.pack(side="left", padx=10, pady=10)

release_button = tk.Button(motor_frame, text="Stop Steps", command=stop_step_loop)
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

# Start the updates in a separate thread
check_values = True
thread = threading.Thread(target=run_updates, daemon=True)
thread.start()

# Start the Tkinter main loop
root.mainloop()

print("Disconnecting motor")
messages_output.config(text="Disconnecting motor")
check_values = False
thread.join()
thread = None