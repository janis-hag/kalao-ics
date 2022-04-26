#include <stdio.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/file.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <gop.h>
#include <signal.h>

#include <readline/history.h>


extern void     handler_ctrlc_();

init_signal_sigint_()
{
	sigset(SIGINT, handler_ctrlc_);
}

reinit_signal_sigint_()
{
	signal(SIGINT, handler_ctrlc_);
}



manage_gop_error(txt)
	char           *txt;
{
	fprintf(stderr, "Erreur GOP : %s: %s\n", txt, gop_get_error_str());
}


static int      client_interrupt;

/*
void
handler_ctrlc(sig)
	int             sig;
{
	printf("F77   client: handler_ctrlc: \n");
	client_interrupt = 1;

}
*/


void
init_connection()
{
}

void
connect_client_(connect, verbose, status)
	struct gop_connect **connect;
	int		*verbose;
	int             *status;
{
	*status = connect_client(connect, *verbose);
}

int
connect_client(connect, verbose)
	struct gop_connect **connect;
	int		verbose;
{

	*connect = (struct gop_connect *) gop_alloc_connect_structure();

	if (*connect == (struct gop_connect *) NULL) {
		return (GOP_KO);
	}
	gop_set_type(*connect, GOP_SOCKET);
	gop_set_name(*connect, "obssq4");
	gop_set_port(*connect, 1298);
	gop_set_maxpacket(*connect, 4096);
	gop_set_from(*connect, "client");
	gop_set_timeout(*connect, 0);
	gop_set_mode(*connect, GOP_NOTHING);
	gop_set_mode(*connect, GOP_PACKET);
	gop_set_mode(*connect, GOP_IO);
	gop_set_stamp(*connect, GOP_TRUE);
	gop_set_hsync(*connect, GOP_SYNCHRO);
	gop_set_dsync(*connect, GOP_SYNCHRO);
	gop_set_stat(*connect, GOP_STAT_OPOK);

	gop_set_mode(*connect, GOP_IO);

	if (gop_connection(*connect) != GOP_OK){
		manage_gop_error("gop_connection");
		return(GOP_KO);
	}
	gop_set_to(*connect, "server");
	return (GOP_OK);


}


void
write_cmd_(connect, status)
	struct gop_connect **connect;
	int            *status;
{
	*status = write_cmd(*connect);
}

int
write_cmd(connect)
	struct gop_connect *connect;
{
	char            cmd[128] = "1234567890";
	gop_set_class(connect, GOP_CLASS_COMD);
	if (gop_write_command(connect, cmd) != GOP_OK) {
		manage_gop_error("gop_write_command");
		return (GOP_KO);
	}
	return (GOP_OK);
}

void
read_buf_(connect, status)
	struct gop_connect **connect;
	int            *status;
{
	*status = read_buf(*connect);
}

int
read_buf(connect)
	struct gop_connect *connect;
{
	char            buf[500000];

	printf("\n\n\n\nAttente de data..... Tapez <CTRL>-C \n\n\n\n");
	if (gop_read(connect, buf, sizeof(buf)) < 0) {
		if (gop_errno == GOP_END_OF_MESSAGE) {
			if (gop_read_end_of_message(connect, buf, sizeof(buf)) < 0) {
				manage_gop_error("gop_write_command");
			}
			printf("Recu fin de message: >%s<\n", buf);
		} else {
			manage_gop_error("gop_write_command");
			return (GOP_KO);
		}
	}

	return (GOP_OK);
}

void
write_buf_(connect, status)
	struct gop_connect **connect;
	int            *status;
{
	*status = write_buf(*connect);
}

int
write_buf(connect)
	struct gop_connect *connect;
{
	char            buf[500000];

	printf("\n\n\n\nRenvoi des données..... Tapez <CTRL>-C \n\n\n\n");
	gop_set_to(connect, "server");
	if (gop_write(connect, buf, sizeof(buf), 4096, GOP_CHAR) != GOP_OK) {
		manage_gop_error("gop_write");
		return (GOP_KO);
	}
	if (client_interrupt != 0) {
		printf("\n\nL'ensemple des données n'a pas été envoyé\n");

		printf("END\n");
	}
	return (GOP_OK);
}



/*
 * HISTORY avec GNU
 */


extern char    *readline();

void
get_input_cmd_(prompt, line, ilen)
	char            prompt[];
char            line[];
int            *ilen;
{
	register int    i;
	char           *answer;

	do {
		answer = readline(prompt);
		strcpy(line, answer);

		for (*ilen=strlen(line)-1;*ilen>=0;(*ilen)--)
			if(*(line+*ilen) != ' ')break;

		*(line + ++(*ilen)) ='\0';
		if (*ilen != 0) {
			char           *expansion;
			int             result;

			using_history();

			result = history_expand(line, &expansion);
			if(strcmp(line, expansion)!=0)printf("%s\n",expansion);
			strcpy(line, expansion);
			*ilen = strlen(line);

			free(expansion);
			/*
			 * if (result) fprintf (stderr, "%s\n", line);
			 * 
			 * if (result < 0) continue;
			 */

			add_history(line);
		} else {
			register HIST_ENTRY **the_list = history_list();
			register int    i;

			if (the_list)
				for (i = 0; the_list[i]; i++)
					fprintf(stdout, "%d: %s\n", i + history_base, the_list[i]->line);
		}
	} while (*ilen == 0);
}

