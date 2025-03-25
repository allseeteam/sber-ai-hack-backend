import base64
import logging
from typing import Optional, List, Dict, Any, Tuple

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langchain_core.messages import ToolMessage
import httpx

from settings import settings
from sourcebot.sourcebot_client import SourcebotClient, SourcebotApiError

logger = logging.getLogger(__name__)

# Configure API URLs with default values
SEARCH_API_URL = settings.code_search.SEARCH_API_URL
SOURCEBOT_URL = settings.code_search.SOURCEBOT_URL


class ExactSearchQuery(BaseModel):
    """Pydantic model for the exact search query"""

    query: str = Field(description="Поисковый запрос для поиска по кодовой базе")
    allowed_repos: Optional[List[str]] = Field(
        description="Список репозиториев, по которым ведется поиск. Пустой список ('[]') будет означать поиск без ограничений.", default=[]
    )


class SemanticSearchQuery(BaseModel):
    """Pydantic model for the semantic search query"""

    query: str = Field(description="Поисковый запрос для векторного поиска по кодовой базе")
    allowed_repos: Optional[List[str]] = Field(
        description="Список репозиториев, по которым ведется поиск. Пустой список ('[]') будет означать поиск без ограничений.", default=[]
    )


def decode_base64_content(content: str) -> str:
    """Decode Base64 encoded content, returning original string if not Base64"""
    try:
        # Try to decode the content as Base64
        decoded = base64.b64decode(content.encode('utf-8')).decode('utf-8')
        return decoded
    except Exception:
        # If decoding fails, return the original content
        return content


