from codecs import open as codopen

class Globals:
	keep = set(["OP-ENG", "OP-JP", "EpTitle", "PreviewTitle", "Signs", "mataashita-jp", "mataashita-en", "tri4", "ED-ENG (right)", "ED-ENG (left)", "ED-JP"])
	default = "Madoka"
	defaultstyle = "Style: Madoka,Doradani Rg,67,&H00FFFFFF,&H001F2AB0,&H00000000,&HC8000000,-1,0,0,0,100,100,0,0,1,2.45,0.7,2,57,57,39,1\n"
	
def stripstyles(infile, outfile):
	mode = 0
	#0 start
	#1 styles
	#2 events

	output = codopen(outfile, "wb", "utf-8")
	
	for line in codopen(infile, "rb", "utf-8"):
		rawline = line
		line = line.strip()
		if line == "": 
			output.write(rawline)
			continue
		
		#pre
		if mode == 0:
			if line == "[V4+ Styles]":
				mode = 1
			output.write(rawline)
		#styles
		elif mode == 1:
			if line == "[Events]":
				mode = 2
				output.write(rawline)
				continue
			
			istyle, rest = line.split(":",1)
			if istyle == "Format": 
				output.write(rawline)
				#put default style:
				output.write(Globals.defaultstyle)
				continue
			elif istyle == "Comment": 
				output.write(rawline)
				continue
			
			rest = rest.strip()
			style, rest = rest.split(",",1)
			if style not in Globals.keep:
				continue
			else:
				output.write(rawline)
			
		#Events
		if mode == 2:
			idia, rest = line.split(":",1)
			if idia == "Format": 
				output.write(rawline)
				continue
			if idia == "Comment": 
				output.write(rawline)
				continue
			
			rest = rest.strip()
			fields = rest.split(",",9)
			style = fields[3]
			
			if style not in Globals.keep:
				output.write(rawline.replace(style,Globals.default, 1))
			else:
				output.write(rawline)
				
if __name__ == "__main__":
	from sys import argv, exit
	
	if len(argv) != 3:
		print "Need original script, and output name"
		exit(1)
	stripstyles(argv[1], argv[2])