#   
# 2026年8月12日  app.py   URL
#
# テキスト・画像・音声・動画ファイルを統合したマルチモーダルなチャットボットU
# 
#   
#  auth=("joekajio90", "Soejima/2874")
#
import os
import sys
import datetime
import gradio as gr
from google import genai
from PIL import Image

# アプリのバージョンとデータベース状態
APP_VERSION = "v1.2.2"
DB_STATUS = "Connected (SQLite)"
START_TIME = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 環境変数からAPIキーを取得
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# 確実に利用可能なモデル名を指定
FAST_MODEL_NAME = "gemini-1.5-flash"

# タイトル下に表示するシステム情報ヘッダー
SYSTEM_INFO_HTML = f"""
<div style="background-color: #1e293b; color: #f8fafc; padding: 12px 16px; border-radius: 8px; font-size: 0.9em; margin-bottom: 15px; border: 1px solid #334155;">
    <div style="display: flex; flex-wrap: wrap; gap: 15px; align-items: center;">
        <span>🤖 <b>使用モデル:</b> <code style="background:#0f172a; padding:2px 6px; border-radius:4px; color:#38bdf8;">{FAST_MODEL_NAME}</code></span>
        <span>🏷️ <b>Version:</b> <code style="background:#0f172a; padding:2px 6px; border-radius:4px; color:#a7f3d0;">{APP_VERSION}</code></span>
        <span>🗄️ <b>DB Status:</b> <code style="background:#0f172a; padding:2px 6px; border-radius:4px; color:#fde047;">{DB_STATUS}</code></span>
        <span>⏰ <b>Server Start:</b> <code style="background:#0f172a; padding:2px 6px; border-radius:4px; color:#cbd5e1;">{START_TIME}</code></span>
    </div>
</div>
"""

def respond(message, history):
    if not client:
        return "APIキーが設定されていません。RenderのEnvironment VariablesでGEMINI_API_KEYを設定してください。"

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text_input = message.get("text", "")
    files = message.get("files", [])
    contents = []

    if files:
        for file_path in files:
            try:
                # 画像の読み込み試行
                img = Image.open(file_path)
                contents.append(img)
            except Exception:
                # 画像以外（音声など）の場合はバイナリデータとして追加
                try:
                    with open(file_path, "rb") as f:
                        contents.append({"mime_type": "audio/mp3", "data": f.read()})
                except Exception as e:
                    return f"ファイル読み込みエラー: {str(e)}"

    prompt_instruction = "思考プロセスは一切出力せず、結論と解説をきれいな日本語で分かりやすく出力してください。"
    
    if text_input:
        contents.append(f"{text_input}\n\n※指示: {prompt_instruction}")
    elif files and not text_input:
        contents.append(f"この入力内容（画像/音声）について説明してください。\n\n※指示: {prompt_instruction}")

    if not contents:
        return "メッセージ、画像、または音声を入力してください。"

    # フォールバック用のモデルリスト
    model_candidates = ["gemini-1.5-flash", "gemini-1.5-pro"]
    
    for model_id in model_candidates:
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=contents
            )
            return f"⏱️ [{now_str}]\n\n{response.text}"
        except Exception as e:
            last_error = str(e)
            continue

    return f"APIエラー: {last_error}"

with gr.Blocks(title="Gemini AI チャットボット") as demo:
    gr.Markdown("# 🎙️🖼️ Gemini AI チャットボット (ap005w - 爆速仕様)")
    gr.HTML(SYSTEM_INFO_HTML)
    
    gr.ChatInterface(
        fn=respond,
        multimodal=True,
        description="画像、音声、テキストを送信すると、Gemini AIが数秒でスマートに回答します。"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(
        server_name="0.0.0.0", 
        server_port=port,
        auth=("joekajio90", "Soejima/2874")
    )