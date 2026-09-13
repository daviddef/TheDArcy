#!/usr/bin/env python3
"""Assemble the register: every named individual this archive has found, anywhere.

Two kinds of entry, and the distinction is the whole point:

  * "family tree"  — a person carried in the family's MyHeritage export. What the
                     family believes, not what a record proves. Treat as a claim
                     until the same person turns up on this page with a source.
  * everything else — a person this archive met in an actual record it read: a
                     civil registration, a parish register, a service dossier, a
                     coroner's file, a newspaper, a payroll.

Living people are excluded from the tree side entirely, exactly as everywhere
else in this build.

Writes site/src/data/register.json. Matches the shape of the Falco archive's
register so the two sites read the same way.
"""
import json, os, sys, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from gedcom import load, display, lifespan

OUT = os.path.join(ROOT, "site", "src", "data", "register.json")

# ── Entries from records this archive has actually read ──────────────────────
# name, what the source says, source label, link (or "" when there is none)
R = []

def rec(name, says, source, link=""):
    R.append({"name": name, "says": says, "source": source, "link": link, "kind": "record"})

QBDM = "Queensland death index"
QBDM_L = "https://www.familyhistory.bdm.qld.gov.au/"

# --- Queensland civil registration, searched 9 September 2026 ----------------
for n, d, reg, mum, dad in [
    ("William Hartley Sneyd", "11/09/1902 · b. 30/09/1837", "1902/B/2776", "Catherine", "Samuel Sneyd"),
    ("Samuel Charles Sneyd", "04/07/1885", "1885/C/4045", "—", "Samuel Sneyd"),
    ("Miriam Sneyd, née Wakefield", "12/08/1909", "1909/C/1054", "Hannah Saniger", "James Wakefield"),
    ("Thomas George Sneyd", "18/10/1927", "1927/B/2729", "Miriam Wakefield", "William Hartley Sneyd"),
    ("Arthur William Hartley Sneyd", "27/05/1922", "1922/B/37152", "Miriam Wakefield", "William Hartley Sneyd"),
    ("Vivian Claude Sneyd", "10/02/1949", "1949/B/20695", "Martha Blum", "Arthur"),
    ("Vivian Ernest William Sneyd", "16/02/1920", "1920/B/31382", "Annie Spalding", "Thomas George Sneyd"),
    ("Kenneth Seigfred Sneyd", "04/02/1935", "1935/B/26753", "Martha Blum", "Arthur William Hartley"),
    ("Ernest Ephraim Sneyd", "20/10/1946", "1946/B/8931", "Miriam Wakefield", "William Hartley"),
    ("Martha Sneyd, née Blum", "19/12/1904", "1904/C/1454", "Mary Ann O'Brien", "John Blum"),
    ("Joseph Samuel Sneyd", "18/07/1905", "1905/B/5838", "Catherine Mulcahy", "Samuel Sneyd"),
    ("Gladys Beryl Sneyd", "13/12/1897", "1897/C/1623", "Annie Spalding", "Thomas George Sneyd"),
    ("Beryl Sneyd", "13/08/1905", "1905/C/3798", "Martha Blume", "Arthur Sneyd"),
    ("Samuel Hanley Stafford Sneyd", "31/07/1901", "1901/B/1543", "Catherine Mulchy", "Samuel Sneyd"),
    ("Arthur Sneyd", "16/09/1896", "1896/B/29077", "Mary Mulchay", "Samuel Sneyd"),
    ("Alice Catherine Irene Sneyd", "12/10/1914", "1914/B/20133", "Ellen Maria Corbett", "Joseph Samuel Sneyd"),
    ("Florence Elsie Sneyd, née Knight", "29/09/1996 · b. 01/07/1899", "1996/9852", "Henrietta Hickman", "Alger Lambert Knight"),
    ("Roy Sneyd", "07/09/1964", "1964/C/4344", "Jessie Steel", "Robert McDowall"),
]:
    rec(n, f"died {d} · parents: {mum} · {dad}", f"record · {QBDM} {reg}", QBDM_L)


# --- Queensland civil registration, the Wakefield family, 13 September 2026 --
# Five of Hannah's children died in Queensland and every one of their death
# registrations names their mother. Five clerks, five years, four spellings —
# which is what a real name looks like when it is written down by ear.
for n, says, reg in [
    ("Ephraim Wakefield", "died 26/05/1868 · mother: Anna Sanniger · father: James Wakefield", "1868/B/4544"),
    ("Aaron Wakefield", "died 21/09/1896 · mother: Hannah Sanegar · father: James Wakefield", "1896/C/3402"),
    ("Zillah Frederich, née Wakefield", "died 27/06/1900 · mother: Hannah Saniger · father: James Wakefield", "1900/C/3322"),
    ("Hiram Wakefield", "died 25/06/1905 · mother: Hannah Sanigar · father: James Wakefield", "1905/B/5782"),
    ("Jabez Wakefield", "died 08/02/1903 · mother: Hannah (no surname given) · father: James Wakefield", "1903/C/5058"),
    ("Hannah Wakefield", "died 04/07/1873 · father entered as “John Jenniger” — John Saniger, written by ear · mother not given", "1873/C/603"),
    ("James Wakefield", "died 08/07/1857 · father: Richard Wakefield — a generation the archive did not have", "1857/B/135"),
    ("Richard Wakefield", "named as the father of James Wakefield on his 1857 Queensland death registration — the only Gloucestershire candidate is a Richard baptised at Chedworth, 21 Dec 1770, and nothing but a name connects them", "1857/B/135"),
]:
    rec(n, says, f"record · {QBDM} {reg}", QBDM_L)

QMAR = "Queensland marriage index"
for n, says, reg in [
    ("Miriam Wakefield", "married William Hartley Sneyd · 15 November 1859 · Brisbane — she was nineteen", "1859/B/255"),
    ("William Hartley Sneyd", "married Miriam Wakefield · 15 November 1859 · Brisbane", "1859/B/255"),
    ("Hiram Wakefield", "married Margaret Birch · 29 March 1861 · Brisbane", "1861/B/129"),
    ("Aaron Wakefield", "married Elizabeth Ann Birch · 11 July 1861 · Brisbane — two brothers, two Birch sisters, four months apart", "1861/B/142"),
    ("Jabez Wakefield", "married Margaret Fraser · 22 April 1863 · Brisbane", "1863/B/539"),
    ("Zillah Wakefield", "married John Ludwig Frederick · 25 October 1871 · Brisbane", "1871/B/3366"),
]:
    rec(n, says, f"record · {QMAR} {reg}", QBDM_L)

# --- FreeREG, Berkeley St Mary, Gloucestershire (transcript 1600–1677) -------
FR = "https://www.freereg.org.uk/"
for n, says in [
    ("William Sainger", "baptised 24 May 1655 · Berkeley St Mary · father Edward Sainger · abode Wanswell"),
    ("William Sainger", "baptised 25 Jun 1657 · Berkeley St Mary · father Edward Sainger · abode Berkeley"),
    ("William Sainger", "baptised Jan 1664/5 · Berkeley St Mary · father Edward Sainger · noted “Mr Edward”"),
    ("Edward Sainger", "of Wanswell · father of the William baptised 24 May 1655"),
    ("Edward Sainger", "married Hester T* · Berkeley St Mary · 21 Feb 1654/55"),
    ("Edward Sainger", "married Mary Smyth · Berkeley St Mary · 30 Jul 1655"),
    ("Mary Smyth", "married Edward Sainger · Berkeley St Mary · 30 Jul 1655"),
    ("Agnis Sainger", "married John Winstone · Berkeley St Mary · 15 Nov 1655"),
    ("John Winstone", "married Agnis Sainger · Berkeley St Mary · 15 Nov 1655"),
    ("Richard Sainger", "baptised 1 Jun 1656 · Berkeley St Mary; buried 6 Jun 1656"),
    ("Mary Sainger", "baptised 31 Aug 1656 · Berkeley St Mary"),
    ("Edward Sainger", "baptised 24 Jun 1657 · Berkeley St Mary"),
    ("Joseph Sainger", "baptised 2 Sep 1657 · Berkeley St Mary; buried 16 Oct 1670"),
    ("Samuell Sainger", "baptised 22 Jan 1659/60 · Berkeley St Mary"),
    ("Elizabeth Sainger", "baptised 8 Mar 1662/63 · Berkeley St Mary"),
    ("Ann Sainger", "baptised 17 Aug 1667 · Berkeley St Mary"),
    ("Esther Sainger", "baptised 5 Mar 1669/70 · Berkeley St Mary"),
    ("Joane Sainger", "baptised 26 May 1670 · Berkeley St Mary"),
    ("James Sainger", "baptised 19 Aug 1671 · Berkeley St Mary"),
    ("Morgan Sainger", "baptised 30 Mar 1672 · Berkeley St Mary; a Morgan buried 23 May 1655"),
    ("Mary Sainger", "buried 27 Nov 1653 · Berkeley St Mary"),
    ("John Sainger", "buried 31 Jul 1656 · Berkeley St Mary; another buried 30 Jan 1663/64"),
    ("Grace Sainger", "buried 13 Nov 1657 · Berkeley St Mary"),
    ("Elinor Sainger", "buried 26 Apr 1661 · Berkeley St Mary"),
    ("Avis Sainger", "buried 19 Aug 1665 · Berkeley St Mary"),
    ("Margarett Sainger", "buried 15 Feb 1665/66 · Berkeley St Mary"),
    ("Agnies Sainger", "buried 2_ May 1655 · Berkeley St Mary · entered “wife of” TYLER — NOT a Sainger wife"),
    ("Thomas Sinnegar", "baptised 17 Mar 1711/12 · Dursley St James"),
    ("William Sinnegar", "baptised 6 Nov 1743 · Dursley St James"),
    ("William Sanigaer", "baptised 27 Sep 1770 · Dursley St James"),
    ("John Sinneger", "baptised 24 Feb 1677/78 · Cam St George; another 14 Nov 1680"),
]:
    rec(n, says, "record · FreeREG, parish register transcript", FR)


