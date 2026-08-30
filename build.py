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
import io, os, re, json, html, datetime
from content import (BIZ, COURSES, ASSESSMENT, CRAFT_GROUPS, CRAFTS, PEOPLE,
                     REVIEWS, FAQ, FINANCING, EMPLOYERS, EMPLOYERS_STATS, EMPLOYER_LOGOS,
                     GROUP_RATE_NOTE, ES, GUIDES, RETEST_POLICY, CREDENTIAL_POSTING_TIME, WHY)

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://primeliftrigging-academy.com"
PREVIEW = "https://prime-lift-rigging-academy.netlify.app"
NOINDEX = True                       # <- flip to False at launch
ORIGIN = PREVIEW if NOINDEX else BASE
YEAR = datetime.date.today().year
TODAY = datetime.date.today().isoformat()

def esc(s): return html.escape(s, quote=True)
def money(n): return "${:,}".format(n)
def w(rel, text):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)

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
    {"id": "advanced", "fmt": "day", "name": "Advanced Rigger", "label": "Weekday Day Class", "time": "Mon – Thu · 8:00 AM – 2:00 PM", "wd": MON, "n": 6},
    {"id": "advanced", "fmt": "night", "name": "Advanced Rigger", "label": "Weekday Night Class", "time": "Mon – Thu · 6:00 PM – 11:00 PM", "wd": MON, "n": 6},
    {"id": "advanced", "fmt": "weekend", "name": "Advanced Rigger", "label": "3-Day Weekend Express", "time": "Fri – Sun · 8:00 AM – 5:00 PM", "wd": FRI, "n": 6},
    {"id": "signal", "fmt": "friday", "name": "Signal Person", "label": "Two Fridays", "time": "Fridays · 8:00 AM – 3:00 PM", "wd": FRI, "n": 6},
    {"id": "assessment", "fmt": "assess", "name": "NCCER Assessments", "label": "Any Weekday", "time": "Mon – Fri · 8:00 AM – 5:00 PM", "wd": "weekday", "n": 10},
]
def next_dates(wd, n):
    """Next n start dates for a rule: wd = JS weekday number, or "weekday" for Mon-Fri."""
    d = datetime.date.today() + datetime.timedelta(days=LEAD_DAYS)
    out = []
    if wd == "weekday":
        while len(out) < n:
            if d.weekday() <= 4: out.append(d)
            d += datetime.timedelta(days=1)
        return out
    while (d.weekday() + 1) % 7 != wd: d += datetime.timedelta(days=1)
    for _ in range(n):
        out.append(d); d += datetime.timedelta(days=7)
    return out
def rules_json():
    return json.dumps(SCHEDULE_RULES, separators=(",", ":"))

# ------------------------------------------------------------------ nav
def nav(home=False):
    h = "" if home else "/"           # anchor prefix for home sections
    def course_items():
        return "".join("""
            <a class="nm-item" href="/%s/">
              <span class="nm-n idx">%02d</span>
              <span class="nm-b"><b>%s</b><span>%s</span></span>
              <span class="nm-p">%s</span>
            </a>""" % (c["slug"], i+1, esc(c["name"]), esc(sub), money(price))
            for i, (c, sub, price) in enumerate([
                (COURSES[0], "Days, nights, or the 3-day weekend express", 1000),
                (COURSES[1], "Two Fridays of class and hands-on", 1000),
                (ASSESSMENT, "Test out in 36 crafts, proctored on-site", 150)]))
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
      <span class="brand-txt">NCCER Training &amp;<br>Assessment Center</span>
    </a>
    <nav class="nav-links" aria-label="Main">
      <div class="nav-item">
        <a href="%(h)s#courses" aria-haspopup="true">Courses %(caret)s</a>
        <div class="nav-menu"><div class="nav-menu-in">%(courses)s
            <a class="nm-all" href="/class-dates/">See All Class Dates %(arrow)s</a>
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
      <a href="/employers/">Employers</a>
      <a href="/contact/">Contact</a>
    </nav>
    <div class="nav-cta">
      <a class="nav-phone" href="tel:%(tel)s" aria-label="Call %(phone)s">%(phone_i)s %(phone)s</a>
      <a class="btn btn-primary" href="%(h)s#schedule">Enroll Now</a>
      <button class="nav-burger" id="navBurger" aria-label="Open menu" aria-expanded="false" aria-controls="mnav"><span></span><span></span><span></span></button>
    </div>
  </div>
  <nav class="mnav" id="mnav" aria-label="Mobile">
    <div class="mnav-in">
      <p class="mnav-h">Courses</p>
      <a href="/advanced-rigger/"><b>Advanced Rigger</b><span>4 days · day, night or weekend</span><em>$1,000</em></a>
      <a href="/signal-person/"><b>Signal Person</b><span>Two Fridays</span><em>$1,000</em></a>
      <a href="/nccer-assessments/"><b>NCCER Assessments</b><span>Test out in 36 crafts</span><em>$150</em></a>
      <a href="/weekend-express/"><b>3-Day Weekend Express</b><span>Fri – Sun, certified by Sunday</span></a>
      <a href="/night-classes/"><b>Night Classes</b><span>Mon – Thu, 6 – 11 PM</span></a>
      <a href="/rigger-recertification/"><b>Recertification</b><span>Credential coming due?</span></a>
      <p class="mnav-h">Academy</p>
      <a href="/class-dates/"><b>Class Dates</b></a>
      <a href="/financing/"><b>Financing</b></a>
      <a href="/instructors/"><b>Instructors</b><span>Andres · Juan · Frank</span></a>
      <a href="/about/"><b>About</b></a>
      <a href="/reviews/"><b>Student Reviews</b></a>
      <a href="/faq/"><b>FAQ</b></a>
      <a href="/employers/"><b>Employers</b><span>Crew training &amp; assessments</span></a>
      <a href="/contact/"><b>Contact</b></a>
      <a href="/es/" lang="es" hreflang="es"><b>Español</b><span>Información en español</span></a>
      <div class="mnav-cta">
        <a class="btn btn-primary btn-block" href="%(h)s#schedule">Reserve Your Seat — $200</a>
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
        <a class="foot-lang" href="/es/" lang="es" hreflang="es">Español</a>
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
      <span><a href="/privacy.html" style="color:var(--muted)">Privacy</a> &middot; <a href="/terms.html" style="color:var(--muted)">Terms</a> &middot; Site by <a href="https://zonkelmedia.com" target="_blank" rel="noopener" style="color:var(--muted)">Zonkel Media</a></span>
    </div>
  </div>
