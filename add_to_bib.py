import requests
import bibtexparser
from get_dev_key import get_dev_key
import re

# ADS API configuration
ADS_API_BASE_URL = "https://api.adsabs.harvard.edu/v1"
ADS_API_TOKEN = get_dev_key()

# ADS Library URL: https://ui.adsabs.harvard.edu/user/libraries/CFJYpXQMRTqHEAe0jOL3VQ
LIBRARY_ID = "CFJYpXQMRTqHEAe0jOL3VQ"

def fetch_ads_library_entries(library_id):
    """
    Fetch all entries from an ADS library using the API with proper pagination
    """
    headers = {
        'Authorization': f'Bearer {ADS_API_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Get library contents (bibcodes) with pagination and filter for refereed publications
    all_bibcodes = []
    start = 0
    rows = 100  # Fetch in batches of 100

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
            'fl': 'bibcode',
            'rows': len(batch_bibcodes)
        }

        response = requests.get(search_url, headers=headers, params=search_params)

        if response.status_code == 200:
            result = response.json()
            docs = result.get('response', {}).get('docs', [])
            batch_refereed = [doc['bibcode'] for doc in docs if 'bibcode' in doc]
            refereed_bibcodes.extend(batch_refereed)
            print(f"  Batch {i//batch_size_filter + 1}: {len(batch_refereed)}/{len(batch_bibcodes)} are refereed")
        else:
            print(f"  Warning: Failed to check refereed status for batch {i//batch_size_filter + 1}")
            # If we can't check, assume they might be refereed (conservative approach)
            refereed_bibcodes.extend(batch_bibcodes)

    print(f"Found {len(refereed_bibcodes)} refereed publications out of {len(all_bibcodes)} total")
    all_bibcodes = refereed_bibcodes  # Use only refereed bibcodes

    if not all_bibcodes:
        print("No refereed documents found in the library")
        return []

    # Use the ADS export API to get BibTeX data in batches
    all_entries = []
    batch_size = 50  # Process bibcodes in smaller batches

    for i in range(0, len(all_bibcodes), batch_size):
        batch_bibcodes = all_bibcodes[i:i+batch_size]
        print(f"Fetching bibtex for batch {i//batch_size + 1} ({len(batch_bibcodes)} entries)...")

        # Use the export API instead of search API
        export_url = f"{ADS_API_BASE_URL}/export/bibtex"
        export_data = {
            'bibcode': batch_bibcodes,
            'format': 'bibtex'
        }

        response = requests.post(export_url, headers=headers, json=export_data)

        if response.status_code != 200:
            print(f"Warning: Failed to fetch batch {i//batch_size + 1}: {response.status_code} - {response.text}")
            continue

        result = response.json()
        bibtex_data = result.get('export', '')

        print(f"  Received BibTeX data: {len(bibtex_data)} characters")

        if bibtex_data:
            # Parse the entire BibTeX string
            parser = bibtexparser.bparser.BibTexParser(common_strings=True)
            try:
                parsed = parser.parse(bibtex_data)
                if parsed.entries:
                    all_entries.extend(parsed.entries)
                    print(f"    Successfully parsed {len(parsed.entries)} entries from batch")
                    if len(all_entries) <= 5:  # Show first few entries for debugging
                        for entry in parsed.entries[:min(3, len(parsed.entries))]:
                            title = entry.get('title', 'No title')[:50]
                            print(f"      - {title}...")
                else:
                    print(f"    Warning: BibTeX parsed but no entries found in batch {i//batch_size + 1}")
            except Exception as e:
                print(f"    Warning: Failed to parse bibtex for batch {i//batch_size + 1}: {e}")
                if len(bibtex_data) < 500:  # Show short bibtex for debugging
                    print(f"    BibTeX content preview: {bibtex_data[:200]}...")
        else:
            print(f"    Warning: No BibTeX data returned for batch {i//batch_size + 1}")

    print(f"Successfully parsed {len(all_entries)} bibtex entries")
    return all_entries

def normalize_title(title):
    """
    Normalize title for comparison by removing LaTeX formatting and extra whitespace
    """
    import re
    if not title:
        return ""

    # Remove outer braces
    title = title.strip('{}').strip()

    # Remove LaTeX commands like \textendash, \ensuremath{}, etc.
    title = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', title)
    title = re.sub(r'\\[a-zA-Z]+', '', title)

    # Remove extra braces and dollar signs
    title = re.sub(r'[{}$]', '', title)

    # Normalize whitespace
    title = ' '.join(title.split())

    return title.lower().strip()

def normalize_entry_key(entry):
    """
    Create a normalized key for comparing entries (using title and year)
    """
    title = normalize_title(entry.get('title', ''))
    year = entry.get('year', '')
    author = entry.get('author', '').split(',')[0] if entry.get('author') else ''
    return f"{title}_{year}_{author}".lower()

