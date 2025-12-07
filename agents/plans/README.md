# Plans Directory

Committed plans for multi-session features, architectural decisions, and implementation strategies.

## Purpose

This directory contains **persistent plans** that should be committed to git and shared across sessions. These are plans for future work, architectural decisions, and implementation strategies.

## What Goes Here

- **Implementation strategies** (e.g., migration plans, upgrade strategies)
- **Architectural decisions** (e.g., infrastructure changes, system designs)
- **Multi-session features** (e.g., complex features that span multiple sessions)
- **Plans that need to persist** (e.g., ZFS migration strategies, deployment plans)

## What Does NOT Go Here

- **Reference documentation** → Use `agents/reference/` instead
- **How-to guides** → Use `agents/reference/` instead
- **Ephemeral/scratch work** → Use `agents/plans-local/` instead (gitignored)
- **Project-level docs** → Use `docs/` for security audits, etc.

## Examples

✅ **Good examples for `agents/plans/`:**
- `ZFS_RAIDZ1_TO_RAIDZ2_MIGRATION.md` - Migration strategy plan
- `ZFS_TWO_POOL_STRATEGY.md` - Implementation strategy
- `infrastructure-upgrade-plan.md` - Architectural decision

❌ **Should be in `agents/reference/`:**
- `ZFS_DRIVE_RECOMMENDATIONS.md` - Reference guide
- `ZFS_20TB_VS_8TB_ANALYSIS.md` - Reference/analysis doc
- Setup guides, troubleshooting guides

## Structure

Plans should follow a clear structure:
- Objective
- Prerequisites
- Steps/process
- Success criteria
- Risks/considerations

See `agents/reference/plan_act.md` for plan templates.
