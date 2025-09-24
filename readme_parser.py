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
