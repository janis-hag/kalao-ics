#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <time.h>
#include <string.h>
#include <gop.h>
// #include <logbook.h>

char	my_name[16];

static void
print_help_connection (void)
{
	fprintf(stderr, "Options connection:\n");
	fprintf(stderr, "\t\t Connection par defaut sur socket Unix (Sur la meme machine).\n");
	fprintf(stderr, "\t\t Nom: \"socket.gop\".\n\n");
	fprintf(stderr, "\t-u -:<unix_socket_name>:<gop_mode>\n");
	fprintf(stderr, "\t\t pour connection socket Unix. (Sur la meme machine)\n");
	fprintf(stderr, "\t\t Defaut: -:gop:0.\n");
	fprintf(stderr, "\t\t Utilise la socket: \"socket.<unix_socket_name>.\"\n");
	fprintf(stderr, "\t-i <socket_port_number>:<destination_host_name>:<gop_mode>\n");
	fprintf(stderr, "\t\t pour connection socket Internet. (Entre machines)\n");
	fprintf(stderr, "\t\t Defaut: 6234:localhost:0.\n");
}
static void print_help()
{

	fprintf(stderr, "Syntaxe:\n");
        fprintf(stderr, "\t gop_wait [<options>]\n");
	fprintf(stderr, "\n");
	print_help_connection();
	fprintf(stderr, "\t-d \n");
	fprintf(stderr, "\t\t delai (def:1[s])\n");
	fprintf(stderr, "\t-h \n");
	fprintf(stderr, "\t\t Ce message de help.\n");
	exit(0);
}

static void
handler_sigint(int sig)
{
	//lbk_info("gop_wait: handler_sigint: recu SIGINT %d\n",sig);
	printf("gop_wait: handler_sigint: recu SIGINT %d\n",sig);
	printf("\n");
	//gop_process_unregistration(my_name);
	exit(0);
}
static void
handler_sighup(int sig)
{
	//lbk_info("gop_wait: handler_sigint: recu SIGHUP %d\n",sig);
	printf("gop_wait: handler_sigint: recu SIGHUP %d\n",sig);
	printf("\n");
	//gop_process_unregistration(my_name);
	exit(0);
}

int
main(int argc, char **argv)
{
	int             socket_unix;
	struct gop_connect *connect;


	//extern char    *optarg;
	int             c;
	int		delay;
	int		status;
	int		printed;
	char		txt[80];

	strcpy(my_name, "gopwait");

	/*
	 * defaut:connection sur machine locale par socket Unix
	 */

	connect = (struct gop_connect *) gop_alloc_connect_structure();
	gop_set_name(connect, "localhost");
	gop_set_type(connect, GOP_SOCKET);
	gop_set_port(connect, 6234);
	gop_set_mode(connect, 0);
	gop_set_my_name(connect, my_name);
	gop_set_maxpacket(connect, 1024);

	/*
	 * enregistrement des handlers de signaux
	 */

	signal(SIGINT, handler_sigint);
	signal(SIGHUP, handler_sighup);

	socket_unix = -1;
	delay	= 1;
	while ((c = getopt(argc, argv, "d:u:i:h")) != -1) {
		switch (c) {
		case 'd':
                        sscanf(optarg, "%d", &delay);
			break;
		case 'i':
			socket_unix = 0;
			gop_parse_opt_cmd_line(connect);
			break;
		case 'u':
			socket_unix = 1;
			gop_set_type(connect, GOP_SOCKET_UNIX);
			gop_parse_opt_cmd_line(connect);
			break;
		default:
		case 'h':
			print_help();

		}
	}

	if(socket_unix == -1){
		print_help();
	}

	//gop_process_registration(my_name, -1, "-", -1, -1);

#pragma warning(disable:981)
/**
pour eviter
gop_wait.c(129): remark #981: operands are evaluated in unspecified order
  		sprintf(txt, "gop_wait (port:%d host:\"%s\"):", gop_get_port(connect), gop_get_name(connect));
  		                                                                       ^

gop_wait.c(129): remark #981: operands are evaluated in unspecified order
  		sprintf(txt, "gop_wait (port:%d host:\"%s\"):", gop_get_port(connect), gop_get_name(connect));
                                        ^                          ^                            ^
**/
	if(socket_unix){
		sprintf(txt, "gop_wait (socket:\"$HOME/socket.%s\"):", gop_get_name(connect));
	} else {
		sprintf(txt, "gop_wait (port:%d host:\"%s\"):", gop_get_port(connect), gop_get_name(connect));
	}


	printed = 0;
	status = GOP_KO;
	while (status == GOP_KO) {
		status = gop_connection(connect);
		if(status==GOP_KO){
			if(!printed)printf("%s", txt);
			printf(".");
			fflush(stdout);
			printed = 1;
			sleep(delay);
		}
	}
	if(printed)printf("\n");

	//gop_process_unregistration(my_name);
	exit(0);

}
