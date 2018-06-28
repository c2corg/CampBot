Export a list of document
=========================

Export to a csv file all documents given by camptocamp URL

Command line
------------

.. code-block:: bash

    campbot export <url> [--out=<filename>] [--delay=<seconds>]

* ``<url>`` is a camptocamp url, like https://www.camptocamp.org/routes#a=523281
* ``<filename>`` is the output file. By default, it will be ``outings.csv`` for outings, ``routes.csv`` for routes...
* ``<seconds>``, numerical, is the delay between each request. 3s by default.

Output
------

here is a sample of output::

    date_start;date_end;title;equipement_rating;global_rating;height_diff_up;rock_free_rating;condition_rating;elevation_max;img_count;quality;activities
    2017-11-20;2017-11-20;Calanque de Morgiou - Le Cancéou : Aven du Cancéou - Prends moi sec au-dessus du lagon bleu;;D+;100;5c;excellent;None;0;draft;rock_climbing
    2017-11-19;2017-11-19;Calanque de Sormiou - Dièdre Guem : Voie NTD;;TD+;140;6c+;excellent;N 