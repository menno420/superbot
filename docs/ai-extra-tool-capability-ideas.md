# AI Extra Tool Capability Ideas Backlog

**Status:** ideas backlog — not approved for implementation yet.  
**Created:** 2026-06-06  
**Purpose:** capture AI tool/capability ideas that are not already covered by the current bot-awareness diagnostics plan or the BTD6 complex tool-orchestration plan.  
**Review required before implementation:** architecture, privacy, Discord permissions/intents, cost controls, model-provider support, data retention, moderation risk, and per-guild configuration.

---

## 1. Relationship to existing docs

This document is intentionally separate from the current implementation plans because the existing docs already have narrow ownership:

- `docs/bot-awareness-implementation-plan.md` focuses on operational health diagnostics, startup health, structured observations, persistent findings, and one deferred read-only AI diagnostics tool.
- `docs/ai-complex-request-tool-orchestration-plan.md` focuses on reusable AI tool orchestration, especially for complex BTD6 requests, toolsets, tool-choice policy, strict schemas, budgets, and evidence contracts.

This backlog should **not** replace those plans. Any idea here should later be refined into one of the existing orchestration/tool registry abstractions rather than implemented as an isolated cog feature.

Core architectural rule:

```text
AI request
→ resolved AI policy / scope
→ deterministic toolset selection
→ AI tool gateway
→ rate limit + budget + audit
→ tool execution
→ bounded structured result
→ answer contract / renderer
```

Do not expose raw unrestricted APIs, raw SQL, raw logs, arbitrary file access, arbitrary web access, or direct destructive Discord actions to the model.

---

## 2. Already covered elsewhere — do not duplicate

The following are already represented in existing docs and should be reused instead of reinvented:

| Area | Existing direction | Reuse decision |
|---|---|---|
| Bot health diagnostics | `diagnostics_health_snapshot`, `HealthSnapshot`, `HealthAudience`, redacted health projections | Extend the diagnostics toolset; do not create a second bot-awareness service |
| Tool orchestration policy | `AIOrchestrationPolicy`, `AIToolBudget`, `AIToolChoice`, `ToolRequirementMode` | Use as the central selection/budget layer |
| Tool metadata | `AIToolDescriptor` with toolsets, cost class, freshness, task affinity, preflight safety, result contract | Add new capabilities as descriptors, not ad hoc handlers |
| BTD6 lookup/calculation tools | `btd6_reference`, `btd6_costs`, `btd6_rounds`, `btd6_paragon`, `btd6_grounding` | Keep BTD6-specific tools in the existing BTD6 orchestration plan |
| Diagnostics toolset | Reserved `diagnostics` toolset | Add future operational tools there when ready |
| Server context toolsets | `server_context_basic`, `server_context_sensitive` | Place Discord context tools there, scope-gated |
| Evidence/calculation contracts | `CalculationEvidence`, typed result contracts, faithfulness guard | Reuse for factual and numeric tools |
| Trace/audit direction | Safe orchestration traces, no raw reasoning/results | Extend for all new tools |

Everything below is an **additional idea** that was not explicitly planned in the existing docs.

---

## 3. Proposed new toolsets

Suggested additional toolsets for later refinement:

| Toolset | Purpose | Likely scope |
|---|---|---|
| `web_research` | Search and summarize current external information | Public/Trusted/Admin depending on channel |
| `media_vision` | Analyze user-provided images and screenshots | Public in allowed channels; Admin for diagnostics/moderation |
| `document_reader` | Read uploaded text/log/config/PDF-like files safely | Trusted/Admin by default |
| `external_integrations` | Approved wrappers for GitHub, YouTube, Twitch, Google, custom APIs | Admin/Owner unless public-safe |
| `observability_extended` | Charts, website checks, uptime/status probes | Admin/Owner |
| `notification_actions` | Controlled report/alert delivery to configured channels | Admin/Owner, confirmation-gated |
| `admin_actions_safe` | Reload cache, sync data, run diagnostics, regenerate reports | Owner-only, confirmation-gated |
| `knowledge_base` | Search SuperBot docs, project plans, command docs, known issues | Public for public docs; Admin/Owner for internal docs |

