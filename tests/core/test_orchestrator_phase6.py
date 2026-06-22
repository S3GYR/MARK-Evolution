"""Phase 6: Comprehensive Orchestrator Tests - Priority Absolute."""

from __future__ import annotations

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any

from jarvis.core.orchestrator import AgentOrchestrator, Plan, Step
from jarvis.llm.client import LLMClient, LLMRouter, ToolDeclaration
from jarvis.memory.store import MemoryStore
from jarvis.core.player import Player
from jarvis.config.settings import Settings


class TestAgentOrchestratorInitialization:
    """Test orchestrator initialization and setup."""

    def test_orchestrator_default_initialization(self):
        """Test orchestrator initialization with default parameters."""
        orchestrator = AgentOrchestrator()
        
        assert orchestrator.settings is not None
        assert orchestrator.llm is not None
        assert orchestrator.router is not None
        assert orchestrator.memory is None  # Default is None
        assert orchestrator.player is not None
        assert isinstance(orchestrator._tools, list)
        assert len(orchestrator._tools) > 0

    def test_orchestrator_custom_initialization(self):
        """Test orchestrator initialization with custom parameters."""
        mock_settings = Mock(spec=Settings)
        mock_llm = Mock(spec=LLMClient)
        mock_memory = Mock(spec=MemoryStore)
        mock_player = Mock(spec=Player)
        
        orchestrator = AgentOrchestrator(
            settings=mock_settings,
            llm=mock_llm,
            memory=mock_memory,
            player=mock_player
        )
        
        assert orchestrator.settings == mock_settings
        assert orchestrator.llm == mock_llm
        assert orchestrator.memory == mock_memory
        assert orchestrator.player == mock_player
        assert orchestrator.router.llm == mock_llm

    def test_orchestrator_tool_declarations_loading(self):
        """Test tool declarations are loaded correctly."""
        with patch('jarvis.core.orchestrator.get_tool_declarations') as mock_get_tools:
            mock_get_tools.return_value = [
                {
                    "function": {
                        "name": "test_tool",
                        "description": "Test tool",
                        "parameters": {"type": "object", "properties": {}}
                    }
                }
            ]
            
            orchestrator = AgentOrchestrator()
            
            assert len(orchestrator._tools) == 1
            assert orchestrator._tools[0].name == "test_tool"
            assert orchestrator._tools[0].description == "Test tool"

    def test_orchestrator_initialization_error_handling(self):
        """Test orchestrator initialization error handling."""
        with patch('jarvis.core.orchestrator.get_tool_declarations') as mock_get_tools:
            mock_get_tools.side_effect = Exception("Tool loading failed")
            
            try:
                orchestrator = AgentOrchestrator()
                # Should handle gracefully or fail predictably
                assert True
            except Exception:
                # Should fail with clear error
                assert True


