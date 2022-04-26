#define NB_KW_MAX		256
#define KW_SIZE			12
#define CONTENT_SIZE		128

#define FORK_PROCESS		1
#define NO_FORK_PROCESS		0

#define WAIT_FOR_ANSWER		1
#define NO_WAIT_FOR_ANSWER 	0

struct key_rec  {
	char	key[KW_SIZE];
	char	content[CONTENT_SIZE];
	};

struct	block_kw{
	int		pid_server;
	int		pid_client;
	int		ackno;
	int		stat_server;
	int		err_server;
	char		err_code[80];
	char		current_cmd[20];
	char		err_str_server[256];
	struct key_rec	line[NB_KW_MAX];
	};


/* libipc.c */
extern char *alloc_block_shm(int *ft_shm);
extern char *alloc_matrix_shm(int shmsize);
extern char *get_block_shm(int *ft_shm);
extern char *my_getdate(int semid);
extern int ask_and_init_shm(int semid, struct block_kw *block, float **pointer, int timeouta, int timeoutb);
extern int create_semaphore(int flag_init_server);
extern int dec_sem(int semid, int semnum, int timeout);
extern int dec_sem_nowait(int semid, int semnum);
extern int dec_sem_zero(int semid, struct block_kw *block, int timeout);
extern int dettach_matrix_shm(void);
extern int discard_semaphore_and_shm(int semid);
extern int get_cmd_sem(int semid, int semnum, int cmd);
extern int get_cmd_sem_pid(int semnum);
extern int get_ncount_sem(int semnum);
extern int get_semaphore(void);
extern int get_sem_block(int *semid, struct block_kw **block);
extern int get_server_value(int semid, struct block_kw *block, char *command, char *content, int timeouta, int timeoutb);
extern int get_shm_ackno(int *val);
extern int get_shm_block_kw_n(struct block_kw *block, int i, char key[], char content[]);
extern int get_shm_block_kw(struct block_kw *block, char key[], char content[]);
extern int get_shm_current_cmd(char *str);
extern int get_shm_err_code(char *str);
extern int get_shm_err(int *val);
extern int get_shm_kw(char *key, char *content);
extern int get_shm_kw_n(int i, char *key, char *content);
extern int get_shm_my_pid(void);
extern int get_shm_pid_client(void);
extern int get_shm_stat(int *val);
extern int get_shm_str_err(char *str);
extern int get_srv_pid();
extern int get_val_sem(int semnum);
extern int get_zcount_sem(int semnum);
extern int inc_sem(int semid, int semnum);
extern int ini_shm_block_kw(struct block_kw *block);
extern int ini_shm_kw(void);
extern int *init_block(void);
extern int init_semaphore(void);
extern int init_sem_block(int *semid, struct block_kw **block, int flag_init_server);
extern int kill_block_shm(int ft_shm);
extern int kill_matrix_shm(void);
extern int kill_semaphore(int semid);
extern int put_shm_block_kw(struct block_kw *block, char key[], char content[]);
extern int put_shm_err_code(char *str);
extern int put_shm_err(int val);
extern int put_shm_kw(char *key, char *content);
extern int put_shm_stat(int val);
extern int put_shm_str_err(char *str);
extern void put_shm_str_err_(char *str, int *status);
extern int send_command(int semid, struct block_kw *block, char cmd[], int wait, int ackno, int timeout);
extern int send_command_ready(int semid, struct block_kw *block, char cmd[]);
extern int send_ctrlc(struct block_kw *block);
extern int send_signal(int sig);
extern int server_free_ressource(int semid);
extern int set_sem(int semnum, int val);
extern int setval_sem(int semid, int semnum, int value);
extern int shm_ack(void);
extern int shm_cont(void);
extern int shm_free(void);
extern int shm_init_ipc_client(void);
extern int shm_wack(int timeout);
extern int shm_wait(int timeout);
extern int show_shm_block_kw(struct block_kw *block);
extern int srvexis();
extern int test_inc_sem(int semid, int semnum);
extern int wait_for_sem(int semid, int semnum, int timeout);
extern int wait_for_sem_nowait(int semid, int semnum);
extern int which_signal_caught(void);
extern int write_read_to_ipc_server(char *string, char *retstr);
extern int write_to_ipc_server(char *string);
extern void ask_and_init_shm_BUG_COMPILATION_(float *pointer, int *timeouta, int *timeoutb, int *status);
extern void decremente_sem_(int *semnum, int *timeout, int *status);
extern void dec_sem_nowait_(int semid, int semnum, int *status);
extern void dettach_mat_shm_(int *status);
extern void discard_semaphore_and_shm_(int *status);
extern void get_key_(int *f_key);
extern void get_ncount_sem_(int *semnum, int *val);
extern void get_shm_ackno_(int *val, int *status);
extern void get_shm_current_cmd_(char *str, int *ilen, int *status);
extern void get_shm_err_code_(char *str, int *ilen);
extern void get_shm_err_(int *val, int *status);
extern void get_shm_kw_(char *key, char *content, int *ilen, int *status);
extern void get_shm_kw_n_(int *i, char *key, int *keylen, char *content, int *conlen, int *status);
extern void get_shm_my_pid_(int *val);
extern void get_shm_pid_client_(int *val);
extern void get_shm_stat_(int *val, int *status);
extern void get_shm_str_err_(char *str, int *ilen);
extern void get_srv_pid_(int *pid);
extern void get_val_sem_(int *semnum, int *val);
extern void get_zcount_sem_(int *semnum, int *val);
extern void incremente_sem_(int *semnum, int *status);
extern void ini_shm_kw_(int *status);
extern void init_ipc_client_(int *f_semid, struct block_kw **f_block, int *status);
extern int init_remote_client(char *host, char *symb_name, char *rcmd, int  port, int semkey);
extern int  init_ipc_remote_client(char *host, char *symb_name, char *rcmd, int port);
extern int  init_ipc_remote_client_final(void);
extern void init_ipc_remote_client_(char *host, char *symb_name, char *rcmd, int *port, int *sd_current, int *status);
extern void init_ipc_server_(int *f_semid, struct block_kw **f_block, int *client_waiting, int *status);
extern void init_shm_(int *isize, char **ptr, int *status);
extern void invalid_remote(char *str);
extern void ipc_alive_(int *status);
extern void kill_mat_shm_(int *status);
extern void perl_shm_wait(void);
extern void print_delay(void);
extern void put_shm_current_cmd_(char *str, int *status);
extern void put_shm_err_code_(char *str, int *status);
extern void put_shm_err_(int *val, int *status);
extern void put_shm_kw_(char *key, char *content, int *status);
extern void put_shm_stat_(int *val, int *status);
extern void select_for_remote(int key, int sd);
extern void select_for_remote_(int *key, int *sd);
extern void select_key_semid_block(int f_key);
extern void select_matrix_key_(int *f_key);
extern void select_semid_block(int f_key, int f_semid, int *f_block);
extern void select_semid_block_(int *f_key, int *f_semid, struct block_kw **f_block);
extern int  send_cmd(char *command, int timeouta, int timeoutb);
extern void send_cmd_(char *command, int *timeouta, int *timeoutb, int *status);
extern void send_cmd_no_wait_(char *command, int *timeout, int *status);
extern void send_signal_(int *sig, int *status);
extern void server_free_ressource_(int *status);
extern void set_sem_(int *semnum, int *val, int *status);
extern void shm_ack_(int *status);
extern void shm_cont_(int *status);
extern void shm_free_(int *status);
extern void shm_wack_(int *timeout, int *status);
extern void shm_wait_(int *timeout, int *status);
extern void sho_shm_kw_(int *status);
extern void srvexis_(int *flag);
extern void this_signal_was_caught_(int *sig);
extern void this_signal_was_caught(int sig);
extern void which_signal_caught_(int *sig);
extern void init_ipc_client(int *f_semid, struct block_kw ** f_block, int *status);
