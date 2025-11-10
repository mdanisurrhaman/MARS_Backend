from transformers import pipeline
from crewai.tools import BaseTool
from collections import Counter
from typing import List, Union

# Load pipelines once at startup
sentiment_pipeline = pipeline(
    "sentiment-analysis", model="tabularisai/multilingual-sentiment-analysis"    #type: ignore
)

emotion_pipeline = pipeline(
    "text-classification", model="boltuix/bert-emotion", top_k=1
)


def analysis_tools(text: str) -> dict:
    """Analyze a single review and return sentiment + primary emotion."""
    if not text.strip():
        return {"Sentiment": "neutral", "Emotion": "unknown"}

    sentiment_result = sentiment_pipeline(text)
    emotion_result = emotion_pipeline(text)

    sentiment = (
        sentiment_result[0] if sentiment_result else {"label": "neutral", "score": 0.0}
    )

    if emotion_result and isinstance(emotion_result[0], list) and emotion_result[0]:
        emotion = emotion_result[0][0]
    elif emotion_result and isinstance(emotion_result[0], dict):
        emotion = emotion_result[0]
    else:
        emotion = {"label": "unknown", "score": 0.0}

    return {"Sentiment": sentiment["label"], "Emotion": emotion["label"]}


def summarize_results(results: list) -> dict:
    """Aggregate sentiments and emotions from all reviews."""
    sentiments = [r["Sentiment"] for r in results]
    emotions = [r["Emotion"] for r in results]

    sentiment_counts = Counter(sentiments)
    emotion_counts = Counter(emotions)

    total = len(results) if results else 1  # avoid division by zero

    pos_pct = (
        (sentiment_counts.get("Positive", 0) + sentiment_counts.get("Very Positive", 0))
        / total
    ) * 100
    neg_pct = (
        (sentiment_counts.get("Negative", 0) + sentiment_counts.get("Very Negative", 0))
        / total
    ) * 100
    neutral_pct = (sentiment_counts.get("Neutral", 0) / total) * 100

    top_emotion = [emotion for emotion, _ in emotion_counts.most_common(3)]

    return {
        "positive_percent": round(pos_pct, 2),
        "negative_percent": round(neg_pct, 2),
        "neutral_percent": round(neutral_pct, 2),
        "dominant_emotion": top_emotion,
    }


class AnalyzeReviewsTool(BaseTool):
    name: str = "analyze_reviews"
    description: str = (
        "Analyzes a list of customer reviews and returns sentiment percentages "
        "and top 3 dominant emotions. Input must be a list of strings or a newline-separated string."
    )

    def _run(self, reviews: Union[List[str], str]) -> dict:
        """Run the tool synchronously."""
        if isinstance(reviews, str):
            reviews = [line.strip() for line in reviews.split("\n") if line.strip()]

        if not isinstance(reviews, list) or not reviews:
            return {"error": "No valid reviews provided."}

        sentiments = [analysis_tools(review) for review in reviews]
        return summarize_results(sentiments)

    async def _arun(self, reviews: Union[List[str], str]) -> dict:
        """Run the tool asynchronously."""
        return self._run(reviews)
