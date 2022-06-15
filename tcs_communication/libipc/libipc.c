/**
	A l'occase voir si ftshm est correctement traité dans le cas d'un
	client qui accède plusieurs blocs de communication. Il semblerait
	qu'il ne reste trace que du dernier!!!
        
        
**/

#include <features.h>	// usage pour semtimedop (voir man feature_test_macros)

#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <unistd.h>
#include <errno.h>
#ifdef    SYSV
#include <string.h>
#else
#include <strings.h>
#endif				/* SYSV */
#include <sys/types.h>
#include <signal.h>
#include <time.h>
#include <sys/time.h>
#include <malloc.h>
#include <alloca.h>

#define __USE_GNU 1	// for declaration of: semtimedop (see /usr/include/sys/sem.h)
#include <sys/ipc.h>
#include <sys/sem.h>
#include <sys/shm.h>

#include <ipcdef.h>
#include <gop.h>


#define TRUE 1
#define FALSE 0


/**

	Ces diverses fonctions permettent  d'utiliser un programme
	interactif (Inter) travaillant sur un tableau de reels, depuis
	un ou plusieurs clients travaillant de maniere asynchrone.

	Un type de client (ex:module d'acquisition) remplis la zone commune
	lorsque Inter est pret a travailler. Il remplis egalement le
	tableau de keywords en donnant les characteristiques des
	donnees transferees ainsi que la commande que devra executer
	Inter sur ces donnees (nom d'un fichier de procedure, ex:"@FLAT").

	Un autre type de client (l'interface utilisateur graphique) peut envoyer
	des commandes de maniere interactive.

	Les commandes peuvent etre envoyee selon deux modes,

		- attente de reponse (handshake)
		- sans attente

	Les clients peuvent acceder au variable interne d'Inter(keyword)
	dans ce cas le client est stoppe jusqu'a qu'Inter lui reponde.

	Ce dernier type d'acces est utilise lors de l'initialisation
	pour connaitre la taille de la zone memoire reservee par Inter.

	Ces fonctions permettant la mise en commun de 2 zones
	de memoires partagees entre un serveur et plusieurs clients.
	L'acces a ces zones est gere par un jeu de 3 semaphores.


		- La premiere zone sert a stocker des keywords et
		le PID du programme serveur. (ID=block_key)

		- La seconde zone sert a stocker les donnees: vecteur
		de reels. (ID=matrix_key)

	La configuration est la suivante:

		- La gestion de la mise en commun est realisee par deux
		semaphores No 0, No 1 et No 2. (sem_key).

			Le No 0 definit la disponibilite de la
			memoire partagee. (Il bloque les clients)

			Le No 1 definit la disponibilite de donnees
			dans la memoire. (Il bloque le server)

			Le No 2 indique la disponibilite de keywords
			resultant d'une interrongation sur le serveur.
			(mis a un par le client avant de passer la main
			au serveur puis mis a zero par le serveur lorsque
			la reponse est a disposition. Le client est attente
			sur la valeur zero)

	Ainsi un nombre indetermine de clients peuvent acceder cette zone.

	Derroullement lors du lancement d'une commande (et utilisation de la memoire)
	SANS demande de reponse du serveur:

		1) Un programme serveur est en attente sur les zones
		de memoires. (dec_sem(1))

		2) lorsqu'un client desire acceder la memoire, il se met
		en attente sur le semaphore No 0. (dec_sem(0))

		3) lorsqu'un client a termine son acces memoire, il pose le semaphore
		No 2 a 1 (setval_sem) pour dire que le serveur travaille puis il met
		le semaphore No 1 ready pour que la memoire soit accessible
		par le serveur (inc_sem(1)). Cela fait partir le serveur.

		4) lorsqu'un serveur a termine son acces memoire, il pose le semaphore
		No 2 a 0 (setval_sem) pour dire qu'il a fini, libere le
		semaphore No 0 (inc_sem(0)), et se remet en attente (point 1)

	Deroullement lors du lancement d'une commande (et utilisation de la memoire)
	AVEC demande de reponse du serveur:

		1) identique

		2) identique

		3) identique, et pose block->ackno=1

		4) le client attend que le semaphore 2 vaille 0.

		5) Detection de la valeur de  block->acknopuis, lorsque le
		serveur a termine son acces memoire, il pose le semaphore
		2 a 0. Cela fait continuer le client.

		6) le client lit les keywords puis libere le semaphore No 0 (inc_sem(0)).



	Par exemple:

		- Inter est le serveur

		- le module d'acquisition est le client envoi de commandes et
		de donnees

		- le user interface est aussi un client et envoie des commande


	On peut aussi envoyer un CTRL-C au server (send_ctrlc()).

	Les indentificateurs sont hardcodes (voir sem_key, block_key, matrix_key)

	status de retour = -1 si erreur.


**************************************************************

Traitement des erreurs provenant de Inter
-----------------------------------------

Si une erreur survient sous inter la variable de block de
communication est posee a 1

	block->err_server == 1

et le message d'erreur (affiche par inter) est place dans

	block->err_str_server    (NULL terminated)

La strategie globale a adopter lors d'un appel a inter est dans
tout les cas :

	Tester "block->err_server" avant de lancer sa commande. S'il
	vaut 1 c'est que la commande precedente c'est mal terminee.
	Normallement la commande, le nom du client, son PID sont
	accessibles. Il faut donc prendre une decision soit a l'aide
	de ces elements, soit avec l'aide de l'utilisateur.

	Si la variable vaut 0, c'est que tout c'est bien deroulle.

Puis lors d'un appel du type:

	- WAIT_FOR_ANSWER: on teste, apres reception de la fin de la
	commande, la variable "block->err_server" est on agit en
	consequence, sachant ce que l'on vient de faire, de maniere
	automatique ou avec l'aide de l'utilisateur. PUIS METTRE A
	ZERO block->err_server !!!! POUR QUE L'ERREUR NE SOIT PAS
	TRAITEE A NOUVEAU PAR LA COMMANDE SUIVANTE (S'IL L'ON
	N'ACCEDE PAS INTER APRES LA DETECTION DE L'ERREUR).

	- NOWAIT_FOR_ANSWER: On ne peut plus rien faire apres avoir
	lance la commande. Donc le test de reussite sera effectue
	par la prochaine commande!

**************************************************************

	UTILISATION DANS un client
	--------------------------

	Voici le squelette des possibilites d'utilisation de ces
	routines dans un client



#include <ipcdef.h>


main()
{
	int             semid;
	char            message[CONTENT_SIZE];
	struct block_kw *block;
	float           *pointer;
	int             i;
	int		timeout=0;

	/ *
	 * INITIALISATION
	 *
	 *
	 * connection sur le semaphore et block de communication
	 * /
	if (init_sem_block(&semid,&block) == -1)
		exit(-1);

	/ *
	 * connection sur la memoire partagee
	 * /
	if (ask_and_init_shm(semid, block, &pointer, timeout, timeout) < 0) {
		stamped_printf("Impossible de se connecter sur la shared memory\n");
		exit(-1);
	}

	/ *
	 * TRAITEMENT
	 * /

	i = 0;
	for (;;) {
		/ *
		 * travail preparatoire, rapatriement des donnees du CCD
		 * par exemple.
		 * /

		/ *..............................* /
		/ *..............................* /
		/ *..............................* /


		/ *
		 * debut de communication avec Inter   vvvvvvvvvvv
                 * le client s'arrete si la
                 * memoire partagee n'est pas accessible
		 * /

		dec_sem_zero(semid,block,timeout);

		/ *
		 * Transfert des donnees du CCD dans la memoire
		 * pour l'exemple, on pose simplement les 2 premieres
		 * positions de la matrice
		 * /

		*pointer       = i++;
		*(pointer + 1) = i++;

		/ *
		 * On passe la commande que doit executer Inter et
		 * divers parametres.
		 * /

		ini_shm_block_kw(block);
		put_shm_block_kw(block, "COMMAND", "show [1](1,1) [1](2,1)");
		put_shm_block_kw(block, "XSIZE", "1024");
		put_shm_block_kw(block, "YSIZE", "1024");
		/ * ...... * /

		/ *
		 * fin transfert a Inter     ^^^^^^^^^^^
		 * le traitement peut continuer
		
		 * /
		inc_sem(semid, 1);


	}
}



**************************************************************

	UTILISATION DANS LE USER INTERFACE
	----------------------------------

	Voici le squelette des possibilites d'utilisation de ces
	routines dans le User Interface (XView)



========== DECLARATIONS

#include <ipcdef.h>

int             semid;
struct block_kw	*block;
float		*pointer;

========== MAIN

main(){
.....
	if (init_sem_block(&semid,&block) == -1)
		exit(-1);
.....
	xv_main_loop(W1_window1->window1);
	exit(0);
}

========== INITIALISATION AVEC INTER

void
init_button(item, event)
	Panel_item	item;
	Event		*event;
{
	int	timeout=0;

	if(ask_and_init_shm(semid,block,&pointer,timeout,timeout) < 0){
		stamped_printf("Impossible de s'attacher sur la shared memory\n");
		exit(-1);
	}
}

========== ENVOI D'UNE COMMANDE SANS ATTENTE

void
execute_button(item, event)
	Panel_item	item;
	Event		*event;
{
	int		timeout=0;

	send_command(semid,block,"MATRIX",FORK_PROCESS,NO_WAIT_FOR_ANSWER,
			timeout);
}

========== ENVOI D'UNE COMMANDE AVEC ATTENTE,
           ex: LECTURE D'UNE VALEUR LOCALE A INTER

void
local_button(item, event)
	Panel_item	item;
	Event		*event;
{
	char            content[80];
	int		timeout=0;

	send_command(semid, block,
                     "show shmput(\"NBPIX\",itoa(nbpix()))",
                     NO_FORK_PROCESS, WAIT_FOR_ANSWER, timeout);
	wait_for_sem(semid, 2, timeout);
	if (get_shm_block_kw(block, "NBPIX", content) == -1) {
		stamped_printf("keyword NBPIX not found\n");
	} else {
		stamped_printf("NBPIX = %s\n", content);
	}
	inc_sem(semid, 0);

}
========== SORTIE DU USER INTERFACE ET D'INTER
void
quit_button(item, event)
	Panel_item	item;
	Event		*event;
{
	int		timeout=0;

	send_command(semid,block,"QUIT",NO_FORK_PROCESS,WAIT_FOR_ANSWER,
		timeout);
	wait_for_sem(semid, 2, timeout);
	exit(0);
}


========== ENVOI D'UN CTRLC A INTER

void
pause_button(item, event)
	Panel_item	item;
	Event		*event;
{
	send_ctrlc(block);
}

*/



#define MAXSEGMENT	10000

int             sem_key;
int             block_key;
int             matrix_key;

/*
 * utilisation en mode remote
 */
int             shm_sd;
int             shm_remote;
struct gop_connect connect_ipc;


int             ftshm;

#ifdef USE_STRERROR
#    define my_strerror(x)  strerror(x)
#else
     extern char           *sys_errlist[];
#    define my_strerror(x)  sys_errlist[x]
#endif

/* variable statique pour l'utilisation depuis le fortran */

int             semid;
struct block_kw *block;


static int ipc_signal_caught;



static void stamped_printf(char *fmt,...)
{	
	va_list	pvar;
	char date[32];
	char out[1024];

	struct timeval  tp;
	gettimeofday(&tp, (void *) NULL);
	
	sprintf(date, "%10d.%6.6d", (int)tp.tv_sec, (int)tp.tv_usec);
	
	va_start(pvar, fmt);
	vsprintf(out, fmt, pvar);
	va_end(pvar);
	
	printf("%s libipc:%s", date, out);
	fflush(stdout);
}


/****************************************************************/
/****************/
/****************      SEMAPHORES*/
/****************/
/****************/
/****************************************************************/

/*
 * Cree le triplet de semaphores
 * 
 * RETURN: create_semaphore() retourne le semaphore identifier (semid) ou -1 en
 * cas de d'erreur
 * 
 */

int
create_semaphore(int flag_init_server)
{
	int             semid, nsems, semflg;

	if (shm_remote) {
		invalid_remote("create_semaphore");
		return (-1);
	}
	nsems = 3;
	semflg = IPC_CREAT | 0666;

	if ((semid = semget((key_t) sem_key, nsems, semflg)) == -1) {
		stamped_printf("create_semaphore: semget - %s\n", my_strerror(errno));
		return (-1);
	}
	
/*
	aie modif 23/10/1998
*/	
	if(flag_init_server) {
		setval_sem(semid, 0, 0);
	}
		
#ifdef DEBUG
        int semnum;
        int val;
	for (semnum = 0; semnum < 3; semnum++) {
		val = get_cmd_sem(semid, semnum, GETVAL);
		stamped_printf("create_semaphore: Initial value %d = %d \n", semnum, val);
	}
#endif
	return (semid);
}

