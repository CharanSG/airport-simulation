"""Class file for `RoutingExpert`."""
import logging
import cache

from link import Link
from route import Route


class RoutingExpert:
    """`RoutingExpert` contains the knownledge of providing routes between any
    two nodes in the airport surfact. It provides `get_shortest_route`
    interface for the scheduler to use for providing itineraries. The routes
    are precomputed and cached per airport.
    """

    def __init__(self, links, nodes, enable_cache):

        # Setups the logger
        self.logger = logging.getLogger(__name__)

        self.routing_table = {}

        # Adds the two ends of a links as a node as well
        for link in links:
            nodes.append(link.start)
            nodes.append(link.end)

        # Saves all the links and nodes
        self.links = links
        self.nodes = nodes
        self.logger.info("%d links and %d nodes are loaded",
                         len(self.links), len(self.nodes))

        # Builds or loads the routing table from cache
        if enable_cache:
            self.__build_or_load_routes()
        else:
            self.__build_routes()

    def __build_or_load_routes(self):

        hash_key = cache.get_hash(self.links, self.nodes)
        cached = cache.get(hash_key)

        if cached:
            self.routing_table = cached
            self.logger.debug("Cached routing table is loaded")
        else:
            # Builds the routes
            self.__build_routes()
            cache.put(hash_key, self.routing_table)

    def __build_routes(self):

        self.logger.debug("Starts building routes, # nodes: %d # links: %d",
                          len(self.nodes), len(self.links))
        self.__init_routing_table()

        # Step 1: Links two nodes with really short distance (using
        # is_close_to method)
        self.logger.debug("Starts linking close nodes")
        self.__link_close_nodes()

        # Step 2: Links the start and end node of the links
        self.logger.debug("Starts linking existing links")
        self.__link_existing_links()

        # Step 3: Applies Floyd–Warshall algorithm to get shortest routes for
        # all node pairs
        self.logger.debug("Starts floyd-warshall for finding shortest routes")
        self.__finds_shortest_route()

        # Prints result
        self.print_route()

    def __init_routing_table(self):

        # Initializes the routing table
        for start in self.nodes:
            self.routing_table[start] = {}
            for end in self.nodes:
                if start == end:
                    self.routing_table[start][end] = None
                else:
                    self.routing_table[start][end] = Route(start, end, [])

    def __link_close_nodes(self):

        counter = 0

        for start in self.nodes:
            for end in self.nodes:
                if start != end and start.is_close_to(end):
                    link = Link("CLOSE_NODE_LINK", [start, end])
                    self.routing_table[start][end].update_link(link)
                    self.logger.debug("%s and %s are close node", start, end)
                    counter += 1
                    if not self.routing_table[start][end].is_completed:
                        raise Exception("Unable to link two close nodes")

        self.logger.debug("Adds %d links for close nodes", counter)

    def __link_existing_links(self):

        for link in self.links:
            start = link.start
            end = link.end

            # If there's already a link exists, store the shortest one
            route = self.routing_table[start][end]
            route_rev = self.routing_table[end][start]
            if route.distance > link.length:
                route.update_link(link)
                route_rev.update_link(link.reverse)

            if not (self.routing_table[start][end].is_completed and
                    self.routing_table[end][start].is_completed):
                raise Exception("Unable to link two ends of a link from %s"
                                " to %s" % (start, end))

    def __finds_shortest_route(self):

        # Floyd-Warshall
        for k in self.nodes:
            for i in self.nodes:
                for j in self.nodes:

                    r_ij = self.routing_table[i][j]
                    r_ik = self.routing_table[i][k]
                    r_kj = self.routing_table[k][j]

                    # Ignores the nodes with no route in between
                    if r_ik is None or r_kj is None or r_ij is None:
                        continue

                    # Ignores the cases where i -> k or k -> j is not connected
                    if not r_ik.is_completed or not r_kj.is_completed:
                        continue

                    # Updates the i -> j route if i -> k -> j is shorter
                    if r_ik.distance + r_kj.distance < r_ij.distance:
                        r_ij.reset_links()
                        r_ij.add_links(r_ik.links)
                        r_ij.add_links(r_kj.links)

                        self.logger.debug("%s -> %s -> %s is shorter than "
                                          "%s -> %s", i, k, j, i, j)

    def print_route(self):
        """Prints all the routes into STDOUT."""

        for start in self.nodes:
            for end in self.nodes:
                self.logger.debug("[%s - %s]", start, end)
                route = self.routing_table[start][end]
                if route:
                    self.logger.debug(route.description)
                else:
                    self.logger.debug("No Route")

    def get_shortest_route(self, start, end):
        """Gets the shortest route by given start and end node."""
        if (start not in self.routing_table) or \
           (end not in self.routing_table[start]):
            return None
        return self.routing_table[start][end]

    def __getstate__(self):
        attrs = dict(self.__dict__)
        del attrs["logger"]
        return attrs

    def __setstate__(self, attrs):
        self.__dict__.update(attrs)

    def set_quiet(self, logger):
        """Sets this object into quiet mode where less logs are printed."""
        self.logger = logger
