from codecs import open as codopen
from unicodedata import name
from time import sleep

from os.path import exists, isdir, join
from os import listdir

from fnmatch import fnmatch

import fontforge

class Globals:
	alphabetdict = {}
	fonts = []
	index = 0
	doneref = False
	tempstuffs = None
	FONTS = "/home/mayuri/substuff/fonts"
	LOOKUPFILE = "fontdb.txt"
	
def genalphabets(fname, fontdb):
	ESCAPE = None
	mode = 0
	#0 start
	#1 styles
	#2 events

	styles = {} # mapping of style to font

	for line in codopen(fname, "rb", "utf-8"):
		line = line.strip()
		if line == "": continue
		
		#pre
		if mode == 0:
			if line == "[V4+ Styles]":
				mode = 1
				continue
		#styles
		if mode == 1:
			if line == "[Events]":
				mode = 2
				continue
			
			istyle, rest = line.split(":",1)
			if istyle == "Format": continue
			elif istyle == "Comment": continue
			
			rest = rest.strip()
			style, font, rest = rest.split(",",2)
			if style not in styles:
				styles[style] = font
			if fontdb[font] not in Globals.alphabetdict:
				if font not in fontdb: 
					print line
					print "---MISSING FONT in DB: %s" % font
					raise NoU
				Globals.alphabetdict[fontdb[font]] = set([])
			
		#Events
		if mode == 2:
			idia, rest = line.split(":",1)
			if idia == "Format": continue
			
			rest = rest.strip()
			fields = rest.split(",",9)
			style = fields[3]
			text = fields[9]
			
			font = styles[style]
			
			escape = False
			comment = False
			index = 0
			while index < len(text):
				if text[index] == ESCAPE:
					index += 1
					escape = True
					continue
				
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
						for com in commands:
							if com == "fn": font = styles[style]
							elif com[:2] == "fn":
								font = com[2:]
								if font not in fontdb: 
									print line
									print "-MISSING FONT in DB: %s" % font
									raise NoU
								if fontdb[font] not in Globals.alphabetdict:
									Globals.alphabetdict[fontdb[font]] = set([])
					index = end+1
					continue
				charnum = ord(text[index])
				Globals.alphabetdict[fontdb[font]].add(charnum)
				index += 1
	return

def setup(dirname):
	if not exists(dirname) or not isdir(dirname): 
		fontforge.postError("ERROR:", "This is not a folder, or whatever it is, it doesn't exist.\nTry Again.")
		return
	
	if len(listdir(dirname)) == 0:
		fontforge.postError("ERROR:", "There are no files in this folder... You want only subtitle script and commentary script if there is one.")
		return
	for f in listdir(dirname):
		if not fnmatch(f, "*.ass"):
			fontforge.postError("ERROR:", "THERE ARE NON .ASS (lol) FILES IN THIS FOLDER. \nTHIS FOLDER SHOULD ONLY HAVE <=2 ASS FILES. SUBTRAX AND COMMENTARY (if it has commentary.)")
			return
	
	
	fontdb = {}
	for line in codopen(join(Globals.FONTS, Globals.LOOKUPFILE),"rb","utf-8"):
		line = line.strip()
		if not line: continue
		
		friendly, fname = line.split("|",1)
		fontdb[friendly] = fname
	
	for subfile in listdir(dirname):
		genalphabets(join(dirname,subfile), fontdb)
	
	Globals.fonts = Globals.alphabetdict.keys()
	Globals.index = 0
	Globals.refs = set([])
	Globals.keep = set([])
	print "SETTED UP"
				
def loadnext():
	while Globals.index < len(Globals.fonts):
		print "AT INDEX: %s of %s" % (Globals.index, len(Globals.fonts)-1)
		print Globals.fonts
		Globals.tempstuffs = None
		fontname = Globals.fonts[Globals.index]
		if fontname == "MSMINCHO.TTF": 
			print "WARNING BAD FONT: %s" % fontname
			print "EXITING. GET BETTER SCRIPT"
			raise NoU
		
		print "	================"
		#print "	==========", characters
		
		p = join(Globals.FONTS, fontname)
		print "OPENING FONT: %s" % p
		Globals.font = fontforge.open(p)
		font = Globals.font
		
		if font.iscid:
			print "LOL CID INCOMING AAAA"
		Globals.doneref = False
		print "LOADED."
		sleep(3)
		findchars()
		sleep(2)

def loadman():
	print "AT INDEX: %s of %s" % (Globals.index, len(Globals.fonts)-1)
	Globals.tempstuffs = None
	fontname = Globals.fonts[Globals.index]
	if fontname == "MSMINCHO.TTF": 
		print "WARNING BAD FONT: %s" % fontname
		print "EXITING. GET BETTER SCRIPT"
		raise NoU
	print "	================"
	
	p = join(Globals.FONTS, fontname)
	print "OPENING FONT: %s" % p
	Globals.font = fontforge.open(p)
	font = Globals.font
	
	if font.iscid:
		print "LOL CID INCOMING AAAA"
	Globals.doneref = False
	print "LOADED."

def findcharsman():
	font = Globals.font
	alphabetdict = Globals.alphabetdict
	characters = alphabetdict[Globals.fonts[Globals.index]]
	if Globals.tempstuffs == None:
		Globals.tempstuffs = set([])
	
	print "FINDING chars... for this subfont:", font
	nfound = findcharinfont(font, characters)
	Globals.tempstuffs.update(nfound)
	print "Done, do next subfont. If last one, do next option in script menu."
	
def mancheck():
	#check difference
	alphabetdict = Globals.alphabetdict
	characters = alphabetdict[Globals.fonts[Globals.index]]
	diff = characters.difference(Globals.tempstuffs)
	if diff:
		print "FONT () DOES NOT HAVE: "
		for uni in diff:
			unichar = unichr(uni)
			try:
				print "%s - %s" % (unichar, name(unichar))
			except:
				print "%s - NO NAME?" % unichar
	Globals.font.close()
	Globals.index += 1
	if Globals.index >= len(Globals.fonts):
		fontforge.postError("Done.", "Done, no more fonts to check.")
	else:
		print "Done. Feel free to load next font."
	
def findcharinfont(font, characters):
	found = set([])
	for gname in font:
		if gname in font:
			if font[gname].unicode >= 0:
				if font[gname].unicode in characters:
					found.add(font[gname].unicode)
					#make sure to keep all variants (And their references?)
					sleep(0)
	return found
	
	
def findchars():
	print "FINDING CHARS"
	alphabetdict = Globals.alphabetdict
	characters = alphabetdict[Globals.fonts[Globals.index]]
	font = Globals.font
	found = set([])
	if font.iscid:
		print "lol cid"
		for x in range(font.cidsubfontcnt):
			font.cidsubfont = x
			print x, ":", font
			sleep(1.5)
			nfound = findcharinfont(font, characters)
			found.update(nfound)
			sleep(1.5)
	else:
		nfound = findcharinfont(font, characters)
		found.update(nfound)

	#check difference
	diff = characters.difference(found)
	if diff:
		print "FONT () DOES NOT HAVE: "
		for uni in diff:
			unichar = unichr(uni)
			try:
				print "%s - %s" % (unichar, name(unichar))
			except:
				print "%s - NO NAME?" % unichar
	font.close()
	Globals.index += 1
	if Globals.index >= len(Globals.fonts):
		fontforge.postError("Done.", "Done, no more fonts to check.")
	else:
		print "Done. Feel free to load next font."