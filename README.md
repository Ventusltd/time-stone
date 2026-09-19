# time-stone
Watches all other public stones, the Kuiper, and Wafers, gridatlas, pipelinenews and other dense code and intellect

## What it does

Once an hour a small Python script runs on GitHub's own machine. It asks GitHub one question: which
repositories of this account are public, and when was each last pushed to. It writes down only what
changed.

- **[NOW.md](NOW.md)** everything watched, newest change first, grouped by kind, and whether the live pages answer.
- **ledger.tsv** append only. One row each time a repository is seen to have changed. Old rows are never rewritten, so this is time, in the order it arrived.
- **site.tsv** append only. One row each time a watched page changes its answer.

## What it costs

Nothing that has to be paid for. No assistant, no credit, no clone, no desktop computer switched
on. A run takes seconds, and it commits only when something changed. If every other machine is off,
this still keeps the record. See `TOKEN-STONE.md` in Ventusltd/tokens for why it is built this way.

## What it will not do

It does not watch itself: a watcher that records its own commits never rests. It sees public
repositories only, and everything it is about to write passes a guard that holds digests, not
names, of what is not public; one match and nothing is written. If GitHub does not answer it writes
nothing, because no answer is not the same as no change.

Provided as is, without warranty.

## Licence

The code is under the MIT licence (see LICENSE). The ledgers and tables this repository itself produces are under CC BY 4.0: use them, and say where they came from. Data belonging to others keeps its own licence, named beside it.
