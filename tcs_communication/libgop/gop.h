#ifndef _GenevaObservatoryProto_H_
#define _GenevaObservatoryProto_H_

/*

historiques des versions:

A: original
B: reduction de struct gop_bench_xdr (on enleve short et double precision)
C: ajout de side dans struct gop_connect
   + transfert des PIDs en mode GOP_SOCKET_UNIX

*/

#define GOP_VERSION_CRT "C"
#define GOP_MIN(a,b)     ((a) < (b) ? (a) : (b))
#define GOP_MAX(a,b)     ((a) > (b) ? (a) : (b))
#define GOP_NM 10

#define GOP_TRUE 1
#define GOP_FALSE 0

#define GOP_STR_TRUE "T"
#define GOP_STR_FALSE "F"

struct gop_header {
	char		header_type;	/* type du header 'H' ou 'E' */
	char            version[2];	/* A-Z */
	char            class[5];	/* classe du message */
	char            date[15];	/* date de remplissage du header */
	char            from[9];	/* nom symbolique expediteur */
	char            to[9];		/* nom symbolique destinataire */
	char            hsync[2];	/* Flag pour la synchronisation du EDM */
	char            dsync[2];	/* Flag pour la synchronisation de la SDD */
	char            mode[2];	/* niveau de debug 0-9 */
	char            msize[11];	/* taille du message en byte */
	char            psize[11];	/* taille des paquet en byte */
	char            cont[2];	/* flag de continuation	 */
	char            stat[5];	/* status du systeme */
	char		datatype[2];	/* type de données de la SDD */
	char		xdr[2];		/* indique si la SDD est codée en XDR */
	char            end[2];
};

struct gop_list {
	unsigned long	nb;		/* nb de client/serveur dans la liste */
	int             timeout;	/* timeout pour le select */
	struct gop_connect *gop[GOP_NM];	/* liste */
};


struct gop_connect {
	/*
         * parametres lies a la connection
         */
	int             type;		/* type de connection */
	char            name[256];	/* nom du host a connecter */
	int             port;		/* port de communication */
	int		side;		/* 0=serveur 1=client 2=transmetteur */
	int		opcrt;		/* 0=read 1=write */
	int		interrupted;	/* 0=normal 1=interrupted */
	int             cd_init;	/* descripteur canal initial */
	int             cd;		/* descripteur canal actif */
	char            my_name[9];	/* mon nom symbolique */
	char            his_name[9];	/* nom symbolique du destinataire */
	int             maxpacket;	/* taille maximum des paquets sur cd */
	int             stamp;		/* flag TRUE pour écrire la date */
	int             need_xdr;	/* indique (TRUE) si le canal a besoin de XDR */
	int		pid;		/* pid du serveur */
	int             timeout;	/* timeout pour l'operation en cours */
	/*
         * parametres du header sous forme naturel (pas ASCII)
         */
	char            class[5];	/* classe du message */
	char            from[9];	/* nom symbolique expediteur */
	char            to[9];		/* nom symbolique destinataire */
	int             hsync;		/* Flag pour la synchronisation du EDM */
	int             dsync;		/* Flag pour la synchronisation de la SDD */
	int             mode;		/* niveau de debug 0-9 */
	int             msize;		/* taille message en byte */
	int             psize;		/* taille paquet en byte */
	int             cont;		/* flag de continuation	 */
	char            stat[5];	/* status du systeme */
	int             datatype;	/* type de données de la SDD */
	int             xdr;		/* indique si la SDD est codée en XDR */
	int             pthread;	/* indique si on est dans un pthread */
	/*
         * header courant
         */
	struct gop_header header;	/* header associe au canal */
};

struct gop_bench_xdr {
	int             j;		/* 4 bytes */
	float           l;		/* 4 bytes */
	double          m;		/* 8 bytes */
};

extern int      gop_errno;

/*
 * LISTE DES TYPES DE HEADER
 * ===========================================================================
 *
 */

#define	GOP_HEADER_STD	'H'
#define	GOP_HEADER_END	'E'
#define	GOP_HEADER_DAT	'D'
#define	GOP_HEADER_ACK	'A'

