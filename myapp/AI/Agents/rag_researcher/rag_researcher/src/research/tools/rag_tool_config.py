tool_config = dict(
    llm=dict(
        provider="google",
        config=dict(
            model="gemini-2.0-flash-lite",
        ),
    ),
    embedder=dict(
        provider="google",
        config=dict(
            model="models/embedding-001",
            task_type="retrieval_document",
        ),
    ),
)