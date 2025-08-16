import requests
from loguru import logger

def send_sensor_data(sensor_name: str, data: dict):
    """
    Sends sensor data to the relay server.
    """
    try:
        url = f"http://localhost:10240/api/sensor/{sensor_name}"
        response = requests.post(url, json=data)
        response.raise_for_status()
        logger.debug(f"Successfully sent data for sensor '{sensor_name}'. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending data for sensor '{sensor_name}': {e}")