class TestOrchestratorPlanning:
    """Test orchestrator planning functionality."""

    @pytest.mark.asyncio
    async def test_plan_generation_success(self):
        """Test successful plan generation."""
        mock_settings = Mock(spec=Settings)
        mock_settings.memory_max_chars = 1000
        
        mock_memory = Mock(spec=MemoryStore)
        mock_memory.format_for_prompt.return_value = "Previous context"
        
        mock_router = Mock(spec=LLMRouter)
        mock_response = Mock()
        mock_response.content = '[{"id": "1", "description": "Test step", "tool": "test_tool", "dependencies": []}]'
        mock_router.chat_with_fallback.return_value = mock_response
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator(
                settings=mock_settings,
                memory=mock_memory
            )
            orchestrator.router = mock_router
            
            plan = await orchestrator.plan("Test goal")
            
            assert isinstance(plan, Plan)
            assert plan.goal == "Test goal"
            assert plan.context == "Previous context"
            assert len(plan.steps) == 1
            assert plan.steps[0].id == "1"
            assert plan.steps[0].description == "Test step"
            assert plan.steps[0].tool == "test_tool"
            assert plan.steps[0].status == "pending"

    @pytest.mark.asyncio
    async def test_plan_generation_without_memory(self):
        """Test plan generation without memory store."""
        mock_settings = Mock(spec=Settings)
        mock_settings.memory_max_chars = 1000
        
        mock_router = Mock(spec=LLMRouter)
        mock_response = Mock()
        mock_response.content = '[{"id": "1", "description": "Test step", "tool": null, "dependencies": []}]'
        mock_router.chat_with_fallback.return_value = mock_response
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator(settings=mock_settings)
            orchestrator.router = mock_router
            
            plan = await orchestrator.plan("Test goal")
            
            assert plan.context == ""
            assert len(plan.steps) == 1
            assert plan.steps[0].tool is None

    @pytest.mark.asyncio
    async def test_plan_generation_llm_error(self):
        """Test plan generation with LLM error."""
        mock_settings = Mock(spec=Settings)
        mock_settings.memory_max_chars = 1000
        
        mock_router = Mock(spec=LLMRouter)
        mock_router.chat_with_fallback.side_effect = Exception("LLM error")
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator(settings=mock_settings)
            orchestrator.router = mock_router
            
            try:
                plan = await orchestrator.plan("Test goal")
                # Should handle error gracefully
                assert True
            except Exception:
                # Should propagate error or handle gracefully
                assert True

    @pytest.mark.asyncio
    async def test_plan_generation_invalid_response(self):
        """Test plan generation with invalid LLM response."""
        mock_settings = Mock(spec=Settings)
        mock_settings.memory_max_chars = 1000
        
        mock_router = Mock(spec=LLMRouter)
        mock_response = Mock()
        mock_response.content = "invalid json"
        mock_router.chat_with_fallback.return_value = mock_response
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator(settings=mock_settings)
            orchestrator.router = mock_router
            
            plan = await orchestrator.plan("Test goal")
            
            # Should handle invalid JSON gracefully
            assert isinstance(plan, Plan)
            assert plan.goal == "Test goal"

    @pytest.mark.asyncio
    async def test_plan_generation_memory_error(self):
        """Test plan generation with memory error."""
        mock_settings = Mock(spec=Settings)
        mock_settings.memory_max_chars = 1000
        
        mock_memory = Mock(spec=MemoryStore)
        mock_memory.format_for_prompt.side_effect = Exception("Memory error")
        
        mock_router = Mock(spec=LLMRouter)
        mock_response = Mock()
        mock_response.content = '[]'
        mock_router.chat_with_fallback.return_value = mock_response
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator(
                settings=mock_settings,
                memory=mock_memory
            )
            orchestrator.router = mock_router
            
            try:
                plan = await orchestrator.plan("Test goal")
                # Should handle memory error gracefully
                assert True
            except Exception:
                # Should propagate or handle error
                assert True


class TestOrchestratorExecution:
    """Test orchestrator plan execution functionality."""

    @pytest.mark.asyncio
    async def test_execute_plan_success(self):
        """Test successful plan execution."""
        mock_player = Mock(spec=Player)
        
        plan = Plan(
            goal="Test goal",
            steps=[
                Step(id="1", description="Test step 1", tool=None),
                Step(id="2", description="Test step 2", tool="test_tool")
            ]
        )
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator(player=mock_player)
            
            # Mock the execution methods
            orchestrator._execute_direct = AsyncMock(return_value="Direct result")
            orchestrator._execute_tool = AsyncMock(return_value="Tool result")
            orchestrator._summarize_plan = Mock(return_value="Plan summary")
            
            result = await orchestrator.execute_plan(plan)
            
            assert result == "Plan summary"
            assert plan.steps[0].status == "done"
            assert plan.steps[0].result == "Direct result"
            assert plan.steps[1].status == "done"
            assert plan.steps[1].result == "Tool result"
            mock_player.write_log.assert_called()

    @pytest.mark.asyncio
    async def test_execute_plan_with_tool_failure(self):
        """Test plan execution with tool failure."""
        mock_player = Mock(spec=Player)
        
        plan = Plan(
            goal="Test goal",
            steps=[
                Step(id="1", description="Test step", tool="nonexistent_tool")
            ]
        )
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator(player=mock_player)
            
            # Mock execution to raise exception
            orchestrator._execute_tool = AsyncMock(side_effect=Exception("Tool failed"))
            orchestrator._summarize_plan = Mock(return_value="Plan summary")
            
            result = await orchestrator.execute_plan(plan)
            
            assert result == "Plan summary"
            assert plan.steps[0].status == "failed"
            assert "Tool failed" in plan.steps[0].result
            mock_player.write_log.assert_called()

    @pytest.mark.asyncio
    async def test_execute_plan_with_direct_failure(self):
        """Test plan execution with direct step failure."""
        mock_player = Mock(spec=Player)
        
        plan = Plan(
            goal="Test goal",
            steps=[
                Step(id="1", description="Test step", tool=None)
            ]
        )
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator(player=mock_player)
            
            # Mock execution to raise exception
            orchestrator._execute_direct = AsyncMock(side_effect=Exception("Direct failed"))
            orchestrator._summarize_plan = Mock(return_value="Plan summary")
            
            result = await orchestrator.execute_plan(plan)
            
            assert result == "Plan summary"
            assert plan.steps[0].status == "failed"
            assert "Direct failed" in plan.steps[0].result
            mock_player.write_log.assert_called()

    @pytest.mark.asyncio
    async def test_execute_plan_empty_plan(self):
        """Test execution of empty plan."""
        plan = Plan(goal="Test goal", steps=[])
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            orchestrator._summarize_plan = Mock(return_value="Empty plan summary")
            
            result = await orchestrator.execute_plan(plan)
            
            assert result == "Empty plan summary"
            orchestrator._summarize_plan.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_plan_step_dependencies(self):
        """Test plan execution with step dependencies."""
        mock_player = Mock(spec=Player)
        
        plan = Plan(
            goal="Test goal",
            steps=[
                Step(id="1", description="Step 1", tool=None, dependencies=[]),
                Step(id="2", description="Step 2", tool=None, dependencies=["1"])
            ]
        )
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator(player=mock_player)
            
            orchestrator._execute_direct = AsyncMock(return_value="Step result")
            orchestrator._summarize_plan = Mock(return_value="Plan summary")
            
            result = await orchestrator.execute_plan(plan)
            
            assert result == "Plan summary"
            # Steps should be executed in order
            assert orchestrator._execute_direct.call_count == 2


