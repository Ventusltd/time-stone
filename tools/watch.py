#!/usr/bin/env python3
r"""tools/watch.py - the time stone: what changed, and when, across everything public.

    python tools/watch.py [--dry]

One question to GitHub per run: which repositories of this account are public, and when was each
last pushed to. No clones, no assistant, no paid credit; a run takes seconds. It writes:

    ledger.tsv   APPEND ONLY. One row each time a repository is seen to have changed:
                 seen_unix, repository, pushed_at. Old rows are never rewritten, so this is a record
                 of the future arriving, in the order it arrived.
    site.tsv     APPEND ONLY. One row each time a watched page changes its answer: seen_unix, status, url.
    NOW.md       rebuilt from the two ledgers: everything watched, newest change first, by kind.

THE MIRROR. This repository does not watch itself. Its own commits would change its own push time,
which it would then record, which would be a commit: a watcher that watches itself never rests.

SAFEGUARDS. Public repositories only, and anything marked private is skipped anyway. Everything
about to be written goes through the digest guard first; one match and nothing is written, exit 2.
If GitHub cannot be reached nothing is written, exit 1: no answer is not the same as no change.
"""
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
OWNER, SELF = 'Ventusltd', 'time-stone'
sys.path.insert(0, os.environ.get('KB_TOOLS', os.path.join(ROOT, 'kb', 'tools')))
from check_proof import leaks                       # the guard lives in kuiper-belt; one copy, not two

PAGES = ['https://globalgrid2050.com/',
         'https://globalgrid2050.com/solar-bess-topology-v5/cable-geometry-visualiser-v5.html',
         'https://ventusltd.github.io/law/',
         'https://ventusltd.github.io/faraday/']

KINDS = [('stone', ('stone', 'tokens', 'law', 'faraday', 'grid', 'sld')), ('kuiper', ('kuiper', 'cosmic')),
         ('wafer', ('wafer', 'cpu')), ('gridatlas', ('gridatlas', 'atlas')), ('pipelinenews', ('pipeline',))]


def kind(name):
    n = name.lower()
    for k, words in KINDS:
        if any(n == w or w in n for w in words if w != 'grid') or (k == 'stone' and n == 'grid'):
            return k
    return 'estate'


def public_repos():
    out, page = [], 1
    while True:
        req = urllib.request.Request('https://api.github.com/users/%s/repos?type=owner&per_page=100&page=%d' % (OWNER, page),
                                     headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'time-stone'})
        if os.environ.get('GITHUB_TOKEN'):
            req.add_header('Authorization', 'Bearer ' + os.environ['GITHUB_TOKEN'])
        rows = json.load(urllib.request.urlopen(req, timeout=60))
        if not rows:
            return out
        out += [(r['name'], r['pushed_at']) for r in rows
                if not r.get('private') and r.get('visibility', 'public') == 'public' and r['name'] != SELF]
        page += 1


def status(url):
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'time-stone'})
        return str(urllib.request.urlopen(req, timeout=30).status)
    except urllib.error.HTTPError as e:
        return str(e.code)
    except Exception:
        return 'unreachable'


def last(path):
    """The newest value recorded for each name in an append only ledger: {name: value}."""
    seen = {}
    if os.path.exists(path):
        for l in io.open(path, encoding='utf-8'):
            if l.strip() and l[0] != '#':
                c = l.rstrip('\n').split('\t')
                seen[c[-1] if path.endswith('site.tsv') else c[1]] = c[1] if path.endswith('site.tsv') else c[2]
    return seen


def main():
    dry = '--dry' in sys.argv
    now = int(time.time())
    try:
        repos = public_repos()
    except Exception as e:
        print('FAIL: GitHub did not answer (%s); nothing written' % type(e).__name__)
        return 1
    lp, sp = os.path.join(ROOT, 'ledger.tsv'), os.path.join(ROOT, 'site.tsv')
    known, answered = last(lp), last(sp)
    changed = [(n, p) for n, p in sorted(repos, key=lambda r: r[1]) if known.get(n) != p]
    pages = [(u, status(u)) for u in PAGES]
    turned = [(u, s) for u, s in pages if answered.get(u) != s]

    add_l = ''.join('%d\t%s\t%s\n' % (now, n, p) for n, p in changed)
    add_s = ''.join('%d\t%s\t%s\n' % (now, s, u) for u, s in turned)
    current = dict(known)
    current.update(dict(changed))
    rows = sorted(current.items(), key=lambda r: r[1], reverse=True)
    md = ['# NOW', '', 'Rebuilt by `tools/watch.py` from `ledger.tsv` and `site.tsv`. Newest change first.', '',
          '| page | answer |', '|---|---|'] + ['| %s | %s |' % (u, s) for u, s in pages] + ['']
    for k in [k for k, _ in KINDS] + ['estate']:
        mine = [(n, p) for n, p in rows if kind(n) == k]
        if mine:
            md += ['## %s' % k, '', '| repository | last pushed (UTC) |', '|---|---|'] + \
                  ['| [%s](https://github.com/%s/%s) | %s |' % (n, OWNER, n, p.replace('T', ' ').replace('Z', '')) for n, p in mine] + ['']
    md = '\n'.join(md)

    if leaks(add_l + md):
        print('REFUSED (L6): a name that is not public is in the result; nothing written')
        return 2
    print('%d public repositories watched, %d changed since last seen, %d pages changed their answer'
          % (len(repos), len(changed), len(turned)))
    for u, s in pages:
        print('  %s  %s' % (s, u))
    if dry:
        print('dry run: nothing written')
        return 0
    for path, head, add in ((lp, '# seen_unix\trepository\tpushed_at\n', add_l), (sp, '# seen_unix\tstatus\turl\n', add_s)):
        if not os.path.exists(path):
            io.open(path, 'w', encoding='utf-8', newline='\n').write(head)
        if add:
            io.open(path, 'a', encoding='utf-8', newline='\n').write(add)
    io.open(os.path.join(ROOT, 'NOW.md'), 'w', encoding='utf-8', newline='\n').write(md)
    return 0


if __name__ == '__main__':
    sys.exit(main())
