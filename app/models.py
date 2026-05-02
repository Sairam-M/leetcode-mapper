from pydantic import BaseModel, Field

class ProblemRequest(BaseModel):
    problem_statement: str = Field(
        ...,
        min_length=20,
        max_length=2000,
        description="The problem statement to map to a LeetCode equivalent"
    )

class ReasoningOutput(BaseModel):
    pattern: str
    core_constraint: str
    why_it_matches: str
    key_difference: str
    confidence: str

class ProblemResponse(BaseModel):
    leetcode_title: str
    leetcode_link: str
    difficulty: str
    acceptance_rate: float
    topics: str
    reasoning: ReasoningOutput