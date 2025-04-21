import json
import numpy as np
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
from collections import defaultdict

from src.helpers.np_helper import  cosine_similarity


class ContentClustering:
    def __init__(self, logger):

        self.logger = logger        


    def load_embeddings_from_json(self, input_file):
        """Load embeddings from a JSON file."""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                self.embeddings = json.load(f)
            return True
        except Exception as e:
            self.logger.error(f'Error loading embeddings: {str(e)}')
            return False
    def perform_clustering(self, n_clusters=5, random_state=42):
        """
        Perform K-means clustering on the document embeddings.

        Args:
            n_clusters: Number of clusters to form
            random_state: Random seed for reproducibility

        Returns:
            Dictionary with cluster assignments
        """
        if not self.embeddings:
            self.logger.error('No embeddings available for clustering')
            raise ValueError('No embeddings available for clustering')

        # Extract file names and embeddings
        filenames = list(self.embeddings.keys())
        embeddings_array = np.array([self.embeddings[filename]['embedding'] for filename in filenames])

        # Perform K-means clustering
        self.logger.info(f'Performing K-means clustering with {n_clusters} clusters')
        kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
        cluster_labels = kmeans.fit_predict(embeddings_array)

        # Organize results by cluster
        clusters = defaultdict(list)
        for filename, cluster_id in zip(filenames, cluster_labels):
            clusters[int(cluster_id)].append(filename)

        return dict(clusters)
    
    def visualize_clusters(self, clusters, output_file=None):
        """
        Visualize document clusters using t-SNE for dimensionality reduction.

        Args:
            clusters: Dictionary of cluster assignments
            output_file: Path to save the visualization (optional)
        """
        if not self.embeddings:
            self.logger.warning('No embeddings available for visualization')
            return

        # Extract embeddings for visualization
        filenames = list(self.embeddings.keys())
        embeddings_array = np.array([self.embeddings[filename]['embedding'] for filename in filenames])

        # Map filenames to cluster ids
        cluster_map = {}
        for cluster_id, docs in clusters.items():
            for doc in docs:
                cluster_map[doc] = cluster_id

        # Create cluster labels array
        labels = np.array([cluster_map[filename] for filename in filenames])

        # Reduce dimensions for visualization using t-SNE
        self.logger.info('Reducing dimensions with t-SNE for visualization')
        tsne = TSNE(n_components=2, random_state=42)
        reduced_embeddings = tsne.fit_transform(embeddings_array)

        # Plot the clusters
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(reduced_embeddings[:, 0], reduced_embeddings[:, 1], c=labels, cmap='viridis', alpha=0.7)

        # Add legend
        legend1 = plt.legend(*scatter.legend_elements(), loc='upper right', title='Clusters')
        plt.gca().add_artist(legend1)

        plt.title('Document Clusters Visualization')
        plt.xlabel('t-SNE dimension 1')
        plt.ylabel('t-SNE dimension 2')

        if output_file:
            plt.savefig(output_file)
            self.logger.info(f'Visualization saved to {output_file}')
        else:
            plt.show()


    def find_similar_documents(self, top_n=1):
        """
        Find the most similar document(s) for each embedding using cosine similarity.

        Args:
            top_n: Number of similar documents to return for each document (default: 1)

        Returns:
            Dictionary mapping each document to its most similar document(s) and similarity score(s)
        """
        if not self.embeddings:
            self.logger.error('No embeddings available for similarity calculation')
            raise ValueError('No embeddings available for similarity calculation')

        self.logger.info(f'Finding top {top_n} similar document(s) for each embedding')

        # Extract file names and embeddings
        filenames = list(self.embeddings.keys())
        similar_docs = {}

        for file1 in filenames:
            # Get the embedding for the current file
            embedding1 = np.array(self.embeddings[file1]['embedding'])

            # Calculate similarities with all other documents
            similarities = []
            for file2 in filenames:
                if file1 == file2:  # Skip self-comparison
                    continue

                # Get the embedding for the comparison file
                embedding2 = np.array(self.embeddings[file2]['embedding'])

                # Calculate cosine similarity
                similarity = cosine_similarity(embedding1, embedding2)
                url = self.embeddings[file2]['source_url']
                similarities.append((file2, similarity, url))

            # Sort by similarity (highest first)
            similarities.sort(key=lambda x: x[1], reverse=True)

            # Store top N similar documents
            top_similar = similarities[:top_n]
            similar_docs[file1] = {'twins': [(doc, sim, url) for doc, sim, url in top_similar]}

        return similar_docs

    def print_similar_documents(self, similar_docs):
        """
        Print the similar documents to the console and optionally save to JSON.

        Args:
            similar_docs: Dictionary mapping each document to its similar document(s)
            output_file: Path to save the similar documents as JSON (optional)
        """
        print('\nSimilar Documents Results:')
        for doc, data in similar_docs.items():
            print(f'\n{doc}:')
            for twin, similarity in data['twins']:
                print(f'  → {twin} (similarity: {similarity:.4f})')

    def present_in_links(self, doc, url):
        for link in self.embeddings[doc]['related_links']:
            if link.get('url') == url:
                return True
        return False


    def linked_documents(self, similar_docs, output_file=None):
        """
        Print both similar documents and their linked documents to the console and optionally save to JSON.

        Args:
            similar_docs: Dictionary mapping each document to its similar document(s)
            output_file: Path to save the combined results as JSON (optional)
        """
        combined_results = {}

        self.logger.debug('Similar and Linked Documents Results:')
        for doc, data in similar_docs.items():
            print(f'\n{doc}:')
            combined_results[doc] = {'similar': {}, 'linked': []}

            # Process similar documents (twins)
            print('  Similar documents:')
            combined_results[doc]['similar']['twins'] = []
            for twin, similarity, url in data['twins']:
                if similarity < 0.82:
                    continue
                _pr = self.present_in_links(doc, url)
                print(f'    → {_pr}\t{twin} (similarity: {similarity:.4f})  {url}')
                if not _pr:
                    combined_results[doc]['similar']['twins'].append(
                        {'document': twin, 'similarity': similarity, 'source': url}
                    )

        return combined_results
