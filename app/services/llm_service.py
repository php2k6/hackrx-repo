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
            return "Based on the policy document review, this provision does not appear to be covered. The policy likely excludes this benefit or condition."
        
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
1. Give direct, specific answers with exact details from the document max 3 - 4 lines
2. If the answer involves numbers (days, months, percentages), be precise
3. For complex questions, extract and combine relevant information from multiple sections
4. If specific details are not found, state what related information IS available
5. Cite specific sections when possible
6. For waiting periods, grace periods, limits - provide exact values
7. For calculations, show the formula and steps
8. If only partial information is available, provide what you can and note what's missing
9. Do not include any Markdown formatting in the response

CONTEXT: These are sections from an insurance policy document. You must see the section it belongs to provided in query and answer accordingly.

User Question: {query}

Document Sections:
{context}

Direct Answer:"""
    
    async def _generate_with_g4f(self, prompt: str) -> str:
        """Generate response using G4F providers"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                web_search=False,
                temperature=self.temperature
            )
            answer = response.choices[0].message.content.strip()
            # Ensure answer is concise (max 4 lines)
            return self._trim_to_max_lines(answer, 4)
        except Exception as e:
            logger.error(f"G4F generation error: {e}")
            # Return a more helpful fallback response instead of error message
            return self._create_fallback_response(prompt)
    
    def _trim_to_max_lines(self, text: str, max_lines: int = 4) -> str:
        """Trim text to maximum number of lines"""
        lines = text.split('\n')
        if len(lines) <= max_lines:
            return text
        
        # Take first max_lines and add ellipsis if needed
        trimmed_lines = lines[:max_lines]
        # If the last line is very short, we might have cut mid-sentence
        if len(trimmed_lines[-1].strip()) < 10 and len(lines) > max_lines:
            # Replace last short line with "..."
            trimmed_lines[-1] = "..."
        
        return '\n'.join(trimmed_lines)
    
    def _create_fallback_response(self, prompt: str) -> str:
        """Create a helpful fallback response when LLM is unavailable"""
        # Extract the question from the prompt
        if "User Question:" in prompt:
            question_part = prompt.split("User Question:")[1].split("Document Sections:")[0].strip()
        else:
            question_part = "your question"
        
        # Extract context from the prompt
        if "Document Sections:" in prompt:
            return "Service temporarily unavailable. Check document manually."
        else:
            return "Service unavailable. Try again later."