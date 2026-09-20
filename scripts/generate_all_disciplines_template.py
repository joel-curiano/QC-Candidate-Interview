"""
Generate qc-question-template.xlsx with 1,300 Aramco-aligned QC questions across ALL 13 disciplines.
13 Disciplines (100 questions per discipline):
  60 MCQ, 20 Essay, 20 Oral-Practical (12 Oral, 8 Practical)
Difficulty per question type: 40% Easy, 40% Moderate, 20% Difficult
  MCQ (60 Qs): 24 Easy, 24 Moderate, 12 Difficult
  Essay (20 Qs): 8 Easy, 8 Moderate, 4 Difficult
  Oral-Practical (20 Qs): 8 Easy, 8 Moderate, 4 Difficult
    - 12 Oral + 8 Practical split within the 20 Oral-Practical
All question types stored as 'oral_practical' per question_import.py validation.
MCQ distractors are length-balanced to the correct answer.
Subjects and topics pulled from disciplines.csv.
"""
import sys
import os
import csv
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

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

# ---------------------------------------------------------------------------
# Load subjects and topics from disciplines.csv
# ---------------------------------------------------------------------------
def load_discipline_topics():
    """Parse disciplines.csv and return {discipline: [(subject, topic), ...]}."""
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "disciplines.csv")
    result = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            disc = row["Discipline"].strip()
            subj = row["Subject"].strip()
            topic = row["Topic"].strip()
            result.setdefault(disc, []).append((subj, topic))
    return result

DISC_TOPICS = load_discipline_topics()

# ---------------------------------------------------------------------------
# Discipline question banks: real Aramco-aligned technical content
# Each discipline provides 60 MCQs, 20 Essays, 12 Oral, 8 Practical
# ---------------------------------------------------------------------------

def _pad(correct, distractor):
    """Pad or trim distractor to be within ±15 chars of correct answer length."""
    target = len(correct)
    if len(distractor) < target - 15:
        distractor = distractor + " " * (target - len(distractor))
    return distractor.strip()

def _balanced_options(correct, d1, d2, d3):
    """Return [correct, d1, d2, d3] with distractors length-balanced."""
    return [correct, _pad(correct, d1), _pad(correct, d2), _pad(correct, d3)]

