#include <stdio.h>
#include <gop.h>
#include <signal.h>
#include <demo.h>

static int      client_interrupt;

static void
manage_gop_error(txt)
	char           *txt;
{
	fprintf(stderr, "test_gop_timer: Erreur GOP : %s: %s\n", txt, gop_get_error_str());
	if (gop_errno == GOP_DISCONNECT)
		exit(0);
}


main(argc, argv)
	int             argc;
	char          **argv;
{
	struct gop_connect *connect;
	char            answer[2048];
	char            host_name[80];
	int             port = 9200, maxpacket = 2048, mode = 1;
	char            from[10];
	int             flag, status;
	int		sec;

	extern char    *optarg;
	char            c;


	connect = (struct gop_connect *) gop_alloc_connect_structure();
	strcpy(host_name, "localhost");


	strcpy(from, "test_timer");

	while ((c = getopt(argc, argv, "i:tm:h")) != -1) {
		switch (c) {
		case 'i':
			strcpy(host_name, optarg);
			break;
		case 'm':
			sscanf(optarg, "%d", &mode);
			break;
		case 'h':
		default:
			fprintf(stderr, "Options: \n");
			fprintf(stderr, "\t -i <host_name> : pour connection internet\n");
			fprintf(stderr, "\t                  (defaut sur localhost)\n");
			fprintf(stderr, "\t -m <mode>      : pour donner le niveau de debug GOP\n");
			fprintf(stderr, "\t                  (defaut = 3)\n");
			fprintf(stderr, "\t -h             : ce help\n");
			exit(0);
		}
	}

	gop_init_client_socket(connect, from, host_name,
			       port, maxpacket, mode, 0);
	gop_set_stamp(connect, GOP_TRUE);

	if (gop_connection(connect) != GOP_OK) {
		manage_gop_error("gop_connection");
		exit(0);
	}
	while (1) {

		printf("Donnez un temp d'attente en sec:\n");
		gets(answer);

		if (*answer == 'q')
			exit(0);
		sec=atoi(answer);

		printf("ENVOI COMMAND SUR >%s<\n", gop_get_to(connect));

		sprintf(answer,"/timer/commande_de_test/%d/0", sec);
		if (gop_write(connect, (char *) &answer, sizeof(answer), 4096, GOP_INT) != GOP_OK) {
			manage_gop_error("gop_write");
			exit(0);
		}
		if (gop_read(connect, answer, sizeof(answer)) < 0) {
			manage_gop_error("gop_read");
			exit(0);
		}
		printf("recu >%s<\n", answer);
	}
}
