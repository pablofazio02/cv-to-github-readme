"""
================================
README Parser - Principal Module

Author: Pablo Fazio Arrabal
================================
"""

"""
Miminal extraction from PDF and README generation (local).
- extract_data_from_pdf(path) -> dict with keys:
    first_name, last_name, email, linkedin, github, website, skills (list), profiles (list)
- generate_readme(data) -> str (markdown)
Requires pdfplumber o PyPDF2 as fallback.
"""
import re
import urllib

def _read_pdf_text(path):
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        return "\n".join(pages)
    except Exception:
        # fallback as PyPDF2
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
            raise RuntimeError("Could not read the PDF. Please install 'pdfplumber' or 'PyPDF2'.")

def extract_data_from_pdf(path):
    """
    Extracts first name and last name (separated), email, linkedin, github, personal website (located in Github Pages),
    skills and social profiles.
    Simple heuristics: looks for name in the first lines that look like a name.
    """
    text = _read_pdf_text(path)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    name_pattern = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s\-\']+$")
    first_name = ""
    last_name = ""
    for ln in lines[:10]:
        if name_pattern.match(ln) and "@" not in ln and len(ln.split()) >= 2:
            parts = ln.split()
            first_name = parts[0]
            last_name = " ".join(parts[1:])
            break

    # occupation detection
    occupation = ""
    occ_keywords = [
        "mathematician", "computer scientist", "student", "intern", "phd", "ph.d", "postdoc",
        "post-doctoral", "professor", "lecturer", "researcher", "scientist", "data scientist",
        "data analyst", "software engineer", "engineer", "developer", "full-stack", "full stack",
        "frontend", "front-end", "backend", "back-end", "machine learning", "ml engineer",
        "research assistant", "manager", "consultant", "analyst", "architect", "teacher",
        "assistant", "director", "engineer-in-training"
    ]

    # build set of name tokens to exclude from occupation
    name_tokens = set()
    if first_name:
        name_tokens.update([t.lower() for t in re.findall(r"\w+", first_name)])
    if last_name:
        name_tokens.update([t.lower() for t in re.findall(r"\w+", last_name)])

    def _remove_name_tokens(s: str) -> str:
        # replace each name token by a single space (use word boundaries) to avoid concatenation
        res = s
        # sort by length descending to avoid partial matches (e.g., "ann" inside "anne")
        for nt in sorted(name_tokens, key=len, reverse=True):
            if not nt:
                continue
            res = re.sub(rf"\b{re.escape(nt)}\b", " ", res, flags=re.IGNORECASE)
        # collapse multiple spaces and trim
        res = re.sub(r"\s+", " ", res).strip()
        return res

    # search first lines (prefer lines near the top of the CV)
    for ln in lines[:6]:
        cleaned = _remove_name_tokens(ln)

        if len(cleaned) < 3:
            continue
        low = cleaned.lower()
        # prefer exact/phrase matches first
        for kw in occ_keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", low, re.IGNORECASE):
                occupation = cleaned
                break
        if occupation:
            break

        # fallback: handle run-on / concatenated words like "mathematicianandcomputerscientist"
        compact = re.sub(r"[^a-z0-9]", "", low)
        matches = []
        for kw in occ_keywords:
            kw_compact = re.sub(r"[^a-z0-9]", "", kw.lower())
            if kw_compact and kw_compact in compact:
                matches.append(kw)

        if matches:
            # keep order and uniqueness, produce readable label(s)
            seen = []
            for m in matches:
                if m not in seen:
                    seen.append(m)
                occupation = " and ".join([m.title() for m in seen])
                break

    # fallback
    if not occupation:
        segments = re.split(r"[.\n\r;]+", text)
        for seg in segments:
            seg = seg.strip()
            if not seg or len(seg) < 3:
                continue
            cleaned = _remove_name_tokens(seg)
            if len(cleaned) < 3:
                continue
            low = cleaned.lower()
            for kw in occ_keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", low, re.IGNORECASE):
                    occupation = cleaned
                    break
            if occupation:
                break

    # email
    email_match = re.search(r"[ÑA-Zña-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}", text)
    email = email_match.group(0) if email_match else ""

    # linkedin
    linkedin_match = re.search(r"(https?://(?:www\.)?linkedin\.com/in/[\w\-.%]+)/?", text, re.IGNORECASE)
    linkedin = linkedin_match.group(1) if linkedin_match else ""
    if not linkedin:
        # try just the handle (allow Unicode word chars, dots, hyphens and %)
        m = re.search(r"linkedin\.com/in/([\w\-.%]+)", text, re.IGNORECASE)
        if m:
            linkedin = "https://www.linkedin.com/in/" + m.group(1)

    # github
    github_match = re.search(r"(https?://(?:www\.)?github\.com/[\w\-.%]+)/?", text, re.IGNORECASE)
    github = github_match.group(1) if github_match else ""
    if not github:
        m = re.search(r"github\.com/([\w\-.%]+)", text, re.IGNORECASE)
        if m:
            github = "https://github.com/" + m.group(1)

    # personal website (deployed in github pages)
    website_match = re.search(r"(https?://[A-Za-z0-9\-_]+\.github\.io)/?", text, re.IGNORECASE)
    website = website_match.group(1) if website_match else ""
    if not website:
        m = re.search(r"([A-Za-z0-9\-_]+\.github\.io)/?", text, re.IGNORECASE)
        if m:
            website = "https://" + m.group(1)

    # additional profiles detection
    profiles = {}
    host_patterns = {
       "instagram": r"https?://(?:www\.)?instagram\.com/([A-Za-z0-9\._]+)/?",
       "x": r"https?://(?:www\.)?x\.com/([A-Za-z0-9_]+)/?",
       "twitter": r"https?://(?:www\.)?twitter\.com/([A-Za-z0-9_]+)/?",
       "gitlab": r"https?://(?:www\.)?gitlab\.com/([A-Za-z0-9\-_]+)/?",
       "tiktok": r"https?://(?:www\.)?tiktok\.com/@?([A-Za-z0-9\-_]+)/?",
       "facebook": r"https?://(?:www\.)?facebook\.com/([A-Za-z0-9\.\-_]+)/?",
       "stackoverflow": r"https?://(?:www\.)?stackoverflow\.com/users/([0-9]+/[A-Za-z0-9\-_]+)/?",
       "medium": r"https?://(?:www\.)?medium\.com/@?([A-Za-z0-9\-_]+)/?",
       "devto": r"https?://(?:www\.)?dev\.to/([A-Za-z0-9\-_]+)/?",
       "kaggle": r"https?://(?:www\.)?kaggle\.com/([A-Za-z0-9\-_]+)/?",
       "codepen": r"https?://(?:www\.)?codepen\.io/([A-Za-z0-9\-_]+)/?",
       "leetcode": r"https?://(?:www\.)?leetcode\.com/([A-Za-z0-9\-/]+)/?",
       "hackerrank": r"https?://(?:www\.)?hackerrank\.com/([A-Za-z0-9\-_]+)/?",
       "bitbucket": r"https?://(?:www\.)?bitbucket\.org/([A-Za-z0-9\-_]+)/?",
       "google_scholar": r"https?://scholar\.google\.com/citations\?user=([A-Za-z0-9\-_]+)/?",
       "arxiv": r"https?://arxiv\.org/a/([A-Za-z0-9\-_]+)/?",
       "orcid": r"https?://orcid\.org/([0-9\-X]+)/?",
       "dialnet": r"https?://dialnet\.unirioja\.es/servlet/articulo?codigo=([0-9]+)/?",
       "scopus": r"https?://www\.scopus\.com/authid/detail\.uri\?authorId=([0-9]+)/?",
       "researchgate": r"https?://(?:www\.)?researchgate\.net/profile/([A-Za-z0-9\-_]+)/?",
       "academia": r"https?://(?:www\.)?academia\.edu/([A-Za-z0-9\-_]+)/?"
    }
    
    for key, pat in host_patterns.items():
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            # reconstruct a clean URL for the profile
            handle = m.group(1).rstrip("/")
            base = {
                "instagram": "https://instagram.com/",
                "x": "https://x.com/",
                "twitter": "https://twitter.com/",
                "tiktok": "https://www.tiktok.com/@",
                "facebook": "https://www.facebook.com/",
                "gitlab": "https://gitlab.com/",
                "stackoverflow": "https://stackoverflow.com/users/",
                "medium": "https://medium.com/@",
                "devto": "https://dev.to/",
                "kaggle": "https://kaggle.com/",
                "codepen": "https://codepen.io/",
                "leetcode": "https://leetcode.com/",
                "hackerrank": "https://www.hackerrank.com/",
                "bitbucket": "https://bitbucket.org/",
                "google_scholar": "https://scholar.google.com/citations?user=",
                "arxiv": "https://arxiv.org/a/",
                "orcid": "https://orcid.org/",
                "dialnet": "https://dialnet.unirioja.es/servlet/articulo?codigo=",
                "scopus": "https://www.scopus.com/authid/detail.uri?authorId=",
                "researchgate": "https://www.researchgate.net/profile/",
                "academia": "https://www.academia.edu/"
            }[key]
            profiles[key] = base + handle

    # fallback: detect other http(s) URLs (personal website / portfolio) excluding known hosts
    if "website" not in profiles:
        all_urls = re.findall(r"https?://[^\s\)\]\>]+", text)
        known_hosts = ("github.com", "linkedin.com", "instagram.com", "x.com", "twitter.com",
                       "gitlab.com", "facebook.com", "tiktok.com", "stackoverflow.com", "medium.com", "dev.to",
                       "kaggle.com", "codepen.io", "leetcode.com", "hackerrank.com",
                       "bitbucket.org", "dialnet.unirioja.es", "scholar.google.com", "arxiv.org", "orcid.org", "scopus.com", "researchgate.net", "academia.edu")
        for u in all_urls:
           u_clean = u.rstrip(".,;)")
           if not any(h in u_clean for h in known_hosts):
            profiles["website"] = u_clean
            break

    # skills: heurística simple: buscar sección "Skills" y tomar las siguientes líneas
    skills = []
    skill_section = None
    for i, ln in enumerate(lines):
        if re.search(r"\b(Skills|Habilidades|Tecnologías|Tecnologias|Technologies|Habilities)\b", ln, re.IGNORECASE):
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
        "occupation": occupation,
        "email": email,
        "linkedin": linkedin,
        "github": github,
        "website": website,
        "profiles": profiles,
        "skills": skills,
    }
    return data