# --- The 1841 census, St Paul, Bristol — the people in the house ------------
CEN = "record · 1841 census, HO107/374, ED 13 p.10, Drivers Fields, St Paul, Bristol"
CEN_L = "https://www.freecen.org.uk/"
for n, says in [
    ("Lyddya Sinegar", "aged 70 · “Independent” · born outside the county · living in the Wakefield household — one of the eleven spellings of Saniger, and the tree names Hannah's mother Lydia"),
    ("James Wakefield", "aged 35 · mason journeyman · born in Gloucestershire"),
    ("Hannah Wakefield", "aged 35 · born outside the county — which is why she cannot be found in the Gloucestershire registers"),
    ("Hiram Wakefield", "aged 4 · born in Gloucestershire"),
    ("Matilda Webb", "aged 2 · born in Gloucestershire · in the household, relationship not recorded — the 1841 census records none"),
    ("Aaron Wakefield", "aged 1 · born in Gloucestershire"),
    ("Miriam Wakefield", "aged 1 · born in Gloucestershire"),
]:
    rec(n, says, CEN, CEN_L)

rec("Miriam Wakefield", "birth registered June quarter 1840 · Bristol district · volume 11, page 183 — the only Miriam Wakefield registered in England between 1839 and 1843",
    "record · FreeBMD, GRO birth index", "https://www.freebmd.org.uk/")
rec("Joseph D'Arcy", "baptised Portsea St Mary, 19 March 1780 · father Robert · mother Jean",
    "record · FreeREG, Portsea St Mary parish register", FR)
rec("William Sneyd", "married Mary Blackbourne · Madeley All Saints, 27 March 1769, entry 68 · WEAVER · witnesses Robert Sneyd and John Kidd",
    "record · FreeREG, Madeley All Saints parish register", FR)
rec("Mary Blackbourne", "married William Sneyd, weaver · Madeley All Saints, 27 March 1769",
    "record · FreeREG, Madeley All Saints parish register", FR)
rec("Robert Sneyd", "witness to the marriage of William Sneyd and Mary Blackbourne, Madeley, 27 March 1769",
    "record · FreeREG, Madeley All Saints parish register", FR)
rec("Samuel Sneyd", "baptised Madeley All Saints, 4 June 1781 · father William Sneyd, weaver — the tree puts him in 1769, which is his eldest brother's year",
    "record · FreeREG, Madeley All Saints parish register", FR)
rec("William Sneyd", "weaver of Madeley · thirteen children baptised there 1769-1794, the 1779 entry naming the mother Mary",
    "record · FreeREG, Madeley All Saints parish register", FR)
rec("Samuel Charles Sneyd", "born 13 March 1811 · baptised Hanley St John the Evangelist 28 April 1811 · father Samuel · mother Elizabeth · abode Hanley — the tree says 15 March 1810",
    "record · FreeREG, Hanley St John the Evangelist, Bishop's Transcript", FR)
rec("Mary Sneyd", "baptised Hanley 18 February 1814 · father Samuel, a SERVANT · mother Elizabeth — sister to Samuel Charles",
    "record · FreeREG, Hanley St John the Evangelist, Bishop's Transcript", FR)
rec("William Sneyd", "baptised Madeley All Saints, 12 September 1742 · father William Sneyd — and a William son of William buried there 29 September 1744",
    "record · FreeREG, Madeley All Saints parish register", FR)


# --- The General Hewitt, Brisbane, 16 December 1854 -------------------------
GH = "record · QSA S13086/ITM18474, passenger register, image DR38490"
GH_L = "https://www.archivessearch.qld.gov.au/api/download_file/DR38490"
for n, says in [
    ("James Wakefield", "aged 48 · MASON · county Gloucester · arrived Brisbane 16 Dec 1854 on the General Hewitt"),
    ("Hannah Wakefield", "aged 48 · county entered as a ditto under her husband's Gloucester — not a statement of her birthplace"),
    ("Jabez Wakefield", "aged 11 · aboard the General Hewitt"),
    ("Zillah Wakefield", "aged 8 · aboard the General Hewitt"),
    ("Ephraim Wakefield", "aged 5 · aboard the General Hewitt"),
    ("Hiram Wakefield", "aged 16 · PLUMBER · native place BRISTOL · entered among the single men"),
    ("Aaron Wakefield", "aged 14 · farm labourer · native place BRISTOL · entered among the single men"),
    ("Marion Wakefield", "aged 14 · DOMESTIC · native place BRISTOL · entered among the single women — this is Miriam"),
]:
    rec(n, says, GH, GH_L)


# --- Chatham St Mary the Virgin, Kent ---------------------------------------
CH = "record · FreeREG, Chatham St Mary the Virgin"
for n, says in [
    ("Robert D'Arcy", "buried Chatham St Mary the Virgin, 19 May 1827, entry 1571 · AGE 76 · abode Chatham — the register the tree's 1751 has always rested on"),
    ("Jean Ward", "buried as Jane D'Arcy, Chatham, 21 March 1823, entry 791 · AGE 66 · abode Chatham"),
    ("Constantine D'Arcy", "buried Chatham, 9 May 1805 · entered as Lt in the Royal Engineers"),
    ("Margarett Maria Isabella D'Arcy", "spinster · married John Maddock Jones Esq. of Penybryn, Ruabon, Denbighshire · Chatham, 23 October 1806, by licence · witness Joseph D'Arcy"),
    ("John Maddock Jones", "bachelor, Esq., of Penybryn in the parish of Ruabon, Denbighshire · married Margarett Maria Isabella D'Arcy at Chatham, 23 October 1806"),
    ("Richd Lovett", "second witness to the D'Arcy-Jones marriage, Chatham, 23 October 1806"),
    ("Frederick Robert D'Arcy", "baptised Chatham, 2 July 1811 · father George · mother MARY — the first wife"),
    ("Charlotte D'Arcy", "born 29 April 1825 · baptised Chatham 31 March 1826 · father GEORGE PITT D'ARCY, Bt: Major 39th Foot · mother MARIA · eight days before the England sailed"),
    ("George Pitt D'Arcy", "named in the Chatham register 31 March 1826 as Bt: Major 39th Foot, of Chatham"),
]:
    rec(n, says, CH, FR)


# --- The London Gazette, and the Birch household ----------------------------
LG = "https://www.thegazette.co.uk/"
rec("Robert D'Arcy", "London Gazette, 19 July 1813, issue 16755 page 1431 — “Brevet Colonel Robert D'Arcy to be Colonel, vice Evelegh”, in an Office of Ordnance list of Royal Engineers promotions. Ten Gazette notices name him between 1793 and 1819.",
    "record · The London Gazette, issue 16755 p.1431", LG)
QMAR2 = "Queensland death index"
rec("Margaret Birch", "married Hiram Wakefield 29 March 1861 · her own death registration 1898/B/30356 names her parents as JOHN BIRCH and ANNIE REEVES",
    "record · Queensland death index 1898/B/30356", QBDM_L)
rec("John Birch", "named with Annie Reeves as the parents of Margaret Birch, who married Hiram Wakefield",
    "record · Queensland death index 1898/B/30356", QBDM_L)
rec("Annie Reeves", "named with John Birch as the parents of Margaret Birch, who married Hiram Wakefield",
    "record · Queensland death index 1898/B/30356", QBDM_L)
rec("Elizabeth Ann Birch", "married Aaron Wakefield 11 July 1861 — sister to Margaret, who married his brother Hiram four months earlier",
    "record · Queensland marriage index 1861/B/142", QBDM_L)


