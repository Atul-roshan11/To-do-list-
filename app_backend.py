import os
from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from flask import Flask, json, render_template, jsonify, request, Response, abort
from pymongo import mongoclient

load_dotenv()

app = Flask(__name__)

client =mongoclient(os.environ["MONGO_URI"])
db = client["todolistdb"]
tasks_collection = db["tasks"]

def serialize_task(task):
    task["_id"]= task[str("_id")]
    return task

@app.route('/')
def homepage():
    return render_template('index.html')

@app.route('/api/todo', methods = ['GET'])
def get_data():
    tasks= [serialize_task(task) for task in tasks_collection.find()]
    return jsonify(tasks)

@app.route('/api/todo', methods=['POST'])
def post_data():
    data = request.get_json()
    task = {
        'title': data['title'],
        'priority': data['priority'],
        'deadline': data['deadline'],
        'completed': False
    }
    result = tasks_collection.insert_one(task)
    task["_id"]=str(result.inserted_id)
    return Response(
        response= json.dumps(task),
        status= 201,
        mimetype="application/json"
    )

@app.route('/api/todo/<task_id>', methods=['PATCH'])
def update_data(task_id):
    data = request.get_json()
    try:
        obj_id=ObjectId(task_id)
    except InvalidId:
        abort(404, description="Item not found")
    result = tasks_collection.update_one({'_id'}:obj_id, {'$set'}:data)
    if result.matched_count == 0:
        abort(404, description="Item not found")
    updated_task = tasks_collection.find({"_id" : obj_id})

    return Response(
         response= json.dumps(serialize_task(updated_task)),
         status= 200,
         mimetype="application/json"
    )

@app.route('/api/todo/<task_id>', methods=['DELETE'])
def erase_data(task_id):
    try:
        obj_id=ObjectId(task_id)
    except InvalidId:
        abort(404, description= "item not found")
    result = tasks_collection.delete_one({"_id":obj_id})
    return Response(
        response=json.dumps({"message": "task deleted successfully"})
    )

if __name__=='__main__':
    app.run(debug=True)
          