def generate_readme(data):

    """
    Generates a simple README.md based on fields in the user CV.
    data: dict with keys: first_name, last_name, email, linkedin, github, website, profiles (list), skills (list)
    """

    # NAME
    fn = data.get("first_name", "") or ""
    ln = data.get("last_name", "") or ""
    full_name = (fn + " " + ln).strip() or "Name Surname"
    md = []
    md.append(f"<h1 align=\"center\">Hi 👋, I'm {fn} </h1>")

    # MAIN OCCUPATION
    occ = data.get("occupation", "") or ""
    if occ:
        md.append(f"<h3 align=\"center\">{occ}</h3>\n")

    # SOCIAL ICONS
    email = data.get("email", "") or ""
    linkedin = data.get("linkedin", "") or ""
    github = data.get("github", "") or ""
    website = data.get("website", "") or ""
    profiles = data.get("profiles", {}) or {}

    icons = []
    if email:
        icons.append(f'<a href="mailto:{email}"><img width="40px" src="https://img.icons8.com/color/48/000000/gmail--v1.png"></a>')
    if linkedin:
        icons.append(f'<a href="{linkedin}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg"></a>')
    if github:
        icons.append(f'<a href="{github}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/github/github-original.svg"></a>')
    if profiles.get("instagram"):
        instagram = profiles["instagram"]
        icons.append(f'<a href="{instagram}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/instagram/instagram-original.svg"></a>')
    if profiles.get("x"):
        x = profiles["x"]
        icons.append(f'<a href="{x}"><img width="40px" src="https://img.icons8.com/ios-filled/50/000000/twitter--v1.png"></a>')
    if profiles.get("twitter"):
        twitter = profiles["twitter"]
        icons.append(f'<a href="{twitter}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/twitter/twitter-original.svg"></a>')
    if profiles.get("gitlab"):
        gitlab = profiles["gitlab"]
        icons.append(f'<a href="{gitlab}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/gitlab/gitlab-original.svg"></a>')
    if profiles.get("facebook"):
        facebook = profiles["facebook"]
        icons.append(f'<a href="{facebook}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/facebook/facebook-original.svg"></a>')
    if profiles.get("tiktok"):
        tiktok = profiles["tiktok"]
        icons.append(f'<a href="{tiktok}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/tiktok/tiktok-original.svg"></a>')
    if profiles.get("stackoverflow"):
        stackoverflow = profiles["stackoverflow"]
        icons.append(f'<a href="{stackoverflow}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/stackoverflow/stackoverflow-original.svg"></a>')
    if profiles.get("medium"):
        medium = profiles["medium"]
        icons.append(f'<a href="{medium}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/medium/medium-original.svg"></a>')
    if profiles.get("devto"):
        devto = profiles["devto"]
        icons.append(f'<a href="{devto}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/devto/devto-original.svg"></a>')
    if profiles.get("kaggle"):
        kaggle = profiles["kaggle"]
        icons.append(f'<a href="{kaggle}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/kaggle/kaggle-original.svg"></a>')
    if profiles.get("codepen"):
        codepen = profiles["codepen"]
        icons.append(f'<a href="{codepen}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/codepen/codepen-original.svg"></a>')
    if profiles.get("leetcode"):
        leetcode = profiles["leetcode"]
        icons.append(f'<a href="{leetcode}"><img width="40px" src="https://img.icons8.com/ios-filled/50/000000/leetcode.png"></a>')
    if profiles.get("hackerrank"):
        hackerrank = profiles["hackerrank"]
        icons.append(f'<a href="{hackerrank}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/hackerrank/hackerrank-original.svg"></a>')
    if profiles.get("bitbucket"):
        bitbucket = profiles["bitbucket"]
        icons.append(f'<a href="{bitbucket}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/bitbucket/bitbucket-original.svg"></a>')
    if profiles.get("google_scholar"):
        google_scholar = profiles["google_scholar"]
        icons.append(f'<a href="{google_scholar}"><img width="40px" src="https://img.icons8.com/ios-filled/50/000000/google-scholar.png"></a>')     
    if profiles.get("arxiv"):
        arxiv = profiles["arxiv"]
        icons.append(f'<a href="{arxiv}"><img width="40px" src="https://upload.wikimedia.org/wikipedia/commons/4/45/ArXiv_logo.svg"></a>')
    if profiles.get("orcid"):
        orcid = profiles["orcid"]
        icons.append(f'<a href="{orcid}"><img width="40px" src="https://orcid.org/sites/default/files/images/orcid_16x16.png"></a>')
    if profiles.get("dialnet"):
        dialnet = profiles["dialnet"]
        icons.append(f'<a href="{dialnet}"><img width="40px" src="https://dialnet.unirioja.es/images/dialnet-logo.png"></a>')
    if profiles.get("scopus"):
        scopus = profiles["scopus"]
        icons.append(f'<a href="{scopus}"><img width="40px" src="https://www.elsevier.com/__data/assets/image/0007/69401/scopus-logo.png"></a>')
    if profiles.get("researchgate"):
        researchgate = profiles["researchgate"]
        icons.append(f'<a href="{researchgate}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/researchgate/researchgate-original.svg"></a>')
    if profiles.get("academia"):
        academia = profiles["academia"]
        icons.append(f'<a href="{academia}"><img width="40px" src="https://upload.wikimedia.org/wikipedia/commons/1/12/Academia.edu_logo.png"></a>')

    # We will add social icons for every social found 
    if icons:
        spacer = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        md.append("<!-- Social icons section -->")
        md.append('<p align="center">')
        md.append(spacer.join(icons))
        md.append('</p>\n')

    if website:
        display_domain = re.sub(r"^https?://(www\.)?", "", website).rstrip("/")
        md.append("") 
        md.append("<!-- Personal website highlight -->")
        md.append('<p align="center">')
        label = urllib.parse.quote("Personal Website")
        badge = f"https://img.shields.io/badge/{label}-{urllib.parse.quote(display_domain)}-2b9348?logo=google-chrome&logoColor=white"
        md.append(f'  <a href="{website}"><img src="{badge}" alt="Visit website" /></a>')
        md.append('</p>\n')

    # Getting github username if available
    if github:
        github_username = github.rstrip("/").split("/")[-1]

    # SKILLS
    md.append('<details open>')
    md.append('<summary><h2>🛠️ Skills</h2></summary>')
    
    # Normalized mappings: key -> (label, badge_src)
    LANG_BADGES = {
    "python": ("Python", "https://img.shields.io/badge/Python-14354C.svg?logo=python&logoColor=white"),
    "java": ("Java", "https://custom-icon-badges.demolab.com/badge/Java-007396.svg?logo=java&logoColor=white"),
    "c": ("C", "https://img.shields.io/badge/C-03599C.svg?logo=c&logoColor=white"),
    "c++": ("C++", "https://img.shields.io/badge/C++-00599C.svg?logo=c%2B%2B&logoColor=white"),
    "c#": ("C#", "https://img.shields.io/badge/C%23-239120.svg?logo=c-sharp&logoColor=white"),
    "go": ("Go", "https://img.shields.io/badge/Go-00ADD8.svg?logo=go&logoColor=white"),
    "rust": ("Rust", "https://img.shields.io/badge/Rust-000000.svg?logo=rust&logoColor=white"),
    "swift": ("Swift", "https://img.shields.io/badge/Swift-FA7343.svg?logo=swift&logoColor=white"),
    "kotlin": ("Kotlin", "https://img.shields.io/badge/Kotlin-0095D5.svg?logo=kotlin&logoColor=white"),
    "ruby": ("Ruby", "https://img.shields.io/badge/Ruby-CC342D.svg?logo=ruby&logoColor=white"),
    "php": ("PHP", "https://img.shields.io/badge/PHP-777BB4.svg?logo=php&logoColor=white"),
    "typescript": ("TypeScript", "https://img.shields.io/badge/TypeScript-3178C6.svg?logo=typescript&logoColor=white"),
    "javascript": ("JavaScript", "https://img.shields.io/badge/JavaScript-F7DF1E.svg?logo=javascript&logoColor=black"),
    "dart": ("Dart", "https://img.shields.io/badge/Dart-0175C2.svg?logo=dart&logoColor=white"),
    "scala": ("Scala", "https://img.shields.io/badge/Scala-DC322F.svg?logo=scala&logoColor=white"),
    "groovy": ("Groovy", "https://img.shields.io/badge/Groovy-E69F56.svg?logo=groovy&logoColor=white"),
    "elixir": ("Elixir", "https://img.shields.io/badge/Elixir-4B275F.svg?logo=elixir&logoColor=white"),
    "haskell": ("Haskell", "https://img.shields.io/badge/Haskell-5D4F85.svg?logo=haskell&logoColor=white"),
    "julia": ("Julia", "https://img.shields.io/badge/Julia-9558B2.svg?logo=julia&logoColor=white"),
    "r": ("R", "https://img.shields.io/badge/R-276DC3.svg?logo=r&logoColor=white"),
    "perl": ("Perl", "https://img.shields.io/badge/Perl-39457E.svg?logo=perl&logoColor=white"),
    "fortran": ("Fortran", "https://img.shields.io/badge/Fortran-4D41B1.svg?logo=fortran&logoColor=white"),
    "matlab": ("MATLAB", "https://img.shields.io/badge/MATLAB-0076A8.svg?logo=matlab&logoColor=white"),
    "clojure": ("Clojure", "https://img.shields.io/badge/Clojure-5881D8.svg?logo=clojure&logoColor=white"),

    "bash": ("Bash", "https://img.shields.io/badge/Bash-121011.svg?logo=gnu-bash&logoColor=white"),
    "shell": ("Shell", "https://img.shields.io/badge/Shell-121011.svg?logo=gnu-bash&logoColor=white"),
    "powershell": ("PowerShell", "https://img.shields.io/badge/PowerShell-012456.svg?logo=powershell&logoColor=white"),

    "sql": ("SQL", "https://img.shields.io/badge/SQL-4479A1.svg?logo=postgresql&logoColor=white"),
    "plsql": ("PL/SQL", "https://img.shields.io/badge/PLSQL-F80000.svg?logo=oracle&logoColor=white"),
    "jpql": ("JPQL", "https://img.shields.io/badge/JPQL-FF2D20.svg?logo=java&logoColor=white"),
    "graphql": ("GraphQL", "https://img.shields.io/badge/GraphQL-E10098.svg?logo=graphql&logoColor=white"),
    "sparql": ("SPARQL", "https://img.shields.io/badge/SPARQL-005A9C.svg?logo=w3c&logoColor=white"),

    "html": ("HTML", "https://img.shields.io/badge/HTML-E34F26.svg?logo=html5&logoColor=white"),
    "css": ("CSS", "https://img.shields.io/badge/CSS-1572B6.svg?logo=css3&logoColor=white"),
    "xml": ("XML", "https://img.shields.io/badge/XML-0060AC.svg?logo=xml&logoColor=white"),
    "json": ("JSON", "https://img.shields.io/badge/JSON-000000.svg?logo=json&logoColor=white"),
    "yaml": ("YAML", "https://img.shields.io/badge/YAML-000000.svg?logo=yaml&logoColor=white"),
    "toml": ("TOML", "https://img.shields.io/badge/TOML-9C4121.svg?logo=toml&logoColor=white"),
    "ini": ("INI", "https://img.shields.io/badge/INI-5B5B5B.svg?logo=windows-terminal&logoColor=white"),

    "lua": ("Lua", "https://img.shields.io/badge/Lua-2C2D72.svg?logo=lua&logoColor=white"),
    "latex": ("LaTeX", "https://img.shields.io/badge/LaTeX-008080.svg?logo=latex&logoColor=white"),
    "markdown": ("Markdown", "https://img.shields.io/badge/Markdown-000000.svg?logo=markdown&logoColor=white"),
    "rst": ("reStructuredText", "https://img.shields.io/badge/reStructuredText-3A6EA5.svg?logo=python&logoColor=white"),

    "verilog": ("Verilog", "https://img.shields.io/badge/Verilog-4D4D4D.svg?logo=verilog&logoColor=white"),
    "vhdl": ("VHDL", "https://img.shields.io/badge/VHDL-0073A6.svg?logo=vhdl&logoColor=white"),
    "prolog": ("Prolog", "https://img.shields.io/badge/Prolog-742F9E.svg?logo=prolog&logoColor=white"),
    "ada": ("Ada", "https://img.shields.io/badge/Ada-002B36.svg?logo=ada&logoColor=white"),
    "lisp": ("Lisp", "https://img.shields.io/badge/Lisp-3FB68B.svg?logo=lisp&logoColor=white"),
    "ocaml": ("OCaml", "https://img.shields.io/badge/OCaml-EC6813.svg?logo=ocaml&logoColor=white"),
    }

    FRAMEWORK_BADGES = {

    "react": ("React", "https://img.shields.io/badge/React-20232a.svg?logo=react&logoColor=%2361DAFB"),
    "angular": ("Angular", "https://img.shields.io/badge/Angular-DD0031.svg?logo=angular&logoColor=white"),
    "vue": ("Vue.js", "https://img.shields.io/badge/Vue.js-4FC08D.svg?logo=vue.js&logoColor=white"),
    "nextjs": ("Next.js", "https://img.shields.io/badge/Next.js-000000.svg?logo=next.js&logoColor=white"),
    "svelte": ("Svelte", "https://img.shields.io/badge/Svelte-FF3E00.svg?logo=svelte&logoColor=white"),
    "bootstrap": ("Bootstrap", "https://img.shields.io/badge/Bootstrap-7952B3.svg?logo=bootstrap&logoColor=white"),
    "tailwind": ("Tailwind CSS", "https://img.shields.io/badge/TailwindCSS-06B6D4.svg?logo=tailwindcss&logoColor=white"),

    "spring": ("Spring", "https://img.shields.io/badge/Spring-6DB33F.svg?logo=spring&logoColor=white"),
    "django": ("Django", "https://img.shields.io/badge/Django-092E20.svg?logo=django&logoColor=white"),
    "flask": ("Flask", "https://img.shields.io/badge/Flask-000000.svg?logo=flask&logoColor=white"),
    "fastapi": ("FastAPI", "https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white"),
    "express": ("Express", "https://img.shields.io/badge/Express.js-000000.svg?logo=express&logoColor=white"),
    "laravel": ("Laravel", "https://img.shields.io/badge/Laravel-FF2D20.svg?logo=laravel&logoColor=white"),
    "nodejs": ("Node.js", "https://img.shields.io/badge/Node.js-339933.svg?logo=node.js&logoColor=white"),
    "dotnet": (".NET", "https://img.shields.io/badge/.NET-512BD4.svg?logo=dotnet&logoColor=white"),
    "ruby_on_rails": ("Ruby on Rails", "https://img.shields.io/badge/Rails-CC0000.svg?logo=rubyonrails&logoColor=white"),

    "numpy": ("NumPy", "https://img.shields.io/badge/Numpy-013243.svg?logo=numpy&logoColor=white"),
    "pandas": ("Pandas", "https://img.shields.io/badge/Pandas-150458.svg?logo=pandas&logoColor=white"),
    "matplotlib": ("Matplotlib", "https://img.shields.io/badge/Matplotlib-11557C.svg?logo=python&logoColor=white"),
    "scikit_learn": ("scikit-learn", "https://img.shields.io/badge/scikit--learn-F7931E.svg?logo=scikit-learn&logoColor=white"),
    "tensorflow": ("TensorFlow", "https://img.shields.io/badge/TensorFlow-FF6F00.svg?logo=tensorflow&logoColor=white"),
    "pytorch": ("PyTorch", "https://img.shields.io/badge/PyTorch-EE4C2C.svg?logo=pytorch&logoColor=white"),
    "keras": ("Keras", "https://img.shields.io/badge/Keras-D00000.svg?logo=keras&logoColor=white"),
    "opencv": ("OpenCV", "https://img.shields.io/badge/OpenCV-5C3EE8.svg?logo=opencv&logoColor=white"),
    "xgboost": ("XGBoost", "https://img.shields.io/badge/XGBoost-AA0000.svg?logo=xgboost&logoColor=white"),

    "docker": ("Docker", "https://img.shields.io/badge/Docker-2496ED.svg?logo=docker&logoColor=white"),
    "kubernetes": ("Kubernetes", "https://img.shields.io/badge/Kubernetes-326CE5.svg?logo=kubernetes&logoColor=white"),
    "jenkins": ("Jenkins", "https://img.shields.io/badge/Jenkins-D24939.svg?logo=jenkins&logoColor=white"),
    "ansible": ("Ansible", "https://img.shields.io/badge/Ansible-EE0000.svg?logo=ansible&logoColor=white"),
    "terraform": ("Terraform", "https://img.shields.io/badge/Terraform-623CE4.svg?logo=terraform&logoColor=white"),

    "pytest": ("PyTest", "https://img.shields.io/badge/Pytest-0A9EDC.svg?logo=pytest&logoColor=white"),
    "junit": ("JUnit", "https://custom-icon-badges.demolab.com/badge/JUnit-25A162.svg?logo=check-circle&logoColor=white"),
    "selenium": ("Selenium", "https://img.shields.io/badge/Selenium-43B02A.svg?logo=selenium&logoColor=white"),
    "cypress": ("Cypress", "https://img.shields.io/badge/Cypress-17202C.svg?logo=cypress&logoColor=white"),

    "wordpress": ("Wordpress", "https://img.shields.io/badge/Wordpress-21759B.svg?logo=wordpress&logoColor=white"),
    "drupal": ("Drupal", "https://img.shields.io/badge/Drupal-0678BE.svg?logo=drupal&logoColor=white"),
    "joomla": ("Joomla", "https://img.shields.io/badge/Joomla-FC8F30.svg?logo=joomla&logoColor=white"),

    "flutter": ("Flutter", "https://img.shields.io/badge/Flutter-02569B.svg?logo=flutter&logoColor=white"),
    "react_native": ("React Native", "https://img.shields.io/badge/React_Native-20232a.svg?logo=react&logoColor=%2361DAFB"),
    "android": ("Android", "https://img.shields.io/badge/Android-3DDC84.svg?logo=android&logoColor=white"),
    }

    DB_BADGES = {
    "oracle": ("Oracle", "https://img.shields.io/badge/Oracle-F80000.svg?logo=oracle&logoColor=white"),
    "postgres": ("Postgres", "https://img.shields.io/badge/Postgres-316192.svg?logo=postgresql&logoColor=white"),
    "postgresql": ("PostgreSQL", "https://img.shields.io/badge/PostgreSQL-316192.svg?logo=postgresql&logoColor=white"),
    "mysql": ("MySQL", "https://img.shields.io/badge/MySQL-4479A1.svg?logo=mysql&logoColor=white"),
    "sqlite": ("SQLite", "https://img.shields.io/badge/SQLite-003B57.svg?logo=sqlite&logoColor=white"),
    "mariadb": ("MariaDB", "https://img.shields.io/badge/MariaDB-003545.svg?logo=mariadb&logoColor=white"),
    "mssql": ("MS SQL Server", "https://img.shields.io/badge/MS_SQL_Server-CC2927.svg?logo=microsoft-sql-server&logoColor=white"),
    "firebird": ("Firebird", "https://img.shields.io/badge/Firebird-E10000.svg?logo=firebird&logoColor=white"),
    "db2": ("IBM Db2", "https://img.shields.io/badge/IBM_Db2-052FAD.svg?logo=ibm&logoColor=white"),

    "mongodb": ("MongoDB", "https://img.shields.io/badge/MongoDB-47A248.svg?logo=mongodb&logoColor=white"),
    "cassandra": ("Cassandra", "https://img.shields.io/badge/Apache_Cassandra-1287B1.svg?logo=apache-cassandra&logoColor=white"),
    "couchdb": ("CouchDB", "https://img.shields.io/badge/CouchDB-E42528.svg?logo=apache-couchdb&logoColor=white"),
    "dynamodb": ("DynamoDB", "https://img.shields.io/badge/DynamoDB-4053D6.svg?logo=amazon-dynamodb&logoColor=white"),
    "redis": ("Redis", "https://img.shields.io/badge/Redis-DC382D.svg?logo=redis&logoColor=white"),
    "neo4j": ("Neo4j", "https://img.shields.io/badge/Neo4j-008CC1.svg?logo=neo4j&logoColor=white"),
    "arangodb": ("ArangoDB", "https://img.shields.io/badge/ArangoDB-DDE072.svg?logo=arangodb&logoColor=black"),
    "couchbase": ("Couchbase", "https://img.shields.io/badge/Couchbase-EA2328.svg?logo=couchbase&logoColor=white"),
    "elasticsearch": ("Elasticsearch", "https://img.shields.io/badge/Elasticsearch-005571.svg?logo=elasticsearch&logoColor=white"),

    "supabase": ("Supabase", "https://img.shields.io/badge/Supabase-3ECF8E.svg?logo=supabase&logoColor=white"),
    "firebase": ("Firebase", "https://img.shields.io/badge/Firebase-FFCA28.svg?logo=firebase&logoColor=black"),
    "aws_rds": ("AWS RDS", "https://img.shields.io/badge/AWS_RDS-527FFF.svg?logo=amazon-aws&logoColor=white"),
    "aws_aurora": ("AWS Aurora", "https://img.shields.io/badge/AWS_Aurora-FF9900.svg?logo=amazon-aws&logoColor=white"),
    "google_bigquery": ("Google BigQuery", "https://img.shields.io/badge/BigQuery-669DF6.svg?logo=google-cloud&logoColor=white"),
    "azure_sql": ("Azure SQL", "https://img.shields.io/badge/Azure_SQL-0078D4.svg?logo=microsoft-azure&logoColor=white"),
    "snowflake": ("Snowflake", "https://img.shields.io/badge/Snowflake-29B5E8.svg?logo=snowflake&logoColor=white"),

    "redshift": ("Amazon Redshift", "https://img.shields.io/badge/Redshift-8C4FFF.svg?logo=amazon-redshift&logoColor=white"),
    "bigquery": ("BigQuery", "https://img.shields.io/badge/BigQuery-4285F4.svg?logo=google-cloud&logoColor=white"),
    "clickhouse": ("ClickHouse", "https://img.shields.io/badge/ClickHouse-FFCC01.svg?logo=clickhouse&logoColor=black"),
    "duckdb": ("DuckDB", "https://img.shields.io/badge/DuckDB-FFF000.svg?logo=duckdb&logoColor=black"),

    "influxdb": ("InfluxDB", "https://img.shields.io/badge/InfluxDB-22ADF6.svg?logo=influxdb&logoColor=white"),
    "timescaledb": ("TimescaleDB", "https://img.shields.io/badge/TimescaleDB-FDB515.svg?logo=timescaledb&logoColor=black"),
    "prometheus": ("Prometheus", "https://img.shields.io/badge/Prometheus-E6522C.svg?logo=prometheus&logoColor=white"),

    "janusgraph": ("JanusGraph", "https://img.shields.io/badge/JanusGraph-1A1A1A.svg?logo=apache&logoColor=white"),
    "solr": ("Apache Solr", "https://img.shields.io/badge/Solr-D9411E.svg?logo=apache-solr&logoColor=white"),

    "realm": ("Realm", "https://img.shields.io/badge/Realm-39477F.svg?logo=realm&logoColor=white"),
    "leveldb": ("LevelDB", "https://img.shields.io/badge/LevelDB-4479A1.svg?logo=google&logoColor=white"),
    "rocksdb": ("RocksDB", "https://img.shields.io/badge/RocksDB-2A5B84.svg?logo=rocksdb&logoColor=white"),
    }

    DEVELOPMENT_TOOLS_BADGES = {

    "git": ("Git", "https://img.shields.io/badge/Git-F05032.svg?logo=git&logoColor=white"),
    "github": ("GitHub", "https://img.shields.io/badge/GitHub-181717.svg?logo=github&logoColor=white"),
    "github_desktop": ("GitHub Desktop", "https://img.shields.io/badge/GitHub_Desktop-8034A9.svg?logo=github&logoColor=white"),
    "gitlab": ("GitLab", "https://img.shields.io/badge/GitLab-FCA121.svg?logo=gitlab&logoColor=white"),
    "bitbucket": ("Bitbucket", "https://img.shields.io/badge/Bitbucket-205081.svg?logo=bitbucket&logoColor=white"),

    "visual_studio_code": ("Visual Studio Code", "https://img.shields.io/badge/Visual%20Studio%20Code-0078d7.svg?logo=visual-studio-code&logoColor=white"),
    "vscode": ("VS Code", "https://img.shields.io/badge/VS_Code-007ACC.svg?logo=visual-studio-code&logoColor=white"),
    "visual_studio": ("Visual Studio", "https://img.shields.io/badge/Visual_Studio-5C2D91.svg?logo=visual-studio&logoColor=white"),
    "intellij_idea": ("IntelliJ IDEA", "https://img.shields.io/badge/IntelliJ_IDEA-000000.svg?logo=intellij-idea&logoColor=white"),
    "pycharm": ("PyCharm", "https://img.shields.io/badge/PyCharm-000000.svg?logo=pycharm&logoColor=white"),
    "eclipse": ("Eclipse", "https://img.shields.io/badge/Eclipse-2C2255.svg?logo=eclipse&logoColor=white"),
    "atom": ("Atom", "https://img.shields.io/badge/Atom-66595C.svg?logo=atom&logoColor=white"),
    "sublime_text": ("Sublime Text", "https://img.shields.io/badge/Sublime_Text-FF9800.svg?logo=sublime-text&logoColor=white"),

    "jupyter": ("Jupyter", "https://img.shields.io/badge/Jupyter-F37626.svg?logo=jupyter&logoColor=white"),
    "mathematica": ("Mathematica", "https://img.shields.io/badge/Mathematica-DD1100.svg?logo=wolfram-mathematica&logoColor=white"),
    "matlab": ("MATLAB", "https://img.shields.io/badge/MATLAB-0076A8.svg?logo=mathworks&logoColor=white"),
    "tableau": ("Tableau", "https://img.shields.io/badge/Tableau-E97627.svg?logo=tableau&logoColor=white"),
    "powerbi": ("Power BI", "https://img.shields.io/badge/Power_BI-F2C811.svg?logo=power-bi&logoColor=black"),
    "more_optimal": ("More Optimal", "https://img.shields.io/badge/More%20Optimal-1E1E1E.svg?logo=python&logoColor=white"),

    "rundeck": ("Rundeck", "https://img.shields.io/badge/Rundeck-E71E1E.svg?logo=rundeck&logoColor=white"),
    "jenkins": ("Jenkins", "https://img.shields.io/badge/Jenkins-D24939.svg?logo=jenkins&logoColor=white"),
    "docker": ("Docker", "https://img.shields.io/badge/Docker-2496ED.svg?logo=docker&logoColor=white"),
    "kubernetes": ("Kubernetes", "https://img.shields.io/badge/Kubernetes-326CE5.svg?logo=kubernetes&logoColor=white"),

    "wireshark": ("Wireshark", "https://img.shields.io/badge/Wireshark-1679A7.svg?logo=wireshark&logoColor=white"),
    "xss": ("XSS", "https://img.shields.io/badge/XSS-2B2B2B.svg?logo=hackthebox&logoColor=green"),
    "cryptography": ("Cryptography", "https://img.shields.io/badge/Cryptography-282C34.svg?logo=letsencrypt&logoColor=white"),
    "burp_suite": ("Burp Suite", "https://img.shields.io/badge/Burp_Suite-FF6633.svg?logo=burp-suite&logoColor=white"),
    "nmap": ("Nmap", "https://img.shields.io/badge/Nmap-4682B4.svg?logo=gnu-bash&logoColor=white"),
    "metasploit": ("Metasploit", "https://img.shields.io/badge/Metasploit-2B2B2B.svg?logo=metasploit&logoColor=blue"),

    "postman": ("Postman", "https://img.shields.io/badge/Postman-FF6C37.svg?logo=postman&logoColor=white"),
    "swagger": ("Swagger", "https://img.shields.io/badge/Swagger-85EA2D.svg?logo=swagger&logoColor=black"),

    "adobe": ("Adobe", "https://img.shields.io/badge/Adobe-FF0000.svg?logo=adobe&logoColor=white"),
    "figma": ("Figma", "https://img.shields.io/badge/Figma-F24E1E.svg?logo=figma&logoColor=white"),
    "canva": ("Canva", "https://img.shields.io/badge/Canva-00C4CC.svg?logo=canva&logoColor=white"),

    "microsoft_office": ("Microsoft Office", "https://img.shields.io/badge/Microsoft_Office-D83B01.svg?logo=microsoft-office&logoColor=white"),
    "word": ("Microsoft Word", "https://img.shields.io/badge/Word-2B579A.svg?logo=microsoft-word&logoColor=white"),
    "excel": ("Microsoft Excel", "https://img.shields.io/badge/Excel-217346.svg?logo=microsoft-excel&logoColor=white"),
    "powerpoint": ("Microsoft PowerPoint", "https://img.shields.io/badge/PowerPoint-B7472A.svg?logo=microsoft-powerpoint&logoColor=white"),
    "outlook": ("Microsoft Outlook", "https://img.shields.io/badge/Outlook-0078D4.svg?logo=microsoft-outlook&logoColor=white"),
    "access": ("Microsoft Access", "https://img.shields.io/badge/Access-A4373A.svg?logo=microsoft-access&logoColor=white"),
    "onenote": ("OneNote", "https://img.shields.io/badge/OneNote-7719AA.svg?logo=microsoft-onenote&logoColor=white"),
    "teams": ("Microsoft Teams", "https://img.shields.io/badge/Teams-6264A7.svg?logo=microsoft-teams&logoColor=white"),
    "sharepoint": ("SharePoint", "https://img.shields.io/badge/SharePoint-0078D4.svg?logo=microsoft-sharepoint&logoColor=white"),
    "onedrive": ("OneDrive", "https://img.shields.io/badge/OneDrive-0078D4.svg?logo=microsoft-onedrive&logoColor=white"),
}


    langs_found = []
    frameworks_found = []
    dbs_found = []
    devtools_found = []

    skills_list = data.get("skills", []) or []

    def norm(s):
        return re.sub(r"[^\w\+\-\#\.]", " ", s.lower()).strip()

    for s in skills_list:
        s_raw = s or ""
        s_norm = norm(s_raw)

        # exact/substring match against language keys
        for key in LANG_BADGES:
            if key in s_norm.split() or key == s_norm or key in s_norm:
                if LANG_BADGES[key] not in langs_found:
                    langs_found.append(LANG_BADGES[key])

        for key in FRAMEWORK_BADGES:
            if key in s_norm.split() or key == s_norm or key in s_norm:
                if FRAMEWORK_BADGES[key] not in frameworks_found:
                    frameworks_found.append(FRAMEWORK_BADGES[key])

        for key in DB_BADGES:
            if key in s_norm.split() or key == s_norm or key in s_norm:
                if DB_BADGES[key] not in dbs_found:
                    dbs_found.append(DB_BADGES[key])

        for key in DEVELOPMENT_TOOLS_BADGES:
            if key in s_norm.split() or key == s_norm or key in s_norm:
                if DEVELOPMENT_TOOLS_BADGES[key] not in devtools_found:
                    devtools_found.append(DEVELOPMENT_TOOLS_BADGES[key])

    # Programming and Markup Languages 
    if langs_found:
        md.append('  <h3>👨‍💻 Programming and Markup Languages</h3>')
        md.append('  <p>')
        md.append('      <p>')
        for label, badge in langs_found:
            lang_q = urllib.parse.quote(label)
            if github_username:
                 href = f"https://github.com/search?q=user%3A{github_username}+language%3A{lang_q}"
                 md.append(f'      <a href="{href}"><img alt="{label}" src="{badge}"></a>')
            else:
                 md.append(f'      <img alt="{label}" src="{badge}">')
        md.append('  </p>')
        md.append('  </p>')

    # Frameworks and Libraries
    if frameworks_found:
        md.append('')
        md.append('  <h3>🧰 Frameworks and Libraries</h3>')
        md.append('  <p>')
        for label, src in frameworks_found:
            md.append(f'      <img alt="{label}" src="{src}">')
        md.append('  </p>')

    # Databases
    if dbs_found:
        md.append('')
        md.append('  <h3>🗄️ Databases</h3>')
        md.append('  <p>')
        for label, src in dbs_found:
            md.append(f'      <img alt="{label}" src="{src}">')
        md.append('  </p>')

    # Development Tools and Others
    if devtools_found:
        md.append('')
        md.append('  <h3>💡 Development Tools and Others</h3>')
        md.append('  <p>')
        for label, src in devtools_found:
            md.append(f'      <img alt="{label}" src="{src}">')
        md.append('  </p>')

    md.append('</details>\n')

    # TO DO: GITHUB PROJECTS
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
        md.append('</details>\n')

   # FOOTER
    md.append("---\n")
    # Include footer with link to the tool written in italics
    md.append('[![Generated with cv-to-github-readme](https://img.shields.io/badge/Generated%20with-cv--to--github--readme-blue?logo=github)](https://github.com/pablofazio02/cv-to-github-readme)')
    return "\n".join(md)
