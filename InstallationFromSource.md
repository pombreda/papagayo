# Installation From Source #

## Windows ##

First you will need to install the various dependencies.  These are:
  * [Python 2.6](http://www.python.org/ftp/python/2.6.6/python-2.6.6.msi)
  * [wxPython 2.8 Unicode](http://downloads.sourceforge.net/wxpython/wxPython2.8-win32-unicode-2.8.11.0-py26.exe)
  * [pyaudio 2.3 for Python 2.6](http://people.csail.mit.edu/hubert/pyaudio/packages/pyaudio-0.2.3.py26.exe)

Sources are available in the project's downloads or you will need to get the current sources from our SVN repository.  This can be done with either the svn command line tool or TortoiseSVN.

Once you've unzipped or checked out the sources go into the directory where you did this and run:
```
python papagayo.py
```

This should start up the application.  If you get a complaint about python not being an application you need to either add the C:\Python26 directory to your path or run it like this instead:
```
C:\Python26\python papagayo.py
```

## Linux (Ubuntu) ##

For Linux users the process is similar.  You will first want to install the various dependencies and subversion if you don't have it already.

```
sudo apt-get install subversion python-dev python-wxgtk2.8 python-setuptools
```

You will also need to install pyaudio which doesn't have a ubuntu package, but can be acquired pretty easily using easy\_install
```
sudo easy_install pyaudio
```

Then just pop over into the directory where you checked out the code and run:
```
python papagayo.py
```