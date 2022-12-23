# SetM3.py
# Set the set_focus of M3 (1=Coralie 2=Necam 3=Kalao)
#

from opcua import Client
from opcua import ua
from opcua.common import methods
from opcua.ua.uaerrors import UaError, BadNodeIdUnknown, BadSessionIdInvalid, BadTimeout
import time
import sys
import logging
import argparse

ready = 0  # global


class SubHandler(object):
    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another
    thread if you need to do such a thing
    """

    #
    # handler on the end of the state machines (looking at the "busy" state)
    #
    def datachange_notification(self, node, val, data):
        global ready
        print("%.6f" % (time.time()), "Datachange_notification: recu", val)
        if (not val):
            print("%.6f" % (time.time()), "Finished")
            ready = True


class plc():

    def manageCommand_Wait(self, client, nodeId):
        global ready  # updated by SubHandler
        print("%.6f" % (time.time()), "Waiting for SM completion")
        ready = False
        busyNode = client.get_node(nodeId + ".b_busy")
        print("%.6f" % (time.time()),
              "State of the node, b_busy boolean flag of the SM = ", busyNode,
              "value =", busyNode.get_value())
        handler = SubHandler()
        sub = client.create_subscription(100, handler)
        handle = sub.subscribe_data_change(busyNode)
        time.sleep(0.1)
        #
        # Wait for the end of the two SMs
        #
        timeCounter = 0
        incrementSecond = 0.1
        print("%.6f" % (time.time()), "Start, timeout 300[s]")

        while (True):
            if (ready):
                print("\n%.6f" % (time.time()), "Ready")
                sub.unsubscribe(handle)
                #
                #to avoid: "WARNING:opcua.client.ua_client.Socket:ServiceFault from
                #           server received while waiting for publish response"
                #
                logging.disable(level=logging.WARN)
                sub.delete()
                return (self.getStatus(client, nodeId))
            time.sleep(incrementSecond)
            timeCounter = timeCounter + incrementSecond
            print("%.1f[s]\r" % timeCounter,
                  end='')  # refresh elapsed time on the same line
            if (timeCounter > 300):
                sub.unsubscribe(handle)
                #
                #to avoid: "WARNING:opcua.client.ua_client.Socket:ServiceFault from
                #           server received while waiting for publish response"
                #
                logging.disable(level=logging.WARN)
                sub.delete()
                print("%.6f" % (time.time()), "Timeout (300[s])")
                return ("/KO/Timeout")

#-------------------------------------------------------------------------------

    def getStatus(self, client, nodeId):
        #
        # Returns the final status of a SM
        #
        #print ("%.6f"%(time.time()), "Status ", nodeId, "    : ", end='')
        if (client.get_node(nodeId + ".b_alarmed").get_value()):
            status = "/KO/"
        else:
            status = "/OK/"
        status = status + client.get_node(nodeId +
                                          ".s_currentStatus").get_value()
        return (status)


###########################################
#
# Main for interactive use
#
###########################################


def main(argv):
    focus = 0
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', help='set_focus: 1=Coralie 2=Necam 3=Kalao',
                        type=int, metavar='set_focus[1..3]')
    parser.add_argument('-r', help='rotation: go to position (coupled)',
                        type=float, metavar='-10.0..280.0')
    parser.add_argument('-l', help='linear: go to position ', type=float,
                        metavar='45.0..90.0')
    args = parser.parse_args()
    if (len(argv) == 0):
        parser.print_help()
        print("/KO/Bad input parameter")
        sys.exit()

    #if(set_focus == 0):
    #  print("exit")
    #  sys.exit()

    myplc = plc()

    try:
        client = Client("opc.tcp://10.10.132.66:4840")  # La Silla
        #client = Client("opc.tcp://10.10.133.64:4840")  # Geneve
        client.connect()

        if args.f is not None:
            #
            # set set_focus
            #
            focus = max(min(args.f, 3), 1)
            nodeId = "ns=4 ; s=MAIN.fb_MAIN_M3.fb_SP_SM_M3Move"
            client.get_node(nodeId +
                            ".i_arg1").set_value(int(focus),
                                                 ua.VariantType.Int32)
            print("set_focus set to = ", focus,
                  "     (0=undefined 1=Coralie 2=Necam 3=Kalao)")
            client.get_node(nodeId + ".b_requested").set_value(True)
            time.sleep(1.0)

            status = myplc.manageCommand_Wait(client, nodeId)
            print(status)

        if args.r is not None:
            rotation = max(min(args.r, 280.0), -5.0)
            nodeId = "ns=4 ; s=MAIN.fb_MAIN_M3.fb_SM_M3RotAblMoveAbsoluCoupled"

            client.get_node(nodeId +
                            ".f_arg1").set_value(rotation,
                                                 ua.VariantType.Double)
            print("set_focus rotation set to = ", rotation)
            client.get_node(nodeId + ".b_requested").set_value(True)
            time.sleep(1.0)

            status = myplc.manageCommand_Wait(client, nodeId)
            print(status)

        if args.l is not None:
            linear = max(min(args.l, 91.0), 44.0)
            nodeId = "ns=4 ; s=MAIN.fb_MAIN_M3.fb_SM_M3LinMoveAbsolu"

            client.get_node(nodeId +
                            ".f_arg1").set_value(linear, ua.VariantType.Double)
            print("set_focus linear set to = ", linear)
            client.get_node(nodeId + ".b_requested").set_value(True)
            time.sleep(1.0)

            status = myplc.manageCommand_Wait(client, nodeId)
            print(status)

    except (IOError) as e:
        errno, strerror = e.args
        print("%.6f" % (time.time()), "SetM3.py: IOError Exception:", str(e),
              "errno =", errno)
        client.disconnect()
        exit(-1)
    except UaError as e:
        print("%.6f" % (time.time()), "SetM3.py: UaError Exception: ", str(e))
        client.disconnect()
        exit(-1)
    except Exception as e:  # All other errors
        print("%.6f" % (time.time()),
              "SetM3.py: Exception (no OPC-UA error): ", str(e))
        client.disconnect()
        exit(-1)

    client.disconnect()
    sys.exit()


if __name__ == "__main__":
    main(sys.argv[1:])
