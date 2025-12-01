from anthropic import Anthropic
from openai import OpenAI
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime

from ..config import get_settings
from ..models import Instance, Provider

settings = get_settings()


class NLQueryService:
    """Natural language query service using Claude API or OpenAI GPT."""

    def __init__(self):
        """Initialize NL query service."""
        self.anthropic_client = None
        self.openai_client = None
        self.provider = settings.ai_provider

        # Initialize Anthropic Claude client
        if settings.anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)

        # Initialize OpenAI GPT client
        if settings.openai_api_key:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)

    def _get_context_data(self, db: Session) -> Dict[str, Any]:
        """Get context data about infrastructure.

        Args:
            db: Database session

        Returns:
            Context dictionary
        """
        instances = db.query(Instance).all()
        providers = db.query(Provider).all()

        return {
            "total_instances": len(instances),
            "total_cost": sum(inst.monthly_cost for inst in instances),
            "providers": [
                {
                    "name": p.name,
                    "type": p.provider_type,
                    "instance_count": len([i for i in instances if i.provider_id == p.id])
                }
                for p in providers
            ],
            "instances_by_status": {
                "running": len([i for i in instances if i.status == "running"]),
                "stopped": len([i for i in instances if i.status in ["stopped", "shutoff"]])
            },
            "top_expensive": [
                {
                    "name": inst.name,
                    "cost": inst.monthly_cost,
                    "type": inst.instance_type
                }
                for inst in sorted(instances, key=lambda x: x.monthly_cost, reverse=True)[:5]
            ]
        }

    def query(self, db: Session, user_query: str) -> Dict[str, Any]:
        """Process natural language query.

        Args:
            db: Database session
            user_query: User's natural language query

        Returns:
            Response dictionary with answer and data
        """
        # Check if any AI provider is configured
        if self.provider == "anthropic" and not self.anthropic_client:
            return {
                "answer": "Anthropic AI is selected but not configured. Please set ANTHROPIC_API_KEY in .env file.",
                "data": None,
                "suggestions": []
            }
        elif self.provider == "openai" and not self.openai_client:
            return {
                "answer": "OpenAI is selected but not configured. Please set OPENAI_API_KEY in .env file.",
                "data": None,
                "suggestions": []
            }

        try:
            # Get context
            context = self._get_context_data(db)

            # Build prompt
            prompt = f"""You are an AI assistant for a cloud resource management platform.
The user has asked: "{user_query}"

Here is the current infrastructure context:
- Total instances: {context['total_instances']}
- Total monthly cost: ${context['total_cost']:.2f}
- Providers: {', '.join([f"{p['type']} ({p['instance_count']} instances)" for p in context['providers']])}
- Running instances: {context['instances_by_status']['running']}
- Stopped instances: {context['instances_by_status']['stopped']}
- Top expensive resources: {', '.join([f"{r['name']} (${r['cost']:.2f}/mo)" for r in context['top_expensive'][:3]])}

Please provide a clear, concise answer to the user's question based on this data.
If the data doesn't contain enough information, explain what additional data would be needed.
"""

            # Call appropriate AI API based on provider
            if self.provider == "anthropic":
                answer = self._query_anthropic(prompt)
            elif self.provider == "openai":
                answer = self._query_openai(prompt)
            else:
                raise ValueError(f"Unknown AI provider: {self.provider}")

            # Generate follow-up suggestions
            suggestions = self._generate_suggestions(user_query, context)

            return {
                "answer": answer,
                "data": context,
                "suggestions": suggestions,
                "provider": self.provider
            }

        except Exception as e:
            print(f"NL query failed: {e}")
            return {
                "answer": f"I encountered an error processing your query: {str(e)}",
                "data": None,
                "suggestions": [],
                "provider": self.provider
            }

    def _query_anthropic(self, prompt: str) -> str:
        """Query Anthropic Claude API.

        Args:
            prompt: The prompt to send

        Returns:
            AI response text
        """
        message = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text

    def _query_openai(self, prompt: str) -> str:
        """Query OpenAI GPT API.

        Args:
            prompt: The prompt to send

        Returns:
            AI response text
        """
        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant for cloud resource management."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024,
            temperature=0.7
        )
        return response.choices[0].message.content

    def _generate_suggestions(self, query: str, context: Dict[str, Any]) -> List[str]:
        """Generate follow-up query suggestions.

        Args:
            query: Original query
            context: Infrastructure context

        Returns:
            List of suggested follow-up queries
        """
        suggestions = [
            "Show me instances with high CPU usage",
            "What are my most expensive resources?",
            "Find idle instances to save money",
            "Show cost trends for this month"
        ]

        return suggestions[:3]


# Global service instance
nl_query_service = NLQueryService()
