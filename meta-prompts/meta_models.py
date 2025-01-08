from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class FrameworkConfig(BaseModel):
    frontend: List[str] = Field(default_factory=list)
    backend: List[str] = Field(default_factory=list)
    ml: List[str] = Field(default_factory=list)
    ai: List[str] = Field(default_factory=list)


class Environment(BaseModel):
    python_version: str
    node_version: str
    cuda_support: bool


class BasicInfo(BaseModel):
    name: str
    version: str
    language: str
    frameworks: FrameworkConfig
    type: str
    environment: Environment


class CodeStyle(BaseModel):
    prefer: List[str] = Field(default_factory=list)
    avoid: List[str] = Field(default_factory=list)


class ErrorHandling(BaseModel):
    strategies: List[str] = Field(default_factory=list)
    logging: List[str] = Field(default_factory=list)


class Performance(BaseModel):
    optimization: List[str] = Field(default_factory=list)
    memory_management: List[str] = Field(default_factory=list)


class CodeGeneration(BaseModel):
    style: CodeStyle
    error_handling: ErrorHandling
    performance: Performance


class LLMIntegration(BaseModel):
    providers: List[str] = Field(default_factory=list)
    model_configurations: List[str] = Field(default_factory=list)


class AgentSystem(BaseModel):
    architecture: str
    communication: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)


class MLPipeline(BaseModel):
    frameworks: List[str] = Field(default_factory=list)
    data_processing: List[str] = Field(default_factory=list)
    model_management: List[str] = Field(default_factory=list)


class AISpecific(BaseModel):
    llm_integration: LLMIntegration
    agent_system: AgentSystem
    ml_pipeline: MLPipeline


class AIBehavior(BaseModel):
    code_generation: CodeGeneration
    ai_specific: AISpecific


class TestingCoverage(BaseModel):
    threshold: float
    excludes: List[str] = Field(default_factory=list)


class Testing(BaseModel):
    frameworks: List[str] = Field(default_factory=list)
    coverage: TestingCoverage
    types: List[str] = Field(default_factory=list)


class Documentation(BaseModel):
    style: str
    required_sections: List[str] = Field(default_factory=list)
    api_documentation: bool


class CodeQuality(BaseModel):
    linters: List[str] = Field(default_factory=list)
    formatters: List[str] = Field(default_factory=list)
    metrics: List[str] = Field(default_factory=list)


class DevelopmentStandards(BaseModel):
    testing: Testing
    documentation: Documentation
    code_quality: CodeQuality


class ProjectInfo(BaseModel):
    name: str
    description: str
    objectives: List[str] = Field(default_factory=list)
    architecture: str
    team_structure: List[str] = Field(default_factory=list)
    development_process: str


class ProjectAnalysis(BaseModel):
    basic_info: BasicInfo
    ai_behavior: AIBehavior
    development_standards: DevelopmentStandards


class CursorRules(BaseModel):
    """Root model for .cursorrules configuration"""
    name: str = Field(default=".cursorrules")
    version: str
    last_updated: datetime = Field(default_factory=datetime.now)
    project_analysis: ProjectAnalysis
    project_info: dict = Field(...)

    class Config:
        json_schema_extra = {
            "example": {
                "name": ".cursorrules",
                "version": "1.0.0",
                "last_updated": "2025-01-05T12:00:00Z",
                "project_analysis": {
                    "basic_info": {
                        "name": "ExampleProject",
                        "version": "1.0.0",
                        "language": "python",
                        "frameworks": {
                            "frontend": [],
                            "backend": ["fastapi"],
                            "ml": ["langchain"],
                            "ai": ["openai"]
                        },
                        "type": "ai-agent",
                        "environment": {
                            "python_version": "3.9",
                            "node_version": "N/A",
                            "cuda_support": False
                        }
                    }
                }
            }
        }

    @classmethod
    def model_validate(cls, obj):
        """Additional validation for CursorRules model"""
        if isinstance(obj, dict):
            if "last_updated" in obj and isinstance(obj["last_updated"], str):
                try:
                    obj["last_updated"] = datetime.fromisoformat(
                        obj["last_updated"].replace("Z", "+00:00")
                    )
                except ValueError as e:
                    raise ValueError(f"Invalid last_updated format: {e}")
        return super().model_validate(obj)
