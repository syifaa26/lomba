"""Fatigue state machine determining driver alertness state.

Transitions between NORMAL, WARNING_FATIGUE, and CRITICAL_DROWSY based on
continuous eye closure duration and cumulative yawn frequency.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any

from config import settings
from core.detector import DetectionResult

logger = logging.getLogger(__name__)


class DriverState(str, Enum):
    """Driver alertness state classification."""

    NORMAL = "NORMAL"
    WARNING_FATIGUE = "WARNING_FATIGUE"
    CRITICAL_DROWSY = "CRITICAL_DROWSY"


@dataclass
class StateOutput:
    """Output summary emitted by FatigueStateMachine on each frame update."""

    state: DriverState
    incident_triggered: bool = False
    incident_type: str | None = None
    confidence_score: float = 0.0
    duration_seconds: float = 0.0
    yawn_count_in_window: int = 0
    consecutive_drowsy_sec: float = 0.0


class FatigueStateMachine:
    """Pure logic state machine tracking driver drowsiness and yawning patterns."""

    def __init__(
        self,
        blink_threshold: float = settings.BLINK_THRESHOLD,
        yawn_threshold: float = settings.YAWN_THRESHOLD,
        drowsy_time_sec: float = settings.DROWSY_TIME_SEC,
        yawn_time_sec: float = settings.YAWN_TIME_SEC,
        yawn_count_trigger: int = settings.YAWN_COUNT_TRIGGER,
        yawn_window_sec: float = settings.YAWN_WINDOW_SEC,
    ) -> None:
        """Initialize thresholds and internal timer states."""
        self.blink_threshold: float = blink_threshold
        self.yawn_threshold: float = yawn_threshold
        self.drowsy_time_sec: float = drowsy_time_sec
        self.yawn_time_sec: float = yawn_time_sec
        self.yawn_count_trigger: int = yawn_count_trigger
        self.yawn_window_sec: float = yawn_window_sec

        self.current_state: DriverState = DriverState.NORMAL

        # Eyes-closed continuous timer
        self._eyes_closed_start: float | None = None
        self._critical_incident_emitted: bool = False

        # Yawn cycle timer and history within window
        self._yawn_start: float | None = None
        self._yawn_recorded_current_cycle: bool = False
        self._yawn_history: deque[float] = deque()
        self._warning_incident_emitted: bool = False

    def update(
        self,
        detection: DetectionResult,
        current_time: float | None = None,
    ) -> StateOutput:
        """Process detection result and transition state accordingly.

        Args:
            detection: Driver face detection scores for current frame.
            current_time: Optional explicit timestamp for deterministic testing.

        Returns:
            StateOutput containing current state and any new incident trigger.
        """
        now: float = current_time if current_time is not None else time.time()

        # If no face is detected, reset continuous timers
        if not detection.face_detected:
            self._eyes_closed_start = None
            self._yawn_start = None
            self._yawn_recorded_current_cycle = False
            self._critical_incident_emitted = False
            self._prune_yawns(now)
            return StateOutput(
                state=self.current_state,
                yawn_count_in_window=len(self._yawn_history),
            )

        # 1. Evaluate Eyes Closure (Microsleep / Drowsiness)
        closed_duration: float = 0.0
        if detection.drowsy_confidence >= self.blink_threshold:
            if self._eyes_closed_start is None:
                self._eyes_closed_start = now
            closed_duration = now - self._eyes_closed_start
        else:
            self._eyes_closed_start = None
            self._critical_incident_emitted = False

        # 2. Evaluate Yawning
        if detection.yawn_confidence >= self.yawn_threshold:
            if self._yawn_start is None:
                self._yawn_start = now
                self._yawn_recorded_current_cycle = False
            yawn_duration = now - self._yawn_start

            # Record qualifying yawn once duration threshold is reached
            if (
                yawn_duration >= self.yawn_time_sec
                and not self._yawn_recorded_current_cycle
            ):
                self._yawn_history.append(now)
                self._yawn_recorded_current_cycle = True
                logger.info(
                    "Qualifying yawn recorded (%.2fs). Total in window: %d",
                    yawn_duration,
                    len(self._yawn_history),
                )
        else:
            self._yawn_start = None
            self._yawn_recorded_current_cycle = False

        # 3. Prune yawns outside sliding time window
        self._prune_yawns(now)

        # 4. State Determination and Incident Triggers
        incident_triggered: bool = False
        incident_type: str | None = None
        confidence_score: float = 0.0
        duration_seconds: float = 0.0

        if closed_duration >= self.drowsy_time_sec:
            new_state = DriverState.CRITICAL_DROWSY
            if not self._critical_incident_emitted:
                incident_triggered = True
                incident_type = DriverState.CRITICAL_DROWSY.value
                confidence_score = detection.drowsy_confidence
                duration_seconds = closed_duration
                self._critical_incident_emitted = True
                logger.warning(
                    "STATE TRANSITION: CRITICAL_DROWSY (eyes closed for %.2fs)",
                    closed_duration,
                )
        elif len(self._yawn_history) >= self.yawn_count_trigger:
            new_state = DriverState.WARNING_FATIGUE
            if not self._warning_incident_emitted:
                incident_triggered = True
                incident_type = DriverState.WARNING_FATIGUE.value
                confidence_score = detection.yawn_confidence
                duration_seconds = self.yawn_time_sec
                self._warning_incident_emitted = True
                logger.warning(
                    "STATE TRANSITION: WARNING_FATIGUE (%d yawns in 10m window)",
                    len(self._yawn_history),
                )
        else:
            new_state = DriverState.NORMAL
            if len(self._yawn_history) < self.yawn_count_trigger:
                self._warning_incident_emitted = False

        self.current_state = new_state

        return StateOutput(
            state=self.current_state,
            incident_triggered=incident_triggered,
            incident_type=incident_type,
            confidence_score=confidence_score,
            duration_seconds=round(duration_seconds, 2),
            yawn_count_in_window=len(self._yawn_history),
            consecutive_drowsy_sec=round(closed_duration, 2),
        )

    def _prune_yawns(self, current_time: float) -> None:
        """Remove yawn events outside the sliding time window."""
        cutoff: float = current_time - self.yawn_window_sec
        while self._yawn_history and self._yawn_history[0] < cutoff:
            self._yawn_history.popleft()

    def reset(self) -> None:
        """Reset all internal state timers and history."""
        self.current_state = DriverState.NORMAL
        self._eyes_closed_start = None
        self._critical_incident_emitted = False
        self._yawn_start = None
        self._yawn_recorded_current_cycle = False
        self._yawn_history.clear()
        self._warning_incident_emitted = False
        logger.info("FatigueStateMachine state reset to NORMAL.")

