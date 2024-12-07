import tkinter as tk
import time
import threading

from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, 
    NavigationToolbar2Tk
) 
from motor_controller import MotorController

# Initialize the Tkinter root window
root = tk.Tk()
root.title("Motor controller")
root.geometry("300x200")

motor : MotorController = None
thread: threading.Thread = None
check_values : bool = False
position_values = []
velocity_values = []
torque_values = []

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
ax = fig.add_subplot(311) 
ax.set_xlabel("s") 
ax.set_ylabel("deg") 
ax.set_title("Postion")
ax.grid() 

ax_vel = fig.add_subplot(312) 
ax_vel.set_xlabel("s") 
ax_vel.set_ylabel("rev/s") 
ax_vel.set_title("Velocity")
ax_vel.grid() 

ax_torq = fig.add_subplot(313) 
ax_torq.set_xlabel("s") 
ax_torq.set_ylabel("Nm") 
ax_torq.set_title("Torque")
ax_torq.grid() 

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
            plot(position_values, ax)
            plot(velocity_values, ax_vel)
            plot(torque_values, ax_torq)
            graph.draw()
            time.sleep(0.5)  # Update every second
    
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

# Create and place the input label and entry
label = tk.Label(root, text="Enter an integer:")
label.pack(pady=5)
entry = tk.Entry(root)
entry.pack(pady=5)

# Bind the Enter key to start the application
entry.bind("<Return>", set_position)

# Create labels for the outputs
messages_output = tk.Label(root, text="Info: ---")
messages_output.pack(pady=5)

position_output = tk.Label(root, text="Position [deg]: ")
position_output.pack(pady=5)

# Create buttons

release_button = tk.Button(root, text="Connect", command=connect)
release_button.pack(side="left", padx=10, pady=10)

release_button = tk.Button(root, text="Calibrate", command=calibrate)
release_button.pack(side="left", padx=10, pady=10)

home_button = tk.Button(root, text="Home", command=reset_to_home)
home_button.pack(side="left", padx=10, pady=10)

release_button = tk.Button(root, text="Release", command=release)
release_button.pack(side="left", padx=10, pady=10)

# Start the Tkinter main loop
root.mainloop()