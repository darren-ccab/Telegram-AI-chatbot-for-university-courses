import logging
import dialogflow_v2 as dialogflow
import uuid
import json
import os
import re
import datetime
import telegram
import adminCredentials
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

# set GOOGLE_APPLICATION_CREDENTIALS=NewAgent-e6b62ce69677.json

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

telegramToken = adminCredentials.telegramToken
sourceChatToken = adminCredentials.sourceChatToken
adminList = adminCredentials.adminList
projectID = adminCredentials.projectID
PROJECT_ID = adminCredentials.PROJECT_ID

jsonLog = "sourceChatLog.json"
ticketLog = 'ticketlog.json'
ratingLog = "ratingLog.json"
deletedLog = 'deletedLog.json'

ratingThreshold = 3


USER_MESSAGE = 'userMessage'
introMessage = "I am a staff bot!"

CHOOSE_UNANSWERED, DELETE_UNANS = range(2)
CHOOSE_BAD, DELETE_PAIR = range(2)
CHOOSING, TYPING_REPLY = range(2)
RC_QUESTION, RC_ANSWER, CONFIRM_UPLOAD = range(3)
CHOSEN_DELETE_OPTION, NEXT_ACTION, REVIVE_CONFIRM, EDIT_ANSWER, EDIT_CONFIRM = range(5)

def get_user_id(update):
    user_id = update.message.from_user.id
    return user_id

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

def upload_intent(question, answerMessage):
    INTENT_DISPLAY_NAME = 'test_' + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    trainPhrase = [question]
    answerMessage = answerMessage.replace('{', '{{')
    answerMessage = answerMessage.replace('}', '}}')
    messageToReturn = [answerMessage]

    create_intent(PROJECT_ID, INTENT_DISPLAY_NAME, trainPhrase, messageToReturn)

# Command Handlers
def start(update, context):
    """Send a message when the command /start is issued."""
    startMessage = 'Hello! ' + introMessage + "\n\n type /help or help for more information and commands"
    update.message.reply_text(startMessage)

def help(update, context):
    """Send a message when the command /help is issued."""
    followUpMessage = introMessage 
    update.message.reply_text(followUpMessage)

def generateID(update, context):
    update.message.reply_text(get_user_id(update))

def generateTickets(update, context):
    with open(ticketLog) as f:
        ticketData = json.load(f)
        f.close()
        
        staffTicketData = {}

        if ticketData:
            lineCount = 0
            wholeTicketMessage = ''
            for uniqueKey in ticketData:
                lineCount += 1
                ticket = ticketData[uniqueKey]

                staffTicketData[str(lineCount)] = {'userID':ticket['userID'], USER_MESSAGE:ticket[USER_MESSAGE], 'uniqueKey':uniqueKey}
                wholeTicketMessage += str(lineCount) + '. ' + ticket[USER_MESSAGE] + ' by user '+ ticket['userID'] + '\n'

            context.user_data['staffTicketData'] = staffTicketData

            update.message.reply_text('There are {} tickets, please select ticket and reply based on ticket number given below:\n{}\n\nPlease type /cancel to cancel operation.'.format(len(ticketData), wholeTicketMessage))
            return CHOOSING
        else:
            update.message.reply_text('There are no tickets')
            return ConversationHandler.END

def selectTicket(update, context):
    text = update.message.text
    staffTicketData = context.user_data['staffTicketData']

    if text in staffTicketData:
        questionSelected = staffTicketData[str(text)]
        context.user_data['questionSelected'] = questionSelected
        update.message.reply_text('You have selected {}. {}? Please input the answer.\n\nPlease type /cancel to cancel operation.'.format(text, questionSelected[USER_MESSAGE]))
        return TYPING_REPLY 
    else:
        update.message.reply_text('Invalid Option')
        return ConversationHandler.END

def sendAnswer(update, context):
    text = update.message.text
    questionSelected = context.user_data['questionSelected']
    userID = questionSelected['userID']
    userMessage = questionSelected[USER_MESSAGE]
    fullString = 'Your ticket has been answered.\n\nQuestion: ' +userMessage + '\n\nAnswer: ' + text
    send(fullString,userID)
    update.message.reply_text('Answer Sent')

    uniqueID = questionSelected['uniqueKey']
    # remove ticket
    with open(ticketLog, "r") as ticketFile:
        ticketData = json.load(ticketFile)
        ticketFile.close()

        if uniqueID in ticketData:
            ticketData.pop(uniqueID, None)
            with open(ticketLog, "w") as ticketFile:
                json.dump(ticketData, ticketFile)
                ticketFile.close()

    return ConversationHandler.END

