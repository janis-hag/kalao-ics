#define _REENTRANT
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <sys/time.h>
#include <string.h>
#include <pthread.h>

#include <gop.h>
#include <logbook.h>


static struct gop_connect *connect_inet;
static struct gop_connect *connect_inet_master;
static struct gop_list    input_list;

static int	cpt=0;
static char	my_name[16];
static int	log_book_status = -1;

struct	pth_struct_def {
	struct gop_connect * connect_timer;
	struct timespec rqtp;
	char	timer_command[80];
};

pthread_mutex_t		mutex;

static void
compress_input_list(int no)
{
	int             i;

/**
	printf("\nAVANT: \n");
	for (i = 0; i < input_list.nb; i++) {

		printf("\t %d: cd=%d cd_init=%d de %s\n",i, input_list.gop[i]->cd,input_list.gop[i]->cd_init,input_list.gop[i]->his_name);

	}
**/

	/*
	 * on libere la structure
	 */
	free(input_list.gop[no]);

	/*
	 * on comprime le tableau
	 */
	for (i = no; i < input_list.nb; i++) {
		input_list.gop[i] = input_list.gop[i+1];
	}
	input_list.nb--;

/**
	printf("APRES: \n");
	for (i = 0; i < input_list.nb; i++) {

		printf("\t %d: cd=%d cd_init=%d de %s\n",i, input_list.gop[i]->cd,input_list.gop[i]->cd_init,input_list.gop[i]->his_name);

	}
**/

}

static void
print_on_logbook(char *str)
 {
	char            out[256];

	sprintf(out, "gop_timer: %s", str);
	if (log_book_status != -1) {
		log_book_status = lbk_write_log_book(out);
	} else {
		lbk_print_on_stderr(out);
	}
}

static void
manage_gop_error(char *txt)
{

	if (gop_errno == GOP_DISCONNECT) {
		lbk_info("Deconnection de %s\n", connect_inet->his_name);
	}
	if (errno == EADDRINUSE) {
		lbk_error("Il y a deja un gop_timer present donc EXIT\n");
		exit(0);
	}
	lbk_error(" GOP : %s: %s  => close_connection\n", txt, gop_get_error_str());
	gop_close_active_connection(connect_inet);
}



static void
handler_sigint(int sig)
{
	signal(SIGINT, handler_sigint);
	lbk_info("handler_sigint: recu SIGINT %d\n",sig);
}

static void
handler_sigalrm(int sig)
{
	signal(SIGALRM, handler_sigalrm);
	lbk_info("handler_sigalrm: recu SIGALRM %d\n",sig);
}


static void
handler_sigurg(int sig)
{
	signal(SIGURG, handler_sigurg);
	lbk_info("handler_sigurg: recu SIGURG (OOB)%d\n",sig);
}

static void
handler_sigpipe(int sig)
{
	signal(SIGPIPE, handler_sigpipe);
	lbk_info("handler_sigpipe: recu SIGPIPE %d\n",sig);
}


static void
handler_sighup(int sig)
{
	signal(SIGHUP, handler_sighup);
	lbk_info("handler_sighup: recu SIGHUP -> reconnection sur logbook %d\n",sig);
	if (log_book_status == -1) {
		if ((log_book_status = lbk_client_log_book()) == -1) {
			lbk_warning("Connection impossible sur le log book\n");
			lbk_warning("===> donc pas de messages\n");
		}
	}
}


static void
*the_timer(void *arg)
{
	struct pth_struct_def *pth_struct;

	pth_struct = (struct pth_struct_def *) arg;

	nanosleep(&pth_struct->rqtp, (struct timespec *) NULL);

	pthread_mutex_lock(&mutex);
	errno     = 0;
	gop_errno = GOP_FALSE;

	gop_set_to(pth_struct->connect_timer, gop_get_his_name(pth_struct->connect_timer));
/**
	printf("On envoie : %s sur %d %s\n",
			pth_struct->timer_command,
			pth_struct->connect_timer->cd,
			pth_struct->connect_timer->his_name);
**/
	if (gop_write_command(pth_struct->connect_timer, pth_struct->timer_command) != GOP_OK) {
		lbk_error(" GOP :the_timer(): gop_write_command(): %s \n", gop_get_error_str());
	}
	free(pth_struct);

	errno     = 0;
	gop_errno = GOP_FALSE;
	pthread_mutex_unlock(&mutex);

	if(pthread_detach(pthread_self()) != 0){
		return ((void *) &errno);
	}
	return ((void *) 0);

}


