from Chain.model.model import Model
from Chain.react.ReACT import ReACT


# Our tools
def check_growing_season(plant: str, zone: int, month: int) -> bool:
    """
    Determine if it's the right time to plant
    plant: common plant name (e.g., 'tomato', 'basil', 'lettuce')
    zone: USDA hardiness zone (1-13)
    month: numeric month (1-12)
    Returns True if it's a good time to plant, False otherwise
    """
    planting_calendar = {
        "tomato": {
            "zones": range(3, 11),
            "months": {  # Different months for different zone ranges
                range(3, 7): [4, 5, 6],  # Cooler zones: plant in spring
                range(7, 11): [2, 3, 4],  # Warmer zones: plant in late winter
            },
        },
        "basil": {
            "zones": range(3, 11),
            "months": {range(3, 11): [4, 5, 6]},  # Plant in spring after last frost
        },
        "lettuce": {
            "zones": range(3, 11),
            "months": {
                range(3, 7): [3, 4, 9],  # Spring and fall for cooler zones
                range(7, 11): [9, 10, 11],  # Fall/winter for warmer zones
            },
        },
        # Add more plants as needed
    }

    if plant not in planting_calendar:
        raise ValueError(f"Plant '{plant}' not found in database")
    if not 1 <= month <= 12:
        raise ValueError("Month must be between 1 and 12")
    if not 1 <= zone <= 13:
        raise ValueError("Zone must be between 1 and 13")

    plant_info = planting_calendar[plant]
    if zone not in plant_info["zones"]:
        return False

    for zone_range, valid_months in plant_info["months"].items():
        if zone in zone_range and month in valid_months:
            return True
    return False


def calculate_spacing(plant: str, width: float, length: float) -> dict[str, int]:
    """
    Calculate garden layout based on plant spacing needs
    plant: common plant name (e.g., 'tomato', 'basil', 'lettuce')
    width: garden width in feet
    length: garden length in feet
    Returns dict with:
    {
        'plants_per_row': int,
        'number_of_rows': int,
        'total_plants': int
    }
    """
    spacing_needs = {
        "tomato": {"between_plants": 2.0, "between_rows": 3.0},
        "basil": {"between_plants": 1.0, "between_rows": 1.0},
        "lettuce": {"between_plants": 0.75, "between_rows": 1.0},
        # Add more plants as needed
    }

    if plant not in spacing_needs:
        raise ValueError(f"Plant '{plant}' not found in database")

    space = spacing_needs[plant]
    plants_per_row = int(width / space["between_plants"])
    number_of_rows = int(length / space["between_rows"])
    total_plants = plants_per_row * number_of_rows

    return {
        "plants_per_row": plants_per_row,
        "number_of_rows": number_of_rows,
        "total_plants": total_plants,
    }


def estimate_water_needs(plants: list[dict[str, int]], soil_type: str) -> float:
    """
    Estimate daily water needs in gallons
    plants: list of dicts with {'plant': str, 'count': int}
    Example: [{'plant': 'tomato', 'count': 4}, {'plant': 'basil', 'count': 6}]
    soil_type: 'sandy', 'loamy', or 'clay'
    Returns gallons of water needed per day
    """
    water_needs = {
        "tomato": 1.0,  # Gallons per plant per day base rate
        "basil": 0.25,
        "lettuce": 0.15,
        # Add more plants as needed
    }

    soil_factors = {
        "sandy": 1.2,  # Needs more frequent watering
        "loamy": 1.0,  # Ideal water retention
        "clay": 0.8,  # Retains water longer
    }

    if soil_type not in soil_factors:
        raise ValueError("Soil type must be 'sandy', 'loamy', or 'clay'")

    total_water = 0.0
    for plant_info in plants:
        if plant_info["plant"] not in water_needs:
            raise ValueError(f"Plant '{plant_info['plant']}' not found in database")
        total_water += water_needs[plant_info["plant"]] * plant_info["count"]

    return round(total_water * soil_factors[soil_type], 1)


if __name__ == "__main__":
    # Our specific scenario
    input = "Garden specifications and plant choices."
    output = "Planting plan and care instructions."
    prompt = """I have an 8x12ft garden in zone 6, sandy soil. 
   How should I plant tomatoes and basil in April?"""

    tools = [check_growing_season, calculate_spacing, estimate_water_needs]
    model = Model("gpt")
    react = ReACT(input, output, tools, model)
    react.query(prompt)
