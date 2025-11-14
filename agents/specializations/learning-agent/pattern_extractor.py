"""Extract patterns from feedback."""

from typing import List, Dict, Any
from datetime import datetime
import uuid
from collections import Counter
from .types import Feedback, Pattern

class PatternExtractor:
    """Extract patterns from feedback."""
    
    def extract_patterns(self, feedbacks: List[Feedback]) -> List[Pattern]:
        """Extract patterns from feedback."""
        patterns = []
        
        # Group by issue type
        issue_groups = {}
        for feedback in feedbacks:
            issue_key = self._normalize_issue(feedback.issue)
            if issue_key not in issue_groups:
                issue_groups[issue_key] = []
            issue_groups[issue_key].append(feedback)
        
        # Create patterns from groups
        for issue_key, group in issue_groups.items():
            if len(group) >= 2:  # Pattern needs at least 2 occurrences
                pattern = Pattern(
                    pattern_id=f"pattern-{uuid.uuid4().hex[:8]}",
                    name=issue_key,
                    description=self._create_description(group),
                    frequency=len(group),
                    feedback_ids=[f.feedback_id for f in group],
                    extracted_at=datetime.now(),
                    confidence=min(len(group) / 10.0, 1.0)  # More occurrences = higher confidence
                )
                patterns.append(pattern)
        
        return patterns
    
    def _normalize_issue(self, issue: str) -> str:
        """Normalize issue description."""
        # Simple normalization - can be enhanced with NLP
        issue_lower = issue.lower()
        
        # Remove common words
        stop_words = ["the", "a", "an", "is", "are", "was", "were", "to", "of", "in", "on", "at", "for", "with"]
        words = [w for w in issue_lower.split() if w not in stop_words]
        
        # Take first few meaningful words
        return " ".join(words[:5])
    
    def _create_description(self, feedbacks: List[Feedback]) -> str:
        """Create pattern description from feedback."""
        # Use most common correction
        corrections = [f.correction for f in feedbacks]
        counter = Counter(corrections)
        most_common = counter.most_common(1)[0][0]
        
        return f"Pattern: {feedbacks[0].issue}. Solution: {most_common}"