/*
 * LISTE ETAT
 * ===========================================================================
 *
 */

#define	GOP_OK	         0
#define	GOP_INTERRUPTED	 1
#define GOP_READ	 0
#define GOP_WRITE	 1
#define GOP_SELECT	 2


/*
 * LISTE SIDES
 * ===========================================================================
 *
 */

#define	GOP_SERVER_SIDE		1
#define	GOP_CLIENT_SIDE		2
#define	GOP_TRANSMIT_SIDE	3

/*
 * LISTE DES CLASSES
 * ===========================================================================
 *
 */

#define	GOP_CLASS_COMD	"COMD"
#define	GOP_CLASS_DATA	"DATA"
#define	GOP_CLASS_STAT	"STAT"
#define	GOP_CLASS_INFO	"INFO"
#define	GOP_CLASS_DBUG	"DBUG"
#define	GOP_CLASS_ACKN	"ACKN"
#define	GOP_CLASS_ALRM	"ALRM"
#define	GOP_CLASS_INIT	"INIT"

/*
 * LISTE DES ETATS
 * ===========================================================================
 *
 */

#define	GOP_STAT_OPOK	"OPOK"
#define	GOP_STAT_WARN	"WARN"
#define	GOP_STAT_RCOV	"RCOV"
#define	GOP_STAT_FTAL	"FTAL"
#define	GOP_STAT_BUSY	"BUSY"
#define	GOP_STAT_TIME	"TIME"

/*
 * LISTE DES TYPES DE COMMUNICATION
 * ===========================================================================
 *
 */

#define	GOP_SOCKET	1	/* socket internet */
#define	GOP_SOCKET_UNIX	2	/* socket unix */
#define	GOP_TPU		3	/* transputer sur sp */

/*
 * CHOIX DES MODES DE FONCTIONNEMENT
 * ===========================================================================
 *
 */

#define	GOP_SYNCHRO	GOP_TRUE	/* mode synchrone */
#define	GOP_ASYNCHRO	GOP_FALSE	/* mode asynchrone */


/*
 * LISTE DES TYPES DE DONNÉES
 * ===========================================================================
 *
 * Attention si on rajoute un type il faut modifier gop_struct_to_header()
 *
 */

#define	GOP_CHAR	0	/* 8 bits		 */
#define	GOP_USHORT	1	/* unsigned int 16 bits	 */
#define	GOP_SHORT	2	/* int 16 bits		 */
#define	GOP_UINT	3	/* unsigned int 32 bits	 */
#define	GOP_INT		4	/* int 32 bits	 	 */
#define	GOP_ULONG	5	/* unsigned int 64 bits	 */
#define	GOP_LONG	6	/* int 64 bits	 	 */
#define	GOP_FLOAT	7	/* real 32 bits		 */
#define	GOP_DOUBLE	8	/* real 64 bits		 */
#define GOP_STRUCT      9       /* structure             */

/*
 * LISTE DES CODES D'ERREUR
 * ===========================================================================
 *
 * attention en cas de modification dans cette liste, mettre a jour:
 * libgop.c:gop_get_error_str()
 */