</footer>
<!-- FOOTER:END -->
""" % dict(fb=BIZ["facebook"], tt=BIZ["tiktok"], gm=BIZ["gmaps"], email=BIZ["email"], tel=BIZ["phone_raw"],
           phone=BIZ["phone"], fb_i=I["fb"], tt_i=I["tiktok"], g_i=I["google"], mail_i=I["mail"], yr=YEAR, h=h)

def callbar():
    return """<div class="callbar" id="callbar">
  <a class="pri" href="tel:%s">%s Call Now</a>
  <a href="/#schedule">%s Book a Class</a>
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
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wdth,wght@62..125,400..900&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">'

def hreflang_links(url):
    """en/es alternates, only for the two pages that have a translation."""
    if url not in ("/", "/es/"): return ""
    return ('<link rel="alternate" hreflang="en" href="%s/">\n<link rel="alternate" hreflang="es" href="%s/es/">\n'
            '<link rel="alternate" hreflang="x-default" href="%s/">\n') % (ORIGIN, ORIGIN, ORIGIN)

def page(url, title, desc, body, crumbs=(), schema=(), og_image="/img/og.jpg", hero_img=None, lang="en"):
    full = ORIGIN + url
    graph = [org_schema()]
    if crumbs: graph.append(crumbs_schema([("Home", "/")] + list(crumbs)))
    graph += list(schema)
    graph.append({"@type": "WebPage", "@id": BASE + url, "url": BASE + url, "name": title,
                  "description": desc, "isPartOf": {"@id": BASE + "/#website"}, "about": {"@id": BASE + "/#org"}})
    pre = '<link rel="preload" as="image" href="%s" fetchpriority="high">' % hero_img if hero_img else ""
    return """<!DOCTYPE html>
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
<link rel="stylesheet" href="/css/site.css">
<link rel="stylesheet" href="/css/pages.css">
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
           ogimg=ORIGIN + og_image, fonts=FONTS, pre=pre, ld=ld(graph),
           nav=es_lang_links(nav()) if lang == "es" else nav(), body=body,
           footer=es_lang_links(footer()) if lang == "es" else footer(), callbar=callbar())

# On Spanish pages the language links flip to English so visitors can switch back.
def es_lang_links(html):
    return (html
        .replace('<a href="/es/" lang="es" hreflang="es"><b>Español</b><span>Información en español</span></a>',
                 '<a href="/" hreflang="en"><b>English</b><span>Volver al sitio en inglés</span></a>')
        .replace('<a class="foot-lang" href="/es/" lang="es" hreflang="es">Español</a>',
                 '<a class="foot-lang" href="/" hreflang="en">English</a>'))

# ------------------------------------------------------------ components
def crumbs_html(crumbs, home="Home"):
    items = ['<a href="/">%s</a>' % esc(home)] + ['<a href="%s">%s</a>' % (u, esc(n)) for n, u in crumbs[:-1]] + ["<span>%s</span>" % esc(crumbs[-1][0])]
    return '<nav class="crumbs" aria-label="Breadcrumb">%s</nav>' % " <i>/</i> ".join(items)

def hero_img_tag(img, alt):
    """Full-bleed hero <img>. Uses a -1200 phone variant via srcset when one exists
    on disk, so phones never download the 2400px master."""
    small = img.replace(".jpg", "-1200.jpg")
    if os.path.exists(os.path.join(ROOT, small)):
        return ('<img src="/%s" srcset="/%s 1200w, /%s 2400w" sizes="100vw" alt="%s" fetchpriority="high">'
                % (img, small, img, esc(alt)))
    return '<img src="/%s" alt="%s" fetchpriority="high">' % (img, esc(alt))

def phero(img, alt, kicker, h1, lede, crumbs, ctas=None, cls="", home="Home"):
    ctas = ctas if ctas is not None else [
        ('<a class="btn btn-primary" href="/#schedule">Reserve Your Seat — $200 %s</a>' % I["arrow"]),
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
    primary = primary or '<a class="btn btn-primary" href="/#schedule">Reserve Your Seat — $200</a>'
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

def review_card(r):
    src = ('%s<span><b>%s</b><span>5-star review on Google</span></span>' % (I["google"], esc(r["who"]))) if r["src"] == "google" \
        else ('%s<span><b>%s</b><span>Recommends on Facebook</span></span>' % (I["fb"], esc(r["who"])))
    stars = ('<span class="stars" role="img" aria-label="5 out of 5 stars">%s</span>' % (I["star"] * 5)) if r["src"] == "google" else ""
    return '<article class="rev rv"><span class="rev-quote">&ldquo;</span>%s<p>%s</p><div class="rev-who">%s</div></article>' % (stars, esc(r["text"]), src)

def rev_grid(revs):
    return '<div class="rev-grid" data-orphan="%d">%s</div>' % (len(revs) % 3, "".join(review_card(r) for r in revs))

def cta_box(title, lines, price=None, href="/#schedule", label="Pick a Start Date"):
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
      </a>""" % (p["slug"], p["img"], esc(p["alt"]), esc(p["role"]), esc(p["name"]), esc(p["bio"][0]), I["arrow"]) for p in ps)

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

