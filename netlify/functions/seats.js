/* Live seat counts, straight from the office's own pipeline.

   GET /.netlify/functions/seats  ->  { cap: 8, taken: { "advanced:night:2026-09-14": 3, ... }, full: [keys], at: iso }

   Every open opportunity in the GHL "Enrollment" pipeline (any stage except
   Lost) holds one seat in the class its custom fields describe:
     Class Program     "Advanced Rigger" | "Signal Person" | "NCCER Assessments"
     Class Format      "Weekday Day Class" | "Weekday Night Class" | "3-Day Weekend Express" | "Two Fridays" | "Any Weekday"
     Class Start Date  date
   Website bookings fill those in through the Enrollment Router; phone bookings
   the office adds by hand count the moment the fields are filled. Moving a
   card to Lost frees the seat. Text is matched loosely (any spelling of
   "night", "weekend", "friday", "assess" works), so a typo doesn't hide a seat.

   Env (Netlify): GHL_PI_TOKEN (Private Integration, opportunities.readonly +
   locations/customFields.readonly), GHL_LOCATION_ID, GHL_PIPELINE_ID.
   Missing token = 200 with empty counts, so the site falls back to the
   static CLOSED/FULL lists in build.py and never breaks. */

const CAP = 8;
const API = "https://services.leadconnectorhq.com";
const VERSION = "2021-07-28";

const json = (status, body, maxAge) => ({
  statusCode: status,
  headers: {
    "Content-Type": "application/json",
    "Cache-Control": maxAge ? `public, max-age=${maxAge}, s-maxage=${maxAge}` : "no-store",
    "Access-Control-Allow-Origin": "*"
  },
  body: JSON.stringify(body)
});

function programId(s) {
  s = String(s || "").toLowerCase();
  if (s.includes("assess")) return "assessment";
  if (s.includes("signal")) return "signal";
  if (s.includes("rigger") || s.includes("advanced")) return "advanced";
  return "";
}
function formatId(s, pid) {
  s = String(s || "").toLowerCase();
  if (s.includes("night")) return "night";
  if (s.includes("weekend")) return "weekend";
  if (s.includes("friday")) return "friday";
  if (s.includes("assess") || s.includes("any weekday")) return "assess";
  if (s.includes("day")) return "day";
  // Blank format: the only sensible default per program.
  if (pid === "signal") return "friday";
  if (pid === "assessment") return "assess";
  return "";
}
function isoDate(v) {
  if (v == null || v === "") return "";
  if (typeof v === "number") return new Date(v).toISOString().slice(0, 10);
  const s = String(v).trim();
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (m) return `${m[1]}-${m[2]}-${m[3]}`;
  const d = new Date(s);
  return isNaN(d) ? "" : d.toISOString().slice(0, 10);
}

async function ghl(path, token) {
  const r = await fetch(API + path, { headers: { Authorization: `Bearer ${token}`, Version: VERSION, Accept: "application/json" } });
  if (!r.ok) throw new Error(`GHL ${path} -> ${r.status}`);
  return r.json();
}

exports.handler = async () => {
  const token = process.env.GHL_PI_TOKEN;
  const loc = process.env.GHL_LOCATION_ID;
  const pipe = process.env.GHL_PIPELINE_ID;
  if (!token || !loc || !pipe) return json(200, { cap: CAP, taken: {}, full: [], note: "seats not configured" }, 60);

  try {
    // Field ids for the three opportunity fields, matched by key so renaming the label in GHL can't break it.
    const cf = await ghl(`/locations/${loc}/customFields?model=opportunity`, token);
    const byKey = {};
    for (const f of cf.customFields || []) {
      const k = String(f.fieldKey || "").toLowerCase();
      if (k.endsWith("class_program")) byKey.program = f.id;
      if (k.endsWith("class_format")) byKey.format = f.id;
      if (k.endsWith("class_start_date")) byKey.date = f.id;
    }

    const taken = {};
    for (let page = 1; page <= 20; page++) {
      const q = `/opportunities/search?location_id=${loc}&pipeline_id=${pipe}&status=open&limit=100&page=${page}`;
      const data = await ghl(q, token);
      const list = data.opportunities || [];
      for (const o of list) {
        const stage = String(o.pipelineStageName || (o.pipelineStage && o.pipelineStage.name) || "").toLowerCase();
        if (stage === "lost") continue;
        const vals = {};
        for (const c of o.customFields || []) {
          // The search API returns typed keys (fieldValueString / fieldValueDate / fieldValueNumber ...); take whichever is set.
          let v = c.fieldValue != null && c.fieldValue !== "" ? c.fieldValue : c.value;
          if (v == null || v === "") for (const k of Object.keys(c)) if (k.startsWith("fieldValue") && c[k] != null && c[k] !== "") { v = c[k]; break; }
          if (c.id === byKey.program) vals.program = v;
          if (c.id === byKey.format) vals.format = v;
          if (c.id === byKey.date) vals.date = v;
        }
        const pid = programId(vals.program), fid = formatId(vals.format, pid), day = isoDate(vals.date);
        if (!pid || !fid || !day) continue;
        const key = `${pid}:${fid}:${day}`;
        taken[key] = (taken[key] || 0) + 1;
      }
      if (list.length < 100) break;
    }
    const full = Object.keys(taken).filter(k => taken[k] >= CAP);
    return json(200, { cap: CAP, taken, full, at: new Date().toISOString() }, 60);
  } catch (e) {
    console.error("seats", e.message);
    return json(200, { cap: CAP, taken: {}, full: [], error: e.message }, 30);
  }
};
