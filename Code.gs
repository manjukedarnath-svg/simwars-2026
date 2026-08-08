/**
 * SIM WARS 2026 — Team Intake backend.
 *
 * Receives POST submissions from the "Enter SIM WARS" form on the landing
 * page and appends each one as a new row in the "SIM WARS 2026 - Team
 * Intake and Draw" Google Sheet.
 *
 * Setup: see TEAM_INTAKE_SETUP.md in the same folder.
 */

var SHEET_ID = '1EjSctw8v54t5KrVNiw0nSB4SuGQficgUrhA-OBtS9Po';

function doPost(e) {
  var sheet = SpreadsheetApp.openById(SHEET_ID).getSheets()[0];
  var p = e.parameter;

  sheet.appendRow([
    '(assign after intake closes)',   // Team Draw Number — filled in manually once intake closes
    p.teamName    || '',
    p.m1name      || '',
    p.m1desig     || '',
    p.m2name      || '',
    p.m2desig     || '',
    p.m3name      || '',
    p.m3desig     || '',
    p.m4name      || '',
    p.m4desig     || '',
    p.leaderName  || '',
    p.leaderPhone || '',
    p.leaderEmail || '',
    p.introVideo  || '',
    new Date()
  ]);

  return ContentService
    .createTextOutput(JSON.stringify({ status: 'ok' }))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Optional: lets you sanity-check the deployment by visiting the Web App
 * URL directly in a browser (GET request) — should return "SIM WARS intake endpoint is live."
 */
function doGet(e) {
  return ContentService.createTextOutput('SIM WARS intake endpoint is live.');
}
