from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class NewsItem:
    id: str
    title: str
    url: str
    source: str
    summary: str
    published_at: str
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Idea:
    name: str
    pitch: str
    problem: str
    customer: str
    solution: str
    why_now: str
    monetization: str
    first_customers: str
    uniqueness_angle: str
    closest_existing_alternative: str
    why_different: str
    news_trend: str
