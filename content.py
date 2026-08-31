# -*- coding: utf-8 -*-
"""
Prime Lift Rigging Academy — site content.
Everything build.py renders comes from here. Facts only: prices, schedules,
policies and people were confirmed by the client (onboarding 8/20/26,
schedule 8/24/26). Do not add claims (pass rates, years founded, student
counts) that the client has not stated.
"""

BIZ = {
    "name": "Prime Lift Rigging Academy",
    "legal": "Prime Lift Rigging Academy LLC",
    "phone": "(361) 213-9690",
    "phone_raw": "+13612139690",
    "email": "primelift26@gmail.com",
    "street": "1605 US Highway 181 Frontage Rd, Suite A",
    "city": "Portland",
    "state": "TX",
    "zip": "78374",
    "hours": "Monday – Friday · 7:00 AM – 5:00 PM",
    "facebook": "https://www.facebook.com/profile.php?id=61591822862013",
    "tiktok": "https://www.tiktok.com/@primeliftacademy",
    "gmaps": "https://www.google.com/maps/place/?cid=16553214961176374110",
    "map_embed": "https://www.google.com/maps?q=1605+US+Highway+181+Frontage+Rd,+Portland,+TX+78374&output=embed",
    "lat": 27.8893523,
    "lng": -97.313445,
    "areas": ["Portland", "Corpus Christi", "Ingleside", "Gregory", "Aransas Pass",
              "Rockport", "Robstown", "Taft", "Sinton", "Kingsville"],
}

# ---------------------------------------------------------------- courses
COURSES = [
    {
        "id": "advanced", "slug": "advanced-rigger",
        "name": "Advanced Rigger",
        "cred": "NCCER Certified Advanced Rigger",
        "price": 1000, "was": 1700, "deposit": 200,
        "img": "img/card-rigger.jpg",
        "hero": "img/card-rigger.jpg",
        "hero_alt": "Instructor demonstrating a sling hitch on a load during an Advanced Rigger class",
        "kicker": "NCCER Certified Advanced Rigger",
        "h1": "Advanced Rigger<em>Certification</em>",
        "lede": "Four days of classroom and hands-on rigging in Portland, TX, then a written and practical test-out in the same building. Day, night or one weekend. $200 holds your seat.",
        "meta_title": "Advanced Rigger Certification (NCCER) in Portland, TX",
        "meta_desc": "NCCER Advanced Rigger certification near Corpus Christi. 4-day course, day or night, or a 3-day weekend express. Test out on-site. $1,000, $200 deposit.",
        "summary": "The Advanced Rigger course is for anyone who rigs loads for a living, or wants to. New hires get the foundation; experienced hands get the card that proves what they already know. You learn to plan a lift, calculate load weight and center of gravity, pick and inspect the right sling and hardware, control the load, and signal the crane, then you test out in our accredited testing room.",
        "learn": [
            "Advanced rigging principles and lift planning",
            "Load weight calculations and center of gravity",
            "Sling selection, hitch configurations and inspections",
            "Rigging hardware: shackles, hooks, spreader bars and below-the-hook devices",
            "Load control, tag lines and crane hand signals",
            "Written and hands-on practical test-out on the last day",
        ],
        "formats": [
            {"name": "Weekday Day Class", "when": "Mon – Thu", "time": "8:00 AM – 2:00 PM", "note": "Four days. Starts every Monday."},
            {"name": "Weekday Night Class", "when": "Mon – Thu", "time": "6:00 PM – 11:00 PM", "note": "Four nights. Built for day-shift crews.", "link": "/night-classes/"},
            {"name": "3-Day Weekend Express", "when": "Fri – Sun", "time": "8:00 AM – 5:00 PM", "note": "Done in one weekend. Starts every Friday.", "link": "/weekend-express/"},
        ],
        "who": [
            ("New hires", "No experience required. The course starts from the ground up and you leave with a credential that gets you through the gate."),
            ("Experienced riggers", "You already know the work. Get the NCCER card that puts it on paper for every contractor and turnaround in the country."),
            ("Recertification", "NCCER rigger credentials are good for five years. Coming due? See our recertification page."),
        ],
        "faq": [
            ("How long is the Advanced Rigger course?", "Four days, Monday through Thursday, in either the day class (8:00 AM to 2:00 PM) or the night class (6:00 PM to 11:00 PM). The 3-Day Weekend Express runs Friday through Sunday, 8:00 AM to 5:00 PM."),
            ("Do I need experience to enroll?", "No. The course is built for both new and experienced riggers. Everything is taught from the ground up, and the hands-on portion uses real rigging hardware."),
            ("What does it cost?", "$1,000 during our current promotion, normally $1,700. A $200 deposit secures your seat and the remaining $800 is due before your class begins. Klarna, Afterpay, Zelle and in-house financing with no credit check are available."),
            ("Is the credential recognized nationally?", "Yes. You test out in our NCCER accredited assessment center and your credential is recorded on the NCCER Registry, which contractors across the country use to verify craft credentials."),
            ("How long is the certification good for?", "Five years from the date it is issued."),
            ("What should I bring?", "A government-issued photo ID for NCCER testing, something to write with, and work boots for the hands-on portion. Book early and we'll send study material so you can start before day one."),
        ],
    },
    {
        "id": "signal", "slug": "signal-person",
        "name": "Signal Person",
        "cred": "NCCER Certified Signal Person",
        "price": 1000, "was": None, "deposit": 200,
        "img": "img/card-signal.jpg",
        "hero": "img/card-signal.jpg",
        "hero_alt": "Rigger giving a hand signal from a personnel platform during a crane lift",
        "kicker": "NCCER Certified Signal Person",
        "h1": "Signal Person<em>Certification</em>",
        "lede": "Be the eyes and the voice of the lift. Two Fridays of classroom and hands-on practice in Portland, TX, then a written and practical test. $200 holds your seat.",
        "meta_title": "Signal Person Certification (NCCER) in Portland, TX",
        "meta_desc": "NCCER Signal Person certification near Corpus Christi. Two Fridays of hands-on training, crane hand signals, written and practical test on-site. $1,000.",
        "summary": "A qualified signal person is required on any lift where the operator can't see the load. This course teaches the standard hand signals, the voice and radio procedures that keep a lift moving safely, and the judgment to stop one. You practice signaling real movements, then test out written and hands-on.",
        "learn": [
            "Industry-standard crane hand signals",
            "Voice and radio communication on the lift",
            "Signal person responsibilities and when to stop the lift",
            "Working with the operator and the rigging crew",
            "Two days of classroom and hands-on practice",
            "Written and practical test, certification on completion",
        ],
        "formats": [
            {"name": "Two Fridays", "when": "Fridays", "time": "8:00 AM – 3:00 PM", "note": "Two days of training. Starts every Friday."},
        ],
        "who": [
            ("Riggers adding a credential", "Most Advanced Rigger students add Signal Person so they can fill either role on a crew."),
            ("Crane crews", "Refineries, plants, construction and shipyards all need a qualified signal person on the ground."),
            ("New to the trade", "No experience required. If you can learn the signals, you can earn the card."),
        ],
        "faq": [
            ("How long is the Signal Person course?", "Two Fridays, 8:00 AM to 3:00 PM, with the written and practical test at the end."),
            ("What does it cost?", "$1,000. A $200 deposit secures your seat and the remaining $800 is due before class begins. Klarna, Afterpay, Zelle and in-house financing are available."),
            ("Do I need to be a rigger first?", "No. Signal Person stands on its own. Many students take it alongside Advanced Rigger, but it isn't a prerequisite."),
            ("Is the credential recognized nationally?", "Yes. Your NCCER Signal Person credential is recorded on the NCCER Registry."),
            ("What should I bring?", "A government-issued photo ID for NCCER testing, something to write with, and work boots for the hands-on portion."),
        ],
    },
]

