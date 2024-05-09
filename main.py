import subprocess
import requests
import json
import smtplib
from email.mime.text import MIMEText
import threading
import queue
from macnotesapp import NotesApp

def process_output(output_queue, file_path):
    """Process and display output in real time, and write to a file."""
    with open(file_path, "w") as file:
        while True:
            line = output_queue.get()
            if line is None:
                break
            print(line, end='')  # Print each line of the output as it's received
            file.write(line)  # Write the line to the file

def extract_speech_data(input_file_path, output_file_path):
    start_marker = "[Start speaking]"
    end_marker = "whisper_print_timings:"
    capture = False
    with open(input_file_path, "r") as input_file:
        lines = input_file.readlines()
    extracted_lines = []
    for line in lines:
        if start_marker in line:
            capture = True
            continue
        if end_marker in line and capture:
            break
        if capture:
            extracted_lines.append(line)
    with open(output_file_path, "w") as output_file:
        output_file.writelines(extracted_lines)
    print(f"Data extracted and stored in {output_file_path}")

def send_email(recipient, message, title):
    YOUR_GOOGLE_EMAIL = 'alfredlongwork@gmail.com'
    YOUR_GOOGLE_EMAIL_APP_PASSWORD = 'igyz mznh sldt rjlg'
    smtpserver = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    smtpserver.ehlo()
    smtpserver.login(YOUR_GOOGLE_EMAIL, YOUR_GOOGLE_EMAIL_APP_PASSWORD)
    email_text = message
    smtpserver.sendmail(YOUR_GOOGLE_EMAIL, recipient, email_text)
    smtpserver.close()

def main():
    command = [
        "./whisper.cpp/stream",
        "-m", "./whisper.cpp/models/ggml-base.en.bin",
        "--step", "4000",
        "--length", "8000",
        "-c", "0",
        "-t", "10",
        "-ac", "512"
    ]
    
    # Create a queue to hold the output lines
    output_queue = queue.Queue()

    # Start the subprocess and set stdout to subprocess.PIPE for real-time output
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    # Start a thread to process output in real time and write it to a file
    threading.Thread(target=process_output, args=(output_queue, "output.txt"), daemon=True).start()

    # Start a thread to listen for the Enter key to stop the transcription
    stop_thread = threading.Thread(target=lambda: input("Press Enter to stop transcription\n"))
    stop_thread.start()

    try:
        # Read from the subprocess output in real time
        while True:
            if not stop_thread.is_alive():
                break  # If Enter is pressed, break the loop to stop transcription
            output_line = process.stdout.readline()
            if output_line == '' and process.poll() is not None:
                break
            if output_line:
                output_queue.put(output_line)  # Add line to the queue to be processed
    finally:
        output_queue.put(None)  # Signal the processing thread to terminate
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        print("Transcription stopped and output stored in output.txt.")
    
    extract_speech_data("output.txt", "extracted_data.txt")

    # Load extracted data as user_msg
    with open("extracted_data.txt", "r") as file:
        user_msg = file.read()
        print(f"User message extracted: {user_msg}")

    handle_user_msg(user_msg)

def handle_user_msg(user_msg):
    # user_msg = """
    # Tell Alfred that I will be late for the party tonight. I will be there at 9:30 PM with booze. Thanks! Also let Amber
    # know that we will see each other on Friday night at RareSteak House. Tell her to book the table.
    # Lastly, tell Suman that I will not come to the lecture tomorrow. I will be busy with my work. Thanks!
    # Remind me that I have a basketball game at 7:00 PM on Saturday and some groceries to buy at Target."""

    email_mapping = {
        "Alfred": "hlong25@wisc.edu",
        "Amber": "bdeng34@wisc.edu",
        "Suman": "suman@cs.wisc.edu",
    }

    schema_emails = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "person": {
                    "type": "string",
                    "description": "The name of the person to receive the email"
                },
                "message": {
                    "type": "string",
                    "description": "The message to be sent in the email"
                },
                "title": {
                    "type": "string",
                    "description": "The title of the email"
                },
                "address": {
                    "type": "string",
                    "description": "The address of the person to receive the email"
                }
            }
        }
    }

    schema_note = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the note"
                },
                "body": {
                    "type": "string",
                    "description": "The body of the note"
                }
            }
        }
    }

    payload = {
        "model": "llama2",
        "messages": [
            {"role": "system", "content": f"""
            You are a helpful AI assitant.
            The user will input a message indicating what he wants to do.
            It could be either of the two cases (or both): 
             1. Send an email to a person with a message and title. 
             2. Make himself a note so that he won't forget important things to do.
            If it falls into the first category:
            Send an email to the corresponding person with the correct information using the emails mapping provided to you here: {email_mapping}
            If there are multiple emails to send, just output every email in the same format.
            Output in JSON format using the schema defined here: {schema_emails}.
            If it falls into the second category:
            Create a new note in default folder of default account using the macnotesapp.
            Output in JSON format using the schema defined here: {schema_note}.
            Note that each thing could falls into both categories. In that case, you should output both two kinds under the corresponding schema.
            """

            """
            ======EXAMPLE=======
            {'emails': [{'person': 'some person', 'message': "some message", 'title': 'some title', 'address': 'some address'}, {...}],  'notes': [{'name': 'some name', 'body': 'some body'}, {...}]}
            ======EXAMPLE=======

            """},
            {"role": "user", "content": user_msg},
        ],
        "format": "json",
        "stream": False,
    }

    response = requests.post("http://localhost:11434/api/chat", json=payload)

    data = response.json()  # Directly parse JSON response from the server

    data = data["message"]["content"]  # Safely get the items list if it exists, else default to empty list
    data = json.loads(data)
    print(data)
    emails = data["emails"]
    notes = data["notes"]


    def send_email(recipient, message, title):
        YOUR_GOOGLE_EMAIL = 'alfredlongwork@gmail.com'
        YOUR_GOOGLE_EMAIL_APP_PASSWORD = 'igyz mznh sldt rjlg'

        smtpserver = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtpserver.ehlo()
        smtpserver.login(YOUR_GOOGLE_EMAIL, YOUR_GOOGLE_EMAIL_APP_PASSWORD)

        sent_from = YOUR_GOOGLE_EMAIL
        sent_to = recipient
        email_text = message
        smtpserver.sendmail(sent_from, sent_to, email_text)

        # Close the connection
        smtpserver.close()

    for item in emails:
        person = item["person"]
        message_content = item["message"]
        address = item["address"]
        title = item["title"]

        print(f"Preparing to send email to {person} at {address} with message: {message_content} and title: {title}")
        # send_email(address, message_content, title)
        print(f"Email sent to {person} at {address} with message: {message_content} and title: {title}")

    notesapp = NotesApp()

    for note in notes:
        name = note["name"]
        body = note["body"]

        print(f"Preparing to create note with name: {name} and body: {body}")
        notesapp.make_note(name=name, body=body)
        print(f"Note created with name: {name} and body: {body}")


if __name__ == "__main__":
    main()

