import time
from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass, field
from contextlib import contextmanager
import json
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Metrics:
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def complete(self, success: bool = True, error: Optional[str] = None):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration": self.duration,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata
        }

class MetricsCollector:
    def __init__(self):
        self.metrics: Dict[str, Metrics] = {}

    @contextmanager
    def measure(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        metrics = Metrics(metadata=metadata or {})
        self.metrics[name] = metrics
        try:
            yield metrics
            metrics.complete(success=True)
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        return {name: metrics.to_dict() for name, metrics in self.metrics.items()}

    def log_metrics(self):
        metrics_dict = self.get_metrics()
        logger.info(f"Metrics: {json.dumps(metrics_dict, indent=2)}")

class WorkflowMetrics:
    def __init__(self):
        self.collector = MetricsCollector()

    def measure_activity(self, activity_name: str, metadata: Optional[Dict[str, Any]] = None):
        return self.collector.measure(activity_name, metadata)

    def measure_workflow(self, workflow_id: str, metadata: Optional[Dict[str, Any]] = None):
        return self.collector.measure(f"workflow_{workflow_id}", metadata)

    def get_workflow_metrics(self) -> Dict[str, Dict[str, Any]]:
        return self.collector.get_metrics()

    def log_workflow_metrics(self):
        self.collector.log_metrics() 