ASSESSMENT = {
    "id": "assessment", "slug": "nccer-assessments",
    "name": "NCCER Assessments",
    "price": 150,
    "img": "img/card-assessment.jpg",
    "hero": "img/testing-room.jpg",
    "hero_alt": "Candidates taking a proctored NCCER assessment in the on-site testing room",
    "kicker": "NCCER Accredited Assessment Center",
    "h1": "Test Out.<em>Get The Card.</em>",
    "lede": "Already know the work? Skip the class. We proctor NCCER written and hands-on assessments in 36 crafts, Monday through Friday by appointment, one flat $150 per assessment.",
    "meta_title": "NCCER Assessments in Portland, TX · Test Out in 36 Crafts · $150",
    "meta_desc": "NCCER craft assessments near Corpus Christi: pipefitter, millwright, boilermaker, electrician, heavy equipment, HVAC, plumber and more. $150 flat, proctored on-site.",
    "faq": [
        ("What is an NCCER assessment?", "A proctored written assessment of what you know about your craft, with a hands-on performance verification where the craft calls for one. Pass, and your credential is recorded on the NCCER Registry, which contractors use to verify craft skills."),
        ("Do I have to take a class first?", "No. Assessments are for people who already have the field experience. If you want training first, see our Advanced Rigger and Signal Person courses."),
        ("What does it cost?", "$150 per assessment, one flat price across every craft we assess. Paid in full when you book."),
        ("When can I test?", "Monday through Friday, 8:00 AM to 5:00 PM, by appointment. Book online or call the office."),
        ("What do I bring?", "A government-issued photo ID. NCCER requires it before you can sit for any assessment."),
        ("What if I don't pass?", "Talk to the office about a retest date. Our instructors can also point you to the areas to study."),
    ],
}

CRAFT_GROUPS = [
    ("Rigging & Lifting", "rigging"),
    ("Heavy Equipment Operation", "heo"),
    ("Pipe, Mechanical & Millwright", "mech"),
    ("Electrical & Instrumentation", "ei"),
    ("Boilermaker & Pressure Equipment", "boiler"),
    ("Structural, Carpentry & Concrete", "struct"),
    ("Finishing, Insulation & Coatings", "finish"),
    ("Cleaning & Support Trades", "support"),
]

