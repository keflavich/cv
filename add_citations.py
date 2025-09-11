import requests
import bibtexparser
from get_dev_key import get_dev_key


parser = bibtexparser.bparser.BibTexParser(common_strings=True)

# ADS API configuration
ADS_API_BASE_URL = "https://api.adsabs.harvard.edu/v1"
ADS_API_TOKEN = get_dev_key()

def get_rate_limits(response_headers):
    """
    Extract rate limit information from response headers
    """
    return {
        'limit': response_headers.get('X-RateLimit-Limit', '0'),
        'remaining': response_headers.get('X-RateLimit-Remaining', '0'),
        'reset': response_headers.get('X-RateLimit-Reset', '0')
    }

def normalize_title_for_dedup(title):
    """
    Normalize title for duplicate detection
    """
    import re
    if not title:
        return ""

    # Remove outer braces and LaTeX formatting
    title = title.strip('{}').strip()
    title = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', title)
    title = re.sub(r'\\[a-zA-Z]+', '', title)
    title = re.sub(r'[{}$]', '', title)

    # Normalize whitespace and convert to lowercase
    title = ' '.join(title.split()).lower()
    return title

def remove_duplicates(entries, description="entries"):
    """
    Remove duplicate entries based on normalized title and year
    Returns deduplicated list and count of duplicates removed
    """
    seen = set()
    unique_entries = []
    duplicates_removed = 0

    for entry in entries:
        # Create a key based on normalized title and year
        title = normalize_title_for_dedup(entry.get('title', ''))
        year = entry.get('year', '')
        key = f"{title}_{year}"

        if key not in seen:
            seen.add(key)
            unique_entries.append(entry)
        else:
            duplicates_removed += 1
            print(f"  Removed duplicate: {entry.get('title', 'Unknown title')[:50]}...")

    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed} duplicate {description}")
    else:
        print(f"No duplicates found in {description}")

    return unique_entries, duplicates_removed

with open('cv.bib','r') as fh:
    bib_database = bibtexparser.load(fh, parser=parser)

firstauthor_entries = []
nonfirstauthor_entries = []

total_cites = 0
total_firstauthor_cites = 0

for entry in bib_database.entries:
    if 'doi' in entry:
        query_params = {'q': f'doi:{entry["doi"]}'}
        pfx = "Loaded from doi {0}".format(entry['doi'])
    elif 'adsurl' in entry:
        adsurl = entry['adsurl'].split("/")[-1].replace("%26","&") if 'adsurl' in entry else None
        query_params = {'q': f'bibcode:{adsurl}'}
        pfx = "Loaded from adsurl {0}".format(adsurl)
    else:
        print("Skipped {0} because it has no DOI or ADSURL".format(entry['title']))
        continue

    # Make API request
    response = requests.get(f"{ADS_API_BASE_URL}/search/query",
                          headers={'Authorization': f'Bearer {ADS_API_TOKEN}'},
                          params={
                              'fl': 'citation_count,author,year,id,bibcode',
                              'rows': 10,
                              **query_params
                          })

    if response.status_code != 200:
        print(f"ERROR: API request failed with status {response.status_code}: {response.text}")
        continue

    ratelimits = get_rate_limits(response.headers)
    if int(ratelimits['remaining']) < 1:
        raise ValueError("Rate limit of ADS queries exceeded.")

    result = response.json()
    docs = result.get('response', {}).get('docs', [])

    if len(docs) == 0:
        print("ERROR: Skipping {0} because it wasn't found.".format(entry['title']))
        raise
        continue

    print(pfx, docs[0]['bibcode'], docs[0]['citation_count'])
    if len(docs) > 1:
        filtered_docs = [doc for doc in docs if 'tmp' not in doc['bibcode']]
        if len(filtered_docs) == 1:
            art = filtered_docs[0]
        else:
            for ii in range(len(docs)):
                print(f"Article {ii} id: {docs[ii]['id']} author: {docs[ii]['author']}")
            raise ValueError("Found multiple articles.")
    else:
        art = docs[0]
    entry['citations'] = "{0}".format(art['citation_count'])

    # special case for pyspeckit
    if 'doi' in entry and entry['doi'] == "10.3847/1538-3881/ac695a":
        ps_response = requests.get(f"{ADS_API_BASE_URL}/search/query",
                                  headers={'Authorization': f'Bearer {ADS_API_TOKEN}'},
                                  params={
                                      'q': 'bibcode:2011ascl.soft09001G',
                                      'fl': 'citation_count,author,year,id,bibcode',
                                      'rows': 1
                                  })
        if ps_response.status_code == 200:
            ps_result = ps_response.json()
            ps_docs = ps_result.get('response', {}).get('docs', [])
            if ps_docs:
                entry['citations'] = "{0}".format(ps_docs[0]['citation_count'])

    total_cites += art['citation_count']
    if "ginsburg" in art['author'][0].lower():
        total_firstauthor_cites += art['citation_count']
        firstauthor_entries.append(entry)
    else:
        nonfirstauthor_entries.append(entry)

