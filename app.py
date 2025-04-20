from flask import Flask, render_template
import requests
import os

app = Flask(__name__)

TARGET_URL = 'https://cb8e-2406-b400-d1-5e81-7d60-ca0-9db7-27c8.ngrok-free.app'  # Replace this with your actual site

def check_website(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except:
        return False

@app.route('/')
def home():
    if check_website(TARGET_URL):
        return render_template('loading.html', site_url=TARGET_URL)
    else:
        return render_template('offline.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
