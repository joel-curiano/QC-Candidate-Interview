# QC Candidate Interview Portal

Streamlit assessment app backed by persistent Supabase PostgreSQL storage. Candidate, Reviewer, and Admin accounts use the portal's existing login system; Supabase Auth is not required. Only Admin and Reviewer users can create Candidate accounts.

## 1. Create a free Supabase database

1. Create a project at https://supabase.com/dashboard under a Free organization. Save its **database password**.
2. Open the project's **SQL Editor**, paste [supabase/schema.sql](supabase/schema.sql), and run it once. This creates the private `qc_portal` schema and tables. **“Success. No rows returned” means the setup succeeded**: this script creates tables rather than returning query results. It does not modify existing tables in `public`.
3. Open **Connect**, choose **Session pooler**, and copy its PostgreSQL URI. Use the exact host shown by Supabase and port **5432**; do not guess the region/host. The pooler supports IPv4, including hosts where the direct IPv6 database connection is unavailable.
4. Replace the URI password placeholder with your database password, URL-encoding special characters (for example, `@` becomes `%40`). This is a database connection string, not the project HTTPS URL or an anon/publishable API key.

Connection details: https://supabase.com/docs/guides/database/connecting-to-postgres

## 2. Configure and run in VS Code (Windows)

Requires Python 3.10+ and VS Code. Open the repository folder using **File > Open Folder**, then select **Terminal > New Terminal**. Use a PowerShell terminal in the project folder containing `app.py` and `requirements.txt`.

Create the virtual environment if `.venv` does not already exist:

```powershell
python -m venv .venv
```

Install the dependencies:

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Create the local secrets file only if it does not already exist, so an existing connection is preserved:

```powershell
if (-not (Test-Path -LiteralPath .streamlit/secrets.toml)) {
    Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml
}
```

Open `.streamlit/secrets.toml` in VS Code and replace the placeholders with your copied Supabase URI:

```toml
SUPABASE_DB_URL = "postgresql://postgres.PROJECT_REF:ENCODED_PASSWORD@POOLER_HOST:5432/postgres"
```

Alternatively set `SUPABASE_DB_URL` as an environment variable; it takes precedence over Streamlit Secrets. No `.env` file loader is used. Never commit the real connection string. `.streamlit/secrets.toml` is ignored by Git.

Start the app:

```powershell
.\.venv\Scripts\python -m streamlit run app.py
```

Open http://localhost:8501 and create the initial administrator locally before exposing the app publicly. This administrator is stored in Supabase and will also work in the deployed app when it uses the same database. There are no default passwords. Accounts require passwords of at least 6 characters, stored as salted PBKDF2-SHA256 hashes with 600,000 iterations. Staff account forms can generate a strong 12-character password. Candidate account creation does not request a password; a temporary password is generated when the schedule invitation is sent. After signing in, any user can open **Change password** in the sidebar; the current password is required and a successful change signs the user out.

Keep the terminal running while using the app. Press **Ctrl+C** to stop it. Start it again with the same `streamlit run` command; do not use `python app.py` or VS Code's **Run Python File** button to launch the UI. Virtual environment activation is optional because these commands use its Python executable directly.

For subsequent runs, open the project terminal and run:

```powershell
.\.venv\Scripts\python -m streamlit run app.py
```

The app seeds sample questions when the question bank is empty. It also adds Civil QC MCQ and essay questions to existing databases when that discipline is missing, without duplicating or reactivating archived questions. Candidates complete a randomized session of 20 MCQ, 5 Essay, 5 Oral, and 5 Practicum questions; the selected discipline must have at least those active questions. The MCQ answer pool is shuffled for each session. Candidate details are captured with each submission. Admin and Reviewer users can assign or revise Candidate test dates and send a meaningful invitation containing the schedule, discipline, assessment link, username, and a newly generated temporary password. New Reviewer accounts receive an email containing the portal link, role, username, initial password, and password-change instructions. Configure `APP_URL`, `SMTP_HOST`, `SMTP_PORT`, and `SMTP_FROM`; optionally configure `SMTP_USERNAME` and `SMTP_PASSWORD`. Invitations use SMTP with STARTTLS and state clearly that candidate login is accepted only on the assigned test date. Practicum, Oral Test, and Practical Test questions are supported in the question bank, Excel import, candidate assessment, and reviewer grading flow. Startup applies safe additive migrations for the question type, candidate submission fields, email, and schedule. Missing configuration or connection/schema failures show a setup message rather than database credentials.

