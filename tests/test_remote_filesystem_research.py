import base64
import tempfile
import time
import unittest
from pathlib import Path

from remote_filesystem_research import (
    DEFAULT_PORT,
    MessageType,
    MonitoringAgent,
    ProtocolMessage,
    format_bytes,
)


class ProtocolMessageTests(unittest.TestCase):
    def test_dict_payload_round_trip(self):
        message = ProtocolMessage(MessageType.DIRECTORY_LIST, 7, 1234.9, {"path": "."})

        decoded = ProtocolMessage.deserialize(message.serialize())

        self.assertIsNotNone(decoded)
        self.assertEqual(decoded.message_type, MessageType.DIRECTORY_LIST)
        self.assertEqual(decoded.sequence, 7)
        self.assertEqual(decoded.timestamp, 1234)
        self.assertEqual(decoded.payload, {"path": "."})

    def test_binary_payload_round_trip(self):
        message = ProtocolMessage(MessageType.DATA_RESPONSE, 3, time.time(), b"binary-data")

        decoded = ProtocolMessage.deserialize(message.serialize())

        self.assertEqual(decoded.payload, b"binary-data")

    def test_incomplete_messages_are_rejected(self):
        self.assertIsNone(ProtocolMessage.deserialize(b"short"))
        serialized = ProtocolMessage(MessageType.HEARTBEAT, 0, 1, b"payload").serialize()
        self.assertIsNone(ProtocolMessage.deserialize(serialized[:-1]))


class FormattingTests(unittest.TestCase):
    def test_format_bytes_uses_expected_units(self):
        self.assertEqual(format_bytes(0), "0 B")
        self.assertEqual(format_bytes(1024), "1.0 KB")
        self.assertEqual(format_bytes(1024 * 1024), "1.0 MB")


class MonitoringAgentTests(unittest.TestCase):
    def test_collector_address_defaults_and_explicit_port(self):
        default = MonitoringAgent("localhost")
        explicit = MonitoringAgent("127.0.0.1:9999")

        self.assertEqual(default.collector_address, ("localhost", DEFAULT_PORT))
        self.assertEqual(explicit.collector_address, ("127.0.0.1", 9999))

    def test_non_recursive_scan_handles_multiple_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one.txt").write_text("one", encoding="utf-8")
            (root / "two.txt").write_text("two-two", encoding="utf-8")
            (root / "nested").mkdir()
            agent = MonitoringAgent("localhost", directory)

            files, directories = agent._scan_directory(".", recursive=False)

            self.assertEqual(
                sorted(files, key=lambda item: item["name"]),
                [{"name": "one.txt", "size": 3}, {"name": "two.txt", "size": 7}],
            )
            self.assertEqual(directories, ["nested"])

    def test_recursive_scan_and_single_file_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "nested").mkdir()
            (root / "nested" / "payload.bin").write_bytes(b"12345")
            agent = MonitoringAgent("localhost", directory)

            files, directories = agent._scan_directory(".", recursive=True)
            single, no_directories = agent._scan_directory("nested/payload.bin", recursive=False)

            self.assertEqual(files, [{"name": "nested/payload.bin", "size": 5}])
            self.assertEqual(directories, ["nested"])
            self.assertEqual(single, [{"name": "payload.bin", "size": 5}])
            self.assertEqual(no_directories, [])

    def test_file_chunk_and_command_responses(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "payload.bin").write_bytes(b"abcdefgh")
            agent = MonitoringAgent("localhost", directory)

            chunk = agent._read_file_chunk("payload.bin", offset=2, size=3)
            missing = agent._read_file_chunk("missing.bin", offset=0, size=1)
            heartbeat = agent._handle_command(
                ProtocolMessage(MessageType.HEARTBEAT, 0, time.time(), {})
            )
            unknown = agent._handle_command(ProtocolMessage(255, 0, time.time(), {}))

            self.assertEqual(base64.b64decode(chunk["data"]), b"cde")
            self.assertEqual(chunk["offset"], 2)
            self.assertEqual(chunk["size"], 3)
            self.assertEqual(chunk["total"], 8)
            self.assertEqual(missing, {"error": "File not found"})
            self.assertEqual(heartbeat, {"type": MessageType.HEARTBEAT_ACK})
            self.assertEqual(unknown["type"], MessageType.ERROR_RESPONSE)


if __name__ == "__main__":
    unittest.main()
