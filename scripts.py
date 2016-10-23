import re

data = """"""

pattern = re.compile(r'\d+\.\s(\w+)[.\D]+(\d+)[.\D]+(\d+)[.\D]+(\d+)')

res = []
for player in data.split('\n'):
    g = pattern.match(player).groups()
    p = (g[0], int(g[2]) + int(g[3]))
    res.append(p)

games = sorted(res, key=lambda a: a[1], reverse=True)

for g in games[:50]:
    print g

frequent_players = [
]

print len(frequent_players)
