# Bedrock Streamlit Example

Bedrock を利用したアプリケーションのプロトタイピングを行うための最低限の実装です。

[devcontainer](.devcontainer/devcontainer.json) を利用することで DynamoDB Local をバックグラウンドで自動起動することができます。

## Run dev server

サンプルコードは AWS SDK (boto3) を利用したものと、[Langchain](https://github.com/langchain-ai/langchain) を利用したものの２つを用意しています。

どちらもチャットの一時記憶領域に DynamoDB を使用しています。

```bash
streamlit run main.py # use AWS SDK

streamlit run chain.py # use Langchain
```
