from kalao.plc import core

from opcua import ua


@core.beckhoff_autoconnect
def print_node_tree(node, short=True, beck=None):
    node = beck.get_node(node)

    def print_children(node, prefix):
        children = node.get_children()
        for i, c in enumerate(
                sorted(
                    children, key=lambda c: str(c.get_node_class() != ua.
                                                NodeClass.Variable) + str(c))):
            if i == len(children) - 1:
                prefix_current = prefix + ' └── '
                prefix_next = prefix + '    '
            else:
                prefix_current = prefix + ' ├── '
                prefix_next = prefix + ' │  '

            if c.get_node_class() == ua.NodeClass.Variable:
                value = ' = ' + str(c.get_value())
            else:
                value = ''

            if short:
                node_name = str(c).split('.')[-1]
            else:
                node_name = str(c)

            print(prefix_current + node_name + value)
            print_children(c, prefix_next)

    print(' ' + str(node))
    print_children(node, '')


print_node_tree('ns=4;s=MAIN')
