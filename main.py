import json
from datetime import timedelta
from flask import Flask, request, jsonify
from flask_mongoengine import MongoEngine
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask.json import JSONEncoder
from mongoengine import Q
from models import Customer, Product, Order

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, create_refresh_token
)
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
jwt = JWTManager(app)

app.config['MONGODB_SETTINGS'] = {
    'db': 'mydatabase',
    'host': 'mongodb://localhost:27017/mydatabase'
}


db = MongoEngine(app)


@app.route('/login', methods=['POST'])
def login():
    customer_email = request.json.get('email')
    customer = Customer.objects(email=customer_email).first()
    if not customer:
        return jsonify({'error': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=str(customer.id), expires_delta=timedelta(days=1))
    refresh_token = create_refresh_token(identity=str(customer.id))
    return jsonify(access_token=access_token, refresh_token=refresh_token), 200


@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_customer_id = get_jwt_identity()
    access_token = create_access_token(identity=current_customer_id)
    return jsonify(access_token=access_token), 200


@app.route('/products', methods=['POST'])
@jwt_required()
def create_product_api():
    data = request.json
    product = Product(**data)
    product.save()
    return jsonify({'message': 'Product created successfully', 'product_id': str(product.id)}), 201

@app.route('/products', methods=['GET'])
@jwt_required()
def get_products_api():
    search_query = request.args.get('search')
    sort_field = request.args.get('sort_field')
    sort_order = request.args.get('sort_order')
    query = Product.objects()
    if search_query:
        query = query.filter(name__icontains=search_query)

    if sort_field and sort_order:
        sort_prefix = '' if sort_order.lower() == 'asc' else '-'
        sort_key = sort_prefix + sort_field
        query = query.order_by(sort_key)

    products = query.all()

    products_list = [
        {
            '_id': str(product.id),
            'name': product.name,
            'price': str(product.price),
            'description': product.description
        }
        for product in products
    ]

    return jsonify(products_list), 200


@app.route('/products/<product_id>', methods=['GET'])
@jwt_required()
def get_product_api(product_id):
    product = Product.objects(id=product_id).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return product.to_json(), 200

@app.route('/products/<product_id>', methods=['PUT'])
@jwt_required()
def update_product_api(product_id):
    data = request.json

    product = Product.objects(id=product_id).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    product.update(**data)
    return jsonify({'message': 'Product updated successfully'}), 200

@app.route('/products/<product_id>', methods=['DELETE'])
@jwt_required()
def delete_product_api(product_id):
    product = Product.objects(id=product_id).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    product.delete()
    return jsonify({'message': 'Product deleted successfully'}), 200

@app.route('/customers', methods=['POST'])
def create_customer_api():
    data = request.json
    customer = Customer(**data)
    customer.save()
    return jsonify({'message': 'Customer created successfully', 'customer_id': str(customer.id)}), 201

# Example for getting all customers via API
@app.route('/customers', methods=['GET'])
def get_customers_api():
    search_query = request.args.get('search')
    filter_criteria = request.args.get('filter_criteria')
    filter_value = request.args.get('filter_value')
    sort_field = request.args.get('sort_field')
    sort_order = request.args.get('sort_order')

    query = Customer.objects()

    if search_query:
        query = query.filter(Q(name__icontains=search_query) | Q(email__icontains=search_query))

    if filter_criteria and filter_value:
        query = query.filter(**{filter_criteria: filter_value})

    if sort_field and sort_order:
        sort_prefix = '' if sort_order.lower() == 'asc' else '-'
        sort_key = sort_prefix + sort_field
        query = query.order_by(sort_key)

    customers = query.all()

    customers_list = []
    for customer in customers:
        customer_dict = {
            '_id': str(customer.id),
            'name': customer.name,
            'email': customer.email
        }
        customers_list.append(customer_dict)

    return jsonify(customers_list), 200

@app.route('/customers/<customer_id>', methods=['PUT'])
def update_customer_api(customer_id):
    data = request.json
    customer = Customer.objects(id=customer_id).first()
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    customer.update(**data)
    return jsonify({'message': 'Customer updated successfully'}), 200


@app.route('/customers/<customer_id>', methods=['DELETE'])
def delete_customer_api(customer_id):
    customer = Customer.objects(id=customer_id).first()
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    customer.delete()
    return jsonify({'message': 'Customer deleted successfully'}), 200


@app.route('/orders', methods=['POST'])
@jwt_required()
def create_order_api():
    data = request.json
    customer_id = data.get('customer')
    customer = Customer.objects(id=customer_id).first()
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    product_ids = data.get('products')
    products = Product.objects(id=product_ids).first()

    current_customer_id = get_jwt_identity()
    current_customer = Customer.objects(id=current_customer_id).first()
    if not current_customer:
        return jsonify({'error': 'Current customer not found'}), 404

    order = Order(customer=customer, products=products, quantity=data['quantity'])
    order.save()
    return jsonify({'message': 'Order created successfully', 'order_id': str(order.id)}), 201

@app.route('/orders', methods=['GET'])
@jwt_required()
def get_orders_api():
    # Get current customer ID
    current_customer_id = get_jwt_identity()

    search_query = request.args.get('search')
    sort_field = request.args.get('sort_field')
    sort_order = request.args.get('sort_order')

    query = Order.objects(customer=current_customer_id)

    if search_query:
        query = query.filter(some_field__icontains=search_query)

    if sort_field and sort_order:
        sort_prefix = '' if sort_order.lower() == 'asc' else '-'
        sort_key = sort_prefix + sort_field
        query = query.order_by(sort_key)

    # Execute the query
    orders = query.all()

    orders_list = []
    for order in orders:
        order_info = {
            'order_id': str(order.id),
            'customer_id': str(order.customer.id),
            'product_ids': str(order.products.id),
            'quantity': order.quantity
        }
        orders_list.append(order_info)

    return orders_list, 200

@app.route('/orders/<order_id>', methods=['PUT'])
@jwt_required()
def update_order_api(order_id):
    data = request.json

    order = Order.objects(id=order_id).first()
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    order.update(**data)
    return jsonify({'message': 'Order updated successfully'}), 200

@app.route('/orders/<order_id>', methods=['DELETE'])
@jwt_required()
def delete_order_api(order_id):
    current_customer_id = get_jwt_identity()
    order = Order.objects(id=order_id, customer=current_customer_id).first()
    if not order:
        return jsonify({'error': 'Order not found or you are not authorized to delete it'}), 404
    order.delete()
    return jsonify({'message': 'Order deleted successfully'}), 200
    
if __name__ == '__main__':
    app.run(debug=True)
