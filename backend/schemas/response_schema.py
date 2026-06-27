# backend/schemas/response_schema.py
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class PredictionMatch(BaseModel):
    label: str
    score: float

class ClassificationResponse(BaseModel):
    domain: str
    model_used: str
    prediction: str
    confidence: float
    top_predictions: List[PredictionMatch]
    caption: str
    explanation: str

    model_config = ConfigDict(protected_namespaces=())


class FeedbackRequest(BaseModel):
    domain: str
    predicted_label: str
    true_label: str
    caption: Optional[str] = None


class FeedbackResponse(BaseModel):
    saved: bool
    message: Optional[str] = None
    domain: Optional[str] = None
    true_label: Optional[str] = None
    learned_labels: List[str] = Field(default_factory=list)
