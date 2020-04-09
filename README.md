# Telegram-AI-chatbot-for-university-courses

**Developer Guide: [PublicDevGuide.pdf](https://github.com/darren-ccab/Telegram-AI-chatbot-for-university-courses/blob/master/PublicDevGuide.pdf)**

## Prerequisites

Python 3

Google Cloud Account Creation: https://console.cloud.google.com/freetrial

Dialogflow Account Creation: https://dialogflow.cloud.google.com/

## Basic Concepts of Dialogflow

1.	https://cloud.google.com/dialogflow/docs/basics

## Setting Up of Dialogflow Project

Adapted from: https://cloud.google.com/dialogflow/docs/quick/setup


1. Create a Cloud Platform Project: https://console.cloud.google.com/project

2. Enable billing for your project: https://support.google.com/cloud/answer/6293499#enable-billing

3. Enable the Google Cloud Dialogflow API: https://console.cloud.google.com/flows/enableapi?apiid=dialogflow.googleapis.com

4. Set up authentication with a service account so you can access the API from your local workstation: https://cloud.google.com/docs/authentication/getting-started

5. Ensure that the service account is set to Dialogflow Integrations and that the service account key is downloaded in json format, this file will be called the Dialogflow json agent file.


Creation of Agent
----------------

https://cloud.google.com/dialogflow/docs/quick/build-agent



Enable API for project and add credentials for read write access for project
----------------
Credential details can be found from dialogflow agent settings. This details are required for google api to grant roles to service accounts.

1.	Obtain credentials from settings of Dialogflow agent

2.	Enabling of API:
https://console.cloud.google.com/flows/enableapi?apiid=dialogflow.googleapis.com

3.	Granting Roles to Service Accounts: 
https://cloud.google.com/iam/docs/granting-roles-to-service-accounts
4.	Granting Access Control for Dialogflow Agents:
https://cloud.google.com/dialogflow/docs/access-control#gcpconsole

5.	Ensure that editor role is given to Dialogflow agent and account

<br />

Installation
---------------

`pip install requirements.txt`



Running of program
----------------

1.	Ensure that Dialogflow json agent file is in same project folder as chatbot program

2.	This is a must do before running any of the chatbots:

      `set GOOGLE_APPLICATION_CREDENTIALS=NewAgent-e6b62ce69677.json`

      where the variable should be changed according to the name of the Dialogflow json agent file.

3.	To run general chatbot program: `python sourcechat.py`

4.	To run staff chatbot program: `python adminchat.py`


<br />

Other features
--------------

1. Batch Upload of question answer pair: uploadIntent.py

      Edit csv filename in script

      Execution steps:

        1. set GOOGLE_APPLICATION_CREDENTIALS=NewAgent-e6b62ce69677.json

        2. `python uploadIntent.py`

<br />

2. Generate Comments: generateResults.py

      `python generateResults.py`