static int
read_serveur(int sd)
{
	char            command[40];
	int             sec, usec;
	char            sep[2];
	int             no, cd;
	char            str[2048];
	struct gop_connect *connect;

	pthread_t       tid;
	struct	pth_struct_def *pth_struct;
	char            timer_command[256];

	pthread_mutex_lock(&mutex);
	errno     = 0;
	gop_errno = GOP_FALSE;

	/*
	 * recherche quelle connection est activée
	 */
	for (no = 0; no < input_list.nb; no++) {
		if (input_list.gop[no]->cd == sd)
			break;
	}
	if(no==input_list.nb){
		fprintf(stderr,"read_serveur: BUG sd not in input_list\n");
		errno     = 0;
		gop_errno = GOP_FALSE;
		pthread_mutex_unlock(&mutex);
		return(GOP_KO);
	}

	connect = input_list.gop[no];
	gop_set_timeout(connect,0);
/**
	gop_set_timeout(connect,1);

	do {
		gop_errno = GOP_FALSE;
		ilen = gop_read(connect, str, sizeof(str));
		if(ilen<0 && gop_errno != GOP_INTERRUPTED_SYSTEM_CALL){
			break;
		}
		if(ilen<0 && gop_errno == GOP_INTERRUPTED_SYSTEM_CALL){
			lbk_info("GOP_INTERRUPTED_SYSTEM_CALL sur read de  \"%s\"\n", connect->his_name);
		}
	} while (gop_errno == GOP_INTERRUPTED_SYSTEM_CALL);
**/
	if (gop_read(connect, str, sizeof(str)) < 0) {
		if (gop_errno == GOP_DISCONNECT) {
			lbk_info("Deconnection de \"%s\"\n", connect->his_name);

			/*
			 * on enleve le cannal qui s'est deconnecte
			 */
			cd = connect->cd;
			gop_close_connection(connect);
			connect->cd = cd;
			compress_input_list(no);
			errno     = 0;
			gop_errno = GOP_FALSE;
			pthread_mutex_unlock(&mutex);
			return(GOP_OK);
		} else {
			gop_handle_eom(connect, NULL);
			manage_gop_error("read_serveur: gop_read\n");
			errno     = 0;
			gop_errno = GOP_FALSE;
			pthread_mutex_unlock(&mutex);
			return(GOP_KO);
		}
	}
	gop_set_timeout(connect,0);
/**
	lbk_debug("read_serveur: recu >%s< from >%s<\n",
			  str, connect->header.from);
**/
	sep[0] = *str;
	sep[1] = 0;


	sscanf(strtok(str + 1, sep), "%s", command);
	/*
	 * traitement du exit
	 */
	if (strcmp(command, "exit") == 0) {
		lbk_info("exit");
		gop_close_connection(connect);
		exit(0);
		/*
		 * traitement du test
		 */
	} else if (strcmp(command, "test") == 0) {
		if (gop_write_command(connect, "OK") != GOP_OK) {
			manage_gop_error("gop_write_command \"OK\" vers client");
		}
	} else if (strcmp(command, "timer") == 0) {
		/*
		 * traitement du timer
		 */
		strcpy(timer_command, strtok(NULL, sep));
		sscanf(strtok(NULL, sep), "%d", &sec);
		sscanf(strtok(NULL, sep), "%d", &usec);

		pth_struct = (struct pth_struct_def *) malloc(sizeof(struct pth_struct_def));
		if(pth_struct == (struct pth_struct_def *) NULL){
			lbk_info("Probleme d'allocation memoire, on continue, sleep(1)\n");
			sleep(1);
			gop_set_to(connect, gop_get_his_name(connect));
			if (gop_write_command(connect, timer_command) != GOP_OK) {
				manage_gop_error("gop_write_command");
			}
			errno     = 0;
			gop_errno = GOP_FALSE;
			pthread_mutex_unlock(&mutex);
			return(GOP_OK);
		}
		strcpy(pth_struct->timer_command, timer_command);
		pth_struct->connect_timer = connect;
		pth_struct->rqtp.tv_sec = sec;
		pth_struct->rqtp.tv_nsec = usec*1000;

		if (cpt++ < 10) {
			lbk_info("Recu: command=>%s< sec=%d usec=%d from %s\n",
				timer_command, sec, usec, connect->his_name);
		}
		if (usec == 0 && sec == 0) {
			gop_set_to(connect, gop_get_his_name(connect));
			if (gop_write_command(connect, pth_struct->timer_command) != GOP_OK) {
				manage_gop_error("gop_write_command");
			}
		} else {

			if (pthread_create(&tid, NULL, the_timer, (void *)pth_struct) != 0) {
				perror("pthread_create");
				exit(-1);
			}
		}
	} else {
		lbk_error("gop_timer: Recu commande inconnue%s: %s\n", command);
		errno     = 0;
		gop_errno = GOP_FALSE;
		pthread_mutex_unlock(&mutex);
		return(GOP_KO);
	}
	errno     = 0;
	gop_errno = GOP_FALSE;
	pthread_mutex_unlock(&mutex);
	return(GOP_OK);
}


