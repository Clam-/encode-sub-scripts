from imp import find_module, load_module
(f, pathname, description) = find_module("checkscripts", ["/home/mayuri/substuff/fonts/module/check"])
checkscripts = load_module("checkscripts", f, pathname, description)

import fontforge
source = fontforge.askString("Folder with scripts", "Where is dir with scripts?", "/home/mayuri/substuff/")
checkscripts.setup(source)