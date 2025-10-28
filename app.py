"""
CLI para generar README a partir de un CV en PDF (local)
Uso:
    python app.py ruta/al/cv.pdf -o salida_README.md [--no-edit]
"""

import argparse
import os
import sys
from readme_parser import extract_data_from_pdf, generate_readme

def prompt_edit(data):
    print("\nValores detectados (deja vacío para mantener el valor detectado):\n")
    for key in ("first_name", "last_name", "email", "linkedin", "github"):
        current = data.get(key, "") or ""
        new = input(f"{key.replace('_',' ').title()} [{current}]: ").strip()
        if new:
            data[key] = new
    current_skills = data.get("skills", [])
    print(f"Skills actuales: {', '.join(current_skills) if current_skills else '(ninguna)'}")
    s = input("Introduce skills separadas por coma (vacío para mantener, prefix '+' para añadir): ").strip()
    if s:
        if s.startswith("+"):
            additions = [x.strip() for x in s[1:].split(",") if x.strip()]
            data["skills"] = current_skills + additions
        else:
            data["skills"] = [x.strip() for x in s.split(",") if x.strip()]
    return data

def main():
    parser = argparse.ArgumentParser(description="Extrae datos de un CV PDF y genera README.md (CLI)")
    parser.add_argument("pdf", help="Ruta al archivo PDF del CV")
    parser.add_argument("--output", "-o", default="generated_README.md", help="Ruta salida README (por defecto generated_README.md)")
    parser.add_argument("--no-edit", action="store_true", help="No preguntar por edición; generar directamente")
    args = parser.parse_args()

    if not os.path.isfile(args.pdf):
        print(f"Error: no se encuentra el archivo PDF: {args.pdf}")
        sys.exit(1)

    try:
        data = extract_data_from_pdf(args.pdf)
    except Exception as e:
        print("Error extrayendo datos del PDF:", e)
        sys.exit(1)

    print("\n--- PREVIEW (Extracted Data) ---\n")
    for k, v in data.items():
        if k == "skills":
            print(f"{k}: {', '.join(v)}")
        else:
            print(f"{k}: {v}")
    print("\n--- PREVIEW END ---\n")

    if not args.no_edit:
        ans = input("Do you want to edit the values before generating the README? [Y/n]: ").strip().lower()
        if ans in ("", "y", "yes"):
            data = prompt_edit(data)

    try:
        readme_md = generate_readme(data)
    except Exception as e:
        print("Error generando README:", e)
        sys.exit(1)

    try:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(readme_md)
    except Exception as e:
        print("Error escribiendo el archivo de salida:", e)
        sys.exit(1)

    print(f"\nREADME generado en: {args.output}")

if __name__ == "__main__":
    main()
