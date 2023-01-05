Supported Format Conversion
==========================================================

Determine the file format
----------------------

User Supplied
~~~~~~~~~~
The user may choose which type each of the file is on the front end. This option has highest priority.

File Extension
~~~~~~~~~~
The track type is first guessed from the file extension.
Expected file extensions are:
bed, bigbed, ...

File Content
~~~~~~~~~~
If the file extension does not indicate file type, the service can try its best to figure out the file format.


Conversion Process
----------------------

BedGraph -> BigWig
~~~~~~~~~~
By UCSC Kent Tool - BedGraphToBigWig

Wig -> BigWig
~~~~~~~~~~
By UCSC Kent Tool - WigToBigWig

Bismark cov file -> Methylc Track
~~~~~~~~~~

The cov file is converted to methylc (a bed-like) format by python script.
For hg38, the service can tell which strand cytosine is on.
For all other genome, the service assumes all cytosines are on positive strand.

Example cov lines are below::

    chr1	10004	10004	0	0	2
    chr1	10006	10006	66.6	20	10
    chr1	10008	10008	100	1	0

Example methylc lines are below::

    chr1	10004	10004	CG  0.00	+	2
    chr1	10006	10006	CG  66.6	-	30
    chr1	10008	10008	CG  100.	+	1


Bed like format
~~~~~~~~~~
Sorted, and processed by tabix.

Processed files
~~~~~~~~~~
They are uploaded, and served to browser directly.
Example: bigwig, bigbed, hic



