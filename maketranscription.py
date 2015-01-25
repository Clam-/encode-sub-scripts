#maketranscription.py v0.2

# 0.2 fixed some line breaking stuff and changed param name
from codecs import open as codopen
from optparse import OptionParser
from sys import exit, stdout, stderr, path as scriptpath
from datetime import time
from os.path import exists, join

class Globals:
	translate = {
		
	}
	strip = 'EpTitle,PreviewTitle,tri4'
	template = u"{timecode} - {style}: "
	timeformat = "{hours}:{minutes}:{seconds}"

	@classmethod
	def loadreplace(cls, fname):
		for line in codopen(fname, "rb", "utf-8"):
			style, replacement = line.split("\t", 1)
			cls.translate[style] = replacement
	
class STDOUTWrapper:
	def __init__(self, stream):
		self.stream = stream
	def write(self, s):
		self.stream.write(s.encode("utf-8"))
	
def getTime(s):
	s, e = s.split(".")
	l = s.split(':')
	micro = "{0:0<6}".format(e)[:6]
	milli = "{0:0<3}".format(e)[:3]
	
	return {"hours" : l[0], 
		"minutes" : l[1], 
		"seconds" : l[2], 
		"milliseconds" : milli, 
		"microseconds" : micro
	}
	
def maketranscription(options):
	mode = 0
	#0 start
	#1 styles
	#2 events
	output = options.output
	template = options.template.decode("utf-8")
	for line in codopen(options.infile, "rb", "utf-8"):
		line = line.strip()
		if line == "": 
			continue
		
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
			if istyle == "Format": 
				continue
			elif istyle == "Comment": 
				continue
			
		#Events
		if mode == 2:
			idia, rest = line.split(":",1)
			if idia == "Format": 
				continue
			if idia == "Comment": 
				continue
			
			rest = rest.strip()
			fields = rest.split(",",9)
			style = fields[3]
			time = options.timeformat.format(**getTime(fields[1]))
			
			if style in Globals.translate:
				#translate
				style = Globals.translate[style]
			if style in options.ignore:
				continue
			
			text = fields[9]
			#build text proper
			output.write(template.format(style=style, timecode=time))
			escape = False
			comment = False
			index = 0
			while index < len(text):
				# if text[index] == ESCAPE:
					# index += 1
					# escape = True
					# continue
				
				if (not escape) and (text[index] == "{"): 
					#find index where closing }
					end = index+1
					index += 1
					while True:
						if text[end] == "}": break
						end += 1
					st = text[index:end]
					if r"\fn" in st:
						commands = st.split("\\")
						# for com in commands:
							# if com == "fn": font = styles[style]
							# elif com[:2] == "fn":
								# font = com[2:]
								# if font not in fontdb: 
									# print line
									# print "-MISSING FONT in DB: %s" % font
									# raise NoU
								# if fontdb[font] not in Globals.alphabetdict:
									# Globals.alphabetdict[fontdb[font]] = set([])
					index = end+1
					continue
				output.write(text[index])
				index += 1
			output.write("\n")

				
if __name__ == "__main__":	
	parser = OptionParser(usage="usage: %prog [options] inputfile")
	parser.add_option("-o", "--output", dest="output", metavar="FILENAME",
		help="Output filename. [STDOUT if not specified]")
	parser.add_option("-p", "--lineprefix", dest="template", default=Globals.template, metavar="TEMPLATESTRING",
		help='Template string for the prefix to the line. style (Inserts the stylename for the line), '
		'timestamp (Inserts the timecode for when the subtitle was to start) ["%s"]' % Globals.template)
	parser.add_option("-i", "--ignore", dest="ignore", default=Globals.strip, metavar="STYLES",
		help='List of stylenames to ignore. Seperated by comma. ["%s"]' % Globals.strip)
	parser.add_option("--timeformat", dest="timeformat", default=Globals.timeformat, metavar="TIMEFORMAT",
		help='String used for formatting timecodes. Available: hours, minutes, seconds, milliseconds, microseconds ["%s"]' % Globals.timeformat)
	parser.add_option("--replacefile", dest="replacefile", metavar="FILENAME",
		help='Filename of file to use for stylename replacements. File should be in the format of "style<tab>replacementtext" per line.'
		'This option adds to the defaultreplace.txt in the script folder if it exists and overides any existing replacement rules.')
	parser.add_option("--nodefaultreplace", action="store_true", default=False, dest="noreplace", metavar="FILENAME",
		help='Do not attempt load the defaultreplace.txt in the script folder.')
		
	(options, args) = parser.parse_args()
	if len(args) != 1:
		parser.print_help()
		print ""
		print "ERROR: Need original script inputfile"
		exit(1)
	options.infile = args[0]
	
	if not options.output:
		options.output = STDOUTWrapper(stdout)
	else:
		options.output = codopen(options.output, "wb", "utf-8")
		
	options.ignore = options.ignore.split(",")
	
	if not options.noreplace:
		fname = join(scriptpath[0], "defaultreplace.txt")
		if exists(fname):
			stderr.write("Loading default replace...\n")
			Globals.loadreplace(fname)
	if options.replacefile:
		if exists(options.replacefile):
			print "Loading replace file replace"
			Globals.loadreplace(options.replacefile)
		else:
			#write to STDERR
			stderr.write("Replacement file (%s) not found.\n" % options.replacefile)
	maketranscription(options)