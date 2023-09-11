from datetime import datetime
from pathlib import Path

import requests
from database import db
from flask import Flask, jsonify, redirect, render_template, request, url_for
from models import Order, Product, ProductsOrder

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///store.db"
app.instance_path = Path(".").resolve()
db.init_app(app)


@app.route("/")
def home():
    data = Product.query.all()
    return render_template("index.html", products=data)

@app.route("/name/<string:order>", methods=["GET"])
def sort_name(order):
    data = Product.query.order_by(Product.name).all()
    if order == 'desc':
        data = Product.query.order_by(Product.name.desc()).all()
    return render_template("index.html", products=data)

@app.route("/price/<string:order>", methods=["GET"])
def sort_price(order):
    data = Product.query.order_by(Product.price).all()
    if order == 'desc':
        data = Product.query.order_by(Product.price.desc()).all()
    return render_template("index.html", products=data)

@app.route("/quantity/<string:order>", methods=["GET"])
def sort_quantity(order):
    data = Product.query.order_by(Product.quantity).all()
    if order == 'desc':
            data = Product.query.order_by(Product.quantity.desc()).all()
    return render_template("index.html", products=data)

@app.route("/api/order")
def order():
    data = Order.query.all()
    return render_template("orders.html", orders=data)

@app.route("/api/order/pending")
def pending():
    data = Order.query.all()
    return render_template("pending.html", orders=data)

@app.route("/api/order/completed")
def completed():
    data = Order.query.all()
    return render_template("completed.html", orders=data)

@app.route("/form/order")
def form_order():
    data = Order.query.all()
    return render_template("order_form.html", customers=data)

@app.route("/search_name", methods=["POST", "GET"])
def search_name():
    # https://levelup.gitconnected.com/building-a-basic-website-with-flask-and-sqlalchemy-2f66ea6c02dc
    if request.method == "POST":
        name = request.form.get("search_name")
        if name == None:
            return "Select an option"
        return redirect(url_for("api_get_order_customer",customer_name=name))
    else:
        return redirect(url_for("search"))

@app.route("/form/product")
def form_product():
    data = Product.query.all()
    return render_template("product_form.html", products=data)

@app.route("/add_product", methods=["POST","GET"])
def add_product():
    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        quantity = request.form["quantity"]
        try:
            exists = db.session.query(Product.name).filter_by(name=name).first() is not None
            if exists:
                raise ValueError
        except ValueError:
            return ("Product already added", 400)
        product = Product(
            name=name.lower(),
            price=price,
            quantity=quantity,
        )
        db.session.add(product)
        db.session.commit()
        return "Item added to database"
    else:
        return redirect(url_for("form_product"))
    
@app.route("/update_product", methods=["POST","GET"])
def update_product():
    if request.method == "POST":
        name = request.form.get("update_name")
        if name == None:
            return "Select an option"
        price = request.form["update_price"]
        quantity = request.form["update_quantity"]
        product = db.session.get(Product, name)
        product.price = price
        product.quantity = quantity
        db.session.commit()
        return "Product updated"
    else:
        return redirect(url_for("form_product"))
    
@app.route("/search_product", methods=["POST","GET"])
def search_product():
    if request.method == "POST":
        name = request.form.get("search_name")
        if name == None:
            return "Select an option"
        return redirect(url_for("api_get_product", name=name))
    else:
        return redirect(url_for("form_product"))
    
@app.route("/api/product/<string:name>", methods=["GET"])
def api_get_product(name):
    try:
        # https://stackoverflow.com/questions/32938475/flask-sqlalchemy-check-if-row-exists-in-table
        exists = db.session.query(Product.name).filter_by(name=name.lower()).first() is not None
        if not exists:
            raise ValueError
    except ValueError:
        return ("Product not found", 404)
    product = db.session.get(Product, name.lower())
    product_json = product.to_dict()
    return jsonify(product_json)


@app.route("/api/product", methods=["POST"])
def api_create_product():
    data = request.json
    # Check all data is provided
    for key in ("name", "price", "quantity"):
        if key not in data:
            return f"The JSON provided is invalid (missing: {key})", 400
    try:
        name = str(data["name"]).lower()
        exists = db.session.query(Product).filter_by(name=name).first() is not None
        if exists:
            raise ValueError
    except ValueError:
        return ("Product already exists", 400)
    try:
        price = float(data["price"])
        quantity = int(data["quantity"])
        # Make sure they are positive
        if price < 0 or quantity < 0:
            raise ValueError
    except ValueError:
        return (
            "Invalid values: price must be a positive float and quantity a positive integer",
            400,
        )

    product = Product(
        name=name,
        price=price,
        quantity=quantity,
    )
    db.session.add(product)
    db.session.commit()
    return "Item added to the database"

@app.route("/api/product/<string:name>", methods=["DELETE"])
def api_delete_product(name):
    try:
        exists = db.session.query(Product).filter_by(name=name.lower()).first() is not None
        if not exists:
            raise ValueError
    except ValueError:
        return ("Product not found", 404)
    product = db.session.get(Product, name.lower())
    db.session.delete(product)
    db.session.commit()
    return "Item deleted from the database"

