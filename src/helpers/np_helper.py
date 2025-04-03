import numpy as np
from typing import List, Union


def normalize_vector(vector: Union[np.ndarray, List[float]]) -> np.ndarray:
    """Normalize a vector to unit length."""
    norm = np.linalg.norm(vector)
    if norm > 0:
        return vector / norm
    return vector


def cosine_similarity(vec1: Union[np.ndarray, List[float]], vec2: Union[np.ndarray, List[float]]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector (numpy array or list of floats)
        vec2: Second vector (numpy array or list of floats)
            
    Returns:
        Cosine similarity value (between -1 and 1)
    """
    # Normalize vectors
    vec1_normalized = normalize_vector(vec1)
    vec2_normalized = normalize_vector(vec2)
    
    # Return dot product of normalized vectors
    return float(np.dot(vec1_normalized, vec2_normalized))


def find_similarities(source_vector: Union[np.ndarray, List[float]], target_vectors_dict: dict) -> List[tuple]:
    """
    Find similarities between a source vector and a dictionary of target vectors.
    
    Args:
        source_vector: The vector to compare against
        target_vectors_dict: Dictionary of {key: vector} pairs
        
    Returns:
        List of tuples (key, similarity_score) sorted by similarity (highest first)
    """
    similarities = []
    source_vector = np.array(source_vector)
    
    for key, vector in target_vectors_dict.items():
        similarity = cosine_similarity(source_vector, np.array(vector))
        similarities.append((key, similarity))
    
    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities
