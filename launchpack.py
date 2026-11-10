#!/usr/bin/env python3
"""LaunchPack v2: turn a product into launch posts for 100+ platforms.

Inputs (no API key, no LLM, pure rules):
  - a GitHub repo URL          launchpack.py https://github.com/you/repo
  - a local project folder     launchpack.py --folder path/to/project
  - a README file              launchpack.py --readme README.md
  - a plain paragraph          launchpack.py --text "MyApp is ..."
  - manual flags               --name X --tagline Y --features "a; b; c"

Outputs: one post per chosen platform, in BOTH Markdown (.md) and
plain text (.txt), written to the output folder. Facts come only from
what you gave it. Story gaps stay as [bracketed placeholders].
"""
import argparse, html, json, os, re, sys, urllib.request
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "LaunchPack/2.0"}
DEFAULT_TAGS = ["BuildInPublic", "OpenSource", "IndieHackers", "SaaS", "AI", "Productivity"]


def load_platforms():
    with open(os.path.join(HERE, "platforms.json"), encoding="utf-8") as f:
        return json.load(f)


def scrub(s):
    return s.replace("—", ", ").replace("–", "-")


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


# ---------- fact extraction ----------

def clean_md(md):
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    md = re.sub(r"\[!\[.*?\]\(.*?\)\]\(.*?\)", "", md)
    md = re.sub(r"!\[.*?\]\(.*?\)", "", md)
    return html.unescape(re.sub(r"<[^>]+>", "", md))


def facts_from_markdown(md, meta=None, fallback_name=""):
    meta = meta or {}
    text = clean_md(md)
    name = (meta.get("name") or fallback_name or "").strip()
    tagline = (meta.get("description") or "").strip()
    bullets, paras = [], []
    in_code = False
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not s or s.startswith("#"):
            continue
        if re.match(r"^[-*+] ", s):
            b = re.sub(r"[*_`]", "", re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s[2:])).strip()
            if 3 < len(b) < 160:
                bullets.append(b)
            continue
        p = re.sub(r"[*_`>]", "", re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)).strip()
        if len(p) > 40:
            paras.append(p)
    if name:
        variants = re.findall(r"\b" + re.escape(name) + r"\b", md, flags=re.I)
        cased = [v for v in variants if any(c.isupper() for c in v)]
        if cased:
            name = Counter(cased).most_common(1)[0][0]
    if not tagline:
        tagline = paras[0] if paras else ""
    desc = ""
    for p in paras:
        if p != tagline or not desc:
            desc = p
            break
    return {"name": name or "My Product", "tagline": tagline or desc,
            "desc": desc or tagline, "features": bullets[:6],
            "link": meta.get("html_url", ""), "topics": meta.get("topics", []),
            "lang": meta.get("language", "")}


def facts_from_github(url):
    m = re.search(r"github\.com[:/]([^/]+)/([^/#?]+)", url)
    if not m:
        sys.exit("Not a GitHub repo URL: " + url)
    owner, repo = m.group(1), m.group(2).removesuffix(".git")
    meta = {}
    try:
        meta = json.loads(fetch(f"https://api.github.com/repos/{owner}/{repo}"))
    except Exception as e:
        print(f"(repo metadata unavailable: {e})")
    readme = None
    for branch in ("main", "master"):
        for nm in ("README.md", "readme.md", "Readme.md"):
            try:
                readme = fetch(f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{nm}")
                break
            except Exception:
                pass
        if readme:
            break
    if readme is None:
        sys.exit("Could not fetch a README for " + url)
    d = facts_from_markdown(readme, meta, repo)
    d["link"] = meta.get("html_url") or url
    return d


def facts_from_folder(path):
    if not os.path.isdir(path):
        sys.exit("Not a folder: " + path)
    name = os.path.basename(os.path.abspath(path)).replace("-", " ").replace("_", " ").title()
    for nm in os.listdir(path):
        if nm.lower().startswith("readme"):
            with open(os.path.join(path, nm), encoding="utf-8", errors="replace") as f:
                d = facts_from_markdown(f.read(), {}, name)
            if d["name"] == "My Product":
                d["name"] = name
            return d
    d = {"name": name, "tagline": "", "desc": "", "features": [], "link": "", "topics": [], "lang": ""}
    pkg = os.path.join(path, "package.json")
    if os.path.exists(pkg):
        try:
            j = json.load(open(pkg, encoding="utf-8"))
            d["tagline"] = j.get("description", "")
            d["desc"] = d["tagline"]
        except Exception:
            pass
    if not d["tagline"]:
        d["tagline"] = "[one line: what " + name + " does]"
        d["desc"] = "[two or three lines about " + name + ": the problem it solves and who it is for]"
    return d


def facts_from_paragraph(text, name_hint=""):
    text = re.sub(r"\s+", " ", text).strip()
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 3]
    name = name_hint
    if not name and sents:
        m = re.match(r"^([A-Z][\w.-]*(?:\s[A-Z][\w.-]*)?)\s+(is|helps|lets|makes)\b", sents[0])
        if m:
            name = m.group(1)
    tagline = sents[0] if sents else text[:120]
    if name and tagline.lower().startswith(name.lower()):
        tagline = tagline
    cues = (" can ", " lets ", " helps ", " includes ", " features ", " supports ",
            " automatically ", " with ", " generates ", " turns ", " makes ")
    feats = []
    for s in sents[1:]:
        if any(c in " " + s.lower() + " " for c in cues) or s.lower().startswith(("it ", "you ")):
            f = re.sub(r"^(it|the app|the tool|this tool)\s+", "", s, flags=re.I).rstrip(".")
            feats.append(f[0].upper() + f[1:] if f else f)
    if not feats and len(text) > 60:
        m = re.search(r"\bwith\s+(.+)$", text, flags=re.I)
        if m:
            feats = [p.strip().rstrip(".") for p in re.split(r",| and ", m.group(1)) if len(p.strip()) > 3][:6]
    desc = " ".join(sents[:3]) if sents else text
    return {"name": name or "My Product", "tagline": tagline, "desc": desc,
            "features": feats[:6], "link": "", "topics": [], "lang": ""}


