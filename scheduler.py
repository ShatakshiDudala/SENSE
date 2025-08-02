# =============================================================================
# 6. scheduler.py - Background Scheduling System
# =============================================================================

import threading
import time
import schedule
from datetime import datetime, timedelta
from control import DeviceController
from db import SenseDB
from utils import generate_sensor_data

class SenseScheduler:
    def __init__(self):
        self.db = SenseDB()
        self.controller = DeviceController()
        self.running = False
        self.scheduler_thread = None
        
    def start_scheduler(self):
        """Start the background scheduler"""
        if self.running:
            return
        
        self.running = True
        
        # Schedule tasks
        schedule.every(5).minutes.do(self.update_sensor_data)
        schedule.every(15).minutes.do(self.controller.auto_control_empty_rooms)
        schedule.every(1).hours.do(self.controller.ac_rotation_system)
        schedule.every(1).hours.do(self.calculate_energy_consumption)
        schedule.every(30).minutes.do(self.check_maintenance_alerts)
        schedule.every(1).minutes.do(self.update_device_runtime)
        
        # Start scheduler in background thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.running = False
        schedule.clear()
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def update_sensor_data(self):
        """Update sensor data for all rooms"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM rooms')
        rooms = cursor.fetchall()
        
        for room in rooms:
            room_id = room[0]
            sensor_data = generate_sensor_data()
            self.db.update_sensor_data(room_id, sensor_data)
        
        conn.close()
    
    def calculate_energy_consumption(self):
        """Calculate and log energy consumption"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get all devices that are currently ON
        cursor.execute('''SELECT d.id, d.room_id, d.device_type, d.power_rating, d.last_switched
                         FROM devices d
                         WHERE d.is_on = TRUE''')
        
        active_devices = cursor.fetchall()
        
        for device in active_devices:
            device_id, room_id, device_type, power_rating, last_switched = device
            
            # Calculate hours since last switched
            last_switch_time = datetime.fromisoformat(last_switched)
            hours_on = (datetime.now() - last_switch_time).total_seconds() / 3600
            
            # Calculate consumption and cost (assuming ₹8 per kWh)
            consumption = power_rating * hours_on
            cost = consumption * 8.0
            
            # Log consumption
            cursor.execute('''INSERT INTO energy_consumption 
                             (device_id, room_id, consumption_kwh, cost) 
                             VALUES (?, ?, ?, ?)''',
                          (device_id, room_id, consumption, cost))
        
        conn.commit()
        conn.close()
    
    def check_maintenance_alerts(self):
        """Check for devices due for maintenance"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get devices due for maintenance in next 7 days
        next_week = datetime.now() + timedelta(days=7)
        
        cursor.execute('''SELECT d.id, d.device_name, d.maintenance_due, r.room_number, b.name
                         FROM devices d
                         JOIN rooms r ON d.room_id = r.id
                         JOIN buildings b ON r.building_id = b.id
                         WHERE d.maintenance_due <= ? AND d.status = 'active'
                         ORDER BY d.maintenance_due''', (next_week,))
        
        due_devices = cursor.fetchall()
        
        for device in due_devices:
            # Log maintenance alert
            cursor.execute('''INSERT INTO activity_logs (user_id, action, details) 
                             VALUES (?, ?, ?)''',
                          (1, "Maintenance Alert", 
                           f"Device {device[1]} in {device[4]} - {device[3]} due for maintenance"))
        
        conn.commit()
        conn.close()
    
    def update_device_runtime(self):
        """Update device runtime hours"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''SELECT id, last_switched FROM devices WHERE is_on = TRUE''')
        active_devices = cursor.fetchall()
        
        for device in active_devices:
            device_id, last_switched = device
            last_switch_time = datetime.fromisoformat(last_switched)
            hours_on = (datetime.now() - last_switch_time).total_seconds() / 3600
            
            cursor.execute('UPDATE devices SET hours_on = hours_on + ? WHERE id = ?',
                          (hours_on, device_id))
        
        conn.commit()
        conn.close()
