The current plan is very very simple:
  * restore the basic functionality of Papagayo without dependencies on Lost Marble's proprietary library.  This will allow building and use of Papagayo on whatever hardware people have (and would allow for future inclusion of Papagayo as a package in a distribution such as Debian).
  * integrate functionality from other Papagayo mods that have been created
    * the [additional language support by myles](http://www.lostmarble.com/forum/viewtopic.php?t=5056)
    * modifications found in [PapagayoMOD](http://nyian.blogspot.com/2007/04/papagayomod-1353.html)

This work will include modularization of language handling (these are now based on configuration files and it is possible to easily add new languages that are based on dictionaries or on breakdown modules (though I think I should rework breakdowns to support adding them without having to precompile them into the system.  This will make supporting extra ones easier for users of prebuilt Papagayo binaries.

The export capabilities need to be modularized in a similar way to support arbitrary numbers of exporters.