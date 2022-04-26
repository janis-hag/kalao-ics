#include <stdio.h>
#include <gop.h>
#include <srvgop.h>

/*
 * test c pour libsrvgop.c
 * 
 * xsdbmanager -s -f libsrvgop.sdb &
 * 
 * cc -g libsrvgop.c -I. -c -L ~/lib/SunOS_5.4 -lgop -ltpudummy -lnsl -lsocket
 */

/**
main()
{
	int             ci = 0;
	char            answer[256];

	while (1) {
		ci = srvg_connect("aff", "test", "aff", 0, "", 0, 0, 1, 1);
		if (ci < 0) {
			printf("ci == 0 == > exit\n");
			exit(-1);
		}
		if(srvg_write(ci, "LOAD|../inter/ramp.bdf") != GOP_OK){
			printf("%s\n", srvg_get_error_string());
			exit(-1);
		}
			
		if(srvg_read(ci, answer, sizeof(answer)) < GOP_OK){
			printf("%s\n", srvg_get_error_string());
			exit(-1);
		}
		if(srvg_write(ci, "RCUR") != GOP_OK){
			printf("%s\n", srvg_get_error_string());
			exit(-1);
		}
		if(srvg_read(ci, answer, sizeof(answer)) < GOP_OK){
			printf("%s\n", srvg_get_error_string());
			exit(-1);
		}
		printf(">%s< \n", answer);
		srvg_disconnect(ci);
	}
}
*/

main()
{
	int             i;
	int             ci = 0;
	char            answer[256];
	char		gop_stat[8];
	char		gop_class[8];
	int		ilen;

	ci = srvg_connect("", "test_c", "libsrvgop", 0, "", 2, 0, 1, 1);
	if (ci < 0) {
		printf("ci == 0 == > exit\n");
		exit(-1);
	}
	if (srvg_verbose(ci, 0) != GOP_OK) {
		printf("%s\n", srvg_get_error_string());
		exit(-1);
	}
	for (i = 0; i < 100; i++) {
		if (srvg_write(ci, "read VALUE") != GOP_OK) {
			printf("%s\n", srvg_get_error_string());
			exit(-1);
		}
		if ((ilen=srvg_read(ci, answer, sizeof(answer), gop_stat, gop_class, 0)) < GOP_OK) {
			printf("%s\n", srvg_get_error_string());
			exit(-1);
		}
		printf("answer = >%s< status=%d gop_stat = >%s< gop_class = >%s<\n", answer, ilen, gop_stat, gop_class);
	}
	srvg_disconnect(ci);
}