To generate the expanded Excel question bank, run:

```powershell
.\.venv\Scripts\python scripts/generate_aramco_question_template.py
```

This writes `qc-question-template.xlsx` with 2,000 original prompts: 80 MCQ, 40 essay, 40 oral, and 40 practicum questions for each of Civil, Electrical, E&I, Instrumentation, Mechanical, NDT, Piping, Welding, Pipeline QC, and PQCS. The workbook keeps the seven-column importer format. Questions use public Saudi Aramco standard identifiers as topic anchors and include a reminder to verify each item against the controlled current revision and project quality plan. They are original assessment prompts, not copied standard text.

## Access from a phone on the same network

After creating the administrator, start the server with:

```powershell
.\.venv\Scripts\python -m streamlit run app.py --server.address 0.0.0.0
```

Run `ipconfig` in another terminal and find the IPv4 address of your active network adapter. On a phone connected to the same network, open `http://YOUR-COMPUTER-IP:8501`. Allow inbound TCP port 8501 through Windows Firewall for your trusted private network if needed. The app uses responsive controls and a collapsible navigation sidebar.

## 3. Deploy to Streamlit Community Cloud

1. Commit and push `app.py`, `database.py`, `seed_questions.json`, `requirements.txt`, `.streamlit/config.toml`, and the setup files to GitHub.
2. At https://share.streamlit.io/, create an app from that repository/branch with main file `app.py`.
3. In **Advanced settings > Secrets**, paste the same `SUPABASE_DB_URL` TOML setting. For an existing app, update **Settings > Secrets**, then reboot if necessary.
4. Deploy and sign in with the administrator you created locally.

All accounts, questions, submissions, and grades now reside in Supabase, so losing the Streamlit container's local files does not erase them. Multiple app instances using the same connection string see the same data. Unsent forms and sign-in sessions are still held in Streamlit memory and can be lost on refresh/restart.

Free plan limits currently include 500 MB database storage, and low-activity projects may pause after a week. Resume a paused project in Supabase before using the app again. Maintain backups of real interview records; free plans do not include automatic backups. See https://supabase.com/pricing and https://supabase.com/docs/guides/platform/free-project-pausing for current terms.

## Publish code changes to GitHub

In VS Code, open **Source Control** (`Ctrl+Shift+G`), review the changed files and deletions, stage the files to publish, enter a commit message, and select **Commit**, then **Push** or **Sync Changes**. Refresh GitHub and select the same branch to see the updated files.

Commit the secrets **example**, but never the real `.streamlit/secrets.toml` file. Local files must be committed and pushed to the branch used by Community Cloud before that deployment can use the changes. Supabase credentials are configured separately in the deployed app's Secrets settings.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `Success. No rows returned` in the SQL Editor | Expected after running the schema script. Continue with the connection settings. |
| `.venv\\Scripts\\python` is not found | Open the terminal at the repository root and run `python -m venv .venv`. |
| Missing `streamlit` or `psycopg` module | Install `requirements.txt` using the same `.venv` Python executable used to run the app. |
| App asks for `SUPABASE_DB_URL` | Set the exact key in local `.streamlit/secrets.toml`, or in Community Cloud Secrets for the deployed app. |
| Database operation failed | Confirm that the Supabase project is active, the schema script ran, and the Session pooler URI uses the exact supplied host, port 5432, and correctly encoded database password. |
| Updated secrets seem to have no effect locally | An existing `SUPABASE_DB_URL` environment variable takes precedence over the secrets file. Update it or remove it, then restart the app. |
| Browser cannot open the local app | Keep the terminal running and use the URL and port printed by Streamlit. |
| Civil QC does not appear | Restart the updated app against the intended database. Missing Civil QC questions are added automatically; archived Civil QC questions must be restored by an Admin in the question bank. |
| Some tests are skipped | PostgreSQL integration tests require `TEST_DATABASE_URL`; see Tests below. |

