"""
Generador de README para GitHub a partir de CV en PDF
====================================================

Esta aplicación Flask permite a los usuarios subir su CV en formato PDF
y generar automáticamente un archivo README.md personalizado para su 
perfil de GitHub con información extraída.
"""

from flask import Flask, render_template, request, send_file
import os
from werkzeug.utils import secure_filename
from readme_parser import extract_data_from_pdf, generate_readme

# Configuración de la aplicación Flask
app = Flask(__name__)
UPLOAD_FOLDER = "uploads/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Crear directorio de uploads si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Ruta principal de la aplicación.
    
    GET: Muestra la página de carga de archivos
    POST: Procesa el CV PDF subido y muestra preview para edición
    
    Returns:
        - GET: Template HTML con formulario de carga
        - POST: Template con preview de datos extraídos para edición
    """
    if request.method == "POST":
        cv_file = request.files["cv_pdf"]
        filename = secure_filename(cv_file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        
        cv_file.save(file_path)
        data = extract_data_from_pdf(file_path)
        
        return render_template("preview_new.html", data=data, filename=filename)
    
    # Mostrar formulario de carga
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    """
    Genera el README final con los datos editados por el usuario.
    
    Returns:
        Archivo README.md generado para descarga
    """

    data = {
        "first_name": request.form.get("first_name", "").strip(),
        "last_name": request.form.get("last_name", "").strip(),
        "github": request.form.get("github", "").strip(),
        "email": request.form.get("email", "").strip(),
        "linkedin": request.form.get("linkedin", "").strip(),
        "skills": [skill.strip() for skill in request.form.get("skills", "").split(",") if skill.strip()]
    }
    
    readme_content = generate_readme(data)
    
    with open("generated_README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
        
    return send_file("generated_README.md", as_attachment=True)

if __name__ == "__main__":
    """
    Ejecutar la aplicación Flask en modo desarrollo.
    """
    app.run(debug=True, host="127.0.0.1", port=5000)