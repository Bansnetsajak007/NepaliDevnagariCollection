import os
import base64
import uuid
import shutil
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image

app = Flask(__name__)

# --- STORAGE CONFIG ---
IS_CLOUD = 'RENDER' in os.environ

if IS_CLOUD:
    BASE_DIR = 'nepali_dataset_cloud'
    print(f"[*] CLOUD MODE → {BASE_DIR}")
else:
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    BASE_DIR = os.path.join(desktop_path, "nepali_devnagaridataset")
    print(f"[*] LOCAL MODE → {BASE_DIR}")

TARGET_SIZE = (32, 32)

os.makedirs(BASE_DIR, exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/save_image', methods=['POST'])
def save_image():
    try:
        data = request.json
        image_data = data['image']
        label = data['label']

        label_path = os.path.join(BASE_DIR, label)
        os.makedirs(label_path, exist_ok=True)

        # Decode base64
        header, encoded = image_data.split(",", 1)
        img_bytes = base64.b64decode(encoded)
        image = Image.open(BytesIO(img_bytes))

        # -------------------------------
        # 🔥 CRITICAL FIX STARTS HERE
        # -------------------------------

        # If transparent → paste on BLACK background (not white)
        if image.mode in ('RGBA', 'LA'):
            black_bg = Image.new("RGB", image.size, (0, 0, 0))
            black_bg.paste(image, mask=image.split()[-1])
            image = black_bg

        # Convert to grayscale
        image = image.convert('L')

        # Resize to model input
        image = image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)

        # -------------------------------
        # 🔥 CRITICAL FIX ENDS HERE
        # -------------------------------

        filename = f"{uuid.uuid4().hex}.png"
        save_path = os.path.join(label_path, filename)
        image.save(save_path)

        return jsonify({"status": "success", "label": label})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/download_data')
def download_data():
    archive_name = "nepali_dataset_backup"
    shutil.make_archive(archive_name, 'zip', BASE_DIR)
    return send_file(f"{archive_name}.zip", as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
