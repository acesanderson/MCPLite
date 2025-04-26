from Chain.model.model import Model
from Chain.react.ReACT import ReACT


# Our tools
def calculate_returns(investments: list[dict[str, float]], timeframe: int) -> float:
    """
    Calculate total return percentage over specified timeframe in years
    Each investment dict should have {'initial_value': float, 'current_value': float}
    Example: [
        {'initial_value': 10000.0, 'current_value': 12000.0},
        {'initial_value': 5000.0, 'current_value': 5500.0}
    ]
    Returns annualized return as percentage (e.g., 7.5 for 7.5%)
    """
    total_initial = sum(inv["initial_value"] for inv in investments)
    total_current = sum(inv["current_value"] for inv in investments)
    if timeframe <= 0 or total_initial <= 0:
        raise ValueError("Timeframe must be positive and initial values must be > 0")
    return round(((total_current / total_initial) ** (1 / timeframe) - 1) * 100, 2)


def assess_risk_level(portfolio: dict[str, float]) -> str:
    """
    Analyze portfolio risk level based on allocation percentages
    Portfolio should be dict of asset_type: allocation_percentage
    Example: {'stocks': 70.0, 'bonds': 20.0, 'cash': 10.0}
    Returns risk level as string: 'Conservative', 'Moderate', or 'Aggressive'
    """
    stock_allocation = portfolio.get("stocks", 0) + portfolio.get("equities", 0)
    if stock_allocation >= 70:
        return "Aggressive"
    elif stock_allocation >= 40:
        return "Moderate"
    else:
        return "Conservative"


def calculate_diversification_score(portfolio: dict[str, float]) -> float:
    """
    Score portfolio diversification from 0-1
    Portfolio should be dict of asset_type: allocation_percentage
    Example: {'US_stocks': 60.0, 'intl_stocks': 30.0, 'bonds': 10.0}
    Returns score where 1.0 is well diversified and 0.0 is poorly diversified
    Scores based on:
    - Geographic diversity
    - Asset class diversity
    - No single position > 40%
    """
    # Check for over-concentration
    if max(portfolio.values()) > 40:
        return round(0.5, 2)

    # Check geographic diversity
    us_exposure = portfolio.get("US_stocks", 0)
    intl_exposure = portfolio.get("intl_stocks", 0)

    # Check asset class diversity
    stocks = us_exposure + intl_exposure
    bonds = portfolio.get("bonds", 0)

    # Calculate score based on balance
    score = 1.0
    if us_exposure / max(stocks, 1) > 0.8:  # Over-concentrated in US
        score *= 0.8
    if stocks > 90 or bonds > 90:  # Over-concentrated in one asset class
        score *= 0.7

    return round(score, 2)


def recommend_rebalancing(
    current_allocation: dict[str, float], target_allocation: dict[str, float]
) -> dict[str, float]:
    """
    Suggest trades to match target allocation
    Both dictionaries should have asset_type: allocation_percentage
    Example:
    current = {'US_stocks': 50.0, 'intl_stocks': 30.0, 'bonds': 20.0}
    target = {'US_stocks': 60.0, 'intl_stocks': 30.0, 'bonds': 10.0}
    Returns dict of asset_type: percentage_change_needed
    Positive numbers indicate buy, negative indicate sell
    """
    changes = {}
    for asset in target_allocation:
        if asset not in current_allocation:
            current_allocation[asset] = 0.0
        change = target_allocation[asset] - current_allocation[asset]
        if abs(change) >= 1:  # Only suggest changes >= 1%
            changes[asset] = round(change, 1)
    return changes


if __name__ == "__main__":
    # Our specific scenario
    input = "Portfolio holdings and investment goals."
    output = "Portfolio analysis and rebalancing recommendations."
    prompt = """Analyze my portfolio: 
    Current allocation:
    - US Stocks (VTI): 50% ($50,000)
    - International Stocks (VXUS): 30% ($30,000)
    - Bonds (BND): 20% ($20,000)
    Target allocation is 60/30/10 split.
    Time horizon: 3 years"""

    tools = [
        calculate_returns,
        assess_risk_level,
        calculate_diversification_score,
        recommend_rebalancing,
    ]
    model = Model("gpt")
    react = ReACT(input, output, tools, model)
    react.query(prompt)
