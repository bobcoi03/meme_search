def get_rid_of_0x0c():
	delete = ["\f"]
	with open("data_uncleaned.xml") as fin, open("data.xml", "w") as fout:
		
		for line in fin:
			for word in delete:
				line = line.replace(word, "")
			fout.write(line)

if __name__ == '__main__':
	get_rid_of_0x0c()