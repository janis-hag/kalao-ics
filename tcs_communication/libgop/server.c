#include <stdio.h>
#include <signal.h>
#include <gop.h>
#include <demo.h>

static int      server_interrupt;

static void
manage_gop_error(txt)
	char           *txt;
{
	fprintf(stderr, "manage_gop_error: Erreur GOP : %s: %s\n", txt, gop_get_error_str());
	if (gop_errno == GOP_DISCONNECT)
		exit(0);
}

static void
handler_sigurg(sig)
	int             sig;
{
	signal(SIGURG, handler_sigurg);
	fprintf(stderr, "handler_sigurg: recu   SIGURG (OOB) \n");
	server_interrupt = 1;
}

main(argc, argv)
	int             argc;
	char          **argv;
{
	struct gop_connect *connect_unix;
	struct gop_connect *connect_inet;
	struct gop_list input_list, output_list;

	char            cmd[128];
	int             i, flag, status;
	int             port = 1280, maxpacket = 1540, mode = GOP_CONNECTION;
	int             timeout = 0;
	char            from[] = "server", socket_name[] = "server";


	extern char    *optarg;
	char            c;


	connect_unix = (struct gop_connect *) gop_alloc_connect_structure();
	connect_inet = (struct gop_connect *) gop_alloc_connect_structure();

	signal(SIGURG, handler_sigurg);


	while ((c = getopt(argc, argv, "m:h")) != -1) {
		switch (c) {
		case 'm':
			sscanf(optarg, "%d", &mode);
			break;
		case 'h':
		default:
			fprintf(stderr, "Options: \n");
			fprintf(stderr, "\t -m <mode>      : pour donner le niveau de debug GOP\n");
			fprintf(stderr, "\t                  (defaut = GOP_CONNECTION)\n");
			fprintf(stderr, "\t -h             : ce help\n");
			exit(0);
		}
	}

	gop_init_server_socket(connect_inet, from, port, maxpacket, mode, timeout);
	gop_init_server_socket_unix(connect_unix, from, socket_name, maxpacket, mode, timeout);

	if (gop_init_connection(connect_inet) != GOP_OK) {
		manage_gop_error("init sur socket internet");
		exit(0);
	}
	if (gop_init_connection(connect_unix) != GOP_OK) {
		manage_gop_error("init sur socket unix");
		exit(0);
	}
	input_list.timeout = 0;
	input_list.nb = 2;
	input_list.gop[0] = connect_inet;
	input_list.gop[1] = connect_unix;

	while (1) {
		if (gop_select_active_channel(&input_list, &output_list) != GOP_OK) {
			manage_gop_error("gop_select_active_channel");
		}
		gop_set_mode(connect_inet, output_list.gop[0]->mode);
		gop_set_mode(connect_unix, output_list.gop[0]->mode);
		for (i = 0; i < output_list.nb; i++) {
			if (gop_get_cd(output_list.gop[i]) == -1) {
				if (gop_accept_connection(output_list.gop[i]) != GOP_OK) {
					manage_gop_error("gop_accept_connection");
					exit(0);
				}
			} else {
				if (gop_read(output_list.gop[i], cmd, sizeof(cmd)) < 0) {
					manage_gop_error("gop_read");
				}
				printf("\n\n Recu: >%s<\n\n", cmd);
				flag = *(cmd + 1) == 'm';
				if (*cmd == 'r') {
					status = write_data_server(output_list.gop[i], flag);
				} else {
					status = read_data(output_list.gop[i], flag);
				}
				if (status < GOP_OK)
					manage_gop_error("gop_write_command");

			}
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
write_data_server(connect, flag)
	struct gop_connect *connect;
	int             flag;
{
	int             buf[NPIX_X * NPIX_Y];
	int             i;
	int             status;
	char		to[12];

	server_interrupt = 0;

	/* envoi des data */

	printf("\n\n Préparation data  \n");
	for (i = 0; i < sizeof(buf) / sizeof(int); i++)
		buf[i] = i;

	printf("%d %d ... %d %d\n", buf[0], buf[1], buf[NPIX_X * NPIX_Y - 2], buf[NPIX_X * NPIX_Y - 1]);

	for (i = 0; i < 4; i++) {
		sleep(1);
		printf(".");
		fflush(stdout);
		if (server_interrupt)
			break;
	}
	printf("\n");

	gop_set_destination(connect);
	strcpy(to, connect->to);

	gop_set_to(connect, "logbook");

	gop_set_cont(connect, GOP_TRUE);
	gop_write_command(connect, "salut logbook\n");

	gop_set_to(connect, "outre");

	gop_set_cont(connect, GOP_FALSE);
	gop_write_command(connect, "salut petite outre\n");

	gop_set_cont(connect, GOP_TRUE);
	strcpy(connect->to, to);

	if (server_interrupt) {
		/*
		 * envoi de EOM si le serveur a ete interrompue hors
		 * communication
		 */
		printf("!!!! Interrupt Détecté durant la péparation des data: \n");
		printf("!!!!    ->  envoi de fin de message\n");
		gop_write_end_of_message(connect, "Interrupted transmission");
		return (GOP_KO);

	} else {
		/*
		 * envoi des data
		 */
		printf(" Envoi data  \n\n");

		gop_set_cont(connect, GOP_FALSE);
		gop_set_class(connect, GOP_CLASS_DATA);
		if (flag)
			status = gop_write_matrix(connect, (char *) &buf, XSIZE * YSIZE * sizeof(int),
			      XSIZE * sizeof(int), GOP_INT, NPIX_X, DX, DY);
		else
			status = gop_write(connect, (char *) &buf, sizeof(buf), 4096, GOP_INT);

		if (status != GOP_OK)
			return (GOP_KO);

	}
	return (GOP_OK);
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
