import json
import csv
import os

USER_MESSAGE = 'userMessage'
USER_EMAIL = 'userID'

class CSVWriter():

    filename = None
    fp = None
    writer = None

    def __init__(self, filename):
        self.filename = filename
        self.fp = open(self.filename, 'w', encoding='utf8')
        self.writer = csv.writer(self.fp, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL, lineterminator='\n')

    def close(self):
        self.fp.close()

    def write(self, elems):
        self.writer.writerow(elems)

    def size(self):
        return os.path.getsize(self.filename)

    def fname(self):
        return self.filename

commentsCsv = CSVWriter('toBeUpdated.csv')

print('Generating Results....\n')

print('-'*100)

print('Generating Answers with Comments')

print('-'*100)

with open('sourceChatLog.json') as f:
    chatData = json.load(f)
    if chatData:
        for uniqueKey in chatData:
            chat = chatData[uniqueKey]
            if chat['comments']:
                commentsCsv.write((chat["intentName"],chat['userMessage'], chat['replyMessage'], chat['comments']))

        print('\nComments listed in toBeUpdated.csv in source folder.\n')
    else:
        print('sourceChatLog.json is empty.')
    
    f.close()

commentsCsv.close()
