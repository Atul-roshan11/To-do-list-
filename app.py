import os
import time
from datetime import timedelta
from functools import wraps
import requests
from authlib.integrations.flask_client import OAuth
from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from flask import (Flask, g, json, jsonify, redirect, render_template,Response, abort, request, session, url_for)
from pymongo import MongoClient
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)

CORS(
    app,
    supports_credentials= True,
    origins=["https://todolistfrontend-jade.vercel.app/"]
)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "to-do-list-")
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="None",
    PERMANENT_SESSION_LIFETIME=timedelta(days=7)
)
client = MongoClient(os.environ["MONGO_URI"])
db = client["todolistdb"]
tasks_collection = db["tasks"]
users_collection = db['users_id']
 
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

def refresh_google_access_token(user):
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "refresh_token": user["refresh_token"],
            "grant_type": "refresh_token",
        },
    )
    resp.raise_for_status()
    data = resp.json()
    new_expires_at = int(time.time()) + data["expires_in"]
 
    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "access_token": data["access_token"],
            "access_token_expires_at": new_expires_at,
        }
        },
    )
    return data["access_token"]
 

def get_valid_access_token(user):
    if user.get("access_token_expires_at", 0) - 60 > int(time.time()):
        return user["access_token"]
    return refresh_google_access_token(user)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("login"))
        try:
            user = users_collection.find_one({"_id": ObjectId(user_id)})
        except InvalidId:
            user = None
        if not user:
            session.clear()
            return redirect(url_for("login"))
        g.user = user
        return f(*args, **kwargs)
    return decorated
 
@app.route("/login")
def login():
    print(url_for('auth_callback'))
    redirect_uri = url_for("auth_callback", _external=True)
    return google.authorize_redirect(redirect_uri)
 
 
@app.route("/auth/callback")
def auth_callback():
    token = google.authorize_access_token()  
    userinfo = token.get("userinfo")
    if not userinfo:
        userinfo = google.get("https://www.googleapis.com/oauth2/v3/userinfo").json()
 
    google_sub = userinfo["sub"]
    update_fields = {
        "email": userinfo.get("email"),
        "name": userinfo.get("name"),
        "access_token": token["access_token"],
        "access_token_expires_at": token["expires_at"],
    }
    if token.get("refresh_token"):
        update_fields["refresh_token"] = token["refresh_token"]
 
    users_collection.update_one(
        {"google_sub": google_sub},
        {"$set": update_fields, "$setOnInsert": {"google_sub": google_sub}},
        upsert=True,
    )
    user = users_collection.find_one({"google_sub": google_sub})
 
    session.clear()
    session["user_id"] = str(user["_id"])
    session.permanent = True
 
    return redirect("https://todolistfrontend-jade.vercel.app/")
 
 
@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    if user_id:
        try:
            user = users_collection.find_one({"_id": ObjectId(user_id)})
        except InvalidId:
            user = None
        if user and user.get("refresh_token"):
            requests.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": user["refresh_token"]},
            )
    session.clear()
    return redirect("https://todolistfrontend-jade.vercel.app/")
 
def serialize_task(task):
    task["_id"] = str(task["_id"])
    task["user_id"]=str(task["user_id"])
    return task 


@app.route('/api/todo', methods=['GET'])
@login_required
def get_data():
    try:
        limit = int(request.args.get("limit", 10))
    except:
        abort(400, description="entre an integer")
    limit= max(1,min(100, limit))
    cursor_param = request.args.get("cursor")
    
    query= {}
    if cursor_param:
        try:
            query['_id']= {'$gt':ObjectId(cursor_param)}
        except:
            abort(400, description="invalid cursor")
    
    cursor = tasks_collection.find(query).sort('_id', 1 ).limit(limit +1)
    results = list(cursor)
    has_more= len(results)>limit
    results = results[:limit]
    
    next_cursor= str(results[-1]['_id']) if has_more and results else None
    
    tasks = [serialize_task(task) for task in results]
    
    return jsonify(tasks)

@app.route('/api/todo', methods=['POST'])
@login_required
def post_data():
    data = request.get_json()
    task = {
        'title': data['title'],
        'priority': data.get('priority'),
        'deadline': data.get('deadline'),
        'completed': False,
        'user_id': g.user["_id"]
    }
    result = tasks_collection.insert_one(task)
    task["_id"] = str(result.inserted_id)
    return Response(
        response=json.dumps(task),
        status=201,
        mimetype="application/json"
    )

@app.route('/api/todo/<task_id>', methods=['PATCH'])
@login_required
def update_data(task_id):
    data = request.get_json()
    try:
        obj_id = ObjectId(task_id)
    except InvalidId:
        abort(404, description="Item not found")

    result = tasks_collection.update_one({'_id': obj_id, 'user_id': g.user["_id"]}, {'$set': data})
    if result.matched_count == 0:
        abort(404, description="Item not found")

    updated_task = tasks_collection.find_one({"_id": obj_id, 'user_id': g.user["_id"]})
    return Response(
        response=json.dumps(serialize_task(updated_task)),
        status=200,
        mimetype="application/json"
    )
    
@app.route('/api/todo/<task_id>', methods=['DELETE'])
@login_required
def erase_data(task_id):
    try:
        obj_id = ObjectId(task_id)
    except InvalidId:
        abort(404, description="Item not found")

    result = tasks_collection.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        abort(404, description="Item not found")

    return Response(
        response=json.dumps({"message": "task deleted successfully"}),
        status=200,
        mimetype="application/json"
    )
    
if __name__ == '__main__':
    app.run(debug=True)

