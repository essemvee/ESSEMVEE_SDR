"use strict";

/*
============================================================
 ESSEMVEE AI SDR — Dashboard Controller
============================================================
*/

const API_BASE = "http://127.0.0.1:8000";

let currentProspects = [];

/* ============================================================
   HELPERS
============================================================ */

function $(selector) {
    return document.querySelector(selector);
}

function $all(selector) {
    return Array.from(document.querySelectorAll(selector));
}

function normalizeText(value) {
    return String(value || "")
        .replace(/\s+/g, " ")
        .trim()
        .toLowerCase();
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

/* ============================================================
   API
============================================================ */

async function apiRequest(path, options = {}) {
    const response = await fetch(API_BASE + path, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "API request failed");
    }

    return data;
}

/* ============================================================
   FINDERS
============================================================ */

function findButton(label) {
    return $all("button").find(button =>
        normalizeText(button.textContent).includes(
            normalizeText(label)
        )
    );
}

function findCardByLabel(label) {
    const wanted = normalizeText(label);

    for (const element of $all("*")) {
        if (normalizeText(element.textContent) !== wanted) {
            continue;
        }

        let parent = element.parentElement;

        for (let i = 0; i < 6 && parent; i++) {
            if (
                normalizeText(parent.innerText).includes(wanted)
            ) {
                return parent;
            }

            parent = parent.parentElement;
        }
    }

    return null;
}

/* ============================================================
   HEALTH
============================================================ */

async function checkApi() {
    try {
        await apiRequest("/health");
        console.log("API connected");
    } catch (error) {
        console.error("API failed", error);
    }
}

/* ============================================================
   DISCOVERY
============================================================ */

async function discoverProspects() {
    const inputs = $all("input");

    const query = inputs[0]?.value?.trim();
    const count = Number(
        inputs.find(i => i.type === "number")?.value || 5
    );

    if (!query) {
        alert("Enter a discovery query.");
        return;
    }

    try {
        const result = await apiRequest(
            "/api/discovery/search",
            {
                method: "POST",
                body: JSON.stringify({
                    query,
                    count
                })
            }
        );

        currentProspects = result.prospects || [];

        if (!currentProspects.length) {
            alert("No prospects found.");
            return;
        }

        await analyzeProspect(currentProspects[0]);

    } catch (error) {
        console.error(error);
        alert(error.message);
    }
}

/* ============================================================
   ANALYSIS
============================================================ */

async function analyzeProspect(prospect) {
    const company = prospect.company || {};
    const signal = prospect.signal || {};

    const result = await apiRequest(
        "/api/prospects/analyze",
        {
            method: "POST",
            body: JSON.stringify({
                company_name: company.company_name,
                website: company.website,
                country: company.country,
                industry: company.industry,
                description: company.description,
                signal: signal
            })
        }
    );

    console.log("Analysis result:", result);

    renderAnalysis(result);
}

/* ============================================================
   RENDER
============================================================ */

function renderAnalysis(result) {
    const scout = result.scout || result;

    setMetric("ICP Score", scout.icp_score);
    setMetric("Intent", scout.intent_score);
    setMetric("Opportunity", scout.opportunity_score);
    setMetric("Priority", scout.priority);

    renderDecisionMaker(
        result.contacts?.best_contact || {},
        result.contacts || {}
    );

    renderRecommendation(scout);
    renderOutreach(result.outreach || {});
    renderEvidence(result.evidence || {});
}

function setMetric(label, value) {
    const card = findCardByLabel(label);

    if (!card) return;

    const elements =
        card.querySelectorAll(
            ".metric-value,.score,.value,h1,h2,h3,h4,strong"
        );

    for (const element of elements) {
        const text = normalizeText(element.textContent);

        if (text !== normalizeText(label)) {
            element.textContent =
                value ?? "—";
            return;
        }
    }
}

/* ============================================================
   DECISION MAKER
============================================================ */

function renderDecisionMaker(contact, contacts) {
    const card =
        findCardByLabel("DECISION MAKER");

    if (!card) return;

    const label =
        card.querySelector(".card-label");

    const labelHtml =
        label
            ? label.outerHTML
            : '<div class="card-label">DECISION MAKER</div>';

    card.innerHTML = `
        ${labelHtml}

        <div class="intelligence-block">

            <h3>
                ${escapeHtml(contact.name || "Not Found")}
            </h3>

            <p>
                ${escapeHtml(contact.role || "—")}
            </p>

            <hr>

            <div>
                <strong>LinkedIn</strong>
                <br>
                ${contact.linkedin_url
                    ? `<a href="${escapeHtml(contact.linkedin_url)}" target="_blank">View Profile</a>`
                    : "Not Found"}
            </div>

            <br>

            <div>
                <strong>Email</strong>
                <br>
                ${escapeHtml(contact.email || "Not Found")}
            </div>

            <br>

            <div>
                <strong>Confidence</strong>
                <br>
                ${contact.contact_confidence ?? "—"}/100
            </div>

            <br>

            <div>
                <strong>Status</strong>
                <br>
                ${escapeHtml(contacts.contact_status || "—")}
            </div>

        </div>
    `;
}

/* ============================================================
   RECOMMENDATION
============================================================ */

function renderRecommendation(scout) {
    const card =
        findCardByLabel("ESSEMVEE RECOMMENDATION");

    if (!card) return;

    const label =
        card.querySelector(".card-label");

    const labelHtml =
        label
            ? label.outerHTML
            : '<div class="card-label">ESSEMVEE RECOMMENDATION</div>';

    card.innerHTML = `
        ${labelHtml}

        <div class="intelligence-block">

            <h3>
                ${escapeHtml(scout.recommended_service || "—")}
            </h3>

            <p>
                <strong>Likely problem</strong><br>
                ${escapeHtml(scout.likely_problem || "—")}
            </p>

            <p>
                <strong>Why now</strong><br>
                ${escapeHtml(scout.why_now || "—")}
            </p>

            <p>
                <strong>Recommended action</strong><br>
                ${escapeHtml(scout.recommended_action || "—")}
            </p>

        </div>
    `;
}

/* ============================================================
   OUTREACH
============================================================ */

function renderOutreach(outreach) {
    const card = findCardByLabel("OUTREACH");

    if (!card) return;

    card.innerHTML = `
        <div class="card-label">OUTREACH</div>

        <div class="intelligence-block">

            <p>
                <strong>LinkedIn connection</strong>
            </p>

            <div class="message-box">
                ${escapeHtml(outreach.linkedin_connection || "—")}
            </div>

            <p>
                <strong>Cold email</strong>
            </p>

            <div class="message-box">
                ${escapeHtml(outreach.cold_email || "—")}
            </div>

        </div>
    `;
}

/* ============================================================
   EVIDENCE
============================================================ */

function renderEvidence(evidence) {
    const card = findCardByLabel("EVIDENCE");

    if (!card) return;

    card.innerHTML = `
        <div class="card-label">EVIDENCE</div>

        <pre class="evidence-box">${escapeHtml(
            JSON.stringify(evidence, null, 2)
        )}</pre>
    `;
}

/* ============================================================
   START
============================================================ */

function wireDashboard() {
    const searchButton = findButton("Search");

    if (searchButton) {
        searchButton.addEventListener(
            "click",
            discoverProspects
        );
    }

    const apiButton = findButton("Check API");

    if (apiButton) {
        apiButton.addEventListener(
            "click",
            checkApi
        );
    }

    checkApi();
}

document.addEventListener(
    "DOMContentLoaded",
    wireDashboard
);