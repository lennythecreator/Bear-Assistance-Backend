from flask import Flask, request, jsonify
import psycopg2 

app = Flask(__name__)

@app.route("/")
def connect_to_db():
    return 'We are live 🚀'


@app.route('/UserMessage', methods = ['POST'])
def receive_user_message(userQuery):
    userQuery = request.json.get('userQuery')
    print('Received user message: {userQuery}')

    return jsonify({'message': f'user sent: {userQuery}'})

@app.route('/AiResponse', methods=['GET'])
def send_ai_response(AIanswer):
    AIanswer = "Hello from GPT :)"
    return jsonify({'AIanmswer': AIanswer})


@app.route('/loginInfo', methods=['POST'])
def get_login_information():
    login_data = request.json
    email = login_data.get('email')
    password = login_data.get('password')
    return jsonify({'status': 'success', 'message': f'login info received for {email} and for {password}'})


if __name__ == '__main__':
    app.run(debug=True)