static int
serveur_accept (int sd)
{
	int             no;

	struct gop_connect *conn;

	pthread_mutex_lock(&mutex);
	errno     = 0;
	gop_errno = GOP_FALSE;
	/*
	 * recherche quelle connection est activée
	 */
	for (no = 0; no < input_list.nb; no++) {
		if (input_list.gop[no]->cd_init == sd)
			break;
	}
	if(no==input_list.nb){
		fprintf(stderr,"serveur_accept: BUG sd not in input_list\n");
		return(GOP_KO);
	}

	conn = (struct gop_connect *) malloc(sizeof(struct gop_connect));
	if (conn == (struct gop_connect *) NULL) {
		lbk_error("Error malloc\n");
		errno     = 0;
		gop_errno = GOP_FALSE;
		pthread_mutex_unlock(&mutex);
		return(GOP_KO);
	}
	memcpy(conn, input_list.gop[no], sizeof(struct gop_connect));

	/*
	 * fait la connection
	 */
	if(gop_accept_connection(conn) != GOP_OK){
		manage_gop_error("gop_accept_connection\n");
		free(conn);
		errno     = 0;
		gop_errno = GOP_FALSE;
		pthread_mutex_unlock(&mutex);
		return(GOP_KO);
	}
	/*
	 * on pose conn->cd_init a -1 car on ne veut pas de connection sur
	 * le socket de base
	 */

	conn->cd_init = -1;

	/*
	 * passe les parametres de cette connection
	 */

	input_list.gop[input_list.nb++] = conn;

	lbk_info("Connection de   \"%s\" OK\n", conn->his_name);
	errno     = 0;
	gop_errno = GOP_FALSE;
	pthread_mutex_unlock(&mutex);

	return(GOP_OK);

}

static int
master_connection(struct gop_connect *connect)
{

	/*
	 * en mode master, c'est le serveur qui se connecte sur le client
	 */
	lbk_info("Connection Internet sur client en attente sur host =\"%s\", port=%d, verbosite GOP=%d\n",
		connect->name, connect->port, connect->mode);

	if (gop_connection(connect) != GOP_OK) {
		return(GOP_KO);
	}

	lbk_info("Connection Internet de \"%s\" sur port=%d, verbosite GOP=%d\n",
		 connect->his_name, connect->port, connect->mode);

	return(GOP_OK);
}


//extern char    *optarg;
int main(int argc, char **argv)
{
	int            c;
	int             port = 9200, maxpacket = 2048;
	int             timeout = 0;
	int             verbose = 0;
	struct gop_connect *connect_lbk;
	int             master = GOP_FALSE;
	struct gop_list	output_list;
	sigset_t        set;

        /*
         * on enleve tous les signaux
         */
        if (sigemptyset(&set) != 0) {
                perror("sigfillset");
                exit(-1);
        }
        /*
         * on met SIGPIPE dans le mask
         */
        if (sigaddset(&set, SIGPIPE) != 0) {
                perror("sigdelset");
                exit(-1);
        }
        /*
         * on met le mask pour qu'il bloque SIGPIPE
         */
/**
        if (sigprocmask(SIG_BLOCK, &set, NULL) != 0) {
                perror("sigprocmask");
                exit(-1);
        }
**/
	pthread_mutex_init(&mutex, NULL);
	errno     = 0;
	gop_errno = GOP_FALSE;

	/*
	 * initialisation parametres connection pour le client
	 */
	strcpy(my_name, "goptimer");

	connect_inet = (struct gop_connect *) gop_alloc_connect_structure();
	connect_inet_master = (struct gop_connect *) gop_alloc_connect_structure();

	/*
	 * initialisation parametres connection pour le logbook
	 */

	connect_lbk = (struct gop_connect *) gop_alloc_connect_structure();

	gop_set_name(connect_lbk, "localhost");
	gop_set_type(connect_lbk, GOP_SOCKET);
	gop_set_port(connect_lbk, lbk_get_port_standard());
	gop_set_mode(connect_lbk, 0);
	gop_set_my_name(connect_lbk, my_name);
	gop_set_maxpacket(connect_lbk, maxpacket);

	/*
	 * enregistrement des handlers de signaux
	 */

	signal(SIGINT, handler_sigint);
	signal(SIGHUP, handler_sighup);
	signal(SIGURG, handler_sigurg);
	signal(SIGPIPE, handler_sigpipe);
	signal(SIGALRM, handler_sigalrm);

	while ((c = getopt(argc, argv, "p:L:v:M:h")) != -1) {
		switch (c) {
		case 'M':
			master = GOP_TRUE;
			gop_parse_opt_cmd_line(connect_inet_master);
			break;
		case 'L':
			gop_parse_opt_cmd_line(connect_lbk);
			lbk_set_param_log_book(connect_lbk);

			if ((log_book_status = lbk_client_log_book()) == -1) {
				lbk_warning("Connection impossible sur le log book\n");
				lbk_warning("===> donc pas de messages\n");
			}
			lbk_registration_for_info(print_on_logbook);
			lbk_registration_for_warning(print_on_logbook);
			lbk_registration_for_error(print_on_logbook);
			gop_registration_for_printf(print_on_logbook);

			break;
		case 'p':
			sscanf(optarg, "%d", &port);
			break;
		case 'v':
			sscanf(optarg, "%d", &verbose);
			break;
		case 'h':
			log_book_status = -1;
			lbk_info("syntax:\n");
			lbk_info("\t-p <port>\t socket port number\n");
			lbk_info("\t-L <port>:<host_name>:<gop_verbos> \n");
			lbk_info("\t\t logbook\n");
			lbk_info("\t-v <level>\t verbose level for GOP\n");
			lbk_info("\t-h \t\t this message\n");
			exit(0);
			break;
		}
	}

	gop_init_server_socket(connect_inet, my_name, port, maxpacket, verbose, timeout);
	gop_init_server_socket(connect_inet_master, my_name, port, maxpacket, verbose, timeout);

	/*
	 * Connection
	 */
	input_list.nb = 0;
	if (master) {
		/*
		 * en mode master, c'est le serveur qui se connecte sur le
		 * client
		 */
		if (master_connection(connect_inet_master) == GOP_OK) {
			input_list.gop[input_list.nb] = connect_inet_master;
			input_list.nb++;
		}
		connect_inet_master->cd_init = -1;
	}

	/*
	 * on met de toute facon le serveur en attente
	 */

	if (gop_init_connection(connect_inet) != GOP_OK) {
		manage_gop_error("gop_init_connection");
		exit(-1);
	}
	input_list.gop[input_list.nb] = connect_inet;
	input_list.nb++;

#pragma warning(disable:981)	/** gop_timer.c(569): remark #981: operands are evaluated in unspecified order **/
	gop_process_registration(gop_get_my_name(connect_inet), gop_get_port(connect_inet), "-", -1, -1);

	cpt = 0;
	input_list.timeout = 0;
	for (;;) {
		errno = 0;
		gop_errno = GOP_FALSE;

		gop_select_active_channel(&input_list, &output_list);
		//if(output_list.nb < 0){
		//	continue;
		//}
		if (gop_errno == GOP_TIMEOUT) {
			continue;
		}
		if (output_list.gop[0]->cd == -1) {
			/*
			 * c'est une nouvelle connection
			 */
			serveur_accept(output_list.gop[0]->cd_init);
		} else {
			/*
			 * c'est une lecture
			 */
			read_serveur(output_list.gop[0]->cd);
		}
	}

}
