Installation On Your Own Machine
==========================================================

Option 1: Docker Container
----------------------
..  code-block:: bash

    docker run -p 10981:10981 wenjin27/egh

.. important:: Make sure the port 10981 is available on your local machine

Option 2: Pure Python
----------------------
We recommend use Python 3.7

..  code-block:: bash

    git clone git@github.com:Hendricks27/egh.git
    cd src
    pip install -r requirement.txt
    python3 browserhelper_local.py

.. important:: Make sure the port 10981 is available on your local machine


Browser Side Settings
----------------------
Because of the self-signed certificate, ...

Chrome
~~~~~~~~~~
Open the URL ( chrome://flags/#allow-insecure-localhost ) in your browser.
And set 'Allow invalid certificates for resources loaded from localhost.' enabled

Edge
~~~~~~~~~~
Open your browser edge://flags/#allow-insecure-localhost, and do the same for chrome.

Safari & Firefox
~~~~~~~~~~
No special tweaks required.



Ready To Go
----------------------
Open your browser https://localhost:10981


