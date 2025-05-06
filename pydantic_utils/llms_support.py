import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import overload
import httpx

from langfuse import Langfuse

from openai import OpenAI

# from google import genai
# from google.genai import types
from google.auth import default
from google.auth.transport.requests import Request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# # Module-level initialization
# BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# SRC_DIR = os.path.join(BASE_DIR, "src")
# sys.path.append(SRC_DIR)



from config.config import config

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_vertex import GoogleVertexProvider
from pydantic_ai import Agent, UserError
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider,Provider
from pydantic_ai.models import cached_async_http_client
from anthropic import AnthropicVertex, AsyncAnthropicVertex
from anthropic import AsyncAnthropic



class VertexAnthropicProvider(AnthropicProvider):
    """Provider for Anthropic vertex API."""

    @property
    def client(self) -> AsyncAnthropicVertex:
        return self._client

    @overload
    def __init__(self, *, anthropic_client: AsyncAnthropicVertex | None = None) -> None: ...

    @overload
    def __init__(self, *, project_id: str | None = None, location: str | None = None, http_client: httpx.AsyncClient | None = None) -> None: ...

    def __init__(
        self,
        *,
        project_id: str | None = None,
        region: str | None = None,
        anthropic_client: AsyncAnthropic | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Create a new Anthropic provider.

        Args:
            api_key: The API key to use for authentication, if not provided, the `ANTHROPIC_API_KEY` environment variable
                will be used if available.
            anthropic_client: An existing [`AsyncAnthropic`](https://github.com/anthropics/anthropic-sdk-python)
                client to use. If provided, the `api_key` and `http_client` arguments will be ignored.
            http_client: An existing `httpx.AsyncClient` to use for making HTTP requests.
        """
        if anthropic_client is not None:
            assert http_client is None, 'Cannot provide both `anthropic_client` and `http_client`'
            assert project_id is None, 'Cannot provide both `anthropic_client` and `project_id`'
            assert region is None, 'Cannot provide both `anthropic_client` and `location`'
            self._client = anthropic_client
        else:
            if not project_id:
                raise UserError(
                    'Set the `GOOGLE_CLOUD_PROJECT_ID` environment variable or pass it via `VertexAnthropicProvider(project_id=...)`'
                    'to use the Anthropic provider.'
                )
            if not region:
                raise UserError(
                    'Set the `VERTEX_LOCATION` environment variable or pass it via `VertexAnthropicProvider(location=...)`'
                    'to use the Anthropic provider.'
                )   

            if http_client is not None:
                self._client = AsyncAnthropicVertex(project_id=project_id, region=region, http_client=http_client)
            else:
                http_client = cached_async_http_client(provider='anthropic')
                self._client = AsyncAnthropicVertex(project_id=project_id, region=region, http_client=http_client)

def get_anthropic_model(reasoner=False):
    logger.info("Getting Anthropic model configuration...")
    if reasoner:
        model_name = config.get("ANTHROPIC_LLM_REASONER_MODEL", 'claude-3-7-sonnet@20250219')
    else:
        model_name = config.get("ANTHROPIC_LLM_MODEL_NAME", 'claude-3-5-sonnet-v2@20241022')
    
    project_id = config.GOOGLE_CLOUD_PROJECT_ID
    location = config.ANTHROPIC_VERTEX_LOCATION  # Use Anthropic-specific location
    
    logger.info(f"Using model: {model_name}")
    logger.info(f"Using location: {location}")
    logger.info(f"Using project: {project_id}")
    
    model = AnthropicModel(
        model_name=model_name, 
        provider=VertexAnthropicProvider(
            project_id=project_id, 
            region=location
        )
    )    
    return model


def get_openai_model(reasoner=False):
    raise NotImplementedError("OpenAI is not supported in the current version")
    logger.info("Getting OpenAI model configuration...")
    if reasoner:
        model_name = config.get("REASONER_MODEL", 'o3-mini')
    else:
        model_name = config.get("OPENAI_LLM_MODEL_NAME", 'gpt-4o-mini')
    
    logger.info(f"Using model name: {model_name}")
    api_key = config.get("OPENAI_API_KEY")
    logger.info(f"OpenAI API key present: {'Yes' if api_key else 'No'}")
    
    if not api_key:
        logger.error("OPENAI_API_KEY not found in config")
        raise ValueError("OPENAI_API_KEY not found in config")
    
    return OpenAIModel(model_name)

def get_gemini_model(reasoner=False):
    logger.info("Getting Gemini model configuration...")
    if reasoner:
        model_name = config.GEMINI_LLM_REASONER_MODEL
    else:
        model_name = config.GEMINI_LLM_MODEL_NAME
    
    project_id = config.GOOGLE_CLOUD_PROJECT_ID
    location = config.VERTEX_LOCATION
    
    # Try to get service account file path from config
    service_account_file = config.GOOGLE_APPLICATION_CREDENTIALS
    logger.info(f"Looking for service account file...")
    logger.info(f"Using model: {model_name}")
    logger.info(f"Using location: {location}")
    
    if service_account_file and os.path.exists(service_account_file):
        logger.info(f"Using service account file from config: {service_account_file}")
        return GeminiModel(
            model_name=model_name,
            provider=GoogleVertexProvider(
                service_account_file=service_account_file,
                project_id=project_id,
                region=location,
                model_publisher='google'
            )
        )
    else:
        logger.info("Using default application credentials")
        return GeminiModel(
            model_name=model_name,
            provider=GoogleVertexProvider(
                project_id=project_id,
                region=location,
                model_publisher='google'
            )
        )



if __name__ == "__main__":
    async def main():
        print(get_gemini_model())
        print(get_anthropic_model())
        print(get_openai_model())
        
        agent = Agent(get_gemini_model(True))
        print(await agent.run("What is the capital of the moon?"))
        
        agent = Agent(get_gemini_model(False))
        print(await agent.run("What is the capital of the moon?"))
        
        agent = Agent(get_anthropic_model(False))
        print(await agent.run("What is the capital of the moon?"))
        
        agent = Agent(get_anthropic_model(True))
        print(await agent.run("What is the capital of the moon?"))
        
        agent = Agent(get_openai_model(True))
        print(await agent.run("What is the capital of the moon?"))

    asyncio.run(main())