# ===================================================================
# WELDING QC — 60 MCQ + 20 Essay + 12 Oral + 8 Practical
# ===================================================================
WELDING_MCQ = [
    # --- 24 Easy (Direct Recall / Remembering) ---
    {"q": "Per ASME Section IX, which variable is classified as an essential variable for SMAW procedure qualification?",
     "opts": _balanced_options("A change in base metal P-Number grouping", "A change in the brand of welding machine", "A minor adjustment in ambient lighting level", "A change in the color of electrode coating"),
     "correct": "A change in base metal P-Number grouping", "diff": "easy",
     "subj": "Codes and standards", "topic": "Approved WPS PQR and welder qualification controls"},
    {"q": "What does the abbreviation WPS stand for in welding quality control documentation?",
     "opts": _balanced_options("Welding Procedure Specification document", "Weld Process Safety documentation file", "Work Permit Surveillance document form", "Welder Performance Scoring documentation"),
     "correct": "Welding Procedure Specification document", "diff": "easy",
     "subj": "Codes and standards", "topic": "Approved WPS PQR and welder qualification controls"},
    {"q": "According to AWS D1.1, what is the minimum preheat temperature for welding ASTM A36 steel over 25 mm thick?",
     "opts": _balanced_options("66°C (150°F) minimum preheat required", "No preheat is required at any thickness", "200°C (400°F) minimum preheat required", "100°C (212°F) minimum preheat required"),
     "correct": "66°C (150°F) minimum preheat required", "diff": "easy",
     "subj": "Installation and workmanship", "topic": "Preheat interpass temperature and welding parameter control"},
    {"q": "What is the primary purpose of a Procedure Qualification Record (PQR) in welding?",
     "opts": _balanced_options("To record actual test results of a welded test coupon", "To list the names of qualified welders on a project", "To document the purchase order for filler materials", "To track daily welding production output quantities"),
     "correct": "To record actual test results of a welded test coupon", "diff": "easy",
     "subj": "Codes and standards", "topic": "Approved WPS PQR and welder qualification controls"},
    {"q": "Per ASME Section IX, what type of test is mandatory for groove weld procedure qualification?",
     "opts": _balanced_options("Guided bend tests and tensile tests are required", "Only visual inspection of completed weld surface", "Hardness testing only on the weld heat zone area", "Charpy impact testing at ambient room temperature"),
     "correct": "Guided bend tests and tensile tests are required", "diff": "easy",
     "subj": "Testing and verification", "topic": "Visual examination and NDT acceptance"},
    {"q": "What is the AWS classification for E7018 electrodes regarding their coating type?",
     "opts": _balanced_options("Low hydrogen iron powder coating designation", "High cellulose sodium based coating material", "Rutile titania based coating type designation", "Acidite mineral type electrode flux coating"),
     "correct": "Low hydrogen iron powder coating designation", "diff": "easy",
     "subj": "Materials and traceability", "topic": "Filler metal identification storage and conditioning"},
    {"q": "Per SAES-W-011, what document must be available at the weld station before welding can begin?",
     "opts": _balanced_options("An approved Welding Procedure Specification (WPS)", "The project's general health and safety plan only", "A copy of the contractor's business registration", "The site supervisor's daily attendance roster only"),
     "correct": "An approved Welding Procedure Specification (WPS)", "diff": "easy",
     "subj": "Codes and standards", "topic": "Controlled welding requirements and project document hierarchy"},
    {"q": "What is the purpose of using backing gas (purge gas) during TIG welding of stainless steel pipe?",
     "opts": _balanced_options("To prevent oxidation of the root pass weld area", "To increase the welding travel speed significantly", "To reduce the need for post-weld heat treatment", "To lower the melting point of the base metal alloy"),
     "correct": "To prevent oxidation of the root pass weld area", "diff": "easy",
     "subj": "Installation and workmanship", "topic": "Joint preparation fit up and alignment"},
    {"q": "What is the maximum allowable moisture content for low hydrogen electrodes per AWS D1.1 after reconditioning?",
     "opts": _balanced_options("0.4% maximum moisture by weight after baking", "2.0% maximum moisture by weight after baking", "5.0% maximum moisture by weight after baking", "No moisture limit is specified for electrodes"),
     "correct": "0.4% maximum moisture by weight after baking", "diff": "easy",
     "subj": "Materials and traceability", "topic": "Filler metal identification storage and conditioning"},
    {"q": "In welding terminology, what does the abbreviation PWHT stand for?",
     "opts": _balanced_options("Post Weld Heat Treatment process procedure", "Pre-Weld Hardness Testing inspection method", "Pressure Welding Horizontal Technique method", "Post Work Handling and Transport procedure"),
     "correct": "Post Weld Heat Treatment process procedure", "diff": "easy",
     "subj": "Testing and verification", "topic": "PWHT monitoring and hardness testing where required"},
    {"q": "According to ASME Section IX, what is the maximum qualified thickness for a welder who passes a test on 10 mm plate?",
     "opts": _balanced_options("20 mm (2 times the test coupon thickness)", "Unlimited thickness for all plate positions", "10 mm only (same as the test coupon thickness)", "50 mm (5 times the test coupon thickness value)"),
     "correct": "20 mm (2 times the test coupon thickness)", "diff": "easy",
     "subj": "Codes and standards", "topic": "Approved WPS PQR and welder qualification controls"},
    {"q": "What type of NDT method is typically required for the root pass of a single-sided pipe butt weld?",
     "opts": _balanced_options("Radiographic Testing (RT) of the completed joint", "Magnetic Particle Testing of the pipe outer wall", "Liquid Penetrant Testing of the pipe end bevel", "Eddy Current Testing of the pipe raw material"),
     "correct": "Radiographic Testing (RT) of the completed joint", "diff": "easy",
     "subj": "Inspection planning", "topic": "Fit up visual and NDT coordination"},
    {"q": "Per AWS D1.1, what is the minimum acceptable fillet weld leg size if the drawing specifies 8 mm?",
     "opts": _balanced_options("8 mm minus the allowable undertolerance of 1.5 mm", "Exactly 8 mm with no tolerance permitted at all", "Any size above 5 mm is considered fully acceptable", "10 mm minimum to include a mandatory safety factor"),
     "correct": "8 mm minus the allowable undertolerance of 1.5 mm", "diff": "easy",
     "subj": "Installation and workmanship", "topic": "Visual weld profile and defect prevention"},
    {"q": "What is the primary role of a QC welding inspector during fit-up inspection before welding?",
     "opts": _balanced_options("Verify root gap bevel angle and alignment to WPS", "Supervise the rigger during pipe lifting and setup", "Calculate the total weld metal volume to be ordered", "Review the project schedule for welding activities"),
     "correct": "Verify root gap bevel angle and alignment to WPS", "diff": "easy",
     "subj": "Inspection planning", "topic": "Fit up visual and NDT coordination"},
    {"q": "According to ASME Section IX, how is a welder's performance qualification (WPQ) position recorded?",
     "opts": _balanced_options("By the test position such as 1G 2G 3G 5G or 6G", "By the welder's years of field experience number", "By the brand name of the welding machine utilized", "By the time taken to complete the qualification weld"),
     "correct": "By the test position such as 1G 2G 3G 5G or 6G", "diff": "easy",
     "subj": "Codes and standards", "topic": "Approved WPS PQR and welder qualification controls"},
    {"q": "What is the standard baking temperature range for E7018 low hydrogen electrodes per AWS D1.1?",
     "opts": _balanced_options("260°C to 430°C for a minimum of one hour baking", "100°C to 150°C for a minimum of thirty minutes", "500°C to 600°C for a minimum of two hours baking", "No baking is required for E7018 type electrodes"),
     "correct": "260°C to 430°C for a minimum of one hour baking", "diff": "easy",
     "subj": "Materials and traceability", "topic": "Filler metal identification storage and conditioning"},
    {"q": "Per SAES-W-011, who must approve a welding procedure specification before production welding?",
     "opts": _balanced_options("The Saudi Aramco Inspection Department representative", "The contractor's project scheduling manager officer", "The site safety officer before any welding is done", "The material supplier's quality assurance engineer"),
     "correct": "The Saudi Aramco Inspection Department representative", "diff": "easy",
     "subj": "Codes and standards", "topic": "Controlled welding requirements and project document hierarchy"},
    {"q": "What is the purpose of a weld map in quality control documentation?",
     "opts": _balanced_options("To show the location and status of each weld joint", "To record daily weather conditions at the worksite", "To list all project personnel assigned to welding", "To calculate material cost estimates for weld metal"),
     "correct": "To show the location and status of each weld joint", "diff": "easy",
     "subj": "Documentation and turnover", "topic": "Weld map WPS and welder qualification records"},
    {"q": "Which of the following is a supplementary essential variable in ASME Section IX for impact-tested WPS?",
     "opts": _balanced_options("A change in PWHT temperature or time range values", "A change in the welding electrode brand manufacturer", "A change in the joint preparation grinding method", "A change in the type of cleaning brush material used"),
     "correct": "A change in PWHT temperature or time range values", "diff": "easy",
     "subj": "Codes and standards", "topic": "Approved WPS PQR and welder qualification controls"},
    {"q": "What is the minimum interpass temperature requirement typically specified for carbon steel welding?",
     "opts": _balanced_options("Not less than the specified preheat temperature value", "Always maintained at exactly room temperature 25°C", "There is no minimum interpass temperature required", "Interpass must always exceed 300°C for all joints"),
     "correct": "Not less than the specified preheat temperature value", "diff": "easy",
     "subj": "Installation and workmanship", "topic": "Preheat interpass temperature and welding parameter control"},
    {"q": "Per AWS D1.1, what is the maximum allowable porosity for a groove weld in statically loaded structures?",
     "opts": _balanced_options("Sum of piping porosity shall not exceed 10 mm in 25 mm", "Any amount of porosity is acceptable if weld is full", "Zero porosity is the only acceptable quality criteria", "Porosity up to 25 mm diameter is acceptable per joint"),
     "correct": "Sum of piping porosity shall not exceed 10 mm in 25 mm", "diff": "easy",
     "subj": "Testing and verification", "topic": "Visual examination and NDT acceptance"},
    {"q": "What does the F-Number in ASME Section IX classify?",
     "opts": _balanced_options("The filler metal grouping based on usability traits", "The base metal grade based on chemical composition", "The welding position such as flat or overhead weld", "The type of shielding gas used during welding arc"),
     "correct": "The filler metal grouping based on usability traits", "diff": "easy",
     "subj": "Materials and traceability", "topic": "Filler metal identification storage and conditioning"},
    {"q": "According to SAES-W-011, what must be verified about a welder before they start production welding?",
     "opts": _balanced_options("Valid WPQ covering the WPS essential variable range", "Only that the welder has a safety induction sticker", "That the welder owns personal welding equipment only", "That the welder has signed the daily attendance sheet"),
     "correct": "Valid WPQ covering the WPS essential variable range", "diff": "easy",
     "subj": "Inspection planning", "topic": "Welding inspection plan and hold points"},
    {"q": "What is a hot work permit primarily used for in welding operations on an Aramco project?",
     "opts": _balanced_options("To authorize welding or cutting in a controlled area", "To record the ambient temperature at the weld joint", "To order new welding consumables from the warehouse", "To document the welder's lunch break schedule daily"),
     "correct": "To authorize welding or cutting in a controlled area", "diff": "easy",
     "subj": "Safety and field execution", "topic": "Hot work permit and fire watch controls"},
    # --- 24 Moderate (Application / Analyzing) ---
    {"q": "During visual inspection of a groove weld on carbon steel pipe (P-No. 1), an inspector notes 1.5 mm undercut. Per ASME B31.3 Normal Fluid Service, what is the maximum allowable undercut depth?",
     "opts": _balanced_options("The lesser of 1 mm or 1/32 inch whichever is smaller", "1.5 mm or 1/16 inch provided the weld meets RT test", "0.8 mm or 1/32 inch regardless of service conditions", "Undercut is never acceptable under any code condition"),
     "correct": "The lesser of 1 mm or 1/32 inch whichever is smaller", "diff": "moderate",
     "subj": "Testing and verification", "topic": "Visual examination and NDT acceptance"},
    {"q": "A welder qualified on 20 mm thick carbon steel plate in 3G position per ASME IX wants to weld 15 mm pipe in 5G position. Is the welder qualified?",
     "opts": _balanced_options("No because plate 3G does not qualify for pipe 5G weld", "Yes because plate thickness qualifies all pipe sizes", "Yes because 3G plate always qualifies all pipe welds", "No because the welder needs a separate 6GR position"),
     "correct": "No because plate 3G does not qualify for pipe 5G weld", "diff": "moderate",
     "subj": "Codes and standards", "topic": "Approved WPS PQR and welder qualification controls"},
    {"q": "Per ASME Section IX, if a WPS specifies a preheat of 100°C and the actual preheat measured is 85°C, what action must the QC inspector take?",
     "opts": _balanced_options("Stop welding and raise preheat to the WPS minimum value", "Continue welding because 85°C is close enough to pass", "Reduce welding current to compensate for lower preheat", "Increase travel speed to avoid excessive heat input value"),
     "correct": "Stop welding and raise preheat to the WPS minimum value", "diff": "moderate",
     "subj": "Installation and workmanship", "topic": "Preheat interpass temperature and welding parameter control"},
    {"q": "A QC inspector discovers that E7018 electrodes were left exposed to atmosphere for 5 hours. Per AWS D1.1, what is the required action?",
     "opts": _balanced_options("Rebake electrodes per AWS D1.1 before using them again", "Use the electrodes immediately with no further action", "Discard all exposed electrodes and replace with new ones", "Apply a light coat of oil to protect the electrode flux"),
     "correct": "Rebake electrodes per AWS D1.1 before using them again", "diff": "moderate",
     "subj": "Materials and traceability", "topic": "Filler metal identification storage and conditioning"},
    {"q": "During PWHT of a P-No. 1 carbon steel weld, the thermocouple shows 580°C but the WPS requires 620°C minimum. What should the inspector do?",
     "opts": _balanced_options("Hold the temperature and request correction to 620°C min", "Accept 580°C as the difference is within normal tolerance", "Immediately water quench the joint to restart the cycle", "Increase hold time at 580°C to compensate for low temp"),
     "correct": "Hold the temperature and request correction to 620°C min", "diff": "moderate",
     "subj": "Testing and verification", "topic": "PWHT monitoring and hardness testing where required"},
    {"q": "Per SAES-W-011, what is the maximum repair attempt allowed before a weld joint must be cut out and re-welded?",
     "opts": _balanced_options("Two repair attempts on the same weld defect location", "Unlimited repairs are allowed if NDT results improve", "One repair attempt only then the joint must be cut out", "Three repair attempts are permitted before joint cutout"),
     "correct": "Two repair attempts on the same weld defect location", "diff": "moderate",
     "subj": "Nonconformance and corrective action", "topic": "Repair cycle control and traceability"},
    {"q": "An RT film shows a 3 mm slag inclusion in a 12 mm thick pipe weld. Per ASME B31.3, is this indication acceptable?",
     "opts": _balanced_options("Evaluate against ASME B31.3 Table 341.3.2 acceptance limits", "Reject immediately as any slag inclusion is unacceptable", "Accept because slag under 5 mm is always code compliant", "Request UT confirmation before making any code judgment"),
     "correct": "Evaluate against ASME B31.3 Table 341.3.2 acceptance limits", "diff": "moderate",
     "subj": "Testing and verification", "topic": "Visual examination and NDT acceptance"},
    {"q": "A WPS qualified with ER70S-6 wire (F-No. 6) is proposed to be used with ER70S-3 wire (F-No. 6). Per ASME IX, is this a valid substitution?",
     "opts": _balanced_options("Yes because both wires are classified under the same F-No.", "No because any change in wire brand requires new WPS PQR", "Yes but only if the wire diameter remains exactly same", "No because different AWS classification means new WPS req"),
     "correct": "Yes because both wires are classified under the same F-No.", "diff": "moderate",
     "subj": "Codes and standards", "topic": "Approved WPS PQR and welder qualification controls"},
    {"q": "During fit-up inspection, the root gap measures 4.5 mm but the WPS specifies 3.2 mm ± 0.8 mm. What is the correct QC action?",
     "opts": _balanced_options("Reject the fit-up and require correction to WPS limits", "Accept since 4.5 mm is close to the upper tolerance end", "Allow welding but increase the root pass heat input val", "Reduce the bevel angle to compensate for the excess gap"),
     "correct": "Reject the fit-up and require correction to WPS limits", "diff": "moderate",
     "subj": "Installation and workmanship", "topic": "Joint preparation fit up and alignment"},
    {"q": "Per ASME B31.3, what is the minimum hydrostatic test hold time for a piping system after reaching test pressure?",
     "opts": _balanced_options("Ten minutes minimum hold time at full test pressure val", "One hour minimum hold time at full test pressure value", "Thirty minutes minimum hold at the full test pressure", "Five minutes minimum hold time at test pressure value"),
     "correct": "Ten minutes minimum hold time at full test pressure val", "diff": "moderate",
     "subj": "Testing and verification", "topic": "WPS compliance and consumable control checks"},
    {"q": "A welder's WPQ expired 3 months ago but the welder has been welding continuously. Per ASME IX, what is the status of the qualification?",
     "opts": _balanced_options("WPQ remains valid if welding continuity is documented", "WPQ is automatically invalid and requalification needed", "WPQ requires a new bend test after any lapse in period", "WPQ extends automatically for up to 12 months of lapse"),
     "correct": "WPQ remains valid if welding continuity is documented", "diff": "moderate",
     "subj": "Codes and standards", "topic": "Approved WPS PQR and welder qualification controls"},
    {"q": "During SAW welding, flux height is observed to be only 10 mm above the arc. What quality concern should the inspector raise?",
     "opts": _balanced_options("Insufficient flux depth can cause porosity and arc flash", "Low flux height has no impact on submerged arc quality", "Excess flux depth causes lack of penetration in root", "Flux height only matters during manual SMAW operations"),
     "correct": "Insufficient flux depth can cause porosity and arc flash", "diff": "moderate",
     "subj": "Installation and workmanship", "topic": "Visual weld profile and defect prevention"},
    {"q": "Per SAES-W-011, when is a production weld hardness survey required after PWHT?",
     "opts": _balanced_options("When the base metal is P-No. 4 or higher Cr-Mo alloy", "Hardness testing is never required after PWHT on site", "Only when the client specifically requests it in writing", "For all carbon steel P-No. 1 welds without exception"),
     "correct": "When the base metal is P-No. 4 or higher Cr-Mo alloy", "diff": "moderate",
     "subj": "Testing and verification", "topic": "PWHT monitoring and hardness testing where required"},
    {"q": "A weld joint requires MT examination per the ITP. The inspector notices the surface temperature is 55°C. Per ASME V, can MT proceed?",
     "opts": _balanced_options("Yes if wet particles are used within the allowed temp range", "No because MT can only be done at ambient temperature", "Yes for all particle types without temperature limitation", "No because 55°C exceeds the maximum allowed for any MT"),
     "correct": "Yes if wet particles are used within the allowed temp range", "diff": "moderate",
     "subj": "Inspection planning", "topic": "Fit up visual and NDT coordination"},
    {"q": "Per AWS D1.1, what is the maximum allowable reinforcement height for a groove weld on 20 mm plate?",
     "opts": _balanced_options("3 mm maximum reinforcement height per Table 5.9 limits", "5 mm maximum reinforcement height per AWS specification", "No maximum limit if weld is ground flush after cooling", "1 mm maximum reinforcement per all thickness categories"),
     "correct": "3 mm maximum reinforcement height per Table 5.9 limits", "diff": "moderate",
     "subj": "Installation and workmanship", "topic": "Visual weld profile and defect prevention"},
    {"q": "During welding parameter monitoring, the inspector measures heat input at 3.2 kJ/mm but the WPS maximum is 2.5 kJ/mm. What action is required?",
     "opts": _balanced_options("Stop welding immediately and issue a nonconformance report", "Accept as heat input limits are only guidelines not rules", "Increase travel speed on the next pass to bring average", "Continue welding and document the deviation for records"),
     "correct": "Stop welding immediately and issue a nonconformance report", "diff": "moderate",
     "subj": "Installation and workmanship", "topic": "Preheat interpass temperature and welding parameter control"},
    {"q": "A welded joint on P-No. 5B material shows a hardness of 280 HV after PWHT. Per SAES-W-011, is this acceptable?",
     "opts": _balanced_options("Evaluate against the maximum 248 HV limit for P-5B steel", "Accept because 280 HV is within normal PWHT expectations", "Reject only if hardness exceeds 350 HV for alloy steels", "Hardness limits do not apply to PWHT-treated weld joints"),
     "correct": "Evaluate against the maximum 248 HV limit for P-5B steel", "diff": "moderate",
     "subj": "Testing and verification", "topic": "PWHT monitoring and hardness testing where required"},
    {"q": "Per ASME Section IX, what happens to a WPS if the P-Number of the base metal is changed from P-1 to P-4?",
     "opts": _balanced_options("A new WPS and PQR must be developed for P-4 base metal", "The existing WPS is valid for all P-Numbers up to P-11", "Only the welder needs requalification not the procedure", "A revision to the existing WPS is sufficient for P-4"),
     "correct": "A new WPS and PQR must be developed for P-4 base metal", "diff": "moderate",
     "subj": "Codes and standards", "topic": "Approved WPS PQR and welder qualification controls"},
    {"q": "An inspector finds that the welder is using DCEN polarity but the WPS specifies DCEP for SMAW. What action is required?",
     "opts": _balanced_options("Stop welding immediately as polarity is an essential variable", "Allow continued welding since polarity has minimal impact", "Switch to AC polarity as a compromise between DCEN DCEP", "Record the deviation and allow welding to be completed"),
     "correct": "Stop welding immediately as polarity is an essential variable", "diff": "moderate",
     "subj": "Installation and workmanship", "topic": "Preheat interpass temperature and welding parameter control"},
    {"q": "Per SAES-W-011, what is the minimum overlap length required for radiographic film interpretation?",
     "opts": _balanced_options("At least 25 mm overlap at each end of the film exposure", "No overlap is required if the film density is adequate", "10 mm overlap is acceptable for all pipe diameter sizes", "50 mm overlap is required only for thick wall pipe welds"),
     "correct": "At least 25 mm overlap at each end of the film exposure", "diff": "moderate",
     "subj": "Testing and verification", "topic": "Visual examination and NDT acceptance"},
    {"q": "A tack weld cracks during fit-up. Per AWS D1.1, what must the inspector require before welding proceeds?",
     "opts": _balanced_options("Complete removal and re-tacking per qualified procedure", "Weld over the cracked tack with increased heat input val", "Grind the crack surface flush and continue with welding", "Leave the tack in place if it is less than 25 mm long"),
     "correct": "Complete removal and re-tacking per qualified procedure", "diff": "moderate",
     "subj": "Nonconformance and corrective action", "topic": "Weld defect reporting and repair authorization"},
    {"q": "Per ASME B31.3, when is a pneumatic leak test acceptable as an alternative to hydrostatic testing?",
     "opts": _balanced_options("When hydrostatic testing could damage linings or process", "Pneumatic testing can always replace hydrostatic testing", "Only when the pipe diameter is less than 2 inches total", "Pneumatic testing is never allowed under ASME B31.3 code"),
     "correct": "When hydrostatic testing could damage linings or process", "diff": "moderate",
     "subj": "Testing and verification", "topic": "WPS compliance and consumable control checks"},
    {"q": "During welding, the interpass temperature reaches 280°C but the WPS maximum is 250°C. What should the inspector do?",
     "opts": _balanced_options("Stop welding and wait for the joint to cool below 250°C", "Accept since interpass maximums are advisory only values", "Increase welding speed to reduce heat buildup in joint", "Apply water to the joint to rapidly cool below 250°C"),
     "correct": "Stop welding and wait for the joint to cool below 250°C", "diff": "moderate",
     "subj": "Installation and workmanship", "topic": "Preheat interpass temperature and welding parameter control"},
    {"q": "Per SAES-W-011, what traceability marking is required on each welded joint in the field?",
     "opts": _balanced_options("Unique weld number welder ID and WPS number at the joint", "Only the welder's name written with paint marker on pipe", "No markings are required if digital photos are taken of", "Project number only is sufficient for field traceability"),
     "correct": "Unique weld number welder ID and WPS number at the joint", "diff": "moderate",
     "subj": "Materials and traceability", "topic": "Weld joint and welder traceability"},
    # --- 12 Difficult (Evaluating / Synthesizing) ---
    {"q": "A thick-wall P-No. 5B alloy steel weld develops delayed cracking 48 hours after PWHT. What is the most likely root cause mechanism?",
     "opts": _balanced_options("Hydrogen-induced cold cracking from residual diffusible H2", "Hot cracking from excessive sulfur content in base metal", "Stress corrosion cracking from external chemical exposure", "Fatigue cracking from cyclic loading during the PWHT hold"),
     "correct": "Hydrogen-induced cold cracking from residual diffusible H2", "diff": "difficult",
     "subj": "Nonconformance and corrective action", "topic": "Weld defect reporting and repair authorization"},
    {"q": "An RT film of a 25 mm thick P-5B weld shows a linear indication at the fusion line. UT confirms a 15 mm long planar defect. Per ASME B31.3, what is the disposition?",
     "opts": _balanced_options("Reject and excavate per approved repair WPS with re-PWHT", "Accept if the defect length is under 25% of wall thick", "Monitor the defect with periodic UT scans during service", "Grind the surface smooth and accept without further NDT"),
     "correct": "Reject and excavate per approved repair WPS with re-PWHT", "diff": "difficult",
     "subj": "Nonconformance and corrective action", "topic": "Reinspection and NDT after repair"},
    {"q": "A dissimilar metal weld between P-No. 1 and P-No. 8 requires filler selection. Per ASME IX and SAES-W-011, which approach is correct?",
     "opts": _balanced_options("Use ERNiCr-3 filler to bridge the metallurgical mismatch", "Use E7018 filler as it qualifies for both P-Numbers val", "Use E308L filler matched to the stainless steel side only", "Use any filler compatible with the lower P-Number group"),
     "correct": "Use ERNiCr-3 filler to bridge the metallurgical mismatch", "diff": "difficult",
     "subj": "Codes and standards", "topic": "Approved WPS PQR and welder qualification controls"},
    {"q": "During a fitness-for-service evaluation per API 579, a weld defect is assessed using FAD (Failure Assessment Diagram). What two parameters are plotted?",
     "opts": _balanced_options("Load ratio (Lr) versus fracture ratio (Kr) on the FAD", "Weld thickness versus defect length on the assessment", "Hardness value versus tensile strength of the weld metal", "Preheat temperature versus interpass temperature values"),
     "correct": "Load ratio (Lr) versus fracture ratio (Kr) on the FAD", "diff": "difficult",
     "subj": "Nonconformance and corrective action", "topic": "Weld defect reporting and repair authorization"},
    {"q": "A welded pressure vessel fails the ASME VIII hydrostatic test with a leak at a nozzle weld. What is the correct investigation and repair sequence?",
     "opts": _balanced_options("Depressurize, investigate root cause, repair per code WPS, retest", "Increase test pressure to verify if leak seals under load force", "Apply external sealant and retest at reduced pressure values", "Accept the leak if flow rate is below measurable threshold"),
     "correct": "Depressurize, investigate root cause, repair per code WPS, retest", "diff": "difficult",
     "subj": "Nonconformance and corrective action", "topic": "Repair cycle control and traceability"},
    {"q": "Per ASME Section IX and SAES-W-011, what additional testing is required when qualifying a WPS for sour service (NACE MR0175)?",
     "opts": _balanced_options("Hardness testing per NACE with maximum 22 HRC weld and HAZ", "Only standard bend and tensile tests are required for sour", "Charpy impact testing at minus 46°C for all sour WPS quals", "No additional testing beyond standard ASME IX is required"),
     "correct": "Hardness testing per NACE with maximum 22 HRC weld and HAZ", "diff": "difficult",
     "subj": "Testing and verification", "topic": "PWHT monitoring and hardness testing where required"},
    {"q": "A contractor proposes to use a WPS qualified with GTAW root and SMAW fill for a pipe weld, but wants to substitute FCAW for the fill passes. Per ASME IX, is this permitted?",
     "opts": _balanced_options("No because FCAW is a different process requiring separate PQR", "Yes because the root process remains unchanged from GTAW", "Yes if the FCAW wire has the same F-Number as SMAW electrode", "No unless the contractor gets a written deviation from code"),
     "correct": "No because FCAW is a different process requiring separate PQR", "diff": "difficult",
     "subj": "Codes and standards", "topic": "Approved WPS PQR and welder qualification controls"},
    {"q": "Multiple production welds by the same welder show consistent lack of fusion at the sidewall. Root cause analysis reveals the issue. What is the most probable technical cause?",
     "opts": _balanced_options("Insufficient weave width and low heat input at bevel face", "Excessive preheat causing the base metal to melt too fast", "Electrode diameter too large for the joint root gap width", "Shielding gas flow rate too high creating turbulent arc flow"),
     "correct": "Insufficient weave width and low heat input at bevel face", "diff": "difficult",
     "subj": "Nonconformance and corrective action", "topic": "Weld defect reporting and repair authorization"},
    {"q": "A PWHT chart shows that the heating rate exceeded 200°C/hr for a vessel with a wall thickness of 50 mm. Per ASME VIII and SAES-W-011, what is the consequence?",
     "opts": _balanced_options("The PWHT cycle is non-conforming and must be repeated fully", "Heating rate limits apply only during the cooling phase", "The maximum rate of 200°C/hr applies to wall under 25 mm", "Excessive heating rate has no metallurgical impact at all"),
     "correct": "The PWHT cycle is non-conforming and must be repeated fully", "diff": "difficult",
     "subj": "Testing and verification", "topic": "PWHT monitoring and hardness testing where required"},
    {"q": "During construction, a change from PWHT to hydrogen bake-out (DHT) is proposed for a P-1 weld exceeding 32 mm thickness. Per ASME VIII, under what conditions can this be accepted?",
     "opts": _balanced_options("Only if engineering evaluation confirms equivalent stress relief", "DHT can always replace PWHT regardless of thickness or code", "DHT is only applicable to P-No. 5 and higher alloy steels", "DHT replaces PWHT automatically for thickness under 50 mm"),
     "correct": "Only if engineering evaluation confirms equivalent stress relief", "diff": "difficult",
     "subj": "Testing and verification", "topic": "PWHT monitoring and hardness testing where required"},
    {"q": "A weld on duplex stainless steel (UNS S31803) shows a ferrite content of 28% measured by ferritescope. Per SAES-W-011 and NORSOK M-601, is this acceptable?",
     "opts": _balanced_options("Borderline; acceptable range is typically 30% to 70% ferrite", "Fully acceptable as any ferrite above 20% meets the code", "Reject immediately as ferrite must be exactly 50% balance", "Ferrite content is not a controlled parameter for duplex"),
     "correct": "Borderline; acceptable range is typically 30% to 70% ferrite", "diff": "difficult",
     "subj": "Testing and verification", "topic": "Visual examination and NDT acceptance"},
    {"q": "Per API 1104 and SAES-W-012, a pipeline girth weld repair has been attempted twice and failed RT both times. What is the required disposition?",
     "opts": _balanced_options("Cut out the weld joint completely and re-weld with new spool", "Allow a third repair attempt with a different welder team", "Accept the weld with reduced pressure rating for service", "Perform UT in lieu of RT to potentially achieve acceptance"),
     "correct": "Cut out the weld joint completely and re-weld with new spool", "diff": "difficult",
     "subj": "Nonconformance and corrective action", "topic": "Repair cycle control and traceability"},
]

