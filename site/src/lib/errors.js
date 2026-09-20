/* Errors this archive made and then corrected in public. Newest first.
   The point of the page is the pattern, not the confession. */
export const OWN = [
  {
    when: "20 September 2026",
    what: "Published “170 distinct catalogue records, 160 of them Berkeley Castle” from a sweep of The National Archives' Discovery API. The true figures are 193 and 183.",
    truth:
      "The tool written for that sweep stopped after one page and returned the first hundred records of however many a query had. SWONHUNGRE alone returns 126, so twenty-six of its records were never seen, and the same was true of any term over a hundred.",
    why: "Discovery's response carries a field called nextBatchMark, which is exactly what a paging loop looks for, and on this endpoint IT IS ALWAYS EMPTY. The loop read it, found nothing, and stopped — correctly, by its own logic. What made it invisible was that the same response also carries the true `count`, and the tool printed that beside the records it had: “126” in the summary, a hundred records in the file. A truncation that reports the number it is missing is the hardest kind to see.",
    lesson:
      "Two days after writing that a null carries the shape of the question that produced it, this archive published a count carrying the shape of a paging bug. The substance survived — every one of the ten non-Berkeley records, which is where the whole value of that sweep lay, was in the first hundred and is unchanged. But it was luck, not method. The tool now uses sps.page, verified by asking for page two of a 232-record query and getting a hundred records none of which were in page one, and it de-duplicates by id so a repeated page cannot inflate a total instead.",
    href: "/swonhungre",
  },
  {
    when: "20 September 2026",
    what: "Published Hannah Saniger's page for weeks with two of its four «written about here» links silently missing — among them her voyage on the General Hewitt, the ship that brought the family to Queensland.",
    truth:
      "The map that holds those links, APPEARS_IN in /people/[slug].astro, carried the key «hannah-saniger» twice: once with four links and once with two. In a JavaScript object literal the later entry simply replaces the earlier one.",
    why: "It is hand-kept, and it is a plain object with thirty-one keys in no particular order, so a second entry for a name already present looks exactly like an edit to the first. Nothing could tell them apart — not a linter, not a build, not a reader, because a reader sees a list of links and has no way of knowing it is short. She is the direct line, and she lost the most substantial page on it.",
    lesson:
      "Found while auditing the other five joins that attach evidence to a person, after the record-row fault of the 17th. The audit expected a second instance of that fault and did not find one: graves.json and households.json do not reach the person page directly, but everything they carry is already there from the family tree. The loss was somewhere nobody was looking, in a data structure whose rules silently permit it. Two of the three checks written that morning were themselves wrong — one could never fail, because it looked for a string that sits in the site navigation, and one reported a grave as missing from a page that states it in full, for want of unescaping an ampersand. Both were caught by trying to make them fail.",
    href: "/hannah-baptism",
  },
  {
    when: "17 September 2026",
    what: "Printed “No record has been found for them” on the pages of thirty people for whom this archive had read a hundred and thirty records — including Constantine D'Arcy, who has two commissions in the London Gazette, a death notice in the Kentish Gazette, a burial register at Medway Archives and an entry in the Corps roll, and a page of this site written about him.",
    truth:
      "One hundred and seventy-six record lines naming fifty-five people in the family tree had been read, graded and published on /register/. Every one of them was dropped before it could reach the person it named.",
    why: "build_dossiers.py gathers every person named in a record and gives them a page. Where the family tree also carries the name it skips them — `if e[\"inTree\"]: continue` — on the reasoning that “the rest already have one”. They do have a page. That page never read the records. /people/[slug] is built from provenance.json, which is a hand-kept list of RELATIONSHIP edges and knows nothing of record rows, so a person with six documents and no relationship edge fell through to the sentence written for people with nothing at all. The data was right, the build dropped it silently, and no gate refused. The Mazza archive had the same fault in a different file and the estate landing page caught it there first.",
    lesson:
      "An assumption inside a build script is a claim, and claims in this archive carry their evidence. “They already have a page” was never checked against the page. The gate that now refuses this reads register.json — the evidence — and works out who is owed a record; the first version of it read the derived file instead, and when the bug was put back that file emptied and the gate reported “0 of 0, ok”. A control that cannot fail is not a control, and it caught its author out twice in one afternoon.",
    href: "/method",
  },
  {
    when: "16 September 2026",
    what: "Announced Ann Saniger's 1798 baptism at Berkeley as a new find — “Ann has never had one” — in a block published on the page that had already been carrying her since 13 September.",
    truth:
      "She was four blocks further up the same page, in the table of John Saniger's children, as ANN SANIGAR 1798. One vowel apart, the same index entry, on the same screen.",
    why: "I opened a record set that named fathers, read the first page of twenty, recognised a name the family tree asserts, and wrote it up against the tree instead of against this archive. The whole point of that page is that this surname is spelled eleven ways; having just written that sentence, I failed to apply it to my own page's contents. Reading the index took an hour; reading the page I was appending to would have taken a minute.",
    lesson:
      "Check the page before you add to the page. A find is only a find against what is already published, and an archive that indexes eleven spellings of a name has to search its own text the same way it searches somebody else's.",
    href: "/hannah-baptism",
  },
  {
    when: "15 September 2026",
    what: "Invented a “Forest side of the family” at AWRE and BLAKENEY, and then built on it — two errands, four coverage rows, an atlas point, and three work-list items, all describing how to reach Sanigers in the Forest of Dean.",
    truth:
      "There is no documented Saniger at Awre or Blakeney anywhere in this archive, and never has been. The 1608 muster puts all eleven men of the surname at HALMORE, HINTON and SANIGER in Berkeley, at Wotton-under-Edge, at Woodmancote in Dursley parish, at Dursley itself, at Paganhill in Stroud, and at Alkerton, Kings Stanley and Oxlynch in Stonehouse — the Vale and the Cotswold edge, and not once across the Severn. Rudder mentions Awre 194 times and names no Saniger in the whole book. Bigland's second volume mentions Awre 172 times and Blakeney 4, and names no Saniger at all, while his first volume gives twenty at Berkeley.",
    why: "I wrote it into a work-list note in the morning — “Saniger of Awre/Blakeney is exactly the sort of name it prints” — as a throwaway justification for opening a journal. Nothing checked it, because it was mine rather than a source's, and for the rest of the day I read it back as though the archive had told me. By evening it had produced an errand asking Gloucestershire Archives for a run of court rolls from 1387 to 1881, on the strength of a phrase I had made up before lunch.",
    lesson:
      "The archive's own rule caught its author out: a claim needs a source named beside it, and that applies hardest to the claims that arrive as background rather than as findings. A premise smuggled in through a to-do list is never graded, never gets a chip, and is never read against anything. It also shows what the control habit is actually worth — the null that exposed this was BIGLAND'S SECOND VOLUME, 172 mentions of Awre and not one of this surname, which is only meaningful because the mention count was taken.",
    href: "/swonhungre",
  },
  {
    when: "15 September 2026",
    what: "Published “Eleven men, four spellings” from the 1608 muster, and named the man living in the hamlet the surname came from JOHN SAINGER — the headline of the whole page, since his name and his address were nearly the same word.",
    truth:
      "There are three spellings, and his name is JOHN SANIGER — identical to his address. Gloucestershire Notes & Queries reviewed Maclean's 1902 edition as it appeared and listed its misreadings: “occasionally marred by errors which the editor, whose name is not indicated, ought not to have passed. Thus SAINGER SHOULD READ SANIGER, and probably seiuger is seivyer; the grotesque Grisseote Cliste should be Greffeote Clifte; Cidolls is probably a blunder for Eidolls; Jugley is probably Ingley; Poutinge is doubtless Pontinge; Slinchcombe should be Stinchcombe; and Stimbridge, Slimbridge.”",
    why: "The page named its source honestly — “the searchable transcript used here was built from the 1902 edition” — and then treated that edition as the manuscript. A printed text is a reading of a document, not the document, and this one had a reviewer going through its errors within the year. I had searched for what the muster said and never asked what anybody thought of the book it was printed in.",
    lesson:
      "When an archive rests on one printed edition, the cheapest next source is not another archive — it is the review of that edition. Somebody with the manuscript in reach has usually already checked it. SAINGER is still a real form of this surname, attested 44 times in the Berkeley registers; it is simply not a 1608 one.",
    href: "/saniger-1608",
  },
  {
    when: "15 September 2026",
    what: "Ran the three Sussex sisters through FreeCEN, found nothing, and recorded it as a NULL — “control: SMITH in Sussex 1861 returns the display cap of 1,000, and the six Darcys are themselves enumerated in Brighton, so the county and the town are both covered”.",
    truth:
      "The county and the town are not the unit. FreeCEN's Sussex 1851 returns NOUGHT for the surname ARCY — and this archive has the three sisters in the 1851 Sussex census under exactly that surname, at HO107/1646 folio 357 page 59 schedule 172, 22 Western Cottages, Brighton. The piece is simply not in FreeCEN. Smith hits the 1,000-row display cap in 1851, 1861 and 1871 alike, which conceals the gap rather than measuring it.",
    why: "I used a common surname as a coverage test, which measures how much a database holds and not whether it holds the thing being looked for. Worse, the cap meant the number could not go up: 1,000 was the ceiling, so it would have looked identical whether Sussex were half-transcribed or whole.",
    lesson:
      "Test an index with a record you already know is in it. This archive had one — the sisters in 1851 — and using it took one query and turned a null into an empty. A control that cannot fail is not a control.",
    href: "/sussex-sisters",
  },
  {
    when: "15 September 2026",
    what: "Printed two different dates for Robert D'Arcy's first commission and never noticed. The timeline, /hornby and three other pages said 1776, from Connolly's Roll. /the-corps said 1778, from a commercial index of the commission registers, and called it “his first commission, and now the earliest record of him anywhere in this archive”.",
    truth:
      "17 JANUARY 1776. The printed Army List of 1781 interleaves each engineer with his seniority date: “Wm. Kesterman 17 Jan. 76 · John Johnson do. · Charles Holloway do. · Thomas Whelpdale do. · John Humfrey do. · James Fiddes do. · Richard Hockings do. · Robert Beatson do. · ROBERT D'ARCY do. · Benjamin Slack 4 Mar.” The men after him break the ditto with their own later dates, which is what makes the chain readable. The 1778 list carries the same run, and Connolly agrees on the year.",
    why: "Two numbers for one event sat on two pages for weeks, and the page that was wrong was the one that sounded most authoritative — it named a record series and claimed a superlative. Nothing in the build checks that a date on one page matches the same date on another, and the archive's own cross-reading tool was run against open questions, never against its own figures.",
    lesson:
      "When two pages give different dates for one event, that is a finding, not a typo — and it is findable without any new source. The fix that generalises is not this correction; it is that a free contemporary printed list settled in ten minutes what a paid index had got wrong, and neither page had ever been read against the other.",
    href: "/the-corps",
  },
  {
    when: "15 September 2026",
    what: "Called Robert D'Arcy's career “a blank of twenty-four years” between 1778 and 1802, and said two Barbados christenings were “the only two records that fall inside it”.",
    truth:
      "The Corps published its own history in 1889. Whitworth Porter puts Lieutenant Robert D'Arcy at the siege of Fort St Philip's on Minorca in 1781 — three years after the commission, squarely inside the blank — and carries “Robert D'Arcy, Barbados” in a station list, so the posting this archive had inferred from a baptism register was stated outright by the Corps all along. Porter also has him Commanding Engineer at Copenhagen in 1807 and Commanding Royal Engineer at Walcheren in 1809.",
    why: "I wrote a sentence about every record that exists after searching the records I happened to have. The book that disproved it is out of copyright, free, full-text searchable, and is the official history of the very corps the page is about — the first place anyone would look, and I had not looked.",
    lesson:
      "This is the same error as the Hampshire Chronicle, five weeks later and with the same shape: “the only records that fall inside it” is a claim about everything ever written, and it cost nothing to say “the only two this archive has found”. When a page is about an institution, read that institution's own published history before describing a gap in it.",
    href: "/the-corps",
  },
  {
    when: "15 September 2026",
    what: "Announced the Morning Herald notice of 1843 as “the first record anywhere to give Robert D'Arcy a corps as well as a rank”. Two older papers had already done it — and the second of them turned up within an hour of my correcting the first.",
    truth:
      "The Hampshire Chronicle of 24 March 1823 carries Jean Ward's death: “At Chatham, MRS. D'ARCY, THE WIFE OF MAJOR-GEN. D'ARCY, OF THE ROYAL ENGINEERS.” And the Oxford University and City Herald of 1 November 1806 carries Margaret's own wedding: “MISS D'ARCY, ELDEST DAUGHTER OF COL. D'ARCY, OF THE ROYAL ENGINEERS” — thirty-seven years before the notice I called the first, in the report of the very marriage that page is about.",
    why: "I had the find of the fortnight and reached for the strongest sentence available instead of the true one. “The only record anywhere” is a claim about every newspaper ever printed, made after searching a handful — and this one turned up in the British Newspaper Archive, which I had already been searching for other things, the very next day.",
    lesson:
      "Say what was searched, not what exists. “The earliest this archive has found” costs nothing and cannot be falsified by tomorrow's search; “the first record anywhere” was falsified twice in one day, the second time by a notice about the very event the page was built on.",
    href: "/margaret-jones",
  },
  {
    when: "14 September 2026",
    what: "Wrote that Martha Wakefield “may never have existed” and that she was “not in the family tree either”, after searching for her in Bristol. She is in the tree, with a death date, a cemetery and a plot number — in Queensland.",
    truth:
      "The tree gives Martha Wakefield 1836–1899, died 23 April 1899 at Maryborough, Queensland, buried Maryborough Cemetery, Plot Monumental L, Grave 410, and cites its source as “Martha HURFORD (born Wakefield)”. The free Queensland death index confirms a Martha Hurford dying on exactly that date — and names her parents as JOHN Wakefield and a HUGHES, not James Wakefield and Hannah Saniger. So she was real, she was not this family's, and none of that required leaving the desk.",
    why: "I searched the country the family came FROM for a woman the archive's own data said died in the country they went TO, under a maiden name she had not used for a decade. Then I published the failure as a finding about her existence.",
    lesson:
      "Before searching for somebody, read everything your own files already say about them — especially where and when they died and what they were called by then. A negative result is only evidence if the search could have succeeded.",
    href: "/crossread",
  },
  {
    when: "14 September 2026",
    what: "Spent a fortnight calling Constantine D'Arcy unplaced while this archive was publishing his christening, his parents' names and both his commissions on another page.",
    truth:
      "Constantine Darcy was christened at St Michael, Barbados on 18 February 1786, father Robert Darcy, mother Jane. That is on /hornby, with the film and batch number, and it has been since the Royal Engineers work of this summer. His sister Jane, christened in the same parish in 1788, is on the same source and the same page. Meanwhile /robert-family listed “Who Constantine was” as an open question, /chatham said his relationship to Robert “has never been established”, and /the-corps displayed a twenty-four-year blank in Robert's career without noticing that two of Robert's children were christened inside it.",
    why: "Pages were written one at a time, each carefully sourced, and nobody ever read them against each other. The archive grew faster than its own index. A search tool that would have caught this in one query has been on the site for weeks and I did not use it on my own material.",
    lesson:
      "Search your own archive before you search anybody else's. A fact you have already published and not cross-read is worse than a fact you never had, because it makes you confident about the wrong things.",
    href: "/constantine",
  },
  {
    when: "14 September 2026",
    what: "Published a nationality audit eleven times over three weeks without ever writing the classifier down.",
    truth: "The figure was a regular expression I retyped from memory on each pass, and it drifted. Sources moved between the Australian and British columns for reasons that had nothing to do with new records, and the percentages I reported to the reader were therefore approximations of varying quality.",
    why: "It was quick to hand-write and it felt like arithmetic rather than method. It is method: the audit is an argument this archive makes about itself, and an argument whose measuring instrument changes shape between readings is not one.",
    lesson: "If a number is worth publishing repeatedly, the thing that computes it is worth committing. tools/audit.py now runs as part of every build.",
    href: "/about",
  },
  {
    when: "13 September 2026",
    what: "Declared Hannah Saniger's baptism missing from every reachable index — twice, on two separate days, each time with a control test behind it.",
    truth: "HANNAH SANIGOR, baptised at Berkeley on 18 August 1804, father JNO SANIGOR. It is in the same FamilySearch index that produced her brothers, and it is on FindMyPast too.",
    why: "This site keeps an alias list of surname spellings — eleven forms of Saniger — and SANIGOR was not one of them. Every “not found” I published was really “not found under the ten spellings I thought of”. The control tests were sound and they were testing the wrong thing: they measured whether the parish was covered, never whether my query could match the name.",
    lesson: "A control test proves the source covers the place. It proves nothing about whether your search string can reach the record. Widen the name before you narrow the conclusion.",
    href: "/hannah-baptism",
  },
  {
    when: "13 September 2026",
    what: "Named a Martha Wakefield, born about 1836, as one of three daughters left behind when the family sailed in 1854 — on five pages.",
    truth: "Two of the three died as children: Eliza at nineteen months in 1834, Ellen at five in 1840, both with Bristol baptisms naming James and Hannah. The third produces no birth registration, no baptism and no burial at Bristol under any spelling — because she is not from Bristol. THE CLAUSE “and is not in the family tree” WHICH STOOD HERE UNTIL 14 SEPTEMBER WAS FALSE: she is in it, and it says she died in Queensland. See the entry of 14 September.",
    why: "The trio was assembled in an early pass and then repeated, and the repetition did the work that evidence should have. Nobody — me — ever went back to ask where the name had come from.",
    lesson: "A fact that has been on the site longest is the one least likely to have been checked. Repetition is not corroboration.",
    href: "/wakefields",
  },
  {
    when: "13 September 2026",
    what: "Reported on several pages that South Leith was not transcribed and that Jean Ward's baptism was therefore out of reach.",
    truth: "It is indexed, with parents named. Jean Ward, baptised South Leith 19 July 1754, father JOSEPH WARD, mother MARTHA GARDEN — an entire Scottish generation this archive did not have.",
    why: "The same fault as Berkeley, on the same afternoon: the free indexes were measured honestly and the conclusion was then widened from “not reachable here” to “not transcribed”, which is a claim about the world rather than about my sources.",
    lesson: "Name the shelf. “Not in FreeREG” and “not transcribed” are different sentences, and only one of them is true.",
    href: "/jean-ward",
  },
  {
    when: "13 September 2026",
    what: "Announced Jabez and Zillah Wakefield as “two children nobody here had ever heard of”, found in the 1851 census.",
    truth: "Both are on the General Hewitt passenger register, which this archive transcribed and published in July, together with an Ephraim aged five. They sailed with their parents, married in Queensland in 1863 and 1871, and Jabez was buried there in 1903.",
    why: "I checked the finding against the family tree, which does not have them, and not against this archive's own pages, which do. The manifest was three clicks away and I had written the page it sits on.",
    lesson: "Check a discovery against what the archive already holds before calling it new. The tree is not the archive.",
    href: "/general-hewitt",
  },
  {
    when: "13 September 2026",
    what: "Built three days of research, two new pages and the top of the errand list on the claim that Hannah Saniger was not born in Gloucestershire.",
    truth: "The 1851 census, taken at Drivers Fields in the same house as the 1841 one, gives her birth town as BERKELEY and her birth county as GLOUCESTERSHIRE — which is exactly what the family tree had said from the beginning.",
    why: "The whole edifice rested on one tick in the 1841 census: the column that asks only whether a person was born in the same county, yes or no. That is the weakest statement a census makes. I treated it as load-bearing because it was the only thing I had, argued from it for days, excluded 81 households with it, catalogued 36 chapel registers because of it, and built a page for a Somerset parish on the strength of it — without ever putting it beside the next census, which asks WHERE rather than WHETHER and was one search away the entire time.",
    lesson: "When a single weak datum is carrying an entire line of research, that is the datum to attack first, not the one to build on. And check the same family in the next census before theorising about the last one.",
    href: "/berkeley-woman",
  },
  {
    when: "13 September 2026",
    what: "Reported repeatedly that the Wakefields could not be found in the 1851 census, and that five of the tree's six Saniger generations at Berkeley could not be tested because the transcript stops in 1677.",
    truth: "Both are in FindMyPast. The 1851 household is complete, with two children this archive had never heard of, and Berkeley baptisms run straight through the supposed gap with parents named.",
    why: "Every null on this site was measured against free indexes. The measuring was right and the conclusion was not: “not reachable from here” quietly became “not there”, which is a statement about a budget rather than about the archives of England.",
    lesson: "Say which shelf you looked on. An index you have not paid for is not an absence of evidence.",
    href: "/coverage",
  },
  {
    when: "13 September 2026",
    what: "Told the reader that the twelve Bristol chapel registers were “digitised, and can be read without leaving the house”.",
    truth: "All twelve are marked DIGITISED: FALSE in The National Archives' own record details. RG 4 is published through commercial partners, so reading them needs a subscription or a visit.",
    why: "I catalogued the pieces carefully — references, dates, denominations, all correct — and then wrote a sentence about access that I had not checked at all. The catalogue lists what a record IS; whether an image exists is a separate field, and I never looked at it until the next pass.",
    lesson: "Finding a document and being able to read it are two different questions, and an errand list that confuses them wastes the reader's afternoon rather than mine.",
    href: "/bristol-chapels",
  },
  {
    when: "13 September 2026",
    what: "Published that Chew Magna lay eight miles from Bristol in a parish of roughly 1,800 people, hours after finding it.",
    truth: "Collinson, writing in 1791, gives “six miles south-west from Bristol … one hundred and seventy houses, and eight hundred and thirty inhabitants”.",
    why: "Both numbers were estimates I made while writing the page and did not mark as estimates. Neither was load-bearing, which is exactly why neither got checked — and one of them was propping up a coverage argument about how many register entries the parish should produce.",
    lesson: "A number written to fill out a sentence is still a number the reader will believe. Either source it or say it is a guess.",
    href: "/chew-magna",
  },
  {
    when: "13 September 2026",
    what: "Treated Portsea as a parish this archive had searched, and read the absence of Joseph D'Arcy's brothers and sisters as though it meant something.",
    truth: "FreeREG's transcript of Portsea St Mary is twenty-two months long. Five common surnames tested across Hampshire for 1778–1783 return forty-six Portsea entries: all baptisms, twenty in 1780, twenty-five in 1781, one in 1782, and none at all in 1778, 1779 or 1783.",
    why: "This site has a rule — establish that a source covers the parish and the window before reporting an absence — and it applied that rule to Berkeley, to Dursley, to Hanley and to eight counties of Sanigers. It never applied it to its own oldest English find. Joseph's baptism was treated as the product of a search when it was the product of a two-year window.",
    lesson: "Test coverage hardest where the source has already given you something. A hit makes a transcript feel complete, and that is exactly when it is least likely to have been measured.",
    href: "/portsea",
  },
  {
    when: "13 September 2026",
    what: "Argued on /berkeley that the archive should stop calling this a Berkeley family — that “of Berkeley” was a label somebody had applied to the whole Vale.",
    truth: "Saniger is a hamlet in Berkeley parish, in the tithing of Hinton. The Berkeley Castle deeds name people “of Saniger” from before 1291, Bigland writes in 1791 that it was “long held by an old Family of the same Name”, and the older spelling — Swanhanger — is on record from 1377.",
    why: "I counted register entries by parish, found 340 at Cam and Dursley against 18 at Berkeley, and let the arithmetic write the conclusion. The counts were right. What they measured was where the family went, not where its name was made, and I never asked whether Saniger was a person or a place.",
    lesson: "Before you weigh a surname's distribution, find out whether it is a surname. A toponym counted as a surname will always look like it belongs somewhere else.",
    href: "/saniger-place",
  },
  {
    when: "13 September 2026",
    what: "Reported twice in one day that no Samuel Sneyd baptism existed at Madeley for the tree's 1769.",
    truth: "The Samuel is there, baptised 4 June 1781 — son of William Sneyd, weaver, and Mary Blackbourne, whose thirteen children fill the register between 1769 and 1794. The year 1769 belongs to his eldest brother William, christened three months after the wedding.",
    why: "I searched for the tree's DATE instead of the tree's PERSON. The 1781 Samuel appeared in every result list I pulled and I discarded him each time for being twelve years out — while the family he belongs to, with the right father, the right mother and the right trade, was sitting underneath him.",
    lesson: "A tree's dates are the softest thing in it. When the person fits and only the year is wrong, suspect the year.",
    href: "/sneyds",
  },
  {
    when: "13 September 2026",
    what: "Said the English origin of this family's Sneyds was “not currently evidenced by anything”, after failing to find two baptisms at Madeley.",
    truth: "Two of the four links are documented: William Sneyd, weaver, married Mary Blackbourne at Madeley on 27 March 1769; and Samuel Charles Sneyd was baptised at Hanley on 28 April 1811, his father Samuel and mother Elizabeth, exactly as the tree says.",
    why: "I searched for baptisms, did not find them, and announced the conclusion — without following up a marriage that was sitting in the same results list, and without ever searching Hanley, the parish the tree plainly names as his birthplace. The negative was published within the hour; the positives took one more query each.",
    lesson: "A negative is not finished until you have tried the places the claim actually points at. Two absent baptisms are not the same as an unevidenced line, and saying so in public before checking is how an archive overcorrects.",
    href: "/sneyd",
  },
  {
    when: "13 September 2026",
    what: "Said Miriam Wakefield “married at twenty-one”.",
    truth: "She married William Hartley Sneyd at Brisbane on 15 November 1859, aged nineteen — Queensland marriage registration 1859/B/255.",
    why: "The age was arithmetic from a birth year and an assumed marriage year, and neither the date nor the registration had ever been looked up. The Queensland marriage index is free and this archive has been using it for other people all week.",
    lesson: "An age you calculated is not a fact you found. If the register that would settle it is one you already have open, look.",
    href: "/drivers-fields",
  },
  {
    when: "13 September 2026",
    what: "Reported that five of the six Saniger generations could not be tested, because Berkeley St Mary's transcript stops in 1677.",
    truth: "They could be tested, three miles away. Dursley St James is transcribed 1577–1951 and Cam St George 1568–1939 — both cover the whole chain, and between them they hold 340 of the 494 Saniger records in the county.",
    why: "The coverage of one parish was checked carefully and then treated as the answer to the whole question. The page even said the surname's real centre was Dursley and Cam, and still did not go and look there.",
    lesson: "Checking coverage is only half the discipline. Having found that one source cannot answer the question, ask which source can — a negative about a parish is not a negative about a family.",
    href: "/berkeley",
  },
  {
    when: "10 September 2026",
    what: "Computed the family tree's predicted Scottish ancestry as 0.02% and announced that a descendant's DNA estimate — 41.9% Scottish and Welsh — was contradicting the tree.",
    truth: "The tree predicts 26.6% Scottish. It was never in disagreement with the DNA.",
    why: "The method attributed each line of descent to the deepest ancestor on record, rather than the deepest ancestor with a known birthplace. Her great-grandfather was born at St Quivox in Ayrshire; the men above him are in the tree as names with no places at all, so the walk stepped straight past Ayrshire and called that eighth of the pedigree unknown.",
    lesson: "When a computed result contradicts something the record plainly says, suspect the computation first. A number produced by your own code is not evidence — it is a claim, and it needs checking like any other.",
    href: "/dna",
  },
  {
    when: "9 September 2026",
    what: "Said William Hartley Sneyd was born in 1838, and that his widow's sworn evidence disproved Find a Grave's 30 September 1837.",
    truth: "He was born on 30 September 1837, and his widow was right.",
    why: "He died on 11 September; his birthday was the 30th, nineteen days later. A man born on 30 September 1837 is 64 on 11 September 1902 — exactly what she swore. I did the arithmetic without checking the death date against the birthday. His Queensland death registration then gave the date outright.",
    lesson: "A stated age is a birth year minus one for everybody whose birthday has not yet come round — which is most of the year, for most people.",
    href: "/inquest-1902",
  },
  {
    when: "9 September 2026",
    what: "Read a handwritten Statement of Service as “marched out to Étaples 26.4.16, taken on strength 29.4.16” and published April dates for Arthur Sneyd's arrival in France.",
    truth: "26 and 29 July 1916.",
    why: "The typed Casualty Form B.103 records the same events in ruled columns and reads unmistakably as July — and July is the only reading consistent with his reverting to the ranks on 29 July.",
    lesson: "Read the typed form before the clerk's freehand, when both record the same events.",
    href: "/great-war",
  },
  {
    when: "9 September 2026",
    what: "Stated that a fourteen-page service dossier for Lindesay Atkinson D'Arcy “is known to exist”.",
    truth: "No such record could be found under any spelling of his name.",
    why: "Nothing was ever checked. The claim had been carried forward on assumption. The search method was then verified by running the same query for his brother-in-law, which returned his dossier at once — so the absence is real.",
    lesson: "“Is known to exist” is a claim like any other and needs a source.",
    href: "/great-war",
  },
  {
    when: "9 September 2026",
    what: "Recommended the Woolwich cadet registers, WO 149, as the best hope for Robert D'Arcy's parentage.",
    truth: "WO 149 runs from 1790 and is held at Sandhurst. It cannot contain a cadet of the early 1770s.",
    why: "The series was recommended without checking its date range.",
    lesson: "Check what a record set actually covers before sending anybody to it.",
    href: "/hornby",
  },
  {
    when: "10 September 2026",
    what: "Called 144 ancestors and twelve generations back to 1654 “what this archive will defend” and “the honest figure”.",
    truth: "Of those 144, eight rest on a record set. Fifty-six rest only on other people's family trees and seventy-nine on nothing at all. Above generation seven, exactly one of sixty ancestors rests on a record.",
    why: "The archive applied its own rule — that a family tree is not a source — to the Hornby descent and to Keele Hall, and never once applied it to the branch it was holding up as solid ground. Nobody counted until somebody asked how far past Brisbane the thing actually went.",
    lesson: "Audit the ground you are standing on before you audit anybody else's. The claim you have never tested is the claim you believe.",
    href: "/how-far-back",
  },
  {
    when: "10 September 2026",
    what: "Told the family their own founding brief was wrong — that the D'Arcys had married Defranceski, and only the Defranceskis had married Falco.",
    truth: "The brief was right. Ian Kenneth D'Arcy married Giuseppina Falco, and their daughter is the person this archive is built outward from.",
    why: "I looked up the root person's spouse instead of her parents, saw a Defranceski, and published a correction to somebody else's accurate account of their own family. It stood on the site for a day.",
    lesson: "The worst errors are the confident ones aimed at somebody else. Before correcting a person about their own family, check the thing they would have checked.",
    href: "/the-other-archives",
  },
  {
    when: "10 September 2026",
    what: "Published William Hartley Sneyd's title in the Government Printing Office as “Quoin-drawer Overseer”.",
    truth: "Fount-room Overseer.",
    why: "The 1884 volume scanned badly. The 1890 volume prints it plainly, and “fount-room” — where a printing house keeps and distributes its type — is what the job actually was.",
    lesson: "One bad scan is not a reading. Find the same fact in a second year.",
    href: "/sergeant-sneyd",
  },
  {
    when: "10 September 2026",
    what: "Quoted the surgeon of the England as receiving “30 men of the 39th regiment”.",
    truth: "39 men, with 6 women and 7 children.",
    why: "The figure came from a secondary account. The National Archives' transcription of the journal itself says 39 — and the regiment's own number is presumably how a 9 became a 0.",
    lesson: "Go to the record. A number that matches something else in the sentence is a number to distrust.",
    href: "/australia",
  },
];

