# How to Extend BaseAgent

This guide walks you through creating your own agent by extending the `BaseAgent` class.

## Quick Start

### Minimal Agent Example

```python
from observable_agent_starter import BaseAgent
import dspy

class MySignature(dspy.Signature):
    """Answer a user question."""
    question: str = dspy.InputField()
    answer: str = dspy.OutputField()

class MyAgent(dspy.Module, BaseAgent):
    """Simple Q&A agent with tracing."""

    def __init__(self):
        dspy.Module.__init__(self)
        BaseAgent.__init__(self, observation_name="my-qa-agent")

        self.predict = dspy.ChainOfThought(MySignature)

    def forward(self, question: str):
        result = self.predict(question=question)

        self.log_generation(
            input_data={"question": question},
            output_data={"answer": result.answer}
        )

        return result.answer
```

### Usage

```python
# Set environment variables
export OPENAI_API_KEY=your-key
export LANGFUSE_PUBLIC_KEY=pk-...  # optional
export LANGFUSE_SECRET_KEY=sk-...  # optional

# Use the agent
agent = MyAgent()
answer = agent(question="What is DSPy?")
print(answer)
```

## Step-by-Step Guide

### Step 1: Define Your DSPy Signature

Signatures define the input/output structure:

```python
import dspy

class VideoIdeaSignature(dspy.Signature):
    """Generate video ideas for a content creator."""

    # Inputs
    creator_profile: str = dspy.InputField(
        desc="Creator's audience, niche, and content pillars"
    )
    request: str = dspy.InputField(
        desc="Specific request or theme for video ideas"
    )

    # Outputs
    ideas: list[str] = dspy.OutputField(
        desc="List of 3-5 video ideas with titles and descriptions"
    )
    reasoning: str = dspy.OutputField(
        desc="Explanation of why these ideas fit the creator"
    )
```

**Best Practices:**
- Use descriptive field names
- Add `desc` for better prompting
- Keep inputs focused and outputs structured
- Use type hints for clarity

### Step 2: Create Your Agent Class

```python
from observable_agent_starter import BaseAgent
import dspy

class VideoIdeaAgent(dspy.Module, BaseAgent):
    """Generate video ideas with observability."""

    def __init__(self):
        # Initialize both parent classes
        dspy.Module.__init__(self)
        BaseAgent.__init__(
            self,
            observation_name="video-idea-generator"
        )

        # Your DSPy modules
        self.generate = dspy.ChainOfThought(VideoIdeaSignature)

    def forward(self, creator_profile: str, request: str):
        """Generate video ideas for a creator."""
        # Call DSPy module
        result = self.generate(
            creator_profile=creator_profile,
            request=request
        )

        # Log to Langfuse (optional but recommended)
        self.log_generation(
            input_data={
                "profile": creator_profile,
                "request": request
            },
            output_data={
                "ideas": result.ideas,
                "reasoning": result.reasoning
            },
            metadata={
                "num_ideas": len(result.ideas)
            }
        )

        return result
```

### Step 3: Add Error Handling

```python
def forward(self, creator_profile: str, request: str):
    """Generate video ideas with error handling."""
    try:
        result = self.generate(
            creator_profile=creator_profile,
            request=request
        )

        self.log_generation(
            input_data={"profile": creator_profile, "request": request},
            output_data={"ideas": result.ideas}
        )

        return result

    except Exception as e:
        self.logger.error(f"Generation failed: {e}")

        # Log error to Langfuse
        self.log_generation(
            input_data={"profile": creator_profile, "request": request},
            output_data={"error": str(e)},
            metadata={"error_type": type(e).__name__}
        )

        # Provide fallback or re-raise
        raise
```

### Step 4: Add Validation