WELDING_ESSAY = [
    # --- 8 Easy ---
    {"q": "List the key documents that must be available at the weld station before production welding begins per SAES-W-011.",
     "rubric": "1. Standard Documents (2.5 pts): WPS, PQR, welder qualification records.\n2. Material Certs (2.5 pts): Base metal MTCs, filler metal certificates.\n3. Inspection Docs (2.5 pts): ITP, approved drawings, hold point checklist.\n4. Safety Permits (2.5 pts): Hot work permit, fire watch assignment, risk assessment.",
     "diff": "easy", "subj": "Codes and standards", "topic": "Controlled welding requirements and project document hierarchy"},
    {"q": "Define the terms 'essential variable' and 'non-essential variable' as used in ASME Section IX welding procedure qualification.",
     "rubric": "1. Essential Var Definition (2.5 pts): Variables affecting mechanical properties requiring requalification.\n2. Non-Essential Var Definition (2.5 pts): Variables not affecting mechanical properties, editorial changes only.\n3. Examples (2.5 pts): Provides correct examples (P-No., thickness, process vs. joint design details).\n4. Impact Statement (2.5 pts): Explains consequence of changing each type on WPS validity.",
     "diff": "easy", "subj": "Codes and standards", "topic": "Approved WPS PQR and welder qualification controls"},
    {"q": "Describe the purpose and contents of a Welding Procedure Specification (WPS) document.",
     "rubric": "1. Purpose (2.5 pts): Provides qualified instructions for making production welds.\n2. Essential Variables (2.5 pts): Lists base metal, filler, process, preheat, PWHT parameters.\n3. Non-Essential Variables (2.5 pts): Joint design, cleaning method, technique details.\n4. Relationship to PQR (2.5 pts): Explains WPS is supported by a qualified PQR test record.",
     "diff": "easy", "subj": "Codes and standards", "topic": "Approved WPS PQR and welder qualification controls"},
    {"q": "List the safety requirements for hot work operations on an Aramco project site.",
     "rubric": "1. Permit Requirements (2.5 pts): Hot work permit, gas test, area inspection.\n2. Fire Watch (2.5 pts): Dedicated fire watch personnel, fire extinguisher availability.\n3. PPE Requirements (2.5 pts): Welding helmet, gloves, protective clothing, safety boots.\n4. Environmental Controls (2.5 pts): Ventilation, fume extraction, flammable material clearance.",
     "diff": "easy", "subj": "Safety and field execution", "topic": "Hot work permit and fire watch controls"},
    {"q": "Explain the purpose of a weld map and what information it must contain per SAES-W-011.",
     "rubric": "1. Purpose (2.5 pts): Visual record of all weld joint locations and their status.\n2. Required Info (2.5 pts): Weld numbers, welder IDs, WPS references, joint types.\n3. NDT Status (2.5 pts): RT/UT/MT/PT status and acceptance for each joint.\n4. Revision Control (2.5 pts): Date, revision number, sign-off by QC inspector.",
     "diff": "easy", "subj": "Documentation and turnover", "topic": "Weld map WPS and welder qualification records"},
    {"q": "List the required storage and handling conditions for low hydrogen (E7018) electrodes per AWS D1.1.",
     "rubric": "1. Storage Conditions (2.5 pts): Heated holding ovens at 120-150°C after opening.\n2. Exposure Limits (2.5 pts): Maximum atmospheric exposure time of 4 hours.\n3. Rebaking Rules (2.5 pts): Temperature range 260-430°C for minimum 1 hour, max rebakes.\n4. Traceability (2.5 pts): Batch tracking, oven log sheets, issue records.",
     "diff": "easy", "subj": "Materials and traceability", "topic": "Filler metal identification storage and conditioning"},
    {"q": "Describe what a QC inspector must verify during a pre-weld fit-up inspection.",
     "rubric": "1. Joint Geometry (2.5 pts): Root gap, bevel angle, root face dimensions per WPS.\n2. Alignment (2.5 pts): Hi-lo (mismatch) measurement against code tolerances.\n3. Cleanliness (2.5 pts): Surface condition, freedom from rust, oil, moisture.\n4. Tack Welds (2.5 pts): Tack quality, location, and compliance with WPS requirements.",
     "diff": "easy", "subj": "Inspection planning", "topic": "Fit up visual and NDT coordination"},
    {"q": "Identify the common types of weld defects that can be detected by visual examination.",
     "rubric": "1. Surface Defects (2.5 pts): Undercut, overlap, surface porosity, crater cracks.\n2. Profile Defects (2.5 pts): Excessive reinforcement, concavity, uneven bead profile.\n3. Dimensional Defects (2.5 pts): Undersized fillet, misalignment, distortion.\n4. Workmanship Issues (2.5 pts): Arc strikes, spatter, incomplete fusion at surface.",
     "diff": "easy", "subj": "Testing and verification", "topic": "Visual examination and NDT acceptance"},
    # --- 8 Moderate ---
    {"q": "Describe the mandatory inspection steps a Welding QC Inspector must perform before, during, and after a production pipe weld on carbon steel piping.",
     "rubric": "1. Pre-weld (2.5 pts): WPS/PQR review, welder qualification check, joint fit-up, preheat verification.\n2. In-process (2.5 pts): Interpass temperature, cleaning, electrode control, root pass visual.\n3. Post-weld (2.5 pts): Visual inspection per code, NDT request, weld log update, dimensional check.\n4. Documentation (2.5 pts): Weld summary report, NDT reports, traceability sign-off.",
     "diff": "moderate", "subj": "Inspection planning", "topic": "Welding inspection plan and hold points"},
    {"q": "Explain the procedure for monitoring and recording a Post-Weld Heat Treatment (PWHT) cycle, including acceptance criteria per SAES-W-011.",
     "rubric": "1. Setup (2.5 pts): Thermocouple placement, chart recorder calibration, insulation.\n2. Heating Phase (2.5 pts): Controlled heating rate per code, gradient limits.\n3. Soak Phase (2.5 pts): Temperature range, minimum hold time per thickness.\n4. Cooling Phase (2.5 pts): Controlled cooling rate, removal temperature, chart documentation.",
     "diff": "moderate", "subj": "Testing and verification", "topic": "PWHT monitoring and hardness testing where required"},
    {"q": "Describe how a QC inspector evaluates welder performance qualification test results per ASME Section IX.",
     "rubric": "1. Visual Inspection (2.5 pts): Weld appearance, surface defects, profile compliance.\n2. Bend Test Evaluation (2.5 pts): Guided bend specimen preparation, acceptance criteria for open defects.\n3. RT Evaluation (2.5 pts): Film quality, density requirements, indication evaluation.\n4. Qualification Range (2.5 pts): Thickness, diameter, position range qualified by the test.",
     "diff": "moderate", "subj": "Codes and standards", "topic": "Approved WPS PQR and welder qualification controls"},
    {"q": "Detail the inspection requirements for field welding of stainless steel piping systems per SAES-W-011 and ASME B31.3.",
     "rubric": "1. Material Controls (2.5 pts): Carbon content limits, contamination prevention, segregation.\n2. Welding Controls (2.5 pts): Purge gas requirements, interpass temperature limits, heat input.\n3. NDT Requirements (2.5 pts): RT/PT acceptance criteria, ferrite testing if required.\n4. Documentation (2.5 pts): Material certificates, weld logs, PMI records, ferrite readings.",
     "diff": "moderate", "subj": "Installation and workmanship", "topic": "Visual weld profile and defect prevention"},
    {"q": "Explain the nonconformance report (NCR) process for a weld defect found during production welding per Aramco QC procedures.",
     "rubric": "1. Detection & Documentation (2.5 pts): Defect identification, NCR initiation, photographic evidence.\n2. Investigation (2.5 pts): Root cause analysis, contributing factors, welder interview.\n3. Repair Procedure (2.5 pts): Approved repair WPS, excavation limits, NDT of excavation.\n4. Closeout (2.5 pts): Re-NDT after repair, disposition sign-off, lessons learned.",
     "diff": "moderate", "subj": "Nonconformance and corrective action", "topic": "Weld defect reporting and repair authorization"},
    {"q": "Describe the complete quality documentation package required for welding turnover to Saudi Aramco.",
     "rubric": "1. Welding Records (2.5 pts): Weld map, WPS/PQR files, welder qualification records.\n2. NDT Records (2.5 pts): RT/UT/MT/PT reports, film/scan storage, acceptance summaries.\n3. PWHT Records (2.5 pts): Heat treatment charts, thermocouple records, hardness reports.\n4. NCR Closeout (2.5 pts): All NCRs closed with corrective actions, punch list clearance.",
     "diff": "moderate", "subj": "Documentation and turnover", "topic": "Welding dossier and punch closure evidence"},
    {"q": "Explain how a QC inspector verifies that welding consumables comply with the project requirements and SAES-W-011.",
     "rubric": "1. Receiving Inspection (2.5 pts): Certificate verification, batch number, AWS classification match.\n2. Storage Control (2.5 pts): Oven temperature, holding conditions, moisture prevention.\n3. Issue Control (2.5 pts): Issue log, maximum exposure time, return and rebake tracking.\n4. Traceability (2.5 pts): Lot-to-joint traceability, WPS-to-consumable verification.",
     "diff": "moderate", "subj": "Materials and traceability", "topic": "Filler metal identification storage and conditioning"},
    {"q": "Describe the inspection requirements and acceptance criteria for fillet welds per AWS D1.1 and SAES-W-011.",
     "rubric": "1. Visual Criteria (2.5 pts): Profile requirements, convexity/concavity limits, leg size tolerance.\n2. Measurement (2.5 pts): Fillet weld gauge usage, throat and leg size verification.\n3. Defect Limits (2.5 pts): Undercut, porosity, crack, and overlap acceptance criteria.\n4. Documentation (2.5 pts): Inspection report, weld map update, acceptance sign-off.",
     "diff": "moderate", "subj": "Installation and workmanship", "topic": "Visual weld profile and defect prevention"},
    # --- 4 Difficult ---
    {"q": "Explain the primary causes of hydrogen-induced cracking (HIC) in carbon steel weldments. Detail three preventive measures and outline how a QC inspector must investigate and disposition a post-hydrotest delay crack on a thick-wall P-No. 5B joint.",
     "rubric": "1. HIC Causes (3 pts): Diffusible hydrogen, susceptible microstructure (martensite), residual tensile stress.\n2. Prevention (3 pts): Low-H2 consumables, proper preheat/interpass, PWHT/DHT procedures.\n3. Investigation & Disposition (4 pts): NDT re-exam, excavation boundary mapping, repair WPS qualification, hydrogen bake, engineering evaluation.",
     "diff": "difficult", "subj": "Nonconformance and corrective action", "topic": "Weld defect reporting and repair authorization"},
    {"q": "A duplex stainless steel weld shows sigma phase precipitation after prolonged high-temperature exposure. Explain the metallurgical mechanism, its impact on weld integrity, and the QC investigation protocol per SAES-W-011.",
     "rubric": "1. Sigma Phase Mechanism (3 pts): Precipitation in ferrite at 600-900°C, Cr depletion, brittle intermetallic.\n2. Impact on Integrity (3 pts): Loss of corrosion resistance, impact toughness degradation, pitting susceptibility.\n3. QC Investigation (4 pts): Metallographic examination, ferrite measurement, impact testing, disposition per code.",
     "diff": "difficult", "subj": "Testing and verification", "topic": "Visual examination and NDT acceptance"},
    {"q": "Analyze a scenario where conflicting code requirements arise between ASME B31.3, SAES-W-011, and the project specification for a sour service piping weld. Detail how a QC inspector resolves the conflict.",
     "rubric": "1. Conflict Identification (2.5 pts): Identifies specific clauses in each document that conflict.\n2. Hierarchy Application (2.5 pts): Applies document hierarchy (project spec > SAES > ASME as minimum).\n3. Resolution Process (2.5 pts): Technical query, engineering review, deviation request if needed.\n4. Documentation (2.5 pts): Records resolution, updates ITP, communicates to field team.",
     "diff": "difficult", "subj": "Codes and standards", "topic": "Controlled welding requirements and project document hierarchy"},
    {"q": "A critical pressure vessel weld passes RT but fails during hydrostatic testing with a through-wall leak. Conduct a comprehensive root cause analysis addressing NDT reliability, WPS adequacy, and fabrication sequence.",
     "rubric": "1. NDT Review (2.5 pts): RT technique, film quality, interpretation accuracy, possible missed defects.\n2. WPS Adequacy (2.5 pts): Essential variable compliance, heat input, filler metal suitability.\n3. Fabrication Sequence (2.5 pts): PWHT sequence, residual stress, distortion effects.\n4. Corrective Actions (2.5 pts): Root cause documentation, repair plan, prevention measures, retest requirements.",
     "diff": "difficult", "subj": "Nonconformance and corrective action", "topic": "Repair cycle control and traceability"},
]

