/*
 * _____________________________________________________
 * ____________________________________________________________
 * ___________/_/_/_/_/______/_/_/_/_/___________/_/_/_/_/_____________
 * __________/_/      ______/_/    _/___________/_/    _/_________________
 * _________/_/  _/_/______/_/    _/___________/_/_/_/_/____________________
 * ________/_/    _/______/_/    _/___________/_/      ________________
 * _______/_/_/_/_/ENEVA_/_/_/_/_/BSERVATORY_/_/ROTOCOL__________
 * _____________________________________________________
 * _____________________________________
 * 
 */


/*
 * REMARQUE/INFO: a propos des packets de type End_Of_Message (EOM): ce type
 * de packet est similaire au packet de donnée, le premier byte du header
 * vaut "E" au lieu de "H". La fonction gop_write() la routine bas niveau
 * utilisée dans tout les cas; c'est a dire que le byte
 * connect->header.header_type est initialisé par gop_write_end_of_message()
 * qui utilise gop_write(). Cela signifie que gop_write() ne doit pas
 * modifier ce premier byte. C'est donc pour cela que les fonctions qui
 * pourait changer connect->header.header_type (exemple typique
 * gop_write_end_of_message()) ou celles qui recoivent une EOM doivent
 * absolument remettre ce byte a GOP_HEADER_STD pour que les appels suivants
 * a gop_write() envoient reelement des headers standards et non des EOM.
 */

/*
 * REMARQUE/INFO: avec l'utilisation d'un transmetteur (gop_forward())
 * l'interruption par CTRL-C n'est possible qu'avec la synchronisation des
 * header et des donnees (GOP_SYNCHRO)
 */

/*
 * REMARQUE/INFO: si psize est donne negatif, cela signifie que l'on ne doit
 * pas changer la taille des packet durant un forward (voir avec
 * gop_read_matrix() et gop_write_matrix())
 */

/*
 * 15/2/96 CLOSE_CONNECTION. j'enleve les close_connection() durant les read
 * et write apres un GOP_DISCONNECT ou GOP_BROKEN_PIPE. C'est le user
 * qui doit le faire.
 */

/*
 * REMARQUE/INFO: 
 */
#include <stdio.h>
#include <unistd.h>
#include <stdarg.h>
#include <strings.h>
#include <stdlib.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <sys/socket.h>
#include <netdb.h>
#include <sys/un.h>
#include <netinet/in.h>
#include <sys/file.h>
#include <malloc.h>
#include <alloca.h>
#include <rpc/rpc.h>
#include <sys/timeb.h>
#include <signal.h>
#include <sys/utsname.h>
#include <ulimit.h>
#include <arpa/inet.h>

#ifdef LINUX
#include <sys/poll.h>
#endif

#include <gop.h>
static void	gop_reinit_handler();
static int	gop_read_core();
static int	gop_write_core();
static int	gop_init_registration();

#ifdef USE_STRERROR
#    define my_strerror(x)  strerror(x)
#else
     extern char           *sys_errlist[];
#    define my_strerror(x)  sys_errlist[x]
#endif

//static int counter_recv=0;

/*
 * REMARQUE/INFO: les variables memo* permettent de memoriser un message
 * arrivant a un mauvais moment lors d'une sequence de forward.
 * 
 * Typique: un client envoie une commande vers un serveur via un transmetteur.
 * Le serveur (qui a un coté client vers un logbook par exemple) envoie juste
 * apres la fin du poll() également une commande. La commande venant du
 * serveur peut etre comprise pour le acknowledge de la commande di serveur
 * vers le client.
 * 
 * Pour eviter cela on stocke le message du serveur dans le variables memo*, on
 * finit la communication en cours. Et seulement ensuite on rejoue le forward
 * du message memorise.
 * 
 * Dans ce cas IL FAUT seulement un message qui sort du serveur à la fois, le
 * serveur doit etre capable de traiter une commande si elle se presente, IL
 * FAUT transmettre le message en mode completement asynchrone, Il faut ne
 * pas ettendre de retour a ce message. C'est donc une modification qui est
 * faite uniquement pour un serveur qui a une partie client-serveur branche
 * sur un transmetteur. Tous les autres cas, ou il n'y a pas de collision
 * sont traites de manière sur.
 */
static	struct gop_connect	memo_connect;
static	char			memo_data_section[2048];
static	int			memo_action=FALSE;


int		gop_errno;
int		gop_broken_pipe=GOP_FALSE;

//static char		tail[2000];

static int 
gop_header_read_without_acknow (struct gop_connect *connect);


/* fonctions de remplacament de  la fonction system() */

//int
//gop_system_rsh_OLD(char *program, char *host)
//{
//	/*
//	 * lance une commande systeme en rsh
//	 */
//	char            true_host[256];
//	int             status;
//	sigset_t        set;
//
//	printf("GOP_SYSTEM_RSH: %s  -- host = %s\n", program, host);
//
//
//	switch (vfork()) {
//	case -1:		/* error */
//		return (-1);
//	case 0:		/* child */
//		if (host == (char *) NULL || *host == (char) 0) {
//			strcpy(true_host, "localhost");
//		} else {
//			strcpy(true_host, host);
//		}
//		if (sigfillset(&set) != 0) {
//			perror("gop_system_rsh(): sigfillset");
//			_exit(127);
//		}
//		if (sigprocmask(SIG_BLOCK, &set, NULL) != 0) {
//			perror("gop_system_rsh(): sigprocmask");
//			_exit(127);
//		}
//		status = execl("/bin/rsh", "rsh", "-n", true_host, program, "&", NULL);
//		if (status != 0) {
//			perror("gop_system_rsh(): execl /bin/rsh");
//		}
//		_exit(127);
//	}
//	return (0);
//}


int
gop_system(char *program)
{
	/*
	 * lance une commande systeme selon le shell décrit dans la variable
	 * SHELL (comme en Fortran). Si cette variable n'est pas définie on
	 * envoie la commande system() avec un message de warning.
	 */
	int             pid;
	int             status;
	char           *shell;
	char           *name;
	char            message[80];

	printf("GOP_SYSTEM: %s\n", program);

	shell = getenv("SHELL");
	if (shell == (char *) NULL) {
		fprintf(stderr, "gop_system():Warning SHELL variable undefined, we use system()\n");
		if (system(program) != 0) {
			perror("gop_system():system()");
			return (-1);
		}
		return (0);
	}
	/* cas normal */
	switch (pid = vfork()) {
	case -1:
		/* error */
		return (-1);

	case 0:
		/* child */
		name = strrchr(shell, '/') + 1;

		status = execl(shell, name, "-c", program, NULL);
		if (status != 0) {
			sprintf(message, "gop_system(): execl %s", shell);
			perror(message);
		}
		_exit(127);
	}
	do{
		status = wait4(pid, (int *) NULL, 0, (struct rusage *) NULL);
	} while (status==-1 && errno == EINTR);
	
	return(status);
}


int
gop_system_rsh(char *program, char *host)
{
	/*
	 * lance une commande systeme en rsh
	 */
	char            true_host[256];
	char            command[256];

	printf("GOP_SYSTEM_RSH: %s  -- host = %s\n", program, host);


	if (host == (char *) NULL || *host == (char) 0) {
		strcpy(true_host, "localhost");
	} else {
		strcpy(true_host, host);
	}

	sprintf(command, "rsh -n %s %s", true_host, program);
	return(gop_system(command));
}



/* registration sur l'utilitaire processes */


int
gop_process_registration(char *name, int port, char *socket_name, int sem_id, int shm_id)
{
	char	pro_host[256];
	char	my_name[32];
	int	pro_port;
	int	stat;
	char	hostname[MAXHOSTNAMELEN];
	char	*ptr;

        struct gop_connect *connect;

	if((stat = gop_init_registration(pro_host, &pro_port)) != 0)
		return(stat);
	gop_printf("INFO: Enregistrement de \"%s\" sur \"processes\", host=%s port=%d\n",
		name, pro_host, pro_port); 

        connect = (struct gop_connect *) gop_alloc_connect_structure();
	if(connect == (struct gop_connect *) NULL)
		return(-1);

/**	version nodename **
	uname(&uts);     **/
	gethostname(hostname, MAXHOSTNAMELEN);
	/* rejet si le node name est présent ex glspc1.ls.eso.org */
	if((ptr = index(hostname, '.')) != (char *) NULL){
		*ptr = (char) 0;
	}
	
	strcpy(my_name, name);
        gop_init_client_socket(connect, my_name, pro_host, pro_port, 1024, 0, 60);

        if (gop_connection(connect) != GOP_OK) 
		return(-7);


/**	version nodename **
	sprintf(pro_host,"#set#%s#%s#%d#%d#%s#%d#%d", name, uts.nodename,
		getpid(), port, socket_name, sem_id, shm_id);   **/
		
	sprintf(pro_host,"#set#%s#%s#%d#%d#%s#%d#%d", name, hostname,
		getpid(), port, socket_name, sem_id, shm_id);

	if (gop_write_command(connect, pro_host) != GOP_OK) 
		return(-8);
/**
	if (gop_close_connection(connect) != GOP_OK) 
		return(-9);
**/
	return(0);

}

int
gop_process_unregistration(char *name)
{
	fprintf(stderr,"Sorry gop_process_unregistration not implemented (for %s)\n", name);
	return(0);
}

/**
	Interface fortran
**/

void
gop_process_registration_(char *name, int *port, char *socket_name, int *sem_id, int *shm_id)
{
	gop_process_registration(name, *port, socket_name, *sem_id, *shm_id);
}

void
gop_process_unregistration_(char *name)
{
	gop_process_unregistration(name);
}


static int
gop_init_registration(char *pro_host, int *pro_port)
{
	char	*root;
	char	*instrument;
	FILE	*pfile;
	char	str[256];


	root = (char *)getenv("HOME");
	if(root == (char *) NULL)
		return(-2);
	instrument = (char *)getenv("INSTRUMENT");
	if(instrument == (char *) NULL){
		sprintf(str, "%s/.processes_coralie", root);
	} else {
		sprintf(str, "%s/.processes_%s", root, getenv("INSTRUMENT"));
	}
	gop_printf("INFO: gop_init_registration open de \"%s\"\n",str);
	if ((pfile = fopen(str, "r")) == NULL) 
		return(-3);
	
	if (fgets(str, sizeof(str), pfile) == (char *) NULL)	
		return(-4);
	if (fscanf(pfile, "%s", pro_host) == 0)
		return(-5);
	if (fscanf(pfile, "%d", pro_port) == 0)
		return(-6);

	return(0);
}

static void     (*gop_fct_printf_std) (char *);


int gop_printf(char *key,...)
{
	va_list         pvar;
	char 		date[32];
	char            str[4096];
	char            out[4096];

	struct timeval  tp;
	gettimeofday(&tp, (void *) NULL);
	
	sprintf(date, "%10d.%6.6d", (int)tp.tv_sec, (int)tp.tv_usec);
	
	va_start(pvar, key);
	vsprintf(str, key, pvar);
	va_end(pvar);

	if (gop_fct_printf_std == NULL){
		fprintf(stderr, "%s %s", date, str);
	} else {
		sprintf(out,"%s %s", date, str);
		gop_fct_printf_std(out);
	}
		
	return(0);
}

/*
 * permet d'enregistrer une fonction pour l'ecriture des messsage
 */
void
gop_registration_for_printf(void (*fct) ())
{
	gop_fct_printf_std = fct;
}
/*
 * permet de de enregistrer une fonction pour l'ecriture des messsage
 */
void
gop_unregistration_for_printf()
{
	gop_fct_printf_std = NULL;
}



struct gop_connect *
gop_alloc_connect_structure (void)
{
	struct gop_connect	*ptr;

	ptr = (struct gop_connect *) malloc(sizeof(struct gop_connect));

	if(ptr != NULL)
		memset(ptr, 0 , sizeof(struct gop_connect));

	gop_set_my_name(ptr, "-unset--");
	gop_set_his_name(ptr, "-unset--");
	gop_set_maxpacket(ptr, 1024);
	gop_set_stamp(ptr, GOP_TRUE);
	gop_set_class(ptr, GOP_CLASS_DATA);
	gop_set_from(ptr, "-unset--");
	gop_set_to(ptr, "-unset--");
	gop_set_stat(ptr, GOP_STAT_OPOK);
	ptr->cd = -1;
	ptr->cd_init = -1;

	return(ptr);
}



int 
gop_parse_opt_cmd_line (struct gop_connect *connect)
{
	char           *ptr;

	/*
	 * decode les argument de la forme:
	 * 
	 * port:host:mode:timeout:stamp:hsync:dsync
	 * 
	 * host est le seul champ de type caractere, les autres sont numerique
	 * (1=true, 0=false)
	 * 
	 * pose des defauts aux champs contenant de mauvaise valeur:
	 * defaut=9999:"localhost":3:0:1:0:0
	 */

	/*
	 * on pose les defauts
	 */
	if (*(connect->name) == (char) 0)
		strcpy(connect->name, "localhost");
	if (connect->port <= 0)
		connect->port = 9999;
	if (connect->mode < 0)
		connect->mode = 0;
	if (connect->mode > 9)
		connect->mode = 9;
	if (connect->timeout < 0)
		connect->timeout = 0;
	if (connect->stamp < 0 || connect->stamp > 1)
		connect->stamp = 1;
	if (connect->hsync < 0 || connect->hsync > 1)
		connect->hsync = 0;
	if (connect->dsync < 0 || connect->dsync > 1)
		connect->dsync = 0;
	/*
	 * lecture des arguments
	 */

	ptr = (char *) strtok(optarg, ":");
	if (ptr == (char *) NULL)
		return (GOP_OK);
	if (strcmp(ptr, "-") != 0)
		connect->port = atoi(ptr);

	ptr = (char *) strtok(NULL, ":");
	if (ptr == (char *) NULL)
		return (GOP_OK);
	if (strcmp(ptr, "-") != 0)
		strcpy(connect->name, ptr);

	ptr = (char *) strtok(NULL, ":");
	if (ptr == (char *) NULL)
		return (GOP_OK);
	if (strcmp(ptr, "-") != 0)
		connect->mode = atoi(ptr);

	ptr = (char *) strtok(NULL, ":");
	if (ptr == (char *) NULL)
		return (GOP_OK);
	if (strcmp(ptr, "-") != 0)
		connect->timeout = atoi(ptr);

	ptr = (char *) strtok(NULL, ":");
	if (ptr == (char *) NULL)
		return (GOP_OK);
	if (strcmp(ptr, "-") != 0)
		connect->stamp = atoi(ptr);

	ptr = (char *) strtok(NULL, ":");
	if (ptr == (char *) NULL)
		return (GOP_OK);
	if (strcmp(ptr, "-") != 0)
		connect->hsync = atoi(ptr);

	ptr = (char *) strtok(NULL, ":");
	if (ptr == (char *) NULL)
		return (GOP_OK);
	if (strcmp(ptr, "-") != 0)
		connect->dsync = atoi(ptr);

	return (GOP_OK);
}




static int	remote_status;

char *
gop_get_error_str (void)
{
	static char    *message[32] = {
		"GOP_OK",
		"GOP_ERRNO",
		"GOP_DISCONNECT",
		"GOP_INVALID_VERSION",
		"GOP_TIMEOUT",
		"GOP_TOO_BIG",
		"GOP_BAD_PROTOCOL",
		"GOP_NOT_IMPLEMENTED",
		"GOP_BROKEN_PIPE",
		"GOP_BAD_SEQUENCE",
		"GOP_RECEIVER_UNKNOWN",
		"GOP_END_OF_MESSAGE",
		"GOP_ALLOC",
		"GOP_ECONNRESET",
		"GOP_BAD_CHANNEL",
		"GOP_XDR_FAILED",
		"GOP_REMOTE_PROBLEM:",
		"GOP_INTERRUPTED_SYSTEM_CALL",
		"GOP_INTERRUPTED_TRANSMISSION",
		"GOP_EOM_TOO_BIG",
		"GOP_BLOCKING",
		"GOP_BAD_HOST_NAME"
	};

	if (gop_errno == GOP_ERRNO)
		return (my_strerror(errno));
	if(gop_errno == GOP_REMOTE_PROBLEM){
		sprintf(message[gop_errno],"GOP_REMOTE_PROBLEM: %s", message[remote_status]);
	}
	return (message[gop_errno]);
}



static int
gop_size_of_datatype(int datatype)
{
	switch (datatype) {
	case GOP_CHAR:
	case GOP_STRUCT:
		return (1);
	case GOP_USHORT:
	case GOP_SHORT:
		return (2);
	case GOP_UINT:
	case GOP_INT:
	case GOP_ULONG:
	case GOP_LONG:
	case GOP_FLOAT:
		return (4);
	case GOP_DOUBLE:
		return (8);
	}
	return(-1);
}

/*
 * GESTION DES SIGNAUX
 */


/**
 * gop_stack_handler_XXXX:   stacks tournants pour le  stockage des handler
 * gop_pointer_handler_XXXX: index sur ces stacks 
 **/
static int             gop_pointer_handler_INT  = 0;
static int             gop_pointer_handler_URG  = 0;
static int             gop_pointer_handler_ALRM = 0;
static int             gop_pointer_handler_PIPE = 0;
static int             gop_pointer_handler_HUP  = 0;

static void             (*gop_stack_handler_INT[10])();
static void             (*gop_stack_handler_URG[10])();
static void             (*gop_stack_handler_ALRM[10])();
static void             (*gop_stack_handler_PIPE[10])();
static void             (*gop_stack_handler_HUP[10])();


/**
 #####    ###    #####    ###   #     # #######
#     #    #    #     #    #    ##    #    #
#          #    #          #    # #   #    #
 #####     #    #  ####    #    #  #  #    #
      #    #    #     #    #    #   # #    #
#     #    #    #     #    #    #    ##    #
 #####    ###    #####    ###   #     #    #
**/
static void
gop_push_handler_INT(void (*handler)())
{
	gop_pointer_handler_INT = (gop_pointer_handler_INT + 1) %
		(sizeof(gop_stack_handler_INT) / sizeof(int));
	if (gop_pointer_handler_INT == 0) {
		fprintf(stderr,"*|* Attention Buffer tournant en usage lors de gop_push_handler_INT.\n");
		fprintf(stderr,"*|* Cette situation est illegale, mais est corrigee.\n");
		fprintf(stderr,"*|* Il faut neanmoins savoir pourquoi on a stocke autant de handler\n");
		fprintf(stderr,"*|* C'est normalement du a mauvaise balance entre les push et les pop dans libgop.c\n");
	}
	gop_stack_handler_INT[gop_pointer_handler_INT] = handler;
}

static void (*gop_pop_handler_INT())()
{
	int	crt=gop_pointer_handler_INT;
	gop_pointer_handler_INT = (gop_pointer_handler_INT - 1) % 
				(sizeof(gop_stack_handler_INT) / sizeof(int));
	return(gop_stack_handler_INT[crt]);
}

static void (*gop_get_handler_INT())()
{
	return(gop_stack_handler_INT[gop_pointer_handler_INT]);
}
/**
 #####    ###    #####  #     # ######   #####
#     #    #    #     # #     # #     # #     #
#          #    #       #     # #     # #
 #####     #    #  #### #     # ######  #  ####
      #    #    #     # #     # #   #   #     #
#     #    #    #     # #     # #    #  #     #
 #####    ###    #####   #####  #     #  #####
**/
static void
gop_push_handler_URG(void (*handler)())
{
	gop_pointer_handler_URG = (gop_pointer_handler_URG + 1) %
		(sizeof(gop_stack_handler_URG) / sizeof(int));
	if (gop_pointer_handler_URG == 0) {
		fprintf(stderr,"*|* Attention Buffer tournant en usage lors de gop_push_handler_URG.\n");
		fprintf(stderr,"*|* Cette situation est illegale, mais est corrigee.\n");
		fprintf(stderr,"*|* Il faut neanmoins savoir pourquoi on a stocke autant de handler\n");
		fprintf(stderr,"*|* C'est normalement du a mauvaise balance entre les push et les pop dans libgop.c\n");
	}
	gop_stack_handler_URG[gop_pointer_handler_URG] = handler;
}

static void (*gop_pop_handler_URG())()
{
	int	crt=gop_pointer_handler_URG;
	gop_pointer_handler_URG = (gop_pointer_handler_URG - 1) % 
				(sizeof(gop_stack_handler_URG) / sizeof(int));
	return(gop_stack_handler_URG[crt]);
}

static void (*gop_get_handler_URG())()
{
	return(gop_stack_handler_URG[gop_pointer_handler_URG]);
}
/**
 #####    ###    #####     #    #       ######  #     #
#     #    #    #     #   # #   #       #     # ##   ##
#          #    #        #   #  #       #     # # # # #
 #####     #    #  #### #     # #       ######  #  #  #
      #    #    #     # ####### #       #   #   #     #
#     #    #    #     # #     # #       #    #  #     #
 #####    ###    #####  #     # ####### #     # #     #
**/
static void
gop_push_handler_ALRM(void (*handler)())
{
	gop_pointer_handler_ALRM = (gop_pointer_handler_ALRM + 1) %
		(sizeof(gop_stack_handler_ALRM) / sizeof(int));
	if (gop_pointer_handler_ALRM == 0) {
		fprintf(stderr,"*|* Attention Buffer tournant en usage lors de gop_push_handler_ALRM.\n");
		fprintf(stderr,"*|* Cette situation est illegale, mais est corrigee.\n");
		fprintf(stderr,"*|* Il faut neanmoins savoir pourquoi on a stocke autant de handler\n");
		fprintf(stderr,"*|* C'est normalement du a mauvaise balance entre les push et les pop dans libgop.c\n");
	}
	gop_stack_handler_ALRM[gop_pointer_handler_ALRM] = handler;
}

static void (*gop_pop_handler_ALRM())()
{
	int	crt=gop_pointer_handler_ALRM;
	gop_pointer_handler_ALRM = (gop_pointer_handler_ALRM - 1) % 
				(sizeof(gop_stack_handler_ALRM) / sizeof(int));
	return(gop_stack_handler_ALRM[crt]);
}

