import unittest
import uuid
from unittest.mock import patch
from core.trace_id_handler import TraceIdHandler

class TestTraceIdHandler(unittest.TestCase):

    def test_logging_scope(self):
        with TraceIdHandler.logging_scope():
            trace_id = TraceIdHandler.get_current_trace_id()
            self.assertIsInstance(trace_id, uuid.UUID)

        # After exiting the scope, trace_id should be None
        self.assertIsNone(TraceIdHandler.get_current_trace_id())

    def test_nested_logging_scopes(self):
        with TraceIdHandler.logging_scope() as outer_trace_id:
            with TraceIdHandler.logging_scope() as inner_trace_id:
                self.assertNotEqual(outer_trace_id, inner_trace_id)
                self.assertEqual(TraceIdHandler.get_current_trace_id(), inner_trace_id)
            
            # After exiting inner scope, we should be back to outer trace_id
            self.assertEqual(TraceIdHandler.get_current_trace_id(), outer_trace_id)

        # After exiting all scopes, trace_id should be None
        self.assertIsNone(TraceIdHandler.get_current_trace_id())

    @patch('uuid.uuid4')
    def test_consistent_trace_id_within_scope(self, mock_uuid4):
        mock_uuid = uuid.UUID('12345678-1234-5678-1234-567812345678')
        mock_uuid4.return_value = mock_uuid

        with TraceIdHandler.logging_scope():
            self.assertEqual(TraceIdHandler.get_current_trace_id(), mock_uuid)
            self.assertEqual(TraceIdHandler.get_current_trace_id(), mock_uuid)  # Should return the same UUID

    def test_get_current_trace_id_outside_scope(self):
        self.assertIsNone(TraceIdHandler.get_current_trace_id())

if __name__ == '__main__':
    unittest.main()