# ---------- post building ----------

def tag_str(d, n):
    if n <= 0:
        return ""
    pool = []
    for t in d.get("topics", []):
        pool.append("".join(w.capitalize() for w in re.split(r"[-_ ]", t) if w))
    pool += DEFAULT_TAGS
    seen, out = set(), []
    for t in pool:
        if t and t not in seen:
            seen.add(t)
            out.append("#" + t)
    return " ".join(out[:n])


def fit(body, limit, link=""):
    if not limit or len(body) <= limit:
        return body
    lines = body.split("\n")
    while len("\n".join(lines)) > limit:
        idx = max((i for i, l in enumerate(lines) if l.startswith("- ")), default=-1)
        if idx == -1:
            break
        lines.pop(idx)
    body = "\n".join(lines)
    if len(body) > limit:
        body = body[: limit - 3].rstrip() + "..."
    return body


RELAXED_FILLS = [
    ("[the problem, in one honest sentence]", "a problem I kept running into myself"),
    ("[name the one thing]", "anything you notice first"),
    ("[Two or three honest lines: the moment you decided this needed to exist.]",
     "I built it because I needed it myself, and people kept asking for the same thing."),
    ("[Quote from the founder, one or two lines.]", '"Built in the open, improved in public."'),
    ("[one specific thing you want feedback on]", "anything you notice first"),
]


def build_post(p, d, md=True, strict=True):
    name, tag, desc = d["name"], d["tagline"], d["desc"]
    feats = d["features"] or ["[add your top features]"]
    link = d["link"] or "[your link]"
    tags = tag_str(d, p["hashtags"])
    H = (lambda t: f"# {t}") if md else (lambda t: t.upper())
    B = (lambda t: f"**{t}**") if md else (lambda t: t)
    fl = "\n".join(f"- {f}" for f in feats)
    st = p["style"]
    if st == "listing":
        body = f"{H(name)}\n\n{B('Tagline:')} {tag}\n\n{desc}\n\n{B('What it does:')}\n{fl}\n\n{B('Link:')} {link}"
    elif st == "community":
        body = (f"{H('Launching ' + name)}\n\nHi everyone, I am the maker of {name}. {tag}\n\n"
                f"{desc}\n\nWhat is inside:\n{fl}\n\nI built it because [the problem, in one honest sentence]. "
                f"Feedback wanted most on: [name the one thing].\n\nTry it: {link}")
        if p["id"] == "hackernews":
            body = (f"Show HN: {name} - {tag}\n\n{desc}\n\nWhat is inside:\n{fl}\n\n"
                    f"I built it because [the problem, in one honest sentence]. Happy to answer questions.\n\n{link}")
    elif st == "short":
        body = f"Just launched {name}. {tag}\n\n{link}"
        if tags:
            body += "\n" + tags
    elif st == "social":
        body = (f"I just launched {name}.\n\n{tag}\n\n{desc}\n\nWhat you get:\n{fl}\n\n"
                f"It is live here: {link}\n\nTell me the one thing you would change first.")
        if tags:
            body += "\n\n" + tags
    elif st == "press":
        body = (f"{H(name + ': ' + tag)}\n\nFOR IMMEDIATE RELEASE\n\n{desc}\n\nKey features:\n{fl}\n\n"
                f"[Quote from the founder, one or two lines.]\n\nAvailability: available now at {link}\n\n"
                f"Media contact: [name and email]")
    elif st == "store":
        body = f"{H(name)}\n\n{tag}\n\n{desc}\n\nFEATURES\n{fl}\n\n[Support email]  [Privacy policy link]"
    else:  # full
        body = (f"{H(name + ': ' + tag)}\n\n[Two or three honest lines: the moment you decided this needed to exist.]\n\n"
                f"{desc}\n\nWhat is inside:\n{fl}\n\nWhere it stands: launched today. {link}\n\n"
                f"Try it, break it, and tell me what happened. I read every reply.")
        if tags:
            body += "\n\n" + tags
    if not strict:
        for a, b in RELAXED_FILLS:
            body = body.replace(a, b)
    return fit(scrub(body), p["limit"], link)


