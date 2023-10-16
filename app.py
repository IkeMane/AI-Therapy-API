import os
from flask import Flask, request, jsonify, session
from chat import main
import chromadb
from chromadb.config import Settings
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

print("app on")
@app.route('/get_response', methods=['POST'])

def get_response():
    data = request.get_json()
    
    #Extract data from the request
    #user_id = data.get('user_id')
    #text = data.get('text')
    api_key = data.get('api_key')
    conversation = data.get('conversation', [])
    current_profile = data.get('current_profile')
    collection_name = data.get('collection_name', "default")

    # Get collection for the user
    persist_directory = "chromadb"
    chroma_client = chromadb.PersistentClient(path=persist_directory,settings=Settings(allow_reset=True))
    collection = chroma_client.get_or_create_collection(name=collection_name)


    # # If there's a RESET command, reset data
    # if text == "RESET":
    #     chroma_client.reset()
    #     return jsonify({"response": "Conversation reset."})

    # Process the data using your main function
    response, conversation, profile = main(conversation, current_profile, collection, api_key)
    #print (response)

    #Return the processed data
    return  jsonify({
        'response': response,
        'conversation': conversation,
        'current_profile': profile,

})


if __name__ == '__main__':
    app.run()