```python
import dspy

class CodePatch(dspy.Signature):
    """Generate code for a task."""
    task: str = dspy.InputField()
    filename: str = dspy.OutputField()
    content: str = dspy.OutputField()
    risk_level: str = dspy.OutputField(desc="low, medium, or high")

class CodeAgent(dspy.Module, BaseAgent):
    def __init__(self, allowed_patterns: list[str]):
        dspy.Module.__init__(self)
        BaseAgent.__init__(self, observation_name="code-agent")

        self.allowed_patterns = allowed_patterns
        self.generate = dspy.ChainOfThought(CodePatch)

    def forward(self, task: str):
        result = self.generate(task=task)

        # Validate output
        dspy.Assert(
            self._validate_filename(result.filename),
            f"Filename must match allowed patterns: {self.allowed_patterns}"
        )

        dspy.Assert(
            result.risk_level in ["low", "medium", "high"],
            "Risk level must be low, medium, or high"
        )

        dspy.Assert(
            len(result.content.strip()) > 0,
            "File content cannot be empty"
        )

        self.log_generation(
            input_data={"task": task},
            output_data={"filename": result.filename, "risk": result.risk_level}
        )

        return result

    def _validate_filename(self, filename: str) -> bool:
        import fnmatch
        return any(
            fnmatch.fnmatch(filename, pattern)
            for pattern in self.allowed_patterns
        )
```

## Advanced Patterns

### Multi-Step Reasoning

```python
class ResearchAgent(dspy.Module, BaseAgent):
    def __init__(self):
        dspy.Module.__init__(self)
        BaseAgent.__init__(self, observation_name="research-agent")

        # Multiple DSPy modules
        self.extract_keywords = dspy.ChainOfThought(ExtractKeywords)
        self.search = dspy.ChainOfThought(SearchDocuments)
        self.synthesize = dspy.ChainOfThought(SynthesizeAnswer)

    def forward(self, question: str, documents: list[str]):
        # Step 1: Extract keywords
        keywords = self.extract_keywords(question=question)

        # Step 2: Search documents
        relevant_docs = self.search(
            keywords=keywords.keywords,
            documents=documents
        )

        # Step 3: Synthesize answer
        answer = self.synthesize(
            question=question,
            context=relevant_docs.documents
        )

        # Log the full pipeline
        self.log_generation(
            input_data={"question": question, "num_docs": len(documents)},
            output_data={"answer": answer.text},
            metadata={
                "keywords": keywords.keywords,
                "relevant_docs_count": len(relevant_docs.documents)
            }
        )

        return answer.text
```

### Structured Data Integration

```python
from pydantic import BaseModel

class CreatorProfile(BaseModel):
    name: str
    audience_size: int
    niche: str
    content_pillars: list[str]

class ProfileAgent(dspy.Module, BaseAgent):
    def __init__(self):
        dspy.Module.__init__(self)
        BaseAgent.__init__(self, observation_name="profile-agent")

        self.generate = dspy.ChainOfThought(VideoIdeaSignature)

    def forward(self, profile: CreatorProfile, request: str):
        # Convert structured data to prompt context
        profile_context = self._format_profile(profile)

        result = self.generate(
            creator_profile=profile_context,
            request=request
        )

        self.log_generation(
            input_data={
                "profile": profile.model_dump(),
                "request": request
            },
            output_data={"ideas": result.ideas}
        )

        return result

    def _format_profile(self, profile: CreatorProfile) -> str:
        return f"""
Creator: {profile.name}
Audience: {profile.audience_size:,} subscribers
Niche: {profile.niche}
Content Pillars: {', '.join(profile.content_pillars)}
        """.strip()
```

### Conditional Logic

```python
class RoutingAgent(dspy.Module, BaseAgent):
    def __init__(self):
        dspy.Module.__init__(self)
        BaseAgent.__init__(self, observation_name="routing-agent")

        self.classifier = dspy.Predict(ClassifyIntent)
        self.qa_agent = dspy.ChainOfThought(QuestionAnswering)
        self.task_agent = dspy.ChainOfThought(TaskExecution)

    def forward(self, user_input: str):
        # Classify intent
        intent = self.classifier(input=user_input)

        # Route based on intent
        if intent.category == "question":
            result = self.qa_agent(question=user_input)
        elif intent.category == "task":
            result = self.task_agent(task=user_input)
        else:
            raise ValueError(f"Unknown intent: {intent.category}")

        self.log_generation(
            input_data={"input": user_input},
            output_data={"result": result.output},
            metadata={"intent": intent.category}
        )

        return result
```

## Testing Your Agent

### Unit Tests