/** not used
static void (*gop_get_handler_ALRM())()
{
	return(gop_stack_handler_ALRM[gop_pointer_handler_ALRM]);
}
**/
/**
 #####    ###    #####  ######    ###   ######  #######
#     #    #    #     # #     #    #    #     # #
#          #    #       #     #    #    #     # #
 #####     #    #  #### ######     #    ######  #####
      #    #    #     # #          #    #       #
#     #    #    #     # #          #    #       #
 #####    ###    #####  #         ###   #       #######
**/
static void
gop_push_handler_PIPE(void (*handler)())
{
	gop_pointer_handler_PIPE = (gop_pointer_handler_PIPE + 1) %
		(sizeof(gop_stack_handler_PIPE) / sizeof(int));
	if (gop_pointer_handler_PIPE == 0) {
		fprintf(stderr,"*|* Attention Buffer tournant en usage lors de gop_push_handler_PIPE.\n");
		fprintf(stderr,"*|* Cette situation est illegale, mais est corrigee.\n");
		fprintf(stderr,"*|* Il faut neanmoins savoir pourquoi on a stocke autant de handler\n");
		fprintf(stderr,"*|* C'est normalement du a mauvaise balance entre les push et les pop dans libgop.c\n");
	}
	gop_stack_handler_PIPE[gop_pointer_handler_PIPE] = handler;
}

static void (*gop_pop_handler_PIPE())()
{
	int	crt=gop_pointer_handler_PIPE;
	gop_pointer_handler_PIPE = (gop_pointer_handler_PIPE - 1) % 
				(sizeof(gop_stack_handler_PIPE) / sizeof(int));
	return(gop_stack_handler_PIPE[crt]);
}

static void (*gop_get_handler_PIPE())()
{
	return(gop_stack_handler_PIPE[gop_pointer_handler_PIPE]);
}

/**
 #####    ###    #####  #     # #     # ######
#     #    #    #     # #     # #     # #     #
#          #    #       #     # #     # #     #
 #####     #    #  #### ####### #     # ######
      #    #    #     # #     # #     # #
#     #    #    #     # #     # #     # #
 #####    ###    #####  #     #  #####  #
**/


static void
gop_push_handler_HUP(void (*handler)())
{
	gop_pointer_handler_HUP = (gop_pointer_handler_HUP + 1) %
		(sizeof(gop_stack_handler_HUP) / sizeof(int));
	if (gop_pointer_handler_HUP == 0) {
		fprintf(stderr,"*|* Attention Buffer tournant en usage lors de gop_push_handler_HUP.\n");
		fprintf(stderr,"*|* Cette situation est illegale, mais est corrigee.\n");
		fprintf(stderr,"*|* Il faut neanmoins savoir pourquoi on a stocke autant de handler\n");
		fprintf(stderr,"*|* C'est normalement du a mauvaise balance entre les push et les pop dans libgop.c\n");
	}
	gop_stack_handler_HUP[gop_pointer_handler_HUP] = handler;
}

static void (*gop_pop_handler_HUP())()
{
	int	crt=gop_pointer_handler_HUP;
	gop_pointer_handler_HUP = (gop_pointer_handler_HUP - 1) % 
				(sizeof(gop_stack_handler_HUP) / sizeof(int));
	return(gop_stack_handler_HUP[crt]);
}

static void (*gop_get_handler_HUP())()
{
	return(gop_stack_handler_HUP[gop_pointer_handler_HUP]);
}




/*
 * pointeurs sur la structure utilisee dans la communication courante.
 * Necessaire pour pouvoir la passer aux handlers.
 */


struct gop_connect *gop_connect_client = (struct gop_connect *) NULL;


/*
 * gop_SIGINT_handler(): envoi un Out Of Band message (OOB) en mode socket si
 * on est cote client et que l'on recoit des données. Execute le handler
 * utilisateur et memorise dans la structure gop_connect_client que
 * l'interruption a eu lieu.
 */


static void
gop_SIGINT_handler(int sig)
{
	void	(*gop_fct_SIGINT_std)();
	char            buf;
	struct gop_connect *gop_connect_client_temp;

	gop_connect_client_temp = gop_connect_client;

	gop_printf("gop: [%8s] -> [%8s] gop_SIGINT_handler %d\n",
		gop_connect_client_temp->my_name, gop_connect_client_temp->his_name, sig); 

	if (gop_connect_client_temp->side == GOP_CLIENT_SIDE) {
		if (gop_connect_client_temp->type == GOP_SOCKET &&
		    gop_connect_client_temp->opcrt == GOP_READ) {
			gop_printf("gop: [%8s] -> [%8s] envoi OOB sur server, cd=%d\n", 
				gop_connect_client_temp->my_name, gop_connect_client_temp->his_name, gop_connect_client_temp->cd); 
			if (send(gop_connect_client_temp->cd, &buf, 1, MSG_OOB) != 1) {
				perror("gop_SIGINT_handler");
				gop_printf("gop: [%8s] -> [%8s] probleme a l'envoi de OOB\n", 
					gop_connect_client_temp->my_name, gop_connect_client_temp->his_name); 
			} else {
				gop_printf("gop: [%8s] -> [%8s] OOB transmis sur server, cd= %d\n", 
					gop_connect_client_temp->my_name, gop_connect_client_temp->his_name, 
					gop_connect_client_temp->cd);
			}
		} else if (gop_connect_client_temp->type == GOP_SOCKET_UNIX &&
			   gop_connect_client_temp->opcrt == GOP_READ) {
			gop_printf("gop: [%8s] -> [%8s] envoi de SIGURG sur server, pid= %d\n", 
				gop_connect_client_temp->my_name, gop_connect_client_temp->his_name, gop_connect_client_temp->pid); 
			if (kill(gop_connect_client_temp->pid, SIGURG) != 0) {
				perror("gop_SIGINT_handler");
				gop_printf("gop: [%8s] -> [%8s] probleme a l'envoi de SIGURG\n", 
					gop_connect_client_temp->my_name, gop_connect_client_temp->his_name); 
			} else {
				gop_printf("gop: [%8s] -> [%8s] SIGURG transmis sur server, pid= %d\n", 
					gop_connect_client_temp->my_name, gop_connect_client_temp->his_name, 
					gop_connect_client_temp->pid);
			}
		}
	}
	/*
	 * envoi de la fonction utilisateur si elle existe et si ce n'est pas recursif
	 */
	gop_fct_SIGINT_std = gop_get_handler_INT();
	if (gop_fct_SIGINT_std != NULL && gop_fct_SIGINT_std != gop_SIGINT_handler) {
		gop_printf("gop: [%8s] -> [%8s] gop_SIGINT_handler: envoi de la fonction enregistree\n", 
			gop_connect_client_temp->my_name, gop_connect_client_temp->his_name);
		gop_connect_client = gop_connect_client_temp;
		gop_fct_SIGINT_std(SIGINT);
	}
	/*
	 * du au fortran on doit reinitialiser le handler
	 */
	gop_reinit_handler(SIGINT);

	gop_connect_client_temp->interrupted = GOP_INTERRUPTED;
}


static void 
gop_send_sigurg (struct gop_connect *connect)
{
	char            buf;

	if (connect->type == GOP_SOCKET) {
		gop_printf("gop: [%8s] -> [%8s] envoi OOB sur server, cd= %d\n", 
			connect->my_name, connect->his_name, connect->cd); 
		if (send(connect->cd, &buf, 1, MSG_OOB) != 1) {
			perror("gop_send_sigurg");
			gop_printf("gop: [%8s] -> [%8s] probleme a l'envoi de OOB\n", 
				connect->my_name, connect->his_name); 
		} else {
			gop_printf("gop: [%8s] -> [%8s] OOB transmis sur server, cd= %d\n", 
				connect->my_name, connect->his_name, connect->cd);
		}
	} else if (connect->type == GOP_SOCKET_UNIX) {
		gop_printf("gop: [%8s] -> [%8s] envoi de SIGURG sur server, pid= %d\n", 
			connect->my_name, connect->his_name, connect->pid); 
		if (kill(connect->pid, SIGURG) != 0) {
			perror("gop_send_sigurg");
			gop_printf("gop: [%8s] -> [%8s] probleme a l'envoi de SIGURG\n", 
				connect->my_name, connect->his_name); 
		} else {
			gop_printf("gop: [%8s] -> [%8s] SIGURG transmis sur server, pid= %d\n", 
				connect->my_name, connect->his_name, connect->pid);
		}
	}
}

/*
 * gop_SIGURG_handler(): Si on est en transmission, repercute le OOB sur le
 * server. Sinon, execute le handler utilisateur et memorise dans la
 * structure gop_connect_client que l'interruption a eu lieu.
 */


static void
gop_SIGURG_handler(int sig)
{
	void	(*gop_fct_SIGURG_std)();
	struct gop_connect *gop_connect_client_temp;

	gop_connect_client_temp = gop_connect_client;

	gop_printf("gop: [%8s] <> [%8s] gop_SIGURG_handler %d\n", 
		gop_connect_client_temp->my_name, gop_connect_client_temp->his_name,sig); 

	gop_connect_client_temp->interrupted = GOP_INTERRUPTED;

	if (gop_connect_client_temp->side == GOP_TRANSMIT_SIDE) {
		if (gop_connect_client_temp->opcrt == GOP_SELECT) {
			gop_printf("gop: [%8s] <- [SIGURG--] Pas d'operation car on est en train de faire un poll() ou select()\n", 
					gop_connect_client_temp->my_name); 
			return;
		} 
		gop_send_sigurg(gop_connect_client_temp);
		return;
	}
	/*
	 * envoi de la fonction utilisateur si elle existe et si ce n'est pas recursif
	 */
	gop_fct_SIGURG_std = gop_get_handler_URG();
	if (gop_fct_SIGURG_std != NULL && gop_fct_SIGURG_std != gop_SIGURG_handler) {
		gop_printf("gop: [%8s] <- [SIGURG--] gop_SIGURG_handler: envoi de la fonction enregistree\n", 
			gop_connect_client_temp->my_name);
		gop_connect_client = gop_connect_client_temp;
		gop_fct_SIGURG_std(SIGURG);
	}
}


static void
gop_SIGPIPE_handler(int sig)
{
	void	(*gop_fct_SIGPIPE_std)();
	struct gop_connect *gop_connect_client_temp;

	gop_connect_client_temp = gop_connect_client;

	/*
	 * ATTENTION: si on a un broken pipe sur le logbook, cet appel est
	 * apelle recursivement et fini par planter (dans le cas ou
	 * gop_printf ecrit sur le logbook).
	 * 
	 * On detecte donc si le destinataire est le logbook (his_name) et dans
	 * ce cas on deenregistre la fonction d'ecriture.
	 * 
	 * Cela veut aussi dire que le logbook doit s'appeler " logbook" 
         * sous GOPgrrr!!!.
	 */
	if(strcmp(gop_connect_client_temp->his_name, " logbook") == 0){
		gop_unregistration_for_printf();
	}
	gop_printf("gop: [%8s] <> [%8s] gop_SIGPIPE_handler %d\n",
		 gop_connect_client_temp->my_name, gop_connect_client_temp->his_name, sig);
	gop_broken_pipe = GOP_TRUE;
	/*
	 * envoi de la fonction utilisateur si elle existe et si ce n'est pas recursif
	 */
	gop_fct_SIGPIPE_std = gop_get_handler_PIPE();
	if (gop_fct_SIGPIPE_std != NULL && gop_fct_SIGPIPE_std != gop_SIGPIPE_handler) {
		gop_printf("gop: [%8s] <- [SIGPIPE-] gop_SIGPIPE_handler: envoi de la fonction enregistree\n",
			   gop_connect_client_temp->my_name);
		gop_connect_client = gop_connect_client_temp;
		gop_fct_SIGPIPE_std(SIGPIPE);
	}
}


static void
gop_SIGALRM_handler(int sig)
{
	if(gop_connect_client != (struct gop_connect *) NULL){
		gop_printf("gop: [%8s] <> [%8s] gop_SIGALRM_handler (ne fait rien) %d\n", 
			gop_connect_client->my_name, gop_connect_client->his_name,sig);
	} else {
		gop_printf("gop: [--------] <> [--------] gop_SIGALRM_handler (ne fait rien) %d\n",sig);
	}
}



static void
gop_SIGHUP_handler(int sig)
{
	void	(*gop_fct_SIGHUP_std)();
	struct gop_connect *gop_connect_client_temp;

	gop_connect_client_temp = gop_connect_client;

	gop_printf("gop: [%8s] <> [%8s] gop_SIGHUP_handler %d\n", 
		gop_connect_client_temp->my_name, gop_connect_client_temp->his_name, sig);
	/*
	 * envoi de la fonction utilisateur si elle existe et si ce n'est pas recursif
	 */
	gop_fct_SIGHUP_std = gop_get_handler_HUP();
	if (gop_fct_SIGHUP_std != NULL && gop_fct_SIGHUP_std != gop_SIGHUP_handler) {
		gop_printf("gop: [%8s] <- [SIGUP---] gop_SIGHUP_handler: envoi de la fonction enregistree %d\n", 
			gop_connect_client_temp->my_name, sig);
		gop_connect_client = gop_connect_client_temp;
		gop_fct_SIGHUP_std(SIGHUP);
	}
}



void 
gop_init_handler (int sig)
{
#ifndef BSD
	struct sigaction act;
	sigset_t        set;

	switch (sig) {
	case SIGINT:
		/*
		 * Initialise le handler gop qui permet de restarter les
		 * appels system s'il sont interrompus. Memorise le handler
		 * utilisateur courant dans le but de le lancer dans le
		 * handler gop_SIGINT_handler() et de le restaurer apres une
		 * communication avec gop_restore_handler(SIGINT).
		 * Initialise le flag d'interruption dans la structure de
		 * communication courante.
		 */
		sigemptyset(&set);
		act.sa_mask = set;
		act.sa_flags = SA_RESTART;
		act.sa_handler = gop_SIGINT_handler;

		gop_push_handler_INT(signal(SIGINT, gop_SIGINT_handler));

		sigaction(SIGINT, &act, (struct sigaction *) NULL);

		gop_connect_client->interrupted = GOP_OK;
		break;
	case SIGURG:
		/*
		 * Initialise le handler gop qui permet de restarter les
		 * appels system s'il sont interrompus. Memorise le handler
		 * utilisateur courant dans le but de le lancer dans le
		 * handler gop_SIGURG_handler() et de le restaurer apres une
		 * communication avec gop_restore_handler(SIGURG).
		 * Initialise le flag d'interruption dans la structure de
		 * communication courante.
		 */
		sigemptyset(&set);
		act.sa_mask = set;
		act.sa_flags = SA_RESTART;
		act.sa_handler = gop_SIGURG_handler;

		gop_push_handler_URG(signal(SIGURG, gop_SIGURG_handler));

		sigaction(SIGURG, &act, (struct sigaction *) NULL);

		gop_connect_client->interrupted = GOP_OK;
		break;
	case SIGALRM:
		gop_push_handler_ALRM(signal(SIGALRM, gop_SIGALRM_handler));
		break;
	case SIGPIPE:
		gop_push_handler_PIPE(signal(SIGPIPE, gop_SIGPIPE_handler));
		break;
	case SIGHUP:
		gop_push_handler_HUP(signal(SIGHUP, gop_SIGHUP_handler));
		break;
	}
#endif
}



static void 
gop_reinit_handler (int sig)
{
#ifndef BSD
	struct sigaction act;
	sigset_t        set;

	switch (sig) {
	case SIGINT:
		/*
		 * Initialise le handler gop qui permet de restarter les
		 * appels system s'il sont interrompus. Memorise le handler
		 * utilisateur courant dans le but de le lancer dans le
		 * handler gop_SIGINT_handler() et de le restaurer apres une
		 * communication avec gop_restore_handler(SIGINT).
		 * Initialise le flag d'interruption dans la structure de
		 * communication courante.
		 */
		sigemptyset(&set);
		act.sa_mask = set;
		act.sa_flags = SA_RESTART;
		act.sa_handler = gop_SIGINT_handler;

		sigaction(SIGINT, &act, (struct sigaction *) NULL);
		break;
	case SIGURG:
		/*
		 * Initialise le handler gop qui permet de restarter les
		 * appels system s'il sont interrompus. Memorise le handler
		 * utilisateur courant dans le but de le lancer dans le
		 * handler gop_SIGURG_handler() et de le restaurer apres une
		 * communication avec gop_restore_handler(SIGURG).
		 * Initialise le flag d'interruption dans la structure de
		 * communication courante.
		 */
		sigemptyset(&set);
		act.sa_mask = set;
		act.sa_flags = SA_RESTART;
		act.sa_handler = gop_SIGURG_handler;

		sigaction(SIGURG, &act, (struct sigaction *) NULL);
		break;
	case SIGALRM:
		break;
	case SIGPIPE:
		break;
	case SIGHUP:
		break;
	}
#endif

}




void 
gop_restore_handler (int sig)
{
	switch(sig){
	case SIGINT:
		signal(SIGINT, gop_pop_handler_INT());
		gop_connect_client->interrupted = GOP_OK;
		break;
	case SIGURG:
		signal(SIGURG, gop_pop_handler_URG());
		gop_connect_client->interrupted = GOP_OK;
		break;
	case SIGALRM:
		signal(SIGALRM, gop_pop_handler_ALRM());
		break;
	case SIGPIPE:
		signal(SIGPIPE, gop_pop_handler_PIPE());
		break;
	case SIGHUP:
		signal(SIGHUP, gop_pop_handler_HUP());
		break;
	}

}

/*


static void 
gop_sig_init_handler (void)
{
	(void) signal(SIGALRM, gop_SIGALRM_handler);
	(void) signal(SIGPIPE, gop_SIGPIPE_handler);
}


static void 
gop_sig_init_handler_ (void)
{
	(void) signal(SIGALRM, gop_SIGALRM_handler);
	(void) signal(SIGPIPE, gop_SIGPIPE_handler);
}

*/

#define GOP_XDR_HEADER_SIZE 4

static int             (*xdr_fct[9]) () = {
	xdr_char,
	xdr_short,
	xdr_u_short,
	xdr_int,
	xdr_u_int,
	xdr_long,
	xdr_u_long,
	xdr_float,
	xdr_double
};




static int 
gop_fill_bench_xdr (struct gop_bench_xdr *test)
{
	float	float_value = (float) 1.23456789;
	double	double_value = (double) 1.2345678901234567;

	test->j = (u_int) 0x01234567;
	test->l = float_value;
	test->m = double_value;
	
	return (GOP_OK);

}


static int 
gop_test_bench_xdr (struct gop_bench_xdr *test)
{
	float	float_value = (float) 1.23456789;
	double	double_value = (double) 1.2345678901234567;

#pragma warning(disable:1572)  /* floating-point equality and inequality comparisons are unreliable */
	if (test->j != (u_int) 0x01234567 ||
	    test->l != float_value ||
	    test->m != double_value)
		return (GOP_KO);
	return (GOP_OK);
}


static int 
gop_set_struct_standart (struct gop_connect *connect)
{
	strcpy(connect->class, GOP_CLASS_COMD);
	connect->cont = GOP_FALSE;
	connect->stamp = GOP_TRUE;
	connect->hsync = GOP_FALSE;
	connect->dsync = GOP_FALSE;
	strcpy(connect->stat, GOP_STAT_OPOK);
	connect->datatype = GOP_CHAR;
	
	return (GOP_OK);

}


static void 
gop_struct_to_header (struct gop_connect *connect)
{
	struct timeval  tp;
	struct timezone tzp;

	if (connect->mode >= GOP_MESSAGE)
		gop_printf("gop: [%8s] -> [%8s] \t fill header\n", connect->my_name, connect->his_name); 

	strcpy(connect->header.version, GOP_VERSION_CRT);
	strncpy(connect->header.class, connect->class,
				sizeof(connect->class)-1);
	*(connect->header.class+sizeof(connect->class)-1) = 0;
	/*
	 * date
	 */
	if (connect->stamp) {
		gettimeofday(&tp, &tzp);
		sprintf(connect->header.date, "%010ld.%03d", (long int)tp.tv_sec, (int)tp.tv_usec/1000);
	} else {
		*connect->header.date = 0;
	}

	sprintf(connect->header.from, "%8s", connect->from);
	sprintf(connect->header.to, "%8s", connect->to);

	if (connect->hsync)
		strcpy(connect->header.hsync, GOP_STR_TRUE);
	else
		strcpy(connect->header.hsync, GOP_STR_FALSE);

	if (connect->dsync)
		strcpy(connect->header.dsync, GOP_STR_TRUE);
	else
		strcpy(connect->header.dsync, GOP_STR_FALSE);

	sprintf(connect->header.mode, "%1d", 
		GOP_MIN(GOP_MAX(connect->mode, 0), 9));

	sprintf(connect->header.msize, "%10d", connect->msize);
	sprintf(connect->header.psize, "%10d", connect->psize);

	if (connect->cont)
		strcpy(connect->header.cont, GOP_STR_TRUE);
	else
		strcpy(connect->header.cont, GOP_STR_FALSE);

	strncpy(connect->header.stat, connect->stat, sizeof(connect->stat)-1);
	*(connect->header.stat+sizeof(connect->stat)-1) = 0;

	sprintf(connect->header.datatype, "%1d", 
		GOP_MIN(GOP_MAX(connect->datatype, 0),9));

	if (connect->need_xdr && !(connect->datatype==GOP_CHAR || connect->datatype==GOP_STRUCT))
		strcpy(connect->header.xdr, GOP_STR_TRUE);
	else
		strcpy(connect->header.xdr, GOP_STR_FALSE);


	strcpy(connect->header.end, "\n");
}



static void 
gop_header_to_struct (struct gop_connect *connect, struct gop_header *header)
{

	/*
	 * passe les elements de header dans connect
	 */

	strncpy(connect->class, header->class, sizeof(header->class)-1);
	*(header->class+sizeof(header->class)-1) = 0;
	connect->hsync = *(header->hsync) == 'T';
	connect->dsync = *(header->dsync) == 'T';
	connect->mode = atoi(header->mode);
	connect->msize = atoi(header->msize);
	connect->psize = atoi(header->psize);
	connect->cont = *(header->cont) == 'T';
	strncpy(connect->stat, header->stat, sizeof(header->stat)-1);
	*(header->stat+sizeof(header->stat)-1) = 0;
	connect->datatype = atoi(header->datatype);
	connect->xdr = *(header->xdr) == 'T';

}


void 
gop_set_destination (struct gop_connect *connect)
{
	strncpy(connect->to, connect->header.from, sizeof(connect->header.to));
	*(connect->header.to+sizeof(connect->header.to)-1) = 0;
	strncpy(connect->from, connect->header.to, sizeof(connect->header.from));
	*(connect->header.from+sizeof(connect->header.from)-1) = 0;


}



