import matplotlib.pyplot as plt
from transformers import pipeline
import nltk
from dotenv import load_dotenv
import boto3
import os
from collections import Counter

nltk.download('punkt')
nltk.download('punkt_tab')

# Charger le pipeline de sentiment-analysis
sentiment_analysis = pipeline("sentiment-analysis")

# Charger les variables d'environnement depuis le fichier .env
load_dotenv() 

# Récupérer les variables d'environnement
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

# Vérifier que les variables sont bien définies
if not aws_access_key_id or not aws_secret_access_key:
    raise ValueError("Les variables d'environnement AWS ne sont pas définies correctement.")

# Configurer boto3 avec les variables d'environnement
boto3.setup_default_session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name='eu-west-1'
)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('reviews-dev')
tableRestaut = dynamodb.Table('restaurants-dev')

# Fonction pour récupérer les critiques depuis DynamoDB
def get_reviews_from_dynamodb():
    reviews = {}
    response = table.scan()  

    while 'LastEvaluatedKey' in response:
        for item in response['Items']:
            restaurant_id = item['restaurantId']
            comment = item['comment']

            # Stocker les avis sous forme de liste par restaurant
            if restaurant_id in reviews:
                reviews[restaurant_id].append(comment)
            else:
                reviews[restaurant_id] = [comment]

        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])

    for item in response['Items']:
        restaurant_id = item['restaurantId']
        comment = item['comment']
        if restaurant_id in reviews:
            reviews[restaurant_id].append(comment)
        else:
            reviews[restaurant_id] = [comment]

    return reviews

# Fonction d'analyse du sentiment
def analyze_sentiment(review):
    max_length = 1024  
    sentences = nltk.sent_tokenize(review)  

    sentiment = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        if current_length + len(sentence.split()) > max_length:
            chunk = ' '.join(current_chunk)
            result = sentiment_analysis(chunk)
            sentiment.append(result[0]['label'])

            current_chunk = [sentence]
            current_length = len(sentence.split())
        else:
            current_chunk.append(sentence)
            current_length += len(sentence.split())

    if current_chunk:
        chunk = ' '.join(current_chunk)
        result = sentiment_analysis(chunk)
        sentiment.append(result[0]['label'])

    return max(set(sentiment), key=sentiment.count) if sentiment else "UNKNOWN"

def get_global_sentiment(sentiments):
    if not sentiments:
        return "UNKNOWN"

    counter = Counter(sentiments)
    return counter.most_common(1)[0][0]  # Retourne le sentiment majoritaire

# Mise à jour du sentiment global dans DynamoDB pour chaque restaurant
def update_global_sentiment_in_dynamodb_reviews(review_id, sentiment):
    try:
        table.update_item(
            Key={'id': review_id},
            UpdateExpression="SET sentiment = :s",
            ExpressionAttributeValues={':s': sentiment}
        )
        print(f"Sentiment mis à jour pour l'avis {review_id}: {sentiment}")
    except Exception as e:
        print(f"Erreur lors de la mise à jour du sentiment pour l'avis {review_id}: {str(e)}")

# Mise à jour du sentiment global dans DynamoDB pour chaque restaurant
def update_global_sentiment_in_dynamodb_restaurants(restaurant_id, global_sentiment):
    try:
        tableRestaut.update_item(
            Key={'id': restaurant_id},
            UpdateExpression="SET global_sentiment = :s",
            ExpressionAttributeValues={':s': global_sentiment}
        )
        print(f"✅ Sentiment global mis à jour pour le restaurant {restaurant_id}: {global_sentiment}")
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour du sentiment global pour le restaurant {restaurant_id}: {str(e)}")

# Données de test : une liste d'avis fictifs
reviews = get_reviews_from_dynamodb()

# Analyser le sentiment pour chaque avis et afficher les résultats
for restaurant_id, comments in reviews.items():
    try:
        sentiments = []
        
        # Analyser chaque avis et mettre à jour son sentiment
        for comment in comments:
            sentiment = analyze_sentiment(comment)
            sentiments.append(sentiment)

            # Mise à jour du sentiment de l'avis dans DynamoDB
            update_global_sentiment_in_dynamodb_reviews(restaurant_id, sentiment)

        # Obtenir le sentiment global pour le restaurant
        global_sentiment = get_global_sentiment(sentiments)

        # Mise à jour du sentiment global dans DynamoDB pour le restaurant
        update_global_sentiment_in_dynamodb_restaurants(restaurant_id, global_sentiment)

        print(f"Restaurant ID: {restaurant_id} - Sentiment Global: {global_sentiment}")
    except Exception as e:
        print(f"Erreur lors du traitement du restaurant {restaurant_id}: {str(e)}")