#define GOP_OK			 0	/* Operation reussie */
#define GOP_KO			-1	/* Operation ratée */
#define GOP_ERRNO		 1	/* erreur systeme dans errno */
#define GOP_DISCONNECT		 2	/* Deconnection client*/
#define GOP_INVALID_VERSION	 3	/* version header invalide */
#define GOP_TIMEOUT		 4	/* Time out */
#define GOP_TOO_BIG		 5	/* message trop grand */
#define GOP_BAD_PROTOCOL	 6	/* protocole pas implémenté */
#define GOP_NOT_IMPLEMENTED	 7	/* protocole pas encore implémenté */
#define GOP_BROKEN_PIPE		 8	/* broken pipe lors d'un write */
#define GOP_BAD_SEQUENCE	 9	/* reception d'un bloc illegal */
#define GOP_RECEIVER_UNKNOWN	10	/* destinataire inconnu */
#define GOP_END_OF_MESSAGE	11	/* fin de message (FDM) */
#define GOP_ALLOC		12	/* problem d'allocation memoire */
#define GOP_ECONNRESET		13	/* deconnection client */
#define GOP_BAD_CHANNEL		14	/* mauvais canal d'initialisation */
#define GOP_XDR_FAILED		15	/* probleme avec convertion XDR */
#define GOP_REMOTE_PROBLEM	16	/* problème côté destinataire */
#define GOP_INTERRUPTED_SYSTEM_CALL	17	/* system call interrompu */
#define GOP_INTERRUPTED_TRANSMISSION	18	/* interruption par CTRL-C ou OOB */
#define GOP_EOM_TOO_BIG		19	/* end of message trop grand */
#define GOP_BLOCKING		20	/* communication bloquante */
#define GOP_TPU_ERROR_FLAG	21	/* error flag raised by transputer */
#define GOP_TPU_2		22	/* error tpu 2 */
#define GOP_TPU_3		23	/* error tpu 3 */
#define GOP_TPU_4		24	/* error tpu 4 */
#define GOP_TPU_5		25	/* error tpu 5 */
#define GOP_TPU_6		26	/* error tpu 6 */
#define GOP_TPU_7		27	/* error tpu 7 */
#define GOP_TPU_8		28	/* error tpu 8 */
#define GOP_TPU_9		29	/* error tpu 9 */
#define GOP_TPU_10		30	/* error tpu 10 */
#define GOP_BAD_HOST_NAME	31	/* nom de host non reconnu */


/*
 * LISTE DES VALEURS DE MODE (CONNECT.MODE) POUR L'AFFICHAGE
 * ===========================================================================
 *
 * chaque niveau implique le precedent
 */

#define GOP_NOTHING		0	/* pas d'affichage */

#define GOP_CONNECTION		1	/* operations de connection */
#define GOP_HEADER		2	/* affichage des headers et contenu pour type GOP_CHAR*/
#define GOP_MESSAGE		3	/* \t reception ou envoi d'un message */
#define GOP_POLL		4	/* operations sur poll() ou select() */
#define GOP_PACKET		5	/* \t\t reception ou envoi d'un paquet */
#define GOP_PACKET_INFO		6	/* \t\t info supplémentaires des paquets */
#define GOP_IO			7	/* \t\t\t operation entree/sortie */
#define GOP_IO_CONTENTS		8	/* \t\t\t contenu operation entree/sortie */

/*
 * PROTOTYPES
 * ===========================================================================
 *
 */

/* libgop.c */

