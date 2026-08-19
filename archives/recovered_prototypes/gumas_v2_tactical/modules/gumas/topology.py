#!/usr/bin/env python3
"""
GUMAS L2 Galaxy Topology System v2.0
Anchor: GUMAS-TOPOLOGY-V2
Seed: EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP: L2_ENGINE_CORE

Manages the galaxy's physical structure — star systems connected by hyperlanes,
with movement constraints, chokepoints, and strategic control.
"""

from typing import Dict, List, Optional
from collections import deque
from modules.gumas.models import (
    TopologyNode,
    HyperlaneEdge,
    GalaxyTopology,
    HyperlaneType,
    LocationType,
    CertaintyTag,
)


class TopologyManager:
    """
    Manages galaxy topology operations: pathfinding, distance calculation,
    strategic analysis, and control updates.
    """

    def __init__(self, topology: GalaxyTopology):
        """
        Initialize topology manager.

        Args:
            topology: GalaxyTopology containing nodes and edges
        """
        self.topology = topology
        self._build_reverse_adjacency()

    def _build_reverse_adjacency(self) -> None:
        """Build reverse adjacency mapping for bidirectional traversal."""
        self.reverse_adjacency: Dict[str, List[str]] = {}
        for node_id in self.topology.nodes:
            self.reverse_adjacency[node_id] = []

        for node_id, neighbors in self.topology.adjacency.items():
            for neighbor in neighbors:
                if neighbor not in self.reverse_adjacency:
                    self.reverse_adjacency[neighbor] = []
                if node_id not in self.reverse_adjacency[neighbor]:
                    self.reverse_adjacency[neighbor].append(node_id)

    def get_neighbors(self, node_id: str) -> List[str]:
        """
        Get all neighbors of a node.

        Args:
            node_id: Node identifier

        Returns:
            List of neighboring node IDs
        """
        return self.topology.adjacency.get(node_id, [])

    def get_path(self, from_node: str, to_node: str) -> List[str]:
        """
        Get shortest path using BFS.

        Args:
            from_node: Starting node ID
            to_node: Destination node ID

        Returns:
            List of node IDs representing path (empty if unreachable)
        """
        if from_node == to_node:
            return [from_node]

        if from_node not in self.topology.nodes or to_node not in self.topology.nodes:
            return []

        queue = deque([(from_node, [from_node])])
        visited = {from_node}

        while queue:
            current, path = queue.popleft()

            for neighbor in self.get_neighbors(current):
                if neighbor == to_node:
                    return path + [to_node]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return []

    def get_distance(self, from_node: str, to_node: str) -> int:
        """
        Get hop count distance between nodes.

        Args:
            from_node: Starting node ID
            to_node: Destination node ID

        Returns:
            Hop count (0 if same node, -1 if unreachable)
        """
        if from_node == to_node:
            return 0

        path = self.get_path(from_node, to_node)
        if not path:
            return -1

        return len(path) - 1

    def get_travel_time(self, from_node: str, to_node: str) -> float:
        """
        Get travel time along shortest path.

        Args:
            from_node: Starting node ID
            to_node: Destination node ID

        Returns:
            Sum of edge travel times (0.0 if unreachable or same node)
        """
        if from_node == to_node:
            return 0.0

        path = self.get_path(from_node, to_node)
        if not path or len(path) < 2:
            return 0.0

        total_time = 0.0
        for i in range(len(path) - 1):
            from_n = path[i]
            to_n = path[i + 1]

            # Find edge
            edge_key = None
            for eid, edge in self.topology.edges.items():
                if (edge.from_node == from_n and edge.to_node == to_n) or \
                   (edge.from_node == to_n and edge.to_node == from_n):
                    edge_key = eid
                    break

            if edge_key:
                total_time += self.topology.edges[edge_key].travel_time
            else:
                return 0.0

        return total_time

    def get_chokepoints(self) -> List[str]:
        """
        Get all chokepoint nodes.

        Chokepoints are nodes with >= 3 edges AND is_chokepoint=True.

        Returns:
            List of chokepoint node IDs
        """
        chokepoints = []
        for node_id, node in self.topology.nodes.items():
            edge_count = len(self.get_neighbors(node_id))
            if edge_count >= 3 and node.is_chokepoint:
                chokepoints.append(node_id)
        return chokepoints

    def get_faction_territory(self, faction_id: str) -> List[str]:
        """
        Get all nodes controlled by faction.

        Args:
            faction_id: Faction identifier

        Returns:
            List of controlled node IDs
        """
        territory = []
        for node_id, node in self.topology.nodes.items():
            if node.owner_faction == faction_id:
                territory.append(node_id)
        return territory

    def get_border_nodes(self, faction_a: str, faction_b: str) -> List[str]:
        """
        Get nodes of faction_a adjacent to faction_b's territory.

        Args:
            faction_a: First faction ID
            faction_b: Second faction ID

        Returns:
            List of faction_a border nodes adjacent to faction_b
        """
        faction_b_territory = set(self.get_faction_territory(faction_b))
        border = []

        for node_id in self.get_faction_territory(faction_a):
            neighbors = self.get_neighbors(node_id)
            if any(n in faction_b_territory for n in neighbors):
                border.append(node_id)

        return border

    def get_contested_lanes(self) -> List[str]:
        """
        Get all contested hyperlanes.

        Returns:
            List of contested edge IDs
        """
        contested = []
        for edge_id, edge in self.topology.edges.items():
            if edge.is_contested:
                contested.append(edge_id)
        return contested

    def can_reach(self, from_node: str, to_node: str) -> bool:
        """
        Check if two nodes are connected.

        Args:
            from_node: Starting node ID
            to_node: Destination node ID

        Returns:
            True if reachable, False otherwise
        """
        if from_node == to_node:
            return True

        return self.get_distance(from_node, to_node) >= 0

    def get_strategic_value(self, node_id: str) -> float:
        """
        Get strategic value of a node.

        Args:
            node_id: Node identifier

        Returns:
            Strategic value (0-1)
        """
        if node_id not in self.topology.nodes:
            return 0.0

        return self.topology.nodes[node_id].strategic_value

    def update_node_control(self, node_id: str, new_faction: str) -> None:
        """
        Update node's controlling faction.

        Args:
            node_id: Node identifier
            new_faction: New controlling faction ID (or None for uncontrolled)
        """
        if node_id in self.topology.nodes:
            self.topology.nodes[node_id].owner_faction = new_faction

    def update_lane_contest(self, edge_id: str, contested: bool) -> None:
        """
        Update lane contested status.

        Args:
            edge_id: Edge identifier
            contested: True if lane is contested, False otherwise
        """
        if edge_id in self.topology.edges:
            self.topology.edges[edge_id].is_contested = contested

    def calc_supply_route_security(self, from_node: str, to_node: str) -> float:
        """
        Calculate average security of edges along shortest path.

        Security is derived from edge capacity (proxy for fortification).
        Contested lanes reduce security by 50%.

        Args:
            from_node: Starting node ID
            to_node: Destination node ID

        Returns:
            Average route security (0-1)
        """
        if from_node == to_node:
            return 1.0

        path = self.get_path(from_node, to_node)
        if not path or len(path) < 2:
            return 0.0

        security_values = []
        for i in range(len(path) - 1):
            from_n = path[i]
            to_n = path[i + 1]

            # Find edge
            edge_key = None
            for eid, edge in self.topology.edges.items():
                if (edge.from_node == from_n and edge.to_node == to_n) or \
                   (edge.from_node == to_n and edge.to_node == from_n):
                    edge_key = eid
                    break

            if edge_key:
                edge = self.topology.edges[edge_key]
                # Base security from capacity (normalize 0-10 to 0-1)
                base_security = min(1.0, edge.capacity / 10.0)
                # Contested lanes reduce security
                if edge.is_contested:
                    base_security *= 0.5
                security_values.append(base_security)
            else:
                return 0.0

        return sum(security_values) / len(security_values) if security_values else 0.0