def format_sourcebot_results(result: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Format Sourcebot search results into formatted text and structured data"""
    if not result or not result.get("matches"):
        return "No matching code found.", {"matches": []}

    result_parts = []
    structured_matches = []
    
    for match in result["matches"]:
        # Extract repository and file information
        repo = match["repository"]
        file_name = match["filePath"]
        
        # Build github_url
        github_url = None
        if "/" in repo:
            github_url = f"https://github.com/{repo}/blob/main/{file_name}"
            if "lines" in match:
                github_url += f"#L{match['lines']['from']}-L{match['lines']['to']}"

        # Get and decode content
        raw_content = match.get("content", "").strip()
        decoded_content = decode_base64_content(raw_content)

        # Format the code for display
        formatted_code = "\n".join("    " + line for line in decoded_content.split("\n")) if decoded_content else ""

        # Create structured match data
        structured_match = {
            "file": file_name,
            "repository": repo,
            "github_url": github_url,
            "lines": match.get("lines"),
            "content": decoded_content,
            "raw_content": raw_content
        }
        structured_matches.append(structured_match)

        # Format text representation
        header = f"\nFile: {file_name}"
        if "lines" in match:
            line_start = match["lines"]["from"]
            line_end = match["lines"]["to"]
            header += f" (Lines {line_start}-{line_end})"
        header += f"\nRepository: {repo}"
        if github_url:
            header += f"\nGitHub: {github_url}"

        result_parts.append(f"{header}\n\n{formatted_code}\n{'='*80}")

    formatted_text = "\n".join(result_parts)
    structured_data = {
        "matches": structured_matches
    }
    
    return formatted_text, structured_data


async def exact_search(query: str, allowed_repos: Optional[List[str]]) -> ToolMessage:
    """A tool for searching for an exact query in the code using Sourcebot"""
    try:
        async with SourcebotClient(base_url=SOURCEBOT_URL) as client:
            # Perform the search with up to 10 matches
            result = await client.search(
                query=query,
                max_match_display_count=10,
                whole=True,  # Get complete file contents for better context
            )

            logging.info(f"Debug - Raw sourcebot response: {result}")  # Debug log

            # Convert sourcebot response format to expected format
            if "Result" in result and "Files" in result["Result"]:
                converted_result = {
                    "matches": [
                        {
                            "repository": file["Repository"],
                            "filePath": file["FileName"],
                            "content": "".join(match["Content"] for match in file.get("ChunkMatches", [])),
                            "lines": {
                                "from": min(match["ContentStart"]["LineNumber"] for match in file.get("ChunkMatches", [])),
                                "to": max(
                                    max(r["End"]["LineNumber"] for r in match.get("Ranges", []))
                                    for match in file.get("ChunkMatches", [])
                                ) if any(file.get("ChunkMatches", [])) else 0
                            } if file.get("ChunkMatches") else None
                        }
                        for file in result["Result"]["Files"]
                    ]
                }
                
                # If allowed_repos is specified, filter the results
                if allowed_repos:
                    filtered_matches = [
                        match
                        for match in converted_result.get("matches", [])
                        if match["repository"] in allowed_repos
                    ]
                    converted_result["matches"] = filtered_matches

                formatted_text, structured_data = format_sourcebot_results(converted_result)
                artifact_data = {
                    "result_type": "search",
                    "matches": structured_data["matches"]
                }
                return ToolMessage(
                    content=formatted_text,
                    name="ExactSearch",
                    artifact=artifact_data
                )
            
            formatted_text, structured_data = format_sourcebot_results({"matches": []})
            return ToolMessage(
                content=formatted_text,
                name="ExactSearch",
                artifact={"result_type": "search", "matches": []}
            )

    except SourcebotApiError as e:
        error_msg = f"Error: Sourcebot search failed - {str(e)}"
        logger.error(error_msg)
        return ToolMessage(
            content=error_msg,
            name="ExactSearch",
            artifact={"result_type": "search", "error": str(e), "matches": []}
        )
    except Exception as e:
        error_msg = f"Error performing exact search: {str(e)}"
        logger.error(error_msg)
        return ToolMessage(
            content=error_msg,
            name="ExactSearch",
            artifact={"result_type": "search", "error": str(e), "matches": []}
        )



def format_search_results(snippets: List[Dict]) -> Tuple[str, Dict[str, Any]]:
    """Format search results into formatted text and structured data"""
    if not snippets:
        return "No matching code found.", {"matches": []}

    result_parts = []
    structured_matches = []

    for snippet in snippets:
        # Format repository information
        repo_info = snippet["repo"]
        repo_url = f"{repo_info['url']}/blob/main/{snippet['file_path']}#L{snippet['line_from']}-L{snippet['line_to']}"

        # Get and decode content
        raw_content = snippet["code"].strip()
        decoded_content = decode_base64_content(raw_content)
        
        # Format the code with basic formatting
        formatted_code = "\n".join("    " + line for line in decoded_content.split("\n")) if decoded_content else ""

        # Create structured match data
        structured_match = {
            "file": snippet["file_path"],
            "repository": repo_info["name"],
            "github_url": repo_url,
            "lines": {
                "from": snippet["line_from"],
                "to": snippet["line_to"]
            },
            "content": decoded_content,
            "raw_content": raw_content
        }
        structured_matches.append(structured_match)

        # Format text representation
        header = f"\nFile: {snippet['file_path']} (Lines {snippet['line_from']}-{snippet['line_to']})"
        header += f"\nRepository: {repo_info['name']}"
        header += f"\nGitHub: {repo_url}"

        result_parts.append(f"{header}\n\n{formatted_code}\n{'='*80}")

    formatted_text = "\n".join(result_parts)
    structured_data = {
        "matches": structured_matches
    }
    
    return formatted_text, structured_data


async def semantic_search(query: str, allowed_repos: Optional[List[str]]) -> ToolMessage:
    """A tool for searching for a semantic query in the code"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SEARCH_API_URL}/search",
                json={"query": query, "allowed_repos": allowed_repos, "top_n": 10},
            )

            if response.status_code != 200:
                error_detail = response.json().get("detail", str(response.text))
                raise Exception(
                    f"Search API error (Status {response.status_code}): {error_detail}"
                )

            result = response.json()
            formatted_text, structured_data = format_search_results(result["snippets"])
            return ToolMessage(
                content=formatted_text,
                name="SemanticSearch",
                artifact={
                    "result_type": "search",
                    "matches": structured_data["matches"]
                }
            )

    except httpx.TimeoutException:
        error_msg = "Error: Search API request timed out. Please try again."
        logger.error(error_msg)
        return ToolMessage(
            content=error_msg,
            name="SemanticSearch",
            artifact={"result_type": "search", "error": error_msg, "matches": []}
        )
    except httpx.RequestError as e:
        error_msg = f"Error: Could not connect to Search API ({str(e)})"
        logger.error(error_msg)
        return ToolMessage(
            content=error_msg,
            name="SemanticSearch",
            artifact={"result_type": "search", "error": str(e), "matches": []}
        )
    except Exception as e:
        error_msg = f"Error performing semantic search: {str(e)}"
        logger.error(error_msg)
        return ToolMessage(
            content=error_msg,
            name="SemanticSearch",
            artifact={"result_type": "search", "error": str(e), "matches": []}
        )


