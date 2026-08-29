import Levenshtein
from collections import defaultdict
from typing import List, Dict, Tuple, Optional

class MultiFramePlateAggregator:
    def __init__(self, max_buffer_size: int = 15, similarity_threshold: float = 0.75):
        self.max_buffer_size = max_buffer_size
        self.similarity_threshold = similarity_threshold
        # vehicle_track_id -> list of (plate_text, confidence)
        self.track_buffers: Dict[int, List[Tuple[str, float]]] = defaultdict(list)

    def add_frame_read(self, track_id: int, plate_text: str, confidence: float):
        """Adds an OCR observation for a tracked vehicle in the current frame."""
        if not plate_text or len(plate_text) < 6:
            return
        
        self.track_buffers[track_id].append((plate_text, confidence))
        # Keep buffer to max size
        if len(self.track_buffers[track_id]) > self.max_buffer_size:
            self.track_buffers[track_id].pop(0)

    def resolve_consensus_plate(self, track_id: int) -> Optional[Tuple[str, float, int]]:
        """
        Performs confidence-weighted majority voting and edit-distance clustering
        across all frame observations for the tracked vehicle.
        
        Returns: (resolved_plate, consensus_confidence, observation_count)
        """
        reads = self.track_buffers.get(track_id, [])
        if not reads:
            return None

        # Cluster similar strings using Levenshtein distance
        clusters: List[List[Tuple[str, float]]] = []

        for text, conf in reads:
            placed = False
            for cluster in clusters:
                rep_text = cluster[0][0]
                ratio = Levenshtein.ratio(text, rep_text)
                if ratio >= self.similarity_threshold or Levenshtein.distance(text, rep_text) <= 2:
                    cluster.append((text, conf))
                    placed = True
                    break
            if not placed:
                clusters.append([(text, conf)])

        # Find largest / highest total weight cluster
        best_cluster = max(
            clusters,
            key=lambda c: sum(conf for _, conf in c) * (len(c) ** 0.5)
        )

        # Inside best cluster, find candidate with highest cumulative confidence
        candidate_scores: Dict[str, float] = defaultdict(float)
        for text, conf in best_cluster:
            candidate_scores[text] += conf

        resolved_plate = max(candidate_scores.items(), key=lambda x: x[1])[0]
        # Average confidence of the resolved plate observations
        cluster_confs = [conf for text, conf in best_cluster if text == resolved_plate]
        consensus_confidence = round(float(sum(cluster_confs) / len(cluster_confs)), 2)

        return resolved_plate, consensus_confidence, len(best_cluster)

    def clear_track(self, track_id: int):
        """Cleans up buffer when vehicle exits camera view."""
        if track_id in self.track_buffers:
            del self.track_buffers[track_id]

def resolve_cross_camera_fuzzy_plate(target_plate: str, candidate_plates: List[str], max_distance: int = 2) -> Optional[str]:
    """
    Fuzzy matching helper for linking vehicle observations across cameras
    when one camera had minor OCR misread (e.g. '0' vs 'O' or '8' vs 'B').
    """
    target = target_plate.replace(" ", "").upper()
    best_match = None
    min_dist = max_distance + 1

    for cand in candidate_plates:
        cand_clean = cand.replace(" ", "").upper()
        dist = Levenshtein.distance(target, cand_clean)
        if dist <= max_distance and dist < min_dist:
            min_dist = dist
            best_match = cand

    return best_match
