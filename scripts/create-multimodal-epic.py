#!/usr/bin/env python3
"""
Script to create Beads epic and tasks for multimodal inference support.
Run this script to add all tasks to .beads/issues.jsonl
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Get repo root
repo_root = Path(__file__).parent.parent
beads_file = repo_root / ".beads" / "issues.jsonl"

# Generate a simple hash-like ID (using title hash)
def generate_id(title, existing_ids):
    """Generate a simple ID from title"""
    import hashlib
    base = hashlib.md5(title.encode()).hexdigest()[:3]
    id_str = f"home-server-{base}"
    # Ensure uniqueness
    counter = 0
    while id_str in existing_ids:
        counter += 1
        id_str = f"home-server-{base}{counter}"
    return id_str

# Read existing issues to get IDs
existing_ids = set()
if beads_file.exists():
    with open(beads_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                issue = json.loads(line)
                existing_ids.add(issue['id'])

now = datetime.now().isoformat()

# Epic
epic_title = "Multimodal Inference Support"
epic_id = generate_id(epic_title, existing_ids)
existing_ids.add(epic_id)

epic = {
    "id": epic_id,
    "title": epic_title,
    "description": "Add support for image generation/editing models alongside existing text generation models in the local AI system. Includes research, manager extension, server proxy updates, UI enhancements, and testing. See agents/plans/multimodal-inference-support.md for full plan.",
    "status": "open",
    "priority": 1,
    "issue_type": "epic",
    "created_at": now,
    "updated_at": now,
    "labels": ["local-ai", "multimodal", "feature"]
}

# Tasks
tasks = [
    # Phase 1: Research & Setup
    {
        "title": "Research inference engines for image models",
        "description": "Research inference engines for image generation models:\n- HuggingFace Diffusers (for diffusion models)\n- Custom FastAPI server with transformers\n- Check if Qwen Image Edit has official inference server\n- Evaluate performance and GPU requirements\n\nDeliverable: Research document comparing options",
        "priority": 1,
        "labels": ["local-ai", "research", "phase-1"]
    },
    {
        "title": "Choose inference engine and document decision",
        "description": "Choose inference engine based on research:\n- Document decision and rationale\n- Test with Qwen Image Edit model\n- Verify GPU compatibility\n\nDeliverable: Decision document with rationale",
        "priority": 1,
        "labels": ["local-ai", "research", "phase-1"]
    },
    {
        "title": "Create image model container setup",
        "description": "Create container setup for image models:\n- New setup script or extend existing setup.sh\n- Dockerfile for image inference engine\n- Test container creation and model loading\n\nDeliverable: Working image model container (proof of concept)",
        "priority": 1,
        "labels": ["local-ai", "docker", "phase-1"]
    },
    
    # Phase 2: Manager Extension
    {
        "title": "Update models.json format with type field",
        "description": "Extend models.json to include model type (text vs image):\n```json\n{\n    \"llama3-8b\": {\n        \"container\": \"vllm-llama3-8b\",\n        \"port\": 8001,\n        \"type\": \"text\"\n    },\n    \"qwen-image-edit\": {\n        \"container\": \"qwen-image-server\",\n        \"port\": 8005,\n        \"type\": \"image\"\n    }\n}\n```\n\nDeliverable: Updated models.json with type field",
        "priority": 1,
        "labels": ["local-ai", "manager", "phase-2"]
    },
    {
        "title": "Update manager.py to detect and route by model type",
        "description": "Extend manager.py to handle both model types:\n- Add model type checking\n- Route text requests to vLLM containers\n- Route image requests to image inference containers\n- Handle different health check endpoints\n\nDeliverable: Updated manager.py with dual-type support",
        "priority": 1,
        "labels": ["local-ai", "manager", "phase-2"]
    },
    {
        "title": "Update container management for image models",
        "description": "Extend container management to support image models:\n- Different start/stop logic for image models\n- Different readiness checks\n- Unified interface for both types\n\nDeliverable: Container management working for both types",
        "priority": 1,
        "labels": ["local-ai", "manager", "phase-2"]
    },
    
    # Phase 3: Server Proxy
    {
        "title": "Add image generation endpoint routing",
        "description": "Update server proxy to handle image generation:\n- Ensure /v1/images/generations properly routes to image models\n- Handle image model-specific request formats\n- Process image responses (base64, URLs, etc.)\n\nDeliverable: Image generation endpoint working",
        "priority": 1,
        "labels": ["local-ai", "proxy", "phase-3"]
    },
    {
        "title": "Update error handling for image models",
        "description": "Improve error handling:\n- Better error messages for unsupported operations\n- Model type validation\n- Clear error messages when wrong endpoint used\n\nDeliverable: Improved error handling",
        "priority": 1,
        "labels": ["local-ai", "proxy", "phase-3"]
    },
    {
        "title": "Add model type detection and validation",
        "description": "Add model type detection to proxy:\n- Check model type before routing\n- Validate requests match model capabilities\n- Prevent text requests to image models and vice versa\n\nDeliverable: Model type validation working",
        "priority": 1,
        "labels": ["local-ai", "proxy", "phase-3"]
    },
    
    # Phase 4: UI Updates
    {
        "title": "Add image display capability to terminal UI",
        "description": "Extend terminal UI to display images:\n- Support base64 image data\n- Support image URLs\n- Retro-styled image display (fits terminal aesthetic)\n\nDeliverable: Images displayed in terminal UI",
        "priority": 1,
        "labels": ["local-ai", "ui", "phase-4"]
    },
    {
        "title": "Update request handling for image models",
        "description": "Update UI request handling:\n- Detect when using image model\n- Use /v1/images/generations endpoint for image models\n- Use /v1/chat/completions for text models\n- Handle both text and image responses\n\nDeliverable: UI correctly routes to appropriate endpoints",
        "priority": 1,
        "labels": ["local-ai", "ui", "phase-4"]
    },
    {
        "title": "Add image input support (optional)",
        "description": "Add image input capability (future enhancement):\n- Image upload capability\n- Multimodal prompts (text + image)\n- Image editing workflow\n\nNote: This is optional and can be deferred",
        "priority": 3,
        "labels": ["local-ai", "ui", "phase-4", "optional"]
    },
    
    # Phase 5: Testing & Documentation
    {
        "title": "End-to-end testing for multimodal support",
        "description": "Comprehensive testing:\n- Test text models still work\n- Test image model loading and generation\n- Test error cases\n- Test model switching\n\nDeliverable: Test suite",
        "priority": 1,
        "labels": ["local-ai", "testing", "phase-5"]
    },
    {
        "title": "Update documentation for multimodal support",
        "description": "Update all relevant documentation:\n- Update local-ai/README.md\n- Update apps/local-ai-app/README.md\n- Update local-ai-agent.md persona\n- Add troubleshooting for image models\n\nDeliverable: Updated documentation",
        "priority": 1,
        "labels": ["local-ai", "docs", "phase-5"]
    },
    {
        "title": "Performance testing and optimization",
        "description": "Performance validation:\n- Measure image generation latency\n- Test GPU memory usage\n- Optimize if needed\n- Benchmark against text models\n\nDeliverable: Performance benchmarks",
        "priority": 2,
        "labels": ["local-ai", "testing", "performance", "phase-5"]
    }
]

# Generate IDs and create task objects
task_objects = []
for task in tasks:
    task_id = generate_id(task["title"], existing_ids)
    existing_ids.add(task_id)
    
    task_obj = {
        "id": task_id,
        "title": task["title"],
        "description": task["description"],
        "status": "open",
        "priority": task["priority"],
        "issue_type": "task",
        "created_at": now,
        "updated_at": now,
        "labels": task["labels"],
        "dependencies": [{
            "issue_id": task_id,
            "depends_on_id": epic_id,
            "type": "parent-child",
            "created_at": now,
            "created_by": "script"
        }]
    }
    task_objects.append((task_id, task_obj))

# Write to JSONL file
print(f"Creating epic: {epic_id}")
print(f"Creating {len(task_objects)} tasks...")

with open(beads_file, 'a', encoding='utf-8') as f:
    # Write epic
    f.write(json.dumps(epic) + '\n')
    print(f"  [OK] Epic: {epic_id}")
    
    # Write tasks
    for task_id, task_obj in task_objects:
        f.write(json.dumps(task_obj) + '\n')
        print(f"  [OK] Task: {task_id} - {task_obj['title']}")

print(f"\nDone! Created epic and {len(task_objects)} tasks.")
print(f"Epic ID: {epic_id}")
print(f"\nTo view:")
print(f"  bd show {epic_id}")
print(f"  bd dep tree {epic_id}")

