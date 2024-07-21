# DAG visualization.

from pyvis.network import Network

def render(mapper, title='', only_active=False):
    nt = Network('600px', '800px', notebook=True, directed=True, cdn_resources="in_line",heading=title)
    # , select_menu=True

    # event cnt
    e_cnt=0

    for name,node in mapper._node_name_map.items():
        if node.is_active:
            nt.add_node(node.id, label=name, color='red')
        else:
            # process event expression
            if len(name.split(' ')) >= 3:  # at least three words
                nt.add_node(node.id, label=name, color='green')
                node.set_active()
                e_cnt+=1
            if not only_active:
                nt.add_node(node.id, label=name) # nature design node, or event with less than 3 words, as blue.

    for name, node in mapper._node_name_map.items():
        for c in node._children:
            if not only_active:
                nt.add_edge(node.id, c.id)
            else:
                if node.is_active and c.is_active:
                    nt.add_edge(node.id, c.id)

    status={'event_cnt':e_cnt}

    return nt, status