# --- The Berkeley estate deeds, and Saniger the place -----------------------
GA = "record · Gloucestershire Archives D2957/41 (catalogue description)"
GA_L = "https://discovery.nationalarchives.gov.uk/"
for n, says in [
    ("John Saniger", "of Berkeley, YEOMAN · release of 2 November 1601 with John Smithe of Panthurste — the earliest Saniger this archive has found"),
    ("Edward Saniger", "of SANIGER, Berkeley, CLOTHIER · mortgage with Richard Holliday of Berkeley, cooper, 9 August 1692"),
    ("Edward Saniger", "of Saniger, Berkeley, GENT · mortgage with Nicholas Morse of Wicks Elme, 13 December 1709; exchange with Isaac Smyth of Dursley, clothier, 13 November 1716"),
    ("Maurice Saniger", "and Jane his wife · a suit brought by John Hardinge, Easter term 1731"),
    ("William Cowley", "of SANIGER, BERKELEY · lease from Daniel Woodward of Bristol city, wine merchant, 28 February 1749"),
    ("Elizabeth Saniger", "widow, of Thornbury, Gloucestershire · will proved 24 December 1833, TNA PROB 11/1825/326"),
]:
    rec(n, says, GA, GA_L)

rec("Robert D'Arcy", "listed among the Second Lieutenants and Practitioner Engineers of the Corps of Engineers in the printed Army List of 1778",
    "record · A List of the Officers of the Army, 1778", "https://archive.org/details/alistofficersar00offigoog")
rec("Francis D'Arcy", "listed in a half-pay section of the same 1778 Army List — a different man from Robert, and the archive was right to separate them",
    "record · A List of the Officers of the Army, 1778", "https://archive.org/details/alistofficersar00offigoog")
rec("John Maddock Jones", "of Ruabon, Denbighshire · will proved 24 January 1844, TNA PROB 11/1991/312 · and “of Penybryn esq” in a Shropshire deed of 18 February 1829, SRO 2847/7/173",
    "record · TNA PROB 11/1991/312", "https://discovery.nationalarchives.gov.uk/")

FC = "record · 1851 census, HO107/1954, 7 Oxford Road, St Philip and Jacob Out, Bristol"
FC_L = "https://www.freecen.org.uk/"
for n, says in [
    ("Thomas Sinegar", "head, aged 42, LABOURER · BORN AT BERKLEY, GLOUCESTERSHIRE · of 7 Oxford Road, Bristol"),
    ("Martha Sinegar", "wife, aged 42, CORDWAINER · born at Berkley, Gloucestershire"),
    ("Samuel Saniger", "aged 50, SHOEMAKER, at Berkeley in 1841 — with his son Samuel, 15, a butcher"),
]:
    rec(n, says, FC, FC_L)


# --- Berkeley Castle Muniments, and Bigland's monuments ---------------------
BCM = "record · Berkeley Castle Muniments (catalogue description)"
BIG = "record · Bigland, Collections relative to the County of Gloucester, 1791"
BIG_L = "https://archive.org/details/bim_eighteenth-century_historical-monumental-a_bigland-ralph_1791_1"
for n, says in [
    ("Robert Gamel", "of Saniger · his daughter Juliana named in a Berkeley deed, late 13th century — the earliest inhabitant of the place this archive has found"),
    ("Geoffrey Nel", "of Saniger IN THE PARISH OF BERKELEY · deed of 1272–1307, which is what fixes Saniger as a place"),
    ("Martin Waleys", "of Saniger · deed with Nigel de Staniteford, before 1291"),
    ("Walter Hevyner", "of Saniger, and Maud his wife · deeds with William Doly, burgess of Berkeley, 1443"),
    ("Richard Webbe", "of Saniger, Margaret his wife · deed with John Doly, burgess of Berkeley, 1473"),
]:
    rec(n, says, BCM, GA_L)
for n, says in [
    ("Edward Saniger", "of Saniger, Gent. · his wife ESTHER died 13 June 1693 and his daughter Esther was buried 16 August 1692 — Berkeley monumental inscriptions"),
    ("Edward Saniger", "of Saniger, Gent. · buried 3 December 1739, AGED 48 · his relict SUSANNA died 14 May 1744 aged 58; his daughter JANE died 15 June 1750 aged 24"),
    ("Edward Saniger", "freeholder for the tithing of Hinton at the Berkeley election of 1776"),
    ("Esther Saniger", "wife of Edward Saniger of Saniger, Gent. · died 13 June 1693"),
    ("Susanna Saniger", "relict of Edward Saniger, Gent. · died 14 May 1744, aged 58"),
    ("Jane Saniger", "daughter of Edward Saniger of Saniger, Gent. · died 15 June 1750, aged 24"),
]:
    rec(n, says, BIG, BIG_L)


# --- The older name, the estate deeds, probate, and the Hanley census ------
TNA_L = "https://discovery.nationalarchives.gov.uk/"
SWAN = "record · Berkeley Castle Muniments / Birmingham MS 3549 (catalogue descriptions)"
for n, says in [
    ("Elias de Swonhongre", "of Swanhanger · grants a messuage to William Panyter for life, 11 April 1377 — the deed Berkeley catalogues under the man and Birmingham under the PLACE, which is what proves Swanhanger and Saniger are one word"),
    ("Thomas de Swonhungre", "of Swanhanger · granted the land of Hekeriche by Sir Thomas de Berkeley, 23 November 1299"),
    ("John de Swonhungre", "of Swanhanger · leased 48 acres 45 perches by Thomas lord of Berkeley, 1 September 1316"),
    ("William Swonhungre", "of Swanhanger · brother and heir of Thomas Swonhungre of Wanswell, 1356"),
    ("William Swannanger", "of Swannanger in Gloucestershire, ESQUIRE · bound with William Newport of Lichfield for £400 to a London goldsmith, 28 November 1385; the sheriff could not find him"),
]:
    rec(n, says, SWAN, TNA_L)

DEED = "record · Gloucestershire Archives D2957/41 (catalogue description)"
for n, says in [
    ("Edward Saniger", "of Saniger, Berkeley, CLOTHIER · lends £100 on mortgage to Richard Holliday of Berkeley, cooper, 9 August 1692"),
    ("Edward Saniger", "of Saniger, Berkeley, GENT. · lends £60 on mortgage to Nicholas Morse of Wicks Elme, 13 December 1709 — the same address, seventeen years, and a different rank"),
    ("Edward Saniger", "of Saniger, Berkeley, gent. · exchanges land in Oakhunger field with Isaac Smyth of DURSLEY, clothier, 13 November 1716"),
    ("Maurice Saniger", "and JANE his wife · a fine with John Hardinge over two messuages and land in Berkeley AND DURSLEY, Easter term 1731"),
]:
    rec(n, says, DEED, TNA_L)

PRO = "record · The National Archives, PROB 11 / Gloucester Diocesan Records (catalogue)"
rec("Elizabeth Saniger", "widow, of THORNBURY, Gloucestershire · will proved 24 December 1833 (PROB 11/1825/326)", PRO, TNA_L)
rec("Samuel Sanigear", "gentleman, of CHIPPING SODBURY, Gloucestershire · will proved 6 November 1832 (PROB 11/1808/232)", PRO, TNA_L)
rec("Christian Saniger", "plaintiff in a defamation suit against Mary Millard in the Gloucester consistory court, 1768 (GDR/B4/1/387)", PRO, TNA_L)

CEN61 = "record · 1861 census, Hanley, Staffordshire (FreeCEN)"
CEN61_L = "https://www.freecen.org.uk/"
rec("Elizabeth Margaret Oliver", "WIDOW, aged 82, born Shropshire · living at Well St, Hanley, in a grocer's shop with her son James on 7 April 1861 — the street and the trade the tree gives her husband, five years after he died there", CEN61, CEN61_L)

GAZ = "record · The London Gazette, issue 16755, 19 July 1813"
GAZ_L = "https://www.thegazette.co.uk/London/issue/16755/page/1431"
rec("Robert D'Arcy", "\u201cBrevet Colonel Robert D'Arcy to be Colonel, vice Evelegh\u201d \u00b7 Office of Ordnance, Corps of Royal Engineers, gazetted 19 July 1813", GAZ, GAZ_L)


# --- The Sneyd deaths at Hanley, and the Sanigers of Chew Magna ------------
HAN = "record · Hanley St John the Evangelist, burial register (FreeREG), entry 2330"
HAN_L = "https://www.freereg.org.uk/"
rec("Samuel Sneyd", "buried 23 September 1855, AGED 77, of 91 WELL ST., Hanley \u00b7 the tree said 20 September 1856 at No 3 Well St, and the year is wrong", HAN, HAN_L)

