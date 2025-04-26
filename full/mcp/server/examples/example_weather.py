from Chain.model.model import Model
from Chain.react.ReACT import ReACT


# Our tools
def convert_temperature(celsius: float) -> float:
    """Convert celsius to fahrenheit"""
    return (celsius * 9 / 5) + 32


def calculate_wind_chill(temp_fahrenheit: float, wind_speed_mph: float) -> float:
    """
    Calculate wind chill using the NWS formula
    Valid for temperatures <= 50°F and wind speeds >= 3 mph
    """
    if temp_fahrenheit > 50 or wind_speed_mph < 3:
        return temp_fahrenheit

    wind_chill = (
        35.74
        + (0.6215 * temp_fahrenheit)
        - (35.75 * wind_speed_mph**0.16)
        + (0.4275 * temp_fahrenheit * wind_speed_mph**0.16)
    )
    return round(wind_chill, 1)


def get_clothing_recommendation(felt_temp: float) -> str:
    """Get clothing recommendations based on the felt temperature"""
    if felt_temp < 0:
        return "Heavy winter coat, layers, gloves, winter hat, and insulated boots required"
    elif felt_temp < 32:
        return "Winter coat, hat, gloves, and warm layers recommended"
    elif felt_temp < 45:
        return "Light winter coat or heavy jacket recommended"
    elif felt_temp < 60:
        return "Light jacket or sweater recommended"
    else:
        return "Light clothing suitable"


if __name__ == "__main__":
    # Our specific scenario
    input = "Facts about the current weather."
    output = "Clothing recommendations."
    prompt = "What should I wear for -5°C weather with 10 mph winds?"
    tools = [convert_temperature, calculate_wind_chill, get_clothing_recommendation]
    model = Model("gpt")
    react = ReACT(input, output, tools, model)
    react.query(prompt)
