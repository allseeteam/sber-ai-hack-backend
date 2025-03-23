from fastapi import FastAPI
from mcp import StdioServerParameters, types

from .common import models, mcp_client


app = FastAPI()


@app.post("/search_similar_code")
async def search_similar_code(
    request: models.CodeSimilarityRequest,
) -> list[models.CodeSimilarityResult]:
    server_params = StdioServerParameters(
        command="python", args=["servers/function_matcher.py"], env=None
    )
    client = mcp_client.MCPClient(server_params)

    result = await client.call_tool(
        name="search_similar_code", arguments={"request": request}
    )
    content: list[types.TextContent] = result.content

    result = [
        models.CodeSimilarityResult.from_text_content(c) for c in content
    ]

    return result


@app.post("/search_similar_file")
async def search_similar_file(request: models.FileSimilarityRequest) -> list[models.FileSimilarityResult]:
    return [models.FileSimilarityResult(repository_url="", branch="", file_path="", code="")]


@app.post("/search_similar_repository")
async def search_similar_repository(request: models.RepositorySimilarityRequest) -> list[models.RepositorySimilarityResult]:
    return [models.RepositorySimilarityResult]