/*
 * Recherche le semaphore identifier (semid) du triplet de semaphores
 * 
 * 
 * RETURN: get_semaphore() retourne le semaphore identifier (semid) ou -1 en cas
 * de d'erreur
 * 
 */

int
get_semaphore(void)
{
	int             semid, nsems, semflg;

	if (shm_remote) {
		invalid_remote("get_semaphore");
		return (-1);
	}
	nsems = 3;
	semflg = 0;

	if ((semid = semget((key_t) sem_key, nsems, semflg)) == -1) {
		stamped_printf("get_semaphore: semget - %s\n", my_strerror(errno));
		return (-1);
	}
#ifdef DEBUG
        int semnum;
        int val;
	for (semnum = 0; semnum < 3; semnum++) {
		val = get_cmd_sem(semid, semnum, GETVAL);
		stamped_printf("get_semaphore: initial value %d = %d \n", semnum, val);
	}
#endif
	return (semid);
}

/*
 * Elimine le triplet de semaphores
 * 
 * 
 * RETURN: kill_semaphore() retourne le 0 ou -1 en cas de d'erreur
 * 
 */

int
kill_semaphore(int semid /* semaphore identifier */ )
{
	if (shm_remote) {
		invalid_remote("kill_semaphore");
		return (-1);
	}
	if (semctl(semid, 0, IPC_RMID) == -1) {
		stamped_printf("kill_semaphore: semctl - %s\n", my_strerror(errno));
		return (-1);
	}
	return (0);
}


/*
 * Attend que le semaphore semnum du triplet semid vaille 0.
 * 
 * C'est la fonction utilisée par un client qui se met en attente de
 * disponibilite d'une ressource. Cette fonction accepte un timeout sur cette
 * attente.
 * 
 * RETURN: wait_for_sem() retourne normallement 0, -1 en cas de d'erreur ou 
 * (-100-signal_value) en cas de timeout.
 * 
 */

int
wait_for_sem(int semid,		/* semaphore identifier */
	     int semnum,	/* semaphore number (0-2) */
	     int timeout /* timeout */ )
{
	struct sembuf   sops;
	int             nsops;
	int             status;
	struct timespec timer_value;

	if (shm_remote) {
		invalid_remote("wait_for_sem");
		return (-1);
	}
	nsops = 1;
	sops.sem_num = (unsigned short)semnum;
	sops.sem_op = 0;
	sops.sem_flg = 0;

#ifdef DEBUG
	stamped_printf("%s %ld semnum = %d   wait for semaphore \n", my_getdate(semid), getpid(), semnum);
#endif

	errno = 0;

	timer_value.tv_sec = timeout;
	timer_value.tv_nsec = 0;

	if(timeout > 0){
		status = semtimedop(semid, &sops, nsops, &timer_value);
	} else {
		status = semop(semid, &sops, nsops);
	}
	if (status == -1 && errno == EAGAIN) {	//timeout
		stamped_printf("wait_for_sem: %s\n", my_strerror(errno));
		return (-114);	// standart Inter 114 mean SIGALRM new from dec2010
	}
	if (status == -1 && errno != EAGAIN) {	// other errno
		stamped_printf("wait_for_sem: %s\n", my_strerror(errno));
		return (status);
	}

#ifdef DEBUG
	stamped_printf("%s %ld semnum = %d   finish wait for semaphore \n", my_getdate(semid), getpid(), semnum);
#endif
	return (0);
}

/*
 * Retourne le status du semaphore semnum du triplet semid
 * 
 * 
 * RETURN: wait_for_sem_nowait() retourne normallement 0 ou -1 en cas de d'erreur.
 * 
 */

int
wait_for_sem_nowait(int semid,	/* semaphore identifier */
		    int semnum /* semaphore number (0-2) */ )
{
	struct sembuf   sops;
	int             nsops;
	int             status;

	if (shm_remote) {
		invalid_remote("wait_for_sem_nowait");
		return (-1);
	}
	nsops = 1;
	sops.sem_num = (unsigned short)semnum;
	sops.sem_op = 0;
	sops.sem_flg = IPC_NOWAIT;

#ifdef DEBUG
	stamped_printf("%s %ld semnum = %d   wait for semaphore no wait \n", my_getdate(semid), getpid(), semnum);
#endif
	status = semop(semid, &sops, nsops);
	if (status == -1) {
		stamped_printf("wait_for_sem_nowait: %s\n", my_strerror(errno));
		return(status);
	}
#ifdef DEBUG
	stamped_printf("%s %ld semnum = %d   wait for semaphore no wait status = %d \n", my_getdate(semid), getpid(), semnum, status);
#endif
	return (status);

}

/*
 * Test si l'incrementation d'un semaphore est autorisee.
 * 
 * Cette fonction affiche a l'ecran un message si le semaphore semnum vaut plus
 * que zero. Cette fonction est principalement utilisee pour tester
 * l'incrementation du semaphore 0, lequel ne doit pas etre incremente s'il
 * vaut deja 0 pour ne pas generer de situation interdite (possibilite de
 * connection de plusieurs client simultanement).
 * 
 * 
 * RETURN: test_inc_sem() retourne normallement 0 ou -1 en cas de d'erreur.
 * 
 */

int
test_inc_sem(int semid,		/* semaphore identifier */
	     int semnum /* semaphore number (0-2) */ )
{
	int             val;

	if (shm_remote) {
		invalid_remote("test_inc_sem");
		return (-1);
	}
	/*
	 * on teste la valeur du semaphore et on signale une erreur si le
	 * semaphore ne vaut pas zero
	 */
	if ((val = get_cmd_sem(semid, semnum, GETVAL)) == -1)
		return (-1);

	if (val > 0) {
		stamped_printf("**********************************************************\n");
		stamped_printf("\n");
		stamped_printf("            ATTENTION\n");
		stamped_printf("\n");
		stamped_printf("Le client (PID=%d) essaie de liberer le\n", getpid());
		stamped_printf("semaphore No %d (incrementation)\n", semnum);
		stamped_printf("\n");
		stamped_printf("Mais le semaphore est deja libre (valeur=%d)\n", val);
		stamped_printf("\n");
		stamped_printf("Cette operation est donc refusee pour ne pas\n");
		stamped_printf("generer de situation interdite\n");
		stamped_printf("\n");
		stamped_printf("Il faut donc determiner la sequence d'operation\n");
		stamped_printf("qui a mene a cette situation et l'empecher\n");
		stamped_printf("\n");
		stamped_printf("Vous pouvez malgres tout continuer a travailler\n");
		stamped_printf("si tout vous parait OK!\n");
		stamped_printf("\n");
		stamped_printf("**********************************************************\n");
		return (1);
	}
	return (0);
}

/*
 * Incremente le semaphore semnum du triplet semid.
 * 
 * Le serveur qui veut incrementer le sem 0 doit utiliser
 * server_free_ressource()
 * 
 * 
 * RETURN: inc_sem() retourne normallement 0 ou -1 en cas de d'erreur.
 * 
 */

int
inc_sem(int semid,		/* semaphore identifier */
	int semnum /* semaphore number (0-2) */ )
{
	struct sembuf   sops;
	int             nsops;
	int             val;
	int             status;

	if (shm_remote) {
		invalid_remote("inc_sem");
		return (-1);
	}
	nsops = 1;
	sops.sem_num = (unsigned short)semnum;
	sops.sem_op = 1;
	sops.sem_flg = 0;

#ifdef DEBUG
	stamped_printf("%s %ld semnum = %d   increment semaphore \n", my_getdate(semid), getpid(), semnum);
#endif

	/*
	 * test si le semaphore peut etre incremente
	 */

	if ((val = test_inc_sem(semid, semnum)) == -1)
		return (-1);
	if (val == 1)
		return (0);

	/*
	 * EN SUSPEND......
	 * 
	 * ensuite, dans le cas ou on incremente le semaphore #0, on autorise
	 * l'action uniquement (c'est le cas pour le client uniquement) 1) si
	 * le serveur est en attente (NCNT sem#1=1) 2) et dans le cas ou NCNT
	 * sem#1 = 0, seulement s'il n'y a pas de client en attente sur le
	 * semaphore #0.
	 */

	if (semnum == 0) {

		if (get_cmd_sem(semid, 0, GETNCNT) < 0)
			return (-1);
		if (get_cmd_sem(semid, 1, GETNCNT) < 0)
			return (-1);
		if (0) {	/* EN SUSPEND ...... */

			stamped_printf("##########################################################\n");
			stamped_printf("\n");
			stamped_printf("\n");
			stamped_printf("            ATTENTION\n");
			stamped_printf("\n");
			stamped_printf("Le client (PID=%d) essaie de liberer son\n", getpid());
			stamped_printf("serveur\n");
			stamped_printf("\n");
			stamped_printf("Mais le serveur n'est pas en attente de commande\n");
			stamped_printf("(soit le serveur est mort, soit il y a eu un time-out\n");
			stamped_printf("durant la commande en cours)\n");
			stamped_printf("\n");
			stamped_printf("Le fait de liberer le serveur genererait une situation \n");
			stamped_printf("illegale (semaphore#1=1)\n");
			stamped_printf("\n");
			stamped_printf("C'est donc a vous de liberer le semaphore manuellement\n");
			stamped_printf("avec un reset (avec ipcstat)\n");
			stamped_printf("\n");
			stamped_printf("En cas de time-out (reel probleme ou process stopp'e),\n");
			stamped_printf("il faut s'assurer que le serveur retrouve un etat stable\n");
			stamped_printf("puis, liberer le serveur manuellement (shmfree() ou\n");
			stamped_printf("avec un reset sur ipcstat)\n");
			stamped_printf("\n");
			stamped_printf("Si le serveur est mort, il faut le relancer puis,\n");
			stamped_printf("liberer le serveur manuellement (shmfree() ou\n");
			stamped_printf("avec un reset sur ipcstat)\n");
			stamped_printf("\n");
			stamped_printf("##########################################################\n");
			return (0);
		}
	}
	if ((status = semop(semid, &sops, nsops)) == -1) {
		stamped_printf("inc_sem: %s\n", my_strerror(errno));
		return (status);
	}
#ifdef DEBUG
	stamped_printf("%s %ld semnum = %d   --- increment fin --- \n", my_getdate(semid), getpid(), semnum);
#endif
	return (status);
}



/*
 * Incremente le semaphore 0 du triplet semid.
 * 
 * L'incrementation ne peut se faire que si elle ne genere pas une situation
 * interdite (semaphore_0 > 0) ainsi cette fonction utilise test_inc_sem()
 * avant de faire l'incrementation. Cette derniere fonction affiche une
 * message d'erreur en cas d'operation interdite et on ne fait pas
 * l'incrementation.
 * 
 * RETURN: server_free_ressource() retourne normallement 0, -1 en cas de
 * d'erreur.
 */



/*
 * Incremente le semaphore 0 du triplet semid.
 * 
 * L'incrementation ne peut se faire que si elle ne genere pas une situation
 * interdite (semaphore_0 > 0) ainsi cette fonction utilise test_inc_sem()
 * avant de faire l'incrementation. Cette derniere fonction affiche une
 * message d'erreur en cas d'operation interdite et on ne fait pas
 * l'incrementation.
 * 
 * STATIC: La variable statique semid doit etre valide.
 * 
 * REMOTE: Cette fonction est invalide en mode remote.
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
server_free_ressource_(int *status /* return status pointer */ )
{
	*status = server_free_ressource(semid);
}


int
server_free_ressource(int semid /* semaphore identifier */ )
{
	struct sembuf   sops;
	int             nsops;
	int             val;
	int             semnum;
	int             status;

	if (shm_remote) {
		invalid_remote("server_free_ressource");
		return (-1);
	}
	semnum = 0;

	nsops = 1;
	sops.sem_num = (unsigned short)semnum;
	sops.sem_op = 1;
	sops.sem_flg = 0;

#ifdef DEBUG
	stamped_printf("%s %ld semnum = 0   increment semaphore \n", my_getdate(semid), getpid());
#endif
	/*
	 * test si le semaphore peut etre incremente
	 */

	if ((val = test_inc_sem(semid, semnum)) == -1)
		return (-1);
	if (val == 1)
		return (0);



	if ((status = semop(semid, &sops, nsops)) == -1) {
		stamped_printf("server_free_ressource: %s\n", my_strerror(errno));
		return (status);
	}
#ifdef DEBUG
	stamped_printf("%s %ld semnum = %d   --- increment fin --- \n", my_getdate(semid), getpid(), semnum);
#endif
	return (status);
}


/*
 * Decremente le semaphore 0.
 * 
 * Si le serveur vient de mourir (dans ce cas sem#0=1 et aucun process n'est en
 * attente sur le sem#1 (ncount#1=0),  cette fonction simule un client en
 * attente avant de se mettre elle meme en attente. Par la suite, lorsque le
 * serveur demarre, il consomme le premier client (donc le faux) et part sur
 * le bon. Dans le cas normal la fonction stoppe le process si le semaphore
 * doit devenir negatif.
 * 
 * RETURN: dec_sem_zero() retourne normallement 0, -1 en cas de d'erreur ou 
 * (-100-signal_value) en cas de timeout.
 */