GRO = "record · General Register Office death index (FreeBMD)"
GRO_L = "https://www.freebmd.org.uk/"
rec("Samuel Sneyd", "death registered September quarter 1855, Stoke upon Trent, volume 6b page 75 \u00b7 the only Samuel Sneyd death registered in England and Wales between 1854 and 1858", GRO, GRO_L)
rec("Elizabeth Margaret Oliver", "death registered December quarter 1861, Stoke upon Trent, volume 6b page 66 \u00b7 the tree's 1 December 1861 confirmed, eight months after the census found her at Well Street", GRO, GRO_L)

CM = "record · 1851 census, St Philip and Jacob, Bristol \u2014 HO107/1954 f.562 p.30 sch.102"
CM_L = "https://www.freecen.org.uk/"
for n, says in [
    ("William Saniger", "head, aged 27, SMITH JOURNEYMAN, of Oxford Road \u00b7 born CHEW MAGNA, SOMERSET"),
    ("Caroline Saniger", "his wife, aged 28 \u00b7 born Fishponds, Gloucestershire"),
    ("Elizabeth Saniger", "his mother, WIDOW, aged 60 \u00b7 born CHEW MAGNA, SOMERSET \u2014 the first Saniger this archive has found with a birthplace outside Gloucestershire"),
]:
    rec(n, says, CM, CM_L)

COLL = "record · Collinson, History and Antiquities of the County of Somerset (1791), vol. II"
COLL_L = "https://archive.org/details/historyantiqutit02colluoft"
rec("Chew Magna", "\u201ca large and populous parish \u2026 six miles south-west from Bristol \u2026 one hundred and seventy houses, and eight hundred and thirty inhabitants\u201d \u00b7 and \u201cin former days \u2026 a LARGE CLOTHING TOWN\u201d", COLL, COLL_L)


C41 = "record \u00b7 1841 census, Chew Magna, Somerset \u2014 piece 938 book 6 folio 6 page 6"
rec("Elizabeth Saniger", "aged 45, born Somerset \u00b7 at BATTLES LANE, CHEW MAGNA in 1841, in the house of Thomas Veale, spade maker \u2014 ten years before she appears at Oxford Road, Bristol", C41, "https://www.freecen.org.uk/")


# --- FindMyPast: the 1851 census, and the marriage --------------------------
FMP51 = "record \u00b7 1851 census, Drivers Fields, St Paul, Bristol \u2014 HO107/1949 f.478 p.14 sch.66 (FindMyPast)"
FMP_L = "https://www.findmypast.com.au/"
rec("Hannah Saniger", "wife, aged 45 \u00b7 BORN AT BERKELEY, GLOUCESTERSHIRE \u2014 the census that finally states her birthplace instead of ticking a column", FMP51, FMP_L)
rec("James Wakefield", "head, aged 45, MASON \u00b7 born at STROUD, GLOUCESTERSHIRE", FMP51, FMP_L)
rec("Miriam Wakefield", "daughter, aged 10, SERVANT \u00b7 already in work three years before she sailed", FMP51, FMP_L)
for n, says in [
    ("Hiram Wakefield", "son, aged 13, errand boy"),
    ("Aaron Wakefield", "son, aged 10, errand boy"),
    ("Jabez Wakefield", "son, aged 8 \u00b7 a child this archive had never heard of"),
    ("Zillah Wakefield", "daughter, aged 5, scholar \u00b7 a child this archive had never heard of"),
]:
    rec(n, says, FMP51, FMP_L)

FMPM = "record \u00b7 England Marriages 1538-1973 (FindMyPast)"
rec("Hannah Saniger", "married JAMES WAKEFIELD at Bristol, 17 OCTOBER 1831 \u00b7 the first English record of the marriage, and the first of any kind in England to give her the surname Saniger", FMPM, FMP_L)

FMPB = "record \u00b7 England Births & Baptisms 1538-1975, Berkeley (FindMyPast)"
rec("Daniel Saniger", "baptised at Berkeley 21 November 1821 \u00b7 father EDWARD Saniger, mother KITURA \u2014 from the stretch of the Berkeley register FreeREG does not reach", FMPB, FMP_L)


# --- FindMyPast: Portsea, and Berkeley after 1677 --------------------------
HGS = "record \u00b7 Hampshire Marriages / Baptisms, Hampshire Genealogical Society (FindMyPast)"
FMP_L2 = "https://www.findmypast.com.au/"
rec("Robert D'Arcy", "married JEAN WARD at PORTSEA ST MARY, 21 JUNE 1779 \u00b7 the marriage this archive has carried on a family tree since it began, nine months before their son Joseph was christened in the same church", HGS, FMP_L2)
rec("Jean Ward", "married ROBERT D'ARCY at Portsea St Mary, 21 June 1779", HGS, FMP_L2)
rec("Joseph D'Arcy", "baptised Portsea St Mary 19 March 1780, SON \u00b7 father ROBERT, mother JEAN \u2014 the Hampshire Genealogical Society's transcription, independent of FreeREG's", HGS, FMP_L2)

BKY = "record \u00b7 Berkeley St Mary the Virgin, after 1677 (FindMyPast \u2014 England Births & Baptisms / Marriages; National Burial Index, Gloucestershire FHS)"
for n, says in [
    ("Thomas Saniger", "baptised at Berkeley 23 AUGUST 1744, father THOMAS Saniger \u00b7 the tree gives the same day"),
    ("Thomas Saniger", "married CATHERINE COTTON at Berkeley, 10 APRIL 1769 \u00b7 a name this archive never had, and the mother of John"),
    ("Catherine Cotton", "married Thomas Saniger at Berkeley, 10 April 1769"),
    ("John Saniger", "baptised at Berkeley 18 MAY 1769, father THO'S Saniger \u00b7 the tree gives his birth as 15 May 1769"),
    ("Thomas Saniger", "buried at Berkeley St Mary the Virgin, 24 JANUARY 1819, AGED 75"),
    ("John Saniger", "buried at Berkeley St Mary the Virgin, 16 JANUARY 1825, AGED 55 \u00b7 the tree says 10 March 1824, ten months early"),
    ("William Saniger", "baptised at Berkeley 6 SEPTEMBER 1801, father JOHN Saniger \u00b7 Hannah's brother"),
    ("John Saniger", "baptised at Berkeley 18 SEPTEMBER 1803, father JNO Saniger \u00b7 Hannah's brother"),
    ("Thomas Saniger", "baptised at Berkeley 3 JULY 1808, father JOHN Saniger \u00b7 Hannah's brother"),
]:
    rec(n, says, BKY, FMP_L2)


# --- FindMyPast: the Sneyds at Well Street, and Elizabeth Oliver -----------
S51 = "record \u00b7 1851 census, Well Street, Hanley \u2014 HO107/2004 f.138 p.13 sch.46 (FindMyPast)"
FMP_L3 = "https://www.findmypast.com.au/"
rec("Samuel Sneyd", "head, aged 72, GROCER, of WELL STREET, Hanley \u00b7 born MADELEY, STAFFORDSHIRE \u2014 alive in his own shop four years before he died", S51, FMP_L3)
rec("Elizabeth Margaret Oliver", "wife, aged 71 \u00b7 born OSWESTRY, SHROPSHIRE \u2014 which settles the unreadable \u201cStaly Cladwin\u201d of the 1861 census", S51, FMP_L3)
rec("James Sneyd", "son, aged 33, ENGRAVER \u00b7 born Hanley \u2014 Samuel Charles Sneyd's brother, who stayed and kept the shop", S51, FMP_L3)

OSW = "record \u00b7 Shropshire Baptisms, Oswestry St Oswald's \u2014 Shropshire Archives P214/A/2/1 p.18 (FindMyPast)"
rec("Elizabeth Margaret Oliver", "born 17 MAY 1782, baptised 19 May 1782 at Oswestry St Oswald's \u00b7 father DAVID OLIVER, mother MARY \u2014 the tree says 7 May 1787, two digits away", OSW, FMP_L3)
rec("David Oliver", "of Oswestry \u00b7 father of Elizabeth, baptised there 19 May 1782 \u2014 a generation this archive did not have", OSW, FMP_L3)


STR = "record \u00b7 England Births & Baptisms 1538-1975, Stroud (FindMyPast)"
FMP_L4 = "https://www.findmypast.com.au/"
rec("James Wakefield", "baptised at STROUD 6 APRIL 1806 \u00b7 father RICHARD WAKEFIELD, mother ELIZABETH WEBB \u2014 matching the birthplace the 1851 census gives him, and naming a generation this archive did not have", STR, FMP_L4)
rec("Richard Wakefield", "of Stroud \u00b7 father of James, baptised there 6 April 1806", STR, FMP_L4)
rec("Elizabeth Webb", "of Stroud \u00b7 mother of James Wakefield \u2014 and a Matilda WEBB, aged two, is living in James's house at Drivers Fields in 1841", STR, FMP_L4)
rec("Jabez Wakefield", "birth registered at Bristol, 1843", "record \u00b7 England & Wales Births 1837-2006 (FindMyPast)", FMP_L4)


BRI = "record \u00b7 Gloucestershire Burials / England Births & Baptisms, Bristol (FindMyPast)"
FMP_L5 = "https://www.findmypast.com.au/"
rec("Ellen Wakefield", "baptised at Bristol 26 OCTOBER 1834 \u00b7 father JAMES WAKEFIELD, mother HANNAH \u2014 the first baptism of any of their children found", BRI, FMP_L5)
rec("Ellen Wakefield", "buried at BRISTOL, ST PAUL, PORTLAND SQUARE, 12 JULY 1840, AGED 5 \u00b7 Bristol Archives P/St P/R/3/3 \u2014 she did not stay behind in 1854; she died fourteen years before the ship", BRI, FMP_L5)


BNA = "record \u00b7 British Newspaper Archive, 17 notices, May\u2013June 1827 (FindMyPast)"
BNA_L = "https://www.findmypast.com.au/search-newspapers"
rec("Robert D'Arcy", "\u201cAt Chatham, on the 13th instant, Major-General D'Arcy, late of the Corps of Royal Engineers\u201d \u00b7 Morning Chronicle, 17 May 1827 \u2014 his death date from the contemporary press rather than from Connolly's book of 1898", BNA, BNA_L)
rec("Robert D'Arcy", "\u201cOn Saturday Major-General D'Arcy, whose death we announced last week, WAS INTERRED AT CHATHAM WITH MILITARY HONOURS\u201d \u00b7 Kent Herald, 24 May 1827 \u2014 the Saturday was 19 May, the date of entry 1571 in Chatham's burial register", BNA, BNA_L)
rec("Robert D'Arcy", "\u201cAt Chatham, AT AN ADVANCED AGE, Major General D'Arcy\u201d \u00b7 Kent Herald, 17 May 1827 \u2014 and not one of the seventeen notices gives his forename or names a single relative", BNA, BNA_L)


BKY2 = "record \u00b7 Berkeley St Mary the Virgin, England Births & Baptisms 1538-1975 (FindMyPast)"
FMP_L6 = "https://www.findmypast.com.au/"
rec("William Saniger", "baptised at Berkeley 12 OCTOBER 1679, father WILLIAM Saniger \u00b7 the family tree gives 12 October 1679 \u2014 the same day", BKY2, FMP_L6)
rec("Thomas Saniger", "baptised at Berkeley 12 DECEMBER 1711, father WILLIAM Saniger \u00b7 the tree gives his birth as 11 December 1711", BKY2, FMP_L6)

QLD2 = "record \u00b7 Queensland Marriages / Burials & Memorials (FindMyPast)"
rec("Jabez Wakefield", "married in Queensland 1863 and buried there 1903 \u00b7 born Bristol 1843, he sailed on the General Hewitt at eleven", QLD2, FMP_L6)
rec("Zillah Wakefield", "married in Queensland 1871 \u00b7 born Bristol 1845, she sailed on the General Hewitt at eight", QLD2, FMP_L6)


ARMY = "record · British Army Lists & Commission Registers 1661-1826 / Officer Promotions 1800-1815 (FindMyPast), citing the London Gazette"
FMP_L7 = "https://www.findmypast.com.au/"
for _says in [
    "1778 · PRACTITIONER ENGINEER AND SECOND LIEUTENANT, The Corps of Engineers — his first commission, and the earliest record of him in this archive",
    "8 May 1802 · Captain promoted MAJOR IN THE ARMY, Royal Engineers · War Office 11 May 1802 · London Gazette 15478 p.468",
    "1 March 1805 · Brevet Major promoted LIEUTENANT-COLONEL, Corps of the Royal Engineers, vice Nepean · Ordnance Office 18 March 1805 · London Gazette 15789 p.351",
    "4 June 1813 · Lieutenant-Colonel promoted COLONEL IN THE ARMY BY BREVET by the Prince Regent · War Office 7 June 1813 · London Gazette 16737 p.1100",
]:
    rec("Robert D'Arcy", _says, ARMY, FMP_L7)
rec("Joseph D'Arcy", "ROYAL ARTILLERY · in the officers' list from 1795, the Army List of 1798, the commission registers of 1802, 1803 and 1826, and the Army Lists of 1840–1844 — commissioned at about fifteen and still listed at sixty-four", "record · British Army Royal Artillery Officers 1716-1899 and Army Lists (FindMyPast, index only)", FMP_L7)


SCO = "record · Scotland, Parish Births & Baptisms 1564-1929, South Leith (FindMyPast)"
FMP_L8 = "https://www.findmypast.com.au/"
rec("Jean Ward", "baptised at SOUTH LEITH, MIDLOTHIAN, 19 JULY 1754 · father JOSEPH WARD, mother MARTHA GARDEN — the parish this archive had repeatedly reported as untranscribed", SCO, FMP_L8)
rec("Joseph Ward", "of South Leith, Midlothian · father of Jean, baptised there 19 July 1754 — and the man her eldest son was named for", SCO, FMP_L8)
rec("Martha Garden", "of South Leith, Midlothian · mother of Jean Ward", SCO, FMP_L8)
rec("George Pitt D'Arcy", "39TH FOOT, Peninsular War officers' roll, 1808 · the same regiment he commanded a detachment of aboard the convict ship England in 1826", "record · Peninsular War, British Army Officers 1808-1814 (RUSI, via FindMyPast)", FMP_L8)


SCO2 = "record · Scotland, Parish Marriages & Banns 1561-1893, South Leith (FindMyPast)"
FMP_L9 = "https://www.findmypast.com.au/"
rec("Joseph Ward", "married MARTH[A] GAIRDEN at SOUTH LEITH, 27 OCTOBER 1747 · her father WILLIAM GAIRDEN — seven years before their daughter Jean was christened in the same parish", SCO2, FMP_L9)
rec("Martha Garden", "married Joseph Ward at South Leith, 27 October 1747 · entered as MARTH GAIRDEN, daughter of WILLIAM GAIRDEN", SCO2, FMP_L9)
rec("William Gairden", "of South Leith, Midlothian · named as Martha's father at her marriage in 1747 — the oldest Scot in this archive", SCO2, FMP_L9)


BRI2 = "record · England Births & Baptisms / Deaths & Burials 1538-1991, Bristol (FindMyPast)"
FMP_LA = "https://www.findmypast.com.au/"
rec("Eliza Wakefield", "baptised at Bristol 14 OCTOBER 1832 · father JAMES WAKEFIELD, mother HANNAH", BRI2, FMP_LA)
rec("Eliza Wakefield", "buried at Bristol 4 MAY 1834, AGED 19 MONTHS · the eldest of the three daughters this archive believed had been left behind in 1854", BRI2, FMP_LA)

SN71 = "record · 1871 and 1881 censuses, Well Street, Hanley — RG10/2857 f.37 p.10; RG11/2719 f.12 p.18 (FindMyPast)"
rec("James Sneyd", "of WELL STREET, Hanley · engraver at 53 in 1871 with his son James A, also an engraver; ENGRAVER (POTTER) at 63 in 1881 at No. 20, with his granddaughter Mary Elizabeth MULLOCK (Sneyd) · his father kept the grocer's shop in the same street in 1851", SN71, FMP_LA)


SIN = "record · 1841 census and Bristol parish registers, St Philip and Jacob (FindMyPast)"
FMP_LB = "https://www.findmypast.com.au/"
rec("Thomas Saniger", "THOMAS SINEGAR, 30, at Sion Road, Johns Place, St Philip & Jacob Without, 1841 · with Martha 31, James 11, LYDIA 9, Thomas 7, Martha 2 — HO107/378 bk5 f.40 p.26 sch.1633 · and in 1851, aged 42, a labourer at 7 Oxford Road BORN BERKLEY, GLOUCESTERSHIRE", SIN, FMP_LB)
rec("Lydia Sinegar", "baptised at Bristol, St Philip and Jacob, 28 JANUARY 1866 · father JAMES SINEGAR, mother Laura — Bristol Archives P/St P&J/R/2/24 · the third Lydia in three generations of this Bristol household", SIN, FMP_LB)
rec("Thomas Sinegar", "married JULIA MARSH at Bristol, St Matthias, 28 MAY 1871 · father THOMAS SINEGAR — Bristol Archives P/St.Mat/R/2/b", SIN, FMP_LB)