These should be added to the existing tool orchestration catalogue only after the base policy resolver, strict schemas, budget enforcement, and audit trace are stable.

---

## 4. Net-new read-only tools

### 4.1 Web search / web research tool

**Idea:** allow the AI to search current web information for questions that require fresh or external context.

Use cases:

- current Discord API behavior or documentation lookup;
- game patch notes and update summaries;
- provider changelogs;
- troubleshooting unknown errors;
- live service status pages;
- recent library/API changes;
- general research questions in allowed channels.

Recommended shape:

```text
web_search(query, max_results, freshness_hint, allowed_domains?, blocked_domains?)
→ normalized source list
→ short cited summary
→ source confidence / freshness metadata
```

Required safeguards:

- configurable per guild/category/channel;
- disabled by default in casual channels unless explicitly enabled;
- source allow/deny lists for high-risk use;
- result caching for repeated queries;
- budget limits for search count and fetched result length;
- clear source/citation output where possible;
- no automatic browsing for every message;
- no arbitrary scraping loops.

Review questions:

- Which provider should power search?
- Should web search be public, trusted-only, or admin-only by default?
- Should specific domains be preferred for Discord/OpenAI/GitHub/BTD6 topics?

Priority: **High**, after orchestration policy exists.

---

### 4.2 Image vision / screenshot analysis tool

**Idea:** allow users to upload images and ask the AI to inspect them.

Use cases:

- Discord permission screenshots;
- bot error screenshots;
- setup/config screenshots;
- game screenshots;
- chart/diagram explanation;
- visible text extraction from screenshots;
- UI troubleshooting.

Recommended shape:

```text
analyze_image(attachment_id, requested_task, context_scope)
→ visible objects/text summary
→ issue diagnosis if requested
→ uncertainty flags
→ no permanent image retention by default
```

Required safeguards:

- only inspect images explicitly uploaded or linked in the request context;
- file type and size validation;
- no persistent storage by default;
- redact or warn on visible tokens/API keys/passwords;
- disallow hidden/private-channel image access unless requester has permission;
- moderation use requires higher scope and clear audit logging.

Review questions:

- Should vision be available to normal users or limited to support/admin channels?
- Should screenshots be passed directly to the model or preprocessed through OCR first?
- What retention should apply to image-derived summaries?

Priority: **Very High** for support and diagnostics.

---

### 4.3 File, log, and document reader tool

**Idea:** allow the AI to read uploaded files and produce safe summaries or diagnostics.

Useful formats:

- `.txt`, `.md`, `.log`;
- `.json`, `.csv`, `.yaml`, `.toml`, `.xml`;
- code snippets such as `.py`, `.js`, `.ts`;
- PDFs only if a safe extraction path is added.

Use cases:

- startup log review;
- config troubleshooting;
- exported stats analysis;
- JSON API response explanation;
- CSV report summaries;
- code/config review for admin support.

Recommended shape:

```text
read_uploaded_file(attachment_id, parser_mode, max_chars, redaction_mode)
→ parsed chunks
→ detected secrets warning
→ summary / findings
```

Required safeguards:

- strict file size limit;
- allowed extension list;
- block executable/binary files by default;
- secret redaction before model context;
- chunking and result-size budgets;
- no long-term storage unless explicitly configured;
- admin-only for logs/configs by default.

Review questions:

- Which parsers are safe to run in production?
- Should PDF support be included or deferred?
- Should detected secrets abort processing or continue with redaction?

Priority: **High**.

---

### 4.4 OCR tool

**Idea:** deterministic text extraction from images before optional AI interpretation.

Use cases:

- logs pasted as screenshots;
- mobile error screenshots;
- Discord settings screenshots;
- game UI text extraction.

Recommended shape:

```text
extract_text_from_image(attachment_id)
→ extracted_text
→ confidence / low-quality warning
```

Required safeguards:

- same access/retention rules as image vision;
- output length cap;
- secret redaction pass before AI summarization.

Review questions:

- Is OCR needed separately if vision model quality is good enough?
- Should OCR be deterministic/local for cost control?

Priority: **Medium**.

---

### 4.5 Knowledge-base search tool

**Idea:** index and search SuperBot-specific knowledge so the AI can answer from project truth instead of memory.

Potential sources:

- command documentation;
- architecture docs;
- implementation plans;
- known issues;
- changelogs;
- BTD6 data documentation;
- moderation/server rules;
- admin runbooks;
- policy previews and configuration docs.

Recommended shape:

```text
knowledge_search(query, corpus, scope, freshness)
→ matching passages
→ source document IDs
→ safe summary
```

Required safeguards:

- separate public/admin/owner corpora;
- document-level ACLs;
- citations/source references in answers;
- stale document warning;
- no indexing of raw private logs by default.

Review questions:

- Should this index repository docs only at first?
- Should Discord-pinned messages or server rules become a separate corpus?
- How should stale plans be marked as superseded?

Priority: **Very High**.

---

### 4.6 Chart generation tool

**Idea:** generate deterministic charts from approved bot/server metrics.

Use cases:

- command usage over time;
- error frequency;
- channel activity heatmaps;
- startup health history;
- API freshness timelines;
- BTD6 lookup usage;
- member growth and invite trends.

Recommended shape:

```text
render_metric_chart(metric_key, timeframe, grouping, output_format)
→ image/file attachment
→ summarized observations
```

Required safeguards:

- chart only from approved metrics/views;
- no raw SQL;
- cap time ranges and series count;
- admin-only for sensitive metrics;
- cache generated charts briefly.

Review questions:

- Should charts be generated locally or through an external chart service?
- Which metrics should be chartable in the first version?

Priority: **High** for admin/reporting workflows.

---

## 5. Net-new external integration tools

### 5.1 GitHub repository and CI tool

**Idea:** let the AI inspect approved GitHub repository information.

Use cases:

- summarize recent commits;
- inspect open issues/PRs;
- summarize failed GitHub Actions runs;
- connect runtime errors to recent code changes;
- generate release/deployment summaries;
- identify docs that mention a subsystem.

Recommended shape:

```text
github_lookup(operation, repository, filters)
→ normalized issue/PR/commit/workflow summary
```

Required safeguards:

- repository allowlist;
- read-only by default;
- owner-only for private repos unless explicitly configured;
- no automatic issue/PR creation in first version;
- redact tokens and private URLs from logs.

Review questions:

- Should GitHub be read-only permanently, or later support issue creation?
- Should failed CI summaries feed startup/deployment reports?

Priority: **High** if GitHub is the main development workflow.

---

### 5.2 Website and API status monitor tool

**Idea:** let the AI check whether approved websites, APIs, or services are reachable.

Use cases:

- check bot website/API uptime;
- verify external API availability;
- inspect response status/time;
- summarize service degradation;
- support scheduled status reports.

Recommended shape:

```text
check_endpoint_status(endpoint_key)
→ status_code
→ latency_ms
→ freshness
→ degraded_reason
```

Required safeguards:

- endpoint allowlist only;
- rate limits;
- no arbitrary URL probing;
- no internal network probing unless explicitly designed;
- clear distinction between transient failure and confirmed outage.

Review questions:

- Which endpoints should be registered first?
- Should this feed the health snapshot service or remain a separate observability tool?

Priority: **High**.

---

### 5.3 YouTube / Twitch content status tool

**Idea:** let the AI inspect approved creator/channel data.

Use cases:

- detect livestream status;
- summarize latest upload;
- prepare announcement text;
- report scheduled streams;
- notify configured channels when content goes live.

Recommended shape:

```text
creator_platform_lookup(platform, channel_key, operation)
→ latest_video / live_status / scheduled_stream summary
```

Required safeguards:

- channel allowlist;
- avoid excessive polling;
- announcement posting requires confirmation or preconfigured automation;
- no private user data access.

Review questions:

- Is this actually needed for SuperBot’s roadmap?
- Should announcements be automatic or manually approved?

Priority: **Medium**.

---

