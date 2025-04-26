from Chain.model.model import Model
from Chain.react.ReACT import ReACT


def calculate_subtotal(items: list[dict]) -> float:
    """
    Calculate the total cost of all items before tax and tip
    Each item should be a dictionary with {'price': float}
    Example: [{'price': 15.99}, {'price': 24.00}, {'price': 8.50}]
    """
    return round(sum(item["price"] for item in items), 2)


def calculate_tax(subtotal: float, tax_rate: float) -> float:
    """
    Calculate tax amount for the bill
    Valid for tax_rate as percentage (e.g. 8.25 for 8.25%)
    """
    return round(subtotal * (tax_rate / 100), 2)


def calculate_tip(subtotal: float, service_rating: int) -> float:
    """
    Calculate recommended tip based on service rating
    Valid for service_rating from 1-5
    Returns tip amount based on:
    1-2: 15%
    3: 18%
    4: 20%
    5: 25%
    """
    if not 1 <= service_rating <= 5:
        raise ValueError("Service rating must be between 1 and 5")

    tip_rates = {1: 0.15, 2: 0.15, 3: 0.18, 4: 0.20, 5: 0.25}
    return round(subtotal * tip_rates[service_rating], 2)


if __name__ == "__main__":
    # Our specific scenario
    input = "Restaurant bill items and service quality."
    output = "Complete bill breakdown with tax and recommended tip."
    prompt = """Calculate the final bill for:
    - Pasta ($15.99)
    - Wine ($24.00)
    - Salad ($8.50)
    with 8.25% tax and a service rating of 4/5"""

    tools = [calculate_subtotal, calculate_tax, calculate_tip]
    model = Model("gpt")
    react = ReACT(input, output, tools, model)
    react.query(prompt)
