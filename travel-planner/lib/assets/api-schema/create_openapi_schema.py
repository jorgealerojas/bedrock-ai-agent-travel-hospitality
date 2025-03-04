import os
import json

from typing import List, Dict
from typing_extensions import Annotated

from serpapi import GoogleSearch
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler.openapi.params import Query, Body
from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

API_KEY = os.environ.get('API_KEY')

tracer = Tracer()
logger = Logger()
app = BedrockAgentResolver()


@app.get("/get_flights", description="Gets best flight results from Google Flights")
@tracer.capture_method
def get_flights(
    departure_id: Annotated[str, Query(description="Parameter defines the departure airport code or location kgmid. An airport code is an uppercase 3-letter code. For example, CDG is Paris Charles de Gaulle Airport and AUS is Austin-Bergstrom International Airport.")], 
    arrival_id: Annotated[str, Query(description="Parameter defines the arrival airport code or location kgmid. An airport code is an uppercase 3-letter code. For example, CDG is Paris Charles de Gaulle Airport and AUS is Austin-Bergstrom International Airport.")], 
    outbound_date: Annotated[str, Query(description="Parameter defines the outbound date. The format is YYYY-MM-DD. e.g. 2024-02-08")], 
    return_date: Annotated[str, Query(description="Parameter defines the return date. The format is YYYY-MM-DD. e.g. 2024-02-08")],
) -> List[dict]:
    
    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "currency": "USD",
        "hl": "en",
        "api_key": API_KEY
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    if results.get('error'):
        output = results['error'] + "Ask the user for more information related to the context received about the function."
    elif results.get("best_flights"):
        output = results.get("best_flights")
    elif results.get("other_flights"):
        output = results.get("other_flights")
    else:
        output = results + "Unknown Error."
    return output


@app.get("/get_hotels", description="Gets hotels properties from Google Hotels")
@tracer.capture_method
def get_hotels(
    q: Annotated[str, Query(description="Parameter defines the location. e.g. Bali Resorts")], 
    check_in_date: Annotated[str, Query(description="Parameter defines the check-in date. The format is YYYY-MM-DD. e.g. 2024-02-10")], 
    check_out_date: Annotated[str, Query(description="Parameter defines the check-out date. The format is YYYY-MM-DD. e.g. 2024-02-10")], 
    adults: Annotated[str, Query(description="Parameter defines the number of adults")] = "",
    country_search: Annotated[str, Query(description="Parameter defines the country to use for the Google Hotels search. It's a two-letter country code. (e.g., us for the United States, uk for United Kingdom, or fr for France) Head to the Google countries page for a full list of supported Google countries.")] = "us"
) -> List[dict]:
    
    params = {
      "engine": "google_hotels",
      "q": q,
      "check_in_date": check_in_date,
      "check_out_date": check_out_date,
      "adults": adults,
      "currency": "USD",
      "gl": country_search.lower(),
      "hl": "en",
      "api_key": API_KEY
    }
    
    logger.info(f'params: {params}')
    search = GoogleSearch(params)
    results = search.get_dict()
    logger.info(f'all results: {results}')
    if results.get('error'):
        output = results['error'] + "Ask the user for more information related to the context received about the function."
    elif results.get("properties"):
        output = results.get("properties")[0:2] if len(results) > 2 else results.get("properties")
    else:
        output = results + "Unknown Error."
        
    logger.info(f'results: {output}')
    return output


@app.post("/check_portfolio", description="Check stock portfolio value and compare with travel budget using Google Finance")
@tracer.capture_method
def check_portfolio(
    travel_budget: Annotated[float, Query(description="Estimated travel budget to compare against portfolio value")] = None
) -> Dict:
    portfolio_str = os.environ.get('STOCK_PORTFOLIO', '{}')
    portfolio = json.loads(portfolio_str)
    
    if not portfolio:
        return {
            'error': 'No portfolio configured'
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
            price = float(results['price'])
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
            'remaining_after_travel': total_value - travel_budget
        })
    
    return result


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)


if __name__ == "__main__":
    # This displays the autogenerated openapi schema by aws_lambda_powertools
    print(
        app.get_openapi_json_schema(
            title="Travel Planner Bot API",
            version="1.0.0",
            description="Travel Planner API for searching the best flight and hotel deals",
            tags=["travel", "flights", "hotels"],
        ),
    )