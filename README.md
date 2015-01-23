# Output data files

All output data files can be found at: `//gdsl.gladstone.internal/gdsl/GICD/Common Use/Samad Lotia/metrics`

# Setting up your environment

__Note__: You will need Python 2.7 to run the scripts.

The scripts depend on a number of Python libraries. All of them can be installed using `pip`, an easy-to-use tool for installing third-party Python libraries.

1. Make sure pip is installed first: `easy_install pip`
1. Install the needed libraries: `pip install ipython lxml numpy pandas python-dateutil python-igraph requests requests-cache scipy suds`

(We recommend using the [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/) tool so that these libraries are installed locally.)

# The top-down network generation workflow
A *top-down network* has these layers:

1. The drug itself.
1. The FDA NDA (New Drug Application) and all clinical trials classified under the given drug.
1. All articles referenced by the FDA NDA and clinical trials. Includes authors, institutions, and grant agencies connected to each article in this layer.
1. All articles that are in the bibliographies of each article above. Includes authors, institutions, and grant agencies connected to each article in this layer.

## Top-down from a drug's FDA NDA

The top-down script can automatically retrieve all articles referred by clinical trials for a given drug. However, it cannot automatically create a bibliography list of the FDA NDA. That must be done manually. Thus the input file for the top-down script contains: a) the drug name b) the articles referred by the FDA NDA. Input files that have already been generated are located in the `input/` directory.

### Create the input file

Here we'll use the Ivacaftor/Kalydeco drug as an example.

1. Go to the [FDA drug site](http://www.accessdata.fda.gov/scripts/cder/drugsatfda/) and search for *Kalydeco*.
1. Click on *Approval History, Letters, Reviews, and Related Documents*.
1. Under the *Approval* item (at the end), click on *Review*. (http://www.accessdata.fda.gov/drugsatfda_docs/nda/2012/203188s000TOC.cfm)
1. Click on *Medical Review (PDF)*. (http://www.accessdata.fda.gov/drugsatfda_docs/nda/2012/203188Orig1s000MedR.pdf)
1. Use the *poppler-util* package's *pdftotext* command to extract the text from the PDF.
1. Copy the *Literature Review/References* section of the text file to its own file `input/Ivacaftor-FDA-NDA-Medical.txt`.
1. Put the name of the drug (`Ivacaftor`) as the first line in the text file above.

The references must follow the *CSE* citation format: `3. Riordan JR, Rommens JM, Kerem B. Identification of the cystic fibrosis gene: cloning and characterization of complementary DNA. Science 1989, Sep 8; 245(4922):1066-73.`

### Run top-down

To generate the network, run the top-down script:

    python src/topdown.py --format cse --levels 2 input.txt output.pklz

The network file will be stored in `output.pklz`. If you want to open this network in Cytoscape, first convert it to XGMML:

    python src/xgmml.py output.pklz output.xgmml

## Top-down from a list of PMIDs

Instead of creating a top-down network from an FDA NDA, you can create one from a list of PMIDs. This is useful for getting a network of peripheral articles.

### Create the input file

Create a text file listing each PMID on a separate line.

### Run top-down 

    python src/topdown.py --format pmid --dont-search-trials --levels 2 input.txt output.pklz

# A summary of each script

* **topdown.py**

    Takes a list of CSE references or PMIDs and creates a top-down network. The network is stored in the `pklz` format.

* **xgmml.py**

    Takes a `pklz` file and converts it into an `xgmml` file.