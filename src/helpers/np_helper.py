import numpy as np
from typing import List, Union


def cosine_similarity(vec1: Union[np.ndarray, List[float]], vec2: Union[np.ndarray, List[float]]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector (numpy array or list of floats)
        vec2: Second vector (numpy array or list of floats)
            
    Returns:
        Cosine similarity value (between -1 and 1)
    """
    # Convert lists to numpy arrays if necessary
    if not isinstance(vec1, np.ndarray):
        vec1 = np.array(vec1)
    if not isinstance(vec2, np.ndarray):
        vec2 = np.array(vec2)
        
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)
    
    if norm_a == 0 or norm_b == 0:
        return 0
        
    return dot_product / (norm_a * norm_b)
