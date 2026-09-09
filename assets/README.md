# Source assets

Masters kept out of `site/public/` so they are versioned but not deployed.

## crossing-master.jpg

3168 × 1344. The frontispiece on the home page. Commissioned for this archive and
generated to a brief, September 2026.

The brief was deliberate and the picture argues the site's case: the great house on the
hill at far left is **faint and undetailed on purpose** — it is the Hornby claim, present
in the family's story but not load-bearing. The solid, close, particular part of the
picture is the quay, the ship and the people carrying their own cases up the gangway. The
right-hand third is Queensland: corrugated iron, hot light, and a railway line running
out of sight, which is where the family actually went and how they spread once there.

No heraldry, no crest, no coat of arms — the archive spends two pages showing that the
aristocratic descents do not hold, and a heraldic hero image would contradict the site in
the first thing anyone sees.

Deployed derivatives, regenerate with:

    sips -s format jpeg -s formatOptions 74 --resampleWidth 2400 assets/crossing-master.jpg --out site/public/img/crossing-2400.jpg
    sips -s format jpeg -s formatOptions 72 --resampleWidth 1500 assets/crossing-master.jpg --out site/public/img/crossing-1500.jpg
    sips -s format jpeg -s formatOptions 70 --resampleWidth 900  assets/crossing-master.jpg --out site/public/img/crossing-900.jpg
