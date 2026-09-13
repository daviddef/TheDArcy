/* Errors this archive made and then corrected in public. Newest first.
   The point of the page is the pattern, not the confession. */
export const OWN = [
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
