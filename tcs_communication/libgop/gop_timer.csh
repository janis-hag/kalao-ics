#! /bin/csh -f
#
# @(#)gop_timer 24/06/96 Luc Weber - Observatoire de Geneve
#
# Script pour le lancement de gop_timer.
#
# Voir la description plus bas ou tapez "gop_timer.csh -h | more".
#
#
# definit les variables d'environnement
#
source $T4HOME/scripts/setinitenv.csh

# defaut pour ECHO_EXE
#
if (! $?ECHO_EXE) then
        set ECHO_EXE=""
endif

#
# initialise $GOP_TIMER si unset
#
if (! $?GOP_TIMER) then
	set GOP_TIMER=""
endif

set OPTION=""

#
# test si on demande la version de developpement
#
if (`expr "$GOP_TIMER" : '.*alpha.*'`) then
	setenv EXE ~weber/bin/$OPSYS/gop_timer
	echo " "
	echo "Attention on utilise la version alpha (developpement) de gop_timer:"
	echo $EXE
else if (`expr "$GOP_TIMER" : '.*beta.*'`) then
	setenv EXE $T4ROOT/beta/bin/$OPSYS/gop_timer
	echo " "
	echo "Attention on utilise la version beta (integration) de gop_timer:"
	echo $EXE
else if (`expr "$GOP_TIMER" : '.*ok.*'`) then
	setenv EXE $T4ROOT/ok/bin/$OPSYS/gop_timer
	echo $EXE
else
	setenv EXE $T4HOME/bin/$OPSYS/gop_timer
	if ( "$T4HOME" == "$T4ROOT/beta" ) then
	  echo " "
	  echo "Attention on utilise la version beta (integration) de gop_timer:"
	  echo $EXE
	endif
endif

#
# gestion du help et arret s'il est affiche
#
if ("$1" == "-H") then
        shift
        cat << %%END%%
#
# Script pour le lancement de gop_timer.
#
# USAGE:
# ------
#
#	gop_timer.csh [-h]
#
# DESCRIPTION:
# ------------
#
# Ce script permet de lancer la version stable, la version beta ou la
# version alpha de gop_timer et ceci avec ou sans debugger.
#
# La variable d'environnement "GOP_TIMER" definit le comportement de ce script.
# Si elle n'est pas definie, le script envoie la version stable sans debugger.
#
# Si $GOP_TIMER contient:
#
#		"ok"	   on utilise la version ok (stable)
#		"beta"	   on utilise la version beta (integration)
#		"alpha"	   on utilise la version alpha (developpement )
#		"debug"	   on lance le debugger definit dans $DEBUGGER
#
# Exemple:
# 	pour lancer la version beta avec le debugger, on donne:
#
#		setenv GOP_TIMER "beta+debug"
#
# VARIABLES D'ENVIRONNEMENT:
# --------------------------
#
# Les variables d'environnement suivantes doivent absolument etre predefinies:
#
#	- T4HOME	(file system pour T4)		ex: /ccd2/t4/ok
#	- OPSYS	(Operating System + Version)	ex: SunOS_5.4
#	- DEBUGGER	(Nom du debugger)		ex: debugger
#	- ECHO_EXE	si == "echo" affiche les commandes au lieu de les
#			executer.
#
# Les assignations possibles sont:
#
setenv   GOP_TIMER    "alpha"
setenv   GOP_TIMER    "beta"
setenv   GOP_TIMER    "ok"
setenv   GOP_TIMER    "alpha+debug"
setenv   GOP_TIMER    "beta+debug"
setenv   GOP_TIMER    "ok+debug"
unsetenv GOP_TIMER
setenv   ECHO_EXE "echo"
unsetenv ECHO_EXE
#
# Les assignations peut aussi être décrites dans un fichier. Si on désire
# utiliser un tel fichier, il faut donner son nom dans la variable
# d'environnement INITENV. (format: <nom> <valeur>)
#
#
%%END%%
        echo "# ETAT ACTUEL:"
        echo "# ------------"
        echo "# "
	echo "# "
	echo "# Variables d'environnement utilisées par gop_timer.csh:"
	echo "# "
	echo "#   GOP_TIMER     = $GOP_TIMER"
	echo "# "
	echo "# On lance:"
	echo "# "
	echo "#   $EXE $OPTION $*"
	if (`expr "$GOP_TIMER" : '.*debug.*'`) then
		echo "#   en mode debug (le debugger utilise est: $DEBUGGER)"
	endif
	echo "# "
        echo "#   ECHO_EXE   = " \"$ECHO_EXE\"

	exit
endif

#
# test si on veut le debug
#
if (`expr "$GOP_TIMER" : '.*debug.*'`) then
#
#       on resoud le link
#
	setenv EXE `/bin/ls -l $EXE | awk '{print $NF}'`
	setenv EXE "$DEBUGGER $EXE"

	echo "$EXE"
	echo "Il faut taper les options de gop_timer dans le debugger; c'est a dire:"
	echo "    run $OPTION $*"
	$ECHO_EXE exec $EXE
else
	$ECHO_EXE exec $EXE $OPTION $* &
endif