int
dec_sem_zero(int semid,		/* semaphore identifier */
	     struct block_kw * block,	/* communication bloc pointer */
	     int timeout /* timeout */ )
{
	int             val, ncnt;
	int             status;

	if (shm_remote) {
		invalid_remote("dec_sem_zero");
		return (-1);
	}
	if ((val = get_cmd_sem(semid, 0, GETVAL)) == -1)
		return (-1);
	if ((ncnt = get_cmd_sem(semid, 1, GETNCNT)) == -1)
		return (-1);

	if (val == 1 && ncnt == 0) {

		if (kill(block->pid_server, 0) != 0) {
			stamped_printf("No server alive...wait for it\n");
			if (setval_sem(semid, 0, 0) == -1)
				return (-1);
		}
	}
	if ((status = dec_sem(semid, 0, timeout)) < 0)
		return (status);
	block->pid_client = getpid();
	return (0);
}

/*
 * Decremente le semaphore semnum du triplet semid. Le process est stoppe si
 * le semaphore doit devenir negatif.
 * 
 * RETURN: dec_sem() retourne normallement 0, -1 en cas de d'erreur ou 
 * (-100-signal_value) en cas de timeout.
 */

int
dec_sem(int semid,		/* semaphore identifier */
	int semnum,		/* semaphore number (0-2) */
	int timeout /* timeout */ )
{
	struct sembuf   sops;
	int             nsops;
	int             status;
	struct timespec timer_value;
	
	
	if (shm_remote) {
		invalid_remote("dec_sem");
		return (-1);
	}
	nsops = 1;
	sops.sem_num = (unsigned short)semnum;
	sops.sem_op = -1;
	sops.sem_flg = 0;

#ifdef DEBUG
	stamped_printf("%s %ld semnum = %d   decrement semaphore \n", my_getdate(semid), getpid(), semnum);
#endif
	errno = 0;

	timer_value.tv_sec = timeout;
	timer_value.tv_nsec = 0;

	if(timeout > 0){
		status = semtimedop(semid, &sops, nsops, &timer_value);
	} else {
		status = semop(semid, &sops, nsops);
	}
	if (status == -1 && errno == EAGAIN) {	//timeout
		stamped_printf("dec_sem: %s\n", my_strerror(errno));
		return (-114);	// standart Inter 114 mean SIGALRM new from dec2010
	}
	if (status == -1 && errno != EAGAIN) {	// other errno
		stamped_printf("dec_sem: %s\n", my_strerror(errno));
		return (status);
	}

#ifdef DEBUG
	stamped_printf("%s %ld semnum = %d   ready for ressource \n", my_getdate(semid), getpid(), semnum);
#endif
	return (0);
}


/*
 * Decremente le semaphore semnum du triplet semid. Cette fonction est snas
 * attente, on reprends la main dans tout les cas.
 * 
 * RETURN: dec_sem_nowait() retourne normallement 0, -1 si le semaphore est deja
 * a zero et qu'on ne puisse le decrementer.
 */

int
dec_sem_nowait(int semid,	/* semaphore identifier */
	       int semnum /* semaphore number (0-2) */ )
{
	struct sembuf   sops;
	int             nsops;
	int             status;

	if (shm_remote) {
		invalid_remote("dec_sem_nowait");
		return (-1);
	}
	nsops = 1;
	sops.sem_num = (unsigned short) semnum;
	sops.sem_op = -1;
	sops.sem_flg = IPC_NOWAIT;

#ifdef DEBUG
	stamped_printf("%s %ld semnum = %d   decrement semaphore no wait \n", my_getdate(semid), getpid(), semnum);
#endif
	status = semop(semid, &sops, nsops);
	if (status == -1) {
		stamped_printf("dec_sem_nowait: %s\n", my_strerror(errno));
		return(status);
	}
#ifdef DEBUG
	stamped_printf("%s %ld semnum = %d   decrement semaphore no wait status = %d \n", my_getdate(semid), getpid(), semnum, status);
#endif
	return (status);
}

/*
 * Decremente le semaphore semnum du triplet semid. Cette fonction est snas
 * attente, on reprends la main dans tout les cas.
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 * 
 */
void
dec_sem_nowait_(int semid,	/* semaphore identifier */
	        int semnum,     /* semaphore number (0-2) */ 
		int *status     /* return status pointer */ )
{
	if (shm_remote) {
		invalid_remote("dec_sem_nowait_");
		*status = -1;
		return;
	}
	*status = dec_sem_nowait(semid, semnum);
}


/*
 * retourne la valeur demandee par le code "cmd" d'un semaphore.
 * 
 * l'operation a lieu sur le semaphore semnum du triplet semid. Les commandes a
 * dispositions sont decrites dans le man de "semctl".
 * 
 * RETURN: get_cmd_sem() retourne normallement 0 ou -1 en cas de d'erreur.
 */

int
get_cmd_sem(int semid,		/* semaphore identifier */
	    int semnum,		/* semaphore number (0-2) */
	    int cmd 		/* code */ )
{

	int             val;

	if (shm_remote) {
		invalid_remote("get_cmd_sem");
		return (-1);
	}
	if ((val = semctl(semid, semnum, cmd)) == -1) {
		stamped_printf("get_cmd_sem: semctl - %s\n", my_strerror(errno));
		return (-1);
	}
	return (val);
}

/* meme chose, mais cherche le pid */
int
get_cmd_sem_pid(int semnum	/* semaphore number (0-2) */)
{
	int             val;

	if (shm_remote) {
		invalid_remote("get_cmd_sem_pid");
		return (-1);
	}
	if ((val = semctl(semid, semnum, GETPID)) == -1) {
		stamped_printf("get_cmd_sem_pid: semctl - %s\n", my_strerror(errno));
		return (-1);
	}
	return (val);
}

/*
 * Pose le semaphore semnum du triplet semid a une valeur donnée.
 * 
 * RETURN: setval_sem() retourne normallement 0 ou -1 en cas de d'erreur.
 */

int
setval_sem(int semid,		/* semaphore identifier */
	   int semnum,		/* semaphore number (0-2) */
	   int value /* semaphore value */ )
{
	union semun {
		int             val;
		struct semid_ds *buf;
		ushort         *array;
	}               arg;

	if (shm_remote) {
		invalid_remote("setval_sem");
		return (-1);
	}
	arg.val = value;

#ifdef DEBUG
	stamped_printf("%s %ld semnum = %d   mis a %d \n", my_getdate(semid),
	       getpid(), semnum, value);
#endif
	if (semctl(semid, semnum, SETVAL, arg) == -1) {
		stamped_printf("setval_sem: semctl - %s\n", my_strerror(errno));
		return (-1);
	}
	return (0);
}


/****************************************************************/
/****************/
/****************      SHARED MEMORY */
/****************/
/****************/
/****************************************************************/


/*
 * Cree le block de communication et retourne son identificateur ft_shm.
 * 
 * RETURN: alloc_block_shm() retourne l'adresse du bloc de communication ou (char *)-1
 * en cas de d'erreur.
 */

char           *
alloc_block_shm(int *ft_shm /* communication bloc identifier */ )
{
	char           *ft_addr;

	if (shm_remote) {
		invalid_remote("alloc_block_shm");
		return ((char *) -1);
	}
	/*
	 * Access/Creates the shared memory region associated with key SHMKEY
	 */

	if ((*ft_shm = shmget((key_t) block_key, sizeof(struct block_kw), 0666 | IPC_CREAT)) == -1) {
		stamped_printf("alloc_block_shm: shmget - %s\n", my_strerror(errno));
		stamped_printf("alloc_block_shm: unable to allocate shared memory\n");
		return (NULL);
	}
#ifdef DEBUG
	stamped_printf("ft_shm = %d   key = %d \n", *ft_shm, block_key);
#endif

	/*
	 * Attaches the shared memory region to virtual address <ft_addr>
	 */
	if ((ft_addr = (char *) shmat(*ft_shm, (char *) 0, SHM_RND)) == (void *) -1) {
		stamped_printf("alloc_block_shm: shmat(%d) - %s\n", 0, my_strerror(errno));
		stamped_printf("alloc_block_shm: unable to attach shared memory\n");
		return (NULL);
	}
	
	memset(ft_addr, sizeof(struct block_kw), (char)0);
	
	return (ft_addr);

}


/*
 * Recherche le block de communication et retourne son identificateur ft_shm.
 * 
 * RETURN: get_block_shm() retourne l'adresse du bloc de communication ou -1 en
 * cas de d'erreur
 */

char           *
get_block_shm(int *ft_shm /* communication bloc identifier */ )
{
	char           *ft_addr;

	if (shm_remote) {
		invalid_remote("get_block_shm");
		return (NULL);
	}
	/*
	 * Access/Creates the shared memory region associated with key SHMKEY
	 */

	if ((*ft_shm = shmget((key_t) block_key, sizeof(struct block_kw), 0)) == -1) {
		stamped_printf("get_block_shm: shmget - %s\n", my_strerror(errno));
		stamped_printf("get_block_shm: unabled to allocate shared memory\n");
		return (NULL);
	}
#ifdef DEBUG
	stamped_printf("ft_shm = %d   key = %d \n", *ft_shm, block_key);
#endif

	/*
	 * Attaches the shared memory region to virtual address <ft_addr>
	 */
	if ((ft_addr = (char *) shmat(*ft_shm, (char *) 0, SHM_RND)) == (void *) -1) {
		stamped_printf("get_block_shm: shmat(%d) - %s\n", 0, my_strerror(errno));
		stamped_printf("get_block_shm: unabled to attach shared memory\n");
		return (NULL);
	}
	return (ft_addr);

}


/*
 * Elimine le block de communication designe par ft_shm
 * 
 * RETURN: kill_block_shm() retourne normallement 0 ou -1 en cas de d'erreur.
 */

int
kill_block_shm(int ft_shm /* communication bloc identifier */ )
{
	if (shm_remote) {
		invalid_remote("kill_block_shm");
		return (-1);
	}
	if (shmctl(ft_shm, IPC_RMID, (struct shmid_ds *) NULL) == -1) {
		stamped_printf("kill_block_shm: shmctl - %s\n", my_strerror(errno));
		return (-1);
	}
	return (0);
}


/*
 * Cree la matrice en memoire partagee de taille shmsize (pixel).
 * 
 * La matrice est fabriquee par segment de sysconf(_SC_PAGESIZE) bytes.
 * 
 * RETURN: alloc_matrix_shm() retourne un pointeur sur la zone allouee ou -1 en
 * cas de d'erreur
 */

char           *
alloc_matrix_shm(int shmsize /* size of the shared matrix (pixels) */ )
{
	int             i, n, rest, size;
	char           *mat_ft_addr[MAXSEGMENT];
	int             mat_ft_shm[MAXSEGMENT];
       
	
	long page_size  = sysconf(_SC_PAGESIZE);
	long pixel_size = sizeof(float);
	long segment_size = page_size*256;	// attention en cas de changement de taille, faire un ipckill 
        stamped_printf("alloc_matrix_shm: ask for %ld [bytes]\n",pixel_size * shmsize);
        stamped_printf("alloc_matrix_shm: PAGESIZE          = %ld\n",page_size);
        stamped_printf("alloc_matrix_shm: segment_size      = %ld\n",segment_size);


	n = (pixel_size * shmsize) / segment_size;
	rest = (pixel_size * shmsize) % segment_size;
	if (rest != 0){
		n++;
	}
        stamped_printf("alloc_matrix_shm: n segment         = %d\n",n);
        stamped_printf("alloc_matrix_shm: size last segment = %d\n",rest);

	for (i = 0; i < n; i++) {

		/*
		 * Access/Creates the shared memory region associated with
		 * key SHMKEY
		 */
		size = segment_size;
		if (i == n - 1 && rest != 0){
			size = rest;
		}
		if ((mat_ft_shm[i] = shmget((key_t) matrix_key - i, size, 0666 | IPC_CREAT)) == -1) {
			stamped_printf("alloc_matrix_shm: shmget - %s\n", my_strerror(errno));
			stamped_printf("alloc_matrix_shm: unabled to allocate shared memory\n");
			return (NULL);
		} else {
			/**
			stamped_printf("\nalloc_shared: shmget succeed mat_ft_shm=%d size=%d\n", mat_ft_shm[i], size);
			**/
		}
		
		/**
		stamped_printf("A-alloc_matrix_shm: shmsize=%d, size=%d, i=%d, mat_ft_shm[i]=%d, n=%d, rest=%d\n",shmsize,size,i,mat_ft_shm[i], n ,rest);
		**/
		if (i == 0) {
			/*
			 * Attaches the shared memory region to virtual
			 * address <mat_ft_addr>
			 */
			/**
			stamped_printf("B-alloc_matrix_shm: shmat: mat_ft_shm[i]=%d, add=0, flag=%d\n",mat_ft_shm[i],SHM_RND);
			**/
			if ((mat_ft_addr[i] = (char *) shmat(mat_ft_shm[i], (const void *)  0, SHM_RND)) == (void *) -1) {
				stamped_printf("alloc_matrix_shm: shmat(%d) - %s\n", i, my_strerror(errno));
				stamped_printf("alloc_matrix_shm: unabled to attach shared memory\n");
				return (NULL);
			}
			
			/**
			stamped_printf("b1-alloc_matrix_shm: shmat: mat_ft_addr[i]=%x\n",mat_ft_addr[i]);
			**/
		} else {

			/**
			stamped_printf("C-alloc_matrix_shm: shmat: mat_ft_shm[i]=%d, add=%x, flag=%d\n",mat_ft_shm[i],(mat_ft_addr[0] - size*i),SHM_RND);
			**/
			if ((mat_ft_addr[i] = (char *) shmat(mat_ft_shm[i], (const void *) (mat_ft_addr[0] - size*i), SHM_RND)) == (void *) -1) {
				stamped_printf("alloc_matrix_shm: shmat(%d) - %s\n", i, my_strerror(errno));
				stamped_printf("alloc_matrix_shm: unabled to attach shared memory\n");
				return (NULL);
			}
						
			/**
			stamped_printf("c1-alloc_matrix_shm: shmat: mat_ft_addr[i]=%x\n",mat_ft_addr[i]);
			**/
		}


	}
#ifdef DEBUG
	stamped_printf("alloc_matrix_shm: demande de %d bytes sur ptr = %lx \n", shmsize, (long)mat_ft_addr[n - 1]);
#endif
	return (mat_ft_addr[n - 1]);
}


