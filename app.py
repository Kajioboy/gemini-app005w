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
import time
import gradio as gr
from google import genai
from PIL import Image

# アプリのバージョンとデータベース状態
APP_VERSION = "v1.3.0"
DB_STATUS = "Connected (SQLite)"
START_TIME = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 環境変数からAPIキーを取得
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# 最新の google-genai クライアント初期化
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def get_header_html(response_time_str="-- 秒"):
    return f"""
<div style="background-color: #1e293b; color: #f8fafc; padding: 12px 16px; border-radius: 8px; font-size: 0.9em; margin-bottom: 15px; border: 1px solid #334155;">
    <div style="display: flex; flex-wrap: wrap; gap: 15px; align-items: center;">
        <span>🤖 <b>使用モデル:</b> <code style="background:#0f172a; padding:2px 6px; border-radius:4px; color:#38bdf8;">Auto-Select (有効モデル自動検出)</code></span>
        <span>🏷️ <b>Version:</b> <code style="background:#0f172a; padding:2px 6px; border-radius:4px; color:#a7f3d0;">{APP_VERSION}</code></span>
        <span>🗄️ <b>DB Status:</b> <code style="background:#0f172a; padding:2px 6px; border-radius:4px; color:#fde047;">{DB_STATUS}</code></span>
        <span>⏰ <b>Server Start:</b> <code style="background:#0f172a; padding:2px 6px; border-radius:4px; color:#cbd5e1;">{START_TIME}</code></span>
        <span>⚡ <b>Response Time:</b> <code style="background:#0f172a; padding:2px 6px; border-radius:4px; color:#f43f5e; font-weight:bold;">{response_time_str}</code></span>
    </div>
</div>
"""

def respond(message, history):
    start_time = time.time()
    
    if not client:
        elapsed = round(time.time() - start_time, 2)
        return "❌ APIキーが設定されていません。\nRenderの Environment Variables で GEMINI_API_KEY を設定してください。", get_header_html(f"{elapsed} 秒")

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text_input = message.get("text", "")
    files = message.get("files", [])
    contents = []

    if files:
        for file_path in files:
            try:
                img = Image.open(file_path)
                contents.append(img)
            except Exception:
                try:
                    with open(file_path, "rb") as f:
                        contents.append({"mime_type": "audio/mp3", "data": f.read()})
                except Exception as e:
                    elapsed = round(time.time() - start_time, 2)
                    return f"ファイル読み込みエラー: {str(e)}", get_header_html(f"{elapsed} 秒")

    prompt_instruction = "思考プロセスは一切出力せず、結論と解説をきれいな日本語で分かりやすく出力してください。"
    
    if text_input:
        contents.append(f"{text_input}\n\n※指示: {prompt_instruction}")
    elif files and not text_input:
        contents.append(f"この入力内容（画像/音声）について説明してください。\n\n※指示: {prompt_instruction}")

    if not contents:
        elapsed = round(time.time() - start_time, 2)
        return "メッセージ、画像、または音声を入力してください。", get_header_html(f"{elapsed} 秒")

    # 利用可能なモデル一覧の自動取得
    candidate_models = []
    try:
        all_models = list(client.models.list())
        for m in all_models:
            m_id = m.name.replace("models/", "") if hasattr(m, "name") else str(m)
            candidate_models.append(m_id)
    except Exception:
        pass

    if not candidate_models:
        candidate_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]

    errors = []
    for model_id in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=contents
            )
            if response and response.text:
                elapsed = round(time.time() - start_time, 2)
                res_text = f"⏱️ [{now_str}] (Model: {model_id})\n\n{response.text}"
                return res_text, get_header_html(f"{elapsed} 秒")
        except Exception as e:
            errors.append(f"[{model_id}]: {str(e)}")
            continue

    elapsed = round(time.time() - start_time, 2)
    err_msg = f"⚠️ 応答の取得に失敗しました。\n\n【試行結果】\n" + "\n".join(errors[:3])
    return err_msg, get_header_html(f"{elapsed} 秒")

with gr.Blocks(title="Gemini AI チャットボット") as demo:
    gr.Markdown("# 🎙️🖼️ Gemini AI チャットボット (ap005w - 爆速仕様)")
    
    # ヘッダーHTMLコンポーネント
    header_box = gr.HTML(get_header_html())
    
    chatbot = gr.Chatbot(label="Chatbot")
    msg_input = gr.MultimodalTextbox(placeholder="画像、音声、テキストを入力...", show_label=False)

    def user_submit(message, history):
        history = history or []
        # テキストまたはファイルを表示用フォーマットに追加
        text = message.get("text", "")
        files = message.get("files", [])
        
        display_content = []
        for f in files:
            display_content.append((f,))
        if text:
            display_content.append(text)
            
        return "", history + [[message, None]]

    def bot_respond(history):
        if not history:
            return history, get_header_html()
        
        user_message = history[-1][0]
        bot_text, updated_header = respond(user_message, history[:-1])
        history[-1][1] = bot_text
        return history, updated_header

    # 送信イベントのハンドリング
    msg_input.submit(
        fn=user_submit,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot],
        queue=False
    ).then(
        fn=bot_respond,
        inputs=[chatbot],
        outputs=[chatbot, header_box]
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(
        server_name="0.0.0.0", 
        server_port=port,
        auth=("joekajio90", "Soejima/2874")
    )