def send(msg, chat_id, token=sourceChatToken):
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=msg)

def startUpload(update, context):
    update.message.reply_text('This process uploads questions and answers to SourceChat. Please input question.\n\nPlease type /cancel to cancel operation.')
    return RC_QUESTION

def receiveQuestion(update, context):
    text = update.message.text
    context.user_data['question'] = text
    update.message.reply_text('Received Question: {} \n\nPlease input answer.\n\nType /cancel to cancel operation.'.format(text))
    return RC_ANSWER

def receiveAnswer(update, context):
    text = update.message.text
    context.user_data['answer'] = text
    update.message.reply_text('Received Answer: {} \n\nTo upload question and answer, please confirm by typing Yes.\n\nType /cancel to cancel operation.'.format(text))  
    return CONFIRM_UPLOAD

def uploadQuestion(update, context):
    text = update.message.text
    if text.lower() == 'yes':
        upload_intent(context.user_data['question'], context.user_data['answer'])
        update.message.reply_text('Question and Answer uploaded')
    else:
        update.message.reply_text('Process stopped, no uploading made.')
    return ConversationHandler.END

def generateUnanswered(update, context):
    with open(jsonLog) as f:
        chatData = json.load(f)
        f.close()
        if chatData:
            staffUnansweredData = {}
            lineCount = 0
            unansweredString = ''
            for uniqueKey in chatData:
                chat = chatData[uniqueKey]
                if chat['intentName'] == 'Default Fallback Intent':
                    lineCount += 1
                    unansweredString += str(lineCount) + '. ' + chat[USER_MESSAGE] + '\n'
                    staffUnansweredData[str(lineCount)] = { USER_MESSAGE:chat[USER_MESSAGE], 'uniqueKey':uniqueKey}

            context.user_data['staffUnansweredData'] = staffUnansweredData
            update.message.reply_text('There are {} unanswered questions:\n{}\n\nPlease type the number of the question to remove from list.\n\nPlease type /cancel to cancel operation.'.format(lineCount, unansweredString))
        else:
            update.message.reply_text('There are no unanswered questions')
            return ConversationHandler.END

    return CHOOSE_UNANSWERED

def chooseUnans(update, context):
    text = update.message.text
    staffUnansweredData = context.user_data['staffUnansweredData']

    if text in staffUnansweredData:
        questionSelected = staffUnansweredData[str(text)]
        context.user_data['questionSelected'] = questionSelected
        update.message.reply_text('You have selected {}. {}? Please type yes to remove the unanswered question.\n\nPlease type /cancel to cancel operation.'.format(text, questionSelected[USER_MESSAGE]))
        return DELETE_UNANS
    else:
        update.message.reply_text('Invalid Option')
        return ConversationHandler.END

def deleteUnans(update, context):
    text = update.message.text
    if text.lower() == 'yes':
        questionSelected = context.user_data['questionSelected']
        uniqueID = questionSelected['uniqueKey']
        # remove ticket
        with open(jsonLog, "r") as chatFile:
            chatData = json.load(chatFile)
            chatFile.close()
            if uniqueID in chatData:
                chatData.pop(uniqueID, None)
                with open(jsonLog, "w") as chatFile:
                    json.dump(chatData, chatFile)
                    chatFile.close()
        update.message.reply_text('Selected Question has been removed')
    else:
        update.message.reply_text('Invalid response. Selected Question has not been removed')
    return ConversationHandler.END

def generateLowRating(update, context):
    with open('ratingLog.json') as f:
        ratingData = json.load(f)
        f.close()
        if ratingData:
            staffRatingData = {}
            ratingString = ''
            lineCount = 0
            for uniqueKey in ratingData:
                intent = ratingData[uniqueKey]
                numbers = [ int(x) for x in intent['rating'] ]
                ratingScore = sum(numbers)/len(intent['rating'])
                if ratingScore <= ratingThreshold:
                    lineCount += 1
                    ratingString += str(lineCount) + '. ' + intent['intentName'] + ' - ' + str(ratingScore) + '\n'
                    staffRatingData[str(lineCount)] = intent
            
            context.user_data['staffRatingData'] = staffRatingData
            if lineCount != 0:
                update.message.reply_text('There are {} rated answers:\n{}\nSelect a number to view details of the rated answer.\n\nType /cancel to cancel the operation'.format(lineCount, ratingString))
            else:
                update.message.reply_text('There are no bad rated answers')
                return ConversationHandler.END
        else:
            update.message.reply_text('There are no bad rated answers')
            return ConversationHandler.END

    return CHOOSE_BAD

