/* C */

extern int
srvg_connect(char *server_command,
	     char *client_name,
	     char *socket_name,
	     int port,
	     char *host,
	     int verbose,
	     int timeout,
	     int hsync,
	     int dsync);

extern int
srvg_disconnect(int ci);

extern int
srvg_write(int ci,
	   char *str);
extern int
srvg_write_bin(int ci, char *str);

extern int
srvg_read(int ci,
	  char *str,
	  int sizeofstr,
	  char *stat,
	  char *class,
	  int timeout);

extern char
*srvg_get_error_string(void);

extern int
srvg_get_gop_errno(void);

extern int
srvg_verbose(int ci,
	     int verbose);

/* Fortran */

extern void
srvg_connect_(char *server_command,
	      char *client_name,
	      char *socket_name,
	      int *port,
	      char *host,
	      int *verbose,
	      int *timeout,
	      int *hsync,
	      int *dsync,
	      int *ci);

extern void
srvg_disconnect_(int *ci,
		 int *status);

extern void
srvg_write_(int *ci,
	    char *str,
	    int *status);

extern void
srvg_write_bin_(int *ci, char *str, int *status);

extern void
srvg_read_(int *ci,
	   char *str,
	   int *sizeofstr,
	   char *gop_stat,
	   char *gop_class,
	   int *timeout,
	   int *status);

extern void
srvg_get_error_string_(char *str,
		       int *ilen);

extern void
srvg_get_gop_errno_(int *gop_errno);


extern void
srvg_verbose_(int *ci,
	      int *verbose,
	      int *status);
