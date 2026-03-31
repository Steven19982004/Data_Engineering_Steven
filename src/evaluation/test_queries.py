from __future__ import annotations

# 10 representative evaluation queries spanning structured / semantic / hybrid routing.
EVAL_QUERIES: list[dict] = [
    {
        "id": "q01",
        "query": "找出 2015 年后的高评分科幻片",
        "expected_tool_path": ["get_top_rated_movies"],
        "expected_route": "structured",
    },
    {
        "id": "q02",
        "query": "找出评分较高且投票数足够的 thriller 电影",
        "expected_tool_path": ["get_top_rated_movies"],
        "expected_route": "structured",
    },
    {
        "id": "q03",
        "query": "比较 Christopher Nolan 和 Denis Villeneuve 的电影表现",
        "expected_tool_path": ["compare_movies_or_directors"],
        "expected_route": "structured",
    },
    {
        "id": "q04",
        "query": "比较 Interstellar 和 Arrival 的评分与投票表现",
        "expected_tool_path": ["compare_movies_or_directors"],
        "expected_route": "structured",
    },
    {
        "id": "q05",
        "query": "找出与 Interstellar 风格相似的电影",
        "expected_tool_path": ["semantic_movie_search"],
        "expected_route": "semantic",
    },
    {
        "id": "q06",
        "query": "总结 Arrival 和 Blade Runner 2049 的共同主题",
        "expected_tool_path": ["semantic_movie_search"],
        "expected_route": "semantic",
    },
    {
        "id": "q07",
        "query": "推荐和 Dune: Part Two 类似的高评分科幻电影",
        "expected_tool_path": ["semantic_movie_search", "get_top_rated_movies"],
        "expected_route": "hybrid",
    },
    {
        "id": "q08",
        "query": "2010 年后 Denis Villeneuve 的电影里，哪些最值得看并且风格接近 Arrival",
        "expected_tool_path": ["compare_movies_or_directors", "semantic_movie_search"],
        "expected_route": "hybrid",
    },
    {
        "id": "q09",
        "query": "筛选 2015 年以后的 Crime 或 Thriller 电影",
        "expected_tool_path": ["search_movies_by_filters"],
        "expected_route": "structured",
    },
    {
        "id": "q10",
        "query": "基于当前数据集中描述文本，哪些电影和时间、记忆主题最相关？",
        "expected_tool_path": ["semantic_movie_search"],
        "expected_route": "semantic",
    },
]
