#   
# 2026年8月12日  app.py   URL
#
# テキスト・画像・音声・動画ファイルを統合したマルチモーダルなチャットボットU
# 
#   
#  
import sys
import os
import gradio as gr
import google.generativeai as genai
from PIL import Image

# 環境変数からAPIキーを取得
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
genai.configure(api_key=GEMINI_API_KEY)

def find_fast_gemini_model():
    candidates = [
        'gemini-2.0-flash',
        'gemini-2.5-flash',
        'gemini-1.5-flash',
        'models/gemini-2.0-flash'
    ]
    for model_name in candidates:
        try:
            m = genai.GenerativeModel(model_name)
            m.generate_content("test")
            return model_name
        except Exception:
            continue
    return 'gemini-2.0-flash'

FAST_MODEL_NAME = find_fast_gemini_model()

def respond(message, history):
    text_input = message.get("text", "")
    files = message.get("files", [])
    contents = []

    if files:
        for file_path in files:
            try:
                img = Image.open(file_path)
                contents.append(img)
            except Exception as e:
                return f"画像読み込みエラー: {str(e)}"

    prompt_instruction = "思考プロセスは一切出力せず、プレゼン向けに結論と解説をきれいな日本語で分かりやすく出力してください。"
    
    if text_input:
        contents.append(f"{text_input}\n\n※指示: {prompt_instruction}")
    elif files and not text_input:
        contents.append(f"この画像について詳しく説明してください。\n\n※指示: {prompt_instruction}")

    if not contents:
        return "メッセージを入力するか、画像を送信してください。"

    try:
        model = genai.GenerativeModel(FAST_MODEL_NAME)
        response = model.generate_content(contents)
        return response.text
    except Exception as e:
        return f"APIエラー: {str(e)}"

demo = gr.ChatInterface(
    fn=respond,
    multimodal=True,
    title="🎙️🖼️ Gemini AI チャットボット (ap005w - 爆速仕様)",
    description="画像や音声を送信すると、Gemini AIが数秒でスマートに回答します。"
)

if __name__ == "__main__":
    # Renderで動作させるために 0.0.0.0 と ポート指定を行う
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)