/* Errors inherited from the family tree and corrected here. Kept separate,
   because they are somebody else's mistakes and the distinction matters. */
export const INHERITED = [
  ["John Saniger married Lydia Jones at Berkeley in 1797", "There is one Lydia marrying at Berkeley between 1790 and 1810 and she is LYDIA JONES, 8 January 1798 — whose husband, on the transcript rather than the result row, is JOHN SAWYER. Berkeley has 272 marriages indexed for 1793-1803, and no Saniger marries there in that decade under any of eight spellings. Lydia herself is real: she dies as LYDIA SANIGAR in the Thornbury district in the September quarter of 1851, GRO volume 11 page 329. It is her maiden name and her wedding that were invented, by somebody who matched four fields in a result row and did not open the fifth.", "/hannah-baptism"],
  ["Lydia Jones was born 13 March 1770 at Wotton-under-Edge", "No Lydia Jones is baptised anywhere in Gloucestershire between 1765 and 1775 in England Births & Baptisms 1538-1975, against 939 Jones baptisms in the county in the same eleven years. Her age is the one part that holds: the 1841 census puts her birth about 1771.", "/hannah-baptism"],
  ["Martha Wakefield, 1836–1899, was a daughter of James Wakefield and Hannah Saniger", "She is MARTHA HURFORD, who died at Maryborough on 23 April 1899 — and the Queensland death index gives her parents as JOHN WAKEFIELD and a HUGHES. The index records James and Hannah's other children correctly (Ephraim 1868, Aaron 1896, Zillah 1900, Hiram 1905, Miriam 1909), each naming Hannah under a different spelling of Saniger. There is no Martha among them: another man's daughter was grafted onto this family.", "/crossread"],
  ["Samuel Sneyd married Elizabeth Oliver at Audlem, Cheshire, 22 October 1809", "Not found, against a parish indexed twice over — register and bishop's transcript — where a control for Smith returns twenty marriages in the same decade. No Sneyd appears in Audlem's parish registers at all.", "/sneyds"],
  ["Elizabeth Margaret Oliver was born 7 May 1787 at Oswestry", "Oswestry is confirmed by the 1851 census. The date is almost certainly 17 May 1782 — her baptism at St Oswald's, father David, mother Mary — and both censuses put her birth nearer 1780 than 1787.", "/sneyds"],
  ["John Saniger died on 10 March 1824 at Berkeley", "Buried at Berkeley St Mary the Virgin on 16 January 1825, aged 55. The tree is ten months early; the age confirms the 1769 birth it gives him.", "/behind-the-paywall"],
  ["Samuel Sneyd died on 20 September 1856 at No 3, Well St, Hanley", "He was buried on 23 September 1855, aged 77, of 91 Well St — and the only Samuel Sneyd death registered in England and Wales between 1854 and 1858 is the September quarter of 1855 at Stoke. The year is wrong and so is the house number.", "/sneyds"],
  ["The Sneyds descend from Ralph Sneyd of Keele Hall", "Disproved from the Madeley register: the 1742 baptism names the father as William, and Ralph was eighteen.", "/how-far-back"],
  ["Robert D'Arcy was born in 1751 in North Yorkshire", "The 1751 is arithmetic from an age on a burial register, and nothing places him in Yorkshire.", "/hornby"],
  ["Major George Pitt D'Arcy married twice at Chatham in 1810", "He married Miss Ludlam in 1805 and Maria White in County Wicklow about 1819.", "/australia"],
  ["Arthur Hartley Sneyd was a clerk, buried in France", "A typist, with no known grave.", "/finding-arthur"],
  ["Vivian Ernest William Sneyd died between 1919 and 1921", "16 February 1920, registration 1920/B/31382.", "/great-war"],
  ["Vivian Claude Sneyd was born at Rockhampton", "Windsor, Brisbane, on his own attestation paper.", "/great-war"],
];

/* Counted, never typed. Three separate pages have now quoted a stale number for
   this because somebody added an entry and did not go and find the others. */
export const nOwn = OWN.length;
export const nInherited = INHERITED.length;
