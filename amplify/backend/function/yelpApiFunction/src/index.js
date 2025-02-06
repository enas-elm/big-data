const awsServerlessExpress = require('aws-serverless-express');
const app = require('./app');
const axios = require('axios');
const cheerio = require('cheerio');
const AWS = require("aws-sdk");
const { v4: uuidv4 } = require("uuid"); // Générer des IDs uniques
const dynamoDB = new AWS.DynamoDB.DocumentClient();

/**
 * @type {import('http').Server}
*/
const server = awsServerlessExpress.createServer(app);

const tableNameReview = process.env.STORAGE_REVIEWS_NAME;
const tableNameRestaurant = process.env.STORAGE_RESTAURANTS_NAME;
const YELP_API_KEY = "8wczhx8stdJahEsSAbjC1uVhbgdpE0jOrGSmHicFSlxn3g0ycs2BxIHJXg6CcozXzI1n9PoNmUuFZ-SqXM8jHRKoRnfjDeKHZQfnxCHN5oeLWIy8LXlE9Stfz6KgZ3Yx"; // ⚠️ Remplace par ta vraie clé API

const yelpApi = axios.create({
  baseURL: "https://api.yelp.com/v3/businesses",
  headers: {
    Authorization: `Bearer ${YELP_API_KEY}`,
    "Content-Type": "application/json",
  },
});

const getRestaurants = async (location, term = "restaurant") => {
  try {
    const response = await yelpApi.get("/search", { params: { location, term, limit: 10 } })
    return response.data.businesses;
  } catch (error) {
    console.error("Erreur lors de la récupération des restaurants :", error);
    return [];
  }
};

const addReview = async (restaurantId, review) => {
  const params = {
    TableName: tableNameReview,
    Item: {
      id: uuidv4(), // Génère un ID unique
      restaurantId: restaurantId, // Lien avec le restaurant
      comment: review
    },
  };

  try {
    await dynamoDB.put(params).promise();
    console.log(`Avis ajouté pour restaurant ${restaurantId}`);
    return params.Item;
  } catch (error) {
    console.error("Erreur lors de l'ajout de l'avis :", error);
    return null;
  }
};


const addRestaurant = async (restaurant) => {
  const params = {
    TableName: tableNameRestaurant,
    Item: {
      id: restaurant.id, // Génère un ID unique
      name: restaurant.name,
    },
  };

  try {
    await dynamoDB.put(params).promise();
    console.log(`Restaurant ajouté: ${restaurant.name}`);
    return params.Item;
  } catch (error) {
    console.error("Erreur lors de l'ajout du restaurant :", error);
    return null;
  }
};

const getReviews = async (restaurantAlias) => {
  try {
    console.debug('Get reviews for', restaurantAlias);
    const document = await fetch(`https://www.yelp.fr/biz/${restaurantAlias}`).then((res) => res.text());
    const $ = cheerio.load(document)
    const reviews = [];

    // Sélectionner les avis Yelp
    $("p.comment__09f24__D0cxf span").each((index, element) => {
      reviews.push($(element).text().trim());
    });

    return reviews;
  } catch (error) {
    console.error(`Erreur lors de la récupération des avis pour ${restaurantAlias} :`, error);
    return [];
  }
};


/**
 * @type {import('@types/aws-lambda').APIGatewayProxyHandler}
 */
exports.handler = async (event, context) => {
  console.log(`EVENT: ${JSON.stringify(event)}`);

  try {
    // Récupérer les restaurants
    const location = event.queryStringParameters?.location || "Paris";
    const restaurants = await getRestaurants(location);

    // Récupérer les avis pour chaque restaurant
    const restaurantsWithReviews = await Promise.all(
      restaurants.map(async (restaurant) => {
        addRestaurant(restaurant);
        const reviews = await getReviews(restaurant.alias);

        await Promise.all(
          reviews.map(async (review) => {
            await addReview(restaurant.id, review);
          })
        );
        return { ...restaurant, reviews }; // Ajouter les avis à chaque restaurant
      })
    );

    return {
      statusCode: 200,
      body: JSON.stringify(restaurantsWithReviews),
    };
  } catch (error) {
    // console.error("Erreur lors de la récupération des restaurants et avis :", error);
    return {
      statusCode: 500,
      body: JSON.stringify({ message: "Erreur interne", error }),
    };
  }

  return awsServerlessExpress.proxy(server, event, context, 'PROMISE').promise;
};