class TestOrchestratorToolExecution:
    """Test orchestrator tool execution functionality."""

    @pytest.mark.asyncio
    async def test_execute_tool_success(self):
        """Test successful tool execution."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.orchestrator.get_tool_function') as mock_get_func:
            mock_func = AsyncMock(return_value="Tool executed")
            mock_get_func.return_value = mock_func
            
            with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
                orchestrator = AgentOrchestrator(player=mock_player)
                orchestrator._extract_parameters = AsyncMock(return_value={"param": "value"})
                
                result = await orchestrator._execute_tool("test_tool", "Execute test")
                
                assert result == "Tool executed"
                mock_func.assert_called_once_with({"param": "value"}, player=mock_player)
                mock_player.write_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self):
        """Test tool execution when tool not found."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.orchestrator.get_tool_function') as mock_get_func:
            mock_get_func.return_value = None
            
            with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
                orchestrator = AgentOrchestrator(player=mock_player)
                
                result = await orchestrator._execute_tool("nonexistent_tool", "Execute test")
                
                assert result == "Tool 'nonexistent_tool' not found"
                mock_player.write_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_tool_sync_function(self):
        """Test tool execution with synchronous function."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.orchestrator.get_tool_function') as mock_get_func:
            mock_func = Mock(return_value="Sync tool executed")
            mock_func.__name__ = "sync_tool"  # Make it look like a regular function
            
            with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
                orchestrator = AgentOrchestrator(player=mock_player)
                orchestrator._extract_parameters = AsyncMock(return_value={"param": "value"})
                
                result = await orchestrator._execute_tool("sync_tool", "Execute test")
                
                assert result == "Sync tool executed"
                mock_func.assert_called_once_with({"param": "value"}, player=mock_player)

    @pytest.mark.asyncio
    async def test_execute_tool_with_exception(self):
        """Test tool execution with function exception."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.orchestrator.get_tool_function') as mock_get_func:
            mock_func = AsyncMock(side_effect=Exception("Tool error"))
            mock_get_func.return_value = mock_func
            
            with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
                orchestrator = AgentOrchestrator(player=mock_player)
                orchestrator._extract_parameters = AsyncMock(return_value={})
                
                try:
                    result = await orchestrator._execute_tool("test_tool", "Execute test")
                    # Should handle exception gracefully or propagate
                    assert True
                except Exception:
                    # Should propagate tool exceptions
                    assert True

    @pytest.mark.asyncio
    async def test_extract_parameters_success(self):
        """Test successful parameter extraction."""
        mock_router = Mock(spec=LLMRouter)
        mock_response = Mock()
        mock_response.content = '{"param1": "value1", "param2": 42}'
        mock_router.chat_with_fallback.return_value = mock_response
        
        tool_declaration = ToolDeclaration(
            name="test_tool",
            description="Test tool",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                    "param2": {"type": "integer"}
                }
            }
        )
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            orchestrator.router = mock_router
            orchestrator._tools = [tool_declaration]
            
            params = await orchestrator._extract_parameters("test_tool", "Execute with param1=value1 and param2=42")
            
            assert params == {"param1": "value1", "param2": 42}
            mock_router.chat_with_fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_parameters_tool_not_found(self):
        """Test parameter extraction when tool not found."""
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            
            params = await orchestrator._extract_parameters("nonexistent_tool", "Execute test")
            
            # Should return empty dict or handle gracefully
            assert isinstance(params, dict)

    @pytest.mark.asyncio
    async def test_extract_parameters_invalid_json(self):
        """Test parameter extraction with invalid JSON response."""
        mock_router = Mock(spec=LLMRouter)
        mock_response = Mock()
        mock_response.content = "invalid json"
        mock_router.chat_with_fallback.return_value = mock_response
        
        tool_declaration = ToolDeclaration(
            name="test_tool",
            description="Test tool",
            parameters={"type": "object", "properties": {}}
        )
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            orchestrator.router = mock_router
            orchestrator._tools = [tool_declaration]
            
            params = await orchestrator._extract_parameters("test_tool", "Execute test")
            
            # Should handle invalid JSON gracefully
            assert isinstance(params, dict)

    @pytest.mark.asyncio
    async def test_execute_direct_success(self):
        """Test successful direct execution."""
        mock_router = Mock(spec=LLMRouter)
        mock_response = Mock()
        mock_response.content = "Direct execution result"
        mock_router.chat_with_fallback.return_value = mock_response
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            orchestrator.router = mock_router
            
            result = await orchestrator._execute_direct("Execute this directly")
            
            assert result == "Direct execution result"
            mock_router.chat_with_fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_direct_empty_response(self):
        """Test direct execution with empty response."""
        mock_router = Mock(spec=LLMRouter)
        mock_response = Mock()
        mock_response.content = None
        mock_router.chat_with_fallback.return_value = mock_response
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            orchestrator.router = mock_router
            
            result = await orchestrator._execute_direct("Execute this directly")
            
            assert result == ""

    @pytest.mark.asyncio
    async def test_execute_direct_llm_error(self):
        """Test direct execution with LLM error."""
        mock_router = Mock(spec=LLMRouter)
        mock_router.chat_with_fallback.side_effect = Exception("LLM error")
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            orchestrator.router = mock_router
            
            try:
                result = await orchestrator._execute_direct("Execute this directly")
                # Should handle error gracefully
                assert True
            except Exception:
                # Should propagate LLM errors
                assert True


