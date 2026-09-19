# Change Plan: Candidate Weakness Identification

## Goal

Add a deterministic, evidence-based weakness summary for each graded candidate assessment. Questions will use a two-level subject and sub-subject taxonomy. Reviewers should be able to see broad subject weaknesses and the specific sub-subjects that need development. Candidate-facing reports should present concise development areas without exposing protected question-bank content.

## Current State

- Questions are classified by discipline and question type only.
- Each submitted answer stores a question snapshot and an awarded score.
- Results show percentages for multiple choice, essay, oral, and practical sections.
- Reviewer feedback is stored at the assessment level.
- Candidate result PDFs do not identify specific subject weaknesses.

Question type alone is not a sufficient weakness category. A low multiple-choice score does not explain whether the candidate struggled with inspection planning, material traceability, acceptance criteria, documentation, or another technical topic.

## Taxonomy Model

Every question will have four classification levels:

1. Discipline: The existing QC discipline, such as Welding QC or Civil QC.
2. Subject: A broad technical domain within the discipline.
3. Sub-subject: A specific assessable topic within the subject.
4. Question type: Multiple choice, essay, oral, or practical.
5. Topic group: A content-owner-approved link between questions that assess the same technical knowledge through different response formats.

Example:

- Discipline: Welding QC
- Subject: Codes and standards
- Sub-subject: WPS and PQR essential variables
- Question type: Multiple choice

Each normalized sub-subject must map to one subject within a discipline. The same sub-subject name may be used under another discipline only when that assignment is intentional.

## Product Decisions

- Add `subject` and `sub_subject` classifications to every question.
- Calculate performance at both taxonomy levels.
- Use the sub-subject result as the primary actionable weakness.
- Include the parent subject result to provide context.
- Generate weakness conclusions only after an assessment is fully graded.
- Support explicitly marked non-scored questions that collect responses without affecting grades or weakness conclusions.
- Begin every oral test with dedicated non-scored questions that establish a communication baseline before technical oral scoring starts.
- Instruct candidates to answer clearly, briefly, and directly, emphasizing the concrete actions they would take.
- Classify every question as easy, moderate, or difficult and use configured bracket quotas during scored-question selection.
- Select essay, oral, and practical questions from the same approved topic groups represented by the selected MCQs.
- Do not use generative AI or infer categories from free-text answers.
- Show no more than the three lowest sub-subjects below the development threshold.
- Do not expose question text, correct answers, or rubrics in candidate-facing summaries.
- Include the applicable confidentiality agreement notice in every candidate result PDF and result email without requesting another acceptance.
- Calculate summaries when read instead of storing a second copy that could become stale.
- Require all users to protect question confidentiality and prohibit discussion or sharing of assessment questions outside authorized assessment activities.
- Require Candidates and Reviewers to accept the confidentiality agreement only on their first successful login before accessing protected application pages.

## Weakness Rules

For every subject and sub-subject represented in an assessment:

1. Sum the awarded points from all answers in the category.
2. Sum the possible points from each stored question snapshot.
3. Calculate `percentage = awarded points / possible points * 100`.
4. Assign one of these statuses:
   - Below 50 percent: Critical development area
   - From 50 percent to below 70 percent: Development area
   - At least 70 percent: Demonstrated strength
5. Mark a category as `Limited evidence` when it contains fewer than two questions.
6. Calculate a subject rollup from every answer assigned to that subject.
7. Rank sub-subject weaknesses by percentage ascending, possible points descending, subject, then sub-subject.
8. Return the first three sub-subjects below 70 percent and include each parent-subject percentage.

An ungraded assessment must return `Pending Review` and no weakness conclusion. An assessment with no sub-subject below 70 percent should state that no scored technical weakness was identified.

## Data Model Changes

Update `database.py` initialization and migrations:

- Add `questions.subject TEXT NOT NULL DEFAULT 'General'`.
- Add `questions.sub_subject TEXT NOT NULL DEFAULT 'General'`.
- Add `questions.is_scored BOOLEAN NOT NULL DEFAULT TRUE`.
- Add `questions.difficulty TEXT NOT NULL DEFAULT 'moderate'` with a database constraint permitting only `easy`, `moderate`, or `difficult`.
- Add `questions.topic_group TEXT NOT NULL DEFAULT 'General'` to link related MCQ, essay, oral, and practical questions.
- Add `questions.delivery_stage TEXT NOT NULL DEFAULT 'standard'` with permitted values `standard` and `oral_opening`.
- Enforce that `oral_opening` questions have question type `oral` and `is_scored` set to false.
- Include all taxonomy, topic-group, scoring-status, difficulty, and delivery-stage fields in new question inserts and validation.
- Preserve subject, sub-subject, topic group, scoring status, difficulty, and delivery stage inside the answer snapshot at submission time.
- Enforce that each normalized sub-subject maps to one subject within a discipline.
- Keep historical snapshots unchanged. Legacy answers without either field should use `General` and be labeled as limited-detail results.
- Add an index on active questions by discipline, subject, and sub-subject if query measurements justify it.
- Add `assessment_settings.non_scored_count INTEGER NOT NULL DEFAULT 0` for each question type.
- Add easy, moderate, and difficult scored-question counts for each question type. Require their sum to equal the configured scored-question count.
- Add validation that every configured essay, oral, and practical slot can be filled from topic groups containing an eligible selected MCQ.
- Add `assessment_settings.oral_opening_count INTEGER NOT NULL DEFAULT 2` and require enough active oral-opening questions before an oral test can begin.
- Add a `confidentiality_agreements` table containing the agreement version, exact text, text fingerprint, effective date, and active status.
- Add a `confidentiality_acceptances` table containing one immutable record per user with the role at acceptance, agreement version, text fingerprint, acceptance time, and first-login session reference. Enforce a unique user identifier.
- Add `submissions.confidentiality_acceptance_id` so a candidate submission can reference the applicable login acceptance.

Do not automatically guess categories from question text in production. Existing questions should initially receive `General` for both levels, followed by a controlled content review to assign accurate categories.

## Question Management Changes

Update `question_import.py` and the Question Bank page in `app.py`:

- Add `Subject` and `Sub-subject` columns to the Excel template and question export.
- Continue accepting the current six-column workbook format for backward compatibility.
- Require both fields for newly created or newly imported questions using the new format.
- Add linked subject and sub-subject fields to the manual question form.
- Display both values in question summaries.
- Add subject and sub-subject filters to the question browser.
- Preserve both values during export and re-import.
- Validate that a sub-subject is assigned to the expected parent subject within its discipline.
- Add an Admin-only taxonomy management view for consistent category creation and renaming.
- Add a `Scored question` control to manual creation, editing, Excel import, and export.
- Display a visible `Non-scored` badge in question-bank browsing and assessment review.
- Add a required `Difficulty` field to manual creation, editing, Excel import, and export.
- Add a required `Topic group` field to manual creation, editing, Excel import, and export.
- Show linked question-type coverage for each topic group in the Question Bank.
- Add a `Delivery stage` control for non-scored oral questions.
- Display an `Oral opening` badge and allow Admin users to filter these questions.
- Display difficulty to authorized Admin and Reviewer users and add a difficulty filter to the question browser.

Suggested initial subjects:

- Codes and standards
- Inspection planning
- Materials and traceability
- Installation and workmanship
- Testing and verification
- Nonconformance and corrective action
- Documentation and turnover
- Safety and field execution

Sub-subjects should identify the specific assessable topic. Examples include `WPS and PQR essential variables` under `Codes and standards`, `Material test certificate traceability` under `Materials and traceability`, and `Punch-list closure evidence` under `Documentation and turnover`.

Discipline owners may add a more specific subject or sub-subject when needed. Normalize whitespace and capitalization to prevent duplicate category names.

## Candidate Response Instructions

Add this instruction to the scheduling email, pre-assessment screen, and the beginning of the essay, oral, and practical sections:

`Answer clearly, briefly, and directly. Focus on the concrete actions you would take, the applicable criteria or evidence you would check, and how you would verify and document the result.`

Supporting guidance:

- Encourage a practical sequence such as action, check, evidence, and closure.
- Explain that a concise answer must still include essential technical, safety, quality, and documentation steps.
- Do not reward unnecessary length, repetition, or jargon.
- Do not penalize a concise response when it fully satisfies the approved rubric.
- Grade technical accuracy and completeness against the rubric, not writing style, accent, or response length alone.
- Repeat a shortened reminder beside essay response fields and in the reviewer-led oral and practical instructions.
- Keep the wording advisory rather than imposing an arbitrary word limit.
- Ensure the instruction does not conflict with the non-scored oral-opening communication purpose.
## Cross-Format Topic Alignment

The assessment should verify knowledge of the same technical topics through complementary question formats.

- Treat the selected MCQs as the anchor topic set for an assessment.
- Select essay, oral, and practical questions only from topic groups represented by at least one selected scored MCQ.
- Keep every topic group inside one discipline, subject, and sub-subject combination.
- Require content owners to confirm that linked questions test the same knowledge objective.
- Make linked questions complementary rather than verbatim duplicates.
- Use MCQs for recognition or application, essays for explanation and reasoning, oral questions for probing understanding, and practical questions for demonstrated execution.
- Do not let later questions disclose the correct answer to an unanswered scored MCQ.
- Lock the MCQ phase before showing linked essay questions. Oral and practical prompts remain reviewer-controlled.
- Prefer coverage across several selected MCQ topic groups instead of drawing every extended-response question from one topic.
- Allow more than one candidate question per topic group when assessment settings require depth, but avoid duplicate prompts.
- If there are not enough eligible linked questions for the configured counts and difficulty brackets, block assessment start and show an Admin-facing readiness error.
- Do not silently select unrelated essay, oral, or practical questions as fallback content.
- Keep non-scored supplementary questions linked when practical, but do not let them satisfy scored linked-question requirements.
- Store the topic group in the answer snapshot for historical audit and reviewer context.

Suggested selection sequence:

1. Select scored MCQs using discipline, difficulty, and configured count rules.
2. Collect the distinct topic groups represented by those MCQs.
3. Build eligible essay, oral, and practical pools from those topic groups.
4. Select the configured counts while balancing topic coverage and difficulty.
5. Validate unique question identifiers and exact counts before starting the timer.
6. Persist the full selected question set in session state and submit only that immutable set.

The reviewer view should group linked responses by topic group so the reviewer can compare recognition, explanation, oral understanding, and practical execution for the same knowledge objective.
## Non-Scored Question Behavior

Non-scored questions collect supplementary evidence without changing assessment results.

- Allow any supported question type to be marked as non-scored.
- Keep `max_points` unchanged for validation and display, but ignore it in all score and maximum-point calculations when `is_scored` is false.
- Store submitted responses and the complete question snapshot for auditability.
- Do not allow non-scored questions to satisfy configured scored-question counts.
- Select them using the separate non-scored count configured for each question type.
- Present candidate-entered non-scored questions in a clearly labeled `Supplementary Questions` section after the scored timed section.
- Do not reduce the time available for scored questions because supplementary questions were added.
- Mark supplementary questions clearly before the candidate answers them.
- For oral and practical items, let the reviewer record the observed response without assigning points.
- Exclude non-scored questions from category percentages, overall percentage, pass or fail decisions, and weakness analysis.
- Keep non-scored responses visible only to authorized Admin and Reviewer users unless a future policy explicitly permits candidate disclosure.
- Default every existing question and legacy import row to scored so current behavior remains unchanged.
## Oral Communication Opening

Begin every oral test with non-scored questions designed to establish how the candidate communicates before technical oral questions are assessed.

- Deliver the oral-opening questions before any scored oral question.
- Clearly tell the candidate that these opening questions are non-scored and are intended to understand their communication approach.
- Use professional, job-relevant prompts that invite a short explanation, such as describing the candidate's inspection experience, explaining how they prepare for a site inspection, or summarizing how they communicate a quality concern.
- Do not ask about protected or irrelevant personal matters, including religion, health, family status, ethnicity, political views, or other sensitive characteristics.
- Let the reviewer record the observed response and concise communication notes.
- Use non-numeric observation fields for clarity, listening and comprehension, organization of explanation, and professional interaction.
- Use observation values such as `Observed`, `Not observed`, and `Insufficient evidence` rather than points or ratings.
- Do not add the observations to awarded points, maximum points, pass or fail decisions, technical weakness analysis, or hidden hiring scores.
- Do not let oral-opening questions satisfy scored oral-question counts.
- Exempt oral-opening questions from MCQ topic-group alignment because their purpose is communication familiarization rather than technical verification.
- Keep the candidate's communication notes restricted to authorized Admin and Reviewer users.
- Label the notes as contextual observations, not a diagnosis or validated language-proficiency assessment.
- Require a separate approved scored criterion if communication proficiency later becomes part of a formal job requirement.

Suggested delivery order:

1. Reviewer explains the non-scored purpose.
2. Reviewer asks the configured oral-opening questions.
3. Reviewer records the candidate responses and communication observations.
4. The application marks the opening stage complete.
5. The scored, MCQ-linked technical oral questions begin.
## Difficulty Bracketing

Every question, including a non-scored question, must use one of these internal brackets:

- Easy: Direct recall, recognition, or a routine single-step application of an approved requirement.
- Moderate: Interpretation or application across multiple steps in a typical field scenario.
- Difficult: Synthesis, judgment, troubleshooting, or application in a non-routine scenario with plausible competing considerations.

Difficulty rules:

- Treat difficulty as an internal assessment-design attribute. Do not show the bracket to candidates before or during the assessment.
- Do not determine difficulty from question length, option length, question type, or vocabulary alone.
- Require a qualified discipline owner to approve each bracket using the question, expected answer, rubric, and required reasoning.
- Keep awarded points and weakness calculations unchanged. Difficulty must not create an unapproved score multiplier.
- Select scored questions using the configured easy, moderate, and difficult counts for each question type.
- Do not silently substitute another bracket when the selected discipline lacks enough active questions. Show an Admin-facing configuration error instead.
- Randomize question selection within each discipline, question type, scoring status, and difficulty bracket.
- Store the difficulty in the answer snapshot so historical assessments retain their original design.
- Show the achieved assessment mix to Admin and Reviewer users for quality review.
- Permit later bracket recalibration from aggregate item-performance evidence only after a documented minimum sample size and content-owner approval.
- Never use a candidate's personal data or protected attributes to assign or alter question difficulty.

Legacy questions should default to `moderate` for technical compatibility, but the maintained template and active bank must undergo content-owner review before balanced selection is enabled.
## Existing Question Categorization

Categorize every maintained question in `qc-question-template.xlsx` and the corresponding database question bank:

1. Extract the question discipline, prompt, options, correct answer, and rubric.
2. Propose a subject and sub-subject from an approved discipline taxonomy.
3. Group questions with similar proposed categories for content-owner review.
4. Have a qualified discipline owner approve or correct every assignment.
5. Check that each sub-subject maps consistently to one subject within its discipline.
6. Write approved categories back to the workbook.
7. Validate that all question rows have both fields and remain importable.
8. Export or migrate the reviewed assignments into the active database question bank.

Automatic proposals may accelerate the review, but they must not become production labels without content-owner approval.
The same review must assign an easy, moderate, or difficult bracket to every question and record the approval in the content-review checklist.
The review must also assign a topic group and confirm that each production group has sufficient MCQ anchors plus the required essay, oral, and practical coverage.

## Calculation Service

Add focused functions in `database.py` or a new `weakness_analysis.py` module:

- `answer_topic_summary(answers)` groups stored answer snapshots and scores by subject and sub-subject.
- `candidate_weaknesses(answers, status)` applies thresholds, evidence labels, and ranking.
- Filter out snapshots where `is_scored` is false before calculating totals or weaknesses.
- Report difficulty coverage as context, but do not weight topic percentages by the difficulty label.
- Preserve topic-group detail so reviewers can compare performance across linked question formats without changing the approved scoring formula.
- Keep these functions pure where possible so they can be tested without a database.
- Treat MCQ possible points as the stored snapshot value, subject to the same scoring rules used at submission.
- Cap essay, oral, and practical possible points consistently with grading.
- Ignore malformed legacy rows safely and surface a reviewer-visible data-quality note.

Each sub-subject result should contain:

- Subject
- Sub-subject
- Awarded points
- Possible points
- Percentage
- Parent-subject percentage
- Question count
- Status
- Evidence label
- Contributing question types

## Reviewer Experience

Update the graded assessment section in `app.py`:

- Add a `Candidate Development Areas` expander below results by question type.
- Show subject rollups first.
- Show up to three weakness cards with subject, sub-subject, both percentages, points, evidence level, and contributing question types.
- Allow reviewers to inspect the related scored answers within the existing questionnaire.
- Keep detailed question-level evidence restricted to Admin and Reviewer roles.
- Show non-scored responses in a separate reviewer-only `Supplementary Responses` section without score controls.
- Place oral-opening responses first in that section and provide structured, non-numeric communication observation fields.
- Remind reviewers that concise, technically complete answers must not lose points solely because of their length or communication style.
- Show the selected easy, moderate, and difficult question counts to Admin and Reviewer users as assessment-design metadata.
- Group MCQ, essay, oral, and practical evidence by topic group in the reviewer view.
- Explain that the summary supports professional judgment and does not replace reviewer evaluation.

## Candidate Result PDF

Update `candidate_result_pdf` in `app.py`:

- Add a `Development Areas` section for graded assessments.
- Show the subject, sub-subject, percentage, and a neutral development statement.
- Include the limited-evidence warning when applicable.
- Do not include correct answers, rubrics, internal question identifiers, or protected question text.
- Do not include supplementary responses or non-scored questions in the candidate result PDF.
- Keep reviewer feedback as the place for personalized recommendations.
- Add a final `Confidentiality Agreement` section to the result PDF.
- State that the result, assessment information, remembered questions, and answers are confidential and must not be forwarded, published, copied, photographed, recorded, or shared with unauthorized persons.
- Show the agreement version and acceptance date from the candidate's saved first-login acceptance record.
- Explain that the PDF notice confirms the existing agreement and does not require another acceptance.
- Keep the confidentiality section in the PDF when the attachment is downloaded or separated from the email.
- For a legacy result without a linked acceptance record, include the confidentiality notice without claiming a recorded version or acceptance date.

Suggested PDF wording:

`Confidentiality Agreement: This result and all related assessment information are confidential and remain subject to the confidentiality agreement accepted at first login. Do not forward, publish, copy, record, photograph, or share this result or any assessment questions or answers with anyone who is not authorized to handle the assessment.`
## Candidate Result Email

Update the candidate result email in `email_service.py` to include a confidentiality agreement reminder.

- State that the email, attached result, and related assessment information are confidential.
- State that the candidate must not forward, publish, copy, photograph, record, or share the result or any remembered assessment questions and answers with unauthorized persons.
- Permit discussion with the assessment administrator or another person formally authorized to handle the assessment result.
- Reference the confidentiality agreement version accepted by the candidate at first login.
- Explain that the email is a reminder of the existing agreement and does not require a second acceptance.
- Do not include question text, correct answers, answer options, scoring rubrics, reviewer-only notes, or non-scored communication observations.
- Keep the wording concise and place it before the email closing.
- Add a received-in-error instruction asking an unintended recipient to notify the sender and delete the email and attachment.
- Continue attaching only the candidate-safe result PDF.

Suggested wording:

`Confidentiality reminder: This email, the attached result, and all assessment information are confidential and remain subject to the confidentiality agreement you accepted when you first signed in. Do not forward, publish, copy, record, photograph, or share this result or any assessment questions or answers with anyone who is not authorized to handle the assessment.`
## Results Export

Update `result_export.py`:

- Add `Primary Development Areas` to the results workbook.
- Format each area as `Subject > Sub-subject: percentage` on a separate line.
- Add `Weakness Evidence Note` when any listed area has limited evidence or legacy classification.
- Add a `Non-scored Questions Answered` count for audit purposes without exporting response text in the general results log.
- Confirm that spreadsheet cells remain safe from formula execution.

## Question Confidentiality

Assessment questions, answer options, expected answers, rubrics, and candidate responses are confidential assessment material.

- Add this instruction to the scheduling email and the pre-assessment screen: `Assessment questions and answers are confidential. Do not discuss, copy, photograph, record, or share them with anyone outside the assessment.`
- Require Candidate and Reviewer users to accept the agreement after credential validation and before protected application access.
- Record the first-login acceptance in the application and link each candidate submission to the candidate's saved acceptance record.
- Apply the same rule to Candidates, Reviewers, and Admin users.
- Permit question discussion only when required for authorized assessment delivery, grading, moderation, question maintenance, or formal quality review.
- Allow candidates to discuss scheduling, technical access, and the assessment process as long as no question or answer content is disclosed.
- Do not include question content in general result exports, candidate emails, or candidate-facing weakness summaries.
- Restrict question-bank exports to authorized staff and log the exporting user and time if an audit log is introduced.
- State the rule clearly without claiming the application can prevent screenshots or off-platform conversations.

### First Login Agreement and Acceptance Record

After valid credentials are entered for the first time, Candidate and Reviewer users must pass a confidentiality gate before the application creates an authorized working session. Later logins use the saved acceptance record and do not show the agreement again.

- Show the current agreement in a readable dialog or dedicated page.
- Require an unchecked acknowledgment box and an explicit `Accept and continue` action.
- Do not preselect the acknowledgment or treat credential submission as acceptance.
- If the user declines or closes the agreement, sign the user out and deny access to assessment, question-bank, review, and result pages.
- Require acceptance only when the Candidate or Reviewer account has no existing confidentiality acceptance record.
- Record one immutable acceptance event for the user's first successful login and prevent duplicate records.
- Store the user identifier, role at acceptance, agreement version, exact-text fingerprint, UTC acceptance time, and a non-secret login-session reference.
- Do not store the password, temporary password, authentication token, or other secret in the acceptance record.
- After the first acceptance is stored, authorize later logins by checking the saved record for that user. Do not rely only on session state.
- Link each candidate submission to the candidate's saved first-login acceptance record.
- Provide an Admin-only `Confidentiality Acceptance Register` showing user, role, version, and acceptance time with date, user, and role filters.
- Make acceptance records append-only in normal application use and include them in the documented records-retention policy.
- When agreement wording changes, publish a new version for new accounts and preserve the wording accepted by existing users. Do not require existing users to accept again unless a future approved policy explicitly changes the first-login-only rule.

The agreement should state that assessment questions, options, expected answers, rubrics, candidate responses, screenshots, recordings, exports, and reviewer notes are confidential. Candidates and Reviewers must not discuss, copy, photograph, record, forward, publish, or use this material outside authorized assessment delivery, grading, moderation, maintenance, or formal quality review. Suspected exposure must be reported to the assessment administrator.

## Security and Fairness Controls

- Apply the same assessment authorization used by `answer_details` before returning question-level evidence.
- Candidate-facing output must not disclose the reusable question bank.
- Use only scored evidence from the selected assessment.
- Never use non-scored responses as an undisclosed factor in hiring recommendations, grading, or weakness labels.
- Verify that the Candidate or Reviewer has a stored first-login confidentiality acceptance before allowing protected assessment or review activity.
- Enforce the confidentiality gate before Candidate or Reviewer navigation becomes available only when no saved acceptance record exists.
- Do not compare a candidate with demographic groups or use protected personal attributes.
- Display question count and evidence quality so small samples are not presented as strong conclusions.
- Keep thresholds explicit and configurable in one location.

## Test Plan

Add unit tests for:

- Correct grouping and weighted percentage calculations.
- Mixed question types within one sub-subject.
- Correct subject rollups across multiple sub-subjects.
- Critical, development, and strength thresholds at boundary values.
- Ranking and the three-area limit.
- Limited-evidence labeling.
- Pending-review behavior.
- Legacy snapshots without subject or sub-subject.
- Zero possible points and malformed snapshots.
- Rejection of a sub-subject assigned to the wrong parent subject.
- Import and export round trips with subject and sub-subject values.
- Backward compatibility with the current workbook format.
- Candidate PDF output without protected question content.
- Results export columns and formula-safe cells.
- Difficulty validation accepting only easy, moderate, and difficult.
- Stratified random selection meeting the configured bracket counts.
- Clear failure when a discipline lacks enough active questions in a required bracket.
- Difficulty preserved in answer snapshots, imports, and exports.
- Difficulty excluded from automatic point multipliers and weakness weighting.
- Candidate views not revealing difficulty labels.
- Essay, oral, and practical selections restricted to topic groups present in the selected MCQs.
- No unrelated fallback when linked pools are insufficient.
- Balanced coverage across multiple selected MCQ topic groups.
- Linked questions sharing discipline, subject, and sub-subject.
- Unique prompts and identifiers across the selected assessment.
- MCQ phase locked before related essay content is displayed.
- Topic group preserved in imports, exports, and answer snapshots.
- Admin and Reviewer access to detailed evidence.
- Candidate denial for protected question-level details.
- Non-scored questions excluded from awarded points, maximum points, percentages, pass or fail, and weaknesses.
- Non-scored questions excluded from configured scored-question quotas.
- Oral-opening questions always delivered before scored oral questions.
- Oral-opening questions exempt from MCQ topic-group matching.
- Oral-opening observations stored without numeric scores or pass or fail effects.
- Protected and irrelevant personal prompts rejected by validation and content review.
- Candidate shown a clear non-scored communication-purpose notice.
- Candidate response instruction shown in the scheduling email, pre-assessment screen, and essay, oral, and practical sections.
- Concise but technically complete answers graded against the rubric without a length penalty.
- Reviewer guidance focused on technical accuracy, concrete actions, evidence, verification, and documentation.
- Separate selection counts for scored and non-scored items.
- Supplementary responses persisted without reviewer score controls.
- Existing questions and old workbook rows defaulting to scored.
- Candidate result PDFs omitting supplementary responses.
- Candidate result PDF containing the confidentiality agreement notice, accepted version, and acceptance date.
- Legacy result PDF containing the notice without an unsupported acceptance claim.
- PDF confidentiality wording preserved when the result is downloaded independently of the email.
- Candidate result email containing the confidentiality reminder and accepted agreement version.
- Candidate result email excluding question content, reviewer-only notes, and non-scored communication observations.
- Result email requiring no second confidentiality acceptance.
- Candidate and Reviewer access blocked until the login confidentiality agreement is accepted.
- Acceptance required only on the first successful Candidate or Reviewer login.
- Declining or closing the agreement signs the user out.
- One immutable acceptance record stored per user with role, version, text fingerprint, UTC time, and non-secret first-login session reference.
- Candidate submission linked to the candidate's saved first-login acceptance record.
- Admin-only acceptance-register filters and authorization.
- Agreement version updates preserve historical wording without prompting existing users again.
- Confidentiality instruction present in scheduling email and pre-assessment screen.
- Acceptance record and agreement version linked to the candidate submission.

Add an application test that grades a candidate, opens the assessment review, verifies the development-area summary, and generates the updated PDF.

## Delivery Sequence

