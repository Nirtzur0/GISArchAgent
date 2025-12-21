"""Agentic architecture using LangGraph for orchestrating the RAG system."""

import logging
from typing import TypedDict, Annotated, Sequence, Dict, Any
import operator

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.config import settings
from src.tools import ArchitectureTools
from src.vectorstore import VectorStoreManager

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the agent graph."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_action: str
    context: Dict[str, Any]


class ArchitectureAgent:
    """Main agentic RAG system for architecture queries."""
    
    def __init__(self, vectorstore: VectorStoreManager):
        """Initialize the architecture agent.
        
        Args:
            vectorstore: Vector store manager for document retrieval
        """
        self.vectorstore = vectorstore
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=settings.model_name,
            temperature=settings.temperature,
            openai_api_key=settings.openai_api_key
        )
        
        # Initialize tools
        self.tools_manager = ArchitectureTools(vectorstore)
        self.tools = self.tools_manager.get_tools()
        self.tool_node = ToolNode(self.tools)
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Build the agent graph
        self.graph = self._build_graph()
        
        logger.info("Architecture agent initialized")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow.
        
        Returns:
            Compiled StateGraph
        """
        # Define the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self._tools_node)
        workflow.add_node("synthesize", self._synthesize_node)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "synthesize": "synthesize",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")
        workflow.add_edge("synthesize", END)
        
        return workflow.compile()
    
    def _agent_node(self, state: AgentState) -> AgentState:
        """Agent reasoning node.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        messages = state["messages"]
        
        # Create system prompt
        system_prompt = """You are an expert architecture and urban planning assistant specializing in Israeli planning regulations.
You have access to tools to search regulations, planning schemes, zoning information, and TAMA plans.

Your role is to:
1. Understand the user's question about planning regulations, approvals, or zoning
2. Decide which tools to use to gather relevant information
3. Provide clear, accurate answers based on the retrieved information
4. Cite specific regulations and plans when applicable

When answering:
- Be precise and cite specific regulation numbers and plan IDs
- Explain requirements clearly for non-experts
- Note when additional verification is needed from planning authorities
- Consider both national (TAMA) and local regulations

Available information includes:
- Israeli National Outline Plans (TAMA)
- Regional and local planning schemes
- Zoning regulations and designations
- Building rights and requirements
- Blue lines and planning procedures"""
        
        # Add system message if not present
        if not messages or not any(isinstance(m, BaseMessage) and m.type == "system" for m in messages):
            messages = [HumanMessage(content=system_prompt)] + messages
        
        # Get response from LLM
        response = self.llm_with_tools.invoke(messages)
        
        return {
            **state,
            "messages": [response]
        }
    
    def _tools_node(self, state: AgentState) -> AgentState:
        """Execute tools based on agent's decision.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with tool results
        """
        messages = state["messages"]
        last_message = messages[-1]
        
        # Extract tool calls
        tool_calls = last_message.tool_calls if hasattr(last_message, 'tool_calls') else []
        
        if not tool_calls:
            return state
        
        # Execute tools using ToolNode
        # ToolNode expects the state to have messages with tool_calls
        tool_result_state = self.tool_node.invoke(state)
        
        return tool_result_state
    
    def _synthesize_node(self, state: AgentState) -> AgentState:
        """Synthesize final answer from gathered information.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with final answer
        """
        messages = state["messages"]
        
        synthesis_prompt = """Based on the information gathered, provide a comprehensive answer to the user's question.

Structure your answer as:
1. **Direct Answer**: Clear response to the question
2. **Key Regulations**: Relevant regulations and requirements
3. **Additional Considerations**: Important factors to consider
4. **Next Steps**: What the user should do next (if applicable)

Be specific and cite sources where possible."""
        
        # Create synthesis message
        synthesis_message = HumanMessage(content=synthesis_prompt)
        final_response = self.llm.invoke(messages + [synthesis_message])
        
        return {
            **state,
            "messages": [final_response]
        }
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine next step in the graph.
        
        Args:
            state: Current agent state
            
        Returns:
            Next node name
        """
        messages = state["messages"]
        last_message = messages[-1]
        
        # Check if we have tool calls
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        
        # Check if we have enough context to synthesize
        if len([m for m in messages if hasattr(m, 'type') and m.type == "tool"]) > 0:
            return "synthesize"
        
        return "end"
    
    def query(self, question: str) -> str:
        """Query the agent with a question.
        
        Args:
            question: User's question
            
        Returns:
            Agent's response
        """
        logger.info(f"Processing query: {question}")
        
        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content=question)],
            "next_action": "",
            "context": {}
        }
        
        # Run the graph
        result = self.graph.invoke(initial_state)
        
        # Extract final answer
        final_message = result["messages"][-1]
        answer = final_message.content if hasattr(final_message, 'content') else str(final_message)
        
        return answer
    
    async def aquery(self, question: str) -> str:
        """Async version of query.
        
        Args:
            question: User's question
            
        Returns:
            Agent's response
        """
        logger.info(f"Processing async query: {question}")
        
        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content=question)],
            "next_action": "",
            "context": {}
        }
        
        # Run the graph asynchronously
        result = await self.graph.ainvoke(initial_state)
        
        # Extract final answer
        final_message = result["messages"][-1]
        answer = final_message.content if hasattr(final_message, 'content') else str(final_message)
        
        return answer
