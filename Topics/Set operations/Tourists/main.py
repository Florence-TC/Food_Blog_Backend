# work with these variables
eugene = set(input().split())
rose = set(input().split())

eugene_or_rose = eugene | rose
eugene_and_rose = eugene & rose

print(eugene_or_rose - eugene_and_rose)
