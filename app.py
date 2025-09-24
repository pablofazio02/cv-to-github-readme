from flask import Flask, render_template, request, send_file
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        cv_file = request.files["cv_pdf"]
        filename = secure_filename(cv_file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        cv_file.save(file_path)

        # Aquí deberías procesar el PDF y generar el README
        from shutil import copyfile
        copyfile("example_README.md", "generated_README.md")
        return send_file("generated_README.md", as_attachment=True)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)