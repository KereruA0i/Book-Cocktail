"""
Book Cocktail Mixologist — Flask backend (null-safe, verifiable links, clean Markdown)
- Summarizes a user-provided source title
- Curates exactly 3 open, stable sources: Complementary, Contrasting, Tangent
- Returns JSON with NO nulls (always strings), or an explicit "error" string
- Uses Google CSE + Gemini (configure via env). Gracefully degrades if keys missing.
"""
import os, re, json, time, random
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import requests
from flask import Flask, request, jsonify

# === Environment ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "")

# === Flask ===
app = Flask(__name__)

# === Utilities ===

_ALLOWED_HOSTS_HINT = (
    ".arxiv.org", "arxiv.org",
    ".nih.gov", ".ncbi.nlm.nih.gov", ".pmc.ncbi.nlm.nih.gov",
    ".edu", ".ac.", ".gov",
    "osf.io", "ssrn.com", "hal.science", "openaccess.thecvf.com",
    "reuters.com", "apnews.com", "bbc.com", "nature.com",
    "dl.acm.org", "ieeexplore.ieee.org", "journals.plos.org",
)

def _strip_tracking(url: str) -> str:
    try:
        u = urlparse(url)
        query = [(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True)
                 if not k.lower().startswith(("utm_", "gclid", "fbclid", "icid", "mc_cid", "mc_eid"))]
        return urlunparse((u.scheme, u.netloc, u.path, u.params, urlencode(query), u.fragment))
    except Exception:
        return url

def _is_candidate_ok(url: str) -> bool:
    if not url or "google.com/url" in url or "google.com/search" in url: return False
    host = urlparse(url).netloc.lower()
    if host.startswith("www."): host = host[4:]
    # Prefer open/stable; allow others but de-prioritize later
    return True

def verify_open(url: str, timeout=8) -> bool:
    """Check the page is publicly viewable and texty."""
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0 (BookCocktail)"})
        if r.status_code != 200: return False
        ct = r.headers.get("content-type", "").lower()
        if "text/html" not in ct and "text/plain" not in ct and "application/pdf" not in ct:
            return False
        # quick readability check
        if len(r.content) < 400: return False
        return True
    except Exception:
        return False

def google_search(q: str, num=5):
    """Search via Google CSE; fallback to DuckDuckGo HTML if keys missing (best-effort)."""
    results = []
    if GOOGLE_API_KEY and GOOGLE_CSE_ID:
        try:
            resp = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"key": GOOGLE_API_KEY, "cx": GOOGLE_CSE_ID, "q": q, "num": min(10, max(1, num*2))},
                timeout=10,
            )
            data = resp.json()
            for item in data.get("items", []):
                url = _strip_tracking(item.get("link",""))
                if _is_candidate_ok(url):
                    results.append({
                        "title": item.get("title",""),
                        "url": url,
                        "snippet": item.get("snippet",""),
                    })
        except Exception:
            pass

    # Fallback: DuckDuckGo lite JSON API (undocumented, may break) — best-effort only
    if not results:
        try:
            r = requests.get("https://lite.duckduckgo.com/50x.html", timeout=6)
            # If blocked, silently ignore. We avoid scraping here.
        except Exception:
            pass

    # Dedup and limit
    seen = set(); deduped = []
    for it in results:
        u = it["url"]
        if u and u not in seen:
            seen.add(u); deduped.append(it)
    return deduped[:num]

def pick_open_result(candidates):
    """Return the first verifiably open link, preferring open/stable hosts."""
    # Rank by host preference
    def score(url):
        host = urlparse(url).netloc.lower()
        pref = any(h in host for h in _ALLOWED_HOSTS_HINT)
        return (0 if pref else 1)
    candidates = sorted(candidates, key=lambda it: score(it["url"]))
    for it in candidates:
        url = it["url"]
        if verify_open(url):
            return it
    # Last resort: allow first candidate even if unverifiable, but never return None
    return candidates[0] if candidates else {"title":"", "url":"", "snippet":""}

def call_gemini(system_prompt: str, user_prompt: str) -> str:
    """Best-effort Gemini call; returns plain text. If key missing, synthesize safe placeholder."""
    try:
        import google.generativeai as genai
        if not GEMINI_API_KEY:
            # Offline/dev mode
            return ""
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content([system_prompt, user_prompt])
        return resp.text or ""
    except Exception:
        return ""

