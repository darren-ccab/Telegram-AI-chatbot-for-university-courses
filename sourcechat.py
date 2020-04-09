import logging
import hashlib
import dialogflow_v2 as dialogflow
import uuid
import json
import os
import re
import telegram
import generalCredentials
from google.protobuf.json_format import MessageToJson
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

# https://cloud.google.com/docs/authentication/getting-started
# set GOOGLE_APPLICATION_CREDENTIALS=[credentials_PATH]
# set GOOGLE_APPLICATION_CREDENTIALS=NewAgent-e6b62ce69677.json

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

telegramToken = generalCredentials.telegramToken
announcementID = generalCredentials.announcementID
projectID = generalCredentials.projectID

jsonLog = "sourceChatLog.json"
ticketLog = 'ticketlog.json'
ratingLog = "ratingLog.json"
deletedLog = 'deletedLog.json'

thresholdNum = 3
ratingDeleteThreshold = 1.5

introMessage = "Just ask me a question and I will try my best to answer it.\nExample: 'What is a compound function?'"
replyFeedback = 'For feedback on answer, please reply to the answer with comments using command: /feedback comment'
ticketSubmitMessage = 'To create a ticket, you can reply to the answer given using command: /ticket'
rateMessage = 'To rate an answer, please reply to the answer given using command: /rate'

RATING = range(1)

def get_user_id(update):
    user_id = update.message.from_user.id
    return user_id

def generateID(responseMessage):
    return hashlib.sha1((str(responseMessage.chat_id) + str(responseMessage.message_id)).encode()).hexdigest()

def fileCheck(fileName):
    if os.path.exists(fileName):
        # checks if file exists
        print ("{} exists and is readable".format(fileName))
    else:
        print ("{} is missing or is not readable, creating file...".format(fileName))
        with open(fileName, 'w') as db_file:
            db_file.write(json.dumps({}))
            db_file.close()

def startupCheck():
    fileCheck(jsonLog)
    fileCheck(ticketLog)
    fileCheck(ratingLog)
    fileCheck(deletedLog)

def send(msg, chat_id, token=telegramToken):
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=msg)

# Dialogflow Detect Intent
def detect_intent_texts(project_id, session_id, texts, language_code):
    """Returns the result of detect intent with texts as inputs.
    Using the same `session_id` between requests allows continuation
    of the conversation."""
    session_client = dialogflow.SessionsClient()

    session = session_client.session_path(project_id, session_id)
    # print('Session path: {}\n'.format(session))

    text_input = dialogflow.types.TextInput(text=texts, language_code=language_code)
    query_input = dialogflow.types.QueryInput(text=text_input)

    response = session_client.detect_intent(session=session, query_input=query_input)

    print('=' * 50)
    print('Query text: {}'.format(response.query_result.query_text))
    print('Detected intent: {} (confidence: {})\n'.format(response.query_result.intent.display_name, response.query_result.intent_detection_confidence))
    print('Fulfillment text: {}\n'.format(response.query_result.fulfillment_text))

    return response.query_result.fulfillment_text, response.query_result.intent.display_name, response.query_result.intent_detection_confidence

# Command Handlers
def start(update, context):
    """Send a message when the command /start is issued."""
    startMessage = 'Hello! ' + introMessage + "\n\n type /help or help for more information and commands"
    update.message.reply_text(startMessage)

def help(update, context):
    """Send a message when the command /help is issued."""
    followUpMessage = introMessage + '\n\n' + replyFeedback + '\n\n' + ticketSubmitMessage + '\n\n' + rateMessage
    update.message.reply_text(followUpMessage)

