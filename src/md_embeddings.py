import os
import json
import argparse
import yaml
import numpy as np
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
from collections import defaultdict

from src.helpers.string_helper import clean_url
from src.helpers.chat_connector import ChatConnector
from src.helpers.embedding_connector import EmbeddingConnector
from src.helpers.np_helper import normalize_vector, cosine_similarity


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy arrays"""

    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


class MarkdownEmbeddingGenerator:
    """Class to generate embeddings for markdown files in a directory."""

    def __init__(self, logger):
        # Set up logger
        self.logger = logger
        model_type = 'google'
        model_chat = 'gemini'
        self.embeddings = {}

        # Initialize the embedding connector
        self.logger.info(f'Initializing {model_type} embedding model')
        self.connector = EmbeddingConnector(self.logger)
        self.connector.init_model(model_type)
        self.chat = ChatConnector(self.logger)
        self.chat.init_model(model_chat)

    def extract_markdown_body(self, content: str) -> str:
        """Extract the body content from a markdown file, excluding frontmatter."""

        # Check if the file has YAML frontmatter (between --- markers)
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                # Return everything after the frontmatter
                return parts[2].strip()

        # If no frontmatter is detected, return the entire content
        return content.strip()

    def extract_yaml(self, content: str) -> dict:
        """Extract the YAML frontmatter from the markdown file."""
        yaml_content = {}

        # Check if the file has YAML frontmatter (between --- markers)
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    # Parse the YAML frontmatter
                    yaml_content = yaml.safe_load(parts[1])
                except Exception as e:
                    self.logger.error(f'Error parsing frontmatter YAML: {str(e)}')

        return yaml_content

    def extract_frontmatter_field(self, content: str, field_name: str, default=None):
        """Extract a specific field from frontmatter YAML.

        Args:
            content: The full content of the markdown file
            field_name: Name of the field to extract
            default: Default value to return if field is not found

        Returns:
            Value of the requested field, or default value if not found
        """
        frontmatter = self.extract_yaml(content)
        if frontmatter and field_name in frontmatter:
            return frontmatter[field_name]
        return default

    def extract_links(self, content: str) -> list:
        """Extract related links from the markdown frontmatter.

        Args:
            content: The full content of the markdown file

        Returns:
            List of dictionaries containing link information, or empty list if none found
        """
        return self.extract_frontmatter_field(content, 'related_links', [])

    def extract_tags(self, content: str) -> list:
        return self.extract_frontmatter_field(content, 'tags', [])

    def extract_source(self, content: str) -> str:
        """Extract source URL from the markdown frontmatter.

        Args:
            content: The full content of the markdown file

        Returns:
            Source URL as string, or empty string if none found
        """
        return self.extract_frontmatter_field(content, 'source_url', '')

    async def summarize(self, content: str) -> str:
        """Summarize the content using the chat model."""
        self.logger.debug('Summarizing content')
        prompt = (
            'Your task is helping me to create better manual to program Madar.\n'
            'Given the content below, please summarize it in a concise and clear manner.\n'
            'Make sure to include all important information.\n'
            'Rules:\n'
            '1. Do not include any code snippets.\n'
            '2. Do not include any links.\n'
            '3. Do not include any tags.\n'
            '4. Do not include any frontmatter.\n'
            '5. Summary must be in Polish.\n'
            '6. Do not include any explanations.\n'
            '7. Length of the summary should be near 30 words.\n'
            'Please summarize the following content:\n\n'
            f'{content}'
        )
        response = await self.chat.ask(prompt)
        return response
    
    def process_links(self,directory_path):
        file_count = 0

        self.logger.debug(f'Traversing directory: {directory_path}')
        embeddings_data = {}

        # Walk through the directory
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    try:
                        self.logger.debug(f'Processing: {file_path}')

                        # Extract body content
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        #body_content = self.extract_markdown_body(content)
                        related_links = self.extract_links(content)
                        for links in related_links:
                            links['url'] = clean_url(links['url'])
          
                        tags = self.extract_tags(content)
                        source = clean_url(self.extract_source(content))
                        #embedding = await self.connector.embed(body_content)
                        #summary = await self.summarize(body_content)

                        # Store relative path and embedding
                        rel_path = os.path.relpath(file_path, directory_path)
                        embeddings_data[rel_path] = {
                            'id': rel_path,
                            #'embedding': embedding,
                            'related_links': related_links,
                            'tags': tags,
                            #'summary': summary,
                            'source_url': source,
                        }

                        file_count += 1
                    except Exception as e:
                        self.logger.error(f'Error processing {file_path}: {str(e)}')
                        break
        self.embeddings = embeddings_data
        self.repair_path()
        return file_count



    async def process_directory(self, directory_path):
        """
        Process all markdown files in the given directory, compute embeddings,
        and store them in a JSON file.

        Args:
            directory_path: Path to directory containing markdown files
        """
        file_count = 0

        self.logger.debug(f'Traversing directory: {directory_path}')
        embeddings_data = {}

        # Walk through the directory
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    try:
                        self.logger.debug(f'Processing: {file_path}')

                        # Extract body content
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        body_content = self.extract_markdown_body(content)
                        related_links = self.extract_links(content)
                        tags = self.extract_tags(content)
                        source = clean_url(self.extract_source(content))
                        embedding = await self.connector.embed(body_content)
                        summary = await self.summarize(body_content)

                        # Store relative path and embedding
                        rel_path = os.path.relpath(file_path, directory_path)
                        embeddings_data[rel_path] = {
                            'id': rel_path,
                            'embedding': embedding,
                            'related_links': related_links,
                            'tags': tags,
                            'summary': summary,
                            'source_url': source,
                        }

                        file_count += 1
                    except Exception as e:
                        self.logger.error(f'Error processing {file_path}: {str(e)}')
                        break
        self.embeddings = embeddings_data
        self.repair_path()
        return file_count

    def repair_path(self):
        for file_name in self.embeddings.keys():
            file1 = self.embeddings[file_name]
            file1['id'] = file_name
            file1['source_url'] = clean_url(file1['source_url'])
            for file2 in self.embeddings.values():
            
                for links in file2['related_links']:
                    
                    if file1['source_url'] == links['url']:
                        links['path'] = file_name
                        print(file_name)

    def save_embeddings_to_json(self, output_file):
        """Save embeddings to JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.embeddings, f, cls=NumpyEncoder)
        self.logger.info(f'Saving {len(self.embeddings)} embeddings to {output_file}')

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

    def save(self, clusters, output_file=None):
        """
        Print the clusters to the console and optionally save to JSON.

        Args:
            clusters: Dictionary of cluster assignments
            output_file: Path to save the clusters as JSON (optional)
        """

        # Save clusters to JSON if output file is provided
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(clusters, f, indent=2)
            self.logger.info(f'Saved to {output_file}')

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

            # Process linked documents from frontmatter
            # if doc in self.embeddings and 'related_links' in self.embeddings[doc]:
            #    print('  Linked documents:')
            #    for link in self.embeddings[doc]['related_links']:
            #        link_text = link.get('text', 'No Text')
            #        link_url = link.get('url', 'No URL')
            #        print(f'    → : {link_url}')
            #        combined_results[doc]['linked'].append({'text': link_text, 'url': link_url})
        return combined_results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate embeddings and cluster markdown files')
    parser.add_argument('--directory', '-d', type=str, help='Directory containing markdown files')
    parser.add_argument('--output', '-o', type=str, help='Output JSON file path for embeddings')
    parser.add_argument(
        '--model',
        '-m',
        type=str,
        default='gemini',
        choices=['gemini', 'openai', 'azure'],
        help='Embedding model type to use (gemini, openai, or azure)',
    )
    parser.add_argument('--input', '-i', type=str, help='Input JSON file containing pre-computed embeddings')
    parser.add_argument('--cluster', '-c', action='store_true', help='Perform clustering on the embeddings')
    parser.add_argument('--num-clusters', '-n', type=int, default=5, help='Number of clusters for K-means (default: 5)')
    parser.add_argument('--visualize', '-v', action='store_true', help='Visualize clusters using t-SNE')
    parser.add_argument('--viz-output', type=str, help='Path to save visualization image')
    parser.add_argument('--cluster-output', type=str, help='Path to save clustering results as JSON')
    parser.add_argument('--similar', '-s', action='store_true', help='Find similar documents')
    parser.add_argument(
        '--top-n', type=int, default=3, help='Number of similar documents to find per document (default: 3)'
    )
    parser.add_argument('--similar-output', type=str, help='Path to save similar documents results as JSON')

    args = parser.parse_args()

    # Configure logging
    import logging

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('md_embeddings')

    # Create instance of the embedding generator
    generator = MarkdownEmbeddingGenerator(logger)

    # Process based on arguments
    if args.input:
        # Load existing embeddings
        generator.load_embeddings_from_json(args.input)
    elif args.directory:
        # Generate new embeddings
        file_count = generator.process_directory(args.directory)
        logger.info(f'Processed {file_count} files')
        if args.output:
            generator.save_embeddings_to_json(args.output)
    else:
        if not (args.input or args.directory):
            logger.error('Either --input or --directory must be provided')
            parser.error('Either --input or --directory must be provided')

    # Perform clustering if requested
    if args.cluster:
        clusters = generator.perform_clustering(n_clusters=args.num_clusters)
        generator.save(clusters, args.cluster_output)

        if args.visualize:
            generator.visualize_clusters(clusters, args.viz_output)
