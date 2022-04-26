#include <stdio.h>
#include <gop.h>
#include <signal.h>
#include <demo.h>

static int      client_interrupt;

static void
manage_gop_error(txt)
	char           *txt;
{
	fprintf(stderr, "manage_gop_error: Erreur GOP : %s: %s\n", txt, gop_get_error_str());
	if (gop_errno == GOP_DISCONNECT)
		exit(0);
}

static void
handler_ctrlc(sig)
	int             sig;
{
	signal(SIGINT, handler_ctrlc);
	printf("handler_ctrlc: recu SIGINT \n");
	client_interrupt = 1;
}

main(argc, argv)
	int             argc;
	char          **argv;
{
	struct gop_connect *connect;
	char            answer[128];
	char            host_name[80];
	char            socket_name[10];
	int             port = 1280, maxpacket = 4096, mode = GOP_CONNECTION;
	int             socket_unix = GOP_TRUE, transmitter = GOP_FALSE;
	char            from[10];
	int             flag, status;

	extern char    *optarg;
	char            c;


	connect = (struct gop_connect *) gop_alloc_connect_structure();

	signal(SIGINT, handler_ctrlc);


	strcpy(socket_name, "server");
	strcpy(from, *argv);

	while ((c = getopt(argc, argv, "i:tm:h")) != -1) {
		switch (c) {
		case 'i':
			strcpy(host_name, optarg);
			socket_unix = GOP_FALSE;
			break;
		case 't':
			transmitter = GOP_TRUE;
			port = 1281;
			strcpy(socket_name, "transmit");
			break;
		case 'm':
			sscanf(optarg, "%d", &mode);
			break;
		case 'h':
		default:
			fprintf(stderr, "Options: \n");
			fprintf(stderr, "\t -i <host_name> : pour connection internet\n");
			fprintf(stderr, "\t                  (defaut sur socket Unix)\n");
			fprintf(stderr, "\t -t             : pour connection sur transmitter\n");
			fprintf(stderr, "\t -m <mode>      : pour donner le niveau de debug GOP\n");
			fprintf(stderr, "\t                  (defaut = GOP_CONNECTION)\n");
			fprintf(stderr, "\t -h             : ce help\n");
			exit(0);
		}
	}

	if (socket_unix) {
		gop_init_client_socket_unix(connect, from, socket_name,
					    maxpacket, mode, 0);
	} else {

		gop_init_client_socket(connect, from, host_name,
				       port, maxpacket, mode, 0);
	}
	gop_set_stamp(connect, GOP_TRUE);

	if (gop_connection(connect) != GOP_OK) {
		manage_gop_error("gop_connection");
		exit(0);
	}
	gop_set_to(connect, "server");

	for (;;) {
		client_interrupt = 0;
		printf("TAPEZ r(ead)  lecture  de 500 [KB] en provenance du serveur\n");
		printf("      w(rite) écriture de 500 [KB] sur le serveur\n");
		printf("      R(EAD)  lecture  de 500 [KB] en provenance du transmetteur\n");
		printf("      W(RITE) écriture de 500 [KB] sur le transmetteur\n");
		printf("      si la 2eme lettre est un 'm' le transfert est en mode matrix\n");
		printf("      0-9     choix du niveau de debug\n");
		printf("      q(uit)  pour quitter:\n");
		gets(answer);

		if (*answer == 'q')
			exit(0);

		if (*answer >= '0' && *answer <= '9')
			gop_set_mode(connect, atoi(answer));

		if (client_interrupt == 0 && (*answer == 'r' || *answer == 'w' ||
					*answer == 'R' || *answer == 'W')) {

			if (transmitter && (*answer == 'R' || *answer == 'W'))
				gop_set_to(connect, "transmit");
			else
				gop_set_to(connect, "server");

			printf("ENVOI COMMAND SUR >%s<\n", gop_get_to(connect));

			gop_set_class(connect, GOP_CLASS_COMD);
			gop_set_cont(connect, GOP_TRUE);
			gop_set_stat(connect, GOP_STAT_OPOK);

			*answer = *answer | 0x20;
			if (*(answer + 1) != 0)
				*(answer + 1) = *(answer + 1) | 0x20;
			if (gop_write_command(connect, answer) != GOP_OK)
				manage_gop_error("gop_write_command");

			flag = *(answer + 1) == 'm' || *(answer + 1) == 'M';

			if (*answer == 'r') {
				status = read_data(connect, flag);
			} else {
				status = write_data_client(connect, flag);
			}
			if (status < 0)
				manage_gop_error("gop_write_command");
		}
	}
}


int
read_data(connect, flag)
	struct gop_connect *connect;
	int             flag;
{
	int             buf[NPIX_X * NPIX_Y];
	int             status;

	if (flag) {
		if ((status = gop_read_matrix(connect, (char *) &buf, sizeof(buf), NPIX_X, DX, DY)) < 0)
			gop_handle_eom(connect, NULL);
	} else {
		if ((status = gop_read(connect, (char *) &buf, sizeof(buf))) < 0)
			gop_handle_eom(connect, NULL);
	}
	test_buf(buf, abs(status) / sizeof(int));

	return (status);
}

int
write_data_client(connect, flag)
	struct gop_connect *connect;
	int             flag;
{
	int             buf[NPIX_X * NPIX_Y];
	int             i;
	int             status;

	/* envoi des data */

	printf("\n\n Préparation data ... \n");
	for (i = 0; i < sizeof(buf) / sizeof(int); i++)
		buf[i] = i;

	printf("%d %d ... %d %d\n", buf[0], buf[1], buf[NPIX_X * NPIX_Y - 2], buf[NPIX_X * NPIX_Y - 1]);

	for (i = 0; i < 4; i++) {
		sleep(1);
		printf(".");
		fflush(stdout);
	}
	printf("\n");

	printf(" Envoi de data..... \n\n");
	gop_set_cont(connect, GOP_FALSE);
	gop_set_class(connect, GOP_CLASS_DATA);

	if (flag)
		status = gop_write_matrix(connect, (char *) &buf, XSIZE * YSIZE * sizeof(int),
			      XSIZE * sizeof(int), GOP_INT, NPIX_X, DX, DY);
	else
		status = gop_write(connect, (char *) &buf, sizeof(buf), 4096, GOP_INT);


	if (status != GOP_OK) {
		if (gop_errno == GOP_INTERRUPTED_TRANSMISSION) {
			printf("message incomplet\n");
		} else {
			manage_gop_error("gop_read");
		}
	}
	return (status);
}

int
test_buf(buf, n)
	int            *buf;
	int             n;
{
	int             i;


	printf("test data: %d %d ... %d %d\n", buf[0], buf[1], buf[NPIX_X * NPIX_Y - 2], buf[NPIX_X * NPIX_Y - 1]);
	if (n < 100)
		return;
	for (i = 0; i < n; i = i + 100)
		if (buf[i] != i) {
			fprintf(stderr, "tableau incoherent a la position %d (%d byte)\n", i, i * sizeof(int));
			exit(0);
		}
}
