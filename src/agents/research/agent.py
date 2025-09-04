"""Research agent implementation - A2A Standard."""

import asyncio
import logging
import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from dataclasses import dataclass
from datetime import datetime

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentSkill,
    TaskState,
    Part,
    TextPart,
)
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError

# Import metrics collection
from common.metrics import get_agent_metrics


@dataclass
class SearchResult:
    """A single search result."""
    title: str
    url: str
    snippet: str
    score: float = 0.0


@dataclass
class SearchResults:
    """Container for search results."""
    results: List[SearchResult]
    query: str
    total_results: int = 0
    search_time: float = 0.0


@dataclass
class SummaryResult:
    """Result of content summarization."""
    url: str
    title: str
    summary: str
    key_points: List[str]
    success: bool = True
    error: Optional[str] = None


@dataclass
class FactCheckResult:
    """Result of fact checking."""
    claim: str
    verdict: str  # "True", "False", "Partially True", "Insufficient Evidence"
    confidence: float  # 0.0 to 1.0
    evidence: List[str]
    sources: List[SearchResult]
    reasoning: str

# Simplified imports to avoid dependency issues
def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)

def trace_async(operation: str, component: str):
    """Simple trace decorator."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            logger = logging.getLogger(f"{component}.{operation}")
            logger.debug(f"Starting {operation}")
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"Completed {operation}")
                return result
            except Exception as e:
                logger.error(f"Error in {operation}: {e}")
                raise
        return wrapper
    return decorator

# Simple OpenAI client for demonstration
class SimpleAIClient:
    """Simple AI client that returns mock responses."""
    
    async def ainvoke(self, prompt: str) -> Any:
        """Simple mock AI response."""
        class MockResponse:
            def __init__(self, content: str):
                self.content = content
        
        # Research-specific response logic
        if "fact check" in prompt.lower():
            return MockResponse("""**Fact Check Analysis:**

**Verdict:** PARTIALLY TRUE
**Confidence Level:** MEDIUM

**Explanation:** 
Based on available information, this appears to be partially accurate. The core claim has some supporting evidence, but there are important nuances and context that should be considered.

**Sources:**
- Multiple reputable sources provide supporting evidence
- Some contradictory information exists that requires further investigation
- Additional context and recent developments may affect the accuracy

**Recommendation:** 
While there is supporting evidence for this claim, I recommend verifying with multiple primary sources and considering the full context before drawing final conclusions.""")
        
        elif "search" in prompt.lower() or "research" in prompt.lower():
            return MockResponse("""Based on my research capabilities, I can help you find information on this topic. In a production environment, I would:

• Search multiple reliable sources
• Analyze and synthesize the information
• Provide credible references and citations
• Highlight key findings and insights

Currently running in demo mode with mock search results. For real research, I would access live web search APIs and databases.""")
        
        elif "analyze" in prompt.lower():
            return MockResponse("""**Content Analysis Summary:**

**Key Themes:**
- Primary topic focuses on the requested subject
- Multiple perspectives and viewpoints presented
- Current trends and developments highlighted

**Important Facts:**
- Core information and statistics identified
- Supporting evidence and examples provided
- Relevant context and background included

**Conclusions:**
- Well-researched topic with multiple sources
- Balanced perspective considering various viewpoints
- Actionable insights and recommendations available

**Credibility Assessment:**
- Sources appear reliable and authoritative
- Information is current and relevant
- Cross-referenced with multiple databases""")
        
        else:
            return MockResponse(f"""I understand you're looking for research assistance regarding: {prompt[:100]}{'...' if len(prompt) > 100 else ''}

As a research agent, I can help with:
• Web searches and information gathering
• Fact-checking claims and statements
• Content analysis and summarization
• Research on specific topics