## Roles and grading

| Role | Access |
| --- | --- |
| Candidate | Sign in on the assigned date, choose a discipline, answer the randomized assessment, view own results and feedback |
| Reviewer | Create and schedule Candidate accounts, send invitations, add questions/disciplines, review submissions, score essays/oral/practical tests, finalize grades, export results CSV |
| Admin | Reviewer access, create accounts, add questions/disciplines, archive/restore questions |

Starter disciplines: Welding, NDT, Piping, Civil, Coating, Electrical, Instrumentation, E&I, Mechanical, Communications, Pipeline QC, and PQCS. Coating QC, Communications QC, E&I QC, and Mechanical QC are available immediately in discipline selectors; add their questions through the Question bank or Excel import before scheduling assessments.

Multiple Choice questions are worth exactly 1 point and receive 1 point or zero. Reviewers award essay, oral, practical, and practicum points within the question maximum. Final percentage is `(Multiple Choice + reviewer-scored points) / total possible points * 100`; 70% passes. Pending reviewer-scored submissions have no final result. Question snapshots preserve historical grading. Final grades are immutable, repeated form tokens are idempotent, and concurrent reviewers cannot overwrite a finalized grade.

## Database access model

`database.py` uses Psycopg directly from the trusted Streamlit server, with TLS required, bounded connection/query/lock timeouts, and prepared statements disabled for pooler compatibility. Each operation commits on success and rolls back on failure. Initial setup, duplicate submissions, and grading use PostgreSQL transaction/row locks.

Tables live in the private `qc_portal` schema with RLS enabled and no client policies. Do not add this schema to Supabase's exposed Data API schemas. Use the server-only database owner connection from the Connect dialog; it can access the tables despite RLS. Candidate/reviewer/admin restrictions are enforced by the Python service, not Supabase Auth policies. Keep the connection password private. A publishable/anon key cannot replace it.

## Tests

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pytest -q
```

Configuration and error-handling tests run without a database. Database and full Streamlit integration tests require a **disposable PostgreSQL database**:

```powershell
$env:TEST_DATABASE_URL = 'postgresql://postgres:TEST_PASSWORD@localhost:5432/qc_test'
.\.venv\Scripts\python -m pytest -q
```

Integration tests create and drop only a random `qc_test_...` schema for each test. Never use a production connection for tests. When `TEST_DATABASE_URL` is absent these tests are explicitly skipped. The GitHub Actions workflow provisions PostgreSQL and runs the full suite on pushes and pull requests.

## Files

- `app.py`: Streamlit screens and startup configuration feedback.
- `database.py`: PostgreSQL access, authentication, and grading rules.
- `question_import.py`: Excel question-bank parsing and template generation.
- `result_export.py`: Formatted CTA Record Log Excel export.
- `supabase/schema.sql`: One-time PostgreSQL schema setup.
- `.streamlit/secrets.toml.example`: Placeholder connection configuration.
- `seed_questions.json`: Original technical sample question bank.
- `scripts/generate_aramco_question_template.py`: Reproducibly generates the populated 2,000-row question workbook for 10 disciplines.
- `qc-question-template.xlsx`: Generated Excel question bank ready for Admin import.
- `tests/`, `.github/workflows/tests.yml`: Unit and real PostgreSQL integration checks.
