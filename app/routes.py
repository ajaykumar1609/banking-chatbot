from flask import render_template, jsonify, request, session, send_file
from flask_socketio import SocketIO
import pyttsx3
from app import app
import vosk
import json
import numpy as np
import wave
import mimetypes
from vosk import Model, KaldiRecognizer
import soundfile
import wave
from app.utils import user_exists, create_user, transfer_money,authorize_user, get_user_accounts, handle_menu_options, generate_user_id
@app.route('/')
def chat():
    return render_template('chat.html')


vosk_model = Model("/Users/kotaajaykumar/Downloads/vosk-model-small-en-in-0.4")
recognizer = vosk.KaldiRecognizer(vosk_model, 16000)

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    message = data.get('message')
    s_id = session.get('s_id')
    print(message,s_id)
    # Check if user_s_id is in the session
    if message.lower() == 'bye':
        session.clear()
        return jsonify({'response': "Goodbye! Have a great day."})
    if not s_id:
        # If user_id is not in the session, it's a new session
        new_user_id = generate_user_id()
        print("Generated user_id:", new_user_id)
        session['s_id'] = new_user_id  # Generate a new user_id
        print("Assigned user_id:", session['s_id'])
        response = "Hello! Welcome to our banking chatbot. Please enter your name."
        return jsonify({'response': response})

    # Check if the user has provided their name
    if 'name' not in session:
        # Ask for the user's name
        session['name'] = message.upper()
        if user_exists(message.upper()):
            response = f"Welcome back, {message.capitalize()}! Please enter your authorization code."
        else:
            x = create_user(message.upper())
            success, response, auth_code = x['success'], x['message'], x['auth_code']
            # session['authorization_code'] = auth_code
            response = f"{response}, This is your authorization code auth_code : {auth_code}. Keep it safe. Now enter your authorization code."
        return jsonify({'response': response})

    # Check if the user has provided their authorization code
    if 'authorization_code' not in session:
        if authorize_user(session['name'], message):
            account_numbers = get_user_accounts(session['name'])
            print(account_numbers)
            session['authorization_code'] = message
            response = f"Welcome back, {session['name'].capitalize()}! Your account numbers are:"
            for i, account_number in enumerate(account_numbers, start=1):
                response += f"{i}. {account_number} "
            response += "Please enter the account number you want to use."
        else:
            response = "Invalid authorization code. Please try again."
        return jsonify({'response': response})
    
    if 'account_number' not in session:
        # Ask for the account number
        account_numbers = get_user_accounts(session['name'])
        if message not in account_numbers:
            response = "Invalid account number. Please try again."
            return jsonify({'response': response})
        session['account_number'] = message
        response = "Thank you! What would you like to do today?"
        return jsonify({'response': response})
    if 'transfer' in session:
        if session['transfer']:
            # If the user has initiated a transfer, handle the transfer
            sender_acc_no = session['account_number']
            receiver_acc_name, amount = message.split(":")
            receiver_acc_no = get_user_accounts(receiver_acc_name)[0]
            sender_acc_name = session['name']
            success, message = transfer_money(sender_acc_no, receiver_acc_no, int(amount),receiver_acc_name, sender_acc_name)
            session['transfer'] = False
            return jsonify({'response': message})
    # If the user has provided their name and authorization code, handle menu options
    response = handle_menu_options(message)
    if response == "initiate_transfer":
        session['transfer'] = True
        response = "Please enter the receiver's name and the amount you want to transfer by a colon(:)."
    output_file = "output.wav"  # Change this path accordingly
    # engine = pyttsx3.init(driverName='espeak')
    # engine.save_to_file(response, output_file)
    # engine.runAndWait()
    return jsonify({'response': response})


@app.route('/audio/<path:audio_path>')
def serve_audio(audio_path):
    return send_file(audio_path, mimetype='audio/wav')


@app.route('/recognize_audio', methods=['POST'])
def recognize_audio():
    
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    mime_type = mimetypes.guess_type(audio_file.filename)[0]
    print(mime_type)
    print(audio_file)
    wav_filename = 'audio_1.wav'
    audio_file.save(wav_filename)


    file_path = "audio_1.wav"

    # Read and rewrite the file with soundfile
    data, samplerate = soundfile.read(file_path)
    soundfile.write(file_path, data, samplerate)

    # Now try to open the file with wave
    with wave.open(file_path) as file:
        print('File opened!')
    # # convert_to_wav(wav_filename, 'audio.wav')
    # if not is_wav_file(wav_filename):
    #     # return jsonify({'error': 'Uploaded file is not in WAV format'}), 400
    #     print("Not a wave file")

    # result = recognize_speech_from_wav(wav_filename)
    
    # audio_data = audio_file.read()

    # # Process the audio data using Vosk recognizer
    # recognizer.AcceptWaveform(audio_data)
    # result = recognizer.Result()

    # # Parse the recognized result
    # result_json = json.loads(result)
    # while True:
    #     data = audio_file.read(4000)
    #     if len(data) == 0:
    #         break
    #     if recognizer.AcceptWaveform(data):
    #         result = json.loads(recognizer.Result())
    #         transcription = result.get('text', '')
    # print(transcription)
    wf = wave.open(wav_filename, 'rb')
    # sample_rate = wf.getframerate()
    # Process the audio file
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if recognizer.AcceptWaveform(data):
            pass
    result = recognizer.FinalResult()
    response = handle_menu_options(result)
    # return result
    # Return the recognized text
    # return jsonify({'transcription': transcription})
    return jsonify({'result': response})