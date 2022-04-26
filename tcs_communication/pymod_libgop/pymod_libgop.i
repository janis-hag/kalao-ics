/* pymod_libgop.i */
/* Modul build:

swig -python pymod_libgop.i
gcc -c -fPIC -Wall -DUSE_STRERROR -DSELECT_CALL -DSYSV -DLINUX ../gop/libgop.c  pymod_libgop_wrap.c -I../gop -I/home/weber/anaconda3/include/python3.6m
ld -shared libgop.o pymod_libgop_wrap.o -o _pymod_libgop.so
*/

%module pymod_libgop
%include "cstring.i"

%{
#include "../libgop/gop.h"
%}
%cstring_mutable(char *myCharOutput);

extern int      gop_errno;
extern char *gop_get_error_str(void);

extern int gop_process_registration(char *, int , char *, int , int);
extern struct gop_connect *gop_alloc_connect_structure(void);

// init client side
extern int gop_connection(struct gop_connect *);
// init server side
extern int gop_init_connection(struct gop_connect *);
extern int gop_accept_connection(struct gop_connect *);



// socket inet (with host:port)
extern void gop_init_server_socket(struct gop_connect *, char *, int, int , int , int);
extern void gop_init_client_socket(struct gop_connect *, char *, char *, int, int , int , int);
// socket Unix (socket name)
extern void gop_init_server_socket_unix(struct gop_connect *, char *, char *, int , int , int);
extern void gop_init_client_socket_unix(struct gop_connect *, char *, char *, int , int , int);

extern int gop_close_connection(struct gop_connect *);
extern int gop_close_init_connection(struct gop_connect *);
extern int gop_close_active_connection(struct gop_connect *);

extern int gop_read(struct gop_connect *, char * myCharOutput, int);


extern int gop_write_command(struct gop_connect *, char *);
extern int gop_get_cd(struct gop_connect *);
