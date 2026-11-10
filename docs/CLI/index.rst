Command line interface
======================

Here is the help you get by typing ``campbot -h`` in your command line tool.
Each command has its own help, for instance ``campbot clean -h``:

.. code-block:: bash

    usage: campbot [-h] COMMAND ...

    CampBot, Python bot framework for camptocamp.org

    positional arguments:
      COMMAND
        report_rc  Make quality report on recent changes.
        clean_rc   Clean recent changes.
        clean      Clean documents.
        report     Make quality report on documents.
        contribs   Export all contributions in a CSV file.
        export     Export all documents in a CSV file.

    options:
      -h, --help   show this help message and exit

    environment variables:
      CAMPBOT_LOGIN, CAMPBOT_PASSWORD   bot credentials, used when --login and
                                        --password are not given
      CAMPBOT_CREDENTIALS               "login@password", same as above
      HTTPS_PROXY                       proxy used for all requests

All commands accept ``--delay=<seconds>``, the minimum delay between each request, and ``--user-agent=<name>``.
If you run CampBot from your own tool or script, ``--user-agent`` names it in the requests: see :doc:`/API/CampBot`.

.. toctree::
   :maxdepth: 1

   export
   contribs
   clean
   report_rc