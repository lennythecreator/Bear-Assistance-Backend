from flask import Flask, request, jsonify
import psycopg2
import chat
import awss3
import urllib.parse
from flask_cors import CORS
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import os
import uuid
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

load_dotenv()

# Initialize ElevenLabs for Voice Responses
client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
)

@app.route("/")
def home():
    return 'We are live 🚀'


def connect_to_db():
    try:
        connection = psycopg2.connect(
            dbname="postgres",
            user="test",
            password="test",
            host="localhost",
            port="5432"
        )
        print("DB connection successful")
        return connection
    except Exception as e:
        print(f"DB connection failed: {e}")
        return None

store =[]
@app.route("/ask", methods=["POST"])
def ask_question():
    try:
        data = request.json
        question = data.get("question", "")
        if not question:
            return jsonify({"error": "No question asked"})
        
        response = chat.graph.invoke({"question": ", ".join(store)+ " " + question})
        answer = response["answer"]
        #store.append(f"question: {question}, response: {answer}")
        # Convert the answer to speech
        # audio = client.text_to_speech.convert_as_stream(
        #     text=answer,
        #     voice_id="onwK4e9ZLuTAKqWW03F9",
        #     model_id="eleven_multilingual_v2",
        #     output_format="mp3_44100_128",
        # )
        
        return jsonify({"answer": response["answer"]})
        
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/loginInfo', methods=['POST'])
def get_login_information():
    login_data = request.json
    email = login_data.get('email')
    password = login_data.get('password')
    return jsonify({'status': 'success', 'message': f'login info received for {email} and for {password}'})


import logging
logging.basicConfig(level=logging.DEBUG)
@app.route('/uploadTranscripts', methods=['POST'] )
def upload_file():
    if 'file' not in request.files:
        return {"error": "No file part"}, 400

    file = request.files['file']
    filename = file.filename
    my_uuid = uuid.uuid4()
    safe_filename = urllib.parse.quote(filename)
    mimetype = file.mimetype
    
    file_url = awss3.s3.uploadToS3(file, f"uploads/{my_uuid}", mimetype)
    print(file_url)
    # Connect to the database
    connection = connect_to_db()
    if connection is None:
        return {"error": "Database connection failed"}, 500

    try:
        cursor = connection.cursor()
        # Insert the file URL into the transcripts table
        cursor.execute("INSERT INTO public.transcripts (file_url) VALUES (%s)", (file_url,))
        connection.commit()
        cursor.close()
    except Exception as e:
        logging.error(f"Error inserting into database: {e}")
        return {"error": f"error inserting {safe_filename} into database"}, 500
    finally:
        connection.close()
    return {'url': file_url}, 201


@app.route('/retrieveTranscripts', methods=['GET'])
def send_user_transcripts():
    try:
        # Connect to the database
        connection = connect_to_db()
        cursor = connection.cursor()

        # Query the database for all file URLs
        cursor.execute("SELECT file_url FROM transcripts")
        urls = cursor.fetchall()

        # Close the database connection
        cursor.close()
        connection.close()

        # Extract URLs from the query result
        url_list = [url[0] for url in urls]

        # Return the URLs in a JSON response
        return jsonify({'success': True, 'transcripts': url_list}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
if __name__ == "__main__":
    app.run(debug=True)
    try:
        _, audio = ask_question()
        play(audio)
    except Exception as e:
        print(f"Error occurred: {str(e)}")