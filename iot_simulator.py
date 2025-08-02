# =============================================================================
# 9. iot_simulator.py - IoT Device Simulation
# =============================================================================

import random
import time
import threading
from datetime import datetime, timedelta
import json

class IoTSimulator:
    def __init__(self):
        self.devices = {}
        self.running = False
        self.simulation_thread = None
        
    def register_device(self, device_id, device_type, room_id):
        """Register a new IoT device"""
        self.devices[device_id] = {
            'type': device_type,
            'room_id': room_id,
            'status': 'online',
            'last_ping': datetime.now(),
            'properties': self._get_device_properties(device_type)
        }
    
    def _get_device_properties(self, device_type):
        """Get device-specific properties"""
        properties = {
            'ac': {
                'temperature_setpoint': 24.0,
                'current_temperature': 26.0,
                'fan_speed': 'medium',
                'mode': 'cool'
            },
            'fan': {
                'speed': 3,
                'max_speed': 5,
                'oscillation': False
            },
            'light': {
                'brightness': 80,
                'color_temperature': 4000
            },
            'projector': {
                'brightness': 2000,
                'resolution': '1920x1080',
                'lamp_hours': random.randint(100, 5000)
            },
            'computer': {
                'cpu_usage': random.randint(10, 80),
                'memory_usage': random.randint(20, 90),
                'temperature': random.randint(35, 65)
            }
        }
        
        return properties.get(device_type, {})
    
    def start_simulation(self):
        """Start IoT device simulation"""
        if self.running:
            return
            
        self.running = True
        self.simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.simulation_thread.start()
    
    def stop_simulation(self):
        """Stop IoT device simulation"""
        self.running = False
    
    def _simulation_loop(self):
        """Main simulation loop"""
        while self.running:
            for device_id, device in self.devices.items():
                # Simulate device heartbeat
                device['last_ping'] = datetime.now()
                
                # Simulate random property changes
                self._update_device_properties(device_id, device)
                
                # Simulate occasional offline status
                if random.random() < 0.001:  # 0.1% chance of going offline
                    device['status'] = 'offline'
                elif device['status'] == 'offline' and random.random() < 0.1:  # 10% chance of coming back online
                    device['status'] = 'online'
            
            time.sleep(30)  # Update every 30 seconds
    
    def _update_device_properties(self, device_id, device):
        """Update device properties with realistic variations"""
        device_type = device['type']
        properties = device['properties']
        
        if device_type == 'ac':
            # Simulate temperature changes
            if 'current_temperature' in properties:
                target = properties.get('temperature_setpoint', 24.0)
                current = properties['current_temperature']
                # Move towards setpoint with some randomness
                diff = target - current
                properties['current_temperature'] = current + (diff * 0.1) + random.uniform(-0.5, 0.5)
                properties['current_temperature'] = max(18, min(35, properties['current_temperature']))
        
        elif device_type == 'computer':
            # Simulate varying CPU and memory usage
            properties['cpu_usage'] = max(5, min(100, properties['cpu_usage'] + random.randint(-10, 10)))
            properties['memory_usage'] = max(10, min(95, properties['memory_usage'] + random.randint(-5, 5)))
            properties['temperature'] = max(30, min(80, properties['temperature'] + random.randint(-2, 2)))
        
        elif device_type == 'projector':
            # Simulate lamp hour accumulation
            if device.get('is_on', False):
                properties['lamp_hours'] += 0.5  # Add 30 minutes
    
    def control_device(self, device_id, action, parameters=None):
        """Send control command to IoT device (simulation)"""
        if device_id not in self.devices:
            return {'success': False, 'message': 'Device not found'}
        
        device = self.devices[device_id]
        
        if device['status'] == 'offline':
            return {'success': False, 'message': 'Device is offline'}
        
        # Simulate command processing delay
        time.sleep(0.1)
        
        # Process different actions
        if action == 'turn_on':
            device['is_on'] = True
            return {'success': True, 'message': 'Device turned ON'}
        
        elif action == 'turn_off':
            device['is_on'] = False
            return {'success': True, 'message': 'Device turned OFF'}
        
        elif action == 'set_temperature' and device['type'] == 'ac':
            if parameters and 'temperature' in parameters:
                temp = float(parameters['temperature'])
                if 16 <= temp <= 30:
                    device['properties']['temperature_setpoint'] = temp
                    return {'success': True, 'message': f'Temperature set to {temp}°C'}
                else:
                    return {'success': False, 'message': 'Temperature out of range (16-30°C)'}
        
        elif action == 'set_speed' and device['type'] == 'fan':
            if parameters and 'speed' in parameters:
                speed = int(parameters['speed'])
                max_speed = device['properties']['max_speed']
                if 0 <= speed <= max_speed:
                    device['properties']['speed'] = speed
                    return {'success': True, 'message': f'Fan speed set to {speed}'}
                else:
                    return {'success': False, 'message': f'Speed out of range (0-{max_speed})'}
        
        elif action == 'set_brightness' and device['type'] == 'light':
            if parameters and 'brightness' in parameters:
                brightness = int(parameters['brightness'])
                if 0 <= brightness <= 100:
                    device['properties']['brightness'] = brightness
                    return {'success': True, 'message': f'Brightness set to {brightness}%'}
                else:
                    return {'success': False, 'message': 'Brightness out of range (0-100%)'}
        
        return {'success': False, 'message': 'Unknown action or invalid parameters'}
    
    def get_device_status(self, device_id):
        """Get current device status"""
        if device_id not in self.devices:
            return None
        
        device = self.devices[device_id].copy()
        device['last_seen'] = (datetime.now() - device['last_ping']).total_seconds()
        
        return device
    
    def get_all_devices_status(self):
        """Get status of all registered devices"""
        return {dev_id: self.get_device_status(dev_id) for dev_id in self.devices.keys()}
    
    def simulate_sensor_readings(self, room_id):
        """Simulate sensor readings for a room"""
        # Base readings with some randomness
        temperature = random.uniform(20, 30)
        humidity = random.uniform(40, 70)
        air_quality = random.randint(50, 100)
        
        # Motion detection based on time of day
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 18:  # Business hours
            motion_probability = 0.7
            people_count = random.randint(0, 10)
        elif 18 <= current_hour <= 22:  # Evening
            motion_probability = 0.3
            people_count = random.randint(0, 3)
        else:  # Night time
            motion_probability = 0.1
            people_count = random.randint(0, 1)
        
        motion_detected = random.random() < motion_probability
        
        return {
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'air_quality': air_quality,
            'motion_detected': motion_detected,
            'people_count': people_count if motion_detected else 0,
            'timestamp': datetime.now().isoformat()
        }