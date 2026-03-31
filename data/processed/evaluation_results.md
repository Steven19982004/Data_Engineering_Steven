# Evaluation Results

- total_cases: 10
- route_match_rate: 1.000
- route_match_rate_explicit: 1.000
- tool_path_match_rate: 1.000
- grounded_rate: 1.000

## Case Details

### q01
- query: 找出 2015 年后的高评分科幻片
- expected_route: structured
- actual_route: structured
- expected_tool_path: ['get_top_rated_movies']
- actual_tool_path: ['get_top_rated_movies']
- retrieved_titles: ['Dune: Part Two', 'Avengers: Infinity War', 'Logan', 'Mad Max: Fury Road', 'The Martian']
- grounded: True
- tool_path_match: True
- route_match: True
- final_answer: 基于当前已索引数据，我给出以下结果（deterministic fallback）：
- Routing: structured (Detected filter/sort/compare intent.)
- Structured tool: get_top_rated_movies
- 结构化结果:
  1. Dune: Part Two (2024) | rating=8.6 | votes=491000 | source=csv|tmdb
  2. Avengers: Infinity War (2018) | rating=8.4 | votes=1497434 | source=csv|tmdb
  3. Logan (2017) | rating=8.1 | votes=2477323 | source=csv|tmdb
  4. Mad Max: Fury Road (2015) | rating=8.1 | votes=1111000 | source=csv|tmdb
  5. The Martian (2015) | rating=8.0 | votes=918000 | source=csv|tmdb
- 证据电影: Dune: Part Two, Avengers: Infinity War, Logan, Mad Max: Fury Road, The Martian
注：以上结论仅基于当前数据库与向量索引中的样本数据，未覆盖外部全量电影库。

### q02
- query: 找出评分较高且投票数足够的 thriller 电影
- expected_route: structured
- actual_route: structured
- expected_tool_path: ['get_top_rated_movies']
- actual_tool_path: ['get_top_rated_movies']
- retrieved_titles: ['Inception', 'The Silence of the Lambs', 'Gisaengchung', 'Psycho', 'Rear Window']
- grounded: True
- tool_path_match: True
- route_match: True
- final_answer: 基于当前已索引数据，我给出以下结果（deterministic fallback）：
- Routing: structured (Detected filter/sort/compare intent.)
- Structured tool: get_top_rated_movies
- 结构化结果:
  1. Inception (2010) | rating=8.8 | votes=2551000 | source=csv|tmdb
  2. The Silence of the Lambs (1991) | rating=8.6 | votes=561140 | source=csv|tmdb
  3. Gisaengchung (2019) | rating=8.5 | votes=2268400 | source=csv|tmdb
  4. Psycho (1960) | rating=8.5 | votes=2260186 | source=csv|tmdb
  5. Rear Window (1954) | rating=8.5 | votes=2248320 | source=csv|tmdb
- 证据电影: Inception, The Silence of the Lambs, Gisaengchung, Psycho, Rear Window
注：以上结论仅基于当前数据库与向量索引中的样本数据，未覆盖外部全量电影库。

### q03
- query: 比较 Christopher Nolan 和 Denis Villeneuve 的电影表现
- expected_route: structured
- actual_route: structured
- expected_tool_path: ['compare_movies_or_directors']
- actual_tool_path: ['compare_movies_or_directors']
- retrieved_titles: []
- grounded: True
- tool_path_match: True
- route_match: True
- final_answer: 基于当前已索引数据，我给出以下结果（deterministic fallback）：
- Routing: structured (Detected filter/sort/compare intent.)
- Structured tool: compare_movies_or_directors
- 对比结果:
  - Director Christopher Nolan: movies=9, avg_rating=8.411, total_votes=12887101
  - Director Denis Villeneuve: movies=7, avg_rating=8.1, total_votes=4605832
- 没有足够证据电影命中。
注：以上结论仅基于当前数据库与向量索引中的样本数据，未覆盖外部全量电影库。

### q04
- query: 比较 Interstellar 和 Arrival 的评分与投票表现
- expected_route: structured
- actual_route: structured
- expected_tool_path: ['compare_movies_or_directors']
- actual_tool_path: ['compare_movies_or_directors']
- retrieved_titles: ['Interstellar', 'Arrival']
- grounded: True
- tool_path_match: True
- route_match: True
- final_answer: 基于当前已索引数据，我给出以下结果（deterministic fallback）：
- Routing: structured (Detected filter/sort/compare intent.)
- Structured tool: compare_movies_or_directors
- 对比结果:
  - Movie Interstellar (2014): rating=8.7, votes=2065000
  - Movie Arrival (2016): rating=7.9, votes=765000
