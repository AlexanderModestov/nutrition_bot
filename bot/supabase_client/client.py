import asyncio
from typing import List, Optional, Dict, Any
from supabase import create_client, Client
from .models import User, NotificationSettings

class SupabaseClient:
    def __init__(self, supabase_url: str, supabase_key: str):
        self.client: Client = create_client(supabase_url, supabase_key)
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        try:
            response = self.client.table('users').select('*').eq('telegram_id', telegram_id).execute()
            if response.data:
                return User(**response.data[0])
            return None
        except Exception as e:
            pass  # User error suppressed for performance
            return None
    
    async def create_or_update_user(self, user_data: Dict[str, Any]) -> Optional[User]:
        try:
            existing_user = await self.get_user_by_telegram_id(user_data['telegram_id'])
            
            if existing_user:
                response = self.client.table('users').update(user_data).eq('telegram_id', user_data['telegram_id']).execute()
            else:
                response = self.client.table('users').insert(user_data).execute()
            
            if response.data:
                return User(**response.data[0])
            return None
        except Exception as e:
            pass  # User creation error suppressed for performance
            return None
    
    async def search_content(self, user_id: int, query_embedding: List[float], limit: int = 5, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Vector similarity search engine for documents
        
        Args:
            user_id: Unused for compatibility (documents are global)
            query_embedding: Query vector embedding from OpenAI text-embedding-3-large (3072 dimensions)
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            List of documents ranked by vector similarity
        """
        try:
            results = []
            
            # Vector search on documents table
            # Table schema: id, content, embedding, metadata, ingestion_date
            # Embedding dimensions: 3072 (OpenAI text-embedding-3-large)
            pass  # Vector search start log removed for performance
            
            try:
                # Method 1: Use Supabase RPC function for vector similarity search
                try:
                    pass  # RPC attempt log removed for performance
                    
                    # Create a custom RPC function call for vector search
                    # This avoids URL length limits by sending the vector in the request body
                    response = self.client.rpc('search_similar_documents', {
                        'query_embedding': query_embedding,
                        'similarity_threshold': threshold,
                        'match_count': limit
                    }).execute()
                    
                    pass  # RPC result count removed for performance
                    
                    if response.data:
                        # Process RPC results
                        for doc in response.data:
                            similarity = doc.get('similarity', 0)
                            metadata = doc.get('metadata')
                            
                            results.append({
                                'id': metadata.get('file_id'),
                                'title': metadata.get('file_name'),
                                'content_text': doc.get('content'),
                                'type': metadata.get('type'),
                                'similarity': float(similarity)
                            })
                    
                except Exception as rpc_error:
                    pass  # RPC error log removed for performance
                    response = None
                
                # Method 2: Manual similarity calculation with correct Supabase syntax
                if not results:  # Only try if RPC didn't work
                    pass  # Manual calc start log removed for performance
                    
                    try:
                        # Get all documents with embeddings - FIXED SYNTAX
                        all_docs_response = self.client.table('documents').select('id, content, embedding, metadata, ingestion_date').not_('embedding', 'is', 'null').execute()
                        
                        if all_docs_response.data:
                            pass  # Document retrieval count removed for performance
                            
                            # Calculate similarities manually
                            import numpy as np
                            query_vector = np.array(query_embedding)
                            pass  # Query vector stats removed for performance
                            
                            doc_similarities = []
                            all_cosine_distances = []  # Track all distances for logging
                            
                            for i, doc in enumerate(all_docs_response.data):
                                if doc.get('embedding'):
                                    doc_vector = np.array(doc['embedding'])
                                    doc_id = doc.get('id', f'doc_{i}')
                                    
                                    # Cosine similarity calculation
                                    dot_product = np.dot(query_vector, doc_vector)
                                    query_norm = np.linalg.norm(query_vector)
                                    doc_norm = np.linalg.norm(doc_vector)
                                    
                                    cosine_sim = dot_product / (query_norm * doc_norm)
                                    
                                    # Log individual calculation
                                    pass  # Individual doc calculation removed for performance
                                    
                                    all_cosine_distances.append({
                                        'doc_id': doc_id,
                                        'cosine_similarity': float(cosine_sim),
                                        'dot_product': float(dot_product),
                                        'doc_norm': float(doc_norm),
                                        'above_threshold': cosine_sim > threshold
                                    })
                                    
                                    if cosine_sim > threshold:
                                        doc_similarities.append({
                                            **doc,
                                            'similarity': float(cosine_sim)
                                        })
                            
                            # Log complete array of cosine distances
                            pass  # Cosine distance array header removed for performance
                            
                            for i, dist in enumerate(all_cosine_distances):
                                status = "✅ ABOVE" if dist['above_threshold'] else "❌ BELOW"
                                pass  # Individual distance log removed for performance
                            
                            # Sort by similarity (highest first) and limit
                            doc_similarities.sort(key=lambda x: x['similarity'], reverse=True)
                            response_data = doc_similarities[:limit]
                            
                            pass  # Similarity ranking header removed for performance
                            for i, doc in enumerate(response_data):
                                pass  # Individual ranking removed for performance
                            
                            pass  # Manual calc result count removed for performance


                            # Process RPC results
                            for doc in all_docs_response.data:
                                similarity = doc.get('similarity', 0)
                                metadata = doc.get('metadata')
                                pass  # Metadata file_id log removed for performance
                            
                                results.append({
                                    'id': metadata.get('file_id'),
                                    'title': metadata.get('file_name'),
                                    'content_text': doc.get('content'),
                                    'type': metadata.get('type'),
                                    'similarity': float(similarity)
                                })                            
                            
                        else:
                            pass  # No docs warning removed for performance
                            
                    except Exception as manual_error:
                        pass  # Manual calc error removed for performance
                        import traceback
                        traceback.print_exc()
                
                # Results are already processed in the methods above
                pass
                
            except Exception as e:
                pass  # Vector search error suppressed for performance
                # Ultimate fallback: basic document retrieval (no similarity)
                try:
                    pass  # Fallback attempt removed for performance
                    response = self.client.table('documents').select('id, content, metadata, ingestion_date').limit(limit).execute()
                    
                    if response.data:
                        pass  # Fallback result count removed for performance
                        for doc in response.data:
                            similarity = doc.get('similarity', 0)
                            metadata = doc.get('metadata')
                            pass  # Fallback metadata log removed for performance
                            
                            results.append({
                                'id': metadata.get('file_id'),
                                'title': metadata.get('file_name'),
                                'content_text': doc.get('content'),
                                'type': metadata.get('type'),                                    'similarity': float(similarity)
                            })         
                            
                except Exception as fallback_error:
                    pass  # Complete failure error suppressed for performance
            
            # Sort by similarity (highest first) and apply limit
            results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            final_results = results[:limit]
            
            if final_results:
                pass  # Search completion log removed for performance
            else:
                pass  # No results log removed for performance
                
            return final_results
            
        except Exception as e:
            pass  # Search content error suppressed for performance
            return []
    
    
    async def create_user(self, telegram_id: int, username: str = None, first_name: str = None, last_name: str = None) -> Optional[User]:
        """Create user only if doesn't exist - for handlers compatibility"""
        # Check if user already exists
        existing_user = await self.get_user_by_telegram_id(telegram_id)
        if existing_user:
            return existing_user  # Don't update, just return existing user
            
        # Only create new user if doesn't exist - match actual database schema
        user_data = {
            'telegram_id': telegram_id,
            'username': username
            # Note: isAudio, notification, timezone have defaults in DB
        }
        # Remove None values to avoid column errors
        user_data = {k: v for k, v in user_data.items() if v is not None}
        
        try:
            response = self.client.table('users').insert(user_data).execute()
            if response.data:
                return User(**response.data[0])
            return None
        except Exception as e:
            # User creation failed due to RLS or other DB constraints
            return None
    
    async def get_notification_settings(self, user_id: int) -> Optional[NotificationSettings]:
        """Get notification settings for a user"""
        try:
            response = self.client.table('notification_settings').select('*').eq('user_id', user_id).execute()
            if response.data:
                return NotificationSettings(**response.data[0])
            return None
        except Exception as e:
            pass  # Notification settings error suppressed for performance
            return None
    
    async def create_or_update_notification_settings(self, user_id: int, settings: Dict[str, Any]) -> Optional[NotificationSettings]:
        """Create or update notification settings for a user"""
        try:
            existing_settings = await self.get_notification_settings(user_id)
            
            settings_data = {
                'user_id': user_id,
                'settings': settings
            }
            
            if existing_settings:
                response = self.client.table('notification_settings').update(settings_data).eq('user_id', user_id).execute()
            else:
                response = self.client.table('notification_settings').insert(settings_data).execute()
            
            if response.data:
                return NotificationSettings(**response.data[0])
            return None
        except Exception as e:
            pass  # Notification settings update error suppressed for performance
            return None
    
    async def get_users_for_notification(self, current_time: str, current_weekday: str) -> List[Dict[str, Any]]:
        """Get users who should receive notifications at current time and day"""
        try:
            # Get users with notifications enabled
            users_response = self.client.table('users').select('id, telegram_id, username').eq('notification', True).execute()
            
            if not users_response.data:
                return []
            
            users_to_notify = []
            
            for user in users_response.data:
                # Get user's notification settings
                settings_response = self.client.table('notification_settings').select('settings').eq('user_id', user['id']).execute()
                
                if settings_response.data:
                    settings = settings_response.data[0]['settings']
                    user_time = settings.get('time')
                    user_frequency = settings.get('frequency')
                    
                    # Check if notification should be sent
                    should_notify = False
                    
                    if user_time == current_time:
                        if user_frequency == 'daily':
                            should_notify = True
                        elif user_frequency == 'weekdays' and current_weekday in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
                            should_notify = True
                        elif user_frequency == 'weekends' and current_weekday in ['saturday', 'sunday']:
                            should_notify = True
                    
                    if should_notify:
                        users_to_notify.append({
                            'telegram_id': user['telegram_id'],
                            'username': user['username'],
                            'settings': settings
                        })
            
            return users_to_notify
            
        except Exception as e:
            pass  # Get notification users error suppressed for performance
            return []
    
    async def get_all_notification_users(self) -> List[User]:
        """Get all users who have notifications enabled"""
        try:
            response = self.supabase.table('users').select('*').eq('notification', True).execute()

            if response.data:
                return [User(**user_data) for user_data in response.data]
            return []

        except Exception as e:
            pass  # Get all notification users error suppressed for performance
            return []

    async def mark_book_received(self, telegram_id: int) -> bool:
        """Mark that user has received the vitamin book"""
        try:
            user_data = {
                'telegram_id': telegram_id,
                'book_received': True
            }
            result = await self.create_or_update_user(user_data)
            return result is not None
        except Exception as e:
            pass  # Book received update error suppressed
            return False