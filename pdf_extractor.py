"""
PDF Extractor
=============

Módulo para extraer datos estructurados de archivos PDF de CV.
Utiliza expresiones regulares para identificar información clave como
nombre, contacto, experiencia, educación y habilidades.
"""

import pdfplumber
import re
from typing import Dict, List


def extract_data_from_pdf(pdf_path: str) -> Dict[str, any]:
    """
    Extrae datos estructurados de un CV en formato PDF.
    
    Args:
        pdf_path (str): Ruta al archivo PDF del CV
        
    Returns:
        Dict[str, any]: Diccionario con datos extraídos del CV:
            - first_name (str): Nombre
            - last_name (str): Apellidos
            - github (str): Usuario de GitHub
            - email (str): Dirección de correo electrónico
            - linkedin (str): Usuario de LinkedIn
            - skills (List[str]): Lista de habilidades y competencias
            
    Raises:
        Exception: Si hay problemas leyendo el archivo PDF
    """
    
    # Estructura de datos inicial
    data = {
        "first_name": "",
        "last_name": "",
        "github": "", 
        "email": "",
        "linkedin": "",
        "skills": []
    }
    
    try:
        # Extraer texto del PDF
        text = _extract_text_from_pdf(pdf_path)
        
        # Buscar datos específicos usando expresiones regulares
        first_name, last_name = _extract_names(text)
        data["first_name"] = first_name
        data["last_name"] = last_name
        data["github"] = _extract_github(text)
        data["email"] = _extract_email(text)
        data["linkedin"] = _extract_linkedin(text)
        data["skills"] = _extract_skills(text)
        
    except Exception as e:
        print(f"Error procesando el PDF: {e}")
    
    return data


def _extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extrae todo el texto de un archivo PDF.
    
    Args:
        pdf_path (str): Ruta al archivo PDF
        
    Returns:
        str: Texto completo extraído del PDF
    """
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def _extract_names(text: str) -> tuple:
    """
    Extrae el nombre y apellidos del texto del CV.
    
    Args:
        text (str): Texto completo del CV
        
    Returns:
        tuple: (nombre, apellidos) o ("", "") si no se encuentra
    """
    # Buscar patrones como "Nombre: Juan Pérez García"
    name_patterns = [
        r"Nombre[:\- ]*([A-Za-záéíóúüñÁÉÍÓÚÜÑ\s]+)",
        r"Name[:\- ]*([A-Za-záéíóúüñÁÉÍÓÚÜÑ\s]+)",
        # Buscar en las primeras líneas si no hay etiquetas
        r"^([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+(?:\s+[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+)+)"
    ]
    
    for pattern in name_patterns:
        name_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if name_match:
            full_name = name_match.group(1).strip()
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = " ".join(name_parts[1:])
                return first_name, last_name
            elif len(name_parts) == 1:
                return name_parts[0], ""
    
    return "", ""


def _extract_email(text: str) -> str:
    """
    Extrae la dirección de correo electrónico del texto del CV.
    Acepta cualquier proveedor de email válido.
    
    Args:
        text (str): Texto completo del CV
        
    Returns:
        str: Dirección de email o cadena vacía si no se encuentra
    """
    # Buscar cualquier email válido
    email_match = re.search(r"[a-zA-Z0-9._%+-áéíóúüñÁÉÍÓÚÜÑ]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text, re.IGNORECASE)
    if email_match:
        return email_match.group(0).strip()
    return ""


def _extract_github(text: str) -> str:
    """
    Extrae el usuario de GitHub del texto del CV.
    
    Args:
        text (str): Texto completo del CV
        
    Returns:
        str: Usuario de GitHub o cadena vacía si no se encuentra
    """
    # Buscar URLs como "github.com/usuario"
    github_match = re.search(r"github\.com/([A-Za-z0-9\-_áéíóúüñÁÉÍÓÚÜÑ]+)", text, re.IGNORECASE)
    if github_match:
        return github_match.group(1).strip()
    return ""


def _extract_linkedin(text: str) -> str:
    """
    Extrae el usuario de LinkedIn del texto del CV.
    
    Args:
        text (str): Texto completo del CV
        
    Returns:
        str: Usuario de LinkedIn o cadena vacía si no se encuentra
    """
    # Buscar URLs como "linkedin.com/in/usuario"
    linkedin_match = re.search(r"linkedin\.com/in/([A-Za-z0-9\-_áéíóúüñÁÉÍÓÚÜÑ]+)", text, re.IGNORECASE)
    if linkedin_match:
        return linkedin_match.group(1).strip()
    return ""


def _extract_skills(text: str) -> List[str]:
    """
    Extrae las habilidades y competencias del texto del CV.
    
    Args:
        text (str): Texto completo del CV
        
    Returns:
        List[str]: Lista de habilidades
    """
    skills = []
    
    # Buscar sección de habilidades con diferentes patrones
    skill_patterns = [
        r"Skills?[:\- ]*(.+?)(?:\n\s*\n|\n[A-Z]|$)",
        r"Habilidades[:\- ]*(.+?)(?:\n\s*\n|\n[A-Z]|$)",
        r"Competencias[:\- ]*(.+?)(?:\n\s*\n|\n[A-Z]|$)",
        r"Technologies?[:\- ]*(.+?)(?:\n\s*\n|\n[A-Z]|$)",
        r"Tecnologías[:\- ]*(.+?)(?:\n\s*\n|\n[A-Z]|$)"
    ]
    
    for pattern in skill_patterns:
        skills_match = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        if skills_match:
            # Procesar el texto encontrado
            skill_text = skills_match[0].replace("\n", " ").strip()
            
            # Dividir por diferentes separadores
            for separator in [",", "|", "•", "-", "·"]:
                if separator in skill_text:
                    skills.extend([s.strip() for s in skill_text.split(separator) if s.strip()])
                    break
            else:
                # Si no hay separadores, dividir por espacios múltiples o saltos de línea
                skills.extend([s.strip() for s in re.split(r"\s{2,}|\n", skill_text) if s.strip()])
            
            break  # Solo usar el primer patrón que coincida
    
    # Limpiar y filtrar skills
    cleaned_skills = []
    for skill in skills:
        # Limpiar caracteres especiales al inicio/final
        clean_skill = re.sub(r"^[^\w\+#]+|[^\w\+#]+$", "", skill.strip())
        if clean_skill and len(clean_skill) > 1:
            cleaned_skills.append(clean_skill)
    
    return list(dict.fromkeys(cleaned_skills))  # Eliminar duplicados manteniendo orden


# Función de utilidad para debugging
def debug_extraction(pdf_path: str) -> None:
    """
    Función de utilidad para debug de la extracción de datos.
    
    Args:
        pdf_path (str): Ruta al archivo PDF
    """
    print("=== DEBUG: Extracción de datos del PDF ===")
    data = extract_data_from_pdf(pdf_path)
    
    for key, value in data.items():
        print(f"{key.upper()}: {value}")
        print("-" * 40)