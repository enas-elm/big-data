# Big Data Project

## Description
Stockage et analyse des restaurants et avis clients avec AWS DynamoDB.

### Données
- **Restaurants** : Importés via l'API Yelp.
- **Avis** : Scrappés et stockés dans DynamoDB.

### API
- Récupération des restaurants et avis.

### Technologies
- **AWS DynamoDB** : Stockage
- **Cheerio** : Scrapping
- **Transformers** : Analyse des sentiments

#### Stockage des restaurants dans DynamoDB, récupéré à partir de l'API Yelp
![dynamodb-restaurants](https://github.com/user-attachments/assets/7e243ef9-0550-4830-b0b7-b4bd4ebd870c)

#### Stockage des reviews grâce au scrapping dans DynamoDB rattaché à leurs restaurants
![dynamodb-reviews](https://github.com/user-attachments/assets/52a0ca9b-4b8b-4413-aae7-1339b3592f48)

#### API de récupération des restaurants
![getRestaurants-api](https://github.com/user-attachments/assets/948631b4-e910-45f7-8332-66f563be0c62)