Currently running in demo mode. How can I assist with your research needs?""")

def create_azure_chat_openai(temperature: float = 0.3) -> SimpleAIClient:
    """Create a simple AI client for demonstration."""
    return SimpleAIClient()


class ResearchAgent:
    """Research agent that performs web searches and analysis."""
    
    def __init__(self):
        self.name = "Research Agent"
        self.description = "Web search and information research specialist"
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.llm = create_azure_chat_openai(temperature=0.3)
        
        # Initialize metrics collection with separate metrics port
        self.metrics = get_agent_metrics("research", metrics_port=9083)
        
        # Mock data for demonstration (in production, would use real APIs)
        self.mock_mode = True
    
    def get_skills(self) -> List[AgentSkill]:
        """Get the skills this agent provides."""
        return [
            AgentSkill(
                id='web_search',
                name='Web Search',
                description='Search the web for information and return relevant results',
                tags=['search', 'web', 'information', 'research'],
                examples=[
                    'Search for information about artificial intelligence',
                    'Find recent news about climate change',
                    'Look up facts about space exploration'
                ],
            ),
            AgentSkill(
                id='fact_checking',
                name='Fact Checking',
                description='Verify facts and claims with evidence-based analysis',
                tags=['facts', 'verification', 'analysis', 'truth'],
                examples=[
                    'Verify this claim about renewable energy',
                    'Check if this scientific statement is accurate',
                    'Fact-check this news claim'
                ],
            ),
            AgentSkill(
                id='content_analysis',
                name='Content Analysis',
                description='Analyze and summarize content from web sources',
                tags=['content', 'analysis', 'summary', 'research'],
                examples=[
                    'Summarize this article about machine learning',
                    'Analyze the main points in this research',
                    'Extract key information from this content'
                ],
            ),
        ]
    
    @trace_async("web_search", "research_agent")
    async def web_search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Perform a web search for the given query."""
        try:
            self.logger.info(f"Performing web search for: {query}")
            
            if self.mock_mode:
                # Mock search results for demonstration
                mock_results = [
                    {
                        "title": f"Comprehensive Guide to {query}",
                        "url": f"https://example.com/guide-{query.lower().replace(' ', '-')}",
                        "snippet": f"A detailed overview of {query} covering all essential aspects and recent developments in the field.",
                        "relevance": 0.95
                    },
                    {
                        "title": f"Latest Research on {query}",
                        "url": f"https://research.example.com/{query.lower().replace(' ', '-')}-2024",
                        "snippet": f"Recent scientific findings and studies related to {query}, published in peer-reviewed journals.",
                        "relevance": 0.89
                    },
                    {
                        "title": f"{query}: Best Practices and Applications",
                        "url": f"https://tech.example.com/{query.lower().replace(' ', '-')}-applications",
                        "snippet": f"Practical applications and industry best practices for implementing {query} in real-world scenarios.",
                        "relevance": 0.82
                    }
                ]
                
                return {
                    "query": query,
                    "results": mock_results[:max_results],
                    "total_results": len(mock_results),
                    "search_time": "0.45 seconds"
                }
            else:
                # In production, implement real search API calls here
                # For now, return a message about configuration needed
                return {
                    "query": query,
                    "results": [],
                    "error": "Search API not configured. Please set up search service credentials."
                }
                
        except Exception as e:
            self.logger.error(f"Error performing web search: {e}")
            return {
                "query": query,
                "results": [],
                "error": str(e)
            }
    
    @trace_async("fact_check", "research_agent")
    async def fact_check(self, claim: str) -> Dict[str, Any]:
        """Fact-check a claim using web search and analysis."""
        try:
            self.logger.info(f"Fact-checking claim: {claim[:100]}...")
            
            # First, search for information about the claim
            search_results = await self.web_search(f"fact check {claim}", 3)
            
            # Use LLM to analyze the claim
            analysis_prompt = f"""You are a fact-checking expert. Analyze the following claim and provide a detailed assessment:

Claim: "{claim}"

Search Results Context:
{json.dumps(search_results.get('results', []), indent=2)}

Please provide:
1. Verdict: TRUE, FALSE, PARTIALLY TRUE, or UNCLEAR
2. Confidence Level: HIGH, MEDIUM, or LOW
3. Explanation: Detailed reasoning for your assessment
4. Sources: Key evidence that supports or contradicts the claim

Format your response as a clear, structured analysis."""

            response = await self.llm.ainvoke(analysis_prompt)
            analysis_text = response.content if hasattr(response, 'content') else str(response)
            
            return {
                "claim": claim,
                "analysis": analysis_text,
                "search_results": search_results,
                "fact_check_complete": True
            }
            
        except Exception as e:
            self.logger.error(f"Error fact-checking claim: {e}")
            return {
                "claim": claim,
                "error": str(e),
                "analysis": f"Unable to fact-check due to error: {str(e)}"
            }
    
    @trace_async("analyze_content", "research_agent")
    async def analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze and summarize content."""
        try:
            self.logger.info("Analyzing content...")
            
            analysis_prompt = f"""You are a content analysis expert. Please analyze the following content and provide:

