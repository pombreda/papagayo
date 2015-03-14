# Building Windows Binaries using Py2exe on Linux (Ubuntu) #

I'm going assume you've already followed the instructions on how to InstallFromSource install from source.  For building the Windows binary version using wine you are going to need to install wine for your distribution.  In Ubuntu I did:

```
sudo apt-get install wine1.2
```

You'll then need to install the normal dependencies for running Papagayo on Windows into your system for use by Wine.  Additionally you're going to need to install some binaries for py2exe as well.

  * [Python 2.6](http://www.python.org/ftp/python/2.6.6/python-2.6.6.msi)
  * [wxPython 2.8 Unicode](http://downloads.sourceforge.net/wxpython/wxPython2.8-win32-unicode-2.8.11.0-py26.exe)
  * [pyaudio 2.3 for Python 2.6](http://people.csail.mit.edu/hubert/pyaudio/packages/pyaudio-0.2.3.py26.exe)
  * [py2exe](http://sourceforge.net/projects/py2exe/files/py2exe/0.6.9/py2exe-0.6.9.win32-py2.6.exe/download)

For the python installer you need to use msiexec:

```
msiexec python-2.6.6.msi
```

For the others you use wine directly:
```
wine <installer exe file>
```

Next you move back to the papagayo source directory and using the copy of python installed for use with wine you do:
```
wine ~/.wine/drive_c/Python26/python.exe setup.py py2exe -d "output"
```

Your finished executable will end up in a subdirectory called "output" inside the source directory.

## Current Issues ##

There are some problems that I'm still sorting out in this process.  The first is that the dependent dlls done's seem to copy correctly from the various places they are found in wine's C: drive (~/.wine/drive\_c).  For now I've resorted to manually copying what I need.  The current dll dependencies are:
```
~/.wine/drive_c/windows/system32/python26.dll
~/.wine/drive_c/Python26/Lib/site-packages/wx-2.8-msw-unicode/wx/wxbase28uh_vc.dll
~/.wine/drive_c/Python26/Lib/site-packages/wx-2.8-msw-unicode/wx/wxbase28uh_net_vc.dll
~/.wine/drive_c/Python26/Lib/site-packages/wx-2.8-msw-unicode/wx/wxmsw28uh_core_vc.dll
~/.wine/drive_c/Python26/Lib/site-packages/wx-2.8-msw-unicode/wx/wxmsw28uh_adv_vc.dll
~/.wine/drive_c/Python26/Lib/site-packages/wx-2.8-msw-unicode/wx/wxmsw28uh_html_vc.dll
```

The other problem is that the current version of the setup.py script doesn't deal with copying over the resources.  Hopefully I can fix this soon.