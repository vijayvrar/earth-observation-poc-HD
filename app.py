from flask import Flask, render_template, request
from eo import get_stitched_satellite_image

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    data = None
    if request.method == 'POST':
        try:
            lat = float(request.form.get('latitude'))
            lon = float(request.form.get('longitude'))
            
            # Fetch stitched satellite imagery from eo.py
            base64_image = get_stitched_satellite_image(lat, lon)
            
            # Package payload for index.html
            data = {
                'latitude': lat,
                'longitude': lon,
                'image': base64_image
            }
        except (ValueError, TypeError) as e:
            print(f"Invalid input submission: {e}")
            
    return render_template('index.html', data=data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
