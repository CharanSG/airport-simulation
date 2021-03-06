"""Class file for `Link`."""
from config import Config
from utils import str2sha1
from id_generator import get_new_link_id


class Link:
    """`Link` is one of the most important class in our link-node model which
    is represent a link composed by a list of nodes.
    """

    def __init__(self, name, nodes):

        if len(nodes) < 2:
            raise Exception("Less than two nodes were given")

        if name is None or not name:
            name = "l-id-" + str(get_new_link_id())

        self.name = name
        self.nodes = nodes
        self.hash = str2sha1("%s#%s" % (self.name, self.nodes))

    @property
    def length(self):
        """Returns the physical length of this link in feets."""
        length = 0.0
        for i in range(1, len(self.nodes)):
            from_node = self.nodes[i - 1]
            to_node = self.nodes[i]
            length += from_node.get_distance_to(to_node)
        return length

    @property
    def start(self):
        """Returns the start node of this link."""
        return self.nodes[0]

    @property
    def end(self):
        """Returns the end node of this link."""
        return self.nodes[len(self.nodes) - 1]

    @property
    def reverse(self):
        """Reverses the node orders, which means the start and end are switched.
        """
        return Link(self.name, self.nodes[::-1])

    def contains_node(self, node):
        """Returns true if this link contains a given `node`."""
        if self.start.is_close_to(node) or self.end.is_close_to(node):
            return False
        return self.contains_node_at(node) is not None

    def contains_node_at(self, node):
        """Returns the index of the given node in this link."""

        for i in range(len(self.nodes) - 1):
            src, dst = self.nodes[i], self.nodes[i + 1]
            if self.contains_node_on_segment(src, dst, node):
                return i

        return None

    @classmethod
    def contains_node_on_segment(cls, src, dst, node):
        """Returns true of a given node in contained by this link between `src`
        and `dst`.
        """

        threshold = Config.params["simulation"]["close_node_link_threshold"]
        return (src.get_distance_to(node) + dst.get_distance_to(node) -
                src.get_distance_to(dst)) < threshold

    def break_at(self, node):
        """Breaks this link into two links at a given `node`. An expection is
        raised if the node isn't be contained by this link.
        """

        if not self.contains_node(node):
            raise Exception("%s is not on %s" % (node, self))

        if self.start.is_close_to(node) or self.end.is_close_to(node):
            return [self]

        marker = self.contains_node_at(node)

        # First part
        nodes_first = []
        for i in range(marker + 1):
            nodes_first.append(self.nodes[i])
        nodes_first.append(node)

        # Second part
        nodes_second = [node]
        for i in range(marker + 1, len(self.nodes)):
            nodes_second.append(self.nodes[i])

        return (Link(self.name + "-b1", nodes_first),
                Link(self.name + "-b2", nodes_second))

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        return self.hash == other.hash

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return "<Link: " + self.name + ">"
