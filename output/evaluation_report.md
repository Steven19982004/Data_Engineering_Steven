# Evaluation Report

- total_cases: 5
- tool_match_rate: 1.0
- keyword_hit_rate: 0.833
- avg_latency_ms: 1.64
- agent_mode: local_rule_based

## Case Details

### q1
- question: 找出 2015 年后的高评分科幻片
- expected_tool: sql.fetch_high_rated_scifi
- used_tools: ['sql.fetch_high_rated_scifi']
- tool_match: True
- keyword_hits: 3/3
- latency_ms: 0.82
- answer_preview: 2015 年后的高评分科幻片:
1. Dune: Part Two (2024) | rating=8.6 | votes=491000 | director=Denis Villeneuve
2. Mad Max: Fury Road (2015) | rating=8.1 | votes=1111000 | director=George Miller
3. The Martian (2015) | rating=8.0 | vot

### q2
- question: 比较 Christopher Nolan 和 Denis Villeneuve 在数据集中的表现
- expected_tool: sql.compare_directors
- used_tools: ['sql.compare_directors']
- tool_match: True
- keyword_hits: 2/2
- latency_ms: 0.57
- answer_preview: 导演表现对比:
- Christopher Nolan: movies=4, avg_rating=8.3, best_rating=8.8, total_votes=6143000
- Denis Villeneuve: movies=6, avg_rating=8.067, best_rating=8.6, total_votes=4135000

### q3
- question: 找出与 Interstellar 在主题或风格上相似的电影
- expected_tool: vector.find_similar_movies
- used_tools: ['vector.find_similar_movies']
- tool_match: True
- keyword_hits: 1/1
- latency_ms: 5.46
- answer_preview: 与 Interstellar 相似的电影:
1. Arrival (score=0.0507)
2. The Martian (score=0.0367)
3. Tenet (score=0.0235)
4. Mad Max: Fury Road (score=0.0235)
5. Blade Runner 2049 (score=0.0187)

### q4
- question: 总结 Arrival 和 Blade Runner 2049 的共同主题
- expected_tool: nlp.summarize_common_themes
- used_tools: ['nlp.summarize_common_themes']
- tool_match: True
- keyword_hits: 1/3
- latency_ms: 0.83
- answer_preview: 匹配电影: Arrival, Blade Runner 2049
主题总结: Common themes observed across retrieved descriptions/reviews include: humanity, time, memory, blade, runner, linguist.

### q5
- question: 找出评分较高且投票数足够的 thriller 电影
- expected_tool: sql.fetch_high_quality_thrillers
- used_tools: ['sql.fetch_high_quality_thrillers']
- tool_match: True
- keyword_hits: 3/3
- latency_ms: 0.52
- answer_preview: 高评分且高投票数 Thriller 电影:
1. Inception (2010) | rating=8.8 | votes=2551000 | director=Christopher Nolan
2. Parasite (2019) | rating=8.5 | votes=1023000 | director=Bong Joon Ho
3. Oppenheimer (2023) | rating=8.4 | votes=92000

