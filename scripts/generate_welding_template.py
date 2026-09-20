"""
Generate qc-question-template-Welding.xlsx with 100 Aramco-aligned Welding QC questions.
60 MCQ, 20 Essay, 20 Oral-Practical questions.
Difficulty: Exactly 50% Easy (50 Easy, 34 Moderate, 16 Difficult).
Options in MCQs are strictly length-balanced.
"""
import sys
import os
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

# Ensure we can import question_import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import question_import

HEADERS = [
    'Discipline',
    'Question type',
    'Question',
    'Multiple Choice options',
    'Correct answer',
    'Scoring rubric',
    'Subject',
    'Sub-subject',
    'Scored question',
    'Difficulty',
    'Topic group',
    'Delivery stage'
]

# List of 100 questions (20 topics x 5 questions each: 3 MCQ, 1 Essay, 1 Oral-Practical)
QUESTIONS_DATA = [
    # -------------------------------------------------------------------------
    # TOPIC 01: Aramco Welding Standard Hierarchy & Specifications
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Which Saudi Aramco Engineering Standard specifies mandatory welding requirements for onshore process piping systems?",
        "options": [
            "SAES-W-011 Welding Requirements Onshore Piping",
            "SAES-W-012 Welding Requirements Cross Pipelines",
            "SAES-W-010 Welding Requirements Pressure Vessel",
            "SAES-A-206 Positive Material Traceability Rules"
        ],
        "correct": "SAES-W-011 Welding Requirements Onshore Piping",
        "rubric": "Verify standard classification under Saudi Aramco Engineering Standards hierarchy.",
        "subject": "Welding Metallurgy & Standards",
        "sub_subject": "Aramco Standard Hierarchy",
        "difficulty": "easy",
        "topic": "Topic 01: Aramco Welding Hierarchy"
    },
    {
        "type": "mcq",
        "question": "Which document governs welding procedure specification (WPS) review and approval protocol across Saudi Aramco projects?",
        "options": [
            "SAEP-302 Instruction for WPS and PQR Approval",
            "SAEP-381 Project Quality Plan Assessment Rules",
            "SAEP-1142 NDT Personnel Qualification Protocol",
            "SAEP-1150 Execution of Field Welding Inspection"
        ],
        "correct": "SAEP-302 Instruction for WPS and PQR Approval",
        "rubric": "Verify procedure review and approval workflow per SAEP-302.",
        "subject": "Welding Metallurgy & Standards",
        "sub_subject": "Aramco Procedure Approval",
        "difficulty": "easy",
        "topic": "Topic 01: Aramco Welding Hierarchy"
    },
    {
        "type": "mcq",
        "question": "When resolving conflicting requirements between ASME B31.3 and SAES-W-011 for onshore piping, which governs on Aramco jobs?",
        "options": [
            "SAES-W-011 requirement governs unless formal waiver is approved",
            "ASME B31.3 standard governs automatically as international standard",
            "Contractor internal specification governs if approved by inspector",
            "Lowest cost requirement governs after joint engineering review"
        ],
        "correct": "SAES-W-011 requirement governs unless formal waiver is approved",
        "rubric": "Apply standard priority rules per Saudi Aramco engineering governance.",
        "subject": "Welding Metallurgy & Standards",
        "sub_subject": "Standard Precedence & Conflicts",
        "difficulty": "moderate",
        "topic": "Topic 01: Aramco Welding Hierarchy"
    },
    {
        "type": "essay",
        "question": "Explain the hierarchy of engineering documents applicable to field welding quality control on Saudi Aramco projects. Detail the step-by-step procedure required when a conflict arises between Saudi Aramco Engineering Standards (SAES), Project Specifications, and International Codes (ASME/AWS).",
        "options": "",
        "correct": "Key hierarchy: 1. Saudi Aramco Directives/Waivers, 2. Project Specifications / SAMSS, 3. SAES standards (SAES-W-011/012), 4. Mandatory Industry Codes (ASME/AWS/API). Mandatory resolution steps: Identify conflict, log formal technical query (TQ), escalate to CSD/Company Inspector, obtain written waiver prior to proceeding.",
        "rubric": "1. Hierarchy Listing (2.5 pts): Correct order of SAES, SAMSS, Project Specs, and ASME/AWS codes.\n2. Conflict Resolution Workflow (2.5 pts): Detailed Technical Query (TQ) submittal and CSD involvement.\n3. Mandatory Waiver Rules (2.5 pts): Clarifies that SAES stringency overrides international codes unless CSD approval granted.\n4. Documentation & Sign-off (2.5 pts): Identifies required quality records and approval documentation.",
        "subject": "Welding Metallurgy & Standards",
        "sub_subject": "Aramco Standard Hierarchy",
        "difficulty": "easy",
        "topic": "Topic 01: Aramco Welding Hierarchy"
    },
    {
        "type": "oral_practical",
        "question": "Using the provided Saudi Aramco standard portfolio binder, locate the governing welding standard for a cross-country crude oil pipeline. Verbally explain to the reviewer the document hierarchy, identify two key differences between pipeline and onshore piping standards, and record the exact standard number on the inspection log.",
        "options": "",
        "correct": "Candidate correctly selects SAES-W-012 for cross-country pipelines, explains precedence over API 1104, cites differences in NDT coverage (100% RT/UT) and essential variable limits, and records 'SAES-W-012' correctly.",
        "rubric": "1. Document Identification (2.5 pts): Correctly selects SAES-W-012 from binder.\n2. Hierarchy Explanation (2.5 pts): Articulates relationship with API 1104 and SAES-W-011.\n3. Comparative Differences (2.5 pts): Identifies specific SAES-W-012 requirements (e.g., API 1104 vs ASME B31.3 scope).\n4. Log Entry (2.5 pts): Documents correct specification reference on inspection report.",
        "subject": "Welding Metallurgy & Standards",
        "sub_subject": "Aramco Standard Hierarchy",
        "difficulty": "easy",
        "topic": "Topic 01: Aramco Welding Hierarchy"
    },

    # -------------------------------------------------------------------------
    # TOPIC 02: ASME Section IX WPS & PQR Essential Variables
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Per ASME Section IX QW-403.6, which change in base metal thickness qualified requires requalification of a WPS for impact-tested applications?",
        "options": [
            "A decrease in qualified base metal thickness below T minimum",
            "An increase in joint bevel angle from thirty to forty degrees",
            "A decrease in shielding gas cup size during welding operations",
            "An increase in stringer bead width by two electrode diameters"
        ],
        "correct": "A decrease in qualified base metal thickness below T minimum",
        "rubric": "Verify against ASME Section IX QW-403.6 essential variable rules for impact testing.",
        "subject": "WPS & PQR Qualification",
        "sub_subject": "ASME IX Essential Variables",
        "difficulty": "easy",
        "topic": "Topic 02: ASME IX WPS/PQR"
    },
    {
        "type": "mcq",
        "question": "Per ASME Section IX Table QW-256 for GTAW, which change is classified as a supplementary essential variable for impact testing?",
        "options": [
            "A change in heat input exceeding qualified maximum limits",
            "A change from direct current straight to reverse polarity",
            "A change in tungsten electrode diameter by one millimeter",
            "A change in joint cleaning method from brushing to grinding"
        ],
        "correct": "A change in heat input exceeding qualified maximum limits",
        "rubric": "Verify against ASME Section IX QW-409.1 and Table QW-256.",
        "subject": "WPS & PQR Qualification",
        "sub_subject": "ASME IX Supplementary Variables",
        "difficulty": "easy",
        "topic": "Topic 02: ASME IX WPS/PQR"
    },
    {
        "type": "mcq",
        "question": "Per SAES-W-011 and ASME IX, what is the maximum heat input increase permitted on a WPS without requalification when impact testing is required?",
        "options": [
            "Zero percent increase over maximum heat input tested on PQR",
            "Ten percent increase over maximum heat input tested on PQR",
            "Twenty percent increase over maximum heat input tested on PQR",
            "Fifteen percent increase over maximum heat input tested on PQR"
        ],
        "correct": "Zero percent increase over maximum heat input tested on PQR",
        "rubric": "Verify heat input limits per SAES-W-011 and ASME Section IX QW-409.1.",
        "subject": "WPS & PQR Qualification",
        "sub_subject": "Heat Input Limits",
        "difficulty": "moderate",
        "topic": "Topic 02: ASME IX WPS/PQR"
    },
    {
        "type": "essay",
        "question": "Review a proposed Welding Procedure Specification (WPS) against its supporting Procedure Qualification Record (PQR) for SMAW on low-temperature P-No. 1 steel. Detail the key essential and supplementary essential variables that must be audited per ASME Section IX and SAES-W-011.",
        "options": "",
        "correct": "Essential variables: Base metal P-No/Group-No, thickness qualified (QW-403), filler metal F-No/A-No (QW-404), PWHT status/temp range (QW-407). Supplementary variables (Impact tested): Preheat/interpass max temp, heat input (kJ/mm) calculated per pass (QW-409.1), electrode diameter range.",
        "rubric": "1. Base Metal & Thickness Limits (2.5 pts): Correctly evaluates P-No, Group-No, and thickness limits per QW-451.\n2. Filler Metal Variables (2.5 pts): Verifies F-Number, A-Number, AWS classification, and diameter limits.\n3. Thermal Controls (2.5 pts): Audits preheat, maximum interpass temperature, and PWHT hold parameters.\n4. Heat Input & Impact Testing (2.5 pts): Calculates heat input formula (V*A*60/S) and enforces zero increase limit for SAES-W-011.",
        "subject": "WPS & PQR Qualification",
        "sub_subject": "WPS Audit & Verification",
        "difficulty": "moderate",
        "topic": "Topic 02: ASME IX WPS/PQR"
    },
    {
        "type": "oral_practical",
        "question": "Examine the provided WPS and supporting PQR test coupon documentation. Verify if the WPS parameters (current, voltage, travel speed, preheat) correctly support welding a 12mm thick P-No. 1 pipe joint requiring toughness testing at -29°C. Verbally explain your findings to the reviewer and record your verdict.",
        "options": "",
        "correct": "Candidate performs heat input calculation on PQR data, compares qualified thickness range (QW-451.1) and interpass limits against WPS parameters, identifies any discrepancy, and logs pass/fail verdict with clause citations.",
        "rubric": "1. Thickness Qualification Check (2.5 pts): Verifies PQR coupon thickness covers 12mm.\n2. Heat Input Calculation (2.5 pts): Accurately calculates heat input for PQR and WPS ranges.\n3. Thermal Limit Verification (2.5 pts): Audits preheat and maximum interpass temperature requirements.\n4. Defend Findings & Sign-off (2.5 pts): Verbally articulates compliance verdict with code references.",
        "subject": "WPS & PQR Qualification",
        "sub_subject": "WPS Audit & Verification",
        "difficulty": "easy",
        "topic": "Topic 02: ASME IX WPS/PQR"
    },

    # -------------------------------------------------------------------------
    # TOPIC 03: Welder Performance Qualification (WPQ/WQR) & Continuity
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Per ASME Section IX QW-301.2, what is the primary purpose of a Welder Performance Qualification (WPQ) test?",
        "options": [
            "To verify welder ability to deposit sound weld metal properly",
            "To verify mechanical property strength of base metal joint",
            "To verify toughness impact values of filler metal deposits",
            "To qualify welding machine electrical output calibration accuracy"
        ],
        "correct": "To verify welder ability to deposit sound weld metal properly",
        "rubric": "Verify purpose of performance qualification per ASME IX QW-301.2.",
        "subject": "Welder Qualification",
        "sub_subject": "WPQ Purpose & Criteria",
        "difficulty": "easy",
        "topic": "Topic 03: Welder Qualification"
    },
    {
        "type": "mcq",
        "question": "Per ASME Section IX QW-322.1 and SAES-W-011, what is the maximum period a welder can remain inactive before qualification expires?",
        "options": [
            "Six consecutive months without using qualified process",
            "Three consecutive months without using qualified process",
            "Twelve consecutive months without using qualified process",
            "Thirty consecutive days without using qualified process"
        ],
        "correct": "Six consecutive months without using qualified process",
        "rubric": "Verify continuity requirements under ASME IX QW-322.1 and SAES-W-011.",
        "subject": "Welder Qualification",
        "sub_subject": "Welder Continuity Rules",
        "difficulty": "easy",
        "topic": "Topic 03: Welder Qualification"
    },
    {
        "type": "mcq",
        "question": "A welder qualifies on a 2-inch NPS (60.3 mm OD) pipe coupon in 6G position. Per ASME IX QW-452.3, what diameter range is qualified?",
        "options": [
            "Qualified for 1 inch NPS and all larger outer diameters",
            "Qualified for 2 inch NPS up to 12 inch outer diameter",
            "Qualified for 1/2 inch NPS up to unlimited outer diameter",
            "Qualified for exact coupon diameter of 2 inch NPS only"
        ],
        "correct": "Qualified for 1 inch NPS and all larger outer diameters",
        "rubric": "Verify qualified diameter range per ASME IX QW-452.3.",
        "subject": "Welder Qualification",
        "sub_subject": "Qualified Ranges",
        "difficulty": "moderate",
        "topic": "Topic 03: Welder Qualification"
    },
    {
        "type": "essay",
        "question": "Detail the essential variables for Welder Performance Qualification (WPQ) under ASME Section IX QW-350. Explain how a Welding QC Inspector verifies and maintains welder continuity records on a Saudi Aramco project site per SAES-W-011.",
        "options": "",
        "correct": "WPQ essential variables (QW-350): Deletion of backing, change in welding process, change in F-Number, change in base metal thickness/diameter qualified, change in position (QW-405), change in vertical direction (uphill/downhill). Continuity (QW-322): Inspector audits monthly welder log, verifies process used every 6 months, updates quality database, issues requalification if inactive >6 months or due to questionable workmanship.",
        "rubric": "1. Essential Variable Identification (2.5 pts): Lists process, backing, F-No, thickness/diameter, position, and progression.\n2. Qualified Limits Application (2.5 pts): Details thickness and diameter ranges per QW-452 tables.\n3. Continuity Verification Protocol (2.5 pts): Describes 6-month log maintenance and audit checks.\n4. Revocation & Re-testing Rules (2.5 pts): Details procedures for performance failure or extended inactivity.",
        "subject": "Welder Qualification",
        "sub_subject": "WPQ Audit & Continuity",
        "difficulty": "easy",
        "topic": "Topic 03: Welder Qualification"
    },
    {
        "type": "oral_practical",
        "question": "Review the provided Welder Qualification Test Record (WQR) card against a target production weld joint description (6-inch NPS, Schedule 80, P-No. 1, 6G position, GTAW root + SMAW fill). Verbally determine if the welder is qualified, check the continuity log for validity, and record your approval/rejection.",
        "options": "",
        "correct": "Candidate checks WQR parameters: process (GTAW/SMAW), F-No (F6/F4), thickness (t=9.5mm qualifies up to 19mm), diameter (NPS 6 qualifies NPS 2.875+), position (6G qualifies all), checks continuity date within 6 months, signs off report.",
        "rubric": "1. Essential Variable Audit (2.5 pts): Verifies process, F-No, position, and progression.\n2. Dimensional Range Check (2.5 pts): Confirms thickness and diameter limits per QW-452.\n3. Continuity Validity Check (2.5 pts): Audits 6-month continuity entry dates.\n4. Recommendation & Sign-off (2.5 pts): Verbally defends decision and completes inspection log.",
        "subject": "Welder Qualification",
        "sub_subject": "WQR Verification Walkthrough",
        "difficulty": "moderate",
        "topic": "Topic 03: Welder Qualification"
    },

    # -------------------------------------------------------------------------
    # TOPIC 04: Base Metals (P-Numbers) & Filler Metals (F-Numbers / A-Numbers)
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Per ASME Section IX QW-420, which P-Number classification is assigned to carbon-manganese structural and piping steels?",
        "options": [
            "P-Number 1 carbon steel base metal group",
            "P-Number 3 alloy steel base metal group",
            "P-Number 8 stainless steel base metal group",
            "P-Number 4 chrome moly steel base metal group"
        ],
        "correct": "P-Number 1 carbon steel base metal group",
        "rubric": "Verify base metal P-Number grouping per ASME IX Table QW/QB-422.",
        "subject": "Materials & Consumables",
        "sub_subject": "Base Metal P-Numbers",
        "difficulty": "easy",
        "topic": "Topic 04: Base & Filler Metals"
    },
    {
        "type": "mcq",
        "question": "Per ASME Section IX Table QW-432, which F-Number is assigned to low-hydrogen SMAW electrodes such as E7018?",
        "options": [
            "F-Number 4 carbon steel low hydrogen electrodes",
            "F-Number 3 carbon steel cellulosic electrodes",
            "F-Number 6 solid bare wire GTAW carbon steel",
            "F-Number 5 austenitic stainless steel electrodes"
        ],
        "correct": "F-Number 4 carbon steel low hydrogen electrodes",
        "rubric": "Verify electrode F-Number grouping per ASME IX Table QW-432.",
        "subject": "Materials & Consumables",
        "sub_subject": "Filler Metal F-Numbers",
        "difficulty": "easy",
        "topic": "Topic 04: Base & Filler Metals"
    },
    {
        "type": "mcq",
        "question": "Which AWS classification represents a carbon steel GTAW filler rod with 70 ksi tensile strength and impact toughness at -30°C?",
        "options": [
            "ER70S-6 solid steel gas tungsten arc wire",
            "E7018-1 low hydrogen shielded metal arc rod",
            "E6010 cellulosic shielded metal arc electrode",
            "ER308L stainless steel gas tungsten arc wire"
        ],
        "correct": "ER70S-6 solid steel gas tungsten arc wire",
        "rubric": "Identify AWS filler metal designation per AWS A5.18.",
        "subject": "Materials & Consumables",
        "sub_subject": "AWS Filler Classifications",
        "difficulty": "moderate",
        "topic": "Topic 04: Base & Filler Metals"
    },
    {
        "type": "essay",
        "question": "Explain the technical rationale behind the ASME Section IX grouping systems for base metals (P-Numbers and Group-Numbers) and filler metals (F-Numbers and A-Numbers). Discuss how changes in these groupings affect WPS requalification per SAES-W-011.",
        "options": "",
        "correct": "P-Numbers group base metals by weldability and chemical/mechanical properties to minimize qualification tests. Group-Numbers refine P-Numbers for impact testing requirements. F-Numbers group electrodes by usability characteristics (arc stability, manipulation difficulty). A-Numbers classify ferrous weld metal chemical composition. SAES-W-011 rules: Any change in P-No is essential; change in Group-No is essential for impact-tested WPS; change in F-No requires WPS/WPQ requalification.",
        "rubric": "1. P-Number & Group-Number Rationale (2.5 pts): Details metallurgical and weldability basis.\n2. F-Number & A-Number Rationale (2.5 pts): Explains usability characteristics and chemical composition classification.\n3. Impact Testing Implications (2.5 pts): Clarifies role of Group-Numbers in toughness qualification.\n4. SAES-W-011 Requalification Enforcements (2.5 pts): Cites specific requalification triggers for P/F/A changes.",
        "subject": "Materials & Consumables",
        "sub_subject": "Grouping Systems & Requalification",
        "difficulty": "moderate",
        "topic": "Topic 04: Base & Filler Metals"
    },
    {
        "type": "oral_practical",
        "question": "Inspect the provided physical filler metal storage rack. Verify that the electrode boxes (E7018-1, E6010, ER70S-6, ER309L) match their Mill Test Certificates (MTC), identify their corresponding P-No, F-No, and A-No classifications, and record your material verification results.",
        "options": "",
        "correct": "Candidate matches heat numbers on wire/electrodes to MTCs, assigns E7018-1 (F4, A1), E6010 (F3, A1), ER70S-6 (F6, A1), ER309L (F5, A8), verifies chemical composition against AWS specs, and logs sign-off.",
        "rubric": "1. Physical Tag & MTC Verification (2.5 pts): Cross-references heat numbers and AWS designations accurately.\n2. F-Number & A-Number Assignment (2.5 pts): Correctly identifies F-No and A-No for each consumable.\n3. Base Metal Compatibility Check (2.5 pts): Explains which base metal P-No each filler matches.\n4. Documentation Completeness (2.5 pts): Fills material receiving inspection sheet accurately.",
        "subject": "Materials & Consumables",
        "sub_subject": "Consumable Receiving Inspection",
        "difficulty": "easy",
        "topic": "Topic 04: Base & Filler Metals"
    },

    # -------------------------------------------------------------------------
    # TOPIC 05: Welding Consumable Baking, Storage & Low-Hydrogen Handling
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Per SAES-W-011 Table 1, what is the mandatory baking temperature range for low-hydrogen SMAW electrodes (E7018) prior to issue?",
        "options": [
            "260 to 430 degrees Celsius for two hours minimum",
            "120 to 150 degrees Celsius for four hours minimum",
            "500 to 600 degrees Celsius for one hour minimum",
            "80 to 100 degrees Celsius for thirty minutes total"
        ],
        "correct": "260 to 430 degrees Celsius for two hours minimum",
        "rubric": "Verify electrode baking parameters per SAES-W-011 Table 1.",
        "subject": "Consumable Control",
        "sub_subject": "Electrode Baking Requirements",
        "difficulty": "easy",
        "topic": "Topic 05: Consumable Handling"
    },
    {
        "type": "mcq",
        "question": "Per SAES-W-011, what is the minimum holding oven temperature for low-hydrogen electrodes after completion of baking?",
        "options": [
            "120 degrees Celsius minimum temperature holding oven",
            "60 degrees Celsius minimum temperature holding oven",
            "200 degrees Celsius minimum temperature holding oven",
            "40 degrees Celsius minimum temperature holding oven"
        ],
        "correct": "120 degrees Celsius minimum temperature holding oven",
        "rubric": "Verify holding oven temperature requirements per SAES-W-011.",
        "subject": "Consumable Control",
        "sub_subject": "Holding Oven Controls",
        "difficulty": "easy",
        "topic": "Topic 05: Consumable Handling"
    },
    {
        "type": "mcq",
        "question": "Per SAES-W-011, what is the maximum atmospheric exposure limit for low-hydrogen electrodes (E7018) after removal from portable quivers?",
        "options": [
            "Four hours maximum exposure before re-baking is required",
            "Eight hours maximum exposure before re-baking is required",
            "Two hours maximum exposure before re-baking is required",
            "Twelve hours maximum exposure before re-baking is required"
        ],
        "correct": "Four hours maximum exposure before re-baking is required",
        "rubric": "Verify exposure time limits for low-H electrodes per SAES-W-011.",
        "subject": "Consumable Control",
        "sub_subject": "Atmospheric Exposure Time",
        "difficulty": "difficult",
        "topic": "Topic 05: Consumable Handling"
    },
    {
        "type": "essay",
        "question": "Describe the complete low-hydrogen consumable control workflow on a Saudi Aramco project site from receiving at the central warehouse to issue at the field welding station. Include baking cycles, holding oven temperatures, portable quiver requirements, atmospheric exposure limits, and re-baking restrictions per SAES-W-011.",
        "options": "",
        "correct": "Workflow: 1. Receiving check of hermetically sealed cans (unopened cans don't need baking unless damaged). 2. Baking: Open cans baked at 260-430°C for 2 hrs min in calibrated oven. 3. Storage/Holding: Transferred to holding oven at 120°C min. 4. Field Issue: Issued to welders in heated portable quivers (65°C min). 5. Atmospheric Exposure: Max 4 hrs exposure. Exposed electrodes must be re-baked (max 1 re-bake cycle allowed, after which they must be scrapped).",
        "rubric": "1. Receiving & Storage Requirements (2.5 pts): Details hermetic packaging rules and warehouse conditions.\n2. Baking & Holding Parameters (2.5 pts): Cites 260-430°C baking and 120°C holding oven rules accurately.\n3. Field Quiver & Exposure Controls (2.5 pts): Explains 65°C portable quiver requirement and 4-hour exposure limit.\n4. Re-baking Limits & Scrapping (2.5 pts): Identifies one-time re-bake maximum and scrap criteria.",
        "subject": "Consumable Control",
        "sub_subject": "Low-H Handling Workflow",
        "difficulty": "easy",
        "topic": "Topic 05: Consumable Handling"
    },
    {
        "type": "oral_practical",
        "question": "Perform a physical audit of the jobsite electrode storage station. Inspect the baking oven temperature recorder, holding oven digital readout, welder portable quivers, and electrode issue log. Identify any non-conformances against SAES-W-011 and record your audit report.",
        "options": "",
        "correct": "Candidate checks baking oven chart (verifies 260-430°C cycle), holding oven temp (verifies >=120°C), quiver temperature (verifies plugged in / >=65°C), checks issue log for 4-hr return tracking, identifies any unheated quiver or missing log entry, logs findings.",
        "rubric": "1. Oven Temperature Verification (2.5 pts): Checks baking chart recorder and holding oven readouts.\n2. Portable Quiver Check (2.5 pts): Verifies quiver power connection and temperature.\n3. Exposure & Log Audit (2.5 pts): Audits time-in/time-out entries on field issue log.\n4. NCR Identification & Sign-off (2.5 pts): Correctly flags violations and writes audit report.",
        "subject": "Consumable Control",
        "sub_subject": "Consumable Audit Walkthrough",
        "difficulty": "easy",
        "topic": "Topic 05: Consumable Handling"
    },

    # -------------------------------------------------------------------------
    # TOPIC 06: Preheat, Interpass Temperature & Heat Input Controls
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Per SAES-W-011, what is the minimum preheat temperature required for welding P-No. 1 carbon steel with wall thickness exceeding 25 mm?",
        "options": [
            "95 degrees Celsius minimum preheat temperature",
            "50 degrees Celsius minimum preheat temperature",
            "150 degrees Celsius minimum preheat temperature",
            "10 degrees Celsius minimum preheat temperature"
        ],
        "correct": "95 degrees Celsius minimum preheat temperature",
        "rubric": "Verify preheat rules per SAES-W-011 Table 2.",
        "subject": "Preheat & Thermal Control",
        "sub_subject": "Preheat Requirements",
        "difficulty": "easy",
        "topic": "Topic 06: Preheat & Thermal Control"
    },
    {
        "type": "mcq",
        "question": "Per SAES-W-011, what is the maximum allowable interpass temperature for impact-tested P-No. 1 carbon steel piping?",
        "options": [
            "230 degrees Celsius maximum interpass temperature",
            "350 degrees Celsius maximum interpass temperature",
            "150 degrees Celsius maximum interpass temperature",
            "400 degrees Celsius maximum interpass temperature"
        ],
        "correct": "230 degrees Celsius maximum interpass temperature",
        "rubric": "Verify maximum interpass temperature limits per SAES-W-011.",
        "subject": "Preheat & Thermal Control",
        "sub_subject": "Interpass Temperature Limits",
        "difficulty": "moderate",
        "topic": "Topic 06: Preheat & Thermal Control"
    },
    {
        "type": "mcq",
        "question": "Which combination of parameters is used to calculate arc heat input (kJ/mm) during welding quality monitoring?",
        "options": [
            "Voltage times current times sixty divided by speed",
            "Voltage times resistance times travel speed total",
            "Current divided by voltage times travel speed total",
            "Voltage times current times travel speed total"
        ],
        "correct": "Voltage times current times sixty divided by speed",
        "rubric": "Apply heat input formula: H = (V * I * 60) / (S * 1000).",
        "subject": "Preheat & Thermal Control",
        "sub_subject": "Heat Input Formula",
        "difficulty": "difficult",
        "topic": "Topic 06: Preheat & Thermal Control"
    },
    {
        "type": "essay",
        "question": "Explain the metallurgical purpose of preheat and interpass temperature controls during structural and piping weld operations. Describe how heat input is monitored in the field, including temperature measurement techniques, distance requirements from the joint, and action required if interpass temperature exceeds qualified WPS limits.",
        "options": "",
        "correct": "Purpose of Preheat: Slows cooling rate, promotes hydrogen diffusion out of weld, reduces risk of hydrogen-assisted cracking (HAC/cold cracking), reduces residual stress. Purpose of Interpass Control: Prevents grain coarsening, maintains yield strength and impact toughness. Field Monitoring: Measured using calibrated pyrometer or temp chalks at least 75mm (3 in) from bevel edge. If max interpass temp exceeded: Welding must pause immediately until joint cools below max limit.",
        "rubric": "1. Metallurgical Rationale (2.5 pts): Details cooling rate control, hydrogen diffusion, and stress reduction.\n2. Interpass & Toughness Effects (2.5 pts): Explains impact of high interpass temp on grain size and toughness.\n3. Measurement Technique (2.5 pts): Specifies pyrometer/temp chalk usage and 75mm distance requirement.\n4. Non-conformance Action (2.5 pts): Outlines immediate stoppage and cooling requirements when limit exceeded.",
        "subject": "Preheat & Thermal Control",
        "sub_subject": "Preheat & Heat Input Theory",
        "difficulty": "moderate",
        "topic": "Topic 06: Preheat & Thermal Control"
    },
    {
        "type": "oral_practical",
        "question": "Using an infrared pyrometer and temp-stik chalks, perform a preheat and interpass temperature check on a production pipe weld joint. Calculate the heat input for the root pass based on observed voltmeter, ammeter, and stopwatch readings, compare against WPS requirements, and log your findings.",
        "options": "",
        "correct": "Candidate checks preheat temp at 75mm from joint, verifies pyrometer calibration, measures voltage (V), current (A), and travel speed (mm/min), calculates heat input H = (V*A*60)/(S*1000) in kJ/mm, checks against WPS limits, and records values.",
        "rubric": "1. Instrument Selection & Distance (2.5 pts): Verifies pyrometer calibration and measures at >=75mm distance.\n2. Preheat & Interpass Check (2.5 pts): Accurately reads temperature before pass starts.\n3. Heat Input Calculation (2.5 pts): Correctly measures V, A, speed and calculates kJ/mm accurately.\n4. WPS Compliance Verification (2.5 pts): Compares results to WPS parameters and signs report.",
        "subject": "Preheat & Thermal Control",
        "sub_subject": "Field Heat Input Verification",
        "difficulty": "easy",
        "topic": "Topic 06: Preheat & Thermal Control"
    },

    # -------------------------------------------------------------------------
    # TOPIC 07: Post Weld Heat Treatment (PWHT) & Hardness Testing (SAES-W-011)
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Per SAES-W-011, what is the nominal wall thickness threshold requiring mandatory PWHT for carbon steel (P-No. 1) piping?",
        "options": [
            "Wall thickness exceeding nineteen millimeters",
            "Wall thickness exceeding twenty five millimeters",
            "Wall thickness exceeding twelve millimeters",
            "Wall thickness exceeding thirty eight millimeters"
        ],
        "correct": "Wall thickness exceeding nineteen millimeters",
        "rubric": "Verify PWHT thickness threshold per SAES-W-011 Table 3.",
        "subject": "PWHT & Hardness Testing",
        "sub_subject": "PWHT Thickness Threshold",
        "difficulty": "easy",
        "topic": "Topic 07: PWHT & Hardness"
    },
    {
        "type": "mcq",
        "question": "Per SAES-W-011, what is the maximum acceptable Vickers hardness (HV10) for production welds on sour service carbon steel piping?",
        "options": [
            "200 HV10 maximum allowable hardness value",
            "250 HV10 maximum allowable hardness value",
            "300 HV10 maximum allowable hardness value",
            "180 HV10 maximum allowable hardness value"
        ],
        "correct": "200 HV10 maximum allowable hardness value",
        "rubric": "Verify hardness limits for sour service per SAES-W-011 and NACE MR0175.",
        "subject": "PWHT & Hardness Testing",
        "sub_subject": "Sour Service Hardness Limits",
        "difficulty": "moderate",
        "topic": "Topic 07: PWHT & Hardness"
    },
    {
        "type": "mcq",
        "question": "During PWHT chart review, what is the maximum heating rate permitted above 400°C for P-No. 1 pipe per ASME B31.3?",
        "options": [
            "222 degrees Celsius per hour divided by thickness",
            "100 degrees Celsius per hour total fixed rate",
            "300 degrees Celsius per hour total fixed rate",
            "50 degrees Celsius per hour divided by thickness"
        ],
        "correct": "222 degrees Celsius per hour divided by thickness",
        "rubric": "Verify PWHT heating rate formula per ASME B31.3 / SAES-W-011.",
        "subject": "PWHT & Hardness Testing",
        "sub_subject": "PWHT Heating Rate Rules",
        "difficulty": "difficult",
        "topic": "Topic 07: PWHT & Hardness"
    },
    {
        "type": "essay",
        "question": "Detail the Quality Control requirements for Post Weld Heat Treatment (PWHT) on a sour service carbon steel piping system per SAES-W-011 and ASME B31.3. Cover thermocouple placement, heating/cooling rates, soak temperature and hold time, production hardness testing (Vickers/Brinell), and acceptance criteria.",
        "options": "",
        "correct": "PWHT QC Requirements: 1. Thermocouple placement: Minimum 2 TCs on weld/HAZ (top and bottom for pipe). 2. Heating/Cooling rates: Max 222°C/hr / (t in inches) above 400°C. 3. Soak Temp & Time: 600-650°C for 1 hr per inch of thickness (1 hr min). 4. Hardness Testing: 100% production hardness testing for sour service; Max 200 HV10 (or 225 BHN) for weld metal and HAZ per SAES-W-011 and NACE MR0175.",
        "rubric": "1. PWHT Temperature & Hold Parameters (2.5 pts): Details soak temp (600-650°C) and hold time calculation.\n2. Thermocouple Placement & Control (2.5 pts): Specifies TC quantity, location, and temperature gradient limits.\n3. Heating & Cooling Rate Rules (2.5 pts): Calculates maximum heating/cooling rate formulas accurately.\n4. Hardness Testing & NACE Limits (2.5 pts): Cites 200 HV10 / 225 BHN limits and NDT post-PWHT requirements.",
        "subject": "PWHT & Hardness Testing",
        "sub_subject": "PWHT Protocol & Hardness Review",
        "difficulty": "moderate",
        "topic": "Topic 07: PWHT & Hardness"
    },
    {
        "type": "oral_practical",
        "question": "Review the provided PWHT chart recording and production hardness test report for a spool piece joint. Verify soak temperature, hold time, heating/cooling rates, thermocouple spread, and hardness readings against SAES-W-011. Verbally explain your audit evaluation and sign the inspection report.",
        "options": "",
        "correct": "Candidate checks chart: start/end soak times, min/max soak temp (600-650°C), calculates heating/cooling slopes, checks max temp differential between TCs (<25°C), reviews Telebrineller/Telebrinell hardness report (checks all points <=200 HV / 225 BHN), flags pass/fail.",
        "rubric": "1. PWHT Chart Parameter Audit (2.5 pts): Verifies soak temp, soak duration, and thermal gradients.\n2. Heating/Cooling Slope Calculation (2.5 pts): Audits rate of temperature change against code limits.\n3. Production Hardness Report Audit (2.5 pts): Evaluates weld and HAZ hardness values against NACE/SAES limits.\n4. Sign-off & Defend Verdict (2.5 pts): Verbally defends audit conclusions to reviewer.",
        "subject": "PWHT & Hardness Testing",
        "sub_subject": "PWHT Chart & Hardness Audit",
        "difficulty": "moderate",
        "topic": "Topic 07: PWHT & Hardness"
    },

    # -------------------------------------------------------------------------
    # TOPIC 08: Visual Inspection & Weld Discontinuities (ASME B31.3 / B31.1)
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Per ASME B31.3 for Normal Fluid Service, what is the maximum allowable depth of undercut on process piping?",
        "options": [
            "Lesser of 1 mm or 1/32 inch depth maximum",
            "Lesser of 1.5 mm or 1/16 inch depth maximum",
            "Lesser of 2 mm or 3/32 inch depth maximum",
            "Undercut is completely prohibited in all cases"
        ],
        "correct": "Lesser of 1 mm or 1/32 inch depth maximum",
        "rubric": "Verify visual inspection acceptance criteria per ASME B31.3 Table 341.3.2.",
        "subject": "Visual Inspection & Defects",
        "sub_subject": "Undercut Acceptance Limits",
        "difficulty": "easy",
        "topic": "Topic 08: Visual Inspection"
    },
    {
        "type": "mcq",
        "question": "Which weld surface flaw is classified as an automatic rejection during visual inspection under ASME B31.3?",
        "options": [
            "Crack or lack of surface fusion flaw",
            "Surface reinforcement of two millimeters",
            "Uniform ripple appearance across weld",
            "Slight oxidation discoloration on cover"
        ],
        "correct": "Crack or lack of surface fusion flaw",
        "rubric": "Verify zero tolerance defects per ASME B31.3 Table 341.3.2.",
        "subject": "Visual Inspection & Defects",
        "sub_subject": "Zero Tolerance Defects",
        "difficulty": "easy",
        "topic": "Topic 08: Visual Inspection"
    },
    {
        "type": "mcq",
        "question": "Per SAES-W-011, what is the maximum allowable internal misalignment (hi-lo) for butt joints prior to welding?",
        "options": [
            "1.5 mm maximum internal misalignment",
            "3.0 mm maximum internal misalignment",
            "0.5 mm maximum internal misalignment",
            "2.5 mm maximum internal misalignment"
        ],
        "correct": "1.5 mm maximum internal misalignment",
        "rubric": "Verify fit-up tolerances per SAES-W-011.",
        "subject": "Visual Inspection & Defects",
        "sub_subject": "Fit-Up Misalignment Limits",
        "difficulty": "moderate",
        "topic": "Topic 08: Visual Inspection"
    },
    {
        "type": "essay",
        "question": "List and describe five critical visual weld defects encountered during VT of girth welds on piping. For each defect, state the root cause, prevention measures, and acceptance/rejection criteria per ASME B31.3 Normal Fluid Service.",
        "options": "",
        "correct": "1. Cracks: Zero tolerance (Reject). Root cause: High restraint, hydrogen, excessive heat input. 2. Lack of Fusion: Zero tolerance (Reject). Root cause: Improper bevel cleaning, low current, poor technique. 3. Undercut: Max 1mm or 1/32 in (Pass/Fail depending on depth). Root cause: Excessive current, arc length, fast travel speed. 4. Incomplete Penetration: Max 38mm total in 150mm weld length, depth <= 1mm (ASME B31.3). Root cause: Small root gap, thick root face, low heat input. 5. Porosity: Max scattered porosity limits per code. Root cause: Contaminated shield gas, wet electrodes, wind.",
        "rubric": "1. Defect Identification & Causes (2.5 pts): Accurately describes 5 distinct surface defects and causes.\n2. Prevention Strategies (2.5 pts): Provides correct corrective actions and welding parameter adjustments.\n3. Acceptance Criteria Citation (2.5 pts): Cites ASME B31.3 Table 341.3.2 limits accurately.\n4. Repair Protocol (2.5 pts): Details excavation and repair inspection rules.",
        "subject": "Visual Inspection & Defects",
        "sub_subject": "Defect Root Causes & VT Criteria",
        "difficulty": "easy",
        "topic": "Topic 08: Visual Inspection"
    },
    {
        "type": "oral_practical",
        "question": "Using a Bridge Cam gauge, Hi-Lo gauge, fillet weld gauge, and flashlight, perform a complete visual inspection on the provided pipe coupon. Measure weld reinforcement height, undercut depth, internal misalignment, and fillet leg length. Log all readings on the VT report and declare pass/fail against ASME B31.3.",
        "options": "",
        "correct": "Candidate uses Hi-Lo gauge (reads internal alignment), Bridge Cam (reads reinforcement height and undercut depth), fillet gauge (reads leg size), records exact values, compares against ASME B31.3 Table 341.3.2, and fills VT report.",
        "rubric": "1. Gauge Handling Precision (2.5 pts): Correctly zeroes and applies Bridge Cam and Hi-Lo gauges.\n2. Measurement Accuracy (2.5 pts): Reads reinforcement, undercut, and misalignment within ±0.5mm.\n3. Code Acceptance Evaluation (2.5 pts): Accurately evaluates readings against ASME B31.3 limits.\n4. VT Report Completion (2.5 pts): Documents all measurements and signs formal inspection report.",
        "subject": "Visual Inspection & Defects",
        "sub_subject": "VT Practical Walkthrough",
        "difficulty": "easy",
        "topic": "Topic 08: Visual Inspection"
    },

    # -------------------------------------------------------------------------
    # TOPIC 09: Radiographic Testing (RT) & Film Quality (ASME V Art 2)
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Per ASME Section V Article 2, what is the mandatory density range for radiographic film exposed with an X-ray source?",
        "options": [
            "1.8 to 4.0 optical density units range",
            "1.0 to 2.5 optical density units range",
            "3.0 to 5.0 optical density units range",
            "0.5 to 1.5 optical density units range"
        ],
        "correct": "1.8 to 4.0 optical density units range",
        "rubric": "Verify RT film density limits per ASME V Article 2 T-282.1.",
        "subject": "NDT & Quality Evaluation",
        "sub_subject": "RT Film Density Range",
        "difficulty": "easy",
        "topic": "Topic 09: Radiographic Testing"
    },
    {
        "type": "mcq",
        "question": "Per ASME Section V Article 2, which image quality indicator (IQI) designation must appear on the essential hole/wire RT image?",
        "options": [
            "Specified wire size on source side IQI",
            "Specified hole size on film side IQI",
            "Any visible wire size on either side IQI",
            "Lead letter B image on front side IQI"
        ],
        "correct": "Specified wire size on source side IQI",
        "rubric": "Verify IQI placement and essential wire requirements per ASME V Art 2.",
        "subject": "NDT & Quality Evaluation",
        "sub_subject": "IQI Selection & Placement",
        "difficulty": "moderate",
        "topic": "Topic 09: Radiographic Testing"
    },
    {
        "type": "mcq",
        "question": "Per ASME B31.3 for Severe Cyclic Service, what is the acceptance criteria for internal root lack of penetration on RT film?",
        "options": [
            "Zero incomplete penetration allowed at all",
            "Maximum 25 mm total length in 300 mm weld",
            "Maximum 1 mm depth provided length is short",
            "Maximum 10 mm total length in 100 mm weld"
        ],
        "correct": "Zero incomplete penetration allowed at all",
        "rubric": "Verify strict NDT criteria for Severe Cyclic Service per ASME B31.3 Table 341.3.2.",
        "subject": "NDT & Quality Evaluation",
        "sub_subject": "RT Defect Acceptance Criteria",
        "difficulty": "difficult",
        "topic": "Topic 09: Radiographic Testing"
    },
    {
        "type": "essay",
        "question": "Explain the Quality Control steps for reviewing Radiographic Testing (RT) film quality prior to defect evaluation per ASME Section V Article 2 and ASME B31.3. Discuss densitometer calibration, geometric unsharpness limits, IQI sensitivity, backscatter check (Lead letter 'B'), and film artifacts.",
        "options": "",
        "correct": "RT Film Review Protocol: 1. Densitometer Calibration: Step wedge calibration check daily. 2. Film Density Check: 1.8-4.0 for X-ray, 2.0-4.0 for Gamma ray. 3. Geometric Unsharpness (Ug): Verified below max allowable (T-274). 4. IQI Sensitivity: Essential wire/hole clearly visible on source side (or film side with 'F'). 5. Backscatter Verification: Lead letter 'B' must NOT appear as light image on dark background. 6. Artifact Inspection: No scratches, chemical stains, or pressure marks interfering with weld area.",
        "rubric": "1. Densitometer & Density Verification (2.5 pts): Details step wedge check and density range (1.8-4.0).\n2. IQI Sensitivity & Location (2.5 pts): Explains essential wire selection and source/film side placement.\n3. Backscatter & Artifact Controls (2.5 pts): Details Lead letter 'B' rules and artifact discrimination.\n4. Geometric Unsharpness Rules (2.5 pts): Cites Ug formulas and code limit compliance.",
        "subject": "NDT & Quality Evaluation",
        "sub_subject": "RT Film Quality Review",
        "difficulty": "moderate",
        "topic": "Topic 09: Radiographic Testing"
    },
    {
        "type": "oral_practical",
        "question": "Using the provided viewer, densitometer, and calibrated step wedge, perform a complete RT film quality audit on three weld radiographic films. Measure density, check IQI wire visibility, inspect for backscatter 'B', identify indications (porosity, slag, crack, LOP), and log pass/fail against ASME B31.3.",
        "options": "",
        "correct": "Candidate calibrates densitometer on step wedge, measures weld and material density (1.8-4.0), verifies IQI wire, checks backscatter 'B', identifies defects (e.g. slag line > allowable length), records findings, and issues formal RT interpretation report.",
        "rubric": "1. Densitometer Calibration (2.5 pts): Performs zeroing and step wedge calibration correctly.\n2. Film Quality Verification (2.5 pts): Audits density, IQI wire visibility, and backscatter 'B' image.\n3. Indication Interpretation (2.5 pts): Accurately identifies defect type, location, and dimensions.\n4. ASME B31.3 Disposition (2.5 pts): Applies acceptance criteria correctly and signs RT log.",
        "subject": "NDT & Quality Evaluation",
        "sub_subject": "RT Interpretation Walkthrough",
        "difficulty": "easy",
        "topic": "Topic 09: Radiographic Testing"
    },

    # -------------------------------------------------------------------------
    # TOPIC 10: Ultrasonic Testing (UT) & Defect Sizing (ASME V Art 4)
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Per ASME Section V Article 4, which calibration block is standard for sweep range and DAC curve construction during manual UT of piping?",
        "options": [
            "Basic Calibration Block with side drilled holes",
            "IIW Type 1 block for angle beam calibration",
            "Step wedge block for thickness gauge checking",
            "AWS Resolution block for transducer testing"
        ],
        "correct": "Basic Calibration Block with side drilled holes",
        "rubric": "Verify UT calibration block requirements per ASME V Article 4 T-434.2.",
        "subject": "NDT & Quality Evaluation",
        "sub_subject": "UT Calibration Blocks",
        "difficulty": "easy",
        "topic": "Topic 10: Ultrasonic Testing"
    },
    {
        "type": "mcq",
        "question": "Per SAEP-1142, which advanced ultrasonic testing technique is mandated by Saudi Aramco for heavy-wall weld replacement of radiography?",
        "options": [
            "Phased Array UT combined with TOFD technique",
            "Manual straight beam longitudinal wave UT",
            "Electromagnetic acoustic transducer technique",
            "Surface acoustic wave flaw detection technique"
        ],
        "correct": "Phased Array UT combined with TOFD technique",
        "rubric": "Identify Aramco advanced NDT requirements per SAEP-1142 / SAES-W-011.",
        "subject": "NDT & Quality Evaluation",
        "sub_subject": "Advanced UT (PAUT/TOFD)",
        "difficulty": "moderate",
        "topic": "Topic 10: Ultrasonic Testing"
    },
    {
        "type": "mcq",
        "question": "During UT flaw sizing, which decibel drop technique is standard for measuring planar defect length per ASME Section V Article 4?",
        "options": [
            "Six decibel drop technique for defect sizing",
            "Twenty decibel drop technique for defect sizing",
            "Three decibel drop technique for defect sizing",
            "Twelve decibel drop technique for defect sizing"
        ],
        "correct": "Six decibel drop technique for defect sizing",
        "rubric": "Verify decibel drop flaw sizing methods per ASME V Article 4.",
        "subject": "NDT & Quality Evaluation",
        "sub_subject": "UT Defect Sizing Methods",
        "difficulty": "difficult",
        "topic": "Topic 10: Ultrasonic Testing"
    },
    {
        "type": "essay",
        "question": "Compare manual Ultrasonic Testing (UT) and Phased Array UT (PAUT) with Time-of-Flight Diffraction (TOFD) for weld quality inspection per SAEP-1142 and ASME Section V Article 4. Discuss calibration, flaw detection/sizing capability, data recordability, and Aramco approval requirements.",
        "options": "",
        "correct": "Comparison: Manual UT relies on operator skill, A-scan display, 6dB drop sizing, basic DAC curve calibration. PAUT/TOFD provides multi-angle electronic scanning, B/C/D-scan images, automated data recordability, precise height/length sizing via diffracted tip signals. SAEP-1142 mandates PAUT/TOFD operator qualification, scan plan approval, and validation block demonstration prior to field deployment.",
        "rubric": "1. Technical Comparison (2.5 pts): Details A-scan vs S-scan/E-scan capabilities accurately.\n2. Sizing Precision & TOFD (2.5 pts): Explains tip diffraction sizing and TOFD depth measurement advantage.\n3. Calibration & Data Recording (2.5 pts): Compares manual DAC vs PAUT encoder calibration and data storage.\n4. SAEP-1142 Approval Rules (2.5 pts): Details scan plan and operator qualification requirements.",
        "subject": "NDT & Quality Evaluation",
        "sub_subject": "PAUT vs Manual UT",
        "difficulty": "moderate",
        "topic": "Topic 10: Ultrasonic Testing"
    },
    {
        "type": "oral_practical",
        "question": "Review the provided PAUT scan data file and calibration setup sheet for a 25mm thickness pipe weld joint. Identify the indication depth, height, and length from the S-scan and TOFD views. Evaluate against ASME Section VIII Div 1 Appendix 12 / SAES-W-011 and log your report verdict.",
        "options": "",
        "correct": "Candidate inspects PAUT scan data, verifies encoder calibration, measures flaw start/end depth via TOFD diffracted signals, calculates flaw length and height, compares against acceptance criteria, and issues UT evaluation report.",
        "rubric": "1. Scan Data & Setup Review (2.5 pts): Audits wedge delay, velocity, and encoder calibration setup.\n2. Flaw Location & Depth (2.5 pts): Accurately determines depth from surface and axial position.\n3. Flaw Sizing Precision (2.5 pts): Measures height and length using TOFD cursor tools accurately.\n4. Disposition & Sign-off (2.5 pts): Evaluates against code acceptance criteria and signs report.",
        "subject": "NDT & Quality Evaluation",
        "sub_subject": "PAUT Data Interpretation Walkthrough",
        "difficulty": "difficult",
        "topic": "Topic 10: Ultrasonic Testing"
    },

    # -------------------------------------------------------------------------
    # TOPIC 11: Liquid Penetrant (PT) & Magnetic Particle (MT) Examination
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Per ASME Section V Article 6, what is the minimum dwell time required for visible solvent-removable liquid penetrant on steel joints?",
        "options": [
            "Ten minutes minimum penetrant dwell time",
            "Five minutes minimum penetrant dwell time",
            "Twenty minutes minimum penetrant dwell time",
            "Thirty minutes minimum penetrant dwell time"
        ],
        "correct": "Ten minutes minimum penetrant dwell time",
        "rubric": "Verify PT dwell time rules per ASME V Article 6 Table T-672.",
        "subject": "NDT & Quality Evaluation",
        "sub_subject": "PT Penetrant Dwell Time",
        "difficulty": "easy",
        "topic": "Topic 11: PT & MT NDT"
    },
    {
        "type": "mcq",
        "question": "Per ASME Section V Article 7, what is the minimum lifting power required for an AC electromagnetic yoke used during MT inspection?",
        "options": [
            "4.5 kg or 10 lbs minimum lifting power",
            "18 kg or 40 lbs minimum lifting power",
            "2.2 kg or 5 lbs minimum lifting power",
            "9.0 kg or 20 lbs minimum lifting power"
        ],
        "correct": "4.5 kg or 10 lbs minimum lifting power",
        "rubric": "Verify MT yoke lifting power calibration per ASME V Article 7 T-762.",
        "subject": "NDT & Quality Evaluation",
        "sub_subject": "MT Yoke Lifting Power",
        "difficulty": "easy",
        "topic": "Topic 11: PT & MT NDT"
    },
    {
        "type": "mcq",
        "question": "During PT examination under ASME Section V, what is the maximum allowable surface temperature for standard penetrant materials?",
        "options": [
            "52 degrees Celsius maximum surface temp",
            "38 degrees Celsius maximum surface temp",
            "65 degrees Celsius maximum surface temp",
            "100 degrees Celsius maximum surface temp"
        ],
        "correct": "52 degrees Celsius maximum surface temp",
        "rubric": "Verify PT temperature range limits per ASME V Article 6 T-652.",
        "subject": "NDT & Quality Evaluation",
        "sub_subject": "PT Surface Temperature Limits",
        "difficulty": "moderate",
        "topic": "Topic 11: PT & MT NDT"
    },
    {
        "type": "essay",
        "question": "Detail the complete procedural steps for performing a solvent-removable visible Liquid Penetrant (PT) examination on a stainless steel attachment weld per ASME Section V Article 6. Include surface preparation, temperature verification, penetrant application/dwell time, excess penetrant removal, developer application, interpretation lighting, and final cleaning.",
        "options": "",
        "correct": "PT Procedure Steps: 1. Surface Prep & Pre-cleaning: Solvent clean weld area (25mm margin), dry thoroughly. 2. Surface Temp: Verify temp is 10-52°C. 3. Penetrant Application: Apply red dye penetrant, allow 10 min min dwell time. 4. Excess Removal: Wipe with clean dry cloth, then cloth dampened with solvent (do NOT spray solvent directly). 5. Developer Application: Spray thin uniform white developer coat, allow 10-30 min development time. 6. Interpretation: Inspect under white light (1000 lux min). 7. Final Cleaning: Remove developer residue.",
        "rubric": "1. Pre-cleaning & Temp Verification (2.5 pts): Specifies solvent cleaning and 10-52°C temp check.\n2. Dwell Time & Removal Technique (2.5 pts): Details 10 min dwell and correct solvent wipe procedure.\n3. Developing & Lighting Controls (2.5 pts): Explains thin developer coat and 1000 lux lighting rule.\n4. Indication Evaluation & Post-cleaning (2.5 pts): Distinguishes relevant/non-relevant indications and final cleaning.",
        "subject": "NDT & Quality Evaluation",
        "sub_subject": "PT Examination Workflow",
        "difficulty": "easy",
        "topic": "Topic 11: PT & MT NDT"
    },
    {
        "type": "oral_practical",
        "question": "Perform a physical Magnetic Particle (MT) examination on the provided welded carbon steel plate coupon using an AC yoke and black dry particles. Verify yoke lifting power with a 4.5kg weight, check light intensity, demonstrate continuous magnetization, interpret indications, and complete the MT inspection report.",
        "options": "",
        "correct": "Candidate performs 4.5kg weight lift test, verifies light level (>=1000 lux), applies AC yoke at 90-degree overlapping positions, applies dry powder gently while energizing yoke, identifies linear indications (cracks), and logs MT report.",
        "rubric": "1. Yoke Calibration Check (2.5 pts): Successfully performs 4.5kg (10 lb) weight lift test.\n2. MT Technique & Field Overlap (2.5 pts): Applies yoke in perpendicular directions with 100% coverage.\n3. Indication Interpretation (2.5 pts): Accurately identifies linear/rounded indications and flaws.\n4. Documentation & Post-demag (2.5 pts): Fills out formal MT report and explains demagnetization.",
        "subject": "NDT & Quality Evaluation",
        "sub_subject": "MT Practical Walkthrough",
        "difficulty": "easy",
        "topic": "Topic 11: PT & MT NDT"
    },

    # -------------------------------------------------------------------------
    # TOPIC 12: Structural Welding & AWS D1.1 Inspection Requirements
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Per AWS D1.1 Clause 6, what is the maximum allowable undercut depth for statically loaded structural members in carbon steel?",
        "options": [
            "1.0 mm or 1/32 inch maximum undercut depth",
            "1.5 mm or 1/16 inch maximum undercut depth",
            "0.5 mm or 1/64 inch maximum undercut depth",
            "2.0 mm or 5/64 inch maximum undercut depth"
        ],
        "correct": "1.0 mm or 1/32 inch maximum undercut depth",
        "rubric": "Verify AWS D1.1 Clause 6 visual acceptance criteria.",
        "subject": "Structural & Pipeline Standards",
        "sub_subject": "AWS D1.1 Undercut Criteria",
        "difficulty": "easy",
        "topic": "Topic 12: Structural Welding AWS D1.1"
    },
    {
        "type": "mcq",
        "question": "Per AWS D1.1, what is the prequalified minimum preheat temperature for welding ASTM A36 steel up to 19 mm thickness with low-hydrogen electrodes?",
        "options": [
            "10 degrees Celsius minimum preheat temp",
            "50 degrees Celsius minimum preheat temp",
            "65 degrees Celsius minimum preheat temp",
            "100 degrees Celsius minimum preheat temp"
        ],
        "correct": "10 degrees Celsius minimum preheat temp",
        "rubric": "Verify prequalified preheat requirements per AWS D1.1 Table 3.3.",
        "subject": "Structural & Pipeline Standards",
        "sub_subject": "AWS D1.1 Preheat Rules",
        "difficulty": "moderate",
        "topic": "Topic 12: Structural Welding AWS D1.1"
    },
    {
        "type": "mcq",
        "question": "Per AWS D1.1 Clause 6, how long must visual inspection be delayed after welding high-strength structural steel (yield > 460 MPa) before final sign-off?",
        "options": [
            "48 hours delay before final visual inspection",
            "24 hours delay before final visual inspection",
            "12 hours delay before final visual inspection",
            "72 hours delay before final visual inspection"
        ],
        "correct": "48 hours delay before final visual inspection",
        "rubric": "Verify delayed inspection requirements for high-strength steel per AWS D1.1 Table 6.1.",
        "subject": "Structural & Pipeline Standards",
        "sub_subject": "AWS D1.1 Delayed Inspection",
        "difficulty": "moderate",
        "topic": "Topic 12: Structural Welding AWS D1.1"
    },
    {
        "type": "essay",
        "question": "Explain the Quality Control requirements for structural steel fabrication and erection under AWS D1.1 and SAES-W-011. Detail prequalified WPS criteria, joint fit-up tolerances, tack welding rules, visual inspection delay for high-strength steel, and NDT sampling rates.",
        "options": "",
        "correct": "AWS D1.1 QC Requirements: 1. Prequalified WPS: Must comply with Clause 3 (approved base metals, filler metals, preheat, joint details). 2. Joint Fit-up: Root opening ±2mm without backing. 3. Tack Welds: Must be made by qualified welders, preheated same as main weld, cleaned and incorporated into final weld. 4. Inspection Delay: 48 hours post-completion VT/NDT delay for high strength steels (>460 MPa yield) to detect delayed hydrogen cracking. 5. NDT Sampling: 100% VT, minimum 10% UT/RT on CJP groove welds per SAES-W-011.",
        "rubric": "1. Prequalified WPS Criteria (2.5 pts): Explains AWS D1.1 Clause 3 prequalification rules.\n2. Fit-up & Tack Welding Rules (2.5 pts): Outlines root gap tolerances and tack welder qualification.\n3. Delayed Inspection Protocol (2.5 pts): Specifies 48-hr delay for high strength steel hydrogen cracking.\n4. NDT Sampling Rates (2.5 pts): Details SAES-W-011 structural NDT sampling requirements.",
        "subject": "Structural & Pipeline Standards",
        "sub_subject": "AWS D1.1 Structural QC",
        "difficulty": "easy",
        "topic": "Topic 12: Structural Welding AWS D1.1"
    },
    {
        "type": "oral_practical",
        "question": "Inspect the provided structural tubular/plate joint fit-up (AWS D1.1 joint detail C-UJ2a). Verify root opening, bevel angle, backing bar alignment, tack weld sound quality, and welder qualification badge. Log your fit-up inspection report.",
        "options": "",
        "correct": "Candidate checks joint detail dimensions (bevel 45 deg, root gap 6mm with backing), verifies backing bar steel grade, inspects tack welds for cracks/porosity, checks welder badge for AWS 3G/4G or 6GR qualification, logs pass/fail verdict.",
        "rubric": "1. Bevel & Root Gap Measurement (2.5 pts): Measures bevel angle and root opening accurately.\n2. Backing Bar Audit (2.5 pts): Verifies backing bar material, continuous length, and fit-up tightness.\n3. Tack Weld Quality Check (2.5 pts): Audits tack welds for sound quality and fusion.\n4. Qualification Sign-off (2.5 pts): Confirms welder performance card covers joint configuration.",
        "subject": "Structural & Pipeline Standards",
        "sub_subject": "AWS D1.1 Fit-Up Walkthrough",
        "difficulty": "moderate",
        "topic": "Topic 12: Structural Welding AWS D1.1"
    },

    # -------------------------------------------------------------------------
    # TOPIC 13: Cross-Country Pipeline Welding & API 1104 Inspection Standards
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Which standard governs welder qualification and field acceptance criteria for cross-country oil pipelines per SAES-W-012?",
        "options": [
            "API 1104 Standard for Welding Pipelines",
            "ASME B31.3 Process Piping Specification",
            "AWS D1.1 Structural Welding Standard Code",
            "ASME Section VIII Pressure Vessel Rules"
        ],
        "correct": "API 1104 Standard for Welding Pipelines",
        "rubric": "Verify cross-country pipeline standards per SAES-W-012 and API 1104.",
        "subject": "Structural & Pipeline Standards",
        "sub_subject": "API 1104 Pipeline Scope",
        "difficulty": "easy",
        "topic": "Topic 13: Pipeline Welding API 1104"
    },
    {
        "type": "mcq",
        "question": "Per API 1104 Section 9, what is the maximum allowable length of an individual crater crack in a pipeline weld?",
        "options": [
            "4.0 mm or 5/32 inch maximum crater crack",
            "6.0 mm or 1/4 inch maximum crater crack",
            "2.0 mm or 1/16 inch maximum crater crack",
            "Crater cracks are completely prohibited"
        ],
        "correct": "4.0 mm or 5/32 inch maximum crater crack",
        "rubric": "Verify API 1104 Section 9 defect acceptance limits.",
        "subject": "Structural & Pipeline Standards",
        "sub_subject": "API 1104 Crater Crack Limits",
        "difficulty": "moderate",
        "topic": "Topic 13: Pipeline Welding API 1104"
    },
    {
        "type": "mcq",
        "question": "Per SAES-W-012, what is the mandatory non-destructive testing (NDT) coverage required for production girth welds on cross-country pipelines?",
        "options": [
            "100 percent Radiographic or Automatic UT coverage",
            "10 percent spot Radiographic testing coverage",
            "50 percent Radiographic testing coverage total",
            "20 percent Ultrasonic testing coverage total"
        ],
        "correct": "100 percent Radiographic or Automatic UT coverage",
        "rubric": "Verify pipeline NDT coverage per SAES-W-012.",
        "subject": "Structural & Pipeline Standards",
        "sub_subject": "Pipeline NDT Sampling Rate",
        "difficulty": "difficult",
        "topic": "Topic 13: Pipeline Welding API 1104"
    },
    {
        "type": "essay",
        "question": "Compare API 1104 and ASME Section IX regarding Welder Performance Qualification essential variables and visual/NDT acceptance criteria. Detail the specific Saudi Aramco amendments imposed by SAES-W-012 on cross-country pipeline girth welding.",
        "options": "",
        "correct": "Comparison: API 1104 qualifies welders by process, pipe diameter group (<2.375\", 2.375\"-12.75\", >12.75\"), wall thickness group, and joint design. ASME IX uses specific P/F-Numbers, exact thickness QW-452 limits, and position groups. API 1104 allows small crater cracks (<=4mm) and minor IP under strict length limits; ASME B31.3/SAES prohibits cracks. SAES-W-012 amendments: Mandates 100% NDT (RT or AUT), zero crack policy, strict hardness limits for sour lines, and automatic welding qualification requirements.",
        "rubric": "1. Welder Qualification Variable Comparison (2.5 pts): Compares API 1104 vs ASME IX essential variables.\n2. Defect Acceptance Differences (2.5 pts): Highlights crater crack and IP acceptance limits in API 1104.\n3. SAES-W-012 Amendments (2.5 pts): Cites mandatory 100% RT/AUT and zero crack overrides.\n4. Pipeline Field Quality Controls (2.5 pts): Details internal clamp removal rules and preheat hold.",
        "subject": "Structural & Pipeline Standards",
        "sub_subject": "API 1104 vs ASME IX Pipeline Rules",
        "difficulty": "moderate",
        "topic": "Topic 13: Pipeline Welding API 1104"
    },
    {
        "type": "oral_practical",
        "question": "Inspect the provided pipeline weld root pass coupon (downhill celluloses E6010 / E8010). Check for burn-through, hollow bead, internal undercut, and incomplete penetration. Verbally evaluate indications against API 1104 Section 9 and SAES-W-012, and complete the pipeline inspection report.",
        "options": "",
        "correct": "Candidate inspects internal root pass with borescope/mirror, measures depth and length of indications (e.g. hollow bead <=12.5mm length), checks against API 1104 and SAES-W-012 zero crack rule, logs pass/fail verdict.",
        "rubric": "1. Internal Root Inspection Technique (2.5 pts): Uses borescope/flashlight properly to inspect root pass.\n2. Pipeline Defect Identification (2.5 pts): Identifies hollow bead, burn-through, or IP accurately.\n3. API 1104 & SAES-W-012 Evaluation (2.5 pts): Applies length limits and SAES overrides correctly.\n4. Documentation Sign-off (2.5 pts): Completes pipeline field inspection log.",
        "subject": "Structural & Pipeline Standards",
        "sub_subject": "Pipeline Practical Walkthrough",
        "difficulty": "easy",
        "topic": "Topic 13: Pipeline Welding API 1104"
    },

    # -------------------------------------------------------------------------
    # TOPIC 14: Dissimilar Metal Welding & Stainless Steel Cladding
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Which filler metal AWS classification is standard for welding carbon steel (P-No. 1) to 304L stainless steel (P-No. 8)?",
        "options": [
            "ER309L over-alloyed stainless steel wire",
            "ER308L matching stainless steel wire",
            "ER70S-6 carbon steel solid wire filler",
            "ER316L matching stainless steel wire"
        ],
        "correct": "ER309L over-alloyed stainless steel wire",
        "rubric": "Identify dissimilar filler metal selection per ASME IX / SAES-W-011.",
        "subject": "Metallurgy & Special Alloys",
        "sub_subject": "Dissimilar Filler Selection",
        "difficulty": "easy",
        "topic": "Topic 14: Dissimilar Metal Welding"
    },
    {
        "type": "mcq",
        "question": "What is the main risk when welding carbon steel to austenitic stainless steel using a matching ER308L filler metal?",
        "options": [
            "Hot cracking due to martensite formation",
            "Excessive carbon pickup causing porosity",
            "Extreme softening of carbon steel HAZ",
            "Hydrogen induced cracking in root pass"
        ],
        "correct": "Hot cracking due to martensite formation",
        "rubric": "Understand Schaeffler diagram and dilution effects in dissimilar welding.",
        "subject": "Metallurgy & Special Alloys",
        "sub_subject": "Dilution & Schaeffler Diagram",
        "difficulty": "moderate",
        "topic": "Topic 14: Dissimilar Metal Welding"
    },
    {
        "type": "mcq",
        "question": "Per SAES-W-011, what is the maximum preheat temperature allowed on carbon steel side when welding to austenitic stainless steel?",
        "options": [
            "Preheat limited to carbon steel WPS requirement",
            "Preheat increased to 300 degrees Celsius",
            "No preheat allowed under any condition",
            "Preheat governed by stainless steel side"
        ],
        "correct": "Preheat limited to carbon steel WPS requirement",
        "rubric": "Verify preheat rules for dissimilar joints per SAES-W-011.",
        "subject": "Metallurgy & Special Alloys",
        "sub_subject": "Dissimilar Joint Thermal Rules",
        "difficulty": "difficult",
        "topic": "Topic 14: Dissimilar Metal Welding"
    },
    {
        "type": "essay",
        "question": "Explain the metallurgical challenges associated with dissimilar metal welding (e.g. carbon steel P-No. 1 to 316L stainless steel P-No. 8). Discuss filler metal selection (ER309L vs Nickel-based ERNiCrMo-3), dilution control, Schaeffler diagram utilization, and PWHT restrictions per SAES-W-011.",
        "options": "",
        "correct": "Challenges: Base metal dilution, brittle martensite formation in transition zone, thermal expansion mismatch, carbon migration during high temp service. Filler Selection: ER309L (over-alloyed 23Cr-12Ni) or Nickel-base ERNiCrMo-3 (Inconel 82) for high temp/sour service to avoid carbon depletion. Schaeffler Diagram: Predicts ferrite content (3-10% ferrite desired to prevent hot cracking). PWHT Restrictions: Avoid PWHT on dissimilar joints if possible; if carbon steel side requires PWHT, butter carbon steel side first, PWHT carbon steel, then weld stainless joint without subsequent PWHT.",
        "rubric": "1. Metallurgical Challenges (2.5 pts): Details dilution, martensite risks, and thermal expansion mismatch.\n2. Filler Metal Selection & Schaeffler Diagram (2.5 pts): Explains 309L vs Nickel-base choice and ferrite control.\n3. Carbon Migration & High Temp Risks (2.5 pts): Discusses carbon depletion across interface.\n4. PWHT Buttering Strategy (2.5 pts): Details SAES-W-011 buttering and heat treatment sequence.",
        "subject": "Metallurgy & Special Alloys",
        "sub_subject": "Dissimilar Welding & Buttering",
        "difficulty": "moderate",
        "topic": "Topic 14: Dissimilar Metal Welding"
    },
    {
        "type": "oral_practical",
        "question": "Inspect the provided dissimilar metal weld joint coupon (P-No. 1 carbon steel to P-No. 8 316L stainless steel). Verify WPS filler metal (ER309L), check PMI test report (Positive Material Identification), inspect root pass for oxidation/purging quality, and log your inspection findings.",
        "options": "",
        "correct": "Candidate checks WPS for ER309L/ERNiCrMo-3 filler, reviews XRF/PMI analyzer report confirming Cr/Ni/Mo content, inspects internal root for sugaring/oxidation (verifies argon purge), logs pass/fail report.",
        "rubric": "1. WPS & Consumable Verification (2.5 pts): Confirms over-alloyed filler metal choice on WPS.\n2. PMI Test Report Review (2.5 pts): Audits XRF elemental analysis against AWS specs.\n3. Purge Quality & Root Inspection (2.5 pts): Evaluates root pass for sugaring/oxidation.\n4. Documentation Sign-off (2.5 pts): Fills out receiving/weld inspection report accurately.",
        "subject": "Metallurgy & Special Alloys",
        "sub_subject": "Dissimilar Joint Inspection Walkthrough",
        "difficulty": "easy",
        "topic": "Topic 14: Dissimilar Metal Welding"
    },

    # -------------------------------------------------------------------------
    # TOPIC 15: Duplex Stainless Steel & Alloy Welding Quality Control
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Per SAES-W-011, what is the required phase balance (ferrite percentage) range for welded 2205 Duplex Stainless Steel (P-No. 10H)?",
        "options": [
            "35 to 65 percent ferrite phase range",
            "10 to 25 percent ferrite phase range",
            "70 to 90 percent ferrite phase range",
            "0 to 10 percent ferrite phase range"
        ],
        "correct": "35 to 65 percent ferrite phase range",
        "rubric": "Verify ferrite limits for Duplex SS per SAES-W-011 and API 938-C.",
        "subject": "Metallurgy & Special Alloys",
        "sub_subject": "Duplex Ferrite Limits",
        "difficulty": "easy",
        "topic": "Topic 15: Duplex & Alloy Welding"
    },
    {
        "type": "mcq",
        "question": "What is the primary risk when welding Duplex Stainless Steel with excessive arc heat input and high interpass temperature?",
        "options": [
            "Precipitation of brittle intermetallic sigma phase",
            "Hydrogen embrittlement in ferrite grains",
            "Excessive austenite formation causing softness",
            "Severe zinc contamination from wire"
        ],
        "correct": "Precipitation of brittle intermetallic sigma phase",
        "rubric": "Understand phase transformations and sigma phase risks in Duplex SS.",
        "subject": "Metallurgy & Special Alloys",
        "sub_subject": "Sigma Phase Risks",
        "difficulty": "moderate",
        "topic": "Topic 15: Duplex & Alloy Welding"
    },
    {
        "type": "mcq",
        "question": "Per SAES-W-011, what is the maximum interpass temperature permitted when welding 2205 Duplex Stainless Steel?",
        "options": [
            "150 degrees Celsius maximum interpass temp",
            "250 degrees Celsius maximum interpass temp",
            "200 degrees Celsius maximum interpass temp",
            "100 degrees Celsius maximum interpass temp"
        ],
        "correct": "150 degrees Celsius maximum interpass temp",
        "rubric": "Verify interpass temperature limits for Duplex SS per SAES-W-011.",
        "subject": "Metallurgy & Special Alloys",
        "sub_subject": "Duplex Interpass Limits",
        "difficulty": "difficult",
        "topic": "Topic 15: Duplex & Alloy Welding"
    },
    {
        "type": "essay",
        "question": "Detail the specialized Quality Control requirements for welding 2205 Duplex Stainless Steel (P-No. 10H) piping systems per SAES-W-011. Cover heat input control (min/max limits), interpass temperature limits, shielding/purging gas selection (Argon + N2 mixtures), ferrite testing methods (Fisher Feritscope vs point counting), and corrosion testing (ASTM G48).",
        "options": "",
        "correct": "Duplex QC Requirements: 1. Heat Input Control: Maintained strictly between 0.5 - 1.5 kJ/mm (too low = excessive ferrite; too high = sigma phase precipitation). 2. Interpass Temp: Max 150°C. 3. Shielding/Purging Gas: Pure Argon or Argon + 2% N2 (nitrogen additions prevent N2 loss and maintain austenite phase balance). Purge oxygen <50 ppm. 4. Ferrite Testing: Feritscope testing on weld metal and HAZ (target 35-65% ferrite). 5. ASTM G48 Ferric Chloride Pitting Test: Mandatory PQR test to verify pitting corrosion resistance.",
        "rubric": "1. Heat Input & Phase Balance Rationale (2.5 pts): Explains ferrite/austenite balance and heat input limits.\n2. Thermal & Interpass Limits (2.5 pts): Cites 150°C interpass cap and cooling rate controls.\n3. Purging Gas & Nitrogen Balance (2.5 pts): Details Ar+N2 gas mix and <50 ppm O2 purge limit.\n4. Ferrite & ASTM G48 Testing (2.5 pts): Explains Feritscope testing (35-65%) and pitting test rules.",
        "subject": "Metallurgy & Special Alloys",
        "sub_subject": "Duplex QC & Ferrite Testing",
        "difficulty": "difficult",
        "topic": "Topic 15: Duplex & Alloy Welding"
    },
    {
        "type": "oral_practical",
        "question": "Using a calibrated Feritscope, perform ferrite content measurements on a welded 2205 Duplex pipe coupon (weld cap, root, and HAZ). Evaluate readings against SAES-W-011 ferrite limits (35-65%), check oxygen purge meter reading from the welding log, and issue your inspection report.",
        "options": "",
        "correct": "Candidate calibrates Feritscope on standard block, takes 5 readings on weld cap, 5 on HAZ, calculates average ferrite percentage (verifies within 35-65%), audits purge log for <50 ppm O2 level, signs off report.",
        "rubric": "1. Feritscope Calibration (2.5 pts): Calibrates instrument using standard reference block.\n2. Ferrite Measurement Technique (2.5 pts): Takes multiple readings across weld center, toe, and HAZ.\n3. Data Analysis & Criteria (2.5 pts): Calculates average and evaluates against 35-65% range.\n4. Log Audit & Final Sign-off (2.5 pts): Audits purge records and writes formal inspection report.",
        "subject": "Metallurgy & Special Alloys",
        "sub_subject": "Feritscope Practical Walkthrough",
        "difficulty": "moderate",
        "topic": "Topic 15: Duplex & Alloy Welding"
    },

    # -------------------------------------------------------------------------
    # TOPIC 16: Weld Joint Fit-Up, Bevel Prep & Alignment Tolerances
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Per SAES-W-011, what is the standard bevel angle requirement for manual butt welding of carbon steel pipe joints?",
        "options": [
            "37.5 degrees plus minus 2.5 degrees bevel angle",
            "45.0 degrees plus minus 5.0 degrees bevel angle",
            "30.0 degrees plus minus 1.0 degrees bevel angle",
            "25.0 degrees plus minus 2.0 degrees bevel angle"
        ],
        "correct": "37.5 degrees plus minus 2.5 degrees bevel angle",
        "rubric": "Verify standard bevel geometry per SAES-W-011 / ASME B16.25.",
        "subject": "Joint Geometry & Fit-Up",
        "sub_subject": "Standard Bevel Angle",
        "difficulty": "easy",
        "topic": "Topic 16: Bevel Prep & Fit-Up"
    },
    {
        "type": "mcq",
        "question": "Per SAES-W-011, what is the standard root gap range for manual GTAW root pass on carbon steel piping?",
        "options": [
            "2.0 mm to 3.2 mm root gap range",
            "4.0 mm to 6.0 mm root gap range",
            "0.5 mm to 1.0 mm root gap range",
            "5.0 mm to 7.0 mm root gap range"
        ],
        "correct": "2.0 mm to 3.2 mm root gap range",
        "rubric": "Verify GTAW root gap fit-up tolerances per SAES-W-011.",
        "subject": "Joint Geometry & Fit-Up",
        "sub_subject": "GTAW Root Gap Range",
        "difficulty": "easy",
        "topic": "Topic 16: Bevel Prep & Fit-Up"
    },
    {
        "type": "mcq",
        "question": "When internal misalignment (hi-lo) exceeds 1.5 mm on pipe butt joints, what corrective action is mandated by SAES-W-011?",
        "options": [
            "Taper machining or grinding at 1 to 4 slope ratio",
            "Force alignment using heavy hydraulic clamps",
            "Increase welding current to melt away high edge",
            "Fill misaligned gap with heavy E7018 weld deposit"
        ],
        "correct": "Taper machining or grinding at 1 to 4 slope ratio",
        "rubric": "Verify hi-lo correction methods per SAES-W-011 / ASME B31.3.",
        "subject": "Joint Geometry & Fit-Up",
        "sub_subject": "Hi-Lo Correction Slope",
        "difficulty": "moderate",
        "topic": "Topic 16: Bevel Prep & Fit-Up"
    },
    {
        "type": "essay",
        "question": "Describe the complete pre-weld inspection workflow for pipe joint fit-up on a carbon steel process line. Cover bevel angle inspection, root face (land) measurement, root gap check, internal misalignment (hi-lo) evaluation, surface cleanliness (grease/rust removal margin), and tack weld inspection per SAES-W-011.",
        "options": "",
        "correct": "Pre-weld Fit-up Workflow: 1. Bevel Prep: Inspect bevel angle (37.5° ± 2.5°), root land (1.6mm ± 0.8mm). 2. Cleanliness: Verify 25mm (1 in) cleaning margin inside/outside bevel (free of rust, oil, paint). 3. Fit-up Alignment: Measure root gap (2.0-3.2mm), internal hi-lo (max 1.5mm). If hi-lo > 1.5mm, apply 1:4 taper transition. 4. Tack Welds: Verify tacks made by qualified welders using WPS filler, examine for cracks/porosity, feather ends of tacks prior to root pass.",
        "rubric": "1. Bevel & Land Geometry (2.5 pts): Details bevel angle (37.5°) and root land tolerances.\n2. Cleaning Margin & Contamination (2.5 pts): Specifies 25mm cleaning area and rust/paint removal.\n3. Fit-up & Alignment Tolerances (2.5 pts): Cites 1.5mm hi-lo limit and 1:4 taper grinding rule.\n4. Tack Weld Inspection (2.5 pts): Details tack quality, feathering, and qualification checks.",
        "subject": "Joint Geometry & Fit-Up",
        "sub_subject": "Pre-Weld Fit-Up Inspection",
        "difficulty": "easy",
        "topic": "Topic 16: Bevel Prep & Fit-Up"
    },
    {
        "type": "oral_practical",
        "question": "Using bevel protractor, root gap gauge, and Hi-Lo gauge, inspect an assembled 8-inch pipe fit-up joint prior to root welding. Measure bevel angle, land thickness, root gap, and internal misalignment. Identify any non-conformance, recommend corrective action, and log your fit-up release sign-off.",
        "options": "",
        "correct": "Candidate measures bevel angle with protractor, checks root gap with wedge gauge, measures internal hi-lo with Hi-Lo gauge, detects any excessive gap or misalignment, recommends 1:4 taper grinding if needed, and signs fit-up release form.",
        "rubric": "1. Bevel Angle & Land Measurement (2.5 pts): Accurately reads bevel angle and land thickness.\n2. Root Gap & Alignment Audit (2.5 pts): Measures root gap and internal hi-lo precision.\n3. Non-conformance Resolution (2.5 pts): Correctly flags fit-up defects and specifies 1:4 taper.\n4. Fit-Up Release Sign-off (2.5 pts): Fills out official pre-weld inspection release form.",
        "subject": "Joint Geometry & Fit-Up",
        "sub_subject": "Fit-Up Practical Walkthrough",
        "difficulty": "easy",
        "topic": "Topic 16: Bevel Prep & Fit-Up"
    },

    # -------------------------------------------------------------------------
    # TOPIC 17: Shielding & Backing Gas Purging (GTAW / GMAW)
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Per SAES-W-011, what is the maximum allowable oxygen concentration inside the pipe purge dam before starting GTAW root welding on stainless steel?",
        "options": [
            "0.05 percent or 500 ppm maximum oxygen limit",
            "1.00 percent or 10000 ppm maximum oxygen limit",
            "0.50 percent or 5000 ppm maximum oxygen limit",
            "2.00 percent or 20000 ppm maximum oxygen limit"
        ],
        "correct": "0.05 percent or 500 ppm maximum oxygen limit",
        "rubric": "Verify purge oxygen limits per SAES-W-011.",
        "subject": "Gas Shielding & Purging",
        "sub_subject": "Purge Oxygen Level Limits",
        "difficulty": "easy",
        "topic": "Topic 17: Shielding & Purging"
    },
    {
        "type": "mcq",
        "question": "Which gas composition is mandatory for backing gas purging during GTAW root welding of nickel alloy and stainless steel per SAES-W-011?",
        "options": [
            "100 percent pure Argon gas backing purge",
            "100 percent pure Carbon Dioxide gas purge",
            "75 percent Argon plus 25 percent CO2 mix",
            "Compressed atmospheric shop air purge"
        ],
        "correct": "100 percent pure Argon gas backing purge",
        "rubric": "Verify backing gas purity requirements per SAES-W-011.",
        "subject": "Gas Shielding & Purging",
        "sub_subject": "Backing Gas Composition",
        "difficulty": "easy",
        "topic": "Topic 17: Shielding & Purging"
    },
    {
        "type": "mcq",
        "question": "How many weld passes must be completed under full backing purge before purging can be safely disconnected on stainless steel piping per SAES-W-011?",
        "options": [
            "Minimum two passes or 5 mm weld thickness",
            "Root pass only is sufficient for purge",
            "Minimum four passes or 10 mm thickness",
            "Purge must remain until weld is 100 percent finished"
        ],
        "correct": "Minimum two passes or 5 mm weld thickness",
        "rubric": "Verify purge retention rules per SAES-W-011.",
        "subject": "Gas Shielding & Purging",
        "sub_subject": "Purge Retention Passes",
        "difficulty": "moderate",
        "topic": "Topic 17: Shielding & Purging"
    },
    {
        "type": "essay",
        "question": "Explain the technical necessity of backing gas purging during GTAW welding of stainless steel and alloy piping. Describe purge dam setup, purge gas flow rate calculation, oxygen analyzer measurement protocol, maximum O2 limits per SAES-W-011, and the visual appearance/consequences of 'sugaring' (root oxidation).",
        "options": "",
        "correct": "Technical Necessity: Prevents root pass oxidation (sugaring), heavy chromium depletion, loss of corrosion resistance, and crusty root profiles. Setup & Protocol: Soluble dams or inflatable bladders placed ~150-300mm from joint. Pure Argon backing gas flushed through lower port, vented at upper port. Oxygen Analyzer: Measures O2 level in vent gas until < 0.05% (500 ppm) for SS or < 50 ppm for Duplex. Minimum 2 passes (or 5mm thickness) completed before removing purge. Sugaring: Heavy black oxidized root scale, automatic rejection under SAES-W-011.",
        "rubric": "1. Metallurgical Purge Rationale (2.5 pts): Details chromium oxidation and loss of corrosion resistance.\n2. Purge Dam Setup & Flow Protocol (2.5 pts): Outlines dam placement, venting, and flow controls.\n3. Oxygen Analyzer & SAES Limits (2.5 pts): Cites <500 ppm (SS) and <50 ppm (Duplex) O2 thresholds.\n4. Sugaring & Acceptance Criteria (2.5 pts): Defines sugaring root defect and zero tolerance rule.",
        "subject": "Gas Shielding & Purging",
        "sub_subject": "Purging Protocol & Sugaring",
        "difficulty": "moderate",
        "topic": "Topic 17: Shielding & Purging"
    },
    {
        "type": "oral_practical",
        "question": "Set up an internal purge monitoring system on a stainless steel pipe spool test rig. Connect the portable oxygen analyzer, flush backing gas, verify oxygen level drops below 500 ppm, record purged gas flow rate, inspect the root pass sample coupon for sugaring, and issue your inspection report.",
        "options": "",
        "correct": "Candidate installs purge dam, connects Argon hose and O2 analyzer, monitors digital O2 readout down to <500 ppm, sets flow meter (10-15 L/min flush, 3-5 L/min bleed), inspects root pass coupon for clean golden/silver root contour, logs pass sign-off.",
        "rubric": "1. Dam Setup & Hose Connection (2.5 pts): Correctly installs dam, vent line, and analyzer sensor.\n2. Analyzer Calibration & O2 Check (2.5 pts): Monitors O2 level reduction down to <500 ppm accurately.\n3. Flow Rate Adjustment (2.5 pts): Sets initial flush flow and reduced welding bleed flow correctly.\n4. Root Quality Verification (2.5 pts): Evaluates root coupon for sugaring and completes purge log.",
        "subject": "Gas Shielding & Purging",
        "sub_subject": "Purge Monitoring Walkthrough",
        "difficulty": "easy",
        "topic": "Topic 17: Shielding & Purging"
    },

    # -------------------------------------------------------------------------
    # TOPIC 18: Welding & NDT Equipment Calibration & Quality Audit Verification
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Per SAEP-381, what is the maximum calibration interval permitted for welding machine voltmeters and ammeters on jobsite?",
        "options": [
            "Six months maximum calibration interval",
            "Twelve months maximum calibration interval",
            "Three months maximum calibration interval",
            "One month maximum calibration interval"
        ],
        "correct": "Six months maximum calibration interval",
        "rubric": "Verify equipment calibration frequencies per SAEP-381 / SAES-W-011.",
        "subject": "Equipment Calibration & Audit",
        "sub_subject": "Machine Calibration Frequencies",
        "difficulty": "easy",
        "topic": "Topic 18: Equipment Calibration"
    },
    {
        "type": "mcq",
        "question": "Which instrument is used by a Welding Quality Inspector to verify the output accuracy of a welding machine ammeter on site?",
        "options": [
            "Calibrated digital clamp meter instrument",
            "Infrared thermal imaging camera gauge",
            "High voltage insulation megger tester",
            "Ultrasonic digital wall thickness gauge"
        ],
        "correct": "Calibrated digital clamp meter instrument",
        "rubric": "Identify field calibration tools for current verification.",
        "subject": "Equipment Calibration & Audit",
        "sub_subject": "Current Verification Tools",
        "difficulty": "easy",
        "topic": "Topic 18: Equipment Calibration"
    },
    {
        "type": "mcq",
        "question": "Per SAES-W-011, what is the maximum permitted deviation between machine panel meter reading and calibrated master meter?",
        "options": [
            "Plus minus 5 percent of full scale reading",
            "Plus minus 10 percent of full scale reading",
            "Plus minus 2 percent of full scale reading",
            "Plus minus 15 percent of full scale reading"
        ],
        "correct": "Plus minus 5 percent of full scale reading",
        "rubric": "Verify meter accuracy tolerance limits per SAES-W-011.",
        "subject": "Equipment Calibration & Audit",
        "sub_subject": "Meter Accuracy Tolerances",
        "difficulty": "moderate",
        "topic": "Topic 18: Equipment Calibration"
    },
    {
        "type": "essay",
        "question": "Outline the site Quality Audit procedure for welding and inspection equipment on a Saudi Aramco project per SAEP-381 and SAES-W-011. Cover calibration verification of welding power sources, baking ovens, temperature pyrometers, NDT equipment, calibration stickers, and non-conformance quarantine procedures.",
        "options": "",
        "correct": "Site Equipment Audit Procedure: 1. Welding Machines: Verify 6-month calibration sticker, audit voltage/amperage accuracy using calibrated clamp meter/voltmeter (tolerance ±5%). 2. Baking & Holding Ovens: Audit digital temperature controllers and chart recorders against calibrated master TC annually. 3. Thermometers/Pyrometers: Verify 6-month calibration sticker. 4. NDT Equipment: Verify densitometers, UT machines, PAUT encoders, MT yokes calibrated per code. 5. Non-conforming Equipment: Out-of-calibration or defective tools tagged with red 'REJECTED/OUT OF SERVICE' sticker, quarantined immediately.",
        "rubric": "1. Calibration Intervals & Sticker Verification (2.5 pts): Outlines 6-month and 12-month calibration cycles.\n2. Machine Meter Accuracy Audit (2.5 pts): Details clamp-meter check and ±5% tolerance rule.\n3. Oven & NDT Calibration Audit (2.5 pts): Audits oven controllers, pyrometers, and NDT equipment.\n4. Quarantine Protocol for Defective Tools (2.5 pts): Explains red-tagging and quarantine procedures.",
        "subject": "Equipment Calibration & Audit",
        "sub_subject": "Site Equipment Quality Audit",
        "difficulty": "easy",
        "topic": "Topic 18: Equipment Calibration"
    },
    {
        "type": "oral_practical",
        "question": "Perform a physical calibration audit on a jobsite SMAW/GTAW welding machine and portable pyrometer. Check calibration sticker validity, take live voltage and amperage readings using a calibrated clamp meter during welding, evaluate accuracy within ±5%, and complete the equipment audit report.",
        "options": "",
        "correct": "Candidate checks calibration tag date on welding machine, applies clamp meter to lead cable during active welding pass, compares clamp meter A/V readings against machine panel, verifies deviation <=5%, audits pyrometer tag, signs audit log.",
        "rubric": "1. Sticker & Tag Audit (2.5 pts): Audits calibration certificates and validity expiration dates.\n2. Live Measurement Setup (2.5 pts): Safely positions clamp meter and voltmeter leads during live welding.\n3. Deviation Calculation (2.5 pts): Calculates percentage difference between machine and master meter.\n4. Audit Report Sign-off (2.5 pts): Issues pass/fail report and documents equipment status.",
        "subject": "Equipment Calibration & Audit",
        "sub_subject": "Machine Calibration Walkthrough",
        "difficulty": "easy",
        "topic": "Topic 18: Equipment Calibration"
    },

    # -------------------------------------------------------------------------
    # TOPIC 19: Non-Conformance Reports (NCR) & Root Cause Defect Repair
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Per SAEP-381, what quality document must be issued when a systemic welding defect or unauthorized code violation is detected on site?",
        "options": [
            "Non-Conformance Report formally issued by QC",
            "Site Observation Note informal verbal warning",
            "Routine Field Weld Inspection Request Sheet",
            "Monthly Quality Performance Trend Diagram"
        ],
        "correct": "Non-Conformance Report formally issued by QC",
        "rubric": "Verify quality non-conformance documentation per SAEP-381.",
        "subject": "Quality Assurance & NCR",
        "sub_subject": "NCR Issuance Criteria",
        "difficulty": "moderate",
        "topic": "Topic 19: Non-Conformance & Repairs"
    },
    {
        "type": "mcq",
        "question": "Per SAES-W-011, what is the maximum number of repair attempts permitted on a single carbon steel production weld joint before replacement?",
        "options": [
            "Maximum two repair attempts permitted on joint",
            "Maximum three repair attempts permitted on joint",
            "Maximum one repair attempt permitted on joint",
            "Unlimited repair attempts allowed if tested"
        ],
        "correct": "Maximum two repair attempts permitted on joint",
        "rubric": "Verify weld repair attempt limits per SAES-W-011.",
        "subject": "Quality Assurance & NCR",
        "sub_subject": "Weld Repair Attempt Limits",
        "difficulty": "moderate",
        "topic": "Topic 19: Non-Conformance & Repairs"
    },
    {
        "type": "mcq",
        "question": "Which corrective action is mandatory when a welder experiences an excessive weld defect reject rate exceeding 5% on Aramco jobs?",
        "options": [
            "Revocation of welder qualification and retraining",
            "Reduction of welder hourly pay rate by ten percent",
            "Transfer of welder to structural tacking duty only",
            "Issuance of verbal warning without re-testing"
        ],
        "correct": "Revocation of welder qualification and retraining",
        "rubric": "Verify welder performance failure actions per SAES-W-011 / SAEP-381.",
        "subject": "Quality Assurance & NCR",
        "sub_subject": "Welder Reject Rate Escalation",
        "difficulty": "difficult",
        "topic": "Topic 19: Non-Conformance & Repairs"
    },
    {
        "type": "essay",
        "question": "Describe the complete lifecycle of a Non-Conformance Report (NCR) issued for recurring root lack of fusion defects in pipe welds on a Saudi Aramco project. Cover initial discovery, NCR drafting, root cause analysis (RCA), corrective/preventive action disposition (CAPA), repair procedure execution, re-inspection, and final closure sign-off per SAEP-381.",
        "options": "",
        "correct": "NCR Lifecycle: 1. Identification & Hold: QC Inspector discovers recurring LOF defects on RT/UT logs, places Hold on joint group. 2. Drafting & Issue: Formal NCR drafted detailing specific code violation (SAES-W-011 / ASME B31.3), issued to Contractor Quality Manager. 3. Root Cause Analysis (RCA): Contractor investigates root cause (e.g., tight root gap, low GTAW current, improper bevel angle). 4. CAPA & Disposition: Contractor submits repair WPS, retraining plan, and fit-up gap correction. CSD/Company QC approves disposition. 5. Repair Execution & Re-inspection: Defect excavated via grinding, PT verified, re-welded, 100% re-inspected by RT/UT. 6. Closure: QC verifies effective corrective action, signs NCR closure.",
        "rubric": "1. Discovery & NCR Framing (2.5 pts): Details initial defect discovery, hold placement, and formal framing.\n2. Root Cause Investigation (2.5 pts): Conducts thorough RCA analyzing human, material, and process factors.\n3. CAPA & Disposition Review (2.5 pts): Evaluates repair WPS, retraining, and engineering approval.\n4. Re-testing & Closure Protocol (2.5 pts): Details excavation PT, re-welding, NDT re-inspection, and sign-off.",
        "subject": "Quality Assurance & NCR",
        "sub_subject": "NCR Lifecycle & Root Cause Analysis",
        "difficulty": "moderate",
        "topic": "Topic 19: Non-Conformance & Repairs"
    },
    {
        "type": "oral_practical",
        "question": "Review the provided RT defect report showing a 50mm slag inclusion in a 16-inch pipe weld. Draft a formal repair procedure request, specify excavation boundaries (25mm beyond defect ends), inspect the excavated cavity with PT, witness the re-weld inspection, and complete the NCR disposition form.",
        "options": "",
        "correct": "Candidate reviews RT film location, marks excavation zone (defect length + 25mm each end), inspects ground cavity visually and with PT to confirm total defect removal, approves re-welding using qualified repair WPS, verifies post-repair RT film, signs NCR closure.",
        "rubric": "1. Defect Location & Marking (2.5 pts): Accurately transfers RT defect position to physical pipe joint.\n2. Excavation & PT Cavity Check (2.5 pts): Verifies 25mm margin and performs PT on ground groove.\n3. Repair WPS Witnessing (2.5 pts): Audits preheat and re-welding parameters against approved repair WPS.\n4. NDT Re-inspection & Closure (2.5 pts): Evaluates final RT film and completes NCR sign-off.",
        "subject": "Quality Assurance & NCR",
        "sub_subject": "Defect Repair Practical Walkthrough",
        "difficulty": "moderate",
        "topic": "Topic 19: Non-Conformance & Repairs"
    },

    # -------------------------------------------------------------------------
    # TOPIC 20: Project Quality Plan (SAEP-381) & Weld Traceability Log (ITP)
    # -------------------------------------------------------------------------
    {
        "type": "mcq",
        "question": "Per SAEP-381, which document details all mandatory inspection hold, witness, and review points throughout fabrication?",
        "options": [
            "Inspection and Test Plan or ITP document",
            "Monthly Quality Management Executive Summary",
            "Subcontractor Material Purchase Requisition",
            "Project Environmental Health Safety Charter"
        ],
        "correct": "Inspection and Test Plan or ITP document",
        "rubric": "Identify core quality control execution document per SAEP-381.",
        "subject": "Quality Assurance & NCR",
        "sub_subject": "ITP Document Scope",
        "difficulty": "easy",
        "topic": "Topic 20: Quality Plan & Traceability"
    },
    {
        "type": "mcq",
        "question": "What is the key difference between a 'Hold Point' and a 'Witness Point' in a Saudi Aramco Inspection and Test Plan (ITP)?",
        "options": [
            "Hold Point requires signed release before proceeding",
            "Witness Point requires work stoppage until approved",
            "Hold Point is optional based on inspector schedule",
            "Witness Point requires third party lab presence"
        ],
        "correct": "Hold Point requires signed release before proceeding",
        "rubric": "Differentiate Hold vs Witness inspection points per SAEP-381.",
        "subject": "Quality Assurance & NCR",
        "sub_subject": "Hold vs Witness Points",
        "difficulty": "easy",
        "topic": "Topic 20: Quality Plan & Traceability"
    },
    {
        "type": "mcq",
        "question": "Which quality log tracks joint number, welder ID, WPS used, fit-up date, visual check, and NDT report number per SAEP-1150?",
        "options": [
            "Daily Field Weld Traceability Summary Log",
            "Site Equipment Receiving Calibration Sheet",
            "Project Safety Incident Frequency Register",
            "Subcontractor Manpower Attendance Roster"
        ],
        "correct": "Daily Field Weld Traceability Summary Log",
        "rubric": "Identify field weld tracking log requirements per SAEP-1150 / SAEP-381.",
        "subject": "Quality Assurance & NCR",
        "sub_subject": "Weld Traceability Log",
        "difficulty": "moderate",
        "topic": "Topic 20: Quality Plan & Traceability"
    },
    {
        "type": "essay",
        "question": "Explain the structure and execution of an Inspection and Test Plan (ITP) for field piping and welding quality control under SAEP-381. Define Hold Points, Witness Points, and Review Points. Describe how weld traceability is maintained from material receiving through final test package sign-off.",
        "options": "",
        "correct": "ITP Structure & Execution: 1. ITP Elements: Lists activity sequence, controlling specification (SAES/ASME), acceptance criteria, responsible party, quality records, and inspection level (Hold, Witness, Review). 2. Definitions: Hold Point (H) - Work CANNOT proceed beyond this point without written sign-off by Company Inspector. Witness Point (W) - Inspector notified in advance; work may proceed if inspector fails to attend. Review Point (R) - Review of quality documents/records. 3. Weld Traceability: Maintained via Weld Log (SAEP-1150) tracking drawing no, joint no, pipe heat no, WPS, welder ID, fit-up release date, VT date, NDT report no, PWHT report no, and hydrotest package sign-off.",
        "rubric": "1. ITP Components & Governance (2.5 pts): Details activity sequence, controlling standards, and quality records.\n2. Inspection Levels Definition (2.5 pts): Accurately defines Hold (H), Witness (W), and Review (R) points.\n3. Weld Traceability Architecture (2.5 pts): Explains joint numbering, heat no tracking, and weld log fields.\n4. Test Package Sign-off (2.5 pts): Details integration into final hydrotest and turnover dossier.",
        "subject": "Quality Assurance & NCR",
        "sub_subject": "ITP Architecture & Traceability",
        "difficulty": "moderate",
        "topic": "Topic 20: Quality Plan & Traceability"
    },
    {
        "type": "oral_practical",
        "question": "Audit a completed piping isometric test package folder containing the Weld Summary Log, NDT reports (RT/UT/PT), MTCs, and ITP sign-off sheet. Verify 100% joint traceability, confirm all Hold points are signed by authorized Aramco QC, flag any missing NDT report, and sign off the quality dossier.",
        "options": "",
        "correct": "Candidate cross-checks isometric drawing against Weld Log, verifies every joint has matching WPS, welder ID, VT sign-off, NDT report number, checks MTC heat numbers, verifies Aramco QC signatures on all Hold points, identifies any un-cleared joint, logs audit result.",
        "rubric": "1. Isometric & Weld Log Reconciliation (2.5 pts): Cross-references joint numbers and drawing revisions.\n2. NDT & MTC Traceability Audit (2.5 pts): Audits RT/UT/PT report numbers and material heat numbers.\n3. ITP Hold Point Signature Verification (2.5 pts): Confirms all mandatory Aramco QC Hold points are signed.\n4. Test Package Certification (2.5 pts): Fills out formal turnover audit sheet and signs release.",
        "subject": "Quality Assurance & NCR",
        "sub_subject": "ITP Audit Practical Walkthrough",
        "difficulty": "easy",
        "topic": "Topic 20: Quality Plan & Traceability"
    }
]

