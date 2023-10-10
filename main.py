import json
import os
import uuid
import boto3
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, JSONAttribute, MapAttribute, ListAttribute
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')

# Bedrock Client
bedrock = boto3.client(service_name='bedrock-runtime', region_name=AWS_REGION)

class Message(MapAttribute):
    role = UnicodeAttribute()
    content = UnicodeAttribute()

class Session(Model):
    class Meta:
        table_name = 'ChatSession'
        region = AWS_REGION
        # for DynamoDB Local
        host = 'http://dynamodb-local:8000' if not "AWS_EXECUTION_ENV" in os.environ else None
        aws_access_key_id = 'DUMMY' if not "AWS_EXECUTION_ENV" in os.environ else None
        aws_secret_access_key = 'DUMMY' if not "AWS_EXECUTION_ENV" in os.environ else None
    session_id = UnicodeAttribute(hash_key=True)
    messages = ListAttribute(of=Message)

if not "AWS_EXECUTION_ENV" in os.environ:
    Session.create_table(read_capacity_units=1, write_capacity_units=1)

# Session ID を取得
ctx = get_script_run_ctx()
session_id = ctx.session_id

# DynamoDB からセッション情報を取得
try:
    session = Session.get(session_id)
except:
    session = Session(session_id, messages=[])

# チャットボットとやりとりする関数
def communicate():
    # ユーザの入力内容を追加
    user_message = Message(role='Human', content=st.session_state['user_input'])
    session.messages.append(user_message)

    # prompt 向けに整形
    prompt = '\n\n'.join([f"{msg['role']}: {msg['content']}" for msg in session.messages]) + '\n\nAssistant:'

    # Bedrock API のリクエストボディ
    body = json.dumps({
        'prompt': prompt,
        'max_tokens_to_sample': 300,
        'temperature': 0.1,
        'top_p': 0.9,
    })

    # Bedrock API を呼び出し
    response = bedrock.invoke_model(
        modelId='anthropic.claude-v2',
        accept='application/json',
        contentType='application/json',
        body=body,
    )

    # レスポンスからメッセージを取得
    response_body = json.loads(response.get('body').read())
    bot_message_content = response_body.get('completion')

    # セッションデータにボットメッセージを追加
    bot_message = Message(role='Assistant', content=bot_message_content)
    session.messages.append(bot_message)

    # DynamoDB に保存
    session.save()

    # 入力欄を消去
    st.session_state['user_input'] = ''


# ユーザーインターフェイスの構築
st.title('[Demo] Bedrock Chat')
st.write('Bedrock と Streamlit を利用したチャットアプリです。')

user_input = st.text_input('メッセージを入力してください。', key='user_input', on_change=communicate)

# チャットメッセージを表示
for msg in reversed(session.messages):  # 直近のメッセージを上に
    speaker = "🙂"
    if msg['role'] == 'Assistant':
        speaker = "🤖"

    st.write(speaker + ': ' + msg['content'])
