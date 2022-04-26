#include <stdio.h>
#include <gop.h>
#include <signal.h>
#include <demo.h>

static int      client_interrupt;
static int      error = 0;

static void
manage_gop_error(txt)
	char           *txt;
{
	fprintf(stderr, "manage_gop_error: Erreur GOP : %s: %s\n", txt, gop_get_error_str());
	if (gop_errno == GOP_DISCONNECT)
		exit(0);
}

static void
print_error(txt)
	char           *txt;
{
	fprintf(stderr, "Probleme avec: >%s<\n", txt);
	error = 1;
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
	struct gop_connect connect;
	char            answer[128];
	char            host_name[80];
	char            socket_name[10];
	int             port = 1280, maxpacket = 4096, mode = GOP_HEADER;
	int             socket_unix = GOP_TRUE, transmitter = GOP_FALSE;
	char            from[10];
	int             flag, status;

	extern char    *optarg;
	char            c;

	signal(SIGINT, handler_ctrlc);

	test_set_get(&connect);
	exit(0);

	strcpy(socket_name, "server");
	strcpy(from, *argv);

	while ((c = getopt(argc, argv, "h:tm:")) != -1) {
		switch (c) {
		case 'h':
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
		default:
			fprintf(stderr, "Options: [-h <host_name>] [-t] [-m] <mode>\n");
			exit(0);
		}
	}

	if (socket_unix) {
		gop_init_client_socket_unix(&connect, from, socket_name,
					    maxpacket, mode, 0);
	} else {

		gop_init_client_socket(&connect, from, host_name,
				       port, maxpacket, mode, 0);
	}
	gop_set_stamp(&connect, GOP_TRUE);

	if (gop_connection(&connect) != GOP_OK) {
		manage_gop_error("gop_connection");
		exit(0);
	}
	gop_set_to(&connect, "server");

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
			gop_set_mode(&connect, atoi(answer));

		if (client_interrupt == 0 && (*answer == 'r' || *answer == 'w' ||
					*answer == 'R' || *answer == 'W')) {

			if (transmitter && (*answer == 'R' || *answer == 'W'))
				gop_set_to(&connect, "transmit");
			else
				gop_set_to(&connect, "server");

			printf("ENVOI COMMAND SUR >%s<\n", gop_get_to(&connect));

			gop_set_class(&connect, GOP_CLASS_COMD);
			gop_set_cont(&connect, GOP_TRUE);
			gop_set_stat(&connect, GOP_STAT_OPOK);

			*answer = *answer | 0x20;
			if (*(answer + 1) != 0)
				*(answer + 1) = *(answer + 1) | 0x20;
			if (gop_write_command(&connect, answer) != GOP_OK)
				manage_gop_error("gop_write_command");

			flag = *(answer + 1) == 'm' || *(answer + 1) == 'M';

			if (*answer == 'r') {
				status = read_data(&connect, flag);
			} else {
				status = write_data_client(&connect, flag);
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



test_set_get(connect)
	struct gop_connect *connect;
{
	/*
	 * gop_set_type
	 */

	gop_set_type(connect, GOP_SOCKET);
	if (gop_get_type(connect) != 1)
		print_error("gop_set_type(connect, GOP_SOCKET)");

	gop_set_type(connect, GOP_SOCKET_UNIX);
	if (gop_get_type(connect) != 2)
		print_error("gop_set_type(connect, GOP_SOCKET_UNIX)");

	gop_set_type(connect, GOP_TPU);
	if (gop_get_type(connect) != 3)
		print_error("gop_set_type(connect, GOP_TPU)");

	/*
	 * gop_set_name
	 */

	gop_set_name(connect, "abcdefghijklmnopqrstuvwxyz");
	if(strcmp(gop_get_name(connect), "abcdefghijklmnopqrstuvwxyz") != 0)
		print_error("gop_get_name()");

	/*
	 * gop_set_port
	 */

	gop_set_port(connect, 1234);
	if(gop_get_port(connect) != 1234)
		print_error("gop_get_port()");

	gop_set_port(connect, 5678);
	if(gop_get_port(connect) != 5678)
		print_error("gop_get_port()");

	/*
	 * gop_set_maxpacket
	 */

	gop_set_maxpacket(connect, 1234);
	if(gop_get_maxpacket(connect) != 1234)
		print_error("gop_get_maxpacket()");

	gop_set_maxpacket(connect, 5678);
	if(gop_get_maxpacket(connect) != 5678)
		print_error("gop_get_maxpacket()");

	/*
	 * gop_set_class
	 */
	gop_set_class(connect, GOP_CLASS_COMD);
	if (strcmp(gop_get_class(connect),"COMD") != 0)
		print_error("gop_get_class(connect, GOP_CLASS_COMD)");

	gop_set_class(connect, GOP_CLASS_DATA);
	if (strcmp(gop_get_class(connect),"DATA") != 0)
		print_error("gop_get_class(connect, GOP_CLASS_DATA)");

	gop_set_class(connect, GOP_CLASS_STAT);
	if (strcmp(gop_get_class(connect),"STAT") != 0)
		print_error("gop_get_class(connect, GOP_CLASS_STAT)");

	gop_set_class(connect, GOP_CLASS_INFO);
	if (strcmp(gop_get_class(connect),"INFO") != 0)
		print_error("gop_get_class(connect, GOP_CLASS_INFO)");

	gop_set_class(connect, GOP_CLASS_DBUG);
	if (strcmp(gop_get_class(connect),"DBUG") != 0)
		print_error("gop_get_class(connect, GOP_CLASS_DBUG)");

	gop_set_class(connect, GOP_CLASS_ACKN);
	if (strcmp(gop_get_class(connect),"ACKN") != 0)
		print_error("gop_get_class(connect, GOP_CLASS_ACKN)");

	gop_set_class(connect, GOP_CLASS_ALRM);
	if (strcmp(gop_get_class(connect),"ALRM") != 0)
		print_error("gop_get_class(connect, GOP_CLASS_ALRM)");

	gop_set_class(connect, GOP_CLASS_INIT);
	if (strcmp(gop_get_class(connect),"INIT") != 0)
		print_error("gop_get_class(connect, GOP_CLASS_INIT)");

	/*
	 * gop_set_from
	 */

	gop_set_from(connect, "abcdefghijklmnopqrstuvwxyz");
	if(strcmp(gop_get_from(connect), "abcdefgh") != 0)
		print_error("gop_get_from()");

	/*
	 * gop_set_to
	 */

	gop_set_to(connect, "abcdefghijklmnopqrstuvwxyz");
	if(strcmp(gop_get_to(connect), "abcdefgh") != 0)
		print_error("gop_get_to()");

	/*
	 * gop_set_my_name
	 */

	gop_set_my_name(connect, "abcdefghijklmnopqrstuvwxyz");
	if(strcmp(gop_get_my_name(connect), "abcdefgh") != 0)
		print_error("gop_get_my_name()");

	/*
	 * gop_set_his_name
	 */

	gop_set_his_name(connect, "abcdefghijklmnopqrstuvwxyz");
	if(strcmp(gop_get_his_name(connect), "abcdefgh") != 0)
		print_error("gop_get_his_name()");

	/*
	 * gop_set_msize
	 */

	gop_set_msize(connect, 1234);
	if(gop_get_msize(connect) != 1234)
		print_error("gop_get_msize()");

	gop_set_msize(connect, 5678);
	if(gop_get_msize(connect) != 5678)
		print_error("gop_get_msize()");

	/*
	 * gop_set_psize
	 */

	gop_set_psize(connect, 1234);
	if(gop_get_psize(connect) != 1234)
		print_error("gop_get_psize()");

	gop_set_psize(connect, 5678);
	if(gop_get_psize(connect) != 5678)
		print_error("gop_get_psize()");

	/*
	 * gop_set_cont
	 */

	gop_set_cont(connect, GOP_TRUE);
	if(!gop_get_cont(connect))
		print_error("gop_get_cont()");

	gop_set_cont(connect, GOP_FALSE);
	if(gop_get_cont(connect))
		print_error("gop_get_cont()");

	/*
	 * gop_set_stamp
	 */

	gop_set_stamp(connect, GOP_TRUE);
	if(!gop_get_stamp(connect))
		print_error("gop_get_stamp()");

	gop_set_stamp(connect, GOP_FALSE);
	if(gop_get_stamp(connect))
		print_error("gop_get_stamp()");

	/*
	 * gop_set_hsync
	 */

	gop_set_hsync(connect, GOP_TRUE);
	if(!gop_get_hsync(connect))
		print_error("gop_get_hsync()");

	gop_set_hsync(connect, GOP_FALSE);
	if(gop_get_hsync(connect))
		print_error("gop_get_hsync()");

	/*
	 * gop_set_dsync
	 */

	gop_set_dsync(connect, GOP_TRUE);
	if(!gop_get_dsync(connect))
		print_error("gop_get_dsync()");

	gop_set_dsync(connect, GOP_FALSE);
	if(gop_get_dsync(connect))
		print_error("gop_get_dsync()");

	/*
	 * gop_set_stat
	 */

	gop_set_stat(connect, GOP_STAT_OPOK);
	if (strcmp(gop_get_stat(connect),"OPOK") != 0)
		print_error("gop_get_stat(connect, GOP_STAT_OPOK)");

	gop_set_stat(connect, GOP_STAT_WARN);
	if (strcmp(gop_get_stat(connect),"WARN") != 0)
		print_error("gop_get_stat(connect, GOP_STAT_WARN)");

	gop_set_stat(connect, GOP_STAT_RCOV);
	if (strcmp(gop_get_stat(connect),"RCOV") != 0)
		print_error("gop_get_stat(connect, GOP_STAT_RCOV)");

	gop_set_stat(connect, GOP_STAT_FTAL);
	if (strcmp(gop_get_stat(connect),"FTAL") != 0)
		print_error("gop_get_stat(connect, GOP_STAT_FTAL)");

	gop_set_stat(connect, GOP_STAT_BUSY);
	if (strcmp(gop_get_stat(connect),"BUSY") != 0)
		print_error("gop_get_stat(connect, GOP_STAT_BUSY)");

	gop_set_stat(connect, GOP_STAT_TIME);
	if (strcmp(gop_get_stat(connect),"TIME") != 0)
		print_error("gop_get_stat(connect, GOP_STAT_TIME)");

	/*
	 * gop_set_mode
	 */

	gop_set_mode(connect, GOP_SYNCHRO);
	if(gop_get_mode(connect) != GOP_TRUE)
		print_error("gop_get_mode()");

	gop_set_mode(connect, GOP_ASYNCHRO);
	if(gop_get_mode(connect) != GOP_FALSE)
		print_error("gop_get_mode()");

	/*
	 * gop_set_datatype
	 */

	gop_set_datatype(connect, GOP_CHAR);
	if(gop_get_datatype(connect) != 0)
		print_error("gop_get_datatype()");

	gop_set_datatype(connect, GOP_USHORT);
	if(gop_get_datatype(connect) != 1)
		print_error("gop_get_datatype()");

	gop_set_datatype(connect, GOP_SHORT);
	if(gop_get_datatype(connect) != 2)
		print_error("gop_get_datatype()");

	gop_set_datatype(connect, GOP_UINT);
	if(gop_get_datatype(connect) != 3)
		print_error("gop_get_datatype()");

	gop_set_datatype(connect, GOP_INT);
	if(gop_get_datatype(connect) != 4)
		print_error("gop_get_datatype()");

	gop_set_datatype(connect, GOP_ULONG);
	if(gop_get_datatype(connect) != 5)
		print_error("gop_get_datatype()");

	gop_set_datatype(connect, GOP_LONG);
	if(gop_get_datatype(connect) != 6)
		print_error("gop_get_datatype()");

	gop_set_datatype(connect, GOP_FLOAT);
	if(gop_get_datatype(connect) != 7)
		print_error("gop_get_datatype()");

	gop_set_datatype(connect, GOP_DOUBLE);
	if(gop_get_datatype(connect) != 8)
		print_error("gop_get_datatype()");

	gop_set_datatype(connect, GOP_STRUCT);
	if(gop_get_datatype(connect) != 9)
		print_error("gop_get_datatype()");

	/*
	 * gop_set_timeout
	 */

	gop_set_timeout(connect, 0);
	if(gop_get_timeout(connect) != 0)
		print_error("gop_get_timeout()");

	gop_set_timeout(connect, 1);
	if(gop_get_timeout(connect) != 1)
		print_error("gop_get_timeout()");

	/*
	 * gop_set_side
	 */

	gop_set_side(connect, GOP_SERVER_SIDE);
	if(gop_get_side(connect) != 1)
		print_error("gop_get_side()");

	gop_set_side(connect, GOP_CLIENT_SIDE);
	if(gop_get_side(connect) != 2)
		print_error("gop_get_side()");

	gop_set_side(connect, GOP_TRANSMIT_SIDE);
	if(gop_get_side(connect) != 3)
		print_error("gop_get_side()");
}