def generate(d, platforms, out, formats, strict=True):
    os.makedirs(out, exist_ok=True)
    made = []
    for p in platforms:
        if "md" in formats:
            open(os.path.join(out, p["id"] + ".md"), "w", encoding="utf-8").write(build_post(p, d, True, strict))
        if "txt" in formats:
            open(os.path.join(out, p["id"] + ".txt"), "w", encoding="utf-8").write(build_post(p, d, False, strict))
        made.append(p["id"])
    with open(os.path.join(out, "index.txt"), "w", encoding="utf-8") as f:
        f.write(f"LaunchPack v2 pack for {d['name']}\n{len(made)} platforms, formats: {', '.join(formats)}\n\n" + "\n".join(made) + "\n")
    return made


PRESETS = {"launch": ["producthunt", "betalist", "uneed", "fazier", "devhunt", "peerlist", "indiehackers", "hackernews"],
           "social": ["x", "linkedin", "instagram", "threads", "facebook_page", "youtube_community", "mastodon", "bluesky"],
           "dev": ["devto", "hashnode", "hackernews", "github_readme_announcement", "sourceforge", "stackshare"]}


def main():
    ap = argparse.ArgumentParser(description="LaunchPack v2: repo, folder or paragraph in, 100+ platform posts out.")
    ap.add_argument("source", nargs="?", help="GitHub repo URL or README path")
    ap.add_argument("--folder", help="Local project folder")
    ap.add_argument("--readme", help="Local README file")
    ap.add_argument("--text", help="A plain paragraph describing your product")
    ap.add_argument("--text-file", help="File containing the paragraph")
    ap.add_argument("--name"); ap.add_argument("--tagline"); ap.add_argument("--desc")
    ap.add_argument("--features", help="Semicolon separated feature list")
    ap.add_argument("--link")
    ap.add_argument("--platforms", help="Comma separated platform ids")
    ap.add_argument("--preset", choices=list(PRESETS) + ["all"])
    ap.add_argument("--format", choices=["both", "md", "txt"], default="both")
    ap.add_argument("-o", "--out", default="launchpack_out")
    ap.add_argument("--list-platforms", action="store_true")
    ap.add_argument("--relaxed", action="store_true", help="Fill story placeholders with neutral lines instead of [brackets]")
    a = ap.parse_args()
    platforms = load_platforms()
    if a.list_platforms:
        for p in platforms:
            print(f"{p['id']:28s} {p['name']}  [{p['category']}]")
        print(f"\n{len(platforms)} platforms")
        return
    if a.folder:
        d = facts_from_folder(a.folder)
    elif a.readme:
        d = facts_from_markdown(open(a.readme, encoding="utf-8").read(), {}, a.name or "")
    elif a.text or a.text_file:
        txt = a.text or open(a.text_file, encoding="utf-8").read()
        d = facts_from_paragraph(txt, a.name or "")
    elif a.source and "github.com" in a.source:
        d = facts_from_github(a.source)
    elif a.source:
        d = facts_from_markdown(open(a.source, encoding="utf-8").read(), {}, a.name or "")
    elif a.name:
        d = {"name": a.name, "tagline": "", "desc": "", "features": [], "link": "", "topics": [], "lang": ""}
    else:
        ap.error("Give a GitHub URL, --folder, --readme, --text, or --name with manual details")
    if a.name: d["name"] = a.name
    if a.tagline: d["tagline"] = a.tagline
    if a.desc: d["desc"] = a.desc
    if a.features: d["features"] = [f.strip() for f in a.features.split(";") if f.strip()]
    if a.link: d["link"] = a.link
    if not d["tagline"]: d["tagline"] = "[one line: what it does]"
    if not d["desc"]: d["desc"] = d["tagline"]
    if a.platforms:
        want = [w.strip() for w in a.platforms.split(",")]
        known = {p["id"] for p in platforms}
        unknown = [w for w in want if w not in known]
        if unknown:
            sys.exit("Unknown platform ids: " + ", ".join(unknown) + " (use --list-platforms)")
        chosen = [p for p in platforms if p["id"] in want]
    elif a.preset == "all":
        chosen = platforms
    elif a.preset:
        chosen = [p for p in platforms if p["id"] in PRESETS[a.preset]]
    else:
        chosen = [p for p in platforms if p["id"] in PRESETS["launch"]]
    formats = ["md", "txt"] if a.format == "both" else [a.format]
    made = generate(d, chosen, a.out, formats, strict=not a.relaxed)
    print(f"LaunchPack v2: {len(made)} platform posts for {d['name']} written to {a.out}/ (formats: {', '.join(formats)})")


if __name__ == "__main__":
    main()