/**
 * evaluation d'une fct par le server.
 *
 * la commande est dans command et le resultat est retourne dans content
 * toujours sous forme caractere. La fonction reste en attente sur le client
 * s'il n'est pas libre. Il est possible de donner des timeouts.
 *
 * ex:	on veut:	type:		commande:
 *
 *	nx(2)		(int)		"itoa(nx(2))"
 *
 *	temps sideral	(char)		"hdtoh(ts())"
 *
 *	par(3)		(real)		"format(par(3),g13.7)"
 *
 * 
 *
 * RETURN: get_server_value() retourne normallement 0, -1 en cas de d'erreur ou 
 * (-100-signal_value) en cas de timeout.
 */

int
get_server_value(int semid,	/* semaphore identifier */
		 struct block_kw * block,	/* communication bloc pointer */
		 char *command,	/* command to evaluate */
		 char *content,	/* result */
		 int timeouta,	/* timeout on command sending */
		 int timeoutb /* timeout on anser */ )
{

	char           *cmd;
	int             status;

	if (shm_remote) {
		invalid_remote("get_server_value");
		return (-1);
	}
	if ((cmd = (char *) alloca(strlen(command) + 28)) == NULL){
		return (-1);
	}
	sprintf(cmd, "show shmput(\"[-VAL-]\",%s)", command);

	if ((status = send_command(semid, block, cmd, NO_FORK_PROCESS, WAIT_FOR_ANSWER, timeouta)) == -1){
		return (status);
	}
	if (wait_for_sem(semid, 2, timeoutb) == -1){
		return (-1);
	}
	if (get_shm_block_kw(block, "[-VAL-]", content) == -1){
		return (-1);
	}
	if (inc_sem(semid, 0) == -1){
		return (-1);
	}
	return (0);
}

/*
 * Initialisation de la matrice en memoire partagee.
 * 
 * La fonction questionne le serveur sur la taille de la matrice puis effectue
 * l'allocation. Elle initialise le pointeur de matrice (pointer).
 * 
 * Cette fonction peut etre utilisee par chaque client une fois que le semaphore
 * semid est initialise et que le server est lance.
 * 
 * Reste en attente si le serveur n'est pas libre.
 * 
 * STATIC: La variable statique matrix_key doit etre valide.
 * 
 * RETURN: ask_and_init_shm() retourne normallement 0, -1 en cas de d'erreur ou
 * (-100-signal_value) en cas de timeout.
 */

int
ask_and_init_shm(int semid,	/* semaphore identifier */
		 struct block_kw * block,	/* communication bloc pointer */
		 float **pointer,	/* matrix pointer address */
		 int timeouta,	/* timeout on command sending */
		 int timeoutb /* timeout on anser */ )
{
	char            content[80];
	int             status;

	if (shm_remote) {
		invalid_remote("ask_and_init_shm");
		return (-1);
	}
	/*
	 * Ask for memory size
	 */
	if ((status = get_server_value(semid, block, "itoa(nbpix())", content, timeouta, timeoutb)) == -1){
		return (status);
	}
	stamped_printf("ask_and_init_shm: NBPIX = %s\n", content);

	if ((*pointer = (float *) alloc_matrix_shm(atoi(content))) == NULL){
		return (-1);
	}
	return (0);
}



/*
 * Detache la matrice en memoire partagee.
 * 
 * RETURN: dettach_matrix_shm() retourne normallement 0 ou -1 en cas de d'erreur.
 */

//int
//dettach_matrix_shm(void)
//{
//	int             i;
//
//	for (i = 0; i < mat_nb_segments; i++) {
//
//		if (shmdt(mat_ft_addr[i]) == -1) {
//			stamped_printf("dettach_matrix_shm: shmdt(%d) - %s\n", i,
//				       my_strerror(errno));
//			stamped_printf("dettach_matrix_shm: unabled to detach shared memory\n");
//			return (-1);
//		}
//	}
//	return (0);
//}

/*
 * Initialise les semaphores et le block de communication.
 * 
 * Cette fonction cree les semaphores et le bloc de communication s'ils
 * n'existent pas. Attention il lui faut des pointeurs.
 * 
 * RETURN: init_sem_block() retourne normallement 0 ou -1 en cas de d'erreur.
 */

int
init_sem_block(int *semid,	/* semaphore identifier pointer */
	 struct block_kw ** block, /* communication bloc pointer address */ 
	 int flag_init_server /* flag si on initilise le sémaphore d'un server */)
{
	if (shm_remote) {
		invalid_remote("init_sem_block");
		return (-1);
	}
	/*
	 * Initialize semaphore
	 */
	if ((*semid = create_semaphore(flag_init_server)) == -1)
		return (-1);
	/*
	 * Initialize communication block on shared memory
	 */
	if ((*block = (struct block_kw *) alloc_block_shm(&ftshm)) == NULL)
		return (-1);

	return (0);
}


/*
 * Recherche les semaphores et le block de communication.
 * 
 * Cette recherche les identificateurs des semaphores et l'adresse du bloc de
 * communication. Il doivent exister sinon il y a une erreur. Attention il
 * lui faut des pointeurs.
 * 
 * RETURN: get_sem_block() retourne normallement 0 ou -1 en cas de d'erreur.
 */
int
get_sem_block(int *semid,	/* semaphore identifier pointer */
	 struct block_kw ** block /* communication bloc pointer address */ )
{
	if (shm_remote) {
		invalid_remote("get_sem_block");
		return (-1);
	}
	/*
	 * Recherche semaphore
	 */
	if ((*semid = get_semaphore()) == -1)
		return (-1);
	/*
	 * Initialize communication block on shared memory
	 */
	if ((*block = (struct block_kw *) get_block_shm(&ftshm)) == NULL)
		return (-1);
	return (0);
}

/*
 * Elimine la matrice en memoire partagee.
 * 
 * STATIC: Les variables statiques mat_ft_shm[i] doivent etre valides (elles le
 * sont depuis la creation de la matrice).
 * 
 * RETURN: kill_matrix_shm() retourne normallement 0 ou -1 en cas de d'erreur.
 */

//int
//kill_matrix_shm(void)
//{
//	int             i;
//
//	for (i = 0; i < mat_nb_segments; i++) {
//
//		if (shmctl(mat_ft_shm[i], IPC_RMID, (struct shmid_ds *) NULL) == -1) {
//			stamped_printf("kill_matrix_shm: shmctl(%d) - %s\n", i, my_strerror(errno));
//			stamped_printf("kill_matrix_shm: unabled to remove shared memory identifier\n");
//			return (-1);
//		}
//	}
//	return (0);
//}


/****************************************************************/
/****************/
/****************      UTILITY */
/****************/
/****************/
/****************************************************************/

/*
 * Elimine les semaphores et le bloc de communication en memoire partagee
 * 
 * STATIC: La variable statique ftshm doit etre valide (elle est valide depuis
 * la creation du bloc de communication).
 * 
 * RETURN: discard_semaphore_and_shm() retourne normallement 0 ou -1 en cas de
 * d'erreur
 */


int
discard_semaphore_and_shm(int semid /* semaphore identifier */ )
{
	if (shm_remote) {
		invalid_remote("discard_semaphore_and_shm");
		return (-1);
	}
	/*
	 * discard shared memory and semaphore
	 */
	stamped_printf("discard_semaphore_and_shm: Discard semaphore and communication block\n");
	if (kill_semaphore(semid) == -1)
		return (-1);
	if (kill_block_shm(ftshm) == -1)
		return (-1);
	return (0);
}


/*
 * Definis les valeurs des cles pour le semaphore identifier semid et la
 * shared memory du block de communication.
 * 
 * Initialise les variables statiques sem_key et block_key en fonction d'une cle
 * unique (f_key). C'est a dire: sem_key = f_key + 1 et block_key = f_key + 2
 * 
 */

void
select_key_semid_block(int f_key /* numerical key */ )
{
	/*
	 * attention pour le calcul de la key, voir aussi: libipc.c:
	 * get_key_()
	 */

	shm_remote = FALSE;

	sem_key = f_key + 1;
	block_key = f_key + 2;
}

/****************************************************************/
/****************/
/****************      SIGNAL */
/****************/
/****************/
/****************************************************************/


/*
 * Envoye un CTRL-C au serveur.
 * 
 * C'est le PID (block->pid_server) du block de communication qui est utilise.
 * 
 * RETURN: send_ctrlc() retourne la valeur de retour de kill()
 */

int
send_ctrlc(struct block_kw * block /* communication bloc pointer */ )
{
	if (shm_remote) {
		invalid_remote("send_ctrlc");
		return (-1);
	}
	if (block == 0)
		return (-1);
	if (block->pid_server == 0)
		return (-1);
	return (kill(block->pid_server, SIGINT));
}

/*
 * Stokage du No de signal.
 * 
 * Cette routine doit être utilisee par les handler de signaux qui enregistre
 * ainsi le No du signal qui a interrompu le process. Cet enregistrement
 * permet notament de diffrerencier les interruption par ctrlc et timeout
 *
 */

void
this_signal_was_caught(int sig)
{
	ipc_signal_caught = sig;
}

/*
 * Stokage du No de signal.
 * 
 * Cette routine doit être utilisee par les handler de signaux qui enregistre
 * ainsi le No du signal qui a interrompu le process. Cet enregistrement
 * permet notament de diffrerencier les interruption par ctrlc et timeout
 *
 */

void
this_signal_was_caught_(int *sig)
{
	this_signal_was_caught(*sig);
}

/*
 * Recupere le No du signal qui a ete enregistre avec
 * this_signal_was_caught().
 * 
 * RETURN: signal number
 */

int
which_signal_caught()
{
	return(ipc_signal_caught);
}

/*
 * Recupere le No du signal qui a ete enregistre avec
 * this_signal_was_caught().
 */

void
which_signal_caught_(int *sig /* signal number pointer */ )
{
	*sig = which_signal_caught();
}

/****************************************************************/
/****************/
/****************      KEYWORDS 				*/
/****************/
/****************/
/****************************************************************/


/*
 * Lit le contenu d'un keyword dans le bloc de communication.
 * 
 * RETURN: get_shm_block_kw() retourne normallement 0, -1 en cas d'erreur ou 1
 * si le keyword n'est pas trouvé
 */

int
get_shm_block_kw(struct block_kw * block,	/* communication bloc pointer */
		 char key[],	/* keyword */
		 char content[] /* content */ )
{
	int             i = 0;

	if (shm_remote) {
		invalid_remote("get_shm_block_kw");
		return (-1);
	}
	if (block == 0)
		return (-1);
	while (strlen((block->line + i)->key) != 0) {
#ifdef DEBUG
		stamped_printf("%s %ld --get-- %s ->  %s\n", my_getdate(0), getpid(), key, (block->line + i)->key);
#endif
		if (strcmp(key, (block->line + i)->key) == 0) {
			(void) strcpy(content, (block->line + i)->content);
			return (0);
		}
		i++;
		if (i == NB_KW_MAX)
			return (1);
	}
	return (1);
}