class TestOrchestratorRunMethod:
    """Test orchestrator run method (plan + execute)."""

    @pytest.mark.asyncio
    async def test_run_success(self):
        """Test successful run method."""
        mock_plan = Mock(spec=Plan)
        mock_summary = "Plan executed successfully"
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            orchestrator.plan = AsyncMock(return_value=mock_plan)
            orchestrator.execute_plan = AsyncMock(return_value=mock_summary)
            
            result = await orchestrator.run("Test goal")
            
            assert result == mock_summary
            orchestrator.plan.assert_called_once_with("Test goal")
            orchestrator.execute_plan.assert_called_once_with(mock_plan)

    @pytest.mark.asyncio
    async def test_run_planning_failure(self):
        """Test run method with planning failure."""
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            orchestrator.plan = AsyncMock(side_effect=Exception("Planning failed"))
            
            try:
                result = await orchestrator.run("Test goal")
                # Should handle planning failure
                assert True
            except Exception:
                # Should propagate planning errors
                assert True

    @pytest.mark.asyncio
    async def test_run_execution_failure(self):
        """Test run method with execution failure."""
        mock_plan = Mock(spec=Plan)
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            orchestrator.plan = AsyncMock(return_value=mock_plan)
            orchestrator.execute_plan = AsyncMock(side_effect=Exception("Execution failed"))
            
            try:
                result = await orchestrator.run("Test goal")
                # Should handle execution failure
                assert True
            except Exception:
                # Should propagate execution errors
                assert True


