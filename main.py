import json
import os
import boto3
# PynamoDB
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, MapAttribute, ListAttribute
# Streamlit
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

region: str = os.environ.get('AWS_REGION', 'us-east-1')
table_name: str = os.environ.get('TABLE_NAME', 'ChatSession')
is_local: bool = True if os.environ.get('AWS_EXECUTION_ENV', '') == '' else False

# Bedrock Client
bedrock = boto3.client(service_name='bedrock-runtime', region_name=region)

class Message(MapAttribute):
    role = UnicodeAttribute()
    content = UnicodeAttribute()

class Session(Model):
    """DynamoDB Table に保存されるセッション情報"""
    class Meta:
        table_name = table_name
        region = region
        # for DynamoDB Local
        host = 'http://dynamodb-local:8000' if is_local else None
        aws_access_key_id = 'DUMMY' if is_local else None
        aws_secret_access_key = 'DUMMY' if is_local else None
    SessionId = UnicodeAttribute(hash_key=True)
    Messages = ListAttribute(of=Message)

if is_local:
    Session.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)

# Session ID を取得
ctx = get_script_run_ctx()
session_id = ctx.session_id

try:
    # DynamoDB Table からセッション情報を取得
    session = Session.get(session_id)
except:
    # ない場合は新規に作成（DynamoDB Table へはまだ書き込みに行かない）
    system_message = Message(role='Human', content='<admin>You are a friendly AI assistant.</admin>')
    session = Session(session_id, Messages=[system_message])

# チャットボットとやりとりする関数
def communicate():
    # ユーザの入力内容をセッション情報に追加
    user_message = Message(role='Human', content=st.session_state['user_input'])
    session.Messages.append(user_message)

    # prompt 向けに整形
    prompt = '\n\n'.join([f"{msg['role']}: {msg['content']}" for msg in session.Messages]) + '\n\nAssistant:'

    # Bedrock API のリクエストボディを定義
    # https://us-west-2.console.aws.amazon.com/bedrock/home?region=us-west-2#/providers?model=claude-v2
    body = json.dumps({
        'prompt': prompt,
        'max_tokens_to_sample': 8000,
        'temperature': 0.1,
        'top_p': 0.9,
        'stop_sequences': ['\\n\\nHuman:'],
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

    # セッション情報にボットメッセージを追加
    bot_message = Message(role='Assistant', content=bot_message_content)
    session.Messages.append(bot_message)

    # DynamoDB Table に保存
    session.save()

    # 入力欄を消去
    st.session_state['user_input'] = ''


# ユーザーインターフェイスの構築
st.title('[Demo] Bedrock Chat')
st.write('Bedrock と Streamlit を利用したチャットアプリです。')

# チャットの入力フォーム
user_input = st.text_input('メッセージを入力してください。', key='user_input', on_change=communicate)

# チャットメッセージを表示
for msg in reversed(session.Messages):
    speaker = "🙂"
    if msg['role'] == 'Assistant':
        speaker = "🤖"

    st.write(speaker + ': ' + msg['content'])