/*
 * Place le keyword et son contenu dans le bloc de communication
 * 
 * Le keyword est mis a la suite des autre, s'il doit etre le premier, il faut
 * utiliser ini_shm_block_kw() au prealable.
 * 
 * RETURN: put_shm_block_kw() retourne normallement 0, -1 en cas d'erreur ou 1
 * si le bloc de communication est plein
 */

int
put_shm_block_kw(struct block_kw * block,	/* communication bloc pointer */
		 char key[],	/* keyword */
		 char content[] /* content */ )
{
	int             i = 0;

	if (shm_remote) {
		invalid_remote("put_shm_block_kw");
		return (-1);
	}
	if (block == 0)
		return (-1);
#ifdef DEBUG
	stamped_printf("%s %ld --put-- %s ->  %s\n", my_getdate(0), getpid(), key, content);
#endif
	while (strlen((block->line + i)->key) != 0) {
		if (strcmp((block->line + i)->key, key) == 0) {
			(void) strncpy((block->line + i)->content, content, CONTENT_SIZE-1);
			*((block->line + i)->content+CONTENT_SIZE-1) = (char) 0;
			return (0);
		}
		i++;
		if (i == NB_KW_MAX)
			return (1);
	}
	(void) strncpy((block->line + i)->key, key, KW_SIZE-1);
	(void) strncpy((block->line + i)->content, content, CONTENT_SIZE-1);
	*((block->line + i)->key+KW_SIZE-1)          = (char) 0;
	*((block->line + i)->content+CONTENT_SIZE-1) = (char) 0;
	return (0);
}


/*
 * Initialise le block de communication.
 * 
 * Cette initialisation se fait pour vider le bloc de communication avant
 * d'ecrire de nouveaux keywords.
 * 
 * RETURN: ini_shm_block_kw() retourne normallement 0, -1 en cas d'erreur
 */

int
ini_shm_block_kw(struct block_kw * block /* communication bloc pointer */ )
{
	int             i = 0;

	if (shm_remote) {
		invalid_remote("ini_shm_block_kw");
		return (-1);
	}
	if (block == 0)
		return (-1);
	for (i = 0; i < NB_KW_MAX; i++) {
		*(block->line + i)->key = '\0';
	}
	return (0);
}


/*
 * Retourne le keyword No "i" du bloc de communication.
 * 
 * RETURN: get_shm_block_kw_n() retourne normallement 0, -1 en cas d'erreur ou 1
 * si le keyword n'est pas trouvé
 */

int
get_shm_block_kw_n(struct block_kw * block,	/* communication bloc pointer */
		 int  i,
		 char *key,	/* keyword */
		 char *content /* content */ )
{
	if (shm_remote) {
		invalid_remote("get_shm_block_kw_n");
		return (-1);
	}
	if (block == 0)
		return (-1);
	if (i > NB_KW_MAX)
		return (1);


#ifdef DEBUG
	stamped_printf("%s %ld --get_n-- %s ->  %s\n", my_getdate(0), getpid(), key, (block->line + i)->key);
#endif
	if (*(block->line + i)->key == (char) 0) {
		return (1);
	}
	(void) strcpy(key,     (block->line + i)->key);
	(void) strcpy(content, (block->line + i)->content);
	
	return (0);
}

/****************************************************************/
/****************/
/****************      COMMANDS					*/
/****************/
/****************/
/****************************************************************/


/*
 * Envoye une commande au serveur.
 * 
 * Il y a 2 mode de travail:
 * 
 * Si (wait==FORK_PROCESS) : on fait un fork() et la demande se traitera de
 * maniere autonome et le client reprend immediatement la main et si
 * (wait==NO_FORK_PROCESS) : on attend la fin.
 * 
 * On definis aussi par (ackno==WAIT_FOR_ANSWER) si le serveur ne doit pas
 * rendre la main. Dans ce cas, c'est le client qui se mettra en attente de
 * la fin du traitement avec wait_for_sem().
 * 
 * Cette fonction peut avoir un timeout sur l'attente de connection au serveur
 * 
 * RETURN: send_command() retourne normallement 0 si wait == NO_FORK_PROCESS, la
 * valeur de retour du fork() si wait == FORK_PROCESS, -1 en cas de d'erreur ou
 * (-100-signal_value) en cas de timeout.
 */

int
send_command(int semid,		/* semaphore identifier */
	     struct block_kw * block,	/* communication bloc pointer */
	     char cmd[],	/* command */
	     int wait,		/* waiting mode (see fork()) */
	     int ackno,		/* wait for serveur acknoledge */
	     int timeout /* timeout */ )
{
	int             status = 0;

	if (shm_remote) {
		invalid_remote("send_command");
		return (-1);
	}
	if (wait == FORK_PROCESS) {

		status = fork();
		if (status == -1) {
			return (-1);
		} else if (status != 0) {
			return (status);
		}
	}
#ifdef DEBUG
	stamped_printf("%s %ld demande de resource,", my_getdate(semid), getpid());
	if (wait == FORK_PROCESS) {
		stamped_printf("command: %s    FORK_PROCESS\n", cmd);
	} else {
		stamped_printf("command: %s    NO_FORK_PROCESS\n", cmd);
	}
#endif

	if ((status = dec_sem_zero(semid, block, timeout)) < 0)
		return (status);

	block->pid_client = getpid();
	block->ackno = 0;
	if (ini_shm_block_kw(block) == -1)
		return (-1);
	if (put_shm_block_kw(block, "COMMAND", cmd) == -1)
		return (-1);

	if (ackno == WAIT_FOR_ANSWER)
		block->ackno = 1;
	if (setval_sem(semid, 2, 1) == -1)
		return (-1);

	if (inc_sem(semid, 1) == -1)
		return (-1);
	if (wait == FORK_PROCESS)
		exit(0);
	return (0);
}

/*
 * Envoye une commande au serveur alors qu'on a deja la main.
 * 
 * Dans ce cas le serveur ne rend pas la main et c'est le client qui se mettra
 * en attente de la fin du traitement avec wait_for_sem().
 * 
 * RETURN: send_command_ready() retourne normallement 0, -1 en cas d'erreur
 */

int
send_command_ready(int semid,	/* semaphore identifier */
		   struct block_kw * block,	/* communication bloc pointer */
		   char cmd[] /* command */ )
{
	if (shm_remote) {
		invalid_remote("send_command_ready");
		return (-1);
	}
	if (ini_shm_block_kw(block) == -1)
		return (-1);
	if (put_shm_block_kw(block, "COMMAND", cmd) == -1)
		return (-1);

	block->pid_client = getpid();
	block->ackno = 1;

	if (setval_sem(semid, 2, 1) == -1)
		return (-1);

	if (inc_sem(semid, 1) == -1)
		return (-1);
	return (0);
}

/****************************************************************/
/****************/
/****************      DEBUGGING TOOlS				*/
/****************/
/****************/
/****************************************************************/

/*
 * Retourne une chaine formattee avec le status courant des semaphores.
 * 
 * c'est a dire: la date, les secondes, les musecondes et l'etat des semaphores
 * 
 * RETURN: my_getdate() retourne normallement la chaine de caracteres, (char*)-1
 * en cas d'erreur
 */

char           *
my_getdate(int semid /* semaphore ID */ )
{
	struct tm      *tmp;
	long            clock;
	static char     tt[100], ttt[100];
	struct timeval  tp;
	struct timezone tzp;

	if (shm_remote) {
		invalid_remote("my_getdate");
		return ((char *) -1);
	}
	clock = (long) time((time_t *) 0);
	tmp = (struct tm *)localtime(&clock);
	strncpy(tt, asctime(tmp), 24);
	tt[19] = '\0';
	(void) gettimeofday(&tp, &tzp);
	if (semid == 0) {
		sprintf(ttt, "%10ld %6ld %s", tp.tv_sec, tp.tv_usec, &tt[0] + 11);
	} else {
#pragma warning(disable:981) // operands are evaluated in unspecified order
  		sprintf(ttt, "%10ld %6ld %s ncnt=%d %d %d val=%d %d %d", tp.tv_sec, tp.tv_usec, &tt[0] + 11,
			get_cmd_sem(semid, 0, GETNCNT), get_cmd_sem(semid, 1, GETNCNT),
			get_cmd_sem(semid, 2, GETNCNT), get_cmd_sem(semid, 0, GETVAL),
			get_cmd_sem(semid, 1, GETVAL), get_cmd_sem(semid, 2, GETVAL));
	}

	return ((char *) ttt);
}

/*
 * Affiche a l'ecran le contenu du bloc de communication
 * 
 * RETURN: show_shm_block_kw() retourne normallement le nb de keyword, -1 en cas d'erreur
 */

int
show_shm_block_kw(struct block_kw * block /* communication bloc pointer */ )
{
	int             i = 0;

	if (shm_remote) {
		invalid_remote("show_shm_block_kw");
		return (-1);
	}
	if (block == 0)
		return (-1);

	stamped_printf("%12s (%3s): %-60s\n", "KEY", "len", "content");
	stamped_printf("%12s  %3s : %-60s\n", "---", "---", "-------");
	while (strlen((block->line + i)->key) != 0) {
		stamped_printf("%12s (%3d): %-60s\n", (block->line + i)->key,
		       (int)strlen((block->line + i)->content),
		       (block->line + i)->content);
		i++;
		if (i == NB_KW_MAX){
			fflush(stdout);
			return (i);
		}
	}
	fflush(stdout);
	return (i);
}

/*
 * affiche 2 points et attends 2 sec pour faire une de simulation de travail
 */

void
print_delay(void)
{
	int             i;

	for (i = 0; i <= 2; i++) {
		sleep(1);
		stamped_printf(".\n");
	}
	stamped_printf("\n");
}

/****************************************************************/
/****************/
/****************      COMMUNICATION AVEC REMOTE SERVER */
/****************/
/****************/
/****************************************************************/



/*
 * Envoie une commande au serveur remote Ipcsrv avec attente de status.
 * 
 * Le message de retour est compose uniquement du status (nombre formatte).
 * 
 * RETURN: write_to_ipc_server() retourne normallement 0, -1 en cas d'erreur
 */

int
write_to_ipc_server(char *string /* command */ )
{
	char            answer[80];
	int             status;

	if (gop_write_command(&connect_ipc, string) != GOP_OK) {
		stamped_printf("write_to_ipc_server: communication error: %s\n:", gop_get_error_str());
		return (-1);
	}
	if (gop_read(&connect_ipc, answer, sizeof(answer)) < GOP_OK) {
		if (gop_errno == GOP_DISCONNECT) {
			stamped_printf("write_to_ipc_server: server deconnection\n");
			return (-1);
		}
		gop_handle_eom(&connect_ipc, NULL);
		stamped_printf("write_to_ipc_server: communication error: %s\n:",
			gop_get_error_str());
		return (-1);
	}
	/*
	 * stamped_printf("recu %d bytes: >%s<\n", nb_bytes, answer);
	 */
	sscanf(answer, "%d", &status);
	/*
	 * stamped_printf("status d'une commande remote= %d\n",status);
	 */
	return (status);
}


/*
 * Envoie une commande au serveur remote Ipcsrv avec attente de reponse.
 * 
 * Le message de retour est compose du status (nombre formatte sur les 3
 * premiers caracteres) puis du message proprement dit.
 * 
 * RETURN: write_read_to_ipc_server() retourne normallement 0, -1 en cas
 * d'erreur.
 */

int
write_read_to_ipc_server(char *string,	/* command */
			 char *retstr /* answer */ )
{
	char            answer[256];
	int             status;

	if (gop_write_command(&connect_ipc, string) != GOP_OK) {
		stamped_printf("write_read_to_ipc_server: communication error: %s\n:", gop_get_error_str());
		return (-1);
	}
	if (gop_read(&connect_ipc, answer, sizeof(answer)) < GOP_OK) {
		if (gop_errno == GOP_DISCONNECT) {
			stamped_printf("write_read_to_ipc_server: server deconnection\n");
			return (-1);
		}
		gop_handle_eom(&connect_ipc, NULL);
		stamped_printf("write_read_to_ipc_server: communication error: %s\n:",
			gop_get_error_str());
		return (-1);
	}
	/*
	 * stamped_printf("recu %d bytes: >%s<\n", nb_bytes, answer);
	 */
	sscanf(answer, "%d", &status);
	if (status >= 0) {
		strcpy(retstr, answer + 3);
	}
	/*
	 * stamped_printf("status d'une commande remote= %d\n",status);
	 */
	return (status);
}





/****************************************************************/
/****************************************************************/
/****************************************************************/
/* INTERFACE FORTRAN -> C				        */
/****************************************************************/
/****************************************************************/
/****************************************************************/

/*
 * Affiche un textexte indiquant que la commande est invalide en mode remote.
 */

void
invalid_remote(char *str)
{
	stamped_printf("Invalid command in remote mode: >%s<\n",str);
}