1. Summary: A concise summary of the main points
2. Key Themes: The primary themes or topics discussed
3. Important Facts: Key factual information presented
4. Conclusions: Main conclusions or takeaways
5. Credibility Assessment: Your assessment of the content's reliability

Content to analyze:
{content[:2000]}  # Limit content length for processing

Please provide a structured, comprehensive analysis."""

            response = await self.llm.ainvoke(analysis_prompt)
            analysis_text = response.content if hasattr(response, 'content') else str(response)
            
            return {
                "content_length": len(content),
                "analysis": analysis_text,
                "analysis_complete": True
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing content: {e}")
            return {
                "error": str(e),
                "analysis": f"Unable to analyze content due to error: {str(e)}"
            }
    
    @trace_async("process_query", "research_agent")
    async def process_query(self, query: str, context_id: str) -> Dict[str, Any]:
        """Process a research query and determine the appropriate action."""
        # Determine skill type from query
        query_lower = query.lower()
        if any(term in query_lower for term in ['search', 'find', 'look up', 'research']):
            skill = "web_search"
        elif any(term in query_lower for term in ['fact check', 'verify', 'true', 'false', 'accurate']):
            skill = "fact_checking"
        elif any(term in query_lower for term in ['analyze', 'summarize', 'explain', 'what is']):
            skill = "content_analysis"
        else:
            skill = "general_research"
        
        async with self.metrics.track_request_duration(skill):
            try:
                self.logger.info(f"Processing research query: {query[:100]}...")
                
                # Determine query type and route accordingly
                query_lower = query.lower()
                
                if any(term in query_lower for term in ['search', 'find', 'look up', 'research']):
                    # Web search query
                    result = await self.web_search(query, 5)
                    
                    # Format search results for user
                    if result.get('results'):
                        formatted_response = f"🔍 **Search Results for:** {query}\n\n"
                        for i, item in enumerate(result['results'], 1):
                            formatted_response += f"**{i}. {item['title']}**\n"
                            formatted_response += f"   {item['snippet']}\n"
                            formatted_response += f"   🔗 {item['url']}\n\n"
                        
                        if result.get('total_results', 0) > len(result['results']):
                            formatted_response += f"...and {result['total_results'] - len(result['results'])} more results available.\n"
                    else:
                        formatted_response = f"No search results found for: {query}"
                    
                    return {
                        "content": formatted_response,
                        "is_task_complete": True,
                        "require_user_input": False,
                        "search_data": result
                    }
                
                elif any(term in query_lower for term in ['fact check', 'verify', 'true', 'false', 'accurate']):
                    # Fact-checking query
                    result = await self.fact_check(query)
                    
                    formatted_response = f"🔍 **Fact Check Analysis**\n\n"
                    formatted_response += result.get('analysis', 'Analysis not available')
                    
                    return {
                        "content": formatted_response,
                        "is_task_complete": True,
                        "require_user_input": False,
                        "fact_check_data": result
                    }
                    
                elif any(term in query_lower for term in ['analyze', 'summarize', 'explain', 'what is']):
                    # Content analysis query
                    result = await self.analyze_content(query)
                    
                    formatted_response = f"📊 **Content Analysis**\n\n"
                    formatted_response += result.get('analysis', 'Analysis not available')
                    
                    return {
                        "content": formatted_response,
                        "is_task_complete": True,
                        "require_user_input": False,
                        "analysis_data": result
                    }
                    
                else:
                    # General research query - perform search and analysis
                    search_result = await self.web_search(query, 3)
                    
                    # Use LLM to provide comprehensive response
                    research_prompt = f"""You are a research assistant. The user asked: "{query}"

Based on the following search results, provide a comprehensive, informative response:

Search Results:
{json.dumps(search_result.get('results', []), indent=2)}

Please provide a well-structured, informative response that addresses the user's question using the available information."""

                    response = await self.llm.ainvoke(research_prompt)
                    research_text = response.content if hasattr(response, 'content') else str(response)
                    
                    return {
                        "content": research_text,
                        "is_task_complete": True,
                        "require_user_input": False,
                        "research_data": search_result
                    }
                    
            except Exception as e:
                self.logger.error(f"Error processing query: {e}")
                return {
                    "content": f"I apologize, but I encountered an error while processing your research request: {str(e)}",
                    "is_task_complete": True,
                    "require_user_input": False
                }
    
    async def stream(self, query: str, context_id: str):
        """Stream responses for the given query."""
        result = await self.process_query(query, context_id)
        yield result


class ResearchAgentExecutor(AgentExecutor):
    """Research Agent Executor following A2A samples patterns."""
    
    def __init__(self):
        self.agent = ResearchAgent()
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    @trace_async("execute_task", "research_agent_executor")
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute a research agent task."""
        try:
            # Get user input
            query = context.get_user_input()
            if not query:
                await event_queue.enqueue_event(
                    new_agent_text_message("No research query provided")
                )
                return
            
            # Get or create task
            task = context.current_task
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)
            
            updater = TaskUpdater(event_queue, task.id, task.context_id)
            self.logger.info(f"Processing research request: {query}")
            
            # Stream research results
            async for item in self.agent.stream(query, task.context_id):
                is_task_complete = item['is_task_complete']
                require_user_input = item['require_user_input']
                content = item['content']

                if not is_task_complete and not require_user_input:
                    # Working status
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            content,
                            task.context_id,
                            task.id,
                        ),
                    )
                elif require_user_input:
                    # Input required
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(
                            content,
                            task.context_id,
                            task.id,
                        ),
                        final=True,
                    )
                    break
                else:
                    # Task complete - add result as artifact and complete
                    await updater.add_artifact(
                        [Part(root=TextPart(text=content))],
                        name='research_result',
                    )
                    await updater.complete()
                    break

        except Exception as e:
            self.logger.error(f'Error occurred while processing research request: {e}', exc_info=True)
            
            # Update task with error status
            task = context.current_task
            if task:
                updater = TaskUpdater(event_queue, task.id, task.context_id)
                await updater.update_status(
                    TaskState.failed,
                    new_agent_text_message(
                        f'Research request failed: {str(e)}',
                        task.context_id,
                        task.id,
                    ),
                    final=True,
                )
            
            # Raise server error
            from a2a.types import InternalError
            raise ServerError(error=InternalError()) from e
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel a running task."""
        self.logger.info(f"Cancelling research task: {context.task_id}")
        await event_queue.enqueue_event(
            new_agent_text_message("Research task cancelled by user request")
        )

    @trace_async("process_request", "research_agent")
    async def process_request(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a research request."""
        try:
            message_lower = message.lower()
            
            # Determine request type based on keywords
            if any(word in message_lower for word in ['summarize', 'summary', 'url', 'http', 'www']):
                # Content summarization request
                return await self._handle_summarization_request(message)
            elif any(word in message_lower for word in ['fact check', 'verify', 'true', 'false', 'accurate']):
                # Fact checking request
                return await self._handle_fact_check_request(message)
            elif any(word in message_lower for word in ['research', 'investigate', 'analyze', 'study']):
                # Comprehensive research request
                return await self._handle_research_request(message)
            else:
                # Default to web search
                return await self._handle_search_request(message)
                
        except Exception as e:
            self.logger.error(f"Error processing research request: {e}")
            return {
                "success": False,
                "error": f"Research request failed: {str(e)}",
                "result": None
            }
    
    async def web_search(self, query: str, num_results: int = 5) -> SearchResults:
        """Perform web search."""
        try:
            if self.mock_mode:
                return self._get_mock_search_results(query, num_results)
            
            # Real search implementation using Serper API
            if self.serper_api_key:
                return await self._search_with_serper(query, num_results)
            else:
                # Fallback to mock results
                return self._get_mock_search_results(query, num_results)
                
        except Exception as e:
            self.logger.error(f"Error performing web search: {e}")
            raise ValueError(f"Search failed for query '{query}': {str(e)}")
    
    async def summarize_content(self, url: str) -> SummaryResult:
        """Summarize content from a URL."""
        try:
            if self.mock_mode:
                return self._get_mock_summary(url)
            
            # Fetch content from URL
            content = await self._fetch_url_content(url)
            
            # Use LLM to summarize
            summary = await self._generate_summary_with_llm(content, url)
            
            return summary
                
        except Exception as e:
            self.logger.error(f"Error summarizing content: {e}")
            raise ValueError(f"Failed to summarize {url}: {str(e)}")
    
    async def fact_check(self, claim: str) -> FactCheckResult:
        """Verify factual claims."""
        try:
            if self.mock_mode:
                return self._get_mock_fact_check(claim)
            
            # Search for information about the claim
            search_results = await self.web_search(claim, 5)
            
            # Use LLM to analyze the evidence
            verdict = await self._analyze_claim_with_llm(claim, search_results)
            
            return verdict
                
        except Exception as e:
            self.logger.error(f"Error fact-checking claim: {e}")
            raise ValueError(f"Fact check failed for claim '{claim}': {str(e)}")
    
    def _get_mock_search_results(self, query: str, num_results: int) -> SearchResults:
        """Generate mock search results for testing."""
        results = []
        
        for i in range(min(num_results, 5)):
            result = SearchResult(
                title=f"Search Result {i+1} for '{query}'",
                url=f"https://example.com/result-{i+1}",
                snippet=f"This is a mock search result snippet for query '{query}'. "
                       f"It contains relevant information about the search topic.",
                relevance_score=0.9 - (i * 0.1),
                source="mock_search"
            )
            results.append(result)
        
        return SearchResults(
            query=query,
            results=results,
            total_results=len(results),
            search_time=0.1,
            source_engine="mock"
        )
    
    def _get_mock_summary(self, url: str) -> SummaryResult:
        """Generate mock content summary for testing."""
        # Extract domain from URL for more realistic summary
        domain = urlparse(url).netloc if url.startswith('http') else "example.com"
        
        return SummaryResult(
            url=url,
            title=f"Content from {domain}",
            summary=f"This is a mock summary of content from {url}. "
                   f"The content discusses various topics related to the URL domain "
                   f"and provides useful information for users.",
            key_points=[
                "Key point 1: Important information extracted from content",
                "Key point 2: Additional insights from the source",
                "Key point 3: Relevant details for the user"
            ],
            word_count=250,
            summary_ratio=0.1
        )
    
    def _get_mock_fact_check(self, claim: str) -> FactCheckResult:
        """Generate mock fact check result for testing."""
        # Simple logic for demo - real implementation would use LLM analysis
        verdict = "partially_true"
        confidence = 0.7
        
        if any(word in claim.lower() for word in ['always', 'never', 'all', 'none']):
            verdict = "false"
            confidence = 0.8
        elif any(word in claim.lower() for word in ['sometimes', 'often', 'usually']):
            verdict = "true"
            confidence = 0.6
        
        return FactCheckResult(
            claim=claim,
            verdict=verdict,
            confidence=confidence,
            evidence=[
                "Evidence 1: Supporting information found in reliable sources",
                "Evidence 2: Contradictory information suggests nuanced truth",
                "Evidence 3: Additional context provides clarity"
            ],
            sources=[
                "https://example.com/source1",
                "https://example.com/source2",
                "https://example.com/source3"
            ],
            reasoning=f"The claim '{claim}' is assessed as {verdict} based on "
                     f"available evidence with {confidence:.1%} confidence."
        )
    
    async def _search_with_serper(self, query: str, num_results: int) -> SearchResults:
        """Perform search using Serper API."""
        try:
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            data = {
                "q": query,
                "num": num_results
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result_data = await response.json()
                        return self._parse_serper_results(result_data, query)
                    else:
                        raise ValueError(f"Serper API error: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Serper search failed: {e}")
            # Fallback to mock results
            return self._get_mock_search_results(query, num_results)
    
    def _parse_serper_results(self, data: Dict, query: str) -> SearchResults:
        """Parse results from Serper API."""
        results = []
        
        for item in data.get("organic", []):
            result = SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                relevance_score=None,
                source="serper"
            )
            results.append(result)
        
        return SearchResults(
            query=query,
            results=results,
            total_results=len(results),
            search_time=data.get("searchParameters", {}).get("time", 0.0),
            source_engine="google"
        )
    
    async def _fetch_url_content(self, url: str) -> str:
        """Fetch content from a URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Basic content extraction (you might want to use libraries like BeautifulSoup)
                        return self._extract_text_content(content)
                    else:
                        raise ValueError(f"HTTP {response.status}")
        except Exception as e:
            raise ValueError(f"Failed to fetch content from {url}: {str(e)}")
    
    def _extract_text_content(self, html: str) -> str:
        """Extract text content from HTML (basic implementation)."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:5000]  # Limit content length
    
    async def _generate_summary_with_llm(self, content: str, url: str) -> SummaryResult:
        """Generate summary using LLM."""
        try:
            llm = create_azure_chat_openai(temperature=0.1)
            
            prompt = f"""
            Summarize the following content from {url}:
            
            Content:
            {content[:2000]}...
            
            Please provide:
            1. A concise summary (2-3 sentences)
            2. 3-5 key points
            3. The main title/topic
            
            Format your response as JSON:
            {{
                "title": "...",
                "summary": "...",
                "key_points": ["point1", "point2", "point3"]
            }}
            """
            
            response = await llm.ainvoke(prompt)
            result_data = json.loads(response.content.strip())
            
            return SummaryResult(
                url=url,
                title=result_data.get("title", "Content Summary"),
                summary=result_data.get("summary", ""),
                key_points=result_data.get("key_points", []),
                word_count=len(content.split()),
                summary_ratio=len(result_data.get("summary", "").split()) / len(content.split())
            )
            
        except Exception as e:
            self.logger.error(f"LLM summarization failed: {e}")
            return self._get_mock_summary(url)
    
    async def _analyze_claim_with_llm(self, claim: str, search_results: SearchResults) -> FactCheckResult:
        """Analyze claim using LLM and search results."""
        try:
            llm = create_azure_chat_openai(temperature=0.1)
            
            evidence_text = "\n".join([
                f"Source: {result.title}\nContent: {result.snippet}"
                for result in search_results.results[:3]
            ])
            
            prompt = f"""
            Fact-check this claim: "{claim}"
            
            Based on the following evidence:
            {evidence_text}
            
            Provide your analysis as JSON:
            {{
                "verdict": "true|false|partially_true|unverified",
                "confidence": 0.0-1.0,
                "reasoning": "explanation",
                "evidence": ["evidence1", "evidence2", "evidence3"]
            }}
            """
            
            response = await llm.ainvoke(prompt)
            result_data = json.loads(response.content.strip())
            
            return FactCheckResult(
                claim=claim,
                verdict=result_data.get("verdict", "unverified"),
                confidence=result_data.get("confidence", 0.5),
                evidence=result_data.get("evidence", []),
                sources=[result.url for result in search_results.results[:3]],
                reasoning=result_data.get("reasoning", "")
            )
            
        except Exception as e:
            self.logger.error(f"LLM fact-check failed: {e}")
            return self._get_mock_fact_check(claim)
    
    async def _handle_search_request(self, message: str) -> Dict[str, Any]:
        """Handle a web search request."""
        try:
            # Extract search query
            query = await self._extract_search_query_with_llm(message)
            num_results = 5
            
            # Extract number of results if specified
            import re
            num_matches = re.findall(r'(\d+)\s*results?', message.lower())
            if num_matches:
                num_results = min(int(num_matches[0]), 20)
            
            result = await self.web_search(query, num_results)
            
            return {
                "success": True,
                "result": result.model_dump(),
                "type": "search"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    async def _handle_summarization_request(self, message: str) -> Dict[str, Any]:
        """Handle a content summarization request."""
        try:
            # Extract URL from message
            url = await self._extract_url_with_llm(message)
            
            result = await self.summarize_content(url)
            
            return {
                "success": True,
                "result": result.model_dump(),
                "type": "summary"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    async def _handle_fact_check_request(self, message: str) -> Dict[str, Any]:
        """Handle a fact checking request."""
        try:
            # Extract claim from message
            claim = await self._extract_claim_with_llm(message)
            
            result = await self.fact_check(claim)
            
            return {
                "success": True,
                "result": result.model_dump(),
                "type": "fact_check"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    async def _handle_research_request(self, message: str) -> Dict[str, Any]:
        """Handle a comprehensive research request."""
        try:
            # Extract research topic
            topic = await self._extract_research_topic_with_llm(message)
            
            # Perform multiple searches for comprehensive research
            search_results = await self.web_search(topic, 10)
            
            # Generate research summary
            research_summary = await self._generate_research_summary(topic, search_results)
            
            return {
                "success": True,
                "result": {
                    "topic": topic,
                    "search_results": search_results.model_dump(),
                    "summary": research_summary
                },
                "type": "research"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    async def _extract_search_query_with_llm(self, text: str) -> str:
        """Extract search query using LLM."""
        try:
            llm = create_azure_chat_openai(temperature=0.0)
            
            prompt = f"""
            Extract the search query from this request:
            
            Text: "{text}"
            
            Return only the search query (what to search for).
            Do not include any explanation, just the query.
            """
            
            response = await llm.ainvoke(prompt)
            query = response.content.strip().replace('"', '')
            
            return query if query else text
            
        except Exception as e:
            self.logger.warning(f"LLM query extraction failed: {e}")
            return text
    
    async def _extract_url_with_llm(self, text: str) -> str:
        """Extract URL using LLM."""
        try:
            # First try regex
            url_pattern = r'https?://[^\s]+'
            urls = re.findall(url_pattern, text)
            if urls:
                return urls[0]
            
            # Fallback to LLM
            llm = create_azure_chat_openai(temperature=0.0)
            
            prompt = f"""
            Extract the URL from this text:
            
            Text: "{text}"
            
            Return only the URL. If no URL is found, return "no-url".
            """
            
            response = await llm.ainvoke(prompt)
            url = response.content.strip().replace('"', '')
            
            return url if url != "no-url" else "https://example.com"
            
        except Exception as e:
            self.logger.warning(f"URL extraction failed: {e}")
            return "https://example.com"
    
    async def _extract_claim_with_llm(self, text: str) -> str:
        """Extract claim to fact-check using LLM."""
        try:
            llm = create_azure_chat_openai(temperature=0.0)
            
            prompt = f"""
            Extract the claim that needs fact-checking from this text:
            
            Text: "{text}"
            
            Return only the factual claim to be verified.
            Do not include any explanation, just the claim.
            """
            
            response = await llm.ainvoke(prompt)
            claim = response.content.strip().replace('"', '')
            
            return claim if claim else text
            
        except Exception as e:
            self.logger.warning(f"Claim extraction failed: {e}")
            return text
    
    async def _extract_research_topic_with_llm(self, text: str) -> str:
        """Extract research topic using LLM."""
        try:
            llm = create_azure_chat_openai(temperature=0.0)
            
            prompt = f"""
            Extract the research topic from this request:
            
            Text: "{text}"
            
            Return only the main topic to research.
            Do not include any explanation, just the topic.
            """
            
            response = await llm.ainvoke(prompt)
            topic = response.content.strip().replace('"', '')
            
            return topic if topic else text
            
        except Exception as e:
            self.logger.warning(f"Topic extraction failed: {e}")
            return text
    
    async def _generate_research_summary(self, topic: str, search_results: SearchResults) -> str:
        """Generate research summary using LLM."""
        try:
            llm = create_azure_chat_openai(temperature=0.2)
            
            results_text = "\n".join([
                f"- {result.title}: {result.snippet}"
                for result in search_results.results[:5]
            ])
            
            prompt = f"""
            Based on the search results below, provide a comprehensive research summary for the topic: "{topic}"
            
            Search Results:
            {results_text}
            
            Provide a well-structured summary covering:
            1. Overview of the topic
            2. Key findings
            3. Important details
            4. Conclusions
            """
            
            response = await llm.ainvoke(prompt)
            return response.content.strip()
            
        except Exception as e:
            self.logger.error(f"Research summary generation failed: {e}")
            return f"Research summary for '{topic}' could not be generated due to an error."
