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

import os
import re
import json
import urllib.parse
from typing import Any, TypedDict, Iterable, List, Dict, Tuple

# --- Types -------------------------------------------------------------------
class CVData(TypedDict, total=False):
    """TypedDict describing extracted CV data returned by extract_data_from_pdf."""
    first_name: str
    last_name: str
    occupation: str
    email: str
    linkedin: str
    github: str
    website: str
    profiles: dict[str, str]
    skills: list[str]

from src.badges import (
    LANG_BADGES,
    FRAMEWORK_BADGES,
    DB_BADGES,
    DEVELOPMENT_TOOLS_BADGES,
    _COMBINED_BADGE_KEYS,
)

Badge = Tuple[str, str]  # (label, badge_url)

# --- PDF reading / text extraction ------------------------------------------
def _read_pdf_text(path: str) -> str:
    """Return the full text of a PDF file.

    Tries pdfplumber first, falls back to PyPDF2. Raises RuntimeError if neither works.
    """
    if not path:
        raise ValueError("path must be provided")
    # try pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            pages: list[str] = [p.extract_text() or "" for p in pdf.pages]
        result = "\n".join(pages)
        return result
    except Exception:
        pass

    # fallback PyPDF2
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(path)
        pages_text: list[str] = []
        for p in reader.pages:
            try:
                pages_text.append(p.extract_text() or "")
            except Exception:
                pages_text.append("")
        return "\n".join(pages_text)
    except Exception as exc:
        raise RuntimeError("Could not read the PDF. Please install 'pdfplumber' or 'PyPDF2'.") from exc

# --- Small helpers for extraction -------------------------------------------
def _remove_name_tokens(s: str, name_tokens: Iterable[str]) -> str:
    """Remove occurrences of name tokens from s to help occupation detection."""
    if not s:
        return ""
    res: str = s
    for nt in sorted((nt for nt in name_tokens if nt), key=len, reverse=True):
        res = re.sub(rf"\b{re.escape(nt)}\b", " ", res, flags=re.IGNORECASE)
    res = re.sub(r"\s+", " ", res).strip()
    return res


def _find_name(lines: list[str]) -> tuple[str, str]:
    """Return (first_name, last_name) or ('','') if not found."""
    first_name: str = ""
    last_name: str = ""
    name_pattern = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s\-\']+$")
    for ln in lines[:10]:
        if name_pattern.match(ln) and "@" not in ln and len(ln.split()) >= 2:
            parts = ln.split()
            first_name = parts[0]
            last_name = " ".join(parts[1:])
            break
    return first_name, last_name


def _detect_profiles(text: str) -> dict[str, str]:
    """Detect common social/profile URLs and return a mapping service->url."""
    profiles: dict[str, str] = {}
    host_patterns: dict[str, str] = {
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
        "dialnet": r"https?://dialnet\.unirioja\.es/servlet/articulo\?codigo=([0-9]+)/?",
        "scopus": r"https?://www\.scopus\.com/authid/detail\.uri\?authorId=([0-9]+)/?",
        "researchgate": r"https?://(?:www\.)?researchgate\.net/profile/([A-Za-z0-9\-_]+)/?",
        "academia": r"https?://(?:www\.)?academia\.edu/([A-Za-z0-9\-_]+)/?",
    }
    for key, pat in host_patterns.items():
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            handle = m.group(1).rstrip("/")
            base_map: dict[str, str] = {
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
                "academia": "https://www.academia.edu/",
            }
            base = base_map.get(key, "")
            profiles[key] = base + handle
    # fallback: detect generic website urls and attach as 'website'
    if "website" not in profiles:
        all_urls = re.findall(r"https?://[^\s\)\]\>]+", text)
        known_hosts = (
            "github.com", "linkedin.com", "instagram.com", "x.com", "twitter.com",
            "gitlab.com", "facebook.com", "tiktok.com", "stackoverflow.com", "medium.com",
            "dev.to", "kaggle.com", "codepen.io", "leetcode.com", "hackerrank.com",
            "bitbucket.org", "dialnet.unirioja.es", "scholar.google.com", "arxiv.org",
            "orcid.org", "scopus.com", "researchgate.net", "academia.edu"
        )
        for u in all_urls:
            u_clean = u.rstrip(".,;)")
            if not any(h in u_clean for h in known_hosts):
                profiles["website"] = u_clean
                break
    return profiles