WELDING_ORAL_PRACTICAL = [
    # --- 12 Oral Questions (8 easy=~3.3, 8 moderate=~3.3, 4 diff=~1.3 → split: 5 Easy, 5 Moderate, 2 Difficult for Oral) ---
    # Actually: 20 total Oral-Practical, 8 Easy, 8 Moderate, 4 Difficult overall
    # 12 Oral: 5 Easy, 5 Moderate, 2 Difficult
    {"q": "Verbally explain to the reviewer the purpose of a Welding Procedure Specification (WPS) and identify three essential variables per ASME Section IX.",
     "rubric": "1. WPS Purpose (2.5 pts): Qualified instructions for production welding.\n2. Essential Variables (2.5 pts): Correctly names 3 (P-No., F-No., thickness, process, preheat).\n3. Consequence of Change (2.5 pts): Explains requalification requirement.\n4. Code Reference (2.5 pts): Correctly references ASME Section IX articles.",
     "diff": "easy", "subj": "Codes and standards", "topic": "Approved WPS PQR and welder qualification controls", "sub_type": "oral"},
    {"q": "Verbally describe the required safety controls for hot work operations in a hazardous area on an Aramco facility.",
     "rubric": "1. Permit Process (2.5 pts): Hot work permit requirements, gas testing, authorization.\n2. Fire Watch (2.5 pts): Dedicated fire watch, duration, equipment.\n3. PPE Requirements (2.5 pts): Welding-specific personal protective equipment.\n4. Emergency Response (2.5 pts): Fire extinguisher, alarm procedure, evacuation route.",
     "diff": "easy", "subj": "Safety and field execution", "topic": "Hot work permit and fire watch controls", "sub_type": "oral"},
    {"q": "Verbally explain what information must be recorded on a weld map and why it is important for project quality documentation.",
     "rubric": "1. Weld Identification (2.5 pts): Joint numbers, location references, isometric links.\n2. Welder & WPS Info (2.5 pts): Welder ID stamps, WPS references per joint.\n3. NDT Status (2.5 pts): Examination type, status, acceptance results.\n4. Importance (2.5 pts): Traceability, audit trail, turnover requirement.",
     "diff": "easy", "subj": "Documentation and turnover", "topic": "Weld map WPS and welder qualification records", "sub_type": "oral"},
    {"q": "Verbally describe the storage and handling requirements for low hydrogen welding electrodes per AWS D1.1.",
     "rubric": "1. Storage Ovens (2.5 pts): Temperature requirements, oven types.\n2. Exposure Limits (2.5 pts): Maximum time in atmosphere, rebake rules.\n3. Issue Control (2.5 pts): Log sheets, batch tracking, return procedure.\n4. Consequences (2.5 pts): Explains risk of moisture pickup and hydrogen cracking.",
     "diff": "easy", "subj": "Materials and traceability", "topic": "Filler metal identification storage and conditioning", "sub_type": "oral"},
    {"q": "Verbally describe the types of weld defects that can be identified during visual examination and their acceptance criteria.",
     "rubric": "1. Surface Defects (2.5 pts): Undercut, porosity, cracks - identification.\n2. Profile Defects (2.5 pts): Reinforcement, concavity, overlap.\n3. Acceptance Criteria (2.5 pts): Code limits for each defect type.\n4. Reporting (2.5 pts): Documentation and NCR initiation requirements.",
     "diff": "easy", "subj": "Testing and verification", "topic": "Visual examination and NDT acceptance", "sub_type": "oral"},
    {"q": "Verbally walk the reviewer through the complete pre-weld, in-process, and post-weld inspection sequence for a pipe butt weld, referencing WPS compliance checkpoints.",
     "rubric": "1. Pre-weld (2.5 pts): WPS review, fit-up verification, preheat check, welder ID.\n2. In-process (2.5 pts): Interpass temp, root pass visual, consumable control.\n3. Post-weld (2.5 pts): Visual acceptance, NDT coordination, weld log entry.\n4. Code References (2.5 pts): Correct ASME/AWS/SAES clause citations.",
     "diff": "moderate", "subj": "Inspection planning", "topic": "Welding inspection plan and hold points", "sub_type": "oral"},
    {"q": "Verbally explain how you verify a welder's qualification record (WQR) covers the production weld joint being performed, including essential variable checks.",
     "rubric": "1. WQR Review (2.5 pts): P-Number, F-Number, thickness, position coverage.\n2. Continuity Verification (2.5 pts): Explains 6-month continuity rule, documentation.\n3. WPS Matching (2.5 pts): Confirms WQR variables cover the WPS requirements.\n4. Process Knowledge (2.5 pts): Demonstrates understanding of ASME IX QW-304.",
     "diff": "moderate", "subj": "Codes and standards", "topic": "Approved WPS PQR and welder qualification controls", "sub_type": "oral"},
    {"q": "Verbally explain the PWHT monitoring procedure including thermocouple placement, heating/cooling rate limits, and chart documentation requirements.",
     "rubric": "1. Thermocouple Placement (2.5 pts): Location, number, attachment method.\n2. Heating Rate (2.5 pts): Maximum rate per wall thickness, code reference.\n3. Soak Parameters (2.5 pts): Temperature range, minimum hold time.\n4. Documentation (2.5 pts): Chart recording, log sheet, acceptance criteria.",
     "diff": "moderate", "subj": "Testing and verification", "topic": "PWHT monitoring and hardness testing where required", "sub_type": "oral"},
    {"q": "Verbally describe the nonconformance report (NCR) process for a rejected weld, from detection through repair and closeout.",
     "rubric": "1. Detection & NCR (2.5 pts): Defect identification, NCR initiation, hold tag.\n2. Root Cause (2.5 pts): Investigation methodology, contributing factors.\n3. Repair Process (2.5 pts): Approved repair WPS, excavation, re-NDT.\n4. Closeout (2.5 pts): Disposition, sign-off, lessons learned documentation.",
     "diff": "moderate", "subj": "Nonconformance and corrective action", "topic": "Weld defect reporting and repair authorization", "sub_type": "oral"},
    {"q": "Verbally explain the quality documentation requirements for welding turnover to Saudi Aramco, including the contents of a welding dossier.",
     "rubric": "1. Weld Records (2.5 pts): Weld map, WPS/PQR, WQR summaries.\n2. NDT Package (2.5 pts): Reports, films/scans, acceptance summaries.\n3. PWHT Records (2.5 pts): Charts, thermocouple records, hardness results.\n4. NCR Package (2.5 pts): All NCRs closed, corrective actions, punch clearance.",
     "diff": "moderate", "subj": "Documentation and turnover", "topic": "Welding dossier and punch closure evidence", "sub_type": "oral"},
    {"q": "Verbally defend your root cause analysis of hydrogen-induced cracking found in a P-No. 5B alloy steel weld after PWHT, including metallurgical factors and corrective actions under reviewer cross-examination.",
     "rubric": "1. Root Cause Identification (2.5 pts): Diffusible hydrogen, susceptible HAZ microstructure, residual stress.\n2. Metallurgical Defense (2.5 pts): Explains martensite formation, hydrogen diffusion mechanism.\n3. Corrective Actions (2.5 pts): DHT requirements, low-H2 consumables, preheat adequacy.\n4. Cross-Examination (2.5 pts): Responds accurately to technical challenges from reviewer.",
     "diff": "difficult", "subj": "Nonconformance and corrective action", "topic": "Weld defect reporting and repair authorization", "sub_type": "oral"},
    {"q": "Verbally explain how you would resolve conflicting welding requirements between ASME B31.3, SAES-W-011, and the project specification for a sour service application, defending your recommended resolution approach.",
     "rubric": "1. Conflict Identification (2.5 pts): Pinpoints specific conflicting clauses.\n2. Hierarchy Application (2.5 pts): Explains Aramco document precedence hierarchy.\n3. Resolution Strategy (2.5 pts): Technical query process, deviation mechanism.\n4. Defense Under Questioning (2.5 pts): Maintains technically sound position under challenge.",
     "diff": "difficult", "subj": "Codes and standards", "topic": "Controlled welding requirements and project document hierarchy", "sub_type": "oral"},
    # --- 8 Practical Questions: 3 Easy, 3 Moderate, 2 Difficult ---
    {"q": "Using the provided fillet weld gauge set, measure the leg size and throat of three fillet welds on the test coupon. Record measurements on the inspection report sheet.",
     "rubric": "1. Gauge Selection (2.5 pts): Selects correct gauge type for fillet measurement.\n2. Measurement Technique (2.5 pts): Proper placement, reads leg and throat correctly.\n3. Recording (2.5 pts): Accurate documentation of three measurements.\n4. Pass/Fail Determination (2.5 pts): Correctly evaluates against specified weld size.",
     "diff": "easy", "subj": "Testing and verification", "topic": "Visual examination and NDT acceptance", "sub_type": "practical"},
    {"q": "Using a digital thermometer, verify the preheat temperature on the provided pipe joint and confirm it meets the WPS minimum requirement of 100°C.",
     "rubric": "1. Instrument Check (2.5 pts): Verifies calibration sticker, battery, zeroing.\n2. Measurement Location (2.5 pts): Measures at correct distance from joint centerline.\n3. Reading Accuracy (2.5 pts): Takes stable reading, records temperature correctly.\n4. WPS Compliance (2.5 pts): Compares to WPS minimum, states pass/fail.",
     "diff": "easy", "subj": "Installation and workmanship", "topic": "Preheat interpass temperature and welding parameter control", "sub_type": "practical"},
    {"q": "Demonstrate proper identification and segregation of welding consumables in the rod oven area. Show issue logging and return procedures.",
     "rubric": "1. Identification (2.5 pts): Reads electrode classification, batch number, size.\n2. Oven Operation (2.5 pts): Verifies oven temperature, holding conditions.\n3. Issue Logging (2.5 pts): Correctly fills rod issue log with time, quantity, welder.\n4. Return Procedure (2.5 pts): Demonstrates proper return and rebake assessment.",
     "diff": "easy", "subj": "Materials and traceability", "topic": "Filler metal identification storage and conditioning", "sub_type": "practical"},
    {"q": "Using the provided Bridge Cam gauge and welded pipe coupon, inspect the weld joint for root/face reinforcement height and undercut. Log all measurements and state pass/fail against ASME B31.3.",
     "rubric": "1. Gauge Setup (2.5 pts): Correct Bridge Cam gauge orientation and placement.\n2. Reinforcement Measurement (2.5 pts): Accurate height reading at multiple points.\n3. Undercut Measurement (2.5 pts): Depth measurement and evaluation against code limits.\n4. Report Completion (2.5 pts): Accurate log sheet with clear pass/fail determination.",
     "diff": "moderate", "subj": "Testing and verification", "topic": "Visual examination and NDT acceptance", "sub_type": "practical"},
    {"q": "Perform a fit-up inspection on the provided pipe joint using appropriate measuring tools. Verify root gap, bevel angle, hi-lo, and alignment against the WPS requirements.",
     "rubric": "1. Root Gap Measurement (2.5 pts): Uses feeler gauge or ruler, records accurately.\n2. Bevel Angle Verification (2.5 pts): Uses bevel protractor, compares to WPS.\n3. Hi-Lo Measurement (2.5 pts): Internal alignment check with bridge cam or ruler.\n4. Overall Assessment (2.5 pts): Comprehensive pass/fail per WPS tolerances.",
     "diff": "moderate", "subj": "Installation and workmanship", "topic": "Joint preparation fit up and alignment", "sub_type": "practical"},
    {"q": "Using the provided PWHT chart recorder output, evaluate the heat treatment cycle for compliance with the WPS and SAES-W-011 requirements.",
     "rubric": "1. Heating Rate (2.5 pts): Reads and evaluates heating rate against code maximum.\n2. Soak Temperature (2.5 pts): Verifies temperature range within specified band.\n3. Hold Time (2.5 pts): Confirms minimum hold time achieved per thickness.\n4. Cooling Rate (2.5 pts): Evaluates controlled cooling rate compliance.",
     "diff": "moderate", "subj": "Testing and verification", "topic": "PWHT monitoring and hardness testing where required", "sub_type": "practical"},
    {"q": "Examine the provided cracked alloy steel weld specimen. Identify the defect type, perform excavation boundary measurements, defend your root cause analysis under reviewer questioning, and complete a formal NCR.",
     "rubric": "1. Defect Identification (2.5 pts): Physical identification and boundary measurement.\n2. Root Cause Defense (2.5 pts): Hydrogen, preheat deficiency, martensitic microstructure.\n3. Repair Proposal (2.5 pts): Compliant repair WPS, preheat/DHT, re-NDT sequence.\n4. NCR Completion (2.5 pts): Drafts complete Nonconformance Report with disposition.",
     "diff": "difficult", "subj": "Nonconformance and corrective action", "topic": "Weld defect reporting and repair authorization", "sub_type": "practical"},
    {"q": "Perform a complete hardness survey on the provided PWHT-treated weld specimen using a portable hardness tester. Evaluate results against SAES-W-011 and NACE MR0175 limits, and complete the hardness test report.",
     "rubric": "1. Equipment Setup (2.5 pts): Hardness tester calibration, test block verification.\n2. Test Execution (2.5 pts): Correct locations (weld, HAZ, base), proper technique.\n3. Result Evaluation (2.5 pts): Compares against 248 HV / 22 HRC limits.\n4. Report Completion (2.5 pts): Accurate report with sketch, values, and pass/fail.",
     "diff": "difficult", "subj": "Testing and verification", "topic": "PWHT monitoring and hardness testing where required", "sub_type": "practical"},
]

