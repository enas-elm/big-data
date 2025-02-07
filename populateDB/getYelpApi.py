import boto3
import requests
from dotenv import load_dotenv
import os

load_dotenv() 

yel_api_key = os.getenv('YELP_API_KEY')

dynamoDB = boto3.client('dynamodb')

def get_restaurants(location, term="restaurant"):
    try:
        yelpApiHeaders = {
            'Authorization': f'Bearer {yel_api_key}',
            'Content-Type': 'application/json',
        }
        
        response = requests.get(
            f"https://api.yelp.com/v3/businesses/search",
            headers=yelpApiHeaders,
            params={'location': location, 'term': term, 'limit': 10}
        )
        response.raise_for_status()
        return response.json().get('businesses', [])
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des restaurants : {e}")
        return []


def add_restaurant(restaurant):
    try:
        response = dynamoDB.put_item(
            TableName="restos-dev",
            Item={
                'id': {'S': restaurant['id']},
                'name': {'S': restaurant['alias']},  
            }
        )
        print(f"Restaurant ajouté : {restaurant['name']}")
        return response
    except Exception as e:
        print(f"Erreur lors de l'ajout du restaurant : {e}")
        return None


def main():
    restaurants = get_restaurants('paris')
    
    if not restaurants:
        print("Aucun restaurant trouvé.")
        return
    
    for restaurant in restaurants:
        add_restaurant(restaurant)


if __name__ == "__main__":
    main()