/*
 * Initialisation d'un server.
 * 
 * Cette fonction cree (s'ils n'existent pas) le triplet de semaphores et le
 * bloc de communication. Elle regarde si l'etat des semaphores indique que
 * la commande precedente ne s'est pas bien terminee et qu'un client "vivant"
 * est toujours en attente puis elle pose le semaphore_2 et place son PID
 * dans block->pid_server.
 * 
 * STATIC: Les variables statiques sem_key et block_key doivent etre valides et
 * les variables statiques semid et block sont mises a jour.
 * 
 * REMOTE: Cette fonction est invalide en mode remote.
 * 
 * RETURN: 1) ID semaphore 2) ID block 3) si un client etait en cours de
 * communication avec le precedent server (client_waiting==1) 4) le status
 * est retourne normallement 0 ou -1 en cas d'erreur.
 */


void
init_ipc_server_(int *f_semid,	/* semaphore identifier pointer */
		 struct block_kw ** f_block,	/* communication bloc pointer
						 * address */
		 int *client_waiting,	/* client waiting exist */
		 int *status /* return status pointer */ )
{
	int             ia;

	if (shm_remote) {
		invalid_remote("init_ipc_server_");
		*status = -1;
		return;
	}
	*status = 0;
	if (init_sem_block(&semid, &block, 1) < 0) {
		*status = -1;
		return;
	}
	if ((*client_waiting = get_cmd_sem(semid, 2, GETVAL)) < 0) {
		*status = -1;
		return;
	}
	if ((ia = get_cmd_sem(semid, 0, GETVAL)) < 0) {
		*status = -1;
		return;
	}
	if (ia == 1)
		*client_waiting = 0;

	if (*client_waiting) {
		if (kill(block->pid_client, 0) != 0)
			*client_waiting = 0;
	}
	if ((int) setval_sem(semid, 2, 1) < 0)
		*status = -1;
	block->pid_server = getpid();
	*f_semid = semid;
	*f_block = block;
}

/*
 * Initialisation d'un client.
 * 
 * Cette fonction cree (s'ils n'existent pas) le triplet de semaphores et le
 * bloc de communication.
 * 
 * STATIC: Les variables statiques sem_key et block_key doivent etre valides et
 * les variables statiques semid et block sont mises a jour.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="init
 * <sem_key>-1").
 * 
 * RETURN: 1) ID semaphore 2) ID block 3) le status est retourne normallement 0
 * ou -1 en cas d'erreur.
 */
 
int init_ipc_remote_client_final(void){ 
	char            message[12];
        if (shm_remote) {
		sprintf(message, "init %d", sem_key - 1);
		return(write_to_ipc_server(message));
	}
	return(-1);
}
 
void
init_ipc_client_(int *f_semid,	/* semaphore identifier pointer */
		 struct block_kw ** f_block,	/* communication bloc pointer
						 * address */
		 int *status /* return status pointer */ )
{
	char            message[12];

	/*
	 * attention pour le calcul de la key original, voir aussi:
	 * select_for_remote_()
	 */

	if (shm_remote) {
		sprintf(message, "init %d", sem_key - 1);
		*status = write_to_ipc_server(message);
		return;
	}
	*status = 0;
	/*
	 * Initialize both semaphore and communication block on shared memory
	 */
	if (init_sem_block(&semid, &block, 0) < 0)
		*status = -1;
	*f_semid = semid;
	*f_block = block;
}


void
init_ipc_client(int *f_semid,	/* semaphore identifier pointer */
		 struct block_kw ** f_block,	/* communication bloc pointer
						 * address */
		 int *status /* return status pointer */ )
{
	/*
	 * attention pour le calcul de la key original, voir aussi:
	 * select_for_remote_()
	 */

	*status = 0;
	/*
	 * Initialize both semaphore and communication block on shared memory
	 */
	if (init_sem_block(&semid, &block, 0) < 0)
		*status = -1;
	*f_semid = semid;
	*f_block = block;

}

int
init_semaphore(void)
{
	return((semid=create_semaphore(0)));
}


int *
init_block(void)
{
	/*
	 * Initialize communication block on shared memory
	 */
	return((int *) (block = (struct block_kw *) alloc_block_shm(&ftshm)));
}


/**** pas utilisé
int
shm_init_ipc_client(void)
{

	return(init_sem_block(&semid, &block, 0));
}
*****/

int      
init_remote_client(char *host, char *symb_name, char *rcmd, int  port, int semkey){
    int status ;
    int socketId;
    
    socketId = init_ipc_remote_client(host, symb_name, rcmd, port);
    stamped_printf("init_ipc_remote_client returns: %d\n", socketId);
    if(socketId <0){
      return(socketId);
    }
    select_for_remote(semkey, socketId);
    stamped_printf("select_for_remote done\n");

    status = init_ipc_remote_client_final();
    stamped_printf("init_ipc_remote_client_final: %d\n", status);
    if(status <0){
      return(status);
    }  
    
    return(socketId);  
}



/*
 * Initialisation d'un client sur un remote serveur.
 * 
 * Pour utiliser les fonctionnalites de libipc concernant la synchronisation par
 * semaphore et la communication au travers du bloc de communication sur un
 * serveur remote, le client doit lancer un serveur specialise emulant la
 * librarie libipc sur le host ou se trouve le serveur (voir ipcsrv).
 * 
 * Cette fonction (le client) cree une connection socket sur un remore host et y
 * lance la commande de demarrage d'un serveur ipc (ipcsrv). Immediatement
 * apres, le client se met en attente de connection. Cote serveur, une fois
 * le serveur ipc lance, celui-ci se connecte sur le client. La connection
 * est ainsi valide. C'est le serveur ipc qui fabrique de son cote les
 * semaphores et le bloc de communication. Par la suite, le client enverra
 * les ordres de controle par le cannal de communication sous forme de chaine
 * ascii. La librarie emule de maniere completement transparente tout les
 * ordres de controle.
 * 
 * 
 * RETURN: 1) socket number (sd_current) 2) le status est retourne normallement
 * 0 ou -1 en cas d'erreur.
 * 
 */
/* version C */ 

int         /* return socketId si positif ou erreur si negatif) */
init_ipc_remote_client( char *host,	/* remote server host */
			char *symb_name,/* nom du client */
			char *rcmd,	/* remote commande, used to run
					 * ipcsrv */
			int  port)	/* remote server port number pointer */
{
	char            cmd[128];
	int             nb_bytes;
	char            answer[12];
	char            client_host[40];
	int		status;
	
	if(connect_ipc.cd != 0){
		status = write_to_ipc_server("aliv");	
		if(status == 0){
			return(connect_ipc.cd);
		}
	}
			
	
        
	gop_init_server_socket(&connect_ipc, symb_name, port, 4096,
			       GOP_CONNECTION, 0);

	if (gop_init_connection(&connect_ipc) != GOP_OK) {
		fflush(stdout);
		stamped_printf("init_ipc_remote_client: communication error: %s\n:", gop_get_error_str());
		return(-1);
	}
	(void) gethostname(client_host, sizeof(client_host));

	sprintf(cmd, "%s %s %d &", rcmd, client_host, port);

	stamped_printf("init_ipc_remote_client: send command: <%s>\n", cmd);

	gop_system_rsh(cmd, host);

	if (gop_accept_connection(&connect_ipc) != GOP_OK) {
		stamped_printf("init_ipc_remote_client: communication error: %s\n:",
			gop_get_error_str());
		return(-1);
	}
	if ((nb_bytes = gop_read(&connect_ipc, answer, sizeof(answer))) < GOP_OK) {
		gop_handle_eom(&connect_ipc, NULL);
		stamped_printf("init_ipc_remote_client: communication error: %s\n:",
			gop_get_error_str());
		stamped_printf("init_ipc_remote_client: no answer (connection hand check).. abort");
		return(-1);
	}
	stamped_printf("init_ipc_remote_client_: receive %d bytes: >%s<\n", nb_bytes, answer);
        

	return(connect_ipc.cd);

}
 
/* version Fortran */ 
void
init_ipc_remote_client_(char *host,	/* remote server host */
			char *symb_name,/* nom du client */
			char *rcmd,	/* remote commande, used to run
					 * ipcsrv */
			int *port,	/* remote server port number pointer */
			int *sd_current,	/* socket number pointer */
			int *status /* return status pointer */ )
{
	char            cmd[128];
	int             nb_bytes;
	char            answer[12];
	char            client_host[40];

	*status = 0;

	gop_init_server_socket(&connect_ipc, symb_name, *port, 4096,
			       GOP_CONNECTION, 0);

	if (gop_init_connection(&connect_ipc) != GOP_OK) {
		fflush(stdout);
		stamped_printf("init_ipc_remote_client_: communication error: %s\n:", gop_get_error_str());
		*status = -1;
		return;
	}
	(void) gethostname(client_host, sizeof(client_host));
/*
	sprintf(cmd, "rsh %s %s %s %d > /dev/null&",
		host, rcmd, client_host, *port);
*/
	sprintf(cmd, "%s %s %d &", rcmd, client_host, *port);

	stamped_printf("init_ipc_remote_client_: send command: <%s>\n", cmd);

	gop_system_rsh(cmd, host);

	if (gop_accept_connection(&connect_ipc) != GOP_OK) {
		stamped_printf("init_ipc_remote_client_: communication error: %s\n:",
			gop_get_error_str());
		*status = -1;
		return;
	}
	if ((nb_bytes = gop_read(&connect_ipc, answer, sizeof(answer))) < GOP_OK) {
		gop_handle_eom(&connect_ipc, NULL);
		stamped_printf("init_ipc_remote_client_: communication error: %s\n:",
			gop_get_error_str());
		stamped_printf("init_ipc_remote_client_: no answer (connection hand check).. abort");
		*status = -1;
		return;
	}
	stamped_printf("init_ipc_remote_client_: receive %d bytes: >%s<\n", nb_bytes, answer);

	*sd_current = connect_ipc.cd;

}

/*
 * Met a jour les variables statiques pour le travail remote.
 * 
 * shm_remote est pose a TRUE, sem_key est pose a key+1 et shm_sd est pose a sd
 */
void
select_for_remote(int key,	/* numerical key */
		  int sd        /* socket number */ )
{
	shm_remote = TRUE;

	sem_key = key + 1;
	shm_sd  = sd;
}
 
void
select_for_remote_(int *key,	/* numerical key */
		   int *sd /* socket number */ )
{
	shm_remote = TRUE;

	sem_key = *key + 1;
	shm_sd  = *sd;
}


/*
 * Cree la matrice en memoire partagee de taille shmsize (pixel).
 * 
 * La matrice est fabriquee par segment de (1024 * SHMSIZE) bytes
 * 
 * RETURN: alloc_matrix_shm() retourne un pointeur sur la zone allouee ou -1 en
 * cas de d'erreur
 */

void
init_shm_(int *isize,		/* size of shared matrix (bytes) */
	  char **ptr,		/* matrix pointer */
	  int *status 		/* return status pointer */ )
{
	*status = 0;
	if ((*ptr = alloc_matrix_shm(*isize)) == NULL)
		*status = -1;
}

/*
 * Met a jour les variables statiques pour les appels suivants (pour
 * clef=f_key).
 * 
 * Cette fonction pose shm_remote=FALSE, sem_key=f_key+1, block_key=f_key+2,
 * semid=f_semid et block=f_block.
 */
void
select_semid_block_(int *f_key,	/* key number pointer */
		    int *f_semid,	/* semaphore identifier pointer */
		    struct block_kw ** f_block	/* communication bloc pointer
		        address */ )
{
	select_key_semid_block(*f_key);

	semid = *f_semid;
	block = *f_block;
}

void
select_semid_block(int f_key, int f_semid, int *f_block)
{
	select_key_semid_block(f_key);

	semid = f_semid;
	block = (struct block_kw *) f_block;
}

/*
 * recherche la clef (f_key) courante.
 * 
 * RETURN: f_key
 */
void
get_key_(int *f_key /* key number pointer */ )
{

	/*
	 * attention pour le calcul de la key original, voir aussi: libipc.c:
	 * select_key_semid_block()
	 */

	*f_key = sem_key - 1;

}

/*
 * Met a jour la variable a statique matrix_key.
 */
void
select_matrix_key_(int *f_key /* key number pointer */ )
{
	matrix_key = *f_key;
}

/*
 * Detache la matrice en memoire partagee.
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur
 */
//void
//dettach_mat_shm_(int *status /* return status pointer */ )
//{
//	*status = dettach_matrix_shm();
//}

/*
 * Elimine les semaphores et le bloc de communication en memoire partagee
 * 
 * STATIC: Les variables statiques semid et ftshm doivent etre valides (ftshm
 * est valide depuis la creation du bloc de communication).
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur
 */