HB = "record · England Births & Baptisms 1538-1975, Berkeley — confirmed on FamilySearch and FindMyPast"
FMP_LC = "https://www.findmypast.com.au/"
rec("Hannah Saniger", "baptised HANNAH SANIGOR at BERKELEY, 18 AUGUST 1804 · father JNO SANIGOR — the baptism this archive twice declared missing, indexed under a spelling its own alias list did not carry", HB, FMP_LC)
rec("Ann Saniger", "baptised at Berkeley 1798, father John Saniger · Hannah's eldest sister", HB, FMP_LC)
rec("Martha Golding", "married THOMAS SANIGER at Bristol St James, 24 August 1828 · the mother of his eleven children, two of whom he named JOHN and one LYDIA and one HANNAH", "record · FamilySearch Family Tree (marriage unsourced there)", "https://www.familysearch.org/tree/person/details/KZ2H-JBP")
rec("Thomas Saniger", "died 1 OCTOBER 1881 at Waterloo Lane, Bristol, and was buried at Greenbank Cemetery, Eastville · baptised Berkeley 3 July 1808, son of John", "record · FamilySearch Family Tree", "https://www.familysearch.org/tree/person/details/KZ2H-JBP")

# --- Australian Imperial Force service records ------------------------------
NAA = "https://recordsearch.naa.gov.au/"
rec("Arthur Hartley Sneyd", "5050 · 9th Battalion · attested Brisbane 16 Sep 1915, aged 21y11m · typist · Baptist · 5ft 7½in · killed in action 20 Aug 1916",
    "record · NAA B2455, item 8088453 (30 pp., read in full)", NAA)
rec("Vivian Claude Sneyd", "1696 · 3rd Australian Field Ambulance · enlisted Brisbane 16 Jul 1915, aged 19y7m · salesman of Windsor · 1914/15 Star · discharged 30 Jul 1919",
    "record · NAA B2455, item 8087524 (21 pp.)", NAA)
rec("Ernest Vivian William Sneyd", "3891 · 31st Battalion · attested 4 Dec 1915, aged 25y2m · labourer · previously rejected on height · albuminuria 1918 · home 5 Jan 1919",
    "record · NAA B2455, item 8087517 (92 pp.)", NAA)
rec("Thomas George Sneyd", "of Landsborough, Queensland · named as next of kin (father) on the attestation of 3891",
    "record · NAA B2455, item 8087517", NAA)
rec("Ivy Marion D'Arcy", "beneficiary of Lindesay Atkinson D'Arcy, 11335 · repatriation pension case file, 1937–38",
    "record · NAA J34, C34558", NAA)
rec("Vivian Claud Sneyd", "1696 · L/Cpl, 3rd Aust. Fld. Ambce. · Bar to the Military Medal, Westhoek, 4 Oct 1917 · endorsed “Awarded”",
    "record · AWM 28 recommendation file", "https://www.awm.gov.au/")
rec("A. Graham Butler", "Lieut-Col., A.D.M.S., 1st Australian Division · signed the Bar recommendation, 12 Oct 1917",
    "record · AWM 28 recommendation file", "https://www.awm.gov.au/")
rec("Vivian Maynard", "3rd Field Ambulance, A.I.F., M.M. · of Bowen Bridge Road · enlisted with Vivian Sneyd in 1915, Gallipoli and France together",
    "record · Brisbane Courier, 18 Jan 1919", "https://nla.gov.au/nla.news-article20275988")

# --- Red Cross Wounded and Missing Enquiry Bureau, AWM 1DRL/0428 ------------
RC = "record · AWM 1DRL/0428, Wounded and Missing file for 5050 Sneyd"
RCL = "https://www.awm.gov.au/"
for n, says in [
    ("P. R. Rhead", "Pte 4280, C Coy, 1 A.D.B.D. · Étaples, 3 Nov 1916 · reported Sneyd killed by a shell"),
    ("R. Kent", "Pte, B Coy, 9th Battalion · the man who said he saw Sneyd killed"),
    ("Clark", "L/Cpl 1328, A Coy · No. 1 Canadian General Hospital, Étaples, 4 Dec 1916 · saw three men struck by one shell"),
    ("George Holloway", "Pte 5377, A Coy · 1 Convalescent Depot, Étaples, 4 Dec 1916 · “his death is mysterious”"),
    ("A. Lee", "Cpl 1370, A Coy 2 Pl · No. 9 General Hospital, Rouen, 16 Dec 1916 · spoke to Sneyd the morning after he was thought dead"),
    ("H. Kendrick", "Cpl, 1st A.D.B.D. · said the pioneers put Sneyd over the parapet and he crawled back next morning"),
    ("George Walsh", "Pte, later Lieut · No. 4 Officer Cadet Battalion, New College, Oxford · Sneyd's closest friend; searched for him for thirteen months"),
    ("Morton", "Sgt, 10th Battalion · reported 1 Sep 1917 that Sneyd was killed at Mouquet Farm on 22 Aug 1916 and buried under a wooden cross"),
]:
    rec(n, says, RC, RCL)

# --- The 1902 coronial file, QSA ITM2736504 / DR103140 ----------------------
QC = "record · QSA coronial file ITM2736504 (DR103140), read in full"
QCL = "https://www.archivessearch.qld.gov.au/items/ITM2736504"
for n, says in [
    ("William Hartley Sneyd", "found dead in Victoria Park, Brisbane, 12 Sep 1902 · contractor · cause “Poisoning (suicide)”"),
    ("Miriam Sneyd", "widow · sworn deposition naming his father “Samuel Sneyd, Gaol Governor” and his mother Catherine"),
    ("John Williams", "labourer, of Roche Street, Spring Hill · found the body"),
    ("Alfred Hutchison", "walked the railway line in Victoria Park with John Williams and saw the body"),
    ("Edward Law", "retired, of Hartley Street off Gregory Terrace · last to speak to him · signed with his mark"),
    ("Patrick Moroney", "police constable, Brisbane · recovered the body; handed a knife, spectacles and two handkerchiefs to a son"),
    ("Mrs Costello", "caretaker of Victoria Park · the death was first reported to her"),
    ("Dr Dods", "Government Medical Officer · performed the post-mortem, 12 Sep 1902"),
    ("J. Brownlie Henderson", "Government Analyst · found 1¼ oz of crude carbolic acid in the stomach, 22 Sep 1902"),
    ("R. D. Neilson", "J.P. · presided at the magisterial inquiry, Brisbane Police Court, 29 Sep 1902"),
    ("Ahern", "Sub-Inspector · conducted the inquiry"),
    ("E. M. Murray", "Police Magistrate · ordered the post-mortem"),
    ("Hislop", "undertaker · John Hislop & Sons of Peel Street, South Brisbane"),
    ("Peter N. Paulsen", "farmer of Meringandan · an unrelated case bound into the same file"),
]:
    rec(n, says, QC, QCL)

# --- The convict ship England, TNA ADM 101/26/1 -----------------------------
ADM = "record · TNA ADM 101/26/1, surgeon's journal of the England"
ADML = "https://discovery.nationalarchives.gov.uk/details/r/C1958733"
for n, says in [
    ("George Thomson", "Surgeon and Superintendent of the convict ship England, 18 Mar – 29 Sep 1826"),
    ("George Pitt D'Arcy", "B. Major · commanded the detachment of the 39th Foot: 39 men, 6 women, 7 children, embarked 8 Apr 1826 · recovered from gout 16 Aug 1826"),
    ("John Wells", "convict · suspected of breaking open Major D'Arcy's crate of dinner ware, 17 May 1826"),
    ("William Kerr", "convict · suspected with John Wells"),
    ("Robert Hughes", "convict · threatened the surgeon; three knives traced to him"),
    ("Henry Stone", "convict · accused of stealing a pair of trousers"),
    ("John Quin", "convict · accused of giving false evidence"),
    ("John Chapman", "convict · handcuffed 15 May 1826 for taking his irons off"),
]:
    rec(n, says, ADM, ADML)

# --- Queensland Blue Books, 1870–1900 --------------------------------------
BB = "https://archive.org/search?query=queensland+blue+book"
for n, says in [
    ("William Hartley Sneyd", "Fount-room Overseer, Government Printing Office · £225 · in the public service from 1 Feb 1862 · last listed 1890"),
    ("Samuel Hanley Stafford Sneyd", "Clerk and Locker, Customs, at Gladstone · £160 · entered 24 Jan 1877"),
    ("Arthur Sneyd", "Operator and later Officer in Charge, Electric Telegraph · £100 rising to £200 · entered 10 Sep 1880"),
    ("Ernest Ephraim Sneyd", "Line Repairer, Electric Telegraph · £120 rising to £140 · entered 9 Jan 1884"),
]:
    rec(n, says, "record · Queensland Blue Books (civil establishment lists)", BB)

