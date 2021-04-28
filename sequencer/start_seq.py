from sequencer import seq_init
from sequencer import seq_server


if __name__ == '__main__':

    if seq_init.initialisation() == 0:
        print("Initialisation OK.")
    else:
        print("Error: Initialisation failed")

    seq_server.seq_server()