1. Define and approve the subject, sub-subject, topic-group, and difficulty criteria for each discipline.
2. Add the schema migration and question validation.
3. Add non-scored question flags, selection settings, and scoring exclusions.
4. Add the oral-opening stage, communication observation fields, and sequencing rules.
5. Add difficulty fields, bracket quotas, and stratified selection.
6. Add topic-group fields and MCQ-anchored cross-format selection.
7. Add the candidate response instructions to email and assessment sections.
8. Add first-login Candidate and Reviewer agreements, blocking access controls, acceptance records, and the Admin audit view.
9. Extend question creation, import, export, filtering, and snapshots.
10. Categorize, link, stage, and difficulty-bracket every maintained template question through content-owner review.
11. Implement and unit-test the pure weakness calculation.
12. Add the reviewer summary, linked-topic grouping, oral communication observations, supplementary-response section, and question-level evidence links.
13. Add the candidate-safe PDF summary and embedded confidentiality agreement notice.
14. Add the confidentiality agreement reminder to the candidate result email.
15. Extend the results workbook export.
16. Migrate approved categories, topic groups, delivery stages, and difficulty brackets to active database questions.
17. Run the full test suite and manually verify candidate instructions, result-email confidentiality wording, oral-opening order, linked-topic selection, balanced difficulty, and one strong, one mixed, and one weak candidate result with supplementary questions present.

## Acceptance Criteria

- Every new question has a valid subject and sub-subject pair.
- Every question is explicitly treated as scored or non-scored, with scored as the backward-compatible default.
- Every oral test begins with the configured number of approved non-scored oral-opening questions.
- Every question has an approved easy, moderate, or difficult bracket.
- Every production question has an approved topic group within its discipline, subject, and sub-subject.
- Every maintained template question has been reviewed and categorized.
- Existing six-column Excel workbooks remain importable.
- New exports preserve subject and sub-subject values.
- Imports, exports, and answer snapshots preserve difficulty.
- Imports, exports, and answer snapshots preserve topic groups.
- A graded assessment shows subject rollups and up to three evidence-based sub-subject development areas.
- Percentages reconcile exactly with stored awarded and possible points.
- Low-sample conclusions are visibly marked as limited evidence.
- Pending assessments do not display weakness conclusions.
- Non-scored questions never affect scores, thresholds, results, or weakness conclusions.
- Non-scored responses remain available to authorized reviewers in a separate section.
- Oral-opening questions appear before scored oral questions and are clearly described as non-scored.
- Communication observations remain non-numeric and do not affect technical results or weakness conclusions.
- Oral-opening prompts avoid protected and irrelevant personal topics.
- Candidate instructions request clear, brief, direct answers centered on concrete actions.
- The instruction appears before the assessment and at the relevant essay, oral, and practical sections.
- Concise answers receive full credit when they satisfy the technical rubric.
- Reviewers do not score verbosity, writing style, or accent unless an explicitly approved job criterion requires it.
- Scored assessments meet their configured easy, moderate, and difficult counts.
- Every selected essay, oral, and practical question is linked to a topic group represented by a selected scored MCQ.
- Insufficient linked-question pools block assessment start with a clear readiness message.
- Linked questions test the same knowledge objective without duplicating prompts or revealing MCQ answers.
- Difficulty does not independently alter points, pass or fail rules, or weakness percentages.
- Candidate views do not reveal internal difficulty labels.
- Candidates and Reviewers cannot access protected pages on their first login until they accept the confidentiality agreement.
- The first successful Candidate or Reviewer login creates one immutable acceptance record.
- Later logins proceed without another agreement prompt when the saved acceptance record is present.
- Acceptance records identify the agreement version and exact-text fingerprint used at that time.
- Candidate submissions reference the applicable login acceptance.
- Declining the agreement ends the first-login attempt without protected access.
- Admin users can review the acceptance register but cannot alter historical records.
- Candidate and staff instructions prohibit discussing or sharing questions outside authorized assessment activities.
- Candidate PDFs contain useful development areas without exposing question-bank content.
- Candidate result PDFs include the applicable first-login confidentiality agreement notice, version, and acceptance date.
- Legacy PDFs include the notice without claiming an acceptance record that does not exist.
- The PDF notice does not require a second acceptance.
- Candidate result emails include the applicable first-login confidentiality agreement reminder.
- The result email does not request another acceptance and contains no protected question-bank or reviewer-only content.
- Result exports include the summarized development areas.
- Historical assessments continue to load safely.
- All automated tests pass.