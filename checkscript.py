from re import compile as recompile
from codecs import open as codopen
# from enchant import Dict as enDict
# d = enDict("en_US")

class Globals:
	rules = {
		"DOTS" : recompile(r"[^.]\.\.$"),
		"DOTS2" : recompile(r"[^.]\.\.[^.]"),
		"Cap" : recompile(r"[^.]\. [^A-Z]"), 
		"Cap2" : recompile(r"! [^A-Z]"), 
		"nospace" : recompile(r"[!?.,][A-Za-z]"),
		"quotes" : recompile(r'".*"[A-Za-z]'),
		"i" : recompile(r" i "),
		
	}

def checkscript(fname):
	ESCAPE = None
	mode = 0
	#0 start
	#1 styles
	#2 events

	for line in codopen(fname, "rb", "utf-8"):
		line = line.strip()
		if line == "": continue
		
		#pre
		if mode == 0:
			if line == "[V4+ Styles]":
				mode = 1
				continue
		#styles
		elif mode == 1:
			if line == "[Events]":
				mode = 2
				continue
			
			istyle, rest = line.split(":",1)
			if istyle == "Format": continue
			elif istyle == "Comment": continue
			
		#Events
		elif mode == 2:
			idia, rest = line.split(":",1)
			if idia == "Format": continue
			elif idia == "Comment": continue
			
			rest = rest.strip()
			fields = rest.split(",",9)
			text = fields[9]
			
			comment = False
			index = 0
			s = ""
			while index < len(text):
				if text[index] == ESCAPE:
					index += 1
					continue
				
				if text[index] == "{": 
					#find index where closing }
					end = index+1
					index += 1
					while True:
						if text[end] == "}": break
						end += 1
					index = end+1
					continue
				if ord(text[index]) < 128:
					s += text[index]
				index += 1
			#print "Line:", s
			# check line:
			
			for k, v in Globals.rules.iteritems():
				m = v.search(s)
				if m:
					print "RULE: %s MATCHED - %s" % (k, s)
	return

if __name__ == "__main__":
	from sys import argv, exit
	
	if len(argv) != 2:
		print "Need scriptname"
		exit(1)
	checkscript(argv[1])