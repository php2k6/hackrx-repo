from typing import List, Optional
import g4f
from g4f.client import Client
import g4f.Provider
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        
        # Initialize client based on provider
        self._initialize_client()
        
        logger.info(f"Initialized LLM service with provider: {self.provider}, model: {self.model}")
    
    def _initialize_client(self):
        """Initialize the appropriate client based on provider string"""
        try:
            # Parse the provider string to get the actual provider class
            if self.provider.startswith("g4f.Provider."):
                provider_name = self.provider.replace("g4f.Provider.", "")
                provider_class = getattr(g4f.Provider, provider_name)
                self.client = Client(provider=provider_class)
                logger.info(f"Successfully initialized provider: {provider_name}")
            else:
                # Fallback to default if provider string is not in expected format
                logger.warning(f"Invalid provider format: {self.provider}, defaulting to Blackbox")
                self.client = Client(provider=g4f.Provider.Blackbox)
                
        except AttributeError as e:
            logger.error(f"Provider {self.provider} not found: {e}")
            logger.warning("Falling back to Blackbox provider")
            self.client = Client(provider=g4f.Provider.Blackbox)
        except Exception as e:
            logger.error(f"Error initializing provider {self.provider}: {e}")
            logger.warning("Falling back to Blackbox provider")
            self.client = Client(provider=g4f.Provider.Blackbox)
    
    async def generate_answer(self, question: str, chunks: List[tuple]) -> str:
        """Generate answer from question and relevant chunks"""
        try:
            return await self._answer_from_chunks(question, chunks)
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Error generating answer: {str(e)}"
    
    async def generate_direct_answer(self, question: str) -> str:
        """Generate answer directly from question without document context"""
        try:
            # Create simple prompt for direct query
            prompt = f"""You are a helpful AI assistant. Answer the user's question directly and accurately.

User Question: {question}

Answer:"""
            
            # Generate response using g4f
            return await self._generate_with_g4f(prompt)
        except Exception as e:
            logger.error(f"Error generating direct answer: {e}")
            return f"Error generating answer: {str(e)}"
    
    async def _answer_from_chunks(self, query: str, chunks: List[tuple]) -> str:
        """Generate answer using the configured LLM provider"""
        if not chunks:
            return "No relevant content found in the document."
        
        # Format context from chunks
        context_parts = []
        for i, (section, content) in enumerate(chunks[:settings.TOP_K_RESULTS]):
            context_parts.append(f"[Section {i+1}] {section}:\n{content}")
        
        context = "\n\n".join(context_parts)
        
        # Create prompt
        prompt = self._create_prompt(query, context)
        
        # Generate response based on provider (all use g4f)
        return await self._generate_with_g4f(prompt)
    
    def _create_prompt(self, query: str, context: str) -> str:
        """Create optimized prompt for insurance document Q&A"""
        return f"""You are an expert insurance policy analyst. Answer the user's question based on the provided document sections. 

IMPORTANT GUIDELINES:
1. Give direct, specific answers with exact details from the document
2. If the answer involves numbers (days, months, percentages), be precise
3. For complex questions, extract and combine relevant information from multiple sections
4. If specific details are not found, state what related information IS available
5. Cite specific sections when possible
6. For waiting periods, grace periods, limits - provide exact values
7. For calculations, show the formula and steps
8. If only partial information is available, provide what you can and note what's missing
9. Do not include any Markdown formatting in the response

CONTEXT: These are sections from an insurance policy document.

User Question: {query}

Document Sections:
{context}

Answer:"""
    
    async def _generate_with_g4f(self, prompt: str) -> str:
        """Generate response using G4F providers"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                web_search=False,
                temperature=self.temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"G4F generation error: {e}")
            # Return a more helpful fallback response instead of error message
            return self._create_fallback_response(prompt)
    
    def _create_fallback_response(self, prompt: str) -> str:
        """Create a helpful fallback response when LLM is unavailable"""
        # Extract the question from the prompt
        if "User Question:" in prompt:
            question_part = prompt.split("User Question:")[1].split("Document Sections:")[0].strip()
        else:
            question_part = "your question"
        
        # Extract context from the prompt
        if "Document Sections:" in prompt:
            context_part = prompt.split("Document Sections:")[1].strip()
            # Get first few lines of context
            context_lines = context_part.split('\n')[:5]
            context_summary = '\n'.join(context_lines)
            
            return f"""Based on the available document content, I found relevant information but cannot provide a detailed analysis due to temporary service limitations. 

Here are the relevant document sections that may contain the answer to: {question_part}

{context_summary}

Please review these sections manually or try again later when the analysis service is restored."""
        else:
            return f"I found relevant information in the document for: {question_part}, but cannot provide detailed analysis due to temporary service limitations. Please try again later."