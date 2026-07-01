## MISS Alpha v0.4

From v0.3.0-alpha: 25+ commits, 7 Specs delivered

### Core Engine (Phase 0-7)

- 10-dimension attribute engine with dual-track cognition
- Jinja2 system prompt template (8 XML blocks)
- PromptBuilder 4-step pipeline, LLMCaller 3-level fallback (TOOLS→JSON→Raw)
- Memory scoring engine, vector store (ChromaDB), streaming SSE
- Easter egg (Cirno mode) and cross-effect matrix

### Desktop (WPF MVVM)

- pythonnet single-process embedding (zero port, zero HTTP overhead)
- CommunityToolkit.Mvvm, LiteDB encrypted persistence, NAudio playback
- 14 avatar presets, role sidebar, attribute panel, settings persistence

### Phase 5: AI Role Factory

- One instructor LLM call generates complete character (name + 10-dim profile + background + tags + avatar suggestion)
- GeneratedRole with embedded AnalysisResult — no second analyze_character() call

### Phase 6: Knowledge Domain + TTS

- KnowledgeDomainEngine — role tags injected into system prompt as pre-constraint
- KnowledgeFilter downgraded to log-only when domains exist (avoids double-stupid)
- TTS Voice Synthesis — Edge TTS + NAudio AudioPlayer on each message bubble
- Fallback to Windows SAPI5 (pyttsx3) when Edge TTS unavailable

### Architecture Optimization (trinity-mentors reviewed)

40 subtasks → 18 subtasks, 9 person-days → 4.5 person-days:
- Merged double LLM calls into one
- Removed /api/tts/synthesize HTTP endpoint (pythonnet in-process instead)
- Removed PyInstaller-related subtasks (switched to pythonnet embedding)

### Specs Delivered

| Spec | Status |
|------|--------|
| fix-role-save-and-ui | PASS |
| desktop-packaging | PASS |
| desktop-rebuild | PASS |
| desktop-polish | PASS |
| fix-binding-and-api | PASS |
| fix-llm-api-compat | PASS |
| fix-license-headers | PASS |
| fix-residual-risks | PASS |
| phase5-role-factory-tts | PASS |
| Security Audit 5 phases (38/38) | A Grade |

### Quality

- pytest ~190/190 full regression
- 63 issues tracked across 7 acceptance rounds
- 7 project Skills (coding-ethics / acceptance-testing / security-academy / spec-pipeline / project-secretary / test-driven-development / trinity-mentors)

### Contributor Notice

Please read [CLA.md](https://github.com/luyi14-bits/MISS-project/blob/master/CLA.md) — submitting a PR implies acceptance of its terms.
