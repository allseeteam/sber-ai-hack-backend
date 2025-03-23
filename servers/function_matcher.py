from mcp.server.fastmcp import FastMCP

from common import models


mcp = FastMCP("Function Matcher")


@mcp.tool()
def search_similar_code(
    request: models.CodeSimilarityRequest,
) -> list[models.CodeSimilarityResult]:
    """Поиск функционально похожего кода в репозиториях."""

    return [
        models.CodeSimilarityResult(
            repository_url="repo",
            branch="master",
            file_path="path",
            code="amazing code",
        )
    ]


if __name__ == "__main__":
    mcp.run()
