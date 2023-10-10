import json
import os
import uuid
import boto3
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, JSONAttribute, MapAttribute, ListAttribute
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from langchain.chat_models.bedrock import BedrockChat
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories.dynamodb import DynamoDBChatMessageHistory
from langchain.chains import LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
# for DynamoDB Local
ddb_endpoint_url = 'http://dynamodb-local:8000' if not "AWS_EXECUTION_ENV" in os.environ else None
access_key_id = 'DUMMY' if not "AWS_EXECUTION_ENV" in os.environ else None
secret_access_key = 'DUMMY' if not "AWS_EXECUTION_ENV" in os.environ else None

# Bedrock Client
bedrock = boto3.client(service_name='bedrock-runtime', region_name=AWS_REGION)

class Data(MapAttribute):
    type = UnicodeAttribute()
    content = UnicodeAttribute()

class Message(MapAttribute):
    type = UnicodeAttribute()
    data = Data()

class Session(Model):
    class Meta:
        table_name = 'ChatSession'
        region = AWS_REGION
        # for DynamoDB Local
        host = ddb_endpoint_url
        aws_access_key_id = access_key_id
        aws_secret_access_key = secret_access_key
    SessionId = UnicodeAttribute(hash_key=True)
    History = ListAttribute(of=Message)

if not "AWS_EXECUTION_ENV" in os.environ:
    Session.create_table(read_capacity_units=1, write_capacity_units=1)

# Session ID を取得
ctx = get_script_run_ctx()
session_id = ctx.session_id

# DynamoDB からセッション情報を取得
try:
    session = Session.get(session_id)
except:
    session = Session(session_id, History=[])

# チャットボットとやりとりする関数
def communicate():
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template('You are a friendly AI assistant.'),
        MessagesPlaceholder(variable_name='chat_history'),
        HumanMessagePromptTemplate.from_template('{input}')
    ])

    llm = BedrockChat(
        model_id='anthropic.claude-v2',
        model_kwargs={
            'temperature':0.1,
        }
    )

    # DynamoDB を記憶領域として使う
    chat_memory = DynamoDBChatMessageHistory(table_name='ChatSession', session_id=session_id, endpoint_url=ddb_endpoint_url)
    memory = ConversationBufferMemory(chat_memory=chat_memory, memory_key='chat_history', return_messages=True)

    chain = LLMChain(llm=llm, memory=memory, prompt=prompt)

    # Bedrock API を呼び出し
    reploy_text = chain.run(st.session_state['user_input'])

    # 入力欄を消去
    st.session_state['user_input'] = ''


# ユーザーインターフェイスの構築
st.title('[Demo] Bedrock Chat')
st.write('Bedrock と Streamlit を利用したチャットアプリです。')

user_input = st.text_input('メッセージを入力してください。', key='user_input', on_change=communicate)

# チャットメッセージを表示
for msg in reversed(session.History):  # 直近のメッセージを上に
    speaker = "🙂"
    if msg['type'] == 'ai':
        speaker = "🤖"

    st.write(speaker + ': ' + msg['data']['content'])
