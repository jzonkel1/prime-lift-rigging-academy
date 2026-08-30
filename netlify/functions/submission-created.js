/* Netlify fires this on every verified form submission (event-triggered
   function, name is fixed by Netlify). It forwards the enrollment request to
   the GoHighLevel Inbound Webhook so the office gets the silent-mode
   notification (email + text) with every detail in it.

   Env var: GHL_WEBHOOK_URL  (Prime Lift sub-account > Automation >
            "Enrollment Router" workflow > Inbound Webhook trigger URL)
   Missing = no-op. Netlify's own email notification still fires either way,
   so nothing is lost while this is unset. */

exports.handler = async (event) => {
  const url = process.env.GHL_WEBHOOK_URL;
  if (!url) return { statusCode: 200, body: "GHL_WEBHOOK_URL not set; skipped" };

  let payload;
  try { payload = JSON.parse(event.body).payload; } catch { return { statusCode: 400, body: "bad body" }; }
  const FORMS = { "enrollment-request": "Website Enrollment Form", "contact": "Website Contact Form" };
  if (!payload || !FORMS[payload.form_name]) return { statusCode: 200, body: "ignored" };

  const d = payload.data || {};
  const body = {
    source: FORMS[payload.form_name],
    form_name: payload.form_name,
    submitted_at: payload.created_at,
    first_name: d.first_name || "",
    last_name: d.last_name || "",
    phone: d.phone || "",
    email: d.email || "",
    program: d.program || "",
    format: d.format || "",
    start_date: d.start_date || "",
    payment_method: d.payment_method || "",
    amount_due_today: d.amount_due_today || "",
    payer: d.payer || "",
    notes: [d.notes, d.note].filter(Boolean).join(" | "),
    sms_consent_nonmarketing: d.sms_consent_nonmarketing || "no",
    sms_consent_marketing: d.sms_consent_marketing || "no",
    page: d.page || ""
  };

  const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  return { statusCode: 200, body: `forwarded to GHL: ${r.status}` };
};
