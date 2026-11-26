import sys
import glob
import time
import os
from fastapi_mqtt import FastMQTT, MQTTConfig

ACTIVE_SERIAL_CONNECTION = None

# Configure MQTT for Smart Home Integration
mqtt_config = MQTTConfig(
    host=os.environ.get("MQTT_HOST", "localhost"),
    port=int(os.environ.get("MQTT_PORT", 1883)),
    username=os.environ.get("MQTT_USER", None),
    password=os.environ.get("MQTT_PASSWORD", None)
)

fast_mqtt = FastMQTT(config=mqtt_config)

async def set_room_lighting(state: str, brightness: int = 100):
    """Sends MQTT command to Home Assistant smart lights."""
    try:
        topic = "homeassistant/light/workshop_lights/set"
        payload = f'{{"state": "{state.upper()}", "brightness": {brightness}}}'
        await fast_mqtt.publish(topic, payload)
        return f"Room lights set to {state.upper()} at {brightness}% brightness, sir."
    except Exception as e:
        return f"Failed to transmit MQTT lighting signal: {str(e)}"

def scan_hardware_ports() -> list:
    """
    Scans macOS hardware ports for connected Arduinos, ESP32s, Microcontrollers, and Bluetooth Serial devices.
    """
    ports = []
    if sys.platform.startswith('darwin'):
        # macOS serial patterns
        patterns = ['/dev/cu.usbmodem*', '/dev/cu.usbserial*', '/dev/cu.SLAB_USBtoUART*', '/dev/cu.wchusbserial*', '/dev/cu.*']
        for pat in patterns:
            found = glob.glob(pat)
            for f in found:
                if f not in ports and 'Bluetooth' not in f and 'AirPods' not in f:
                    ports.append(f)
    return ports

def control_hardware_device(device_name: str = "auto", action: str = "toggle_pin", parameter: int = 13) -> str:
    """
    Sends control signals to a connected Arduino / ESP32 / Microcontroller over USB Serial or Bluetooth.
    Supports motor control (servo angle 0-180), relay toggles, LED matrix signals, and pin high/low state.
    """
    ports = scan_hardware_ports()
    if not ports:
        return f"Hardware scan complete. No active USB Serial microcontrollers (Arduino/ESP32) detected on your Mac ports. Please plug in your device, sir."

    target_port = ports[0]
    if device_name != "auto":
        for p in ports:
            if device_name.lower() in p.lower():
                target_port = p
                break

    try:
        import serial
        # Send serial command payload
        cmd_str = f"{action.upper()}:{parameter}\n"
        
        with serial.Serial(target_port, 9600, timeout=1.0) as ser:
            time.sleep(1.5) # Wait for DTR reset
            ser.write(cmd_str.encode('utf-8'))
            time.sleep(0.5)
            response = ser.readline().decode('utf-8', errors='ignore').strip()
            
        res_msg = f" [Signal ACK: {response}]" if response else ""
        return f"Hardware signal '{action.upper()}:{parameter}' transmitted to microcontroller on {target_port}{res_msg}, boss."
    except Exception as e:
        return f"Device detected on {target_port}, but transmission protocol encountered: {str(e)}"
