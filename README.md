# Output data files

All output data files can be found at: `//gdsl.gladstone.internal/gdsl/GICD/Common Use/Samad Lotia/metrics`

# Setting up your environment

__Note__: You will need Python 2.7 as your default Python version.

## Preliminary steps

Before installing the needed libraries, make sure your system is ready. The commands below are for Ubuntu.

 * Install compiler tools on your system:

    sudo apt-get install build-essential gfortran

 * Make sure your system has `easy_install`. If it doesn't, you will need *setuptools*:

        sudo apt-get install python-setuptools

 * Install `pip`:

        sudo easy_install pip

 * Install the Python shared libraries and headers:

        sudo apt-get install python-dev

 * Install necessary C libraries:

        sudo apt-get install libz-dev libigraph0-dev libblas-dev liblapack-dev

## Install Python libraries

The scripts depend on a number of Python libraries. All of them can be installed using `pip`.

    pip install ipython lxml numpy pandas python-dateutil python-igraph requests requests-cache scipy suds cssselect

(We recommend using the [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/) tool so that these libraries are installed locally.)

If you're having trouble installing lxml using pip, you can install it with Ubuntu's package manager: `sudo apt-get install python-lxml`.

## Setup the shell

If you're not running Python in virtualenv, you will need to tell Python where to find the `metrics/src` directory. To do so:

    export PYTHONPATH=/path/to/metrics/src


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

The network file will be stored in `output.pklz`. If you want to open this network in Cytoscape, convert it to XGMML:

    python src/xgmml.py output.pklz output.xgmml

## Top-down from a list of PMIDs

Instead of creating a top-down network from an FDA NDA, you can create one from a list of PMIDs. This is useful for getting a network of peripheral articles.

### Create the input file

Create a text file listing each PMID on a separate line.

### Run top-down 

    python src/topdown.py --format pmid --dont-search-trials --levels 2 input.txt output.pklz

## Score top-down networks

The `score.py` script takes a top-down network file and outputs the same network but with each node containing a score attribute.

Article nodes can be scored by:

* **individual**: the article's score is its citation count
* **propagate**: the article's score is its citation count plus the score of any lower-level article that connects to it

Author, institution, and grant agency ("neighbor") nodes can be scored by:

* **sum**: sum the score of all articles that connect to a neighbor node
* **indegree**: the neighbor's score is the number of articles that connect to it

Example of calling `score.py`:

    python src/score.py --article-scoring propagate --neighbor-scoring indegree input.pklz output.pklz

## Publication plots

You can create a histogram plot of the publication dates from articles in a network file using the `articlestats.py` script.

Create three separate CSV files: one containing all article publication dates, another only for articles marked as clinical trial, and another for articles not marked as clinical trial.

    python src/articlestats.py output.pklz article_years.csv pmid pubdays
    python src/articlestats.py --filter clinical-only output.pklz clinical_article_years.csv pmid pubdays
    python src/articlestats.py --filter non-clinical-only output.pklz non_clinical_article_years.csv pmid pubdays

Use the `article_years_plot.R` command:

    R CMD src/article_years_plot.R

The R script expects the `article_years.csv`, `clinical_article_years.csv`, and `non_clinical_article_years.csv` files to be in the current directory. It will create the file `article-years.pdf` in the current directory when it finishes.

# Bottom-up network generation workflow

A *bottom-up network* has these layers:

1. An author
2. All articles written by the author above. Included are co-authors, institutions, and grant agencies connected to each article in this layer.
2. (Only two-level.) Another layer of articles that cite the articles above. Included are authors, institutions, and grant agencies connected to each article.

## Running bottom-up on a single author

The bottom-up script needs an author name and an institution. Here's an example of how to run the bottom-up script on a single author:

    python src/bottomup.py --levels 2 "Pico AR" "gladstone" output.pklz

The network file will be stored in `output.pklz`. If you want to open this network in Cytoscape, convert it to XGMML:

    python src/xgmml.py output.pklz output.xgmml

## Running bottom-up on many authors