static int 
gop_socket_init_connection (struct gop_connect *connect)
{
	/*
	 * met à jour connect.cd
	 */

	struct sockaddr_in sinet;
	int             on = 1;

	/* Initialize the socket structure */
	(void) memset((char *) &sinet, 0, sizeof(sinet));
	sinet.sin_family = AF_INET;
#pragma warning(disable:2259) //non-pointer conversion from "int" to "unsigned short" may lose significant bits
#ifdef linux
	sinet.sin_port = htons(connect->port);
#else
	sinet.sin_port = htonl(connect->port);
#endif
	sinet.sin_addr.s_addr = INADDR_ANY;

	if (connect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] <- [%8s] gop_socket_init_connection() port=%d\n", 
			connect->my_name, connect->his_name, connect->port);
	}
	/* Get an internet domain socket */
	if ((connect->cd_init = socket(AF_INET, SOCK_STREAM, 0)) == EOF) {
		gop_errno = GOP_ERRNO;
		return (GOP_KO);
	}
	if (connect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] <- [%8s] \t socket()   cd=%d OK\n", 
			connect->my_name, connect->his_name,  connect->cd_init);
	}
	if (setsockopt(connect->cd_init, SOL_SOCKET, SO_REUSEADDR,
		       (const char *) &on, sizeof(on)) == EOF) {
		gop_errno = GOP_ERRNO;
		return (GOP_KO);
	}

	/* Bind the socket to the port number */

	if (bind(connect->cd_init, (struct sockaddr *) &sinet, sizeof(sinet)) == EOF) {
		gop_errno = GOP_ERRNO;
		return (GOP_KO);
	}

	if (connect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] <- [%8s] \t bind()     cd=%d OK\n", 
			connect->my_name, connect->his_name,  connect->cd_init);
	}
	/* Show that we are willing to listen */
	if (listen(connect->cd_init, 5) == EOF) {
		gop_errno = GOP_ERRNO;
		return (GOP_KO);
	}
	if (connect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] <- [%8s] \t listen()   cd=%d OK\n", 
			connect->my_name, connect->his_name,  connect->cd_init);
	}
	return(GOP_OK);
}


static int 
gop_socket_unix_init_connection (struct gop_connect *connect)
{
	/*
	 * met à jour connect.cd
	 */

	char	socket_name[256];
	struct	sockaddr_un	sunix;

	sprintf(socket_name,"%s/.socket.%s",getenv("HOME"),connect->name);
	unlink(socket_name);
	
 	if(connect->cd_init != 0) close(connect->cd_init);
	if(connect->cd != 0)      close(connect->cd);

	strcpy (sunix.sun_path, socket_name);
	sunix.sun_family = AF_UNIX;

	if (connect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] <- [%8s] gop_socket_unix_init_connection() socket_name=%s\n", 
			connect->my_name, connect->his_name, socket_name);
	}

	if((connect->cd_init = socket(AF_UNIX, SOCK_STREAM, 0)) == EOF) {
		gop_errno = GOP_ERRNO;
		return (GOP_KO);
	}
	if (connect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] <- [%8s] \t socket()   cd=%d OK\n", 
			connect->my_name, connect->his_name,  connect->cd_init);
	}

	if(bind(connect->cd_init, (struct sockaddr *) &sunix, 
		strlen(sunix.sun_path) + sizeof(sunix.sun_family)) == EOF) {
		gop_errno = GOP_ERRNO;
		return (GOP_KO);
	}

	if (connect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] <- [%8s] \t bind()     cd=%d OK\n", 
			connect->my_name, connect->his_name,  connect->cd_init);
	}

	if(listen(connect->cd_init, 5)  == EOF) {
		gop_errno = GOP_ERRNO;
		return (GOP_KO);
	}
	if (connect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] <- [%8s] \t listen()   cd=%d OK\n", 
			connect->my_name, connect->his_name,  connect->cd_init);
	}

	return(GOP_OK);
}



int 
gop_init_connection (struct gop_connect *connect)
{
	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <- [%8s] debut de init connection\n", 
			connect->my_name, connect->his_name); 

	connect->side = GOP_SERVER_SIDE;

	connect->cd = -1;
	connect->cd_init = -1;
        gop_errno = 0;

	switch (connect->type) {
	case GOP_SOCKET:
		(void) gop_socket_init_connection(connect);
		break;
	case GOP_SOCKET_UNIX:
		(void) gop_socket_unix_init_connection(connect);
		break;
	default:
		gop_errno = GOP_BAD_PROTOCOL;
		return (GOP_KO);
		break;
	}
	if (gop_errno != GOP_OK)
		return (GOP_KO);

	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <- [%8s] init connection ok\n", connect->my_name, connect->his_name); 

	return (GOP_OK);
}

/**********************************************************************/


static int
gop_socket_accept_connection(struct gop_connect * connect)
{
	/*
	 * met à jour connect.cd
	 */
	struct itimerval timer_value;
	int             local_errno;
	int		use_timer=GOP_FALSE;

	if (connect->cd_init == -1) {
		gop_errno = GOP_BAD_CHANNEL;
		return (GOP_KO);
	}
	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <> [-accept-] gop_socket_accept_connection() sur cd=%d timeout=%d\n",
		      connect->my_name, connect->cd_init, connect->timeout);

	if (connect->timeout > 0) {
		/* mise en place du timer */
		if (connect->mode >= GOP_CONNECTION)
			gop_printf("gop: [%8s] <> [-accept-] gop_socket_accept_connection() SET TIMER: timeout=%d\n",
		      		connect->my_name, connect->timeout);

		use_timer = GOP_TRUE;
		timer_value.it_interval.tv_sec = 0;
		timer_value.it_interval.tv_usec = 0;
		timer_value.it_value.tv_sec = connect->timeout;
		timer_value.it_value.tv_usec = 0;
		/* remise a zero de la valeur de timeout */
		connect->timeout = 0;

		if (setitimer(ITIMER_REAL, &timer_value, (struct itimerval *) NULL) == -1) {
			gop_errno = GOP_ERRNO;
			return (GOP_KO);
		}
	}
	errno = 0;
	connect->cd = accept(connect->cd_init, (struct sockaddr *) NULL, (socklen_t *) NULL);
	local_errno = errno;
	/* arret du timer */
	if (use_timer) {
		timer_value.it_value.tv_sec = 0;
		timer_value.it_value.tv_usec = 0;
		if (setitimer(ITIMER_REAL, &timer_value, (struct itimerval *) NULL) == -1) {
			gop_errno = GOP_ERRNO;
			return (GOP_KO);
		}
	}
	errno = local_errno;

	if (connect->cd == -1 && errno != EINTR) {
		/* test erreur system */
		gop_printf("gop: [%8s] <> [-accept-] erreur system %d (GOP_ERRNO) durant accept()\n",
			   connect->my_name, errno);
		gop_errno = GOP_ERRNO;
		return (GOP_KO);
	}
	/* detection du timeout */
	if (errno == EINTR) {
		gop_printf("gop: [%8s] <> [-accept-] EINTR (GOP_INTERRUPTED_SYSTEM_CALL) durant accept()\n",
			   connect->my_name);
		gop_errno = GOP_INTERRUPTED_SYSTEM_CALL;
		return (GOP_KO);
	}
	if (connect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] <- [%8s] \t accept() OK, socket %d ready\n",
			   connect->my_name, connect->his_name, connect->cd);
#ifdef   BSD
		i = 4;
		if (getsockopt(connect->cd, SOL_SOCKET, SO_SNDBUF, &sndbuf, &i) == -1) {
			gop_printf("gop: [%8s] <- [%8s] warning = %s \n",
				   connect->my_name, connect->his_name, my_strerror(errno));
		}
		gop_printf("gop: [%8s] <- [%8s] socket send buffer    = %d \n",
			   connect->my_name, connect->his_name, sndbuf);
		i = 4;
		if (getsockopt(connect->cd, SOL_SOCKET, SO_RCVBUF, &rcvbuf, &i) == -1) {
			gop_printf("gop: [%8s] <- [%8s] warning = %s \n",
				   connect->my_name, connect->his_name, my_strerror(errno));
		}
		gop_printf("gop: [%8s] <- [%8s] socket receive buffer = %d \n",
			   connect->my_name, connect->his_name, rcvbuf);
#endif				/* BSD */
	}
	return (GOP_OK);

}


static int 
gop_socket_unix_accept_connection (struct gop_connect *connect)
{
	/*
	 * met à jour connect.cd
	 */
	int	len;
	struct	sockaddr	snew;
	struct itimerval timer_value;
	int             local_errno;
	int		use_timer=GOP_FALSE;

	if(connect->cd_init == -1){
		gop_errno = GOP_BAD_CHANNEL;
		return (GOP_KO);
	}
	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <> [-accept-] gop_socket_unix_accept_connection() sur cd=%d\n", 
			connect->my_name, connect->cd_init);

	len = sizeof(struct sockaddr);

	if (connect->timeout > 0) {
		/* mise en place du timer */
		if (connect->mode >= GOP_CONNECTION)
			gop_printf("gop: [%8s] <> [-accept-] gop_socket_unix_accept_connection() SET TIMER: timeout=%d\n",
				connect->my_name, connect->timeout);
		use_timer = GOP_TRUE;
		timer_value.it_interval.tv_sec = 0;
		timer_value.it_interval.tv_usec = 0;
		timer_value.it_value.tv_sec = connect->timeout;
		timer_value.it_value.tv_usec = 0;
		/* remise a zero de la valeur de timeout */
		connect->timeout = 0;

		if (setitimer(ITIMER_REAL, &timer_value, (struct itimerval *) NULL) == -1) {
			gop_errno = GOP_ERRNO;
			return (GOP_KO);
		}
	}

	errno = 0;
	connect->cd = accept(connect->cd_init, &snew, (socklen_t *) &len);
	local_errno = errno;
	/* arret du timer */
	if (use_timer) {
		timer_value.it_value.tv_sec = 0;
		timer_value.it_value.tv_usec = 0;
		if (setitimer(ITIMER_REAL, &timer_value, (struct itimerval *) NULL) == -1) {
			gop_errno = GOP_ERRNO;
			return (GOP_KO);
		}
	}
	errno = local_errno;
	/* detection erreurs systemes */
	if (connect->cd == -1 && errno != EINTR) {
		/* test erreur system */
		gop_printf("gop: [%8s] <> [-accept-] erreur system %d (GOP_ERRNO) durant accept()\n",
			   connect->my_name, errno);
		gop_errno = GOP_ERRNO;
		return (GOP_KO);
	}
	/* detection du timeout */
	if (errno == EINTR) {
		gop_printf("gop: [%8s] <> [-accept-] EINTR (GOP_INTERRUPTED_SYSTEM_CALL) durant accept()\n",
			   connect->my_name);
		gop_errno = GOP_INTERRUPTED_SYSTEM_CALL;
		return (GOP_KO);
	}

	if (connect->mode >= GOP_CONNECTION){
		gop_printf("gop: [%8s] <> [-accept-] \t accept() OK, socket %d ready\n", 
			connect->my_name, connect->cd);
	}

	return (GOP_OK);

}



int 
gop_accept_connection (struct gop_connect *connect)
{
	struct gop_connect rd_work;
	struct gop_connect wr_work;
	struct gop_bench_xdr packet;
	int	maxpacket;
	int	pid;

	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <- [%8s] debut de accept connection\n", 
			connect->my_name, connect->his_name); 

        gop_errno = 0;

	switch (connect->type) {
	case GOP_SOCKET:
		(void) gop_socket_accept_connection(connect);
		break;
	case GOP_SOCKET_UNIX:
		(void) gop_socket_unix_accept_connection(connect);
		break;
	default:
		gop_errno = GOP_BAD_PROTOCOL;
		return (GOP_KO);
		break;
	}
	if (gop_errno != GOP_OK)
		return (GOP_KO);

	/*
	 * echange de header pour se passer le nom symbolique du
	 * correspondant ainsi que la taille maximum des paquets qu'il
	 * accepte et le besoin de XDR
	 */

	(void) memcpy((char *) &rd_work, (char *) connect, 
				sizeof(struct gop_connect));
	(void) memcpy((char *) &wr_work, (char *) connect, 
				sizeof(struct gop_connect));
	gop_set_struct_standart(&wr_work);
	wr_work.need_xdr = GOP_FALSE;

	if(gop_h_read(connect)!=GOP_OK)
		return(GOP_KO);
	if (gop_header_read(&rd_work) != GOP_OK){
		return (GOP_KO);
	}

	if (gop_data_section_read(&rd_work, (char *) &packet, 
			sizeof(struct gop_bench_xdr), GOP_TRUE, 0, 0, 0) <= GOP_OK){
		return (GOP_KO);
	}

	/* besoin de XDR ? */
	connect->need_xdr = gop_test_bench_xdr(&packet)!=0;

	/* taille des packets temporaires */
	maxpacket = rd_work.psize;

	/* nom du destinataire */
	strcpy(connect->his_name, rd_work.header.from);

	strcpy(wr_work.class, GOP_CLASS_INIT);
	wr_work.msize = sizeof(struct gop_bench_xdr);
	wr_work.psize = connect->maxpacket;
	wr_work.datatype = GOP_STRUCT;
	wr_work.header.header_type = GOP_HEADER_STD;

	gop_struct_to_header(&wr_work);
	strcpy(wr_work.header.from, wr_work.my_name);
	gop_fill_bench_xdr(&packet);

	if (gop_header_write(&wr_work) != GOP_OK){
		return (GOP_KO);
	}

	if (gop_data_section_write(&wr_work, (char *) &packet, GOP_TRUE, 0, 0, 0) != GOP_OK){
		return (GOP_KO);
	}

	/* taille des packets definitif */
	connect->maxpacket = GOP_MIN(connect->maxpacket, maxpacket);

	if (connect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] <> [%8s] taille des packets entre >%s< et >%s< = %d\n", 
			connect->my_name, connect->his_name, connect->my_name, connect->his_name, connect->maxpacket);
		gop_printf("gop: [%8s] <> [%8s] convertion XDR entre >%s< et >%s< = %d\n", 
			connect->my_name, connect->his_name, connect->my_name, connect->his_name, connect->need_xdr);
	}
	/*
	 * permet la reception de OOB sous forme de SIGURG
	 */
	if (connect->type == GOP_SOCKET) {
		if (fcntl(connect->cd, F_SETOWN, getpid()) < 0) {
			gop_errno = GOP_ERRNO;
			return (GOP_KO);
		}
	}

	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <- [%8s] accept connection ok\n", connect->my_name, connect->his_name); 

	/*
	 * Pour les communication type GOP_SOCKET_UNIX, on s'echange les
	 * pid, le pid du serveur est utilise pour propager le sigurg
         * vers le serveur
	 */
	if(connect->type == GOP_SOCKET_UNIX){
		if (gop_read(connect, (char *) &pid, 4) < 0){
			return (GOP_KO);
		}
		connect->pid = pid;
		pid = getpid();
		gop_set_class(connect, GOP_CLASS_DATA);
		if (gop_write(connect, (char *) &pid, 4, 4, GOP_CHAR) != GOP_OK){
			return (GOP_KO);
		}
	}


	return (GOP_OK);
}


/**********************************************************************/




static int 
gop_socket_connection (struct gop_connect *wconnect)
{
	/*
	 * met à jour wconnect.cd
	 */

	struct hostent *hp;
	struct sockaddr_in sinet;

	if (wconnect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] -> [%8s] gop_socket_connection() host=>%s< port=%d\n", 
			wconnect->my_name, wconnect->his_name, wconnect->name, wconnect->port);
	}
	if ((hp = gethostbyname(wconnect->name)) == NULL) {
		gop_printf("gop: [%8s] -> [%8s] gop_socket_connection(), gethostbyname() unknown host: >%s< \n", 
			wconnect->my_name, wconnect->his_name, wconnect->name);
		gop_errno = GOP_BAD_HOST_NAME;
		return (GOP_KO);
	}
	/*
	 * Initialize the socket structure
	 */
	(void) memset((char *) &sinet, (char) 0, sizeof(sinet));
	sinet.sin_family = AF_INET;
#pragma warning(disable:2259) //non-pointer conversion from "int" to "unsigned short" may lose significant bits
#ifdef linux
	sinet.sin_port = htons(wconnect->port);
#else
	sinet.sin_port = htonl(wconnect->port);
#endif
	sinet.sin_addr.s_addr = ((struct in_addr *) (hp->h_addr))->s_addr;

	/*
	 * Get an internet domain socket
	 */
	if ((wconnect->cd = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
		gop_errno = GOP_ERRNO;
		return (GOP_KO);
	}
	if (wconnect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] -> [%8s] \t socket()   cd=%d OK\n", 
			wconnect->my_name, wconnect->his_name,  wconnect->cd);
	}
	/*
	 * Initiate connection on the socket
	 */

	if (connect(wconnect->cd, (struct sockaddr *) &sinet, sizeof(sinet)) == -1) {
		gop_errno = GOP_ERRNO;
		return (GOP_KO);
	}

	if (wconnect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] -> [%8s] \t connect()  cd=%d OK\n", 
			wconnect->my_name, wconnect->his_name,  wconnect->cd);
	}
#ifdef   BSD
	/*
	 * Set the process ID that will subsequently receive SIGIO or SIGURG
	 * signal to us.
	 */
	if (fcntl(wconnect->cd, F_SETOWN, getpid()) == EOF) {
		gop_errno = GOP_ERRNO;
		return (GOP_KO);
	}
	/*
	 * Allow receipt of asynchronous I/O signals.
	 */
	if (fcntl(wconnect->cd, F_SETFL, FASYNC) == EOF) {
		gop_errno = GOP_ERRNO;
		return (GOP_KO);
	}
#endif /* BSD */

	if (wconnect->mode >= GOP_CONNECTION) {

		gop_printf("gop: [%8s] -> [%8s] socket %d ready\n", 
			wconnect->my_name, wconnect->his_name,  wconnect->cd);

#ifdef   BSD
		i = 4;
		if (getsockopt(wconnect->cd, SOL_SOCKET, SO_SNDBUF, &sndbuf, &i) == -1) {
			gop_printf("gop: [%8s] -> [%8s] warning = %s \n", 
				wconnect->my_name, wconnect->his_name,  my_strerror(errno));
		}
		gop_printf("gop: [%8s] -> [%8s] socket send buffer    = %d \n", 
			wconnect->my_name, wconnect->his_name,  sndbuf);
		i = 4;
		if (getsockopt(wconnect->cd, SOL_SOCKET, SO_RCVBUF, &rcvbuf, &i) == -1) {
			gop_printf("gop: [%8s] -> [%8s] warning = %s \n", 
				wconnect->my_name, wconnect->his_name,  my_strerror(errno));
		}
		gop_printf("gop: [%8s] -> [%8s] socket receive buffer = %d \n", 
			wconnect->my_name, wconnect->his_name,  rcvbuf);
#endif /* BSD */
	}
	return (GOP_OK);
}



static int 
gop_socket_unix_connection (struct gop_connect *wconnect)
{
	/*
	 * met à jour wconnect.cd
	 */

	struct	sockaddr_un sunix;

	sprintf(sunix.sun_path,"%s/.socket.%s",getenv("HOME"),wconnect->name);
	sunix.sun_family = AF_UNIX;

        if(wconnect->cd != 0) close(wconnect->cd);

	if((wconnect->cd = socket(AF_UNIX, SOCK_STREAM, 0))== EOF) {
		gop_errno = GOP_ERRNO;
		return (GOP_KO);
	}
	if (wconnect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] -> [%8s] \t socket()   cd=%d OK\n", 
			wconnect->my_name, wconnect->his_name,  wconnect->cd);
	}

	if(connect(wconnect->cd, (struct sockaddr *)&sunix, 
		strlen(sunix.sun_path) + sizeof(sunix.sun_family)) == EOF) {
		gop_errno = GOP_ERRNO;
		return (GOP_KO);
	}

	if (wconnect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] -> [%8s] \t connect()  cd=%d OK\n", 
			wconnect->my_name, wconnect->his_name,  wconnect->cd);
	}

	return (GOP_OK);
}



int 
gop_connection (struct gop_connect *connect)
{

	struct gop_connect rd_work;
	struct gop_connect wr_work;
	struct gop_bench_xdr packet;
	int	pid;

	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] -> [%8s] debut de connection\n", 
			connect->my_name, connect->his_name); 

	connect->side = GOP_CLIENT_SIDE;

	connect->cd = -1;
	connect->cd_init = -1;
        gop_errno = 0;

	switch (connect->type) {
	case GOP_SOCKET:
		(void) gop_socket_connection(connect);
		break;
	case GOP_SOCKET_UNIX:
		(void) gop_socket_unix_connection(connect);
		break;
	default:
		gop_errno = GOP_BAD_PROTOCOL;
		return (GOP_KO);
		break;
	}

	if (gop_errno != GOP_OK){
		gop_close_connection(connect);
		return (GOP_KO);
	}


	/*
	 * echange de header pour se passer le nom symbolique du
	 * correspondant ainsi que la taille maximum des paquets qu'il
	 * accepte et le besoin de XDR
	 */
	(void) memcpy((char *) &rd_work, (char *) connect, sizeof(struct gop_connect));
	(void) memcpy((char *) &wr_work, (char *) connect, sizeof(struct gop_connect));
	gop_set_struct_standart(&wr_work);
	wr_work.need_xdr = GOP_FALSE;

	strcpy(wr_work.class, GOP_CLASS_INIT);
	wr_work.msize = sizeof(struct gop_bench_xdr);
	wr_work.psize = connect->maxpacket;
	wr_work.datatype = GOP_STRUCT;
	wr_work.header.header_type = GOP_HEADER_STD;

	gop_struct_to_header(&wr_work);
	strcpy(wr_work.header.from, wr_work.my_name);
	gop_fill_bench_xdr(&packet);

	if (gop_header_write(&wr_work) != GOP_OK){
		return (GOP_KO);
	}
	if (gop_data_section_write(&wr_work, (char *) &packet, GOP_TRUE, 0, 0, 0) != GOP_OK){
		return (GOP_KO);
	}

	if(gop_h_read(connect)!=GOP_OK)
		return(GOP_KO);
	if (gop_header_read(&rd_work) != GOP_OK){
		return (GOP_KO);
	}
	if (gop_data_section_read(&rd_work, (char *) &packet, 
			sizeof(struct gop_bench_xdr), GOP_TRUE, 0, 0, 0) <= GOP_OK){
		return (GOP_KO);
	}

	/* besoin de XDR ? */
	connect->need_xdr = gop_test_bench_xdr(&packet)!=0;

	/* taille des packets */
	connect->maxpacket = GOP_MIN(connect->maxpacket, rd_work.psize);

	/* nom du destinataire */
	strcpy(connect->his_name, rd_work.header.from);



	if (connect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] <> [%8s] taille des packets = %d\n", 
			connect->my_name, connect->his_name, connect->maxpacket);
		gop_printf("gop: [%8s] <> [%8s] convertion XDR = %d\n", 
			connect->my_name, connect->his_name, connect->need_xdr);
	}

	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] -> [%8s] connection ok\n", connect->my_name, connect->his_name); 

	/*
	 * Pour les communication type GOP_SOCKET_UNIX, on s'echange les
	 * pid, le pid du serveur est utilise pour propager le sigurg
         * vers le serveur
	 */
	if(connect->type == GOP_SOCKET_UNIX){
		pid = getpid();
		gop_set_class(connect, GOP_CLASS_DATA);
		if (gop_write(connect, (char *) &pid, 4, 4, GOP_CHAR) != GOP_OK){
			return (GOP_KO);
		}
		if (gop_read(connect, (char *) &pid, 4) < 0){
			return (GOP_KO);
		}
		connect->pid = pid;
	}

	return (GOP_OK);
}