def detect_badge_keys_from_text(text: str) -> list[str]:
    """Return ordered list of badge keys found in text (handles symbols like C++/C#)."""
    found: list[str] = []
    if not text:
        return found
    t = text.lower()
    tokens: list[str] = re.findall(r"[A-Za-z0-9\+\#\.\-]{2,}", t)
    for key in _COMBINED_BADGE_KEYS:
        k = key.lower()
        pat = re.compile(r'(?<![A-Za-z0-9])' + re.escape(k) + r'(?![A-Za-z0-9])', re.IGNORECASE)
        matched = False
        if pat.search(t):
            matched = True
        else:
            for tok in tokens:
                if tok == k:
                    matched = True
                    break
        if matched and key not in found:
            found.append(key)
    return found

# --- Main extraction function -----------------------------------------------
def extract_data_from_pdf(path: str) -> CVData:
    """Extract personal and skill information from a CV PDF file.

    Args:
        path: Path to the PDF file.

    Returns:
        CVData TypedDict with extracted fields.
    """
    if not path:
        raise ValueError("path must be provided")
    text: str = _read_pdf_text(path)
    lines: list[str] = [ln.strip() for ln in text.splitlines() if ln.strip()]

    first_name, last_name = _find_name(lines)

    # occupation detection: uses heuristics from the original implementation
    occupation: str = ""
    occ_keywords: list[str] = [
        "mathematician", "computer scientist", "student", "intern", "phd", "ph.d", "postdoc",
        "post-doctoral", "professor", "lecturer", "researcher", "scientist", "data scientist",
        "data analyst", "software engineer", "engineer", "developer", "full-stack", "full stack",
        "frontend", "front-end", "backend", "back-end", "machine learning", "ml engineer",
        "research assistant", "manager", "consultant", "analyst", "architect", "teacher",
        "assistant", "director", "engineer-in-training"
    ]
    # build set of name tokens to exclude from occupation detection
    name_tokens: set[str] = set()
    if first_name:
        name_tokens.update([t.lower() for t in re.findall(r"\w+", first_name)])
    if last_name:
        name_tokens.update([t.lower() for t in re.findall(r"\w+", last_name)])

    # scan a few top lines first
    for ln in lines[:6]:
        cleaned = _remove_name_tokens(ln, name_tokens)
        if len(cleaned) < 3:
            continue
        low = cleaned.lower()
        found_kw: list[str] = [kw for kw in occ_keywords if re.search(r"\b" + re.escape(kw) + r"\b", low, re.IGNORECASE)]
        if found_kw:
            occupation = cleaned
            break
        compact = re.sub(r"[^a-z0-9]", "", low)
        matches: list[str] = []
        for kw in occ_keywords:
            kw_compact = re.sub(r"[^a-z0-9]", "", kw.lower())
            if kw_compact and kw_compact in compact:
                matches.append(kw)
        if matches:
            seen: list[str] = []
            for m in matches:
                if m not in seen:
                    seen.append(m)
            occupation = " and ".join([m.title() for m in seen])
            break

    # fallback occupation scan
    if not occupation:
        for seg in re.split(r"[.\n\r;]+", text):
            seg = seg.strip()
            if not seg or len(seg) < 3:
                continue
            cleaned = _remove_name_tokens(seg, name_tokens)
            if len(cleaned) < 3:
                continue
            low = cleaned.lower()
            for kw in occ_keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", low, re.IGNORECASE):
                    occupation = cleaned
                    break
            if occupation:
                break

    # contacts
    email_match = re.search(r"[ÑA-Zña-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}", text)
    email: str = email_match.group(0) if email_match else ""

    linkedin_match = re.search(r"(https?://(?:www\.)?linkedin\.com/in/[\w\-.%]+)/?", text, re.IGNORECASE)
    linkedin: str = linkedin_match.group(1) if linkedin_match else ""
    if not linkedin:
        m = re.search(r"linkedin\.com/in/([\w\-.%]+)", text, re.IGNORECASE)
        if m:
            linkedin = "https://www.linkedin.com/in/" + m.group(1)

    github_match = re.search(r"(https?://(?:www\.)?github\.com/[\w\-.%]+)/?", text, re.IGNORECASE)
    github: str = github_match.group(1) if github_match else ""
    if not github:
        m = re.search(r"github\.com/([\w\-.%]+)", text, re.IGNORECASE)
        if m:
            github = "https://github.com/" + m.group(1)

    website_match = re.search(r"(https?://[A-Za-z0-9\-_]+\.github\.io)/?", text, re.IGNORECASE)
    website: str = website_match.group(1) if website_match else ""
    if not website:
        m = re.search(r"([A-Za-z0-9\-_]+\.github\.io)/?", text, re.IGNORECASE)
        if m:
            website = "https://" + m.group(1)

    profiles: dict[str, str] = _detect_profiles(text)

    # detect badge keys (skills) from full text
    skills: list[str] = detect_badge_keys_from_text(text)

    data: CVData = {
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

# --- README generation helpers ----------------------------------------------
def _render_social_icons(data: CVData) -> list[str]:
    """Render social icons HTML block and return markdown lines."""
    md: list[str] = []
    icons: list[str] = []
    email = data.get("email", "") or ""
    linkedin = data.get("linkedin", "") or ""
    github = data.get("github", "") or ""
    profiles = data.get("profiles", {}) or {}

    if email:
        icons.append(f'<a href="mailto:{email}"><img width="40px" src="https://img.icons8.com/color/48/000000/gmail--v1.png"></a>')
    if linkedin:
        icons.append(f'<a href="{linkedin}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg"></a>')
    if github:
        icons.append(f'<a href="{github}"><img width="40px" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/github/github-original.svg"></a>')
    # other profiles (preserve previous mapping)
    profile_icon_map: dict[str, str] = {
        "instagram": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/instagram/instagram-original.svg",
        "x": "https://img.icons8.com/ios-filled/50/000000/twitter--v1.png",
        "twitter": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/twitter/twitter-original.svg",
        "gitlab": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/gitlab/gitlab-original.svg",
        "facebook": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/facebook/facebook-original.svg",
        "tiktok": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/tiktok/tiktok-original.svg",
        "stackoverflow": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/stackoverflow/stackoverflow-original.svg",
        "medium": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/medium/medium-original.svg",
        "devto": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/devto/devto-original.svg",
        "kaggle": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/kaggle/kaggle-original.svg",
        "codepen": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/codepen/codepen-original.svg",
        "leetcode": "https://img.icons8.com/ios-filled/50/000000/leetcode.png",
        "hackerrank": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/hackerrank/hackerrank-original.svg",
        "bitbucket": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/bitbucket/bitbucket-original.svg",
        "google_scholar": "https://img.icons8.com/ios-filled/50/000000/google-scholar.png",
        "arxiv": "https://upload.wikimedia.org/wikipedia/commons/4/45/ArXiv_logo.svg",
        "orcid": "https://orcid.org/sites/default/files/images/orcid_16x16.png",
        "dialnet": "https://dialnet.unirioja.es/images/dialnet-logo.png",
        "scopus": "https://www.elsevier.com/__data/assets/image/0007/69401/scopus-logo.png",
        "researchgate": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/researchgate/researchgate-original.svg",
        "academia": "https://upload.wikimedia.org/wikipedia/commons/1/12/Academia.edu_logo.png",
    }
    for key, url in profiles.items():
        if key in profile_icon_map:
            icons.append(f'<a href="{url}"><img width="40px" src="{profile_icon_map[key]}"></a>')

    if icons:
        spacer = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        md.append("<!-- Social icons section -->")
        md.append('<p align="center">')
        md.append(spacer.join(icons))
        md.append('</p>\n')
    return md


def _render_website_highlight(website: str) -> list[str]:
    """Return markdown lines highlighting personal website (if provided)."""
    md: list[str] = []
    if not website:
        return md
    display_domain = re.sub(r"^https?://(www\.)?", "", website).rstrip("/")
    label = urllib.parse.quote("Personal Website")
    badge = f"https://img.shields.io/badge/{label}-{urllib.parse.quote(display_domain)}-2b9348?logo=google-chrome&logoColor=white"
    md.append("")
    md.append("<!-- Personal website highlight -->")
    md.append('<p align="center">')
    md.append(f'  <a href="{website}"><img src="{badge}" alt="Visit website" /></a>')
    md.append('</p>\n')
    return md


def _collect_skill_badges(keys: Iterable[str]) -> tuple[list[Badge], list[Badge], list[Badge], list[Badge]]:
    """Resolve skill keys into badge tuples grouped by category."""
    langs_found: list[Badge] = []
    frameworks_found: list[Badge] = []
    dbs_found: list[Badge] = []
    devtools_found: list[Badge] = []
    for k in keys:
        kk = k.lower()
        if kk in LANG_BADGES:
            langs_found.append(LANG_BADGES[kk])
        elif kk in FRAMEWORK_BADGES:
            frameworks_found.append(FRAMEWORK_BADGES[kk])
        elif kk in DB_BADGES:
            dbs_found.append(DB_BADGES[kk])
        elif kk in DEVELOPMENT_TOOLS_BADGES:
            devtools_found.append(DEVELOPMENT_TOOLS_BADGES[kk])
    return langs_found, frameworks_found, dbs_found, devtools_found


def _render_skills_section(data: CVData, github_username: str | None) -> list[str]:
    """Render skills details section and return markdown lines."""
    md: list[str] = []
    md.append('<details open>')
    md.append('<summary><h2>🛠️ Skills</h2></summary>')
    skills_keys = data.get("skills", []) or []
    langs_found, frameworks_found, dbs_found, devtools_found = _collect_skill_badges(skills_keys)

    if langs_found:
        md.append('  <h3>👨‍💻 Programming and Markup Languages</h3>')
        md.append('  <p>')
        md.append('      <p>')
        for label, badge in langs_found:
            lang_q = urllib.parse.quote(label)
            if github_username:
                href = f"https://github.com/search?q=user%3A{urllib.parse.quote(github_username)}+language%3A{lang_q}"
                md.append(f'      <a href="{href}"><img alt="{label}" src="{badge}"></a>')
            else:
                md.append(f'      <img alt="{label}" src="{badge}">')
        md.append('  </p>')
        md.append('  </p>')

    if frameworks_found:
        md.append('')
        md.append('  <h3>🧰 Frameworks and Libraries</h3>')
        md.append('  <p>')
        for label, src in frameworks_found:
            md.append(f'      <img alt="{label}" src="{src}">')
        md.append('  </p>')

    if dbs_found:
        md.append('')
        md.append('  <h3>🗄️ Databases</h3>')
        md.append('  <p>')
        for label, src in dbs_found:
            md.append(f'      <img alt="{label}" src="{src}">')
        md.append('  </p>')

    if devtools_found:
        md.append('')
        md.append('  <h3>💡 Development Tools and Others</h3>')
        md.append('  <p>')
        for label, src in devtools_found:
            md.append(f'      <img alt="{label}" src="{src}">')
        md.append('  </p>')

    md.append('</details>\n')
    return md


def _render_projects_section(github_username: str | None, langs_found: list[Badge]) -> list[str]:
    """Render GitHub Projects section using same external-card behavior as before."""
    md: list[str] = []
    if not github_username:
        return md
    md.append('<details open>')
    md.append('<summary><h2>📘 GitHub Projects</h2></summary>')
    md.append('<p>')

    top_repos: list[str] = []
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    try:
        from urllib.request import Request, urlopen
        api_url = f"https://api.github.com/users/{urllib.parse.quote(github_username)}/repos?per_page=100&type=owner"
        req = Request(api_url, headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "cv-to-github-readme"})
        if token:
            req.add_header("Authorization", f"token {token}")
        with urlopen(req, timeout=10) as resp:
            repos_raw = json.loads(resp.read().decode())
            repos_sorted = sorted(repos_raw, key=lambda r: r.get("stargazers_count", 0), reverse=True)
            for r in repos_sorted[:6]:
                if r.get("name"):
                    top_repos.append(r["name"])
    except Exception:
        top_repos = []

    if top_repos:
        md.append('<p align="center">')
        for repo in top_repos:
            repo_esc = urllib.parse.quote(repo)
            card_url = f"https://github-readme-stats.vercel.app/api/pin/?username={urllib.parse.quote(github_username)}&repo={repo_esc}&theme=transparent"
            repo_link = f"https://github.com/{urllib.parse.quote(github_username)}/{repo_esc}"
            md.append(f'  <a href="{repo_link}"><img src="{card_url}" alt="Repo {repo}" width="320" /></a>')
        md.append('</p>')
    else:
        if langs_found:
            md.append('<p align="center">')
            for label, badge in langs_found:
                lang_q = urllib.parse.quote(label)
                href = f"https://github.com/search?q=user%3A{urllib.parse.quote(github_username)}+language%3A{lang_q}&type=Repositories&s=stars&o=desc"
                md.append(f'  <a href="{href}"><img alt="{label}" src="{badge}" /></a>')
            md.append('</p>')

    md.append('</p>')
    md.append('</details>\n')
    return md