def entries_are_similar(entry1, entry2):
    """
    Check if two entries are similar enough to be considered the same paper
    """
    # Compare by title and year primarily
    title1 = normalize_title(entry1.get('title', ''))
    title2 = normalize_title(entry2.get('title', ''))
    year1 = entry1.get('year', '')
    year2 = entry2.get('year', '')

    # Debug output for troubleshooting
    if 'alma-imf' in title1 or 'alma-imf' in title2:
        print(f"DEBUG: Comparing titles:")
        print(f"  Title 1: '{title1}' (year: {year1})")
        print(f"  Title 2: '{title2}' (year: {year2})")
        print(f"  Match: {title1 == title2 and year1 == year2}")

    # Exact match on normalized titles and years
    return title1 == title2 and year1 == year2

def detect_entry_changes(existing_entry, new_entry):
    """
    Detect changes between existing and new entry
    """
    changes = []
    important_fields = ['title', 'author', 'journal', 'year', 'volume', 'pages', 'doi']

    for field in important_fields:
        existing_val = existing_entry.get(field, '').strip('{}').strip()
        new_val = new_entry.get(field, '').strip('{}').strip()

        if existing_val != new_val and new_val:  # Only report if new value exists
            changes.append(f"  {field}: '{existing_val}' -> '{new_val}'")

    return changes

# Load existing cv.bib file
parser = bibtexparser.bparser.BibTexParser(common_strings=True)
with open('cv.bib','r') as fh:
    bib_database = bibtexparser.load(fh, parser=parser)

print(f"Loaded {len(bib_database.entries)} entries from cv.bib")

# Fetch entries from ADS library
try:
    ads_entries = fetch_ads_library_entries(LIBRARY_ID)
    print(f"Fetched {len(ads_entries)} entries from ADS library")
except Exception as e:
    print(f"Error fetching ADS library: {e}")
    exit(1)

# Create lookup dictionaries for comparison
existing_entries_by_title = {}
for entry in bib_database.entries:
    normalized_title = normalize_title(entry.get('title', ''))
    year = entry.get('year', '')
    key = f"{normalized_title}_{year}"
    existing_entries_by_title[key] = entry

print(f"Created lookup table with {len(existing_entries_by_title)} existing entries")

# Process ADS entries
new_entries = []
changed_entries = []

for ads_entry in ads_entries:
    ads_title = normalize_title(ads_entry.get('title', ''))
    ads_year = ads_entry.get('year', '')
    ads_key = f"{ads_title}_{ads_year}"

    # Debug output for ALMA-IMF entries
    if 'alma-imf' in ads_title.lower():
        print(f"DEBUG: Processing ADS entry: '{ads_title}' ({ads_year})")
        print(f"DEBUG: Looking for key: '{ads_key}'")

    # Check if entry already exists using direct key lookup
    if ads_key in existing_entries_by_title:
        existing_entry = existing_entries_by_title[ads_key]
        # Check for changes
        changes = detect_entry_changes(existing_entry, ads_entry)
        if changes:
            changed_entries.append((existing_entry, ads_entry, changes))

        if 'alma-imf' in ads_title.lower():
            print(f"DEBUG: Found existing match for '{ads_title}'")
    else:
        new_entries.append(ads_entry)
        if 'alma-imf' in ads_title.lower():
            print(f"DEBUG: No match found - adding as new entry: '{ads_title}'")

# Report results
print(f"\n=== RESULTS ===")
print(f"Found {len(new_entries)} new entries to add")
print(f"Found {len(changed_entries)} entries with changes (will not modify)")

# Add new entries to database
if new_entries:
    print(f"\nAdding {len(new_entries)} new entries:")
    for entry in new_entries:
        title = entry.get('title', 'Unknown Title').strip('{}')
        year = entry.get('year', 'Unknown Year')
        print(f"  + {title} ({year})")
        bib_database.entries.append(entry)

    # Save updated cv.bib
    with open('cv.bib', 'w') as fh:
        bibtexparser.dump(bib_database, fh)
    print(f"\nUpdated cv.bib with {len(new_entries)} new entries")
else:
    print("\nNo new entries to add - cv.bib is up to date")

# Report changed entries (but don't modify them)
if changed_entries:
    print(f"\n=== DETECTED CHANGES (NOT MODIFIED) ===")
    for existing_entry, new_entry, changes in changed_entries:
        title = existing_entry.get('title', 'Unknown Title').strip('{}')
        print(f"\nChanges detected for: {title}")
        for change in changes:
            print(change)
else:
    print(f"\nNo changes detected in existing entries")