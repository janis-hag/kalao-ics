/**

    _/_/_/_/_/ _/_/_/_/_/ _/      _/ _/_/_/_/_/ _/_/_/_/_/ _/_/_/_/_/
   _/         _/      _/ _/      _/ _/         _/      _/ _/      _/
  _/_/_/_/_/ _/_/_/_/_/ _/      _/ _/  _/_/_/ _/      _/ _/_/_/_/_/
         _/ _/    _/     _/  _/   _/      _/ _/      _/ _/
_/_/_/_/_/ _/      _/     _/     _/_/_/_/_/ _/_/_/_/_/ _/

Librarie pour l'acces simplifie aux serveurs gop de type ASCII.

**/

/*
 * La principale différence de cette librarie sur libgop est l'emploi d'un
 * "channel identifier" (CI) de type numérique, plutot qu'un "channel
 * descripteur" (cd) de type pointeur sur structure.
 *
 * Ainsi  les appels aux fonctions se font en passant une simple valeur
 * numerique, les structures sont allouées dans la librarie. Les appels sont
 * simplifiés et il existe uniquement 6 fonctions principales:
 *
 * - srvg_connect():	pour se connecter sur un serveur
 *
 * - srvg_disconnect():	pour se déconnecter d'un serveur
 *
 * - srvg_write():	écriture (envoi d'une commande par exemple)
 *
 * - srvg_read():	lecture
 *
 * - en cas d'erreur, le texte du message d'erreur se récupère avec
 * srvg_get_error_string()
 *
 * - srvg_verbose():	pour changer le mode de verbosité de gop.
 *
 * Pour permettre le travail avec cette librarie, le serveur doit absolument
 * pouvoir repondre a la commande "/test" et renvoyer un écho (max 8
 * caractères)
 *
 * Cette librarie permet d'accéder un serveur existant, mais peut aussi le
 * lancer s'il n'existe pas. Dans ce cas, le serveur doit avoir la
 * fonctionalité suivante:
 *
 * - Connection en mode MASTER (option -M) c'est a dire le serveur lancé avec
 * cette option fait le connect() (comme le fait un client traditionel) car
 * la librarie fait le accept(). Cette technique permet d'éviter les
 * problèmes de synchronisations. Une fois lancé le serveur retrouve un mode
 * de fonctionnement normal et fait uniquement des accept() pour de nouveaux
 * clients.
 *
 */

#include <stdio.h>
#include <unistd.h>
#include <malloc.h>
#include <errno.h>
#include <string.h>

#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>

#include <gop.h>
#include <srvgop.h>

#ifdef USE_STRERROR
#    define my_strerror(x)  strerror(x)
#else
     extern char           *sys_errlist[];
#    define my_strerror(x)  sys_errlist[x]
#endif

/*
 * functions prototypes pour les statics
 */
static struct gop_connect *
srvg_alloc_connect_structure(char *client_name, char *socket_name, int port, char *host, int verbose);

static int
srvg_run_server(struct gop_connect *connect, char *server_command);

static int
srvg_test_communication(struct gop_connect * connect);

static int
srvg_add_connect_structure(struct gop_connect * connect, char *socket_name, int port, char *host);

static struct gop_connect *
srvg_get_connect_structure(int ci);

static int
srvg_find_ci(char *socket_name, int port, char *host);

static void
srvg_remove_channel_id(int ci);

/*
 * MESSAGES D'ERREUR
 */

static char     srvg_erreur_string[256];

#define CI_INVALID	"Le <channel_Identifier> donne est invalide"
#define MALLOC_ERR	"Probleme d'allocation memoire"
#define TOO_MANY_CON	"Trop de connections etablies"
#define NO_SERVER	"Pas de serveur present"
#define ARG_INVALID	"Arguments invalides"

/*
 * structure contrôle des connections
 */

struct srvg_list {
	struct gop_connect *connect;	/* structure de connection GOP */
	char           *socket_name;	/* nom du socket (connection Unix) */
	int             port;	/* no du port (connection Internet) */
	char           *host;	/* nom du host (connection Internet) */
};


#define NB_CONNECTION_MAX 100
static
struct srvg_list *list_connect[NB_CONNECTION_MAX] = {
	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
};


/*
 * retourne le message d'erreur courant
 */

char           *
srvg_get_error_string()
{
	return (srvg_erreur_string);
}


int
srvg_get_gop_errno()
{
	return (gop_errno);
}

/*
 * permet de tester si le serveur est en écoute une fois connecté
 */