def _render_stats_section(github_username: str | None) -> list[str]:
    """Render the GitHub stats images (unchanged behavior)."""
    md: list[str] = []
    if not github_username:
        return md
    md.append('<details open>')
    md.append('<summary><h2>📊 GitHub Stats</h2></summary>')
    md.append('<p align="center">')
    md.append(f'    <img align="center" height=200 alt="{github_username}\'s Github Stats" src="https://github-readme-stats.vercel.app/api/?username={urllib.parse.quote(github_username)}" />')
    md.append('&nbsp;')
    md.append(f'    <img align="center" height=200 alt="{github_username}\'s Top Languages" src="https://github-readme-stats.vercel.app/api/top-langs/?username={urllib.parse.quote(github_username)}&langs_count=8&layout=compact" />')
    md.append('</p>')
    md.append('</details>\n')
    return md

# --- README generator (public) ----------------------------------------------
def generate_readme(data: CVData) -> str:
    """Generate README markdown string from extracted CV data.

    Args:
        data: CVData obtained from extract_data_from_pdf.

    Returns:
        A markdown string suitable for writing to a README file.
    """
    if not isinstance(data, dict):
        raise TypeError("data must be a dict-like CVData")

    fn: str = data.get("first_name", "") or ""
    ln: str = data.get("last_name", "") or ""
    full_name: str = (fn + " " + ln).strip() or "Name Surname"

    md_lines: list[str] = []
    md_lines.append(f'<h1 align="center">Hi 👋, I\'m {fn} </h1>')

    occ: str = data.get("occupation", "") or ""
    if occ:
        md_lines.append(f"<h3 align=\"center\">{occ}</h3>\n")

    # Social icons
    md_lines.extend(_render_social_icons(data))

    # website highlight
    website: str = data.get("website", "") or ""
    md_lines.extend(_render_website_highlight(website))

    # github username extraction
    github_username: str | None = None
    github_url: str = data.get("github", "") or ""
    if github_url:
        github_username = github_url.rstrip("/").split("/")[-1]

    # skills section
    md_lines.extend(_render_skills_section(data, github_username))

    # collect langs badges for projects fallback
    skills_keys: list[str] = data.get("skills", []) or []
    langs_found, _, _, _ = _collect_skill_badges(skills_keys)

    # projects
    md_lines.extend(_render_projects_section(github_username, langs_found))

    # stats
    md_lines.extend(_render_stats_section(github_username))

    # footer
    md_lines.append("---\n")
    md_lines.append('[![Generated with cv-to-github-readme](https://img.shields.io/badge/Generated%20with-cv--to--github--readme-blue?logo=github)](https://github.com/pablofazio02/cv-to-github-readme)')
    result = "\n".join(md_lines)
    return result