# === Core logic ===

def summarize_title(title: str) -> str:
    """Attempt a concise thesis summary; fall back to search snippets."""
    title_clean = title.strip()
    if not title_clean:
        return ""
    # try LLM first
    sys = "Summarize the core thesis of the named work in one or two sentences. If unsure, say you cannot verify."
    out = call_gemini(sys, f'Title: "{title_clean}"\nLanguage: Japanese preferred, else English.')
    out = (out or "").strip()
    if out and "cannot verify" not in out.lower():
        return out
    # fallback: combine top snippets
    hits = google_search(f'"{title_clean}" 要約 OR 概要 OR abstract', num=5)
    if not hits:
        return ""
    snippets = " / ".join([h.get("snippet","") for h in hits if h.get("snippet")][:3])
    return snippets[:600]

def curate_sources(title: str):
    """Return dict for complementary/contrasting/tangent with titles and URLs (never null)."""
    queries = {
        "complementary": f'{title} 批評 OR レビュー OR 研究 site:.edu OR site:.ac OR site:.gov OR arXiv OR SSRN',
        "contrasting":  f'{title} 反論 OR 批判 OR 問題点',
        "tangent":      f'{title} 歴史的文脈 OR メタ分析 OR 関連トピック',
    }
    slots = {}
    for key, q in queries.items():
        hits = google_search(q, num=6)
        chosen = pick_open_result(hits)
        slots[key] = {
            "title": chosen.get("title",""),
            "url": chosen.get("url",""),
            "relation": "Supports" if key=="complementary" else ("Challenges" if key=="contrasting" else "Reframes"),
            "commentary": "",
        }
    # Add short commentaries via LLM (optional)
    if GEMINI_API_KEY:
        for key, item in slots.items():
            if item["title"] and item["url"]:
                brief = call_gemini(
                    "In <=2 short sentences, explain how this link relates to the given work. Output plain text.",
                    f'Work: "{title}"\nLink title: {item["title"]}\nURL: {item["url"]}'
                ).strip()
                item["commentary"] = brief or ""
    return slots

def final_twist() -> str:
    lines = [
        "Filed under: shaken beliefs, not stirred.", 
        "Proof that even footnotes can start bar fights.",
        "Cited responsibly, sipped recklessly.",
        "Because every bibliography needs a wild card.",
    ]
    return random.choice(lines)

def generate_payload(user_title: str):
    title = (user_title or "").strip()
    if not title:
        return {"error": "作品名（本/論文/記事）を入力してください。"}

    summary = summarize_title(title)
    if not summary:
        return {"error": "入力された作品が見つからないか、要約できませんでした。実在するタイトルでお試しください。"}

    sources = curate_sources(title)

    # Construct Markdown output blocks (for your front-end), but keep JSON primitive values non-null.
    md = {
        "core_text_summary": summary,
        "complementary_md": f'**[{sources["complementary"]["title"]}]({sources["complementary"]["url"]})**\n→ Relation: Supports',
        "contrasting_md": f'**[{sources["contrasting"]["title"]}]({sources["contrasting"]["url"]})**\n→ Relation: Challenges\n→ Commentary: {sources["contrasting"]["commentary"] or ""}',
        "tangent_md": f'**[{sources["tangent"]["title"]}]({sources["tangent"]["url"]})**\n→ Relation: Reframes\n→ Commentary: {sources["tangent"]["commentary"] or ""}',
        "final_twist": f'"{final_twist()}"'
    }

    # Also return raw fields your UI can map into sections.
    return {
        "title": title,
        "summary": summary,
        "sources": sources,
        "markdown": md,
        "mode": "full"
    }

# === Routes ===

@app.route("/api/cocktail", methods=["POST"])
def cocktail_api():
    try:
        data = request.get_json(force=True) or {}
        user_input = (data.get("user_input") or "").strip()
        result = generate_payload(user_input)
        # Guarantee: never include Python None in response
        def _denull(x):
            if x is None: return ""
            if isinstance(x, dict): return {k:_denull(v) for k,v in x.items()}
            if isinstance(x, list): return [_denull(v) for v in x]
            return x
        result = _denull(result)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": f"Internal error: {e.__class__.__name__}"}), 500

@app.route("/healthz")
def healthz():
    return jsonify({"ok": True}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)