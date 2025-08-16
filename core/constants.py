from enum import Enum

class QueueNames(str, Enum):
    MAIN = "main"
    MAIN_RESPONSE = "main_response"
    HEART = "heart"
    STEP_MOTOR = "step_motor"
    WHEEL = "wheel"
    RADAR = "radar"