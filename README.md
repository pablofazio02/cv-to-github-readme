# cv-to-github-readme 

Local CLI tool that parses a PDF CV and generates a GitHub profile README (in Markdown). The tool extracts primary contact information, public profiles and skills and builds a ready-to-use profile README template with optional GitHub stats badges.

![Initial Demo](assets/initial_demo.gif)

**IMPORTANT**: It is recommended to have a GitHub profile linked from your CV for best results.

## Features

- Extracts: first name, last name, email, LinkedIn, GitHub, other public profiles (GitLab, Bitbucket, ResearchGate, ORCID, Google Scholar, ...) and a skills list.
- Generates a GitHub-friendly README.md with:
  - Centered social icons (only shown when present)
  - Language badges (user-specific search links)
  - GitHub stats + top languages cards
  - Optional GitHub streak badge
  - Skills section
- Fully local: no server required, no uploads
- CLI preview and interactive editing before writing the README file.

## Quick install (Windows)

1. Ensure Python 3.8+ is installed and `python` is available in PATH.
2. Create and activate a virtual environment:

```powershell
# Create virtual environment
python -m venv venv

# CMD activation
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py "C:\path\to\CV.pdf" -o generated_README.md [--no-edit]
```

## Quick install (Linux / macOS)

1. Ensure Python 3.8+ is installed and `python3` is available in PATH.
2. Create and activate a virtual environment:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python3 app.py "/path/to/CV.pdf" -o generated_README.md [--no-edit]
```

## Privacy
- All parsing and image downloading run locally on your machine.
- No files or extracted data are uploaded or sent to external servers by this tool.
- The README generated may contain personal links and contact information — review and sanitize before publishing.


## License
MIT License — see LICENSE file. Short summary: you are free to use, modify and distribute the code. No warranty provided.


## To Do / Contribute
- Add more profile hosts and skill parsing improvements.
- New README template options.
- Support for more input formats (DOCX, ODT, etc.).
- Improve regular expressions detection (e.g. usernames with Unicode characters /AI API support).
- Normalize profile URLs both when parsing from CV and when editing the generated README.
- Links parsing

---

Contributions, issues and improvements are welcome. Create an issue if you have parser edge-cases to add (new profile hosts, language badge tweaks, extraction heuristics).
