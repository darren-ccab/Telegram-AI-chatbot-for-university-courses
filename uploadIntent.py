import dialogflow_v2 as dialogflow
import datetime
import csv

# https://cloud.google.com/docs/authentication/getting-started
# set GOOGLE_APPLICATION_CREDENTIALS=NewAgent-e6b62ce69677.json

PROJECT_ID = "newagent-sokofq"
csvName = 'FYPupload.csv'

def create_intent(project_id, display_name, training_phrases_parts, message_texts):
    intents_client = dialogflow.IntentsClient()
    parent = intents_client.project_agent_path(project_id)
    training_phrases = []
    for training_phrases_part in training_phrases_parts:
        part = dialogflow.types.Intent.TrainingPhrase.Part(
            text=training_phrases_part)
        # Here we create a new training phrase for each provided part.
        training_phrase = dialogflow.types.Intent.TrainingPhrase(parts=[part])
        training_phrases.append(training_phrase)

    text = dialogflow.types.Intent.Message.Text(text=message_texts)
    message = dialogflow.types.Intent.Message(text=text)

    intent = dialogflow.types.Intent(
        display_name=display_name,
        training_phrases=training_phrases,
        messages=[message])

    response = intents_client.create_intent(parent, intent)

    print('Intent {} created: {}'.format(display_name, response))

#INTENT_DISPLAY_NAME = 'test_' + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
# MESSAGE_TEXTS = ['mr tester']
# TRAINING_PHRASE_PARTS = ['what is my new name']
#create_intent(PROJECT_ID, INTENT_DISPLAY_NAME, TRAINING_PHRASE_PARTS,MESSAGE_TEXTS)

with open(csvName, newline='', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    lineCount = 0

    for row in csv_reader:
        INTENT_DISPLAY_NAME = 'test_' + str(lineCount) + '_' + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        trainPhrase = [row[0]]

        answerMessage = row[1]
        answerMessage = answerMessage.replace('{', '{{')
        answerMessage = answerMessage.replace('}', '}}')
        messageToReturn = [answerMessage]

        create_intent(PROJECT_ID, INTENT_DISPLAY_NAME, trainPhrase, messageToReturn)

        lineCount += 1