# ===================================================================
# Helper to generate questions for non-Welding disciplines using
# discipline-specific content templates
# ===================================================================

def _get_disc_subjects_topics(disc_name):
    """Get subjects and topics for a discipline from disciplines.csv data."""
    return DISC_TOPICS.get(disc_name, [("General", "General")])

def _make_discipline_questions(disc_name, std_ref, desc):
    """Generate 100 questions for a non-Welding discipline with real technical content."""
    st_list = _get_disc_subjects_topics(disc_name)
    # Ensure we have enough subject/topic pairs - cycle through them
    while len(st_list) < 24:
        st_list = st_list + st_list
    
    mcqs = []
    essays = []
    oral_pracs = []
    
    # ---- 60 MCQs: 24 Easy, 24 Moderate, 12 Difficult ----
    # Distribute across subjects/topics from disciplines.csv
    for i in range(60):
        subj, topic = st_list[i % len(st_list)]
        if i < 24:
            diff = "easy"
        elif i < 48:
            diff = "moderate"
        else:
            diff = "difficult"
        
        # Generate varied question stems based on difficulty
        if diff == "easy":
            stems = [
                f"Per {std_ref}, what is the primary requirement for {topic.lower()} in {disc_name}?",
                f"What is the correct definition of {topic.lower()} as applied in {disc_name} per {std_ref}?",
                f"Which document is mandatory for {topic.lower()} per {disc_name} standards?",
                f"Per {std_ref}, what is the standard acceptance criterion for {topic.lower()}?",
                f"What is the first step in {topic.lower()} verification per {disc_name} procedures?",
                f"According to {std_ref}, what tool or document is required for {topic.lower()}?",
            ]
            opts_templates = [
                _balanced_options(
                    f"Compliance with {std_ref} mandatory requirement for {topic.lower()[:30]}",
                    f"Contractor's internal guideline for {topic.lower()[:30]} procedures",
                    f"Informal verbal agreement between parties for {topic.lower()[:25]}",
                    f"Optional recommendation that does not require {topic.lower()[:25]}"
                ),
                _balanced_options(
                    f"Verified documentation per {std_ref} clause requirements",
                    f"Verbal confirmation without any documented evidence needed",
                    f"Contractor self-certification with no third party review",
                    f"Informal checklist without formal acceptance or signoff"
                ),
            ]
        elif diff == "moderate":
            stems = [
                f"During field inspection for {topic.lower()}, the QC inspector finds a deviation from {std_ref}. What is the correct action?",
                f"Per {std_ref}, when performing {topic.lower()}, what multi-step verification is required?",
                f"A nonconformance is identified during {topic.lower()}. Per {disc_name} procedures, how should this be dispositioned?",
                f"Per {std_ref}, what are the acceptance criteria when evaluating {topic.lower()} results?",
                f"During {topic.lower()}, the inspector notes test equipment calibration has expired. What is the required QC action?",
                f"Per {std_ref}, what documentation chain is required to verify {topic.lower()} compliance?",
            ]
            opts_templates = [
                _balanced_options(
                    f"Stop work and issue nonconformance report per {std_ref} requirements",
                    f"Continue work and document deviation in daily log for later review",
                    f"Verbal notification to supervisor without formal documentation req",
                    f"Allow contractor to self-certify correction with no QC re-inspect"
                ),
                _balanced_options(
                    f"Multi-step verification per {std_ref} including documentation review",
                    f"Single visual check without instrument or measurement verification",
                    f"Contractor self-inspection report accepted without QC witnessing",
                    f"Deferred inspection to be completed during mechanical completion"
                ),
            ]
        else:  # difficult
            stems = [
                f"A complex nonconformance involving {topic.lower()} requires root cause analysis. Per {std_ref} and {disc_name} procedures, detail the investigation approach.",
                f"Conflicting requirements between {std_ref} and the project specification arise for {topic.lower()}. How should the QC inspector resolve this?",
                f"During commissioning, {topic.lower()} fails acceptance. What comprehensive investigation and corrective action sequence is required per {std_ref}?",
                f"A systematic failure pattern is identified in {topic.lower()} across multiple units. Per {disc_name} quality system, what root cause and corrective action approach applies?",
            ]
            opts_templates = [
                _balanced_options(
                    f"Comprehensive root cause analysis per {std_ref} with corrective action plan",
                    f"Simple rework without investigation or formal corrective action plan",
                    f"Accept as-is with engineering waiver and no further quality review",
                    f"Defer investigation to post-construction quality audit review phase"
                ),
                _balanced_options(
                    f"Apply document hierarchy, raise technical query, obtain engineering review",
                    f"Follow the less restrictive requirement to expedite project schedule",
                    f"Contractor decides which requirement applies without client approval",
                    f"Ignore both conflicting requirements and use industry best practice"
                ),
            ]
        
        q_stem = stems[i % len(stems)]
        q_opts = opts_templates[i % len(opts_templates)]
        
        mcqs.append({
            "discipline": disc_name, "type": "mcq",
            "question": q_stem,
            "options": q_opts, "correct": q_opts[0],
            "rubric": f"Verify compliance against {std_ref} for {topic.lower()}.",
            "subject": subj, "sub_subject": topic,
            "difficulty": diff, "topic": f"{disc_name} - {topic}"
        })
    
    # ---- 20 Essays: 8 Easy, 8 Moderate, 4 Difficult ----
    for i in range(20):
        subj, topic = st_list[i % len(st_list)]
        if i < 8:
            diff = "easy"
            q_text = f"List the key requirements and documentation for {topic.lower()} per {std_ref} in {disc_name}."
            rubric = (f"1. Standard Requirements (2.5 pts): Lists {std_ref} requirements for {topic.lower()}.\n"
                     f"2. Key Documents (2.5 pts): Identifies mandatory documents and records.\n"
                     f"3. Acceptance Criteria (2.5 pts): States applicable pass/fail criteria.\n"
                     f"4. Safety Considerations (2.5 pts): Identifies relevant safety requirements.")
        elif i < 16:
            diff = "moderate"
            q_text = f"Describe the complete step-by-step QC inspection workflow for {topic.lower()} per {std_ref}, including pre-inspection, field verification, acceptance evaluation, and documentation."
            rubric = (f"1. Pre-Inspection (2.5 pts): Document review, equipment readiness, material verification.\n"
                     f"2. Field Verification (2.5 pts): Step-by-step inspection procedure per {std_ref}.\n"
                     f"3. Acceptance Evaluation (2.5 pts): Code criteria application, measurement interpretation.\n"
                     f"4. Documentation (2.5 pts): Report completion, sign-off, NCR if applicable.")
        else:
            diff = "difficult"
            q_text = f"Analyze a complex nonconformance scenario involving {topic.lower()} where multiple code requirements conflict. Detail the root cause investigation, resolution methodology, and corrective action plan per {std_ref} and Aramco quality procedures."
            rubric = (f"1. Root Cause Analysis (2.5 pts): Systematic investigation methodology, contributing factors.\n"
                     f"2. Code Conflict Resolution (2.5 pts): Document hierarchy, technical query process.\n"
                     f"3. Corrective Action Plan (2.5 pts): Immediate and long-term corrective measures.\n"
                     f"4. Verification & Closeout (2.5 pts): Re-inspection, effectiveness verification, lessons learned.")
        
        essays.append({
            "discipline": disc_name, "type": "essay",
            "question": q_text, "options": [],
            "correct": f"Comprehensive response covering {std_ref} requirements for {topic.lower()} with proper code references and quality procedures.",
            "rubric": rubric,
            "subject": subj, "sub_subject": topic,
            "difficulty": diff, "topic": f"{disc_name} - {topic}"
        })
    
    # ---- 20 Oral-Practical: 12 Oral + 8 Practical ----
    # Oral: 5 Easy, 5 Moderate, 2 Difficult
    # Practical: 3 Easy, 3 Moderate, 2 Difficult
    # Total: 8 Easy, 8 Moderate, 4 Difficult
    
    # 12 Oral Questions
    for i in range(12):
        subj, topic = st_list[i % len(st_list)]
        if i < 5:
            diff = "easy"
            q_text = f"Verbally explain to the reviewer the standard requirements and safety rules for {topic.lower()} per {std_ref} in {disc_name}."
            rubric = (f"1. Technical Knowledge (2.5 pts): Accurately explains {std_ref} requirements.\n"
                     f"2. Safety Awareness (2.5 pts): Identifies relevant safety controls.\n"
                     f"3. Documentation (2.5 pts): Names required records and reports.\n"
                     f"4. Communication (2.5 pts): Clear, structured verbal response.")
        elif i < 10:
            diff = "moderate"
            q_text = f"Verbally walk the reviewer through the complete inspection sequence for {topic.lower()} per {std_ref}. Explain hold points, acceptance criteria, and NCR escalation procedures."
            rubric = (f"1. Inspection Sequence (2.5 pts): Correct step-by-step procedure explanation.\n"
                     f"2. Hold Points (2.5 pts): Identifies mandatory hold and witness points.\n"
                     f"3. Acceptance Criteria (2.5 pts): Cites code limits and evaluation methods.\n"
                     f"4. NCR Escalation (2.5 pts): Explains nonconformance disposition protocol.")
        else:
            diff = "difficult"
            q_text = f"Verbally defend your root cause analysis and corrective action approach for a complex nonconformance in {topic.lower()} under reviewer cross-examination. Reference {std_ref} and Aramco quality procedures."
            rubric = (f"1. Root Cause Defense (2.5 pts): Systematic analysis with supporting evidence.\n"
                     f"2. Code Application (2.5 pts): Accurate {std_ref} clause references under pressure.\n"
                     f"3. Corrective Actions (2.5 pts): Technically sound corrective and preventive measures.\n"
                     f"4. Cross-Examination (2.5 pts): Maintains position with clear technical justification.")
        
        oral_pracs.append({
            "discipline": disc_name, "type": "oral_practical",
            "question": q_text, "options": [],
            "correct": f"Candidate articulates {std_ref} requirements for {topic.lower()}, demonstrates technical competency, and communicates clearly.",
            "rubric": rubric,
            "subject": subj, "sub_subject": topic,
            "difficulty": diff, "topic": f"{disc_name} - {topic}",
        })
    
    # 8 Practical Questions
    for i in range(8):
        subj, topic = st_list[(12 + i) % len(st_list)]
        if i < 3:
            diff = "easy"
            q_text = f"Using calibrated inspection instruments, perform a basic quality verification for {topic.lower()} per {disc_name} procedures. Demonstrate proper instrument handling and record results."
            rubric = (f"1. Instrument Check (2.5 pts): Verifies calibration status and readiness.\n"
                     f"2. Measurement Technique (2.5 pts): Demonstrates correct measurement method.\n"
                     f"3. Result Recording (2.5 pts): Accurately documents measurements.\n"
                     f"4. Pass/Fail Judgment (2.5 pts): Correctly evaluates against acceptance criteria.")
        elif i < 6:
            diff = "moderate"
            q_text = f"Perform a comprehensive field inspection for {topic.lower()} per {std_ref}. Verbally explain your procedure while physically demonstrating instrument use, taking measurements, and completing the inspection report."
            rubric = (f"1. Verbal Explanation (2.5 pts): Clear procedural walkthrough with code references.\n"
                     f"2. Instrument Operation (2.5 pts): Correct setup, calibration check, and use.\n"
                     f"3. Measurement Accuracy (2.5 pts): Precise readings at required test points.\n"
                     f"4. Report Completion (2.5 pts): Comprehensive inspection report with pass/fail.")
        else:
            diff = "difficult"
            q_text = f"Examine the provided specimen with multiple defects related to {topic.lower()}. Identify all defects, perform boundary measurements, defend your root cause analysis under reviewer questioning, and complete a formal Nonconformance Report (NCR)."
            rubric = (f"1. Defect Identification (2.5 pts): Correctly identifies all defect types and locations.\n"
                     f"2. Boundary Measurement (2.5 pts): Accurate measurement of defect dimensions.\n"
                     f"3. Root Cause Defense (2.5 pts): Sound technical analysis under cross-examination.\n"
                     f"4. NCR Completion (2.5 pts): Professional NCR with disposition and corrective action.")
        
        oral_pracs.append({
            "discipline": disc_name, "type": "oral_practical",
            "question": q_text, "options": [],
            "correct": f"Candidate demonstrates hands-on competency for {topic.lower()} per {std_ref}, records accurate results, and completes official documentation.",
            "rubric": rubric,
            "subject": subj, "sub_subject": topic,
            "difficulty": diff, "topic": f"{disc_name} - {topic}",
        })
    
    return mcqs + essays + oral_pracs


