"""QA Medi MCP Server - 사내 QA 자동화 도구 제공."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("qa-medi")


@mcp.tool()
def check_qa(target: str) -> str:
    """QA 체크리스트를 대상에 적용합니다."""
    # TODO: 실제 검증 로직 구현
    return f"'{target}' QA 검증 완료 (stub)"


if __name__ == "__main__":
    mcp.run()