def ticket(update, context):
    if update.message.reply_to_message is not None:
        userID = str(get_user_id(update))

        with open(jsonLog, "r") as jsonFile:
            data = json.load(jsonFile)
            jsonFile.close()
            uniqueID = generateID(update.message.reply_to_message)
            
            if uniqueID in data:
                element = data[uniqueID]
                with open(ticketLog, "r") as ticketFile:
                    ticketData = json.load(ticketFile)
                    ticketFile.close()

                    if uniqueID not in ticketData:
                        with open(ticketLog, "w") as ticketFile:
                            ticketData[uniqueID] = {'userMessage': element['userMessage'], 'userID': userID}
                            json.dump(ticketData, ticketFile)
                            ticketFile.close()
                        update.message.reply_text('Ticket submitted. Please wait for response to be sent to your Telegram.')
                        send("New Ticket Submitted: {}\nPlease go to @source_chat_staff_bot to respond".format(element['userMessage']), announcementID)
                    else:
                        update.message.reply_text('Ticket already submitted. Please wait for response to be sent to your Telegram.')
            else:
                update.message.reply_text('This is not my answer. Please reply /ticket to my answer.')           
    else:
        update.message.reply_text('Invalid Format. To submit a ticket, please reply to my answer using: \n/ticket')

def feedback(update, context):
    if update.message.reply_to_message is not None:
        if len(context.args) >= 1:
            uniqueID = generateID(update.message.reply_to_message)
            feedbackMessage = ' '.join(context.args[0:len(context.args)])

            with open(jsonLog, "r") as jsonFile:
                data = json.load(jsonFile)
                jsonFile.close()

            if uniqueID in data:
                element = data[uniqueID]
                element['comments'].append(feedbackMessage)    

                with open(jsonLog, "w") as jsonFile:
                    json.dump(data, jsonFile)
                    jsonFile.close()

                update.message.reply_text('Feedback Received')
            else:
                update.message.reply_text('This is not my answer. Please reply to my answer:\n/feedback comment') 
        else:
            update.message.reply_text('Invalid feedback format. Please try again, E.g: \n/feedback comment')        
    else:
        update.message.reply_text('Invalid Format. To comment on an answer, please reply to my answer using: \n/feedback comment')

def rate(update, context):
    if update.message.reply_to_message is not None:
        uniqueID = generateID(update.message.reply_to_message)

        with open(jsonLog, "r") as jsonFile:
            data = json.load(jsonFile)
            jsonFile.close()

        if uniqueID in data:
            context.user_data['uniqueID'] = uniqueID
            context.bot.send_message(chat_id=update.message.chat_id, text='Type in a rating from 1 to 5, with 1 being the worst and 5 being the best\n\nType /cancel to cancel operation.')
        else:
            update.message.reply_text('This is not my answer. Please reply to my answer:\n/rate')
            return ConversationHandler.END
    else:
        update.message.reply_text('Invalid Format. To rate an answer, please reply to my answer using: \n/rate')
        return ConversationHandler.END

    return RATING

