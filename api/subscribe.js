// Vercel serverless function: adds a newsletter signup to Resend as a contact.
// Needs the RESEND_API_KEY environment variable. RESEND_SEGMENT_ID is optional.
// Endpoint and body follow Resend's current "create contact" docs: POST https://api.resend.com/contacts

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const ALLOWED_ORIGINS = ["https://eva-suggestions.vercel.app"];

module.exports = async (req, res) => {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "method_not_allowed" });
  }

  // Only accept requests that come from this site's own pages.
  const origin = req.headers.origin;
  if (origin && !ALLOWED_ORIGINS.includes(origin)) {
    return res.status(403).json({ error: "forbidden" });
  }

  const key = process.env.RESEND_API_KEY;
  if (!key) {
    return res.status(503).json({ error: "not_configured" });
  }

  let body = req.body;
  if (typeof body === "string") {
    try {
      body = JSON.parse(body);
    } catch (e) {
      body = {};
    }
  }
  body = body || {};

  // Hidden field that real visitors never fill in. Pretend success so bots learn nothing.
  if (body.website) {
    return res.status(200).json({ ok: true });
  }

  const email = String(body.email || "").trim().toLowerCase();
  if (email.length > 254 || !EMAIL_RE.test(email)) {
    return res.status(400).json({ error: "invalid_email" });
  }

  const payload = { email, unsubscribed: false };
  if (process.env.RESEND_SEGMENT_ID) {
    payload.segments = [{ id: process.env.RESEND_SEGMENT_ID }];
  }

  try {
    const r = await fetch("https://api.resend.com/contacts", {
      method: "POST",
      headers: {
        Authorization: "Bearer " + key,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    // An existing contact counts as success, so the form never reveals who is already on the list.
    if (r.ok || r.status === 409) {
      return res.status(200).json({ ok: true });
    }
    console.error("resend_contact_failed status=" + r.status);
    return res.status(502).json({ error: "upstream_error" });
  } catch (e) {
    console.error("resend_request_error");
    return res.status(502).json({ error: "upstream_error" });
  }
};
