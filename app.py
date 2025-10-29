"""
======================================================================
app.py

Author: Pablo Fazio Arrabal
======================================================================
CLI to generate README from a CV PDF (local)
Usage (Windows):
    python app.py route/to/cv.pdf -o generated_README.md [--no-edit]
Usage (Linux/Mac):
    python3 app.py route/to/cv.pdf -o generated_README.md [--no-edit]
======================================================================

"""

import argparse
import os
import sys
import urllib.parse
from readme_parser import extract_data_from_pdf, generate_readme

def _normalize_url(u):
    """Return a URL with scheme. If empty, return as-is."""
    if not u:
        return u
    u = u.strip()
    parsed = urllib.parse.urlparse(u)
    if parsed.scheme:
        return u
    # add https if missing
    return "https://" + u

def prompt_edit(data):
    print("\nDetected values (leave empty to keep detected value):\n")
    for key in ("first_name", "last_name", "occupation", "email", "linkedin", "github", "website"):
        current = data.get(key, "") or ""
        new = input(f"{key.replace('_',' ').title()} [{current}]: ").strip()
        if new:
            data[key] = new
    
    current_skills = data.get("skills", [])
    print(f"Current skills: {', '.join(current_skills) if current_skills else '(none)'}")
    s = input("Enter skills separated by commas (empty to keep, prefix '+' to add): ").strip()
    if s:
        if s.startswith("+"):
            additions = [x.strip() for x in s[1:].split(",") if x.strip()]
            data["skills"] = current_skills + additions
        else:
            data["skills"] = [x.strip() for x in s.split(",") if x.strip()]

    current_profiles = data.get("profiles", [])
    print(f"Current profiles: {', '.join(current_profiles) if current_profiles else '(none)'}")
    s = input("Enter profiles separated by commas (empty to keep, prefix '+' to add): ").strip()
    if s:
        if s.startswith("+"):
            additions = [x.strip() for x in s[1:].split(",") if x.strip()]
            data["profiles"] = current_profiles + additions
        else:
            data["profiles"] = [x.strip() for x in s.split(",") if x.strip()]
    
    return data

def main():
    parser = argparse.ArgumentParser(description="Extract data from a CV PDF and generate README.md (CLI)")
    parser.add_argument("pdf", help="Path to the CV PDF file")
    parser.add_argument("--output", "-o", default="generated_README.md", help="Output path for README (default generated_README.md)")
    parser.add_argument("--no-edit", action="store_true", help="Do not prompt for editing; generate directly")
    args = parser.parse_args()

    if not os.path.isfile(args.pdf):
        print(f"Error: PDF file not found: {args.pdf}")
        sys.exit(1)

    try:
        data = extract_data_from_pdf(args.pdf)
    except Exception as e:
        print("Error extracting data from PDF:", e)
        sys.exit(1)

    print("\n--- PREVIEW (Extracted Data) ---\n")
    friendly = {
        "first_name": "First name",
        "last_name": "Last name",
        "occupation": "Occupation",
        "email": "Email",
        "linkedin": "LinkedIn",
        "github": "GitHub",
        "website": "Personal website",
        "skills": "Skills",
        "profiles": "Social Profiles",
    }
    order = [
        "first_name",
        "last_name",
        "occupation",
        "email",
        "linkedin",
        "github",
        "personal_website",
        "skills",
        "profiles",
    ]
    
    extra = [k for k in data.keys() if k not in order]
    for k in order + extra:
        if k not in data:
            continue
        v = data[k]
        label = friendly.get(k, k.replace("_", " ").title())
        if isinstance(v, list):
            print(f"{label}: {', '.join(v) if v else '(none)'}")
        else:
            print(f"{label}: {v}")
    print("\n--- PREVIEW END ---\n")

    if not args.no_edit:
        ans = input("Do you want to edit the values before generating the README? [Y/n]: ").strip().lower()
        if ans in ("", "y", "yes"):
            data = prompt_edit(data)

    # Normalize common URL fields so links in README are absolute
    for key in ("github", "linkedin", "website", "profiles"):
        if key in data:
            data[key] = _normalize_url(data[key] or "")

    try:
        readme_md = generate_readme(data)
    except Exception as e:
        print("Error generating README file:", e)
        sys.exit(1)

    try:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(readme_md)
    except Exception as e:
        print("Error writing output file:", e)
        sys.exit(1)

    full_path = os.path.abspath(args.output)
    print(f"\nREADME generated at: {full_path}")

if __name__ == "__main__":
    main()
