"""
README Generator
===============

Módulo para generar archivos README.md personalizados para GitHub.
Toma datos estructurados extraídos de un CV y los convierte en un
README.md con formato profesional, incluyendo estadísticas de GitHub,
iconos sociales y secciones organizadas.
"""

from typing import Dict, List


def generate_readme(data: Dict[str, any]) -> str:
    """
    Genera un archivo README.md personalizado para GitHub.
    
    Args:
        data (Dict[str, any]): Diccionario con datos del CV:
            - first_name (str): Nombre
            - last_name (str): Apellidos
            - github (str): Usuario de GitHub
            - email (str): Dirección de correo electrónico
            - linkedin (str): Usuario de LinkedIn
            - skills (List[str]): Lista de habilidades
            
    Returns:
        str: Contenido completo del archivo README.md
    """
    
    # Construir nombre completo
    readme = f"<h1 align=\"center\">Hi 👋, I'm {first_name} </h1>"

    
    # Agregar sección de iconos sociales si hay datos disponibles
    social_section = _generate_social_icons_section(data)
    if social_section:
        readme += social_section + "\n"
    
    # Agregar sección de habilidades
    readme += _generate_skills_section(data.get('skills', []))

    # Agregar estadísticas de GitHub si hay usuario
    if data.get('github'):
        readme += _generate_github_stats_section(data['github']) + "\n"
    
    return readme


def _generate_social_icons_section(data: Dict[str, any]) -> str:
    """
    Genera la sección de iconos sociales.
    
    Args:
        data (Dict[str, any]): Datos del CV
        
    Returns:
        str: HTML con iconos sociales o cadena vacía si no hay datos
    """
    social_icons = []
    
    # Icono de email
    if data.get('email'):
        email_icon = f'<a href="mailto:{data["email"]}">' \
                    f'<img width="40px" src="https://img.icons8.com/color/48/000000/gmail--v1.png" alt="Email"></a>'
        social_icons.append(email_icon)
    
    # Icono de LinkedIn
    if data.get('linkedin'):
        linkedin_icon = f'<a href="https://linkedin.com/in/{data["linkedin"]}">' \
                       f'<img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg" alt="LinkedIn"></a>'
        social_icons.append(linkedin_icon)
    
    # Icono de GitHub
    if data.get('github'):
        github_icon = f'<a href="https://github.com/{data["github"]}">' \
                     f'<img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/github/github-original.svg" alt="GitHub"></a>'
        social_icons.append(github_icon)
    
    # Retornar sección completa si hay iconos
    if social_icons:
        icons_html = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".join(social_icons)
        return f'<!-- Social icons section -->\n<p align="center">\n  {icons_html}\n</p>'
    
    return ""


def _generate_github_stats_section(github_username: str) -> str:
    """
    Genera la sección de estadísticas de GitHub.
    
    Args:
        github_username (str): Nombre de usuario de GitHub
        
    Returns:
        str: HTML con estadísticas de GitHub
    """
    stats_section = f"""
<details open>
<summary><h2>📊 GitHub Stats</h2></summary>
<p align="center">
    <a href="https://github.com/anuraghazra/github-readme-stats">
        <img align="center" height="200" alt="{github_username}'s Github Stats"
        src="https://github-readme-stats.vercel.app/api/?username={github_username}" />
    </a>&nbsp;
    <a href="https://github.com/anuraghazra/github-readme-stats">
        <img align="center" height="200" alt="{github_username}'s Top Languages"
        src="https://github-readme-stats.vercel.app/api/top-langs/?username={github_username}&langs_count=8&layout=compact&hide=Jupyter%20Notebook,Roff" />
    </a>
</p>
</details>"""
    
    return stats_section


def _generate_skills_section(skills: List[str]) -> str:
    """
    Genera la sección de habilidades y competencias.
    
    Args:
        skills (List[str]): Lista de habilidades
        
    Returns:
        str: Sección de habilidades en formato Markdown
    """
    section = "\n## 🛠 Skills & Technologies\n\n"
    
    if skills:
        for skill in skills:
            if skill.strip():  # Solo agregar habilidades no vacías
                section += f"- {skill.strip()}\n"
    else:
        section += "_No se encontraron skills en el CV._\n"
    
    return section


def generate_preview_readme(data: Dict[str, any]) -> str:
    """
    Genera una versión de vista previa del README (más compacta).
    
    Args:
        data (Dict[str, any]): Datos del CV
        
    Returns:
        str: Versión compacta del README para vista previa
    """

    preview = f"<h1 align=\"center\">Hi 👋, I'm {first_name} </h1>"
    
    # Solo mostrar datos disponibles
    if data.get('email') or data.get('linkedin') or data.get('github'):
        preview += "**Contacto:** "
        contact_info = []
        if data.get('email'):
            contact_info.append(f"📧 {data['email']}")
        if data.get('linkedin'):
            contact_info.append(f"💼 LinkedIn: {data['linkedin']}")
        if data.get('github'):
            contact_info.append(f"🐙 GitHub: {data['github']}")
        preview += " | ".join(contact_info) + "\n\n"
    
    # Resumen de datos encontrados
    sections_found = []
    if data.get('skills'):
        sections_found.append(f"Skills ({len(data['skills'])} elementos)")
    
    if sections_found:
        preview += "**Secciones encontradas:** " + " | ".join(sections_found) + "\n"
    
    return preview


# Función de utilidad para debugging
def debug_readme_generation(data: Dict[str, any]) -> None:
    """
    Función de utilidad para debug de la generación del README.
    
    Args:
        data (Dict[str, any]): Datos del CV
    """
    print("=== DEBUG: Generación del README ===")
    readme = generate_readme(data)
    
    print("README Generado:")
    print("=" * 50)
    print(readme)
    print("=" * 50)
    print(f"Longitud total: {len(readme)} caracteres")