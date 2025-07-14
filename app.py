from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

app = Flask(__name__)
CORS(app)

def extract_images_from_soup(soup, base_url):
    images = set()
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src') or img.get('data-original') or img.get('data-lazy-src')
        if src:
            images.add(urljoin(base_url, src))
    for source in soup.find_all('source'):
        srcset = source.get('srcset')
        if srcset:
            images.add(urljoin(base_url, srcset.split(',')[0].split()[0]))
    for tag in soup.find_all(style=True):
        style = tag['style']
        if 'background-image' in style:
            start = style.find('url(')
            end = style.find(')', start)
            if start != -1 and end != -1:
                bg_url = style[start+4:end].strip('\"\'')
                images.add(urljoin(base_url, bg_url))
    for meta in soup.find_all('meta', property='og:image'):
        if meta.get('content'):
            images.add(urljoin(base_url, meta['content']))
    return list(images)

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        images = extract_images_from_soup(soup, url)
        return jsonify({'images': images})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
