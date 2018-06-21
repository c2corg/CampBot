Clean a set of documents
========================

This command line will process all clean processors to objects given by a camptocamp url.


Command line
------------

.. code-block:: bash

    campbot clean <url> <langs> --login=<login> --password=<password> [--delay=<seconds>] [--bbcode]

Options and arguments 
---------------------

* ``<url>`` is like https://www.camptocamp.org/routes#w=940468 : all routes associated to waypoint 940468 will be cleaned. Shorthand ``routes#w=940468`` is accepted.
* ``<langs>`` is a comma-saprated list of langs, like fr,de. Clean procedure will impacts only this langs.

Clean processors
----------------
* https://www.camptocamp.org/articles/996571
* Some letter capitalization
* Spaces between numbers and units


Good advice
-----------

``--delay`` is the time between each API request. By default, it's 3s, which is very low. As it's time consuming, it's preferable to set ``--delay`` to a low value. As you will have to validate each modification, API w'ont be overloaded.

Sample
------

.. code-block:: bash

    campbot clean https://www.camptocamp.org/routes#w=940468 fr --login=rabot --password=fake_pwd --delay=0.1

bbcode 
------

This option clean old good BBCode tags with their markdown equivalents. No more usefull, except for your outings : 

.. code-block:: bash

    campbot clean outings#u=123 fr --login=your_login --password=fake_pwd --bbcode
   

.. warning ::
    ``123`` must be your user numerical id, you can find it in your home page's URL. 