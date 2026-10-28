"""Check the reviewed public file list and local links before publication."""
from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    '.nojekyll', 'README.md', 'AGENTS.md', 'index.html',
    'scd-replication/index.html',
    'scd-replication/files/SCD_Model_Research_Access_and_Use_Agreement_v1.4.docx',
    're-ecg-scd/index.html',
    'scripts/check_site.py',
    're-ecg-scd/styles.css',
    're-ecg-scd/files/SCD_Model_Research_Access_and_Use_Agreement_v1.5.docx',
    're-ecg-scd/files/SCD_Model_Research_Access_and_Use_Agreement_v1.4.docx',
}


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        self.urls.extend(v for k, v in attrs if k in ('href', 'src'))


def main():
    actual = {str(p.relative_to(ROOT)) for p in ROOT.rglob('*')
              if p.is_file() and '.git' not in p.relative_to(ROOT).parts}
    errors = []
    if actual != EXPECTED:
        errors.append(f'Public file list changed: added {sorted(actual - EXPECTED)}, missing {sorted(EXPECTED - actual)}')
    page_text = (ROOT / 're-ecg-scd/index.html').read_text()
    required = (
        'https://eccentric-health.github.io/re-ecg-scd/',
        'https://github.com/eccentric-health/re-ecg-scd',
        'mailto:ziad@eccentric.health?subject=SCD%20model%20access',
        'files/SCD_Model_Research_Access_and_Use_Agreement_v1.5.docx',
    )
    for url in required:
        if url not in page_text:
            errors.append(f'Current page is missing its required destination: {url}')
    for obsolete in ('https://github.com/zobermeyer/re-ecg-scd',
                     'https://eccentric-health.github.io/scd-replication/',
                     'mailto:ziadoo@gmail.com'):
        if obsolete in page_text:
            errors.append(f'Current page has an obsolete destination: {obsolete}')
    for page in ROOT.rglob('*.html'):
        if '.git' in page.relative_to(ROOT).parts:
            continue
        links = Links()
        links.feed(page.read_text())
        for url in links.urls:
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (ROOT / unquote(parsed.path.lstrip('/')) if parsed.path.startswith('/')
                      else page.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():
                errors.append(f'{page.relative_to(ROOT)}: invalid local link {url}')
    print('\n'.join(errors) if errors else 'PASS: public file list and local links')
    return int(bool(errors))


if __name__ == '__main__':
    sys.exit(main())
