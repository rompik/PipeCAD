# Repository Structure Cases for PipeCAD

## Purpose
This document proposes folder structure cases to simplify development, improve ownership, and make release control more predictable.

## Current Pain Points
- Runtime assets are split across multiple top-level folders (`settings`, `uic`, `templates`, `translations`).
- Source code is concentrated in `lib/pipecad` with many modules at one level.
- Documentation is organized by language, but content parity is hard to track.
- Product assets and documentation assets are mixed in different places.

## Case A: Minimal Change (Low Risk)
### Goal
Improve clarity with minimal file moves.

### Structure
- Keep existing top-level folders.
- Add governance files and naming rules.

### Actions
1. Add ownership map by area (code, docs, translations, UI files).
2. Standardize naming for docs and translation files.
3. Add CI checks for docs links and translation consistency.

### Pros
- Very low migration effort.
- Minimal risk of import/path breakage.

### Cons
- Structural complexity remains.
- Long-term scaling is limited.

## Case B: Balanced Refactor (Recommended)
### Goal
Separate source, runtime resources, and documentation while keeping migration manageable.

### Target Structure
- `src/pipecad` (from `lib/pipecad`)
- `src/omp` (from `lib/omp`)
- `resources/runtime/settings`
- `resources/runtime/uic`
- `resources/runtime/templates`
- `resources/runtime/translations`
- `docs/en`, `docs/ru`, `docs/zh`, `docs/shared`

### Actions
1. Move `lib/pipecad` to `src/pipecad` and `lib/omp` to `src/omp`.
2. Move runtime data folders under `resources/runtime`.
3. Normalize Chinese docs to `docs/zh` directory layout.
4. Add compatibility path handling during transition.
5. Update build/package scripts once, then remove compatibility layer after stabilization.

### Pros
- Clear domain boundaries.
- Better onboarding and ownership.
- Better release control for runtime assets.

### Cons
- Requires coordinated path updates.
- Medium migration effort.

## Case C: Full Product Monorepo Layout (High Control)
### Goal
Create strict separation for product lifecycle and team scaling.

### Target Structure
- `apps/pipecad-desktop`
- `packages/core`, `packages/features`, `packages/ui`
- `resources/runtime`
- `docs`
- `tools/qa`, `tools/release`, `tools/dev`
- `tests/unit`, `tests/integration`, `tests/smoke`

### Actions
1. Split application layers into package boundaries.
2. Add explicit API contracts between packages.
3. Add full CI matrix (lint, test, packaging, docs, i18n).
4. Add release manifests for runtime artifacts.

### Pros
- Maximum scalability and governance.
- Strong release and quality gates.

### Cons
- Highest migration and maintenance cost.
- Requires stronger engineering process maturity.

## Recommendation
Select Case B as the default path.

Reason:
- It solves most structural issues.
- It avoids monorepo-level complexity.
- It can be delivered in phased migration without long freeze windows.

## Phased Rollout for Case B
1. Phase 1: Move runtime resource folders first and update loading paths.
2. Phase 2: Move source folders from `lib/*` to `src/*` with compatibility imports.
3. Phase 3: Normalize docs language structure and add parity checks.
4. Phase 4: Remove compatibility layer and lock structure with CI rules.

## Decision Checklist
- Do we need minimal disruption now? Choose Case A.
- Do we need better structure without heavy process overhead? Choose Case B.
- Do we plan multi-team scaling with strict release governance? Choose Case C.
