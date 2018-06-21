Search documents that contains... 
=================================

Based on :doc:`get document sample </recipes/get_documents>`, here is the code to search for text. This code is very slow, but may do the job for a small set of documents 

.. code-block:: python

    from campbot import CampBot
    
    bot = CampBot(use_demo=True)
    
    # Here is the text to search 
    needle_text = "aiguille dans une botte de foin"

    # Use a pre-filter, otherwise, it will never end 
    filters = {
        "a": 14405, 
        "act":["rock_climbing", "mountain_climbing"]
    }
    
    for route in bot.wiki.get_routes(filters):
        locale = route.get_locale("fr") # we will search only french text 

        if locale: # document may not contain french version
            for field in locale:
                if locale[field] is not None: # field may be set to None 
                    if needle_text in locale[field]:
                        print(route)
