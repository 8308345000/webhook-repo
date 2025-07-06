from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from models import collection
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/webhook', methods=['POST'])
def github_webhook():
    print("✅ Webhook POST received!")

    event_type = request.headers.get('X-GitHub-Event')
    data = request.json

    event = {
        "type": event_type,
        "author": data.get('sender', {}).get('login'),
        "timestamp": datetime.utcnow().strftime('%d %B %Y - %I:%M %p UTC')
    }

    # PUSH event
    if event_type == 'push':
        event["to_branch"] = data.get('ref', '').split('/')[-1]

    # PULL_REQUEST event
    elif event_type == 'pull_request':
        pr = data.get('pull_request', {})
        event["from_branch"] = pr.get('head', {}).get('ref')
        event["to_branch"] = pr.get('base', {}).get('ref')

        # MERGE check (Brownie points)
        if pr.get('merged'):
            event["type"] = 'merge'

    # Store in MongoDB
    try:
        collection.insert_one(event)
        print("✅ Event stored in DB:", event)
    except Exception as e:
        print("❌ Failed to insert into DB:", e)

    return "OK", 200  # Return AFTER processing

@app.route('/events')
def get_events():
    events = list(collection.find().sort('_id', -1).limit(10))
    for e in events:
        e['_id'] = str(e['_id'])  # Convert ObjectId to string for JSON
    return jsonify(events)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(port=5000)
