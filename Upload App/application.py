from flask import Flask, request, redirect, url_for, send_from_directory, render_template, jsonify
import os
from datetime import datetime
from pydub import AudioSegment
import pytz
import openai
import assemblyai as aai
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

client = openai.OpenAI()

# Retrieve the AssemblyAI API key from the environment variables
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

# Retrieve the OpenAI API key from the environment variables``
openai.api_key = os.getenv("AI_API_KEY")

application = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
application.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(PROCESSED_FOLDER):
    os.makedirs(PROCESSED_FOLDER)

@application.route('/')
def index():
    return render_template('index.html')

@application.route('/upload', methods=['POST'])
def upload_file():
    try:
        print("Received a file upload request")
        if 'file' not in request.files:
            print("No file part in the request")
            return jsonify(success=False, message="No file part in the request")
        file = request.files['file']
        if file.filename == '':
            print("No selected file")
            return jsonify(success=False, message="No selected file")
        if file:
            form_data = request.form.to_dict()
            name = form_data.get('name', 'unknown').replace(' ', '_')
            est = pytz.timezone('US/Eastern')
            current_time = datetime.now(est).strftime('%Y-%m-%d_%H-%M-%S')
            unique_filename = f"{name}_{current_time}.mp3"
            filepath = os.path.join(application.config['UPLOAD_FOLDER'], unique_filename)
            print(f"Saving file to {filepath}")
            file.save(filepath)
            print("File saved successfully")

            # Compress the file to 23MB
            audio = AudioSegment.from_file(filepath)
            compressed_filepath = os.path.join(application.config['PROCESSED_FOLDER'], unique_filename)
            audio.export(compressed_filepath, format="mp3", bitrate="23k")
            print(f"Compressed file saved to {compressed_filepath}")

            # Transcribe the audio file using AssemblyAI
            transcriber = aai.Transcriber()
            config = aai.TranscriptionConfig(speaker_labels=True)
            transcript = transcriber.transcribe(
                compressed_filepath,
                config=config
            )
            
            # Prepare the transcription text for OpenAI
            transcription_text = " ".join([f"Speaker {utterance.speaker}: {utterance.text}" for utterance in transcript.utterances])
            
            # Send the transcription to OpenAI Chat Completion
            response = client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=[
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                          "text": "Directions for the Assistant:\n\n\t1.\tPurpose:\n\t•\tThe AI assistant will analyze the call based on SPIN Selling methodology and Cialdini’s 7 Principles of Influence. The analysis will fill out the autofill and Cialdini keys in the JSON structure provided. The output must consist only of the JSON, which will then be sent to a webhook.\n\t2.\tAnalyze the Call:\n\t•\tSPIN Selling:\n\t•\tIdentify and count Basic, Situation, Problem, and Implication Questions in the discovery and demonstrating parts of the call.\n\t•\tEvaluate whether the implication of the problem was amplified and assess how well implicit needs were identified and converted into explicit needs.\n\t•\tCount and evaluate how objections were handled, and determine if the intake person successfully converted the PNC into a client.\n\t•\tCialdini Principles:\n\t•\tIdentify if and how each of Cialdini’s principles (Reciprocity, Liking, Authority, Social Proof, Commitment and Consistency, Scarcity, Unity) were applied during the conversation.\n\t•\tFor each principle, determine if it was used effectively and indicate this in the corresponding boolean field.\n\t•\tIdentify the Intake Person:\n\t•\tThe first person to mention the name of the law firm is the intake person. The assistant should judge this person, not the PNC.\n\t3.\tAutofill and Cialdini Key Explanation:\n\t•\tAutofill Key:\n\t•\taf1_number: Number of Basic Questions in the discovery part of the call.\n\t•\taf2_number: Number of Situation Questions in the discovery part of the call.\n\t•\taf3_number: Number of unnecessary questions asked in the discovery part of the call.\n\t•\taf4_number: Number of Problem Questions in the discovery part of the call.\n\t•\taf5_number: Number of Implication Questions in the demonstrating part of the call.\n\t•\taf6_boolean: Did the intake person amplify the implication of the problem indicated in the Implication Questions? (Yes or No)\n\t•\taf7_number: Number of implicit needs identified in the demonstrating part of the call.\n\t•\taf8_number: Number of implicit needs converted to explicit needs in the demonstrating part of the call.\n\t•\taf9_number: Number of Objections brought up by the PNC in the driving-to-a-decision part of the call.\n\t•\taf10_number: Number of Objections addressed by the intake person in the driving-to-a-decision part of the call.\n\t•\taf11_number: Number of buying questions asked by the intake person in the driving-to-a-decision part of the call.\n\t•\taf12_boolean: Was the intake person successful in converting the PNC into a client? (Yes or No)\n\t•\tCialdini Key:\n\t•\tci1_boolean: Reciprocity – Did they use it effectively? (Yes or No)\n\t•\tci2_boolean: Liking – Did they use it effectively? (Yes or No)\n\t•\tci3_boolean: Authority – Did they use it effectively? (Yes or No)\n\t•\tci4_boolean: Liking – Did they use it effectively? (Yes or No)\n\t•\tci5_boolean: Commitment and Consistency – Did they use it effectively? (Yes or No)\n\t•\tci6_boolean: Liking – Did they use it effectively? (Yes or No)\n\t•\tci7_boolean: Commitment and Consistency – Did they use it effectively? (Yes or No)\n\t•\tci8_boolean: Reciprocity – Did they use it effectively? (Yes or No)\n\t•\tci9_boolean: Social Proof – Did they use it effectively? (Yes or No)\n\t•\tci10_boolean: Authority – Did they use it effectively? (Yes or No)\n\t•\tci11_boolean: Scarcity – Did they use it effectively? (Yes or No)\n\t•\tci12_boolean: Unity – Did they use it effectively? (Yes or No)\n\t4.\tFinal Paragraphs:\n\t•\tParagraph 1: This is your overall comment on the intake person’s performance during the call. Provide general feedback on how they handled the call, based on the SPIN Selling analysis.\n\t•\tParagraph 2: This is your overall comment based on the Cialdini Principles. Provide feedback on how well they applied these principles during the call and any actionable insights for improvement.\n\t5.\tOutput Requirements:\n\t•\tThe output must be a JSON object that fills all placeholders in the key with the relevant data from the analysis. No additional information should be provided—only the JSON.\n\t•\tThe completed JSON must be sent to the designated webhook.\n\nJSON Template\n{\n\n    \"af1\": \"{{af1_number}}\",\n    \"af2\": \"{{af2_number}}\",\n    \"af3\": \"{{af3_number}}\",\n    \"af4\": \"{{af4_number}}\",\n    \"af5\": \"{{af5_number}}\",\n    \"af6\": \"{{af6_boolean}}\",\n    \"af7\": \"{{af7_number}}\",\n    \"af8\": \"{{af8_number}}\",\n    \"af9\": \"{{af9_number}}\",\n    \"af10\": \"{{af10_number}}\",\n    \"af11\": \"{{af11_number}}\",\n    \"af12\": \"{{af12_boolean}}\",\n    \"ci1\": \"{{ci1_boolean}}\",\n    \"ci2\": \"{{ci2_boolean}}\",\n    \"ci3\": \"{{ci3_boolean}}\",\n    \"ci4\": \"{{ci4_boolean}}\",\n    \"ci5\": \"{{.ci5_boolean}}\",\n    \"ci6\": \"{{.ci6_boolean}}\",\n    \"ci7\": \"{{.ci7_boolean}}\",\n    \"ci8\": \"{.ci8_boolean}}\",\n    \"ci9\": \"{{ci9_boolean}}\",\n    \"ci10\": \"{{ci10_boolean}}\",\n    \"ci11\": \"{{ci11_boolean}}\",\n    \"ci12\": \"{{ci12_boolean\",\n    \"para1\": \"{{paragraph1}}\",\n    \"para2\": \"{{paragraph2}}\"\n}"
                            }
                        ]
                    }
                ],
                temperature=1,
                max_tokens=16383,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                response_format={
                    "type": "json_object"
                }
            )
            
            # Extract the response content from OpenAI
            openai_response_content = response.choices[0].message.content
            print(openai_response_content)
            
            # Convert the response content to JSON
            openai_response_json = json.loads(openai_response_content)
            
            # Add additional fields to the JSON response
            openai_response_json.update({
                "name": form_data.get("name", ""),
                "email": form_data.get("email", ""),
                "transcript": transcription_text
            })
            
            print("Processing complete, returning payload")
            compact_payload = json.dumps(openai_response_json, separators=(',', ':'))  # Compact JSON format
            print(compact_payload)  # Print the compact JSON payload to the console
            
            # Send the payload to the webhook URL
            webhook_url = "https://services.leadconnectorhq.com/hooks/HeJLk2Lp3vTNLGO1aMMu/webhook-trigger/db1bc3fd-1632-4d45-8ae5-dcd91b5e980d"
            response = requests.post(webhook_url, json=openai_response_json)
            print(f"Webhook response status: {response.status_code}")
            print(f"Webhook response content: {response.content}")
            
            # Delete the files after processing
            os.remove(filepath)
            os.remove(compressed_filepath)
            print(f"Deleted files: {filepath} and {compressed_filepath}")
            
            return jsonify(success=True, payload=compact_payload)

    except Exception as e:
        print(f"Error during file upload: {e}")
        return jsonify(success=False, message=str(e))

@application.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    application.run()