def main():
    print(f"Total questions loaded: {len(QUESTIONS_DATA)}")
    
    # Validate count and difficulty distribution
    counts = {"mcq": 0, "essay": 0, "oral_practical": 0}
    diff_counts = {"easy": 0, "moderate": 0, "difficult": 0}
    
    for q in QUESTIONS_DATA:
        q_type = q["type"]
        if q_type in counts:
            counts[q_type] += 1
        diff = q["difficulty"]
        if diff in diff_counts:
            diff_counts[diff] += 1
            
    print(f"Type breakdown: {counts}")
    print(f"Difficulty breakdown: {diff_counts}")
    
    # Check 50% easy rule
    total_q = len(QUESTIONS_DATA)
    easy_q = diff_counts["easy"]
    print(f"Easy percentage: {(easy_q / total_q) * 100:.1f}%")
    
    # Validate MCQ option lengths
    print("\n--- Validating MCQ Option Lengths ---")
    mcq_count = 0
    for idx, q in enumerate(QUESTIONS_DATA, 1):
        if q["type"] == "mcq":
            mcq_count += 1
            opts = q["options"]
            lens = [len(o) for o in opts]
            min_l, max_l = min(lens), max(lens)
            diff_l = max_l - min_l
            if diff_l > 15:
                print(f"Warning MCQ #{mcq_count} (Topic: {q['topic']}): Length diff {diff_l} (min {min_l}, max {max_l})")
                for o in opts:
                    print(f"  [{len(o)}] {o}")

    # Build Excel Workbook matching HEADERS in question_import.py
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Questions"
    
    # Append Header
    sheet.append(HEADERS)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:L{len(QUESTIONS_DATA) + 1}"
    
    # Styles
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Calibri", size=10)
    align_center = Alignment(horizontal="center", vertical="top", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="top", wrap_text=True)
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )
    
    # Format Header Row
    for col_idx, cell in enumerate(sheet[1], 1):
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center
        cell.border = thin_border

    # Append Data Rows
    for q in QUESTIONS_DATA:
        q_type = q["type"]
        options_str = "\n".join(q["options"]) if q_type == "mcq" else ""
        row = [
            "Welding QC",                       # Discipline
            q_type,                             # Question type
            q["question"],                      # Question
            options_str,                        # Multiple Choice options
            q["correct"],                       # Correct answer
            q["rubric"],                        # Scoring rubric
            q["subject"],                       # Subject
            q["sub_subject"],                   # Sub-subject
            "yes",                              # Scored question
            q["difficulty"],                    # Difficulty
            q["topic"],                         # Topic group
            "standard"                          # Delivery stage
        ]
        sheet.append(row)
        
    # Format Data Cells
    for row_idx in range(2, len(QUESTIONS_DATA) + 2):
        sheet.row_dimensions[row_idx].height = None  # Auto height
        for col_idx in range(1, len(HEADERS) + 1):
            cell = sheet.cell(row=row_idx, column=col_idx)
            cell.font = data_font
            cell.border = thin_border
            if col_idx in (1, 2, 9, 10, 12):
                cell.alignment = align_center
            else:
                cell.alignment = align_left
                
    # Column Widths
    widths = {
        'A': 16, # Discipline
        'B': 16, # Question type
        'C': 65, # Question
        'D': 55, # Multiple Choice options
        'E': 45, # Correct answer
        'F': 65, # Scoring rubric
        'G': 28, # Subject
        'H': 28, # Sub-subject
        'I': 16, # Scored question
        'J': 14, # Difficulty
        'K': 32, # Topic group
        'L': 16  # Delivery stage
    }
    for col_letter, width in widths.items():
        sheet.column_dimensions[col_letter].width = width

    # Add Instructions sheet
    instructions = wb.create_sheet(title="Instructions")
    instructions.append(["Question bank import instructions"])
    instructions.append(["Fill the Questions sheet and leave no completely blank rows between questions."])
    instructions.append(["Question type must be mcq, essay, or oral_practical. For Multiple Choice questions, put one option per line in Multiple Choice options."])
    instructions.append(["Assessment Settings determines the maximum points for each question type. Keep the headers unchanged."])
    instructions.column_dimensions['A'].width = 110

    target_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "qc-question-template-Welding.xlsx")
    wb.save(target_file)
    print(f"\nSuccessfully generated {target_file}")
    
    # Validate with question_import.py
    print("\n--- Validating Excel File with question_import.py ---")
    with open(target_file, "rb") as f:
        file_bytes = f.read()
    parsed = question_import.parse_questions(file_bytes)
    print(f"Successfully parsed {len(parsed)} questions with zero errors!")
    
    # Check parsed results summary
    parsed_types = {}
    parsed_diffs = {}
    for p in parsed:
        if not p["success"]:
            print(f"ERROR on row {p['row_number']}: {p['error']}")
        q = p["question"]
        k = q["kind"]
        parsed_types[k] = parsed_types.get(k, 0) + 1
        d = q["difficulty"]
        parsed_diffs[d] = parsed_diffs.get(d, 0) + 1
        
    print(f"Parsed Types: {parsed_types}")
    print(f"Parsed Difficulties: {parsed_diffs}")
    easy_percent = (parsed_diffs.get('easy', 0) / len(parsed)) * 100
    print(f"Final Verified Easy Percentage: {easy_percent:.1f}%")

if __name__ == "__main__":
    main()