- 证据电影: Interstellar, Arrival
注：以上结论仅基于当前数据库与向量索引中的样本数据，未覆盖外部全量电影库。

### q05
- query: 找出与 Interstellar 风格相似的电影
- expected_route: semantic
- actual_route: semantic
- expected_tool_path: ['semantic_movie_search']
- actual_tool_path: ['semantic_movie_search']
- retrieved_titles: ['Dune: Part Two', 'Jagten', 'Braveheart', 'WALL·E', 'Oldeuboi']
- grounded: True
- tool_path_match: True
- route_match: True
- final_answer: 基于当前已索引数据，我给出以下结果（deterministic fallback）：
- Routing: semantic (Detected similarity/theme/summary intent.)
- 结构化结果为空。
- 语义检索结果:
  1. Dune: Part Two (2024) | score=0.2309 | source=csv|tmdb
  2. Jagten (2013) | score=0.2118 | source=csv
  3. Braveheart (1995) | score=0.1298 | source=csv
  4. WALL·E (2008) | score=0.1284 | source=csv|tmdb
  5. Oldeuboi (2003) | score=0.128 | source=csv|tmdb
- 证据电影: Dune: Part Two, Jagten, Braveheart, WALL·E, Oldeuboi
注：以上结论仅基于当前数据库与向量索引中的样本数据，未覆盖外部全量电影库。

### q06
- query: 总结 Arrival 和 Blade Runner 2049 的共同主题
- expected_route: semantic
- actual_route: semantic
- expected_tool_path: ['semantic_movie_search']
- actual_tool_path: ['semantic_movie_search']
- retrieved_titles: ['Star Wars', 'The Empire Strikes Back', 'The Lord of the Rings: The Return of the King', 'Spider-Man: Into the Spider-Verse', 'Up']
- grounded: True
- tool_path_match: True
- route_match: True
- final_answer: 基于当前已索引数据，我给出以下结果（deterministic fallback）：
- Routing: semantic (Detected similarity/theme/summary intent.)
- 结构化结果为空。
- 语义检索结果:
  1. Star Wars (1977) | score=0.1505 | source=csv|tmdb
  2. The Empire Strikes Back (1980) | score=0.1377 | source=csv|tmdb
  3. The Lord of the Rings: The Return of the King (2003) | score=0.127 | source=csv|tmdb
  4. Spider-Man: Into the Spider-Verse (2018) | score=0.1235 | source=csv|tmdb
  5. Up (2009) | score=0.0926 | source=csv|tmdb
- 证据电影: Star Wars, The Empire Strikes Back, The Lord of the Rings: The Return of the King, Spider-Man: Into the Spider-Verse, Up
注：以上结论仅基于当前数据库与向量索引中的样本数据，未覆盖外部全量电影库。

### q07
- query: 推荐和 Dune: Part Two 类似的高评分科幻电影
- expected_route: hybrid
- actual_route: hybrid
- expected_tool_path: ['semantic_movie_search', 'get_top_rated_movies']
- actual_tool_path: ['get_top_rated_movies', 'semantic_movie_search']
- retrieved_titles: ['Inception', 'Interstellar', 'The Matrix', 'Dune: Part Two', 'Terminator 2: Judgment Day', 'Hauru no ugoku shiro', 'Judgment at Nuremberg', 'Per qualche dollaro in più', 'Dersu Uzala']
- grounded: True
- tool_path_match: True
- route_match: True
- final_answer: 基于当前已索引数据，我给出以下结果（deterministic fallback）：
- Routing: hybrid (Detected both analytical and semantic intent.)
- Structured tool: get_top_rated_movies
- 结构化结果:
  1. Inception (2010) | rating=8.8 | votes=2551000 | source=csv|tmdb
  2. Interstellar (2014) | rating=8.7 | votes=2065000 | source=csv|tmdb
  3. The Matrix (1999) | rating=8.7 | votes=593316 | source=csv|tmdb
  4. Dune: Part Two (2024) | rating=8.6 | votes=491000 | source=csv|tmdb
  5. Terminator 2: Judgment Day (1991) | rating=8.6 | votes=211751 | source=csv
- 语义检索结果:
  1. Hauru no ugoku shiro (2005) | score=0.2631 | source=csv|tmdb
  2. Judgment at Nuremberg (1961) | score=0.2582 | source=csv
  3. Per qualche dollaro in più (1967) | score=0.239 | source=csv|tmdb
  4. Dersu Uzala (1977) | score=0.2314 | source=csv|tmdb
  5. Interstellar (2014) | score=0.2268 | source=csv|tmdb
