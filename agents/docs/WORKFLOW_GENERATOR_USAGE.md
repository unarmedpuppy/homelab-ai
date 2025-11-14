# Workflow Generator Meta-Prompt - Usage Guide

## Quick Start

The `WORKFLOW_GENERATOR_PROMPT.md` is a **meta-prompt** that instructs an AI agent to set up a complete agent workflow infrastructure for any feature or project.

## How to Use

### Step 1: Provide the Meta-Prompt

Give an AI agent (like Claude, GPT-4, etc.) the contents of `WORKFLOW_GENERATOR_PROMPT.md` along with your feature description.

### Step 2: Provide Feature Description

**Example Input**:
```
Feature: "Refactor this application to migrate from Redux/Sagas to React Context providers"

Project: Existing React/TypeScript application
Location: /path/to/project
```

### Step 3: Agent Will Ask Questions

The agent will first ask clarifying questions about:
- Project structure (new vs existing)
- Tech stack details
- Migration strategy
- Scope and timeline
- Coding standards preferences

**Answer these questions** so the agent can generate accurate, project-specific files.

### Step 4: Agent Generates All Files

The agent will create the complete workflow infrastructure in `agents/` directory:

```
agents/
├── docs/
│   ├── IMPLEMENTATION_PLAN_[FEATURE].md
│   ├── GETTING_STARTED.md
│   ├── CODING_STANDARDS.md
│   ├── CODING_prompts/base.md
│   ├── REVIEW_prompts/base.md
│   └── TASKS.md
└── scripts/
    └── pre-submit-check.sh
```

### Step 5: Start Using the Workflow

1. **For Coding Agents**: Use `agents/docs/CODING_prompts/base.md`
2. **For Review Agents**: Use `agents/docs/REVIEW_prompts/base.md`
3. **For Task Tracking**: Use the Task Coordination System (`agents/tasks/registry.md`) - See `agents/tasks/README.md`
4. **For Setup**: Read `agents/docs/GETTING_STARTED.md`

## What Gets Generated

### 1. Implementation Plan
Complete specification of the feature including:
- Requirements
- Architecture
- API specs (if applicable)
- Migration plan (if refactoring)
- Testing strategy

### 2. Getting Started Guide
Essential information for agents:
- Environment setup
- Configuration
- Common gotchas
- Testing procedures

### 3. Coding Standards
Extracted from codebase analysis:
- Code style
- Naming conventions
- Patterns to follow
- Documentation requirements

### 4. Coding Agent Prompt
Complete prompt for coding agents with:
- Role and responsibilities
- Technology stack
- Coding standards
- Pre-submission checklist (full, inline)
- Task claiming process

### 5. Review Agent Prompt
Complete prompt for review agents with:
- Review process
- Detailed checklists
- Feedback template (full, inline)
- Batch review process

### 6. Task List
Breakdown of feature into:
- Claimable tasks (1-4 hours each)
- Dependencies (auto-detected)
- Priority levels
- Acceptance criteria

### 7. Pre-Submission Script
Project-specific validation script:
- Syntax checking
- Type checking
- Linting
- Format checking

## Example Workflow

```
1. User: "Use WORKFLOW_GENERATOR_PROMPT.md to set up workflow for migrating Redux to Context"

2. Agent: "I need to clarify:
   - Is this an existing project? What's the path?
   - What's the current Redux structure?
   - Should we migrate all at once or incrementally?
   ..."

3. User: [Answers questions]

4. Agent: [Analyzes codebase, generates all files]

5. User: [Uses generated prompts for coding/review agents]
```

## Key Features

✅ **Self-Contained**: All templates included inline, no external references  
✅ **Project-Specific**: Customized for your codebase and tech stack  
✅ **Complete**: Generates all necessary files for the workflow  
✅ **Auto-Detection**: Detects dependencies, patterns, and structure  
✅ **Asks Questions**: Clarifies before generating to ensure accuracy  

## Tips

1. **Be Specific**: The more detail in your feature description, the better
2. **Answer Questions**: Don't skip the clarification phase
3. **Review Generated Files**: Check that everything matches your project
4. **Customize if Needed**: You can adjust generated files after creation
5. **Archive Old Files**: Move completed/stale docs to `agents/archive/`

## Troubleshooting

**Agent asks too many questions?**
- Provide more detail in your initial feature description
- Include tech stack, project type, and scope upfront

**Generated files don't match project?**
- Review the codebase analysis section
- Manually adjust files as needed
- Re-run with more specific instructions

**Missing dependencies?**
- Use Task Coordination System to register tasks with dependencies
- Dependencies are automatically validated when claiming tasks
- See `agents/tasks/README.md` for dependency management

## Next Steps

After generating the workflow:

1. Review all generated files
2. Test the pre-submit script: `./agents/scripts/pre-submit-check.sh`
3. Start with task T1.1 using CODING_prompts/base.md
4. Use REVIEW_prompts/base.md for code reviews
5. Track progress using Task Coordination System (`update_task_status()`)

---

**See Also**:
- `WORKFLOW_GENERATOR_PROMPT.md` - The meta-prompt itself
- `AGENT_WORKFLOW.md` - Overall workflow documentation

