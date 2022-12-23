Remarque importante concernant l'importation de ce module par les scripts python
================================================================================

Actuellement les scripts perl travaillent avec l'environnement anaconda qui est propre
a chaque utilisateur

Ainsi pour lancer un utilitaire python (ex: tcs_srv) on utilise la commande suivante:

/home/weber/anaconda3/bin/python /home/weber/src/tcs_srv/tcs_srv.py


le script python lui code ceci:

import sys
sys.path.append("/home/weber/src/pymod_libgop/")
import pymod_libgop

Tout cela est certainement a ameliorer afin de travailler en beta



Installation et utilisation (preliminaires)
===========================================

etre sous bash, car c'est /home/weber/.bashrc qui definit le path de anaconda3
(
	# added by Anaconda3 installer
	export PATH="/home/weber/anaconda3/bin:$PATH"
)

cd src/pymod_libgop/

on utilise les sources de ../libgop


Compilation (python3)
---------------------
swig -python pymod_libgop.i

gcc -c -fPIC -Wall -DUSE_STRERROR -DSELECT_CALL -DSYSV -DLINUX ../libgop/libgop.c  pymod_libgop_wrap.c -I../libgop -I/home/weber/anaconda3/include/python3.6m

ld -shared libgop.o pymod_libgop_wrap.o -o _pymod_libgop.so


Test avec processes
-------------------

processes &

python

```
 import pymod_libgop
 pymod_libgop.gop_process_registration("salut",10,"poilu",2,3)
 quit()
```


Test client server
------------------
Sur glslogin1 ou gvanuc1, lancer 2 terminaux (en bash si le path de python est defini dans un .bashrc)

Dans un:

```
python test_server.py
```
puis dans l'autre
```
python test_client.py
```

Ce qui est tapé dans la partie client est envoyé au serveur et affiché par celui-client

Dans ce test, les commandes sont parsées selon le premier délimiteur par exemple
```
"|my_command|arg1|arg2"
```
sera affiché par le serveur comme:
```
 "my_command" "arg1" "arg2"
```
Le serveur et le client reconnait des commandes simple pour terminer "quit" et "exit"

Ainsi pour terminer un session de test il faut taper dans le client:
```
\quit
quit
```
Le premier fera terminer le serveur ("\quit" devient "quit") et le deuxieme fera terminer le client.