- 证据电影: Inception, Interstellar, The Matrix, Dune: Part Two, Terminator 2: Judgment Day, Hauru no ugoku shiro, Judgment at Nuremberg, Per qualche dollaro in più, Dersu Uzala
注：以上结论仅基于当前数据库与向量索引中的样本数据，未覆盖外部全量电影库。

### q08
- query: 2010 年后 Denis Villeneuve 的电影里，哪些最值得看并且风格接近 Arrival
- expected_route: hybrid
- actual_route: hybrid
- expected_tool_path: ['compare_movies_or_directors', 'semantic_movie_search']
- actual_tool_path: ['compare_movies_or_directors', 'semantic_movie_search']
- retrieved_titles: ['Arrival', 'To Be or Not to Be', 'Tengoku to jigoku', 'Modern Times', 'Schindler&apos;s List', 'Léon']
- grounded: True
- tool_path_match: True
- route_match: True
- final_answer: 基于当前已索引数据，我给出以下结果（deterministic fallback）：
- Routing: hybrid (Detected both analytical and semantic intent.)
- Structured tool: compare_movies_or_directors
- 对比结果:
  - Director Denis Villeneuve: movies=7, avg_rating=8.1, total_votes=4605832
  - Movie Arrival (2016): rating=7.9, votes=765000
- 语义检索结果:
  1. To Be or Not to Be (1942) | score=0.2449 | source=csv|tmdb
  2. Tengoku to jigoku (1963) | score=0.2405 | source=csv|tmdb
  3. Modern Times (1936) | score=0.1489 | source=csv|tmdb
  4. Schindler&apos;s List (1994) | score=0.1371 | source=csv|tmdb
  5. Léon (1994) | score=0.1318 | source=csv|tmdb
- 证据电影: Arrival, To Be or Not to Be, Tengoku to jigoku, Modern Times, Schindler&apos;s List, Léon
注：以上结论仅基于当前数据库与向量索引中的样本数据，未覆盖外部全量电影库。

### q09
- query: 筛选 2015 年以后的 Crime 或 Thriller 电影
- expected_route: structured
- actual_route: structured
- expected_tool_path: ['search_movies_by_filters']
- actual_tool_path: ['search_movies_by_filters']
- retrieved_titles: ['Gisaengchung', 'Parasite', 'Joker', 'Oppenheimer', 'Ah-ga-ssi']
- grounded: True
- tool_path_match: True
- route_match: True
- final_answer: 基于当前已索引数据，我给出以下结果（deterministic fallback）：
- Routing: structured (Detected filter/sort/compare intent.)
- Structured tool: search_movies_by_filters
- 结构化结果:
  1. Gisaengchung (2019) | rating=8.5 | votes=2268400 | source=csv|tmdb
  2. Parasite (2019) | rating=8.5 | votes=1023000 | source=csv|tmdb
  3. Joker (2019) | rating=8.4 | votes=1665294 | source=csv|tmdb
  4. Oppenheimer (2023) | rating=8.4 | votes=920000 | source=csv|tmdb
  5. Ah-ga-ssi (2016) | rating=8.1 | votes=1919064 | source=csv|tmdb
- 证据电影: Gisaengchung, Parasite, Joker, Oppenheimer, Ah-ga-ssi
注：以上结论仅基于当前数据库与向量索引中的样本数据，未覆盖外部全量电影库。

### q10
- query: 基于当前数据集中描述文本，哪些电影和时间、记忆主题最相关？
- expected_route: semantic
- actual_route: semantic
- expected_tool_path: ['semantic_movie_search']
- actual_tool_path: ['semantic_movie_search']
- retrieved_titles: ['Everything Everywhere All at Once', 'Jagten', 'The Elephant Man', 'Get Out', 'The Incredibles']
- grounded: True
- tool_path_match: True
- route_match: True
- final_answer: 基于当前已索引数据，我给出以下结果（deterministic fallback）：
- Routing: semantic (Detected similarity/theme/summary intent.)
- 结构化结果为空。
- 语义检索结果:
  1. Everything Everywhere All at Once (2022) | score=0.2074 | source=csv|tmdb
  2. Jagten (2013) | score=0.1513 | source=csv
  3. The Elephant Man (1980) | score=0.1258 | source=csv|tmdb
  4. Get Out (2017) | score=0.1231 | source=csv|tmdb
  5. The Incredibles (2004) | score=0.1216 | source=csv|tmdb
- 证据电影: Everything Everywhere All at Once, Jagten, The Elephant Man, Get Out, The Incredibles
注：以上结论仅基于当前数据库与向量索引中的样本数据，未覆盖外部全量电影库。

