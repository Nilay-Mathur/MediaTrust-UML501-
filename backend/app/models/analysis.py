import datetime
import json
from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from app.database.session import Base

class AnalysisRecord(Base):
    __tablename__ = "analyses"

    id = Column(String(64), primary_key=True, index=True)
    input_type = Column(String(32), nullable=False, index=True)
    status = Column(String(32), default="completed", index=True)
    overall_risk = Column(String(32), nullable=False, index=True)  # low, moderate, high, critical
    risk_score = Column(Integer, nullable=False)  # 0 to 100
    score_type = Column(String(64), default="heuristic_risk_score")
    classification_tag = Column(String(64), default="normal", nullable=True)
    classification_label = Column(String(128), default="No strong threat indicators in scanned content", nullable=True)
    confidence = Column(Float, nullable=True)
    summary = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=True, index=True)
    source_reference = Column(String(256), nullable=True)

    # JSON stored as text for maximum SQLite / PostgreSQL portability
    _findings = Column("findings", Text, default="[]")
    _detector_results = Column("detector_results", Text, default="{}")
    _limitations = Column("limitations", Text, default="[]")
    _recommended_actions = Column("recommended_actions", Text, default="[]")
    _model_versions = Column("model_versions", Text, default="{}")

    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    @property
    def findings(self):
        return json.loads(self._findings) if self._findings else []

    @findings.setter
    def findings(self, value):
        self._findings = json.dumps(value)

    @property
    def detector_results(self):
        return json.loads(self._detector_results) if self._detector_results else {}

    @detector_results.setter
    def detector_results(self, value):
        self._detector_results = json.dumps(value)

    @property
    def limitations(self):
        return json.loads(self._limitations) if self._limitations else []

    @limitations.setter
    def limitations(self, value):
        self._limitations = json.dumps(value)

    @property
    def recommended_actions(self):
        return json.loads(self._recommended_actions) if self._recommended_actions else []

    @recommended_actions.setter
    def recommended_actions(self, value):
        self._recommended_actions = json.dumps(value)

    @property
    def model_versions(self):
        return json.loads(self._model_versions) if self._model_versions else {}

    @model_versions.setter
    def model_versions(self, value):
        self._model_versions = json.dumps(value)
