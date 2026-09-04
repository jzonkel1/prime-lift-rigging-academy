# -*- coding: utf-8 -*-
"""
Prime Lift Rigging Academy — static site builder.

    python build.py

Generates every page except index.html from content.py, rewrites the shared
nav / footer / schema blocks INSIDE index.html (between the marker comments),
and writes css/pages.css, js/site.js, sitemap.xml, llms.txt, 404.html and the
Sitemap line in robots.txt.

Never hand-edit a generated page: it is overwritten on the next build.
Edit content.py (copy/facts) or this file (markup), then rebuild.

Launch switch: set NOINDEX = False. That drops the noindex meta on every page,
and moves canonical / og / sitemap URLs from the Netlify preview origin to the
real domain in one build.
"""
import io, os, re, json, html, datetime, urllib.parse, hashlib
from content import (BIZ, COURSES, ASSESSMENT, CRAFT_GROUPS, CRAFTS, PEOPLE,
                     REVIEWS, FAQ, FINANCING, ES, GUIDES, RETEST_POLICY, CREDENTIAL_POSTING_TIME, WHY)

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://primeliftriggingtx.com"   # launch domain per Jeffrey 8/31/26 (NOT primeliftrigging-academy.com; 301 that one here at launch)
PREVIEW = "https://prime-lift-rigging-academy.netlify.app"
NOINDEX = False                      # LIVE on primeliftriggingtx.com 9/4/26
ORIGIN = PREVIEW if NOINDEX else BASE
YEAR = datetime.date.today().year
TODAY = datetime.date.today().isoformat()

def esc(s): return html.escape(s, quote=True)
def money(n): return "${:,}".format(n)
def w(rel, text):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)

# ------------------------------------------------------ responsive images
# Every <img src="img/*.jpg|png"> in the output (generated pages AND index.html)
# gets WebP variants, made on demand into img/ and cached by mtime, plus a
# srcset/sizes pair chosen from the markup around it. Before this, phones pulled
# 2400px JPEG masters (up to 1.4 MB) into 350px cards: Lighthouse mobile 64.
# To swap a photo, edit the src (or data-o once it has been rewritten) and rebuild.
IMG_SKIP = {"cur-arrow.png", "cur-arrow@2x.png", "cur-link.png", "cur-link@2x.png",   # CSS cursors, never in <img>
            "favicon-32.png", "apple-touch-icon.png", "icon-192.png", "icon-512.png", "icon-512-maskable.png",
            "og.jpg", "grunge.png", "optin-consent.png", "chevron.png", "hook.png"}
IMG_WIDTHS = (320, 480, 800, 1200, 1600, 2400)
VARIANTS = {}          # "img/x.jpg" -> (orig_width, [(w, "img/x-w.webp"), ...])
CSS_VER = "dev"        # content hash of css/bundle.css, set by write_assets()

def make_variants():
    from PIL import Image
    d = os.path.join(ROOT, "img")
    for name in sorted(os.listdir(d)):
        base, ext = os.path.splitext(name)
        if ext.lower() not in (".jpg", ".jpeg", ".png") or name in IMG_SKIP or base.endswith("-1200"):
            continue
        src = os.path.join(d, name)
        with Image.open(src) as im0:
            ow, oh = im0.size
        widths = [x for x in IMG_WIDTHS if x <= ow] or [ow]
        if ow > widths[-1] * 1.15: widths.append(ow)     # e.g. a 2000px master keeps a 2000w rung above 1600
        outs, im = [], None
        for wd in widths:
            rel = "img/%s-%d.webp" % (base, wd)
            out = os.path.join(ROOT, rel)
            if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(src):
                im = im or Image.open(src)
                r = im if wd == ow else im.resize((wd, max(1, round(oh * wd / ow))), Image.LANCZOS)
                if r.mode not in ("RGB", "RGBA"):
                    r = r.convert("RGBA" if ext.lower() == ".png" else "RGB")
                r.save(out, "WEBP", quality=90 if ext.lower() == ".png" else 80, method=4)
            outs.append((wd, rel))
        if im: im.close()
        VARIANTS["img/" + name] = (ow, outs)

def variant_src(path, want=800):
    """'/img/x.jpg' -> '/img/x-800.webp' (largest variant <= want). For markup built by JS."""
    key = path.lstrip("/")
    if key not in VARIANTS: return path
    outs = VARIANTS[key][1]
    pick = [o for o in outs if o[0] <= want] or outs[:1]
    return ("/" if path.startswith("/") else "") + pick[-1][1]

_IMG_TAG = re.compile(r"<img\b[^>]*>", re.I)
_ATTR = re.compile(r'([^\s=/>]+)(?:\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+)))?')
_FULL = {"hero-bg", "phero-bg", "band-bg", "how-bg"}                  # full-bleed, object-fit:cover
_GRID = {"person-img", "course-shot", "prog-shot", "rv-panel", "hero-photo", "storefront",
         "person-portrait", "team-grid", "rev3", "fin-photo"}          # a column of a 2-3 column grid
_STRIP = {"gw-strip"}                                                  # graduate wall: 6-up desktop, 3-up phones
_GAL = {"gal"}                                                         # photo gallery: 4-up desktop, 2-up phones
SIZES = {"full": "(max-width:900px) 200vw, 100vw",   # a tall phone box covered by a landscape photo needs > 100vw (200vw x 2 DPR = the 1600 rung)
         "grid": "(min-width:1040px) 34vw, (min-width:640px) 50vw, 100vw",
         "strip": "(min-width:760px) 16vw, 33vw",
         "gal": "(min-width:780px) 25vw, 50vw",
         "logo": "120px", "page": "100vw"}

def responsive_images(html_text):
    def fix(m):
        tag = m.group(0)
        attrs = [(a.group(1), a.group(2) if a.group(2) is not None else a.group(3) if a.group(3) is not None else a.group(4))
                 for a in _ATTR.finditer(tag[4:-1].rstrip("/"))]
        d = dict(attrs)
        if "data-nors" in d: return tag
        orig = d.get("data-o") or d.get("src") or ""
        key = orig.lstrip("/")
        if key not in VARIANTS: return tag
        lead = "/" if orig.startswith("/") else ""
        ow, outs = VARIANTS[key]
        role = "page"
        if "fl" in (d.get("class") or "").split(): role = "logo"
        else:
            ctx = html_text[max(0, m.start() - 3000):m.start()]   # rewritten tags are long; a 6-up strip needs the reach
            for cm in reversed(list(re.finditer(r'class="([^"]*)"', ctx))):
                toks = set(cm.group(1).split())
                if toks & _FULL: role = "full"; break
                if toks & _STRIP: role = "strip"; break
                if toks & _GAL: role = "gal"; break
                if toks & _GRID: role = "grid"; break
                if "brand" in toks: role = "logo"; break
        sizes = d.get("data-sizes") or SIZES[role]      # data-sizes="..." on the tag overrides the role rule; plain sizes= is recomputed each build
        fallback = ([o for o in outs if o[0] <= 1200] or outs[:1])[-1][1]
        srcset = ", ".join("%s%s %dw" % (lead, rel, wd) for wd, rel in outs)
        keep = " ".join(('%s="%s"' % (k, v)) if v is not None else k for k, v in attrs if k not in ("src", "srcset", "sizes", "data-o", "data-src", "data-srcset"))
        # data-defer: emit data-src/data-srcset instead, and a script swaps them in after first paint
        # (the home hero photo: the headline is the LCP and must never wait on a 200 KB image)
        pre = "data-" if "data-defer" in d else ""
        return '<img %ssrc="%s%s" %ssrcset="%s" sizes="%s" data-o="%s"%s>' % (pre, lead, fallback, pre, srcset, sizes, orig, (" " + keep) if keep else "")
    return _IMG_TAG.sub(fix, html_text)

# ----------------------------------------------------------------- icons
I = {
 "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13.832 16.568a1 1 0 0 0 1.213-.303l.355-.465A2 2 0 0 1 17 15h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2A18 18 0 0 1 2 4a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2v3a2 2 0 0 1-.8 1.6l-.468.351a1 1 0 0 0-.292 1.233 14 14 0 0 0 6.392 6.384"/></svg>',
 "arrow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>',
 "check": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
 "caret": '<svg class="caret" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>',
 "cal": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/><path d="m9 16 2 2 4-4"/></svg>',
 "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/></svg>',
 "clock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',
 "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 7-8.991 5.727a2 2 0 0 1-2.009 0L2 7"/><rect x="2" y="4" width="20" height="16" rx="2"/></svg>',
 "fb": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z"/></svg>',
 "tiktok": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/></svg>',
 "google": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M21.35 11.1H12v2.9h5.35c-.25 1.4-1.6 4.1-5.35 4.1a6.1 6.1 0 1 1 0-12.2c1.9 0 3.15.8 3.85 1.5l2.6-2.5A10 10 0 0 0 12 2a10 10 0 1 0 0 20c5.75 0 9.6-4.05 9.6-9.75 0-.65-.1-1.15-.25-1.15z"/></svg>',
 "star": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.5l2.9 6.1 6.6.8-4.9 4.6 1.3 6.6L12 17.3l-5.9 3.3 1.3-6.6L2.5 9.4l6.6-.8z"/></svg>',
 "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/></svg>',
}
FULL_ADDR = "%s, %s, %s %s" % (BIZ["street"], BIZ["city"], BIZ["state"], BIZ["zip"])

# ------------------------------------------------------- schedule rules
# ONE set of recurrence rules. The class-dates page's JS gets this table as
# JSON and the course pages' "next start dates" strip is rendered from it in
# Python (then refreshed client-side from the same rule), so they can't
# disagree. Booking closes the day before a class starts (LEAD_DAYS).
LEAD_DAYS = 1
MON, FRI = 1, 5                      # JS getDay() numbering (Sun=0)
SCHEDULE_RULES = [
    {"id": "advanced", "fmt": "day", "name": "Advanced Rigger", "label": "Weekday Day Class", "time": "Mon – Thu · 8:00 AM – 2:00 PM", "note": "Four days, starts every Monday", "wd": MON, "n": 6},
    {"id": "advanced", "fmt": "night", "name": "Advanced Rigger", "label": "Weekday Night Class", "time": "Mon – Thu · 6:00 PM – 11:00 PM", "note": "Four nights, built for day-shift crews", "wd": MON, "n": 6},
    {"id": "advanced", "fmt": "weekend", "name": "Advanced Rigger", "label": "3-Day Weekend Express", "time": "Fri – Sun · 8:00 AM – 5:00 PM", "note": "Done in one weekend, every other Friday", "wd": FRI, "n": 6, "every": 14, "anchor": "2026-09-04"},
    {"id": "signal", "fmt": "friday", "name": "Signal Person", "label": "Two Fridays", "time": "Fridays · 8:00 AM – 3:00 PM", "note": "Two Fridays of class and hands-on, every other Friday", "wd": FRI, "n": 6, "every": 14, "anchor": "2026-09-11"},
    {"id": "assessment", "fmt": "assess", "name": "NCCER Assessments", "label": "Any Weekday", "time": "Mon – Fri · 8:00 AM – 5:00 PM", "note": "By appointment, 36 crafts", "wd": "weekday", "n": 10},
]
# Office exceptions. Edit here, run build.py, deploy (two minutes, see SOP in
# the project memory). CLOSED dates vanish from every list on the site
# (holiday, no class that week). FULL classes stay visible but can't be picked.
# FULL keys: "advanced:day", "advanced:night", "advanced:weekend",
# "signal:friday", "assessment:assess", or "*" for every class that day.
CLOSED = {
    "2026-09-07": "Labor Day",   # pending Andres: does the Labor Day week class run?
}
FULL = {
    # "2026-09-14": ["advanced:day"],
}
def is_full(iso, key):
    f = FULL.get(iso, ())
    return key in f or "*" in f

def next_dates(wd, n, key=None, every=7, anchor=None):
    """Next n bookable start dates for a rule: wd = JS weekday number, or "weekday"
    for Mon-Fri. Skips CLOSED dates and, when key is given, FULL classes.
    A rule wider than weekly (every=14) has to be phased off its anchor date
    rather than off today, or the run lands on the wrong Fridays."""
    d = datetime.date.today() + datetime.timedelta(days=LEAD_DAYS)
    out = []
    ok = lambda x: x.isoformat() not in CLOSED and not (key and is_full(x.isoformat(), key))
    if wd == "weekday":
        while len(out) < n:
            if d.weekday() <= 4 and ok(d): out.append(d)
            d += datetime.timedelta(days=1)
        return out
    while (d.weekday() + 1) % 7 != wd: d += datetime.timedelta(days=1)
    if anchor and every != 7:
        off = (d - datetime.date(*map(int, anchor.split("-")))).days % every
        if off: d += datetime.timedelta(days=every - off)
    while len(out) < n:
        if ok(d): out.append(d)
        d += datetime.timedelta(days=every)
    return out
def rules_json():
    return json.dumps(SCHEDULE_RULES, separators=(",", ":"))
def sched_json():
    """CLOSED/FULL as one JS object literal, injected wherever dates are computed client-side."""
    return json.dumps({"closed": CLOSED, "full": FULL}, separators=(",", ":"))

# ------------------------------------------------------------------ nav
def nav(home=False):
    h = "" if home else "/"           # anchor prefix for home sections
    def course_items():
        def item(slug, n, name, sub, price):
            return """
            <a class="nm-item" href="/%s/">
              <span class="nm-n idx">%02d</span>
              <span class="nm-b"><b>%s</b><span>%s</span></span>
              <span class="nm-p">%s</span>
            </a>""" % (slug, n, esc(name), esc(sub), price)
        courses = [
            (COURSES[0]["slug"], COURSES[0]["name"], "Days, nights, or the 3-day weekend express", money(1000)),
            (COURSES[1]["slug"], COURSES[1]["name"], "Two Fridays of class and hands-on", money(1000)),
            (ASSESSMENT["slug"], ASSESSMENT["name"], "Test out in 36 crafts, proctored on-site", money(150))]
        # the format + renewal pages used to be reachable only from the footer
        formats = [
            ("weekend-express", "3-Day Weekend Express", "Fri – Sun, certified by Sunday", ""),
            ("night-classes", "Night Classes", "Mon – Thu, 6 – 11 PM", ""),
            ("rigger-recertification", "Recertification", "Credential coming due?", "")]
        out = "".join(item(s, i + 1, n, sub, p) for i, (s, n, sub, p) in enumerate(courses))
        out += '\n            <p class="nm-h">Schedules &amp; Renewals</p>'
        out += "".join(item(s, i + 4, n, sub, p) for i, (s, n, sub, p) in enumerate(formats))
        return out
    def people_items():
        return "".join("""
            <a class="nm-item" href="/instructors/%s/">
              <span class="nm-n idx">%02d</span>
              <span class="nm-b"><b>%s</b><span>%s</span></span>
              <span class="nm-p"></span>
            </a>""" % (p["slug"], i+1, esc(p["name"]), esc(p["role"])) for i, p in enumerate(PEOPLE))
    return """<!-- ================= NAV ================= -->
<!-- NAV:START — generated by build.py, do not edit by hand -->
<header class="nav" id="nav">
  <div class="wrap nav-in">
    <a class="brand" href="/">
      <img src="/img/logo.png" alt="Prime Lift Rigging Academy">
      <span class="brand-txt"><img class="nccer" src="/img/nccer.svg" alt="NCCER" width="94" height="23"> Training &amp;<br>Assessment Center</span>
    </a>
    <nav class="nav-links" aria-label="Main">
      <div class="nav-item">
        <a href="%(h)s#courses" aria-haspopup="true">Courses %(caret)s</a>
        <div class="nav-menu"><div class="nav-menu-in">%(courses)s
            <a class="nm-all" href="/class-dates/">See All Class Dates %(arrow)s</a>
            <a class="nm-all" href="/guides/">Read The Rigging Guides %(arrow)s</a>
        </div></div>
      </div>
      <a href="/class-dates/">Dates</a>
      <a href="/financing/">Financing</a>
      <div class="nav-item">
        <a href="/instructors/" aria-haspopup="true">Team %(caret)s</a>
        <div class="nav-menu"><div class="nav-menu-in nm-narrow">%(people)s
            <a class="nm-all" href="/instructors/">Meet The Whole Team %(arrow)s</a>
        </div></div>
      </div>
      <a href="/contact/">Contact</a>
    </nav>
    <div class="nav-cta">
      <a class="nav-phone" href="tel:%(tel)s" aria-label="Call %(phone)s">%(phone_i)s %(phone)s</a>
      <a class="btn btn-primary" href="/book/">Book a Class</a>
      <button class="nav-burger" id="navBurger" aria-label="Open menu" aria-expanded="false" aria-controls="mnav"><span></span><span></span><span></span></button>
    </div>
  </div>
  <nav class="mnav" id="mnav" aria-label="Mobile">
    <div class="mnav-in">
      <div class="macc">
        <button class="macc-t" type="button" aria-expanded="false" aria-controls="macc-courses"><b>Courses</b><span>Certifications, schedules &amp; renewal</span>%(caret)s</button>
        <div class="macc-p" id="macc-courses">
          <a href="/advanced-rigger/"><b>Advanced Rigger</b><span>4 days · day, night or weekend</span><em>$1,000</em></a>
          <a href="/signal-person/"><b>Signal Person</b><span>Two Fridays</span><em>$1,000</em></a>
          <a href="/nccer-assessments/"><b>NCCER Assessments</b><span>Test out in 36 crafts</span><em>$150</em></a>
          <a href="/weekend-express/"><b>3-Day Weekend Express</b><span>Fri – Sun, certified by Sunday</span></a>
          <a href="/night-classes/"><b>Night Classes</b><span>Mon – Thu, 6 – 11 PM</span></a>
          <a href="/rigger-recertification/"><b>Recertification</b><span>Credential coming due?</span></a>
        </div>
      </div>
      <div class="macc">
        <button class="macc-t" type="button" aria-expanded="false" aria-controls="macc-academy"><b>Academy</b><span>Dates · Instructors · Guides</span>%(caret)s</button>
        <div class="macc-p" id="macc-academy">
          <a href="/class-dates/"><b>Class Dates</b><span>Every upcoming start date</span></a>
          <a href="/instructors/"><b>Instructors</b><span>Andres · Juan · Frank</span></a>
          <a href="/guides/"><b>Guides</b><span>NCCER vs. NCCCO · test prep · verifying credentials</span></a>
        </div>
      </div>
      <a href="/financing/"><b>Financing</b></a>
      <a href="/about/"><b>About</b></a>
      <a href="/reviews/"><b>Student Reviews</b></a>
      <a href="/faq/"><b>FAQ</b></a>
      <a href="/contact/"><b>Contact</b></a>
      <div class="mnav-cta">
        <a class="btn btn-primary btn-block" href="/book/">Book a Class</a>
        <a class="btn btn-ghost btn-block" href="tel:%(tel)s">%(phone_i)s Call %(phone)s</a>
      </div>
    </div>
  </nav>
</header>
<!-- NAV:END -->
""" % dict(h=h, caret=I["caret"], arrow=I["arrow"], courses=course_items(), people=people_items(),
           tel=BIZ["phone_raw"], phone=BIZ["phone"], phone_i=I["phone"])

def footer(home=False):
    h = "" if home else "/"
    return """<!-- ================= FOOTER ================= -->
<!-- FOOTER:START — generated by build.py, do not edit by hand -->
<footer class="foot">
  <div class="wrap">
    <div class="foot-grid foot-grid-4">
      <div>
        <img class="fl" src="/img/logo.png" alt="Prime Lift Rigging Academy">
        <p>NCCER Accredited Training &amp; Assessment Center in Portland, Texas. Rigging, signal person and craft assessments for the Coastal Bend.</p>
        <div class="socials">
          <a href="%(fb)s" target="_blank" rel="noopener" aria-label="Facebook">%(fb_i)s</a>
          <a href="%(tt)s" target="_blank" rel="noopener" aria-label="TikTok">%(tt_i)s</a>
          <a href="%(gm)s" target="_blank" rel="noopener" aria-label="Google">%(g_i)s</a>
          <a href="mailto:%(email)s" aria-label="Email">%(mail_i)s</a>
        </div>
      </div>
      <div>
        <p class="foot-h">Certifications</p>
        <ul>
          <li><a href="/advanced-rigger/">Advanced Rigger</a></li>
          <li><a href="/signal-person/">Signal Person</a></li>
          <li><a href="/nccer-assessments/">NCCER Assessments</a></li>
          <li><a href="/weekend-express/">3-Day Weekend Express</a></li>
          <li><a href="/night-classes/">Night Classes</a></li>
          <li><a href="/rigger-recertification/">Recertification</a></li>
          <li><a href="/guides/">Guides</a></li>
        </ul>
      </div>
      <div>
        <p class="foot-h">Academy</p>
        <ul>
          <li><a href="/class-dates/">Class Dates</a></li>
          <li><a href="/financing/">Financing</a></li>
          <li><a href="/instructors/">Instructors</a></li>
          <li><a href="/about/">About</a></li>
          <li><a href="/reviews/">Student Reviews</a></li>
          <li><a href="/faq/">FAQ</a></li>
        </ul>
      </div>
      <div>
        <p class="foot-h">Contact</p>
        <ul>
          <li><a href="tel:%(tel)s">%(phone)s</a></li>
          <li><a href="mailto:%(email)s">%(email)s</a></li>
          <li><a href="/contact/">1605 US Hwy 181 Frontage Rd, Suite A<br>Portland, TX 78374</a></li>
          <li><a href="/contact/">Mon–Fri · 7 AM – 5 PM</a></li>
        </ul>
      </div>
    </div>
    <div class="foot-base">
      <span>© <span id="yr">%(yr)s</span> Prime Lift Rigging Academy LLC · Portland, Texas · Locally &amp; Latino-owned</span>
      <span><a href="/privacy.html" style="color:var(--muted)">Privacy</a> &middot; <a href="/terms.html" style="color:var(--muted)">Terms</a> &middot; <a href="/accessibility.html" style="color:var(--muted)">Accessibility</a> &middot; Site by <a href="https://zonkelmedia.com" target="_blank" rel="noopener" style="color:var(--muted)">Zonkel Media</a></span>
    </div>
  </div>
</footer>
<!-- FOOTER:END -->
""" % dict(fb=BIZ["facebook"], tt=BIZ["tiktok"], gm=BIZ["gmaps"], email=BIZ["email"], tel=BIZ["phone_raw"],
           phone=BIZ["phone"], fb_i=I["fb"], tt_i=I["tiktok"], g_i=I["google"], mail_i=I["mail"], yr=YEAR, h=h)

def callbar():
    return """<div class="callbar" id="callbar">
  <a class="pri" href="tel:%s">%s Call Now</a>
  <a href="/book/">%s Book a Class</a>
</div>""" % (BIZ["phone_raw"], I["phone"], I["cal"])

# --------------------------------------------------------------- schema
def org_schema():
    return {
        "@type": ["EducationalOrganization", "LocalBusiness"],
        "@id": BASE + "/#org",
        "name": BIZ["name"], "legalName": BIZ["legal"],
        "url": BASE + "/", "logo": BASE + "/img/logo.png", "image": BASE + "/img/og.jpg",
        "telephone": BIZ["phone_raw"], "email": BIZ["email"], "priceRange": "$150 - $1,000",
        "description": "NCCER Accredited Training and Assessment Center in Portland, Texas. Advanced Rigger and Signal Person certification and NCCER craft assessments in 36 crafts.",
        "address": {"@type": "PostalAddress", "streetAddress": BIZ["street"], "addressLocality": BIZ["city"],
                    "addressRegion": BIZ["state"], "postalCode": BIZ["zip"], "addressCountry": "US"},
        "geo": {"@type": "GeoCoordinates", "latitude": BIZ["lat"], "longitude": BIZ["lng"]},
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "opens": "07:00", "closes": "17:00"}],
        "areaServed": [{"@type": "City", "name": a + ", TX"} for a in BIZ["areas"]],
        "sameAs": [BIZ["facebook"], BIZ["tiktok"], BIZ["gmaps"]],
        "hasCredential": {"@type": "EducationalOccupationalCredential", "name": "NCCER Accredited Training and Assessment Center"},
    }

