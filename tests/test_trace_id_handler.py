import unittest
import uuid
import asyncio
from unittest.mock import patch
from core.trace_id_handler import TraceIdHandler


class TestTraceIdHandler(unittest.TestCase):

    async def test_logging_scope(self):
        async with TraceIdHandler.logging_scope():
            trace_id = TraceIdHandler.get_current_trace_id()
            self.assertIsInstance(trace_id, uuid.UUID)

        # After exiting the scope, trace_id should be None
        self.assertIsNone(TraceIdHandler.get_current_trace_id())

    @patch('uuid.uuid4')
    async def test_consistent_trace_id_within_scope(self, mock_uuid4):
        mock_uuid = uuid.UUID('12345678-1234-5678-1234-567812345678')
        mock_uuid4.return_value = mock_uuid

        async with TraceIdHandler.logging_scope():
            self.assertEqual(TraceIdHandler.get_current_trace_id(), mock_uuid)
            self.assertEqual(TraceIdHandler.get_current_trace_id(), mock_uuid)  # Should return the same UUID

    def test_get_current_trace_id_outside_scope(self):
        self.assertIsNone(TraceIdHandler.get_current_trace_id())


if __name__ == '__main__':
    asyncio.run(unittest.main())
