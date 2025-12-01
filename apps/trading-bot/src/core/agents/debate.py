"""
Debate Room (T8: Bull vs Bear Debate System)
=============================================

Implements a structured debate between bullish and bearish perspectives
on a trading opportunity. Analysts are assigned to teams based on their
analysis, then argue their positions through multiple rounds.

The debate produces a final verdict with confidence adjustment based on
argument quality and rebuttal effectiveness.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .base import (
    AnalystAgent,
    AnalystRecommendation,
    AnalystReport,
    SignalStrength,
)
from .registry import AggregatedAnalysis, get_analyst_registry

logger = logging.getLogger(__name__)


class DebatePosition(Enum):
    """Position in the debate"""
    BULL = "bull"
    BEAR = "bear"
    NEUTRAL = "neutral"


class ArgumentType(Enum):
    """Type of argument in debate"""
    OPENING = "opening"
    REBUTTAL = "rebuttal"
    CLOSING = "closing"


class VerdictType(Enum):
    """Final verdict of debate"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"
    NO_CONSENSUS = "no_consensus"


@dataclass
class DebateArgument:
    """Single argument in a debate"""
    id: str
    round_number: int
    position: DebatePosition
    argument_type: ArgumentType
    analyst_name: str
    analyst_type: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Content
    main_point: str = ""
    supporting_factors: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)

    # Strength metrics
    conviction_score: float = 0.5  # 0-1, how strongly argued
    evidence_quality: float = 0.5  # 0-1, quality of supporting data

    # Response to opposing argument (for rebuttals)
    responding_to: Optional[str] = None  # ID of argument being rebutted
    rebuttal_effectiveness: float = 0.0  # 0-1, how well it counters

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "round_number": self.round_number,
            "position": self.position.value,
            "argument_type": self.argument_type.value,
            "analyst_name": self.analyst_name,
            "analyst_type": self.analyst_type,
            "timestamp": self.timestamp.isoformat(),
            "main_point": self.main_point,
            "supporting_factors": self.supporting_factors,
            "evidence": self.evidence,
            "conviction_score": self.conviction_score,
            "evidence_quality": self.evidence_quality,
            "responding_to": self.responding_to,
            "rebuttal_effectiveness": self.rebuttal_effectiveness,
        }


@dataclass
class DebateRound:
    """Single round of debate"""
    round_number: int
    round_type: ArgumentType
    bull_arguments: List[DebateArgument] = field(default_factory=list)
    bear_arguments: List[DebateArgument] = field(default_factory=list)

    # Round scoring
    bull_score: float = 0.0
    bear_score: float = 0.0
    round_winner: Optional[DebatePosition] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_number": self.round_number,
            "round_type": self.round_type.value,
            "bull_arguments": [a.to_dict() for a in self.bull_arguments],
            "bear_arguments": [a.to_dict() for a in self.bear_arguments],
            "bull_score": self.bull_score,
            "bear_score": self.bear_score,
            "round_winner": self.round_winner.value if self.round_winner else None,
        }


@dataclass
class DebateVerdict:
    """Final verdict from debate"""
    verdict: VerdictType
    confidence: float  # 0-1

    # Scoring breakdown
    bull_total_score: float = 0.0
    bear_total_score: float = 0.0
    margin: float = 0.0  # How decisive the win was

    # Reasoning
    summary: str = ""
    key_bull_points: List[str] = field(default_factory=list)
    key_bear_points: List[str] = field(default_factory=list)
    decisive_factors: List[str] = field(default_factory=list)

    # Recommendation
    recommended_action: str = ""
    risk_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "confidence": self.confidence,
            "bull_total_score": self.bull_total_score,
            "bear_total_score": self.bear_total_score,
            "margin": self.margin,
            "summary": self.summary,
            "key_bull_points": self.key_bull_points,
            "key_bear_points": self.key_bear_points,
            "decisive_factors": self.decisive_factors,
            "recommended_action": self.recommended_action,
            "risk_notes": self.risk_notes,
        }


