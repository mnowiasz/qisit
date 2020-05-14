# qisit
## A PyQT recipe manager
![Recipe front](docs/screenshots/recipefront.png)

Qisit is a kind-of spiritual successor to [Gourmet](https://github.com/thinkle/gourmet) - Qisit is able 
to import Gourmet's database without losing any data so you can continue using your recipes collection.

### Why Qisit?
I was a long-term user of Gourmet (after migrating my recipes from Krecipes, 
another dead project) when it became clear that Gourmet wasn't developed any more - the original
author had a completely different approach planned for [Gourmet 2.0](https://github.com/thinkle/gourmet/issues/897)
basically a [web based community with mobile clients](https://github.com/thinkle/gourmet/wiki/Gourmet-2.0---Web-Based-Version---Brainstorm). 

Unfortunately, the already exiting product - Gourmet 1 - has a major problem: It's still based on python 2.7 and 
PyGtk2 which isn't supported anymore, therefore making it increasingly difficult to even run the program (obsolete
libraries conflicting with newer ones, and so on), installing it from scratch is next to impossible. Since I didn't
want to lose my personal recipe collection I decided to do something about it. My first idea was to fork Gourmet and 
port it to Python 3.x, unfortunately that wasn't feasible - it would have taken too much time and a complete rewrite 
of the code. Since time was an essential factor (deprecation of Python 2.7) I decided to start from scratch with the 
goal of importing all Gourmet's recipes. 