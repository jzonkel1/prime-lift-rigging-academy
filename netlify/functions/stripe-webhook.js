/* Stripe -> GHL: tells the system a deposit actually landed.

   The booking is recorded BEFORE the student is handed to Stripe (see
   book/index.html), so the pipeline card and the seat exist even if he never
   pays. That leaves the other half open: nothing knew when he DID pay, so the
   card sat in New Request and the confirmation still told him the office would
   call to collect money he had already paid. This closes it.

   Stripe fires here on checkout.session.completed (card) and on
   async_payment_succeeded (Klarna / Afterpay settle after the redirect). We
   verify the signature ourselves, then hand the details to a GHL Inbound
   Webhook, which is the same pattern submission-created.js uses: GHL owns the
   stage move and the messaging, this function just reports the fact.

   Env vars (Netlify site settings > Environment variables):
     STRIPE_WEBHOOK_SECRET    whsec_... from the Stripe endpoint's signing secret
     GHL_PAYMENT_WEBHOOK_URL  Inbound Webhook trigger of the "Payment Received"
                              workflow in the Prime Lift sub-account
   Either missing = 200 with a no-op, so a half-configured deploy never makes
   Stripe retry forever. */

const crypto = require("crypto");

/* Stripe signs `${timestamp}.${rawBody}`; the header carries t= and one or more
   v1= signatures. Compare in constant time and reject anything older than the
   tolerance so a captured payload can't be replayed. */
const TOLERANCE_SECONDS = 300;

function verify(rawBody, header, secret) {
  if (!header) return false;
  const parts = Object.fromEntries(
    header.split(",").map(kv => kv.split("=", 2)).filter(a => a.length === 2)
  );
  const ts = parts.t;
  if (!ts) return false;
  if (Math.abs(Math.floor(Date.now() / 1000) - Number(ts)) > TOLERANCE_SECONDS) return false;

  const expected = crypto.createHmac("sha256", secret).update(`${ts}.${rawBody}`).digest("hex");
  const expectedBuf = Buffer.from(expected, "utf8");
  return header
    .split(",")
    .map(kv => kv.split("=", 2))
    .filter(a => a[0].trim() === "v1")
    .some(a => {
      const got = Buffer.from(a[1].trim(), "utf8");
      return got.length === expectedBuf.length && crypto.timingSafeEqual(got, expectedBuf);
    });
}

/* GHL date fields parse MM-DD-YYYY; the site puts the ISO date in metadata. */
const toMdy = iso =>
  /^\d{4}-\d{2}-\d{2}$/.test(iso || "") ? `${iso.slice(5, 7)}-${iso.slice(8, 10)}-${iso.slice(0, 4)}` : "";

const HANDLED = new Set(["checkout.session.completed", "checkout.session.async_payment_succeeded"]);

exports.handler = async (event) => {
  const secret = process.env.STRIPE_WEBHOOK_SECRET;
  const url = process.env.GHL_PAYMENT_WEBHOOK_URL;
  if (!secret || !url) return { statusCode: 200, body: "stripe-webhook not configured; skipped" };

  const raw = event.isBase64Encoded
    ? Buffer.from(event.body || "", "base64").toString("utf8")
    : (event.body || "");

  const sig = event.headers["stripe-signature"] || event.headers["Stripe-Signature"];
  if (!verify(raw, sig, secret)) return { statusCode: 400, body: "bad signature" };

  let evt;
  try { evt = JSON.parse(raw); } catch { return { statusCode: 400, body: "bad json" }; }
  if (!HANDLED.has(evt.type)) return { statusCode: 200, body: `ignored ${evt.type}` };

  const s = evt.data && evt.data.object ? evt.data.object : {};
  /* Klarna and Afterpay can land here still unpaid; only a paid session counts. */
  if (s.payment_status && s.payment_status !== "paid") {
    return { statusCode: 200, body: `ignored payment_status ${s.payment_status}` };
  }

  const m = s.metadata || {};
  const paid = (s.amount_total != null ? s.amount_total / 100 : Number(m.paid_today || 0));
  const body = {
    source: "Stripe Payment",
    event_type: evt.type,
    session_id: s.id || "",
    payment_status: s.payment_status || "",
    first_name: m.first_name || "",
    last_name: m.last_name || "",
    phone: m.phone || (s.customer_details && s.customer_details.phone) || "",
    email: m.email || (s.customer_details && s.customer_details.email) || s.customer_email || "",
    program: m.program || "",
    format: m.format || "",
    class_times: m.class_times || "",
    start_date: m.start_date || "",                 // YYYY-MM-DD
    start_mdy: toMdy(m.start_date),                 // MM-DD-YYYY for GHL date fields
    payment_method: m.payment_method || "",
    amount_paid: String(paid),
    course_total: m.course_total || "",
    balance_due: m.balance_due || "",
    sms_consent_nonmarketing: m.sms_consent_nonmarketing || "no",
    sms_consent_marketing: m.sms_consent_marketing || "no",
    payer: m.payer || "",
    notes: m.notes || ""
  };

  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  return { statusCode: 200, body: `forwarded to GHL: ${r.status}` };
};