void
discard_semaphore_and_shm_(int *status /* return status pointer */ )
{
	if (shm_remote) {
		invalid_remote("discard_semaphore_and_shm_");
		*status = -1;
		return;
	}
	*status = discard_semaphore_and_shm(semid);
}

/*
 * Elimine la matrice en memoire partagee.
 * 
 * STATIC: Les variables statiques mat_ft_shm[i] doivent etre valides (elles le
 * sont depuis la creation de la matrice).
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
//void
//kill_mat_shm_(int *status /* return status pointer */ )
//{
//	*status = kill_matrix_shm();
//}

/*
 * Decremente le semaphore semnum.
 * 
 * STATIC: La variable statique semid doit etre valide.
 * 
 * REMOTE: Cette fonction est invalide en mode remote.
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 * 
 */
void
decremente_sem_(int *semnum,	/* semaphore number pointer */
		int *timeout,	/* timeout */
		int *status /* return status pointer */ )
{
	if (shm_remote) {
		invalid_remote("decremente_sem_");
		*status = -1;
		return;
	}
	*status = dec_sem(semid, *semnum, *timeout);
}

/*
 * incremente le semaphore semnum.
 * 
 * STATIC: La variable statique semid doit etre valide.
 * 
 * REMOTE: Cette fonction est invalide en mode remote.
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
incremente_sem_(int *semnum,	/* semaphore number pointer */
		int *status /* return status pointer */ )
{
	if (shm_remote) {
		invalid_remote("incremente_sem_");
		*status = -1;
		return;
	}
	*status = inc_sem(semid, *semnum);
}


/*
 * Pose le semaphore semnum a val.
 * 
 * STATIC: La variable statique semid doit etre valide.
 * 
 * REMOTE: Cette fonction est invalide en mode remote.
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
set_sem_(int *semnum,		/* semaphore number pointer */
	 int *val,		/* setting value pointer */
	 int *status /* return status pointer */ )
{
	*status = set_sem(*semnum, *val);
}
int
set_sem(int semnum,		/* semaphore number */
	int val		/* setting value */ )
{
	if (shm_remote) {
		invalid_remote("set_sem_");
		return(-1);
	}
	return(setval_sem(semid, semnum, val));
}



/*
 * Retourne le pid du serveur.
 * 
 * REMOTE: Cette fonction est invalide en mode remote.
 * 
 * RETURN: Le PID en mémoire
 */
void
srvexis_(int *flag)
{
	*flag = srvexis();
}

int
srvexis()
{
	if (kill(block->pid_server, 0) == 0) {
		return(1);
	} else {
		return(0);
	}
}

/*
 * Retourne le pid du serveur.
 * 
 * REMOTE: Cette fonction est invalide en mode remote.
 * 
 * RETURN: Le PID en mémoire
 */
void
get_srv_pid_(int *pid)
{
	*pid = get_srv_pid();
}

int
get_srv_pid()
{
	if (shm_remote) {
		invalid_remote("get_srv_pid");
		return(-1);
	}
	return(block->pid_server);
}

/*
 * Lit le nb de client en attente.
 * 
 * STATIC: La variable statique semid doit etre valide.
 * 
 * REMOTE: Cette fonction est invalide en mode remote.
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
get_ncount_sem_(int *semnum,	/* semaphore number pointer */
		int *val	/* client number pointer */ )
{
	*val = get_ncount_sem(*semnum);
}

int
get_ncount_sem(int semnum	/* semaphore number */ )
{
	if (shm_remote) {
		invalid_remote("get_ncount_sem_");
		return(-1);
	}
	return(get_cmd_sem(semid, semnum, GETNCNT));
}

/*
 * Lit le nb de client en attente de zero.
 * 
 * STATIC: La variable statique semid doit etre valide.
 * 
 * REMOTE: Cette fonction est invalide en mode remote.
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
get_zcount_sem_(int *semnum,	/* semaphore number pointer */
		int *val	/* client number pointer */ )
{
	*val = get_zcount_sem(*semnum);
}

int
get_zcount_sem(int semnum	/* semaphore number */ )
{
	if (shm_remote) {
		invalid_remote("get_ncount_sem_");
		return(-1);
	}
	return(get_cmd_sem(semid, semnum, GETZCNT));
}


/*
 * Lit la valeur du semaphore.
 * 
 * STATIC: La variable statique semid doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="gval").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
get_val_sem_(int *semnum,	/* semaphore number pointer */
	     int *val		/* semaphore value pointer */ )
{
	*val = get_val_sem(*semnum);
}

int
get_val_sem(int semnum	/* semaphore number */ )
{
	int	status;
	char	answer[12];

	if (shm_remote) {
		status = write_read_to_ipc_server("gval", answer);
		if (status != 0)
			return(status);
		return(atoi(answer));
	}

	return(get_cmd_sem(semid, semnum, GETVAL));
}


/*
 * Lit le contenu d'un keyword dans le bloc de communication.
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="getk <key>").
 * 
 * RETURN: Le status est retourne normallement a 0, -1 en cas d'erreur ou 1 si
 * le keyword n'est pas trouvé
 */
void
get_shm_kw_(char *key,		/* keyword */
	    char *content,	/* content */
	    int *ilen,		/* length of the content */
	    int *status /* return status pointer */ )
{
	*ilen   =  0;
	*status = get_shm_kw(key, content);
	if (*status == 0)
		*ilen = strlen(content);
}

int
get_shm_kw(char *key,	/* keyword */
	   char *content	/* content */)
{
	int	status;
	char	message[KW_SIZE + CONTENT_SIZE + 8];

	if (shm_remote) {
		sprintf(message, "getk %s", key);
		status = write_read_to_ipc_server(message, content);
		return(status);
	}

	if (block == 0)
		return(-1);

	return(get_shm_block_kw(block, key, content));
}
/*
 * Lit le contenu du keyword No "i" dans le bloc de communication.
 * 
 * STATIC: i doit être plus petit que NB_KW_MAX.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="getnk <n>").
 * 
 * RETURN: Le status est retourne normallement a 0, -1 en cas d'erreur ou 1 si
 * le keyword n'est pas trouvé
 */
void
get_shm_kw_n_(int *i,		/* No keyword */
	    char *key,		/* keyword */
	    int *keylen,	/* length of the key */
	    char*content,	/* content */
	    int *conlen,	/* length of the content */
	    int *status /* return status pointer */ )
{
	*conlen = 0;
	*keylen = 0;
	*status = get_shm_kw_n(*i, key, content);
	if(*status == 0){
		*keylen = strlen(key);
		*conlen = strlen(content);
	}
	return;
}
int
get_shm_kw_n(int i,		/* No keyword */
	    char *key,		/* keyword */
	    char *content	/* content */)
{
	int	status;
	char	message[KW_SIZE + CONTENT_SIZE + 8];
	char	answer[12];

	*key     = (char) 0;
	*content = (char) 0;
	if (shm_remote) {
		sprintf(message, "getnk %d", i);
		status = write_read_to_ipc_server(message, answer);
		if (status == -1)
			return(status);

		if(*answer=='|')
			return(status);
		strcpy(key, (char *) strtok(answer, "|"));
		strcpy(content, (char *) strtok(NULL, "|"));
		return(status);
	}
	return(get_shm_block_kw_n(block, i, key, content));
}


/*
 * Initialise le block de communication.
 * 
 * Cette initialisation se fait pour vider le bloc de communication avant
 * d'ecrire de nouveaux keywords.
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="inik").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
ini_shm_kw_(int *status /* return status pointer */ )
{
	*status = ini_shm_kw();
}

int
ini_shm_kw(void)
{
	if (shm_remote) {
		return(write_to_ipc_server("inik"));
	}
	return(ini_shm_block_kw(block));
}

/*
 * Affiche a l'ecran le contenu du bloc de communication.
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est invalide en mode remote.
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
sho_shm_kw_(int *status /* return status pointer */ )
{
	if (shm_remote) {
		invalid_remote("sho_shm_kw_");
		*status = -1;
		return;
	}
	*status = show_shm_block_kw(block);
}


/*
 * Place le keyword et son contenu dans le bloc de communication.
 * 
 * Le keyword est mis a la suite des autre, s'il doit etre le premier, il faut
 * utiliser ini_shm_block_kw() au prealable.
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="putk <key>
 * <content>").
 * 
 * RETURN: Le status est retourne normallement a 0, -1 en cas d'erreur ou 1 si
 * le bloc de communication est plein
 */
void
put_shm_kw_(char *key,		/* keyword */
	    char *content,	/* content */
	    int *status /* return status pointer */ )
{
	*status = put_shm_kw(key, content);
}

int
put_shm_kw(char *key,		/* keyword */
	    char *content	/* content */)
{
	int	status;
	char	message[KW_SIZE + CONTENT_SIZE + 8];

	if (shm_remote) {
		sprintf(message, "putk %s %s", key, content);
		status = write_to_ipc_server(message);
		return(status);
	}
	return(put_shm_block_kw(block, key, content));
}

/*
 * Test si le bloc de communication a ete cree.
 * 
 * Le test est effectue sur la validite de la variable statique block.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="aliv").
 * 
 * RETURN: Le status est retourne a 0 si le bloc existe ou a -1 s'il n'existe
 * pas.
 */
void
ipc_alive_(int *status /* return status pointer */ )
{
	if (shm_remote) {
		*status = write_to_ipc_server("aliv");
		return;
	}
	*status = -1;
	if (block != 0)
		*status = 0;
}

/*
 * Pose le flag d'erreur dans le bloc de communication.
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="perr <val>").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
put_shm_err_(int *val,		/* erreur value pointer */
	     int *status /* return status pointer */ )
{
	*status = put_shm_err(*val);
}

int
put_shm_err(int val		/* erreur value */)
{
	char	message[12];

	if (shm_remote) {
		sprintf(message, "perr %d", val);
		return(write_to_ipc_server(message));
	}

	if (block == 0)
		return(-1);

	//stamped_printf("put_shm_err: set err_server = %d\n", val);
	block->err_server = val;
	return(0);
}

/*
 * Pose le flag de status dans le bloc de communication.
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="psta <val>").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
put_shm_stat_(int *val,		/* status value pointer */
	      int *status /* return status pointer */ )
{
	*status = put_shm_stat(*val);
}

int
put_shm_stat(int val		/* status value */)
{
	char	message[12];

	if (shm_remote) {
		sprintf(message, "psta %d", val);
		return(write_to_ipc_server(message));
	}

	if (block == 0)
		return(-1);

	block->stat_server = val;
	return(0);
}


/*
 * Pose le message d'erreur dans le bloc de communication.
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="pste <str>")
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
put_shm_str_err_(char *str,	/* error string */
		 int *status /* return status pointer */ )
{
	*status = put_shm_str_err(str);
}

int
put_shm_str_err(char *str	/* error string */ )
{
	char	message[256];

	if (shm_remote) {
		sprintf(message, "pste %s", str);
		return(write_to_ipc_server(message));
	}

	if (block == 0)
		return(-1);

	strncpy(block->err_str_server, str, sizeof(block->err_str_server) - 1);
	return(0);
}

/*
 * Pose le code d'erreur dans le bloc de communication.
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="pecd <str>")
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
put_shm_err_code_(char *str,	/* error code */
		  int *status /* return status pointer */ )
{
	*status = put_shm_err_code(str);
}

int
put_shm_err_code(char *str	/* error code */ )
{
	int	status;
	char	message[80];

	if (shm_remote) {
		sprintf(message, "pecd %s", str);
		status = write_to_ipc_server(message);
		return(status);
	}

	if (block == 0)
		return(-1);

	strncpy(block->err_code, str, sizeof(block->err_code) - 1);
	return(0);
}

/*
 * Pose le nom de la commande courante dans le bloc de communication.
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="pcmd <str>")
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
put_shm_current_cmd_(char *str,	/* current commande */
		     int *status /* return status pointer */ )
{
	char            message[256];

	if (shm_remote) {
		sprintf(message, "pcmd %s", str);
		*status = write_to_ipc_server(message);
		return;
	}
	*status = -1;
	if (block == 0)
		return;
	strncpy(block->current_cmd, str, sizeof(block->current_cmd) - 1);
	*status = 0;
}

/*
 * Lit le flag d'erreur dans le bloc de communication.
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="gerr").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
get_shm_err_(int *val,	/* error value pointer */
	     int *status /* return status pointer */ )
{
	*status = get_shm_err(val);
}

int
get_shm_err(int *val	/* error value pointer */)
{
	int	status;
	char	answer[12];

	if (shm_remote) {
		status = write_read_to_ipc_server("gerr", answer);
		if (status == 0)
			*val = atoi(answer);
		return(status);
	}
	if (block == 0)
		return(-1);
	*val = block->err_server;
	return(0);
}

/*
 * Lit le flag d'acknowledge dans le bloc de communication.
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="gack").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
get_shm_ackno_(int *val,	/* acknowledge value pointer */
	       int *status /* return status pointer */ )
{
	*status = get_shm_ackno(val);
}

