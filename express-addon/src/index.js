import addOnUISdk from "https://new.express.adobe.com/static/add-on-sdk/sdk.js";
import { errorMessage, parseLink, titleFrom } from "./link.js";

const form = document.getElementById("import-form");
const input = document.getElementById("link");
const button = document.getElementById("import");
const status = document.getElementById("status");

function show(message, tone = "info") {
  status.textContent = message;
  status.dataset.tone = tone;
}

async function importFromRedraft(raw) {
  const url = parseLink(raw);
  show("Exporting from Redraft. This takes a few seconds.");
  const response = await fetch(url, { credentials: "omit" });
  if (!response.ok) throw new Error(await errorMessage(response));

  const pdf = await response.blob();
  const title = titleFrom(response.headers.get("content-disposition"));
  await addOnUISdk.app.document.importPdf(pdf, { title, sourceMimeType: "application/pdf" });
  show(`Imported "${title}". It opens as editable pages in Express.`, "success");
}

addOnUISdk.ready.then(() => {
  button.disabled = false;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    button.disabled = true;
    try {
      await importFromRedraft(input.value);
      input.value = "";
    } catch (error) {
      show(error.message, "error");
    } finally {
      button.disabled = false;
    }
  });
});
