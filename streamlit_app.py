import streamlit as st
import re
import os
import time
# import torch
# from transformers import AutoTokenizer, AutoModelForCausalLM
from googleapiclient.discovery import build

MODEL_PATH = "./final_model"
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# @st.cache_resource
# def load_model():
#     tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
#     model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)
#     model.to(device)
#     model.eval()
#     return tokenizer, model

# tokenizer, model = load_model()


def extract_video_id(url):
    match = re.search(r"(?:v=|youtu\.be/)([^&]+)", url)
    return match.group(1) if match else None


def get_video_info(video_id):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    request = youtube.videos().list(
        part="snippet,statistics",
        id=video_id
    )
    response = request.execute()

    if not response["items"]:
        return None

    item = response["items"][0]

    title = item["snippet"]["title"]
    tags = item["snippet"].get("tags", [])
    likes = int(item["statistics"].get("likeCount", 0))

    return title, tags, likes


def build_prompt(title, tone):
    prompt = f'''[VIDEO]
Title: {title}
[COMMENT]
Sentiment: {tone}
Text: '''
    return prompt


# def generate_comment_stream(prompt):
#     inputs = tokenizer(prompt, return_tensors="pt")
#     inputs = {k: v.to(device) for k, v in inputs.items()}
#     streamer = TextIteratorStreamer(
#         tokenizer,
#         skip_prompt=True,
#         skip_special_tokens=True
#     )
#     generation_kwargs = dict(
#         **inputs,
#         max_new_tokens=60,
#         temperature=0.8,
#         top_p=0.9,
#         do_sample=True,
#         repetition_penalty=1.2,
#         streamer=streamer,
#         pad_token_id=tokenizer.eos_token_id
#     )
#     thread = threading.Thread(target=model.generate, kwargs=generation_kwargs)
#     thread.start()
#     return streamer


# def generate_comment(prompt):
#     inputs = tokenizer(prompt, return_tensors="pt")
#     inputs = {k: v.to(device) for k, v in inputs.items()}
#     with torch.no_grad():
#         output = model.generate(
#             **inputs,
#             max_new_tokens=60,
#             temperature=0.8,
#             top_p=0.9,
#             do_sample=True,
#             repetition_penalty=1.2,
#             pad_token_id=tokenizer.eos_token_id
#         )
#     text = tokenizer.decode(output[0], skip_special_tokens=True)
#     # вытаскиваем только комментарий
#     comment = text.split("[COMMENT]")[-1].strip()
#     return comment


def fake_stream(text):
    for word in text.split():
        yield word + " "
        time.sleep(0.1)


def render_comment(text, tone):
    colors = {
        "POSITIVE": "#d4edda",  # светло-зелёный
        "NEGATIVE": "#f8d7da",  # светло-красный
        "NEUTRAL": "#e2e3e5"    # серый
    }

    border_colors = {
        "POSITIVE": "#28a745",
        "NEGATIVE": "#dc3545",
        "NEUTRAL": "#6c757d"
    }

    html = f"""
    <div style="
        background-color: {colors[tone]};
        border-left: 5px solid {border_colors[tone]};
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 10px;
    ">
        <strong>{tone}</strong><br><br>
        {text}
    </div>
    """
    return html


st.title("YouTube Comment Generator")
url = st.text_input("Введите ссылку на YouTube видео:")
if st.button("Сгенерировать комментарий"):
    if not url:
        st.warning("Введите ссылку")
    else:
        video_id = extract_video_id(url)

        if not video_id:
            st.error("Не удалось извлечь video_id")
        else:
            with st.spinner("Получаем данные видео..."):
                info = get_video_info(video_id)

            if info is None:
                st.error("Видео не найдено или недоступно")
            else:
                title, tags, likes = info
                st.subheader("Видео")
                st.write(f"**Title:** {title}")
                st.write(f"**Tags:** {', '.join(tags[:10])}")
                st.write(f"**Likes:** {likes}")
                st.subheader("Сгенерированные комментарии")

                tones = ["POSITIVE", "NEUTRAL", "NEGATIVE"]
                placeholders = {tone: st.empty() for tone in tones}
                for tone in tones:
                    with st.spinner(f"Генерируется {tone} комментарий..."):
                        prompt = build_prompt(title, tone)
                        full_text = ""
                        # streamer = generate_comment_stream(prompt)
                        streamer = fake_stream(prompt + "generated comment\n\n" + prompt)
                        for chunk in streamer:
                            full_text += chunk
                            if len(full_text) > len(prompt):
                                placeholders[tone].markdown(
                                    render_comment(full_text[len(prompt):], tone),
                                    unsafe_allow_html=True
                                )
