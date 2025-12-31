# import os
# import base64
# import uuid
# from io import BytesIO
# from flask import Flask, render_template, request, jsonify
# from PIL import Image, ImageOps

# app = Flask(__name__)

# # --- CONFIGURATION ---
# DATASET_FOLDER = 'dataset'
# TARGET_SIZE = (32, 32)  # Final image size

# # Ensure dataset directory exists
# if not os.path.exists(DATASET_FOLDER):
#     os.makedirs(DATASET_FOLDER)

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/save_image', methods=['POST'])
# def save_image():
#     try:
#         data = request.json
#         image_data = data['image']
#         label = data['label']

#         # 1. Create folder for this character if it doesn't exist
#         label_path = os.path.join(DATASET_FOLDER, label)
#         if not os.path.exists(label_path):
#             os.makedirs(label_path)

#         # 2. Decode Base64 Image
#         # Remove the header "data:image/png;base64,"
#         header, encoded = image_data.split(",", 1)
#         img_bytes = base64.b64decode(encoded)
        
#         # 3. Process Image with PIL
#         image = Image.open(BytesIO(img_bytes))
        
# # FIX: Handle Transparency (Alpha Channel)
#         if image.mode in ('RGBA', 'LA'):
#             # Create a white background image
#             background = Image.new(image.mode[:-1], image.size, (255, 255, 255))
#             # Paste the drawing on top using the alpha channel as a mask
#             background.paste(image, image.split()[-1])
#             image = background
        
#         image = image.convert('L') 

#         # 4. Resize to 32x32 using High Quality downsampling
#         image = image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)

#         # 5. Save with unique filename
#         filename = f"{uuid.uuid4().hex}.png"
#         save_path = os.path.join(label_path, filename)
#         image.save(save_path)

#         return jsonify({"status": "success", "message": f"Saved to {label}"})

#     except Exception as e:
#         print(f"Error: {e}")
#         return jsonify({"status": "error", "message": str(e)}), 500

# if __name__ == '__main__':
#     # '0.0.0.0' allows you to access this from your phone on the same WiFi
#     app.run(debug=True, host='0.0.0.0', port=5000)



import os
import base64
import uuid
import shutil
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image

app = Flask(__name__)

# --- 1. SMART STORAGE CONFIGURATION ---
# Render sets the 'RENDER' environment variable automatically.
IS_CLOUD = 'RENDER' in os.environ

if IS_CLOUD:
    # CLOUD MODE: Save to a folder inside the server container
    BASE_DIR = 'nepali_dataset_cloud'
    print(f"[*] RUNNING ON CLOUD (Render). Data saving to: {BASE_DIR}")
else:
    # LOCAL MODE: Save directly to your Desktop
    # This finds the Desktop path for Windows, Mac, or Linux automatically
    DATASET_FOLDER = 'dataset'
    TARGET_SIZE = (32, 32)  # Final image size

    # Ensure dataset directory exists
    if not os.path.exists(DATASET_FOLDER):
        os.makedirs(DATASET_FOLDER)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save_image', methods=['POST'])
def save_image():
    try:
        data = request.json
        image_data = data['image']
        label = data['label']

        # 1. Create the specific character folder (e.g., .../nepali_devnagaridataset/क)
        label_path = os.path.join(DATASET_FOLDER, label)
        if not os.path.exists(label_path):
            os.makedirs(label_path)

        # 2. Decode Base64 Image
        header, encoded = image_data.split(",", 1)
        img_bytes = base64.b64decode(encoded)
        
        # 3. Process with PIL
        image = Image.open(BytesIO(img_bytes))

        # IMPORTANT: Handle Transparency
        # If the image has an alpha channel (transparent background),
        # paste it onto a white background.
        if image.mode in ('RGBA', 'LA'):
            background = Image.new(image.mode[:-1], image.size, (255, 255, 255))
            background.paste(image, image.split()[-1])
            image = background
        
        # Convert to Grayscale (L)
        image = image.convert('L')

        # Resize to 32x32 (Research Standard) using High Quality Downsampling
        image = image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)

        # 4. Save file
        filename = f"{uuid.uuid4().hex}.png"
        save_path = os.path.join(label_path, filename)
        image.save(save_path)

        return jsonify({"status": "success", "message": f"Saved to {label}"})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- 2. DOWNLOAD FEATURE (Crucial for Cloud) ---
@app.route('/download_data')
def download_data():
    """
    Zips the entire dataset folder and sends it to the browser.
    Useful for retrieving data from Render before the server restarts.
    """
    archive_name = "nepali_dataset_backup"
    
    # Create a zip file of the BASE_DIR
    shutil.make_archive(archive_name, 'zip', BASE_DIR)
    
    # Send the zip file to the user
    return send_file(f"{archive_name}.zip", as_attachment=True)

if __name__ == '__main__':
    # '0.0.0.0' allows local network access (e.g. from your phone)
    app.run(debug=True, host='0.0.0.0', port=5000)