/**********************************************************************/



static int 
gop_socket_close_connection (struct gop_connect *connect)
{
	int		status;
	
	
	gop_printf("gop: [%8s] <> [-CLOSE--] gop_socket_close_connection() cd = %d cd_init = %d\n", 
				connect->my_name, connect->cd, connect->cd_init);

	if (connect->cd != -1) {
		if (connect->mode >= GOP_CONNECTION) {
			gop_printf("gop: [%8s] <> [-CLOSE--] gop_socket_close_connection() cd = %d\n", 
				connect->my_name, connect->cd);
		}
		status = shutdown(connect->cd, 2);
		if (connect->mode >= GOP_CONNECTION)
			gop_printf("gop: [%8s] <> [-CLOSE--] shutdown(%d,2) status = %d\n", 
				connect->my_name, connect->cd, status);
		status = close(connect->cd);
		if (connect->mode >= GOP_CONNECTION)
			gop_printf("gop: [%8s] <> [-CLOSE--] close(%d) status = %d\n", 
			connect->my_name, connect->cd, status);
		connect->cd = -1;

	}
	
	if (connect->cd_init != -1) {
		if (connect->mode >= GOP_CONNECTION) {
			gop_printf("gop: [%8s] <> [-CLOSE--] gop_socket_close_connection() cd_init = %d\n", 
				connect->my_name, connect->cd_init);
		}
		status = shutdown(connect->cd_init, 2);
		if (connect->mode >= GOP_CONNECTION)
			gop_printf("gop: [%8s] <> [-CLOSE--] shutdown(%d,2) status = %d\n", 
				connect->my_name, connect->cd_init, status);
		status = close(connect->cd_init);
		if (connect->mode >= GOP_CONNECTION)
			gop_printf("gop: [%8s] <> [-CLOSE--] close(%d) status = %d\n", 
				connect->my_name, connect->cd_init, status);
		connect->cd_init = -1;
	}

	return (GOP_OK);
}


static int 
gop_socket_unix_close_connection (struct gop_connect *connect)
{

	char            name[256];
	int		status;

	if (connect->cd != -1) {
		if (connect->mode >= GOP_CONNECTION) {
			gop_printf("gop: [%8s] <> [-CLOSE--] gop_socket_unix_close_connection() cd=%d\n", 
				connect->my_name, connect->cd);
		}
		status = shutdown(connect->cd, 2);
		if (connect->mode >= GOP_CONNECTION)
			gop_printf("gop: [%8s] <> [-CLOSE--] shutdown(%d,2) status = %d\n", 
				connect->my_name, connect->cd, status);
		status = close(connect->cd);
		if (connect->mode >= GOP_CONNECTION)
			gop_printf("gop: [%8s] <> [-CLOSE--] close(%d) status = %d\n", 
				connect->my_name, connect->cd, status);
		connect->cd = -1;

	}

	if (connect->cd_init != -1) {
		if (connect->mode >= GOP_CONNECTION) {
			gop_printf("gop: [%8s] <> [-CLOSE--] gop_socket_unix_close_connection() cd_init = %d\n", 
				connect->my_name, connect->cd_init);
		}
		status = shutdown(connect->cd_init, 2);
		if (connect->mode >= GOP_CONNECTION)
			gop_printf("gop: [%8s] <> [-CLOSE--] shutdown(%d,2) status = %d\n", 
				connect->my_name, connect->cd_init, status);
		status = close(connect->cd_init);
		if (connect->mode >= GOP_CONNECTION)
			gop_printf("gop: [%8s] <> [-CLOSE--] close(%d) status = %d\n", 
				connect->my_name, connect->cd_init, status);
		sprintf(name, "%s/.socket.%s", getenv("HOME"), connect->name);
		unlink(name);
		connect->cd_init = -1;
	}

	return (GOP_OK);
}


int 
gop_close_connection (struct gop_connect *connect)
{

	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <> [%8s] debut de close_connection, gop_errno=%d (en entree)\n", 
			connect->my_name, connect->his_name,  gop_errno);

	switch (connect->type) {
	case GOP_SOCKET:
		(void) gop_socket_close_connection(connect);
		break;
	case GOP_SOCKET_UNIX:
		(void) gop_socket_unix_close_connection(connect);
		break;
	default:
		gop_errno = GOP_BAD_PROTOCOL;
		return (GOP_KO);
		break;
	}

	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <> [%8s] fin close_connection, gop_errno=%d (en sortie)\n", 
			connect->my_name, connect->his_name,  gop_errno);

	return (GOP_OK);
}


/**********************************************************************/



static int 
gop_socket_close_init_connection (struct gop_connect *connect)
{
	int		status;

	if (connect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] <> [-CLOSE--] gop_socket_close_init_connection() cd_init = %d\n", 
			connect->my_name, connect->cd_init);
	}

	if(connect->cd_init == -1)
		return (GOP_OK);

	status = shutdown(connect->cd_init, 2);
	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <> [-CLOSE--] shutdown(%d,2) status = %d\n", 
			connect->my_name, connect->cd_init, status);
	status = close(connect->cd_init);
	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <> [-CLOSE--] close(%d) status = %d\n", 
			connect->my_name, connect->cd_init, status);

	connect->cd_init = -1;

	return (GOP_OK);
}


static int 
gop_socket_unix_close_init_connection (struct gop_connect *connect)
{

	char	socket_name[256];
	int	status;


	if (connect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] <> [-CLOSE--] gop_socket_unix_close_init_connection() cd_init = %d\n", 
			connect->my_name, connect->cd_init);
	}

	if(connect->cd_init == -1)
		return (GOP_OK);

	status = shutdown(connect->cd_init, 2);
	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <> [-CLOSE--] shutdown(%d,2) status = %d\n", 
			connect->my_name, connect->cd_init, status);
	status = close(connect->cd_init);
	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <> [-CLOSE--] close(%d) status = %d\n", 
			connect->my_name, connect->cd_init, status);

	sprintf(socket_name,"%s/.socket.%s",getenv("HOME"),connect->name);
	unlink(socket_name);
	
	connect->cd_init = -1;

	return (GOP_OK);
}


int 
gop_close_init_connection (struct gop_connect *connect)
{

	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <> [%8s] debut de gop_close_init_connection, gop_errno=%d (en entree)\n", 
			connect->my_name, connect->his_name,  gop_errno);

	switch (connect->type) {
	case GOP_SOCKET:
		(void) gop_socket_close_init_connection(connect);
		break;
	case GOP_SOCKET_UNIX:
		(void) gop_socket_unix_close_init_connection(connect);
		break;
	default:
		gop_errno = GOP_BAD_PROTOCOL;
		return (GOP_KO);
		break;
	}

	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <> [%8s] fin de gop_close_init_connection, gop_errno=%d (en entree)\n", 
			connect->my_name, connect->his_name,  gop_errno);
	return (GOP_OK);
}

/**********************************************************************/



static int 
gop_socket_close_active_connection (struct gop_connect *connect)
{
	int		status;


	if (connect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] <> [-CLOSE--] gop_socket_close_active_connection() cd = %d\n", 
			connect->my_name, connect->cd);
	}
	if(connect->cd == -1)
		return (GOP_OK);

	status = shutdown(connect->cd, 2);
	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <> [-CLOSE--] shutdown(%d,2) status = %d\n", 
			connect->my_name, connect->cd, status);
	status = close(connect->cd);
	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <> [-CLOSE--] close(%d) status = %d\n", 
			connect->my_name, connect->cd, status);

	connect->cd = -1;

	return (GOP_OK);
}


static int 
gop_socket_unix_close_active_connection (struct gop_connect *connect)
{

	int		status;

	if (connect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] <> [-CLOSE--] gop_socket_unix_close_active_connection() cd = %d\n", 
			connect->my_name, connect->cd);
	}

	if(connect->cd == -1)
		return (GOP_OK);

	status = shutdown(connect->cd, 2);
	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <> [-CLOSE--] shutdown(%d,2) status = %d\n", 
			connect->my_name, connect->cd, status);
	status = close(connect->cd);
	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <> [-CLOSE--] close(%d) status = %d\n", 
			connect->my_name, connect->cd, status);

	connect->cd = -1;

	return (GOP_OK);
}


int 
gop_close_active_connection (struct gop_connect *connect)
{

	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <> [%8s] debut de gop_close_active_connection, gop_errno=%d (en entree)\n", 
			connect->my_name, connect->his_name,  gop_errno);

	switch (connect->type) {
	case GOP_SOCKET:
		(void) gop_socket_close_active_connection(connect);
		break;
	case GOP_SOCKET_UNIX:
		(void) gop_socket_unix_close_active_connection(connect);
		break;
	default:
		gop_errno = GOP_BAD_PROTOCOL;
		return (GOP_KO);
		break;
	}

	if (connect->mode >= GOP_CONNECTION)
		gop_printf("gop: [%8s] <> [%8s] fin de gop_close_active_connection, gop_errno=%d (en entree)\n", 
			connect->my_name, connect->his_name,  gop_errno);
	return (GOP_OK);
}


/**********************************************************************/


static int
gop_socket_read(struct gop_connect * connect, char *buf, int size)
{
	int             len, ilen;
	struct itimerval timer_value;
	int             local_errno;
	/*
	 * Pour gerer les timeouts, on s'envoie un SIGALRM dans le but
	 * d'interrompre le read().
	 * 
	 * Sous BSD, lorsque survient un interrupt lors du read(), le system
	 * relance automatiquement le read. Pour empecher ceci, la fonction
	 * sigvec (avec flags=SV_INTERRUPT) permet de reelement interompre le
	 * read().
	 * 
	 * Sous POSIX, le read() est automatiquement interrompu, ce qui ne
	 * necessite aucun traitement.
	 * 
	 * Le programme utilisant les timeouts doivent avoir un handler de
	 * SIGALRM qui ne fait rien. fait par gop_write() et gop_read().
	 */

	/*
	 * memo de la structure de connection courante
	 
	 pas une bonne idée car l'utilisation simultanee du logbook
	 embrouille tout des qu'on l'utilise pour envoyer des messages
	 dans gop 
	 */
	/**
	gop_connect_client = connect;
	connect->opcrt = GOP_READ;
	**/


#ifdef    BSD
	struct sigvec   vec, ovec;
#endif	/* BSD */

	errno = 0;
	ilen = 0;

	/* pour permettre une interruption dans le read() */

#ifdef   BSD
	if (connect->timeout > 0) {
		if (sigvec(SIGALRM, (struct sigvec *) NULL, &ovec) == -1) {
			gop_errno = GOP_ERRNO;
			return (GOP_KO);
		}
		vec.sv_handler = ovec.sv_handler;	/* setting selon valeur
							 * actuelle */
		vec.sv_mask = ovec.sv_mask;	/* setting selon valeur
						 * actuelle */
		vec.sv_flags = SV_INTERRUPT;
		if (sigvec(SIGALRM, &vec, (struct sigvec *) NULL) == -1) {
			gop_errno = GOP_ERRNO;
			return (GOP_KO);
		}
	}
#endif	/* BSD */

	/* lecture de size bytes */

	if (connect->mode >= GOP_IO)
		gop_printf("gop: [%8s] <- [%8s] \t\t\t read socket debut: reception sur cd=%d de %d bytes\n", 
			connect->my_name, connect->his_name, connect->cd, size - ilen);

	while (ilen < size) {

		if (connect->timeout > 0) {
			/* mise en place du timer */
			if (connect->mode >= GOP_CONNECTION)
				gop_printf("gop: [%8s] <- [%8s] gop_socket_read() SET TIMER: timeout=%d\n",
		      			connect->my_name, connect->his_name, connect->timeout);
			timer_value.it_interval.tv_sec = 0;
			timer_value.it_interval.tv_usec = 0;
			timer_value.it_value.tv_sec = connect->timeout;
			timer_value.it_value.tv_usec = 0;
			if (setitimer(ITIMER_REAL, &timer_value, (struct itimerval *) NULL) == -1) {
				gop_errno = GOP_ERRNO;
				return (GOP_KO);
			}
		}
		/* lecture */
		//counter_recv++;
		//gop_printf("gop: [%8s] <- [%8s] %4.4d ------------------------------- gop_socket_read: start recv       ---------------------\n",
		//	connect->my_name, connect->his_name,  counter_recv);
		len = recv(connect->cd, buf + ilen, size - ilen, 0);
		//counter_recv++;
		//gop_printf("gop: [%8s] <- [%8s] %4.4d ------------------------------- gop_socket_read: revc de %d bytes ---------first=%c-----------\n",
		//	connect->my_name, connect->his_name,  counter_recv,len,*(buf + ilen));
		/* arret du timer */
		local_errno = errno;
		if (connect->timeout > 0) {
			timer_value.it_value.tv_sec = 0;
			timer_value.it_value.tv_usec = 0;
			if (setitimer(ITIMER_REAL, &timer_value, (struct itimerval *) NULL) == -1) {
				gop_errno = GOP_ERRNO;
				return (GOP_KO);
			}
		}
		errno = local_errno;
		/* test deconnection */
		if (len == -1 && errno == ECONNRESET) {
			gop_printf("gop: [%8s] <- [%8s] ECONNRESET (GOP_BROKEN_PIPE) durant gop_socket_read()\n",
				connect->my_name, connect->his_name); 
			gop_errno = GOP_BROKEN_PIPE;
			return (GOP_KO);
		} else if (len == -1 && errno != EINTR) { 
		/* test erreur system */
			gop_printf("gop: [%8s] <- [%8s] erreur system %d (GOP_ERRNO) durant gop_socket_read()\n",
				connect->my_name, connect->his_name, errno); 
			gop_errno = GOP_ERRNO;
			return (GOP_KO);
		}
		/* detection du timeout */
		if (errno == EINTR) {
			gop_printf("gop: [%8s] <- [%8s] EINTR (GOP_INTERRUPTED_SYSTEM_CALL) durant gop_socket_read()\n",
				connect->my_name, connect->his_name); 
			gop_errno = GOP_INTERRUPTED_SYSTEM_CALL;
			return (GOP_KO);
		}
		/* detection de la deconnection */
		if (len == 0) {
			if (connect->mode >= GOP_CONNECTION)
				gop_printf("gop: [%8s] <- [%8s] Detection deconnection (GOP_DISCONNECT) sur cd=%d durant gop_socket_read()\n",
					connect->my_name, connect->his_name, connect->cd); 
			gop_errno = GOP_DISCONNECT;
			return (GOP_KO);
		}
		ilen = ilen + len;
		if (connect->mode >= GOP_IO)
			gop_printf("gop: [%8s] <- [%8s] \t\t\t read socket effectif de %d bytes sur cd=%d\n", 
				connect->my_name, connect->his_name,  len, connect->cd);
	}
	if (connect->mode >= GOP_IO)
		gop_printf("gop: [%8s] <- [%8s] \t\t\t read socket fin: %d bytes ont ete recu sur cd=%d\n", 
			connect->my_name, connect->his_name,  ilen, connect->cd);

#ifdef   BSD
	if (connect->timeout > 0) {
		if (sigvec(SIGALRM, &ovec, (struct sigvec *) NULL) == -1) {
			gop_errno = GOP_ERRNO;
			return (GOP_KO);
		}
	}
#endif	/* BSD */
	return (GOP_OK);
}



static int 
gop_socket_write (struct gop_connect *connect, char *buf, int size)
{
	int             ilen = 0;
	int             len;

	/*
	 * memo de la structure de connection courante
	 
	 pas une bonne idée car l'utilisation simultanee du logbook
	 embrouille tout des qu'on l'utilise pour envoyer des messages
	 dans gop 
	 */
	/**
	gop_connect_client = connect;
	connect->opcrt = GOP_WRITE;
	**/


	errno = 0;
	if (connect->mode >= GOP_IO)
		gop_printf("gop: [%8s] -> [%8s] \t\t\t write socket debut: envoi sur cd=%d de %d bytes\n", 
			connect->my_name, connect->his_name, connect->cd, size);

	gop_broken_pipe = GOP_FALSE;

	while (ilen < size) {

		if ((len = send(connect->cd, buf+ilen, size-ilen, 0)) < 0) {
			if (gop_broken_pipe) {
				gop_printf("gop: [%8s] -> [%8s] GOP_BROKEN_PIPE sur cd=%d durant gop_socket_write()\n",
					connect->my_name, connect->his_name, connect->cd); 
				gop_errno = GOP_BROKEN_PIPE;
			} else {
				gop_printf("gop: [%8s] -> [%8s] erreur system %d (GOP_ERRNO) durant gop_socket_write()\n",
					connect->my_name, connect->his_name, errno); 
				gop_errno = GOP_ERRNO;
			}
			return (GOP_KO);
		}
		if (connect->mode >= GOP_IO)
			gop_printf("gop: [%8s] -> [%8s] \t\t\t write socket effectif de %d bytes sur cd=%d\n", 
				connect->my_name, connect->his_name,  len, connect->cd);
		ilen = ilen + len;
	}
	if (connect->mode >= GOP_IO)
		gop_printf("gop: [%8s] -> [%8s] \t\t\t write socket fin: %d bytes ont ete envoye sur cd=%d\n", 
			connect->my_name, connect->his_name,  size, connect->cd);

	return (GOP_OK);
}

/**********************************************************************/



static int 
gop_io_read (struct gop_connect *connect, char *buf, int size)

{
        gop_errno = 0;
	errno     = 0;

	switch (connect->type) {
	case GOP_SOCKET:
	case GOP_SOCKET_UNIX:
		(void) gop_socket_read(connect, buf, size);
		break;
	default:
		gop_errno = GOP_BAD_PROTOCOL;
		return (GOP_KO);
		break;
	}

	if (gop_errno != GOP_OK)
		return (GOP_KO);

	return(GOP_OK);
}


static int 
gop_io_write (struct gop_connect *connect, char *buf, int size)

{
        gop_errno = 0;
	errno     = 0;

	switch (connect->type) {
	case GOP_SOCKET:
	case GOP_SOCKET_UNIX:
		(void) gop_socket_write(connect, buf, size);
		break;
	default:
		gop_errno = GOP_BAD_PROTOCOL;
		return (GOP_KO);
		break;
	}

	if (gop_errno != GOP_OK)
		return (GOP_KO);

	return(GOP_OK);
}

/**********************************************************************/


static int 
gop_first_byte_read (struct gop_connect *connect, char *value)
{

	/*
	 * lecture du premier byte d'un message
	 */

	if (connect->mode >= GOP_PACKET)
		gop_printf("gop: [%8s] <- [%8s] \t\t attente premier byte d'un packet sur cd=%d\n", 
			connect->my_name, connect->his_name,  connect->cd);

	if(gop_io_read(connect, value, 1) != GOP_OK)
		return (GOP_KO);

	if (connect->mode >= GOP_PACKET)
		gop_printf("gop: [%8s] <- [%8s] \t\t premier byte d'un packet = %c sur cd=%d\n", 
			connect->my_name, connect->his_name,  *value, connect->cd);
	return (GOP_OK);
}


static int 
gop_first_byte_write (struct gop_connect *connect, char *value)
{

	/*
	 * ecriture du premier byte d'un packet
	 */

	if (connect->mode >= GOP_PACKET)
		gop_printf("gop: [%8s] -> [%8s] \t\t ecriture premier byte d'un packet '%c' sur cd=%d\n", 
			connect->my_name, connect->his_name,  *value, connect->cd);

	if(gop_io_write(connect, value, 1) != GOP_OK)
		return (GOP_KO);

	return (GOP_OK);
}



static int 
gop_acknow_write (struct gop_connect *connect)
{
	char            ackno[4];

	if (connect->mode >= GOP_PACKET)
		gop_printf("gop: [%8s] -> [%8s] \t\t write acknowledge sur cd=%d\n", 
			connect->my_name, connect->his_name,  connect->cd);

	sprintf(ackno, "A%2d", gop_errno);

	if(gop_io_write(connect, ackno, 4) != GOP_OK)
		return (GOP_KO);

	return (GOP_OK);
}


static int
gop_acknow_read(struct gop_connect * connect)
{
	char            ackno[4];
	char            lettre;


	if (connect->mode >= GOP_PACKET)
		gop_printf("gop: [%8s] <- [%8s] \t\t read acknowledge sur cd=%d\n",
			   connect->my_name, connect->his_name, connect->cd);

	do {
		if (gop_first_byte_read(connect, &lettre) != GOP_OK)
			return (GOP_KO);
		if (lettre == GOP_HEADER_STD) {
			if (connect->mode >= GOP_HEADER)
				gop_printf("gop: [%8s] -> [%8s] \t **** DETECTION DE COLISISION*** \n",
				       connect->my_name, connect->his_name);

			/* on memorise le header et la data section s'il y a une collision */
			memcpy((char *)&memo_connect, (char *)connect, sizeof(struct gop_connect));

			if (gop_header_read_without_acknow(&memo_connect) != GOP_OK)
				return (GOP_KO);
			strcpy(memo_connect.to, memo_connect.header.to);
			strcpy(memo_connect.from, memo_connect.header.from);
			if (gop_data_section_read(&memo_connect, memo_data_section, sizeof(memo_data_section), GOP_TRUE, 0, 0, 0) < GOP_OK)
				return (GOP_KO);
			memo_action = GOP_TRUE;
			if (connect->mode >= GOP_HEADER)
				gop_printf("gop: [%8s] -> [%8s] \t **** FIN DE DETECTION DE COLISISION*** Le message est differe\n",
				       connect->my_name, connect->his_name);
		}
	}
	while (lettre != GOP_HEADER_ACK);


	if (gop_io_read(connect, ackno, 3) != GOP_OK)
		return (GOP_KO);

	ackno[3] = (char) 0;

	remote_status = atoi(ackno);

	return (GOP_OK);
}