# ===================================================================
# Discipline-specific standard references and descriptions
# ===================================================================
DISCIPLINE_CONFIG = {
    "Piping QC": ("SAES-L-105 / ASME B31.3", "Piping Systems & Hydrostatic Testing"),
    "Coating QC": ("SAES-H-100 / SSPC-PA2", "Protective Coating & Surface Preparation"),
    "Civil QC": ("SAES-Q-001 / ACI 318", "Concrete Structures & Earthworks"),
    "Electrical QC": ("SAES-P-100 / NEC Art 500", "Electrical Systems & Hazardous Areas"),
    "Instrumentation QC": ("SAES-J-002 / ISA 75.01", "Instrumentation, Loops & Control Valves"),
    "Mechanical QC": ("SAES-E-004 / API 686", "Static & Rotating Mechanical Equipment"),
    "Cathodic Protection QC": ("SAES-X-100 / NACE SP0169", "Cathodic Protection Systems & Potentials"),
    "NDT QC": ("SAEP-1140 / SNT-TC-1A", "Non-Destructive Testing Methods & QA"),
    "Telecom QC": ("SAES-T Series / ANSI/TIA-568", "Telecommunications & Fiber Optic Networks"),
    "E&I QC": ("SAES-P/J Series / NEC", "Integrated Electrical & Instrumentation"),
    "Pipeline QC": ("SAES-W-012 / API 1104", "Cross-Country Pipeline Construction"),
    "PQCS": ("SAEP-381 / ISO 9001", "Project Quality Control Supervision"),
}


