import os

filepath = "/home/checkmate/Documents/chess-bot/main/config.yaml"

print(repr(filepath))
print(os.path.exists(filepath))
print(os.path.isfile(filepath))
print(os.path.dirname(filepath))
print(os.listdir("/home/checkmate/Documents/chess-bot/main"))