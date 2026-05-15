"""
AgentLogger: Structured conversation logging for the LangGraph agent.

Logs user requests, tool calls, LLM thinking, and final responses to a
Unity Catalog Delta table. Supports three log levels (off, min, verbose)
controlled by AGENT_LOG_LEVEL environment variable.

All logging is async, non-blocking, and fire-and-forget.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from databricks.sdk import WorkspaceClient

logger = logging.getLogger(__name__)


class AgentLogger:
    """
    Structured logging for agent conversations.

    Reads environment variables:
    - AGENT_LOG_LEVEL: 'off' | 'min' | 'verbose' (default: 'off')
    - DEBUG_LOG_TABLE: Unity Catalog table path (default: 'slf_srvc.test_db.agent_debug_log')
    - DEBUG_WAREHOUSE_ID: SQL Warehouse ID for statement execution

    In-memory state (keyed by conversation_id):
    - _turn_counter: increments per user message
    - _request_start: datetime when user request was logged
    - _user_prompt_cache: original user question for the turn
    """

    # Log level ordering: off < min < verbose
    LOG_LEVELS = {"off": 0, "min": 1, "verbose": 2}

    def __init__(self, workspace_client: WorkspaceClient):
        """
        Initialize the logger.

        Args:
            workspace_client: Databricks WorkspaceClient for statement execution
        """
        self.workspace_client = workspace_client

        # Read environment variables
        log_level_str = os.getenv("AGENT_LOG_LEVEL", "off").lower()
        self.log_level = self.LOG_LEVELS.get(log_level_str, 0)
        self.log_level_name = log_level_str

        self.debug_log_table = os.getenv(
            "DEBUG_LOG_TABLE", "slf_srvc.test_db.agent_debug_log"
        )
        self.debug_warehouse_id = os.getenv("DEBUG_WAREHOUSE_ID", "")

        # In-memory state
        self._turn_counter: Dict[str, int] = {}
        self._request_start: Dict[str, datetime] = {}
        self._user_prompt_cache: Dict[str, str] = {}

        logger.info(
            "AgentLogger initialized: level=%s, table=%s",
            self.log_level_name,
            self.debug_log_table,
        )

    def _is_enabled(self, min_level: str) -> bool:
        """
        Check if logging is enabled at the given level.

        Args:
            min_level: 'min' or 'verbose'

        Returns:
            True if current log level >= min_level
        """
        min_level_value = self.LOG_LEVELS.get(min_level, 0)
        return self.log_level >= min_level_value

    async def log_user_request(
        self,
        conversation_id: str,
        user_id: str,
        user_prompt: str,
        orchestrator_model: str,
    ) -> None:
        """
        Log the start of a user request.

        Fires at: min, verbose
        Records: start timestamp, increments turn counter, caches user_prompt
        Writes: activity = "User Request"

        Args:
            conversation_id: Chat session UUID
            user_id: User email
            user_prompt: The original user question
            orchestrator_model: LLM endpoint name
        """
        if not self._is_enabled("min"):
            return

        try:
            # Initialize or increment turn counter
            if conversation_id not in self._turn_counter:
                self._turn_counter[conversation_id] = 0
            self._turn_counter[conversation_id] += 1

            # Record start time and cache prompt
            self._request_start[conversation_id] = datetime.utcnow()
            self._user_prompt_cache[conversation_id] = user_prompt

            session_turn = self._turn_counter[conversation_id]

            row = {
                "logged_at": self._request_start[conversation_id],
                "conversation_id": conversation_id,
                "session_turn": session_turn,
                "user_id": user_id,
                "orchestrator_model": orchestrator_model,
                "activity": "User Request",
                "user_prompt": user_prompt,
                "response": None,
                "duration_ms": None,
                "status": "success",
                "error_message": None,
                "raw_payload": None,
                "retrieved_ids": None,
                "similarity_scores": None,
            }

            await self._insert(row)
        except Exception as e:
            logger.error("Error in log_user_request: %s", e, exc_info=True)

    async def log_tool_call(
        self,
        conversation_id: str,
        activity: str,
        tool_input: str,
        response: str,
        duration_ms: int,
        status: str,
        error_message: Optional[str] = None,
        raw_payload: Optional[str] = None,
        retrieved_ids: Optional[str] = None,
        similarity_scores: Optional[str] = None,
    ) -> None:
        """
        Log a tool call (Genie, Vector DB, or Copilot).

        Fires at: verbose only
        activity: "Call Genie" | "Call Vector DB" | "Call Copilot"
        retrieved_ids and similarity_scores only populated for "Call Vector DB"

        Args:
            conversation_id: Chat session UUID
            activity: Tool activity type
            tool_input: Input to the tool
            response: Response from the tool
            duration_ms: Time taken in milliseconds
            status: 'success' or 'error'
            error_message: Error detail if status='error'
            raw_payload: Full JSON payload (verbose level only)
            retrieved_ids: JSON string of matched IDs (Vector DB only)
            similarity_scores: JSON string of similarity scores (Vector DB only)
        """
        if not self._is_enabled("verbose"):
            return

        try:
            # Get cached values
            user_id = "unknown"
            orchestrator_model = "unknown"
            session_turn = self._turn_counter.get(conversation_id, 0)
            user_prompt = self._user_prompt_cache.get(conversation_id, "")

            row = {
                "logged_at": datetime.utcnow(),
                "conversation_id": conversation_id,
                "session_turn": session_turn,
                "user_id": user_id,
                "orchestrator_model": orchestrator_model,
                "activity": activity,
                "user_prompt": user_prompt,
                "response": response[:2000] if response else None,  # Truncate to 2000 chars
                "duration_ms": duration_ms,
                "status": status,
                "error_message": error_message,
                "raw_payload": raw_payload,
                "retrieved_ids": retrieved_ids,
                "similarity_scores": similarity_scores,
            }

            await self._insert(row)
        except Exception as e:
            logger.error("Error in log_tool_call: %s", e, exc_info=True)

    async def log_llm_thinking(
        self, conversation_id: str, orchestrator_model: str
    ) -> None:
        """
        Log LLM thinking activity.

        Fires at: verbose only
        Writes: activity = "LLM Thinking"

        Args:
            conversation_id: Chat session UUID
            orchestrator_model: LLM endpoint name
        """
        if not self._is_enabled("verbose"):
            return

        try:
            # Get cached values
            user_id = "unknown"
            session_turn = self._turn_counter.get(conversation_id, 0)
            user_prompt = self._user_prompt_cache.get(conversation_id, "")

            row = {
                "logged_at": datetime.utcnow(),
                "conversation_id": conversation_id,
                "session_turn": session_turn,
                "user_id": user_id,
                "orchestrator_model": orchestrator_model,
                "activity": "LLM Thinking",
                "user_prompt": user_prompt,
                "response": None,
                "duration_ms": None,
                "status": "success",
                "error_message": None,
                "raw_payload": None,
                "retrieved_ids": None,
                "similarity_scores": None,
            }

            await self._insert(row)
        except Exception as e:
            logger.error("Error in log_llm_thinking: %s", e, exc_info=True)

    async def log_final_response(
        self,
        conversation_id: str,
        user_id: str,
        orchestrator_model: str,
        response: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Log the final response to the user.

        Fires at: min, verbose
        Calculates end-to-end duration_ms
        Cleans up in-memory state after logging

        Args:
            conversation_id: Chat session UUID
            user_id: User email
            orchestrator_model: LLM endpoint name
            response: Final response text
            status: 'success' or 'error'
            error_message: Error detail if status='error'
        """
        if not self._is_enabled("min"):
            return

        try:
            # Calculate duration
            start_time = self._request_start.get(conversation_id)
            duration_ms = None
            if start_time:
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            session_turn = self._turn_counter.get(conversation_id, 0)
            user_prompt = self._user_prompt_cache.get(conversation_id, "")

            row = {
                "logged_at": datetime.utcnow(),
                "conversation_id": conversation_id,
                "session_turn": session_turn,
                "user_id": user_id,
                "orchestrator_model": orchestrator_model,
                "activity": "Final Response",
                "user_prompt": user_prompt,
                "response": response[:2000] if response else None,  # Truncate to 2000 chars
                "duration_ms": duration_ms,
                "status": status,
                "error_message": error_message,
                "raw_payload": None,
                "retrieved_ids": None,
                "similarity_scores": None,
            }

            await self._insert(row)

            # Clean up in-memory state
            self._request_start.pop(conversation_id, None)
            self._user_prompt_cache.pop(conversation_id, None)
            # Note: _turn_counter is NOT cleaned up — it accumulates across turns

        except Exception as e:
            logger.error("Error in log_final_response: %s", e, exc_info=True)

    async def _insert(self, row: Dict[str, Any]) -> None:
        """
        Insert a log row into the Delta table.

        Never raises — errors are printed to stdout only.
        Uses statement_execution.execute_statement() for async execution.

        Args:
            row: Dictionary with log row data
        """
        try:
            if not self.debug_warehouse_id:
                print(
                    f"WARNING: DEBUG_WAREHOUSE_ID not set; log row not inserted: {row}"
                )
                return

            # Build INSERT SQL with proper escaping
            columns = []
            values = []
            for key, value in row.items():
                columns.append(f"`{key}`")
                if value is None:
                    values.append("NULL")
                elif isinstance(value, str):
                    # Escape single quotes
                    escaped = value.replace("'", "''")
                    values.append(f"'{escaped}'")
                elif isinstance(value, datetime):
                    # Format datetime as ISO string
                    values.append(f"'{value.isoformat()}'")
                elif isinstance(value, bool):
                    values.append("true" if value else "false")
                else:
                    # Numbers, etc.
                    values.append(str(value))

            columns_str = ", ".join(columns)
            values_str = ", ".join(values)
            sql = f"INSERT INTO {self.debug_log_table} ({columns_str}) VALUES ({values_str})"

            # Execute asynchronously using statement_execution
            try:
                self.workspace_client.statement_execution.execute_statement(
                    warehouse_id=self.debug_warehouse_id,
                    statement=sql,
                    wait_timeout="10s",
                )
            except Exception as e:
                # Print to stdout but don't raise
                print(f"ERROR: Failed to insert log row: {e}")
                print(f"SQL: {sql}")

        except Exception as e:
            # Catch any other exceptions and print to stdout
            print(f"ERROR in _insert: {e}")