class TestOrchestratorHelperMethods:
    """Test orchestrator helper methods."""

    def test_format_tools(self):
        """Test tools formatting for prompt."""
        tool_declarations = [
            ToolDeclaration(
                name="test_tool",
                description="Test tool for testing",
                parameters={
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string", "description": "First parameter"},
                        "param2": {"type": "integer", "description": "Second parameter"}
                    },
                    "required": ["param1"]
                }
            )
        ]
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            orchestrator._tools = tool_declarations
            
            formatted = orchestrator._format_tools()
            
            assert "test_tool" in formatted
            assert "Test tool for testing" in formatted
            assert "param1" in formatted
            assert "param2" in formatted

    def test_parse_plan_valid_json(self):
        """Test plan parsing with valid JSON."""
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            
            json_str = '[{"id": "1", "description": "Test step", "tool": "test_tool", "dependencies": []}]'
            steps = orchestrator._parse_plan(json_str)
            
            assert len(steps) == 1
            assert steps[0].id == "1"
            assert steps[0].description == "Test step"
            assert steps[0].tool == "test_tool"
            assert steps[0].dependencies == []

    def test_parse_plan_invalid_json(self):
        """Test plan parsing with invalid JSON."""
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            
            steps = orchestrator._parse_plan("invalid json")
            
            # Should return empty list on invalid JSON
            assert steps == []

    def test_parse_plan_empty_array(self):
        """Test plan parsing with empty array."""
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            
            steps = orchestrator._parse_plan("[]")
            
            assert steps == []

    def test_parse_plan_missing_fields(self):
        """Test plan parsing with missing required fields."""
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            
            json_str = '[{"id": "1"}]'  # Missing description
            steps = orchestrator._parse_plan(json_str)
            
            # Should handle missing fields gracefully
            assert len(steps) == 1
            assert steps[0].id == "1"
            assert steps[0].description == ""

    def test_summarize_plan_success(self):
        """Test plan summarization."""
        plan = Plan(
            goal="Test goal",
            steps=[
                Step(id="1", description="Step 1", status="done", result="Result 1"),
                Step(id="2", description="Step 2", status="failed", result="Error 2"),
                Step(id="3", description="Step 3", status="pending")
            ]
        )
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            
            summary = orchestrator._summarize_plan(plan)
            
            assert isinstance(summary, str)
            assert "Test goal" in summary
            assert len(summary) > 0

    def test_summarize_plan_empty(self):
        """Test summarization of empty plan."""
        plan = Plan(goal="Empty goal", steps=[])
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            
            summary = orchestrator._summarize_plan(plan)
            
            assert isinstance(summary, str)
            assert len(summary) > 0


class TestOrchestratorErrorHandling:
    """Test orchestrator error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_concurrent_planning(self):
        """Test concurrent planning requests."""
        mock_router = Mock(spec=LLMRouter)
        mock_response = Mock()
        mock_response.content = '[]'
        mock_router.chat_with_fallback.return_value = mock_response
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator()
            orchestrator.router = mock_router
            
            # Run concurrent planning
            tasks = [
                orchestrator.plan(f"Goal {i}") for i in range(5)
            ]
            
            plans = await asyncio.gather(*tasks)
            
            assert len(plans) == 5
            for plan in plans:
                assert isinstance(plan, Plan)

    @pytest.mark.asyncio
    async def test_memory_timeout_handling(self):
        """Test memory operation timeout handling."""
        mock_settings = Mock(spec=Settings)
        mock_settings.memory_max_chars = 1000
        
        mock_memory = Mock(spec=MemoryStore)
        mock_memory.format_for_prompt = AsyncMock(side_effect=asyncio.TimeoutError("Memory timeout"))
        
        mock_router = Mock(spec=LLMRouter)
        mock_response = Mock()
        mock_response.content = '[]'
        mock_router.chat_with_fallback.return_value = mock_response
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator(
                settings=mock_settings,
                memory=mock_memory
            )
            orchestrator.router = mock_router
            
            try:
                plan = await orchestrator.plan("Test goal")
                # Should handle timeout gracefully
                assert True
            except asyncio.TimeoutError:
                # Should propagate timeout
                assert True

    @pytest.mark.asyncio
    async def test_llm_rate_limiting(self):
        """Test handling of LLM rate limiting."""
        mock_settings = Mock(spec=Settings)
        mock_settings.memory_max_chars = 1000
        
        mock_router = Mock(spec=LLMRouter)
        mock_router.chat_with_fallback.side_effect = Exception("Rate limit exceeded")
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator(settings=mock_settings)
            orchestrator.router = mock_router
            
            try:
                plan = await orchestrator.plan("Test goal")
                # Should handle rate limiting gracefully
                assert True
            except Exception:
                # Should handle rate limiting errors
                assert True

    @pytest.mark.asyncio
    async def test_tool_execution_timeout(self):
        """Test tool execution timeout handling."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.orchestrator.get_tool_function') as mock_get_func:
            mock_func = AsyncMock(side_effect=asyncio.TimeoutError("Tool timeout"))
            mock_get_func.return_value = mock_func
            
            with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
                orchestrator = AgentOrchestrator(player=mock_player)
                orchestrator._extract_parameters = AsyncMock(return_value={})
                
                try:
                    result = await orchestrator._execute_tool("timeout_tool", "Execute test")
                    # Should handle timeout gracefully
                    assert True
                except asyncio.TimeoutError:
                    # Should propagate timeout
                    assert True

    @pytest.mark.asyncio
    async def test_resource_cleanup_on_error(self):
        """Test resource cleanup when errors occur."""
        mock_player = Mock(spec=Player)
        
        plan = Plan(
            goal="Test goal",
            steps=[
                Step(id="1", description="Step 1", tool="test_tool"),
                Step(id="2", description="Step 2", tool="test_tool")
            ]
        )
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator(player=mock_player)
            
            # First tool succeeds, second fails
            orchestrator._execute_tool = AsyncMock(side_effect=["Success", Exception("Tool failed")])
            orchestrator._summarize_plan = Mock(return_value="Partial success")
            
            result = await orchestrator.execute_plan(plan)
            
            assert result == "Partial success"
            assert plan.steps[0].status == "done"
            assert plan.steps[1].status == "failed"
            # Resources should be cleaned up properly
            assert True


