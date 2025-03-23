from pydantic import BaseModel
from mcp import types


class ProBaseModel(BaseModel):
    @classmethod
    def from_text_content(cls, text_content: types.TextContent):
        return cls.model_validate_json(text_content.text)


class CodeSimilarityRequest(BaseModel):
    code: str
    allow_repositories: list[str]


class FileSimilarityRequest(BaseModel):
    file_url: str
    allow_repositories: list[str]


class RepositorySimilarityRequest(BaseModel):
    repository_url: str
    allow_repositories: list[str]


class CodeSimilarityResult(ProBaseModel):
    repository_url: str
    branch: str
    file_path: str
    code: str | None


class FileSimilarityResult(ProBaseModel):
    repository_url: str
    branch: str
    file_path: str
    code: str | None


class RepositorySimilarityResult(ProBaseModel):
    repository_url: str
    branch: str
    file_path: str
    code: str | None
