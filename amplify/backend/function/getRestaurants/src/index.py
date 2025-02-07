import json
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration AWS
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

if not aws_access_key_id or not aws_secret_access_key:
    raise ValueError("Les variables d'environnement AWS ne sont pas définies correctement.")

# Connexion à DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name='eu-west-1'
)

table_restos = dynamodb.Table('restaurants-dev')

def get_restaurants_from_dynamodb():
    restos = []
    response = table_restos.scan()  
    
    for item in response.get('Items', []):
        restos.append({
            'id': item.get('id', 'N/A'),
            'name': item.get('name', 'N/A'),
        })
    
    return restos

def handler(event, context):
    try:
        restos = get_restaurants_from_dynamodb()
        return {
            'statusCode': 200,
            'body': json.dumps({'restaurants': restos}, ensure_ascii=False)
        }
    except Exception as e:
        print(f"🚨 Erreur : {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Erreur interne', 'error': str(e)})
        }

import http.client

def send_to_api(restaurants):
    API_HOST = "1tk1tcoxg9.execute-api.eu-west-1.amazonaws.com" 
    API_PATH = "/getRestaurants"  

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        conn = http.client.HTTPSConnection(API_HOST)
        payload = json.dumps({"restaurants": restaurants})

        conn.request("POST", API_PATH, body=payload, headers=headers)
        response = conn.getresponse()
        data = response.read().decode()

        conn.close()
        return json.loads(data)
    
    except Exception as e:
        print(f"Erreur lors de l'envoi des données : {e}")
        return None