# slug, name, group, blurb (what the craft does), covers (what the assessment
# measures), tests (True = there is a hands-on performance component we advertise)
CRAFTS = [
    ("boilermaker-pressure-vessel", "Boilermaker (Pressure Vessel)", "boiler",
     "Pressure-vessel boilermakers fabricate, erect and repair boilers, tanks, vessels and exchangers in refineries, chemical plants and power stations.",
     "vessel components and nomenclature, layout and fit-up, rigging vessel sections, tube work, welding-related tasks, hydrostatic testing and boilermaker safety."),
    ("commercial-carpenter", "Commercial Carpenter", "struct",
     "Commercial carpenters build the forms, framing, interior and exterior systems on commercial construction projects.",
     "blueprint reading, layout, framing, concrete formwork, interior finish systems, doors and hardware, and jobsite safety."),
    ("commercial-electrician", "Commercial Electrician", "ei",
     "Commercial electricians install and maintain the power, lighting and control systems in commercial buildings.",
     "the National Electrical Code, conductors and raceways, boxes and fittings, branch circuits and feeders, motors and controls, and electrical safety."),
    ("concrete-finisher", "Concrete Finisher", "struct",
     "Concrete finishers place, screed, float, trowel and cure concrete slabs, walls and structures.",
     "concrete properties and admixtures, placing and consolidating, screeding and floating, troweling and finishing, joints, curing and repair."),
    ("drywall-mechanic", "Drywall Mechanic", "finish",
     "Drywall mechanics hang, tape and finish gypsum board on walls and ceilings in commercial and industrial buildings.",
     "board types and fasteners, layout and hanging, taping and finishing levels, corner beads and trims, and material handling safety."),
    ("heavy-equipment-operator-backhoe", "Heavy Equipment Operator: Backhoe", "heo",
     "Backhoe operators dig trenches, set pipe, backfill and load material on construction and utility jobs.",
     "backhoe controls and pre-operation inspection, trenching and excavation, loading, grade checking, and safe operation around utilities and workers."),
    ("heavy-equipment-operator-compaction-equipment", "Heavy Equipment Operator: Compaction Equipment", "heo",
     "Compaction operators run rollers and compactors to build stable subgrades, base courses and asphalt mats.",
     "compactor types and pre-operation inspection, lift thickness and pattern, soil and asphalt compaction, and safe operation on grades and near workers."),
    ("heavy-equipment-operator-dozer", "Heavy Equipment Operator: Dozer", "heo",
     "Dozer operators clear, cut, push and grade earth on site preparation and heavy civil projects.",
     "dozer controls and inspection, blade types, cutting and pushing, rough and finish grading, slope work, and safe operation."),
    ("heavy-equipment-operator-excavator", "Heavy Equipment Operator: Excavator", "heo",
     "Excavator operators dig foundations, trenches and ponds, and load trucks on construction and industrial sites.",
     "excavator controls and inspection, trenching and mass excavation, loading, grade control, attachments, and safe operation near utilities."),
    ("heavy-equipment-operator-forklift", "Heavy Equipment Operator: Forklift", "heo",
     "Forklift operators move, stack and stage material in plants, laydown yards and warehouses.",
     "forklift types and pre-operation inspection, load capacity and stability, picking and placing loads, traveling with a load, and OSHA-aligned safe operation."),
    ("heavy-equipment-operator-loader", "Heavy Equipment Operator: Loader", "heo",
     "Loader operators load trucks, move aggregate and stockpile material on construction and plant sites.",
     "loader controls and inspection, bucket loading and carrying, truck loading, stockpiling, and safe operation on uneven ground."),
    ("heavy-equipment-operator-motor-grader", "Heavy Equipment Operator: Motor Grader", "heo",
     "Motor grader operators cut and finish subgrade, base and road surfaces to grade and crown.",
     "grader controls and inspection, blade positioning, cutting and spreading, ditching, finish grading to stakes or GPS, and safe operation."),
    ("heavy-equipment-operator-off-road-dump-truck", "Heavy Equipment Operator: Off-Road Dump Truck", "heo",
     "Off-road dump truck operators haul earth and aggregate on mine, quarry and heavy civil sites.",
     "articulated and rigid haul truck inspection, loading and dumping procedures, haul-road operation, backing and spotting, and safe operation on grades."),
    ("heavy-equipment-operator-scraper", "Heavy Equipment Operator: Scraper", "heo",
     "Scraper operators cut, haul and spread earth over long distances on mass grading projects.",
     "scraper controls and inspection, loading with and without a push, hauling, spreading and finishing, and safe operation."),
    ("heavy-equipment-operator-skid-steer", "Heavy Equipment Operator: Skid Steer", "heo",
     "Skid steer operators handle grading, loading, demolition and attachment work in tight spaces.",
     "skid steer controls and inspection, attachments, loading and grading, operating on slopes and in confined areas, and safe operation."),
    ("hvac-technician", "HVAC Technician", "mech",
     "HVAC technicians install, service and troubleshoot heating, ventilation, air conditioning and refrigeration systems.",
     "refrigeration cycle and components, electrical circuits and controls, air distribution, system installation and startup, troubleshooting, and EPA-related refrigerant handling."),
    ("hydroblasting-technician", "Hydroblasting Technician", "support",
     "Hydroblasting technicians use high-pressure water to clean exchangers, vessels, piping and surfaces during turnarounds.",
     "high-pressure water jetting equipment, hose and lance handling, pressure and flow control, exclusion zones and PPE, and industrial cleaning safety."),
    ("industrial-boilermaker-exchanger", "Industrial Boilermaker (Exchanger)", "boiler",
     "Exchanger boilermakers pull, clean, re-tube and re-bundle heat exchangers in refinery and petrochemical maintenance.",
     "exchanger types and components, bundle pulling and rigging, gasket and flange work, tube rolling and plugging, hydrotesting, and boilermaker safety."),
    ("industrial-boilermaker-maintenance", "Industrial Boilermaker (Maintenance)", "boiler",
     "Maintenance boilermakers repair boilers, vessels, tanks and stacks in operating plants.",
     "boiler and vessel components, inspection and repair methods, rigging and fit-up, welding-related tasks, testing, and confined-space and hot-work safety."),
    ("industrial-carpenter", "Industrial Carpenter", "struct",
     "Industrial carpenters build formwork, scaffolds, decking and temporary structures in plants and heavy construction.",
     "blueprint reading and layout, concrete formwork, framing, scaffold and temporary structures, and jobsite safety."),
    ("industrial-electrician", "Industrial Electrician", "ei",
     "Industrial electricians install and maintain power distribution, motors and controls in plants and refineries.",
     "the National Electrical Code, conduit and cable systems, motors and motor controls, transformers and distribution, hazardous-location wiring, and electrical safety."),
    ("industrial-insulator", "Industrial Insulator", "finish",
     "Industrial insulators apply insulation and jacketing to piping, vessels and equipment.",
     "insulation materials and selection, pipe and vessel insulation, metal jacketing and fabrication, vapor barriers, and safe work around hot and cold systems."),
    ("industrial-ironworker", "Industrial Ironworker", "struct",
     "Industrial ironworkers erect structural steel, set equipment and install grating, handrail and platforms.",
     "structural steel erection, bolting and torquing, rigging and connecting, layout and plumbing, grating and handrail, and fall protection."),
    ("industrial-maintenance-ei-technician", "Industrial Maintenance E&I Technician", "ei",
     "Electrical and Instrumentation technicians keep plant power, control and measurement systems running.",
     "electrical troubleshooting, motor controls, instrumentation loops, calibration, control valves, and electrical and process safety."),
    ("industrial-maintenance-mechanic", "Industrial Maintenance Mechanic", "mech",
     "Industrial maintenance mechanics repair and align pumps, compressors, gearboxes and rotating equipment.",
     "precision measuring, bearings and seals, shaft alignment, pumps and compressors, lubrication, and mechanical safety."),
    ("industrial-maintenance-support-mechanic", "Industrial Maintenance Support Mechanic", "mech",
     "Support mechanics assist maintenance crews with equipment disassembly, rigging, parts handling and reassembly.",
     "hand and power tools, fasteners and torque, basic rigging, equipment disassembly and reassembly, and maintenance safety."),
    ("industrial-millwright", "Industrial Millwright", "mech",
     "Millwrights install, align and maintain machinery: pumps, turbines, conveyors, gearboxes and compressors.",
     "precision measurement, leveling and alignment, bearings and couplings, conveyors and gear drives, machinery installation, and millwright safety."),
    ("industrial-painter", "Industrial Painter", "finish",
     "Industrial painters prepare and coat steel, piping and structures to protect them from corrosion.",
     "surface preparation and abrasive blasting, coating types and mixing, spray and brush application, inspection and film thickness, and coatings safety."),
    ("industrial-pipefitter", "Industrial Pipefitter", "mech",
     "Pipefitters lay out, fabricate, install and test piping systems in refineries, plants and power stations.",
     "pipe and fitting identification, blueprint and isometric reading, layout and takeoffs, threaded, socket-weld and butt-weld fit-up, flanges and bolting, pipe hangers, and hydrotesting."),
    ("instrumentation-fitter", "Instrumentation Fitter", "ei",
     "Instrumentation fitters install tubing, instruments and supports for process measurement and control.",
     "tubing bending and fitting, instrument mounting and supports, impulse lines, process connections, and instrument installation safety."),
    ("instrumentation-technician", "Instrumentation Technician", "ei",
     "Instrumentation technicians calibrate, troubleshoot and maintain the instruments that measure and control a process.",
     "pressure, level, flow and temperature instruments, calibration, control loops and valves, transmitters and signals, and loop troubleshooting."),
    ("mason", "Mason", "struct",
     "Masons lay brick, block and stone for walls, structures and industrial refractory work.",
     "masonry materials and mortar, layout and leveling, laying units to the line, reinforcing and anchoring, and masonry safety."),
    ("offshore-maintenance-mechanic", "Offshore Maintenance Mechanic", "mech",
     "Offshore maintenance mechanics keep rotating and process equipment running on platforms and vessels.",
     "pumps and compressors, bearings and alignment, hydraulics, preventive maintenance, and offshore safety practices."),
    ("plumber", "Plumber", "mech",
     "Plumbers install and repair water supply, drain-waste-vent and gas piping in commercial and industrial buildings.",
     "plumbing codes, DWV and water supply systems, pipe materials and joining, fixtures, backflow prevention, and plumbing safety."),
    ("reinforcing-iron-rebar-worker", "Reinforcing Iron & Rebar Worker", "struct",
     "Rebar workers place and tie the reinforcing steel that gives concrete its strength.",
     "bar identification and placing drawings, cutting and bending, tying and splicing, chairs and spacing, and rebar safety."),
    ("scaffold-builder", "Scaffold Builder", "struct",
     "Scaffold builders erect and dismantle the frame, tube-and-clamp and system scaffolds every turnaround runs on.",
     "scaffold components and types, foundations and bracing, planking and access, tie-ins, inspection tagging, and fall protection."),
]