@app.route("/api/product/<string:name>", methods=["PUT"])
def api_put_product(name):
    try:
        exists = db.session.query(Product).filter_by(name=name.lower()).first() is not None
        if not exists:
            raise ValueError
    except ValueError:
        return ("Product not found", 404)
    product = db.session.get(Product, name.lower())
    data = request.json
    for key in ("price", "quantity"):
        if key not in data:
            return f"The JSON provided is invalid (missing: {key})", 400
    try:
        price = float(data["price"])
        quantity = int(data["quantity"])
        # Make sure they are positive
        if price < 0 or quantity < 0:
            raise ValueError
    except ValueError:
        return (
            "Invalid values: price must be a positive float and quantity a positive integer",
            400,
        )
    product.price = price
    product.quantity = quantity
    db.session.commit()
    return "Item updated"

@app.route("/api/order/<int:order_id>", methods=["GET"])
def api_get_order(order_id):
    try:
        exists = db.session.query(Order).filter_by(id=order_id).first() is not None
        if not exists:
            raise ValueError
    except ValueError:
        return ("Order ID not found", 404)
    customer = db.session.get(Order, order_id)
    customer_json = customer.to_dict()
    return jsonify(customer_json)

@app.route("/api/order/<string:customer_name>", methods=["GET"])
def api_get_order_customer(customer_name):
    try:
        exists = db.session.query(Order).filter_by(name=customer_name).first() is not None
        if not exists:
            raise ValueError
    except ValueError:
        return ("Customer not found", 404)
    order_ids = db.session.query(Order.id).filter_by(name=customer_name).all()
    order_list = []
    for id in order_ids:
        order = db.session.get(Order, id)
        order_list.append(order.to_dict())
    return jsonify(order_list)


@app.route("/api/order", methods=["POST"])
def api_create_order():
    data = request.json
    for key in ("customer_name", "customer_address", "products"):
        if key not in data:
            return f"The JSON provided is invalid (missing: {key})", 400
    customer_name = str(data["customer_name"])
    customer_address = str(data["customer_address"])
    order = Order(
        name=customer_name,
        address=customer_address
    )
    db.session.add(order)
    products = list(data["products"])
    for product in products:
        name = product["name"]
        quantity = product["quantity"]
        try:
            exists = db.session.query(Product.name).filter_by(name=name.lower()).first() is not None
            if not isinstance(quantity, int) or int(quantity) < 0:
                raise TypeError
            if not exists:
                raise ValueError
        except ValueError:
            return ("Product not found", 404)
        except TypeError:
            return ("Invalid type", 400)
        item = db.session.get(Product, name)
        productorder = ProductsOrder(
            product=item,
            order=order,
            quantity=quantity
        )
        db.session.add(productorder)
    db.session.commit()
    return jsonify(order.to_dict())

@app.route("/api/product/<int:order_id>", methods=["PUT"])
def api_process_order(order_id):
    data = request.json
    if "process" not in data:
            return ("The JSON provided is invalid (missing: process)", 400)
    process = data["process"]
    if process != True:
        return "Not processing the data"
    try:
        exists = db.session.query(Order).filter_by(id=order_id).first() is not None 
        if not exists:
            raise ValueError
    except ValueError:
        return("Order ID not found", 400)
    order = db.session.get(Order, order_id)
    if order.completed == True:
        return "Order already processed"
    order.process()
    db.session.query(Order).filter_by(id=order_id).update({"processed_date":datetime.now()})
    db.session.commit()
    return jsonify(order.to_dict())

@app.route("/process_order", methods=["POST", "GET"])
def process_order():
    if request.method == "POST":
        id = request.form.get("id")
        if id == None:
            return "Select an option"   
        requests.put(f"http://127.0.0.1:5000/api/product/{id}",json={'process': True})
        return "Order Processed"
    else:
        return redirect(url_for("form_order"))
    
@app.route("/create_order", methods=["POST", "GET"])
def create_order():
    if request.method == "POST":
        customer_name = request.form.get("customer_name")
        customer_address =  request.form.get("customer_address")
        order = Order(
                name=customer_name,
                address=customer_address
        )
        db.session.add(order)
        db.session.commit()
        return redirect(url_for("form_add_order",customer_name=customer_name, customer_address=customer_address))
    else:
        return redirect(url_for("form_order"))

@app.route("/create_order/add/<string:customer_name>/<string:customer_address>", methods=["GET"])
def form_add_order(customer_name, customer_address):
    data = Product.query.all()
    return render_template("order_add.html", products=data, customer_name=customer_name, customer_address=customer_address)

customer_products=[]
@app.route("/create_order/add_order", methods=["POST", "GET"])
def create_order_add():
    if request.method == "POST":
        if request.form['action'] == 'Add Product':
            product_name = request.form.get('product_name')
            quantity = request.form['quantity']
            last_order = db.session.query(Order).order_by(Order.id.desc()).first()
            customer_name = last_order.name
            customer_address = last_order.address
            json = {"name": product_name, "quantity": quantity}
            customer_products.append(json)
            return redirect(url_for("form_add_order",customer_name=customer_name, customer_address=customer_address))
        if request.form['action'] == 'Submit Order':
            last_order = db.session.query(Order).order_by(Order.id.desc()).first()
            if len(customer_products) == 0:
                db.session.delete(last_order)
                db.session.commit()
                return ("No products added to order", 400)
            customer_name = last_order.name
            customer_address = last_order.address
            for item in customer_products:
                product = db.session.get(Product, item["name"])
                productorder = ProductsOrder(
                product=product,
                order=last_order,
                quantity=item["quantity"]
                )
                db.session.add(productorder)
            db.session.commit()
            return "Order added"
        else:
            # customer_products=[]
            return redirect(url_for("form_add_order",customer_name=customer_name, customer_address=customer_address))
        
if __name__ == "__main__":
    app.run(debug=True)
