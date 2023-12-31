import streamlit as st
from openai import OpenAI
import urllib
import re
import datetime
import sqlite3
import pandas as pd

# OpenAIのAPIキーを入力
api_key = st.text_input('OpenAIのAPIキーを入力してください', type='password')
client = OpenAI(api_key=api_key)

# 音声ファイルを文字起こしする関数
def transcribe(audio_file, prompt: str) -> str:
    transcript = client.audio.transcriptions.create(
        file=audio_file,
        model="whisper-1",
        prompt=prompt,
    )
    return transcript.text

# 句読点で改行する関数
def split_text_by_punctuation(text: str) -> str:
    return re.sub(r'([。])', r'\1\n', text)

# OpenAIのChatGPTを使用してテキストを要約する関数
def summarize_text_with_chatgpt(text: str) -> str:
    chat_model = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[
            {"role": "system", "content": "You use only Japanese. So, you must response by Japanese."},
            {"role": "user", "content": f"Please summarize the following content: {text}"},
            {"role": "user", "content": "Defenitely total words is 1000 words."},
            {"role": "user", "content": "Please insert a summarized title at the beginning."},
        ],
    )
    return chat_model.choices[0].message.content


def fetch_transcriptions():
    c.execute("SELECT * FROM transcriptions")
    rows = c.fetchall()
    return pd.DataFrame(rows, columns=['id', 'transcript', 'summary'])

def save_to_db(transcript: str, summary: str):
    c.execute("INSERT INTO transcriptions (transcript, summary) VALUES (?, ?)", (transcript, summary))
    conn.commit()


# StreamlitのUIを定義
st.title('音声ファイルの文字起こしと要約')
uploaded_file = st.file_uploader("音声ファイルをアップロードしてください", type=['m4a'])

if uploaded_file is not None:
    conn = sqlite3.connect('transcriptions.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS transcriptions
        (id INTEGER PRIMARY KEY, transcript TEXT, summary TEXT)
    ''')
    conn.commit()
    # 音声ファイルを文字起こし
    prompt = "日本語の音声を文字起こししてください。"
    transcript = transcribe(uploaded_file, prompt)

    # 句読点で改行
    split_transcript = split_text_by_punctuation(transcript)

    # 要約
    summary = summarize_text_with_chatgpt(split_transcript)
    # データベースに保存
    save_to_db(transcript, summary)

    # 結果を表示
    st.write('文字起こし結果:')
    st.write(transcript)
    st.write('要約結果:')
    st.write(summary)

    # データベースから内容を取得
    df = fetch_transcriptions()

    # 結果を表示
    st.write('データベースの内容:')
    st.dataframe(df)