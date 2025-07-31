from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F
from typing import List, Union
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.device = torch.device(
            "cuda" if settings.EMBEDDING_DEVICE == "cuda" and torch.cuda.is_available() 
            else "cpu"
        )
        
        logger.info(f"Initializing embedding model: {self.model_name} on {self.device}")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        
        # Move to device and set to eval mode
        self.model = self.model.to(self.device)
        self.model.eval()
        
        logger.info(f"Embedding model loaded successfully with dimension: {settings.EMBEDDING_DIMENSION}")
    
    def embed(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """Generate embeddings for input text(s)"""
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return []
        
        try:
            # Tokenize with truncation and padding
            encoded_input = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors='pt'
            ).to(self.device)

            with torch.no_grad():
                model_output = self.model(**encoded_input)
            
            # Use CLS token as embedding
            embeddings = model_output.last_hidden_state[:, 0]
            # Normalize to unit length (for cosine similarity)
            embeddings = F.normalize(embeddings, p=2, dim=1)

            # Convert to list of lists for JSON serialization
            return embeddings.cpu().numpy().tolist()
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def get_dimension(self) -> int:
        """Get the embedding dimension"""
        return settings.EMBEDDING_DIMENSION

# Create a global instance
embedding_service = EmbeddingService()
