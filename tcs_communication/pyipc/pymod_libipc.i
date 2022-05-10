/* pymod_libipc.i */
/* Modul build:

swig -python pymod_libipc.i
gcc -c -fPIC -Wall -DUSE_STRERROR -DSELECT_CALL -DSYSV -DLINUX ../libipc/libipc.c  pymod_libipc_wrap.c -I../libipc -I../gop -I/home/weber/anaconda3/include/python3.6m
ld -shared libipc.o ../pymod_libgop/libgop.o pymod_libipc_wrap.o -o _pymod_libipc.so
*/

%module pymod_libipc
%include "cstring.i"


%{
#include "../libgop/gop.h"
#include "../libipc/ipcdef.h"
%}
%cstring_bounded_output(char *myCharOutput, 256);
%cstring_bounded_output(char *myCharOutput2, 256);


//
// Rem: OutChar sont les arguments de type (char *) en retour. Ils
// n ont pas besoin d être spécifiés sous Perl.
//
// Exemple:   @result=get_shm_kw(<my_key>);
//	     $result[0] == <status de get_shm_kw()>
//	     $result[1] == <content>
//
// 	     @result=get_shm_kw_n(<n>);
//	     $result[0] == <status de get_shm_kw_n()>
//	     $result[1] == <key>
//	     $result[2] == <content>
//
//
//--------Fonctions--------------------------------------------------------------
//
// Remarque: les fonctions retournent -1 en cas de d erreur
//
// Connection (coté client)
//
extern void	select_key_semid_block(int f_key);
//extern int	init_ipc_client(void);
extern int	init_semaphore(void);
extern int *	init_block(void);
extern void 	select_semid_block(int f_key, int f_semid, int *f_block);

extern int      init_ipc_remote_client(char *host, char *symb_name, char *rcmd, int  port);
extern void     select_for_remote(int key, int sd);
extern int      init_ipc_remote_client_final(void);

extern int      init_remote_client(char *host, char *symb_name, char *rcmd, int  port, int key);

//
// Macros-Operations sur sémaphores (coté client)
//
extern int	shm_wait(int timeout=0);		
extern int	shm_ack(void);
extern int	shm_wack(int timeout=0);	 	
extern int	shm_cont(void);
extern int	shm_free(void);
//
// Operations sur sémaphores
//
extern int	set_sem(int semnum, int val);
extern int	get_val_sem(int semnum);
extern int	get_ncount_sem(int semnum);
extern int	get_zcount_sem(int semnum);
extern int	get_cmd_sem_pid(int semnum);
//
// Keywords
//
extern int	ini_shm_kw(void);
extern int	put_shm_kw(char *key, char *content);
extern int	get_shm_kw(char *key, char *myCharOutput);
extern int	get_shm_kw_n(int i, char *myCharOutput, char *myCharOutput2);
//
// valeur (numerique) d erreur
//
extern int	put_shm_err(int val);
extern int	get_shm_err(int *OutInt);
//
// code (ascii) d erreur (get_shm_err_code() retourne la longueur)
//
extern int	put_shm_err_code(char *str);
extern int	get_shm_err_code(char *OutChar);
//
// texte (ascii) d erreur (get_shm_str_err() retourne la longueur)
//
extern int	put_shm_str_err(char *str);
extern int	get_shm_str_err(char *OutChar);
//
// flag de status (rem: le put est utilisé uniquement par le serveur))
//
extern int	put_shm_stat(int val);
extern int	get_shm_stat(int *OutInt);
//
// flag de ackno
//
extern int	get_shm_ackno(int *OutInt);
//
// Signaux
extern int	send_signal(int sig);
//
// Demande de pid
//
extern int	get_shm_pid_client(void);
extern int	get_shm_my_pid(void);
extern int	get_srv_pid(void);
//
// Demande de commande courante
//
extern int	get_shm_current_cmd(char *OutChar);
//
// Envoi de commande simplifie
//
extern int send_cmd(char *command, int timeouta, int timeoutb);
