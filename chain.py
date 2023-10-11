import os
import boto3
# PynamoDB
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, MapAttribute, ListAttribute
# Langchain
from langchain.chat_models import BedrockChat
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories.dynamodb import DynamoDBChatMessageHistory
from langchain.chains import LLMChain
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate
# Streamlit
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

region: str = os.environ.get('AWS_REGION', 'us-east-1')
table_name: str = os.environ.get('TABLE_NAME', 'ChatSession')
is_local: bool = True if os.environ.get('AWS_EXECUTION_ENV', '') == '' else False
endpoint_url: str | None = 'http://dynamodb-local:8000' if is_local else None

# Bedrock Client
bedrock = boto3.client(service_name='bedrock-runtime', region_name=region)


class Data(MapAttribute):
    type = UnicodeAttribute()
    content = UnicodeAttribute()


class Message(MapAttribute):
    type = UnicodeAttribute()
    data = Data()


class Session(Model):
    """Langchain のメモリー機能用 DynamoDB Table"""
    class Meta:
        table_name = table_name
        region = region
        # for DynamoDB Local
        host = endpoint_url
        aws_access_key_id = 'DUMMY' if is_local else None
        aws_secret_access_key = 'DUMMY' if is_local else None
    SessionId = UnicodeAttribute(hash_key=True)
    History = ListAttribute(of=Message)


if is_local:
    Session.create_table(read_capacity_units=1, write_capacity_units=1)

# Session ID を取得
ctx = get_script_run_ctx()
session_id = ctx.session_id

try:
    # DynamoDB Table からセッション情報を取得
    session = Session.get(session_id)
except:
    # ない場合は新規に作成（DynamoDB Table へはまだ書き込みに行かない）
    session = Session(session_id, History=[])


# チャットボットとやりとりする関数
def communicate():
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template('You are a friendly AI assistant.'),
        MessagesPlaceholder(variable_name='chat_history'),
        HumanMessagePromptTemplate.from_template('{input}')  # chain.run() 実行時の input が代入される
    ])

    # https://us-west-2.console.aws.amazon.com/bedrock/home?region=us-west-2#/providers?model=claude-v2
    llm = BedrockChat(
        model_id='anthropic.claude-v2',
        model_kwargs={
            'temperature': 0.1,
            'top_p': 0.9,
            'stop_sequences': ['\\n\\nHuman:'],
        }
    )

    # DynamoDB Table を記憶領域 (Memory) として使う
    chat_memory = DynamoDBChatMessageHistory(table_name=table_name, session_id=session_id, endpoint_url=endpoint_url)
    memory = ConversationBufferMemory(chat_memory=chat_memory, memory_key='chat_history', return_messages=True)

    chain = LLMChain(llm=llm, memory=memory, prompt=prompt)

    # Bedrock API を呼び出し
    reploy_text = chain.run(st.session_state['user_input'])

    # 入力欄を消去
    st.session_state['user_input'] = ''


# ユーザーインターフェイスの構築
st.title('[Demo] Bedrock Chat')
st.write('Bedrock と Streamlit および Langchain を利用したチャットアプリです。')

# チャットの入力フォーム
user_input = st.text_input('メッセージを入力してください。', key='user_input', on_change=communicate)

# チャットメッセージを表示
for msg in reversed(session.History):
    speaker = "🙂"
    if msg['type'] == 'ai':
        speaker = "🤖"

    st.write(speaker + ': ' + msg['data']['content'])
