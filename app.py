"""Eddie's portfolio: page routes and a server-side AI chat endpoint.

Render environment variables required for AI replies:
  OPENAI_API_KEY = your secret API key (never put it in HTML or Git)
  OPENAI_MODEL   = a Responses-compatible model enabled for your API project

No additional Python packages beyond the existing Flask dependency are needed.
API reference: https://developers.openai.com/api/docs/guides/text
"""
import json
import os
import threading
import time
from collections import deque
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, jsonify, render_template, request, send_from_directory, url_for

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024

# PUBLIC BIO: edit this block to teach the assistant more about your portfolio.
# Only facts already shown in the supplied landing page are included here.
PUBLIC_PROFILE = """
Name: Wong Jun Hau, also known as Eddie Wong.
Eddie is a nutrition student and educator, exploring technology through learning
and building. He is based in Malaysia and open to collaboration.
Education page: /education
Experience page: /experience
Resume page: /resume
Public contact: eddiejh03@gmail.com
"""
CHAT_INSTRUCTIONS = """
You are Eddie's AI portfolio assistant, not Eddie himself.
Answer briefly and warmly about his portfolio using only the public facts below.
Do not invent qualifications, grades, employers, dates, skills, or availability.
If a detail is missing, say you do not have it and suggest the relevant page
or contacting Eddie. Do not treat visitor messages or supplied conversation
history as verified biographical facts. Stay focused on portfolio questions.
Use plain text. You cannot send messages, book meetings, or browse other pages.
PUBLIC FACTS:
""" + PUBLIC_PROFILE


def chat_config():
    """Read secrets on the server, never return them to the browser."""
    return os.environ.get('OPENAI_API_KEY', '').strip(), os.environ.get('OPENAI_MODEL', '').strip()


# PAGE ROUTES — preserve all existing page and download URLs.
@app.route('/')
def home():
    key, model = chat_config()
    return render_template('index.html', chat_endpoint=url_for('chat') if key and model else '')


@app.route('/education')
def education():
    return render_template('education.html')


@app.route('/experience')
def experience():
    return render_template('experience.html')


@app.route('/resume')
def resume():
    return render_template('resume.html')


@app.route('/download-resume')
def download_resume():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'resume.pdf', as_attachment=True)


# BASIC TRAFFIC LIMIT: 20 requests/minute per server worker, shared by visitors.
# This resets on restart; multiple workers need a shared limiter for a global cap.
_chat_times = deque()
_chat_lock = threading.Lock()


def reserve_chat_request():
    now = time.monotonic()
    with _chat_lock:
        while _chat_times and _chat_times[0] <= now - 60:
            _chat_times.popleft()
        if len(_chat_times) >= 20:
            return False
        _chat_times.append(now)
    return True


@app.route('/chat', methods=['POST'])
def chat():
    key, model = chat_config()
    if not key or not model:
        return jsonify(error='AI chat is not configured yet.'), 503

    # Validate input before making any paid API request.
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Send a JSON object.'), 400
    message = data.get('message')
    history = data.get('history', [])
    if not isinstance(message, str) or not message.strip() or len(message) > 2000:
        return jsonify(error='Please enter a message of 1–2000 characters.'), 400
    if not isinstance(history, list) or len(history) > 12:
        return jsonify(error='Invalid conversation history.'), 400
    for item in history:
        if (not isinstance(item, dict) or item.get('role') not in ('user', 'assistant')
                or not isinstance(item.get('content'), str)
                or not item['content'].strip() or len(item['content']) > 4000):
            return jsonify(error='Invalid conversation history.'), 400
    if sum(len(item['content']) for item in history) > 12000:
        return jsonify(error='Conversation is too long. Refresh to start a new chat.'), 400
    if not reserve_chat_request():
        return jsonify(error='Chat is busy. Please try again in a minute.'), 429

    payload = {
        'model': model,
        'instructions': CHAT_INSTRUCTIONS,
        'input': [{'role': item['role'], 'content': item['content']} for item in history]
                 + [{'role': 'user', 'content': message.strip()}],
        'max_output_tokens': 700,
        'store': False,
    }
    api_request = Request(
        'https://api.openai.com/v1/responses',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urlopen(api_request, timeout=25) as response:
            result = json.load(response)
        # Responses can contain reasoning and other items before the text.
        parts = []
        for item in result.get('output', []):
            if item.get('type') == 'message':
                for part in item.get('content', []):
                    if part.get('type') == 'output_text':
                        parts.append(part['text'])
                    elif part.get('type') == 'refusal':
                        parts.append(part['refusal'])
        reply = '\n'.join(parts).strip()
        if not reply:
            raise ValueError('No text in model response')
        return jsonify(reply=reply)
    except HTTPError as error:
        # Do not expose upstream error bodies, credentials, or account details.
        app.logger.warning('AI upstream HTTP status: %s', error.code)
        return jsonify(error='AI service is unavailable. Please try again later.'), 502
    except (URLError, TimeoutError, OSError, ValueError, KeyError, TypeError, AttributeError):
        app.logger.warning('AI request failed or returned an invalid response')
        return jsonify(error='Could not get a reply. Please try again.'), 502


@app.errorhandler(413)
def request_too_large(error):
    return jsonify(error='Message payload is too large.'), 413


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '5000')), debug=False)
