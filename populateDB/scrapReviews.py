import boto3
from dotenv import load_dotenv
import os
import uuid
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from transformers import pipeline
import boto3
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


sentiment_analysis = pipeline("sentiment-analysis")

# Charger les variables d'environnement
load_dotenv()
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

table_restos = dynamodb.Table('restos-dev')
table_avis = dynamodb.Table('avis-dev')

def get_restaurants_from_dynamodb():
    restos = []
    response = table_restos.scan()
    
    for item in response.get('Items', []):
        if 'name' in item:
            restos.append({'id': item['id'], 'url': 'https://www.yelp.fr/biz/' + item['name']})
    
    return restos



# Charger les variables d'environnement
load_dotenv()
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

table_avis = dynamodb.Table('avis-dev')

def get_reviews_from_dynamodb():
    reviews = []
    response = table_avis.scan()
    
    for item in response.get('Items', []):
        if 'comment' in item:
            reviews.append(item['comment'])
    
    return reviews

def scrape_reviews_with_requests(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Erreur {response.status_code} pour {url}")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    reviews = []
    
    driver = webdriver.Chrome()
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    
    try:
        review_elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'comment__09f24__D0cxf')))
        
        for element in review_elements:
            try:
                comment_element = element.find_element(By.CLASS_NAME, "raw__09f24__T4Ezm")
                comment = comment_element.text.strip()
                if comment:
                    reviews.append(comment)
                    print(f"Avis récupéré : {comment}")
            except Exception as e:
                print(f"Erreur lors de l'extraction d'un avis : {e}")
    finally:
        driver.quit()
    
    return reviews

def add_review(restos_id, avis):
    try:
        response = table_avis.put_item(Item={
            'id': str(uuid.uuid4()),
            'restaurantId': restos_id,
            'comment': avis,
        })
        print(f"Avis ajouté pour restaurant {avis}")
        return response
    except Exception as e:
        print(f"Erreur lors de l'ajout de l'avis : {e}")
        return None

# Exécution
restos = get_restaurants_from_dynamodb()
print(f"📌 Restaurants récupérés : {restos}")

for resto in restos:
    try:
        reviews = scrape_reviews_with_requests(resto['url'])
        for review in reviews:
            add_review(resto['id'], review)
    except Exception as e:
        print(f"Erreur pour {resto['url']} : {e}")

print(f"Avis ajoutés à la base de données.") 

