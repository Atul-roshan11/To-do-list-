import os
from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from flask import Flask, json, render_template, jsonify, request, Response, abort
from pymongo import MongoClient

load_dotenv()

app = Flask(__name__)
client = MongoClient(os.environ["MONGO_URI"])
db = client["todolistdb"]
tasks_collection = db["tasks"]

def serialize_task(task):
    task["_id"] = str(task["_id"])
    return task 

@app.route('/api/todo', methods=['GET'])
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
def post_data():
    data = request.get_json()
    task = {
        'title': data['title'],
        'priority': data['priority'],
        'deadline': data['deadline'],
        'completed': False
    }
    result = tasks_collection.insert_one(task)
    task["_id"] = str(result.inserted_id)
    return Response(
        response=json.dumps(task),
        status=201,
        mimetype="application/json"
    )

@app.route('/api/todo/<task_id>', methods=['PATCH'])
def update_data(task_id):
    data = request.get_json()
    try:
        obj_id = ObjectId(task_id)
    except InvalidId:
        abort(404, description="Item not found")

    result = tasks_collection.update_one({'_id': obj_id}, {'$set': data})
    if result.matched_count == 0:
        abort(404, description="Item not found")

    updated_task = tasks_collection.find_one({"_id": obj_id})
    return Response(
        response=json.dumps(serialize_task(updated_task)),
        status=200,
        mimetype="application/json"
    )

@app.route('/api/todo/<task_id>', methods=['DELETE'])
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

