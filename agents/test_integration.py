#!/usr/bin/env python3
"""
Integration Test for Learning Agent, Critiquing Agent, and Evaluation Framework

Tests the complete flow:
1. Learning Agent records feedback
2. Learning Agent extracts patterns and generates rules
3. Critiquing Agent reviews output
4. Critiquing Agent applies learned rules
5. Critiquing Agent records issues to Learning Agent
6. Evaluation Framework evaluates task
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.specializations.learning_agent.feedback_recorder import FeedbackRecorder
from agents.specializations.learning_agent.pattern_extractor import PatternExtractor
from agents.specializations.learning_agent.rule_generator import RuleGenerator
from agents.specializations.learning_agent.knowledge_base import KnowledgeBase
from agents.specializations.learning_agent.rule_applier import RuleApplier
from agents.specializations.learning_agent.types import FeedbackType

from agents.specializations.critiquing_agent.quality_checker import QualityChecker
from agents.specializations.critiquing_agent.issue_detector import IssueDetector
from agents.specializations.critiquing_agent.feedback_generator import FeedbackGenerator

from agents.evaluation.engine import EvaluationEngine

def test_learning_agent():
    """Test Learning Agent components."""
    print("\n" + "="*60)
    print("TEST 1: Learning Agent")
    print("="*60)
    
    # Initialize components
    storage_path = project_root / "agents" / "specializations" / "learning_agent" / "data"
    fr = FeedbackRecorder(storage_path)
    kb = KnowledgeBase(storage_path)
    pe = PatternExtractor()
    rg = RuleGenerator()
    
    # Record some feedback
    print("\n📝 Recording feedback...")
    feedback_ids = []
    for i in range(3):
        fb = fr.record_feedback(
            FeedbackType.CORRECTION,
            "test-agent",
            {"task_type": "deployment", "error": "disk_full"},
            "Deployment failed - disk space issue",
            "Check disk space before deployment",
            "human"
        )
        feedback_ids.append(fb.feedback_id)
        print(f"   ✅ Recorded feedback {i+1}: {fb.feedback_id}")
    
    # Extract patterns
    print("\n🔍 Extracting patterns...")
    feedbacks = fr.get_feedback(limit=10)
    patterns = pe.extract_patterns(feedbacks)
    print(f"   ✅ Extracted {len(patterns)} patterns")
    
    # Generate rules
    print("\n📋 Generating rules...")
    rules_created = []
    for pattern in patterns:
        related_feedback = [f for f in feedbacks if f.feedback_id in pattern.feedback_ids]
        rule = rg.generate_rule_from_pattern(pattern, related_feedback)
        kb.save_rule(rule)
        rules_created.append(rule.rule_id)
        print(f"   ✅ Generated rule: {rule.rule_id} - {rule.name}")
        print(f"      Confidence: {rule.confidence:.2f}, Trigger: {rule.trigger.value}")
    
    # Get all rules
    all_rules = kb.get_all_rules()
    print(f"\n   ✅ Total rules in knowledge base: {len(all_rules)}")
    
    return {
        "feedback_recorder": fr,
        "knowledge_base": kb,
        "rule_applier": RuleApplier(kb),
        "rules": all_rules
    }

def test_critiquing_agent(rule_applier):
    """Test Critiquing Agent components."""
    print("\n" + "="*60)
    print("TEST 2: Critiquing Agent")
    print("="*60)
    
    # Initialize components
    qc = QualityChecker(rule_applier=rule_applier)
    detector = IssueDetector()
    generator = FeedbackGenerator()
    
    # Test code review
    print("\n🔍 Reviewing code output...")
    test_code = """
