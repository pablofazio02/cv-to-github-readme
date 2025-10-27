"""
README Parser - Módulo principal
================================
"""

from pdf_extractor import extract_data_from_pdf
from readme_generator import generate_readme

# Re-exportar las funciones principales para mantener compatibilidad
__all__ = ['extract_data_from_pdf', 'generate_readme']


def process_cv_to_readme(pdf_path: str) -> str:
    """
    Función de conveniencia que procesa un CV completo en una sola llamada.
    
    Args:
        pdf_path (str): Ruta al archivo PDF del CV
        
    Returns:
        str: Contenido completo del README.md generado
        
    Example:
        >>> readme_content = process_cv_to_readme("mi_cv.pdf")
        >>> with open("README.md", "w", encoding="utf-8") as f:
        ...     f.write(readme_content)
    """
    data = extract_data_from_pdf(pdf_path)
    return generate_readme(data)


def get_extracted_data_preview(pdf_path: str) -> dict:
    """
    Extrae y muestra un preview de los datos encontrados en el CV.
    
    Args:
        pdf_path (str): Ruta al archivo PDF del CV
        
    Returns:
        dict: Datos extraídos con conteos adicionales para debug
    """
    data = extract_data_from_pdf(pdf_path)
    
    # Agregar información de debug
    data['_debug_info'] = {
        'experience_count': len(data.get('experience', [])),
        'education_count': len(data.get('education', [])),
        'skills_count': len(data.get('skills', [])),
        'has_contact_info': bool(data.get('email') or data.get('linkedin')),
        'has_github': bool(data.get('github'))
    }
    
    return data

"""
Extracción mínima desde PDF y generación de README (local).
- extract_data_from_pdf(path) -> dict con keys:
    first_name, last_name, email, linkedin, github, skills (lista)
- generate_readme(data) -> str (markdown)
Requiere pdfplumber (mejor) o PyPDF2 como fallback.
"""
import re

def _read_pdf_text(path):
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        return "\n".join(pages)
    except Exception:
        # fallback a PyPDF2
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(path)
            texts = []
            for p in reader.pages:
                t = ""
                try:
                    t = p.extract_text() or ""
                except Exception:
                    t = ""
                texts.append(t)
            return "\n".join(texts)
        except Exception:
            raise RuntimeError("No se pudo leer el PDF. Instala 'pdfplumber' o 'PyPDF2'.")

def extract_data_from_pdf(path):
    """
    Extrae nombre y apellidos (separados), email, linkedin, github y skills simples.
    Heurísticas sencillas: busca nombre en las primeras líneas que parezcan un nombre.
    """
    text = _read_pdf_text(path)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Detect name: buscar en las primeras 10 líneas una que tenga al menos 2 palabras y solo letras/acentos/espacios
    name_pattern = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s\-\']+$")
    first_name = ""
    last_name = ""
    for ln in lines[:10]:
        if name_pattern.match(ln) and "@" not in ln and len(ln.split()) >= 2:
            parts = ln.split()
            first_name = parts[0]
            last_name = " ".join(parts[1:])
            break

    # email (cualquiera)
    email_match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    email = email_match.group(0) if email_match else ""

    # linkedin (url o handle)
    linkedin_match = re.search(r"(https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-_]+)/?", text, re.IGNORECASE)
    linkedin = linkedin_match.group(1) if linkedin_match else ""
    if not linkedin:
        # también intentar sólo el handle linkedin.com/in/handle sin http
        m = re.search(r"linkedin\.com/in/([A-Za-z0-9\-_]+)", text, re.IGNORECASE)
        if m:
            linkedin = "https://www.linkedin.com/in/" + m.group(1)

    # github
    github_match = re.search(r"(https?://(?:www\.)?github\.com/[A-Za-z0-9\-_]+)/?", text, re.IGNORECASE)
    github = github_match.group(1) if github_match else ""
    if not github:
        m = re.search(r"github\.com/([A-Za-z0-9\-_]+)", text, re.IGNORECASE)
        if m:
            github = "https://github.com/" + m.group(1)

    # skills: heurística simple: buscar sección "Skills" o "Habilidades" y tomar la línea o lista siguiente
    skills = []
    skill_section = None
    for i, ln in enumerate(lines):
        if re.search(r"\b(Skills|Habilidades|Tecnologías|Tecnologias)\b", ln, re.IGNORECASE):
            skill_section = i
            break
    if skill_section is not None:
        # tomar hasta 3 líneas siguientes y extraer palabras separadas por comas o bullets
        candidates = lines[skill_section:skill_section+4]
        joined = " ".join(candidates)
        # separar por comas o bullets
        items = re.split(r"[•\-\n\r,;]+", joined)
        skills = [s.strip() for s in items if 2 <= len(s.strip()) <= 40]
        # filtrar nombres demasiado genéricos
        skills = [s for s in skills if not re.match(r"^(skills|habilidades|tecnologías)$", s, re.IGNORECASE)]
    # Si no se detectaron skills, dejar lista vacía
    data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "linkedin": linkedin,
        "github": github,
        "skills": skills
    }
    return data