static int
srvg_test_communication(struct gop_connect *connect)
{
	char            answer[8];
	if (gop_write_command(connect, "/test") != GOP_OK) {
		strcpy(srvg_erreur_string, gop_get_error_str());
		return (GOP_KO);
	}
	if (gop_read(connect, answer, sizeof(answer)) < GOP_OK) {
		gop_handle_eom(connect, NULL);
		strcpy(srvg_erreur_string, gop_get_error_str());
		return (GOP_KO);
	}
	return (GOP_OK);
}

/*
 * alloue une structure de connection et initialise les parametres de
 * connection
 */

static struct gop_connect *
srvg_alloc_connect_structure(char *client_name,	/* symbolic name of the
						 * client */
			     char *socket_name,	/* socket name four Unix
						 * connection */
			     int port,	/* port number for Internet
					 * connection */
			     char *host,	/* hoat name for Internet
						 * connection */
			     int verbose /* GOP verbosity level */ )
{
	struct gop_connect *connect;

	connect = (struct gop_connect *) gop_alloc_connect_structure();

	if (connect == (struct gop_connect *) NULL) {
		strcpy(srvg_erreur_string, MALLOC_ERR);
		return ((struct gop_connect *) NULL);
	}
	/* mis en place des defauts */
	if (port != 0) {
		gop_set_type(connect, GOP_SOCKET);
		gop_set_port(connect, port);
		if (host == (char *) NULL || *host == 0)
			gop_set_name(connect, "localhost");
		else
			gop_set_name(connect, host);

	} else {
		gop_set_type(connect, GOP_SOCKET_UNIX);
		if (socket_name != (char *) NULL)
			gop_set_name(connect, socket_name);
	}

	gop_set_my_name(connect, client_name);
	gop_set_mode(connect, verbose);

	gop_set_maxpacket(connect, 16384);
	gop_set_timeout(connect, 0);
	gop_set_class(connect, GOP_CLASS_COMD);
	gop_set_stamp(connect, GOP_TRUE);
	gop_set_stat(connect, GOP_STAT_OPOK);
	gop_set_hsync(connect, GOP_SYNCHRO);
	gop_set_dsync(connect, GOP_SYNCHRO);
	return (connect);
}

/*
 * Lance le serveur (commande: <server_command>) avec l'option -M et
 * initialise la communication client-serveur avec la structure <connect>. La
 * fonction attend la connection du serveur (sur un accept())
 */
static int
srvg_run_server(struct gop_connect *connect, char *server_command)
{
	char            cmd_name[256];
	char		host_name[80];
	int		local;
	int		addr_src=0;
	int		addr_dest=0;
	struct hostent *hinfo_src;
	struct hostent *hinfo_dest;

	gethostname(host_name, sizeof(host_name));

	/*
	 * Attention pour savoir si on travaille en local,
	 * on compare les adresse IP
	 */

	if ((hinfo_src = gethostbyname(host_name)) != NULL) {
		addr_src = ((struct in_addr *) (hinfo_src->h_addr))->s_addr;
	}
	if(connect->type == GOP_SOCKET){
		if ((hinfo_dest = gethostbyname(connect->name)) != NULL) {
			addr_dest = ((struct in_addr *) (hinfo_dest->h_addr))->s_addr;
		}
	}
	local = (connect->type == GOP_SOCKET_UNIX ||
		   (addr_src == addr_dest) ||
		   (strcmp(connect->name,"localhost") == 0));

	if (gop_init_connection(connect) != GOP_OK) {
		fflush(stderr);
		sprintf(srvg_erreur_string, "srvg_run_server: gop_init_connection: %s",
			gop_get_error_str());
		return (GOP_KO);
	}
	if(connect->type == GOP_SOCKET_UNIX){
		sprintf(cmd_name, "%s -M -:%s &", server_command, connect->name);
	} else {
		sprintf(cmd_name, "%s -M %d:%s &", server_command, connect->port, host_name);
	}

#ifdef DEBUG
	fprintf(stderr, "Envoi commande: <%s>\n", cmd_name);
#endif				/* DEBUG */
	if(local){
		if (gop_system(cmd_name) == -1) {
			strcpy(srvg_erreur_string, my_strerror(errno));
			return (GOP_KO);
		}
	} else {
		if (gop_system_rsh(cmd_name, connect->name) == -1) {
			strcpy(srvg_erreur_string, my_strerror(errno));
			return (GOP_KO);
		}
	}
	/*
	 * une fois la connection acceptee, on libere la socket initiale car
	 * on ne fais plus d'accept sur cette socket (en aucun cas)
	 */
	if (gop_accept_connection(connect) != GOP_OK) {
		sprintf(srvg_erreur_string, "srvg_run_server: gop_accept_connection: %s",
			gop_get_error_str());
		gop_close_init_connection(connect);
		return (GOP_KO);
	}
	gop_close_init_connection(connect);

	return (GOP_OK);
}

