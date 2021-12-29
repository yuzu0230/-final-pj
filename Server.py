import os
from datetime import datetime, timedelta
from math import pow

from flask import Flask, request, jsonify, render_template, abort
from flask.json.tag import JSONTag
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import *

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
# CREATE DATABASE, "test.db" is database's name
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
# Optional: But it will silence the deprecation warning in the console.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

ma = Marshmallow(app)

class Member(db.Model):
    __tablename__ = "member"
    id = db.Column(db.Integer, primary_key=True)
    member_name = db.Column(db.String(50), nullable=False)
    sex = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    monetary = db.Column(db.Integer, nullable=False)

    db_member_order = db.relationship("Order", backref="member")

    def __init__(self, member_name, sex, age):
        self.member_name = member_name
        self.sex = sex
        self.age = age
        self.monetary = 0


class Order(db.Model):
    __tablename__ = "order"
    order_id = db.Column(db.Integer, primary_key=True)
    total_amount = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    # 一對多的多
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)

    def __init__(self, total_amount, member_id, date):
        self.total_amount = total_amount
        self.member_id = member_id
        self.date = date

class Product(db.Model):
    __tablename__ = 'product'
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    on_hand_balance = db.Column(db.Integer, nullable=False)
    leading_time = db.Column(db.Integer, nullable=False)
    reorder_point = db.Column(db.Float, nullable=False)

    def __init__(self, product_name, price, on_hand_balance, leading_time,
                 reorder_point):
        self.product_name = product_name
        self.price = price
        self.on_hand_balance = on_hand_balance
        self.leading_time = leading_time
        self.reorder_point = reorder_point

class OrderProduct(db.Model):
    __tablename__ = 'order_product'
    order_product_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)

    def __init__(self, order_id, product_id):
        self.order_id = order_id
        self.product_id = product_id

class Material(db.Model):
    __tablename__ = 'material'
    material_id = db.Column(db.Integer, primary_key=True)
    material_name = db.Column(db.String(50), nullable=False)

    def __init__(self, material_name):
        self.material_name = material_name

# Product-Material 多對多，BOM
class ProductMaterial(db.Model):
    __tablename__ = 'product_material'
    product_material_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    material_id = db.Column(db.Integer, nullable=False)

    def __init__(self, product_id, material_id):
        self.product_id = product_id
        self.material_id = material_id

class Season_Sale(db.Model):
    __tablename__ = "season_sale"
    year = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.Integer, primary_key=True)
    sale = db.Column(db.Integer, nullable=False)

    def __init__(self, year, season, sale):
        self.year = year
        self.season = season
        self.sale = sale

# Member Schema
class MemberSchema(ma.Schema):
    class Meta:
        fields = ('id', 'member_name', 'sex', 'age', 'monetary')

# Order Schema
class OrderSchema(ma.Schema):
    class Meta:
        fields = ("order_id", "total_amount", "date", "member_id")

# Product schema
class ProductSchema(ma.Schema):
    class Meta:
        fields = ('product_id', 'product_name', 'price', 'on_hand_balance',
                  'leading_time', 'reorder_point')

# Order-Product schema
class OrderProductSchema(ma.Schema):
    class Meta:
        fields = ('order_product_id', 'order_id', 'product_id')

# Material schema
class MaterialSchema(ma.Schema):
    class Meta:
        fields = ('material_id', 'material_name')

# Product-Material schema
class ProductMaterialSchema(ma.Schema):
    class Meta:
        fields = ('product_material_id', 'product_id', 'material_id')

# Season_Sale Schema
class SeasonSaleSchema(ma.Schema):
    class Meta:
        fields = ("year", "season", "sale")

# Init schema
member_schema = MemberSchema()
members_schema = MemberSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
order_product_schema = OrderProductSchema()
orders_products_schema = OrderProductSchema(many=True)
material_schema = MaterialSchema()
materials_schema = MaterialSchema(many=True)
product_material_schema = ProductMaterialSchema()
products_materials_schema = ProductMaterialSchema(many=True)
season_sale_schema = SeasonSaleSchema()
season_sales_schema = SeasonSaleSchema(many=True)

db.create_all()

@app.route('/')
def home():
    # READ ALL RECORDS
    all_members = db.session.query(Member).all()
    print(all_members)
    return render_template("index.html", members=all_members)