extern int gop_system_rsh(char *, char *);
extern int gop_system(char *);
extern int gop_process_registration(char *, int , char *, int , int);
extern int gop_process_unregistration(char *);
extern void gop_process_registration_(char *, int *, char *, int *, int *);
extern void gop_process_unregistration_(char *);
extern int gop_printf(char *, ...);
extern void gop_registration_for_printf(void (*)());
extern void gop_unregistration_for_printf(void);
extern struct gop_connect *gop_alloc_connect_structure(void);
extern int gop_parse_opt_cmd_line(struct gop_connect *);
extern char *gop_get_error_str(void);
extern void gop_init_handler(int);
extern void gop_restore_handler(int);
extern void gop_set_destination(struct gop_connect *);
extern int gop_init_connection(struct gop_connect *);
extern int gop_accept_connection(struct gop_connect *);
extern int gop_connection(struct gop_connect *);
extern int gop_close_connection(struct gop_connect *);
extern int gop_close_init_connection(struct gop_connect *);
extern int gop_close_active_connection(struct gop_connect *);
extern int gop_echo_header(char *, char *, struct gop_header *);
extern int gop_header_write(struct gop_connect *);
extern int gop_h_read(struct gop_connect *);
extern int gop_header_read(struct gop_connect *);
extern int gop_select_destination(struct gop_connect *, struct gop_list *, struct gop_connect **);
extern int gop_data_section_write(struct gop_connect *, char *, int , int , int , int);
extern int gop_data_section_read(struct gop_connect *, char *, int , int , int , int , int);
extern int gop_select_active_channel(struct gop_list *, struct gop_list *);
extern int gop_select_active_channel_poll(struct gop_list *, struct gop_list *);
extern int gop_select_active_channel_select(struct gop_list *, struct gop_list *);
extern int gop_read(struct gop_connect *, char *, int);
extern void gop_handle_eom(struct gop_connect *, void (char *));
extern int gop_read_matrix(struct gop_connect *, char *, int , int , int , int);
extern int gop_read_data(struct gop_connect *, char *, int);
extern int gop_read_end_of_message(struct gop_connect *, char *, int);
extern int gop_write(struct gop_connect *, char *, int , int , int);
extern int gop_write_matrix(struct gop_connect *, char *, int , int , int , int , int , int);
extern int gop_write_command(struct gop_connect *, char *);
extern int gop_write_acknowledgement(struct gop_connect *, char *e, char *);
extern int gop_write_end_of_message(struct gop_connect *, char *);
extern int gop_forward(struct gop_connect *, struct gop_connect *, int , struct gop_list *);
extern int gop_forward_locked(struct gop_connect *, struct gop_connect *, int , struct gop_list *);
extern void gop_set_type(struct gop_connect *, int);
extern void gop_set_name(struct gop_connect *, char *);
extern void gop_set_port(struct gop_connect *, int);
extern void gop_set_maxpacket(struct gop_connect *, int);
extern void gop_set_class(struct gop_connect *, char *);
extern void gop_set_from(struct gop_connect *, char *);
extern void gop_set_to(struct gop_connect *, char *);
extern void gop_set_my_name(struct gop_connect *, char *);
extern void gop_set_his_name(struct gop_connect *, char *);
extern void gop_set_msize(struct gop_connect *, int);
extern void gop_set_psize(struct gop_connect *, int);
extern void gop_set_cont(struct gop_connect *, int);
extern void gop_set_stamp(struct gop_connect *, int);
extern void gop_set_hsync(struct gop_connect *, int);
extern void gop_set_dsync(struct gop_connect *, int);
extern void gop_set_stat(struct gop_connect *, char *);
extern void gop_set_mode(struct gop_connect *, int);
extern void gop_set_datatype(struct gop_connect *, int);
extern void gop_set_timeout(struct gop_connect *, int);
extern void gop_set_side(struct gop_connect *, int);
extern int gop_get_type(struct gop_connect *);
extern char *gop_get_name(struct gop_connect *);
extern char *gop_get_my_name(struct gop_connect *);
extern char *gop_get_his_name(struct gop_connect *);
extern int gop_get_port(struct gop_connect *);
extern int gop_get_maxpacket(struct gop_connect *);
extern char *gop_get_class(struct gop_connect *);
extern char *gop_get_from(struct gop_connect *);
extern char *gop_get_to(struct gop_connect *);
extern int gop_get_msize(struct gop_connect *);
extern int gop_get_psize(struct gop_connect *);
extern int gop_get_cont(struct gop_connect *);
extern int gop_get_stamp(struct gop_connect *);
extern int gop_get_hsync(struct gop_connect *);
extern int gop_get_dsync(struct gop_connect *);
extern char *gop_get_stat(struct gop_connect *);
extern int gop_get_mode(struct gop_connect *);
extern int gop_get_datatype(struct gop_connect *);
extern int gop_get_timeout(struct gop_connect *);
extern int gop_get_side(struct gop_connect *);
extern int gop_get_cd(struct gop_connect *);
extern int gop_get_cd_init(struct gop_connect *);
extern void gop_init_server_socket(struct gop_connect *, char *, int , int , int , int);
extern void gop_init_client_socket(struct gop_connect *, char *, char *, int , int , int , int);
extern void gop_init_server_socket_unix(struct gop_connect *, char *, char *, int , int , int);
extern void gop_init_client_socket_unix(struct gop_connect *, char *, char *, int , int , int);

extern int gop_tpu_init_connection(struct gop_connect *);
extern int gop_tpu_accept_connection(struct gop_connect *);
extern int gop_tpu_connection(struct gop_connect *);
extern int gop_tpu_close_connection(struct gop_connect *);
extern int gop_tpu_read(struct gop_connect *, char *, int);
extern int gop_tpu_write(struct gop_connect *, char *, int);


#endif /* _GenevaObservatoryProto_H_ */