/*
 * Effectue la connection, sur socket de  type Internet si <port> != 0, sinon
 * sur socket de type Unix. Pour la connection Internet <host> est pris par
 * défaut à "LOCALHOST". Pour connection Unix <socket_name> doit etre
 * specifie
 *
 * Si on est déjà connecté, seul un test de connection est effectué et on
 * retourne le <ci> de la connection
 *
 * Retourne le <ci>
 */

int
srvg_connect(char *server_command,	/* name of the unix command to run
					 * server */
	     char *client_name,	/* symbolic name of the client */
	     char *socket_name,	/* socket name four Unix connection */
	     int port,		/* port number for Internet connection */
	     char *host,	/* host name for Internet connection */
	     int verbose, /* GOP verbosity level */
	     int timeout, /* timeout on connection */
	     int hsync, /* header sync 0|1 */
	     int dsync) /* data sync 0|1 */
{

	int             ci;	/* channel identifier */
	struct gop_connect *connect;	/* conenction structure */

	if ((socket_name == (char *) NULL || *socket_name == 0) && port == 0) {
		strcpy(srvg_erreur_string, ARG_INVALID);
		return (GOP_KO);
	}
	ci = srvg_find_ci(socket_name, port, host);

	/*
	 * recuperation de la structure de communication si ci est valide
	 */
	if (ci != GOP_KO) {
		connect = srvg_get_connect_structure(ci);
		if (connect == (struct gop_connect *) NULL) {
			srvg_remove_channel_id(ci);
			ci = GOP_KO;
		}
		gop_set_hsync(connect, hsync);
		gop_set_dsync(connect, dsync);
	}
	/*
	 * test le la communication
	 */
	if (ci != GOP_KO) {
		/*
		 * cas de connection redondante: on est sense etre connecte
		 * mais le serveur peut etre mort. On teste donc la
		 * connection. la structure connect est valide
		 */
		if (srvg_test_communication(connect) == GOP_OK)
			return (ci);
	}
	/*
	 * on est pas connecté (durant cette session) ou on a eu un broken
	 * pipe sur le test de communication. Mais le serveur est peut etre
	 * present. On cree ici la structure connect si besoin.
	 */
	if (ci == GOP_KO) {
		connect = srvg_alloc_connect_structure(client_name,
					  socket_name, port, host, verbose);
		if (connect == (struct gop_connect *) NULL)
			return (GOP_KO);
		gop_set_hsync(connect, hsync);
		gop_set_dsync(connect, dsync);
		ci = srvg_add_connect_structure(connect, socket_name, port, host);
		if (ci == GOP_KO)
			return (GOP_KO);

	}
	if (gop_connection(connect) != GOP_OK) {
		strcpy(srvg_erreur_string, gop_get_error_str());
	} else {
		/*
		 * test de connection si la connection a marche et si OK, on
		 * sort
		 */
		if (srvg_test_communication(connect) == GOP_OK)
			return (ci);
	}
	/*
	 * a ce stade le client n'est pas connectable donc on le lance (si
	 * <server_command> contient quelque chose) en mode master (l'option
	 * -M est rajoutée d'office)
	 */
	if (server_command == (char *) NULL || *server_command == 0) {
		srvg_remove_channel_id(ci);
		strcpy(srvg_erreur_string, NO_SERVER);

		return (GOP_KO);
	}
	gop_set_timeout(connect, timeout);
	if (srvg_run_server(connect, server_command) != GOP_OK) {
		srvg_remove_channel_id(ci);
		return (GOP_KO);
	}
	if (srvg_test_communication(connect) != GOP_OK) {
		srvg_disconnect(ci);
		return (GOP_KO);
	}
	return (ci);
}

/*
 * Déconnection d'un serveur identifié par <ci>, la structure de connection
 * est déallouée
 */