Create an input file that follows this format:

    Author-A
    Institution-A
    Output/Path/A.pklz
    Author-B
    Institution-B
    Output/Path/B.pklz
    ...

Run the pipeline script:

    sh src/bottomup-pipeline.sh input-scripted.txt

Note: The pipeline script creates one-level networks for each author. If you want to change this, open this file and look at line 15, which invokes `bottomup.py`. You can change the number of levels there.

## Create a random sample list of authors from MeSH terms

The `authorssample.py` script will:

1. Collect all articles published under the given MeSH terms.
1. Create a list of last authors from each article.
1. Randomly sample from this list based on the given sample size.
1. Output the author's name and the five most common institutions affiliated with the author's articles under the given MeSH term.

Here's an example of how to run it:

    python src/authorssample.py --output random-authors-and-institutions.txt --num-samples 200 --mesh-terms anticoagulant thrombosis

Adding more than one MeSH term will do an *and* operation across all the terms.

The output file can then be converted into the bottom-up pipeline input file (described above) using the `pickno1.py` script:

    cat random-authors-and-institutions.txt | python src/pickno1.py > random-authors-scripted.txt

## Output summary statistics about each bottom-up network

The `authormat.py` script takes a list of bottom-up network files and outputs a matrix, with each row containing summary statistics for each given file.

Here's how to run it:

    python src/authormat.py output.csv network-1.pklz network-2.pklz ...

Note that each file path is contained in every third line of the bottom-up pipeline input file. You can get each third line using bash like so:

    while read l; do read l; read l; if [ -f "$l" ]; then echo -ne "\"$l\" "; fi; done < input-scripted.txt

(The above snippet also makes sure that the network file exists.)

Copy the output of the above snippet and paste it after entering `python src/authormat.py output.csv`.

### Remove duplicate authors

Let's say you have two matrices, one containing core author networks and another of peripheral author networks. You want to remove all authors in the peripheral matrix who are core authors. You can do this with the `dupauthors.py` script:

    python dupauthors.py core-matrix.csv peripheral-matrix.csv

This will output all author names that appear in both matrices. You can then delete these duplicated authors from the peripheral matrix.

# Summaries of command scripts

* **articlestats.py**

    Takes a top-down network file as input and creates a CSV file containing information about each article node.

* **authormat.py**

    Creates a summary matrix for each given bottom-up network file. Outputs a CSV file that can be imported into R.

* **authorssample.py**

    Creates a random sample of last authors who published under given MeSH terms. Outputs a file listing each sampled author and top 5 institutions affiliated with the articles published by the given author.

* **bottomup.py**

    Takes an author and his or her institution affiliation and creates a bottom-up network. The network is stored in the `pklz` format.

* **dupauthors.py**

    Lists all duplicated authors across two author matrix files.

* **meshmat.py**

    Takes a network file as input and outputs a CSV file of MeSH term frequency across all article nodes.

* **pickno1.py**

    Processes the text output of `authorssample.py` and converts it into an input file suitable for `bottomup-pipeline.sh`.

* **score.py**

    Takes a top-down network file in the `pklz` format. adds a score attribute to all article, author, institution, and grant agency nodes. Outputs a network file in the `pklz` format.

* **testparse.py**

    Takes an input file of CSE styled references and tries to parse them. Useful for debugging an input file for the top-down CSE workflow.

* **topdown.py**

    Takes a list of CSE references or PMIDs and creates a top-down network. The network is stored in the `pklz` format.

* **xgmml.py**

    Takes a `pklz` file and converts it into an `xgmml` file.

# Infrastructure code

The command scripts above rely on infrastructure code. Here's an explanation of each file:

* **clinicaltrials.py**

    Provides the `Client` class for the clinicaltrials.gov web service.

* **litnet.py**

    Provides the `LitNet` class that makes it easy to generate networks that represent relationships between articles, authors, institutions, and grant agencies.

* **pubmed.py**

    Provides the `Client` class for the PubMed web service.

* **wos.py**

    Provides the `Client` class for the Thomson Reuters Web of Science web service.

* **util.py**

    Utility functions for working with XML files.