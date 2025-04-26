from Chain.model.model import Model
from Chain.react.ReACT import ReACT


# Our tools
def scale_ingredients(recipe: dict[str, float], servings: float) -> dict[str, float]:
    """
    Scale recipe ingredients for desired number of servings
    Recipe should be dict of ingredient_name: amount_in_grams
    Example: {'flour': 250.0, 'sugar': 100.0, 'butter': 115.0}
    Returns scaled amounts in grams
    """
    scale_factor = servings / recipe.get("original_servings", 1)
    scaled = {}
    for ingredient, amount in recipe.items():
        if ingredient != "original_servings":
            scaled[ingredient] = round(amount * scale_factor, 1)
    return scaled


def calculate_nutrition(ingredients: dict[str, float]) -> dict[str, float]:
    """
    Calculate nutrition facts for recipe
    Ingredients should be dict of ingredient_name: amount_in_grams
    Example: {'flour': 250.0, 'sugar': 100.0, 'butter': 115.0}
    Returns dict of nutrition values per serving:
    {'calories': float, 'protein': float, 'carbs': float, 'fat': float}
    """
    # Simplified nutrition values per 100g
    nutrition_db = {
        "flour": {"calories": 364, "protein": 10, "carbs": 76, "fat": 1},
        "sugar": {"calories": 387, "protein": 0, "carbs": 100, "fat": 0},
        "butter": {"calories": 717, "protein": 0.9, "carbs": 0, "fat": 81},
        # Add more ingredients as needed
    }

    totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    for ingredient, amount in ingredients.items():
        if ingredient in nutrition_db:
            ratio = amount / 100  # Convert to 100g units
            for nutrient in totals:
                totals[nutrient] += nutrition_db[ingredient][nutrient] * ratio

    return {k: round(v, 1) for k, v in totals.items()}


def check_substitutions(
    ingredients: dict[str, float], allergies: list[str]
) -> dict[str, str]:
    """
    Suggest substitutions for allergens
    Ingredients should be dict of ingredient_name: amount_in_grams
    Allergies should be list of strings: ['dairy', 'gluten', 'nuts']
    Returns dict of ingredient: substitution_suggestion
    """
    allergen_map = {
        "dairy": ["milk", "butter", "cream", "cheese", "yogurt"],
        "gluten": ["flour", "wheat", "barley", "rye"],
        "nuts": ["almond", "walnut", "pecan", "peanut"],
    }

    substitutions = {
        "butter": "plant-based butter or coconut oil",
        "milk": "almond milk or oat milk",
        "flour": "gluten-free flour blend",
        "cream": "coconut cream",
        "cheese": "dairy-free cheese alternative",
    }

    needed_subs = {}
    for ingredient in ingredients:
        for allergy in allergies:
            if ingredient in allergen_map.get(allergy, []):
                if ingredient in substitutions:
                    needed_subs[ingredient] = substitutions[ingredient]

    return needed_subs


if __name__ == "__main__":
    # Our specific scenario
    input = "Recipe ingredients and dietary requirements."
    output = "Scaled recipe with nutrition info and substitutions."
    prompt = """Scale this pizza recipe (serves 2) for 6 people and check for dairy allergies:
   - Flour: 250g
   - Water: 150g
   - Yeast: 7g
   - Salt: 5g
   - Olive Oil: 15g
   - Mozzarella: 200g
   - Tomato Sauce: 150g"""

    tools = [scale_ingredients, calculate_nutrition, check_substitutions]
    model = Model("gpt")
    react = ReACT(input, output, tools, model)
    react.query(prompt)
