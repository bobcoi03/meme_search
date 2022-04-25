import os
counter = 0
limit = 1000
for file in os.listdir("./static/memeImages"):
	if file.endswith('.gif') and counter < limit:
		counter += 1
		os.remove(f"./static/memeImages/{file}")
		print(f"deleted {file}")
