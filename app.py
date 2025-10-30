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

from __future__ import annotations

import argparse
import os
import sys
import urllib.parse
from typing import Any, TypedDict

from readme_parser import extract_data_from_pdf, generate_readme


class CVData(TypedDict, total=False):
    """TypedDict describing extracted CV data."""
    first_name: str
    last_name: str
    occupation: str
    email: str
    linkedin: str
    github: str
    website: str
    profiles: Any
    skills: list[str]


def _normalize_url(u: str | None) -> str:
    """Ensure a URL has a scheme. Return empty string if input is falsy.

    Args:
        u: Candidate URL or None.

    Returns:
        Normalized URL as string (may be empty).
    """
    if not u:
        return ""
    s: str = u.strip()
    parsed = urllib.parse.urlparse(s)
    if parsed.scheme:
        return s
    return "https://" + s


def _print_preview(data: CVData) -> None:
    """Print a friendly preview of extracted data.

    Args:
        data: Extracted CV data.
    """
    friendly: dict[str, str] = {
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
    order: list[str] = [
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

    print("\n--- PREVIEW (Extracted Data) ---\n")
    extra: list[str] = [k for k in data.keys() if k not in order]
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


def _edit_skills(current: list[str] | None) -> list[str]:
    """Prompt user to edit skills list.

    Args:
        current: Current skills list or None.

    Returns:
        Updated skills list.
    """
    current_skills: list[str] = current or []
    print(f"Current skills: {', '.join(current_skills) if current_skills else '(none)'}")
    s: str = input("Enter skills separated by commas (empty to keep, prefix '+' to add): ").strip()
    if not s:
        return current_skills
    if s.startswith("+"):
        additions: list[str] = [x.strip() for x in s[1:].split(",") if x.strip()]
        return current_skills + additions
    return [x.strip() for x in s.split(",") if x.strip()]


def _edit_profiles(current: list[str] | None) -> list[str]:
    """Prompt user to edit profiles list (keeps simple list behavior).

    Args:
        current: Current profiles list or None.

    Returns:
        Updated profiles list.
    """
    current_profiles: list[str] = current or []
    print(f"Current profiles: {', '.join(current_profiles) if current_profiles else '(none)'}")
    s: str = input("Enter profiles separated by commas (empty to keep, prefix '+' to add): ").strip()
    if not s:
        return current_profiles
    if s.startswith("+"):
        additions: list[str] = [x.strip() for x in s[1:].split(",") if x.strip()]
        return current_profiles + additions
    return [x.strip() for x in s.split(",") if x.strip()]


def prompt_edit(data: CVData) -> CVData:
    """Interactive editing of extracted values.

    Args:
        data: CVData with extracted values.

    Returns:
        Possibly modified CVData.
    """
    if data is None:
        raise ValueError("data must be provided to prompt_edit")

    print("\nDetected values (leave empty to keep detected value):\n")
    for key in ("first_name", "last_name", "occupation", "email", "linkedin", "github", "website"):
        current: str = data.get(key, "") or ""
        new: str = input(f"{key.replace('_',' ').title()} [{current}]: ").strip()
        if new:
            data[key] = new

    # Skills
    skills_in: list[str] | None = data.get("skills")  # type: ignore[assignment]
    data["skills"] = _edit_skills(skills_in)

    # Profiles (kept as simple list to preserve original behavior)
    profiles_in = data.get("profiles")
    # ensure profiles_in is a list for interactive editing here
    if isinstance(profiles_in, list):
        data["profiles"] = _edit_profiles(profiles_in)
    else:
        # if it's not a list, show as list-like string and allow replace
        current_profiles_list: list[str] = []
        if profiles_in:
            try:
                # attempt to stringify dict values if needed (preserve behavior)
                if isinstance(profiles_in, dict):
                    current_profiles_list = [v for v in profiles_in.values()]
                else:
                    current_profiles_list = [str(profiles_in)]
            except Exception:
                current_profiles_list = [str(profiles_in)]
        data["profiles"] = _edit_profiles(current_profiles_list)

    return data


def main() -> None:
    """CLI entrypoint: parse args, extract data, allow edit, generate README."""
    parser = argparse.ArgumentParser(description="Extract data from a CV PDF and generate README.md (CLI)")
    parser.add_argument("pdf", help="Path to the CV PDF file")
    parser.add_argument("--output", "-o", default="generated_README.md", help="Output path for README (default generated_README.md)")
    parser.add_argument("--no-edit", action="store_true", help="Do not prompt for editing; generate directly")
    args = parser.parse_args()

    if not os.path.isfile(args.pdf):
        print(f"Error: PDF file not found: {args.pdf}")
        sys.exit(1)

    try:
        data: CVData = extract_data_from_pdf(args.pdf)  # type: ignore[assignment]
    except Exception as e:
        print("Error extracting data from PDF:", e)
        sys.exit(1)

    _print_preview(data)

    if not args.no_edit:
        ans: str = input("Do you want to edit the values before generating the README? [Y/n]: ").strip().lower()
        if ans in ("", "y", "yes"):
            try:
                data = prompt_edit(data)
            except Exception as e:
                print("Error during edit:", e)
                sys.exit(1)

    # Normalize URL-like fields (preserve profile behavior from original)
    for key in ("github", "linkedin", "website"):
        if key in data:
            data[key] = _normalize_url(data.get(key, "") or "")

    # preserve original behavior: attempt to normalize profiles if it's a string
    if "profiles" in data and isinstance(data.get("profiles"), str):
        data["profiles"] = _normalize_url(data.get("profiles") or "")

    try:
        readme_md: str = generate_readme(data)  # type: ignore[arg-type]
    except Exception as e:
        print("Error generating README file:", e)
        sys.exit(1)

    out_path: str = getattr(args, "output", "generated_README.md")
    fobj = None
    try:
        fobj = open(out_path, "w", encoding="utf-8")
        fobj.write(readme_md)
    except Exception as e:
        print("Error writing output file:", e)
        sys.exit(1)
    finally:
        if fobj is not None:
            try:
                fobj.close()
            except Exception:
                pass

    full_path: str = os.path.abspath(out_path)
    print(f"\nREADME generated at: {full_path}")


if __name__ == "__main__":
    main()