def chooseBad(update, context):
    text = update.message.text
    staffRatingData = context.user_data['staffRatingData']

    if text in staffRatingData:
        badAnswerSelected = staffRatingData[str(text)]
        context.user_data['answerSelected'] = badAnswerSelected
        #append first 5 or less than 5 messages by users to reply string with answer
        userMessageString = ''
        counter = 0
        for x in badAnswerSelected['messages']:
            counter += 1
            userMessageString += str(counter) + '. ' + x + '\n'
            if counter == 5:
                break
        update.message.reply_text('You have selected {}. {}\nUser Messages:\n{}\nAnswer: {}\n\nTo proceed with deleting, please type Yes.\n\nType /cancel to cancel operation.'.format(text, badAnswerSelected['intentName'], userMessageString, badAnswerSelected['replyMessage'][0]))
        return DELETE_PAIR
    else:
        update.message.reply_text('Invalid Option')
        return ConversationHandler.END     

def deleteQA(update, context):
    text = update.message.text
    if text.lower() == 'yes':
        badAnswerSelected = context.user_data['answerSelected']
        intentName = badAnswerSelected['intentName']
        client = dialogflow.IntentsClient()
        parent = client.project_agent_path(PROJECT_ID)
        for element in client.list_intents(parent):
            if element.display_name == intentName:
                client.delete_intent(element.name)
                update.message.reply_text('Question Answer Pair deleted')  
                break 
        
        with open(ratingLog, "r") as ratingFile:
            ratingData = json.load(ratingFile)
            ratingFile.close()

            if intentName in ratingData:
                ratingData.pop(intentName, None)
                with open(ratingLog, "w") as ratingFile:
                    json.dump(ratingData, ratingFile)
                    ratingFile.close()
        update.message.reply_text('Question Answer Pair deleted')  
    else:
        update.message.reply_text('Question Answer Pair not deleted')

    return ConversationHandler.END     

def viewdelete(update,context):
    with open(deletedLog) as f:
        deletedData = json.load(f)
        f.close()
        
        staffDeletedData = {}
        if deletedData:
            lineCount = 0
            wholeTicketMessage = ''
            for uniqueKey in deletedData:
                lineCount += 1
                ratingElement = deletedData[uniqueKey]
                staffDeletedData[str(lineCount)] = {'originalQ':ratingElement['originalQ'], 'originalA':ratingElement['originalA'], 'uniqueKey':uniqueKey, 'userMessages':ratingElement['userMessages'], 'rating':ratingElement['rating'], 'confidenceLevel':ratingElement['confidenceLevel']}
                wholeTicketMessage += str(lineCount) + '. ' + uniqueKey + ' - '+ str(ratingElement['rating']) + '\n'

            context.user_data['staffDeletedData'] = staffDeletedData
            update.message.reply_text('There are {} deleted question answers, please select an index to view details:\n{}\n\nPlease type /cancel to cancel operation.'.format(len(deletedData), wholeTicketMessage))
            return CHOSEN_DELETE_OPTION
        else:
            update.message.reply_text('There are no Deleted Data')
            return ConversationHandler.END

def selectDeleted(update, context):
    text = update.message.text
    staffDeletedData = context.user_data['staffDeletedData']

    if text in staffDeletedData:
        badAnswerSelected = staffDeletedData[str(text)]
        context.user_data['answerSelected'] = badAnswerSelected
        #append first 5 or less than 5 messages by users to reply string with answer
        userMessageString = ''
        counter = 0
        messageConfidenceLevel = badAnswerSelected['confidenceLevel']
        for x in badAnswerSelected['userMessages']:
            counter += 1
            userMessageString += str(counter) + '. ' + x + ' - ' + str(messageConfidenceLevel[counter-1]) + '\n'
            if counter == 5:
                break
        update.message.reply_text('You have selected {}. {}\nUser Messages:\n{}\nStored Question: {}\n\nStored Answer: {}\n\nTo reupload the question, type reupload.\nTo edit the answer of the question, type edit.\n\nType /cancel to cancel operation.'.format(text, badAnswerSelected['uniqueKey'], userMessageString, badAnswerSelected['originalQ'], badAnswerSelected['originalA']))
        return NEXT_ACTION
    else:
        update.message.reply_text('Invalid Option')
        return ConversationHandler.END

    return ConversationHandler.END