# ------------------------------------------------------------- instructors
PEOPLE = [
    {
        "slug": "andres-herrera", "name": "Andres Herrera",
        "role": "Co-Founder · NCCER Practical Examiner",
        "short": "Director / Manager",
        "img": "img/team-andres.jpg",
        "card": "img/team-andres-card.jpg",   # face-centered 4:5 crop for grids; "img" stays the full shot for his page + schema
        "alt": "Andres Herrera working from a personnel platform on a refinery lift",
        "teaches": ["advanced-rigger", "signal-person", "nccer-assessments"],
        "bio": [
            "After years of hands-on field experience, Andres and his business partner built Prime Lift to help craft professionals earn the credentials that move their careers.",
            "As an NCCER Practical Examiner he runs the hands-on training and the test-outs, with a hard focus on safety and jobsite reality. Students know him as Andy, and the reviews say the same thing over and over: he makes sure you understand it before the class moves on.",
        ],
        "meta_desc": "Andres Herrera, co-founder of Prime Lift Rigging Academy and NCCER Practical Examiner. Runs hands-on rigging training and NCCER test-outs in Portland, TX.",
    },
    {
        "slug": "juan-meza", "name": "Juan Meza",
        "role": "Director",
        "short": "Director / Manager",
        "img": "img/team-juan.jpg",
        "card": "img/team-juan-card.jpg",
        "alt": "Juan Meza on the tracks of a Liebherr crawler crane at a jobsite",
        "teaches": ["advanced-rigger", "nccer-assessments"],
        "bio": [
            "Juan built his career through years of hands-on industry experience and now leads the academy's programs.",
            "He's the one making sure every student leaves with the skills, the confidence and the foundation to build a real career in the trades, and that the schedule works around the shifts people actually work.",
        ],
        "meta_desc": "Juan Meza, Director at Prime Lift Rigging Academy in Portland, TX. Leads the academy's NCCER rigging and assessment programs.",
    },
    {
        "slug": "frank-torres", "name": "Frank Torres",
        "role": "Advanced Rigging Instructor",
        "short": "Advanced Rigging Instructor",
        "img": "img/team-frank.jpg",
        "alt": "Frank Torres at a heavy lift jobsite with crawler cranes",
        "teaches": ["advanced-rigger", "signal-person"],
        "bio": [
            "Frank is an NCCER Advanced Rigger and Signal Person with more than 10 years of crane and rigging experience, and he brings all of it into the classroom.",
            "He genuinely wants every student to pass. Don't be afraid to ask him to explain something twice; take advantage of what he knows.",
        ],
        "meta_desc": "Frank Torres, Advanced Rigging Instructor at Prime Lift Rigging Academy. NCCER Advanced Rigger and Signal Person with 10+ years of crane and rigging experience.",
    },
]

# ----------------------------------------------------------------- reviews
REVIEWS = [
    {"who": "Ryan P", "src": "google", "stars": 5,
     "text": "Awesome experience, a lot of knowledge on all rigging, from forklifts to rigging I've never even seen or heard of. Great teachers and instructors, Frank and Andy will make sure you understand before moving on to the next lesson. 5/5 stars, highly recommend to any and everybody wanting to get their certifications."},
    {"who": "Joshua Fonseca", "src": "google", "stars": 5,
     "text": "A lot of one-to-one explanation. All questions will be answered directly to you; the teacher will sit there and go over it as many times as you need until you understand. Definitely recommend."},
    {"who": "Viko Ledesma", "src": "facebook",
     "text": "All you need to know, they will teach and guide you thru the process of getting your NCCER certification!"},
    {"who": "Arturo Duran Jr.", "src": "facebook",
     "text": "It's a very great class, a lot of good information, and the instructor did an awesome job explaining the information."},
    {"who": "Michael Cervantes", "src": "facebook",
     "text": "Great exercise, very professional. I recommend others to go through Prime Lift Rigging."},
]

