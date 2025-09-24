from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import os
from werkzeug.utils import secure_filename
from cv_parser import CVParser, ReadmeGenerator

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # For flash messages
UPLOAD_FOLDER = "uploads/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        cv_file = request.files["cv_pdf"]
        
        if not cv_file or cv_file.filename == '':
            flash("Por favor selecciona un archivo PDF", "error")
            return redirect(url_for('index'))
        
        filename = secure_filename(cv_file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        cv_file.save(file_path)

        # Initialize parsers
        cv_parser = CVParser()
        readme_generator = ReadmeGenerator()
        
        try:
            # Extract GitHub information from CV
            github_info = cv_parser.extract_github_info(file_path)
            
            if not github_info['text_extracted']:
                flash("No se pudo extraer texto del PDF. Por favor verifica que el archivo no esté dañado.", "error")
                return redirect(url_for('index'))
            
            if not github_info['username']:
                flash("No se encontró un nombre de usuario de GitHub en el CV. Usando el template por defecto.", "warning")
                # Use default template without changes
                from shutil import copyfile
                copyfile("example_README.md", "generated_README.md")
            elif not github_info['verified']:
                flash(f"Se encontró el usuario '{github_info['username']}' pero no se pudo verificar que exista en GitHub. Usando el template por defecto.", "warning")
                # Use default template without changes  
                from shutil import copyfile
                copyfile("example_README.md", "generated_README.md")
            else:
                # Successfully found and verified GitHub username
                flash(f"¡Éxito! Se encontró y verificó el usuario de GitHub: {github_info['username']}", "success")
                # Generate personalized README
                success = readme_generator.generate_readme(github_info['username'])
                if not success:
                    flash("Error al generar el README personalizado. Usando el template por defecto.", "error")
                    from shutil import copyfile
                    copyfile("example_README.md", "generated_README.md")
            
            # Clean up uploaded file
            os.remove(file_path)
            
            return send_file("generated_README.md", as_attachment=True)
            
        except Exception as e:
            flash(f"Error procesando el archivo: {str(e)}", "error")
            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
            return redirect(url_for('index'))
    
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)