/**********************************************************************/

int 
gop_echo_header (char *my_name, char *his_name, struct gop_header *header)
{
	gop_printf("gop: [%8s] <> [%8s] \t V CLAS DATE__________ FROM____ TO______ H D M MSIZE_____ PSIZE_____ C STAT X D\n",
		my_name, his_name); 
	gop_printf("gop: [%8s] <> [%8s] \t %1s %4s %14s %8s %8s %1s %1s %1s %10s %10s %1s %4s %1s %1s %s", 
		my_name, his_name,
		header->version, header->class, header->date,
		header->from, header->to, header->hsync,
		header->dsync, header->mode, header->msize,
		header->psize, header->cont, header->stat, header->xdr,
                header->datatype, header->end);
	return(0);
}

/**********************************************************************/



int 
gop_header_write (struct gop_connect *connect)
{

	if (connect->mode >= GOP_MESSAGE ) {
		gop_printf("gop: [%8s] -> [%8s] \t write_header: sur cd=%d\n", 
			connect->my_name, connect->his_name,  connect->cd);
	}
	if (connect->mode >= GOP_HEADER ) {
		gop_echo_header(connect->my_name, connect->his_name, &(connect->header));
	}

	if(gop_io_write(connect, (char *) &(connect->header),
				sizeof(struct gop_header)) != GOP_OK)
		return (GOP_KO);

	/*
	 * si ce n'est pas une erreur system, on doit lire l'acknow si
	 * necessaire
	 */
	if (errno == 0 && connect->hsync) {
		if (gop_acknow_read(connect) != GOP_OK)
			return (GOP_KO);
		if (remote_status != GOP_OK){
			gop_errno = GOP_REMOTE_PROBLEM;
			return (GOP_KO);
		}

	}
	return (GOP_OK);
}



int 
gop_h_read (struct gop_connect *connect)
{
	if (connect->mode >= GOP_PACKET)
		gop_printf("gop: [%8s] <- [%8s] \t\t read '%c' sur cd=%d\n", 
			connect->my_name, connect->his_name, GOP_HEADER_STD , connect->cd);

	/* 
	lit sur le cannal jusqu'a la reception d'un 'H' 
	*/
	do {
		if (gop_first_byte_read(connect, &connect->header.header_type) != GOP_OK)
			return (GOP_KO);
	}
	while (connect->header.header_type != GOP_HEADER_STD && 
		connect->header.header_type != GOP_HEADER_END);

	/*
	 * detection de fin de message
	 */
	if (connect->header.header_type == GOP_HEADER_END) {
		if (connect->mode >= 0)
			gop_printf("gop: [%8s] <- [%8s]  DETECTION BLOC FIN MESSAGE ****** sur cd=%d\n", 
				connect->my_name, connect->his_name,  connect->cd);
		gop_errno = GOP_END_OF_MESSAGE;
		connect->header.header_type = GOP_HEADER_STD;
		return (GOP_KO);
	}

	return(GOP_OK);
}



static int 
gop_header_read_without_acknow (struct gop_connect *connect)
{

	if (connect->mode >= GOP_MESSAGE) {
		gop_printf("gop: [%8s] <- [%8s] \t read header: sur cd=%d\n", 
			connect->my_name, connect->his_name,  connect->cd);
	}

	/*
	 * lecture du header (EDM)
	 */
	if(gop_io_read(connect, connect->header.version,
				sizeof(struct gop_header)-1) != GOP_OK)
		return (GOP_KO);

	if (connect->mode >= GOP_HEADER) {
		gop_echo_header(connect->my_name, connect->his_name, &(connect->header));
	}
	/*
	 * test de la compatibilite de version
	 */
	if (strcmp(connect->header.version, GOP_VERSION_CRT) != 0) {
		gop_errno = GOP_INVALID_VERSION;
		return (GOP_KO);
	}
	/*
	 * transfert du header
	 */
	gop_header_to_struct(connect, &(connect->header));

	if (gop_errno != GOP_OK)
		return (GOP_KO);

	return (GOP_OK);
}


int 
gop_header_read (struct gop_connect *connect)
{

	if(gop_header_read_without_acknow(connect)!= GOP_OK)
		return (GOP_KO);

	/*
	 * acknowledge du header
	 */

	if (connect->hsync)
		if (gop_acknow_write(connect) != GOP_OK)
			return (GOP_KO);

	if (gop_errno != GOP_OK)
		return (GOP_KO);

	return (GOP_OK);
}



int 
gop_select_destination (struct gop_connect *from_connect, struct gop_list *list, struct gop_connect **to_connect)
{

	int             i;
	int             local_gop_errno;

	if (gop_h_read(from_connect) != GOP_OK){
		if(gop_errno == GOP_END_OF_MESSAGE)
			gop_errno = GOP_OK;
		else
			return (GOP_KO);
	}

	if (gop_header_read_without_acknow(from_connect) != GOP_OK)
		return (GOP_KO);

	if (from_connect->mode >= GOP_HEADER) {
		gop_printf("gop: [%8s] <> [--------] \t select possible destination from >%s<\n",
			   from_connect->my_name, list->gop[0]->my_name);

		for (i = 0; i < list->nb; i++) {
			gop_printf("gop: [%8s] <> [--------] \t\t %d) to: >%s<  cd=%d\n", 
				from_connect->my_name, i, 
				list->gop[i]->his_name, list->gop[i]->cd);
		}
	}

	/*
	 * on pose "to"=NULL par defaut et on cherche apres si on est le
	 * destinataire
	 */

	*to_connect = NULL;

	/*
	 * si list est NULL c'est qu'on est le destinataire dans le cas
	 * contraire, recherche du destinataire
	 */

	if (list != NULL) {

		if (strcmp(list->gop[0]->my_name, from_connect->header.to) != 0) {

			/*
			 * on est pas le destinataire
			 */

			if (from_connect->mode >= GOP_HEADER)
				gop_printf("gop: [%8s] <> [--------] \t destination research:\n", 
					from_connect->my_name); 

			for (i = 0; i < list->nb; i++) {

				if (from_connect->mode >= GOP_HEADER)
					gop_printf("gop: [%8s] <> [--------] \t\t >%s< == >%s< equal ??\n", 
						from_connect->my_name,   
						list->gop[i]->his_name, from_connect->header.to);


				if (strcmp(list->gop[i]->his_name, from_connect->header.to) == 0) {

					if (from_connect->mode >= GOP_HEADER)
						gop_printf("gop: [%8s] <> [--------] \t\t ok, destination is >%s< cd=%d\n", 
							from_connect->my_name,  
							list->gop[i]->his_name, list->gop[i]->cd);

					/*
					 * on a un destinataire
					 */

					*to_connect = list->gop[i];

					/*
					 * on sauvegarde egalement le header
					 * original
					 */
					(void) memcpy((char *) &(*to_connect)->header, (char *) &(from_connect->header),
						 sizeof(struct gop_header));
					break;
				}
			}
			/*
			 * test si on'a pas trouve de destinataire
			 */
			if (*to_connect == NULL) {
				gop_errno = GOP_RECEIVER_UNKNOWN;
			}
		}
	}
	/*
	 * acknowledge du header uniquement si on est le destinataire ou s'il
	 * y a une erreur
	 */
	if (*to_connect == NULL) {
		local_gop_errno = gop_errno;
		if (from_connect->hsync)
			if (gop_acknow_write(from_connect) != GOP_OK)
				return (GOP_KO);
		gop_errno = local_gop_errno;
	}
	if (gop_errno != GOP_OK)
		return (GOP_KO);

	return (GOP_OK);
}


static int 
gop_d_packet_write (struct gop_connect *connect, char *buf, int size)
{
	/*
	 * ecrit un packet "buf" de Section_De_Donnee contenant "size" bytes.
	 */

	char            lettre = 'D';
	char		*ptr;
	XDR             xdrs;
	int		len;

	if (connect->mode >= GOP_PACKET)
		gop_printf("gop: [%8s] -> [%8s] \t\t write 1 packet data_section sur cd=%d\n", 
			connect->my_name, connect->his_name,  connect->cd);


	/*
	si on envoie un paquet type XDR, il faut le convertir dans un
	buffer intermediaire.
	*/
	if (connect->need_xdr && !(connect->datatype==GOP_CHAR || connect->datatype==GOP_STRUCT))  {
		if (connect->mode >= GOP_PACKET_INFO)
			gop_printf("gop: [%8s] -> [%8s] \t\t xdr: taille originale = %d\n", 
				connect->my_name, connect->his_name,  size);
		len = size/gop_size_of_datatype(connect->datatype);
		size = size + GOP_XDR_HEADER_SIZE;
		if (connect->mode >= GOP_PACKET_INFO)
			gop_printf("gop: [%8s] -> [%8s] \t\t xdr: nouvelle taille =  %d\n", 
				connect->my_name, connect->his_name,  size);
		ptr = (char *) alloca(size);
		if (ptr <= (char *)NULL) {
			gop_errno = GOP_ALLOC;
			return (GOP_KO);
		}
		xdrmem_create(&xdrs, (char *) ptr, (u_int) size, XDR_ENCODE);
		if (connect->mode >= GOP_PACKET)
			gop_printf("gop: [%8s] -> [%8s] \t\t XDR_ENCODE dans %d \n", 
				connect->my_name, connect->his_name,  ptr);

		/*
		 * convertion pour le paquet XDR
		 */

		if (xdr_array(&xdrs, &buf, (u_int *) &len, (u_int) size,
			      (u_int) gop_size_of_datatype(connect->datatype),
			      (xdrproc_t) xdr_fct[connect->datatype]) != 1) {
			gop_errno = GOP_XDR_FAILED;
			return (GOP_KO);
		}
		if (connect->mode >= GOP_PACKET_INFO)
			gop_printf("gop: [%8s] -> [%8s] \t\t xdr: code = %d element\n", 
				connect->my_name, connect->his_name,  len);
	} else {
		ptr = buf;
	}



	if (gop_first_byte_write(connect, &lettre) != GOP_OK)
		return (GOP_KO);

	if(gop_io_write(connect, ptr, size) != GOP_OK)
		return (GOP_KO);

	/*
	 * si ce n'est pas une erreur system, on doit lire l'acknow si
	 * necessaire
	 */
	if (errno == 0 && connect->dsync) {
		if (gop_acknow_read(connect) != GOP_OK)
			return (GOP_KO);
		if (remote_status != GOP_OK){
			gop_errno = GOP_REMOTE_PROBLEM;
			return (GOP_KO);
		}
	}
	return (GOP_OK);

}



int 
gop_data_section_write (struct gop_connect *connect, char *buf, int flag, int npix_x, int dx, int dy)
{
	int             nb_packet;
	int             i, size, size_of_last_packet;
	int             write_bytes, offset;

	if(connect->msize == 0) return(GOP_OK);

	if (connect->mode >= GOP_MESSAGE){
		gop_printf("gop: [%8s] -> [%8s] \t write data section sur cd=%d\n", 
			connect->my_name, connect->his_name,  connect->cd);
	}
	if (connect->mode >= GOP_HEADER){
		if (connect->datatype == GOP_CHAR){
			gop_printf("gop: [%8s] -> [%8s] Contenu: >>%s<<\n", 
				connect->my_name, connect->his_name, buf);
		}
	}


	nb_packet = connect->msize / abs(connect->psize);
	if ((size_of_last_packet = connect->msize % connect->psize) != 0) {
		nb_packet = nb_packet + 1;
	} else {
		size_of_last_packet = abs(connect->psize);
	}

	if (connect->mode >= GOP_PACKET_INFO)
		gop_printf("gop: [%8s] -> [%8s] \t\t write %d packets sur cd=%d, size=%d  last_size=%d\n", 
			connect->my_name, connect->his_name,  nb_packet, 
			connect->cd, connect->psize, size_of_last_packet);

	write_bytes = 0;

	for (i = 0; i < nb_packet; i++) {

		if(flag == GOP_TRUE){
			offset = write_bytes;
		} else {
			offset = gop_size_of_datatype(connect->datatype)*(npix_x * (i + dy) + dx);
		}
			

		/*
		 * simulation de FDM au Neme block (modifier le test avec i
		 * positif)
		 */

		if (i == -1) {
			gop_printf("gop: [%8s] -> [%8s] *********** arret d'urgence\n", 
				connect->my_name, connect->his_name); 
			(void) gop_write_end_of_message(connect, "SIMULATION D'ERREUR");
			return (GOP_OK);

		}
		size = abs(connect->psize);
		if (i == nb_packet - 1)
			size = size_of_last_packet;

		if (connect->mode >= GOP_PACKET_INFO)
			gop_printf("gop: [%8s] -> [%8s] \t\t write packet No %d sur cd=%d, size=%d, offset=%d, addr=%d\n", 
				connect->my_name, connect->his_name,  
				i, connect->cd, size, offset, buf + offset);
		if (gop_d_packet_write(connect, buf + offset, size) != GOP_OK)
			return (GOP_KO);

		write_bytes = write_bytes + size;
		if (connect->mode >= GOP_PACKET_INFO)
			gop_printf("gop: [%8s] -> [%8s] \t\t %d bytes transmis sur cd=%d\n", 
				connect->my_name, connect->his_name,  write_bytes, connect->cd);

		if(connect->interrupted == GOP_INTERRUPTED){
			/*
			 * si le dernier packet est transmis, on oublie
			 * l'interruption. PAR CONTRE, CELA SIGNIFIE QUE LE
			 * SIGNAL TOMBE A L'EAU ET QUE LE MESSAGE EST QUAND
			 * MEME TRANSMIS. Cas typique, 2 clients: le ctrl-c
			 * est tape sur le deuxieme client alors que le
			 * premier est en cours de traitement. Losque c'est
			 * son tour, le message est donc transmis, est le
			 * signal oublie....
			 */
			if (i == nb_packet-1) {
				connect->interrupted = GOP_OK;
			} else {
				/*
				 * on restaure les signaux car il sont
				 * initialises dans
				 * gop_write_end_of_message().
				 */
				gop_restore_handler(SIGINT);
				gop_restore_handler(SIGURG);
				gop_restore_handler(SIGPIPE);
				gop_restore_handler(SIGHUP);
				gop_write_end_of_message(connect, "Interrupted transmission");
				gop_errno = GOP_INTERRUPTED_TRANSMISSION;
				return (GOP_OK);
			}
		}

	}
	return (GOP_OK);
}


static int 
gop_d_packet_read (struct gop_connect *connect, char *buf, int size, int flag_acknow)
{
	/*
	 * lit un packet de Section_De_Donnee contenant "size" bytes dans
	 * "buf". Retourne GOP_END_OF_MESSAGE en cas de reception d'un byte
	 * de header Fin_De_Message.
	 */

	char            lettre;
	char		*ptr;
	XDR             xdrs;
	int		len=0;

	if (connect->mode >= GOP_PACKET)
		gop_printf("gop: [%8s] <- [%8s] \t\t read 1 packet data_section sur cd=%d\n", 
			connect->my_name, connect->his_name,  connect->cd);
/*
	if (gop_first_byte_read(connect, &lettre) != GOP_OK)
		return (GOP_KO);
	if (lettre != GOP_HEADER_DAT && lettre != GOP_HEADER_END) {
		gop_errno = GOP_BAD_SEQUENCE;
		return (GOP_KO);
	}
*/
	/* 
	lit sur le cannal jusqu'a la reception d'un 'D' ou d'un 'E'
	*/
	do {
		if (gop_first_byte_read(connect, &lettre) != GOP_OK)
			return (GOP_KO);
		if (lettre == GOP_HEADER_STD) {
			if (connect->mode >= GOP_HEADER)
				gop_printf("gop: [%8s] -> [%8s] \t **** DETECTION DE COLISISION*** \n",
				       connect->my_name, connect->his_name);

			/* on memorise le header et la data section s'il y a une collision */
			memcpy((char *)&memo_connect, (char *)connect, sizeof(struct gop_connect));

			if (gop_header_read_without_acknow(&memo_connect) != GOP_OK)
				return (GOP_KO);
			strcpy(memo_connect.to, memo_connect.header.to);
			strcpy(memo_connect.from, memo_connect.header.from);
			if (gop_data_section_read(&memo_connect, memo_data_section, sizeof(memo_data_section), GOP_TRUE, 0, 0, 0) < GOP_OK)
				return (GOP_KO);
			memo_action = GOP_TRUE;
			if (connect->mode >= GOP_HEADER)
				gop_printf("gop: [%8s] -> [%8s] \t **** FIN DE DETECTION DE COLISISION*** Le message est differe\n",
				       connect->my_name, connect->his_name);
		}
	}
	while (lettre != GOP_HEADER_DAT && lettre != GOP_HEADER_END);

	/*
	 * detection de fin de message
	 */
	if (lettre == GOP_HEADER_END) {
		if (connect->mode >= 0)
			gop_printf("gop: [%8s] <- [%8s]  DETECTION BLOC FIN MESSAGE ****** sur cd=%d\n", 
				connect->my_name, connect->his_name,  connect->cd);
		gop_errno = GOP_END_OF_MESSAGE;
		connect->header.header_type = GOP_HEADER_STD;
		return (GOP_KO);
	}

	/*
	si on recoit un paquet type XDR, il faut le lire dans un
	buffer intermediaire afin de le convertir dans le vrai
	buffer.
	*/
	if (connect->xdr && !(connect->datatype==GOP_CHAR || connect->datatype==GOP_STRUCT)) {
		if (connect->mode >= GOP_PACKET_INFO)
			gop_printf("gop: [%8s] <- [%8s] \t\t xdr: taille originale = %d\n", 
				connect->my_name, connect->his_name,  size);
		size = size + GOP_XDR_HEADER_SIZE;
		if (connect->mode >= GOP_PACKET_INFO)
			gop_printf("gop: [%8s] <- [%8s] \t\t xdr: nouvelle taille =  %d\n", 
				connect->my_name, connect->his_name,  size);
		ptr = (char *) alloca(size);
		if (ptr <= (char *)NULL) {
			gop_errno = GOP_ALLOC;
			return (GOP_KO);
		}
		xdrmem_create(&xdrs, (char *) ptr, (u_int) size, XDR_DECODE);
		if (connect->mode >= GOP_PACKET)
			gop_printf("gop: [%8s] <- [%8s] \t\t XDR_DECODE dans %d \n", 
				connect->my_name, connect->his_name,  ptr);
	} else {
		ptr = buf;
	}

	/*
	lecture
	*/
	
	if(gop_io_read(connect, ptr, size) != GOP_OK)
		return (GOP_KO);

	/*
	 * si on a lu quelque chose et qu'il n'y a pas d'erreur system, on
	 * renvoie un acknow(connect)
	 */

	if (errno == 0 && connect->dsync && flag_acknow) {
		if (gop_acknow_write(connect) != GOP_OK)
			return (GOP_KO);
	}
	/*
	 * si  erreur GOP: arret
	 */
	if (gop_errno != GOP_OK)
		return (GOP_KO);

	/*
	convertion pour le paquet XDR
	*/

	if (connect->xdr && !(connect->datatype==GOP_CHAR || connect->datatype==GOP_STRUCT)) {
		if (xdr_array(&xdrs, &buf, (u_int *) &len, (u_int) size,
			      (u_int) gop_size_of_datatype(connect->datatype),
			      (xdrproc_t) xdr_fct[connect->datatype]) != 1) {
			gop_errno = GOP_XDR_FAILED;
			return (GOP_KO);
		}
		if (connect->mode >= GOP_PACKET_INFO)
			gop_printf("gop: [%8s] <- [%8s] \t\t xdr: lu = %d element\n", 
				connect->my_name, connect->his_name,  len);
	}

	return (GOP_OK);
}




int 
gop_data_section_read (struct gop_connect *connect, char *buf, int maxsize, int flag, int npix_x, int dx, int dy)
{
	/*
	 * avec flag = GOP_FALSE les adresses de destinations
	 * ne sont pas successives car on tranfert une partie d'un tableau 2D
	 * (patch). npix_x est la taille selon X de la matrice d'origine et
	 * dx et dy l'offset de lasous matrice dans cette matrice
	 */

	/*
	 * RETURN VALUE:
	 * 
	 * >0 = nb_bytes_lus
	 * 
	 * < 0 = nb de bytes lus (valeur absolue) avec erreur dans gop_errno
	 * 
	 * cas special si == -1 erreur sans bytes lus
	 * 
	 * si gop_errno = GOP_END_OF_MESSAGE -> on a recu le premier byte du
	 * bloc de fin de message, c'est la fonction appellante qui doit lire
	 * le bloc complet
	 */

	int             nb_packet, offset;
	int             i, size, size_of_last_packet;
	int             read_bytes;

	if(connect->msize == 0) return(0);

	if (connect->mode >= GOP_MESSAGE)
		gop_printf("gop: [%8s] <- [%8s] \t read data section sur cd=%d\n", 
			connect->my_name, connect->his_name,  connect->cd);

	if (connect->msize > maxsize) {
		gop_errno = GOP_TOO_BIG;
		if (connect->dsync) {
			if (gop_acknow_write(connect) != GOP_OK)
				return (GOP_KO);
		}
		/* on repete GOP_TOO_BIG car gop_acknow_write pose gop_errno=0 */
		gop_errno = GOP_TOO_BIG;
		return (GOP_KO);
	}

	nb_packet = connect->msize / abs(connect->psize);
	if ((size_of_last_packet = connect->msize % abs(connect->psize)) != 0) {
		nb_packet = nb_packet + 1;
	} else {
		size_of_last_packet = abs(connect->psize);
	}

	if (connect->mode >= GOP_PACKET_INFO)
		gop_printf("gop: [%8s] <- [%8s] \t\t read %d packets sur cd=%d, size=%d  last_size=%d\n", 
			connect->my_name, connect->his_name,  nb_packet, 
			connect->cd, connect->psize, size_of_last_packet);

	read_bytes = 0;

	for (i = 0; i < nb_packet; i++) {

		if(flag == GOP_TRUE){
			offset = read_bytes;
		} else {
			offset = gop_size_of_datatype(connect->datatype)*((dy + i) * npix_x + dx);
		}

		size = abs(connect->psize);
		if (i == nb_packet - 1)
			size = size_of_last_packet;

		if (connect->mode >= GOP_PACKET_INFO)
			gop_printf("gop: [%8s] <- [%8s] \t\t read packet No %d sur cd=%d, size=%d, offset=%d, addr=%d\n", 
				connect->my_name, connect->his_name,  
				i, connect->cd, size, offset, buf + offset);

		if (gop_d_packet_read(connect, buf + offset, size, GOP_TRUE) != GOP_OK)
			return (GOP_MIN(GOP_KO, -read_bytes));

		read_bytes = read_bytes + size;

		if (connect->mode >= GOP_PACKET_INFO)
			gop_printf("gop: [%8s] <- [%8s] \t\t %d bytes lus sur cd=%d\n", 
				connect->my_name, connect->his_name,  read_bytes, connect->cd);

	}


	if (connect->mode >= GOP_HEADER){
		if (connect->datatype == GOP_CHAR){
			gop_printf("gop: [%8s] <- [%8s] Contenu: >>%s<<\n", 
				connect->my_name, connect->his_name, buf);
		}
	}


	return (read_bytes);
}



