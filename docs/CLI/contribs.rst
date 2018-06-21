Export whatsnew page
====================

This command will load all contributions made in the last 24 hours

Command line
------------

.. code-block:: bash

    campbot contribs


Optional arguments
------------------

* ``--starts=2017-12-07`` : will export all contributions after this date (included)
* ``--ends=2017-12-07`` : will export all contributions before this date (excluded)
* ``--out=data.csv`` : out file name, default value is contributions.csv


Output
------

.. code-block:: csv

    timestamp;type;document_id;version_id;document_version;title;quality;username;lang
    2017-12-21T21:49:41.363647+00:00;routes;293549;1738922;4;Escalades à Presles;medium;charles b;fr
    2017-12-20T21:49:41.363647+00:00;routes;123;123;4;Escalades à Presles;medium;munch;fr