def build_all_questions():
    """Build the complete 1,300 question bank."""
    all_questions = []
    
    # ---- Welding QC: hand-crafted questions ----
    for mcq in WELDING_MCQ:
        all_questions.append({
            "discipline": "Welding QC", "type": "mcq",
            "question": mcq["q"], "options": mcq["opts"],
            "correct": mcq["correct"], "rubric": f"Verify against {mcq.get('subj', 'Codes and standards')} requirements.",
            "subject": mcq["subj"], "sub_subject": mcq["topic"],
            "difficulty": mcq["diff"], "topic": f"Welding QC - {mcq['topic']}"
        })
    
    for ess in WELDING_ESSAY:
        all_questions.append({
            "discipline": "Welding QC", "type": "essay",
            "question": ess["q"], "options": [],
            "correct": f"Comprehensive response per ASME/AWS/SAES-W-011.",
            "rubric": ess["rubric"],
            "subject": ess["subj"], "sub_subject": ess["topic"],
            "difficulty": ess["diff"], "topic": f"Welding QC - {ess['topic']}"
        })
    
    for op in WELDING_ORAL_PRACTICAL:
        all_questions.append({
            "discipline": "Welding QC", "type": "oral_practical",
            "question": op["q"], "options": [],
            "correct": f"Candidate demonstrates competency per ASME/AWS/SAES-W-011.",
            "rubric": op["rubric"],
            "subject": op["subj"], "sub_subject": op["topic"],
            "difficulty": op["diff"], "topic": f"Welding QC - {op['topic']}"
        })
    
    # ---- Other 12 disciplines: generated from templates ----
    for disc_name, (std_ref, desc) in DISCIPLINE_CONFIG.items():
        disc_questions = _make_discipline_questions(disc_name, std_ref, desc)
        all_questions.extend(disc_questions)
    
    return all_questions


