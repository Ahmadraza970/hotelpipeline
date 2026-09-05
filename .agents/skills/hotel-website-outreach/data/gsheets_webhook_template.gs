/*
  Google Apps Script web app template for receiving hotel leads.

  DEPLOYMENT STEPS:
  1. Create a new Google Sheet → rename tab to "Hotel Leads"
  2. Extensions → Apps Script
  3. Paste ALL of this code (replace existing content)
  4. Replace "YOUR_SHEET_ID" with your Sheet ID (from URL)
  5. Deploy → New Deployment → Select type: "Web app"
  6. Execute as: "Me" | Who has access: "Anyone"
  7. Copy the Web app URL
  8. Save URL in data/gsheets_config.json:
     { "gsheet_webhook_url": "https://script.google.com/macros/s/YOUR_KEY/exec", ... }

  Duplicates are skipped by hotel_name + city combination.
*/

var SHEET_ID = "1wt74LQbaVKT4um2Auv92lJDWF0lKj7_JejnrRBi26cY";  // Your Sheet ID

function doPost(e) {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sheet = ss.getSheetByName("Hotel Leads") || ss.getActiveSheet();

  try {
    var data = JSON.parse(e.postData.contents);

    // Create header row if sheet is empty
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(["ID", "Hotel Name", "City", "Phone", "Email", "Website", "Status", "Date", "Audit Notes"]);
    }

    var results = [];

    if (Array.isArray(data)) {
      var existing = [];
      if (sheet.getLastRow() > 1) {
        existing = sheet.getRange(2, 2, sheet.getLastRow() - 1, 2).getValues();
      }
      for (var i = 0; i < data.length; i++) {
        var row = data[i];
        var isDup = false;
        for (var j = 0; j < existing.length; j++) {
          if (existing[j][0] == row.hotel_name && existing[j][1] == row.city) {
            isDup = true;
            break;
          }
        }
        if (!isDup) {
          sheet.appendRow([
            row.id || "",
            row.hotel_name || "",
            row.city || "",
            row.phone || "",
            row.email || "",
            row.website || "",
            row.status || "identified",
            row.date_discovered || "",
            row.audit_notes || ""
          ]);
          results.push({"id": row.id, "status": "added"});
        } else {
          results.push({"id": row.id, "status": "skipped_duplicate"});
        }
      }
    } else {
      sheet.appendRow([
        data.id || "",
        data.hotel_name || "",
        data.city || "",
        data.phone || "",
        data.email || "",
        data.website || "",
        data.status || "identified",
        data.date_discovered || "",
        data.audit_notes || ""
      ]);
      results.push({"status": "added"});
    }

    return ContentService
      .createTextOutput(JSON.stringify({status: "success", processed: results.length, results: results}))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({status: "error", message: err.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService
    .createTextOutput("Hotel Leads Webhook is active.")
    .setMimeType(ContentService.MimeType.TEXT);
}
