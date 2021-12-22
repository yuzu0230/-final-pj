import os
# pip install -U Flask
from flask import Flask, request, jsonify, render_template
# pip install -U Flask-SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
# pip install flask-marshmallow
from flask_marshmallow import Marshmallow


app = Flask(__name__)

# 取得絕對的路徑位置，不會因為不同作業系統而導致的路徑表示方式之間的差異
basedir = os.path.abspath(os.path.dirname(__file__))
# CREATE DATABASE, "pj-test-1" is database's name
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'member-test-1')
# Optional: But it will silence the deprecation warning in the console.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

ma = Marshmallow(app)


class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_name = db.Column(db.String(50), nullable=False)
    sex = db.Column(db.String(50), nullable=False)
    age = db.Column(db.String(50), nullable=False)
    residence = db.Column(db.String(50))
    monetary = db.Column(db.String(50), nullable=False)

    def __init__(self, id, member_name, sex, age, residence, monetary):
        self.id = id
        self.member_name = member_name
        self.sex = sex
        self.age = age
        self.residence = residence
        self.monetary = monetary


# Member Schema
class MemberSchema(ma.Schema):
  class Meta:
    fields = ('id', 'member_name', 'sex', 'age', 'residence', 'monetary')


# Init schema
member_schema = MemberSchema()
members_schema = MemberSchema(many=True)

db.create_all()

@app.route('/')
def home():
    # READ ALL RECORDS
    all_members = db.session.query(Member).all()
    print(all_members)
    return render_template("index.html", members=all_members)


# Add a member
@app.route("/member", methods=['POST'])
def add_member():
    request_data = request.get_json()
    print(request_data)
    id = int(request.json['id'])
    member_name = request_data['member_name']
    sex = request_data['sex']
    age = request_data['age']
    residence = request_data['residence']
    monetary = request_data['monetary']

    new_member = Member(id, member_name, sex, age, residence, monetary)
    db.session.add(new_member)
    db.session.commit()

    return member_schema.jsonify(new_member)


# Get all member
@app.route('/member', methods=['GET'])
def get_members():
    all_members = Member.query.all()
    result = members_schema.dump(all_members)
    return jsonify(result)


# Get a single member by id
@app.route('/member/<id>', methods=['GET'])
def get_member(id):
    member = Member.query.get(id)
    return member_schema.jsonify(member)


# Delete a member by id
@app.route('/member/<id>', methods=['DELETE'])
def delete_member(id):
    # DELETE A RECORD BY ID
    member_to_delete = Member.query.get(id)
    db.session.delete(member_to_delete)
    db.session.commit()
    return member_schema.jsonify(member_to_delete)


if __name__ == "__main__":
    app.run(debug=True)


# Test data
test_data = {
    "id": 9,
    "member_name": "luke",
    "sex": "M",
    "age": "88",
    "residence": "xinyi",
    "monetary": 88888
}
