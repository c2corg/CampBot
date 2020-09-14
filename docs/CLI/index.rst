Command line interface
======================

Here isthe help you get by typing ``campbot`` in you command line tool :

.. code-block:: bash

    CampBot, Python bot framework for camptocamp.org

    Usage:
      campbot clean_rc <days> [--login=<login>] [--password=<password>] [--delay=<seconds>] [--batch]
      campbot report_rc <days> [--login=<login>] [--password=<password>] [--delay=<seconds>] [--batch]
      campbot clean <url_or_file> <langs> [--login=<login>] [--password=<password>] [--delay=<seconds>] [--batch] [--bbcode]
      campbot contribs [--out=<filename>] [--starts=<start_date>] [--ends=<end_date>] [--delay=<seconds>]
      campbot export <url> [--out=<filename>] [--delay=<seconds>]


    Options:
      --login=<login>           Bot login
      --password=<password>     Bot password
      --batch                   Batch mode, means that no confirmation is required before saving
                                Use very carefully!
      --delay=<seconds>         Minimum delay between each request. Default : 3 seconds
      --bbcode                  Clean old BBCode in markdown
      --out=<filename>          Output file name. Default value will depend on process


    Commands:
      report_rc     Make quality report on recent changes.
      clean_rc      Clean recent changes.
      clean         Clean documents.
                    <url_or_file> is like https://www.camptocamp.org/routes#a=523281, or, simplier, routes#a=523281. 
                    filename is also accepted, and must be like : 
                    123 | r
                    456 | w
                    <langs> is comma-separated lang identifiers, like fr,de for french and german.
      contribs      Export all contribution in a CSV file. <start_date> and <end_date> are like 2018-05-12
      export        Export all documents in a CSV file.
                    <url> is like https://www.camptocamp.org/outings#u=2, or, simplier, outings#u=2


.. toctree::
   :maxdepth: 1

   export
   contribs
   clean
   report_rc