def build_canonical_topology() -> GalaxyTopology:
    """
    Build the canonical galaxy map with all systems and hyperlanes.

    Returns:
        GalaxyTopology with 20 nodes and 22 edges
    """
    nodes: Dict[str, TopologyNode] = {}
    edges: Dict[str, HyperlaneEdge] = {}
    adjacency: Dict[str, List[str]] = {}

    # Create nodes
    nodes["GU-CORE-01"] = TopologyNode(
        node_id="GU-CORE-01",
        name="Union Capital System",
        location_type=LocationType.SYSTEM,
        owner_faction="galactic_union",
        strategic_value=1.0,
        resources={},
        population=0.9,
        defense_level=0.8,
        is_chokepoint=False,
        certainty=CertaintyTag.CANON,
    )

    nodes["GU-CORE-02"] = TopologyNode(
        node_id="GU-CORE-02",
        name="Union Industrial Hub",
        location_type=LocationType.SYSTEM,
        owner_faction="galactic_union",
        strategic_value=0.7,
        resources={},
        population=0.7,
        defense_level=0.6,
        is_chokepoint=False,
        certainty=CertaintyTag.CANON,
    )

    nodes["GU-CORE-03"] = TopologyNode(
        node_id="GU-CORE-03",
        name="Union Science District",
        location_type=LocationType.SYSTEM,
        owner_faction="galactic_union",
        strategic_value=0.6,
        resources={},
        population=0.5,
        defense_level=0.5,
        is_chokepoint=False,
        certainty=CertaintyTag.CANON,
    )

    nodes["GU-LOG-01"] = TopologyNode(
        node_id="GU-LOG-01",
        name="Nexus Citadel System",
        location_type=LocationType.SYSTEM,
        owner_faction="prime_construct",
        strategic_value=0.9,
        resources={},
        population=0.4,
        defense_level=0.9,
        is_chokepoint=True,
        certainty=CertaintyTag.CANON,
    )

    nodes["AI-FRINGE-01"] = TopologyNode(
        node_id="AI-FRINGE-01",
        name="Broken Fringe",
        location_type=LocationType.SYSTEM,
        owner_faction="ai_warlord",
        strategic_value=0.5,
        resources={},
        population=0.2,
        defense_level=0.4,
        is_chokepoint=False,
        certainty=CertaintyTag.CANON,
    )

    nodes["VEL-CORE-01"] = TopologyNode(
        node_id="VEL-CORE-01",
        name="Velar Imperial Core",
        location_type=LocationType.SYSTEM,
        owner_faction="velar_imperium",
        strategic_value=0.9,
        resources={},
        population=0.7,
        defense_level=0.8,
        is_chokepoint=False,
        certainty=CertaintyTag.CANON,
    )

    nodes["VEL-BORDER-01"] = TopologyNode(
        node_id="VEL-BORDER-01",
        name="Velar Outer Marches",
        location_type=LocationType.SYSTEM,
        owner_faction="velar_imperium",
        strategic_value=0.6,
        resources={},
        population=0.3,
        defense_level=0.6,
        is_chokepoint=True,
        certainty=CertaintyTag.CANON,
    )

    nodes["OUTER-01"] = TopologyNode(
        node_id="OUTER-01",
        name="Frontier Haven",
        location_type=LocationType.SYSTEM,
        owner_faction="outer_colonies",
        strategic_value=0.4,
        resources={},
        population=0.5,
        defense_level=0.3,
        is_chokepoint=False,
        certainty=CertaintyTag.CANON,
    )

    nodes["ZYP-TRADE-01"] = TopologyNode(
        node_id="ZYP-TRADE-01",
        name="Zyphari Trade Nexus",
        location_type=LocationType.SYSTEM,
        owner_faction="zyphari_compact",
        strategic_value=0.8,
        resources={},
        population=0.6,
        defense_level=0.5,
        is_chokepoint=True,
        certainty=CertaintyTag.CANON,
    )

    nodes["ELARI-01"] = TopologyNode(
        node_id="ELARI-01",
        name="Luminous Reach",
        location_type=LocationType.SYSTEM,
        owner_faction="elari_ascendancy",
        strategic_value=0.5,
        resources={},
        population=0.7,
        defense_level=0.4,
        is_chokepoint=False,
        certainty=CertaintyTag.CANON,
    )

    nodes["VORRAN-01"] = TopologyNode(
        node_id="VORRAN-01",
        name="Resonance Cluster",
        location_type=LocationType.SYSTEM,
        owner_faction="vorran_clans",
        strategic_value=0.4,
        resources={},
        population=0.6,
        defense_level=0.4,
        is_chokepoint=False,
        certainty=CertaintyTag.CANON,
    )

    nodes["KAELAR-01"] = TopologyNode(
        node_id="KAELAR-01",
        name="Ink Sanctum System",
        location_type=LocationType.SYSTEM,
        owner_faction="kaelar_orders",
        strategic_value=0.3,
        resources={},
        population=0.4,
        defense_level=0.3,
        is_chokepoint=False,
        certainty=CertaintyTag.CANON,
    )

    nodes["THARAX-01"] = TopologyNode(
        node_id="THARAX-01",
        name="Driftfront Nexus",
        location_type=LocationType.SYSTEM,
        owner_faction="tharaxian_nomads",
        strategic_value=0.3,
        resources={},
        population=0.3,
        defense_level=0.2,
        is_chokepoint=False,
        certainty=CertaintyTag.CANON,
    )

    nodes["SEP-01"] = TopologyNode(
        node_id="SEP-01",
        name="Separatist Bastion",
        location_type=LocationType.SYSTEM,
        owner_faction="separatist_confed",
        strategic_value=0.5,
        resources={},
        population=0.4,
        defense_level=0.6,
        is_chokepoint=True,
        certainty=CertaintyTag.CANON,
    )

    nodes["PMC-01"] = TopologyNode(
        node_id="PMC-01",
        name="Syndicate Operations Hub",
        location_type=LocationType.SYSTEM,
        owner_faction="pmc_syndicate",
        strategic_value=0.5,
        resources={},
        population=0.3,
        defense_level=0.5,
        is_chokepoint=False,
        certainty=CertaintyTag.CANON,
    )

    nodes["CRIMSON-01"] = TopologyNode(
        node_id="CRIMSON-01",
        name="Pyre Sanctum",
        location_type=LocationType.SYSTEM,
        owner_faction="crimson_pact",
        strategic_value=0.4,
        resources={},
        population=0.4,
        defense_level=0.5,
        is_chokepoint=False,
        certainty=CertaintyTag.CANON,
    )

    nodes["HOLLOW-01"] = TopologyNode(
        node_id="HOLLOW-01",
        name="Hollow Expanse",
        location_type=LocationType.ANOMALY,
        owner_faction=None,
        strategic_value=0.7,
        resources={},
        population=0.0,
        defense_level=0.0,
        is_chokepoint=False,
        certainty=CertaintyTag.UNCONFIRMED,
    )

    nodes["XYPHOS-01"] = TopologyNode(
        node_id="XYPHOS-01",
        name="Xyphos Prime",
        location_type=LocationType.ANOMALY,
        owner_faction=None,
        strategic_value=0.8,
        resources={},
        population=0.0,
        defense_level=0.0,
        is_chokepoint=True,
        certainty=CertaintyTag.UNCONFIRMED,
    )

    nodes["VEIL-01"] = TopologyNode(
        node_id="VEIL-01",
        name="Veil Nebula",
        location_type=LocationType.ANOMALY,
        owner_faction=None,
        strategic_value=0.3,
        resources={},
        population=0.0,
        defense_level=0.0,
        is_chokepoint=False,
        certainty=CertaintyTag.LEGEND_CONTESTED,
    )

    nodes["BLACK-GRID-01"] = TopologyNode(
        node_id="BLACK-GRID-01",
        name="The Black Grid",
        location_type=LocationType.DOMAIN,
        owner_faction=None,
        strategic_value=0.6,
        resources={},
        population=0.0,
        defense_level=0.0,
        is_chokepoint=False,
        certainty=CertaintyTag.CANON,
    )

    # Initialize adjacency for all nodes
    for node_id in nodes:
        adjacency[node_id] = []

    # Create edges
    edge_counter = 0

    # GU-CORE-01 connections
    edges["EDGE-001"] = HyperlaneEdge(
        edge_id="EDGE-001",
        from_node="GU-CORE-01",
        to_node="GU-CORE-02",
        lane_type=HyperlaneType.MAJOR_LANE,
        travel_time=1.0,
        capacity=5.0,
        is_contested=False,
    )
    adjacency["GU-CORE-01"].append("GU-CORE-02")
    adjacency["GU-CORE-02"].append("GU-CORE-01")

    edges["EDGE-002"] = HyperlaneEdge(
        edge_id="EDGE-002",
        from_node="GU-CORE-01",
        to_node="GU-CORE-03",
        lane_type=HyperlaneType.MAJOR_LANE,
        travel_time=1.0,
        capacity=5.0,
        is_contested=False,
    )
    adjacency["GU-CORE-01"].append("GU-CORE-03")
    adjacency["GU-CORE-03"].append("GU-CORE-01")

    edges["EDGE-003"] = HyperlaneEdge(
        edge_id="EDGE-003",
        from_node="GU-CORE-01",
        to_node="GU-LOG-01",
        lane_type=HyperlaneType.MAJOR_LANE,
        travel_time=2.0,
        capacity=5.0,
        is_contested=False,
    )
    adjacency["GU-CORE-01"].append("GU-LOG-01")
    adjacency["GU-LOG-01"].append("GU-CORE-01")

    edges["EDGE-004"] = HyperlaneEdge(
        edge_id="EDGE-004",
        from_node="GU-CORE-01",
        to_node="ZYP-TRADE-01",
        lane_type=HyperlaneType.MAJOR_LANE,
        travel_time=2.0,
        capacity=5.0,
        is_contested=False,
    )
    adjacency["GU-CORE-01"].append("ZYP-TRADE-01")
    adjacency["ZYP-TRADE-01"].append("GU-CORE-01")

    # GU-CORE-02 connections
    edges["EDGE-005"] = HyperlaneEdge(
        edge_id="EDGE-005",
        from_node="GU-CORE-02",
        to_node="VEL-BORDER-01",
        lane_type=HyperlaneType.MINOR_LANE,
        travel_time=3.0,
        capacity=3.0,
        is_contested=True,
    )
    adjacency["GU-CORE-02"].append("VEL-BORDER-01")
    adjacency["VEL-BORDER-01"].append("GU-CORE-02")

    edges["EDGE-006"] = HyperlaneEdge(
        edge_id="EDGE-006",
        from_node="GU-CORE-02",
        to_node="OUTER-01",
        lane_type=HyperlaneType.MINOR_LANE,
        travel_time=2.5,
        capacity=3.0,
        is_contested=False,
    )
    adjacency["GU-CORE-02"].append("OUTER-01")
    adjacency["OUTER-01"].append("GU-CORE-02")

    # GU-CORE-03 connections
    edges["EDGE-007"] = HyperlaneEdge(
        edge_id="EDGE-007",
        from_node="GU-CORE-03",
        to_node="ELARI-01",
        lane_type=HyperlaneType.MAJOR_LANE,
        travel_time=2.0,
        capacity=5.0,
        is_contested=False,
    )
    adjacency["GU-CORE-03"].append("ELARI-01")
    adjacency["ELARI-01"].append("GU-CORE-03")

    edges["EDGE-008"] = HyperlaneEdge(
        edge_id="EDGE-008",
        from_node="GU-CORE-03",
        to_node="XYPHOS-01",
        lane_type=HyperlaneType.WORMHOLE,
        travel_time=1.0,
        capacity=2.0,
        is_contested=False,
    )
    adjacency["GU-CORE-03"].append("XYPHOS-01")
    adjacency["XYPHOS-01"].append("GU-CORE-03")

    # GU-LOG-01 connections
    edges["EDGE-009"] = HyperlaneEdge(
        edge_id="EDGE-009",
        from_node="GU-LOG-01",
        to_node="AI-FRINGE-01",
        lane_type=HyperlaneType.MINOR_LANE,
        travel_time=2.0,
        capacity=3.0,
        is_contested=False,
    )
    adjacency["GU-LOG-01"].append("AI-FRINGE-01")
    adjacency["AI-FRINGE-01"].append("GU-LOG-01")

    # VEL-CORE-01 connections
    edges["EDGE-010"] = HyperlaneEdge(
        edge_id="EDGE-010",
        from_node="VEL-CORE-01",
        to_node="VEL-BORDER-01",
        lane_type=HyperlaneType.MAJOR_LANE,
        travel_time=1.5,
        capacity=5.0,
        is_contested=False,
    )
    adjacency["VEL-CORE-01"].append("VEL-BORDER-01")
    adjacency["VEL-BORDER-01"].append("VEL-CORE-01")

    # VEL-BORDER-01 connections
    edges["EDGE-011"] = HyperlaneEdge(
        edge_id="EDGE-011",
        from_node="VEL-BORDER-01",
        to_node="SEP-01",
        lane_type=HyperlaneType.MINOR_LANE,
        travel_time=2.0,
        capacity=3.0,
        is_contested=True,
    )
    adjacency["VEL-BORDER-01"].append("SEP-01")
    adjacency["SEP-01"].append("VEL-BORDER-01")

    # VEL-CORE-01 additional
    edges["EDGE-012"] = HyperlaneEdge(
        edge_id="EDGE-012",
        from_node="VEL-CORE-01",
        to_node="CRIMSON-01",
        lane_type=HyperlaneType.MINOR_LANE,
        travel_time=3.0,
        capacity=3.0,
        is_contested=False,
    )
    adjacency["VEL-CORE-01"].append("CRIMSON-01")
    adjacency["CRIMSON-01"].append("VEL-CORE-01")

    # ZYP-TRADE-01 connections
    edges["EDGE-013"] = HyperlaneEdge(
        edge_id="EDGE-013",
        from_node="ZYP-TRADE-01",
        to_node="PMC-01",
        lane_type=HyperlaneType.MAJOR_LANE,
        travel_time=2.0,
        capacity=5.0,
        is_contested=False,
    )
    adjacency["ZYP-TRADE-01"].append("PMC-01")
    adjacency["PMC-01"].append("ZYP-TRADE-01")

    edges["EDGE-014"] = HyperlaneEdge(
        edge_id="EDGE-014",
        from_node="ZYP-TRADE-01",
        to_node="OUTER-01",
        lane_type=HyperlaneType.MAJOR_LANE,
        travel_time=2.5,
        capacity=5.0,
        is_contested=False,
    )
    adjacency["ZYP-TRADE-01"].append("OUTER-01")
    adjacency["OUTER-01"].append("ZYP-TRADE-01")

    # ELARI-01 connections
    edges["EDGE-015"] = HyperlaneEdge(
        edge_id="EDGE-015",
        from_node="ELARI-01",
        to_node="VORRAN-01",
        lane_type=HyperlaneType.MAJOR_LANE,
        travel_time=1.5,
        capacity=5.0,
        is_contested=False,
    )
    adjacency["ELARI-01"].append("VORRAN-01")
    adjacency["VORRAN-01"].append("ELARI-01")

    # VORRAN-01 connections
    edges["EDGE-016"] = HyperlaneEdge(
        edge_id="EDGE-016",
        from_node="VORRAN-01",
        to_node="KAELAR-01",
        lane_type=HyperlaneType.MINOR_LANE,
        travel_time=2.0,
        capacity=3.0,
        is_contested=False,
    )
    adjacency["VORRAN-01"].append("KAELAR-01")
    adjacency["KAELAR-01"].append("VORRAN-01")

    # KAELAR-01 connections
    edges["EDGE-017"] = HyperlaneEdge(
        edge_id="EDGE-017",
        from_node="KAELAR-01",
        to_node="THARAX-01",
        lane_type=HyperlaneType.MINOR_LANE,
        travel_time=3.0,
        capacity=3.0,
        is_contested=False,
    )
    adjacency["KAELAR-01"].append("THARAX-01")
    adjacency["THARAX-01"].append("KAELAR-01")

    # THARAX-01 connections
    edges["EDGE-018"] = HyperlaneEdge(
        edge_id="EDGE-018",
        from_node="THARAX-01",
        to_node="OUTER-01",
        lane_type=HyperlaneType.MINOR_LANE,
        travel_time=2.5,
        capacity=3.0,
        is_contested=False,
    )
    adjacency["THARAX-01"].append("OUTER-01")
    adjacency["OUTER-01"].append("THARAX-01")

    # SEP-01 connections
    edges["EDGE-019"] = HyperlaneEdge(
        edge_id="EDGE-019",
        from_node="SEP-01",
        to_node="OUTER-01",
        lane_type=HyperlaneType.MINOR_LANE,
        travel_time=3.0,
        capacity=3.0,
        is_contested=False,
    )
    adjacency["SEP-01"].append("OUTER-01")
    adjacency["OUTER-01"].append("SEP-01")

    # OUTER-01 to precursor sites
    edges["EDGE-020"] = HyperlaneEdge(
        edge_id="EDGE-020",
        from_node="OUTER-01",
        to_node="HOLLOW-01",
        lane_type=HyperlaneType.DRIFT_CORRIDOR,
        travel_time=4.0,
        capacity=2.0,
        is_contested=False,
    )
    adjacency["OUTER-01"].append("HOLLOW-01")
    adjacency["HOLLOW-01"].append("OUTER-01")

    # VEL-CORE-01 to anomaly
    edges["EDGE-021"] = HyperlaneEdge(
        edge_id="EDGE-021",
        from_node="VEL-CORE-01",
        to_node="VEIL-01",
        lane_type=HyperlaneType.DRIFT_CORRIDOR,
        travel_time=5.0,
        capacity=2.0,
        is_contested=False,
    )
    adjacency["VEL-CORE-01"].append("VEIL-01")
    adjacency["VEIL-01"].append("VEL-CORE-01")

    # Secret passage and jump gate
    edges["EDGE-022"] = HyperlaneEdge(
        edge_id="EDGE-022",
        from_node="PMC-01",
        to_node="AI-FRINGE-01",
        lane_type=HyperlaneType.SECRET_PASSAGE,
        travel_time=3.0,
        capacity=1.0,
        is_contested=False,
    )
    adjacency["PMC-01"].append("AI-FRINGE-01")
    adjacency["AI-FRINGE-01"].append("PMC-01")

    edges["EDGE-023"] = HyperlaneEdge(
        edge_id="EDGE-023",
        from_node="GU-CORE-01",
        to_node="SEP-01",
        lane_type=HyperlaneType.JUMP_GATE,
        travel_time=1.5,
        capacity=4.0,
        is_contested=False,
    )
    adjacency["GU-CORE-01"].append("SEP-01")
    adjacency["SEP-01"].append("GU-CORE-01")

    return GalaxyTopology(
        nodes=nodes,
        edges=edges,
        adjacency=adjacency,
    )


__all__ = [
    "TopologyManager",
    "build_canonical_topology",
]
