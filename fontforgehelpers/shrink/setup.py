from imp import find_module, load_module
(f, pathname, description) = find_module("mfimport2", ["/home/mayuri/substuff/fonts/module/shrink"])
mfimport = load_module("mfimport2", f, pathname, description)

import fontforge
source = fontforge.askString("Folder with scripts", "Where is dir with scripts?", "/home/mayuri/substuff/madomagi")
mfimport.setup(source)