int
srvg_disconnect(int ci)
{
	struct gop_connect *connect;

#ifdef DEBUG
	printf("srvg_disconnect ci=%d\n", ci);
#endif				/* DEBUG */

	connect = srvg_get_connect_structure(ci);
	if (connect == (struct gop_connect *) NULL) {
		strcpy(srvg_erreur_string, CI_INVALID);
		return (GOP_KO);
	}
#ifdef DEBUG
	printf("srvg_write connect=%d\n", (int) &connect);
#endif				/* DEBUG */
	gop_close_connection(connect);
	srvg_remove_channel_id(ci);
	return (GOP_OK);
}

/*
 * Déalloue la structure de connection identifiée par <ci>.
 */

static void
srvg_remove_channel_id(int ci)
{
#ifdef DEBUG
	printf("srvg_remove_channel_id ci=%d\n", ci);
#endif				/* DEBUG */

	free(list_connect[ci]->connect);
	free(list_connect[ci]->socket_name);
	free(list_connect[ci]->host);
	free(list_connect[ci]);
	list_connect[ci] = (struct srvg_list *) NULL;

	return;
}

/*
 * Retourne la structure de connection identifiée par <ci>.
 */

static struct gop_connect *
srvg_get_connect_structure(int ci)
{
#ifdef DEBUG
	printf("srvg_get_connect_structure ci=%d\n", ci);
#endif				/* DEBUG */
	if (ci < 1 || ci > NB_CONNECTION_MAX){
		strcpy(srvg_erreur_string, ARG_INVALID);
		return ((struct gop_connect *) NULL);
	}
	if(list_connect[ci] == (struct srvg_list *) NULL){
		strcpy(srvg_erreur_string, CI_INVALID);
		return ((struct gop_connect *) NULL);
	}
	return (list_connect[ci]->connect);
}

/*
 * recherche le <ci> d'apres <socket_name> ou d'apres  <port> et <host> si
 * <socket_name> n'est pas specifie (NULL ou 0).
 */
static int
srvg_find_ci(char *socket_name, int port, char *host)
{
	int             i;

	if (socket_name == (char *) NULL || *socket_name == 0 || *socket_name == ' ') {
		for (i = 1; i < NB_CONNECTION_MAX; i++) {
			if (list_connect[i] != (struct srvg_list *) NULL) {
				if ((list_connect[i]->port == port) && (strcmp(list_connect[i]->host, host) == 0)) {
					return (i);
				}
			}
		}
	} else {
		for (i = 1; i < NB_CONNECTION_MAX; i++) {
			if (list_connect[i] != (struct srvg_list *) NULL) {
				if (strcmp(list_connect[i]->socket_name, socket_name) == 0) {
					return (i);
				}
			}
		}
	}
	return (GOP_KO);
}

/*
 * rajoute une structure de connection <connect> avec les éléments associés
 * (<socket_name>, <port> et <host>) dans le premier endroit libre de la
 * liste
 */

static int
srvg_add_connect_structure(struct gop_connect * connect, char *socket_name, int port, char *host)
{
	int             i;
#ifdef DEBUG
	printf("srvg_add_connect_structure connect=%d\n", (int) &connect);
#endif				/* DEBUG */
	for (i = 1; i < NB_CONNECTION_MAX; i++) {
		if (list_connect[i] == (struct srvg_list *) NULL) {
			list_connect[i] = (struct srvg_list *) malloc(sizeof(struct srvg_list));
			if (list_connect[i] == (struct srvg_list *) NULL) {
				strcpy(srvg_erreur_string, MALLOC_ERR);
				return (GOP_KO);
			}
			memset(list_connect[i], 0, sizeof(struct srvg_list));
			list_connect[i]->connect = connect;
			if (socket_name != (char *) NULL)
				list_connect[i]->socket_name = (char *) strdup(socket_name);
			list_connect[i]->port = port;
			if (host != (char *) NULL)
				list_connect[i]->host = (char *) strdup(host);
			return (i);
		}
	}
	strcpy(srvg_erreur_string, TOO_MANY_CON);
	return (GOP_KO);
}

/*
 * Ecriture d'une chaine de caractère <str> terminée par le caractère NULL
 * sur le canal <ci>.
 */

int
srvg_write(int ci, char *str)
{
	struct gop_connect *connect;

	connect = srvg_get_connect_structure(ci);
	if (connect == (struct gop_connect *) NULL) {
		strcpy(srvg_erreur_string, CI_INVALID);
		return (GOP_KO);
	}
#ifdef DEBUG
	printf("srvg_write connect=%d\n", (int) &connect);
#endif				/* DEBUG */
	if (gop_write_command(connect, str) != GOP_OK) {
		strcpy(srvg_erreur_string, gop_get_error_str());
		srvg_disconnect(ci);
		return (GOP_KO);
	}
	return (GOP_OK);
}