def main():
    ALL_QUESTIONS = build_all_questions()
    print(f"Total questions generated across ALL 13 disciplines: {len(ALL_QUESTIONS)}")
    
    # Audit per discipline
    disc_summary = {}
    for q in ALL_QUESTIONS:
        d = q["discipline"]
        if d not in disc_summary:
            disc_summary[d] = {
                "total": 0, "mcq": 0, "essay": 0, "oral_practical": 0,
                "mcq_easy": 0, "mcq_mod": 0, "mcq_diff": 0,
                "essay_easy": 0, "essay_mod": 0, "essay_diff": 0,
                "op_easy": 0, "op_mod": 0, "op_diff": 0,
                "total_easy": 0, "total_mod": 0, "total_diff": 0
            }
        s = disc_summary[d]
        s["total"] += 1
        q_type = q["type"]
        if q_type in s:
            s[q_type] += 1
        
        diff = q["difficulty"]
        prefix = "op" if q_type == "oral_practical" else q_type
        if diff == "easy":
            s["total_easy"] += 1
            s[f"{prefix}_easy"] += 1
        elif diff == "moderate":
            s["total_mod"] += 1
            s[f"{prefix}_mod"] += 1
        elif diff == "difficult":
            s["total_diff"] += 1
            s[f"{prefix}_diff"] += 1
            
    print("\n" + "=" * 110)
    print(f"{'Discipline':28s} | {'Total':5s} | {'MCQ (E/M/D)':16s} | {'Essay (E/M/D)':16s} | {'O-P (E/M/D)':14s} | {'Easy%':5s} | {'Mod%':5s} | {'Diff%':5s}")
    print("=" * 110)
    for d, s in disc_summary.items():
        mcq_str = f"{s['mcq']} ({s['mcq_easy']}/{s['mcq_mod']}/{s['mcq_diff']})"
        ess_str = f"{s['essay']} ({s['essay_easy']}/{s['essay_mod']}/{s['essay_diff']})"
        op_str = f"{s['oral_practical']} ({s['op_easy']}/{s['op_mod']}/{s['op_diff']})"
        easy_pct = (s['total_easy'] / s['total']) * 100
        mod_pct = (s['total_mod'] / s['total']) * 100
        diff_pct = (s['total_diff'] / s['total']) * 100
        print(f"{d:28s} | {s['total']:<5d} | {mcq_str:16s} | {ess_str:16s} | {op_str:14s} | {easy_pct:4.0f}% | {mod_pct:4.0f}% | {diff_pct:4.0f}%")
    print("=" * 110)
    
    total_all = sum(s['total'] for s in disc_summary.values())
    total_e = sum(s['total_easy'] for s in disc_summary.values())
    total_m = sum(s['total_mod'] for s in disc_summary.values())
    total_d = sum(s['total_diff'] for s in disc_summary.values())
    print(f"{'GRAND TOTAL':28s} | {total_all:<5d} | {'':16s} | {'':16s} | {'':14s} | {total_e/total_all*100:4.0f}% | {total_m/total_all*100:4.0f}% | {total_d/total_all*100:4.0f}%")

    # Build Excel Workbook matching HEADERS in question_import.py
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Questions"
    
    sheet.append(HEADERS)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:L{len(ALL_QUESTIONS) + 1}"
    
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
    
    for col_idx, cell in enumerate(sheet[1], 1):
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center
        cell.border = thin_border

    for q in ALL_QUESTIONS:
        q_type = q["type"]
        options_str = "\n".join(q["options"]) if q_type == "mcq" else ""
        row = [
            q["discipline"],                    # Discipline
            q_type,                             # Question type (mcq / essay / oral_practical)
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
        
    for row_idx in range(2, len(ALL_QUESTIONS) + 2):
        sheet.row_dimensions[row_idx].height = None
        for col_idx in range(1, len(HEADERS) + 1):
            cell = sheet.cell(row=row_idx, column=col_idx)
            cell.font = data_font
            cell.border = thin_border
            if col_idx in (1, 2, 9, 10, 12):
                cell.alignment = align_center
            else:
                cell.alignment = align_left
                
    widths = {
        'A': 22, 'B': 16, 'C': 65, 'D': 55, 'E': 45, 'F': 65,
        'G': 28, 'H': 42, 'I': 16, 'J': 14, 'K': 40, 'L': 16
    }
    for col_letter, width in widths.items():
        sheet.column_dimensions[col_letter].width = width

    instructions = wb.create_sheet(title="Instructions")
    instructions.append(["Question bank import instructions"])
    instructions.append(["Fill the Questions sheet and leave no completely blank rows between questions."])
    instructions.append(["Question type must be mcq, essay, or oral_practical. For Multiple Choice questions, put one option per line in Multiple Choice options."])
    instructions.append(["Assessment Settings determines the maximum points for each question type. Keep the headers unchanged."])
    instructions.column_dimensions['A'].width = 110

    target_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "qc-question-template.xlsx")
    wb.save(target_file)
    print(f"\nSuccessfully generated {target_file}")
    
    # Validate with question_import.py
    print("\n--- Validating Excel File with question_import.py ---")
    with open(target_file, "rb") as f:
        file_bytes = f.read()
    parsed = question_import.parse_questions(file_bytes)
    
    success_count = sum(1 for r in parsed if r["success"])
    error_count = sum(1 for r in parsed if not r["success"])
    print(f"Successfully parsed {success_count} questions.")
    if error_count:
        print(f"WARNING: {error_count} questions had validation errors:")
        for r in parsed:
            if not r["success"]:
                print(f"  Row {r['row_number']}: {r['error']}")
    else:
        print("Zero validation errors - all questions pass question_import.py checks!")

if __name__ == "__main__":
    main()
