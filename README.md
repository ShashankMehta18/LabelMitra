# LabelMitra

**AI-Assisted Legal Metrology Compliance**

An explainable, evidence-linked inspection assistant for packaged-product labels.

> "AI helps us read the label. Rules help us decide what it means."

Built by **Team Neural Nexus, IIT Patna**.

---

## Overview

Verifying that a packaged product's label meets Legal Metrology requirements is currently a manual, inconsistent process. LabelMitra is designed as a first-level inspection and documentation assistant that turns a photo of a label into a structured, explainable compliance check, without treating an AI model as the legal decision-maker.

**LabelMitra is not a substitute for a certified Legal Metrology Officer.** It is intended to support and speed up first-level review, with every finding traceable back to the evidence that produced it.

## The Problem

Manual label verification struggles with:

- **Time**: inspectors must manually read a large number of declarations.
- **Scale**: wide product variety makes consistent checking difficult.
- **Traceability**: reports and inspection history can become disconnected from each other.
- **Evidence**: a finding needs a clear, auditable link back to what was actually visible on the label.

## How It Works

The intended end-to-end workflow:

```
Label Image → PreProcessing → OCR → AI → Information Extraction → Rule Engine → PASS / FAIL / REVIEW → Report
```

At the backend/service level, the scan pipeline is structured as:

```
File validation → OCR → AI-assisted extraction (using OCR output and the original image) → Deterministic rules → Scoring / status → Database persistence → API response
```

## Architecture: AI Reads, Rules Decide

LabelMitra's core design principle is a strict separation of concerns between interpretation and decision-making:

**AI / OCR layer**
- OCR reads visible text from the label.
- The AI layer, using the Grok API, receives both the OCR output and the original label image together to assist with understanding and extracting the required label information.
- It is used particularly for ambiguous wording or unclear cases that plain OCR text alone doesn't resolve.
- It returns structured data along with uncertainty; it does not invent unclear values.

**Rule engine**
- Maps extracted fields to applicable Legal Metrology rules.
- Performs deterministic compliance checks.
- Is responsible for the actual compliance decision, producing explainable PASS / FAIL / REVIEW outcomes.
- Can be updated (new or changed rules) without retraining the AI component.

**AI assists interpretation. The Rule Engine owns the compliance decision.** The AI layer never makes the final legal or compliance determination itself.

## What LabelMitra Checks (MVP Scope)

The current scope focuses on practical, declaration-level checks:

- Product / commodity identity
- Manufacturer / packer / importer details
- Net quantity / relevant declaration
- Maximum Retail Price (MRP) information
- Applicable date information
- Consumer-care contact details
- Readability of visible information, where image evidence permits

Properties that are unknown or cannot be physically verified from an image are escalated to **REVIEW** rather than assumed.

## Two User Journeys

The product design separates two distinct ways of using the same underlying pipeline:

- **For Inspectors, Legal Metrology Inspection**: "Is this packaged commodity compliant?" OCR, rule checks, evidence, inspection report.
- **For Consumers, Food Intelligence**: "What am I actually eating?" Nutrition, ingredients, health signals, food profile.

*(These describe the intended product surfaces as presented in project planning; see [Current Status](#current-status) for what is confirmed working today.)*

## Why Not "Just OCR"

LabelMitra's differentiator is not text extraction alone; it's the chain connecting extraction to a decision and a record:

| Layer | Question it answers |
|---|---|
| OCR | What is written? |
| Rule | What is required? |
| Evidence | Where did we see it? |
| History | Has this been seen before? |

`OCR → declaration → legal rule → result → evidence → history`

## Technology Stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | React | Upload, workflows, results, dashboard |
| Backend | Python + FastAPI | APIs, orchestration, validation |
| OCR | EasyOCR | English + Hindi label text |
| AI | Grok API | Processes OCR output together with the original image to assist with ambiguous or unclear extraction |
| Rules | Python + JSON | Deterministic compliance logic; owns the compliance decision |
| Data | SQLite → PostgreSQL | SQLite is the current MVP store; PostgreSQL is a planned scalability direction, not yet in place |
| Reports | HTML → PDF | HTML is the current direction; PDF is a planned extension |

The architecture keeps OCR, AI, rules, and persistence as independently replaceable components.

## Current Status

Being explicit about what's actually running matters more than sounding finished:

**Working**
- FastAPI backend starts locally.
- Frontend upload workflow.
- Local API documentation.

**Integrated**
- Frontend successfully reaches the `/consumer/scan` endpoint.

**Pending Configuration**
- Grok API key for AI analysis. The AI-assisted extraction step is not yet fully operational end-to-end pending this configuration.

> Core local integration is in place; the team is finalizing the AI environment configuration and end-to-end reliability.

Everything described under Architecture and Technology Stack above reflects the intended design. Components not listed here as "Working" or "Integrated" should be read as designed/in-progress, not confirmed end-to-end.

## Trust & "Needs Verification"

A photo cannot reliably prove every physical property of a product, and LabelMitra is designed around that limitation rather than around it:

**When evidence is strong**: a visible declaration can be extracted, the relevant rule can be evaluated, and the finding can be explained with source evidence.

**When evidence is insufficient**: the image is blurry, glared, or at a bad angle; an exact physical measurement would need a reference object; or the required information is unclear or absent.

In the second case, the system is designed to mark the result as **REVIEW / NEEDS VERIFICATION** rather than guess. This is treated as a deliberate responsible-AI design choice, not a shortcoming. For example, something like font height cannot be reliably measured from a normal photograph without a physical reference, so the system is not designed to claim that it can.

## Responsible Use

**LabelMitra is:**
- An AI-assisted first-level verification tool.
- An evidence-linked workflow for inspection documentation.
- An explainable bridge between label data and structured compliance rules.

**LabelMitra is not:**
- A substitute for a certified Legal Metrology Officer.
- A guarantee that every physical property can be verified from a photograph.
- A reason to hide uncertainty or fabricate missing information.

Final legal determinations may require physical inspection and additional evidence beyond what an image can provide.

## Roadmap

1. **Rule Library**: expand and version additional Legal Metrology checks.
2. **Image Robustness**: improve handling of blur, glare, angle, and preprocessing.
3. **Evidence**: strengthen field-to-image evidence mapping.
4. **History**: improve repeat-product / repeat-issue tracking.
5. **Infrastructure**: move MVP persistence toward PostgreSQL, with production hardening.
6. **Deployment**: strengthen auth, logging, security, and operational reliability.

The current prototype is designed to grow along this roadmap without changing its core architecture.

## Potential Impact

If the roadmap is realized, the intended benefits are faster first-level verification, more consistent checks across products, explainable evidence trails, and connected inspection history. Extension beyond the current MVP scope, to retail, supermarkets, warehouses, e-commerce, and other packaged commodities, is a stated future direction, not a current deployment.

## Team

**Neural Nexus**, IIT Patna


*This README reflects the project's current design and confirmed implementation status as of the latest development round. Sections will be updated as components move from planned to working.*
