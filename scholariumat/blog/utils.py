import re
import os

import pypandoc

from django.conf import settings


def markdown_to_html(markdown):
    """Converts Articles written in Markdown to HTML and splits up hidden and visible parts."""

    base_dir = os.path.join(settings.MEDIA_ROOT, 'Schriften')
    bib = os.path.join(base_dir, "scholarium.bib")

    # codecs.decode(markdown)
    text = "---\nbibliography: {}\n---\n\n{}\n\n## Literatur".format(bib, markdown)

    # Convert to html
    md = text
    extra_args = []
    filters = ['pandoc-citeproc']
    html = pypandoc.convert(md, 'html', format='md', extra_args=extra_args, filters=filters)

    # Add class tp blockquotes
    p = re.compile("<blockquote>")
    html = p.sub("<blockquote class=\"blockquote\">", html)

    # Change "--" to "–"
    p = re.compile("--")
    html = p.sub("&ndash;", html)

    # References
    p = re.compile(r'<h2.*Literatur</h2>')
    split = re.split(p, html)
    literatur = split[1].lstrip() if len(split) > 1 else ""
    if not literatur:
        print('Keine Literatur gefunden.')

    # Split visible and hidden parts
    p = re.compile(r"<p>&lt;&lt;&lt;</p>")
    split = re.split(p, split[0])
    public = split[0]

    # Remove possible whitespace
    private = split[1].lstrip() if len(split) > 1 else ""
    public2 = split[2].lstrip() if len(split) > 2 else ""

    if not private:
        print('Keinen privaten Teil gefunden.')
    return public, private, public2, literatur
