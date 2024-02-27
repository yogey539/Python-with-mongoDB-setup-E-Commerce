from mongoengine import Document, StringField, ReferenceField, DateTimeField
from datetime import datetime
class Customer(Document):
    name = StringField(required=True)
    email = StringField(required=True, unique=True)

class Product(Document):
    name = StringField(required=True)
    price = StringField(required=True)
    description = StringField(required=True)

class Order(Document):
    customer = ReferenceField(Customer, required=True)
    products = ReferenceField(Product, required=True)
    quantity = StringField(required=True)
    date = DateTimeField(default=datetime.utcnow, required=True)
