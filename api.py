
from fastapi import FastAPI, HTTPException
import uvicorn

from fastapi.middleware.cors import CORSMiddleware
from motor_controller import MotorController

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your React app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

motor : MotorController = None

@app.post("/motor/connect")
async def set_home_position():
    """Write a UTF-8 string to serial port."""
    try:
        print("Initializing motor")

        print("Waitting for motor to connect")
        motor = MotorController()
        
        print("Configuring motor")
        motor.config()
        motor.save_and_reboot()

        return {
            "status": "success"
        }
    except UnicodeEncodeError as e:
        raise HTTPException(status_code=400, detail="Error connecting motor")
        
@app.post("/motor/calibrate")
async def set_home_position():
    """Write a UTF-8 string to serial port."""
    try:
        print("Calibrate motor") 
        motor.calibrate()
        return {
            "status": "success"
        }
    except UnicodeEncodeError as e:
        raise HTTPException(status_code=400, detail="Error calibrating motor")
    
@app.post("/motor/release")
async def set_home_position():
    """Write a UTF-8 string to serial port."""
    try:
        print("Releasing motor") 
        motor.release_torque()
        return {
            "status": "success"
        }
    except UnicodeEncodeError as e:
        raise HTTPException(status_code=400, detail="Error releasing motor")

@app.post("/motor/set_home")
async def set_home_position():
    """Write a UTF-8 string to serial port."""
    try:
        print("Set new home")
        motor.set_home()
        pos = motor.get_position()
        return {
            "status": "success",
            "position": pos
        }
    except UnicodeEncodeError as e:
        raise HTTPException(status_code=400, detail="Error settign home")

@app.post("/motor/set_position/{position}")
async def set_position(position: float):
    """Read data and decode as UTF-8 string."""
    try:
        print("setting position to", position)
        motor.set_pos(position)
        pos = motor.get_position()
        return {
            "status": "success",
            "position": pos
        }
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail=f"Error setting position {position}")

@app.post("/motor/get_values")
async def set_position():
    """Read data and decode as UTF-8 string."""
    try:
        pos = motor.get_position()
        vel = motor.get_velocity()
        torq = motor.get_torque()
        return {
            "position": pos,
            "velocity": vel,
            "torque": torq
        }
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail=f"Error getting position")
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)