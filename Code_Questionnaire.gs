/**
 * SIM WARS 2026 — Pre-Event Questionnaire backend.
 *
 * Receives POST submissions from the Pre-Event Questionnaire page
 * (simwars-2026-questionnaire.html) and appends each one as a new row in a
 * dedicated "SIM WARS 2026 - Questionnaire Responses" Google Sheet.
 *
 * This is a SEPARATE Apps Script project/deployment from the team-intake
 * one (Code.gs) — the questionnaire has ~90 fields vs. intake's ~14, so
 * rather than mapping every single question to its own column, this script
 * breaks out a handful of key fields for quick scanning (team, email, role,
 * designation) plus one column with the complete response set as JSON, so
 * no answer is ever lost even as the questionnaire's questions change.
 *
 * ---- SETUP ----
 * 1. Create a new Google Sheet (e.g. "SIM WARS 2026 - Questionnaire
 *    Responses"). In row 1, add these headers:
 *      Timestamp | Team Number | Email | Professional Role | Designation | Full Responses (JSON)
 * 2. Extensions -> Apps Script. Delete the placeholder code and paste this
 *    whole file in.
 * 3. Replace SHEET_ID below with your new sheet's ID (from its URL).
 * 4. Deploy -> New deployment -> type "Web app".
 *      - Execute as: Me
 *      - Who has access: Anyone
 * 5. Copy the resulting Web App URL and paste it into
 *    simwars-2026-questionnaire.html as QUESTIONNAIRE_ENDPOINT (see the
 *    comment near the top of that file's <script> block).
 * 6. Re-deploy (New deployment, not "manage deployments" edit-in-place)
 *    any time you edit this script, or the live URL keeps running the old
 *    version.
 */

var SHEET_ID = 'PASTE_YOUR_QUESTIONNAIRE_SHEET_ID_HERE';

function doPost(e) {
  var sheet = SpreadsheetApp.openById(SHEET_ID).getSheets()[0];
  var p = e.parameter;

  sheet.appendRow([
    new Date(),
    p.teamNumber          || '',
    p.email                || '',
    p.professional_role    || '',
    p.designation           || '',
    p.responsesJson         || ''
  ]);

  return ContentService
    .createTextOutput(JSON.stringify({ status: 'ok' }))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Optional: lets you sanity-check the deployment by visiting the Web App
 * URL directly in a browser (GET request).
 */
function doGet(e) {
  return ContentService.createTextOutput('SIM WARS questionnaire endpoint is live.');
}
