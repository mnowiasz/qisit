## Missing features
* While adding new items (category, author, yields, units...) is working perfectly fine, there's 
currently no way to rename/delete/merge them. A data editor for that purpose
will be implemented next
* There's no import/export/print feature (apart from importing Gourmet's db, that is). This is the second highest
priority
* You cannot choose which database system (SQlite, MySQL, PostgreSQL) you want - currently it's sqlite and a database
named "qisit.db" will be created in your home directory. Will be fixed soon

## ToDo
Apart from the missing features above
* Translations (GUI). Just has to be done.
* Icons to ingredients. The database is ready for that. An example:
"tomatoes, chopped", "tomatoes, fresh" and so on all belong to the generic 
ingredient ("ingkey" in Gourmet) "tomato" (this will be later used for 
nutrional calculcations). If the "tomato" ingredient has an tomato shaped icon,
all the ingredient would display this icon - apart from being eye-candy this
could be useful, you can seed at glance what this ingredient is
* Nutritional information, including importing current data from the FDA

## Ideas
* How about ingredient tags? You could specify tags for the generic ingredient. 
For example: You could tag tomatoes, peppers, potatoes as "vegetarian". If all 
ingredients have this tag, the recipe itself would be considered suitable for 
vegetarians. Or for special dietary requirements, and so on.
* Menus. Plan a weekly/monthly menu plan