def generate_readme(data):
    """
    Generates a simple README.md based on fields in the user CV.
    data: dict con keys: first_name, last_name, email, linkedin, github, skills (list)
    """

    # NAME
    fn = data.get("first_name", "") or ""
    ln = data.get("last_name", "") or ""
    full_name = (fn + " " + ln).strip() or "Name Surname"
    md = []
    md.append(f"<h1 align=\"center\">Hi 👋, I'm {fn} </h1>")

    # SOCIAL ICONS
    email = data.get("email", "") or ""
    linkedin = data.get("linkedin", "") or ""
    github = data.get("github", "") or ""

    icons = []
    if email:
        icons.append(f'<a href="mailto:{email}"><img width="40px" src="https://img.icons8.com/color/48/000000/gmail--v1.png"></a>')
    if linkedin:
        icons.append(f'<a href="{linkedin}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg"></a>')
    if github:
        icons.append(f'<a href="{github}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/github/github-original.svg"></a>')

    # We will add social icons for every social found 
    if icons:
        spacer = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        md.append("<!-- Social icons section -->")
        md.append('<p align="center">')
        md.append(spacer.join(icons))
        md.append('</p>\n')

    # Getting github username if available
    if github:
        github_username = github.rstrip("/").split("/")[-1]

    # SKILLS
    md.append('<details open>')
    skills = data.get("skills", []) or []
    md.append('<summary><h2>🛠️ Skills</h2></summary>')
    if skills:
        
        for s in skills:
            md.append(f"- {s}")
            md.append("")
    else:
        md.append("Here you can add your main skills.\n")
    md.append('</details>\n')

    # GITHUB PROJECTS
    if github:
        md.append('<details open>')
        md.append('<summary><h2>📘 GitHub Projects</h2></summary>')
        md.append('<p>')
        md.append(f'  <a href="{github}?tab=repositories&sort=stargazers">')
        md.append('  </a>')
        md.append('</p>')
        md.append('</details>\n')

    # GITHUB STATS
    if github_username:
        md.append('<details open>')
        md.append('<summary><h2>📊 GitHub Stats</h2></summary>')
        md.append('<p align="center">')
        md.append(f'    <img align="center" height=200 alt="{github_username}\'s Github Stats" src="https://github-readme-stats.vercel.app/api/?username={github_username}" />')
        md.append('&nbsp;')
        md.append(f'    <img align="center" height=200 alt="{github_username}\'s Top Languages" src="https://github-readme-stats.vercel.app/api/top-langs/?username={github_username}&langs_count=8&layout=compact" />')
        md.append('</p>')
        md.append('<p align="center">')
        md.append(f'  <img src="https://streak-stats.demolab.com?user={github_username}&theme=transparent&date_format=j%20M%5B%20Y%5D" height="180em"/>')
        md.append('</p>')
        md.append('</details>\n')

   # FOOTER
    md.append("---\n")
    md.append("Generado con cv-to-github-readme (local parser). Revisa y ajusta antes de publicar.\n")
    return "\n".join(md)
