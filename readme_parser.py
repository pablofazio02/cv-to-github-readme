"""
================================
README Parser - Principal Module

Author: Pablo Fazio Arrabal
================================
"""

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

    # occupation detection: searching by keywords
    occupation = ""
    occ_keywords = [
        # English
        "student", "intern", "phd", "ph.d", "postdoc", "post-doctoral", "professor", "lecturer",
        "researcher", "scientist", "data scientist", "data analyst", "software engineer",
        "engineer", "developer", "full[- ]stack", "frontend", "backend", "machine learning",
        "ml engineer", "research assistant", "manager", "consultant", "analyst", "architect",
    ]

   # searching first lines for occupation
    for ln in lines[:8]:
        lnl = ln.lower()
        for kw in occ_keywords:
            if re.search(r"\b" + kw + r"\b", lnl, re.IGNORECASE):
                occupation = ln.strip()
                break
        if occupation:
            break

    # fallback: searching by keywords in the entire text
    if not occupation:
        esc_keys = [re.escape(k) for k in occ_keywords]
        key_pat = r"|".join(esc_keys)
        pattern = rf"((?:[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\.\-']+\s?){{0,3}}(?:{key_pat})(?:\s?[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\.\-']+){{0,3}})"
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            occupation = m.group(1).strip()

    # normalize common formats
    if occupation:
        occupation = re.sub(r"\s{2,}", " ", occupation)
        occupation = re.sub(r"\bph[\.\s]?d\b", "PhD", occupation, flags=re.IGNORECASE)
        occupation = occupation.strip()

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
    if website:
        icons.append(f'<a href="{website}"><img width="40px" src="https://img.icons8.com/ios-filled/50/000000/portfolio.png" alt="Personal website"></a>')

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
        md.append('</details>\n')

   # FOOTER
    md.append("---\n")
    # Include footer with link to the tool written in italics
    md.append('[![Generated with cv-to-github-readme](https://img.shields.io/badge/Generated%20with-cv--to--github--readme-blue?logo=github)](https://github.com/pablofazio02/cv-to-github-readme)')
    return "\n".join(md)
