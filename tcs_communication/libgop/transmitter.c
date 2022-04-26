#include <stdio.h>
#include <signal.h>
#include <gop.h>
#include <logbook.h>

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
	struct gop_connect *connect_client_inet;
	struct gop_connect *connect_client_unix;
	struct gop_connect *connect_server;
	struct gop_connect *to_connect;
	struct gop_connect *connect_log;
	struct gop_list active_list;
	struct gop_list input_list, output_list;
	struct gop_list srv_list;

	char            cmd[128];
	int             i, flag, status;
	char            host_name[80];
	char            socket_name_server[] = "server";
	char            socket_name_client[] = "transmit";
	int             port_server = 1280, port_client = 1281;
	int             maxpacket = 4096, mode = GOP_CONNECTION;
	int             socket_unix = GOP_TRUE;
	char            from[] = "transmit";
	int		log_book_status;
	int		error;
	int             poll_timeout;

	extern char    *optarg;
	char            c;

	connect_client_inet = (struct gop_connect *) gop_alloc_connect_structure();
	connect_client_unix = (struct gop_connect *) gop_alloc_connect_structure();
	connect_server = (struct gop_connect *) gop_alloc_connect_structure();

	signal(SIGURG, handler_sigurg);


	while ((c = getopt(argc, argv, "i:m:h")) != -1) {
		switch (c) {
		case 'i':
			strcpy(host_name, optarg);
			socket_unix = GOP_FALSE;
			break;
		case 'm':
			sscanf(optarg, "%d", &mode);
			break;
		case 'h':
		default:
			fprintf(stderr, "Options: \n");
			fprintf(stderr, "\t -i <host_name> : pour connection internet\n");
			fprintf(stderr, "\t                  (defaut sur socket Unix)\n");
			fprintf(stderr, "\t -m <mode>      : pour donner le niveau de debug GOP\n");
			fprintf(stderr, "\t                  (defaut = GOP_CONNECTION)\n");
			fprintf(stderr, "\t -h             : ce help\n");
			exit(0);
		}
	}


	lbk_set_default_param_log_book();
	lbk_set_my_name(from);
	if ((log_book_status = lbk_client_log_book()) == -1)
	{
		srv_list.nb = 0;
		srv_list.timeout = 0;
		fprintf(stderr, "Connexion impossible sur le log book\n");
	} else {
		connect_log = lbk_get_connect_struct();
		srv_list.nb = 1;
		srv_list.timeout = 0;
		srv_list.gop[0] = connect_log;
	}


	if (socket_unix) {
		gop_init_client_socket_unix(connect_server, from, socket_name_server,
					    maxpacket, mode, 0);
	} else {

		gop_init_client_socket(connect_server, from, host_name,
				       port_server, maxpacket, mode, 0);
	}
	gop_set_stamp(connect_server, GOP_TRUE);

	if (gop_connection(connect_server) != GOP_OK) {
		manage_gop_error("gop_connection");
		exit(0);
	}
	gop_init_server_socket(connect_client_inet, from, port_client, maxpacket, mode, 0);
	gop_init_server_socket_unix(connect_client_unix, from, socket_name_client, maxpacket, mode, 0);
	gop_set_stamp(connect_client_inet, GOP_TRUE);
	gop_set_stamp(connect_client_unix, GOP_TRUE);

	if (gop_init_connection(connect_client_inet) != GOP_OK) {
		manage_gop_error("init sur socket internet");
		exit(0);
	}
	if (gop_init_connection(connect_client_unix) != GOP_OK) {
		manage_gop_error("init sur socket unix");
		exit(0);
	}

        poll_timeout        = 0;

	input_list.nb       = 3;
	input_list.timeout  = poll_timeout;
	input_list.gop[0]   = connect_client_inet;
	input_list.gop[1]   = connect_client_unix;
	input_list.gop[2]   = connect_server;

	active_list.nb      = 1;
	active_list.timeout = 0;
	active_list.gop[0]  = connect_server;

	while (1) {
		error = gop_select_active_channel(&input_list, &output_list);
		if ((error != GOP_OK ) && (gop_errno != GOP_TIMEOUT)) {
			manage_gop_error("gop_select_active_channel");
		}
		for (i = 0; i < output_list.nb; i++) {

			if (gop_get_cd(output_list.gop[i]) == -1) {
				if (gop_accept_connection(output_list.gop[i]) != GOP_OK) {
					manage_gop_error("gop_accept_connection");
					exit(0);
				}
				active_list.gop[active_list.nb] = output_list.gop[i];
				active_list.nb = active_list.nb + 1;
			} else {

				if (gop_select_destination(output_list.gop[i], &active_list,
						   &to_connect) != GOP_OK) {
					if(gop_errno == GOP_DISCONNECT){
						if(output_list.gop[i] == connect_client_inet){
							if (gop_accept_connection(output_list.gop[i]) != GOP_OK) {
								manage_gop_error("gop_accept_connection");
								exit(0);
							}
							continue;
						} else if(output_list.gop[i] == connect_client_unix){
							if (gop_accept_connection(output_list.gop[i]) != GOP_OK) {
								manage_gop_error("gop_accept_connection");
								exit(0);
							}
							continue;
						}

					}
					manage_gop_error("gop_select_destination");
				}
				gop_set_mode(connect_client_inet, output_list.gop[i]->mode);
				gop_set_mode(connect_client_unix, output_list.gop[i]->mode);
				if (to_connect != NULL) {
					printf("COMMUNICATION EN TRANSIT\n");

					gop_set_side(output_list.gop[i], GOP_TRANSMIT_SIDE);

					if (gop_forward(output_list.gop[i], to_connect, poll_timeout, &srv_list) != GOP_OK) {
						manage_gop_error("gop_read");
					}
				} else {

					printf("COMMUNICATION LOCALE\n");
					gop_set_side(output_list.gop[i], GOP_SERVER_SIDE);
					if (gop_read_data(output_list.gop[i], cmd, sizeof(cmd)) < 0) {
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
