from sys import argv, exit

if len(argv) != 2:
	print "Need RGB value only"
	exit(1)
	
rgb = argv[1][1:]

r = rgb[:2]
g = rgb[2:4]
b = rgb[4:6]

print "&H%s%s%s&" % (b,g,r)