# Database
Table | Purpose
-----|-------
| [author](../../src/qisit/core/db/data/author.py) | Authors for recipes |
| [category](../../src/qisit/core/db/data/category.py) | Categories for recipes | 
| [category_list](../../src/qisit/core/db/data/category_list.py) | Categories that a recipe has |
| [cuisine](../../src/qisit/core/db/data/cuisine.py) | Cuisines for recipes | 
| [ingredient](../../src/qisit/core/db/data/ingredient.py) | A "generic" ingredient  |
| [ingredient_list_entry](../../src/qisit/core/db/data/ingredient_list_entry.py) | The ingredients for a recipe |
| [ingredient_unit](../../src/qisit/core/db/data/ingredient_unit) | A (amount) unit for an ingredient on the recipe's list of ingredients |
| [meta](../../src/qisit/core/db/data/meta.py) | Meta information, like version |
| [recipe](../../src/qisit/core/db/data/recipe.py) | Recipes |
| [recipe_images](../../src/qisit/core/db/data/recipe_image.py) | Images/pictures for a recipe |
| [yield_unit_ name](../../src/qisit/core/db/data/yield_unit_name.py) | A unit for yields (e.g. loaf, serving, ...)

## Overview
This the database's diagram (taken from sqlite):
![Overview](overview.svg)