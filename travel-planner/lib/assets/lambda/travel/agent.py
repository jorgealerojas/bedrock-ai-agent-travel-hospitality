import os

from typing import List, Dict
from typing_extensions import Annotated

from serpapi import GoogleSearch
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler.openapi.params import Query
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
    num_passengers: Annotated[int, Query(description="Number of passengers traveling")] = 1,
) -> Dict:
    
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

    logger.info(f"params: {params}")

    search = GoogleSearch(params)
    results = search.get_dict()

    logger.info(f"response: {results}")

    if results.get('error'):
        output = {
            'error': results['error'] + " Ask the user for more information related to the context received about the function.",
            'total_cost': 0
        }
    elif results.get("best_flights"):
        flights = results.get("best_flights")
        # Calculate total cost for all passengers
        total_cost = sum(float(flight.get('price', '0').replace('$', '').replace(',', '')) for flight in flights) * num_passengers
        output = {
            'flights': flights,
            'num_passengers': num_passengers,
            'total_cost': total_cost,
            'per_passenger_cost': total_cost / num_passengers
        }
    elif results.get("other_flights"):
        flights = results.get("other_flights")
        total_cost = sum(float(flight.get('price', '0').replace('$', '').replace(',', '')) for flight in flights) * num_passengers
        output = {
            'flights': flights,
            'num_passengers': num_passengers,
            'total_cost': total_cost,
            'per_passenger_cost': total_cost / num_passengers
        }
    else:
        output = {
            'error': "Unknown Error.",
            'total_cost': 0
        }
    return output


@app.get("/get_hotels", description="Gets hotels properties from Google Hotels")
@tracer.capture_method
def get_hotels(
    q: Annotated[str, Query(description="Parameter defines the location. e.g. Bali Resorts")], 
    check_in_date: Annotated[str, Query(description="Parameter defines the check-in date. The format is YYYY-MM-DD. e.g. 2024-02-10")], 
    check_out_date: Annotated[str, Query(description="Parameter defines the check-out date. The format is YYYY-MM-DD. e.g. 2024-02-10")], 
    num_rooms: Annotated[int, Query(description="Number of rooms needed")] = 1,
    adults: Annotated[int, Query(description="Number of adults per room")] = 2,
    country_search: Annotated[str, Query(description="Parameter defines the country to use for the Google Hotels search. It's a two-letter country code.")] = "us"
) -> Dict:
    params = {
        "engine": "google_hotels",
        "q": q,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "adults": str(adults),
        "currency": "USD",
        "gl": country_search.lower(),
        "hl": "en",
        "api_key": API_KEY
    }

    logger.info(f"params: {params}")
    
    search = GoogleSearch(params)
    results = search.get_dict()

    logger.info(f'response: {results}')

    if results.get('error'):
        return {
            'error': results['error'] + " Ask the user for more information related to the context received about the function.",
            'total_cost': 0
        }
    elif results.get("properties"):
        properties = results.get("properties")[0:2] if len(results.get("properties", [])) > 2 else results.get("properties")
        # Calculate total cost for all rooms
        total_cost = sum(float(prop.get('price', '0').replace('$', '').replace(',', '')) for prop in properties) * num_rooms
        return {
            'properties': properties,
            'num_rooms': num_rooms,
            'adults_per_room': adults,
            'total_cost': round(total_cost, 2),
            'per_room_cost': round(total_cost / num_rooms if num_rooms > 0 else 0, 2)
        }
    else:
        return {
            'error': "Unknown Error.",
            'total_cost': 0
        }


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