def receive_rating(update, context):
    rating = update.message.text
    uniqueID = context.user_data['uniqueID']

    if re.match(r"[1-5]", rating):
        with open(jsonLog, "r") as jsonFile:
            chatHistory = json.load(jsonFile)
            jsonFile.close()

        with open(ratingLog, "r") as jsonFile:
            ratingData = json.load(jsonFile)
            jsonFile.close()
            
        with open(ratingLog, "w") as ratingFile:
            intentName = chatHistory[uniqueID]['intentName']

            if intentName in ratingData:
                ratingData[intentName]['messages'].append(chatHistory[uniqueID]['userMessage'])
                ratingData[intentName]['confidenceLevel'].append(chatHistory[uniqueID]['confidenceLevel'])
                ratingData[intentName]['rating'].append(rating)

            else:
                ratingData[intentName] = {'intentName': intentName, 'replyMessage':[chatHistory[uniqueID]['replyMessage']] , 'messages': [chatHistory[uniqueID]['userMessage']], 'rating': [rating], 'confidenceLevel':[chatHistory[uniqueID]["confidenceLevel"]]}
                
            json.dump(ratingData, ratingFile)
            ratingFile.close()

            if len(ratingData[intentName]['rating']) >= thresholdNum:
                numbers = [ int(x) for x in ratingData[intentName]['rating'] ]
                ratingScore = sum(numbers)/len(ratingData[intentName]['rating'])
                if ratingScore <= ratingDeleteThreshold:
                    # Delete from dialogflow
                    # Upload to staff delete json file
                    # pop from ratingLog?
                    chosen = False
                    client = dialogflow.IntentsClient()
                    parent = client.project_agent_path(projectID)
                    for element in client.list_intents(parent, intent_view='INTENT_VIEW_FULL'):
                        if element.display_name == intentName:
                            chosenElement = element
                            chosen = True
                            break 
                      
                    if chosen == True:
                        client.delete_intent(chosenElement.name)
                        newElement = json.loads(MessageToJson(chosenElement))
                        
                        stringToSend = 'Intent Name: ' + intentName + '\n\n' +'Stored Question: '+ newElement['trainingPhrases'][0]['parts'][0]['text'] + '\n\n' + 'Stored Answer: ' + newElement['messages'][0]['text']['text'][0]
                        userMessageString = ''
                        counter = 0
                        userMessages = ratingData[intentName]['messages']
                        messageConfidenceLevel = ratingData[intentName]['confidenceLevel']
                        for x in userMessages:
                            counter += 1
                            userMessageString += str(counter) + '. ' + x + ' - ' + str(messageConfidenceLevel[counter-1]) + '\n'
                            if counter == 3:
                                break

                        if intentName in ratingData:
                            ratingData.pop(intentName, None)
                            with open(ratingLog, "w") as ratingFile:
                                json.dump(ratingData, ratingFile)
                                ratingFile.close()

                        with open(deletedLog, "r") as deleteFile:
                            deletedData = json.load(deleteFile)
                            deleteFile.close()

                            deletedData[intentName] = {'userMessages':userMessages, 'rating':ratingScore, 'confidenceLevel':messageConfidenceLevel, 'originalQ': newElement['trainingPhrases'][0]['parts'][0]['text'], 'originalA': newElement['messages'][0]['text']['text'][0]}

                            with open(deletedLog, "w") as deleteFile:
                                json.dump(deletedData, deleteFile)
                                deleteFile.close()                                              
                        
                        send("Question Answer Deleted via Rating System\nRating: {}\n\n{}\n\nUser Messages:\n{}".format(ratingScore, stringToSend, userMessageString), announcementID)

            context.bot.send_message(chat_id=update.message.chat_id, text="Your rating {} has been received.".format(rating))
    else:
        update.message.reply_text('Invalid Format. To rate an answer, please type in a rating from 1 to 5, with 1 being the worst and 5 being the best')
        return ConversationHandler.END

    return ConversationHandler.END

def textMessage(update, context):
    """Process the user message through dialogflow"""
    userID = str(get_user_id(update))
    userMessage = update.message.text
    dialogID = str(uuid.uuid4())
    
    responseText, intentName, confidenceLevel = detect_intent_texts(projectID, dialogID, userMessage, "en-US")  
    responseMessage = update.message.reply_text(responseText)

    if intentName != 'Default Welcome Intent' and intentName != 'helper':
        followUpMessage = replyFeedback + '\n\n' + ticketSubmitMessage + '\n\n' + rateMessage
        update.message.reply_text(followUpMessage)
        uniqueID = generateID(responseMessage)
        with open(jsonLog, "r") as jsonFile:
            data = json.load(jsonFile)

        data[uniqueID] = {'confidenceLevel': confidenceLevel, 'intentName': intentName, 'userMessage': userMessage, 'userID': userID, 'replyMessage': responseText,'comments': []}

        with open(jsonLog, "w") as jsonFile:
            json.dump(data, jsonFile)
            jsonFile.close()

        if intentName == 'Default Fallback Intent':
            send("Unable to respond to User Message:\n{}".format(userMessage), announcementID)


def cancel(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Okay! Rating canceled.")
    return ConversationHandler.END

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    """Start the bot."""
    updater = Updater(telegramToken, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("ticket", ticket))
    dp.add_handler(CommandHandler("feedback", feedback))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('rate', rate)],
        states={
            RATING: [MessageHandler(Filters.text, receive_rating)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv_handler)

    dp.add_handler(MessageHandler(Filters.text, textMessage))

    # log all errors
    dp.add_error_handler(error)

    # Start Telegram Bot
    updater.start_polling()
    print('Bot Started')

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT.
    updater.idle()

if __name__ == '__main__':
    startupCheck()
    main()