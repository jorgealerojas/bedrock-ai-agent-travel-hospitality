import os
import json
from typing import Dict, List
from typing_extensions import Annotated

from serpapi import GoogleSearch
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.event_handler.openapi.params import Query

API_KEY = os.environ.get('API_KEY')

tracer = Tracer()
logger = Logger()
app = BedrockAgentResolver()

@app.get("/check_portfolio", description="Check stock portfolio value and compare with travel budget using Google Finance")
@tracer.capture_method
def check_portfolio(
    travel_budget: Annotated[float, Query(description="Estimated travel budget to compare against portfolio value")] = None
) -> Dict:
    """Check portfolio value and compare with travel budget."""
    try:
        portfolio_str = os.environ.get('STOCK_PORTFOLIO', '{}')
        portfolio = json.loads(portfolio_str)
        
        if not portfolio:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'No portfolio configured'
                })
            }
        
        total_value = 0
        stock_values = {}
        
        for symbol, quantity in portfolio.items():
            params = {
                "engine": "google_finance",
                "q": symbol,
                "api_key": API_KEY
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if results.get('error'):
                logger.error(f"Error fetching price for {symbol}: {results['error']}")
                continue
                
            try:
                price = float(results.get('price', 0))
                value = price * quantity
                total_value += value
                stock_values[symbol] = {
                    'quantity': quantity,
                    'price': price,
                    'value': value
                }
            except (KeyError, ValueError) as e:
                logger.error(f"Error processing price for {symbol}: {str(e)}")
                continue
        
        result = {
            'total_value': total_value,
            'stocks': stock_values
        }
        
        if travel_budget is not None:
            result.update({
                'can_afford_travel': total_value >= travel_budget,
                'travel_budget': travel_budget,
                'remaining_after_travel': total_value - float(travel_budget)
            })
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Error in portfolio checking: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f"Internal server error: {str(e)}"
            })
        }

@app.get("/calculate_shares_to_sell", description="Calculate how many shares of each stock to sell to meet a target amount")
@tracer.capture_method
def calculate_shares_to_sell(
    target_amount: Annotated[float, Query(description="The target amount needed from selling shares")],
    strategy: Annotated[str, Query(description="Strategy for selling shares: 'proportional' (sell equal percentage from each), 'minimize_tax_impact' (prioritize long-term holdings), or 'single_stock' (sell from highest value stock first)")] = "proportional"
) -> Dict:
    """Calculate which shares to sell to meet a target amount."""
    try:
        portfolio_str = os.environ.get('STOCK_PORTFOLIO', '{}')
        portfolio = json.loads(portfolio_str)
        
        if not portfolio:
            return {
                'error': 'No portfolio configured',
                'shares_to_sell': {}
            }
        
        # Get current prices and values
        stock_values = {}
        total_value = 0
        
        for symbol, quantity in portfolio.items():
            params = {
                "engine": "google_finance",
                "q": symbol,
                "api_key": API_KEY
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if results.get('error'):
                logger.error(f"Error fetching price for {symbol}: {results['error']}")
                continue
                
            try:
                price = float(results.get('price', 0))
                value = price * quantity
                total_value += value
                stock_values[symbol] = {
                    'quantity': quantity,
                    'price': price,
                    'value': value
                }
            except (KeyError, ValueError) as e:
                logger.error(f"Error processing price for {symbol}: {str(e)}")
                continue
        
        if target_amount > total_value:
            return {
                'error': f'Insufficient portfolio value ({total_value}) to meet target amount ({target_amount})',
                'shares_to_sell': {}
            }
        
        shares_to_sell = {}
        
        if strategy == "proportional":
            # Sell equal percentage from each stock
            percentage_to_sell = target_amount / total_value
            for symbol, data in stock_values.items():
                shares = data['quantity']
                price = data['price']
                shares_to_sell[symbol] = {
                    'shares': round(shares * percentage_to_sell, 2),
                    'estimated_value': round(shares * percentage_to_sell * price, 2)
                }
        
        elif strategy == "single_stock":
            # Sort stocks by value and sell from highest value first
            sorted_stocks = sorted(stock_values.items(), key=lambda x: x[1]['value'], reverse=True)
            remaining_target = target_amount
            
            for symbol, data in sorted_stocks:
                if remaining_target <= 0:
                    break
                    
                max_value = data['value']
                shares = data['quantity']
                price = data['price']
                
                if max_value >= remaining_target:
                    shares_needed = remaining_target / price
                    shares_to_sell[symbol] = {
                        'shares': round(shares_needed, 2),
                        'estimated_value': round(shares_needed * price, 2)
                    }
                    remaining_target = 0
                else:
                    shares_to_sell[symbol] = {
                        'shares': shares,
                        'estimated_value': max_value
                    }
                    remaining_target -= max_value
        
        return {
            'target_amount': target_amount,
            'strategy': strategy,
            'shares_to_sell': shares_to_sell,
            'total_portfolio_value': total_value,
            'remaining_value': total_value - target_amount
        }
        
    except Exception as e:
        logger.error(f"Error calculating shares to sell: {str(e)}")
        return {
            'error': f"Internal server error: {str(e)}",
            'shares_to_sell': {}
        }

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext):
    """Main Lambda handler."""
    return app.resolve(event, context)

if __name__ == "__main__":
    # This displays the autogenerated openapi schema
    print(
        app.get_openapi_json_schema(
            title="Portfolio Checker API",
            version="1.0.0",
            description="API for checking stock portfolio value and comparing with travel costs",
            tags=["finance", "portfolio", "stocks"],
        ),
    ) 