int
get_shm_ackno(int *val		/* acknowledge value pointer */)
{
	int	status;
	char            answer[12];
	
	if (shm_remote) {
		status = write_read_to_ipc_server("gack", answer);
		if (status == 0)
			*val = atoi(answer);
		return(status);
	}
	if (block == 0)
		return(-1);
	*val = block->ackno;
	return(0);
}


/*
 * Lit le status dans le bloc de communication.
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="gsta").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
get_shm_stat_(int *val,		/* status value pointer */
	      int *status /* return status pointer */ )
{
	*status = get_shm_stat(val);
}


int
get_shm_stat(int *val		/* status value pointer */)
{
	int	status;
	char	answer[12];

	if (shm_remote) {
		status = write_read_to_ipc_server("gsta", answer);
		if (status == 0)
			*val = atoi(answer);
		return(status);
	}
	if (block == 0)
		return(-1);
	*val = block->stat_server;
	return(0);
}

/*
 * Lit le pid du client dans le bloc de communication.
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="gpid").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
get_shm_pid_client_(int *val	/* PID value pointer */)
{
	*val = get_shm_pid_client();
}

int
get_shm_pid_client(void)
{
	int	status;
	char	answer[12];

	if (shm_remote) {
		status = write_read_to_ipc_server("gpid", answer);
		if (status != 0)
			return(status);
		return(atoi(answer));
	}

	if (block == 0)
		return(-1);

	return(block->pid_client);
}

/*
 * Retourne son propre PID. C'est a dire celui du process courant
 * en mode static ou celui de ipcsrv et mode remote
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="gpid").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
get_shm_my_pid_(int *val	/* PID value pointer */ )
{
	*val = get_shm_my_pid();
}

int
get_shm_my_pid(void)
{
	int	status;
	char	answer[12];
	if (shm_remote) {
		status = write_read_to_ipc_server("gmyp", answer);
		if (status != 0)
			return(status);
		return(atoi(answer));
	}

	return(getpid());
}

/*
 * Lit le message d'erreur dans le bloc de communication.
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="gers").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
get_shm_str_err_(char *str,	/* error string */
		 int *ilen	/* error string length */)
{
	*ilen = get_shm_str_err(str);
}

int
get_shm_str_err(char *str	/* error string */)
{
	int	status;

	if (shm_remote) {
		status = write_read_to_ipc_server("gers", str);
		if(status!=0)
			return(status);
		return(strlen(str));
	}
	if (block == 0)
		return(-1);

	strcpy(str, block->err_str_server);
	return(strlen(str));
}

/*
 * Lit le code d'erreur dans le bloc de communication.
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="gerc").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
get_shm_err_code_(char *str,	/* error code */
		  int *ilen	/* error code length */ )
{
	*ilen = get_shm_err_code(str);
}

int
get_shm_err_code(char *str	/* error code */)
{
	int	status;

	if (shm_remote) {
		status = write_read_to_ipc_server("gerc", str);
		if(status!=0)
			return(status);
		return(strlen(str));
	}

	if (block == 0)
		return(-1);

	strcpy(str, block->err_code);
	return(strlen(str));
}

/*
 * Lit la commande courante dans le bloc de communication.
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="gcmd").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
get_shm_current_cmd_(char *str,	/* current command */
		     int *ilen,	/* current command length */
		     int *status /* return status pointer */ )
{
	if (shm_remote) {
		*status = write_read_to_ipc_server("gcmd", str);
		*ilen = strlen(str);
		return;
	}
	*status = -1;
	if (block == 0)
		return;
	strcpy(str, block->current_cmd);
	*ilen = strlen(str);
	*status = 0;
}


int
get_shm_current_cmd(char *str)
{
	
	if (block == 0)
		return(-1);
	strcpy(str, block->current_cmd);
	return(0);
}

/*
 * Envoi d'une commande simple au serveur avec attente.
 * 
 * Cette fonction attend que le serveur soit pret.
 * 
 * La commande est sans parametre et comme on libere le serveur, le bloc de
 * communication n'est pas valide apres la fin de cette fonction.
 * 
 * STATIC: Les variables statiques semid et block doivent etre valides.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="cmdw <timeouta>
 * <timeoutb> |<command>").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
int
send_cmd(char *command,	  /* command */
	 int timeouta,	/* timeout on command sending pointer */
	 int timeoutb	/* timeout on anser pointer */)
{
	char  message[KW_SIZE + CONTENT_SIZE + 8];
        int status;

	if (shm_remote) {
		sprintf(message, "cmdw %d %d |%s", timeouta, timeoutb, command);
		return(write_to_ipc_server(message));
	}
	/*
	 * on se met en attente
	 */

	if ((status = dec_sem_zero(semid, block, timeouta)) < 0)
		return(status);

	/*
	 * on s'installe comme client
	 */

	status = -1;

	block->ackno = 1;
	if (ini_shm_block_kw(block) < 0)
		return(status);
	if (put_shm_block_kw(block, "COMMAND", command) < 0)
		return(status);

	/*
	 * on fait partir le serveur
	 */

	if (setval_sem(semid, 2, 1) < 0)
		return(status);
	if (inc_sem(semid, 1) < 0)
		return(status);
	/*
	 * on attend la reponse
	 */

	if ((status = wait_for_sem(semid, 2, timeoutb)) < 0)
		return(status);

	/*
	 * status de retour
	 */

	status = block->err_server;
	if (block->stat_server != 0)
		status = block->stat_server;
	/*
	 * on libere la ressource
	 */

	if (inc_sem(semid, 0) < 0) {
		status = -1;
	}
        
	return(status);
} 
 
void
send_cmd_(char *command,	/* command */
	  int *timeouta,	/* timeout on command sending pointer */
	  int *timeoutb,	/* timeout on anser pointer */
	  int *status /* return status pointer */ )
{
	char            message[KW_SIZE + CONTENT_SIZE + 8];

	if (shm_remote) {
		sprintf(message, "cmdw %d %d |%s", *timeouta, *timeoutb, command);
		*status = write_to_ipc_server(message);
		return;
	}
	/*
	 * on se met en attente
	 */

	if ((*status = dec_sem_zero(semid, block, *timeouta)) < 0)
		return;

	/*
	 * on s'installe comme client
	 */

	*status = -1;

	block->ackno = 1;
	if (ini_shm_block_kw(block) < 0)
		return;
	if (put_shm_block_kw(block, "COMMAND", command) < 0)
		return;

	/*
	 * on fait partir le serveur
	 */

	if (setval_sem(semid, 2, 1) < 0)
		return;
	if (inc_sem(semid, 1) < 0)
		return;
	/*
	 * on attend la reponse
	 */

	if ((*status = wait_for_sem(semid, 2, *timeoutb)) < 0)
		return;

	/*
	 * status de retour
	 */

	*status = block->err_server;
	if (block->stat_server != 0)
		*status = block->stat_server;
	/*
	 * on libere la ressource
	 */

	if (inc_sem(semid, 0) < 0) {
		*status = -1;
		return;
	}
}

/*
 * Envoi d'une commande au serveur sans attente de reponse.
 * 
 * Cette fonction attend que le serveur soit pret et signale si il y a eu une
 * erreur sur la commande precedente dans status.
 * 
 * La commande est sans parametre et comme on libere le serveur, le bloc de
 * communication n'est pas valide apres la fin de cette fonction.
 * 
 * STATIC: Les variables statiques semid et block doivent etre valides.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="cmdn <timeout>
 * |<command>").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
send_cmd_no_wait_(char *command,/* command */
		  int *timeout,	/* timeout */
		  int *status /* return status pointer */ )
{
	int             lstat;

	char            message[KW_SIZE + CONTENT_SIZE + 8];

	if (shm_remote) {
		sprintf(message, "cmdn %d |%s", *timeout, command);
		*status = write_to_ipc_server(message);
		return;
	}
	/*
	 * on se met en attente
	 */

	if ((*status = dec_sem_zero(semid, block, *timeout)) < 0)
		return;

	/*
	 * fabrique le status qui est le status de la commande precedente
	 */

	*status = -1;

	lstat = block->err_server;
	if (block->stat_server != 0)
		lstat = block->stat_server;

	/*
	 * on s'installe comme client
	 */

	block->ackno = 0;
	if (ini_shm_block_kw(block) < 0)
		return;
	if (put_shm_block_kw(block, "COMMAND", command) < 0)
		return;

	/*
	 * on fait partir le serveur
	 */

	if (setval_sem(semid, 2, 1) < 0)
		return;
	if (inc_sem(semid, 1) < 0)
		return;

	*status = lstat;
}

/*
 * Attend que le server soit pret. 
 *
 * Cette fonction ne teste ni ne clear les status.
 * 
 * STATIC: Les variables statiques semid et block doivent etre valides.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="cmdn <timeout>
 * |<command>").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
shm_wait_(int *timeout,		/* timeout */
	  int *status /* return status pointer */ )
{
	*status = shm_wait(*timeout);
}
int
shm_wait(int timeout		/* timeout */)
{
	int	status;
	char	message[12];

	if (shm_remote) {
		sprintf(message, "wait %d", timeout);
		return(write_to_ipc_server(message));
	}
	/*
	 * wait
	 */

	if ((status = dec_sem_zero(semid, block, timeout)) < 0)
		return(status);

	block->ackno = 0;
	return(status);
}

/*
 * Fait continuer le server, c'est le serveur qui rend la main.
 * 
 * Cette fonction est utilisee un fois que le client qui a pris la main a finis
 * de remplir le bloc de communication.
 * 
 * STATIC: Les variables statiques semid et block doivent etre valides.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="cont").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
shm_cont_(int *status /* return status pointer */ )
{
	*status = shm_cont();
}
int
shm_cont(void)
{
	int	status;

	if (shm_remote) {
		return(write_to_ipc_server("cont"));
	}
	if (block == 0)
		return(-1);

	block->ackno = 0;
	if ((status = setval_sem(semid, 2, 1)) != 0)
		return(status);
	return(inc_sem(semid, 1));
}

/*
 * Fait continuer le server, mais le serveur ne rend pas la main.
 * 
 * STATIC: Les variables statiques semid et block doivent etre valides.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="ackn").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
shm_ack_(int *status /* return status pointer */ )
{
	*status = shm_ack();
}
int
shm_ack(void)
{
	int	status;

	if (shm_remote) {
		return(write_to_ipc_server("ackn"));
	}
	if (block == 0)
		return(-1);

	block->ackno = 1;

	if ((status = setval_sem(semid, 2, 1)) != 0)
		return(status);

	return(inc_sem(semid, 1));
}

/*
 * Attend que le server ait finis la command en cours.
 * 
 * Utilise apres un shm_ack_(), c'est une fonction de resynchronisation. Elle
 * signale si il y a eu une erreur sur la commande en cours
 * 
 * STATIC: Les variables statiques semid et block doivent etre valides.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="wack <timeout>").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
shm_wack_(int *timeout,		/* timeout */
	  int *status /* return status pointer */ )
{
	*status = shm_wack(*timeout);
}

int
shm_wack(int timeout		/* timeout */)
{
	int	status;
	char	message[12];

	if (shm_remote) {
		sprintf(message, "wack %d", timeout);
		return(write_to_ipc_server(message));
	}
	if (block == 0)
		return(-1);

	if ((status = wait_for_sem(semid, 2, timeout)) != 0)
		return(status);

	status = block->err_server;

	if (block->stat_server != 0)
		status = block->stat_server;

	return(status);
}

/*
 * Libere le server
 * 
 * Utilise par le client ou le serveur pour rendre la main.
 * 
 * STATIC: La variable statique semid doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="free").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 * 
 */
void
shm_free_(int *status /* return status pointer */ )
{
	*status = shm_free();
}

int
shm_free(void)
{
	if (shm_remote) {
		return(write_to_ipc_server("free"));
	}

	if (block == 0)
		return(-1);

	return(inc_sem(semid, 0));
}
/****************************************************************/
/****************/
/****************      SIGNAL*/
/****************/
/****************/
/****************************************************************/

/*
 * Envoye un signal au serveur
 * 
 * La fonction fait un kill() sur block->pid_server
 * 
 * STATIC: La variable statique block doit etre valide.
 * 
 * REMOTE: Cette fonction est valide en mode remote (commande="sign <signal>").
 * 
 * RETURN: Le status est retourne normallement a 0 ou -1 en cas d'erreur.
 */
void
send_signal_(int *sig,		/* signal number pointer */
	     int *status /* return status pointer */ )
{
	*status = send_signal(*sig);
}

int
send_signal(int sig		/* signal number pointer */)
{
	char	message[12];

	if (shm_remote) {
		sprintf(message, "sign %d", sig);
		return(write_to_ipc_server(message));
	}
	if (block == 0)
		return(-1);
	if (block->pid_server == 0)
		return(-1);

	return(kill(block->pid_server, sig));
}