def receiveOption(update, context):
    text = update.message.text
    if text == 'reupload':
        update.message.reply_text('Reupload Chosen. Please type yes to confirm reupload.\n\nType /cancel to cancel operation.')
        return REVIVE_CONFIRM
    elif text == 'edit':
        update.message.reply_text('Edit chosen. Please type in new answer.\n\nType /cancel to cancel operation.')
        return EDIT_ANSWER
    else:
        update.message.reply_text('Invalid Response.')
        return ConversationHandler.END

def uploadDeletedQuestion(update, context):
    text = update.message.text
    if text.lower() == 'yes':
        badAnswerSelected = context.user_data['answerSelected']
        upload_intent(badAnswerSelected['originalQ'], badAnswerSelected['originalA'])
        update.message.reply_text('Question and Answer uploaded')

        with open(deletedLog, "r") as deleteFile:
            deletedData = json.load(deleteFile)
            deleteFile.close()
            if badAnswerSelected['uniqueKey'] in deletedData:
                deletedData.pop(badAnswerSelected['uniqueKey'], None)
                with open(deletedLog, "w") as deleteFile:
                    json.dump(deletedData, deleteFile)
                    deleteFile.close()
    else:
        update.message.reply_text('Process stopped, no uploading made.')
    return ConversationHandler.END

def receiveEditted(update, context):
    text = update.message.text
    context.user_data['newAnswer'] = text
    badAnswerSelected = context.user_data['answerSelected']
    update.message.reply_text('Answer received for Question: {}\nPlease type yes to confirm upload.\n\nType /cancel to cancel operation.'.format(badAnswerSelected['originalQ']))
    return EDIT_CONFIRM

def uploadEditted(update, context):
    text = update.message.text
    if text.lower() == 'yes':
        badAnswerSelected = context.user_data['answerSelected']
        upload_intent(badAnswerSelected['originalQ'], context.user_data['newAnswer'])
        update.message.reply_text('Question and Answer uploaded')

        with open(deletedLog, "r") as deleteFile:
            deletedData = json.load(deleteFile)
            deleteFile.close()
            if badAnswerSelected['uniqueKey'] in deletedData:
                deletedData.pop(badAnswerSelected['uniqueKey'], None)
                with open(deletedLog, "w") as deleteFile:
                    json.dump(deletedData, deleteFile)
                    deleteFile.close()
    else:
        update.message.reply_text('Process stopped, no uploading made.')
    return ConversationHandler.END

def cancel(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Okay! Operation canceled.")
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
    dp.add_handler(CommandHandler("getid", generateID))

    deleted_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('viewdelete', viewdelete, Filters.user(user_id=adminList))],

        states={
            CHOSEN_DELETE_OPTION: [MessageHandler(Filters.text, selectDeleted)],
            NEXT_ACTION:[MessageHandler(Filters.text, receiveOption)],
            REVIVE_CONFIRM: [MessageHandler(Filters.text, uploadDeletedQuestion)],
            EDIT_ANSWER: [MessageHandler(Filters.text, receiveEditted)],
            EDIT_CONFIRM: [MessageHandler(Filters.text, uploadEditted)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(deleted_conv_handler)

    unanswered_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("getunanswered", generateUnanswered, Filters.user(user_id=adminList))],

        states={
            CHOOSE_UNANSWERED: [MessageHandler(Filters.text, chooseUnans)],
            DELETE_UNANS: [MessageHandler(Filters.text, deleteUnans)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(unanswered_conv_handler)

    rating_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("getlowrating", generateLowRating, Filters.user(user_id=adminList))],

        states={
            CHOOSE_BAD: [MessageHandler(Filters.text, chooseBad)],
            DELETE_PAIR: [MessageHandler(Filters.text, deleteQA)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(rating_conv_handler)

    ticket_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('gettickets', generateTickets, Filters.user(user_id=adminList))],

        states={
            CHOOSING: [MessageHandler(Filters.text, selectTicket)],
            TYPING_REPLY: [MessageHandler(Filters.text, sendAnswer)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(ticket_conv_handler)


    upload_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('uploadquestion', startUpload, Filters.user(user_id=adminList))],

        states={
            RC_QUESTION: [MessageHandler(Filters.text, receiveQuestion)],
            RC_ANSWER: [MessageHandler(Filters.text, receiveAnswer)],
            CONFIRM_UPLOAD: [MessageHandler(Filters.text, uploadQuestion)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(upload_conv_handler)

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