# --------------------------------------------------------------------- FAQ
FAQ = [
    ("How long does the Advanced Rigger course take?",
     "Four days, Monday through Thursday. Day classes run 8:00 AM to 2:00 PM and night classes run 6:00 PM to 11:00 PM, so you can keep working either shift. If you can't take time off during the week at all, the 3-Day Weekend Express runs Friday through Sunday, 8:00 AM to 5:00 PM, and you walk out certified after one weekend."),
    ("What does it cost and what do I pay today?",
     "Advanced Rigger is $1,000 during our current promotion, normally $1,700. Signal Person is $1,000. A $200 deposit secures your seat and the remaining $800 is due before your class begins. NCCER assessments are $150 flat for any of our 36 crafts, paid in full at registration."),
    ("What if I can't pay the whole thing up front?",
     "You have options. Klarna and Afterpay are available; both cover the full $1,000 up front and then split it into payments for you, so those are pay-in-full options at checkout rather than the $200 deposit. If you don't qualify for either, we offer in-house financing with no credit check: as little as $200 down and payments leading up to your course date. We also take Zelle if you'd rather register that way. Either way, your course can't begin until the balance is paid in full."),
    ("Is this a real NCCER certification?",
     "Yes. We're an NCCER Accredited Training and Assessment Center, so you train and test out in the same building and your credential is recorded on the NCCER national registry, recognized on jobsites across the country."),
    ("Do I need experience to take the Advanced Rigger course?",
     "No experience required. The course is designed for both new and experienced riggers. We cover advanced rigging principles, load weight calculations, center of gravity, sling selection and inspection, hitch configurations, load control, lift planning and crane hand signals from the ground up."),
    ("What's included in the course?",
     "Classroom instruction, hands-on practice with real rigging hardware, your written and practical assessment, and your NCCER certification upon successful completion. Book early and we'll get study material to you so you can start before day one."),
    ("Can I test out without taking a class?",
     "Yes. As an accredited NCCER Assessment Center we proctor written and hands-on assessments in 36 crafts, from pipefitter and millwright to forklift and excavator, for $150 per assessment. Monday through Friday, 8:00 AM to 5:00 PM, by appointment."),
    ("How long is the credential good for?",
     "NCCER rigger credentials are valid for five years from the date they're issued. When yours is coming due, call the office and we'll schedule your recertification."),
    ("What is your deposit and reschedule policy?",
     "A $200 deposit is required to secure your spot. This deposit is non-refundable. However, you are allowed one reschedule as long as at least 48 hours' notice is provided. Rescheduling requests made with less than 48 hours' notice will result in the loss of your deposit."),
    ("Do you offer training in Spanish?",
     "Not at this time. All classes and assessments are taught and proctored in English."),
    ("Where are you located?",
     "1605 US Highway 181 Frontage Rd, Suite A, in Portland, Texas, minutes from Corpus Christi, Ingleside and Gregory. Office hours are Monday through Friday, 7:00 AM to 5:00 PM, though hours vary during class weeks."),
]

# ------------------------------------------------------------- financing
FINANCING = [
    ("Deposit & Balance", "$200 holds your seat today by card. The remaining $800 is due before your class starts, and you can pay it online, in the office, or on a schedule.", "Most students"),
    ("Klarna or Afterpay", "Split the cost into scheduled payments. Both pay the full $1,000 at checkout and then break it up for you, so choose Klarna or Afterpay on the checkout screen instead of the $200 deposit.", "Instant decision"),
    ("In-House Financing", "Don't qualify for Klarna or Afterpay? Start with as little as $200 down and make payments leading up to your class date. No credit check. Your course begins once the balance is paid in full.", "No credit check"),
    ("Zelle", "Prefer Zelle? Pick In-House on the booking screen and note it, or message us on Facebook or email the office and we'll register you manually.", "primelift26@gmail.com"),
    ("Employer Paying", "Company covering it? Choose \"My employer is paying\" on the booking form and the office will coordinate the invoice with them.", "Company pays"),
]


