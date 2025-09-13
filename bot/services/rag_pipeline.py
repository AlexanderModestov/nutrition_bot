from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from bot.config import Config
from bot.supabase_client import SupabaseClient
import logging

class RAGPipeline:
    def __init__(self, supabase_client: SupabaseClient):
        self.supabase_client = supabase_client
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=Config.OPENAI_API_KEY,
            model=Config.EMBEDDING_MODEL
        )
        self.llm = ChatOpenAI(
            openai_api_key=Config.OPENAI_API_KEY,
            model=Config.GPT_MODEL,
            temperature=0.1
        )
        
        # Custom prompt template for RAG
        self.prompt_template = PromptTemplate(
            template=Config.RAG_PROMPT_TEMPLATE,
            input_variables=["context", "question"]
        )
    
    async def get_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for given text"""
        embeddings = await self.embeddings.aembed_query(text)
        return embeddings
    
    async def search_and_answer(self, user_id: int, question: str, user_settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main RAG pipeline: search content and generate answer
        
        Args:
            user_id: User's database ID
            question: User's question
            user_settings: User preferences (answer style, filters, etc.)
            
        Returns:
            Dict with answer, sources, and metadata
        """
            # Generate query embeddings
        query_embeddings = await self.get_embeddings(question)
            
            # Apply user filters
        search_limit = Config.SEARCH_LIMIT
            
        # Search in user's content
        search_results = await self.supabase_client.search_content(
            user_id=user_id,
            query_embedding=query_embeddings,
            limit=search_limit
        )
            
        # Prepare context for LLM
        context_parts = []
        sources = []
            
        for i, result in enumerate(search_results):
            context_parts.append(result['content_text'])
            sources.append({
                'type': result.get('type'),
                'title': result.get('title'),
                'file_id': result.get('file_id')
            })
            
        context = "\n\n---\n\n".join(context_parts)
            
        # Generate answer using LLM
        prompt = self.prompt_template.format(context=context, question=question)

        pass  # Prompt debugging removed for performance
            
        response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
        answer = response.content.strip()
            
        result = {
            "answer": answer,
            "sources": sources,
            "context_used": len(search_results),
            "total_available": len(search_results)
        }
        return result
    
    
    async def save_query_to_history(self, user_id: int, question: str, answer: str, sources: List[Dict]) -> Optional[Dict]:
        """Save query and answer to history (disabled - no QueryHistory table)"""
        # Disabled since query_history table doesn't exist
        return None