##### MEMBER FUCTIONS #####
# Add a member
@app.route("/member", methods=['POST'])
def add_member():
    request_data = request.get_json()
    print(request_data)
    member_name = request_data['member_name']
    sex = request_data['sex']
    age = int(request_data['age'])

    new_member = Member(member_name, sex, age)
    db.session.add(new_member)
    db.session.commit()

    return member_schema.jsonify(new_member)


# Get all members
@app.route('/member', methods=['GET'])
def get_members():
    # Check if there is any member in database, if no member, response a 404 page
    if Member.query.first_or_404():
        all_members = Member.query.all()
        result = members_schema.dump(all_members)
        return jsonify(result)


# Get all members by pagination
@app.route('/member/page/<int:request_page>', methods=['GET'])
def get_members_paginate(request_page):
    # Check if there is any member in database, if no member, response a 404 page
    if Member.query.first_or_404():
        # request_page表示要求第幾頁，10代表一頁幾筆資料，False代表出錯時要不要回傳error
        pages = Member.query.paginate(request_page, 10, False)
        # 如果要求的頁數多於所有的頁數，回傳404頁面
        if pages.page > pages.pages:
            abort(404)
        result = members_schema.dump(pages.items)
        return jsonify(result)


# Get a single member by id
@app.route('/member/<int:id>', methods=['GET'])
def get_member(id):
    # Check if there is any member with this id in database, if no, response a 404 page
    if Member.query.filter_by(id=id).first_or_404():
        member = Member.query.get(id)
        return member_schema.jsonify(member)


# Delete a member by member's id
@app.route('/member/<id>', methods=['DELETE'])
def delete_member(id):
    # Check if there is any member with this in database, if no member, response a 404 page
    if Member.query.filter_by(id=id).first_or_404():
        member_to_delete = Member.query.get(id)
        orders_to_delete = Order.query.filter_by(member_id=id).all()
        db.session.delete(member_to_delete)
        # Delete all deleted member's orders
        for order in orders_to_delete:
            db.session.delete(order)
        db.session.commit()
        return member_schema.jsonify(member_to_delete)


##### ORDER FUNCTIONS #####
# 當訂單增加或刪除時，依據member_id更新會員的monetary
def update_member_monetary(member_id):
    update_monetary = 0
    member_orders = Order.query.filter_by(member_id=member_id).all()
    for order in member_orders:
        update_monetary += order.total_amount
    member_to_update = Member.query.get(member_id)
    member_to_update.monetary = update_monetary


# Add an order
@app.route("/order", methods=['POST'])
def add_order():
    request_data = request.get_json()
    print(request_data)
    member_id = int(request_data['member_id'])
    # Check if there is any member with this order's member_id in database
    if Member.query.filter_by(id=member_id).first_or_404():
        total_amount = request_data['total_amount']
        date = request_data['date']
        date = datetime.strptime(date, '%Y-%m-%d')

        new_order = Order(total_amount, member_id, date)
        db.session.add(new_order)
        # When add an order, update member's monetary
        update_member_monetary(member_id)
        db.session.commit()
        return order_schema.jsonify(new_order)


# Get all orders
@app.route('/order', methods=['GET'])
def get_orders():
    # Check if there is any order in database, if no order, response a 404 page
    if Order.query.first_or_404():
        all_orders = Order.query.all()
        result = orders_schema.dump(all_orders)
        return jsonify(result)

# Get all single member's orders
@app.route('/order/mid=<int:member_id>', methods=['GET'])
def get_a_member_orders(member_id):
    # Check if there is any order in database, if no order, response a 404 page
    if Order.query.filter_by(member_id=member_id).first_or_404():
        all_member_orders = Order.query.filter_by(member_id=member_id).all()
        result = orders_schema.dump(all_member_orders)
        return jsonify(result)

# Get members by pagination
@app.route('/order/page/<int:request_page>', methods=['GET'])
def get_orders_paginate(request_page):
    # Check if there is any order in database, if no order, response a 404 page
    if Order.query.first_or_404():
        pages = Order.query.paginate(request_page, 10, False)
        # 如果要求的頁數多於所有的頁數，回傳404
        if pages.page > pages.pages:
            abort(404)
        result = orders_schema.dump(pages.items)
        return jsonify(result)

# Get a single order by order's id
@app.route('/order/<id>', methods=['GET'])
def get_order(id):
    # Check if there is any order with this id in database, if no, response a 404 page
    if Order.query.filter_by(order_id=id).first_or_404():
        order = Order.query.get(id)
        return order_schema.jsonify(order)