static int 
gop_data_section_forward (struct gop_connect *from_connect, struct gop_connect *to_connect)
{
	char           *buf;
	int             size_of_buf;
	int             nb_bytes_in_buf;
	int             nb_packet_read;
	int             nb_packet_write;
	int             ptr;

	int             from_nb_packet;
	int             from_size_of_last_packet;
	int             from_size;

	int             to_nb_packet;
	int             to_size_of_last_packet;
	int             to_size;

	int             max_size_transfert;


	/*
	 * la structure from_connect contient les parametre de reception,
	 * 
	 * la structure to_connect contient le header initial avec les
	 * parametres pour l'envoi
	 * 
	 * la seule valeur a changer dans le header initial est
	 * to_connect->header->psize, si to_connect->maxpacket est plus petit
	 * que from_connect->psize
	 * 
	 */

	if (from_connect->msize == 0)
		return (GOP_OK);

	if (from_connect->mode >= GOP_MESSAGE)
		gop_printf("gop: [%8s] -> [%8s] \t forward data_section from cd=%d to cd=%d ([%8s] sur [%8s])\n", 
				from_connect->my_name, from_connect->his_name,  
				from_connect->cd, to_connect->cd,
				from_connect->his_name, to_connect->his_name);

	/*
	 * passage des parametres initiaux de to_connect->header dans
	 * to_connect
	 */

	gop_header_to_struct(to_connect, &(to_connect->header));

	max_size_transfert = GOP_MAX(abs(from_connect->psize), to_connect->maxpacket);
	size_of_buf = 2 * max_size_transfert - 1;

	if (from_connect->mode >= GOP_MESSAGE)
		gop_printf("gop: [%8s]    [--------] \t allocation de buffer intermediaire de %d bytes\n", 
			from_connect->my_name, size_of_buf);
	buf = (char *) alloca(size_of_buf);
	if (buf == 0) {
		gop_errno = GOP_ALLOC;
		return (GOP_KO);
	}
	/*
	 * lecture de la section de donnée
	 */
	/*
	 * nombre et taille du dernier paquet en reception
	 */

	from_size = abs(from_connect->psize);
	from_nb_packet = from_connect->msize / from_size;
	if ((from_size_of_last_packet = from_connect->msize % from_size) != 0) {
		from_nb_packet = from_nb_packet + 1;
	} else {
		from_size_of_last_packet = from_size;
	}
	/*
	 * nombre et taille du dernier paquet en emission. La taille de
	 * sortie est posée a maxpacket sauf si la taille de doit pas etre
	 * changee (psize negatif)
	 */

	to_size = to_connect->maxpacket;
	if(from_connect->psize < 0)
		to_size = from_size;

	to_nb_packet = to_connect->msize / to_size;
	if ((to_size_of_last_packet = to_connect->msize % to_size) != 0) {
		to_nb_packet = to_nb_packet + 1;
	} else {
		to_size_of_last_packet = to_size;
	}


	if (from_nb_packet == 1)
		from_size = from_size_of_last_packet;

	if (to_nb_packet == 1)
		to_size = to_size_of_last_packet;

	nb_bytes_in_buf = 0;
	nb_packet_read = 0;
	nb_packet_write = 0;


	while (nb_packet_read < from_nb_packet) {

		/*
		 * etape 1: remplissage du buffer buf. test: tant qu'on peut
		 * lire un packet dans buf ET qu'on n'a pas encore tout lu
		 * tous les packets ALORS remplissage de buf
		 */

		do {
			if (from_connect->mode >= GOP_PACKET_INFO)
				gop_printf("gop: [%8s] <- [%8s] \t\t read packet No %d sur cd=%d, size=%d\n", 
					from_connect->my_name, from_connect->his_name, 
					nb_packet_read, from_connect->cd, from_size);
			if (gop_d_packet_read(from_connect, buf + nb_bytes_in_buf,
						     from_size, GOP_TRUE) != GOP_OK) {
				if (gop_errno == GOP_END_OF_MESSAGE) {
					/*
					 * en cas de reception du 'E' de fin
					 * de message
					 */

					if (gop_header_read(from_connect) != GOP_OK)
						return (GOP_KO);

					from_connect->header.header_type = GOP_HEADER_END;

					(void) memcpy((char *) &to_connect->header, (char *) &from_connect->header,
						 sizeof(struct gop_header));

					gop_header_to_struct(to_connect, &(to_connect->header));


					if (gop_header_write(to_connect) != GOP_OK)
						return (GOP_KO);

					from_connect->header.header_type = GOP_HEADER_STD;

					return (gop_data_section_forward(from_connect, to_connect));
				} else {
					return (GOP_KO);
				}
			}

			if (from_connect->mode >= GOP_HEADER){
				if (from_connect->datatype == GOP_CHAR){
					gop_printf("gop: [%8s] <- [%8s] Contenu: >>%s<<\n", 
						from_connect->my_name, from_connect->his_name, buf + nb_bytes_in_buf);
				}
			}

			nb_packet_read++;
			nb_bytes_in_buf = nb_bytes_in_buf + from_size;

			if (nb_packet_read + 1 == from_nb_packet)
				from_size = from_size_of_last_packet;
		}
		while (nb_bytes_in_buf < max_size_transfert &&
		       nb_packet_read < from_nb_packet);


		/*
		 * etape 2: envoi du buffer tampon "buf" test: tant que la
		 * taille restante du buffer permet de remplir un packet
		 * ALORS envoi
		 */

		ptr = 0;

		while (nb_bytes_in_buf - ptr >= to_size) {

			if (to_connect->mode >= GOP_PACKET_INFO)
				gop_printf("gop: [%8s] -> [%8s] \t\t write packet No %d sur cd=%d, size=%d\n", 
					to_connect->my_name, to_connect->his_name, 
					nb_packet_write, to_connect->cd, to_size);
			if (gop_d_packet_write(to_connect, buf + ptr, to_size) != GOP_OK) {
				return (GOP_KO);
			}
			if (to_connect->mode >= GOP_HEADER){
				if (to_connect->datatype == GOP_CHAR){
					gop_printf("gop: [%8s] -> [%8s] Contenu: >>%s<<\n", 
						to_connect->my_name, to_connect->his_name, buf + ptr);
				}
			}

			nb_packet_write++;

			ptr = ptr + to_size;

			if (nb_packet_write + 1 == to_nb_packet)
				to_size = to_size_of_last_packet;
		}
		if (ptr != nb_bytes_in_buf)
			(void) memcpy(buf, buf + ptr, nb_bytes_in_buf - ptr);
		nb_bytes_in_buf = nb_bytes_in_buf - ptr;
	}

	return (GOP_OK);
}



static int 
gop_header_forward (struct gop_connect *from_connect, struct gop_connect *to_connect)
{
	int             local_gop_errno;
	int		to_psize;

	if (to_connect->mode >= GOP_MESSAGE)
		gop_printf("gop: [%8s] -> [%8s] \t forward header from cd=%d to cd=%d ([%8s] sur [%8s])\n", 
			from_connect->my_name, from_connect->his_name, 
			from_connect->cd, to_connect->cd,
			from_connect->his_name, to_connect->his_name);

	/*
	 * changement de la taille des packets
	 */
	to_psize = to_connect->maxpacket;
	if(from_connect->psize < 0)
		to_psize = from_connect->psize;

	sprintf(to_connect->header.psize, "%d", to_psize);
	/*
	 * determine le besoin en XDR
	 */
	if (to_connect->need_xdr && !(to_connect->datatype==GOP_CHAR || to_connect->datatype==GOP_STRUCT)) {
		strcpy(to_connect->header.xdr, GOP_STR_TRUE);
	} else {
		strcpy(to_connect->header.xdr, GOP_STR_FALSE);
	}

	gop_header_to_struct(to_connect, &(to_connect->header));

	gop_header_write(to_connect);
	local_gop_errno = gop_errno;
	/*
	 * acknowledge du header selon status
	 */
	if (from_connect->hsync)
		if (gop_acknow_write(from_connect) != GOP_OK)
			return (GOP_KO);

	gop_errno = local_gop_errno;
	if (gop_errno != GOP_OK)
		return (GOP_KO);
	return (GOP_OK);
}


