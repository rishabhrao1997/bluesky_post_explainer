# Test cases for Bluesky post explanation evaluation
# Each test case includes: URL, description, expected_output

from typing import List, Dict, Any

TEST_CASES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "url": "https://bsky.app/profile/coreyspowell.bsky.social/post/3mdhhq4osec27",
        "description": "Post from coreyspowell.bsky.social",
        "expected_output": """- Rare "vanishing star" cases are interesting because they might be **failed supernovae**—massive stars that collapse into a black hole without producing a normal, bright explosion—so the star seems to disappear in visible light. [1]  
- The post is pointing to **M31-2014-DS1 in the Andromeda Galaxy**, which had an outburst in **2014** and then stayed **very faint optically** for years, making it a prominent failed-supernova candidate. [1]  
- New follow-up using **JWST (mid‑infrared)** finds there's still a **luminous IR source at the same location**, consistent with a surviving source that's now heavily **enshrouded by dust** rather than simply "gone." [1]  
- The same study reports **no X‑ray detection** (from Chandra), which **argues against** the idea that the observed late-time emission is mainly powered by bright accretion onto a newborn black hole—pushing the interpretation toward "dusty survivor / complex dust geometry." [1]  
- Net implication: it's a live debate between **black-hole formation** vs a **stellar merger or dust-creation event** that hides the star; either way, the "fade away" is being framed as an unresolved, high-value clue about how massive stars end their lives. [1][2]  

References:  
[1] https://arxiv.org/abs/2601.05317  
[2] https://academic.oup.com/mnras/advance-article/doi/10.1093/mnras/stag052/8424233
"""
    },
    {
        "id": 2,
        "url": "https://bsky.app/profile/cenmag.bsky.social/post/3mdiu372has22",
        "description": "Post from cenmag.bsky.social",
        "expected_output": """- Longstanding view in cell biology: genes and growth signaling pathways (e.g., mTORC1/Myc/PI3K-Akt) are the main "control knobs" for how big a cell gets; this is being challenged by new work highlighting metabolism as the upstream limiter. [1]  
- The key lever in the study is **pyruvate** (a central product of glycolysis) and where it gets routed—especially whether it's imported into mitochondria via the **mitochondrial pyruvate carrier (MPC)**. [1][2]  
- Shunting more pyruvate into mitochondria shifts the cell's **NAD/NADH redox balance**, which can suppress growth-supporting biosynthesis; in the fly fat body (liver-like tissue), boosting MPC kept cells small even when "pro-growth" signaling was active. [1][3]  
- Limiting mitochondrial pyruvate import (lower MPC) favors cytosolic/alternative fates of pyruvate that better support biomass building (e.g., amino acid/protein synthesis), leading to larger cells—suggesting metabolic routing can override canonical signaling. [1][3]  
- Takeaway/implication: metabolism isn't just housekeeping; **cell size control may fundamentally come down to metabolic tradeoffs (energy extraction vs. building blocks)**, with pyruvate fate acting like a master switch. [1][2]

References:  
[1] https://cen.acs.org/biological-chemistry/chemical-communication/cell-regulates-size/104/web/2026/01  
[2] https://elifesciences.org/articles/109482  
[3] https://pmc.ncbi.nlm.nih.gov/articles/PMC12629591/
"""
    },
    {
        "id": 3,
        "url": "https://bsky.app/profile/elisecutts.bsky.social/post/3mdir6ylezk27",
        "description": "Post from elisecutts.bsky.social",
        "expected_output": """- The post is teeing up a science-news story meant as a break from negative headlines, using a dramatic "tidal wave of lava" hook to grab attention.  
- "They're as high as a skyscraper" and "really, really hot" evokes towering lava fountains and extreme volcanic heat—imagery associated with intense eruptions and basaltic volcanism.  
- "Ooze at the speed of a human sprinter" points to the fact that some lava (especially in channels/tubes on steep slopes) can move surprisingly fast—fast enough to be compared to running speeds. [2][3]  
- The hashtag and conference mention ("#RockyWorlds4") places the reporting in the rocky-planet/exoplanet research community, where "lava worlds" (highly irradiated rocky exoplanets with magma oceans and extreme volcanism) are a major theme. [1]  
- "By me for @science.org" indicates this is a promo for her journalism for *Science* (Science.org), reported on location from the Rocky Worlds 4 conference in Groningen (held Jan 19–23, 2026). [1]

References:  
[1] https://science.nasa.gov/astrophysics/programs/exep/resources/exoplanet-meetings/rocky-worlds-4/  
[2] https://www.usgs.gov/news/volcano-watch-how-fast-does-hawaiian-lava-flow  
[3] https://www.usgs.gov/programs/VHP/lava-flows-destroy-everything-their-path
"""
    },
    {
        "id": 4,
        "url": "https://bsky.app/profile/greenleejw.bsky.social/post/3mdioseyyw22g",
        "description": "Post from greenleejw.bsky.social",
        "expected_output": """- Henry VIII's English Reformation included the **Dissolution of the Monasteries (1536–1541)**, where the Crown—largely through **Thomas Cromwell's administration**—shut down monasteries and seized their wealth and property. [2][3]  
- In **1537**, the abbot of **Crowland (Croyland) Abbey** appealed directly to Cromwell, trying to avoid suppression by offering a "gift" of **"fenn-fysche"**—i.e., fish from the fenlands, likely **eels**, a local staple and economic product. [1]  
- The joke is that this is basically an early-modern **bribe/care package**: "please spare our abbey; here's a barrel of our best local delicacy," leaning into the account's "eel historian" persona. [1]  
- The meme punchline flips Cromwell's perspective into cartoon villain logic: instead of accepting the gift, he can **dissolve the monastery and take everything**—including all future eels—echoing Cromwell's reputation as a hard-nosed enforcer of monastic closures. [1][2]  
- The humor lands because Crowland Abbey was **dissolved anyway (1539)**, making the eel-barrel gambit feel doomed in hindsight. [1]  

References:  
[1] https://en.wikipedia.org/wiki/Crowland_Abbey  
[2] https://www.britannica.com/biography/Thomas-Cromwell-earl-of-Essex-Baron-Cromwell-of-Okeham  
[3] https://en.wikipedia.org/wiki/Dissolution_of_the_monasteries
"""
    },
    {
        "id": 5,
        "url": "https://bsky.app/profile/mimi9324.bsky.social/post/3mdixehnojc2l",
        "description": "Post from mimi9324.bsky.social",
        "expected_output": """- A criticism of a recurring media/activism dynamic: influential white commentators urging high-profile people of color to "do something" publicly, as if they're obligated to lead the response or take the biggest risks.
- The pushback is framed as a safety issue, not just annoyance: prominent minorities can be uniquely exposed targets when they speak or act, so "use your platform" demands can be reckless rather than supportive.
- The Obama example points to the real-world threat environment: during Trump's first term, pipe bombs were mailed to multiple Trump critics, including a package addressed to Barack Obama (intercepted by the Secret Service) during the 2018 mail-bombing attempts.  
- Reposting the Ezra Klein/Caitlin Dickerson piece ties the post to an argument that intensified immigration enforcement is already producing intimidation/violence dynamics on the ground—raising the stakes for who is asked to publicly resist and how.  
- The "Drowning High Five" meme punchline ("Here's a podcast") implies that offering "content" (a podcast/link) is performative, inadequate help—like congratulating someone who's drowning instead of materially assisting.  

References:  
[1] https://knowyourmeme.com/memes/drowning-high-five  
[2] https://en.wikipedia.org/wiki/2018_United_States_mail_bombing_attempts  
[3] https://muckrack.com/podcast/TheEzraKleinShow/episodes/8332923-minneapolis-reveals-where-trumps-deportati/  
[4] https://www.nytimes.com/2026/01/23/opinion/ezra-klein-podcast-caitlin-dickerson.html?unlocked_article_code=1.H1A.8Eps.KaUppxOPpoDm&smid=url-share
"""
    },
    {
        "id": 6,
        "url": "https://bsky.app/profile/bullet1982.bsky.social/post/3mdixbzfzdc2i",
        "description": "Post from bullet1982.bsky.social",
        "expected_output": """- A "On This Day" history thread spotlighting aviator Bessie Coleman, framed as a reminder of how Black women (and Black/Indigenous women in particular) have been erased or under-taught in U.S. history.  
- The post celebrates Coleman's birth and positions her as a barrier-breaking figure who pursued aviation despite the era's systemic racism and sexism that blocked her from U.S. flight schools. [1][2]  
- "Unable to get a pilot's license in America because you already know why" is shorthand for Jim Crow–era discrimination: she had to go to France for training and licensing. [1][2]  
- The key fact being referenced: in June 1921, Coleman earned an international pilot's license from the Fédération Aéronautique Internationale (FAI), then returned to the U.S. and became famous as a stunt/barnstorming pilot while also challenging segregation. [1][2][3]  
- A subtle correction/nuance: multiple reputable references list her birthdate as **January 26, 1892** (not 1893), so the "#OTD January 26, 1893" line likely reflects a common misstatement or typo while still pointing to the same commemorated figure. [1][2]  

References:  
[1] https://www.britannica.com/biography/Bessie-Coleman  
[2] https://www.si.edu/newsdesk/snapshot/bessie-coleman-first-african-american-licensed-pilot  
[3] https://www.pbs.org/wgbh/americanexperience/features/flygirls-bessie-coleman/
"""
    },
    {
        "id": 7,
        "url": "https://bsky.app/profile/insidehighered.com/post/3mdiug2hqws2s",
        "description": "Post from insidehighered.com",
        "expected_output": """- A wave of higher-education organizations, universities, and advocacy groups has been filing lawsuits to stop or roll back Trump administration actions affecting colleges—especially policy moves tied to DEI restrictions, federal guidance, and other executive-branch changes. [1]  
- The post is pointing readers to Inside Higher Ed's running "tracker" article, which compiles major cases in one place and is updated regularly as new complaints are filed and judges issue rulings. [1]  
- The central theme is that the scale of litigation is unusually high for the higher-ed sector, reflecting how many policy disputes are being routed through courts rather than resolved through Congress or standard rulemaking. [1]  
- It frames DEI-related actions as a major flashpoint: multiple challenges argue the administration's directives are unconstitutional/vague or chill speech, while courts have sometimes blocked enforcement while cases proceed. [2][3][4]  
- The imagery (Trump + courthouse + scales of justice) reinforces the "policy fight is now a legal battle" message and signals that outcomes will depend on court decisions and injunctions, not just agency announcements.  

References:  
[1] https://www.insidehighered.com/news/government/politics-elections/2025/09/30/tracking-key-lawsuits-against-trump-administration  
[2] https://www.insidehighered.com/news/government/2025/02/05/higher-ed-organizations-sue-against-trumps-dei-orders  
[3] https://apnews.com/article/5b04fbc742bd32adf98ca108b4b12b37  
[4] https://www.politico.com/news/2025/04/24/federal-judge-temporarily-blocks-education-department-from-enforcing-dei-orders-00307831
"""
    },
    {
        "id": 8,
        "url": "https://bsky.app/profile/dszlosek.bsky.social/post/3mdirq5tz6c2d",
        "description": "Post from dszlosek.bsky.social",
        "expected_output": """- FDA drug approvals aren't always driven by a single "p < 0.05" win on a primary endpoint; in severe diseases with high unmet need, the agency may accept more uncertainty if the alternative is delaying access to a potentially helpful therapy.  
- The example highlighted is Qalsody (tofersen) for SOD1-ALS, which received **accelerated approval on April 25, 2023** based on lowering plasma neurofilament light (NfL), a surrogate biomarker considered "reasonably likely" to predict clinical benefit. [2]  
- The screenshot's voting numbers reflect the FDA advisory committee discussion: **9–0** that NfL reduction is "reasonably likely" to predict benefit, but **5–3 (with one abstention)** that the clinical dataset was not "convincing evidence" of effectiveness for traditional approval—illustrating how accelerated approval can move forward even when clinical endpoints are not definitive. [3]  
- The "frequentist vs calibrated Bayes" framing is pointing out that a strict null-hypothesis lens ("trial failed; don't approve") can clash with a decision-theoretic/regulatory lens ("which error is worse in a fatal disease?"), especially when using surrogate endpoints plus required follow-up studies. [2][3]  
- The linked "Evidence in the Wild" site is being recommended as a deeper statistics/regulatory-methods explainer (Bayesian methods, trial design, and how regulators interpret evidence), matching the poster's wish for more transparent detail on decisions like this. [1]  

References:  
[1] https://evidenceinthewild.com/  
[2] https://www.fda.gov/drugs/news-events-human-drugs/fda-approves-treatment-amyotrophic-lateral-sclerosis-associated-mutation-sod1-gene  
[3] https://www.als.org/stories-news/fda-committee-unanimously-recommends-accelerated-approval-tofersen
"""
    },
    {
        "id": 9,
        "url": "https://bsky.app/profile/bakitchen.bsky.social/post/3mdhlmv6fy226",
        "description": "Post from bakitchen.bsky.social",
        "expected_output": """- Potatoes O'Brien is a classic American breakfast-style potato dish—diced potatoes cooked until crisp/tender with bell peppers and onions—often grouped with "home fries" or "breakfast potatoes," with origins commonly traced to early-1900s diners/restaurants (Boston or Manhattan are often cited). [1]  
- The post shares a scaled-up, batch-friendly version designed for shared/community meals: sheet-pan potatoes cooked in an oven's air-fryer/convection setting, which avoids stovetop babysitting and makes large quantities easier.  
- The linked recipe emphasizes flexibility and accessibility (potato type and dice size aren't critical; peppers/onions can be fresh or even canned/prepped), and it's intended to reheat well for later meals—useful for meal prep or service settings.  
- The hashtags frame it as part of an online food-sharing community (#foodsky) and explicitly connect it to hunger/food insecurity work (#foodaccess), aligning with Boarding Axe Kitchen's nonprofit mission around food access, education, and practical cooking documentation. [2]  

References:  
[1] https://en.wikipedia.org/wiki/Potatoes_O%27Brien  
[2] https://www.boardingaxekitchen.org/
"""
    },
    {
        "id": 10,
        "url": "https://bsky.app/profile/jeffgreene.bsky.social/post/3mdidfzfyv32v",
        "description": "Post from jeffgreene.bsky.social",
        "expected_output": """- Higher-ed teaching context: the post leans on a well-known educator/leadership aphorism ("no one cares how much you know…") to argue that students' sense that a professor genuinely *cares* is a prerequisite for students valuing (and benefiting from) that professor's expertise.  
- "Care is multidimensional" here means faculty–student relationship quality isn't just friendliness or frequency of contact; it includes things like perceived support, responsiveness, emotional safety, and relational closeness—how students *experience* the relationship. [1]  
- The linked 2026 meta-analysis synthesizes 36 studies (128 effect sizes) and finds an overall positive association between perceived faculty–student relationships and student outcomes (about *r* = .18 overall). [1]  
- The strongest link is for *persistence/retention* (about *r* = .33), implying that relationship quality may matter even more for whether students *stay enrolled* than for grades alone. [1]  
- The practical implication: professors who develop students' perception of "care" (as part of relationship quality) may be improving both performance and persistence, supporting professional development that builds relational/mentoring skills alongside content delivery. [1]

References:  
[1] https://doi.org/10.1007/s10648-025-10100-9
"""
    },
    {
        "id": 11,
        "url": "https://bsky.app/profile/pennneuroknow.bsky.social/post/3mdgbbt6jfs22",
        "description": "Post from pennneuroknow.bsky.social",
        "expected_output": """- Parasitic "zombie" fungi are a real biology phenomenon: certain fungi infect insects and reliably alter their behavior in ways that improve fungal survival and spore spread (often cited with Ophiocordyceps and the "zombie ant" story). [1]  
- The linked piece highlights multiple examples beyond ants, framing them as striking cases of behavior manipulation that can look like "mind control," even though it's driven by parasite life cycles rather than intentionality.  
- One theme is "summiting" (infected insects climbing to elevated spots before dying), which helps dispersal—e.g., Entomophaga grylli in grasshoppers and Entomophthora muscae in flies, with evidence pointing toward early nervous-system involvement and/or chemical signals affecting the brain.  
- Another example shifts from movement to social/sexual signaling: Massospora cicadina can induce infected male periodical cicadas to perform female-typical wing-flick signals, attracting mating attempts that help transmit spores (essentially turning mating into a transmission route). [2]  
- The neuroscience angle: these systems are used as a provocative comparison—fungi can "steer" animal behavior with surprising specificity, suggesting there's still a lot to learn about how brains can be pushed into particular behavioral states (and what that might imply for future therapeutic control of dysfunctional brain circuits).  

References:  
[1] https://www.nationalgeographic.com/animals/article/cordyceps-zombie-fungus-takes-over-ants  
[2] https://www.nature.com/articles/s41598-018-19813-0
"""
    },
    {
        "id": 12,
        "url": "https://bsky.app/profile/pocket-ireland.com/post/3mdhxbbr4eu2p",
        "description": "Post from pocket-ireland.com",
        "expected_output": """- A smartphone photographer is sharing a low-angle macro shot taken in autumn, emphasizing the creative technique of shooting at ground level to make a familiar subject feel dramatic and immersive.  
- The subject is a wild mushroom photographed to highlight the underside gills (a common macro/nature-photography approach), and the caption is essentially a "nature ID" prompt inviting mycology help from the community.  
- The location tags point to Kilmacurragh in County Wicklow—specifically the National Botanic Gardens, Kilmacurragh—framing this as a nature find from a well-known garden/arboretum area in Ireland. [1][2]  
- Hashtags like #fungi, #mushroom, #macro, #nature, plus the place tags (#Kilmacurragh #Wicklow #Ireland) are there to route the post into both photography and local nature/wildlife discovery feeds.  
- #EastCoastKin functions like a community/collective tag used on Bluesky for sharing photos/art as part of an "EastCoastKin" group/challenge feed, widening engagement beyond just Ireland-specific audiences. [3]  

References:  
[1] https://www.botanicgardens.ie/kilmacurragh/  
[2] https://en.wikipedia.org/wiki/National_Botanic_Gardens%2C_Kilmacurragh  
[3] https://bskyview.com/1832902d/eastcoastkin-ac
"""
    },
]