```python
import pytest
import dspy
from your_agent import VideoIdeaAgent

@pytest.fixture(autouse=True)
def reset_dspy():
    """Reset DSPy between tests."""
    dspy.settings.configure(lm=None)
    yield
    dspy.settings.configure(lm=None)

def test_agent_generates_ideas(monkeypatch):
    """Should generate video ideas."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    agent = VideoIdeaAgent()
    result = agent(
        creator_profile="Tech YouTuber with 100k subs",
        request="AI tutorial ideas"
    )

    assert len(result.ideas) > 0
    assert result.reasoning
```

### Integration Tests

```python
def test_agent_with_langfuse(monkeypatch):
    """Should log to Langfuse when configured."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

    # Mock Langfuse
    from observable_agent_starter import config

    class MockLangfuse:
        def __init__(self, *args, **kwargs):
            self.observations = []

        def start_observation(self, **kwargs):
            self.observations.append(kwargs)
            return self

        def update(self, **kwargs):
            pass

        def end(self):
            pass

        def flush(self):
            pass

    monkeypatch.setattr(config, "Langfuse", MockLangfuse)

    agent = VideoIdeaAgent()
    agent(creator_profile="Test", request="Test")

    # Verify observation was created
    client = config.configure_langfuse_from_env()
    assert len(client.observations) > 0
```

## Best Practices

### 1. Observation Naming

Use descriptive, hierarchical names:

```python
BaseAgent.__init__(self, observation_name="video-ideas-generator")
BaseAgent.__init__(self, observation_name="code-agent-file-creation")
BaseAgent.__init__(self, observation_name="research-document-synthesis")
```

### 2. Structured Logging

Log structured data for better analysis:

```python
self.log_generation(
    input_data={
        "user_id": user.id,
        "query": query,
        "context_size": len(context)
    },
    output_data={
        "response": response,
        "confidence": confidence_score
    },
    metadata={
        "model": "gpt-4",
        "temperature": 0.7,
        "tokens_used": usage.total_tokens
    }
)
```

### 3. Error Recovery

Provide graceful fallbacks:

```python
def forward(self, question: str):
    try:
        result = self.predict(question=question)
        return result.answer
    except Exception as e:
        self.logger.warning(f"Primary model failed: {e}")

        # Fallback to simpler model
        result = self.fallback_predict(question=question)
        return f"[FALLBACK] {result.answer}"
```

### 4. Configuration

Make agents configurable:

```python
class ConfigurableAgent(dspy.Module, BaseAgent):
    def __init__(
        self,
        observation_name: str = "agent",
        temperature: float = 0.7,
        max_retries: int = 3
    ):
        dspy.Module.__init__(self)
        BaseAgent.__init__(self, observation_name=observation_name)

        self.temperature = temperature
        self.max_retries = max_retries
```

## Next Steps

- Review [Architecture Documentation](../architecture.md)
- Check out [Example Implementations](../../examples/)
- Add evaluation metrics with [DeepEval](https://docs.confident-ai.com/)
- Set up Langfuse for [production tracing](https://langfuse.com/docs)

## Common Pitfalls

### 1. Not Calling Both Inits

```python
# Wrong - only one init
class MyAgent(dspy.Module, BaseAgent):
    def __init__(self):
        super().__init__()  # Ambiguous which parent

# Correct - explicit init for both
class MyAgent(dspy.Module, BaseAgent):
    def __init__(self):
        dspy.Module.__init__(self)
        BaseAgent.__init__(self, observation_name="my-agent")
```

### 2. Forgetting to Configure LM

```python
# Your code
agent = MyAgent()
result = agent(question="test")  # May fail if no LM configured

# Better - check configuration
from observable_agent_starter.config import configure_lm_from_env

if not configure_lm_from_env():
    raise RuntimeError("Set OPENAI_API_KEY environment variable")

agent = MyAgent()
result = agent(question="test")
```

### 3. Not Handling Missing Langfuse

Langfuse is optional - your agent should work without it:

```python
# Already handled by BaseAgent.log_generation()
# No need to check if Langfuse is configured
self.log_generation(...)  # Gracefully skips if not configured
```

## Support

- [Open an issue](https://github.com/your-org/observable-agent-starter/issues)
- Review existing [examples](../../examples/)
- Check [DSPy documentation](https://dspy-docs.vercel.app/)
