"""
Supabase database client wrapper
"""

import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SupabaseClient:
    """Wrapper for Supabase client with connection management"""

    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """
        Get or create Supabase client singleton

        Returns:
            Supabase client instance
        """
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")

            if not url or not key:
                raise ValueError(
                    "Missing Supabase credentials. "
                    "Please set SUPABASE_URL and SUPABASE_KEY in .env file"
                )

            cls._instance = create_client(url, key)

        return cls._instance

    @classmethod
    def reset_client(cls):
        """Reset the client instance (useful for testing)"""
        cls._instance = None


def get_db() -> Client:
    """
    Convenience function to get database client

    Returns:
        Supabase client instance
    """
    return SupabaseClient.get_client()
