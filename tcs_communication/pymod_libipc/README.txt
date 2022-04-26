Remarque importante concernant l'importation de ce module par les scripts python
================================================================================

Actuellement les cripts perl travaillent avec l'environnement anaconda qui est propre
a chaque utilisateur

Ainsi pour lancer un utilitaire python (ex: xxxxx) on utilise la commande suivante:

/home/weber/anaconda3/bin/python /home/weber/src/yyyyy/xxxxx.py


le script python lui code ceci:

import sys
sys.path.append("/home/weber/src/pymod_libipc/")
import pymod_libipc

Tout cela est certainement a ameliorer afin de travailler en beta



Installation et utilisation (preliminaires)
===========================================

etre sous bash, car c'est /home/weber/.bashrc qui definit le path de anaconda3
```
	# added by Anaconda3 installer
	export PATH="/home/weber/anaconda3/bin:$PATH"
```

cd src/pymod_libipc/

on utilise les sources de ../libipc


Compilation (python3)
---------------------
swig -python pymod_libipc.i

gcc -c -fPIC -Wall -DUSE_STRERROR -DSELECT_CALL -DSYSV -DLINUX ../libipc/libipc.c  pymod_libipc_wrap.c -I../libipc -I../gop -I/home/weber/anaconda3/include/python3.6m

ld -shared libipc.o ../gop/libgop.a pymod_libipc_wrap.o -o _pymod_libipc.so


Test 
-------------------
Sur glslogin1 ou gvanuc1, lancer 2 terminaux (en bash si le path de python est defini dans un .bashrc)

Dans un:
```
inter -server -echo
```
Le bloc doit etre charge et le texte "inter (mode serveur) en attente" doit apparaitre

puis dans l'autre terminal
```
python test_ipc.py
```