# --- Queensland State Archives, other series -------------------------------
QSA = "https://www.archivessearch.qld.gov.au/"
for n, says, item in [
    ("Arthur Hartley Sneyd", "intestacy file, Public Trust Office, 26 Mar 1916 – 30 Nov 1917 · file 687/1917", "ITM1412361"),
    ("William Hartley Sneyd", "insolvency, Public Curator Office Brisbane · file 230/1873 · 6 Oct – 3 Nov 1873", "ITM1056950"),
    ("Samuel Sneyd", "mortgagor to James Gibbon · Subdivision 3, Portions 152–153, Parish of North Brisbane, 1870", "ITM3248152"),
    ("Samuel Sneyd", "mortgagor to the Brisbane Mutual Building and Investment Society · Allotment 293, Parish of North Brisbane, 1872", "ITM3622143"),
    ("Samuel Sneyd", "one of three trustees, with James Voller and William Bell, Parish of Enoggera, 1872", "ITM3621487"),
    ("James Voller", "trustee with Samuel Sneyd and William Bell, Parish of Enoggera, 1872", "ITM3621487"),
    ("William Bell", "trustee with Samuel Sneyd and James Voller, Parish of Enoggera, 1872", "ITM3621487"),
    ("Richard George Petty", "settlor · Resubdivision A, Subdivision 3, Portion 417, Parish of Enoggera, 1872", "ITM3621487"),
    ("Samuel Hanley Stafford Sneyd", "vendor to John Hennessey · Portion 209, Parish of South Brisbane, 1877", "ITM4088729"),
    ("Roy Sneyd", "alias Raymond Smith · photographic record and criminal history, 29 Apr 1922 — NOT published on this site", "ITM86903"),
    ("SNEYD, Hanley", "Queensland Police staff file AF1623 · 7 Dec 1881 – 28 Feb 1883", "ITM564421"),
    ("SNEYD, Samuel Charles", "Queensland Police staff file AF1599 · 8 May 1890 – 30 Sep 1897", "ITM564398"),
]:
    rec(n, says, f"record · QSA {item}", QSA + "items/" + item)

# --- The National Archives (UK) --------------------------------------------
rec("Robert D'Arcy", "will proved 4 July 1827 · “Major General in the Army and Colonel of the Royal Engineers of Chatham, Kent”",
    "record · TNA PROB 11/1728/64 (digitised, unread)", "https://discovery.nationalarchives.gov.uk/details/r/D192027")
rec("Robert D'Arcy", "entry 203 · 2nd Lt 17 Jan 1776 → Major-General 12 Aug 1819, C.B. · “Died at Chatham, 13 5 1827”",
    "record · Connolly, Roll of Officers of the Corps of Royal Engineers", "https://archive.org/")
rec("Constantine D'Arcy", "entry 335 · “Died at Chatham, 6 5 1805” · christened St Michael, Barbados, 18 Feb 1786",
    "record · Connolly, Roll of Officers of the Corps of Royal Engineers", "https://archive.org/")
rec("Francis D'Arcey", "alias Francis D'Arcy · born Sovell, Galway · served 39th and 45th Foot — a different man",
    "record · TNA WO 97/1144/236", "https://discovery.nationalarchives.gov.uk/")

# --- Trove ------------------------------------------------------------------
for n, says, art in [
    ("George Pitt D'Arcy", "obituary · died Parramatta 22 Jul 1849, aged 69 · verdict “gout which had flown to the head”", "59769271"),
    ("Lindsay Atkinson D'Arcy", "obituary · died suddenly 10 Nov 1936, aged 44, of Botany Street, Clayfield", "37013266"),
    ("Arthur Sneyd", "“Q.M.S. Arthur Sneyd, killed in action at Pozières” · memorial notice, 20 Aug 1919", "20379031"),
    ("Ruby", "signed a memorial notice for Q.M.S. Arthur Sneyd, 20 Aug 1919 — surname unknown", "20379031"),
    ("Samuel Charles Sneyd", "obituary, The Queenslander, 11 Jul 1885", "19799164"),
    ("J. A. McIntyre", "wrote the letter to the Brisbane Courier, 7 Jul 1885, from which the obituary was taken", "3443970"),
]:
    rec(n, says, "record · Trove, Australian newspapers", f"https://nla.gov.au/nla.news-article{art}")


# ── The two grafts, so the register can say which people hang on them ─────────
HORNBY_ROOT = "@I1872@"     # Thomas (Francis) D'Arcy — unevidenced
KEELE_ROOT  = "@I501870@"   # Ralph Sneyd of Keele, b. 10 Dec 1723 — disproved


def ancestors_of(pid, people, families):
    """pid and everyone above it."""
    seen, stack = set(), [pid]
    while stack:
        x = stack.pop()
        if x in seen or x not in people:
            continue
        seen.add(x)
        for fid in people[x].get("famc", []):
            fam = families.get(fid, {})
            for role in ("husb", "wife"):
                if fam.get(role):
                    stack.append(fam[role])
    return seen


def kebab(s):
    import unicodedata
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def slugs_for(recs):
    """Reproduce site/src/lib/people.js exactly, so every link resolves."""
    counts = collections.Counter(kebab(r["name"]) for r in recs)
    used, out = set(), {}
    for r in recs:
        base = kebab(r["name"]) or "unnamed"
        slug = base
        if counts[base] > 1:
            m = re.search(r"\d{4}", (r.get("born") or "") + (r.get("died") or ""))
            slug = f"{base}-{m.group(0)}" if m else base
        while slug in used:
            slug += "-2"
        used.add(slug)
        out[r["id"]] = slug
    return out


ROMAN = re.compile(r"^(?=[IVXLC]+$)M*(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", re.I)


def surname_of(rec):
    """The tree's own surname field, except where it holds a regnal number —
    the royal graft carries people as “Christian V” with V in the surname."""
    s = (rec.get("surname") or "").strip()
    if s and (ROMAN.match(s) or len(s) < 2):
        s = ""
    if not s:
        n = re.sub(r"\([^)]*\)", " ", rec.get("name") or "")
        n = re.sub(r",.*$", "", n)
        parts = [x for x in n.split() if x and not ROMAN.match(x)]
        s = parts[-1] if parts else ""
    s = re.sub(r"[?)(,.]+$", "", s.strip())
    return (s or "—").upper()


