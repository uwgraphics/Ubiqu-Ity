## Ubiqu+Ity Offline Edition

### Summer 2021 Addendum

Mike Gleicher tried (and used) this tool in the summer of 2021.

Some things worth remembering:

1. Ubiquity was built to be an online system that stopped working.
   It used a complex server architecture that was not sustainable.
2. This version was meant to be a **minimal subset** of Ubiquity that did
   its most important task: tagging a set of text files.
3. In creating this version, Erin left a lot of the unnused code in place:
   the goal was to make as little change as possible. A lot of unneeded
   stuff is included.
4. As of today, the GitHub dependency problems are all for JS pieces that
   were only used by the online system.

To make this work:

1. The Docuscope files need to go into `Data/Docuscope` - but they need
   to be in a directory, whose name is used as a command line argument.
   So, for example, I put the files I downloaded from GitHub (below)
   in a directory called "321" (since it was Docuscope v3.21)
2. It does need Python 2.7. You can create a Python 2.7 environment
   using conda (from Anaconda). You don't need all of Anaconda (which)
   is huge, but just flask, pandas, and unicodecsv. `conda install flask`
   (and so forth) is sufficient.
3. I stripped out some things that prevented it from working without
   all the online infrastructure. But a lot of excess stuff remains.
4. The ngrams do not seem to generate row-per-file csv files.

### Original Notes:

 *written and maintained by Erin Winter (wintere@cs.wisc.edu)*
  
 This tool requires **Python 2.7** and a command line interface. Anaconda -- a distribution of Python and many useful packages -- is recommended. This repository has a subset of the files required for running Ubiqu+Ity on a server because it is intended for offline, command-line use instead. Basic command line proficiency is assumed.

### How to use Ubiqu+Ity's tagging functionality
1. Open a command prompt and navigate to the "Ubiqu+Ity/Ubiqu" folder.
2. Run `python tagCorpus.py -h` to get a list of suggested arguments and their descriptions.
3. Make sure to follow the instructions for downloading the Docuscope dictionary below if you would like to use the open source version of Docuscope for text tagging, as we can't distribute it with Ubiqu+Ity.

### How to install the Docuscope dictionary for command line use:

1. Go to https://github.com/docuscope/DocuScope-Dictionary-June-26-2012 and click the download option from the "Clone or Download" menu.
2. Once you have the dictionary, create a folder named "Docuscope" in "Ubiqu+Ity\Data" folder.
3. Move the files from the download to the Docuscope directory.
4. Pass in the name of the dictionary directory as an --docuscope_version argument OR name the folder default.
