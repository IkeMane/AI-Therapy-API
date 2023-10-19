import os
from flask import Flask, request, jsonify, session
from chat import main
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

print("app on")
@app.route('/get_response', methods=['POST'])

def get_response():
    try:
        data = request.get_json()
        #Extract data from the request
        api_key = data.get('api_key')
        conversation = data.get('conversation', [])
        #print(type(conversation))
        #print('\n\nConversation: %s' %conversation)
        current_profile = data.get('current_profile')
        kb = data.get('kb')

        # Process the data using your main function
        response, conversation, profile,kb = main(conversation, current_profile, kb, api_key)
        #print (response)

        #Return the processed data
        return  jsonify({
            'response': response,
            'conversation': conversation,
            'current_profile': profile,
            'kb': kb,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run()

