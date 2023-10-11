# Bedrock Streamlit Example

Bedrock を利用したアプリケーションのプロトタイピングを行うための最低限の実装です。

[devcontainer](.devcontainer/devcontainer.json) を利用することで DynamoDB Local をバックグラウンドで自動起動することができます。

## AWS Credentials

Bedrock API を利用するため、ローカル開発時も AWS の認証情報が必要です。

### IAM Identity Center (AWS SSO) を利用する場合

下記コマンドで IAM Identity Center から認証情報を取得してください。

```bash
aws configure sso --profile default
aws sso login  # 初回以降
```

### IAM User を利用する場合

下記コマンドで Access Key 等を設定してください。

```bash
aws configure --profile default
```

## Run dev server

サンプルコードは AWS SDK (boto3) を利用したものと、[Langchain](https://github.com/langchain-ai/langchain) を利用したものの２つを用意しています。

どちらもチャットの一時記憶領域に DynamoDB を使用しています。

```bash
streamlit run main.py # use AWS SDK

streamlit run chain.py # use Langchain
```