@dataclass
class DebateRecord:
    """Complete record of a debate session"""
    id: str
    symbol: str
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None

    # Participants
    bull_team: List[str] = field(default_factory=list)  # Analyst names
    bear_team: List[str] = field(default_factory=list)
    neutral_analysts: List[str] = field(default_factory=list)

    # Input analysis
    initial_analysis: Optional[AggregatedAnalysis] = None
    analyst_reports: List[AnalystReport] = field(default_factory=list)

    # Debate content
    rounds: List[DebateRound] = field(default_factory=list)
    total_arguments: int = 0

    # Output
    verdict: Optional[DebateVerdict] = None

    # Status
    status: str = "pending"  # pending, in_progress, completed, error
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "bull_team": self.bull_team,
            "bear_team": self.bear_team,
            "neutral_analysts": self.neutral_analysts,
            "rounds": [r.to_dict() for r in self.rounds],
            "total_arguments": self.total_arguments,
            "verdict": self.verdict.to_dict() if self.verdict else None,
            "status": self.status,
            "error_message": self.error_message,
        }


class DebateRoom:
    """
    Orchestrates bull vs bear debates on trading opportunities.

    Process:
    1. Receive analyst reports for a symbol
    2. Assign analysts to bull/bear teams based on their recommendations
    3. Run multiple debate rounds (opening, rebuttal, closing)
    4. Score arguments and determine winner
    5. Produce final verdict with confidence adjustment
    """

    def __init__(
        self,
        num_rounds: int = 3,
        min_analysts_per_side: int = 1,
    ):
        """
        Initialize debate room.

        Args:
            num_rounds: Number of debate rounds (opening + rebuttals + closing)
            min_analysts_per_side: Minimum analysts needed per side to debate
        """
        self.num_rounds = num_rounds
        self.min_analysts_per_side = min_analysts_per_side
        self._debate_history: List[DebateRecord] = []

        logger.info("DebateRoom initialized (T8: Bull vs Bear Debate)")

    async def conduct_debate(
        self,
        symbol: str,
        analysis: Optional[AggregatedAnalysis] = None,
        reports: Optional[List[AnalystReport]] = None,
    ) -> DebateRecord:
        """
        Conduct a full debate on a symbol.

        Args:
            symbol: Trading symbol
            analysis: Optional pre-computed aggregated analysis
            reports: Optional list of analyst reports

        Returns:
            Complete DebateRecord with all rounds and verdict
        """
        debate_id = str(uuid.uuid4())[:8]
        record = DebateRecord(
            id=debate_id,
            symbol=symbol.upper(),
            status="in_progress",
        )

        try:
            # Get analysis if not provided
            if analysis is None or reports is None:
                from .registry import run_all_analysts
                analysis = await run_all_analysts(symbol)
                reports = analysis.reports

            record.initial_analysis = analysis
            record.analyst_reports = reports

            # Assign teams
            bull_team, bear_team, neutral = self._assign_teams(reports)
            record.bull_team = [r.analyst_name for r in bull_team]
            record.bear_team = [r.analyst_name for r in bear_team]
            record.neutral_analysts = [r.analyst_name for r in neutral]

            # Check if we have enough participants
            if len(bull_team) < self.min_analysts_per_side or len(bear_team) < self.min_analysts_per_side:
                # Not enough for debate - return consensus verdict
                record.verdict = self._create_consensus_verdict(analysis, bull_team, bear_team)
                record.status = "completed"
                record.ended_at = datetime.now()
                self._debate_history.append(record)
                return record

            # Run debate rounds
            round_types = self._get_round_types()

            for round_num, round_type in enumerate(round_types, 1):
                debate_round = await self._run_round(
                    round_num=round_num,
                    round_type=round_type,
                    bull_team=bull_team,
                    bear_team=bear_team,
                    previous_rounds=record.rounds,
                )
                record.rounds.append(debate_round)
                record.total_arguments += len(debate_round.bull_arguments) + len(debate_round.bear_arguments)

            # Determine verdict
            record.verdict = self._determine_verdict(record)
            record.status = "completed"
            record.ended_at = datetime.now()

        except Exception as e:
            logger.error(f"Debate error for {symbol}: {e}", exc_info=True)
            record.status = "error"
            record.error_message = str(e)
            record.ended_at = datetime.now()

        # Store in history
        self._debate_history.append(record)

        # Broadcast via WebSocket
        await self._broadcast_debate(record)

        return record

    def _assign_teams(
        self, reports: List[AnalystReport]
    ) -> Tuple[List[AnalystReport], List[AnalystReport], List[AnalystReport]]:
        """Assign analysts to bull/bear teams based on their recommendations"""
        bull_team = []
        bear_team = []
        neutral = []

        for report in reports:
            if report.is_bullish():
                bull_team.append(report)
            elif report.is_bearish():
                bear_team.append(report)
            else:
                neutral.append(report)

        # Sort by conviction (confidence * signal strength)
        bull_team.sort(key=lambda r: r.confidence_score * abs(r.directional_bias), reverse=True)
        bear_team.sort(key=lambda r: r.confidence_score * abs(r.directional_bias), reverse=True)

        return bull_team, bear_team, neutral

    def _get_round_types(self) -> List[ArgumentType]:
        """Get round types based on num_rounds"""
        if self.num_rounds == 1:
            return [ArgumentType.OPENING]
        elif self.num_rounds == 2:
            return [ArgumentType.OPENING, ArgumentType.CLOSING]
        else:
            # 3+ rounds: opening, rebuttals, closing
            types = [ArgumentType.OPENING]
            for _ in range(self.num_rounds - 2):
                types.append(ArgumentType.REBUTTAL)
            types.append(ArgumentType.CLOSING)
            return types

    async def _run_round(
        self,
        round_num: int,
        round_type: ArgumentType,
        bull_team: List[AnalystReport],
        bear_team: List[AnalystReport],
        previous_rounds: List[DebateRound],
    ) -> DebateRound:
        """Run a single debate round"""
        debate_round = DebateRound(
            round_number=round_num,
            round_type=round_type,
        )

        # Generate arguments for both sides
        for report in bull_team:
            arg = self._generate_argument(
                report=report,
                round_num=round_num,
                round_type=round_type,
                position=DebatePosition.BULL,
                opposing_args=self._get_opposing_arguments(previous_rounds, DebatePosition.BEAR),
            )
            debate_round.bull_arguments.append(arg)

        for report in bear_team:
            arg = self._generate_argument(
                report=report,
                round_num=round_num,
                round_type=round_type,
                position=DebatePosition.BEAR,
                opposing_args=self._get_opposing_arguments(previous_rounds, DebatePosition.BULL),
            )
            debate_round.bear_arguments.append(arg)

        # Score the round
        debate_round.bull_score = self._score_arguments(debate_round.bull_arguments)
        debate_round.bear_score = self._score_arguments(debate_round.bear_arguments)

        if debate_round.bull_score > debate_round.bear_score:
            debate_round.round_winner = DebatePosition.BULL
        elif debate_round.bear_score > debate_round.bull_score:
            debate_round.round_winner = DebatePosition.BEAR
        # else: tie, no winner

        return debate_round

    def _generate_argument(
        self,
        report: AnalystReport,
        round_num: int,
        round_type: ArgumentType,
        position: DebatePosition,
        opposing_args: List[DebateArgument],
    ) -> DebateArgument:
        """Generate an argument from an analyst report"""
        arg_id = str(uuid.uuid4())[:8]

        # Build main point based on round type
        if round_type == ArgumentType.OPENING:
            main_point = self._build_opening_argument(report, position)
        elif round_type == ArgumentType.REBUTTAL:
            main_point, responding_to = self._build_rebuttal(report, position, opposing_args)
        else:  # CLOSING
            main_point = self._build_closing_argument(report, position)

        # Extract evidence from report metrics
        evidence = {
            "confidence_score": report.confidence_score,
            "directional_bias": report.directional_bias,
            "signal_strength": report.signal_strength.value,
        }
        if report.metrics:
            evidence.update({k: v for k, v in report.metrics.items() if isinstance(v, (int, float, str, bool))})

        arg = DebateArgument(
            id=arg_id,
            round_number=round_num,
            position=position,
            argument_type=round_type,
            analyst_name=report.analyst_name,
            analyst_type=report.analyst_type,
            main_point=main_point,
            supporting_factors=report.key_factors[:3],  # Top 3 factors
            evidence=evidence,
            conviction_score=report.confidence_score,
            evidence_quality=self._assess_evidence_quality(report),
        )

        # Add rebuttal info if applicable
        if round_type == ArgumentType.REBUTTAL and opposing_args:
            arg.responding_to = opposing_args[0].id if opposing_args else None
            arg.rebuttal_effectiveness = self._calculate_rebuttal_effectiveness(arg, opposing_args)

        return arg

    def _build_opening_argument(self, report: AnalystReport, position: DebatePosition) -> str:
        """Build opening argument from report"""
        direction = "bullish" if position == DebatePosition.BULL else "bearish"
        strength = "strongly " if abs(report.directional_bias) > 0.5 else ""

        point = f"{report.analyst_name} ({report.analyst_type}) is {strength}{direction}. "
        point += report.summary

        return point

    def _build_rebuttal(
        self,
        report: AnalystReport,
        position: DebatePosition,
        opposing_args: List[DebateArgument],
    ) -> Tuple[str, Optional[str]]:
        """Build rebuttal argument"""
        if not opposing_args:
            return self._build_opening_argument(report, position), None

        # Find strongest opposing argument to rebut
        strongest_opposing = max(opposing_args, key=lambda a: a.conviction_score)

        # Build rebuttal
        if position == DebatePosition.BULL:
            rebuttal = f"Countering bearish argument from {strongest_opposing.analyst_name}: "
            rebuttal += f"While bears cite {strongest_opposing.supporting_factors[0] if strongest_opposing.supporting_factors else 'their analysis'}, "
            rebuttal += f"bullish indicators show {report.key_factors[0] if report.key_factors else 'positive momentum'}. "
        else:
            rebuttal = f"Countering bullish argument from {strongest_opposing.analyst_name}: "
            rebuttal += f"Despite bulls citing {strongest_opposing.supporting_factors[0] if strongest_opposing.supporting_factors else 'their analysis'}, "
            rebuttal += f"risk factors include {report.warnings[0] if report.warnings else 'caution signals'}. "

        rebuttal += report.summary

        return rebuttal, strongest_opposing.id

    def _build_closing_argument(self, report: AnalystReport, position: DebatePosition) -> str:
        """Build closing argument"""
        direction = "buy" if position == DebatePosition.BULL else "sell/avoid"

        closing = f"In conclusion, {report.analyst_name} recommends to {direction}. "
        closing += f"Key factors: {', '.join(report.key_factors[:2]) if report.key_factors else report.summary}. "
        closing += f"Confidence: {report.confidence_score * 100:.0f}%"

        return closing

    def _get_opposing_arguments(
        self,
        previous_rounds: List[DebateRound],
        position: DebatePosition,
    ) -> List[DebateArgument]:
        """Get arguments from opposing side from previous rounds"""
        args = []
        for round in previous_rounds:
            if position == DebatePosition.BULL:
                args.extend(round.bull_arguments)
            else:
                args.extend(round.bear_arguments)
        return args

    def _assess_evidence_quality(self, report: AnalystReport) -> float:
        """Assess quality of evidence in a report"""
        quality = 0.3  # Base quality

        # More key factors = better evidence
        quality += min(0.2, len(report.key_factors) * 0.05)

        # Metrics provide quantitative backing
        if report.metrics:
            quality += min(0.2, len(report.metrics) * 0.02)

        # Higher confidence from analyst = better evidence
        quality += report.confidence_score * 0.2

        # Warnings show balanced analysis
        if report.warnings:
            quality += 0.1

        return min(1.0, quality)

    def _calculate_rebuttal_effectiveness(
        self,
        rebuttal: DebateArgument,
        opposing_args: List[DebateArgument],
    ) -> float:
        """Calculate how effectively a rebuttal counters opposing arguments"""
        if not opposing_args:
            return 0.0

        # Find the argument being rebutted
        target = next((a for a in opposing_args if a.id == rebuttal.responding_to), opposing_args[0])

        # Effectiveness based on relative conviction and evidence quality
        conviction_ratio = rebuttal.conviction_score / max(0.1, target.conviction_score)
        evidence_ratio = rebuttal.evidence_quality / max(0.1, target.evidence_quality)

        effectiveness = (conviction_ratio * 0.5 + evidence_ratio * 0.5)
        return min(1.0, effectiveness)

    def _score_arguments(self, arguments: List[DebateArgument]) -> float:
        """Score a list of arguments"""
        if not arguments:
            return 0.0

        total_score = 0.0
        for arg in arguments:
            # Base score from conviction and evidence
            score = (arg.conviction_score * 0.4 + arg.evidence_quality * 0.4)

            # Bonus for effective rebuttals
            if arg.argument_type == ArgumentType.REBUTTAL:
                score += arg.rebuttal_effectiveness * 0.2

            total_score += score

        return total_score / len(arguments)

    def _determine_verdict(self, record: DebateRecord) -> DebateVerdict:
        """Determine final verdict from debate record"""
        # Sum up scores from all rounds
        bull_total = sum(r.bull_score for r in record.rounds)
        bear_total = sum(r.bear_score for r in record.rounds)

        # Count round wins
        bull_wins = sum(1 for r in record.rounds if r.round_winner == DebatePosition.BULL)
        bear_wins = sum(1 for r in record.rounds if r.round_winner == DebatePosition.BEAR)

        # Determine winner
        margin = abs(bull_total - bear_total)

        # Collect key points
        key_bull_points = []
        key_bear_points = []
        for round in record.rounds:
            for arg in round.bull_arguments:
                if arg.supporting_factors:
                    key_bull_points.extend(arg.supporting_factors[:1])
            for arg in round.bear_arguments:
                if arg.supporting_factors:
                    key_bear_points.extend(arg.supporting_factors[:1])

        # Determine verdict
        if margin < 0.1:
            verdict_type = VerdictType.NO_CONSENSUS
            confidence = 0.3
            summary = "Debate ended in near-tie. Bulls and bears presented equally compelling arguments."
            action = "HOLD - Wait for clearer signals"
        elif bull_total > bear_total:
            confidence = min(0.9, 0.5 + margin)
            if margin > 0.3:
                verdict_type = VerdictType.STRONG_BUY
                summary = f"Bulls won decisively ({bull_wins}/{len(record.rounds)} rounds). Strong bullish case."
                action = "BUY with conviction"
            else:
                verdict_type = VerdictType.BUY
                summary = f"Bulls edged out bears ({bull_wins}/{len(record.rounds)} rounds). Moderate bullish case."
                action = "BUY with caution"
        else:
            confidence = min(0.9, 0.5 + margin)
            if margin > 0.3:
                verdict_type = VerdictType.STRONG_SELL
                summary = f"Bears won decisively ({bear_wins}/{len(record.rounds)} rounds). Strong bearish case."
                action = "SELL or AVOID"
            else:
                verdict_type = VerdictType.SELL
                summary = f"Bears edged out bulls ({bear_wins}/{len(record.rounds)} rounds). Moderate bearish case."
                action = "SELL or reduce position"

        # Identify decisive factors
        decisive_factors = []
        if key_bull_points and bull_total > bear_total:
            decisive_factors.append(f"Bull: {key_bull_points[0]}")
        if key_bear_points and bear_total > bull_total:
            decisive_factors.append(f"Bear: {key_bear_points[0]}")

        # Risk notes from warnings
        risk_notes = []
        for report in record.analyst_reports:
            risk_notes.extend(report.warnings[:1])

        return DebateVerdict(
            verdict=verdict_type,
            confidence=confidence,
            bull_total_score=bull_total,
            bear_total_score=bear_total,
            margin=margin,
            summary=summary,
            key_bull_points=list(set(key_bull_points))[:3],
            key_bear_points=list(set(key_bear_points))[:3],
            decisive_factors=decisive_factors[:3],
            recommended_action=action,
            risk_notes=list(set(risk_notes))[:3],
        )

    def _create_consensus_verdict(
        self,
        analysis: AggregatedAnalysis,
        bull_team: List[AnalystReport],
        bear_team: List[AnalystReport],
    ) -> DebateVerdict:
        """Create verdict when there's not enough for a debate (one-sided)"""
        if len(bull_team) > len(bear_team):
            if analysis.consensus_score > 0.5:
                verdict_type = VerdictType.STRONG_BUY
            else:
                verdict_type = VerdictType.BUY
            summary = f"Consensus bullish - {len(bull_team)} analysts agree, no bear opposition."
            action = "BUY - Unanimous bullish sentiment"
        elif len(bear_team) > len(bull_team):
            if analysis.consensus_score < -0.5:
                verdict_type = VerdictType.STRONG_SELL
            else:
                verdict_type = VerdictType.SELL
            summary = f"Consensus bearish - {len(bear_team)} analysts agree, no bull opposition."
            action = "SELL - Unanimous bearish sentiment"
        else:
            verdict_type = VerdictType.HOLD
            summary = "No clear consensus among analysts."
            action = "HOLD - Insufficient conviction"

        return DebateVerdict(
            verdict=verdict_type,
            confidence=analysis.consensus_confidence,
            bull_total_score=len(bull_team),
            bear_total_score=len(bear_team),
            margin=abs(len(bull_team) - len(bear_team)),
            summary=summary,
            recommended_action=action,
        )

    async def _broadcast_debate(self, record: DebateRecord):
        """Broadcast debate result via WebSocket"""
        try:
            from ..api.websocket import get_websocket_manager

            manager = get_websocket_manager()
            if manager:
                ws_data = {
                    "type": "debate",
                    "channel": "debate",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "id": record.id,
                        "symbol": record.symbol,
                        "status": record.status,
                        "verdict": record.verdict.to_dict() if record.verdict else None,
                        "bull_team": record.bull_team,
                        "bear_team": record.bear_team,
                        "rounds_count": len(record.rounds),
                        "total_arguments": record.total_arguments,
                    }
                }

                try:
                    loop = asyncio.get_running_loop()
                    asyncio.create_task(manager.broadcast("debate", ws_data))
                except RuntimeError:
                    pass

        except Exception as e:
            logger.debug(f"Error broadcasting debate: {e}")

    def get_history(self, limit: int = 50) -> List[DebateRecord]:
        """Get debate history"""
        return self._debate_history[-limit:]

    def get_debate(self, debate_id: str) -> Optional[DebateRecord]:
        """Get specific debate by ID"""
        for record in self._debate_history:
            if record.id == debate_id:
                return record
        return None


# Global debate room instance
_debate_room: Optional[DebateRoom] = None


def get_debate_room() -> DebateRoom:
    """Get or create global DebateRoom instance"""
    global _debate_room
    if _debate_room is None:
        _debate_room = DebateRoom()
    return _debate_room


async def conduct_debate(
    symbol: str,
    analysis: Optional[AggregatedAnalysis] = None,
) -> DebateRecord:
    """Conduct a debate on a symbol"""
    room = get_debate_room()
    return await room.conduct_debate(symbol, analysis)
