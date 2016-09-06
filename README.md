## Ubiqu+Ity Offline Edition

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
