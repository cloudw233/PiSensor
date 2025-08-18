from enum import Enum

class QueueNames(Enum):
    MAIN = "main"
    MAIN_RESPONSE = "main_response"
    HEART = "heart"
    STEP_MOTOR = "step_motor"
    WHEEL = "wheel"
    RADAR = "radar"
    HUMITURE = "humiture"
    LOCATOR = "locator"
    SMBUS = "smbus"
    URGENT_BUTTON = "urgent_button"