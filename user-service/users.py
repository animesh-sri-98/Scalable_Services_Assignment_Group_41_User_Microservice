from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import requests

app = Flask(__name__)
print("connecting to mongodb server")
client = MongoClient("mongodb://mongodb-service:27017/")
db = client["users_db"]
collection = db["users"]

# Get the last used user_id from the database
last_user = collection.find_one(sort=[("user_id", -1)])
if last_user:
    last_user_id = last_user["user_id"]
else:
    last_user_id = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/users', methods=['POST'])
def create_user():
    global last_user_id
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')

    # Validate input fields
    if not username or not isinstance(username, str) or not email or not isinstance(email, str):
        return jsonify({"message": "Invalid input data"}), 400

    # Increment the user_id and insert new user into MongoDB
    last_user_id += 1
    user_data = {
        "user_id": last_user_id,
        "username": username,
        "email": email
    }
    collection.insert_one(user_data)

    response = {
        "message": "User created successfully",
        "user_id": last_user_id
    }
    return jsonify(response), 201

@app.route('/users', methods=['GET'])
def get_all_users():
    # Retrieve all users from MongoDB
    users = list(collection.find({}, {"_id": 0}))
    return jsonify(users), 200

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # Retrieve user details from MongoDB based on user_id
    user = collection.find_one({"user_id": user_id})

    if user:
        response = {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"]
        }
        return jsonify(response), 200
    else:
        # User not found, return 404 response
        return jsonify({"message": "User not found"}), 404
    
@app.route('/users/<int:user_id>/orders', methods=['GET'])
def get_orders_by_user_id(user_id):
    # Retrieve orders for a specific user based on user_id
    order_url = f'http://order-microservice:80/orders/{user_id}'

    try:
        order_response = requests.get(order_url, timeout=5)
        order_response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        return jsonify(order_response.json()), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"message": "Error fetching orders"}), 500
    
@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    new_username = data.get('username')
    new_email = data.get('email')

    # Validate input fields
    if not new_username or not isinstance(new_username, str) or not new_email or not isinstance(new_email, str):
        return jsonify({"message": "Invalid input data"}), 400

    # Update user details in MongoDB based on user_id
    user = collection.find_one({"user_id": user_id})
    if user:
        user['username'] = new_username
        user['email'] = new_email
        collection.update_one({"user_id": user_id}, {"$set": user})
        return jsonify({"message": "User details updated successfully"}), 200
    else:
        # User not found, return 404 response
        return jsonify({"message": "User not found"}), 404
    
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Delete user from MongoDB based on user_id
    result = collection.delete_one({"user_id": user_id})

    if result.deleted_count > 0:
        return jsonify({"message": "User deleted successfully"}), 200
    else:
        # User not found, return 404 response
        return jsonify({"message": "User not found"}), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9998)
