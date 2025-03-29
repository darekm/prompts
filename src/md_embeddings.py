import os
import json
import argparse
import yaml
import numpy as np

from src.helpers.embedding_connector import EmbeddingConnector


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
        model_type='google'
        self.embeddings = {}
        
        # Initialize the embedding connector
        print(f"Initializing {model_type} embedding model")
        self.connector = EmbeddingConnector(self.logger)
        self.connector.init_model(model_type)
    
    def extract_markdown_body(self, file_path: str) -> str:
        """Extract the body content from a markdown file, excluding frontmatter."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the file has YAML frontmatter (between --- markers)
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                # Return everything after the frontmatter
                return parts[2].strip()
        
        # If no frontmatter is detected, return the entire content
        return content.strip()
    
    def compute_embedding(self, text: str) :
        """Compute embedding for the given text using the provided embedding connector."""
        return self.connector.embed_sync(text)
    
    def process_directory(self, directory_path):
        """
        Process all markdown files in the given directory, compute embeddings,
        and store them in a JSON file.
        
        Args:
            directory_path: Path to directory containing markdown files
            output_file: Path to output JSON file where embeddings will be stored
        """
        file_count = 0
        
        print(f"Traversing directory: {directory_path}")
        embeddings_data = {}
        
        # Walk through the directory
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    try:
                        print(f"Processing: {file_path}")
                        
                        # Extract body content
                        body_content = self.extract_markdown_body(file_path)
                        embedding = self.connector.embed_sync(body_content)
                        
                        # Store relative path and embedding
                        rel_path = os.path.relpath(file_path, directory_path)
                        embeddings_data[rel_path] = embedding
                        
                        file_count += 1
                    except Exception as e:
                        print(f"Error processing {file_path}: {str(e)}")
        self.embeddings=embeddings_data
        return file_count
        
    def save_embeddings_to_json(self, output_file):
        
        # Save embeddings to JSON file
        print(f"Saving {len(self.embeddings)} embeddings to {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.embeddings, f, cls=NumpyEncoder)
        
        print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate embeddings for markdown files")
    parser.add_argument("--directory", "-d", type=str, required=True, 
                        help="Directory containing markdown files")
    parser.add_argument("--output", "-o", type=str, required=True, 
                        help="Output JSON file path")
    parser.add_argument("--model", "-m", type=str, default="gemini",
                        choices=["gemini", "openai", "azure"],
                        help="Embedding model type to use (gemini, openai, or azure)")
    
    args = parser.parse_args()
    
    # Create instance of the embedding generator and process the directory
    generator = MarkdownEmbeddingGenerator(args.model)
    generator.process_directory(args.directory, args.output)
