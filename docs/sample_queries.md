# Sample Queries

Below are 10 representative queries and expected behavior.

1. `找出 2015 年后的高评分科幻片`
- Expected: structured route, top-rated SQL filtering by year+genre+votes.

2. `找出评分较高且投票数足够的 thriller 电影`
- Expected: structured route, top-rated SQL filtering by genre+rating+vote_count.

3. `比较 Christopher Nolan 和 Denis Villeneuve 的电影表现`
- Expected: structured route, director-level aggregate comparison.

4. `比较 Interstellar 和 Arrival 的评分与投票表现`
- Expected: structured route, movie-level comparison.

5. `找出与 Interstellar 风格相似的电影`
- Expected: semantic route, vector retrieval of similar documents.

6. `总结 Arrival 和 Blade Runner 2049 的共同主题`
- Expected: semantic route, retrieval-driven thematic evidence.

7. `推荐和 Dune: Part Two 类似的高评分科幻电影`
- Expected: hybrid route, combine semantic similarity + structured ranking.

8. `2010 年后 Denis Villeneuve 的电影里，哪些最值得看并且风格接近 Arrival`
- Expected: hybrid route, structured director/time filter + semantic evidence.

9. `筛选 2015 年以后的 Crime 或 Thriller 电影`
- Expected: structured route, filtered SQL query.

10. `基于当前数据集中描述文本，哪些电影和时间、记忆主题最相关？`
- Expected: semantic route, theme-oriented semantic retrieval.