### 5.4 Google Sheets / Docs reader tool

**Idea:** allow AI to read approved planning documents or spreadsheets.

Use cases:

- summarize planning docs;
- inspect project/status sheets;
- read structured configuration tables;
- generate reports from maintained spreadsheets.

Recommended shape:

```text
google_workspace_read(document_key, range_or_section, scope)
→ normalized text/table summary
```

Required safeguards:

- explicit document allowlist;
- read-only first;
- owner/admin-only by default;
- avoid syncing private personal documents;
- log every access.

Review questions:

- Is project planning stored in Google Workspace enough to justify this?
- Should write/update support ever be allowed?

Priority: **Medium to Low** unless planning data lives there.

---

### 5.5 Generic approved API fetch tool

**Idea:** create a generic connector pattern for approved APIs without allowing arbitrary fetches.

Use cases:

- Ninja Kiwi/BTD6 live endpoints;
- GitHub;
- creator platforms;
- website status;
- custom SuperBot endpoints;
- future game/community APIs.

Recommended shape:

```text
api_connector_call(provider_key, operation_key, params)
→ provider-normalized result contract
```

Required safeguards:

- approved provider registry;
- strict parameter schemas per operation;
- per-provider rate limits;
- result caps;
- no arbitrary user-supplied URLs;
- provider health exposed through diagnostics.

Review questions:

- Should this be a low-level shared service below individual tools?
- Which provider should be the first reference implementation?

Priority: **Very High** as reusable infrastructure.

---

## 6. Net-new action-gated tools

These tools should not be available until the tool gateway, audit trace, confirmation flow, and role/scope model are stable.

### 6.1 Scheduler / recurring report tool

**Idea:** let authorized users configure scheduled reports or reminders.

Use cases:

- daily health report;
- weekly community activity summary;
- startup follow-up after restart;
- stale thread reminders;
- API freshness checks;
- event reminders.

Recommended shape:

```text
schedule_report(report_type, target_channel, cadence, audience)
→ draft schedule
→ explicit confirmation
→ stored scheduler job
```

Required safeguards:

- confirmation required;
- target channel permission check;
- no uncontrolled mentions;
- owner/admin-only for recurring jobs;
- clear cancellation command;
- audit all schedule changes.

Review questions:

- Should this extend the existing managed task registry or use a dedicated persistent scheduler?
- Which report types are safe for automation?

Priority: **High**, but only after read-only reports exist.

---

### 6.2 Notification delivery tool

**Idea:** allow AI-generated summaries or alerts to be sent to configured channels.

Use cases:

- startup report to debug channel;
- API sync failure alert;
- command failure spike alert;
- weekly admin report;
- moderation anomaly summary.

Recommended shape:

```text
send_configured_notification(template_key, target_key, payload)
→ posted message metadata
```

Required safeguards:

- target allowlist;
- mention policy;
- no mass-DM;
- confirmation for ad hoc sends;
- fixed templates for automated sends;
- audit message ID and payload summary.

Review questions:

- Which alerts should be automatic vs manually requested?
- Should AI draft the message, or should deterministic templates own the final text?

Priority: **High** for operations.

---

### 6.3 Safe admin action tool

**Idea:** allow owner-only AI-assisted execution of low-risk maintenance actions.

Potential safe actions:

- rerun health snapshot;
- refresh approved API cache;
- resync slash commands;
- reload a non-critical cog;
- clear bot-owned ephemeral cache;
- regenerate startup/diagnostic report;
- run a configured check.

Recommended shape:

```text
propose_admin_action(action_key, params)
→ risk summary
→ explicit owner confirmation
→ execute through deterministic service
→ audit result
```

Required safeguards:

- owner-only;
- confirmation required;
- action allowlist;
- no direct shell access;
- no arbitrary Python/code execution;
- no database writes except through approved services;
- rollback/failure message where possible.

Explicitly out of scope for first version:

- ban/kick/timeout;
- mass delete;
- role/permission edits;
- deployment;
- shell commands;
- arbitrary file editing;
- arbitrary SQL;
- mass messaging.

Review questions:

- Which maintenance actions are truly safe enough?
- Should cog reload be allowed in production or only test/staging?

Priority: **Medium**, after diagnostics are trusted.

---

### 6.4 Moderation recommendation tool

**Idea:** have the AI summarize moderation signals and recommend review actions, without directly punishing users.

Use cases:

- suspicious join wave summary;
- invite spike summary;
- repeated spam pattern explanation;
- audit-log correlation;
- member behavior review packet for moderators.

Recommended shape:

```text
moderation_review_summary(subject, timeframe, evidence_types)
→ evidence summary
→ risk indicators
→ recommended manual review action
```

Required safeguards:

- moderator/admin-only;
- evidence must come from approved moderation signal services;
- no raw private data dumping;
- no automatic punitive action;
- separate facts from recommendations;
- audit reviewer and subject.

Review questions:

- Which moderation signals are reliable enough?
- Should this be implemented before or after audit-log/invite tracking exists?

Priority: **Medium**.

---

## 7. Provider/model capability considerations

Before implementation, review current provider support and cost/latency behavior for:

- web search support;
- image input support;
- file input support;
- strict function schemas;
- required tool choice;
- parallel tool calls;
- structured outputs;
- token/result limits;
- image/file retention behavior;
- pricing by modality.

Do not design the internal architecture around one provider-specific feature. Keep provider-specific payloads inside provider adapters and expose provider-neutral contracts to the rest of SuperBot.

---

## 8. Privacy, safety, and retention defaults

Default stance for all new tools:

- read-only before write/action;
- explicit per-guild/channel enablement for sensitive tools;
- strict scope checks before tool selection;
- bounded input and output sizes;
- result redaction before model context;
- audit every sensitive tool call;
- no permanent storage of uploaded files/images by default;
- no arbitrary web/API/file/database access;
- no destructive Discord actions without explicit confirmation;
- deterministic services remain source of truth;
- AI explains and recommends, but does not own facts.

Suggested retention classes:

| Data | Default retention |
|---|---|
| Uploaded image/file bytes | Do not persist beyond processing unless explicitly configured |
| Extracted text from uploads | Short-lived session cache only |
| Tool call trace | Bounded audit summary, no raw private content |
| Web search results | Short cache with source URLs and snippets only |
| Generated charts | Short-lived attachment/cache |
| Scheduled report configs | Persistent until disabled/deleted |
| Admin action audit | Persistent operational audit |

---

## 9. Suggested phased refinement order

### Phase A — foundations only

- Extend `AIToolDescriptor`/toolsets for the new categories.
- Confirm strict schema validator covers new tools.
- Add policy preview for offered/excluded tools.
- Add safe audit trace fields.

### Phase B — low-risk high-value tools

- Knowledge-base search over repository docs.
- Image vision for user-uploaded screenshots.
- File/log reader for uploaded text/log/config files.
- Web search in admin/support channels.

### Phase C — operational integrations

- Approved API connector base.
- GitHub read-only lookup.
- Website/API status monitor.
- Chart generation from approved metrics.

### Phase D — scheduled and notification workflows

- Recurring health/community reports.
- Configured admin/debug notifications.
- Startup/deployment summary delivery.

### Phase E — confirmation-gated actions

- Safe admin actions.
- Moderation review packets.
- Optional creator-platform announcements.

---

## 10. First refinement targets

The strongest candidates for a first dedicated planning pass are:

1. **Knowledge-base search** — gives the AI reliable access to SuperBot docs/plans and reduces repeated context loss.
2. **Image vision** — high support/debug value for screenshots with clear user intent.
3. **File/log reader** — directly supports startup/debug workflows.
4. **Web search** — solves freshness gaps, but needs stronger source/cost controls.
5. **Approved API connector base** — reusable foundation for GitHub, BTD6 live data, YouTube/Twitch, website checks, and custom APIs.

Recommended next step: convert one of these into a dedicated planning doc that plugs into `AIOrchestrationPolicy`, `AIToolDescriptor`, strict schemas, budget controls, audit traces, and per-guild/channel configuration.
