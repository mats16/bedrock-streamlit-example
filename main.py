import json
import os
import uuid
import boto3
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, JSONAttribute, MapAttribute, ListAttribute
import streamlit as st

AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')

# Bedrock Client
bedrock = boto3.client(service_name='bedrock-runtime', region_name=AWS_REGION)

class Message(MapAttribute):
    role = UnicodeAttribute()
    content = UnicodeAttribute()

class SesstionModel(Model):
    class Meta:
        table_name = 'ChatHostory'
        #host = 'http://localhost:8000'
        region = AWS_REGION
    sesstion_id = UnicodeAttribute(hash_key=True)
    messages = ListAttribute(of=Message)

#if not "AWS_EXECUTION_ENV" in os.environ:
#    ChatHistory.create_table(read_capacity_units=1, write_capacity_units=1)

if 'session_id' not in st.session_state:
    session_id = str(uuid.uuid4())
    st.session_state['session_id'] = session_id
    SesstionModel(session_id, messages=[]).save()

# チャットボットとやりとりする関数
def communicate():
    session_id = st.session_state['session_id']
    session = SesstionModel.get(session_id)

    user_message = Message(role='Human', content=st.session_state['user_input'])
    session.messages.append(user_message)

    prompt = '\n\n'.join([f"{msg['role']}: {msg['content']}" for msg in session.messages]) + '\n\nAssistant:'

    body = json.dumps({
        'prompt': prompt,
        'max_tokens_to_sample': 300,
        'temperature': 0.1,
        'top_p': 0.9,
    })

    response = bedrock.invoke_model(
        modelId='anthropic.claude-v2',
        accept='application/json',
        contentType='application/json',
        body=body,
    )
    response_body = json.loads(response.get('body').read())

    bot_message_content = response_body.get('completion')

    bot_message = Message(role='Assistant', content=bot_message_content)
    session.messages.append(bot_message)

    # DynamoDB に保存
    session.save()

    # 入力欄を消去
    st.session_state['user_input'] = ''


# ユーザーインターフェイスの構築
st.title('[Demo] Bedrock Chat')
st.write('Bedrock と Streamlit を利用したチャットアプリです。')
st.write('Session ID: ' + st.session_state['session_id'])

user_input = st.text_input('メッセージを入力してください。', key='user_input', on_change=communicate)

if 'session_id' in st.session_state:
    session_id = st.session_state['session_id']
    session = SesstionModel.get(session_id)
    for msg in reversed(session.messages):  # 直近のメッセージを上に
        speaker = "🙂"
        if msg['role'] == 'Assistant':
            speaker = "🤖"

        st.write(speaker + ': ' + msg['content'])