def crumbs_schema(crumbs):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i+1, "name": n, "item": BASE + u} for i, (n, u) in enumerate(crumbs)]}

def faq_schema(faq):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}

def course_schema(c, url):
    return {
        "@type": "Course", "name": c["name"] + " Certification", "description": c["meta_desc"],
        "url": BASE + url, "provider": {"@id": BASE + "/#org"},
        "educationalCredentialAwarded": c["cred"],
        "offers": {"@type": "Offer", "price": c["price"], "priceCurrency": "USD", "category": "Paid",
                   "availability": "https://schema.org/InStock", "url": BASE + url},
        "hasCourseInstance": [{"@type": "CourseInstance", "courseMode": "Onsite", "name": f["name"],
            "location": {"@type": "Place", "name": BIZ["name"], "address": FULL_ADDR},
            "courseSchedule": {"@type": "Schedule", "repeatFrequency": "Weekly", "byDay": f["when"], "startTime": f["time"].split(" – ")[0]}}
            for f in c["formats"]],
    }

def service_schema(name, desc, url, price=150):
    return {"@type": "Service", "name": name, "description": desc, "url": BASE + url,
            "serviceType": "NCCER craft assessment", "provider": {"@id": BASE + "/#org"},
            "areaServed": {"@type": "State", "name": "Texas"},
            "offers": {"@type": "Offer", "price": price, "priceCurrency": "USD", "availability": "https://schema.org/InStock"}}

def person_schema(p, url):
    return {"@type": "Person", "name": p["name"], "jobTitle": p["role"], "url": BASE + url,
            "image": BASE + "/" + p["img"], "worksFor": {"@id": BASE + "/#org"}, "description": p["meta_desc"]}

