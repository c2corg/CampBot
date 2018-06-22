Check (and clean) recent changes
================================

Check that last day modifications pass these tests :

* History is filled
* No big deletions
* Pitch type is set
* Warning for new users
* all patterns present in the first message of topic where report should be posted

Also, all corrections made by :doc:`clean </CLI/clean>` procedure.

Report will be posted on https://forum.camptocamp.org/t/topoguide-verifications-automatiques/201480

Command line
------------

.. code-block:: bash

    campbot check_rc <days> [--login=<login>] [--password=<password>] [--delay=<seconds>]

Arguments and options
---------------------

* ``<days>`` : Number of day to check Let says that we are on 17 june 2018, 12h. if ``<days>`` is ``2``, the process will run on all contributions made from ``2018-06-15 00:00:00`` to ``2018-06-16 23:59:59``
* ``<login>`` : your bot login
* ``<password>`` : your bot password
* ``<delay>`` : delay, in seconds between each request. By defaut, 3 seconds 
