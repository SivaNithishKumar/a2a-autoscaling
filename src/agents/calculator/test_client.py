import asyncio
import logging
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, ClientConfig, ClientFactory, create_text_message_object
from a2a.types import (
    TransportProtocol,
)


async def test_calculator_agent():
    """Test the calculator agent with a simple query."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    base_url = 'http://localhost:8004'

    async with httpx.AsyncClient() as httpx_client:
        # Initialize A2ACardResolver
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )

        try:
            # Fetch agent card
            logger.info(f'Fetching agent card from {base_url}')
            agent_card = await resolver.get_agent_card()
            logger.info(f'Successfully fetched agent card: {agent_card.name}')

            # Initialize modern A2A client using ClientFactory
            config = ClientConfig(
                httpx_client=httpx_client,
                supported_transports=[
                    TransportProtocol.jsonrpc,
                    TransportProtocol.http_json,
                ],
                use_client_preference=True,
            )

            factory = ClientFactory(config)
            client = factory.create(agent_card)

            # Test queries
            test_queries = [
                "What is 15 + 27?",
                "Calculate the square root of 144",
                "What is 12 * 8 / 4?",
                "Convert 100 feet to meters"
            ]

            print(f"\n🔢 Calculator Agent Test Results:")
            print("=" * 50)

            for i, query in enumerate(test_queries, 1):
                logger.info(f'Test {i}: {query}')
                
                # Create message object using the modern helper
                message_obj = create_text_message_object(content=query)

                print(f"\n📝 Query {i}: {query}")
                print("-" * 40)

                # Send message and collect responses
                responses = []
                async for response in client.send_message(message_obj):
                    responses.append(response)

                # Process responses
                response_text = ""
                for response in responses:
                    if isinstance(response, tuple) and len(response) > 0:
                        task = response[0]
                        if hasattr(task, 'history') and task.history:
                            for message in task.history:
                                if hasattr(message, 'parts') and message.parts:
                                    for part in message.parts:
                                        if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                            response_text += part.root.text

                print(f"✅ Result: {response_text.strip()}")

            print("\n" + "=" * 50)
            print("✅ All calculator tests completed successfully!")

        except Exception as e:
            logger.error(f'Error testing calculator agent: {e}')
            raise


if __name__ == '__main__':
    asyncio.run(test_calculator_agent())