# Creating a structured tool for searching for an exact query in the code
exact_search_tool = StructuredTool.from_function(
    coroutine=exact_search,
    name="ExactSearch",
    description=(
        """
Поиск точного запроса в коде.
Может обнаруживать дублирующиеся функции и классы в репозитории.

### Справочник по синтаксису

Запросы состоят из регулярных выражений, разделённых пробелами. Если обернуть выражение в кавычки (`""`), оно будет рассматриваться как единое целое. По умолчанию файл должен содержать хотя бы одно совпадение для каждого выражения, чтобы быть включённым в результаты.

**Примеры и объяснения:**

- `foo` — Найти файлы, соответствующие регулярному выражению `/foo/`.
- `foo bar` — Найти файлы, соответствующие регулярным выражениям `/foo/` и `/bar/`.
- `"foo bar"` — Найти файлы, соответствующие регулярному выражению `/foo bar/`.

---

Можно объединять выражения с помощью `or`, отрицать с помощью `-`, а также группировать с помощью скобок `()`.

**Примеры и объяснения:**

- `foo or bar` — Найти файлы, соответствующие регулярным выражениям `/foo/` или `/bar/`.
- `foo -bar` — Найти файлы, соответствующие регулярному выражению `/foo/`, но не `/bar/`.
- `foo (bar or baz)` — Найти файлы, соответствующие регулярному выражению `/foo/` и либо `/bar/`, либо `/baz/`.

---

Выражения можно дополнять определёнными ключевыми словами, чтобы изменить поведение поиска. Некоторые ключевые слова можно отрицать, добавив префикс `-`.

**Список префиксов:**

- `file:`  
  Фильтрует результаты по путям к файлам, соответствующим регулярному выражению.  
  По умолчанию ищутся все файлы.  
  Примеры:  
  `file:README`  
  `file:"my file"`  
  `-file:test\\.ts$`

- `repo:`  
  Фильтрует результаты по репозиториям, соответствующим регулярному выражению.  
  По умолчанию ищутся все репозитории.  
  Примеры:  
  `repo:linux`  
  `-repo:^web/.*`

- `rev:`  
  Фильтрует результаты по определённой ветке или тегу.  
  По умолчанию ищется только в основной ветке.  
  Пример:  
  `rev:beta`

- `lang:`  
  Фильтрует результаты по языку программирования (определяется с помощью linguist).  
  По умолчанию ищутся все языки.  
  Примеры:  
  `lang:TypeScript`  
  `-lang:YAML`

- `sym:`  
  Ищет определения символов, созданные с помощью universal ctags во время индексации.  
  Пример:  
  `sym:\bmain\b`
"""
    ),
    args_schema=ExactSearchQuery,
)


# Creating a structured tool for searching for a semantic query in the code
semantic_search_tool = StructuredTool.from_function(
    coroutine=semantic_search,
    name="SemanticSearch",
    description=(
"""
Поиск по смыслу (векторный) по кодовой базе выбанных репозиториев.
"""
    ),
    args_schema=SemanticSearchQuery,
)
