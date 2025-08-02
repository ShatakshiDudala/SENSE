# =============================================================================
# 2. utils.py - Helper Functions
# =============================================================================

import datetime
import logging
import json
import random

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('sense.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def get_current_time():
    """Get current timestamp"""
    return datetime.datetime.now()

def format_time(dt):
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def calculate_power_consumption(device_type, hours_on):
    """Calculate power consumption in kWh"""
    power_ratings = {
        'ac': 1.5,      # 1.5 kW per hour
        'fan': 0.075,   # 75W per hour
        'light': 0.02,  # 20W per hour
        'projector': 0.3, # 300W per hour
        'computer': 0.15  # 150W per hour
    }
    return power_ratings.get(device_type, 0) * hours_on

def generate_sensor_data():
    """Generate realistic sensor data"""
    return {
        'temperature': round(random.uniform(20, 30), 1),
        'humidity': round(random.uniform(40, 70), 1),
        'motion': random.choice([True, False]),
        'people_count': random.randint(0, 10),
        'air_quality': random.randint(50, 100)
    }

def log_activity(user, action, details):
    """Log user activities"""
    logger = setup_logging()
    logger.info(f"User: {user}, Action: {action}, Details: {details}")
