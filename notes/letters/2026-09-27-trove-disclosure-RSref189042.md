# Trove — disclosure, and a request to widen the scope

**To:** Trove Support (Liz), RSref189042
**Re:** API key issued 27 September 2026 — scope of use
**Status: DRAFTED, NOT SENT.** David decides whether this goes, and in what form.

**Why it is a disclosure and not just a request.** A letter asking «may we also
search articles» would omit that the searching has already happened, in another
archive of the same family estate, using this key. The Library would discover
that by opening either repository, both of which are public. It is better said
by us, on the day, than found later.

---

Dear Liz,

Thank you for the key, which arrived this morning.

I need to tell you that within the first hour it was used outside the scope I
described to you on 20 September, and to ask you a question that I should
probably have asked then.

**What I undertook.** In answer to your second question I wrote that no Trove
content would train or evaluate any model; that no full text of any article
would be retrieved, the request being «metadata only — newspaper and gazette
titles, their place coverage and their date ranges»; that nothing AI-written
would be published as though it were a Trove record; and that the build refuses
if a published claim loses its source.

**What happened.** I keep several family archives in one estate, and the key was
shared across them. They are not equally at fault and I would rather give you
the two separately than a figure averaged across them.

The larger part, in the Defranceski archive: the article endpoint `/v3/result`
was searched rather than the titles endpoints; 170 article records were kept;
53 of them carried extracts of article prose, 7,898 characters in all, which
were committed to a public GitHub repository within the hour; about seventy
further article texts were fetched from the public Trove website rather than
through the API; and six passages of article prose were quoted into that
archive's published pages.

The smaller part, in this archive: six words quoted from an 1849 obituary —
found on your website months ago, before any key existed — sitting in a person
record beside its citation.

I do not think the second is the same thing as the first, but it is the same
question, so you have both.

The first two undertakings were not kept. No Trove content has been used to
train or evaluate any model, and nothing AI-written has been published as a
Trove record; those two hold.

**What has been done since.** The extracts were deleted from the working file
within the hour, the field removed rather than emptied so that a later pass
cannot restore it, and what remains is citation only — date, newspaper, heading,
page and the Trove URL. Article searching and article-text retrieval have
stopped across the estate pending your answer. Two things have deliberately not
been done, because they are yours to direct rather than ours: the extracts
remain in the repository's published history, since rewriting it breaks anyone
who has cloned it; and six passages quoted into one archive's pages are still
there, including a 1982 death notice that names seven children and is the best
single finding that archive has made.

**What I am asking.** Whether a standard key permits searching the article
endpoint and citing what it returns — newspaper, date, page and the article URL,
which is a citation rather than content — and whether short quotations from
out-of-copyright articles may be published with that citation attached. If the
answer to either is no, tell me and it stops and is removed; if removal should
extend to the published history, say so and it will be done.

I would rather have a narrow key I am certainly keeping to than a wide one I am
guessing about.

The titles work you were originally asked for is done and is published as an
open file, as promised: 2,052 newspaper and gazette titles with their places and
date ranges, and the issue counts held per year for the 725 Queensland and New
South Wales titles this archive works in. It is at
https://daviddef.github.io/TheDArcy/trove-titles.json and it is free for anyone.

Yours sincerely,

David Defranceski

---

## Notes for David before this goes

- **It admits a breach in writing.** That is the point, and it is a real cost. The
  alternative is that the Library finds fifty-three article extracts in a public
  repository with their key on it and draws its own conclusion about why nobody
  mentioned it.
- **Nothing here is guessed.** The undertaking text is from the sent letter of 20
  September. The 170 records, 53 extracts, 7,898 characters, ~70 website
  fetches and six quotations are the Defranceski archive's own account, which
  it verified against its files rather than accepting my summary, and which it
  asked to have stated plainly as the worse half rather than averaged with
  mine. The six words are in this archive's `person-records.json`.
- **It says which archive did what.** That is deliberate. A disclosure that
  blurs two very different degrees of fault into one paragraph invites the
  Library to assume the worse of both.
- **The two things left undone are deliberately left to them**, because both are
  irreversible in one direction and neither is urgent.
- **If you would rather not disclose**, the honest alternative is not a
  request-only letter. It is to stop at titles everywhere, remove the extracts
  and the quotations, and say nothing — which is defensible, and which I would
  do without complaint if you say so.
