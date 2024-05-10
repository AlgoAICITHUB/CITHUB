from pymongo import MongoClient
from bson.objectid import ObjectId


DATABASE = 'cithubNever'

uri = "mongodb+srv://tudo:tudo@cluster0.xrxmrc8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client[DATABASE]

def get_user_by_username(username):
    user = db.users.find_one({"username": username})
    return user

def create_user(username, password, email):
    user_id = db.users.insert_one({
        "username": username,
        "password": password,
        "email": email
    }).inserted_id
    return user_id

def create_profile_for_user(user_id):
    db.profiles.insert_one({
        "user_id": user_id,
        "photo": "",
        "bio": ""
    })

def validate_user_login(username, password):
    user = db.users.find_one({
        "username": username,
        "password": password
    })
    return user

def upload(user_id,title,content):
    db.posts.insert_one({
    "user_id": user_id,
    "title": title,
    "content": content
})
    