# Remove duplicates from all entry lists before writing files
print("\n=== DEDUPLICATION STEP ===")
print("Checking for and removing duplicate entries...")

# Deduplicate main database entries
bib_database.entries, main_dups = remove_duplicates(bib_database.entries, "main database entries")

# Deduplicate first author entries
firstauthor_entries, fa_dups = remove_duplicates(firstauthor_entries, "first author entries")

# Deduplicate non-first author entries
nonfirstauthor_entries, nfa_dups = remove_duplicates(nonfirstauthor_entries, "non-first author entries")

total_duplicates = main_dups + fa_dups + nfa_dups
print(f"Total duplicates removed: {total_duplicates}")

# Create databases with deduplicated entries
firstauthor_database = bibtexparser.bibdatabase.BibDatabase()
firstauthor_database.entries = firstauthor_entries
nonfirstauthor_database = bibtexparser.bibdatabase.BibDatabase()
nonfirstauthor_database.entries = nonfirstauthor_entries

print(f"\nFinal counts:")
print(f"  Main database: {len(bib_database.entries)} entries")
print(f"  First author: {len(firstauthor_entries)} entries")
print(f"  Non-first author: {len(nonfirstauthor_entries)} entries")

with open('cv_cites.bib','w') as fh:
    bibtexparser.dump(bib_database, fh)

with open('cv_firstauthor_cites.bib','w') as fh:
    bibtexparser.dump(firstauthor_database, fh)

with open('cv_nonfirstauthor_cites.bib','w') as fh:
    bibtexparser.dump(nonfirstauthor_database, fh)

with open('ncites.tex', 'w') as fh:
    fh.write(r"\input{hindex.tex}")
    #fh.write("\\newcommand{{\\ncitestotal}}{{{0}}}\n".format(total_cites))
    #fh.write("\\newcommand{{\\nfirstcitestotal}}{{{0}}}\n".format(total_firstauthor_cites))

# Calculate and display h-index
print("\n=== H-INDEX CALCULATION ===")

def calculate_hindex(citation_counts):
    """
    Calculate h-index from a list of citation counts
    h-index is the largest number h such that h papers have at least h citations each
    """
    if not citation_counts:
        return 0

    # Sort citation counts in descending order
    sorted_cites = sorted(citation_counts, reverse=True)

    h_index = 0
    for i, citations in enumerate(sorted_cites):
        # i+1 is the number of papers (1-indexed)
        # citations is the citation count for the i-th most cited paper
        if i + 1 <= citations:
            h_index = i + 1
        else:
            break

    return h_index

# Collect citation counts from all entries
all_citation_counts = []
firstauthor_citation_counts = []

for entry in bib_database.entries:
    if 'citations' in entry:
        try:
            citations = int(entry['citations'])
            all_citation_counts.append(citations)
        except (ValueError, TypeError):
            # Skip entries with invalid citation counts
            pass

for entry in firstauthor_entries:
    if 'citations' in entry:
        try:
            citations = int(entry['citations'])
            firstauthor_citation_counts.append(citations)
        except (ValueError, TypeError):
            # Skip entries with invalid citation counts
            pass

# Calculate h-indices
overall_hindex = calculate_hindex(all_citation_counts)
firstauthor_hindex = calculate_hindex(firstauthor_citation_counts)

# Display results
print(f"Total papers processed: {len(bib_database.entries)}")
print(f"Papers with citation data: {len(all_citation_counts)}")
print(f"Total citations: {total_cites}")
print(f"Overall h-index: {overall_hindex}")
print()
print(f"First-author papers: {len(firstauthor_entries)}")
print(f"First-author papers with citation data: {len(firstauthor_citation_counts)}")
print(f"First-author citations: {total_firstauthor_cites}")
print(f"First-author h-index: {firstauthor_hindex}")

# Show papers contributing to h-index
if all_citation_counts:
    sorted_all = sorted(all_citation_counts, reverse=True)
    contributing_papers = [c for c in sorted_all[:overall_hindex] if c >= overall_hindex]
    print(f"\nPapers contributing to overall h-index ({overall_hindex}):")
    print(f"Citation counts: {contributing_papers}")

if firstauthor_citation_counts:
    sorted_fa = sorted(firstauthor_citation_counts, reverse=True)
    contributing_fa_papers = [c for c in sorted_fa[:firstauthor_hindex] if c >= firstauthor_hindex]
    print(f"\nFirst-author papers contributing to h-index ({firstauthor_hindex}):")
    print(f"Citation counts: {contributing_fa_papers}")
