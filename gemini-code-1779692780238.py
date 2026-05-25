import math

def calculate_flight_time(distance_m: float, v_max: float, acceleration: float, jerk: float) -> float:
    """
    Computes single-trip transit times across given floor distance blocks.
    Protects calculations from zero/negative parameters.
    """
    if distance_m <= 0: 
        return 0.0
    v_max, acceleration, jerk = max(v_max, 0.1), max(acceleration, 0.1), max(jerk, 0.1)
    
    # Check if lift can reach full velocity profile prior to deceleration phase boundary
    distance_to_reach_speed = (v_max ** 2 / acceleration) + (v_max * (acceleration / jerk))
    if distance_m >= distance_to_reach_speed:
        return (distance_m / v_max) + (v_max / acceleration) + (acceleration / jerk)
    
    return 2 * math.sqrt(distance_m / acceleration) + (acceleration / jerk)