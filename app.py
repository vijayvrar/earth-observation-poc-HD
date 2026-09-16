from eo import get_satellite_image
from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    lat = lon = None
    requested = False
    error_message = None

    if request.method == "POST":
        requested = True
        try:
            lat = float(request.form["lat"])
            lon = float(request.form["lon"])
            result = get_satellite_image(lat, lon)
        except Exception as e:
            error_message = str(e)

    return render_template(
        "index.html",
        image_data=result["image"] if result else None,
        observation=result["observation"] if result else None,
        lat=lat,
        lon=lon,
        requested=requested,
        error_message=error_message,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)