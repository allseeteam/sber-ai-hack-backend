import asyncio
import base64
from rich import print
from .sourcebot.sourcebot_client import SourcebotClient, SourcebotApiError

async def test_version(client: SourcebotClient) -> None:
    """Test the version endpoint"""
    print("[bold blue]Testing version endpoint...[/bold blue]")
    version = await client.get_version()
    print(f"Sourcebot version: {version['version']}\n")

async def test_repos(client: SourcebotClient) -> None:
    """Test the repos endpoint"""
    print("[bold blue]Testing repos endpoint...[/bold blue]")
    repos = await client.get_repos()
    
    print("Repository information:")
    print(f"Raw response: {repos}")  # Debug raw response
    
    try:
        if repos['List']['Repos']:  # Try original case first
            for repo_info in repos['List']['Repos']:
                repo = repo_info['Repository']
                print(f"\n[bold green]{repo['Name']}[/bold green]")
                print(f"URL: {repo['URL']}")
                print(f"Branches: {len(repo['Branches']) if repo['Branches'] else 0}")
                if repo['RawConfig']:
                    github_stats = {k: v for k, v in repo['RawConfig'].items() if k.startswith('github-')}
                    if github_stats:
                        print("GitHub stats:")
                        for key, value in github_stats.items():
                            print(f"  {key}: {value}")

                print("\nIndex stats:")
                print(f"Documents: {repo_info['Stats']['Documents']}")
                print(f"Lines of code: {repo_info['Stats']['NewLinesCount']}")
                print(f"Index size: {repo_info['Stats']['IndexBytes'] / 1024:.1f} KB")
                print(f"Content size: {repo_info['Stats']['ContentBytes'] / (1024*1024):.1f} MB")

            # Print total stats
            print("\n[bold blue]Total Statistics:[/bold blue]")
            stats = repos['List']['Stats']
            print(f"Total repositories: {stats['Repos']}")
            print(f"Total documents: {stats['Documents']:,}")
            print(f"Total lines of code: {stats['NewLinesCount']:,}")
            print(f"Total index size: {stats['IndexBytes'] / (1024*1024):.1f} MB")
            print(f"Total content size: {stats['ContentBytes'] / (1024*1024*1024):.1f} GB\n")
        else:
            print("No repositories found\n")
    except KeyError as e:
        print(f"[bold red]Error accessing key:[/bold red] {str(e)}")

async def test_search(client: SourcebotClient) -> None:
    """Test the search endpoint"""
    print("[bold blue]Testing search endpoint...[/bold blue]")
    search_query = "def"  # Looking for Python function definitions
    search_results = await client.search(
        query=search_query,
        max_match_display_count=5
    )
    
    print(f"Raw response: {search_results}")  # Debug raw response
    
    try:
        if search_results['Result']['Files']:
            print(f"Found {len(search_results['Result']['Files'])} files containing '{search_query}':")
            for file in search_results['Result']['Files']:
                print(f"\n[bold green]{file['FileName']}[/bold green]")
                print(f"Repository: {file['Repository']}")
                print(f"Language: {file['Language']}")
                print("Matches:")
                for match in file['ChunkMatches']:
                    # Decode base64 content
                    decoded_content = base64.b64decode(match['Content']).decode('utf-8')
                    print(f"\n  [dim]{decoded_content.strip()}[/dim]")
                    print(f"  Score: {match['Score']}")
                    print(f"  Location: Line {match['ContentStart']['LineNumber']}, Column {match['ContentStart']['Column']}")
                    print("  ---")

            # Test file source endpoint with the first found file
            first_file = search_results['Result']['Files'][0]
            print("\n[bold blue]Testing file source endpoint...[/bold blue]")
            source = await client.get_file_source(
                file_name=first_file['FileName'],
                repository=first_file['Repository']
            )
            print(f"File language: {source['language']}")
            print("First 200 characters of source:")
            print(source['source'][:200] + "...\n")

            # Print search stats
            print("[bold blue]Search Statistics:[/bold blue]")
            stats = search_results['Result']
            print(f"Files considered: {stats['FilesConsidered']:,}")
            print(f"Files loaded: {stats['FilesLoaded']:,}")
            print(f"Files skipped: {stats['FilesSkipped']:,}")
            print(f"Match count: {stats['MatchCount']:,}")
            print(f"Duration: {stats['Duration']/1e6:.2f}ms")
            print(f"Content loaded: {stats['ContentBytesLoaded'] / (1024*1024):.1f} MB")
            print(f"Index loaded: {stats['IndexBytesLoaded'] / 1024:.1f} KB\n")
        else:
            print("No files found matching the search query.")
    except KeyError as e:
        print(f"[bold red]Error accessing key:[/bold red] {str(e)}")

async def main():
    try:
        async with SourcebotClient() as client:
            await test_version(client)
            await test_repos(client)
            await test_search(client)
    except SourcebotApiError as e:
        print(f"[bold red]API Error:[/bold red] {str(e)}")
    except Exception as e:
        print(f"[bold red]Error:[/bold red] {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
