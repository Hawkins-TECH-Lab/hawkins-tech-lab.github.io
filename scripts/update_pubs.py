import requests
import urllib.parse
import xml.etree.ElementTree as ET
import yaml
import os

# Define your static topic categories and target keywords
TOPIC_CATEGORIES = {
    "Equity": [
        "equity", "social justice", "accessibility", "distributive justice", 
        "vulnerable populations", "spatial disparity"
    ],
    "Choice Model Methods": [
        "discrete choice", "random utility", "revealed preference", 
        "stated preference", "latent class", "choice modeling", "econometrics"
    ],
    "Ecological Economics": [
        "ecological economics", "sustainability", "environmental impact", 
        "co2 emissions", "climate change mitigation", "lifecycle assessment"
    ],
    "General Transport": [
        "transportation", "travel behavior", "traffic", "transit", 
        "urban mobility", "transport planning"
    ],
    "Infrastructure Finance": [
        "infrastructure finance", "public-private partnership", "funding", 
        "cost-benefit analysis", "investment", "capital budgeting"
    ],
    "Shared Mobility": [
        "shared mobility", "ride-hailing", "maas", "micromobility", 
        "car-sharing", "on-demand transport"
    ],
    "Vehicle Adoption": [
        "vehicle adoption", "electric vehicle", "ev", "autonomous vehicle", 
        "technology diffusion", "consumer acceptance"
    ]
}

# Base URL
BASE_URL = 'https://export.arxiv.org/api/query?'

# Use a dictionary for the query parameters
params = {
    'search_query': 'au:"Jason Hawkins"',
    'sortBy': 'submittedDate',
    'sortOrder': 'descending',
    'max_results': '50'
}

def categorize_paper(text):
    """Returns a list of all categories that match the paper."""
    text_lower = text.lower()
    matches = []
    for category, keywords in TOPIC_CATEGORIES.items():
        if any(kw in text_lower for kw in keywords):
            matches.append(category)
    
    # Return matches, or a default if empty
    return matches if matches else ["General Transport"]

def fetch_and_categorize():
    query_string = urllib.parse.urlencode(params)
    full_url = BASE_URL + query_string

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*"
    }

    r = requests.get(full_url, headers=headers, timeout=60)

    if r.status_code != 200:
        raise RuntimeError(f"arXiv returned {r.status_code} for URL: {full_url}")

    xml_data = r.text

    root = ET.fromstring(xml_data)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}

    publications = []

    for entry in root.findall('atom:entry', ns):
        title = entry.find('atom:title', ns).text.replace('\n', ' ').strip()
        summary = entry.find('atom:summary', ns).text.replace('\n', ' ').strip()
        link = entry.find('atom:id', ns).text
        published = entry.find('atom:published', ns).text[:10]

        assigned_categories = categorize_paper(title + " " + summary)

        authors = [
            author.find('atom:name', ns).text
            for author in entry.findall('atom:author', ns)
        ]

        publications.append({
            'title': title,
            'description': summary,
            'path': link,
            'date': published,
            'categories': assigned_categories,
            'author': ", ".join(authors),
            'pub_number': "arXiv:" + link.split('/')[-1].replace('v1', ''),
            'journ': "arXiv Preprint",
            'year': published[:4],
            'url_preprint': link
        })

    return publications

if __name__ == '__main__':
    pubs = fetch_and_categorize()
    
    os.makedirs('data', exist_ok=True)
    os.makedirs('../publications', exist_ok=True)
    
    with open('../publications/publications_by_topic.yml', 'w') as f:
        yaml.dump(pubs, f, sort_keys=False)
