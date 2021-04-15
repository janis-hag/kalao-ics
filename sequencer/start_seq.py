import seq_init
import seq_server


if __name__ == '__main__':

    if seq_init.initialisation() == 0:
        print("Initialisation OK.")
    else:
        print("Error: Initialisation failed")
        return 1

    seq_server.seq_server()

    return 0
