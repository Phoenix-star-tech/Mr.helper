from flask import Flask, render_template
import requests

app = Flask(__name__)

TARGET_URL = 'https://www.youtube.com/'  # Replace this with your actual site

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
    app.run(debug=True)
