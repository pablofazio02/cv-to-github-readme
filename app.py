from flask import Flask, render_template, request, send_file
import os
from werkzeug.utils import secure_filename
import pdfplumber

app = Flask(__name__)
UPLOAD_FOLDER = "uploads/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def extract_data_from_pdf(pdf_path):
    
    data = {
        "name": "",
        "github": "", 
        "experience": [],
        "education": [],
        "skills": [],
        "email": "",
        "linkedin": ""
    }
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"

        # Ejemplo básico de extracción: mejora los patrones para tu CV
        import re

        # Buscar nombre
        name_match = re.search(r"Nombre[:\- ]*([A-Za-záéíóúüñÁÉÍÓÚÜÑ\s]+)", text, re.IGNORECASE)
        if name_match:
            data["name"] = name_match.group(1).strip()

        # Buscar usuario de GitHub o link
        github_match = re.search(r"github\.com/([A-Za-z0-9\-_áéíóúüñÁÉÍÓÚÜÑ]+)", text, re.IGNORECASE)
        if github_match:
            data["github"] = github_match.group(1).strip()

        # Buscar email
        email_match = re.search(r"[a-zA-Z0-9._%+-áéíóúüñÁÉÍÓÚÜÑ]+@(gmail|hotmail|outlook|yahoo)\.com", text, re.IGNORECASE)
        if email_match:
            data["email"] = email_match.group(0).strip()

        # Buscar LinkedIn 
        linkedin_match = re.search(r"linkedin\.com/in/([A-Za-z0-9\-_áéíóúüñÁÉÍÓÚÜÑ]+)", text, re.IGNORECASE)
        if linkedin_match:
            data["linkedin"] = linkedin_match.group(1).strip()

        # Experiencia
        exp_match = re.findall(r"Experiencia(?: Laboral)?[:\- ]*(.+?)(?:Educación|Skills|$)", text, re.IGNORECASE | re.DOTALL)
        if exp_match:
            data["experience"] = [e.strip() for e in exp_match[0].split("\n") if e.strip()]

        # Educación
        edu_match = re.findall(r"Educación[:\- ]*(.+?)(?:Skills|Experiencia|$)", text, re.IGNORECASE | re.DOTALL)
        if edu_match:
            data["education"] = [e.strip() for e in edu_match[0].split("\n") if e.strip()]

        # Skills
        skills_match = re.findall(r"Skills?[:\- ]*(.+?)(?:Experiencia|Educación|$)", text, re.IGNORECASE | re.DOTALL)
        if skills_match:
            skill_line = skills_match[0].replace("\n", " ")
            data["skills"] = [s.strip() for s in re.split(r"[,|]", skill_line) if s.strip()]

    except Exception as e:
        print(f"Error procesando el PDF: {e}")

    return data

def generate_readme(data):
   
    # Construye el README dinámicamente
    readme = f"""# {data['name'] or data['github']}

<!-- Social icons section -->
<p align="center">"""
    
    # Solo agregar iconos si los datos están disponibles
    social_icons = []
    
    if data['email']:
        social_icons.append(f'<a href="mailto:{data["email"]}"><img width="40px" src="https://img.icons8.com/color/48/000000/gmail--v1.png"></a>')
    
    if data['linkedin']:
        social_icons.append(f'<a href="https://linkedin.com/in/{data["linkedin"]}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg"></a>')
    
    if data['github']:
        social_icons.append(f'<a href="https://github.com/{data["github"]}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/github/github-original.svg"></a>')

    # Unir los iconos con espacios
    if social_icons:
        readme += "\n  " + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".join(social_icons)
    
    readme += "\n</p>"
    
    # Solo agregar GitHub Stats si hay usuario de GitHub
    if data['github']:
        readme += f"""
    
<details open>
<summary><h2>📊 GitHub Stats</h2></summary>
<p align="center">
    <a href="https://github.com/anuraghazra/github-readme-stats">
        <img align = "center" height=200 alt="{data['github']}'s Github Stats"
        src="https://github-readme-stats.vercel.app/api/?username={data['github']}" />
    </a>&nbsp;
    <a href="https://github.com/anuraghazra/github-readme-stats">
        <img align = "center" height=200 alt="{data['github']}'s Top Languages"
        src="https://github-readme-stats.vercel.app/api/top-langs/?username={data['github']}&langs_count=8&layout=compact&hide=Jupyter%20Notebook,Roff" />
    </a>
</p>
</details>
"""

    readme += "\n## 💼 Experiencia\n"
    if data['experience']:
        for exp in data['experience']:
            readme += f"- {exp}\n"
    else:
        readme += "_No se encontró experiencia en el CV._\n"

    readme += "\n## 🎓 Educación\n"
    if data['education']:
        for edu in data['education']:
            readme += f"- {edu}\n"
    else:
        readme += "_No se encontró educación en el CV._\n"

    readme += "\n## 🛠 Skills\n"
    if data['skills']:
        for skill in data['skills']:
            readme += f"- {skill}\n"
    else:
        readme += "_No se encontraron skills en el CV._\n"

    readme += f"\n---\n*Generado automáticamente desde el CV PDF por [cv-to-github-readme](https://github.com/pablofazio02/cv-to-github-readme)*\n"
    return readme

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        cv_file = request.files["cv_pdf"]
        filename = secure_filename(cv_file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        cv_file.save(file_path)

        # Procesa el PDF y genera el README dinámico
        data = extract_data_from_pdf(file_path)
        readme_content = generate_readme(data)
        with open("generated_README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
        return send_file("generated_README.md", as_attachment=True)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)