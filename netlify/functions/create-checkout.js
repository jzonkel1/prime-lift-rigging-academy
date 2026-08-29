/* Creates a Stripe Checkout Session for a course deposit (or a full
   assessment fee) and returns its URL. No SDK: Stripe's REST API takes
   form-encoded bodies, so a plain fetch keeps this dependency-free.

   Env vars (Netlify site settings > Environment variables):
     STRIPE_SECRET_KEY   sk_live_... from the CLIENT's Stripe account.
                         Missing = 503, and the page falls back to the
                         enrollment-request form so nothing is lost.
     SITE_URL            optional; defaults to Netlify's own URL env.

   Klarna and Afterpay must be turned on in the client's Stripe dashboard
   (Settings > Payment methods) or Stripe rejects the session. Both pay
   the FULL course price, never the $200 deposit; the page already
   computes that in depositFor() and sends amount_due_today. */

const CATALOG = {
  advanced:   { name: "Advanced Rigger",           price: 1000, deposit: 200 },
  signal:     { name: "Signal Person",             price: 1000, deposit: 200 },
  assessment: { name: "NCCER Craft Assessment",    price: 150,  deposit: 150 }
};

const json = (status, body) => ({
  statusCode: status,
  headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  body: JSON.stringify(body)
});

exports.handler = async (event) => {
  if (event.httpMethod !== "POST") return json(405, { error: "POST only" });

  const key = process.env.STRIPE_SECRET_KEY;
  if (!key) return json(503, { error: "payments_not_configured" });

  let p;
  try { p = JSON.parse(event.body || "{}"); } catch { return json(400, { error: "bad json" }); }

  const item = CATALOG[p.program_id];
  if (!item) return json(400, { error: "unknown program" });

  const method = String(p.payment_method || "card");
  const bnpl = method === "klarna" || method === "afterpay";
  // Never trust the browser's amount: recompute server-side from the catalog.
  const amount = bnpl ? item.price : item.deposit;
  const label = amount === item.price ? item.name : `${item.name} deposit`;

  const site = (process.env.SITE_URL || process.env.URL || "").replace(/\/$/, "");
  const success = `${site}/?booked=1&program=${encodeURIComponent(item.name)}&date=${encodeURIComponent(p.start_date_label || "")}`;
  const cancel  = `${site}/?canceled=1#schedule`;

  const body = new URLSearchParams();
  body.append("mode", "payment");
  body.append("success_url", success);
  body.append("cancel_url", cancel);
  body.append("line_items[0][quantity]", "1");
  body.append("line_items[0][price_data][currency]", "usd");
  body.append("line_items[0][price_data][unit_amount]", String(amount * 100));
  body.append("line_items[0][price_data][product_data][name]", label);
  body.append("line_items[0][price_data][product_data][description]",
    `${p.format || ""} starting ${p.start_date_label || p.start_date || ""}`.trim());
  if (bnpl) {
    body.append("payment_method_types[0]", method === "klarna" ? "klarna" : "afterpay_clearpay");
  } else {
    body.append("payment_method_types[0]", "card");
  }
  if (p.email) body.append("customer_email", p.email);
  body.append("phone_number_collection[enabled]", "true");
  body.append("payment_intent_data[description]", `${label} for ${p.first_name || ""} ${p.last_name || ""}`.trim());
  body.append("payment_intent_data[receipt_email]", p.email || "");

  const meta = {
    first_name: p.first_name, last_name: p.last_name, phone: p.phone, email: p.email,
    program: item.name, format: p.format, class_times: p.class_times,
    start_date: p.start_date, payment_method: method,
    course_total: String(item.price), paid_today: String(amount), balance_due: String(item.price - amount)
  };
  for (const [k, v] of Object.entries(meta)) {
    if (v != null && v !== "") {
      body.append(`metadata[${k}]`, String(v).slice(0, 500));
      body.append(`payment_intent_data[metadata][${k}]`, String(v).slice(0, 500));
    }
  }

  const r = await fetch("https://api.stripe.com/v1/checkout/sessions", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString()
  });
  const data = await r.json();
  if (!r.ok) {
    console.error("stripe", data.error);
    return json(502, { error: (data.error && data.error.message) || "stripe error" });
  }
  return json(200, { url: data.url });
};
