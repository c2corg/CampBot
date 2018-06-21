CampBot class
=============

CampBot() class is the main class, you must instanciate a singleton : 

 
.. code-block:: python

    from campbot import CampBot
    
    bot = CampBot()

Optionnal arguments are : 

``CampBot(proxies=None, min_delay=None, use_demo=False)``

* ``use_demo`` – (optional) Boolean, True if you want to use demo API, instead of production API.
* ``min_delay`` – (optional) numeric, the minimum delay in second between each request.
* ``proxies`` – (optional) a key-value dict if your bot is behinD a proxy


Properties
----------

* ``bot.wiki`` : a :doc:`WikiBot instance </API/WikiBot>`
* ``bot.forum`` : a :doc:`Forum instance </API/ForumBot>`
* ``bot.moderator`` : Boolean, True if logged with a moderator account

Methods
-------

``CampBot().login(login, password)``

* ``login`` : 
* ``password`` : 

``CampBot().clean(url, langs, ask_before_saving=True, clean_bbcode=False)``

* ``url`` : 
* ``langs`` : 
* ``ask_before_saving`` : 
* ``clean_bbcode`` : 

``CampBot().export(url, filename=None)``

* ``url`` : 
* ``filename`` : 


``CampBot().export_contributions(starts=None, ends=None, filename=None)``

* ``starts`` : 
* ``ends`` : 
* ``filename`` : 


``CampBot().fix_recent_changes(oldest_date, newest_date, lang, ask_before_saving)``

* ``oldest_date`` : 
* ``newest_date`` : 
* ``lang`` : 
* ``ask_before_saving`` : 
