import requests
import datetime
import bibtexparser
from get_dev_key import get_dev_key

# ADS API configuration
ADS_API_BASE_URL = "https://api.adsabs.harvard.edu/v1"
ADS_API_TOKEN = get_dev_key()

# ADS Library ID
LIBRARY_ID = "CFJYpXQMRTqHEAe0jOL3VQ"

parser = bibtexparser.bparser.BibTexParser(common_strings=True)

print("hindex")
print("Today is {0}".format(datetime.datetime.now().strftime("%D")))

def fetch_library_papers(library_id, fields):
    """
    Fetch refereed papers from an ADS library
    """
    headers = {
        'Authorization': f'Bearer {ADS_API_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Get library contents (bibcodes) with pagination
    all_bibcodes = []
    start = 0
    rows = 100  # Fetch in batches of 100

    print("Fetching library contents...")
    while True:
        library_url = f"{ADS_API_BASE_URL}/biblib/libraries/{library_id}"
        params = {
            'start': start,
            'rows': rows
        }
        response = requests.get(library_url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch library: {response.status_code} - {response.text}")

        library_data = response.json()
        bibcodes = library_data.get('documents', [])

        if not bibcodes:
            break

        all_bibcodes.extend(bibcodes)
        print(f"Fetched {len(bibcodes)} bibcodes (total so far: {len(all_bibcodes)})")

        # If we got fewer than requested, we're done
        if len(bibcodes) < rows:
            break

        start += rows

    print(f"Found {len(all_bibcodes)} total documents in ADS library")

    # Filter for refereed publications only
    print("Filtering for refereed publications only...")
    refereed_bibcodes = []
    batch_size_filter = 50  # Check in smaller batches for refereed status

    for i in range(0, len(all_bibcodes), batch_size_filter):
        batch_bibcodes = all_bibcodes[i:i+batch_size_filter]

        # Query to check which entries are refereed
        search_url = f"{ADS_API_BASE_URL}/search/query"
        search_params = {
            'q': f'bibcode:({" OR ".join(batch_bibcodes)}) AND property:refereed',
            'fl': ','.join(fields),
            'rows': len(batch_bibcodes)
        }

        response = requests.get(search_url, headers=headers, params=search_params)

        if response.status_code == 200:
            result = response.json()
            docs = result.get('response', {}).get('docs', [])
            refereed_bibcodes.extend(docs)
            print(f"  Batch {i//batch_size_filter + 1}: {len(docs)}/{len(batch_bibcodes)} are refereed")
        else:
            print(f"  Warning: Failed to check refereed status for batch {i//batch_size_filter + 1}")

    print(f"Found {len(refereed_bibcodes)} refereed publications out of {len(all_bibcodes)} total")
    return refereed_bibcodes

# Fetch papers from ADS library (refereed only)
fields = ['id', 'bibcode', 'title', 'citation_count', 'property', 'database',
          'first_author', 'first_author_norm', 'pubdate', 'identifier',
          'author', 'year']

mypapers = fetch_library_papers(LIBRARY_ID, fields)

print("Found {0} refereed papers from ADS library".format(len(mypapers)))

# Calculate total citations from refereed papers
ncites_total = sum([art.get('citation_count', 0) for art in mypapers])

print("Processing papers for astronomy articles (already filtered for refereed)...")

# Filter for astronomy articles, exclude errata, post-2005 only
papers = []
for art in mypapers:
    properties = art.get('property', [])
    database = art.get('database', [])
    title = art.get('title', [''])
    year = art.get('year', '0')

    # Papers are already refereed, just filter for astronomy articles
    if ('ARTICLE' in properties and
        'astronomy' in database and
        not any('Erratum' in title_part for title_part in title) and
        int(year) > 2005):
        papers.append(art)

print("Found {0} papers from library: refereed, astronomy, articles, post-2005".format(len(papers)))

# Extract citation counts and sort them
citations = sorted([art.get('citation_count', 0) for art in papers])

print(f"Total papers for h-index calculation: {len(citations)}")
print(f"Papers with >0 citations: {len([c for c in citations if c > 0])}")
print(f"Total citations: {sum(citations)}")
print(f"Citation range: {min(citations)} to {max(citations)}")

# Store full paper information for later use
full_paper_info = [(art.get('first_author', ''),
                    art.get('first_author_norm', ''),
                    art.get('pubdate', ''),
                    art.get('bibcode', ''),
                    art.get('id', ''),
                    art.get('identifier', []),
                    art.get('author', []),
                    art.get('title', ['']),
                    art.get('citation_count', 0))
                   for art in papers]

print("Found {0} total citations to refereed articles.".format(sum(citations)))

# Calculate h-index using correct algorithm
# Sort in descending order (highest citations first)
citations_desc = sorted(citations, reverse=True)

h_index = 0
for i, nc in enumerate(citations_desc):
    # i+1 is the number of papers (1-indexed)
    # nc is the citation count for the i-th most cited paper
    if i + 1 <= nc:
        h_index = i + 1
    else:
        break

# Debug output (can be removed after verification)
if len(citations_desc) > 50:  # Only show debug for reasonable h-index ranges
    print(f"DEBUG: Top 10 citation counts: {citations_desc[:10]}")
    print(f"DEBUG: Around h-index {h_index}:")
    start_idx = max(0, h_index - 3)
    end_idx = min(len(citations_desc), h_index + 5)  # Show a few more after h-index
    for i in range(start_idx, end_idx):
        position = i + 1
        cites = citations_desc[i]
        contributing = "✓" if position <= cites else "✗"
        print(f"  Position {position}: {cites} citations {contributing}")

    # Show papers with exactly h_index or h_index+1 citations (these are critical)
    critical_papers = [(i, art) for i, art in enumerate(papers)
                      if art.get('citation_count', 0) in [h_index, h_index + 1]]
    if critical_papers:
        print(f"\nPapers with {h_index} or {h_index+1} citations (critical for h-index):")
        for i, art in critical_papers[:5]:  # Show first 5
            title = art.get('title', ['Unknown'])[0][:60] if art.get('title') else 'Unknown'
            cites = art.get('citation_count', 0)
            year = art.get('year', 'Unknown')
            print(f"  {cites} citations: {title}... ({year})")

# Create citation dictionary for display
citedict = {}
for art in papers:
    title = art.get('title', ['Unknown Title'])[0] if art.get('title') else 'Unknown Title'
    first_author = art.get('first_author', 'Unknown Author')
    pubdate = art.get('pubdate', 'Unknown Date')
    citation_count = art.get('citation_count', 0)

    key = "{0}: {1}, {2}{3}".format(citation_count, title, first_author, pubdate)
    citedict[key] = citation_count

citelist = sorted(citedict, key=lambda x: citedict[x])

# Filter for first author papers (where Ginsburg is first author)
first_author_papers = {key: val for key, val in citedict.items()
                      if 'Ginsburg' in key}

print("Computed H-index {0}".format(h_index))
print()
print("Titles contributing to H-index: ")
print("\n".join([description for description,citation_count in citedict.items() if citation_count >= h_index]))


with open('hindex.tex', 'w') as fh:
    fh.write("\\usepackage{xspace}\n")
    fh.write("\\newcommand{{\\nrefereed}}{{{0}\\xspace}}\n".format(len(papers)))
    fh.write("\\newcommand{{\\ntotalpapers}}{{{0}\\xspace}}\n".format(len(mypapers)))
    fh.write("\\newcommand{{\\ncites}}{{{0}\\xspace}} % refereed\n".format(sum(citations)))
    fh.write("\\newcommand{{\\ncitestotal}}{{{0}\\xspace}}\n".format(ncites_total))
    fh.write("\\newcommand{{\\hindex}}{{{0}\\xspace}}\n".format(h_index))
    fh.write("\\newcommand{{\\nfirst}}{{{0}\\xspace}}\n".format(len(first_author_papers)))
    fh.write("\\newcommand{{\\ncitesfirst}}{{{0}\\xspace}}\n".format(sum(first_author_papers.values())))




with open('cv.bib','r') as fh:
    bib_database = bibtexparser.load(fh, parser=parser)

print(f"Loaded {len(bib_database.entries)} entries from cv.bib")

# Check for potential duplicates in cv.bib
print("Checking for potential duplicates in cv.bib...")
doi_count = {}
bibcode_count = {}
potential_duplicates = 0

for entry in bib_database.entries:
    # Check DOI duplicates
    doi = entry.get('doi', '').strip()
    if doi:
        if doi in doi_count:
            doi_count[doi] += 1
            potential_duplicates += 1
        else:
            doi_count[doi] = 1

    # Check bibcode duplicates
    if 'adsurl' in entry:
        bibcode = entry['adsurl'].split("/")[-1].replace("%26","&")
        if bibcode in bibcode_count:
            bibcode_count[bibcode] += 1
            potential_duplicates += 1
        else:
            bibcode_count[bibcode] = 1

if potential_duplicates > 0:
    print(f"WARNING: Found {potential_duplicates} potential duplicate entries in cv.bib")
    print("Consider running 'python add_to_bib.py' to clean up duplicates")

    # Show some examples
    duplicate_dois = {doi: count for doi, count in doi_count.items() if count > 1}
    duplicate_bibcodes = {bc: count for bc, count in bibcode_count.items() if count > 1}

    if duplicate_dois:
        print("Duplicate DOIs found:")
        for doi, count in list(duplicate_dois.items())[:3]:  # Show first 3
            print(f"  {doi} appears {count} times")

    if duplicate_bibcodes:
        print("Duplicate bibcodes found:")
        for bibcode, count in list(duplicate_bibcodes.items())[:3]:  # Show first 3
            print(f"  {bibcode} appears {count} times")
    print()

print()
print("cv.bib matches: (blank means good)")
matches = {}
cvbib_only = []  # cv.bib entries with no DOI/bibcode match in the filtered ADS set
for entry in bib_database.entries:
    doi = entry.get('doi')
    bibcode = entry['adsurl'].split("/")[-1].replace("%26","&") if 'adsurl' in entry else None

    # Find matches in papers list
    match = []
    for art in papers:
        identifiers = art.get('identifier', [])
        art_bibcode = art.get('bibcode', '')

        if (doi and doi in identifiers) or (bibcode and bibcode == art_bibcode):
            match.append(art)

    if len(match) == 0:
        cvbib_only.append(entry)
        print("No match for {0}, which is in cv.bib, in downloaded papers".format(entry.get('title')))
    elif len(match) > 1:
        print("Multiple matches for {0} among downloaded papers".format(entry.get('title')))
    else:
        matches[bibcode] = match[0]

print()
print("ADS search matches (blank means good):")

def resolve_multiple_matches(matches, art_bibcode, art_identifiers):
    """
    Resolve multiple matches by preferring published versions over arXiv preprints
    """
    if len(matches) <= 1:
        return matches

    # Prefer entries with journal information (published versions)
    published_matches = [m for m in matches if m.get('journal', '').strip()]
    if len(published_matches) == 1:
        return published_matches
    elif len(published_matches) > 1:
        # If multiple published versions, prefer the one that matches the bibcode exactly
        exact_bibcode_matches = [m for m in published_matches
                                if 'adsurl' in m and
                                m['adsurl'].split("/")[-1].replace("%26","&") == art_bibcode]
        if len(exact_bibcode_matches) == 1:
            return exact_bibcode_matches

    # If no clear published version, prefer the one with exact bibcode match
    exact_bibcode_matches = [m for m in matches
                            if 'adsurl' in m and
                            m['adsurl'].split("/")[-1].replace("%26","&") == art_bibcode]
    if len(exact_bibcode_matches) == 1:
        return exact_bibcode_matches

    # If still multiple matches, prefer non-arXiv DOIs
    non_arxiv_matches = [m for m in matches
                        if m.get('doi', '') and 'arxiv' not in m.get('doi', '').lower()]
    if len(non_arxiv_matches) == 1:
        return non_arxiv_matches

    # As last resort, just return the first match and warn
    print(f"  Warning: Could not resolve {len(matches)} matches, using first one")
    return matches[:1]

reverse_matches = {}
ads_only_reliable = []  # filtered ADS papers with no DOI/bibcode match in cv.bib
for art in papers:
    bibcode = art.get('bibcode', '')
    title = art.get('title', ['Unknown Title'])[0] if art.get('title') else 'Unknown Title'
    identifiers = art.get('identifier', [])

    # Find matching entries in cv.bib
    match = []
    for entry in bib_database.entries:
        entry_doi = entry.get('doi', '')
        entry_bibcode = entry['adsurl'].split("/")[-1].replace("%26","&") if 'adsurl' in entry else None

        if (any(doi == entry_doi for doi in identifiers if entry_doi) or
            (bibcode and bibcode == entry_bibcode)):
            match.append(entry)

    if len(match) == 0:
        ads_only_reliable.append(art)
        print("No match for {0} in cv.bib: {1}".format(title, bibcode))
    elif len(match) > 1:
        print("Multiple matches for {0} in cv.bib.  doi: {1} bibcode: {2}".format(title, identifiers, bibcode))
        print(f"  Found {len(match)} matches - attempting to resolve...")

        # Show the matches for debugging
        for i, m in enumerate(match):
            entry_title = m.get('title', 'No title')[:50]
            entry_doi = m.get('doi', 'No DOI')
            entry_journal = m.get('journal', 'No journal')
            print(f"    Match {i+1}: {entry_title}... (DOI: {entry_doi}, Journal: {entry_journal})")

        # Try to resolve the multiple matches
        resolved_matches = resolve_multiple_matches(match, bibcode, identifiers)

        if len(resolved_matches) == 1:
            print(f"  Resolved to single match: {resolved_matches[0].get('title', 'No title')[:50]}...")
            reverse_matches[bibcode] = resolved_matches[0]
        else:
            print(f"  Could not resolve to single match, found {len(resolved_matches)} candidates")
            # Don't raise an error, just use the first one
            reverse_matches[bibcode] = resolved_matches[0]
    else:
        reverse_matches[bibcode] = match[0]

# Compare paper counts between sources
print(f"\n=== DATA SOURCE COMPARISON ===")
print(f"Papers from ADS library (after filtering): {len(papers)}")
print(f"Papers from cv.bib: {len(bib_database.entries)}")
print(f"Difference: {len(bib_database.entries) - len(papers)} papers")

# Reliable mismatch analysis based on DOI + bibcode matching.
# NOTE: an earlier version compared lowercased title strings, which produced
# dozens of bogus "missing" papers whenever a title differed only in LaTeX /
# Unicode encoding (e.g. {\ensuremath{\lambda}} vs the literal character).
# We instead reuse the DOI/bibcode matches collected above (cvbib_only and
# ads_only_reliable), which are authoritative.
print(f"\n=== MISMATCH ANALYSIS (by DOI/bibcode) ===")

print(f"\nFiltered ADS-library papers NOT found in cv.bib ({len(ads_only_reliable)}):")
if ads_only_reliable:
    for art in ads_only_reliable:
        title = art.get('title', ['Unknown'])[0] if art.get('title') else 'Unknown'
        print(f"  - {title[:70]} ({art.get('bibcode', '?')})")
    print("   → Run 'python add_to_bib.py' to sync these into cv.bib")
else:
    print("  (none — cv.bib already contains every refereed library article)")

print(f"\ncv.bib entries NOT in the filtered refereed-article set ({len(cvbib_only)}):")
if cvbib_only:
    for entry in cvbib_only:
        title = entry.get('title', 'Unknown').strip('{}')
        year = entry.get('year', '?')
        etype = entry.get('ENTRYTYPE', '?')
        print(f"  - {title[:70]} ({year}, @{etype})")
    print("   → Typically theses, errata/corrigenda, proceedings, or pre-2006 /")
    print("     non-article entries that are correctly excluded from the h-index.")
else:
    print("  (none)")

# QUICK COMPARISON: compute the cv.bib-based h-index from cv_cites.bib.
# add_citations.py writes the per-paper 'citations' field to cv_cites.bib
# (NOT to cv.bib), so the comparison must read cv_cites.bib.
print(f"\n=== QUICK COMPARISON: cv_cites.bib vs filtered library ===")
cv_citations = []
try:
    with open('cv_cites.bib', 'r') as fh:
        cv_cites_db = bibtexparser.load(
            fh, parser=bibtexparser.bparser.BibTexParser(common_strings=True))
    for entry in cv_cites_db.entries:
        if 'citations' in entry:
            try:
                cv_citations.append(int(entry['citations']))
            except (ValueError, TypeError):
                pass
except FileNotFoundError:
    print("   cv_cites.bib not found — run add_citations.py first.")

if cv_citations:
    cv_citations_desc = sorted(cv_citations, reverse=True)
    cv_hindex = 0
    for i, nc in enumerate(cv_citations_desc):
        if i + 1 <= nc:
            cv_hindex = i + 1
        else:
            break

    print(f"   cv_cites.bib (all {len(cv_citations)} entries): h-index {cv_hindex}")
    print(f"   hindex.py (refereed astronomy articles, post-2005): h-index {h_index}")
    print(f"   Difference: {cv_hindex - h_index} "
          f"(from the {len(cvbib_only)} cv.bib entries outside the filtered set)")
else:
    print("   No citation data found in cv_cites.bib (run add_citations.py).")