# Delete a order by id
@app.route('/order/<id>', methods=['DELETE'])
def delete_order(id):
    # Check if there is any order with this id in database, if no, response a 404 page
    if Order.query.filter_by(order_id=id).first_or_404():
        # DELETE A RECORD BY ID
        order_to_delete = Order.query.get(id)
        db.session.delete(order_to_delete)
        # When delete an order, update member's monetary
        update_member_monetary(order_to_delete.member_id)
        db.session.commit()
        return order_schema.jsonify(order_to_delete)

##### PRODUCT FUNCTIONS #####
# Get all products.
@app.route('/products')
def get_products():
    #  Check if there is any order in database, if no order, response a 404 page
    if Product.query.first_or_404():
        all_products = Product.query.all()
        result = products_schema.dump(all_products)
        return jsonify(result)

# Get products paginate.
@app.route('/products/page/<int:request_page>')
def get_products_paginate(request_page):
    if Product.query.first_or_404():
        pages = Product.query.paginate(request_page, 10, False)
        # 如果要求的頁數多於所有的頁數，回傳404
        if pages.page > pages.pages:
            abort(404)
        result = products_schema.dump(pages.items)
        return jsonify(result)

@app.route('/product/<int:product_id>/edit', methods=['GET'])
def get_product(product_id):
    request_data = request.get_json()
    if Product.query.fist_or_404():
        product_id = request_data['product_id']
        product = Product.query.filter(Product.product_id==product_id)
        result = products_schema.dump(product)
        return jsonify(result)

@app.route('/product/<int:product_id>/edit', methods=['POST'])
def update_product():
    request_data = request.get_json()
    product_id = request_data['product_id']
    if Product.query.first_or_404():
        product = Product.query.filter(Product.product_id==product_id)
        data = product.update(dict(request_data))
        db.session.commit()

        result = products_schema.dump(data)
        return jsonify(result)


##### MARKETING METRTICS - SEASON_SALE FUNCTIONS #####
# Add a season_sale
@app.route("/ssale", methods=['POST'])
def add_season_sale():
    request_data = request.get_json()
    print(request_data)
    year = int(request_data['year'])
    season = int(request_data['season'])
    sale = int(request_data['sale'])

    new_season_sale = Season_Sale(year, season, sale)
    db.session.add(new_season_sale)
    db.session.commit()

    return season_sale_schema.jsonify(new_season_sale)


# Get all season_sales
@app.route('/ssale', methods=['GET'])
def get_season_sales():
    # Check if there is any season_sale in database, if no, response a 404 page
    if Season_Sale.query.first_or_404():
        all_season_sales = Season_Sale.query.all()
        result = season_sales_schema.dump(all_season_sales)
        return jsonify(result)


# Get a single season_sale by year and season
@app.route('/ssale/<int:year>/<int:season>', methods=['GET'])
def get_season_sale(year, season):
    # Check if there is any season_sale in this year and season in database, if no, response a 404 page
    if Season_Sale.query.filter_by(year=year, season=season).first_or_404():
        # If two input parameters or above, using tuple
        season_sale = Season_Sale.query.get((year, season))
        return season_sale_schema.jsonify(season_sale)


# Get all season_sales in single year by year
@app.route('/ssale/year/<int:year>', methods=['GET'])
def get_season_sales_by_year(year):
    # Check if there is any season_sale in this year in database, if no, response a 404 page
    if Season_Sale.query.filter_by(year=year).first_or_404():
        season_sales_by_year = Season_Sale.query.filter_by(year=year).all()
        result = season_sales_schema.dump(season_sales_by_year)
        return jsonify(result)


# Get all season_sales in single season by season
@app.route('/ssale/season/<int:season>', methods=['GET'])
def get_season_sales_by_season(season):
    # Check if there is any season_sale in this season in database, if no, response a 404 page
    if Season_Sale.query.filter_by(season=season).first_or_404():
        season_sales_by_season = Season_Sale.query.filter_by(
            season=season).all()
        result = season_sales_schema.dump(season_sales_by_season)
        return jsonify(result)


# Update a season_sale by year and season
@app.route('/ssale/<int:year>/<int:season>', methods=['PUT'])
def update_season_sale(year, season):
    # Check if there is any season_sale in this year and season in database, if no, response a 404 page
    if Season_Sale.query.filter_by(year=year, season=season).first_or_404():
        # Update a record by year and season
        season_sale_to_update = Season_Sale.query.get((year, season))
        sale = request.json["sale"]
        season_sale_to_update.sale = sale
        db.session.commit()
        return season_sale_schema.jsonify(season_sale_to_update)