# ── Relationships a record actually asserts ──────────────────────────────────
# Every one of these is a parent/child or marriage link written down in a
# document this archive has read, not inferred from the tree. The person pages
# draw these edges solid and everything else dotted, so a reader can see at a
# glance how much of any pedigree is evidence and how much is belief.
#   (person, relative, what the record is)
REL = [
    # Queensland death registrations name the deceased's parents outright.
    ("William Hartley Sneyd", "Samuel Charles Sneyd|1810", "Qld death reg. 1902/B/2776"),
    ("William Hartley Sneyd", "Catherine Margaret Mulcahy", "Qld death reg. 1902/B/2776"),
    ("William Hartley Sneyd", "Miriam Wakefield", "her sworn deposition, DR103140"),
    ("Miriam Wakefield", "James Wakefield", "Qld death reg. 1909/C/1054"),
    ("Miriam Wakefield", "Hannah Saniger", "Qld death reg. 1909/C/1054"),
    ("Thomas George Sneyd", "William Hartley Sneyd", "Qld death reg. 1927/B/2729"),
    ("Thomas George Sneyd", "Miriam Wakefield", "Qld death reg. 1927/B/2729"),
    ("Arthur William Hartley Sneyd", "William Hartley Sneyd", "Qld death reg. 1922/B/37152"),
    ("Arthur William Hartley Sneyd", "Miriam Wakefield", "Qld death reg. 1922/B/37152"),
    ("Ernest Ephraim Sneyd", "William Hartley Sneyd", "Qld death reg. 1946/B/8931"),
    ("Ernest Ephraim Sneyd", "Miriam Wakefield", "Qld death reg. 1946/B/8931"),
    ("Vivian Claude Sneyd", "Arthur William Hartley Sneyd", "Qld death reg. 1949/B/20695"),
    ("Vivian Claude Sneyd", "Martha Blum", "Qld death reg. 1949/B/20695"),
    ("Kenneth Seigfried Sneyd", "Arthur William Hartley Sneyd", "Qld death reg. 1935/B/26753"),
    ("Kenneth Seigfried Sneyd", "Martha Blum", "Qld death reg. 1935/B/26753"),
    ("Beryl Marie Sneyd", "Arthur William Hartley Sneyd", "Qld death reg. 1905/C/3798"),
    ("Beryl Marie Sneyd", "Martha Blum", "Qld death reg. 1905/C/3798"),
    ("Vivian Ernest William Sneyd", "Thomas George Sneyd", "Qld death reg. 1920/B/31382"),
    ("Gladys Beryl Sneyd", "Thomas George Sneyd", "Qld death reg. 1897/C/1623"),
    ("Martha Blum", "John Blum|1842", "Qld death reg. 1904/C/1454"),
    ("Martha Blum", "Mary Ann O'Brien", "Qld death reg. 1904/C/1454"),
    # The service records name a next of kin in the man's own hand.
    ("Vivian Ernest William Sneyd", "Thomas George Sneyd", "NAA B2455 attestation, next of kin"),
    ("Arthur Hartley Sneyd", "Miriam Wakefield", "NAA B2455 8088453, next of kin"),
    ("Ivy Miriam Sneyd", "Lindesay Atkinson D'Arcy", "NAA J34 C34558, pension beneficiary"),
    ("Charlotte Maria D'Arcy", "George Pitt D'Arcy|1783", "baptism, Chatham, 31 Mar 1826"),
    ("Frederick Robert D'Arcy", "George Pitt D'Arcy|1783", "baptism, Chatham, 2 Jul 1811"),
    ("Samuel Sneyd|1769", "William Sneyd|1746", "baptism, Madeley, 4 Jun 1781; marriage, Madeley, 27 Mar 1769"),
    ("Samuel Charles Sneyd|1810", "Samuel Sneyd", "baptism, Hanley, 28 Apr 1811"),
    ("William Sneyd|1746", "Mary Blackbourne", "marriage, Madeley, 27 Mar 1769"),
    ("Hiram Wakefield", "Margaret Birch", "Qld marriage reg. 1861/B/129"),
    ("Aaron Wakefield", "Elizabeth Ann Birch", "Qld marriage reg. 1861/B/142"),
    ("Miriam Wakefield", "William Hartley Sneyd", "Qld marriage reg. 1859/B/255"),
    ("Hiram Wakefield", "James Wakefield", "Qld death reg. 1905/B/5782"),
    ("Aaron Wakefield", "James Wakefield", "Qld death reg. 1896/C/3402"),
    ("Jabez Wakefield", "James Wakefield", "Qld death reg. 1903/C/5058"),
    ("Zillah Wakefield", "James Wakefield", "Qld death reg. 1900/C/3322"),
    ("Ephraim Wakefield **", "James Wakefield", "Qld death reg. 1868/B/4544"),
    ("Miriam Wakefield", "James Wakefield", "Qld death reg. 1909/C/1054"),
    ("Miriam Wakefield", "Hannah SANIGER", "Qld death reg. 1909/C/1054"),
    ("Hiram Wakefield", "Hannah SANIGER", "Qld death reg. 1905/B/5782 — “Hannah Sanigar”"),
    ("Aaron Wakefield", "Hannah SANIGER", "Qld death reg. 1896/C/3402 — “Hannah Sanegar”"),
    ("Zillah Wakefield", "Hannah SANIGER", "Qld death reg. 1900/C/3322 — “Hannah Saniger”"),
    ("Ephraim Wakefield **", "Hannah SANIGER", "Qld death reg. 1868/B/4544 — “Anna Sanniger”"),
    ("Hannah SANIGER", "John Saniger", "Qld death reg. 1873/C/603 — entered “John Jenniger”"),
    ("Hannah SANIGER", "James Wakefield", "named together on five children's death registrations"),
    ("Joseph D'Arcy", "Robert D'Arcy", "baptism, Portsea St Mary, 19 Mar 1780"),
    ("Joseph D'Arcy", "Jean Ward", "baptism, Portsea St Mary, 19 Mar 1780"),
    ("Robert D'Arcy", "Jean Ward", "named together as parents, Portsea, 19 Mar 1780"),
    # Deliberately NOT here: George Pitt D'Arcy to Robert D'Arcy. Connolly's
    # Roll documents both men's whole careers and records no parentage for
    # either — see /hornby. The tree asserts the link; no record this archive
    # has read does, and drawing it solid would be exactly the error /register
    # was built to expose.
]


def main():
    people, families = load()

    # the published set, decided once, in site/src/lib/people.js's own terms
    by_id = {}
    src = json.load(open(os.path.join(ROOT, "site/src/data/ancestors.json"), encoding="utf-8"))
    fams = json.load(open(os.path.join(ROOT, "site/src/data/families.json"), encoding="utf-8"))
    for r in src:
        if not r.get("living"):
            by_id.setdefault(r["id"], {}).update(r)
    for f in fams:
        for r in f["members"]:
            if not r.get("living"):
                by_id.setdefault(r["id"], {}).update(r)

    recs = sorted(by_id.values(), key=lambda r: (
        int((re.search(r"\d{4}", r.get("born") or "") or ["9999"])[0]
            if re.search(r"\d{4}", r.get("born") or "") else 9999),
        r["name"]))
    slug = slugs_for(recs)

    hornby = ancestors_of(HORNBY_ROOT, people, families)
    keele = ancestors_of(KEELE_ROOT, people, families)
    # 243 direct ancestors; the spine is the 15 of them the site walks page by page
    direct = {r["id"] for r in src}
    spine = {r["id"] for r in json.load(
        open(os.path.join(ROOT, "site/src/data/line.json"), encoding="utf-8"))}

    entries = []
    for r in recs:
        bits = []
        life = (r.get("life") or "").strip()
        if life:
            bits.append(life)
        if r.get("occupation"):
            bits.append(r["occupation"])
        place = r.get("bornPlace") or r.get("diedPlace") or ""
        if place:
            bits.append(place)
        if not bits:
            bits.append("no dates, no place — a name and a position in the tree")

        if r["id"] in hornby:
            source = "family tree · above the Hornby graft"
        elif r["id"] in keele:
            source = "family tree · above the Keele graft"
        elif r["id"] in direct:
            source = "family tree · direct line"
        else:
            source = "family tree"

        entries.append({"name": r["name"], "says": " · ".join(bits),
                        "source": source, "link": "/people/" + slug[r["id"]],
                        "kind": "tree", "sur": surname_of(r)})

    for e in R:
        n = re.sub(r"\([^)]*\)", " ", e["name"])
        n = re.sub(r",.*$", "", n)
        parts = [x for x in n.split() if x and not ROMAN.match(x)]
        e["sur"] = re.sub(r"[?)(,.]+$", "", parts[-1] if parts else "—").upper()
    entries.extend(R)

    groups = collections.defaultdict(list)
    for e in entries:
        groups[e.pop("sur")].append(e)
    ordered = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))

    data = {
        "entries": len(entries),
        "distinct": len({e["name"] for e in entries}),
        "records": sum(1 for e in entries if e["kind"] == "record"),
        "tree": sum(1 for e in entries if e["kind"] == "tree"),
        "grafted": sum(1 for e in entries if "graft" in e["source"]),
        "linked": sum(1 for e in entries if e["link"]),
        "surnames": len(ordered),
        "groups": [{"surname": s, "n": len(v),
                    "rows": sorted(v, key=lambda e: (e["kind"] != "record", e["name"]))}
                   for s, v in ordered],
    }

    # ── provenance, keyed by slug, for the pedigree charts ──────────────────
    by_name = collections.defaultdict(list)
    by_rec = {r["id"]: r for r in recs}
    for r in recs:
        by_name[r["name"].lower()].append(r["id"])

    def ids_for(name):
        """Exactly one person, or nothing. This family reuses forenames without
        mercy — two George Pitt D'Arcys, three Conyers, two Samuel Charles
        Sneyds — and an ambiguous match here would draw a recorded edge onto
        the wrong man, which is the one failure this whole page exists to
        prevent. Write "Name|1810" to name the year and settle it."""
        name, _, hint = name.partition("|")
        n = name.strip().lower()
        hits = by_name.get(n, [])
        if hint:
            hits = [i for i in hits
                    if hint in ((by_rec[i].get("born") or "") + (by_rec[i].get("died") or ""))]
        return hits if len(hits) == 1 else []

    prov = {}
    unmatched = []
    for a, b, why in REL:
        ia, ib = ids_for(a), ids_for(b)
        if not ia or not ib:
            unmatched.append(a if not ia else b)
            continue
        for x, y in ((ia, ib), (ib, ia)):
            for i in x:
                e = prov.setdefault(slug[i], {"rel": {}, "graft": None, "line": False, "spine": False})
                for j in y:
                    e["rel"].setdefault(slug[j], []).append(why)

    for r in recs:
        e = prov.setdefault(slug[r["id"]], {"rel": {}, "graft": None, "line": False})
        e["line"] = r["id"] in direct
        e["spine"] = r["id"] in spine
        if r["id"] in hornby:
            e["graft"] = "Hornby"
        elif r["id"] in keele:
            e["graft"] = "Keele"

    with open(os.path.join(ROOT, "site/src/data/provenance.json"), "w", encoding="utf-8") as f:
        json.dump(prov, f, ensure_ascii=False, indent=0)
    if unmatched:
        print("  REL names that are ambiguous or absent, so no edge was drawn:")
        for x in sorted(set(unmatched)):
            print("   ·", x)
    edges = sum(len(v["rel"]) for v in prov.values()) // 2
    print(f"provenance: {edges} recorded relationships across "
          f"{sum(1 for v in prov.values() if v['rel'])} people")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=0)
    print(f"entries {data['entries']} · distinct {data['distinct']} · "
          f"records {data['records']} · tree {data['tree']} "
          f"(of which grafted {data['grafted']}) · surnames {data['surnames']}")


if __name__ == "__main__":
    main()
