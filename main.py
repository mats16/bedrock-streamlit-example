import json
import os
import boto3
import streamlit as st

AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')

# Bedrock Client
bedrock = boto3.client(service_name='bedrock-runtime', region_name=AWS_REGION)

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": ""}
    ]


# チャットボットとやりとりする関数
def communicate():
    messages = st.session_state["messages"]

    user_message = {"role": "user", "content": st.session_state["user_input"]}
    messages.append(user_message)

    prompt = "Human:" + "\n\n".join(f"{message['role']}: {message['content']}" for message in messages[1:]) + "\n\nAssistant:"

    body = json.dumps({
        "prompt": prompt,
        "max_tokens_to_sample": 300,
        "temperature": 0.1,
        "top_p": 0.9,
    })

    modelId = 'anthropic.claude-v2'
    accept = 'application/json'
    contentType = 'application/json'

    response = bedrock.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
    response_body = json.loads(response.get('body').read())

    bot_message_content = response_body.get('completion')
    bot_message = {"role": "assistant", "content": bot_message_content}
    messages.append(bot_message)

    st.session_state["user_input"] = ""  # 入力欄を消去


# ユーザーインターフェイスの構築
st.title("Bedrock Chatbot")
st.write("Bedrock and Claudeモデルを使ったチャットボットです。")

user_input = st.text_input("メッセージを入力してください。", key="user_input", on_change=communicate)

if st.session_state["messages"]:
    messages = st.session_state["messages"]

    for message in reversed(messages[1:]):  # 直近のメッセージを上に
        speaker = "🙂"
        if message["role"] == "assistant":
            speaker = "🤖"

        st.write(speaker + ": " + message["content"])