def ld(graph):
    return '<script type="application/ld+json">%s</script>' % json.dumps(
        {"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))

# ---------------------------------------------------------------- shell
# Fonts are self-hosted (css/fonts.css, /fonts/*.woff2): no Google Fonts round trips
# on the critical path. The two faces above the fold are preloaded.
FONTS = '<link rel="preload" as="font" type="font/woff2" href="/fonts/ibm-plex-sans.woff2" crossorigin>'   # Anton rides inside bundle.css

def hreflang_links(url):
    """No translated pages ship right now, so there are no alternates to declare.
    The Spanish summary was pulled 9/2: the client's own onboarding answered
    "Spanish: No", so it was generating leads the office cannot serve."""
    return ""

def page(url, title, desc, body, crumbs=(), schema=(), og_image="/img/og.jpg", hero_img=None, lang="en"):
    full = ORIGIN + url
    graph = [org_schema()]
    if crumbs: graph.append(crumbs_schema([("Home", "/")] + list(crumbs)))
    graph += list(schema)
    graph.append({"@type": "WebPage", "@id": BASE + url, "url": BASE + url, "name": title,
                  "description": desc, "isPartOf": {"@id": BASE + "/#website"}, "about": {"@id": BASE + "/#org"}})
    pre = "<!--PRE-->" if hero_img else ""
    out = """<!DOCTYPE html>
<html lang="%(lang)s">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>%(title)s%(suffix)s</title>
<meta name="description" content="%(desc)s">
<link rel="canonical" href="%(full)s">
%(alt)s%(robots)s
<meta property="og:type" content="website">
<meta property="og:site_name" content="Prime Lift Rigging Academy">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(full)s">
<meta property="og:image" content="%(ogimg)s">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(title)s">
<meta name="twitter:description" content="%(desc)s">
<meta name="twitter:image" content="%(ogimg)s">
%(fonts)s
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" type="image/png" sizes="32x32" href="/img/favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/img/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#111828">
%(pre)s
<link rel="stylesheet" href="/css/bundle.css?v=%(cssv)s">
%(ld)s
</head>
<body class="sub">
%(nav)s
<main id="main">
%(body)s
</main>
%(footer)s
%(callbar)s
<script src="/js/site.js" defer></script>
</body>
</html>
""" % dict(title=esc(title), desc=esc(desc), full=full, lang=lang, alt=hreflang_links(url),
           suffix="" if len(title) > 40 else " | Prime Lift Rigging Academy",
           robots='<meta name="robots" content="noindex, nofollow">' if NOINDEX else '<meta name="robots" content="index, follow, max-image-preview:large">',
           ogimg=ORIGIN + og_image, fonts=FONTS, pre=pre, ld=ld(graph), cssv=CSS_VER,
           nav=nav(), body=body,
           footer=footer(), callbar=callbar())
    out = responsive_images(out)
    if hero_img:
        # preload exactly what the hero <img> will pick (same srcset + sizes), or the file itself
        mm = re.search(r'<img [^>]*data-o="%s"[^>]*>' % re.escape(hero_img), out)
        if mm:
            ss = re.search(r'srcset="([^"]*)"', mm.group(0)).group(1)
            sz = re.search(r'sizes="([^"]*)"', mm.group(0)).group(1)
            link = '<link rel="preload" as="image" imagesrcset="%s" imagesizes="%s" fetchpriority="high">' % (ss, sz)
        else:
            link = '<link rel="preload" as="image" href="%s" fetchpriority="high">' % hero_img
        out = out.replace("<!--PRE-->", link, 1)
    return out

# ------------------------------------------------------------ components
def crumbs_html(crumbs, home="Home"):
    items = ['<a href="/">%s</a>' % esc(home)] + ['<a href="%s">%s</a>' % (u, esc(n)) for n, u in crumbs[:-1]] + ["<span>%s</span>" % esc(crumbs[-1][0])]
    return '<nav class="crumbs" aria-label="Breadcrumb">%s</nav>' % " <i>/</i> ".join(items)

def hero_img_tag(img, alt):
    """Full-bleed hero <img>. responsive_images() adds the WebP srcset (full-bleed sizes)."""
    return '<img src="/%s" alt="%s" fetchpriority="high">' % (img, esc(alt))

def phero(img, alt, kicker, h1, lede, crumbs, ctas=None, cls="", home="Home"):
    ctas = ctas if ctas is not None else [
        ('<a class="btn btn-primary" href="/book/">Book a Class %s</a>' % I["arrow"]),
        ('<a class="btn btn-ghost" href="tel:%s">%s Call %s</a>' % (BIZ["phone_raw"], I["phone"], BIZ["phone"]))]
    return """<section class="phero %s">
  <div class="phero-bg">%s</div>
  <div class="wrap phero-in">
    %s
    <p class="eyebrow">%s</p>
    <h1>%s</h1>
    <p class="lede">%s</p>
    <div class="hero-cta">%s</div>
  </div>
</section>""" % (cls, hero_img_tag(img, alt), crumbs_html(crumbs, home), esc(kicker), h1, esc(lede), "".join(ctas))

def specbar(cells):
    return '<div class="specbar"><div class="wrap specbar-in">%s</div></div>' % "".join(
        '<div class="spec"><span>%s</span><b>%s</b></div>' % (esc(k), v) for k, v in cells)

def sec_head(idx, eyebrow, h2, lede=None, center=False):
    c = " is-center" if center else ""
    return '<div class="sec-head%s rv"><p class="eyebrow%s"><span class="idx">%s</span>%s</p><h2 class="h-sec">%s</h2>%s</div>' % (
        c, c, idx, esc(eyebrow), h2, ('<p class="lede">%s</p>' % esc(lede)) if lede else "")

def checks(items):
    return '<ul class="checks">%s</ul>' % "".join("<li>%s%s</li>" % (I["check"], esc(t)) for t in items)

def faq_html(faq, start=1):
    return '<div class="faq-list rv" data-faq>%s</div>' % "".join("""
  <div class="faq-item">
    <button class="faq-q" aria-expanded="false" aria-controls="fa%d"><span class="idx">%02d</span><span class="qt">%s</span><i></i></button>
    <div class="faq-a" id="fa%d"><p>%s</p></div>
  </div>""" % (i, i, esc(q), i, esc(a)) for i, (q, a) in enumerate(faq, start))

def band(h2="Building Skills.<br class=\"mbr\"> Bettering Futures.", p="Spots are limited and classes fill. Lock your seat in now, start studying early, and come ready to pass.", primary=None, eyebrow="Your Future Starts Here", call="Call"):
    primary = primary or '<a class="btn btn-primary" href="/book/">Book a Class</a>'
    return """<section class="band">
  <div class="band-bg" aria-hidden="true"><img src="/img/bg-crane-golden.jpg" alt="" loading="lazy"></div>
  <div class="wrap band-in rv">
    <div class="chev-div"><img class="chev" src="/img/chevron.png" alt=""></div>
    <p class="eyebrow is-center">%s</p>
    <h2>%s</h2>
    <p>%s</p>
    <div class="band-cta">%s<a class="btn btn-ghost" href="tel:%s">%s %s</a></div>
  </div>
</section>""" % (esc(eyebrow), h2, esc(p), primary, BIZ["phone_raw"], esc(call), BIZ["phone"])

# Student reviews that name an instructor link that name to his page.
# First names come from PEOPLE; students call Andres "Andy" in the reviews.
INSTRUCTOR_LINKS = {p["name"].split()[0]: p for p in PEOPLE}
INSTRUCTOR_LINKS["Andy"] = INSTRUCTOR_LINKS["Andres"]
_INSTRUCTOR_RE = re.compile(r"\b(%s)\b" % "|".join(sorted(INSTRUCTOR_LINKS, key=len, reverse=True)))

def link_names(t):
    """t is already HTML-escaped review text."""
    def sub(m):
        p = INSTRUCTOR_LINKS[m.group(1)]
        return '<a class="iname" href="/instructors/%s/" title="Meet %s, %s">%s</a>' % (p["slug"], esc(p["name"]), esc(p["role"]), m.group(1))
    return _INSTRUCTOR_RE.sub(sub, t)

def review_card(r):
    src = ('%s<span><b>%s</b><span>5-star review on Google</span></span>' % (I["google"], esc(r["who"]))) if r["src"] == "google" \
        else ('%s<span><b>%s</b><span>Recommends on Facebook</span></span>' % (I["fb"], esc(r["who"])))
    stars = ('<span class="stars" role="img" aria-label="5 out of 5 stars">%s</span>' % (I["star"] * 5)) if r["src"] == "google" else ""
    return '<article class="rev rv"><span class="rev-quote">&ldquo;</span>%s<p>%s</p><div class="rev-who">%s</div></article>' % (stars, link_names(esc(r["text"])), src)

def rev_grid(revs):
    return '<div class="rev-grid" data-orphan="%d">%s</div>' % (len(revs) % 3, "".join(review_card(r) for r in revs))

def cta_box(title, lines, price=None, href="/book/", label="Pick a Start Date"):
    return """<aside class="cta-box rv">
  %s<b>%s</b>%s
  <a class="btn btn-primary btn-block" href="%s">%s</a>
  <a class="btn btn-ghost btn-block" href="tel:%s">%s Call %s</a>
</aside>""" % (('<span class="cta-price">%s</span>' % price) if price else "", esc(title),
               "".join("<p>%s</p>" % l for l in lines), href, esc(label), BIZ["phone_raw"], I["phone"], BIZ["phone"])

def steps():
    return """<div class="how-grid">
  <div class="how-card rv"><span class="idx">01</span><h3>Register &amp; Hold Your Seat</h3><p>Book online in about two minutes. $200 holds your spot, and we'll send your study material so you can start early and walk in ready.</p></div>
  <div class="how-card rv"><span class="idx">02</span><h3>Train Classroom &amp; Hands-On</h3><p>Real rigging hardware, real load calculations, real crane hand signals. Small classes so you actually get your hands on the gear.</p></div>
  <div class="how-card rv"><span class="idx">03</span><h3>Test Out &amp; Get Credentialed</h3><p>Written and practical assessment right here in our accredited testing room. Pass, and your NCCER credential goes on the national registry.</p></div>
</div>"""

def people_grid(only=None):
    ps = [p for p in PEOPLE if not only or p["slug"] in only]
    return '<div class="team-grid">%s</div>' % "".join("""
      <a class="person rv" href="/instructors/%s/">
        <div class="person-img"><img src="/%s" alt="%s" loading="lazy"></div>
        <div class="person-body"><span class="person-role">%s</span><h3>%s</h3><p>%s</p><span class="person-more">Read more %s</span></div>
      </a>""" % (p["slug"], p.get("card", p["img"]), esc(p["alt"]), esc(p["role"]), esc(p["name"]), esc(p["bio"][0]), I["arrow"]) for p in ps)

def craft_short(name):
    if name.startswith("Heavy Equipment Operator: "):
        return name.split(": ", 1)[1] + " Operator"
    return name

def craft_groups_html(current=None):
    out = []
    for gname, gid in CRAFT_GROUPS:
        cs = [c for c in CRAFTS if c[2] == gid]
        if not cs: continue
        out.append('<div class="cgroup rv"><h3>%s</h3><ul class="craft-list">%s</ul></div>' % (esc(gname), "".join(
            '<li><a href="/nccer-assessments/%s/"%s>%s%s</a></li>' % (s, ' aria-current="page"' if s == current else "", I["arrow"], esc(craft_short(n)))
            for s, n, g, b, cov in cs)))
    return '<div class="cgroups">%s</div>' % "".join(out)

# ---------------------------------------------------------------- pages
PAGES = []          # (url, lastmod-priority) for sitemap
def emit(url, html_text, prio="0.7"):
    w(url.strip("/") + "/index.html" if url != "/" else "index.html", html_text)
    PAGES.append((url, prio))

TEACH_LEDE = ("We understand everyone learns differently, which is why we run plenty of visual "
              "scenarios and demonstrations: boom deflection, side loading, shock loading, block "
              "factors, the two most important knots in rigging and much more, all to help you "
              "understand the information being taught.")

# Andres described each of these photos individually, so each one gets a row of
# its own with the explanation beside it rather than a caption under a thumbnail.
# The technical detail comes off the client's own material: the wedge-socket
# steps are the slide in the first photo, the loading factors are the chart on
# the board in the last one. Do not add claims that aren't visible in the photo.
TEACH_ROWS = [
    ("demo-terminator",
     "Instructor Frank Torres showing a class how to assemble a terminator wedge socket on wire rope",
     "Assembling a terminator (becket)",
     "A Termination Is Only As Good As The Assembly",
     ["A terminator, the wedge socket that anchors the end of a wire rope, gets assembled in front "
      "of the class. The parts come apart, get inspected for cracks and wear, and go back together "
      "in order.",
      "The details are the lesson. Never mix wedges, sockets and pins across different models or "
      "sizes. Match the wedge and the socket to the rope you are actually using. Seize the dead end "
      "instead of welding it, so the strands cannot untwist or flatten. Miss one of those and the "
      "termination becomes the weakest point in the lift."]),
    ("demo-chain-hoist",
     "Two students communicating with each other to drift a load across a gantry with chain hoists",
     "Drifting a load with chain hoists",
     "Two Hoists, One Load, One Conversation",
     ["Drifting a load means moving it sideways: one hoist pays out while the other takes up, and "
      "the load walks across the span. Here two students run opposite hoists on the same load and "
      "have to keep it under control between them.",
      "The rigging is the easy half. The hard half is two people agreeing out loud on what happens "
      "next, which is exactly what goes wrong on a real job when nobody is talking."]),
    ("demo-knots",
     "Students tying the two most important knots in rigging on the training gantry",
     "The two most important knots",
     "The Two Knots You Will Actually Use",
     ["Every rigger ends up with a short list of knots that carry almost all of the work, and two of "
      "them do most of it. Students tie them on the gantry with the same rope and hardware they will "
      "see on a job, not on a desk with a length of string.",
      "Once you have tied one correctly with your own hands a few times, you stop having to remember "
      "how it goes."]),
    ("demo-block-loading",
     "Block loading demonstration board showing line pull angles and the loading factor each one produces",
     "Block loading: angles and factors",
     "The Angle Is The Whole Story",
     ["One line on the board carries the whole idea: line pull times a factor equals the load on the "
      "block and its anchorage. Change the angle between the two lines and the factor changes with "
      "it.",
      "The same rope is set at 60, 90 and 120 degrees so the difference stops being a formula on a "
      "page. Two lines running side by side put twice the line pull on the block. Open them to "
      "ninety degrees and it falls to about 1.41. Open them out into a straight line and the block "
      "carries almost nothing at all."]),
]
TEACH_CLOSE = ("Boom deflection, side loading and shock loading get the same treatment. If a thing "
               "can be shown instead of described, it gets shown.")

def teach_section(idx=None, home=False):
    """The "How We Teach It" editorial block. idx=None drops the section numeral
    (the home page's section heads don't carry one). home=True emits relative
    image paths, matching the rest of index.html."""
    lead = "" if home else "/"
    rows = "".join("""
      <article class="teach-row rv">
        <figure class="teach-shot"><img src="%simg/%s.jpg" alt="%s" loading="lazy"><figcaption>%s</figcaption></figure>
        <div class="teach-copy">
          <span class="idx">%02d</span>
          <h3>%s</h3>
          %s
        </div>
      </article>""" % (lead, slug, esc(alt), esc(cap), i + 1, esc(head),
                       "".join("<p>%s</p>" % esc(p) for p in paras))
        for i, (slug, alt, cap, head, paras) in enumerate(TEACH_ROWS))
    head = '<div class="sec-head rv"><p class="eyebrow">%s%s</p><h2 class="h-sec">Shown, Not<br>Just Told.</h2><p class="lede">%s</p></div>' % (
        ('<span class="idx">%s</span>' % idx) if idx else "", "How We Teach It", esc(TEACH_LEDE))
    return """<section class="section teach" id="how-we-teach">
  <div class="wrap">
    %s
    <div class="teach-rows" data-gallery="demonstrations">%s
    </div>
    <p class="teach-close rv">%s</p>
  </div>
</section>""" % (head, rows, esc(TEACH_CLOSE))

def build_course(c):
    url = "/%s/" % c["slug"]
    # Section numbers come off a counter: the demonstrations section only appears
    # on the rigging course, and hard-coded indices would leave a gap on the other.
    _sec = [0]
    def sn():
        _sec[0] += 1
        return "%02d" % _sec[0]
    crumbs = [("Courses", "/#courses"), (c["name"], url)]
    price_line = "%s" % money(c["price"]) + (' <s class="was">%s</s>' % money(c["was"]) if c["was"] else "")
    fmts = "".join("""
      <div class="fmt-card rv">
        <span class="idx">%02d</span>
        <b>%s</b>
        <span class="fmt-when">%s · %s</span>
        <p>%s</p>
        %s
      </div>""" % (i+1, esc(f["name"]), esc(f["when"]), esc(f["time"]), esc(f["note"]),
                   ('<a class="more" href="%s">More about this format %s</a>' % (f["link"], I["arrow"])) if f.get("link") else "")
        for i, f in enumerate(c["formats"]))
    who = "".join('<div class="who-card rv"><b>%s</b><p>%s</p></div>' % (esc(t), esc(d)) for t, d in c["who"])
    teachers = [p["slug"] for p in PEOPLE if c["slug"] in p["teaches"]]
    body = phero(c["hero"], c["hero_alt"], c["kicker"], c["h1"], c["lede"], crumbs,
                 ctas=['<a class="btn btn-primary" href="/book/?book=%s">Pick a Start Date %s</a>' % (c["id"], I["arrow"]),
                       '<a class="btn btn-ghost" href="tel:%s">%s Call %s</a>' % (BIZ["phone_raw"], I["phone"], BIZ["phone"])])
    body += specbar([("Course price", price_line), ("Holds your seat", money(c["deposit"])),
                     ("Length", "4 days" if c["id"] == "advanced" else "2 Fridays"),
                     ("Credential", esc(c["cred"].replace("NCCER Certified ", "NCCER ")))])
    body += next_dates_strip(c["id"])
    body += """<section class="section"><div class="wrap split">
  <div class="prose rv">
    %s
    <p class="lede">%s</p>
    <h3 class="h-sub">What you'll learn</h3>
    %s
  </div>
  %s
</div></section>""" % (sec_head(sn(), "The Course", "What The<br>Course Covers"), esc(c["summary"]), checks(c["learn"]),
                       cta_box("%s · %s" % (c["name"], money(c["price"])),
                               ["$%d holds your seat. Balance due before class." % c["deposit"], "Klarna, Afterpay, Zelle or in-house financing with no credit check."],
                               price=price_line, href="/book/?book=%s" % c["id"]))
    if c["id"] == "advanced": body += teach_section(sn())
    body += """<section class="section alt" id="formats"><div class="wrap">
  %s
  <div class="fmt-grid">%s</div>
  <p class="center-note rv"><a class="btn btn-ghost" href="/class-dates/">%s See Upcoming Dates</a></p>
</div></section>""" % (sec_head(sn(), "Schedules", "Built Around<br>Your Shift.", "Every format ends the same way: a written and hands-on test-out in our accredited testing room, and a credential on the NCCER Registry.", center=True), fmts, I["cal"])
    body += """<section class="section"><div class="wrap">
  %s
  <div class="who-grid">%s</div>
</div></section>""" % (sec_head(sn(), "Who It's For", "Who Takes<br>This Course"), who)
    body += """<section class="section how"><div class="how-bg" aria-hidden="true"><img src="/img/bg-classroom.jpg" alt="" loading="lazy"></div><div class="wrap">
  %s%s
</div></section>""" % (sec_head(sn(), "The Process", "Three Steps To Certified"), steps())
    body += """<section class="section"><div class="wrap">
  %s%s
</div></section>""" % (sec_head(sn(), "Who's Teaching You", "Your Instructors"), people_grid(teachers))
    body += """<section class="section alt"><div class="wrap">
  %s%s
  <p class="center-note rv"><a href="/faq/" class="more">All questions %s</a></p>
</div></section>""" % (sec_head(sn(), "Common Questions", "%s FAQ" % esc(c["name"]), center=True), faq_html(c["faq"]), I["arrow"])
    body += band(primary='<a class="btn btn-primary" href="/book/?book=%s">Pick a Start Date</a>' % c["id"])
    emit(url, page(url, c["meta_title"], c["meta_desc"], body, crumbs,
                   [course_schema(c, url), faq_schema(c["faq"])], hero_img="/" + c["hero"]), "0.9")

def build_assessments():
    url = "/nccer-assessments/"
    a = ASSESSMENT
    crumbs = [("Courses", "/#courses"), ("NCCER Assessments", url)]
    body = phero(a["hero"], a["hero_alt"], a["kicker"], a["h1"], a["lede"], crumbs,
                 ctas=['<a class="btn btn-primary" href="/book/?book=assessment">Request a Test Date %s</a>' % I["arrow"],
                       '<a class="btn btn-ghost" href="tel:%s">%s Call %s</a>' % (BIZ["phone_raw"], I["phone"], BIZ["phone"])])
    body += specbar([("Per assessment", "$150"), ("Crafts", "36"), ("When", "Mon – Fri · 8 AM – 5 PM"), ("Credential", "NCCER Registry")])
    body += """<section class="section"><div class="wrap split">
  <div class="prose rv">
    %s
    <p class="lede">An NCCER assessment is how an experienced hand gets the card without sitting through a class. You take a proctored written assessment of what you know, and for crafts that call for it a hands-on performance verification, in our accredited testing room here in Portland. Pass, and the credential is recorded on the NCCER Registry, where contractors look first.</p>
    <h3 class="h-sub">How it works</h3>
    %s
  </div>
  %s
</div></section>""" % (sec_head("01", "Test Out", "Skip The Class.<br>Prove The Craft."),
                       checks(["Book a date online or call the office.",
                               "Bring a government-issued photo ID. NCCER requires it.",
                               "Written assessment, then the hands-on performance verification where the craft calls for one.",
                               "Pass and your credential goes on the NCCER Registry.",
                               "One flat $150 per assessment, paid in full when you book."]),
                       cta_box("NCCER Assessment · $150", ["Monday through Friday, 8 AM to 5 PM, by appointment."], price="$150", href="/book/?book=assessment", label="Request a Test Date"))
    body += """<section class="section alt" id="crafts"><div class="wrap">
  %s%s
</div></section>""" % (sec_head("02", "36 Crafts", "Crafts We Assess", "Pick your craft for what the assessment covers and who it's for. Don't see yours? Call the office; more crafts are available on request.", center=True), craft_groups_html())
    body += """<section class="section"><div class="wrap">
  %s%s
</div></section>""" % (sec_head("03", "Common Questions", "Assessment FAQ", center=True), faq_html(a["faq"]))
    body += band(h2="Already Know<br class=\"mbr\"> The Work?", p="Book your assessment date, bring your ID, and leave with a credential the whole industry recognizes.",
                 primary='<a class="btn btn-primary" href="/book/?book=assessment">Request a Test Date</a>')
    emit(url, page(url, a["meta_title"], a["meta_desc"], body, crumbs,
                   [service_schema("NCCER Craft Assessments", a["meta_desc"], url), faq_schema(a["faq"])], hero_img="/" + a["hero"]), "0.9")

def build_craft(c):
    slug, name, gid, blurb, covers = c
    gname = dict((g, n) for n, g in CRAFT_GROUPS)[gid]
    url = "/nccer-assessments/%s/" % slug
    short = craft_short(name)
    crumbs = [("NCCER Assessments", "/nccer-assessments/"), (short, url)]
    title = "NCCER %s Assessment · Portland, TX" % short
    desc = "Test out of the NCCER %s assessment near Corpus Christi: proctored written and hands-on, $150 flat, credential on the NCCER Registry." % short
    book = "/book/?book=assessment&amp;craft=%s" % urllib.parse.quote(short)   # /book/ prefills the craft select from ?craft=
    siblings = [x for x in CRAFTS if x[2] == gid and x[0] != slug]
    sib = "".join('<li><a href="/nccer-assessments/%s/">%s%s</a></li>' % (s, I["arrow"], esc(craft_short(n))) for s, n, g, b, cv in siblings)
    faq = [
        ("What does the %s assessment cover?" % short, "The NCCER %s assessment covers %s Pass, and your credential is recorded on the NCCER Registry." % (name, covers)),
        ("Do I need to take a class first?", "No. This is a test-out for people who already do the work. If you want training first, see our Advanced Rigger and Signal Person courses."),
        ("What does it cost and when can I test?", "$150 flat, paid in full when you book. Assessments run Monday through Friday, 8:00 AM to 5:00 PM, by appointment at our Portland, TX testing room."),
        ("What do I bring?", "A government-issued photo ID. NCCER requires it before you can sit for the assessment."),
    ]
    body = phero("img/testing-room.jpg", "Candidates taking a proctored NCCER assessment in the on-site testing room",
                 gname, "%s<em>NCCER Assessment</em>" % esc(short),
                 "Proctored written and hands-on assessment in Portland, TX. One flat $150, credential to the NCCER Registry. Monday through Friday by appointment.", crumbs,
                 ctas=['<a class="btn btn-primary" href="%s">Request a Test Date %s</a>' % (book, I["arrow"]),
                       '<a class="btn btn-ghost" href="tel:%s">%s Call %s</a>' % (BIZ["phone_raw"], I["phone"], BIZ["phone"])], cls="phero-craft")
    body += specbar([("Assessment fee", "$150"), ("Format", "Written + hands-on"), ("When", "Mon – Fri · 8 AM – 5 PM"), ("Credential", "NCCER Registry")])
    body += """<section class="section"><div class="wrap split">
  <div class="prose rv">
    %s
    <p class="lede">%s</p>
    <h3 class="h-sub">What the assessment covers</h3>
    <p>The NCCER %s assessment covers %s Pass, and the credential is recorded on the NCCER Registry.</p>
    <h3 class="h-sub">Who tests out</h3>
    %s
  </div>
  %s
</div></section>""" % (sec_head("01", "The Assessment", "Prove What<br>You Already Know."), esc(blurb), esc(name), esc(covers),
                       checks(["Experienced %ss who need the NCCER credential on paper" % short.lower() if not short.endswith("Operator") else "Experienced operators who need the NCCER credential on paper",
                               "Hands whose credential is coming due for renewal",
                               "Hands whose contractor needs the credential verified before a turnaround",
                               "Anyone hired on the condition of getting the card"]),
                       cta_box("%s · $150" % short, ["Written and hands-on, proctored on-site.", "Monday through Friday, 8 AM to 5 PM, by appointment."], price="$150", href=book, label="Request a Test Date"))
    body += """<section class="section how"><div class="how-bg" aria-hidden="true"><img src="/img/bg-classroom.jpg" alt="" loading="lazy"></div><div class="wrap">
  %s
  <div class="how-grid">
    <div class="how-card rv"><span class="idx">01</span><h3>Book Your Date</h3><p>Online in two minutes, or call the office.</p></div>
    <div class="how-card rv"><span class="idx">02</span><h3>Test In Portland</h3><p>Written assessment first, then the hands-on performance verification where the craft calls for one.</p></div>
    <div class="how-card rv"><span class="idx">03</span><h3>Get The Credential</h3><p>Pass and it's recorded on the NCCER Registry, where every contractor in the country can verify it.</p></div>
  </div>
</div></section>""" % sec_head("02", "How It Works", "Three Steps To The Card")
    body += """<section class="section alt"><div class="wrap split">
  <div class="rv">%s%s</div>
  <div class="rv"><h3 class="h-sub">Other crafts in %s</h3><ul class="craft-list">%s</ul><p style="margin-top:18px"><a class="more" href="/nccer-assessments/#crafts">All 36 crafts %s</a></p></div>
</div></section>""" % (sec_head("03", "Common Questions", "%s FAQ" % esc(short)), faq_html(faq), esc(gname), sib, I["arrow"])
    body += band(h2="Already Know<br class=\"mbr\"> The Work?", p="Book your %s assessment, bring your ID, and leave with a credential the whole industry recognizes." % short,
                 primary='<a class="btn btn-primary" href="%s">Request a Test Date</a>' % book)
    emit(url, page(url, title, desc, body, crumbs,
                   [service_schema("NCCER %s Assessment" % name, desc, url), faq_schema(faq)], hero_img="/img/testing-room.jpg"), "0.6")

def build_format_page(url, title, desc, hero, alt, kicker, h1, lede, idx_title, paras, checks_list, faq, book="advanced", specs=None, band_h2=None, crumb=None, cta=None, hero_cta=None, band_primary=None):
    crumbs = [("Advanced Rigger", "/advanced-rigger/"), (crumb or title.split(" (")[0].split(" in ")[0], url)]
    body = phero(hero, alt, kicker, h1, lede, crumbs,
                 ctas=hero_cta or ['<a class="btn btn-primary" href="/book/?book=%s">Pick a Start Date %s</a>' % (book, I["arrow"]),
                       '<a class="btn btn-ghost" href="tel:%s">%s Call %s</a>' % (BIZ["phone_raw"], I["phone"], BIZ["phone"])])
    if specs: body += specbar(specs)
    body += """<section class="section"><div class="wrap split">
  <div class="prose rv">%s%s<h3 class="h-sub">What's included</h3>%s</div>
  %s
</div></section>""" % (sec_head("01", "The Format", idx_title), "".join('<p class="lede">%s</p>' % esc(p) for p in paras), checks(checks_list),
                       cta or cta_box("Advanced Rigger · $1,000", ["$200 holds your seat. Balance due before class.", "Klarna, Afterpay, Zelle or in-house financing."], price='$1,000 <s class="was">$1,700</s>', href="/book/?book=%s" % book))
    body += """<section class="section alt"><div class="wrap">%s%s</div></section>""" % (sec_head("02", "Common Questions", "Before You Enroll", center=True), faq_html(faq))
    body += """<section class="section"><div class="wrap">%s%s</div></section>""" % (sec_head("03", "Who's Teaching You", "Your Instructors"), people_grid(["andres-herrera", "frank-torres"]))
    body += band(h2=band_h2 or "Building Skills. Bettering Futures.", primary=band_primary or '<a class="btn btn-primary" href="/book/?book=%s">Pick a Start Date</a>' % book)
    emit(url, page(url, title, desc, body, crumbs, [faq_schema(faq)], hero_img="/" + hero), "0.8")

def build_dates():
    url = "/class-dates/"
    crumbs = [("Class Dates", url)]
    body = phero("img/bg-classroom.jpg", "Students in the Prime Lift Rigging Academy classroom", "Upcoming Classes",
                 "Class Dates<em>&amp; Schedules</em>",
                 "Advanced Rigger starts every Monday (days or nights) and every other Friday (weekend express). Signal Person starts every other Friday. Assessments run any weekday. Booking closes the day before a class starts.", crumbs)
    body += specbar([("Advanced Rigger", "Mon – Thu · 8 AM – 2 PM"), ("Night class", "Mon – Thu · 6 – 11 PM"), ("Weekend express", "Fri – Sun · 8 AM – 5 PM"), ("Signal Person", "Fridays · 8 AM – 3 PM")])
    body += ("""<section class="section"><div class="wrap">
  %s
  <div class="sched-list" id="schedList"></div>
  <p class="center-note rv" style="margin-top:30px">Seats are capped at 8 per class. Pick a date to reserve yours with a $200 deposit, or <a href="tel:%s" style="color:var(--accent)">call %s</a> to book by phone.</p>
</div></section>
<script>
/* Recurrence rules come from SCHEDULE_RULES in build.py (shared with the course pages). Change the rule there, never a list of dates. */
(function(){
  const SEATS=8, LEAD=1, MON=1, FRI=5, X=__SCHED__;
  const MONS=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], DOW=["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
  const iso=d=>d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");
  const SHORT={day:"Day class",night:"Night class",weekend:"Weekend Express",friday:"Two Fridays",assess:"Assessment"};
  const closed=d=>!!X.closed[iso(d)];
  /* full = the office's static FULL list OR the live seat count (site.js -> window.__plSeats).
     A full date is never rendered: the office wants booked dates gone, not counted down. */
  const full=(d,k)=>{ const f=X.full[iso(d)]||[]; if(f.includes(k)||f.includes("*")) return true;
    const L=window.__plSeats; return !!(L&&L.taken&&((L.cap||SEATS)-(L.taken[k+":"+iso(d)]||0)<=0)); };
  function first(){ const d=new Date(); d.setHours(0,0,0,0); d.setDate(d.getDate()+LEAD); return d; }
  /* a cadence wider than weekly is phased off the rule anchor date, not off today. */
  function phase(d,step,anchor){ if(!anchor||step===7) return; const p=anchor.split("-").map(Number), a=new Date(p[0],p[1]-1,p[2]); const off=((Math.round((d-a)/864e5)%%step)+step)%%step; if(off) d.setDate(d.getDate()+(step-off)); }
  function every(wd,n,step,anchor,k){ step=step||7; const d=first(),o=[]; while(d.getDay()!==wd) d.setDate(d.getDate()+1); phase(d,step,anchor); while(o.length<n){ if(!closed(d)&&!full(d,k)) o.push(new Date(d)); d.setDate(d.getDate()+step);} return o; }
  function weekdays(n,k){ const d=first(),o=[]; while(o.length<n){ if(d.getDay()>=MON&&d.getDay()<=FRI&&!closed(d)&&!full(d,k)) o.push(new Date(d)); d.setDate(d.getDate()+1);} return o; }
  /* rendered as a function: live counts land after first paint (pl:seats), and a date
     that just filled drops out with the next one backfilling behind it */
  function render(){
    const P=__RULES__.map(r=>Object.assign({},r,{dates:r.wd==="weekday"?weekdays(r.n,r.id+":"+r.fmt):every(r.wd,r.n,r.every,r.anchor,r.id+":"+r.fmt)}));
    document.getElementById("schedList").innerHTML=P.map((p,i)=>`
    <div class="sched-block rv in">
      <div class="sched-head"><span class="idx">${String(i+1).padStart(2,"0")}</span><div><b>${p.name}</b><span>${p.label} · ${p.time}</span></div></div>
      <div class="date-grid">${p.dates.map(d=>`
        <a class="date" href="/book/?book=${p.id}&fmt=${p.fmt}&date=${iso(d)}">
          <span class="date-cal"><em>${MONS[d.getMonth()]}</em><b>${d.getDate()}</b></span>
          <span class="date-info"><b>${DOW[d.getDay()]}</b><span>${p.name} · ${SHORT[p.fmt]||p.label}</span></span>
        </a>`).join("")}</div>
    </div>`).join("");
  }
  render();
  document.addEventListener("pl:seats",render);
})();
</script>""" % (sec_head("01", "Pick A Date", "Next Classes<br>In Portland, TX", "Weekday classes start every Monday. The weekend express and signal person classes run every other Friday. Tap a date to hold it.", center=True), BIZ["phone_raw"], BIZ["phone"])).replace("__RULES__", rules_json()).replace("__SCHED__", sched_json())
    body += band(primary='<a class="btn btn-primary" href="/book/">Book a Class</a>')
    emit(url, page(url, "Class Dates & Schedules · Rigging Classes in Portland, TX", "Upcoming Advanced Rigger and Signal Person class dates in Portland, TX: weekday day and night classes, 3-day weekend express, assessment dates. $200 holds a seat.", body, crumbs, hero_img="/img/bg-classroom.jpg"), "0.8")

def build_financing():
    url = "/financing/"
    crumbs = [("Financing", url)]
    cards = "".join('<div class="fin-card rv"><span class="idx">%02d</span><b>%s</b><span>%s</span><em class="fin-tag">%s</em></div>' % (i+1, esc(t), esc(d), esc(tag)) for i, (t, d, tag) in enumerate(FINANCING))
    faq = [
        ("What do I pay today?", "$200 for a course, which holds your seat. The remaining $800 is due before your class begins. Assessments are $150, paid in full when you book."),
        ("How do Klarna and Afterpay work here?", "Both pay the full $1,000 at checkout and then split it into installments for you. On the checkout screen, choose Klarna or Afterpay instead of the $200 card deposit. Approval is instant and your seat is confirmed the moment they approve."),
        ("What if I don't qualify for Klarna or Afterpay?", "Choose in-house financing. As little as $200 down, no credit check, and payments leading up to your class date. Your course begins once the balance is paid in full."),
        ("Is the deposit refundable?", "A $200 deposit is required to secure your spot. This deposit is non-refundable. However, you are allowed one reschedule as long as at least 48 hours' notice is provided. Rescheduling requests made with less than 48 hours' notice will result in the loss of your deposit."),
        ("Can my employer pay?", "Yes. Choose \"My employer is paying\" on the booking form and the office will coordinate with them. Companies can book up to 8 seats per class."),
        ("Do you take Zelle or cash?", "Zelle, yes: message us on Facebook or email primelift26@gmail.com and we'll register you manually. For anything else, call the office."),
    ]
    body = phero("img/bg-crane-golden.jpg", "Crawler crane at golden hour on a Coastal Bend jobsite", "Payment Options",
                 "Don't Let The Cost<em>Hold You Back.</em>",
                 "$200 holds your seat today. After that, pay it how it works for you: card, Klarna, Afterpay, Zelle, or in-house financing with no credit check.", crumbs)
    body += specbar([("Course price", '$1,000 <s class="was">$1,700</s>'), ("Deposit", "$200"), ("Assessment", "$150"), ("Credit check", "None for in-house")])
    body += """<section class="section"><div class="wrap">
  %s
  <div class="fin-cards fin-cards-3">%s</div>
  <div class="fin-note rv" style="max-width:760px;margin:30px auto 0"><strong>Heads up:</strong> your course can't begin until the balance is paid in full, so get started early and give yourself room to pay it down before your start date.</div>
</div></section>""" % (sec_head("01", "Five Ways To Pay", "Pick The One<br>That Fits.", center=True), cards)
    body += """<section class="section alt" id="employer"><div class="wrap split">
  <div class="prose rv">
    %s
    <p class="lede">If your company is covering the course, you don't need to front the money. Choose "My employer is paying" on the booking form and put your supervisor's or safety manager's contact in the notes; the office coordinates payment with them directly. Assessments work the same way.</p>
    %s
  </div>
  %s
</div></section>""" % (sec_head("02", "Employer-Sponsored Training", "Your Employer<br>Can Pay."),
                       checks(["Pick \"My employer is paying\" on the booking form and add their contact",
                               "The office coordinates payment with your company",
                               "You train and test out here like any other student; the credential posts to the NCCER Registry under your name"]),
                       cta_box("Company Paying?", ["Choose \"My employer is paying\" when you book and put your supervisor's contact in the notes.", "The office coordinates the invoice with them directly."], href="/book/", label="Reserve Your Seat"))
    body += """<section class="section"><div class="wrap">%s%s</div></section>""" % (sec_head("03", "Common Questions", "Financing FAQ", center=True), faq_html(faq))
    body += band(h2="Your Goals<br class=\"mbr\"> Are Worth It.", p="Reserve your seat with $200 and we'll walk you through the rest on the phone if you'd rather talk it through.")
    emit(url, page(url, "Financing & Payment Plans · No Credit Check", "Pay for NCCER rigger certification your way: $200 deposit, Klarna, Afterpay, Zelle, or in-house financing with no credit check. Portland, TX.", body, crumbs, [faq_schema(faq)], hero_img="/img/bg-crane-golden.jpg"), "0.8")

def build_instructors():
    url = "/instructors/"
    crumbs = [("Instructors", url)]
    body = phero("img/class-sling-demo.jpg", "Instructor demonstrating a sling hitch on a load during class", "Who's Teaching You",
                 "Craft Pros Aren't Born.<em>They're Built.</em>",
                 "Every person in front of the class came up in the field first: refineries, plants, shipyards and heavy lift. Ask questions. That's what they're here for.", crumbs)
    body += """<section class="section"><div class="wrap">%s%s</div></section>""" % (sec_head("01", "The Team", "Meet Your<br>Instructors", center=True), people_grid())
    body += """<section class="section alt"><div class="wrap">%s%s</div></section>""" % (sec_head("02", "Straight From Our Students", "What Students Say<br>About The Teaching", center=True), rev_grid([r for r in REVIEWS if r["src"] == "google"] + REVIEWS[3:4]))
    body += band()
    emit(url, page(url, "Instructors · NCCER Rigging Instructors in Portland, TX", "Meet the Prime Lift team: Andres Herrera (NCCER Practical Examiner), Juan Meza (Director) and Frank Torres (Advanced Rigging Instructor). Craft pros teaching in Portland, TX.", body, crumbs,
                   [person_schema(p, "/instructors/%s/" % p["slug"]) for p in PEOPLE], hero_img="/img/class-sling-demo.jpg"), "0.7")

def build_person(p):
    url = "/instructors/%s/" % p["slug"]
    crumbs = [("Instructors", "/instructors/"), (p["name"], url)]
    course_map = {"advanced-rigger": ("Advanced Rigger", "/advanced-rigger/"), "signal-person": ("Signal Person", "/signal-person/"), "nccer-assessments": ("NCCER Assessments", "/nccer-assessments/")}
    teaches = "".join('<li><a href="%s">%s%s</a></li>' % (course_map[t][1], I["arrow"], course_map[t][0]) for t in p["teaches"])
    others = [x for x in PEOPLE if x["slug"] != p["slug"]]
    body = """<section class="person-hero">
  <div class="wrap person-hero-in">
    <div class="person-portrait rv"><img src="/%s" alt="%s" fetchpriority="high"></div>
    <div class="person-copy rv">
      %s
      <p class="eyebrow">%s</p>
      <h1>%s</h1>
      %s
      <h3 class="h-sub">Teaches</h3>
      <ul class="craft-list">%s</ul>
      <div class="hero-cta">
        <a class="btn btn-primary" href="/book/">Book a Class %s</a>
        <a class="btn btn-ghost" href="tel:%s">%s Call %s</a>
      </div>
    </div>
  </div>
</section>""" % (p["img"], esc(p["alt"]), crumbs_html(crumbs), esc(p["role"]), esc(p["name"]).replace(" ", "<em>", 1) + "</em>",
                 "".join('<p class="lede">%s</p>' % esc(b) for b in p["bio"]), teaches, I["arrow"], BIZ["phone_raw"], I["phone"], BIZ["phone"])
    body += """<section class="section alt"><div class="wrap">%s%s</div></section>""" % (sec_head("01", "The Rest Of The Team", "Also Teaching<br>At Prime Lift", center=True), people_grid([o["slug"] for o in others]))
    body += band()
    emit(url, page(url, "%s · %s" % (p["name"], p["role"]), p["meta_desc"], body, crumbs, [person_schema(p, url)], og_image="/" + p["img"], hero_img="/" + p["img"]), "0.6")

def build_contact():
    url = "/contact/"
    crumbs = [("Contact", url)]
    body = phero("img/storefront-front.jpg", "Prime Lift Rigging Academy storefront at 1605 US Highway 181 Frontage Rd, Suite A, Portland, TX", "Find Us",
                 "Portland,<em>Texas</em>",
                 "Right off US-181, minutes from Corpus Christi, Ingleside and Gregory. Walk in during office hours, call, or send a message and the office will get back to you.", crumbs,
                 ctas=['<a class="btn btn-primary" href="tel:%s">%s Call %s</a>' % (BIZ["phone_raw"], I["phone"], BIZ["phone"]),
                       '<a class="btn btn-ghost" href="#message">Send a Message %s</a>' % I["arrow"]])
    body += """<section class="section"><div class="wrap contact-grid">
  <div class="rv">
    <ul class="loc-list">
      <li>%s<div><b>Training &amp; Assessment Center</b><span>%s<br>%s, %s %s</span></div></li>
      <li>%s<div><b>Office Hours</b><span>%s<br><em>Hours may vary during class weeks</em></span></div></li>
      <li>%s<div><b>Phone</b><a href="tel:%s">%s</a></div></li>
      <li>%s<div><b>Email</b><a href="mailto:%s">%s</a></div></li>
    </ul>
    <div class="contact-links">
      <a class="btn btn-ghost" href="%s" target="_blank" rel="noopener">%s Directions</a>
      <a class="btn btn-ghost" href="%s" target="_blank" rel="noopener">%s Facebook</a>
      <a class="btn btn-ghost" href="%s" target="_blank" rel="noopener">%s TikTok</a>
    </div>
  </div>
  <div class="map rv"><iframe title="Map to Prime Lift Rigging Academy, %s" src="%s" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe></div>
</div></section>""" % (I["pin"], esc(BIZ["street"]), BIZ["city"], BIZ["state"], BIZ["zip"], I["clock"], esc(BIZ["hours"]), I["phone"], BIZ["phone_raw"], BIZ["phone"],
                       I["mail"], BIZ["email"], BIZ["email"], BIZ["gmaps"], I["pin"], BIZ["facebook"], I["fb"], BIZ["tiktok"], I["tiktok"], esc(FULL_ADDR), BIZ["map_embed"])
    body += """<section class="section alt" id="message"><div class="wrap split">
  <div class="rv">
    %s
    <p class="lede">Questions about a class, an assessment craft you don't see listed, or paying by Zelle? Send it here and the office will call or email you back during business hours. Ready to book? <a href="/book/" style="color:var(--accent)">Reserve online</a> and skip the wait.</p>
  </div>
  <form class="cform rv" name="contact" method="POST" data-netlify="true" netlify-honeypot="bot-field" action="/thanks.html">
    <input type="hidden" name="form-name" value="contact">
    <p class="sr"><label>Don't fill this out: <input name="bot-field"></label></p>
    <div class="two-up">
      <label class="field"><span>First name</span><input type="text" name="first_name" autocomplete="given-name" required></label>
      <label class="field"><span>Last name</span><input type="text" name="last_name" autocomplete="family-name"></label>
    </div>
    <label class="field"><span>Mobile number</span><input type="tel" name="phone" autocomplete="tel" required></label>
    <label class="field"><span>Email</span><input type="email" name="email" autocomplete="email"></label>
    <label class="field"><span>What are you asking about?</span>
      <select name="program">
        <option>Advanced Rigger course</option><option>Signal Person course</option><option>NCCER assessment (test out)</option>
        <option>Recertification</option><option>Financing or paying by Zelle</option><option>Something else</option>
      </select></label>
    <label class="field"><span>Your message</span><textarea name="notes" rows="4" required></textarea></label>
    <input type="hidden" name="page" value="/contact/">
    <button class="btn btn-primary btn-block" type="submit">Send Message %s</button>
    <p class="pay-legal">The office answers during business hours, Monday through Friday. For anything urgent, call %s.</p>
  </form>
</div></section>""" % (sec_head("01", "Send A Message", "Talk To<br>The Office"), I["arrow"], BIZ["phone"])
    body += band(h2="Or Just<br class=\"mbr\"> Book It.", p="No phone tag. Pick your class, pick a start date, and hold your seat with $200 in about two minutes.")
    emit(url, page(url, "Contact · Prime Lift Rigging Academy, Portland, TX", "Call (361) 213-9690, email primelift26@gmail.com, or visit 1605 US Hwy 181 Frontage Rd, Suite A, Portland, TX 78374. Mon–Fri 7 AM to 5 PM.", body, crumbs, hero_img="/img/storefront-front.jpg"), "0.7")

def build_about():
    url = "/about/"
    crumbs = [("About", url)]
    body = phero("img/bg-crane-golden.jpg", "Crawler crane at golden hour on a Coastal Bend jobsite", "About Prime Lift",
                 "Building Skills.<em>Bettering Futures.</em>",
                 "Prime Lift Rigging Academy is an NCCER Accredited Training and Assessment Center in Portland, Texas, built by craft professionals for the crews of the Coastal Bend.", crumbs)
    body += """<section class="section"><div class="wrap split">
  <div class="prose rv">
    %s
    <p class="lede">After years of hands-on field experience, Andres Herrera and his business partner built Prime Lift to help craft professionals earn the credentials that move their careers. The idea was simple: train people the way the work actually happens, test them in the same building, and put the credential on the NCCER Registry where every contractor looks.</p>
    <p class="lede">We're a locally and Latino-owned school on the US-181 frontage road in Portland, minutes from the refineries, plants and shipyards of Corpus Christi, Ingleside and Gregory. Classes are small, capped at 8, and taught by people who came up in the field.</p>
    <h3 class="h-sub">What we do</h3>
    %s
  </div>
  %s
</div></section>""" % (sec_head("01", "Our Story", "Built By Craft Pros,<br>For Craft Pros."),
                       checks(["NCCER Advanced Rigger certification: 4-day, night, or 3-day weekend express",
                               "NCCER Signal Person certification: two Fridays",
                               "NCCER craft assessments in 36 crafts, $150 flat, by appointment",
                               "Financing with no credit check, so the cost never decides it",
                               "Classes capped at 8 seats"]),
                       cta_box("Ready When You Are", ["$200 holds a seat in any course.", "Assessments run every weekday by appointment."]))
    body += """<section class="section alt"><div class="wrap">%s%s</div></section>""" % (sec_head("02", "The Team", "Who's Teaching You", center=True), people_grid())
    body += """<section class="section"><div class="wrap">%s%s</div></section>""" % (sec_head("03", "Where We Are", "Serving The<br>Coastal Bend", "Students come to us from %s and %s, and from across South Texas." % (", ".join(BIZ["areas"][:-1]), BIZ["areas"][-1]), center=True),
        '<div class="map rv" style="max-width:960px;margin-inline:auto"><iframe title="Map to Prime Lift Rigging Academy" src="%s" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe></div>' % BIZ["map_embed"])
    body += band()
    emit(url, page(url, "About · NCCER Accredited Rigging School in Portland, TX", "Locally and Latino-owned NCCER Accredited Training and Assessment Center in Portland, TX, serving the refineries, plants and shipyards of the Coastal Bend.", body, crumbs, hero_img="/img/bg-crane-golden.jpg"), "0.6")

def build_reviews():
    url = "/reviews/"
    crumbs = [("Student Reviews", url)]
    body = phero("img/grad-johnny.jpg", "Prime Lift graduate holding an NCCER Certified Advanced Rigger certificate", "Straight From Our Students",
                 "Certified.<em>Confident. Hired.</em>",
                 "Every review here is from a real student, on Google or Facebook, in their own words.", crumbs,
                 ctas=['<a class="btn btn-primary" href="%s" target="_blank" rel="noopener">%s Read Them On Google</a>' % (BIZ["gmaps"], I["google"]),
                       '<a class="btn btn-ghost" href="/book/">Reserve Your Seat %s</a>' % I["arrow"]])
    body += """<section class="section"><div class="wrap">%s%s
  <div class="gal rv">
    <figure><img src="/img/grad-aaron.jpg" alt="Aaron S. holding his NCCER Certified Advanced Rigger certificate" loading="lazy"><figcaption>Aaron S. &middot; Advanced Rigger</figcaption></figure>
    <figure><img src="/img/grad-andrew.jpg" alt="Andrew M. holding his NCCER Certified Advanced Rigger certificate" loading="lazy"><figcaption>Andrew M. &middot; Advanced Rigger</figcaption></figure>
    <figure><img src="/img/grad-justin.jpg" alt="Justin M. holding his NCCER Certified Advanced Rigger certificate" loading="lazy"><figcaption>Justin M. &middot; Advanced Rigger</figcaption></figure>
    <figure><img src="/img/grad-dustin.jpg" alt="Dustin T. holding his NCCER Certified Advanced Rigger certificate" loading="lazy"><figcaption>Dustin T. &middot; Advanced Rigger</figcaption></figure>
    <figure><img src="/img/grad-michael.jpg" alt="Michael C. holding his NCCER Certified Advanced Rigger certificate" loading="lazy"><figcaption>Michael C. &middot; Advanced Rigger</figcaption></figure>
    <figure><img src="/img/grad-leonel.jpg" alt="Prime Lift graduate holding an NCCER Certified Advanced Rigger certificate" loading="lazy"><figcaption>Certified Advanced Rigger</figcaption></figure>
    <figure><img src="/img/class-sling-demo.jpg" alt="Instructor demonstrating a sling hitch on a load during class" loading="lazy"><figcaption>Hands-on rigging class</figcaption></figure>
    <figure><img src="/img/testing-room.jpg" alt="Candidates taking a proctored NCCER assessment in the on-site testing room" loading="lazy"><figcaption>NCCER testing room</figcaption></figure>
  </div>
</div></section>""" % (sec_head("01", "Reviews", "What Students<br>Are Saying", center=True), rev_grid(REVIEWS))
    body += band(h2="Be The<br class=\"mbr\"> Next Review.", p="Small classes, instructors who don't move on until you get it, and a credential that follows you to every jobsite.")
    emit(url, page(url, "Student Reviews · Prime Lift Rigging Academy", "What students say about Prime Lift Rigging Academy's NCCER rigging classes in Portland, TX: 5-star Google reviews and Facebook recommendations from graduates.", body, crumbs, hero_img="/img/grad-johnny.jpg"), "0.6")

def build_faq():
    url = "/faq/"
    crumbs = [("FAQ", url)]
    body = phero("img/bg-classroom.jpg", "Students in the Prime Lift Rigging Academy classroom", "Common Questions",
                 "Before<em>You Enroll</em>",
                 "Straight answers on cost, schedules, financing, credentials and testing out. Don't see yours? Call the office or send a message.", crumbs,
                 ctas=['<a class="btn btn-primary" href="/book/">Book a Class %s</a>' % I["arrow"],
                       '<a class="btn btn-ghost" href="/contact/#message">Ask A Question</a>'])
    body += """<section class="section"><div class="wrap">%s</div></section>""" % faq_html(FAQ)
    body += band()
    emit(url, page(url, "FAQ · NCCER Rigging Classes & Assessments in Portland, TX", "Course length, cost, the $200 deposit, Klarna and Afterpay, no-credit-check financing, NCCER credentials, testing out and where to find us.", body, crumbs, [faq_schema(FAQ)], hero_img="/img/bg-classroom.jpg"), "0.7")


def next_dates_strip(cid):
    """Next 3 start dates per format, from SCHEDULE_RULES. Refreshed client-side (site.js) from the same rule."""
    rows = []
    for r in SCHEDULE_RULES:
        if r["id"] != cid: continue
        links = "".join('<a class="nd-date" href="/book/?book=%s&amp;fmt=%s&amp;date=%s">%s</a>' % (
            r["id"], r["fmt"], d.isoformat(), d.strftime("%a, %b ") + str(d.day))
            for d in next_dates(r["wd"], 3, r["id"] + ":" + r["fmt"], r.get("every", 7), r.get("anchor")))
        rows.append('<div class="nd-row" data-wd="%s" data-lead="%d" data-book="%s" data-fmt="%s" data-every="%d" data-anchor="%s"><b>%s</b><div class="nd-dates">%s</div></div>' % (
            r["wd"], LEAD_DAYS, r["id"], r["fmt"], r.get("every", 7), r.get("anchor", ""), esc(r["label"]), links))
    return '<div class="nextdates"><div class="wrap nextdates-in"><p class="nd-h">Next start dates</p>%s<a class="more nd-all" href="/class-dates/">See all dates %s</a></div></div>' % ("".join(rows), I["arrow"])

GUIDE_DATE = "2026-08-29"
GUIDE_RELATED = {
    "nccer-vs-nccco-rigger": [("Advanced Rigger course", "/advanced-rigger/"), ("Signal Person course", "/signal-person/")],
    "is-the-nccer-advanced-rigger-test-hard": [("Advanced Rigger course", "/advanced-rigger/"), ("Class dates", "/class-dates/")],
    "how-to-verify-nccer-credentials": [("NCCER assessments in 36 crafts", "/nccer-assessments/"), ("Rigger recertification", "/rigger-recertification/")],
}

def guide_url(g): return "/guides/%s/" % g["slug"]

def build_guides():
    url = "/guides/"
    crumbs = [("Guides", url)]
    cards = "".join("""
      <a class="guide-card rv" href="%s">
        <span class="idx">%02d</span>
        <b>%s</b>
        <p>%s</p>
        <span class="person-more">Read the guide %s</span>
      </a>""" % (guide_url(g), i+1, esc(g["title"]), esc(g["meta_desc"]), I["arrow"]) for i, g in enumerate(GUIDES))
    body = phero("img/bg-classroom.jpg", "Students in the Prime Lift Rigging Academy classroom", "Straight Answers",
                 "Rigging<em>Guides</em>",
                 "Plain-English answers for Coastal Bend workers deciding on training: which rigger credential you need, what the test is like, and how credentials get verified.", crumbs,
                 ctas=['<a class="btn btn-primary" href="/book/">Book a Class %s</a>' % I["arrow"],
                       '<a class="btn btn-ghost" href="/faq/">Read The FAQ</a>'])
    body += """<section class="section"><div class="wrap">%s<div class="guide-grid">%s</div></div></section>""" % (
        sec_head("01", "Guides", "Before You<br>Spend A Dime", "Written by the school, checked against what we actually do here in Portland. No pass-rate hype, no fluff.", center=True), cards)
    body += band()
    schema = [{"@type": "ItemList", "name": "Rigging guides", "itemListElement": [
        {"@type": "ListItem", "position": i+1, "url": BASE + guide_url(g), "name": g["title"]} for i, g in enumerate(GUIDES)]}]
    emit(url, page(url, "Rigging Guides · NCCER Credentials, Tests & Verification", "Plain-English guides for Coastal Bend workers: NCCER vs. NCCCO rigger credentials, what the Advanced Rigger test covers, and how NCCER credentials are verified.", body, crumbs, schema, hero_img="/img/bg-classroom.jpg"), "0.6")
    for g in GUIDES: build_guide(g)

def build_guide(g):
    url = guide_url(g)
    crumbs = [("Guides", "/guides/"), (g["title"], url)]
    words = len(re.sub(r"<[^>]+>", " ", g["body"]).split())
    # in-article CTA: dropped in before the third h2 so it sits mid-read
    parts = g["body"].split("<h2>")
    cta = """<aside class="guide-cta rv"><b>Train And Test In Portland</b><p>Advanced Rigger $1,000, Signal Person $1,000, NCCER assessments $150. Day, night or one weekend, test-out on site, $200 holds a seat.</p>
<div class="hero-cta"><a class="btn btn-primary" href="/book/">Pick a Start Date</a><a class="btn btn-ghost" href="tel:%s">%s Call %s</a></div></aside>
""" % (BIZ["phone_raw"], I["phone"], BIZ["phone"])
    cut = min(3, len(parts) - 1)
    body_html = "<h2>".join(parts[:cut]) + cta + "<h2>" + "<h2>".join(parts[cut:])
    if g["slug"] == "is-the-nccer-advanced-rigger-test-hard" and RETEST_POLICY:
        body_html = body_html.replace("Ask us about retest options;", "%s Ask us about retest options;" % esc(RETEST_POLICY), 1)
    if g["slug"] == "how-to-verify-nccer-credentials" and CREDENTIAL_POSTING_TIME:
        body_html = body_html.replace("Ask the office how long posting takes", "%s Ask the office how long posting takes" % esc(CREDENTIAL_POSTING_TIME), 1)
    related = [(x["title"], guide_url(x)) for x in GUIDES if x["slug"] != g["slug"]] + GUIDE_RELATED[g["slug"]]
    rel = "".join('<li><a href="%s">%s%s</a></li>' % (u, I["arrow"], esc(n)) for n, u in related)
    date_txt = datetime.date.fromisoformat(GUIDE_DATE).strftime("%B ") + str(datetime.date.fromisoformat(GUIDE_DATE).day) + ", " + GUIDE_DATE[:4]
    body = """<section class="ghead"><div class="wrap ghead-in rv">
  %s
  <p class="eyebrow">%s</p>
  <h1>%s</h1>
  <p class="lede">%s</p>
  <p class="gmeta">By Prime Lift Rigging Academy · <time datetime="%s">%s</time> · %s</p>
</div></section>
<article class="section"><div class="wrap guide-wrap">
  <div class="guide-body rv">%s</div>
  <div class="rv" style="margin-top:44px;padding-top:30px;border-top:1px solid var(--edge)"><h2 class="h-sub" style="margin-top:0">Related</h2><ul class="craft-list">%s</ul></div>
</div></article>""" % (crumbs_html(crumbs), esc(g["kicker"]), g.get("h1") or esc(g["title"]), esc(g["lede"]), GUIDE_DATE, date_txt, esc(g["read"]), body_html, rel)
    body += band()
    schema = [{"@type": "Article", "@id": BASE + url + "#article", "headline": g["title"], "description": g["meta_desc"],
               "url": BASE + url, "mainEntityOfPage": {"@id": BASE + url}, "datePublished": GUIDE_DATE, "dateModified": GUIDE_DATE,
               "author": {"@type": "Organization", "@id": BASE + "/#org", "name": BIZ["name"]}, "publisher": {"@id": BASE + "/#org"},
               "image": BASE + "/img/og.jpg", "inLanguage": "en-US", "wordCount": words, "articleSection": "Guides"}]
    emit(url, page(url, g["meta_title"], g["meta_desc"], body, crumbs, schema), "0.6")

# ------------------------------------------------------------------ /book/
# The booking page. Steps stack down the page; each finished step collapses to a
# one-line summary with a Change link, the current one is open, later ones wait.
# Program / format / date data come from COURSES + SCHEDULE_RULES, the same source
# as the class-dates page and the course-page date strips, so they can't disagree.
# The home page's #schedule band and every "Pick a Start Date" button deep-link
# here: /book/?book=advanced&fmt=night&date=2026-09-14
BOOK_BLURBS = {
    "advanced":   "Lift planning, load math, slings, hardware and a hands-on practical. Four days, or one weekend.",
    "signal":     "Crane hand signals, radio and voice procedure, written and practical test. Two Fridays.",
    "assessment": "Already do the work? Test out: written and hands-on, proctored on-site. One flat price, 36 crafts.",
}
def book_programs():
    fmts = {}
    for r in SCHEDULE_RULES:
        fmts.setdefault(r["id"], []).append({"id": r["fmt"], "name": r["label"], "time": r["time"], "note": r["note"], "wd": r["wd"], "every": r.get("every", 7), "anchor": r.get("anchor")})
    out = [{"id": c["id"], "name": c["name"], "price": c["price"], "was": c["was"], "deposit": c["deposit"],
            "shot": variant_src("/" + c["img"], 800), "blurb": BOOK_BLURBS[c["id"]], "formats": fmts[c["id"]]} for c in COURSES]
    out.append({"id": "assessment", "name": "NCCER Assessment", "price": ASSESSMENT["price"], "was": None, "deposit": ASSESSMENT["price"],
                "shot": variant_src("/" + ASSESSMENT["img"], 800), "blurb": BOOK_BLURBS["assessment"], "formats": fmts["assessment"]})
    return out

def build_book():
    url = "/book/"
    crumbs = [("Book a Class", url)]
    body = r"""<section class="bk-head">
  <div class="wrap">
    __CRUMBS__
    <p class="eyebrow">Book Online</p>
    <h1>Pick Your Class.<em>Hold Your Seat.</em></h1>
    <p class="lede">Choose a certification, a schedule and a start date. $200 holds a seat in any course; assessments are $150, paid in full. About two minutes.</p>
    <ul class="bk-marks">
      <li>__CHECK__ 8 seats per class</li>
      <li>__CHECK__ Book up to the day before</li>
      <li>__CHECK__ Card, Klarna, Afterpay, Zelle or in-house financing</li>
    </ul>
  </div>
</section>
<section class="bk-main">
  <div class="wrap">
    <p class="bk-flash" id="bkCanceled" hidden>No payment was taken, so your seat isn't held yet. Your request did reach the office, so nothing is lost: call <a href="tel:__TEL__">__PHONE__</a> to finish it by phone, or pick your class below to run the payment again.</p>
    <div class="bk-grid" id="bkGrid">
      <div class="bk-steps">
        <section class="bk-step is-open" data-step="1">
          <button class="bk-step-h" type="button" disabled><span class="idx">01</span><span><b>Certification</b><span class="bk-pick"></span></span><span class="bk-change">Change</span></button>
          <div class="bk-step-b">
            <p class="bk-q">Which credential are you after?</p>
            <div class="bp-grid" id="bpGrid"></div>
          </div>
        </section>
        <section class="bk-step is-locked" data-step="2">
          <button class="bk-step-h" type="button" disabled><span class="idx">02</span><span><b>Schedule</b><span class="bk-pick"></span></span><span class="bk-change">Change</span></button>
          <div class="bk-step-b">
            <p class="bk-q">How do you want to take it?</p>
            <div class="fmt-list" id="fmtList"></div>
          </div>
        </section>
        <section class="bk-step is-locked" data-step="3">
          <button class="bk-step-h" type="button" disabled><span class="idx">03</span><span><b>Start Date</b><span class="bk-pick"></span></span><span class="bk-change">Change</span></button>
          <div class="bk-step-b">
            <p class="bk-q"><span id="dateQt">Pick a start date</span> <span id="dateSub"></span></p>
            <div class="bd-grid" id="bdGrid"></div>
            <p class="bk-note">Every class is capped at 8 seats, and booking closes the day before it starts. Need a date you don't see? <a href="tel:__TEL__">Call the office</a>.</p>
          </div>
        </section>
        <section class="bk-step is-locked" data-step="4">
          <button class="bk-step-h" type="button" disabled><span class="idx">04</span><span><b>Your Details</b><span class="bk-pick"></span></span><span class="bk-change">Change</span></button>
          <div class="bk-step-b">
            <p class="bk-q">Who is the seat for?</p>
            <div class="two-up">
              <label class="field"><span>First name</span><input type="text" id="fFirst" placeholder="Miguel" autocomplete="given-name"></label>
              <label class="field"><span>Last name</span><input type="text" id="fLast" placeholder="Reyes" autocomplete="family-name"></label>
            </div>
            <label class="field"><span>Mobile number</span><input type="tel" id="fPhone" placeholder="(361) 555-0134" autocomplete="tel"></label>
            <label class="field"><span>Email</span><input type="email" id="fEmail" placeholder="you@email.com" autocomplete="email"></label>
            <label class="field" id="craftField" hidden><span>Which craft are you testing in?</span><select id="fCraft"></select></label>
            <label class="field"><span>Who's paying?</span>
              <select id="fPayer">
                <option>I'm paying for myself</option>
                <option>My employer is paying</option>
                <option>I want to use financing</option>
              </select>
            </label>
            <label class="field"><span>Do you already have an NCCER account?</span>
              <select id="fNccerHas">
                <option>No, this would be my first</option>
                <option>Yes, I have one</option>
              </select>
            </label>
            <label class="field" id="nccerField" hidden><span>Your NCCER card or account number</span><input type="text" id="fNccer" placeholder="Card or account number" autocomplete="off"></label>
            <label class="field"><span>Anything we should know? (optional)</span><textarea id="fNotes" rows="2" placeholder="Night shift, need the evening class…"></textarea></label>
            <div class="consent" id="smsConsent">
              <label class="chk"><input type="checkbox" id="cNon"><span><b>Text me about my enrollment.</b> I agree to receive enrollment confirmations, class reminders and schedule updates by SMS from Prime Lift Rigging Academy at the mobile number above. Msg frequency varies. Msg &amp; data rates may apply. Reply HELP for help, STOP to opt out.</span></label>
              <label class="chk"><input type="checkbox" id="cMkt"><span><b>Text me about future classes.</b> I agree to receive occasional class openings, recertification reminders and review requests by SMS from Prime Lift Rigging Academy. Msg frequency varies. Msg &amp; data rates may apply. Reply HELP for help, STOP to opt out.</span></label>
              <p class="consent-note">Consent is not a condition of enrollment. We never share or sell your mobile number or opt-in information with third parties. <a href="/privacy.html">Privacy Policy</a> &middot; <a href="/terms.html">Terms &amp; Enrollment Policy</a></p>
            </div>
            <p class="bk-err" id="bkErr" hidden></p>
            <button class="btn btn-primary btn-block" id="toPay" type="button">Continue to Payment __ARROW__</button>
          </div>
        </section>
        <section class="bk-step is-locked" data-step="5">
          <button class="bk-step-h" type="button" disabled><span class="idx">05</span><span><b>Hold Your Seat</b><span class="bk-pick"></span></span><span class="bk-change">Change</span></button>
          <div class="bk-step-b">
            <p class="bk-q">Your order</p>
            <dl class="summary" id="bkSummary"></dl>
            <p class="pay-legal" id="coLegal"></p>
            <p class="bk-q">How do you want to pay?</p>
            <div class="paytabs" role="tablist">
              <button class="paytab on" data-pay="card" role="tab" type="button">Card</button>
              <button class="paytab" data-pay="klarna" role="tab" type="button">Klarna</button>
              <button class="paytab" data-pay="afterpay" role="tab" type="button">Afterpay</button>
              <button class="paytab" data-pay="inhouse" role="tab" type="button">In-House</button>
            </div>
            <div class="payform on" data-form="card"><div class="alt-pay"><b id="cardH">Pay the deposit by card</b><p>You'll enter your card on Stripe's secure checkout page. Your seat is held the moment the payment goes through, and a receipt is emailed to you.</p><ul><li>Visa, Mastercard, Amex, Discover</li><li>Apple Pay and Google Pay on your phone</li><li id="cardBal">Balance can be paid online any time before class</li></ul></div></div>
            <div class="payform" data-form="klarna"><div class="alt-pay"><b>Pay with Klarna</b><p>Klarna covers your course in full and then splits it into scheduled payments for you, so this option charges the <strong style="color:#fff">full course price</strong>, not the $200 deposit.</p><ul><li>Choose your payment plan on Klarna</li><li>Instant decision</li><li>Your seat is confirmed the moment Klarna approves</li></ul></div></div>
            <div class="payform" data-form="afterpay"><div class="alt-pay"><b>Pay with Afterpay</b><p>Same as Klarna: Afterpay pays the course in full and breaks it into installments for you, so this option charges the <strong style="color:#fff">full course price</strong> rather than the deposit.</p><ul><li>Instant decision</li><li>Installments handled by Afterpay</li><li>Seat confirmed on approval</li></ul></div></div>
            <div class="payform" data-form="inhouse"><div class="alt-pay"><b>In-House Financing, No Credit Check</b><p>Didn't qualify for Klarna or Afterpay? We'll set you up directly. Start with as little as $200 down and make payments leading up to your class date.</p><ul><li>No credit check</li><li>Payments scheduled before your start date</li><li>Course begins once the balance is paid in full</li></ul><p style="margin-top:13px">Prefer Zelle? Choose this and note it below; the office will send details and register you manually.</p></div>
              <label class="field" style="margin-top:12px"><span>Anything we should know (optional)</span><input type="text" id="fNote" placeholder="Paying by Zelle, employer is covering it, etc." autocomplete="off"></label></div>
            <button class="btn btn-primary btn-block" id="payBtn" type="button" style="margin-top:19px">Pay $200 Deposit</button>
            <p class="pay-legal">By continuing you agree to Prime Lift Rigging Academy's <a href="/terms.html" style="color:var(--accent)">enrollment terms</a>. Deposits hold your seat and are applied to your course total.</p>
          </div>
        </section>
      </div>
      <aside class="bk-side" id="bkSide" aria-live="polite">
        <div class="bk-side-shot"><img id="sideImg" data-nors src="__SIDEIMG__" alt="" width="640" height="360"><b id="sideName">Your Seat</b></div>
        <dl class="summary" id="sideSummary"></dl>
        <p class="bk-side-call">Rather book by phone? <a href="tel:__TEL__">__PHONE__</a><br>Mon – Fri · 7 AM – 5 PM</p>
      </aside>
    </div>
    <div class="bk-done" id="bkDone" hidden>
      <div class="co-success">
        <div class="co-success-ico">__CHECK__</div>
        <h2 id="doneH">You're On The List</h2>
        <p id="doneMsg"></p>
        <div class="co-success-box">
          <b>Questions before class?</b>
          <p>Call the office at <a href="tel:__TEL__" style="color:var(--accent);font-weight:700">__PHONE__</a> or email <a href="mailto:__EMAIL__" style="color:var(--accent);font-weight:700">__EMAIL__</a>.</p>
        </div>
        <a class="btn btn-ghost" href="/" style="margin-top:26px">Back To The Site</a>
      </div>
    </div>
  </div>
</section>
<!-- Enrollment requests that don't go through Stripe (in-house financing, Zelle,
     or a card booking made before payments are switched on). Static markup on
     purpose: Netlify only registers fields it can see in the deployed HTML. -->
<form name="enrollment-request" method="POST" data-netlify="true" netlify-honeypot="bot-field" action="/thanks.html" hidden aria-hidden="true">
  <input type="hidden" name="form-name" value="enrollment-request">
  <input name="bot-field">
  <input name="first_name"><input name="last_name"><input name="phone"><input name="email">
  <input name="program"><input name="format"><input name="start_date"><input name="start_iso"><input name="start_mdy"><input name="class_times">
  <input name="payment_method"><input name="amount_due_today"><input name="note"><input name="page">
  <input name="payer"><input name="notes"><input name="sms_consent_nonmarketing"><input name="sms_consent_marketing">
  <input name="nccer_has"><input name="nccer_number">
</form>
<script>
/* Booking flow. Dates come from SCHEDULE_RULES + CLOSED/FULL in build.py (injected below),
   the same rule the class-dates page and course strips use. Change the rule there, never a list. */
(function(){
  const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const SEATS=8, LEAD=__LEAD__, X=__SCHED__, PROGS=__PROGS__, CRAFTS=__CRAFTS__, PHONE="__PHONE__";
  const MONS=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const DOWS=["Sun","Mon","Tue","Wed","Thu","Fri","Sat"], DOWFULL=["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
  const pad2=n=>String(n).padStart(2,"0");
  const iso=d=>d.getFullYear()+"-"+pad2(d.getMonth()+1)+"-"+pad2(d.getDate());
  const dparts=s=>{ const p=s.split("-").map(Number); return new Date(p[0],p[1]-1,p[2]); };
  const fmtLong=s=>{ const d=dparts(s); return DOWFULL[d.getDay()]+", "+MONS[d.getMonth()]+" "+d.getDate(); };
  const money=n=>"$"+n.toLocaleString("en-US");
  /* full = the office's static FULL list OR the live count from the Enrollment pipeline (site.js -> window.__plSeats) */
  const seatsLeft=(s,k)=>{ const L=window.__plSeats; return L&&L.taken?(L.cap||SEATS)-(L.taken[k+":"+s]||0):SEATS; };
  const isFull=(s,k)=>{ const f=X.full[s]||[]; return f.includes(k)||f.includes("*")||seatsLeft(s,k)<=0; };
  function first(){ const d=new Date(); d.setHours(0,0,0,0); d.setDate(d.getDate()+LEAD); return d; }
  /* a cadence wider than weekly is phased off the rule anchor date, not off today. */
  function phase(d,step,anchor){ if(!anchor||step===7) return; const a=dparts(anchor); const off=((Math.round((d-a)/864e5)%step)+step)%step; if(off) d.setDate(d.getDate()+(step-off)); }
  function every(wd,n,step,anchor){ step=step||7; const d=first(),o=[]; while(d.getDay()!==wd) d.setDate(d.getDate()+1); phase(d,step,anchor); while(o.length<n){ if(!X.closed[iso(d)]) o.push(iso(d)); d.setDate(d.getDate()+step); } return o; }
  function weekdays(n){ const d=first(),o=[]; while(o.length<n){ if(d.getDay()>=1&&d.getDay()<=5&&!X.closed[iso(d)]) o.push(iso(d)); d.setDate(d.getDate()+1); } return o; }
  PROGS.forEach(p=>p.formats.forEach(f=>{ f.dates=f.wd==="weekday"?weekdays(15):every(f.wd,8,f.every,f.anchor); }));

  const S={prog:null,fmt:null,date:null,method:"card",step:1};
  const ARROW='<svg class="go" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>';
  const step=n=>$('.bk-step[data-step="'+n+'"]');
  const key=()=>S.prog.id+":"+S.fmt.id;
  const depositFor=(p,m)=>(m==="klarna"||m==="afterpay")?p.price:Math.min(p.deposit,p.price);
  const setPick=(n,t)=>{ $(".bk-pick",step(n)).textContent=t||""; };
  const val=id=>(($("#"+id)||{}).value||"").trim();

  /* one step open, the finished ones collapsed to their pick, the rest waiting */
  function show(n,scroll){
    S.step=n;
    for(let i=1;i<=5;i++){
      const s=step(i);
      s.classList.toggle("is-open",i===n);
      s.classList.toggle("is-done",i<n);
      s.classList.toggle("is-locked",i>n);
      $(".bk-step-h",s).disabled=i>=n;
    }
    if(n===5) renderPay();
    renderSide();
    if(scroll) requestAnimationFrame(()=>{ const y=step(n).getBoundingClientRect().top+window.scrollY-84; window.scrollTo({top:y,behavior:"smooth"}); });
  }
  $$(".bk-step-h").forEach(h=>h.addEventListener("click",()=>{ const n=+h.parentElement.dataset.step; if(n<S.step) show(n,true); }));

  /* 01 certification */
  $("#bpGrid").innerHTML=PROGS.map(p=>'<button class="bp" type="button" data-prog="'+p.id+'">'
    +'<span class="bp-shot"><img src="'+p.shot+'" alt="" loading="lazy" width="640" height="360"></span>'
    +'<span class="bp-body"><b>'+p.name+'</b><span class="bp-blurb">'+p.blurb+'</span>'
    +'<span class="bp-price">'+money(p.price)+(p.was?' <s class="was">'+money(p.was)+'</s>':'')+'<small>'+(p.id==="assessment"?"per craft":"per course")+'</small></span></span></button>').join("");
  $("#bpGrid").addEventListener("click",e=>{ const b=e.target.closest("[data-prog]"); if(b) pickProgram(b.dataset.prog,true); });
  function pickProgram(id,scroll){
    const same=S.prog&&S.prog.id===id;
    if(!same){ S.prog=PROGS.find(p=>p.id===id); S.fmt=null; S.date=null; }
    $$("#bpGrid .bp").forEach(b=>b.classList.toggle("sel",b.dataset.prog===id));
    setPick(1,S.prog.name+" · "+money(S.prog.price));
    /* Hiding the craft field is not enough: the <select> keeps its value, so a
       student who starts on an assessment and switches to a course sends
       "Craft: Plumber" to the office on an Advanced Rigger booking. Clear it. */
    const isAssess=S.prog.id==="assessment";
    $("#craftField").hidden=!isAssess;
    if(!isAssess) $("#fCraft").value="";
    /* NCCER number is only useful if they already have an account, so it stays hidden until they say so. */
    $("#fNccerHas").onchange=e=>{ const yes=/^Yes/.test(e.target.value); $("#nccerField").hidden=!yes; if(!yes) $("#fNccer").value=""; };
    if(!same){
      $("#fmtList").innerHTML=S.prog.formats.map((f,i)=>'<button class="fmt" type="button" data-fmt="'+f.id+'"><span class="idx">'+pad2(i+1)+'</span><span><b>'+f.name+'</b><span>'+f.time+' &nbsp;<em>· '+f.note+'</em></span></span>'+ARROW+'</button>').join("");
    }
    if(same&&S.fmt){ show(S.date?4:3,scroll); return; }
    /* Always stop on the schedule step, even when the program has a single format
       (assessments, Signal Person). Auto-picking it used to drop students on the
       date step with a schedule they never chose. Now they tap it and see the times. */
    const assess=S.prog.id==="assessment";
    $(".bk-step-h b",step(3)).textContent=assess?"Test Date":"Start Date";
    $("#dateQt").textContent=assess?"Pick a test date":"Pick a start date";
    show(2,scroll);
  }

  /* 02 schedule */
  $("#fmtList").addEventListener("click",e=>{ const b=e.target.closest("[data-fmt]"); if(b) pickFormat(b.dataset.fmt,true); });
  function pickFormat(id,scroll){
    const same=S.fmt&&S.fmt.id===id;
    if(!same){ S.fmt=S.prog.formats.find(f=>f.id===id); S.date=null; }
    $$("#fmtList .fmt").forEach(b=>b.classList.toggle("sel",b.dataset.fmt===id));
    setPick(2,S.fmt.name+" · "+S.fmt.time);
    $("#dateSub").textContent=S.fmt.time;
    if(!same) renderDates();
    if(same&&S.date){ show(4,scroll); return; }
    show(3,scroll);
  }
  function renderDates(){
    /* a booked-up date is simply not offered: no seats-left counts, no Full tiles */
    const k=key(), open=S.fmt.dates.filter(s=>!isFull(s,k));
    $("#bdGrid").innerHTML=open.length?open.map(s=>{ const d=dparts(s);
      return '<button class="bd'+(S.date===s?' sel':'')+'" type="button" data-date="'+s+'"><em>'+DOWS[d.getDay()]+'</em><b>'+d.getDate()+'</b><span>'+MONS[d.getMonth()]+'</span></button>'; }).join("")
      :'<p class="bk-note">Upcoming dates for this schedule are booked up. Call the office at '+PHONE+' and we will find you a seat.</p>';
  }
  /* live counts arrive after first paint: redraw the tiles, and drop a pick that just filled up */
  document.addEventListener("pl:seats",()=>{
    if(!S.fmt) return;
    if(S.date&&isFull(S.date,key())){ S.date=null; setPick(3,""); if(S.step>3) show(3,true); }
    renderDates();
  });

  /* 03 start date */
  $("#bdGrid").addEventListener("click",e=>{ const b=e.target.closest("[data-date]"); if(!b||b.disabled) return; pickDate(b.dataset.date,true); });
  function pickDate(s,scroll){
    S.date=s;
    $$("#bdGrid .bd").forEach(b=>b.classList.toggle("sel",b.dataset.date===s));
    setPick(3,fmtLong(s));
    setTimeout(()=>show(4,scroll),scroll?140:0);
  }

  /* 04 details */
  $("#fCraft").innerHTML='<option value="">Choose a craft</option>'+CRAFTS.map(c=>'<option>'+c+'</option>').join("")+'<option>Not sure / another craft</option>';
  $("#toPay").addEventListener("click",()=>{
    const err=$("#bkErr"), first=val("fFirst"), phone=val("fPhone"), email=val("fEmail");
    let msg="";
    if(!first) msg="Add your first name so the office knows who the seat is for.";
    else if(!phone&&!email) msg="Add a mobile number or an email so we can confirm your seat.";
    else if(S.prog.id==="assessment"&&!val("fCraft")) msg="Pick the craft you're testing in.";
    err.textContent=msg; err.hidden=!msg;
    if(msg){ err.scrollIntoView({block:"center",behavior:"smooth"}); return; }
    setPick(4,(first+" "+val("fLast")).trim()+" · "+(phone||email));
    show(5,true);
  });

  /* 05 hold your seat */
  function summaryRows(m){
    const p=S.prog, f=S.fmt, dep=depositFor(p,m), bal=p.price-dep;
    let h=[["Certification",p.name],["Schedule",f.name],["Class times",f.time],["Start date",fmtLong(S.date)]].map(r=>'<div class="summary-row"><dt>'+r[0]+'</dt><dd>'+r[1]+'</dd></div>').join("");
    h+='<div class="summary-row total"><dt>'+(p.id==="assessment"?"Assessment fee":"Course total")+'</dt><dd>'+money(p.price)+'</dd></div>';
    h+='<div class="summary-row due"><dt>Due today</dt><dd>'+money(dep)+'</dd></div>';
    if(bal>0) h+='<div class="summary-row"><dt>Balance before class</dt><dd>'+money(bal)+'</dd></div>';
    return h;
  }
  function payLabel(m){
    if(m==="inhouse") return "Request My Payment Plan";
    const dep=depositFor(S.prog,m);
    if(m==="klarna") return "Continue to Klarna · "+money(dep);
    if(m==="afterpay") return "Continue to Afterpay · "+money(dep);
    return dep===S.prog.price?"Pay "+money(dep):"Pay "+money(dep)+" Deposit";
  }
  function renderPay(){
    const p=S.prog, assess=p.id==="assessment";
    /* a $150 assessment has no balance to finance: no in-house tab, and the card copy drops the deposit language */
    const inh=$('.paytab[data-pay="inhouse"]'); inh.style.display=assess?"none":""; if(assess&&S.method==="inhouse") S.method="card";
    const bnpl=(S.method==="klarna"||S.method==="afterpay"), bal=p.price-depositFor(p,S.method);
    $("#bkSummary").innerHTML=summaryRows(S.method);
    $("#payBtn").textContent=payLabel(S.method);
    $("#cardH").textContent=bal>0?"Pay the deposit by card":"Pay by card";
    $("#cardBal").style.display=bal>0?"":"none";
    $("#coLegal").textContent=bnpl
      ?"Klarna and Afterpay pay your course in full, then split it into installments for you. Your seat is confirmed as soon as they approve."
      :bal>0?"Balance must be paid in full before your class begins. Seats are released if the deposit isn't received."
      :assess?"The assessment fee is paid in full today. Your test date is held the moment the payment goes through."
      :"Paid in full today. Your seat is held the moment the payment goes through.";
    $$(".paytab").forEach(t=>t.classList.toggle("on",t.dataset.pay===S.method));
    $$(".payform").forEach(f=>f.classList.toggle("on",f.dataset.form===S.method));
  }
  $$(".paytab").forEach(t=>t.addEventListener("click",()=>{ S.method=t.dataset.pay; renderPay(); renderSide(); }));

  /* desktop side card: the running order */
  function renderSide(){
    if(!$("#bkSide")) return;
    const p=S.prog, dash="—";
    $("#sideName").textContent=p?p.name:"Your Seat";
    const img=$("#sideImg"), src=p?p.shot:"/img/bg-classroom.jpg"; if(img.getAttribute("src")!==src) img.src=src;
    let h=[["Schedule",S.fmt?S.fmt.name:dash],["Class times",S.fmt?S.fmt.time:dash],["Start date",S.date?fmtLong(S.date):dash]].map(r=>'<div class="summary-row"><dt>'+r[0]+'</dt><dd>'+r[1]+'</dd></div>').join("");
    if(p){ const dep=depositFor(p,S.method), bal=p.price-dep;
      h+='<div class="summary-row total"><dt>'+(p.id==="assessment"?"Assessment fee":"Course total")+'</dt><dd>'+money(p.price)+'</dd></div><div class="summary-row due"><dt>Due today</dt><dd>'+money(dep)+'</dd></div>'+(bal>0?'<div class="summary-row"><dt>Balance before class</dt><dd>'+money(bal)+'</dd></div>':''); }
    else h+='<div class="summary-row due"><dt>Holds a seat</dt><dd>$200</dd></div>';
    $("#sideSummary").innerHTML=h;
  }

  /* submit: card / Klarna / Afterpay -> Stripe Checkout via Netlify Function; in-house -> Netlify Form.
     No STRIPE_SECRET_KEY on the site = 503, and the booking falls back to the form so nobody is dropped. */
  function payload(){
    /* craft only belongs on an assessment, whatever is left in the hidden select */
    const m=S.method, craft=S.prog.id==="assessment"?val("fCraft"):"", notes=val("fNotes");
    return { first_name:val("fFirst"), last_name:val("fLast"), phone:val("fPhone"), email:val("fEmail"),
      program:S.prog.name, program_id:S.prog.id, format:S.fmt.name, format_id:S.fmt.id, class_times:S.fmt.time,
      start_date:S.date, start_date_label:fmtLong(S.date), payment_method:m, amount_due_today:depositFor(S.prog,m), course_total:S.prog.price,
      note:val("fNote"), payer:val("fPayer"), notes:(craft?"Craft: "+craft+(notes?". ":""):"")+notes,
      nccer_has:/^Yes/.test(val("fNccerHas"))?"yes":"no", nccer_number:/^Yes/.test(val("fNccerHas"))?val("fNccer"):"",
      sms_consent_nonmarketing:$("#cNon").checked?"yes":"no", sms_consent_marketing:$("#cMkt").checked?"yes":"no", page:location.href };
  }
  async function submitForm(p){
    const body=new URLSearchParams({"form-name":"enrollment-request"});
    /* start_date goes out human-readable: it lands verbatim in the office email, the opportunity name and the student's
       confirmation. start_iso (YYYY-MM-DD) rides along for the opportunity's date field: seat counts and class reminders key on it. */
    const s=p.start_date||"", mdy=s?s.slice(5,7)+"-"+s.slice(8,10)+"-"+s.slice(0,4):"";   /* GHL date fields want MM-DD-YYYY */
    const q=Object.assign({},p,{start_date:s?fmtLong(s)+", "+s.slice(0,4):"", start_iso:s, start_mdy:mdy});
    ["first_name","last_name","phone","email","program","format","start_date","start_iso","start_mdy","class_times","payment_method","amount_due_today","note","page","payer","notes","sms_consent_nonmarketing","sms_consent_marketing","nccer_has","nccer_number"].forEach(k=>body.append(k,String(q[k]==null?"":q[k])));
    const r=await fetch("/",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:body.toString()});
    if(!r.ok) throw new Error("form "+r.status);
  }
  function showDone(msg){
    $("#doneMsg").textContent=msg;
    $("#bkGrid").hidden=true; $("#bkCanceled").hidden=true;
    const d=$("#bkDone"); d.hidden=false;
    requestAnimationFrame(()=>window.scrollTo({top:d.getBoundingClientRect().top+window.scrollY-110,behavior:"smooth"}));
  }
  function confirmLine(p){
    const to=[]; if(p.email) to.push("your email"); if(p.phone&&p.sms_consent_nonmarketing==="yes") to.push("your phone");
    return to.length?" A confirmation is on its way to "+to.join(" and ")+".":"";
  }
  $("#payBtn").addEventListener("click",async()=>{
    const btn=$("#payBtn"), label=btn.textContent, p=payload(), who=p.first_name?p.first_name+", you're":"You're";
    const dep=money(p.amount_due_today)+(p.amount_due_today<p.course_total?" deposit":" fee");
    btn.innerHTML='<span class="spin"></span> Processing…'; btn.disabled=true;
    const reset=()=>{ btn.disabled=false; btn.textContent=label; };
    try{
      if(p.payment_method==="inhouse"){
        await submitForm(p); reset();
        showDone(who+" on the list for "+p.program+" starting "+p.start_date_label+"."+confirmLine(p)+" The office will call you to set up your payment schedule and hold your seat.");
        return;
      }
      const r=await fetch("/.netlify/functions/create-checkout",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(p)});
      if(r.status===503){
        p.payment_method=p.payment_method+" (online payments pending, take by phone)";
        await submitForm(p); reset();
        showDone(who+" on the list for "+p.program+" starting "+p.start_date_label+"."+confirmLine(p)+" The office will call you to take the "+dep+" and confirm your seat.");
        return;
      }
      const data=await r.json().catch(()=>({}));
      if(!r.ok||!data.url) throw new Error(data.error||"checkout "+r.status);
      /* Record the booking BEFORE handing off to Stripe, so the office email, the pipeline card and the
         seat count exist even if the student never finishes paying. Stripe's webhook moves the card to
         Deposit Paid and sends the confirmation once the money actually lands. */
      try{ await submitForm(Object.assign({},p,{payment_method:p.payment_method+" (Stripe checkout opened; confirm payment in Stripe)"})); }catch(e){ console.warn(e); }
      location.href=data.url;
    }catch(err){
      console.error(err); reset();
      alert("Something went wrong on our end. Call the office at "+PHONE+" and we'll hold your seat by phone.");
    }
  });

  /* arrivals: /book/?book=advanced&fmt=night&date=2026-09-14 from course pages, the class-dates page
     and the home band; ?booked=1 back from Stripe; ?canceled=1 if they bailed out of Stripe */
  (function(){
    const q=new URLSearchParams(location.search);
    if(q.get("booked")==="1"){
      $("#doneH").textContent="Seat Reserved";
      showDone("Your deposit went through and your seat in "+(q.get("program")||"your course")+(q.get("date")?" starting "+q.get("date"):"")+" is reserved. A receipt is in your email, and the office will reach out with your study material.");
      history.replaceState(null,"",location.pathname); return;
    }
    if(q.get("canceled")==="1") $("#bkCanceled").hidden=false;
    const id=q.get("book");
    if(id&&PROGS.some(p=>p.id===id)){
      pickProgram(id,false);
      const f=q.get("fmt"); if(f&&S.prog.formats.some(x=>x.id===f)) pickFormat(f,false);
      const d=q.get("date"); if(S.fmt&&d&&S.fmt.dates.includes(d)&&!isFull(d,key())) pickDate(d,false);
      /* craft pages pass their craft (?craft=Plumber): prefill the step-4 select, still changeable */
      const c=q.get("craft"); if(c&&S.prog.id==="assessment"&&CRAFTS.includes(c)) $("#fCraft").value=c;
    }
    if(location.search) history.replaceState(null,"",location.pathname);
    renderSide();
  })();
})();
</script>"""
    body = (body.replace("__CRUMBS__", crumbs_html(crumbs)).replace("__CHECK__", I["check"]).replace("__ARROW__", I["arrow"])
                .replace("__TEL__", BIZ["phone_raw"]).replace("__PHONE__", esc(BIZ["phone"])).replace("__EMAIL__", BIZ["email"])
                .replace("__PROGS__", json.dumps(book_programs(), separators=(",", ":")))
                .replace("__SIDEIMG__", variant_src("/img/bg-classroom.jpg", 800))
                .replace("__SCHED__", sched_json()).replace("__LEAD__", str(LEAD_DAYS))
                .replace("__CRAFTS__", json.dumps([craft_short(n) for s, n, g, b, cov in CRAFTS], separators=(",", ":"))))
    emit(url, page(url, "Book a Class · Advanced Rigger, Signal Person & NCCER Assessments in Portland, TX",
                   "Book your NCCER Advanced Rigger or Signal Person class, or an NCCER assessment, in Portland, TX. Pick a schedule and a start date online; $200 holds your seat.",
                   body, crumbs), "0.9")

def build_404():
    body = """<section class="section" style="min-height:70svh;display:flex;align-items:center"><div class="wrap" style="text-align:center">
  <p class="eyebrow is-center">404</p>
  <h1 class="h-sec">That Page<br>Isn't Rigged Up.</h1>
  <p class="lede" style="margin:22px auto 0;max-width:52ch">The link is broken or the page moved. Everything you need is one tap away.</p>
  <div class="hero-cta" style="justify-content:center">
    <a class="btn btn-primary" href="/">Back To Home</a>
    <a class="btn btn-ghost" href="/class-dates/">See Class Dates</a>
  </div>
</div></section>"""
    w("404.html", page("/404.html", "Page Not Found", "That page isn't here. Head back to Prime Lift Rigging Academy.", body))

# ---------------------------------------------------------- index rewrite
def rewrite_index():
    p = os.path.join(ROOT, "index.html")
    s = io.open(p, encoding="utf-8").read()
    def between(s, a, b, new):
        i, j = s.index(a), s.index(b)
        return s[:i] + new + s[j:]
    s = between(s, "<!-- ================= NAV ================= -->", "<!-- ================= HERO ================= -->", nav(home=True) + "\n")
    s = between(s, "<!-- ================= FOOTER ================= -->", "<!-- ================= STICKY CALL BAR ================= -->", footer(home=True) + "\n")
    # "How We Teach It" is generated so the home page and the course page cannot drift
    s = between(s, "<!-- TEACH:START", "<!-- TEACH:END -->",
                "<!-- TEACH:START \u2014 generated by build.py, do not edit by hand -->\n"
                + teach_section(home=True) + "\n")
    # booking form: closed / full dates from CLOSED + FULL above
    s = between(s, "/* SCHED:START */", "/* SCHED:END */", "/* SCHED:START */ const SCHED=%s; " % sched_json())
    # head: robots + canonical + og origin + schema
    s = re.sub(r'<meta name="robots"[^>]*>', '<meta name="robots" content="noindex, nofollow">' if NOINDEX else '<meta name="robots" content="index, follow, max-image-preview:large">', s)
    s = re.sub(r'https://(?:jzonkel1\.github\.io/prime-lift-rigging-academy|prime-lift-rigging-academy\.netlify\.app|primeliftrigging-academy\.com|primeliftriggingtx\.com)/', ORIGIN + "/", s)
    s = re.sub(r'<link rel="canonical"[^>]*>\n?', "", s)
    s = re.sub(r'<link rel="alternate" hreflang=[^>]*>\n?', "", s)
    s = s.replace('<link rel="icon" href="/favicon.ico" sizes="32x32">', '<link rel="canonical" href="%s/">\n%s<link rel="icon" href="/favicon.ico" sizes="32x32">' % (ORIGIN, hreflang_links("/")), 1)
    graph = [dict(org_schema(), **{"@id": BASE + "/#org"}),
             {"@type": "WebSite", "@id": BASE + "/#website", "url": BASE + "/", "name": BIZ["name"], "publisher": {"@id": BASE + "/#org"}},
             faq_schema(FAQ[:8]),
             {"@type": "ItemList", "name": "Courses", "itemListElement": [
                 {"@type": "ListItem", "position": 1, "url": BASE + "/advanced-rigger/", "name": "Advanced Rigger Certification"},
                 {"@type": "ListItem", "position": 2, "url": BASE + "/signal-person/", "name": "Signal Person Certification"},
                 {"@type": "ListItem", "position": 3, "url": BASE + "/nccer-assessments/", "name": "NCCER Craft Assessments"}]}]
    block = "<!-- SCHEMA:START -->\n%s\n<!-- SCHEMA:END -->" % ld(graph)
    if "<!-- SCHEMA:START -->" in s:
        s = between(s, "<!-- SCHEMA:START -->", "<!-- SCHEMA:END -->", block[:-len("<!-- SCHEMA:END -->")])
    else:
        s = s.replace("</head>", block + "\n</head>", 1)
    # css bundle version + WebP srcsets (idempotent: rewritten tags carry data-o)
    s = re.sub(r'/css/bundle\.css(\?v=[^"]*)?', "/css/bundle.css?v=" + CSS_VER, s)
    s = responsive_images(s)
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    PAGES.insert(0, ("/", "1.0"))

# ---------------------------------------------------------------- assets
PAGES_CSS = r"""
/* ============================================================
   PAGES — components for the generated inner pages (build.py)
   and the mobile menu, which the home page shares.
   ============================================================ */

/* ---- mobile nav ---- */
.nav-burger{display:none; width:44px; height:44px; flex-direction:column; justify-content:center; gap:5px; align-items:center; border-radius:var(--r)}
.nav-burger span{display:block; width:22px; height:2px; background:#fff; transition:transform .25s ease, opacity .2s}
@media(max-width:999px){.nav-burger{display:flex}}
body.mnav-open .nav-burger span:nth-child(1){transform:translateY(7px) rotate(45deg)}
body.mnav-open .nav-burger span:nth-child(2){opacity:0}
body.mnav-open .nav-burger span:nth-child(3){transform:translateY(-7px) rotate(-45deg)}
/* .mnav lives INSIDE header.nav, so these three only stack against each other:
   the sheet (1), the opaque lid that hides rows scrolling past the top (2), and
   the logo + close button row (3), which has to stay on top or the menu can't
   be dismissed. */
.nav-in{position:relative; z-index:3}
/* The open menu is a solid ink sheet that drops out from under a solid header bar.
   It used to be a blurred translucent overlay fading in while the header cross-faded
   to ink on its own timer: two surfaces, two timings, one seam at the logo, and a
   full-screen backdrop-filter animating on a phone GPU (the stutter). Now: the
   header snaps solid with a hairline the instant the menu opens, the sheet starts
   exactly below the bar (whichever height the bar is in) and slides down 12px. */
.mnav{
  position:fixed; inset:0; z-index:1; display:none; overflow:auto;
  /* plain ink sheet; the hairline at the bar's edge belongs to the lid below,
     which is opaque and does not scroll with the menu */
  background:var(--ink);
  padding-top:calc(110px - 22px * var(--navp) + 6px); -webkit-overflow-scrolling:touch;
}
@keyframes mnavIn{from{opacity:0; transform:translateY(-12px)}to{opacity:1; transform:none}}
body.mnav-open .mnav{display:block; animation:mnavIn .28s cubic-bezier(.2,.7,.2,1) both}
@media(prefers-reduced-motion:reduce){body.mnav-open .mnav{animation:none}}
body.mnav-open{overflow:hidden}
body.mnav-open .nav{z-index:80}   /* the sheet (z-index:1) already covers the glass (z-index:0) */
/* The bar is an opaque lid while the menu is open. Without it the sheet's
   padding-top only sets the RESTING position of the first row: scroll the menu
   and every row travels up through the bar, colliding with the logo and the
   close button (rows appeared to float over the logo). The lid is painted
   between the sheet and the logo row, so rows now disappear cleanly under it.
   Height comes from .nav itself, so it tracks the scroll-driven bar height. */
body.mnav-open .nav::after{
  content:""; position:absolute; inset:0; z-index:2; pointer-events:none;
  background:var(--ink); border-bottom:1px solid var(--edge);
}
.mnav-in{padding:0 var(--pad) 40px; max-width:560px; margin-inline:auto}
/* rows: top-level links, the two accordion triggers (Courses / Academy) and the links inside them */
.mnav-in>a,.macc-t,.macc-p a{display:grid; grid-template-columns:1fr auto; align-items:center; gap:2px 12px; padding:14px 4px; border-bottom:1px solid var(--edge); color:inherit}
.mnav-in>a b,.macc-t b,.macc-p a b{font-family:var(--f-head); font-weight:400; text-transform:uppercase; font-size:21px; letter-spacing:.012em; line-height:1.05; text-align:left}
.mnav-in>a span,.macc-t span,.macc-p a span{grid-column:1; font-size:13px; color:var(--muted-2); line-height:1.4; text-align:left}
.mnav-in>a em,.macc-p a em{grid-column:2; grid-row:1/3; font-style:normal; font-family:var(--f-fig); font-stretch:125%; font-weight:700; font-size:14px; color:var(--accent)}
.macc-t{appearance:none; -webkit-appearance:none; width:100%; background:none; border:0; border-bottom:1px solid var(--edge); border-radius:0; font:inherit; cursor:pointer; -webkit-tap-highlight-color:transparent}
.macc-t svg{grid-column:2; grid-row:1/3; width:18px; height:18px; color:var(--accent); transition:transform .25s ease}
.macc.open .macc-t svg{transform:rotate(180deg)}
.macc-p{display:none; margin:0 0 4px 6px; padding-left:16px; border-left:2px solid rgba(41,182,232,.35)}
.macc.open .macc-p{display:block; animation:fade .2s ease}
.macc-p a{padding:12px 4px}
.macc-p a b{font-size:18px}
.mnav-cta{display:grid; gap:10px; margin-top:28px}
.nm-h{margin:8px 0 2px; padding:12px 13px 6px; border-top:1px solid var(--edge); font-family:var(--f-display); font-weight:700; font-size:10px; letter-spacing:.22em; text-transform:uppercase; color:var(--accent)}
.nm-all+.nm-all{margin-top:0}
.nm-narrow{width:330px}
.nm-narrow .nm-item{grid-template-columns:24px minmax(0,1fr)}
.nm-narrow .nm-p{display:none}
@media(max-width:999px){.nav-cta .btn{display:none} .nav-cta{margin-left:auto}}
/* mobile-only line break: lets a headline stack on purpose instead of wrapping mid-phrase */
.mbr{display:none}
@media(max-width:639px){.mbr{display:inline}}
/* hero flag chips: two columns at phone width, so tighten the caps to keep each on one line */
@media(max-width:480px){.flag{font-size:9.5px; letter-spacing:.1em; gap:8px; padding-inline:10px}}
@media(min-width:1000px){.mnav{display:none!important}}

/* ---- page hero ---- */
.phero{position:relative; min-height:clamp(560px,78svh,820px); display:flex; align-items:flex-end; overflow:hidden; background:var(--ink)}
.phero-bg{position:absolute; inset:0; z-index:0}
.phero-bg img{width:100%; height:100%; object-fit:cover; object-position:50% 40%; transform:scale(1.1); animation:zoomout 30s cubic-bezier(.2,.5,.3,1) forwards}
@media(prefers-reduced-motion:reduce){.phero-bg img{animation:none; transform:none}}
.phero-bg::after{content:""; position:absolute; inset:0; background:linear-gradient(180deg,rgba(10,10,12,.62) 0%,rgba(10,10,12,.5) 38%,rgba(10,10,12,.9) 72%,var(--ink) 100%)}
.phero-in{position:relative; z-index:2; width:100%; padding-block:150px 64px; text-align:center}
@media(min-width:900px){.phero-in{text-align:left; padding-block:180px 84px}}
.phero h1{font-size:clamp(46px,11.5vw,92px); line-height:.92; margin-inline:auto}
/* phone width: the hero eyebrows are long enough that the chevron rules squeeze them onto two lines */
@media(max-width:559px){
  .hero .eyebrow::before,.hero .eyebrow::after,.phero .eyebrow::before,.phero .eyebrow::after,.band .eyebrow::before,.band .eyebrow::after,.person-copy .eyebrow::before,.person-copy .eyebrow::after{display:none}
  .hero .eyebrow,.phero .eyebrow,.band .eyebrow,.person-copy .eyebrow{letter-spacing:.2em}
}
@media(min-width:900px){.phero h1{margin-inline:0; max-width:18ch}}
.phero h1 em{font-style:normal; color:var(--accent); display:block}
.phero-craft h1{font-size:clamp(36px,8.6vw,76px); max-width:none}
@media(min-width:900px){.phero-craft h1{max-width:18ch}}
.phero .lede{margin:22px auto 0; max-width:58ch}
@media(min-width:900px){.phero .lede{margin-inline:0}}
.phero .eyebrow{justify-content:center}
@media(min-width:900px){.phero .eyebrow{justify-content:flex-start}}
.crumbs{display:flex; flex-wrap:wrap; justify-content:center; gap:8px; margin-bottom:22px; font-family:var(--f-display); font-size:11px; letter-spacing:.14em; text-transform:uppercase; color:var(--muted-2); font-weight:700}
@media(min-width:900px){.crumbs{justify-content:flex-start}}
.crumbs a:hover{color:#fff}
.crumbs i{font-style:normal; color:var(--edge-3)}
.crumbs span{color:var(--accent)}

/* ---- spec bar (under a page hero) ---- */
.specbar{background:var(--steel); border-top:1px solid var(--edge); border-bottom:1px solid var(--edge)}
.specbar-in{display:grid; grid-template-columns:repeat(2,minmax(0,1fr))}
@media(min-width:900px){.specbar-in{grid-template-columns:repeat(4,minmax(0,1fr))}}
.spec{padding:20px 14px; border-left:1px solid var(--edge); text-align:center}
.spec:first-child{border-left:0}
@media(max-width:899px){.spec:nth-child(3){border-left:0} .spec:nth-child(-n+2){border-bottom:1px solid var(--edge)}}
/* phone: one fact per row so no value ever breaks mid-phrase */
@media(max-width:559px){
  .specbar-in{grid-template-columns:1fr}
  .spec{display:block; text-align:left; padding:13px 0; border:0; border-bottom:1px solid var(--edge)}
  .spec:last-child{border-bottom:0}
  .spec span{margin:0 0 5px}
  .spec b{font-size:15px}
}
.spec span{display:block; font-family:var(--f-display); font-size:10.5px; letter-spacing:.2em; text-transform:uppercase; color:var(--muted-2); font-weight:700; margin-bottom:8px}
.spec b{display:block; font-family:var(--f-fig); font-stretch:115%; font-weight:600; font-size:15.5px; color:#fff; letter-spacing:.01em; line-height:1.3}
.spec b .was,.cta-price .was,.was{font-family:var(--f-fig); font-weight:500; color:var(--muted-2); text-decoration:line-through; font-size:.78em; margin-left:6px}

/* ---- content layouts ---- */
.section.alt{background:var(--steel); border-top:1px solid var(--edge); border-bottom:1px solid var(--edge)}
.split{display:grid; gap:var(--gut); grid-template-columns:1fr; align-items:start}
@media(min-width:960px){.split{grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr)}}
.split .sec-head{margin-bottom:26px}
.prose .lede{margin:0 0 18px}
.prose p{color:var(--muted); font-size:16.5px; line-height:1.7}
.h-sub{font-size:clamp(22px,2.6vw,28px); margin:30px 0 14px}
.checks{list-style:none; margin:0; padding:0; display:grid; gap:11px}
.checks li{display:flex; gap:12px; align-items:flex-start; font-size:15.5px; color:var(--text); line-height:1.5}
.checks svg{width:18px; height:18px; flex:none; color:var(--accent); margin-top:3px}
.center-note{text-align:center; color:var(--muted); font-size:15px; margin-top:34px}
.more{display:inline-flex; align-items:center; gap:8px; font-family:var(--f-display); font-weight:700; font-size:11.5px; letter-spacing:.16em; text-transform:uppercase; color:var(--muted); border-bottom:1px solid var(--edge-2); padding-bottom:4px; transition:.18s}
.more svg{width:14px; height:14px; color:var(--accent); transition:transform .2s}
.more:hover{color:#fff; border-bottom-color:var(--accent)}
.more:hover svg{transform:translateX(4px)}

/* sticky CTA card */
.cta-box{position:sticky; top:96px; padding:28px; border:1px solid var(--edge-2); border-top:2px solid var(--accent); border-radius:var(--r); background:var(--steel); display:grid; gap:12px}
.cta-box b{font-family:var(--f-head); font-weight:400; text-transform:uppercase; font-size:22px; letter-spacing:.012em; line-height:1.05}
.cta-box p{font-size:14px; color:var(--muted); line-height:1.55; margin:0}
.cta-price{font-family:var(--f-fig); font-stretch:125%; font-weight:700; font-size:34px; color:var(--accent); line-height:1}
.cta-box .btn{margin-top:4px}
@media(max-width:959px){.cta-box{position:static}}

/* format cards */
.fmt-grid{display:grid; gap:14px; grid-template-columns:1fr}
@media(min-width:760px){.fmt-grid{grid-template-columns:repeat(3,1fr)}}
.fmt-card{padding:26px; border:1px solid var(--edge); border-radius:var(--r); background:var(--ink); display:flex; flex-direction:column; gap:8px}
.fmt-card .idx{font-size:16px}
.fmt-card b{font-family:var(--f-head); font-weight:400; text-transform:uppercase; font-size:22px; letter-spacing:.012em; line-height:1.05}
.fmt-when{font-family:var(--f-fig); font-stretch:115%; font-weight:600; font-size:13.5px; color:#fff}
.fmt-card p{font-size:14.5px; color:var(--muted); margin:0}
.fmt-card .more{margin-top:auto; padding-top:12px; align-self:flex-start}
.who-grid{display:grid; gap:14px; grid-template-columns:1fr}
@media(min-width:640px){.who-grid{grid-template-columns:repeat(2,1fr)}}
.who-card{padding:26px; border:1px solid var(--edge); border-radius:var(--r); background:var(--steel)}
.who-card b{display:block; font-family:var(--f-head); font-weight:400; text-transform:uppercase; font-size:21px; letter-spacing:.012em; margin-bottom:9px}
.who-card p{font-size:14.5px; color:var(--muted); margin:0; line-height:1.6}

/* craft lists */
.cgroups{display:grid; gap:26px 32px; grid-template-columns:1fr}
@media(min-width:700px){.cgroups{grid-template-columns:repeat(2,1fr)}}
@media(min-width:1100px){.cgroups{grid-template-columns:repeat(4,1fr)}}
.cgroup h3{font-size:19px; margin-bottom:12px; padding-bottom:10px; border-bottom:1px solid var(--edge-2)}
.craft-list{list-style:none; margin:0; padding:0; display:grid; gap:2px}
.craft-list a{display:flex; align-items:center; gap:9px; padding:9px 6px; border-radius:2px; font-size:14.5px; color:var(--muted); transition:.16s}
.craft-list a svg{width:13px; height:13px; color:var(--accent); flex:none; transition:transform .2s}
.craft-list a:hover,.craft-list a[aria-current]{background:rgba(41,182,232,.08); color:#fff}
.craft-list a:hover svg{transform:translateX(3px)}

/* team cards as links */
a.person{display:block; color:inherit}
.person-more{display:inline-flex; align-items:center; gap:7px; margin-top:14px; font-family:var(--f-display); font-weight:700; font-size:11px; letter-spacing:.16em; text-transform:uppercase; color:var(--accent)}
.person-more svg{width:13px; height:13px}
.person-hero{padding:132px 0 var(--sec); background:var(--steel); border-bottom:1px solid var(--edge)}
@media(min-width:900px){.person-hero{padding-top:170px}}
.person-hero-in{display:grid; gap:var(--gut); grid-template-columns:1fr; align-items:center}
@media(min-width:900px){.person-hero-in{grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr)}}
.person-portrait{aspect-ratio:4/5; max-width:420px; margin-inline:auto; width:100%; border:1px solid var(--edge-2); border-radius:var(--r); overflow:hidden}
.person-portrait img{width:100%; height:100%; object-fit:cover}
.person-copy{text-align:center}
@media(min-width:900px){.person-copy{text-align:left} .person-copy .eyebrow{justify-content:flex-start} .person-copy .crumbs{justify-content:flex-start}}
.person-copy h1{font-size:clamp(46px,11vw,84px); line-height:.92; margin-bottom:22px}
.person-copy h1 em{font-style:normal; color:var(--accent); display:block}
.person-copy .lede{margin:0 0 14px}
.person-copy .craft-list{display:flex; flex-wrap:wrap; gap:6px 14px; justify-content:center}
@media(min-width:900px){.person-copy .craft-list{justify-content:flex-start}}

/* reviews: stars + centred orphan row */
.stars{display:flex; gap:2px; margin-bottom:12px; color:#F5B301}
.stars svg{width:15px; height:15px}
.rev-who svg{color:var(--muted)}
@media(min-width:880px){
  .rev-grid{grid-template-columns:repeat(6,1fr)}
  .rev-grid .rev{grid-column:span 2}
  .rev-grid[data-orphan="2"] .rev:nth-last-child(2){grid-column:2/span 2}
  .rev-grid[data-orphan="2"] .rev:nth-last-child(1){grid-column:4/span 2}
  .rev-grid[data-orphan="1"] .rev:nth-last-child(1){grid-column:3/span 2}
}

/* schedule page */
.sched-list{display:grid; gap:34px}
.sched-head{display:flex; align-items:center; gap:16px; margin-bottom:16px}
.sched-head .idx{font-size:18px}
.sched-head b{display:block; font-family:var(--f-head); font-weight:400; text-transform:uppercase; font-size:clamp(21px,2.6vw,26px); letter-spacing:.012em; line-height:1.05}
.sched-head span{font-size:13.5px; color:var(--muted)}
a.date{color:inherit}

/* financing */
.fin-cards-3{grid-template-columns:1fr}
@media(min-width:640px){.fin-cards-3{grid-template-columns:repeat(2,1fr)}}
@media(min-width:1000px){.fin-cards-3{grid-template-columns:repeat(3,1fr)} .fin-cards-3 .fin-card:nth-last-child(2):nth-child(3n+1){grid-column:auto}}
.fin-tag{display:inline-block; margin-top:14px; font-style:normal; font-family:var(--f-display); font-size:10.5px; letter-spacing:.16em; text-transform:uppercase; color:var(--accent); font-weight:700}

/* contact */
.contact-grid{display:grid; gap:var(--gut); grid-template-columns:1fr}
@media(min-width:960px){.contact-grid{grid-template-columns:.9fr 1.1fr}}
.contact-links{display:flex; flex-wrap:wrap; gap:10px; margin-top:24px}
.contact-links .btn svg{width:15px; height:15px}
.cform{padding:28px; border:1px solid var(--edge-2); border-top:2px solid var(--accent); border-radius:var(--r); background:var(--ink)}
.cform .btn{margin-top:8px}

/* 404 + misc */
body.sub .callbar{display:none}
@media(max-width:900px){body.sub .callbar{display:flex}}
/* a11y: footer column labels are not headings; contrast bumps on the smallest labels */
.foot .foot-h{font-family:var(--f-display); font-weight:700; text-transform:uppercase; letter-spacing:.2em; font-size:11px; color:var(--muted); margin:0 0 16px}
.foot p{color:var(--muted)}
.spec span,.was,.crumbs,.foot-base{color:var(--muted)}
.foot-grid-4{grid-template-columns:1fr}
@media(min-width:720px){.foot-grid-4{grid-template-columns:1.6fr 1fr 1fr 1.2fr}}

/* ---- next start dates strip (course pages, under the specbar) ---- */
.nextdates{background:var(--ink); border-bottom:1px solid var(--edge)}
.nextdates-in{display:flex; flex-wrap:wrap; align-items:center; gap:14px 30px; padding:18px 0}
.nd-h{margin:0; font-family:var(--f-display); font-weight:700; font-size:10.5px; letter-spacing:.2em; text-transform:uppercase; color:var(--accent); white-space:nowrap}
.nd-row{display:flex; flex-wrap:wrap; align-items:center; gap:8px 12px}
.nd-row b{font-family:var(--f-fig); font-stretch:115%; font-weight:600; font-size:13.5px; color:#fff; white-space:nowrap}
.nd-dates{display:flex; flex-wrap:wrap; gap:6px}
.nd-date{display:inline-block; padding:7px 11px; border:1px solid var(--edge-2); border-radius:2px; font-family:var(--f-fig); font-stretch:115%; font-weight:600; font-variant-numeric:tabular-nums; font-size:13px; color:var(--text); white-space:nowrap; transition:.16s}
.nd-date:hover{border-color:var(--accent); color:#fff}
.nd-all{margin-left:auto}
@media(max-width:899px){.nextdates-in{display:grid; gap:14px} .nd-all{margin-left:0; justify-self:start}}

/* ---- home "Why Train Here" cards (index.html) ---- */
.why-grid{display:grid; gap:14px; grid-template-columns:1fr}
@media(min-width:640px){.why-grid{grid-template-columns:repeat(2,1fr)}}
@media(min-width:1000px){.why-grid{grid-template-columns:repeat(3,1fr)}}
.why-grid .who-card b{font-size:19px}
@media(max-width:399px){.why-grid .who-card b{font-size:17.5px; letter-spacing:.005em}}

/* ---- employers: checkbox group + optional stat row ---- */
.chkgroup{border:0; padding:0; margin:0 0 15px; min-width:0}
.chkgroup legend{padding:0; display:block; width:100%}
.chkgroup legend span{display:block; font-family:var(--f-display); font-size:10.5px; letter-spacing:.18em; text-transform:uppercase; font-weight:700; color:var(--muted-2); margin-bottom:8px}
.chkgroup-in{display:grid; gap:2px 14px; grid-template-columns:repeat(2,minmax(0,1fr))}
.chkgroup .chk{display:flex; gap:10px; align-items:center; font-size:15px; color:var(--text); padding:8px 0; cursor:pointer}
.chkgroup .chk input{flex:none; width:18px; height:18px; accent-color:var(--accent); margin:0}
.stat-row{display:grid; gap:14px; grid-template-columns:repeat(3,minmax(0,1fr)); margin-top:30px}
.stat{padding:20px; border:1px solid var(--edge); border-radius:var(--r); background:var(--steel); text-align:center}
.stat b{display:block; font-family:var(--f-fig); font-stretch:125%; font-weight:700; font-size:32px; color:var(--accent); line-height:1}
.stat span{display:block; font-size:13px; color:var(--muted); margin-top:8px}
.foot-lang{display:inline-block; margin-top:20px; font-family:var(--f-display); font-weight:700; font-size:11px; letter-spacing:.16em; text-transform:uppercase; color:var(--muted); border-bottom:1px solid var(--edge-2); padding-bottom:4px}
.foot-lang:hover{color:var(--accent); border-bottom-color:var(--accent)}

/* ---- guides ---- */
.ghead{padding:132px 0 clamp(36px,5vw,56px); background:var(--steel); border-bottom:1px solid var(--edge); text-align:center}
.ghead-in{max-width:860px; margin-inline:auto}
.ghead .crumbs{justify-content:center}
.ghead .eyebrow{justify-content:center}
.ghead h1{font-size:clamp(31px,6vw,58px); line-height:1.02; margin:0 auto}
.ghead .lede{margin:20px auto 0; max-width:60ch}
.gmeta{margin:18px 0 0; font-family:var(--f-display); font-size:11px; letter-spacing:.16em; text-transform:uppercase; color:var(--muted-2); font-weight:700}
@media(min-width:900px){.ghead{padding-top:170px}}
.guide-wrap{max-width:780px; margin-inline:auto}
.guide-body p,.guide-body li{color:var(--muted); font-size:17px; line-height:1.72}
.guide-body p{margin:0 0 20px}
.guide-body h2{font-size:clamp(24px,3vw,32px); line-height:1.05; margin:38px 0 14px}
.guide-body ul{margin:0 0 22px; padding-left:22px; display:grid; gap:8px}
.guide-body a:not(.btn){color:var(--accent)}
.guide-body strong{color:#DCDAD6}
.guide-cta{margin:34px 0; padding:26px; border:1px solid var(--edge-2); border-left:3px solid var(--accent); border-radius:var(--r); background:var(--steel)}
.guide-cta b{display:block; font-family:var(--f-head); font-weight:400; text-transform:uppercase; font-size:22px; margin-bottom:8px; letter-spacing:.012em}
.guide-cta p{margin:0 0 16px; font-size:15px; line-height:1.6}
.guide-cta .hero-cta{justify-content:flex-start; margin:0}
.guide-grid{display:grid; gap:14px; grid-template-columns:1fr}
@media(min-width:760px){.guide-grid{grid-template-columns:repeat(3,1fr)}}
a.guide-card{display:flex; flex-direction:column; gap:10px; padding:26px; border:1px solid var(--edge); border-radius:var(--r); background:var(--steel); color:inherit; transition:border-color .18s}
a.guide-card:hover{border-color:var(--accent)}
.guide-card .idx{font-size:16px}
.guide-card b{font-family:var(--f-head); font-weight:400; text-transform:uppercase; font-size:21px; line-height:1.05; letter-spacing:.012em}
.guide-card p{font-size:14.5px; color:var(--muted); margin:0; line-height:1.6}
.guide-card .person-more{margin-top:auto; padding-top:8px}

/* ---- /book/: the booking page. Steps stack; the finished ones collapse to a
   one-line summary with a Change link, the current one is open, later ones wait. ---- */
.bk-head{padding:124px 0 30px; background:var(--steel); border-bottom:1px solid var(--edge)}
@media(min-width:900px){.bk-head{padding:160px 0 40px}}
.bk-head .crumbs,.bk-head .eyebrow{justify-content:flex-start}
.bk-head .eyebrow::before{display:none}
.bk-head h1{font-size:clamp(42px,9vw,76px); line-height:.94; max-width:none}
.bk-head h1 em{font-style:normal; color:var(--accent); display:block}
.bk-head .lede{margin:18px 0 0; max-width:58ch}
.bk-marks{display:flex; flex-wrap:wrap; gap:8px 22px; margin:22px 0 0; padding:0; list-style:none; font-family:var(--f-display); font-size:11px; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--muted)}
.bk-marks li{display:flex; align-items:center; gap:8px}
.bk-marks svg{width:14px; height:14px; color:var(--accent); flex:none}
.bk-main{padding:clamp(26px,4vw,52px) 0 var(--sec)}
.bk-flash{margin:0 0 18px; padding:13px 16px; border-left:3px solid var(--accent); background:rgba(41,182,232,.08); font-size:14.5px; line-height:1.55; color:#D8D6D2}
.bk-flash a{color:var(--accent); font-weight:600}
.bk-grid{display:grid; gap:var(--gut); grid-template-columns:minmax(0,1fr); align-items:start}
@media(min-width:1000px){.bk-grid{grid-template-columns:minmax(0,1fr) 336px}}
.bk-steps{display:grid; gap:10px}
.bk-step{border:1px solid var(--edge); background:var(--steel)}
.bk-step-h{display:grid; grid-template-columns:auto minmax(0,1fr) auto; align-items:center; gap:14px; width:100%; padding:17px 20px; text-align:left; cursor:default}
.bk-step.is-done .bk-step-h{cursor:pointer}
.bk-step.is-done .bk-step-h:hover{background:rgba(255,255,255,.02)}
.bk-step-h .idx{font-size:15px}
.bk-step-h b{display:block; font-family:var(--f-head); font-weight:400; text-transform:uppercase; font-size:clamp(19px,2.2vw,23px); letter-spacing:.012em; line-height:1.05}
.bk-pick{display:none; font-size:13.5px; color:#fff; line-height:1.4; margin-top:3px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
.bk-change{display:none; font-family:var(--f-display); font-size:10.5px; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--accent); white-space:nowrap}
.bk-step.is-done .bk-pick,.bk-step.is-done .bk-change{display:block}
.bk-step.is-done .idx{color:var(--ok)}
.bk-step.is-locked{opacity:.4}
.bk-step.is-open{border-color:var(--edge-2)}
.bk-step-b{display:none; padding:2px 20px 24px; border-top:1px solid var(--edge); animation:fade .3s ease}
.bk-step.is-open .bk-step-b{display:block}
.bk-q{margin:20px 0 16px; font-family:var(--f-display); font-weight:700; font-size:11px; letter-spacing:.18em; text-transform:uppercase; color:var(--muted-2)}
.bk-q span{color:var(--accent); margin-left:8px}
.bk-step .field input,.bk-step .field select,.bk-step .field textarea,.bk-step .summary{background:var(--ink)}
.bk-step .consent{margin-top:6px}
.bk-step .paytabs{margin-bottom:14px}
.bk-step #coLegal{margin:10px 0 0}
@media(max-width:560px){.bk-step-h{padding:14px 14px; gap:12px} .bk-step-b{padding:2px 14px 20px}}
/* certification cards: photo left on phones, photo on top from tablet up */
.bp-grid{display:grid; gap:10px; grid-template-columns:1fr}
@media(min-width:760px){.bp-grid{grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px}}
.bp{display:grid; grid-template-columns:110px minmax(0,1fr); text-align:left; border:1px solid var(--edge); background:var(--ink); overflow:hidden; transition:border-color .18s; padding:0}
@media(min-width:760px){.bp{grid-template-columns:1fr; grid-template-rows:auto 1fr}}
.bp:hover{border-color:rgba(41,182,232,.5)}
.bp.sel{border-color:var(--accent); box-shadow:inset 0 0 0 1px var(--accent)}
.bp-shot{position:relative; overflow:hidden; background:var(--steel-3); min-height:112px}
@media(min-width:760px){.bp-shot{aspect-ratio:16/9; min-height:0}}
.bp-shot img{position:absolute; inset:0; width:100%; height:100%; object-fit:cover}
.bp-shot::after{content:""; position:absolute; inset:0; background:linear-gradient(180deg,transparent 50%,rgba(10,10,12,.55))}
.bp-body{display:flex; flex-direction:column; min-width:0; padding:13px 15px 14px}
.bp b{font-family:var(--f-head); font-weight:400; text-transform:uppercase; font-size:19px; letter-spacing:.01em; line-height:1.05}
.bp-blurb{display:block; margin-top:5px; font-size:13px; line-height:1.45; color:var(--muted)}
.bp-price{display:flex; flex-wrap:wrap; align-items:baseline; gap:3px 8px; margin-top:auto; padding-top:10px; font-family:var(--f-fig); font-stretch:125%; font-weight:700; font-size:18px; color:var(--accent); line-height:1}
.bp-price .was{margin-left:0}
.bp-price small{font-family:var(--f-display); font-stretch:100%; font-weight:600; font-size:10px; color:var(--muted-2); letter-spacing:.08em; text-transform:uppercase}
@media(max-width:400px){.bp{grid-template-columns:92px minmax(0,1fr)} .bp-shot{min-height:100px} .bp-blurb{display:none} .bp-body{padding:12px 13px}}
/* start dates: a calendar tile per date */
.bd-grid{display:grid; gap:8px; grid-template-columns:repeat(3,minmax(0,1fr))}
@media(min-width:480px){.bd-grid{grid-template-columns:repeat(4,minmax(0,1fr))}}
@media(min-width:700px){.bd-grid{grid-template-columns:repeat(5,minmax(0,1fr))}}
@media(min-width:1000px){.bd-grid{grid-template-columns:repeat(4,minmax(0,1fr))}}
@media(min-width:1180px){.bd-grid{grid-template-columns:repeat(5,minmax(0,1fr))}}
.bd{display:flex; flex-direction:column; align-items:center; padding:12px 4px; border:1px solid var(--edge); background:var(--ink); text-align:center; transition:.16s}
.bd:hover:not(:disabled){border-color:rgba(41,182,232,.5); transform:translateY(-2px)}
.bd.sel{border-color:var(--accent); background:rgba(41,182,232,.09)}
.bd:disabled{opacity:.32; cursor:not-allowed}
.bd em{font-style:normal; font-family:var(--f-display); font-weight:700; font-size:9.5px; letter-spacing:.16em; text-transform:uppercase; color:var(--muted)}
.bd.sel em{color:var(--accent)}
.bd b{font-family:var(--f-fig); font-stretch:125%; font-weight:700; font-variant-numeric:tabular-nums; font-size:26px; line-height:1; margin:6px 0 3px; color:#fff}
.bd span{font-family:var(--f-display); font-size:11px; font-weight:600; color:var(--muted)}
.bd i{font-style:normal; margin-top:6px; font-family:var(--f-display); font-size:9px; letter-spacing:.12em; text-transform:uppercase; color:var(--muted-2); font-weight:700}
.bd i.left{color:var(--accent)}
/* live seat counts on date chips (home band, course strips): "· 2 left" / "· full" */
.ln-date .left,.nd-date .left{color:var(--accent); font-weight:600}
.ln-date.is-full,.nd-date.is-full{opacity:.38; pointer-events:none; text-decoration:line-through}
.ln-date.is-full .left,.nd-date.is-full .left{text-decoration:none; color:var(--muted-2)}
.bk-note{margin:16px 0 0; font-size:13px; color:var(--muted-2); line-height:1.55}
.bk-note a{color:var(--accent)}
.bk-err{margin:0 0 12px; padding:11px 14px; border-left:3px solid #E86A5A; background:rgba(232,106,90,.09); font-size:14px; color:#F1D7D2}
/* desktop: the running order sticks beside the steps */
.bk-side{display:none}
@media(min-width:1000px){
  .bk-side{display:block; position:sticky; top:96px; border:1px solid var(--edge-2); border-top:2px solid var(--accent); background:var(--steel)}
  .bk-side-shot{position:relative; aspect-ratio:16/9; background:var(--steel-3); overflow:hidden}
  .bk-side-shot img{width:100%; height:100%; object-fit:cover}
  .bk-side-shot::after{content:""; position:absolute; inset:0; background:linear-gradient(180deg,transparent 30%,rgba(10,10,12,.88))}
  .bk-side-shot b{position:absolute; left:18px; right:18px; bottom:14px; z-index:1; font-family:var(--f-head); font-weight:400; text-transform:uppercase; font-size:24px; letter-spacing:.012em; line-height:1.05}
  .bk-side .summary{border:0; background:none; margin:0}
  .bk-side .summary-row{padding:12px 18px}
  .bk-side .summary-row.total{background:var(--steel-3)}
  .bk-side-call{padding:14px 18px; border-top:1px solid var(--edge); font-size:13px; line-height:1.55; color:var(--muted); margin:0}
  .bk-side-call a{color:#fff; font-weight:600; white-space:nowrap}
}
.bk-done{max-width:720px; margin-inline:auto; border:1px solid var(--edge-2); border-top:2px solid var(--ok); background:var(--steel)}
.bk-done .co-success h2{font-size:30px; margin-bottom:12px}

/* ---- desktop cursor ----
   The site's own arrow: the lucide pointer the icon set already comes from, white
   with an ink edge everywhere, accent blue over anything clickable. SVG serves
   Firefox and Chrome; the image-set PNGs (1x/2x) cover Safari (no SVG cursors)
   and keep HiDPI Chrome crisp. Every rule keeps the native cursor as its
   fallback, and phones/tablets never see any of it. Last in the bundle on
   purpose: it has to outrank every component's own cursor:pointer. */
@media (hover:hover) and (pointer:fine){
  html{cursor:url(/img/cur-arrow.svg) 2 2, auto}
  html{cursor:-webkit-image-set(url(/img/cur-arrow.png) 1x, url(/img/cur-arrow@2x.png) 2x) 2 2, auto}
  :is(p, li, dd, dt, td, th, blockquote, figcaption, small, input, textarea){cursor:text}
  :is(a, button, select, label, summary, [role=button], .btn, .macc-t, .faq-q, .hero-fig, .reel-arw, .consent .chk, .chkgroup .chk, .bk-step.is-done .bk-step-h, .reel-frame.needs-tap, input[type=submit], input[type=button], input[type=checkbox], input[type=radio]):not(:disabled),
  :is(a, button, label, summary, [role=button], .btn, .macc-t, .faq-q, .hero-fig, .consent .chk, .chkgroup .chk) *{cursor:url(/img/cur-link.svg) 2 2, pointer}
  :is(a, button, select, label, summary, [role=button], .btn, .macc-t, .faq-q, .hero-fig, .reel-arw, .consent .chk, .chkgroup .chk, .bk-step.is-done .bk-step-h, .reel-frame.needs-tap, input[type=submit], input[type=button], input[type=checkbox], input[type=radio]):not(:disabled),
  :is(a, button, label, summary, [role=button], .btn, .macc-t, .faq-q, .hero-fig, .consent .chk, .chkgroup .chk) *{cursor:-webkit-image-set(url(/img/cur-link.png) 1x, url(/img/cur-link@2x.png) 2x) 2 2, pointer}
  /* booking steps that are not finished yet are not clickable: plain arrow */
  .bk-step:not(.is-done) .bk-step-h, .bk-step:not(.is-done) .bk-step-h *{cursor:inherit}
  /* gallery tiles are role=button (so the link rule catches them); the native
     zoom glass says more than a blue arrow does */
  .gal figure, .gal figure *{cursor:zoom-in !important}
}
"""

SITE_JS = r"""
/* Prime Lift — shared page script (generated by build.py). Nav, mobile menu,
   reveal-on-scroll, FAQ accordions and the sticky call bar for inner pages. */
(function(){
  const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const nav=$("#nav"), burger=$("#navBurger"), callbar=$("#callbar");
  const home=!!$(".hero");            /* the home page keeps its own scroll logic */

  if(burger){
    const setAcc=(acc,open)=>{ acc.classList.toggle("open",open); acc.querySelector(".macc-t").setAttribute("aria-expanded",open?"true":"false"); };
    burger.addEventListener("click",()=>{
      const open=document.body.classList.toggle("mnav-open");
      burger.setAttribute("aria-expanded",open?"true":"false");
      burger.setAttribute("aria-label",open?"Close menu":"Open menu");
      if(!open) $$(".macc.open").forEach(a=>setAcc(a,false));   /* collapse on close so it reopens tidy */
    });
    /* Courses / Academy accordions inside the mobile menu */
    $$(".macc-t").forEach(t=>t.addEventListener("click",()=>{ const acc=t.parentElement; setAcc(acc,!acc.classList.contains("open")); }));
    $$("#mnav a").forEach(a=>a.addEventListener("click",()=>{ document.body.classList.remove("mnav-open"); burger.setAttribute("aria-expanded","false"); }));
    document.addEventListener("keydown",e=>{ if(e.key==="Escape"&&document.body.classList.contains("mnav-open")) burger.click(); });
    /* rotate a small tablet past the desktop breakpoint with the menu open and the
       sheet hides itself, leaving the scroll lock and the opaque bar behind */
    window.matchMedia("(min-width:1000px)").addEventListener("change",e=>{
      if(e.matches&&document.body.classList.contains("mnav-open")) burger.click();
    });
  }

  if(!home){
    /* no layout reads inside the handler: just scrollY, which is free */
    let ticking=false, navp="";
    /* COMPARISON SWITCH (temporary, mirrors index.html): ?nav=flat = header never
       changes; ?nav=scrim = scroll-driven. Remembered per tab. Remove once decided. */
    const NAVMODE=(()=>{ try{ const q=new URLSearchParams(location.search).get("nav"); if(q) sessionStorage.setItem("navMode",q); return sessionStorage.getItem("navMode")||"scrim"; }catch(e){ return "scrim"; } })();
    function paint(){
      const y=window.scrollY;
      /* header progress 0..1 over the first 160px, eased out so the scrim is
         already there by the time the hero text has moved; drives bar height,
         logo size and the scrim opacity in CSS (--navp) */
      if(nav&&NAVMODE!=="flat"){ const t=Math.min(1,Math.max(0,y/160)), p=(1-(1-t)*(1-t)).toFixed(3); if(p!==navp){ navp=p; nav.style.setProperty("--navp",p); } }
      if(callbar) callbar.classList.toggle("show",y>360);
      ticking=false;
    }
    window.addEventListener("scroll",()=>{ if(!ticking){ ticking=true; requestAnimationFrame(paint); } },{passive:true});
    paint();
  }

  /* reveal */
  const rv=$$(".rv");
  if("IntersectionObserver" in window){
    const io=new IntersectionObserver(es=>es.forEach(e=>{ if(e.isIntersecting){ e.target.classList.add("in"); io.unobserve(e.target); } }),{rootMargin:"0px 0px -8% 0px",threshold:.08});
    rv.forEach(el=>io.observe(el));
  } else rv.forEach(el=>el.classList.add("in"));

  /* FAQ accordions on inner pages (home renders its own) */
  $$("[data-faq]").forEach(host=>{
    host.addEventListener("click",e=>{
      const q=e.target.closest(".faq-q"); if(!q) return;
      const item=q.parentElement, a=item.querySelector(".faq-a"), open=item.classList.contains("open");
      $$(".faq-item",host).forEach(it=>{ it.classList.remove("open"); it.querySelector(".faq-a").style.maxHeight=null; it.querySelector(".faq-q").setAttribute("aria-expanded","false"); });
      if(!open){ item.classList.add("open"); a.style.maxHeight=a.scrollHeight+"px"; q.setAttribute("aria-expanded","true"); }
    });
  });
  window.addEventListener("resize",()=>{ $$(".faq-item.open .faq-a").forEach(a=>{ a.style.maxHeight="none"; const h=a.scrollHeight; a.style.maxHeight=h+"px"; }); });

  /* Photo gallery lightbox. The CSS for this (.gal-zoom, .lb) shipped a while
     back with nothing driving it, so galleries showed a zoom cursor that did
     nothing. Click a figure to open it full size; arrows or swipe-free nav
     buttons to move; Esc or the backdrop to close. Body overflow is the same
     scroll lock the Lenis prevent hook already looks for. */
  (function(){
    /* index.html ships its own lightbox (#lightbox) bound to the same .gal
       figures, and its graduate wall is class="gal gw-strip". Never double-bind
       on top of it. */
    if(document.getElementById("lightbox")) return;
    const figs=$$(".gal figure, [data-gallery] figure"); if(!figs.length) return;
    const svg=d=>'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'+d+'</svg>';
    const ZOOM=svg('<circle cx="11" cy="11" r="7"/><path d="m20 20-3.6-3.6"/><path d="M11 8.4v5.2"/><path d="M8.4 11h5.2"/>');
    figs.forEach(f=>{ const b=document.createElement("button"); b.type="button"; b.className="gal-zoom"; b.setAttribute("aria-label","View larger"); b.innerHTML=ZOOM; f.appendChild(b); });
    const lb=document.createElement("div");
    lb.className="lb"; lb.setAttribute("role","dialog"); lb.setAttribute("aria-modal","true"); lb.setAttribute("aria-label","Photo");
    lb.innerHTML='<button class="lb-x" type="button" aria-label="Close">'+svg('<path d="M18 6 6 18"/><path d="m6 6 12 12"/>')+'</button>'
      +'<button class="lb-nav lb-prev" type="button" aria-label="Previous photo">'+svg('<path d="m15 18-6-6 6-6"/>')+'</button>'
      +'<button class="lb-nav lb-next" type="button" aria-label="Next photo">'+svg('<path d="m9 18 6-6-6-6"/>')+'</button>'
      +'<figure class="lb-fig"><img alt=""><figcaption class="lb-cap"><span class="idx"></span><i></i><em></em></figcaption></figure>';
    document.body.appendChild(lb);
    const img=$("img",lb), idx=$(".idx",lb), cap=$("em",lb);
    let at=0, last=null;
    const pad=n=>String(n).padStart(2,"0");
    /* currentSrc is whatever the 25vw thumbnail loaded (often the 480 rung), which
       is useless full screen. Take the widest candidate in the srcset instead. */
    function widest(im){
      const ss=im.getAttribute("srcset");
      if(!ss) return im.currentSrc||im.src;
      return ss.split(",").map(x=>x.trim().split(/\s+/))
               .reduce((a,b)=>(parseInt(b[1])||0)>(parseInt(a[1])||0)?b:a)[0];
    }
    function paint(){
      const f=figs[at], src=$("img",f);
      img.src=widest(src); img.alt=src.alt||"";
      idx.textContent=pad(at+1)+" / "+pad(figs.length);
      cap.textContent=(($("figcaption",f)||{}).textContent||"").trim();
    }
    function open(i){ at=i; last=document.activeElement; paint(); lb.classList.add("open"); document.body.style.overflow="hidden"; $(".lb-x",lb).focus(); }
    function close(){ lb.classList.remove("open"); document.body.style.overflow=""; if(last&&last.focus) last.focus(); }
    const go=d=>{ at=(at+d+figs.length)%figs.length; paint(); };
    figs.forEach((f,i)=>f.addEventListener("click",()=>open(i)));
    $(".lb-x",lb).addEventListener("click",close);
    $(".lb-prev",lb).addEventListener("click",e=>{ e.stopPropagation(); go(-1); });
    $(".lb-next",lb).addEventListener("click",e=>{ e.stopPropagation(); go(1); });
    lb.addEventListener("click",e=>{ if(e.target===lb) close(); });
    document.addEventListener("keydown",e=>{
      if(!lb.classList.contains("open")) return;
      if(e.key==="Escape") close();
      else if(e.key==="ArrowLeft") go(-1);
      else if(e.key==="ArrowRight") go(1);
    });
  })();

  /* course pages: the "next start dates" strip is rendered at build time from
     SCHEDULE_RULES in build.py; recompute from today's date so it never goes
     stale between builds. Same rule: next N occurrences of the weekday, from
     tomorrow (booking closes the day before). */
  const MONS=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], DOWS=["Sun","Mon","Tue","Wed","Thu","Fri","Sat"], SCHED=__SCHED__;
  const iso=d=>d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");
  const bookable=(x,k)=>{ if(SCHED.closed[iso(x)]||(SCHED.full[iso(x)]||[]).some(f=>f===k||f==="*")) return false;
    const L=window.__plSeats; return !(L&&L.taken&&((L.cap||8)-(L.taken[k+":"+iso(x)]||0)<=0)); };
  function renderStrips(){
  $$(".nd-row").forEach(row=>{
    const wd=+row.dataset.wd; if(isNaN(wd)) return;
    const key=row.dataset.book+":"+row.dataset.fmt, links=$$(".nd-date",row);
    const step=+row.dataset.every||7, anchor=row.dataset.anchor||"";
    const d=new Date(); d.setHours(0,0,0,0); d.setDate(d.getDate()+(+row.dataset.lead||1));
    while(d.getDay()!==wd) d.setDate(d.getDate()+1);
    /* biweekly rules are phased off their anchor date, not off today */
    if(anchor&&step!==7){ const p=anchor.split("-").map(Number), a=new Date(p[0],p[1]-1,p[2]); const off=((Math.round((d-a)/864e5)%step)+step)%step; if(off) d.setDate(d.getDate()+(step-off)); }
    const dates=[]; while(dates.length<links.length){ if(bookable(d,key)) dates.push(new Date(d)); d.setDate(d.getDate()+step); }
    links.forEach((a,i)=>{
      const x=dates[i];
      a.href="/book/?book="+row.dataset.book+"&fmt="+row.dataset.fmt+"&date="+iso(x);
      a.textContent=DOWS[x.getDay()]+", "+MONS[x.getMonth()]+" "+x.getDate();
    });
  });
  }
  renderStrips();
  document.addEventListener("pl:seats",renderStrips);
})();

/* GOOGLE ANALYTICS (GA4, property "Prime Lift Rigging Academy", stream
   primeliftriggingtx.com). Loaded the same lazy way as the chat widget below so
   it never costs Lighthouse points: first scroll / touch / key, or 6s idle,
   whichever comes first. gtag sends the page_view on config whenever it loads,
   so pageviews still record for visitors who bounce without interacting. */
(function(){
  if (window.__plGa) return; window.__plGa = 1;
  var done = false;
  function ga(){
    if (done) return; done = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function(){ dataLayer.push(arguments); };
    gtag("js", new Date());
    gtag("config", "G-Z01JPFJB5X");
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=G-Z01JPFJB5X";
    document.head.appendChild(s);
    ["scroll","pointerdown","touchstart","keydown"].forEach(function(e){ window.removeEventListener(e, ga); });
  }
  ["scroll","pointerdown","touchstart","keydown"].forEach(function(e){ window.addEventListener(e, ga, {passive:true}); });
  setTimeout(ga, 6000);
})();

/* GHL live chat widget (Conversation AI). Loaded lazily so it never competes with
   first paint: first scroll / touch / pointer, or 6s idle, whichever comes first. */
(function(){
  if (window.__plChat) return; window.__plChat = 1;
  var done = false;
  function load(){
    if (done) return; done = true;
    var s = document.createElement("script");
    s.src = "https://widgets.leadconnectorhq.com/loader.js";
    s.setAttribute("data-resources-url", "https://widgets.leadconnectorhq.com/chat-widget/loader.js");
    s.setAttribute("data-widget-id", "6a935fa49f17bc64b3251340");
    document.body.appendChild(s);
    ["scroll","pointerdown","touchstart","keydown"].forEach(function(e){ window.removeEventListener(e, load); });
    lift();
  }
  /* On phones the sticky call bar owns the bottom 60px; keep the bubble above it.
     The widget's bubble lives in an open shadow root with inline bottom:20px, and
     the widget REWRITES that inline style every time the chat window closes, so
     setting it once is not enough (the bubble dropped back onto the Book button).
     A stylesheet inside the shadow root with !important beats the inline value
     for good; the offset rides on a CSS variable on the host element. */
  function lift(){
    var tries = 0;
    var cb = document.getElementById("callbar");
    var CSS = "#lc_text-widget,#lc_text-widget--btn{bottom:var(--pl-bottom,20px)!important}";
    function place(){
      var host = document.querySelector("chat-widget"), sr = host && host.shadowRoot;
      var box = sr && sr.getElementById("lc_text-widget"), btn = sr && sr.getElementById("lc_text-widget--btn");
      if (!box || !btn) { if (tries++ < 60) setTimeout(place, 500); return; }
      if (!sr.getElementById("pl-lift")) { var st = document.createElement("style"); st.id = "pl-lift"; st.textContent = CSS; sr.appendChild(st); }
      var mobile = window.innerWidth <= 900, up = mobile && cb && cb.classList.contains("show");
      host.style.visibility = (mobile && !up) ? "hidden" : "visible";
      host.style.setProperty("--pl-bottom", up ? "78px" : "20px");
      if (!host.__plObs) {
        /* if the widget ever rebuilds its shadow tree, put the stylesheet back */
        host.__plObs = new MutationObserver(function(){ if (!sr.getElementById("pl-lift")) place(); });
        host.__plObs.observe(sr, {childList:true});
      }
    }
    place();
    if (cb) new MutationObserver(place).observe(cb, {attributes:true, attributeFilter:["class"]});
    window.addEventListener("resize", place, {passive:true});
  }
  ["scroll","pointerdown","touchstart","keydown"].forEach(function(e){ window.addEventListener(e, load, {passive:true, once:true}); });
  setTimeout(load, 12000);   /* idle fallback; anyone who scrolls or taps gets it immediately */
})();

/* LIVE SEATS. /.netlify/functions/seats counts open cards in the office's own
   Enrollment pipeline (one card = one seat, Lost frees it), so a class fills up
   on the site the moment the 8th student is booked online OR by phone. Nothing
   is decorated any more: the office wants booked dates GONE, never labeled or
   counted down. Each date surface listens for pl:seats and re-renders itself
   without the full dates (home band + next-class strip in index.html, course
   strips and the class-dates page here, the /book/ grid in its own script).
   Fails silent. */
(function(){
  function go(){
    var url = "/.netlify/functions/seats";
    if (location.protocol === "file:" || /^(127\.0\.0\.1|localhost)$/.test(location.hostname) && location.port !== "8888") return;
    fetch(url, {cache: "no-cache"}).then(function(r){ return r.ok ? r.json() : null; }).then(function(d){
      if (!d || !d.taken) return;
      window.__plSeats = d;
      document.dispatchEvent(new CustomEvent("pl:seats", {detail: d}));
    }).catch(function(){});
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", go); else go();
})();

/* DESKTOP INERTIA SCROLL. On fine-pointer screens 1000px and up, /js/lenis.min.js
   (vendored, MIT, v1.3.26) eases wheel scrolling and same-page anchor jumps, the
   glide people know from agency sites. Phones, tablets and reduced-motion users
   never download it and keep native scroll-behavior:smooth from site.css.
   The prevent hook keeps native behaviour wherever hijacking would break things:
   any overflowing nested scroller under the pointer (chat log, tables, strips)
   and any body scroll lock (gallery lightbox, mobile menu). Lenis honours each
   target's scroll-margin-top, so anchors land where they do today. */
(function(){
  var mm = window.matchMedia;
  if (!mm || !mm("(pointer:fine)").matches || mm("(prefers-reduced-motion:reduce)").matches || window.innerWidth < 1000) return;
  var s = document.createElement("script");
  s.src = "/js/lenis.min.js"; s.defer = true;
  s.onload = function(){
    if (!window.Lenis) return;
    var lenis = window.__lenis = new Lenis({
      lerp: 0.1, wheelMultiplier: 1, smoothWheel: true, syncTouch: false, anchors: false, autoRaf: true,
      prevent: function(node){
        if (node === document.body) return document.body.style.overflow === "hidden" || document.body.classList.contains("mnav-open");
        if (node.nodeType !== 1 || node === document.documentElement) return false;
        if (node.scrollHeight <= node.clientHeight + 1) return false;
        var o = getComputedStyle(node).overflowY;
        return o === "auto" || o === "scroll";
      }
    });
    /* Same-page anchors: Lenis's own `anchors` option never cancels the browser's
       hash jump, so a click flashed to the target, snapped back and then glided.
       Cancel the jump here and let Lenis ease from where the page is; the hash
       still lands in the URL. Bubble phase, so a link's own handler (FAQ, reel
       arrows, "#" hooks) that preventDefaults keeps winning. */
    document.addEventListener("click", function(e){
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var a = e.target.closest && e.target.closest("a[href]"); if (!a) return;
      var u; try { u = new URL(a.href); } catch (_) { return; }
      if (u.host !== location.host || u.pathname !== location.pathname || u.hash.length < 2) return;
      var el = document.getElementById(decodeURIComponent(u.hash.slice(1))); if (!el) return;
      e.preventDefault();
      if (location.hash !== u.hash) history.pushState(null, "", u.hash);
      lenis.scrollTo(el);
    });
  };
  document.head.appendChild(s);
})();

/* THIS WEEK'S SPECIAL. The office edits row 2 of the "Prime Lift Weekly
   Updates" Google Sheet (tab "This Week's Special", published to the web as
   CSV): A2 = the banner sentence, B2 = last day to show it. Empty A2 = no
   banner. Injected AFTER the 100svh hero so it costs nothing at first paint
   and never shifts visible layout. Fails silent; renders home page only. */
(function(){
  var hero = document.querySelector(".hero");
  if (!hero || !window.fetch) return;
  var CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSwHQGTw88cR99Mj_Bg0OenyFiPZb3jVtatRpygtuOwA-KNqold2F6P98cgOLB9HEAM84YeSlQ8jCV2/pub?gid=1405683584&single=true&output=csv";
  /* 5-minute cache bucket: fresh enough for a weekly banner, kind to Google's edge */
  fetch(CSV + "&cb=" + Math.floor(Date.now() / 3e5), {cache: "no-store"})
    .then(function(r){ return r.ok ? r.text() : ""; })
    .then(function(t){
      var line = (t.split(/\r?\n/)[1] || "");
      /* first two CSV fields of the data row; handles quoted commas */
      var f = [], cur = "", q = false, i, c;
      for (i = 0; i < line.length && f.length < 2; i++) {
        c = line[i];
        if (q) { if (c === '"') { if (line[i+1] === '"') { cur += '"'; i++; } else q = false; } else cur += c; }
        else if (c === '"') q = true;
        else if (c === ",") { f.push(cur); cur = ""; }
        else cur += c;
      }
      f.push(cur);
      var text = (f[0] || "").trim(), until = (f[1] || "").trim();
      if (!text) return;
      if (until) {
        var end = null, m = until.match(/^(\d{1,2})[\/\-.](\d{1,2})(?:[\/\-.](\d{2,4}))?$/);
        if (m) {
          var y = m[3] ? (m[3].length === 2 ? 2000 + +m[3] : +m[3]) : new Date().getFullYear();
          end = new Date(y, +m[1] - 1, +m[2], 23, 59, 59);
          /* no year given and the date is months gone: they meant next year */
          if (!m[3] && (new Date() - end) > 90 * 864e5) end.setFullYear(y + 1);
        } else {
          var d = new Date(until);
          if (!isNaN(d)) { d.setHours(23, 59, 59, 0); end = d; }
        }
        if (end && new Date() > end) return;
      }
      var s = document.createElement("section"); s.className = "spx"; s.setAttribute("aria-label", "This week's special");
      var w = document.createElement("div"); w.className = "wrap spx-in";
      var k = document.createElement("span"); k.className = "spx-k"; k.textContent = "This Week";
      var b = document.createElement("span"); b.className = "spx-t"; b.textContent = text;
      var a = document.createElement("a"); a.className = "spx-cta"; a.href = "/book/"; a.textContent = "Book a Class ›";
      w.appendChild(k); w.appendChild(b); w.appendChild(a); s.appendChild(w);
      hero.parentNode.insertBefore(s, hero.nextSibling);
    })
    .catch(function(){});
})();
"""

def write_assets():
    global CSS_VER
    make_variants()
    w("css/pages.css", PAGES_CSS.lstrip("\n"))
    w("js/site.js", SITE_JS.lstrip("\n").replace("__SCHED__", sched_json()))
    # one stylesheet request instead of three (fonts + site + pages); URL carries a content hash
    bundle = "\n".join(io.open(os.path.join(ROOT, "css", f), encoding="utf-8").read() for f in ("fonts.css", "site.css", "pages.css"))
    # the headline grunge mask (7 KB png) rides inside the CSS: a masked element can't paint until its
    # mask arrives, and as a separate request it sat behind the stylesheet on the LCP path
    import base64
    g = base64.b64encode(open(os.path.join(ROOT, "img", "grunge.png"), "rb").read()).decode("ascii")
    bundle = bundle.replace("url(/img/grunge.png)", "url(data:image/png;base64,%s)" % g)
    # Anton (18 KB) is the headline face and the LCP text: shipping it inside the stylesheet means the
    # headline paints in Anton on the first frame instead of fallback-then-swap (the swap re-paint is
    # what Lighthouse was timing as LCP). The other faces stay as files with font-display:swap.
    an = base64.b64encode(open(os.path.join(ROOT, "fonts", "anton-400.woff2"), "rb").read()).decode("ascii")
    bundle = bundle.replace("url(/fonts/anton-400.woff2)", "url(data:font/woff2;base64,%s)" % an)
    CSS_VER = hashlib.md5(bundle.encode("utf-8")).hexdigest()[:8]
    w("css/bundle.css", bundle)

def write_sitemap():
    items = "".join("  <url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>\n" % (ORIGIN, u, TODAY, p) for u, p in PAGES)
    w("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s</urlset>\n' % items)
    rp = os.path.join(ROOT, "robots.txt")
    r = io.open(rp, encoding="utf-8").read()
    r = re.sub(r"\nSitemap: .*", "", r).rstrip("\n") + "\n\nSitemap: %s/sitemap.xml\n" % ORIGIN
    io.open(rp, "w", encoding="utf-8", newline="\n").write(r)

def write_llms():
    lines = ["# Prime Lift Rigging Academy", "",
             "> NCCER Accredited Training and Assessment Center in Portland, Texas (Coastal Bend, near Corpus Christi). Advanced Rigger and Signal Person certification courses, and NCCER craft assessments (test-outs) in 36 crafts. Locally and Latino-owned.", "",
             "- Address: %s" % FULL_ADDR, "- Phone: %s" % BIZ["phone"], "- Email: %s" % BIZ["email"], "- Office hours: %s" % BIZ["hours"],
             "- Advanced Rigger course: $1,000 (promotion; normally $1,700), $200 deposit. 4 days Mon-Thu 8 AM-2 PM (day) or 6-11 PM (night), or 3-Day Weekend Express Fri-Sun 8 AM-5 PM. NCCER Certified Advanced Rigger, valid 5 years.",
             "- Signal Person course: $1,000, $200 deposit. Two Fridays 8 AM-3 PM. NCCER Certified Signal Person.",
             "- NCCER assessments: $150 flat per assessment, 36 crafts, Mon-Fri 8 AM-5 PM by appointment. Written and hands-on, credential recorded on the NCCER Registry.",
             "- Payment: card deposit, Klarna and Afterpay (pay in full at checkout), Zelle, in-house financing with no credit check. Deposit non-refundable; one reschedule with 48 hours' notice.",
             "- Class size: 8 seats. Individual enrollment only: no employer, crew or group training programs and no training at employer sites (an employer may pay for a student's seat).", "",
             "## Pages", ""]
    names = {"/": "Home", "/book/": "Book a class online (certification, schedule and start date; $200 deposit, assessments $150)", "/guides/": "Guides (plain-English articles)"}
    names.update(("/guides/%s/" % g["slug"], "Guide: " + g["title"]) for g in GUIDES)
    for u, p in PAGES:
        lines.append("- [%s](%s%s)" % (names.get(u, u.strip("/").replace("-", " ").replace("/", " / ").title()), BASE, u))
    lines += ["", "## Policies", "- [Privacy Policy](%s/privacy.html)" % BASE, "- [Terms & Enrollment Policy](%s/terms.html)" % BASE, "- [Accessibility Statement](%s/accessibility.html)" % BASE, ""]
    w("llms.txt", "\n".join(lines))

# ---------------------------------------------------------------- main
def main():
    write_assets()
    rewrite_index()
    build_book()
    for c in COURSES: build_course(c)
    build_assessments()
    for c in CRAFTS: build_craft(c)
    build_format_page("/weekend-express/", "3-Day Weekend Express Rigger Class in Portland, TX",
        "Get NCCER Advanced Rigger certified in one weekend. Friday through Sunday, 8 AM to 5 PM, in Portland, TX. Same credential, same instructors. $1,000, $200 deposit.",
        "img/card-rigger.jpg", "Instructor demonstrating a sling hitch on a load during an Advanced Rigger class", "Advanced Rigger · Weekend Format",
        "Certified<em>In One Weekend.</em>",
        "The full Advanced Rigger course, Friday through Sunday, 8:00 AM to 5:00 PM. Walk in Friday morning, test out Sunday, and go back to work Monday with the card.",
        "Same Course.<br>Three Days.",
        ["The 3-Day Weekend Express is the Advanced Rigger course compressed into one weekend. Nothing is cut: you cover the same lift planning, load math, sling and hardware selection, load control and hand signals, and you test out written and hands-on on Sunday.",
         "It exists for one reason: you can't take four weekdays off. Plenty of students drive in from Corpus Christi, Kingsville and the Valley on Friday morning and are certified by Sunday afternoon."],
        ["Full Advanced Rigger curriculum, Friday through Sunday", "Hands-on with real rigging hardware", "Written and practical test-out Sunday", "NCCER Certified Advanced Rigger, valid five years", "$200 holds your seat, $800 due before Friday"],
        [("When does the weekend class run?", "Friday through Sunday, 8:00 AM to 5:00 PM, starting every other Friday. Booking closes the day before."),
         ("Is it the same certification as the 4-day class?", "Yes. Same NCCER Certified Advanced Rigger credential, same instructors, same written and practical test. Only the calendar is different."),
         ("Can I still pay over time?", "Yes. Klarna, Afterpay, Zelle and in-house financing with no credit check all apply. The balance has to be paid before Friday morning."),
         ("What should I bring?", "A government-issued photo ID for NCCER testing, something to write with, and work boots for the hands-on portion.")],
        specs=[("Course price", '$1,000 <s class="was">$1,700</s>'), ("Holds your seat", "$200"), ("Schedule", "Fri – Sun · 8 AM – 5 PM"), ("Credential", "NCCER Advanced Rigger")],
        band_h2="Certified<br class=\"mbr\"> By Sunday.", crumb="Weekend Express")
    build_format_page("/night-classes/", "Night Rigging Classes for Day-Shift Crews in Portland, TX",
        "NCCER Advanced Rigger night class, Monday through Thursday 6 to 11 PM in Portland, TX. Keep your day job and get certified in four nights. $1,000, $200 deposit.",
        "img/bg-classroom.jpg", "Students in the Prime Lift Rigging Academy classroom at night", "Advanced Rigger · Night Format",
        "Work Days.<em>Certify Nights.</em>",
        "The full Advanced Rigger course, Monday through Thursday, 6:00 PM to 11:00 PM. Built for crews on days who can't give up a paycheck to get the card.",
        "Same Course.<br>After Your Shift.",
        ["The night class is the Advanced Rigger course on a schedule that doesn't cost you a week of work. Four nights, Monday through Thursday, with the same classroom instruction, hands-on rigging and Thursday test-out as the day class.",
         "Most night students are already on a crew at a plant, refinery or shipyard and need the NCCER card to move up or to get on the next turnaround. Come straight from work; boots are fine."],
        ["Full Advanced Rigger curriculum, four nights", "Monday through Thursday, 6:00 PM to 11:00 PM", "Hands-on with real rigging hardware", "Written and practical test-out Thursday night", "NCCER Certified Advanced Rigger, valid five years"],
        [("When does the night class run?", "Monday through Thursday, 6:00 PM to 11:00 PM, starting every Monday. Booking closes the day before."),
         ("Is it the same certification as the day class?", "Yes. Same NCCER Certified Advanced Rigger credential, same instructors, same written and practical test."),
         ("Can I come straight from work?", "Yes. Come in your work clothes; you'll need boots for the hands-on portion anyway."),
         ("What does it cost?", "$1,000 during our current promotion, normally $1,700. $200 holds your seat and $800 is due before Monday night. Klarna, Afterpay, Zelle and in-house financing are available.")],
        specs=[("Course price", '$1,000 <s class="was">$1,700</s>'), ("Holds your seat", "$200"), ("Schedule", "Mon – Thu · 6 – 11 PM"), ("Credential", "NCCER Advanced Rigger")],
        band_h2="Keep The Paycheck.<br class=\"mbr\"> Get The Card.", crumb="Night Classes")
    build_format_page("/rigger-recertification/", "Advanced Rigger Recertification in Portland, TX",
        "NCCER Advanced Rigger credentials are valid five years. Recertify in Portland, TX: retest for $550, or take the refresher course. Scheduled by appointment.",
        "img/testing-room.jpg", "Candidates taking a proctored NCCER assessment in the on-site testing room", "Advanced Rigger · Recertification",
        "Credential<em>Coming Due?</em>",
        "NCCER rigger credentials are valid for five years. When yours is coming up, get it renewed here in Portland before it lapses and costs you a gate pass.",
        "Don't Let It<br>Lapse.",
        ["Your NCCER Advanced Rigger credential is good for five years from the date it was issued. Contractors check the NCCER Registry, and an expired credential reads the same as no credential.",
         "If you are already working as a rigger and you know the material, you do not have to sit through the course again. Come in, take the written assessment and the hands-on practical, and the renewal goes on the Registry. Retests are scheduled by appointment so we can work around your shift.",
         "If it has been a while and you would rather go back through the material first, take the refresher. That is the full Advanced Rigger course in day, night or weekend format, ending in the same test-out."],
        ["Written assessment $275, hands-on practical $275", "$550 in total to retest, with no class time to sit through", "Scheduled by appointment, around your shift", "Refresher option: the full Advanced Rigger course, $1,000", "Renewal recorded on the NCCER Registry"],
        [("How long is an NCCER Advanced Rigger credential valid?", "Five years from the date it was issued. Check your card or the NCCER Registry for the date."),
         ("Do I have to retake the whole class?", "Not if you are already working as a rigger and you know the material. You can come in and take the written assessment and the hands-on practical without sitting through the course. If you would rather go back through the material first, take the refresher, which is the full Advanced Rigger course."),
         ("What does recertification cost?", "$275 for the written assessment and $275 for the hands-on practical, $550 in total. If you take the refresher instead, that is the Advanced Rigger course at $1,000."),
         ("When can I retest?", "By appointment. Call (361) 213-9690 with your NCCER card number and we will put you on the schedule.")],
        book="advanced",
        specs=[("Credential life", "5 years"), ("Retest", "$550"), ("Refresher class", "$1,000"), ("Schedule", "By appointment")],
        cta=cta_box("Retest Your Advanced Rigger Card", ["$275 written assessment, $275 hands-on practical.", "By appointment. Have your NCCER card number handy."], price="$550", href="/contact/", label="Request a Retest Date"),
        hero_cta=['<a class="btn btn-primary" href="/contact/">Request a Retest Date %s</a>' % I["arrow"],
                  '<a class="btn btn-ghost" href="tel:%s">%s Call %s</a>' % (BIZ["phone_raw"], I["phone"], BIZ["phone"])],
        band_primary='<a class="btn btn-primary" href="/contact/">Request a Retest Date</a>',
        band_h2="Renew It<br class=\"mbr\"> Before It Lapses.", crumb="Recertification")
    build_dates()
    build_financing()
    build_instructors()
    for p in PEOPLE: build_person(p)
    build_contact()
    build_about()
    build_reviews()
    build_faq()
    build_guides()
    build_404()
    write_sitemap()
    write_llms()
    print("built %d pages (+404), origin %s, noindex=%s" % (len(PAGES), ORIGIN, NOINDEX))

if __name__ == "__main__":
    main()
