from datetime import datetime

from database import db


class Product(db.Model):
    name = db.Column(db.String, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer)
    def to_dict(self):
        return {"name": self.name, "price": self.price, "quantity": self.quantity}

class Order(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String, nullable=False)
    address = db.Column(db.String)
    completed = db.Column(db.Boolean, default=False)
    recieved_date = db.Column(db.DateTime, default=datetime.now())
    processed_date = db.Column(db.DateTime)
    products = db.relationship('ProductsOrder', back_populates='order')

    def to_dict(self):
        product_list=[]
        price = 0
        for product in self.products:
            price += product.product.price * product.quantity
            product_list.append({"name": product.product_name, "quantity": product.quantity})
        return {"customer_name": self.name, "customer_address": self.address, "products": product_list, "time_recieved": self.recieved_date, "price": round(price,2)}

    def process(self):
        product_list=[]
        price = 0
        for product in self.products:
            # if the quantity in order is greater than the quantity in inventory
            # then change quantity in order equal to quantity in inventory
            if product.quantity > product.product.quantity:
                product.quantity = product.product.quantity
            price += product.product.price * product.quantity
            product_list.append({"name": product.product_name, "quantity": product.quantity})
            # update inventory
            product.product.quantity -= product.quantity
        self.completed = True
        return {"customer_name": self.name, "customer_address": self.address, "products": product_list, "processed_date": self.processed_date, "price": round(price,2)}

class ProductsOrder(db.Model): 
    # Product foreign key is name
    product_name = db.Column(db.ForeignKey("product.name"), primary_key=True)
    # Order foreign key is ID
    order_id = db.Column(db.ForeignKey("order.id"), primary_key=True)
    # This is how many items we want
    quantity = db.Column(db.Integer, nullable=False)
    # Relationships and backreferences for SQL Alchemy
    product = db.relationship('Product')
    order = db.relationship('Order', back_populates='products')
