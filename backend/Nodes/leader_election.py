import requests
import threading
import time


class LeaderElection:
    def __init__(self, cluster_context):
        self.cluster = cluster_context
        self.election_in_progress = False

    def start_election(self):
        if self.election_in_progress:
            return

        self.election_in_progress = True
        local_id = self.cluster.local_node.node_id
        higher_nodes = [
            peer for peer in self.cluster.get_peers()
            if peer.node_id > local_id
        ]

        print(f"[ELECTION] Node {local_id} starting election")

        for peer in higher_nodes:
            try:
                requests.post(f"http://{peer.address}/election", timeout=2)
                print(f"[ELECTION] Higher node {peer.node_id} responded")
                self.election_in_progress = False
                return
            except requests.RequestException:
                continue

        # Nadie respondió → soy líder
        self.become_leader()

    def become_leader(self):
        node = self.cluster.local_node
        node.set_role("leader")
        self.cluster.set_leader(node.node_id)

        print(f"[LEADER] Node {node.node_id} became leader")

        for peer in self.cluster.get_peers():
            try:
                requests.post(
                    f"http://{peer.address}/leader",
                    json={"leader_id": node.node_id},
                    timeout=2
                )
            except requests.RequestException:
                pass

        self.election_in_progress = False

    def receive_leader(self, leader_id: int):
        self.cluster.set_leader(leader_id)
        if leader_id != self.cluster.local_node.node_id:
            self.cluster.local_node.set_role("follower")

        print(f"[LEADER] Leader set to {leader_id}")
