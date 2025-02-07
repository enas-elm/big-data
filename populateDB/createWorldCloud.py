import matplotlib.pyplot as plt
from wordcloud import WordCloud
from dotenv import load_dotenv
import boto3
import os

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()  # charge les variables d'environnement du fichier .env

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

# Fonction pour récupérer les critiques depuis DynamoDB avec gestion de pagination
def get_reviews_from_dynamodb():
    reviews = []
    response = table.scan()  # Effectuer le scan initial

    # Récupérer toutes les critiques avec pagination si nécessaire
    while 'LastEvaluatedKey' in response:
        # Ajouter les critiques récupérées
        for item in response['Items']:
            reviews.append(item['comment'])  # Vérifie le nom du champ dans ta table DynamoDB
        
        # Continuer le scan avec la clé de pagination
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])

    # Ajouter les critiques du dernier lot de résultats
    for item in response['Items']:
        reviews.append(item['comment'])

    return reviews

# Fonction pour générer le nuage de mots
def generate_wordcloud(reviews):
    text = " ".join(reviews)

    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')  
    plt.show()

# Récupérer les critiques de DynamoDB
try:
    reviews = get_reviews_from_dynamodb()
    print(f"Nombre de critiques récupérées: {len(reviews)}")
    
    # Générer et afficher le nuage de mots
    generate_wordcloud(reviews)
except Exception as e:
    print(f"Une erreur s'est produite : {e}")
