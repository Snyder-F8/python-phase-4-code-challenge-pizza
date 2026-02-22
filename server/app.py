#!/usr/bin/env python3

from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get(
    "DB_URI",
    f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)

api = Api(app)


# ======================================
# Root Route
# ======================================

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"


# ======================================
# GET /restaurants
# ======================================

class Restaurants(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        return [
            r.to_dict(only=("id", "name", "address"))
            for r in restaurants
        ], 200


api.add_resource(Restaurants, "/restaurants")


# ======================================
# GET /restaurants/<int:id>
# DELETE /restaurants/<int:id>
# ======================================

class RestaurantById(Resource):

    def get(self, id):
        restaurant = Restaurant.query.get(id)

        if not restaurant:
            return {"error": "Restaurant not found"}, 404

        # Use rules instead of deep only to prevent recursion errors
        return restaurant.to_dict(
            rules=(
                "-restaurant_pizzas.restaurant",
            )
        ), 200

    def delete(self, id):
        restaurant = Restaurant.query.get(id)

        if not restaurant:
            return {"error": "Restaurant not found"}, 404

        # If cascade isn't configured, manually delete children
        for rp in restaurant.restaurant_pizzas:
            db.session.delete(rp)

        db.session.delete(restaurant)
        db.session.commit()

        return "", 204


api.add_resource(RestaurantById, "/restaurants/<int:id>")


# ======================================
# GET /pizzas
# ======================================

class Pizzas(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return [
            p.to_dict(only=("id", "name", "ingredients"))
            for p in pizzas
        ], 200


api.add_resource(Pizzas, "/pizzas")


# ======================================
# POST /restaurant_pizzas
# ======================================

class RestaurantPizzas(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            return {"errors": ["Invalid JSON"]}, 400

        try:
            new_restaurant_pizza = RestaurantPizza(
                price=data["price"],
                pizza_id=data["pizza_id"],
                restaurant_id=data["restaurant_id"]
            )

            db.session.add(new_restaurant_pizza)
            db.session.commit()

            return new_restaurant_pizza.to_dict(
                rules=(
                    "-restaurant.restaurant_pizzas",
                    "-pizza.restaurant_pizzas",
                )
            ), 201

        except ValueError as e:
            db.session.rollback()
            return {"errors": [str(e)]}, 400


api.add_resource(RestaurantPizzas, "/restaurant_pizzas")


if __name__ == "__main__":
    app.run(port=5555, debug=True)