/*
 * Ecriture d'une chaine de caractère (non affichable) <str> terminée
 * par le caractère NULL sur le canal <ci>.
 */

int
srvg_write_bin(int ci, char *str)
{
	struct gop_connect *connect;

	connect = srvg_get_connect_structure(ci);
	if (connect == (struct gop_connect *) NULL) {
		strcpy(srvg_erreur_string, CI_INVALID);
		return (GOP_KO);
	}
#ifdef DEBUG
	printf("srvg_write connect=%d\n", (int) &connect);
#endif				/* DEBUG */
	connect->header.header_type = GOP_HEADER_STD;
	if ((gop_write(connect, str, strlen(str)+1, connect->maxpacket,
			GOP_STRUCT)) != GOP_OK) {
		strcpy(srvg_erreur_string, gop_get_error_str());
		srvg_disconnect(ci);
		return (GOP_KO);
	}
	return (GOP_OK);
}

/*
 * lecture d'une chaîne de caractère <str> de longueur maximum <sizeofstr>
 * sur le canal <ci>. Rend la longeur de la chaine et le status gop
 * (4caractères) dans <stat>.
 */
int
srvg_read(int ci, char *str, int sizeofstr, char *gop_stat, char *gop_class, int timeout)
{
	struct gop_connect *connect;
	int             ilen;

	connect = srvg_get_connect_structure(ci);
	if (connect == (struct gop_connect *) NULL) {
		strcpy(srvg_erreur_string, CI_INVALID);
		return (GOP_KO);
	}
#ifdef DEBUG
	printf("srvg_write connect=%d\n", (int) &connect);
#endif				/* DEBUG */

	gop_set_timeout(connect, timeout);
	if ((ilen = gop_read(connect, str, sizeofstr)) < GOP_OK) {
		gop_handle_eom(connect, NULL);
		if (gop_errno == GOP_INTERRUPTED_TRANSMISSION) {
			*str = 0;
			ilen = 0;
		} else {
			strcpy(srvg_erreur_string, gop_get_error_str());
			srvg_disconnect(ci);
			gop_set_timeout(connect, 0);
			return (GOP_KO);
		}
	}
	strcpy(gop_stat, gop_get_stat(connect));
	strcpy(gop_class, gop_get_class(connect));
	gop_set_timeout(connect, 0);
	return (ilen);
}

/*
 * Modifie le niveau de verbosité pour le canal <ci>.
 */
int
srvg_verbose(int ci, int verbose)
{
	struct gop_connect *connect;

	connect = srvg_get_connect_structure(ci);
	if (connect == (struct gop_connect *) NULL) {
		strcpy(srvg_erreur_string, CI_INVALID);
		return (GOP_KO);
	}
	gop_set_mode(connect, verbose);
	return (GOP_OK);
}


/*
 * INTERFACE FORTRAN
 */

void
srvg_connect_(char *server_command, char *client_name, char *socket_name, int *port, char *host, int *verbose, int *timeout, int *hsync, int *dsync, int *ci)
{
	*ci = srvg_connect(server_command, client_name, socket_name, *port, host, *verbose, *timeout, *hsync, *dsync);

}

void
srvg_disconnect_(int *ci, int *status)
{
	*status = srvg_disconnect(*ci);
}

void
srvg_write_(int *ci, char *str, int *status)
{
	*status = srvg_write(*ci, str);
}

void
srvg_write_bin_(int *ci, char *str, int *status)
{
	*status = srvg_write_bin(*ci, str);
}

void
srvg_read_(int *ci, char *str, int *sizeofstr, char *gop_stat,
		char *gop_class, int *gop_timeout, int *status)
{
	*status = srvg_read(*ci, str, *sizeofstr, gop_stat, gop_class, *gop_timeout);
	if (*status > 0)
		*status = strlen(str);
}

void
srvg_get_error_string_(char *str, int *ilen)
{
	strcpy(str, srvg_get_error_string());
	*ilen = strlen(str);
}

void
srvg_get_gop_errno_(int *gop_errno)
{
	*gop_errno = srvg_get_gop_errno();
}

void
srvg_verbose_(int *ci, int *verbose, int *status)
{
	*status = srvg_verbose(*ci, *verbose);
}
