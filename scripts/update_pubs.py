"""Merge new publications into publications/publications.yml.

Sources
  * OpenAlex, by ORCID: journal articles, conference papers, SSRN and other
    preprints that carry a DOI.
  * arXiv, by author name: catches preprints OpenAlex hasn't linked yet.

The YAML file is the source of truth and is meant to be hand-edited. This script
NEVER deletes an entry and never overwrites a field you have filled in. It only:
  * appends works it hasn't seen before (with suggested categories);
  * fills in fields that are empty on an existing entry;
  * upgrades a preprint entry in place when its journal version appears
    (keeping your categories and the preprint link).

Hand-edit conventions
  * hidden: true    -> keep the entry but don't show it on the site (also stops
                       the script from re-adding it).
  * Papers on ResearchGate etc. with no DOI: add an entry by hand. The script
    leaves it alone.

Usage:  python scripts/update_pubs.py [--dry-run]
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET

import requests
import yaml

ORCID = "0000-0002-9655-4846"
ARXIV_AUTHOR = 'au:"Jason Hawkins"'

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PUBS_FILE = os.path.join(ROOT, "publications", "publications.yml")

HEADERS = {"User-Agent": "hawkins-tech-lab-site/1.0 (publication sync)"}

# OpenAlex work types that aren't publications we want to list.
SKIP_TYPES = {"dataset", "editorial", "erratum", "peer-review", "paratext",
              "other", "letter", "retraction", "supplementary-materials"}

# Suggested topic tags for NEW entries only. Matched on whole words/phrases,
# case-insensitive. Edit the `categories` field in the YAML to correct them.
TOPIC_CATEGORIES = {
    "Equity": [
        "equity", "social justice", "distributive justice", "justice40",
        "vulnerable population", "spatial disparity", "disadvantaged",
    ],
    "Choice Model Methods": [
        "discrete choice", "random utility", "revealed preference",
        "stated preference", "latent class", "choice model", "choice modelling",
        "choice modeling", "logit", "mdcev", "integrated choice and latent",
        "goal pursuit",
    ],
    "Ecological Economics": [
        "ecological economics", "life cycle assessment", "lifecycle assessment",
        "carbon", "emissions", "input-output", "social accounting matri",
        "decarbonization", "environmentally extended",
    ],
    "Infrastructure Finance": [
        "infrastructure finance", "public-private partnership",
        "cost-benefit analysis", "congestion pricing", "road pricing",
        "carbon pricing", "property value", "housing price", "price model",
    ],
    "Shared Mobility": [
        "shared mobility", "ride-hailing", "ride-sourcing", "ride hailing",
        "ridesourcing", "transportation network compan", "uber", "maas",
        "micromobility", "bikeshare", "bike share", "car-sharing", "carsharing",
        "taxi sharing", "ride-splitting",
    ],
    "Vehicle Adoption": [
        "vehicle adoption", "electric vehicle", "evs?", "evse",
        "autonomous vehicle", "self-driving", "automated vehicle",
        "vehicle ownership", "car ownership", "vehicle diffusion",
    ],
}
DEFAULT_CATEGORY = "General Transport"

FIELD_ORDER = ["title", "author", "date", "year", "journ", "volume", "issue",
               "page", "pub_number", "doi", "arxiv", "path", "url_source",
               "url_preprint", "categories", "type", "hidden", "description"]


# ---------------------------------------------------------------- helpers ---

def norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def same_title(a: str, b: str) -> bool:
    a, b = norm_title(a), norm_title(b)
    if not a or not b:
        return False
    return a == b or difflib.SequenceMatcher(None, a, b).ratio() >= 0.93


def suggest_categories(text: str) -> list[str]:
    text = text.lower()
    cats = [c for c, kws in TOPIC_CATEGORIES.items()
            if any(re.search(rf"\b{kw}\b", text) for kw in kws)]
    return cats or [DEFAULT_CATEGORY]


def arxiv_id_from(s: str | None) -> str | None:
    if not s:
        return None
    m = re.search(r"arxiv[./:](?:abs/)?(\d{4}\.\d{4,5})", s, re.I) or \
        re.search(r"arxiv\.org/abs/(\d{4}\.\d{4,5})", s, re.I)
    return m.group(1) if m else None


def is_preprint(e: dict) -> bool:
    return e.get("type") == "preprint"


# ---------------------------------------------------------------- sources ---

def abstract_from_index(inv: dict | None) -> str:
    if not inv:
        return ""
    words = sorted((pos, w) for w, ps in inv.items() for pos in ps)
    return " ".join(w for _, w in words)


def fetch_openalex() -> list[dict]:
    out, cursor = [], "*"
    while cursor:
        r = requests.get(
            "https://api.openalex.org/works",
            params={"filter": f"author.orcid:{ORCID}", "per-page": 100,
                    "cursor": cursor},
            headers=HEADERS, timeout=60)
        r.raise_for_status()
        data = r.json()
        for w in data["results"]:
            e = openalex_entry(w)
            if e:
                out.append(e)
        cursor = data["meta"].get("next_cursor") if data["results"] else None
    return out


def openalex_entry(w: dict) -> dict | None:
    wtype = w.get("type") or ""
    if wtype in SKIP_TYPES:
        return None
    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    venue = src.get("display_name")
    doi = (w.get("doi") or "").replace("https://doi.org/", "").lower() or None
    if not venue and not doi:
        return None  # orphan records with no venue or DOI are usually duplicates

    axid = arxiv_id_from(doi) or arxiv_id_from(loc.get("landing_page_url"))
    preprint = wtype == "preprint" or (wtype == "article"
                                         and src.get("type") == "repository")
    if preprint:
        if axid:
            venue = "arXiv Preprint"
        elif doi and doi.startswith("10.2139/ssrn"):
            venue = "SSRN Preprint"
        elif venue:
            venue = f"{venue} Preprint"

    biblio = w.get("biblio") or {}
    pages = "–".join(p for p in [biblio.get("first_page"),
                                 biblio.get("last_page")] if p)
    date = w.get("publication_date") or ""
    url = f"https://doi.org/{doi}" if doi else loc.get("landing_page_url")
    title = re.sub(r"<[^>]+>", "", w.get("title") or "").strip()

    e = {
        "title": title,
        "author": ", ".join(a["author"]["display_name"]
                            for a in w.get("authorships", [])),
        "date": date,
        "year": date[:4],
        "journ": venue,
        "volume": biblio.get("volume"),
        "issue": biblio.get("issue"),
        "page": pages or None,
        "doi": doi,
        "arxiv": axid,
        "pub_number": f"doi:{doi}" if doi and not axid else
                      (f"arXiv:{axid}" if axid else None),
        "path": url,
        "type": "preprint" if preprint else (wtype or "article"),
        "description": abstract_from_index(w.get("abstract_inverted_index")),
    }
    if preprint:
        e["url_preprint"] = url
    else:
        e["url_source"] = url
    return e


def fetch_arxiv() -> list[dict]:
    q = urllib.parse.urlencode({"search_query": ARXIV_AUTHOR,
                                "sortBy": "submittedDate",
                                "sortOrder": "descending",
                                "max_results": "100"})
    r = requests.get("https://export.arxiv.org/api/query?" + q,
                     headers=HEADERS, timeout=60)
    r.raise_for_status()
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for entry in ET.fromstring(r.text).findall("a:entry", ns):
        link = entry.find("a:id", ns).text
        axid = arxiv_id_from(link)
        url = f"https://arxiv.org/abs/{axid}"
        date = entry.find("a:published", ns).text[:10]
        out.append({
            "title": " ".join(entry.find("a:title", ns).text.split()),
            "author": ", ".join(a.find("a:name", ns).text
                                for a in entry.findall("a:author", ns)),
            "date": date,
            "year": date[:4],
            "journ": "arXiv Preprint",
            "arxiv": axid,
            "pub_number": f"arXiv:{axid}",
            "path": url,
            "url_preprint": url,
            "type": "preprint",
            "description": " ".join(entry.find("a:summary", ns).text.split()),
        })
    return out


# ------------------------------------------------------------------ merge ---

def find_match(entries: list[dict], new: dict) -> dict | None:
    for e in entries:
        if new.get("doi") and e.get("doi") == new["doi"]:
            return e
        if new.get("arxiv") and e.get("arxiv") == new["arxiv"]:
            return e
    for e in entries:
        if same_title(e.get("title"), new.get("title")):
            return e
    return None


def merge_into(old: dict, new: dict) -> bool:
    """Update `old` in place from `new`. Returns True if anything changed."""
    before = dict(old)
    if is_preprint(old) and not is_preprint(new):
        # Journal version appeared: upgrade, keeping categories/preprint link.
        keep = {k: old[k] for k in ("categories", "hidden", "url_preprint",
                                    "arxiv") if old.get(k)}
        if old.get("path") and not keep.get("url_preprint"):
            keep["url_preprint"] = old["path"]
        for k, v in new.items():
            if v:
                old[k] = v
        old.update(keep)
    else:
        if is_preprint(new) and not is_preprint(old):
            new = {k: new[k] for k in ("url_preprint", "arxiv") if new.get(k)}
        for k, v in new.items():
            if v and not old.get(k):
                old[k] = v
    return old != before


def tidy(e: dict) -> dict:
    out = {k: e[k] for k in FIELD_ORDER if e.get(k) not in (None, "", [])}
    out.update({k: v for k, v in e.items()
                if k not in out and v not in (None, "", [])})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    entries: list[dict] = []
    if os.path.exists(PUBS_FILE):
        with open(PUBS_FILE, encoding="utf-8") as f:
            entries = yaml.safe_load(f) or []

    incoming = []
    for name, fetch in (("OpenAlex", fetch_openalex), ("arXiv", fetch_arxiv)):
        try:
            got = fetch()
            print(f"{name}: {len(got)} works")
            incoming += got
        except Exception as exc:  # one source failing shouldn't block the other
            print(f"WARNING: {name} fetch failed: {exc}", file=sys.stderr)

    # Journal versions first, so preprints attach to them rather than vice versa.
    incoming.sort(key=is_preprint)

    added, updated = [], []
    for new in incoming:
        old = find_match(entries, new)
        if old is None:
            new["categories"] = suggest_categories(
                f"{new['title']} {new.get('description', '')}")
            entries.append(new)
            added.append(new["title"])
        elif merge_into(old, new):
            updated.append(old["title"])

    entries = [tidy(e) for e in entries]
    entries.sort(key=lambda e: str(e.get("date", "")), reverse=True)

    for t in added:
        print(f"  + {t}")
    for t in updated:
        print(f"  ~ {t}")
    print(f"{len(added)} added, {len(updated)} updated, {len(entries)} total")

    if not args.dry_run:
        with open(PUBS_FILE, "w", encoding="utf-8", newline="\n") as f:
            f.write("# Publication list. Hand edits are safe: see "
                    "scripts/update_pubs.py for conventions.\n")
            yaml.safe_dump(entries, f, sort_keys=False, allow_unicode=True,
                           width=100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
