import argparse
import os
import re
from datetime import datetime

from flask import Flask, jsonify, request
from flask_restful import Api, Resource, reqparse, inputs
from flask_cors import CORS
from db import (
    ProductModel,
    create_product,
    get_product_by_id,
    update_product,
    delete_product,
)

app = Flask(__name__)
# Enable CORS globally
CORS(app)
api = Api(app)


# Health check endpoint
@app.route("/health")
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "service": "react-python-playground-backend",
        }
    )


# Define the resources
class Products(Resource):
    def get(self):
        return [product.to_dict() for product in ProductModel.select()]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str, required=True)
        parser.add_argument("price", type=float, required=True)
        args = parser.parse_args()

        data = {"name": args["name"], "price": args["price"]}
        product = create_product(**data)

        return {"message": "Product added successfully.", "productId": product.id}, 201


class Product(Resource):
    def get(self, product_id):
        product = get_product_by_id(product_id)
        if product:
            return product.to_dict()
        else:
            return {"error": "Product not found."}, 404

    def patch(self, product_id):
        product = get_product_by_id(product_id)
        if not product:
            return {"error": "Product not found."}, 404

        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str)
        parser.add_argument("price", type=float)
        args = parser.parse_args()
        data = {"product_id": product_id}
        if args["name"]:
            data["name"] = args["name"]
        if args["price"]:
            data["price"] = args["price"]
        update_product(**data)
        return {"message": "Product updated successfully."}, 200

    def delete(self, product_id):
        product = get_product_by_id(product_id)
        if not product:
            return {"error": "Product not found."}, 404
        delete_product(product_id)

        return {"message": "Product deleted."}, 200


# Add the resources to the API
api.add_resource(Products, "/api/products")
api.add_resource(Product, "/api/products/<int:product_id>")


if __name__ == "__main__":

    def ipv4_or_localhost_regex_type(arg_value):
        ipv4_or_localhost_regex = re.compile(
            r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.)){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|^(localhost|127(\.[0-9]+){0,2}\.[0-9]+|0\.0\.0\.0)$"
        )
        if not ipv4_or_localhost_regex.match(arg_value):
            raise argparse.ArgumentTypeError("invalid ipv4 or localhost value")
        return arg_value

    # Create the table
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        help="Host to bind to (default: 0.0.0.0 for container compatibility)",
        default="0.0.0.0",
        type=ipv4_or_localhost_regex_type,
    )
    parser.add_argument("--port", help="Port to bind to", default=5000, type=int)
    args = parser.parse_args()
    print(args.host, args.port)

    # Use production settings if FLASK_ENV is not development
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(host=args.host, port=args.port, debug=debug_mode)
