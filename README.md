# Output data files

All output data files can be found at: `//gdsl.gladstone.internal/gdsl/GICD/Common Use/Samad Lotia/metrics`

# Setting up your environment

__Note__: You will need Python 2.7 to run the scripts.

The scripts depend on a number of Python libraries. All of them can be installed using `pip`, an easy-to-use tool for installing third-party Python libraries.

1. Make sure pip is installed first: `easy_install pip`
1. Install the needed libraries: `pip install ipython lxml numpy pandas python-dateutil python-igraph requests requests-cache scipy suds`

(We recommend using the [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/) tool so that these libraries are installed locally.)

# Creating an input file for top-down network generation
Here we'll use the Ivacaftor/Kalydeco drug as an example.

1. Go to the [FDA drug site](http://www.accessdata.fda.gov/scripts/cder/drugsatfda/) and search for *Kalydeco*.
1. Click on *Approval History, Letters, Reviews, and Related Documents*.
1. Under the *Approval* item (at the end), click on *Review*. (http://www.accessdata.fda.gov/drugsatfda_docs/nda/2012/203188s000TOC.cfm)
1. Click on *Medical Review (PDF)*. (http://www.accessdata.fda.gov/drugsatfda_docs/nda/2012/203188Orig1s000MedR.pdf)
1. Use the *poppler-util* package's *pdftotext* command to extract the text from the PDF.
1. Copy the *Literature Review/References* section of the text file to its own file `input/Ivacaftor-FDA-NDA-Medical.txt`.
1. Put the name of the drug (`Ivacaftor`) as the first line in the text file above.