# ------------------------------------------------------------------ Spanish
# /es/ landing page. Usted / impersonal register. Do not add claims about the
# language classes are taught in or about bilingual staff.
ES = {
    "title": "Certificación NCCER de Rigger y Signal Person en Portland, TX",
    "desc": "Cursos de Advanced Rigger y Signal Person y evaluaciones NCCER en 36 oficios en Portland, Texas. Precios publicados, planes de pago sin revisión de crédito.",
    "kicker": "Centro Acreditado NCCER",
    "h1": "Certificación<br class=\"mbr\"> NCCER<em>Portland, Texas</em>",
    "lede": "Cursos presenciales de Advanced Rigger y Signal Person, y evaluaciones NCCER en 36 oficios, con el examen en el mismo edificio. $200 aparta su lugar.",
    "call": "Llamar",
    "enroll": "Inscribirse",
    "specs": [("Advanced Rigger", "$1,000 · depósito $200"), ("Signal Person", "$1,000 · depósito $200"), ("Evaluaciones NCCER", "$150 · 36 oficios"), ("Ubicación", "Portland, TX")],
    "courses_eyebrow": "Los Cursos",
    "courses_h2": "Capacitación<br>Presencial",
    "advanced": {
        "name": "Advanced Rigger",
        "cred": "NCCER Certified Advanced Rigger",
        "price": "$1,000",
        "was": "$1,700",
        "deposit": "Depósito de $200 para apartar su lugar; el saldo de $800 se paga antes de que empiece la clase.",
        "summary": "Cuatro días de clase y práctica con equipo real de rigging en Portland, y al final el examen escrito y práctico en nuestro centro de evaluación acreditado. Sin experiencia previa necesaria. La credencial NCCER Advanced Rigger tiene una vigencia de cinco años.",
        "learn": [
            "Principios de rigging avanzado y planeación de izajes",
            "Cálculo del peso de la carga y centro de gravedad",
            "Selección de eslingas, configuraciones de enganche e inspecciones",
            "Herrajes de rigging: grilletes, ganchos, barras separadoras y dispositivos bajo el gancho",
            "Control de la carga, líneas guía y señales manuales para grúa",
            "Examen escrito y práctico el último día",
        ],
        "formats": [
            ("Clase de día", "Lunes a jueves", "8:00 AM – 2:00 PM", "Cuatro días. Empieza cada lunes."),
            ("Clase de noche", "Lunes a jueves", "6:00 PM – 11:00 PM", "Cuatro noches. Para quien trabaja de día."),
            ("Fin de semana (3 días)", "Viernes a domingo", "8:00 AM – 5:00 PM", "Todo el curso en un fin de semana. Empieza cada viernes."),
        ],
    },
    "signal": {
        "name": "Signal Person",
        "cred": "NCCER Certified Signal Person",
        "price": "$1,000",
        "deposit": "Depósito de $200 para apartar su lugar; el saldo de $800 se paga antes de que empiece la clase.",
        "summary": "Dos viernes de clase y práctica para ser los ojos y la voz del izaje: señales manuales estándar, comunicación por voz y radio, y cuándo detener la maniobra. Termina con examen escrito y práctico. No es necesario ser rigger primero.",
        "formats": [("Dos viernes", "Viernes", "8:00 AM – 3:00 PM", "Dos días de capacitación. Empieza cada viernes.")],
    },
    "assess_eyebrow": "Evaluaciones NCCER",
    "assess_h2": "¿Ya Domina<br>Su Oficio?",
    "assess_lede": "Si ya tiene la experiencia, no necesita tomar la clase. Aplicamos evaluaciones NCCER (examen escrito y, según el oficio, verificación práctica) en nuestro centro acreditado, de lunes a viernes con cita. $150 por evaluación, precio fijo en los 36 oficios. Al aprobar, la credencial queda registrada en el NCCER Registry. Las páginas de cada oficio están en inglés.",
    "groups": [
        ("rigging", "Rigging e izajes"),
        ("heo", "Operación de|equipo pesado"),
        ("mech", "Tubería, mecánica|y millwright"),
        ("ei", "Eléctrico e|instrumentación"),
        ("boiler", "Boilermaker y|equipo a presión"),
        ("struct", "Estructuras, carpintería|y concreto"),
        ("finish", "Acabados, aislamiento|y recubrimientos"),
        ("support", "Limpieza industrial|y oficios de apoyo"),
    ],
    "fin_eyebrow": "Formas De Pago",
    "fin_h2": "Que El Costo<br>No Lo Detenga.",
    "financing": [
        ("Depósito y saldo", "$200 aparta su lugar hoy con tarjeta. Los $800 restantes se pagan antes de que empiece la clase: en línea, en la oficina o en pagos programados.", "La mayoría de los estudiantes"),
        ("Klarna o Afterpay", "Divida el costo en pagos programados. Ambos pagan los $1,000 completos al momento de la compra y después lo dividen en cuotas, así que en la pantalla de pago elija Klarna o Afterpay en lugar del depósito de $200.", "Decisión inmediata"),
        ("Financiamiento interno", "¿No califica para Klarna o Afterpay? Empiece con tan solo $200 de enganche y haga pagos hasta la fecha de su clase. Sin revisión de crédito. El curso comienza cuando el saldo está pagado por completo.", "Sin revisión de crédito"),
        ("Zelle", "¿Prefiere Zelle? En la pantalla de reservación elija la opción de financiamiento interno y anótelo, o escríbanos por Facebook o por correo y lo registramos manualmente.", "primelift26@gmail.com"),
        ("Paga su empleador", "¿Su empresa cubre el curso? Elija \"My employer is paying\" en el formulario de reservación y la oficina se coordina con ellos.", "Grupos"),
    ],
    "fin_note": "El curso no puede comenzar hasta que el saldo esté pagado por completo. El depósito de $200 no es reembolsable; se permite un cambio de fecha con al menos 48 horas de anticipación.",
    "team_eyebrow": "Sus Instructores",
    "team_h2": "Profesionales<br>Del Campo",
    "roles": {"andres-herrera": "Cofundador · Examinador Práctico NCCER", "juan-meza": "Director", "frank-torres": "Instructor de Rigging Avanzado"},
    "visit_eyebrow": "Ubicación Y Horario",
    "visit_h2": "Portland,<br>Texas",
    "visit_lede": "Sobre la vía de servicio de la US-181, a minutos de Corpus Christi, Ingleside y Gregory.",
    "hours": "Lunes a viernes · 7:00 AM – 5:00 PM",
    "hours_note": "El horario puede variar en semanas de clase",
    "labels": {"center": "Centro de Capacitación y Evaluación", "hours": "Horario de oficina", "phone": "Teléfono", "email": "Correo", "directions": "Cómo llegar", "book": "Reservar en línea", "all_dates": "Ver todas las fechas", "learn": "Lo que aprenderá", "formats": "Horarios", "cred": "Credencial"},
    "band_eyebrow": "Su Futuro Empieza Aquí",
    "band_h2": "Aparte Su Lugar<br class=\"mbr\"> Con $200.",
    "band_p": "Los grupos son pequeños y las clases se llenan. Reserve su fecha, empiece a estudiar desde antes y llegue listo para aprobar.",
}

# ------------------------------------------------------------------- guides
# Optional facts referenced by the guides. Rendered only when set.
RETEST_POLICY = None              # e.g. "One retest of a failed section is included." (client has not stated one)
CREDENTIAL_POSTING_TIME = None    # e.g. "Results are usually on the Registry within two weeks." (client has not stated one)