int 
gop_select_active_channel (struct gop_list *list_active, struct gop_list *list_ready)
{
	/*
	 * prend une liste de channel descriptor en entree pour effectuer un
	 * select. Retourne la liste des numero de cd qui on qqch en attente.
	 * Le premier cd de la liste a la plus grande priorite.
	 */

	int             i, ptr;
	long            width;
	int             cd;
	//int		cpt_eagain=0;

#ifdef SELECT_CALL
	fd_set          readfds;
	struct timeval  timeout, *ptr_timeout;
#endif
#ifdef POLL_CALL
	struct pollfd  *pfd;
	int		timeout;
#endif


	if (list_active->gop[0]->mode >= GOP_POLL) {
#ifdef SELECT_CALL
		gop_printf("gop: [%8s] <> [-SELECT-] select sur %d channel descriptor:\n", 
			list_active->gop[0]->my_name, list_active->nb);
#endif
#ifdef POLL_CALL
		gop_printf("gop: [%8s] <> [--POLL--] poll sur %d channel descriptor:\n", 
			list_active->gop[0]->my_name, list_active->nb);
#endif
		for (i = 0; i < list_active->nb; i++) {
			if (list_active->gop[i]->cd != -1) {
				gop_printf("gop: [%8s] <> [%8s] \t cd[%d]      = %d\n", 
					list_active->gop[i]->my_name, list_active->gop[i]->his_name, 
					i, list_active->gop[i]->cd);
			} else {
				gop_printf("gop: [%8s] <> [%8s] \t cd_init[%d] = %d\n", 
					list_active->gop[i]->my_name, list_active->gop[i]->his_name, 
					i, list_active->gop[i]->cd_init);
			}
		}
	}
	/*
	 * selection des channel descriptor
	 */
#ifdef SELECT_CALL
#pragma warning(disable:593)
	FD_ZERO(&readfds);
	for (i = 0; i < list_active->nb; i++) {
		if (list_active->gop[i]->cd != -1) {
			FD_SET(list_active->gop[i]->cd, &readfds);
		} else {
			FD_SET(list_active->gop[i]->cd_init, &readfds);
		}
	}

	/*
	 * attente sur select
	 */
	width = ulimit(4, 0L);

	/* initilialisation du timer */

	if (list_active->timeout <= 0) {
		ptr_timeout = (struct timeval *) NULL;
	} else {
		timeout.tv_sec = list_active->timeout;
		timeout.tv_usec = 0;
		ptr_timeout = &timeout;
	}
#endif
#ifdef POLL_CALL
	pfd = (struct pollfd *) alloca(list_active->nb * sizeof(struct pollfd));
	if(pfd == (struct pollfd *) NULL){
			gop_errno = GOP_ALLOC;
			return (GOP_KO);
	}
	memset(pfd, 0, list_active->nb * sizeof(struct pollfd));
	for (i = 0; i < list_active->nb; i++) {
		if (list_active->gop[i]->cd != -1) {
			pfd[i].fd = list_active->gop[i]->cd;
		} else {
			pfd[i].fd = list_active->gop[i]->cd_init;
		}
		pfd[i].events = POLLRDNORM;
	}
#endif

	/*
	 * gestion des signaux alors que le process est en attente de message
	 */
	/*
	 * initialisation pour le handler
	 */
	gop_connect_client = list_active->gop[0];
	gop_connect_client->opcrt = GOP_SELECT;
	gop_set_side(gop_connect_client, GOP_TRANSMIT_SIDE);	/* <<<<< a verifier
								 * !!!!!! */
	/*
	 * installation du handler uniquement pour SIGURG, car on est
	 * uniquement un serveur ou un transmetter
	 */
	gop_init_handler(SIGURG);

#ifdef SELECT_CALL
	while ((list_ready->nb = select((int) width, &readfds, (fd_set *) 0, (fd_set *) 0, ptr_timeout)) <= 0) {
#endif

#ifdef POLL_CALL
	if(list_active->timeout == 0){
		timeout = -1;
	}else{
		timeout = list_active->timeout*1;
	}
	while ((list_ready->nb = poll(pfd, list_active->nb, timeout)) <= 0) {
#endif
		if (list_active->gop[0]->mode >= GOP_POLL) {
			gop_printf("gop: [%8s] <> [--POLL--] \t sortie de poll() ou select() avec nb d'evenements en attente = %d et errno = %d\n", 
				list_active->gop[0]->my_name, list_ready->nb, errno);
		}

		if (list_ready->nb == 0) {
			/*
			 * cas du timeout
			 */
			gop_restore_handler(SIGURG);
			gop_errno = GOP_TIMEOUT;
			return (GOP_KO);
		} else if (gop_connect_client->interrupted == GOP_INTERRUPTED) {
			/*
			 * interruption durant le select
			 */
			gop_printf("gop: [%8s] <> [--POLL--] \n\n GOP_INTERRUPTED: interruption durant le select \n\n", 
				gop_connect_client->my_name); 
			/*
			 * on recherche dans la liste des connections en
			 * attente sur le select si une est en cours de
			 * transmission (flag CONT a GOP_TRUE) si c'est le
			 * cas, on lui balance un sigurg
			 */
			for (i = 0; i < list_active->nb; i++) {
				if (list_active->gop[i]->cont) {
					gop_send_sigurg(list_active->gop[i]);
				}
			}

		//} else if (list_ready->nb < 0) {
		//	/* erreur system */
		//	if(errno==EAGAIN){
		//		gop_printf("gop: [%8s] <> [--POLL--] ***** ERREUR SYSTEM EAGAIN: %s: \n", 
		//			gop_connect_client->my_name, my_strerror(errno)); 
		//		if(cpt_eagain++<1000){
		//			continue;
		//		}
		//	}
		//	gop_restore_handler(SIGURG);
		//	gop_errno = GOP_ERRNO;
		//	return (GOP_KO);
		}
	}
	gop_restore_handler(SIGURG);

	if (list_active->gop[0]->mode >= GOP_POLL) {
		gop_printf("gop: [%8s] <> [--POLL--] \t sortie de poll() ou select() avec nb d'evenements en attente = %d et errno = %d\n", 
			list_active->gop[0]->my_name, list_ready->nb, errno);
	}


	/*
	 * decodage des channel descriptor en attente
	 */

	ptr = 0;
	for (i = 0; i < list_active->nb; i++) {

		if (list_active->gop[i]->cd != -1) {
			cd = list_active->gop[i]->cd;
		} else {
			cd = list_active->gop[i]->cd_init;
		}

#ifdef SELECT_CALL
		if (FD_ISSET(cd, &readfds) != 0) {
			if (list_active->gop[0]->mode >= GOP_POLL) {
				gop_printf("gop: [%8s] <- [%8s] \t\t detection sur cannal: cd[%d] = %d\n", 
					list_active->gop[i]->my_name, list_active->gop[i]->his_name,  ptr, cd);
			}
			list_ready->gop[ptr++] = list_active->gop[i];
		}
#endif

#ifdef POLL_CALL
		/* gop_printf("gop: [%8s] -> [%8s] %d & %d = %d\n", connect->my_name, connect->his_name, pfd[i].revents, pfd[i].events, pfd[i].revents & pfd[i].events); */
		if((pfd[i].revents & pfd[i].events) != 0){
			if (list_active->gop[0]->mode >= GOP_POLL) {
				gop_printf("gop: [%8s] <- [%8s] \t\t detection sur cannal: cd[%d] = %d\n", 
					list_active->gop[i]->my_name, list_active->gop[i]->his_name,  ptr, cd);
			}
			list_ready->gop[ptr++] = list_active->gop[i];
		}

#endif

	}

	return (GOP_OK);
}

#ifdef POLL_CALL

int 
gop_select_active_channel_poll (struct gop_list *list_active, struct gop_list *list_ready)
{
	/*
	 * prend une liste de channel descriptor en entree pour effectuer un
	 * select. Retourne la liste des numero de cd qui on qqch en attente.
	 * Le premier cd de la liste a la plus grande priorite.
	 */

	int             i, ptr;
	long            width;
	int             cd;
	//int		cpt_eagain=0;

	struct pollfd  *pfd;
	int		timeout;


	if (list_active->gop[0]->mode >= GOP_POLL) {
		gop_printf("gop: [%8s] <> [--POLL--] poll sur %d channel descriptor:\n", 
			list_active->gop[0]->my_name, list_active->nb);
		for (i = 0; i < list_active->nb; i++) {
			if (list_active->gop[i]->cd != -1) {
				gop_printf("gop: [%8s] <> [%8s] \t cd[%d]      = %d\n", 
					list_active->gop[i]->my_name, list_active->gop[i]->his_name, 
					i, list_active->gop[i]->cd);
			} else {
				gop_printf("gop: [%8s] <> [%8s] \t cd_init[%d] = %d\n", 
					list_active->gop[i]->my_name, list_active->gop[i]->his_name, 
					i, list_active->gop[i]->cd_init);
			}
		}
	}
	/*
	 * selection des channel descriptor
	 */
	pfd = (struct pollfd *) alloca(list_active->nb * sizeof(struct pollfd));
	if(pfd == (struct pollfd *) NULL){
			gop_errno = GOP_ALLOC;
			return (GOP_KO);
	}
	memset(pfd, 0, list_active->nb * sizeof(struct pollfd));
	for (i = 0; i < list_active->nb; i++) {
		if (list_active->gop[i]->cd != -1) {
			pfd[i].fd = list_active->gop[i]->cd;
		} else {
			pfd[i].fd = list_active->gop[i]->cd_init;
		}
		pfd[i].events = POLLRDNORM;
	}

	/*
	 * gestion des signaux alors que le process est en attente de message
	 */
	/*
	 * initialisation pour le handler
	 */
	gop_connect_client = list_active->gop[0];
	gop_connect_client->opcrt = GOP_SELECT;
	gop_set_side(gop_connect_client, GOP_TRANSMIT_SIDE);	/* <<<<< a verifier
								 * !!!!!! */
	/*
	 * installation du handler uniquement pour SIGURG, car on est
	 * uniquement un serveur ou un transmetter
	 */
	gop_init_handler(SIGURG);

	if(list_active->timeout == 0){
		timeout = -1;
	}else{
		timeout = list_active->timeout*1;
	}
	while ((list_ready->nb = poll(pfd, list_active->nb, timeout)) <= 0) {
		if (list_active->gop[0]->mode >= GOP_POLL) {
			gop_printf("gop: [%8s] <> [--POLL--] \t sortie de poll() ou select() avec nb d'evenements en attente = %d et errno = %d\n", 
				list_active->gop[0]->my_name, list_ready->nb, errno);
		}

		if (list_ready->nb == 0) {
			/*
			 * cas du timeout
			 */
			gop_restore_handler(SIGURG);
			gop_errno = GOP_TIMEOUT;
			return (GOP_KO);
		} else if (gop_connect_client->interrupted == GOP_INTERRUPTED) {
			/*
			 * interruption durant le select
			 */
			gop_printf("gop: [%8s] <> [--POLL--] \n\n GOP_INTERRUPTED: interruption durant le select \n\n", 
				gop_connect_client->my_name); 
			/*
			 * on recherche dans la liste des connections en
			 * attente sur le select si une est en cours de
			 * transmission (flag CONT a GOP_TRUE) si c'est le
			 * cas, on lui balance un sigurg
			 */
			for (i = 0; i < list_active->nb; i++) {
				if (list_active->gop[i]->cont) {
					gop_send_sigurg(list_active->gop[i]);
				}
			}

		//} else if (list_ready->nb < 0) {
		//	/* erreur system */
		//	if(errno==EAGAIN){
		//		gop_printf("gop: [%8s] <> [--POLL--] ***** ERREUR SYSTEM EAGAIN: %s: \n", 
		//			gop_connect_client->my_name, my_strerror(errno)); 
		//		if(cpt_eagain++<1000){
		//			continue;
		//		}
		//	}
		//	gop_restore_handler(SIGURG);
		//	gop_errno = GOP_ERRNO;
		//	return (GOP_KO);
		}
	}
	gop_restore_handler(SIGURG);

	if (list_active->gop[0]->mode >= GOP_POLL) {
		gop_printf("gop: [%8s] <> [--POLL--] \t sortie de poll() ou select() avec nb d'evenements en attente = %d et errno = %d\n", 
			list_active->gop[0]->my_name, list_ready->nb, errno);
	}


	/*
	 * decodage des channel descriptor en attente
	 */

	ptr = 0;
	for (i = 0; i < list_active->nb; i++) {

		if (list_active->gop[i]->cd != -1) {
			cd = list_active->gop[i]->cd;
		} else {
			cd = list_active->gop[i]->cd_init;
		}

		/* gop_printf("gop: [%8s] -> [%8s] %d & %d = %d\n", connect->my_name, connect->his_name, pfd[i].revents, pfd[i].events, pfd[i].revents & pfd[i].events); */
		if((pfd[i].revents & pfd[i].events) != 0){
			if (list_active->gop[0]->mode >= GOP_POLL) {
				gop_printf("gop: [%8s] <- [%8s] \t\t detection sur cannal: cd[%d] = %d\n", 
					list_active->gop[i]->my_name, list_active->gop[i]->his_name,  ptr, cd);
			}
			list_ready->gop[ptr++] = list_active->gop[i];
		}


	}

	return (GOP_OK);
}

#endif

int 
gop_select_active_channel_select (struct gop_list *list_active, struct gop_list *list_ready)
{
	/*
	 * prend une liste de channel descriptor en entree pour effectuer un
	 * select. Retourne la liste des numero de cd qui on qqch en attente.
	 * Le premier cd de la liste a la plus grande priorite.
	 */

	int             i, ptr;
	long            width;
	int             cd;
	//int		cpt_eagain=0;

	fd_set          readfds;
	struct timeval  timeout, *ptr_timeout;

	if (list_active->gop[0]->mode >= GOP_POLL) {
		gop_printf("gop: [%8s] <> [-SELECT-] select sur %d channel descriptor:\n", 
			list_active->gop[0]->my_name, list_active->nb);
		for (i = 0; i < list_active->nb; i++) {
			if (list_active->gop[i]->cd != -1) {
				gop_printf("gop: [%8s] <> [%8s] \t cd[%d]      = %d\n", 
					list_active->gop[i]->my_name, list_active->gop[i]->his_name, 
					i, list_active->gop[i]->cd);
			} else {
				gop_printf("gop: [%8s] <> [%8s] \t cd_init[%d] = %d\n", 
					list_active->gop[i]->my_name, list_active->gop[i]->his_name, 
					i, list_active->gop[i]->cd_init);
			}
		}
	}
	/*
	 * selection des channel descriptor
	 */
#pragma warning(disable:593)
	FD_ZERO(&readfds);
	for (i = 0; i < list_active->nb; i++) {
		if (list_active->gop[i]->cd != -1) {
			FD_SET(list_active->gop[i]->cd, &readfds);
		} else {
			FD_SET(list_active->gop[i]->cd_init, &readfds);
		}
	}

	/*
	 * attente sur select
	 */
	width = ulimit(4, 0L);

	/* initilialisation du timer */

	if (list_active->timeout <= 0) {
		ptr_timeout = (struct timeval *) NULL;
	} else {
		timeout.tv_sec = list_active->timeout;
		timeout.tv_usec = 0;
		ptr_timeout = &timeout;
	}

	/*
	 * gestion des signaux alors que le process est en attente de message
	 */
	/*
	 * initialisation pour le handler
	 */
	gop_connect_client = list_active->gop[0];
	gop_connect_client->opcrt = GOP_SELECT;
	gop_set_side(gop_connect_client, GOP_TRANSMIT_SIDE);	/* <<<<< a verifier
								 * !!!!!! */
	/*
	 * installation du handler uniquement pour SIGURG, car on est
	 * uniquement un serveur ou un transmetter
	 */
	gop_init_handler(SIGURG);

	while ((list_ready->nb = select((int) width, &readfds, (fd_set *) 0, (fd_set *) 0, ptr_timeout)) <= 0) {
		if (list_active->gop[0]->mode >= GOP_POLL) {
			gop_printf("gop: [%8s] <> [--POLL--] \t sortie de poll() ou select() avec nb d'evenements en attente = %d et errno = %d\n", 
				list_active->gop[0]->my_name, list_ready->nb, errno);
		}

		if (list_ready->nb == 0) {
			/*
			 * cas du timeout
			 */
			gop_restore_handler(SIGURG);
			gop_errno = GOP_TIMEOUT;
			return (GOP_KO);
		} else if (gop_connect_client->interrupted == GOP_INTERRUPTED) {
			/*
			 * interruption durant le select
			 */
			gop_printf("gop: [%8s] <> [--POLL--] \n\n GOP_INTERRUPTED: interruption durant le select \n\n", 
				gop_connect_client->my_name); 
			/*
			 * on recherche dans la liste des connections en
			 * attente sur le select si une est en cours de
			 * transmission (flag CONT a GOP_TRUE) si c'est le
			 * cas, on lui balance un sigurg
			 */
			for (i = 0; i < list_active->nb; i++) {
				if (list_active->gop[i]->cont) {
					gop_send_sigurg(list_active->gop[i]);
				}
			}

		//} else if (list_ready->nb < 0) {
		//	/* erreur system */
		//	if(errno==EAGAIN){
		//		gop_printf("gop: [%8s] <> [--POLL--] ***** ERREUR SYSTEM EAGAIN: %s: \n", 
		//			gop_connect_client->my_name, my_strerror(errno)); 
		//		if(cpt_eagain++<1000){
		//			continue;
		//		}
		//	}
		//	gop_restore_handler(SIGURG);
		//	gop_errno = GOP_ERRNO;
		//	return (GOP_KO);
		}
	}
	gop_restore_handler(SIGURG);

	if (list_active->gop[0]->mode >= GOP_POLL) {
		gop_printf("gop: [%8s] <> [--POLL--] \t sortie de poll() ou select() avec nb d'evenements en attente = %d et errno = %d\n", 
			list_active->gop[0]->my_name, list_ready->nb, errno);
	}


	/*
	 * decodage des channel descriptor en attente
	 */

	ptr = 0;
	for (i = 0; i < list_active->nb; i++) {

		if (list_active->gop[i]->cd != -1) {
			cd = list_active->gop[i]->cd;
		} else {
			cd = list_active->gop[i]->cd_init;
		}

		if (FD_ISSET(cd, &readfds) != 0) {
			if (list_active->gop[0]->mode >= GOP_POLL) {
				gop_printf("gop: [%8s] <- [%8s] \t\t detection sur cannal: cd[%d] = %d\n", 
					list_active->gop[i]->my_name, list_active->gop[i]->his_name,  ptr, cd);
			}
			list_ready->gop[ptr++] = list_active->gop[i];
		}

	}

	return (GOP_OK);
}

/**********************************************************************/


int 
gop_read (struct gop_connect *connect, char *cmd, int sizeof_cmd)
{
	int             status;

	/*
	 * memo de la structure de connection courante
	 */
	gop_connect_client = connect;
	connect->opcrt = GOP_READ;
	/*
	 * installation du handler specifique + handler user
	 */
	gop_init_handler(SIGINT);
	gop_init_handler(SIGURG);
	gop_init_handler(SIGPIPE);
	gop_init_handler(SIGHUP);

	status = gop_read_core(connect, cmd, sizeof_cmd, GOP_TRUE, 0, 0, 0);

	/*
	 * re-installation du handler user
	 */
	gop_restore_handler(SIGINT);
	gop_restore_handler(SIGURG);
	gop_restore_handler(SIGPIPE);
	gop_restore_handler(SIGHUP);
	return (status);

}





void
gop_handle_eom(struct gop_connect *connect, void fct(char *message))
{
	char           *message;
	char            buf;
	int             size = 256;
	int             malloc_ok;

	if (gop_errno == GOP_END_OF_MESSAGE) {

		malloc_ok = GOP_FALSE;
		message = malloc(size);

		if (message == NULL) {
			message = &buf;
			size = 1;
		} else {
			malloc_ok = GOP_TRUE;
		}
		if (gop_read_end_of_message(connect, message, size) < 0) {
			if (gop_errno == GOP_TOO_BIG)
				gop_errno = GOP_EOM_TOO_BIG;
			return;
		}
		if (fct == NULL) {
			gop_printf("gop: [%8s] <- [%8s] Recu fin de message: >%s<\n", 
				connect->my_name, connect->his_name,  message);
		} else {
			fct(message);
		}
		if (malloc_ok)
			free(message);
		gop_errno = GOP_INTERRUPTED_TRANSMISSION;
	}
	return;
}








int 
gop_read_matrix (struct gop_connect *connect, char *cmd, int sizeof_cmd, int npix_x, int dx, int dy)
{
	int             status;

	/*
	 * initialisation pour le handler
	 */
	gop_connect_client = connect;
	gop_connect_client->opcrt = GOP_READ;
	/*
	 * installation du handler specifique + handler user
	 */
	gop_init_handler(SIGINT);
	gop_init_handler(SIGURG);
	gop_init_handler(SIGPIPE);
	gop_init_handler(SIGHUP);

	status = gop_read_core(connect, cmd, sizeof_cmd, GOP_FALSE, npix_x, dx, dy);

	/*
	 * re-installation du handler user
	 */
	gop_restore_handler(SIGINT);
	gop_restore_handler(SIGURG);
	gop_restore_handler(SIGPIPE);
	gop_restore_handler(SIGHUP);
	return (status);

}


static int 
gop_read_core (struct gop_connect *connect, char *cmd, int sizeof_cmd, int flag, int npix_x, int dx, int dy)
{


	if(gop_h_read(connect)!=GOP_OK)return(GOP_KO);

	if(gop_header_read_without_acknow(connect)!= GOP_OK)
		return (GOP_KO);

	/*
	 * acknowledge du header avec tes tde la taille du message
	 */

	if (connect->msize > sizeof_cmd) 
		gop_errno = GOP_TOO_BIG;

	if (connect->hsync)
		if (gop_acknow_write(connect) != GOP_OK)
			return (GOP_KO);

	if (connect->msize > sizeof_cmd) 
		/* on repete GOP_TOO_BIG car gop_acknow_write pose gop_errno=0 */
		gop_errno = GOP_TOO_BIG;

	if (gop_errno != GOP_OK)
		return (GOP_KO);

	return(gop_data_section_read(connect, cmd, sizeof_cmd, flag, npix_x, dx, dy));

}



int 
gop_read_data (struct gop_connect *connect, char *buf, int sizeof_buf)
{
	int             status;

	/*
	 * initialisation pour le handler
	 */
	gop_connect_client = connect;
	gop_connect_client->opcrt = GOP_READ;
	/*
	 * installation du handler specifique + handler user
	 */
	gop_init_handler(SIGINT);
	gop_init_handler(SIGURG);
	gop_init_handler(SIGPIPE);
	gop_init_handler(SIGHUP);

	status = gop_data_section_read(connect, buf, sizeof_buf, GOP_TRUE, 0, 0, 0);

	/*
	 * re-installation du handler user
	 */
	gop_restore_handler(SIGINT);
	gop_restore_handler(SIGURG);
	gop_restore_handler(SIGPIPE);
	gop_restore_handler(SIGHUP);
	return (status);

}





int 
gop_read_end_of_message (struct gop_connect *connect, char *cmd, int sizeof_cmd)
{
	/*
	 * lit un message alors que le premier byte a deja ete lu
	 */
	if (gop_header_read_without_acknow(connect) != GOP_OK)
		return (GOP_KO);
	/*
	 * acknowledge du header avec tes tde la taille du message
	 */

	if (connect->msize > sizeof_cmd)
		gop_errno = GOP_TOO_BIG;

	if (connect->hsync)
		if (gop_acknow_write(connect) != GOP_OK)
			return (GOP_KO);

	if (connect->msize > sizeof_cmd)
		/* on repete GOP_TOO_BIG car gop_acknow_write pose gop_errno=0 */
		gop_errno = GOP_TOO_BIG;

	if (gop_errno != GOP_OK)
		return (GOP_KO);

	return (gop_data_section_read(connect, cmd, sizeof_cmd, GOP_TRUE, 0, 0, 0));
}


int 
gop_write (struct gop_connect *connect, char *data, int msize, int psize, int datatype)
{
	int             status;

	gop_set_from(connect, connect->my_name);
	/*
	 * initialisation pour le handler
	 */
	gop_connect_client = connect;
	gop_connect_client->opcrt = GOP_WRITE;
	/*
	 * installation du handler specifique + handler user
	 */
	gop_init_handler(SIGINT);
	gop_init_handler(SIGURG);
	gop_init_handler(SIGPIPE);
	gop_init_handler(SIGHUP);

	status = gop_write_core(connect, data, msize, psize, datatype, GOP_TRUE, 0, 0, 0);

	/*
	 * re-installation du handler user
	 */
	gop_restore_handler(SIGINT);
	gop_restore_handler(SIGURG);
	gop_restore_handler(SIGPIPE);
	gop_restore_handler(SIGHUP);
	return (status);

}


int 
gop_write_matrix (struct gop_connect *connect, char *data, int msize, int psize, int datatype, int npix_x, int dx, int dy)
{
	int             status;

	/*
	 * initialisation pour le handler
	 */
	gop_connect_client = connect;
	gop_connect_client->opcrt = GOP_WRITE;
	/*
	 * installation du handler specifique + handler user
	 */
	gop_init_handler(SIGINT);
	gop_init_handler(SIGURG);
	gop_init_handler(SIGPIPE);
	gop_init_handler(SIGHUP);

	status = gop_write_core(connect, data, msize, psize, datatype, GOP_FALSE, npix_x, dx, dy);

	/*
	 * re-installation du handler user
	 */
	gop_restore_handler(SIGINT);
	gop_restore_handler(SIGURG);
	gop_restore_handler(SIGPIPE);
	gop_restore_handler(SIGHUP);
	return (status);

}


static int 
gop_write_core (struct gop_connect *connect, char *data, int msize, int psize, int datatype, int flag, int npix_x, int dx, int dy)
{
	connect->msize = msize;
	connect->psize = GOP_MIN(psize, connect->maxpacket);
	/*
	 * on veut une taille fixe dans le transfert de type matrix donc
	 * psize est < 0
	 */
	if (!flag)
		connect->psize = -1 * psize;

	connect->datatype = datatype;

	gop_struct_to_header(connect);

	if (gop_header_write(connect) != GOP_OK)
		return (GOP_KO);

	if (gop_data_section_write(connect, data, flag, npix_x, dx, dy) != GOP_OK)
		return (GOP_KO);

	return (GOP_OK);
}


int 
gop_write_command (struct gop_connect *connect, char *cmd)
{
	connect->header.header_type = GOP_HEADER_STD;
	return(gop_write(connect, cmd, strlen(cmd)+1, connect->maxpacket,
			GOP_CHAR));

}


int 
gop_write_acknowledgement (struct gop_connect *connect, char *state, char *texte)
{
	int	msize;
	int	psize;

	connect->header.header_type = GOP_HEADER_STD;
	strcpy(connect->class, GOP_CLASS_ACKN);
	strcpy(connect->stat, state);

	strcpy(connect->to, connect->header.from);
	strcpy(connect->from, connect->header.to);

        if (texte == (char *) NULL){
		msize = 0;
	} else {
		msize = strlen(texte)+1;
	}
	psize = connect->maxpacket;

	if(gop_write(connect, texte, msize, psize, GOP_CHAR) != GOP_OK)
		return(GOP_KO);

	return(GOP_OK);
}



int 
gop_write_end_of_message (struct gop_connect *connect, char *texte)
{
	/*
	 * par surete du EOM on change quelques parametres de communication
	 * ainsi la structure est sauvee en debut de fonction de retournee
	 * dans son etat d'origine
	 */

	int	status;

	struct gop_connect *tempo;

	tempo = (struct gop_connect *) alloca(sizeof(struct gop_connect));
	memcpy(tempo, connect, sizeof(struct gop_connect));

	gop_set_class(connect, GOP_CLASS_DATA);
	connect->hsync = GOP_FALSE;
	connect->dsync = GOP_FALSE;
	connect->cont  = GOP_FALSE;
	connect->stamp = GOP_TRUE;
	connect->header.header_type = GOP_HEADER_END;
	connect->datatype = GOP_CHAR;

	if (connect->mode >= GOP_CONNECTION) {
		gop_printf("gop: [%8s] -> [%8s] ++++++ gop_write_end_of_message() sur cd=%d\n", 
			connect->my_name, connect->his_name, 
			connect->port, connect->cd);
	}

	status = gop_write(connect, texte, strlen(texte)+1, connect->maxpacket,
			GOP_CHAR);


	memcpy(connect, tempo, sizeof(struct gop_connect));

	return(status);

}


static int 
gop_forward_core (struct gop_connect *from_connect, struct gop_connect *to_connect, int timeout, struct gop_list *srv_list)
{
	struct gop_list input_list, output_list;
	struct gop_connect 	*destination;
	struct gop_connect 	*sender;
	int			i;
	char			*buf=NULL;

	int			continuation_flag;

	int	to_psize;
	int	not_found;

	/*
	 * transmission du header et de la SDD. On a deja lu le header dans
	 * from_connect mais pas encore fait l'acknowledge vers from_connect
	 */

	if (gop_header_forward(from_connect, to_connect) != GOP_OK)
		return (GOP_KO);

	if (gop_data_section_forward(from_connect, to_connect) != GOP_OK)
		return (GOP_KO);

	/*
	 * On transmet les messages suivants uniquement si le message courant
	 * a le flag de continuation Dans ce cas on peut ne peut etre en
	 * attente que de l'un des deux partenaires. Par contre on ne sait
	 * pas dans quel sens part le message suivant. On effectue donc un
	 * select() sur les deux.
	 * 
	 * On accepte toutefois les message destiné a des serveurs desquels on
	 * n'attend pas de reponse (typiquement logbook ou serveur d'etat)
	 */

	input_list.nb = 2;
	input_list.gop[0] = from_connect;
	input_list.gop[1] = to_connect;
	input_list.timeout = timeout;

	continuation_flag = from_connect->cont;

	while (continuation_flag == GOP_TRUE) {
		if(from_connect->mode >= GOP_POLL){
			gop_printf("gop: [%8s] <> [--POLL--] Channels cd=%d ([%8s]) and cd=%d ([%8s]) booked (connect->cont=1)\n", 
				from_connect->my_name, from_connect->cd, from_connect->his_name, 
				to_connect->cd, to_connect->his_name);
		}
		/*
		 * on restaure le handler car il est mis dans
		 * gop_select_active_channel()
		 */
		gop_restore_handler(SIGURG);
		do {
			gop_errno = GOP_OK;
			gop_select_active_channel(&input_list, &output_list);
		} while ((gop_errno == GOP_TIMEOUT || output_list.nb==0) &&
			!(gop_errno != GOP_OK && gop_errno != GOP_TIMEOUT));
		
		if(gop_errno != GOP_OK)
			return (GOP_KO);
		/*
		 * si on a un acces simultane des 2 cotes
		 */
		if (output_list.nb > 1) {
			gop_errno = GOP_BLOCKING;
			return (GOP_KO);
		}

		sender = output_list.gop[0];

		gop_connect_client = sender;
		gop_connect_client->opcrt = GOP_READ;
		gop_connect_client->side = GOP_TRANSMIT_SIDE;
		/*
		 * initialisation pour le handler
		 */
		gop_init_handler(SIGURG);

		/*
		 * determination du destinataire: on regarde si le
		 * destinataire est bien le correspondant sur lequel on
		 * bloque la communication. Si ce n'est pas le cas, le
		 * message est affiche a l'ecran (s'il est de type GOP_CHAR).
		 * Cette partie est a develloper, ce comportement est
		 * momentane...
		 */

		if (sender == from_connect){
			destination = to_connect;
		} else {
			destination = from_connect;
		}
		/*
		 * lecture du premier byte, si c'est un EOM, ce n'est pas
		 * considere comme une erreur et on forward naturellement le
		 * message
		 */
		if (gop_h_read(sender) != GOP_OK) {
			if (gop_errno == GOP_END_OF_MESSAGE)
				gop_errno = GOP_OK;
			else
				return (GOP_KO);
		}
		/*
		 * lecture et transfert du header
		 */
		if (gop_header_read(sender) != GOP_OK)
			return (GOP_KO);

		memcpy((char *) &destination->header,
		       (char *) &sender->header,
		       sizeof(struct gop_header));

		/*
		 * psize peut etre different entre les deux cotes !!!
		 * Attention peut etre d'autre parametres sont a echanger de la
		 * meme maniere (xdr, ...)
		 */
		to_psize = atoi(destination->header.psize);
		destination->psize = destination->maxpacket;
		if(to_psize < 0)
			destination->psize = to_psize;
		sprintf(destination->header.psize, "%10d", destination->psize);

		if (destination->need_xdr && !(atoi(destination->header.datatype)==GOP_CHAR || atoi(destination->header.datatype)==GOP_STRUCT)) 
			strcpy(destination->header.xdr, GOP_STR_TRUE);
		else
			strcpy(destination->header.xdr, GOP_STR_FALSE);

		gop_header_to_struct(sender, &(sender->header));
		gop_set_cont(destination, sender->cont);

		/* test du bon destinataire */

		if (strcmp(sender->header.to, destination->his_name) != 0) {
			/*
			 * c'est un autre destinataire on determine si le
			 * destinataire est dans la liste des des serveur
			 * possible.
			 */
			if (from_connect->mode >= GOP_HEADER) {
				gop_printf("gop: [%8s] <> [--------] \t select possible server destination from >%s<:\n",
					   sender->my_name, sender->my_name);

				for (i = 0; i < srv_list->nb; i++) {
					gop_printf("gop: [%8s] <> [--------] \t\t %d) to: >%s<  cd=%d\n",
						   sender->my_name, i,
						   srv_list->gop[i]->his_name, srv_list->gop[i]->cd);
				}
			}
			not_found = GOP_TRUE;
			for (i = 0; i < srv_list->nb; i++) {
				if (strcmp(sender->header.to, srv_list->gop[i]->his_name) == 0) {
					/* c'est le bon destinataire */

					if (from_connect->mode >= GOP_HEADER) {
						gop_printf("gop: [%8s] <> [--------] \t\t ok, destination is >%s< cd=%d\n", 
							sender->my_name,  
							srv_list->gop[i]->his_name, srv_list->gop[i]->cd);
					}

					memcpy(&srv_list->gop[i]->header, &destination->header, sizeof(struct gop_header));

					if (gop_header_write(srv_list->gop[i]) != GOP_OK)
						return (GOP_KO);
					/*
					 * forward de la SDD
					 */

					if (gop_data_section_forward(sender, srv_list->gop[i]) != GOP_OK)
						return (GOP_KO);
					not_found = GOP_FALSE;
				}
			}
			/*
			 * si on ne trouve pas le destinataire dans la liste
			 */
			if (not_found) {
				gop_printf("gop: [%8s] <> [--------] le message n'est pas pour le destinataire mais pour [%8s], donc affichage (si ASCII):\n",
					   sender->my_name, sender->header.to);

				if (buf != (char *) NULL)
					free(buf);
				buf = (char *) alloca(sender->msize);
				if (buf <= (char *) NULL) {
					gop_errno = GOP_ALLOC;
					return (GOP_KO);
				}
				if (gop_data_section_read(sender, buf, sender->msize, GOP_TRUE, 0, 0, 0) <= GOP_OK) {
					return (GOP_KO);
				}
				if (sender->datatype == GOP_CHAR) {
					printf("%s\n", buf);
				}
			}
			/*
			 * On emet un message d'erreur si le message a un
			 * flag de continuation. IL N'Y A PAS DE RECURSIVITE
			 * DANS CE CAS et donc c'est invalide.
			 * en fait c'est valide pour les message d'info passant durant
			 * la reservation de connection. Donc en oublie
			 */
/***
			if (sender->cont) {
				gop_printf("gop: [%8s] -> [%8s] Attention le message destiné au server [%8s] a le flag de continuation a TRUE. Ce cas n'est pas géré. (Mais on continue)\n",
					   sender->my_name, sender->header.to, sender->header.to);
			}
***/
			/*
			 * comme on etait en reservation de cannal, on se
			 * remet dans le meme etat
			 */
			continuation_flag = GOP_TRUE;
		} else {
			/*
			 * on a trouve le bon destinataire
			 */

			if (gop_header_write(destination) != GOP_OK)
				return (GOP_KO);
			/*
			 * forward de la SDD
			 */

			if (gop_data_section_forward(sender, destination) != GOP_OK)
				return (GOP_KO);
			continuation_flag = sender->cont;

		}
	}

	/* si une collision est survenue durant 
	   le forward on l'envoie maintenant */
	   
	if (memo_action) {
		if (memo_connect.mode >= GOP_HEADER)
			gop_printf("gop: [%8s] -> [%8s] \t **** EXECUTION DIFFEREE DU A UNE COLISISION*** \n",
			       memo_connect.my_name, memo_connect.his_name);

		/* on recherche la structure de connection du destinataire */

		if (memo_connect.mode >= GOP_HEADER) {
			gop_printf("gop: [%8s] <> [--------] \t select possible server destination from >%s<:\n",
				   memo_connect.my_name, memo_connect.my_name);

			for (i = 0; i < srv_list->nb; i++) {
				gop_printf("gop: [%8s] <> [--------] \t\t %d) to: >%s<  cd=%d\n",
					   memo_connect.my_name, i,
					   srv_list->gop[i]->his_name, srv_list->gop[i]->cd);
			}
		}
		not_found = GOP_TRUE;
		for (i = 0; i < srv_list->nb; i++) {
			if (strcmp(memo_connect.header.to, srv_list->gop[i]->his_name) == 0) {
				/* c'est le bon destinataire */

				if (memo_connect.mode >= GOP_HEADER) {
					gop_printf("gop: [%8s] <> [--------] \t\t ok, destination is >%s< cd=%d\n",
						   memo_connect.my_name,
						   srv_list->gop[i]->his_name, srv_list->gop[i]->cd);
				}
/**
				memcpy(&memo_connect, &srv_list->gop[i]->header, sizeof(struct gop_header));
**/
				memo_connect.cd = srv_list->gop[i]->cd;

				not_found = GOP_FALSE;
			}
		}
		/*
		 * si on ne trouve pas le destinataire dans la liste
		 */
		if (not_found) {
			gop_printf("gop: [%8s] <> [--------] le message n'est pas pour le destinataire mais pour [%8s], donc affichage (si ASCII):\n",
				   memo_connect.my_name, memo_connect.header.to);

			if (memo_connect.datatype == GOP_CHAR) {
				printf("%s\n", memo_data_section);
			}
		} else {
			if (gop_write(&memo_connect, memo_data_section, memo_connect.msize,
		   		memo_connect.maxpacket, memo_connect.datatype) != GOP_OK)
				return (GOP_KO);
		}
		memo_action = GOP_FALSE;
		if (memo_connect.mode >= GOP_HEADER)
			gop_printf("gop: [%8s] -> [%8s] \t **** EXECUTION DIFFEREE DU A UNE COLISISION FIN*** \n",
			       memo_connect.my_name, memo_connect.his_name);
	}

	return (GOP_OK);
}


static int 
gop_forward_locked_core (struct gop_connect *from_connect, struct gop_connect *to_connect, int timeout, struct gop_list *srv_list)
{
#pragma warning(disable:869)  // parameter "timeout" was never referenced
	//struct gop_list 	input_list;
	struct gop_connect 	*destination;
	struct gop_connect 	*sender;
	struct gop_connect 	*dummy;
	int			i;
	char			*buf=NULL;

	int			continuation_flag;

	int	to_psize;
	int	not_found;

	/*
	 * transmission du header et de la SDD. On a deja lu le header dans
	 * from_connect mais pas encore fait l'acknowledge vers from_connect
	 */

	if (gop_header_forward(from_connect, to_connect) != GOP_OK)
		return (GOP_KO);

	if (gop_data_section_forward(from_connect, to_connect) != GOP_OK)
		return (GOP_KO);

	/*
	 * On transmet les messages suivants uniquement si le message courant
	 * a le flag de continuation. Dans ce cas on attend sur le destinataire
	 * 
	 * On accepte toutefois les message destiné a des serveurs desquels on
	 * n'attend pas de reponse (typiquement logbook ou serveur d'etat)
	 */

	//input_list.nb = 2;
	//input_list.gop[0] = from_connect;
	//input_list.gop[1] = to_connect;
	//input_list.timeout = timeout;

	continuation_flag = from_connect->cont;
	
	/*
	 * nouveau partenaires
	 */
	 
	sender      = to_connect;
	destination = from_connect;

	while (continuation_flag == GOP_TRUE) {
		if(from_connect->mode >= GOP_POLL){
			gop_printf("gop: [%8s] <- [%8s] Channels cd=%d ([%8s]) and cd=%d ([%8s]) booked (connect->cont=1)\n", 
				destination->his_name, sender->his_name, destination->cd, destination->his_name, 
				sender->cd, sender->his_name);
		}
		/*
		 * initialisation pour le handler
		 */
		gop_connect_client = sender;
		gop_connect_client->opcrt = GOP_READ;
		gop_connect_client->side = GOP_TRANSMIT_SIDE;

		/*
		 * lecture du premier byte, si c'est un EOM, ce n'est pas
		 * considere comme une erreur et on forward naturellement le
		 * message
		 */
		if (gop_h_read(sender) != GOP_OK) {
			if (gop_errno == GOP_END_OF_MESSAGE)
				gop_errno = GOP_OK;
			else
				return (GOP_KO);
		}
		/*
		 * lecture et transfert du header
		 */
		if (gop_header_read(sender) != GOP_OK)
			return (GOP_KO);

		memcpy((char *) &destination->header,
		       (char *) &sender->header,
		       sizeof(struct gop_header));

		/*
		 * psize peut etre different entre les deux cotes !!!
		 * Attention peut etre d'autre parametres sont a echanger de la
		 * meme maniere (xdr, ...)
		 */
		to_psize = atoi(destination->header.psize);
		destination->psize = destination->maxpacket;
		if(to_psize < 0)
			destination->psize = to_psize;
		sprintf(destination->header.psize, "%10d", destination->psize);

		if (destination->need_xdr && !(atoi(destination->header.datatype)==GOP_CHAR || atoi(destination->header.datatype)==GOP_STRUCT)) 
			strcpy(destination->header.xdr, GOP_STR_TRUE);
		else
			strcpy(destination->header.xdr, GOP_STR_FALSE);

		gop_header_to_struct(sender, &(sender->header));
		gop_set_cont(destination, sender->cont);

		/* test du bon destinataire */

		if (strcmp(sender->header.to, destination->his_name) != 0) {
			/*
			 * c'est un autre destinataire on determine si le
			 * destinataire est dans la liste des des serveur
			 * possible.
			 */
			if (from_connect->mode >= GOP_HEADER) {
				gop_printf("gop: [%8s] <> [--------] \t select possible server destination from >%s<:\n",
					   sender->my_name, sender->my_name);

				for (i = 0; i < srv_list->nb; i++) {
					gop_printf("gop: [%8s] <> [--------] \t\t %d) to: >%s<  cd=%d\n",
						   sender->my_name, i,
						   srv_list->gop[i]->his_name, srv_list->gop[i]->cd);
				}
			}
			not_found = GOP_TRUE;
			for (i = 0; i < srv_list->nb; i++) {
				if (strcmp(sender->header.to, srv_list->gop[i]->his_name) == 0) {
					/* c'est le bon destinataire */

					if (from_connect->mode >= GOP_HEADER) {
						gop_printf("gop: [%8s] <> [--------] \t\t ok, destination is >%s< cd=%d\n", 
							sender->my_name,  
							srv_list->gop[i]->his_name, srv_list->gop[i]->cd);
					}

					memcpy(&srv_list->gop[i]->header, &destination->header, sizeof(struct gop_header));

					if (gop_header_write(srv_list->gop[i]) != GOP_OK)
						return (GOP_KO);
					/*
					 * forward de la SDD
					 */

					if (gop_data_section_forward(sender, srv_list->gop[i]) != GOP_OK)
						return (GOP_KO);
					not_found = GOP_FALSE;
				}
			}
			/*
			 * si on ne trouve pas le destinataire dans la liste
			 */
			if (not_found) {
				gop_printf("gop: [%8s] <> [--------] le message n'est pas pour le destinataire mais pour [%8s], donc affichage (si ASCII):\n",
					   sender->my_name, sender->header.to);

				if (buf != (char *) NULL)
					free(buf);
				buf = (char *) alloca(sender->msize);
				if (buf <= (char *) NULL) {
					gop_errno = GOP_ALLOC;
					return (GOP_KO);
				}
				if (gop_data_section_read(sender, buf, sender->msize, GOP_TRUE, 0, 0, 0) <= GOP_OK) {
					return (GOP_KO);
				}
				if (sender->datatype == GOP_CHAR) {
					printf("%s\n", buf);
				}
			}
			/*
			 * comme on etait en reservation de cannal, on se
			 * remet dans le meme etat
			 */
			continuation_flag = GOP_TRUE;
		} else {
			/*
			 * on a trouve le bon destinataire
			 */

			if (gop_header_write(destination) != GOP_OK)
				return (GOP_KO);
			/*
			 * forward de la SDD
			 */

			if (gop_data_section_forward(sender, destination) != GOP_OK)
				return (GOP_KO);
			continuation_flag = sender->cont;
			/*
			 * on inverse les partenaires
			 */
			 
			 dummy       = sender;
			 sender      = destination;
			 destination = dummy;

		}
	}

	/* si une collision est survenue durant 
	   le forward on l'envoie maintenant */
	   
	if (memo_action) {
		if (memo_connect.mode >= GOP_HEADER)
			gop_printf("gop: [%8s] -> [%8s] \t **** EXECUTION DIFFEREE DU A UNE COLISISION*** \n",
			       memo_connect.my_name, memo_connect.his_name);

		/* on recherche la structure de connection du destinataire */

		if (memo_connect.mode >= GOP_HEADER) {
			gop_printf("gop: [%8s] <> [--------] \t select possible server destination from >%s<:\n",
				   memo_connect.my_name, memo_connect.my_name);

			for (i = 0; i < srv_list->nb; i++) {
				gop_printf("gop: [%8s] <> [--------] \t\t %d) to: >%s<  cd=%d\n",
					   memo_connect.my_name, i,
					   srv_list->gop[i]->his_name, srv_list->gop[i]->cd);
			}
		}
		not_found = GOP_TRUE;
		for (i = 0; i < srv_list->nb; i++) {
			if (strcmp(memo_connect.header.to, srv_list->gop[i]->his_name) == 0) {
				/* c'est le bon destinataire */

				if (memo_connect.mode >= GOP_HEADER) {
					gop_printf("gop: [%8s] <> [--------] \t\t ok, destination is >%s< cd=%d\n",
						   memo_connect.my_name,
						   srv_list->gop[i]->his_name, srv_list->gop[i]->cd);
				}
/**
				memcpy(&memo_connect, &srv_list->gop[i]->header, sizeof(struct gop_header));
**/
				memo_connect.cd = srv_list->gop[i]->cd;

				not_found = GOP_FALSE;
			}
		}
		/*
		 * si on ne trouve pas le destinataire dans la liste
		 */
		if (not_found) {
			gop_printf("gop: [%8s] <> [--------] le message n'est pas pour le destinataire mais pour [%8s], donc affichage (si ASCII):\n",
				   memo_connect.my_name, memo_connect.header.to);

			if (memo_connect.datatype == GOP_CHAR) {
				printf("%s\n", memo_data_section);
			}
		} else {
			if (gop_write(&memo_connect, memo_data_section, memo_connect.msize,
		   		memo_connect.maxpacket, memo_connect.datatype) != GOP_OK)
				return (GOP_KO);
		}
		memo_action = GOP_FALSE;
		if (memo_connect.mode >= GOP_HEADER)
			gop_printf("gop: [%8s] -> [%8s] \t **** EXECUTION DIFFEREE DU A UNE COLISISION FIN*** \n",
			       memo_connect.my_name, memo_connect.his_name);
	}

	return (GOP_OK);
}


int 
gop_forward (struct gop_connect *from_connect, struct gop_connect *to_connect, int timeout, struct gop_list *srv_list)
{
	int             status;

	/*
	 * initialisation pour le handler
	 */
	gop_connect_client = from_connect;
	/*
	 * installation du handler specifique + handler user
	 */
	gop_init_handler(SIGINT);
	gop_init_handler(SIGURG);
	gop_init_handler(SIGPIPE);
	gop_init_handler(SIGHUP);

	status = gop_forward_core(from_connect, to_connect, timeout, srv_list);

	/*
	 * re-installation du handler user
	 */
	gop_restore_handler(SIGINT);
	gop_restore_handler(SIGURG);
	gop_restore_handler(SIGPIPE);
	gop_restore_handler(SIGHUP);
	return (status);

}

int 
gop_forward_locked (struct gop_connect *from_connect, struct gop_connect *to_connect, 
		int timeout, struct gop_list *srv_list)
{
	int             status;

	/*
	 * initialisation pour le handler
	 */
	gop_connect_client = from_connect;
	/*
	 * installation du handler specifique + handler user
	 */
	gop_init_handler(SIGINT);
	gop_init_handler(SIGURG);
	gop_init_handler(SIGPIPE);
	gop_init_handler(SIGHUP);

	status = gop_forward_locked_core(from_connect, to_connect, timeout, srv_list);

	/*
	 * re-installation du handler user
	 */
	gop_restore_handler(SIGINT);
	gop_restore_handler(SIGURG);
	gop_restore_handler(SIGPIPE);
	gop_restore_handler(SIGHUP);
	return (status);

}


//void 
//gop_forward_memo_side (struct gop_connect *from_connect, struct gop_connect *to_connect)
//
//{
//	/*
//	 * memo de la structure de connection courante
//	 */
//	gop_connect_client = from_connect;
//}
/**********************************************************************/



void 
gop_set_type (struct gop_connect *connect, int type)
{
	connect->type = type;
}


void 
gop_set_name (struct gop_connect *connect, char *name)
{
	if(name == (char *) NULL)
		return;
	strcpy(connect->name, name);
	*(connect->name+sizeof(connect->name)-1) = (char) 0;
}


void 
gop_set_port (struct gop_connect *connect, int port)
{
	connect->port = port;
}


void 
gop_set_maxpacket (struct gop_connect *connect, int maxpacket)
{
	connect->maxpacket = maxpacket;
}


void 
gop_set_class (struct gop_connect *connect, char *class)
{
	if(class == (char *) NULL)
		return;
	strcpy(connect->class, class);
	*(connect->class+sizeof(connect->class)-1) = (char) 0;
}


void 
gop_set_from (struct gop_connect *connect, char *from)
{
	if(from == (char *) NULL)
		return;
	if(strlen(from) > 8)
		*(from+8) = (char) 0;
	sprintf(connect->from, "%8s", from);
}


void 
gop_set_to (struct gop_connect *connect, char *to)
{
	if(to == (char *) NULL)
		return;
	if(strlen(to) > 8)
		*(to+8) = (char) 0;
	sprintf(connect->to, "%8s", to);
}


void 
gop_set_my_name (struct gop_connect *connect, char *my_name)
{
	if(my_name == (char *) NULL)
		return;
	if(strlen(my_name) > 8)
		*(my_name+8) = (char) 0;
	sprintf(connect->my_name, "%8s", my_name);
}


void 
gop_set_his_name (struct gop_connect *connect, char *his_name)
{
	if(his_name == (char *) NULL)
		return;
	if(strlen(his_name) > 8)
		*(his_name+8) = (char) 0;
	sprintf(connect->his_name, "%8s", his_name);
}


void 
gop_set_msize (struct gop_connect *connect, int msize)
{
	connect->msize = msize;
}


void 
gop_set_psize (struct gop_connect *connect, int psize)
{
	connect->psize = psize;
}


void 
gop_set_cont (struct gop_connect *connect, int cont)
{
	connect->cont = cont!=0;
}


void 
gop_set_stamp (struct gop_connect *connect, int stamp)
{
	connect->stamp = stamp!=0;
}


void 
gop_set_hsync (struct gop_connect *connect, int hsync)
{
	connect->hsync = hsync!=0;
}


void 
gop_set_dsync (struct gop_connect *connect, int dsync)
{
	connect->dsync = dsync!=0;
}


void 
gop_set_stat (struct gop_connect *connect, char *stat)
{
	if(stat == (char *) NULL)
		return;
	strcpy(connect->stat, stat);
	*(connect->stat+sizeof(connect->stat)-1) = (char) 0;
}


void 
gop_set_mode (struct gop_connect *connect, int mode)
{
	connect->mode = mode;
}


void 
gop_set_datatype (struct gop_connect *connect, int datatype)
{
	connect->datatype = datatype;
}


void 
gop_set_timeout (struct gop_connect *connect, int timeout)
{
	connect->timeout = timeout;
}


void 
gop_set_side (struct gop_connect *connect, int side)
{
	connect->side = side;
}


/**********************************************************************/



int 
gop_get_type (struct gop_connect *connect)
{
	return(connect->type);
}


char *
gop_get_name (struct gop_connect *connect)
{
	return(connect->name);
}


char *
gop_get_my_name (struct gop_connect *connect)
{
	return(connect->my_name);
}


char *
gop_get_his_name (struct gop_connect *connect)
{
	return(connect->his_name);
}


int 
gop_get_port (struct gop_connect *connect)
{
	return(connect->port);
}


int 
gop_get_maxpacket (struct gop_connect *connect)
{
	return(connect->maxpacket);
}


char *
gop_get_class (struct gop_connect *connect)
{
	return(connect->class);
}


char *
gop_get_from (struct gop_connect *connect)
{
	return(connect->from);
}


char *
gop_get_to (struct gop_connect *connect)
{
	return(connect->to);
}


int 
gop_get_msize (struct gop_connect *connect)
{
	return(connect->msize);
}


int 
gop_get_psize (struct gop_connect *connect)
{
	return(connect->psize);
}


int 
gop_get_cont (struct gop_connect *connect)
{
	return(connect->cont);
}


int 
gop_get_stamp (struct gop_connect *connect)
{
	return(connect->stamp);
}


int 
gop_get_hsync (struct gop_connect *connect)
{
	return(connect->hsync);
}


int 
gop_get_dsync (struct gop_connect *connect)
{
	return(connect->dsync);
}


char *
gop_get_stat (struct gop_connect *connect)
{
	return(connect->stat);
}


int 
gop_get_mode (struct gop_connect *connect)
{
	return(connect->mode);
}


int 
gop_get_datatype (struct gop_connect *connect)
{
	return(connect->datatype);
}


int 
gop_get_timeout (struct gop_connect *connect)
{
	return(connect->timeout);
}


int 
gop_get_side (struct gop_connect *connect)
{
	return(connect->side);
}


int 
gop_get_cd (struct gop_connect *connect)
{
	return(connect->cd);
}

int 
gop_get_cd_init (struct gop_connect *connect)
{
	return(connect->cd_init);
}

/**********************************************************************/


void 
gop_init_server_socket (struct gop_connect *connect, char *my_name, int port, int maxpacket, int mode, int timeout)
{
	gop_set_hsync(connect, GOP_ASYNCHRO);
	gop_set_dsync(connect, GOP_ASYNCHRO);
	gop_set_type(connect, GOP_SOCKET);
	gop_set_my_name(connect, my_name);
	gop_set_port(connect, port);
	gop_set_maxpacket(connect, maxpacket);
	gop_set_mode(connect, mode);
	gop_set_timeout(connect, timeout);
}

void 
gop_init_client_socket (struct gop_connect *connect, char *my_name, char *host, int port, int maxpacket, int mode, int timeout)
{
	gop_set_hsync(connect, GOP_ASYNCHRO);
	gop_set_dsync(connect, GOP_ASYNCHRO);
	gop_set_type(connect, GOP_SOCKET);
	gop_set_my_name(connect, my_name);
	gop_set_name(connect, host);
	gop_set_port(connect, port);
	gop_set_maxpacket(connect, maxpacket);
	gop_set_mode(connect, mode);
	gop_set_timeout(connect, timeout);
}


void 
gop_init_server_socket_unix (struct gop_connect *connect, char *my_name, char *name, int maxpacket, int mode, int timeout)
{
	gop_set_hsync(connect, GOP_ASYNCHRO);
	gop_set_dsync(connect, GOP_ASYNCHRO);
	gop_set_type(connect, GOP_SOCKET_UNIX);
	gop_set_my_name(connect, my_name);
	gop_set_name(connect, name);
	gop_set_maxpacket(connect, maxpacket);
	gop_set_mode(connect, mode);
	gop_set_timeout(connect, timeout);
}


void 
gop_init_client_socket_unix (struct gop_connect *connect, char *my_name, char *name, int maxpacket, int mode, int timeout)
{
	gop_set_hsync(connect, GOP_ASYNCHRO);
	gop_set_dsync(connect, GOP_ASYNCHRO);
	gop_set_type(connect, GOP_SOCKET_UNIX);
	gop_set_my_name(connect, my_name);
	gop_set_name(connect, name);
	gop_set_maxpacket(connect, maxpacket);
	gop_set_mode(connect, mode);
	gop_set_timeout(connect, timeout);
}