def build_course(c):
    url = "/%s/" % c["slug"]
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
                 ctas=['<a class="btn btn-primary" href="/?book=%s#schedule">Pick a Start Date %s</a>' % (c["id"], I["arrow"]),
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
</div></section>""" % (sec_head("01", "The Course", "What The<br>Course Covers"), esc(c["summary"]), checks(c["learn"]),
                       cta_box("%s · %s" % (c["name"], money(c["price"])),
                               ["$%d holds your seat. Balance due before class." % c["deposit"], "Klarna, Afterpay, Zelle or in-house financing with no credit check."],
                               price=price_line, href="/?book=%s#schedule" % c["id"]))
    body += """<section class="section alt" id="formats"><div class="wrap">
  %s
  <div class="fmt-grid">%s</div>
  <p class="center-note rv"><a class="btn btn-ghost" href="/class-dates/">%s See Upcoming Dates</a></p>
</div></section>""" % (sec_head("02", "Schedules", "Built Around<br>Your Shift.", "Every format ends the same way: a written and hands-on test-out in our accredited testing room, and a credential on the NCCER Registry.", center=True), fmts, I["cal"])
    body += """<section class="section"><div class="wrap">
  %s
  <div class="who-grid">%s</div>
</div></section>""" % (sec_head("03", "Who It's For", "Who Takes<br>This Course"), who)
    body += """<section class="section how"><div class="how-bg" aria-hidden="true"><img src="/img/bg-classroom.jpg" alt="" loading="lazy"></div><div class="wrap">
  %s%s
</div></section>""" % (sec_head("04", "The Process", "Three Steps To Certified"), steps())
    body += """<section class="section"><div class="wrap">
  %s%s
</div></section>""" % (sec_head("05", "Who's Teaching You", "Your Instructors"), people_grid(teachers))
    body += """<section class="section alt"><div class="wrap">
  %s%s
  <p class="center-note rv"><a href="/faq/" class="more">All questions %s</a></p>
</div></section>""" % (sec_head("06", "Common Questions", "%s FAQ" % esc(c["name"]), center=True), faq_html(c["faq"]), I["arrow"])
    body += band(primary='<a class="btn btn-primary" href="/?book=%s#schedule">Pick a Start Date</a>' % c["id"])
    emit(url, page(url, c["meta_title"], c["meta_desc"], body, crumbs,
                   [course_schema(c, url), faq_schema(c["faq"])], hero_img="/" + c["hero"]), "0.9")

def build_assessments():
    url = "/nccer-assessments/"
    a = ASSESSMENT
    crumbs = [("Courses", "/#courses"), ("NCCER Assessments", url)]
    body = phero(a["hero"], a["hero_alt"], a["kicker"], a["h1"], a["lede"], crumbs,
                 ctas=['<a class="btn btn-primary" href="/?book=assessment#schedule">Request a Test Date %s</a>' % I["arrow"],
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
                       checks(["Book a date online or call the office. Bringing a crew? Call for group scheduling.",
                               "Bring a government-issued photo ID. NCCER requires it.",
                               "Written assessment, then the hands-on performance verification where the craft calls for one.",
                               "Pass and your credential goes on the NCCER Registry.",
                               "One flat $150 per assessment, paid in full when you book."]),
                       cta_box("NCCER Assessment · $150", ["Monday through Friday, 8 AM to 5 PM, by appointment.", "Bringing a crew? Call the office for group scheduling."], price="$150", href="/?book=assessment#schedule", label="Request a Test Date"))
    body += """<section class="section alt" id="crafts"><div class="wrap">
  %s%s
</div></section>""" % (sec_head("02", "36 Crafts", "Crafts We Assess", "Pick your craft for what the assessment covers and who it's for. Don't see yours? Call the office; more crafts are available on request.", center=True), craft_groups_html())
    body += """<section class="section"><div class="wrap">
  %s%s
</div></section>""" % (sec_head("03", "Common Questions", "Assessment FAQ", center=True), faq_html(a["faq"]))
    body += band(h2="Already Know<br class=\"mbr\"> The Work?", p="Book your assessment date, bring your ID, and leave with a credential the whole industry recognizes.",
                 primary='<a class="btn btn-primary" href="/?book=assessment#schedule">Request a Test Date</a>')
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
                 ctas=['<a class="btn btn-primary" href="/?book=assessment#schedule">Request a Test Date %s</a>' % I["arrow"],
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
                               "Crews a contractor needs verified before a turnaround",
                               "Anyone hired on the condition of getting the card"]),
                       cta_box("%s · $150" % short, ["Written and hands-on, proctored on-site.", "Monday through Friday, 8 AM to 5 PM, by appointment."], price="$150", href="/?book=assessment#schedule", label="Request a Test Date"))
    body += """<section class="section how"><div class="how-bg" aria-hidden="true"><img src="/img/bg-classroom.jpg" alt="" loading="lazy"></div><div class="wrap">
  %s
  <div class="how-grid">
    <div class="how-card rv"><span class="idx">01</span><h3>Book Your Date</h3><p>Online in two minutes, or call the office. Bringing a crew? Call for group scheduling.</p></div>
    <div class="how-card rv"><span class="idx">02</span><h3>Test In Portland</h3><p>Written assessment first, then the hands-on performance verification where the craft calls for one.</p></div>
    <div class="how-card rv"><span class="idx">03</span><h3>Get The Credential</h3><p>Pass and it's recorded on the NCCER Registry, where every contractor in the country can verify it.</p></div>
  </div>
</div></section>""" % sec_head("02", "How It Works", "Three Steps To The Card")
    body += """<section class="section alt"><div class="wrap split">
  <div class="rv">%s%s</div>
  <div class="rv"><h3 class="h-sub">Other crafts in %s</h3><ul class="craft-list">%s</ul><p style="margin-top:18px"><a class="more" href="/nccer-assessments/#crafts">All 36 crafts %s</a></p></div>
</div></section>""" % (sec_head("03", "Common Questions", "%s FAQ" % esc(short)), faq_html(faq), esc(gname), sib, I["arrow"])
    body += band(h2="Already Know<br class=\"mbr\"> The Work?", p="Book your %s assessment, bring your ID, and leave with a credential the whole industry recognizes." % short,
                 primary='<a class="btn btn-primary" href="/?book=assessment#schedule">Request a Test Date</a>')
    emit(url, page(url, title, desc, body, crumbs,
                   [service_schema("NCCER %s Assessment" % name, desc, url), faq_schema(faq)], hero_img="/img/testing-room.jpg"), "0.6")

def build_format_page(url, title, desc, hero, alt, kicker, h1, lede, idx_title, paras, checks_list, faq, book="advanced", specs=None, band_h2=None, crumb=None):
    crumbs = [("Advanced Rigger", "/advanced-rigger/"), (crumb or title.split(" (")[0].split(" in ")[0], url)]
    body = phero(hero, alt, kicker, h1, lede, crumbs,
                 ctas=['<a class="btn btn-primary" href="/?book=%s#schedule">Pick a Start Date %s</a>' % (book, I["arrow"]),
                       '<a class="btn btn-ghost" href="tel:%s">%s Call %s</a>' % (BIZ["phone_raw"], I["phone"], BIZ["phone"])])
    if specs: body += specbar(specs)
    body += """<section class="section"><div class="wrap split">
  <div class="prose rv">%s%s<h3 class="h-sub">What's included</h3>%s</div>
  %s
</div></section>""" % (sec_head("01", "The Format", idx_title), "".join('<p class="lede">%s</p>' % esc(p) for p in paras), checks(checks_list),
                       cta_box("Advanced Rigger · $1,000", ["$200 holds your seat. Balance due before class.", "Klarna, Afterpay, Zelle or in-house financing."], price='$1,000 <s class="was">$1,700</s>', href="/?book=%s#schedule" % book))
    body += """<section class="section alt"><div class="wrap">%s%s</div></section>""" % (sec_head("02", "Common Questions", "Before You Enroll", center=True), faq_html(faq))
    body += """<section class="section"><div class="wrap">%s%s</div></section>""" % (sec_head("03", "Who's Teaching You", "Your Instructors"), people_grid(["andres-herrera", "frank-torres"]))
    body += band(h2=band_h2 or "Building Skills. Bettering Futures.", primary='<a class="btn btn-primary" href="/?book=%s#schedule">Pick a Start Date</a>' % book)
    emit(url, page(url, title, desc, body, crumbs, [faq_schema(faq)], hero_img="/" + hero), "0.8")

def build_dates():
    url = "/class-dates/"
    crumbs = [("Class Dates", url)]
    body = phero("img/bg-classroom.jpg", "Students in the Prime Lift Rigging Academy classroom", "Upcoming Classes",
                 "Class Dates<em>&amp; Schedules</em>",
                 "Advanced Rigger starts every Monday (days or nights) and every Friday (weekend express). Signal Person starts every Friday. Assessments run any weekday. Booking closes the day before a class starts.", crumbs)
    body += specbar([("Advanced Rigger", "Mon – Thu · 8 AM – 2 PM"), ("Night class", "Mon – Thu · 6 – 11 PM"), ("Weekend express", "Fri – Sun · 8 AM – 5 PM"), ("Signal Person", "Fridays · 8 AM – 3 PM")])
    body += ("""<section class="section"><div class="wrap">
  %s
  <div class="sched-list" id="schedList"></div>
  <p class="center-note rv" style="margin-top:30px">Seats are capped at 8 per class. Pick a date to reserve yours with a $200 deposit, or <a href="tel:%s" style="color:var(--accent)">call %s</a> to book a crew.</p>
</div></section>
<script>
/* Recurrence rules come from SCHEDULE_RULES in build.py (shared with the course pages). Change the rule there, never a list of dates. */
(function(){
  const SEATS=8, LEAD=1, MON=1, FRI=5;
  const MONS=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], DOW=["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
  const iso=d=>d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");
  function first(){ const d=new Date(); d.setHours(0,0,0,0); d.setDate(d.getDate()+LEAD); return d; }
  function every(wd,n){ const d=first(),o=[]; while(d.getDay()!==wd) d.setDate(d.getDate()+1); for(let i=0;i<n;i++){ o.push(new Date(d)); d.setDate(d.getDate()+7);} return o; }
  function weekdays(n){ const d=first(),o=[]; while(o.length<n){ if(d.getDay()>=MON&&d.getDay()<=FRI) o.push(new Date(d)); d.setDate(d.getDate()+1);} return o; }
  const P=__RULES__.map(r=>Object.assign({},r,{dates:r.wd==="weekday"?weekdays(r.n):every(r.wd,r.n)}));
  document.getElementById("schedList").innerHTML=P.map((p,i)=>`
    <div class="sched-block rv">
      <div class="sched-head"><span class="idx">${String(i+1).padStart(2,"0")}</span><div><b>${p.name}</b><span>${p.label} · ${p.time}</span></div></div>
      <div class="date-grid">${p.dates.map(d=>`
        <a class="date" href="/?book=${p.id}&fmt=${p.fmt}&date=${iso(d)}#schedule">
          <span class="date-cal"><em>${MONS[d.getMonth()]}</em><b>${d.getDate()}</b></span>
          <span class="date-info"><b>${DOW[d.getDay()]}</b><span>Starts ${MONS[d.getMonth()]} ${d.getDate()}</span></span>
          <span class="seats"><b>${SEATS}</b><span>seats/class</span></span>
        </a>`).join("")}</div>
    </div>`).join("");
  document.querySelectorAll("#schedList .rv").forEach(el=>el.classList.add("in"));
})();
</script>""" % (sec_head("01", "Pick A Date", "Next Classes<br>In Portland, TX", "Dates roll forward every week. Tap one to hold it.", center=True), BIZ["phone_raw"], BIZ["phone"])).replace("__RULES__", rules_json())
    body += band(primary='<a class="btn btn-primary" href="/#schedule">Reserve Your Seat — $200</a>')
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
    <p style="margin-top:26px"><a class="btn btn-ghost" href="/employers/">Crew Training For Employers %s</a></p>
  </div>
  %s
</div></section>""" % (sec_head("02", "Employer-Sponsored Training", "Your Employer<br>Can Pay."),
                       checks(["Pick \"My employer is paying\" on the booking form and add their contact",
                               "The office coordinates payment with your company",
                               "Employers can book whole crews: up to 8 seats per class, day, night or weekend",
                               "Crews test out on site and credentials post to the NCCER Registry"]),
                       I["arrow"],
                       cta_box("Sending A Crew?", ["Company bookings for up to 8 students and crew assessments, with one point of contact at the office.", "Use the crew quote form and the office will call you back."], href="/employers/#quote", label="Request a Crew Quote"))
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
        <a class="btn btn-primary" href="/#schedule">Reserve Your Seat — $200 %s</a>
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
    body = phero("img/storefront-door.jpg", "Prime Lift Rigging Academy Training and Assessment Center entrance in Portland, TX", "Find Us",
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
    <p class="lede">Questions about a class, a crew booking, an assessment craft you don't see listed, or paying by Zelle? Send it here and the office will call or email you back during business hours. Ready to book? <a href="/#schedule" style="color:var(--accent)">Reserve online</a> and skip the wait.</p>
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
        <option>Recertification</option><option>Booking a crew</option><option>Financing or paying by Zelle</option><option>Something else</option>
      </select></label>
    <label class="field"><span>Your message</span><textarea name="notes" rows="4" required></textarea></label>
    <input type="hidden" name="page" value="/contact/">
    <button class="btn btn-primary btn-block" type="submit">Send Message %s</button>
    <p class="pay-legal">The office answers during business hours, Monday through Friday. For anything urgent, call %s.</p>
  </form>
</div></section>""" % (sec_head("01", "Send A Message", "Talk To<br>The Office"), I["arrow"], BIZ["phone"])
    body += band(h2="Or Just<br class=\"mbr\"> Book It.", p="No phone tag. Pick your class, pick a start date, and hold your seat with $200 in about two minutes.")
    emit(url, page(url, "Contact · Prime Lift Rigging Academy, Portland, TX", "Call (361) 413-0160, email primelift26@gmail.com, or visit 1605 US Hwy 181 Frontage Rd, Suite A, Portland, TX 78374. Mon–Fri 7 AM to 5 PM.", body, crumbs, hero_img="/img/storefront-door.jpg"), "0.7")

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
                               "Company bookings for crews of up to 8"]),
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
                       '<a class="btn btn-ghost" href="/#schedule">Reserve Your Seat %s</a>' % I["arrow"]])
    body += """<section class="section"><div class="wrap">%s%s
  <div class="gal rv">
    <figure><img src="/img/grad-johnny.jpg" alt="Prime Lift graduate holding an NCCER Certified Advanced Rigger certificate" loading="lazy"><figcaption>Certified Advanced Rigger</figcaption></figure>
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
                 ctas=['<a class="btn btn-primary" href="/#schedule">Reserve Your Seat — $200 %s</a>' % I["arrow"],
                       '<a class="btn btn-ghost" href="/contact/#message">Ask A Question</a>'])
    body += """<section class="section"><div class="wrap">%s</div></section>""" % faq_html(FAQ)
    body += band()
    emit(url, page(url, "FAQ · NCCER Rigging Classes & Assessments in Portland, TX", "Course length, cost, the $200 deposit, Klarna and Afterpay, no-credit-check financing, NCCER credentials, testing out, crew bookings and where to find us.", body, crumbs, [faq_schema(FAQ)], hero_img="/img/bg-classroom.jpg"), "0.7")


def next_dates_strip(cid):
    """Next 3 start dates per format, from SCHEDULE_RULES. Refreshed client-side (site.js) from the same rule."""
    rows = []
    for r in SCHEDULE_RULES:
        if r["id"] != cid: continue
        links = "".join('<a class="nd-date" href="/?book=%s&amp;fmt=%s&amp;date=%s#schedule">%s</a>' % (
            r["id"], r["fmt"], d.isoformat(), d.strftime("%a, %b ") + str(d.day)) for d in next_dates(r["wd"], 3))
        rows.append('<div class="nd-row" data-wd="%s" data-lead="%d" data-book="%s" data-fmt="%s"><b>%s</b><div class="nd-dates">%s</div></div>' % (
            r["wd"], LEAD_DAYS, r["id"], r["fmt"], esc(r["label"]), links))
    return '<div class="nextdates"><div class="wrap nextdates-in"><p class="nd-h">Next start dates</p>%s<a class="more nd-all" href="/class-dates/">See all dates %s</a></div></div>' % ("".join(rows), I["arrow"])

def build_employers():
    url = "/employers/"
    e = EMPLOYERS
    crumbs = [("Employers", url)]
    body = phero("img/hero-cranes.jpg", "Two mobile cranes rigging at a Coastal Bend refinery turnaround at sunset", e["kicker"], e["h1"], e["lede"], crumbs,
                 ctas=['<a class="btn btn-primary" href="#quote">Request a Crew Quote %s</a>' % I["arrow"],
                       '<a class="btn btn-ghost" href="tel:%s">%s Call %s</a>' % (BIZ["phone_raw"], I["phone"], BIZ["phone"])])
    body += specbar(e["specs"])
    # optional proof: rendered only when the client gives us numbers
    stats = [(v, lbl) for k, lbl, v in [("crews_trained", "crews trained", EMPLOYERS_STATS["crews_trained"]),
                                         ("credentials_issued", "credentials posted to the Registry", EMPLOYERS_STATS["credentials_issued"]),
                                         ("employers_served", "Coastal Bend employers served", EMPLOYERS_STATS["employers_served"])] if v]
    stat_html = ('<div class="stat-row rv">%s</div>' % "".join('<div class="stat"><b>%s</b><span>%s</span></div>' % (esc(str(v)), esc(l)) for v, l in stats)) if stats else ""
    logos = ('<p class="center-note rv">Crews we have trained: %s</p>' % esc(", ".join(EMPLOYER_LOGOS))) if EMPLOYER_LOGOS else ""
    cta_lines = ["Advanced Rigger $1,000 · Signal Person $1,000 · Assessments $150 per person.", "Classes capped at 8. Larger crews run across sessions."]
    if GROUP_RATE_NOTE: cta_lines.append(GROUP_RATE_NOTE)
    body += """<section class="section"><div class="wrap split">
  <div class="prose rv">
    %s
    <p class="lede">A crew that trains here tests here. There is no second trip to a third-party site and no waiting on someone else's calendar: the written and practical test-out happens in our on-site NCCER accredited assessment center, and passing credentials go on the NCCER Registry where your safety department verifies them.</p>
    <h3 class="h-sub">Why crews train here</h3>
    %s
    %s%s
  </div>
  %s
</div></section>""" % (sec_head("01", "For Employers", "Train And Test<br>In One Building."), checks(e["why"]), stat_html, logos,
                       cta_box("Train Your Crew Here", cta_lines, href="#quote", label="Request a Crew Quote"))
    steps_html = '<div class="how-grid">%s</div>' % "".join('<div class="how-card rv"><span class="idx">%02d</span><h3>%s</h3><p>%s</p></div>' % (i+1, t, esc(d)) for i, (t, d) in enumerate(e["steps"]))
    body += """<section class="section how"><div class="how-bg" aria-hidden="true"><img src="/img/bg-classroom.jpg" alt="" loading="lazy"></div><div class="wrap">
  %s%s
</div></section>""" % (sec_head("02", "How It Works", "Three Steps To<br>A Credentialed Crew"), steps_html)
    opts = "".join("<option>%s</option>" % esc(h) for h in e["headcounts"])
    chks = "".join('<label class="chk"><input type="checkbox" name="training" value="%s"><span>%s</span></label>' % (esc(t), esc(t)) for t in e["training_options"])
    body += """<section class="section alt" id="quote"><div class="wrap split">
  <div class="rv">
    %s
    <p class="lede">Tell us the headcount, the credential and when you need the crew back on the job. The office will call you back during business hours with dates and a total. Prefer the phone? Call <a href="tel:%s" style="color:var(--accent)">%s</a> and ask for group scheduling.</p>
  </div>
  <form class="cform rv" name="employer-quote" method="POST" data-netlify="true" netlify-honeypot="bot-field" action="/thanks.html">
    <input type="hidden" name="form-name" value="employer-quote">
    <p class="sr"><label>Don't fill this out: <input name="bot-field"></label></p>
    <label class="field"><span>Company</span><input type="text" name="company" autocomplete="organization" required></label>
    <div class="two-up">
      <label class="field"><span>Your name</span><input type="text" name="contact_name" autocomplete="name" required></label>
      <label class="field"><span>Phone</span><input type="tel" name="phone" autocomplete="tel" required></label>
    </div>
    <label class="field"><span>Email</span><input type="email" name="email" autocomplete="email"></label>
    <label class="field"><span>How many people?</span><select name="headcount">%s</select></label>
    <fieldset class="field chkgroup"><legend><span>Training needed</span></legend><div class="chkgroup-in">%s</div></fieldset>
    <label class="field"><span>Target date or window</span><input type="text" name="target_date" placeholder="e.g. week of Oct 5, before the fall turnaround"></label>
    <label class="field"><span>Notes</span><textarea name="notes" rows="4" placeholder="Shift, site requirements, credentials expiring…"></textarea></label>
    <input type="hidden" name="page" value="/employers/">
    <button class="btn btn-primary btn-block" type="submit">Request a Crew Quote %s</button>
    <p class="pay-legal">The office answers during business hours, Monday through Friday. Nothing is booked or charged until you confirm dates with the office.</p>
  </form>
</div></section>""" % (sec_head("03", "Crew Quote", "Get Dates<br>For Your Crew"), BIZ["phone_raw"], BIZ["phone"], opts, chks, I["arrow"])
    body += """<section class="section"><div class="wrap">
  %s%s
  <p class="center-note rv"><a href="/faq/" class="more">All questions %s</a></p>
</div></section>""" % (sec_head("04", "Common Questions", "Employer FAQ", center=True), faq_html(e["faq"]), I["arrow"])
    body += band(h2="Get The Whole Crew<br class=\"mbr\"> Credentialed.", p="One call to the office, one point of contact, and your crew trains and tests in the same building in Portland.",
                 primary='<a class="btn btn-primary" href="#quote">Request a Crew Quote</a>')
    schema = [{"@type": "Service", "name": "Crew Training and NCCER Assessments for Employers", "serviceType": "Group craft training and NCCER assessment",
               "description": e["meta_desc"], "url": BASE + url, "provider": {"@id": BASE + "/#org"},
               "areaServed": {"@type": "State", "name": "Texas"},
               "audience": {"@type": "BusinessAudience", "name": "Employers, contractors, refineries and port operators in the Coastal Bend"},
               "availableChannel": {"@type": "ServiceChannel", "serviceUrl": BASE + url + "#quote", "servicePhone": BIZ["phone_raw"]}},
              faq_schema(e["faq"])]
    emit(url, page(url, e["meta_title"], e["meta_desc"], body, crumbs, schema, hero_img="/img/hero-cranes.jpg"), "0.8")

def build_es():
    url = "/es/"
    s = ES
    crumbs = [("Español", url)]
    L = s["labels"]
    body = phero(COURSES[0]["hero"], "Instructor demostrando un enganche de eslinga durante la clase de Advanced Rigger", s["kicker"], s["h1"], s["lede"], crumbs,
                 ctas=['<a class="btn btn-primary" href="/?book=advanced#schedule">%s %s</a>' % (esc(s["enroll"]), I["arrow"]),
                       '<a class="btn btn-ghost" href="tel:%s">%s %s %s</a>' % (BIZ["phone_raw"], I["phone"], esc(s["call"]), BIZ["phone"])], home="Inicio")
    body += specbar(s["specs"])
    def fmt_cards(fmts):
        return '<div class="fmt-grid">%s</div>' % "".join('<div class="fmt-card rv"><span class="idx">%02d</span><b>%s</b><span class="fmt-when">%s · %s</span><p>%s</p></div>' % (
            i+1, esc(n), esc(wh), esc(t), esc(note)) for i, (n, wh, t, note) in enumerate(fmts))
    a, sg = s["advanced"], s["signal"]
    body += """<section class="section"><div class="wrap split">
  <div class="prose rv">
    %s
    <h3 class="h-sub">%s <span class="idx" style="font-size:.7em;margin-left:8px">%s <s class="was">%s</s></span></h3>
    <p class="lede">%s</p>
    <p><strong style="color:#DCDAD6">%s:</strong> %s</p>
    <p>%s</p>
    <h4 class="h-sub" style="font-size:19px;margin-top:22px">%s</h4>
    %s
    <h4 class="h-sub" style="font-size:19px">%s</h4>
    %s
    <h3 class="h-sub" style="margin-top:44px">%s <span class="idx" style="font-size:.7em;margin-left:8px">%s</span></h3>
    <p class="lede">%s</p>
    <p><strong style="color:#DCDAD6">%s:</strong> %s</p>
    <p>%s</p>
    <h4 class="h-sub" style="font-size:19px">%s</h4>
    %s
  </div>
  <aside class="cta-box rv">
    <span class="cta-price">$1,000 <s class="was">$1,700</s></span><b>Advanced Rigger</b>
    <p>$200 aparta su lugar. El saldo se paga antes de la clase.</p>
    <p>Klarna, Afterpay, Zelle o financiamiento interno sin revisión de crédito.</p>
    <a class="btn btn-primary btn-block" href="/?book=advanced#schedule">%s</a>
    <a class="btn btn-ghost btn-block" href="tel:%s">%s %s %s</a>
    <a class="more" href="/class-dates/">%s %s</a>
  </aside>
</div></section>""" % (sec_head("01", s["courses_eyebrow"], s["courses_h2"]),
                       esc(a["name"]), a["price"], a["was"], esc(a["summary"]), esc(L["cred"]), esc(a["cred"]), esc(a["deposit"]),
                       esc(L["learn"]), checks(a["learn"]), esc(L["formats"]), fmt_cards(a["formats"]),
                       esc(sg["name"]), sg["price"], esc(sg["summary"]), esc(L["cred"]), esc(sg["cred"]), esc(sg["deposit"]), esc(L["formats"]), fmt_cards(sg["formats"]),
                       esc(s["enroll"]), BIZ["phone_raw"], I["phone"], esc(s["call"]), BIZ["phone"], esc(L["all_dates"]), I["arrow"])
    groups = []
    for gid, gname in s["groups"]:
        cs = [c for c in CRAFTS if c[2] == gid]
        if not cs: continue
        groups.append('<div class="cgroup rv"><h3>%s</h3><ul class="craft-list">%s</ul></div>' % (esc(gname).replace("|", '<br class="mbr">'), "".join(
            '<li><a href="/nccer-assessments/%s/" hreflang="en">%s%s</a></li>' % (sl, I["arrow"], esc(craft_short(n))) for sl, n, g, bl, cv in cs)))
    body += """<section class="section alt" id="evaluaciones"><div class="wrap">
  %s
  <div class="cgroups">%s</div>
  <p class="center-note rv"><a class="btn btn-primary" href="/?book=assessment#schedule">Solicitar fecha de evaluación</a></p>
</div></section>""" % (sec_head("02", s["assess_eyebrow"], s["assess_h2"], s["assess_lede"], center=True), "".join(groups))
    cards = "".join('<div class="fin-card rv"><span class="idx">%02d</span><b>%s</b><span>%s</span><em class="fin-tag">%s</em></div>' % (i+1, esc(t), esc(d), esc(tag)) for i, (t, d, tag) in enumerate(s["financing"]))
    body += """<section class="section" id="pagos"><div class="wrap">
  %s
  <div class="fin-cards fin-cards-3">%s</div>
  <div class="fin-note rv" style="max-width:760px;margin:30px auto 0">%s</div>
</div></section>""" % (sec_head("03", s["fin_eyebrow"], s["fin_h2"], center=True), cards, esc(s["fin_note"]))
    team = "".join("""
      <a class="person rv" href="/instructors/%s/" hreflang="en">
        <div class="person-img"><img src="/%s" alt="%s" loading="lazy"></div>
        <div class="person-body"><span class="person-role">%s</span><h3>%s</h3><span class="person-more">Ver perfil (en inglés) %s</span></div>
      </a>""" % (p["slug"], p["img"], esc(p["alt"]), esc(s["roles"][p["slug"]]), esc(p["name"]), I["arrow"]) for p in PEOPLE)
    body += """<section class="section alt" id="instructores"><div class="wrap">%s<div class="team-grid">%s</div></div></section>""" % (
        sec_head("04", s["team_eyebrow"], s["team_h2"], center=True), team)
    body += """<section class="section" id="ubicacion"><div class="wrap">
  %s
  <div class="contact-grid">
  <div class="rv">
    <ul class="loc-list">
      <li>%s<div><b>%s</b><span>%s<br>%s, %s %s</span></div></li>
      <li>%s<div><b>%s</b><span>%s<br><em>%s</em></span></div></li>
      <li>%s<div><b>%s</b><a href="tel:%s">%s</a></div></li>
      <li>%s<div><b>%s</b><a href="mailto:%s">%s</a></div></li>
    </ul>
    <div class="contact-links">
      <a class="btn btn-ghost" href="%s" target="_blank" rel="noopener">%s %s</a>
      <a class="btn btn-primary" href="/?book=advanced#schedule">%s</a>
    </div>
  </div>
  <div class="map rv"><iframe title="Mapa a Prime Lift Rigging Academy, %s" src="%s" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe></div>
  </div>
</div></section>""" % (sec_head("05", s["visit_eyebrow"], s["visit_h2"], s["visit_lede"], center=True),
                       I["pin"], esc(L["center"]), esc(BIZ["street"]), BIZ["city"], BIZ["state"], BIZ["zip"],
                       I["clock"], esc(L["hours"]), esc(s["hours"]), esc(s["hours_note"]),
                       I["phone"], esc(L["phone"]), BIZ["phone_raw"], BIZ["phone"],
                       I["mail"], esc(L["email"]), BIZ["email"], BIZ["email"],
                       BIZ["gmaps"], I["pin"], esc(L["directions"]), esc(L["book"]), esc(FULL_ADDR), BIZ["map_embed"])
    body += band(h2=s["band_h2"], p=s["band_p"], primary='<a class="btn btn-primary" href="/?book=advanced#schedule">%s</a>' % esc(s["enroll"]),
                 eyebrow=s["band_eyebrow"], call=s["call"])
    emit(url, page(url, s["title"], s["desc"], body, crumbs, hero_img="/" + COURSES[0]["hero"], lang="es"), "0.8")

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
                 ctas=['<a class="btn btn-primary" href="/#schedule">Reserve Your Seat — $200 %s</a>' % I["arrow"],
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
<div class="hero-cta"><a class="btn btn-primary" href="/#schedule">Pick a Start Date</a><a class="btn btn-ghost" href="tel:%s">%s Call %s</a></div></aside>
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
    # head: robots + canonical + og origin + schema
    s = re.sub(r'<meta name="robots"[^>]*>', '<meta name="robots" content="noindex, nofollow">' if NOINDEX else '<meta name="robots" content="index, follow, max-image-preview:large">', s)
    s = re.sub(r'https://(?:jzonkel1\.github\.io/prime-lift-rigging-academy|prime-lift-rigging-academy\.netlify\.app|primeliftrigging-academy\.com)/', ORIGIN + "/", s)
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
.mnav{
  position:fixed; inset:0; top:0; z-index:70; display:none; overflow:auto;
  background:rgba(10,10,12,.985); backdrop-filter:blur(14px);
  padding-top:96px; -webkit-overflow-scrolling:touch;
}
body.mnav-open .mnav{display:block; animation:fade .2s ease}
body.mnav-open{overflow:hidden}
body.mnav-open .nav{background:var(--ink); z-index:80}
.mnav-in{padding:0 var(--pad) 40px; max-width:560px; margin-inline:auto}
.mnav-h{font-family:var(--f-display); font-weight:700; font-size:10.5px; letter-spacing:.24em; text-transform:uppercase; color:var(--accent); margin:26px 0 6px; padding-bottom:10px; border-bottom:1px solid var(--edge)}
.mnav-in>a{display:grid; grid-template-columns:1fr auto; align-items:center; gap:2px 12px; padding:14px 4px; border-bottom:1px solid var(--edge)}
.mnav-in>a b{font-family:var(--f-head); font-weight:400; text-transform:uppercase; font-size:21px; letter-spacing:.012em; line-height:1.05}
.mnav-in>a span{grid-column:1; font-size:13px; color:var(--muted-2); line-height:1.4}
.mnav-in>a em{grid-column:2; grid-row:1/3; font-style:normal; font-family:var(--f-fig); font-stretch:125%; font-weight:700; font-size:14px; color:var(--accent)}
.mnav-cta{display:grid; gap:10px; margin-top:28px}
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
.guide-body a{color:var(--accent)}
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
"""

SITE_JS = r"""
/* Prime Lift — shared page script (generated by build.py). Nav, mobile menu,
   reveal-on-scroll, FAQ accordions and the sticky call bar for inner pages. */
(function(){
  const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const nav=$("#nav"), burger=$("#navBurger"), callbar=$("#callbar");
  const home=!!$(".hero");            /* the home page keeps its own scroll logic */

  if(burger){
    burger.addEventListener("click",()=>{
      const open=document.body.classList.toggle("mnav-open");
      burger.setAttribute("aria-expanded",open?"true":"false");
      burger.setAttribute("aria-label",open?"Close menu":"Open menu");
    });
    $$("#mnav a").forEach(a=>a.addEventListener("click",()=>{ document.body.classList.remove("mnav-open"); burger.setAttribute("aria-expanded","false"); }));
    document.addEventListener("keydown",e=>{ if(e.key==="Escape"&&document.body.classList.contains("mnav-open")) burger.click(); });
  }

  if(!home){
    /* no layout reads inside the handler: just scrollY, which is free */
    let ticking=false;
    function paint(){
      const y=window.scrollY;
      if(nav) nav.classList.toggle("stuck",y>40);
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

  /* course pages: the "next start dates" strip is rendered at build time from
     SCHEDULE_RULES in build.py; recompute from today's date so it never goes
     stale between builds. Same rule: next N occurrences of the weekday, from
     tomorrow (booking closes the day before). */
  const MONS=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], DOWS=["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
  const iso=d=>d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");
  $$(".nd-row").forEach(row=>{
    const wd=+row.dataset.wd; if(isNaN(wd)) return;
    const d=new Date(); d.setHours(0,0,0,0); d.setDate(d.getDate()+(+row.dataset.lead||1));
    while(d.getDay()!==wd) d.setDate(d.getDate()+1);
    $$(".nd-date",row).forEach((a,i)=>{
      const x=new Date(d); x.setDate(d.getDate()+7*i);
      a.href="/?book="+row.dataset.book+"&fmt="+row.dataset.fmt+"&date="+iso(x)+"#schedule";
      a.textContent=DOWS[x.getDay()]+", "+MONS[x.getMonth()]+" "+x.getDate();
    });
  });
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
     The widget's bubble lives in an open shadow root with inline bottom:20px. */
  function lift(){
    var tries = 0;
    var cb = document.getElementById("callbar");
    function place(){
      var host = document.querySelector("chat-widget"), sr = host && host.shadowRoot;
      var box = sr && sr.getElementById("lc_text-widget"), btn = sr && sr.getElementById("lc_text-widget--btn");
      if (!box || !btn) { if (tries++ < 60) setTimeout(place, 500); return; }
      var mobile = window.innerWidth <= 900, up = mobile && cb && cb.classList.contains("show");
      host.style.visibility = (mobile && !up) ? "hidden" : "visible";
      var b = up ? "78px" : "20px";
      box.style.bottom = b; btn.style.bottom = b;
    }
    place();
    if (cb) new MutationObserver(place).observe(cb, {attributes:true, attributeFilter:["class"]});
    window.addEventListener("resize", place, {passive:true});
  }
  ["scroll","pointerdown","touchstart","keydown"].forEach(function(e){ window.addEventListener(e, load, {passive:true, once:true}); });
  setTimeout(load, 6000);
})();
"""

def write_assets():
    w("css/pages.css", PAGES_CSS.lstrip("\n"))
    w("js/site.js", SITE_JS.lstrip("\n"))

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
             "- Class size: 8 seats. Crew and employer bookings at the Portland center (company bookings up to 8 students, crew assessments); no training at employer sites. No Spanish-language instruction; a Spanish-language summary page exists at /es/.", "",
             "## Pages", ""]
    names = {"/": "Home and online booking", "/employers/": "Crew training for employers (company bookings up to 8, crew assessments, quote form)",
             "/es/": "Resumen en español (Spanish-language summary of courses, assessments, financing, location)", "/guides/": "Guides (plain-English articles)"}
    names.update(("/guides/%s/" % g["slug"], "Guide: " + g["title"]) for g in GUIDES)
    for u, p in PAGES:
        lines.append("- [%s](%s%s)" % (names.get(u, u.strip("/").replace("-", " ").replace("/", " / ").title()), BASE, u))
    lines += ["", "## Policies", "- [Privacy Policy](%s/privacy.html)" % BASE, "- [Terms & Enrollment Policy](%s/terms.html)" % BASE, ""]
    w("llms.txt", "\n".join(lines))

# ---------------------------------------------------------------- main
def main():
    write_assets()
    rewrite_index()
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
        [("When does the weekend class run?", "Friday through Sunday, 8:00 AM to 5:00 PM, starting every Friday. Booking closes the day before."),
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
        "NCCER Advanced Rigger credentials are valid five years. Recertify in Portland, TX: call the office to schedule your retest or a refresher class.",
        "img/testing-room.jpg", "Candidates taking a proctored NCCER assessment in the on-site testing room", "Advanced Rigger · Recertification",
        "Credential<em>Coming Due?</em>",
        "NCCER rigger credentials are valid for five years. When yours is coming up, get it renewed here in Portland before it lapses and costs you a gate pass.",
        "Don't Let It<br>Lapse.",
        ["Your NCCER Advanced Rigger credential is good for five years from the date it was issued. Contractors check the NCCER Registry, and an expired credential reads the same as no credential.",
         "Call the office with your NCCER card number and we'll tell you exactly what you need: a retest in our accredited assessment center, or a refresher class first if it's been a while. Either way you test out in the same building and the renewal is recorded on the Registry."],
        ["Written and practical retest in our accredited testing room", "Refresher option: the full Advanced Rigger class in day, night or weekend format", "Renewal recorded on the NCCER Registry", "Crews with credentials expiring together can book as a group"],
        [("How long is an NCCER Advanced Rigger credential valid?", "Five years from the date it was issued. Check your card or the NCCER Registry for the date."),
         ("Do I have to retake the whole class?", "Not necessarily. Call the office with your card number and we'll tell you whether you can go straight to the retest or should take a refresher first."),
         ("What does recertification cost?", "It depends on whether you retest or retake the course. Call (361) 413-0160 for a quote; the Advanced Rigger course is $1,000 if you choose the refresher."),
         ("Can you recertify my whole crew?", "Yes. If several credentials expire together, call and we'll schedule the crew as a group, up to 8 per session.")],
        book="advanced",
        specs=[("Credential life", "5 years"), ("Retest", "Written + hands-on"), ("Refresher class", "$1,000"), ("Schedule", "Call the office")],
        band_h2="Renew It<br class=\"mbr\"> Before It Lapses.", crumb="Recertification")
    build_dates()
    build_financing()
    build_instructors()
    for p in PEOPLE: build_person(p)
    build_contact()
    build_about()
    build_reviews()
    build_faq()
    build_employers()
    build_es()
    build_guides()
    build_404()
    write_sitemap()
    write_llms()
    print("built %d pages (+404), origin %s, noindex=%s" % (len(PAGES), ORIGIN, NOINDEX))

if __name__ == "__main__":
    main()