# Delete a season_sale by year and season
@app.route('/ssale/<int:year>/<int:season>', methods=['DELETE'])
def delete_season_sale(year, season):
    # Check if there is any season_sale in this year and season in database, if no, response a 404 page
    if Season_Sale.query.filter_by(year=year, season=season).first_or_404():
        # DELETE A RECORD BY year and season
        season_sale_to_delete = Season_Sale.query.get((year, season))
        db.session.delete(season_sale_to_delete)
        db.session.commit()
        return season_sale_schema.jsonify(season_sale_to_delete)

##### 顧客活動指標 #####
# 回購率
@app.route('/repurchase-rate', methods=['GET'])
def cal_repurchase_rate():
    one_year_ago = datetime.today() - timedelta(days = 365)
    two_year_ago = datetime.today() - timedelta(days = 730)
    if Order.query.filter(Order.date >= two_year_ago, Order.date <= one_year_ago).first_or_404():
        last_year_orders = Order.query.filter(Order.date >= two_year_ago, Order.date <= one_year_ago).group_by(Order.member_id).all()
        result = orders_schema.dump(last_year_orders)
        member_id_list =[]
        for order in last_year_orders:
            member_id_list.append(order.member_id)
        count = 0
        for member_id in member_id_list:
            if Order.query.filter(Order.date >= one_year_ago, Order.member_id == member_id).first():
                count += 1
        repurchase_rate = count /len(member_id_list)
        result = {"repurchase_rate": repurchase_rate}
        return jsonify(result)

# 活躍率
@app.route('/active-rate', methods=['GET'])
def cal_active_rate():
    one_year_ago = datetime.today() - timedelta(days = 365)
    result = []
    member_id_list = []
    members = Member.query.all()
    for member in members: 
        member_id_list.append(member.id)
    for member_id in member_id_list:
        name = Member.query.get(member_id).member_name
        if Order.query.filter(Order.date >= one_year_ago, Order.member_id==member_id).first():
            count = Order.query.filter(Order.date >= one_year_ago, Order.member_id==member_id).count()
            order = Order.query.filter(Order.date >= one_year_ago, Order.member_id==member_id).order_by(desc(Order.date)).first()
            months_ago_purchase = round(((datetime.today() - order.date).days)/30, 2) 
            active_rate = round(pow(months_ago_purchase/12, count), 4)
        else:
            count = 0
            months_ago_purchase = 0
            active_rate = 0
            
        result_list ={
            "member_id": member_id,
            "name": name,
            "purchase_time": count,
            "months_ago_purchase": months_ago_purchase,
            "active_rate": active_rate
        }
        result.append(result_list)
    return jsonify(result)

# RFM
@app.route('/rfm', methods=['GET'])
def cal_rfm():
    if Order.query.first_or_404():
        #R
        counts = Order.query.group_by(Order.member_id).count()
        orders = Order.query.order_by(desc(Order.date)).all()
        selected_member_id = []
        for order in orders:
            if order.member_id not in selected_member_id:
                selected_member_id.append(order.member_id)
            if len(selected_member_id) >= int((counts+1)/2):
                break
        print(selected_member_id)

        #F
        freq_dict = {}
        for member_id in selected_member_id:
            count = Order.query.filter(Order.member_id==member_id).count()
            freq_dict[member_id] = count
        print(freq_dict)
        freq_list = sorted(freq_dict.items(), key=lambda x:x[1])
        print("half length of list is", int(len(selected_member_id)/2))
        member_id_list = freq_list[int(len(selected_member_id)/2):]
        selected_member_id = []
        for i in range(len(member_id_list)):
            selected_member_id.append(member_id_list[i][0])
        print(selected_member_id)

        #M
        limit_length = (len(selected_member_id)+1)/2
        members = Member.query.filter(Member.id.in_(selected_member_id)).order_by(desc(Member.monetary)).limit(limit_length).all()
        result = members_schema.dump(members)
        print(result)
        return jsonify(result)




if __name__ == "__main__":
    app.run(debug=True)

# "POST" test data
member_test_data = {
    "member_name": "luke",
    "sex": "M",
    "age": 88
}

order_test_data = {
    "member_id": 1,
    "total_amount": 888,
    "date": "2021-12-25"
}

season_sale_test_data = {
    "year": 2019,
    "season": 1,
    "sale": 147
}