GUIDES = [
    {
        "slug": "nccer-vs-nccco-rigger",
        "title": "NCCER Rigger vs. NCCCO Rigger: Which Certification Do You Need?",
        "meta_title": "NCCER Rigger vs. NCCCO Rigger: Which Do You Need?",
        "meta_desc": "NCCER and NCCCO rigger credentials are not the same thing. What each one is, what OSHA actually requires, and how to find out which one your employer wants.",
        "h1": "NCCER Rigger vs.<br class=\"mbr\"> NCCCO Rigger:<br> Which Certification<br class=\"mbr\"> Do You Need?",
        "kicker": "Credentials Explained",
        "lede": "Two rigger credentials show up on Coastal Bend job postings, and they are not interchangeable. Here is what each one is, what OSHA actually requires, and how to pick.",
        "read": "5 min read",
        "body": """
<p>If you have looked at rigger jobs around Corpus Christi, Ingleside or Portland, you have seen both names: NCCER and NCCCO. They sound alike, they both put the word "rigger" on a card, and plenty of people use them as if they were the same thing. They are not. Which one you need depends almost entirely on who is hiring you and whose site you will be working on.</p>
<h2>What an NCCER rigger<br class="mbr"> credential is</h2>
<p>NCCER is the National Center for Construction Education and Research. It is a craft credentialing organization: it publishes the curriculum most industrial contractors train from, and it runs assessments in dozens of crafts, rigging included. An NCCER rigger credential is earned by passing a written assessment and a hands-on performance verification in front of an NCCER practical examiner. The result is recorded on the NCCER Registry, the national database contractors and site owners use to look up a worker's craft credentials by card number.</p>
<p>NCCER credentials are used heavily by industrial contractors and by Associated Builders and Contractors (ABC) member companies. In refinery, petrochemical and shipyard work along the Gulf Coast, "NCCER rigger" is often the credential a contractor's safety department expects to see before a hand gets a gate pass. Prime Lift teaches the NCCER Advanced Rigger and Signal Person courses and proctors the assessments in the same building. See the <a href="/advanced-rigger/">Advanced Rigger course</a> for the schedule and price.</p>
<h2>What an NCCCO rigger<br class="mbr"> certification is</h2>
<p>NCCCO is the National Commission for the Certification of Crane Operators. It is best known for crane operator certification, and it also offers CCO Rigger Level I, Rigger Level II and Signalperson certifications. CCO certifications are accredited under ANSI standards, which is one reason some owners and general contractors write "CCO certified" into their site requirements. Like NCCER, the CCO rigger exams have a written and a practical component.</p>
<p>You will run into CCO requirements most often where the employer or the site owner specifies it by name: certain construction general contractors, some crane and rigging companies, and owners whose lift plans call for CCO-certified personnel. Prime Lift does not offer CCO testing. If a job posting says CCO, you will need to find a CCO test site.</p>
<h2>What OSHA actually requires</h2>
<p>This is where most of the confusion starts. OSHA's cranes and derricks standard for construction, 29 CFR 1926 Subpart CC (1926.1400 and following), requires a <em>qualified rigger</em> for rigging work during assembly and disassembly and whenever workers are in the fall zone hooking, unhooking or guiding a load. It also requires a qualified signal person. OSHA defines "qualified" in terms of knowledge, training and demonstrated ability. It does not name NCCER, NCCCO or any other organization, and it does not require a card from either one.</p>
<p>In practice, a credential is how your employer proves you are qualified. Which credential satisfies them is their call, and it is usually driven by their customers' site requirements.</p>
<h2>How to decide</h2>
<ul>
<li><strong>Ask the employer.</strong> Before you spend a dime, ask the safety manager or the recruiter exactly which credential the job requires. Get the name, not just "rigger certified."</li>
<li><strong>Check the site owner.</strong> If you will be working turnarounds at a specific plant, ask what that owner requires of contractor riggers. Many Coastal Bend industrial sites verify NCCER credentials on the Registry.</li>
<li><strong>Look at the crew around you.</strong> If everyone on the crew carries NCCER cards, that tells you what the company's safety program is built on.</li>
<li><strong>Check the expiration.</strong> NCCER rigger credentials are valid for five years. If yours is coming due, <a href="/rigger-recertification/">recertify</a> before it lapses.</li>
</ul>
<h2>Where Prime Lift fits</h2>
<p>Prime Lift Rigging Academy is an NCCER Accredited Training and Assessment Center in Portland, TX. We teach the Advanced Rigger course in day, night and 3-day weekend formats, teach a standalone <a href="/signal-person/">Signal Person</a> course, and proctor NCCER assessments in 36 crafts for $150 each. If NCCER is what your employer asks for, you can train and test out here without going anywhere else. If they ask for CCO, we will tell you so up front rather than sell you the wrong card.</p>
""",
    },
    {
        "slug": "is-the-nccer-advanced-rigger-test-hard",
        "title": "Is the NCCER Advanced Rigger Test Hard? What to Expect",
        "meta_title": "Is the NCCER Advanced Rigger Test Hard? What to Expect",
        "meta_desc": "What the NCCER Advanced Rigger written and practical tests cover, how the 4-day class is built around them, how to prepare, and what if you miss a section.",
        "h1": "Is The NCCER Advanced<br class=\"mbr\"> Rigger Test Hard?<br> What To Expect",
        "kicker": "Before You Enroll",
        "lede": "The honest answer: it is a real test, and the class is built to get you through it. Here is what the written and hands-on portions cover and how to walk in ready.",
        "read": "5 min read",
        "body": """
<p>Most people asking this question are about to spend $1,000 and four days of their life, so it deserves a straight answer. The NCCER Advanced Rigger assessment is not a formality. It has a written portion and a hands-on practical, and you have to pass both. It is also not designed to trick you. The Advanced Rigger class exists to teach exactly what the test measures, and the test is given in the same building by the people who taught you.</p>
<h2>What the written test covers</h2>
<p>The written assessment is a proctored, multiple-choice test on the knowledge side of rigging. Expect questions drawn from the same topics the class covers:</p>
<ul>
<li>Advanced rigging principles and lift planning</li>
<li>Load weight calculations and center of gravity</li>
<li>Sling selection, hitch configurations and sling inspection</li>
<li>Rigging hardware: shackles, hooks, spreader bars and below-the-hook devices</li>
<li>Load control, tag lines and crane hand signals</li>
</ul>
<p>The part that worries students most is the math: figuring load weight from dimensions and material, working out sling tension at different angles, and locating a center of gravity on an uneven load. None of it is beyond basic arithmetic, but you have to know the formulas and use them under time. That is why the class spends real time on it instead of skimming.</p>
<h2>What the practical test covers</h2>
<p>The performance verification is hands-on, in front of an NCCER practical examiner. You are asked to do the work: inspect slings and hardware and reject what should be rejected, select and rig a hitch for a given load, control the load, and give the correct hand signals. If you have rigged on a crew, most of this is familiar. If you are new, the class is where you get the reps. You will be handling real rigging hardware from the first day, not looking at pictures of it.</p>
<h2>How the 4-day class is built</h2>
<p>The <a href="/advanced-rigger/">Advanced Rigger course</a> runs Monday through Thursday in two formats: the day class from 8:00 AM to 2:00 PM, and the <a href="/night-classes/">night class</a> from 6:00 PM to 11:00 PM for crews working days. The first three days move through lift planning, load math, slings, hardware, load control and signals, with classroom time and hands-on time each day. The written and practical test-out is on the last day. The <a href="/weekend-express/">3-Day Weekend Express</a> covers the same material Friday through Sunday, 8:00 AM to 5:00 PM, with the test on Sunday. Classes are capped at 8, so if you do not understand something, you ask, and the instructor goes over it again.</p>
<h2>How to prepare</h2>
<ul>
<li><strong>Book early and study the material.</strong> When you reserve a seat, the office sends study material so you can start before day one. The students who read it ahead of time have the easiest week.</li>
<li><strong>Brush up on the math.</strong> Volume, area, multiplication and a little trigonometry for sling angles. If you have not done arithmetic on paper in a while, practice before class.</li>
<li><strong>Bring what you need.</strong> A government-issued photo ID (NCCER will not let you test without it), something to write with, and work boots for the hands-on portion.</li>
<li><strong>Ask questions in class.</strong> The reviews say it over and over: the instructors do not move on until you get it. Take them up on that.</li>
<li><strong>Get sleep before test day.</strong> The last day is the long one.</li>
</ul>
<h2>What if you miss a section?</h2>
<p>The written and practical portions are scored separately. If you pass one and miss the other, you do not start the whole course over. Ask us about retest options; the office will tell you what applies to your situation, and your instructor can point you to the areas to study before you sit again.</p>
<h2>The bottom line</h2>
<p>Is the Advanced Rigger test hard? It is a real credential with a real test, and it should be, because a rigging mistake can hurt someone. But it is a test of things you will be taught, by people who want you to pass, in the same room where you learned them. Show up, do the reading, ask your questions, and you will be in good shape. Pick a <a href="/class-dates/">start date</a> when you are ready.</p>
""",
    },
    {
        "slug": "how-to-verify-nccer-credentials",
        "title": "How to Verify NCCER Credentials (For Workers and Employers)",
        "meta_title": "How to Verify NCCER Credentials: Registry, Card & Lookup",
        "meta_desc": "How the NCCER Registry works, what the card shows, how an employer looks up a credential on nccer.org, and training vs. assessment credentials explained.",
        "h1": "How To Verify<br class=\"mbr\"> NCCER Credentials<br> (For Workers<br class=\"mbr\"> And Employers)",
        "kicker": "Credentials Explained",
        "lede": "Your NCCER credential is only worth something if an employer can verify it. Here is where it lives, what the card shows, and how the lookup works.",
        "read": "4 min read",
        "body": """
<p>When you pass an NCCER assessment or complete NCCER training, the result does not just sit in a filing cabinet in Portland. It goes into a national database that any contractor or site owner in the country can check. Understanding how that works helps you as a worker, and it helps a safety manager who has a stack of cards on the desk and needs to know which ones are real.</p>
<h2>The NCCER Registry</h2>
<p>The NCCER Registry System is NCCER's national database of craft training and assessment records. Every person who tests or trains through an NCCER accredited organization gets an NCCER card number, and their results are recorded against that number. An accredited assessment center like Prime Lift submits results to NCCER after testing, and NCCER posts them to the Registry. The Registry is the source of truth: a card is a convenience, but the Registry record is what an employer relies on.</p>
<h2>Your NCCER card</h2>
<p>NCCER issues a wallet card tied to your card number, and transcripts and certificates can be pulled from your Registry record. Keep the card number somewhere safe, on your phone as well as in your wallet. You will need it to register for future assessments, to <a href="/rigger-recertification/">recertify</a>, and to give to an employer who wants to verify you. If you lose the card, the record is still there; the number is what matters.</p>
<h2>How an employer<br class="mbr"> verifies a credential</h2>
<p>NCCER offers a credential verification lookup through nccer.org. An employer enters the worker's NCCER card number (with the worker's permission, or as part of the hiring paperwork) and sees what credentials are on record and when they were earned. Safety departments at Coastal Bend industrial sites use this to check contractor riggers, signal persons and craft hands before a turnaround. If you are an employer verifying a crew, use the lookup rather than trusting a photocopy of a card.</p>
<h2>Training credentials vs.<br class="mbr"> assessment credentials</h2>
<p>This is the distinction that trips people up. NCCER records two different kinds of things:</p>
<ul>
<li><strong>Training completions</strong> come from completing NCCER curriculum modules through an accredited training sponsor. They show that you were taught the material and passed the module tests.</li>
<li><strong>Assessment credentials</strong> come from passing NCCER's standardized craft assessments: a written knowledge assessment and, where the craft calls for it, a hands-on performance verification, proctored by an accredited assessment center. These are the credentials most industrial contractors mean when they say "NCCER certified."</li>
</ul>
<p>Prime Lift is accredited for both training and assessment, so a student who takes the <a href="/advanced-rigger/">Advanced Rigger course</a> and passes the test-out gets the assessment credential, not just a training record. An experienced hand who skips the class and takes a <a href="/nccer-assessments/">$150 assessment</a> in one of 36 crafts gets the same kind of assessment credential. When an employer says they need to see the credential, the assessment record is what they are looking for.</p>
<h2>How long until it shows up?</h2>
<p>Results are submitted to NCCER after testing and posted to the Registry by NCCER, not by us, so the timing is not something we control. Ask the office how long posting takes for your credential, and keep your card number handy so you can check the record yourself once it is up.</p>
<h2>How long it stays valid</h2>
<p>NCCER rigger credentials are valid for five years from the date they are issued. An expired credential on the Registry reads the same as no credential to a safety department, so note the date and <a href="/rigger-recertification/">recertify</a> before it lapses.</p>
<h2>Quick checklist</h2>
<ul>
<li>Save your NCCER card number in more than one place.</li>
<li>Know whether your record shows a training completion, an assessment credential, or both.</li>
<li>Employers: verify on nccer.org, not from a photocopy.</li>
<li>Watch the five-year date on rigger credentials.</li>
</ul>
""",
    },
]

# --------------------------------------------------------------- home: why
# "Why Train Here" cards on the home page (index.html is patched by hand from
# this list; keep the six titles short so they hold one line at 390px).
WHY = [
    ("In-Person, Hands-On", "Small classes in Portland with real rigging hardware, not a video course."),
    ("Test On Site", "Written and practical test-out in our own NCCER accredited assessment center."),
    ("$150 Assessments, 36 Crafts", "One flat price to test out of any craft we assess, by appointment."),
    ("Day, Night Or Weekend", "Four weekdays, four nights, or one Friday-to-Sunday weekend."),
    ("Transparent Pricing", "Course and assessment prices are published right here. No quotes, no surprises."),
    ("Payment Plans, No Credit Check", "In-house financing from $200 down, plus Klarna, Afterpay and Zelle."),
]
