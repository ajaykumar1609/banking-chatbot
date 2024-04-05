import json
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from flask import session
import uuid 

import vosk
import numpy as np
import wave
from vosk import Model, KaldiRecognizer

def read_data_from_json(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

def write_data_to_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def llm_model(test_sentence):
    # Load the model and tokenizer
    model = BertForSequenceClassification.from_pretrained("app/data/Model_bert_ds_b1")
    tokenizer = BertTokenizer.from_pretrained("app/data/Model_bert_ds_b1")

    inputs = tokenizer(test_sentence, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    print(outputs.logits)
    predicted_labels = torch.argmax(outputs.logits, dim=1)
    # labels = ['GET_BALANCE', 'GET_DUE', 'TRANSFER_MONEY']
    # predicted_label = labels[predicted_labels]
    return int(predicted_labels)

def get_account_balance(account_number, user_name):
    data = read_data_from_json('app/data/data.json')
    for user in data['users']:
        if user['name'] == user_name:
            for account in user['accounts']:
                if account['acc_no'] == account_number:
                    return account['balance']
    return None  # Account not found

def check_dues(account_number, user_name):
    data = read_data_from_json('app/data/data.json')
    for user in data['users']:
        if user['name'] == user_name:
            for account in user['accounts']:
                if account['acc_no'] == account_number:
                    return account['dues']
    return None  # Account not found

def transfer_money(sender_acc_no, receiver_acc_no, amount, receiver_acc_name, sender_acc_name):
    print(sender_acc_no,receiver_acc_no)
    data = read_data_from_json('app/data/data.json')
    sender_account = None
    receiver_account = None

    # Find sender and receiver accounts
    for user in data['users']:
        if user['name'] == receiver_acc_name.upper():
            for account in user['accounts']:
                if account['acc_no'] == receiver_acc_no:
                    receiver_account = account
        if user['name'] == sender_acc_name.upper():
            for account in user['accounts']:
                if account['acc_no'] == sender_acc_no:
                    sender_account = account
    print(sender_account,receiver_account)
    # Check if sender and receiver accounts exist
    if sender_account is None or receiver_account is None:
        print(sender_account,receiver_account)
        return False, "Sender or receiver account not found."

    # Check if sender has sufficient balance
    if sender_account['balance'] < amount:
        return False, "Insufficient balance."

    # Deduct amount from sender's balance
    sender_account['balance'] -= amount

    # Add amount to receiver's balance
    receiver_account['balance'] += amount

    # Update JSON data
    write_data_to_json('app/data/data.json', data)

    return True, "Transfer successful. You have transffered " + str(amount) + " to " + str(receiver_acc_name) + "."
 # For generating unique IDs

def create_user(name):
    # Generate a unique authorization code
    auth_code = str(uuid.uuid4())

    # Read existing data from JSON file
    data = read_data_from_json('app/data/data.json')

    # Check if the user already exists
    for user in data.get('users', []):
        if user['name'] == name:
            return {'success': False, 'message': 'User already exists.'}
    account_number_counter = read_account_number_counter()
    # Create user profile
    user_profile = {'name': name.upper(), 'auth_code': auth_code, 'accounts': [{
                    "acc_no": f"{account_number_counter:03}",
                    "balance": 0,
                    "dues": 0
                }]}
    write_account_number_counter(account_number_counter+1)

    # Add user profile to data
    if 'users' not in data:
        data['users'] = []
    data['users'].append(user_profile)

    # Write updated data to JSON file
    write_data_to_json('app/data/data.json', data)

    return {'success': True, 'message': 'User created successfully.', 'auth_code': auth_code}


def user_exists(name):
    # Check if the user exists in the database
    data = read_data_from_json('app/data/data.json')
    users = data.get('users', [])
    for user in users:
        if user['name'] == name:
            return True
    return False

def authorize_user(name, auth_code):
    # Check if the user exists in the database
    data = read_data_from_json('app/data/data.json')
    users = data.get('users', [])
    for user in users:
        if user['name'] == name and user['auth_code'] == auth_code:
            return True
    return False

def get_user_accounts(name):
    # Get the accounts of the user
    data = read_data_from_json('app/data/data.json')
    users = data.get('users', [])
    for user in users:
        if user.get('name', '').upper() == name.upper():
            accounts = user.get('accounts', [])
            account_numbers = [account['acc_no'] for account in accounts]
            return account_numbers
    return []

def generate_user_id():
    # Generate a unique user_id using some method (e.g., UUID)
    id = str(uuid.uuid4())
    return id

def handle_menu_options(message):
    # Sample implementation to handle menu options
    # You can call existing functions to handle balance, dues, and transfer
    if message.lower() == 'bye':
        session.clear()
        return "Goodbye! Have a great day."
    elif llm_model(message) == 0:
        user_name = session['name']
        balance = get_account_balance(session['account_number'],user_name)
        return f"Your account balance is {balance} $ . If you want to exit, type 'bye' . Is there anything else i can help you with?."
    elif llm_model(message) == 1:
        user_name = session['name']
        dues = check_dues(session['account_number'], user_name)
        return f"Your dues are {dues}$ . If you want to exit, type 'bye' . Is there anything else i can help you with?."
    elif llm_model(message) == 2:
        return "initiate_transfer"
    else:
        return "I'm sorry, I didn't understand that. Can you please try again?"

def add_money_balance(account_number, amount):
    data = read_data_from_json('app/data/data.json')
    for user in data['users']:
        for account in user['accounts']:
            if account['acc_no'] == account_number:
                account['balance'] += amount
    write_data_to_json('app/data/data.json', data)
    return f"{amount}$ added to your account number{account_number}."

def add_money_dues(account_number, amount):
    data = read_data_from_json('app/data/data.json')
    for user in data['users']:
        for account in user['accounts']:
            if account['acc_no'] == account_number:
                account['dues'] += amount
    write_data_to_json('app/data/data.json', data)
    return f"{amount}$ added to your dues for account number{account_number}."
    

# Function to read the account number counter from a text file
def read_account_number_counter():
    try:
        with open('app/data/account_number_counter.txt', 'r') as file:
            return int(file.read().strip())
    except FileNotFoundError:
        # If the file doesn't exist, return 1 as the default counter value
        return 1

# Function to write the account number counter to a text file
def write_account_number_counter(counter):
    with open('app/data/account_number_counter.txt', 'w') as file:
        file.write(str(counter))


# def recognize_speech_from_wav(wav_filename):
#     # Initialize Vosk recognizer
#     vosk_model = Model("/Users/kotaajaykumar/Downloads/vosk-model-small-en-in-0.4")
#     recognizer = vosk.KaldiRecognizer(vosk_model, 16000)
#     # Read the WAV file
#     wf = wave.open(wav_filename, 'rb')
#     sample_rate = wf.getframerate()
#     # Process the audio file
#     while True:
#         data = wf.readframes(4000)
#         if len(data) == 0:
#             break
#         if recognizer.AcceptWaveform(data):
#             pass
#     result = recognizer.FinalResult()
#     return result