import os
from datetime import datetime

# pip install -U Flask
from flask import Flask, request, jsonify, render_template, abort
# pip install flask_cors
from flask_cors import CORS
# pip install flask-marshmallow
from flask_marshmallow import Marshmallow
# pip install -U Flask-SQLAlchemy
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app)

# 取得絕對的路徑位置，不會因為不同作業系統而導致的路徑表示方式之間的差異
basedir = os.path.abspath(os.path.dirname(__file__))
# CREATE DATABASE, "member-test-2" is database's name
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'member-test-2')
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

    # 一對多的一
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
    date = db.Column(db.DateTime, default=datetime.now, nullable=False)

    # 一對多的多
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)

    def __init__(self, total_amount, member_id):
        self.total_amount = total_amount
        self.member_id = member_id


# Member Schema
class MemberSchema(ma.Schema):
    class Meta:
        fields = ('id', 'member_name', 'sex', 'age', 'monetary')


# Order Schema
class OrderSchema(ma.Schema):
    class Meta:
        fields = ("order_id", "total_amount", "date", "member_id")


# Init schema
member_schema = MemberSchema()
members_schema = MemberSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

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

        new_order = Order(total_amount, member_id)
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
    "total_amount": 888
}