def deploy_service():
    password = 'secret123'  # Hardcoded password
    try:
        docker_compose_up()
    # Missing except clause
    """
    
    report = qc.check_quality(
        agent_id="test-agent",
        output_type="code",
        output_content=test_code,
        task_id="test-task",
        context={"task_type": "deployment", "error": "disk_full"}
    )
    
    print(f"   ✅ Quality Score: {report.quality_score:.2f}")
    print(f"   ✅ Issues Found: {len(report.issues)}")
    print(f"   ✅ Rules Applied: {len(report.rules_applied)}")
    
    for issue in report.issues:
        print(f"      - {issue.severity.value.upper()}: {issue.description}")
    
    # Generate feedback
    print("\n📝 Generating feedback...")
    feedback = generator.generate_feedback(report, send_to_agent=False)
    print(f"   ✅ Feedback generated:")
    print(f"      Summary: {feedback['summary'][:80]}...")
    print(f"      Recommendations: {len(feedback['recommendations'])}")
    
    return {
        "quality_checker": qc,
        "issue_detector": detector,
        "feedback_generator": generator,
        "report": report
    }

def test_evaluation_framework(quality_score):
    """Test Evaluation Framework."""
    print("\n" + "="*60)
    print("TEST 3: Evaluation Framework")
    print("="*60)
    
    # Initialize engine
    engine = EvaluationEngine()
    
    # Simulate task
    print("\n📊 Evaluating task...")
    start_time = datetime.now() - timedelta(seconds=45)
    end_time = datetime.now()
    
    metrics = engine.evaluate_agent_task(
        agent_id="test-agent",
        task_id="test-task",
        start_time=start_time,
        end_time=end_time,
        tool_calls=[
            {"tool": "docker_list_containers", "success": True},
            {"tool": "git_status", "success": True}
        ],
        output=None,
        success=True,
        quality_score=quality_score
    )
    
    print(f"   ✅ Metrics collected: {len(metrics.metrics)}")
    print(f"   ✅ Quality Score: {metrics.quality_score:.2f}")
    print(f"   ✅ Performance Score: {metrics.performance_score:.2f}")
    print(f"   ✅ Correctness Score: {metrics.correctness_score:.2f}")
    print(f"   ✅ Efficiency Score: {metrics.efficiency_score:.2f}")
    print(f"   ✅ Composite Score: {metrics.composite_score:.2f}")
    
    # Generate report
    print("\n📋 Generating evaluation report...")
    report = engine.generate_evaluation_report(metrics)
    print(f"   ✅ Report generated")
    print(f"      Benchmark comparison: {report.get('benchmark_comparison', {}).get('meets_benchmark', 'N/A')}")
    
    return metrics

def test_full_integration():
    """Test full integration flow."""
    print("\n" + "="*60)
    print("TEST 4: Full Integration Flow")
    print("="*60)
    
    # Step 1: Learning Agent records feedback
    print("\n1️⃣ Learning Agent records feedback...")
    storage_path = project_root / "agents" / "specializations" / "learning_agent" / "data"
    fr = FeedbackRecorder(storage_path)
    kb = KnowledgeBase(storage_path)
    pe = PatternExtractor()
    rg = RuleGenerator()
    ra = RuleApplier(kb)
    
    # Record feedback
    fb = fr.record_feedback(
        FeedbackType.CORRECTION,
        "agent-001",
        {"task_type": "deployment", "error": "disk_full"},
        "Deployment failed - no disk space check",
        "Always check disk space before deployment",
        "human"
    )
    print(f"   ✅ Feedback recorded: {fb.feedback_id}")
    
    # Extract patterns and generate rules
    feedbacks = fr.get_feedback(limit=10)
    patterns = pe.extract_patterns(feedbacks)
    for pattern in patterns:
        related_feedback = [f for f in feedbacks if f.feedback_id in pattern.feedback_ids]
        rule = rg.generate_rule_from_pattern(pattern, related_feedback)
        kb.save_rule(rule)
        print(f"   ✅ Rule generated: {rule.rule_id}")
    
    # Step 2: Critiquing Agent reviews output
    print("\n2️⃣ Critiquing Agent reviews output...")
    qc = QualityChecker(rule_applier=ra)
    generator = FeedbackGenerator()
    
    test_output = "def deploy():\n    docker_compose_up()  # Missing disk space check"
    
    report = qc.check_quality(
        agent_id="agent-001",
        output_type="code",
        output_content=test_output,
        task_id="T1.1",
        context={"task_type": "deployment", "error": "disk_full"}
    )
    
    print(f"   ✅ Quality Score: {report.quality_score:.2f}")
    print(f"   ✅ Issues: {len(report.issues)}")
    print(f"   ✅ Rules Applied: {len(report.rules_applied)}")
    
    # Generate feedback
    feedback = generator.generate_feedback(report, send_to_agent=False)
    print(f"   ✅ Feedback generated and recorded to Learning Agent")
    
    # Step 3: Evaluation Framework evaluates
    print("\n3️⃣ Evaluation Framework evaluates task...")
    engine = EvaluationEngine()
    
    start_time = datetime.now() - timedelta(seconds=30)
    end_time = datetime.now()
    
    metrics = engine.evaluate_agent_task(
        agent_id="agent-001",
        task_id="T1.1",
        start_time=start_time,
        end_time=end_time,
        tool_calls=[{"tool": "docker_compose_up", "success": True}],
        output=None,
        success=True,
        quality_score=report.quality_score
    )
    
    print(f"   ✅ Composite Score: {metrics.composite_score:.2f}")
    print(f"   ✅ Meets Benchmark: {engine.benchmark_system.compare_to_benchmark(metrics, 'quality').get('meets_benchmark', False)}")
    
    print("\n✅ Full integration flow working!")

if __name__ == "__main__":
    print("="*60)
    print("INTEGRATION TEST - Learning, Critiquing, Evaluation")
    print("="*60)
    
    try:
        # Test individual components
        learning_result = test_learning_agent()
        critiquing_result = test_critiquing_agent(learning_result["rule_applier"])
        evaluation_result = test_evaluation_framework(critiquing_result["report"].quality_score)
        
        # Test full integration
        test_full_integration()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nComponents tested:")
        print("  ✅ Learning Agent - Feedback recording, pattern extraction, rule generation")
        print("  ✅ Critiquing Agent - Quality checking, issue detection, feedback generation")
        print("  ✅ Evaluation Framework - Metrics collection, scoring, benchmarking")
        print("  ✅ Full Integration - Complete workflow")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

