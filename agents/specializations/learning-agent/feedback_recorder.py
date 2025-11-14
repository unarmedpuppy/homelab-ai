"""Record feedback for learning."""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import json
from pathlib import Path
from .types import Feedback, FeedbackType

class FeedbackRecorder:
    """Records feedback for learning."""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.feedback_file = storage_path / "feedback.jsonl"
    
    def record_feedback(
        self,
        feedback_type: FeedbackType,
        agent_id: str,
        context: Dict[str, Any],
        issue: str,
        correction: str,
        provided_by: str,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Feedback:
        """Record feedback."""
        feedback = Feedback(
            feedback_id=f"fb-{uuid.uuid4().hex[:8]}",
            feedback_type=feedback_type,
            agent_id=agent_id,
            task_id=task_id,
            context=context,
            issue=issue,
            correction=correction,
            provided_by=provided_by,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        # Store feedback
        self._store_feedback(feedback)
        
        return feedback
    
    def _store_feedback(self, feedback: Feedback):
        """Store feedback to file."""
        with open(self.feedback_file, "a") as f:
            f.write(json.dumps({
                "feedback_id": feedback.feedback_id,
                "feedback_type": feedback.feedback_type.value,
                "agent_id": feedback.agent_id,
                "task_id": feedback.task_id,
                "context": feedback.context,
                "issue": feedback.issue,
                "correction": feedback.correction,
                "provided_by": feedback.provided_by,
                "timestamp": feedback.timestamp.isoformat(),
                "metadata": feedback.metadata
            }) + "\n")
    
    def get_feedback(
        self,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        feedback_type: Optional[FeedbackType] = None,
        limit: int = 100
    ) -> List[Feedback]:
        """Get feedback matching criteria."""
        feedbacks = []
        
        if not self.feedback_file.exists():
            return feedbacks
        
        with open(self.feedback_file, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                # Filter
                if agent_id and data.get("agent_id") != agent_id:
                    continue
                if task_id and data.get("task_id") != task_id:
                    continue
                if feedback_type and data.get("feedback_type") != feedback_type.value:
                    continue
                
                feedback = Feedback(
                    feedback_id=data["feedback_id"],
                    feedback_type=FeedbackType(data["feedback_type"]),
                    agent_id=data["agent_id"],
                    task_id=data.get("task_id"),
                    context=data["context"],
                    issue=data["issue"],
                    correction=data["correction"],
                    provided_by=data["provided_by"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    metadata=data.get("metadata", {})
                )
                
                feedbacks.append(feedback)
                
                if len(feedbacks) >= limit:
                    break
        
        return feedbacks