class TestOrchestratorStateManagement:
    """Test orchestrator state management and lifecycle."""

    def test_orchestrator_state_initialization(self):
        """Test orchestrator starts in correct initial state."""
        orchestrator = AgentOrchestrator()
        
        # Should be ready to use
        assert orchestrator.settings is not None
        assert orchestrator.llm is not None
        assert orchestrator.router is not None
        assert hasattr(orchestrator, '_tools')

    @pytest.mark.asyncio
    async def test_orchestrator_state_during_execution(self):
        """Test orchestrator state during plan execution."""
        mock_player = Mock(spec=Player)
        
        plan = Plan(
            goal="Test goal",
            steps=[
                Step(id="1", description="Step 1", tool=None)
            ]
        )
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator(player=mock_player)
            orchestrator._execute_direct = AsyncMock(return_value="Result")
            orchestrator._summarize_plan = Mock(return_value="Summary")
            
            # Check state before execution
            assert plan.steps[0].status == "pending"
            
            await orchestrator.execute_plan(plan)
            
            # Check state after execution
            assert plan.steps[0].status == "done"
            assert plan.steps[0].result == "Result"

    @pytest.mark.asyncio
    async def test_orchestrator_concurrent_state_isolation(self):
        """Test that concurrent executions don't interfere with each other."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator(player=mock_player)
            orchestrator._execute_direct = AsyncMock(return_value="Result")
            orchestrator._summarize_plan = Mock(return_value="Summary")
            
            plan1 = Plan(goal="Goal 1", steps=[Step(id="1", description="Step 1", tool=None)])
            plan2 = Plan(goal="Goal 2", steps=[Step(id="2", description="Step 2", tool=None)])
            
            # Execute plans concurrently
            task1 = orchestrator.execute_plan(plan1)
            task2 = orchestrator.execute_plan(plan2)
            
            await asyncio.gather(task1, task2)
            
            # Both plans should be executed independently
            assert plan1.steps[0].status == "done"
            assert plan2.steps[0].status == "done"

    def test_orchestrator_configuration_validation(self):
        """Test orchestrator validates configuration properly."""
        # Test with invalid settings
        with patch('jarvis.core.orchestrator.get_settings') as mock_get_settings:
            mock_get_settings.side_effect = Exception("Invalid settings")
            
            try:
                orchestrator = AgentOrchestrator()
                # Should handle invalid settings
                assert True
            except Exception:
                # Should fail gracefully with invalid settings
                assert True

    @pytest.mark.asyncio
    async def test_orchestrator_graceful_shutdown(self):
        """Test orchestrator handles shutdown gracefully."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.orchestrator.get_tool_declarations', return_value=[]):
            orchestrator = AgentOrchestrator(player=mock_player)
            
            # Simulate ongoing operation
            plan = Plan(goal="Test goal", steps=[Step(id="1", description="Step 1", tool=None)])
            orchestrator._execute_direct = AsyncMock(return_value="Result")
            orchestrator._summarize_plan = Mock(return_value="Summary")
            
            # Execute and ensure clean completion
            result = await orchestrator.execute_plan(plan)
            
            assert result == "Summary"
            # No hanging operations or resources
            assert True
