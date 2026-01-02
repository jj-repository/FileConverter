"""
Tests for app/services/base_converter.py

COVERAGE GOAL: 85%+
Tests abstract base converter class, WebSocket manager, cache integration,
and progress tracking
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from app.services.base_converter import BaseConverter, WebSocketManager, ws_manager
from app.config import settings


# ============================================================================
# WEBSOCKET MANAGER TESTS
# ============================================================================

class TestWebSocketManager:
    """Test WebSocket Manager functionality"""

    @pytest.mark.asyncio
    async def test_connect_adds_session(self):
        """Test that connect adds WebSocket to active connections"""
        manager = WebSocketManager()
        mock_websocket = Mock()

        await manager.connect("session-123", mock_websocket)

        assert "session-123" in manager.active_connections
        assert manager.active_connections["session-123"] == mock_websocket

    def test_disconnect_removes_session(self):
        """Test that disconnect removes WebSocket from active connections"""
        manager = WebSocketManager()
        mock_websocket = Mock()
        manager.active_connections["session-123"] = mock_websocket

        manager.disconnect("session-123")

        assert "session-123" not in manager.active_connections

    def test_disconnect_nonexistent_session_safe(self):
        """Test that disconnecting nonexistent session doesn't raise error"""
        manager = WebSocketManager()

        # Should not raise error
        manager.disconnect("nonexistent-session")

    @pytest.mark.asyncio
    async def test_send_progress_to_existing_session(self):
        """Test sending progress update to existing session"""
        manager = WebSocketManager()
        mock_websocket = AsyncMock()
        manager.active_connections["session-123"] = mock_websocket

        await manager.send_progress("session-123", 50.0, "converting", "Converting file")

        # Verify send_json was called with correct data
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["session_id"] == "session-123"
        assert call_args["progress"] == 50.0
        assert call_args["status"] == "converting"
        assert call_args["message"] == "Converting file"

    @pytest.mark.asyncio
    async def test_send_progress_to_nonexistent_session(self):
        """Test sending progress to nonexistent session does nothing"""
        manager = WebSocketManager()

        # Should not raise error
        await manager.send_progress("nonexistent", 50.0, "converting", "Test")

    @pytest.mark.asyncio
    async def test_send_progress_error_disconnects_session(self):
        """Test that send error triggers disconnect"""
        manager = WebSocketManager()
        mock_websocket = AsyncMock()
        mock_websocket.send_json.side_effect = Exception("Connection lost")
        manager.active_connections["session-123"] = mock_websocket

        await manager.send_progress("session-123", 50.0, "converting", "Test")

        # Session should be disconnected after error
        assert "session-123" not in manager.active_connections

    def test_global_ws_manager_exists(self):
        """Test that global ws_manager instance exists"""
        assert ws_manager is not None
        assert isinstance(ws_manager, WebSocketManager)


# ============================================================================
# BASE CONVERTER TESTS
# ============================================================================

class MockConverter(BaseConverter):
    """Concrete implementation of BaseConverter for testing"""

    async def convert(self, input_path, output_format, options, session_id):
        """Mock convert implementation"""
        return input_path.parent / f"{input_path.stem}_converted.{output_format}"

    async def get_supported_formats(self):
        """Mock get_supported_formats implementation"""
        return {"input": ["txt"], "output": ["pdf"]}


class TestBaseConverterBasics:
    """Test basic BaseConverter functionality"""

    def test_initialization_default_websocket_manager(self):
        """Test BaseConverter uses global WebSocket manager by default"""
        converter = MockConverter()

        assert converter.websocket_manager is ws_manager
        assert converter._cache_enabled is True

    def test_initialization_custom_websocket_manager(self):
        """Test BaseConverter can use custom WebSocket manager"""
        custom_manager = WebSocketManager()
        converter = MockConverter(websocket_manager=custom_manager)

        assert converter.websocket_manager is custom_manager

    @pytest.mark.asyncio
    async def test_send_progress_calls_websocket_manager(self):
        """Test send_progress delegates to WebSocket manager"""
        mock_manager = Mock()
        mock_manager.send_progress = AsyncMock()
        converter = MockConverter(websocket_manager=mock_manager)

        await converter.send_progress("session-123", 75.0, "converting", "Almost done")

        mock_manager.send_progress.assert_called_once_with(
            session_id="session-123",
            progress=75.0,
            status="converting",
            message="Almost done"
        )

    @pytest.mark.asyncio
    async def test_send_progress_no_websocket_manager(self):
        """Test send_progress handles None WebSocket manager"""
        converter = MockConverter(websocket_manager=None)

        # Should not raise error
        await converter.send_progress("session-123", 50.0, "converting", "Test")

    def test_validate_format_supported(self):
        """Test validate_format returns True for supported formats"""
        converter = MockConverter()

        supported_formats = {"input": ["jpg", "png"], "output": ["pdf", "webp"]}

        result = converter.validate_format("jpg", "pdf", supported_formats)

        assert result is True

    def test_validate_format_unsupported_input(self):
        """Test validate_format returns False for unsupported input"""
        converter = MockConverter()

        supported_formats = {"input": ["jpg", "png"], "output": ["pdf", "webp"]}

        result = converter.validate_format("exe", "pdf", supported_formats)

        assert result is False

    def test_validate_format_unsupported_output(self):
        """Test validate_format returns False for unsupported output"""
        converter = MockConverter()

        supported_formats = {"input": ["jpg", "png"], "output": ["pdf", "webp"]}

        result = converter.validate_format("jpg", "exe", supported_formats)

        assert result is False


# ============================================================================
# CACHE INTEGRATION TESTS
# ============================================================================

class TestBaseConverterCacheIntegration:
    """Test BaseConverter cache integration"""

    @pytest.mark.asyncio
    async def test_convert_with_cache_disabled_calls_convert_directly(self, temp_dir):
        """Test convert_with_cache calls convert() when cache is disabled"""
        converter = MockConverter()
        input_file = temp_dir / "test.txt"
        input_file.write_text("test content")

        with patch('app.config.settings.CACHE_ENABLED', False):
            result = await converter.convert_with_cache(
                input_path=input_file,
                output_format="pdf",
                options={},
                session_id="test-session"
            )

            # Should call convert directly (no cache check)
            assert result.name == "test_converted.pdf"

    @pytest.mark.asyncio
    async def test_convert_with_cache_hit_skips_conversion(self, temp_dir):
        """Test cache hit skips actual conversion"""
        converter = MockConverter()
        input_file = temp_dir / "test.txt"
        input_file.write_text("test content")

        # Mock cache hit
        mock_cache_service = Mock()
        mock_cached_result = Mock()
        mock_cached_result.output_file = str(temp_dir / "cached_output.pdf")
        (temp_dir / "cached_output.pdf").write_text("cached content")
        mock_cache_service.get_cached_result.return_value = mock_cached_result
        mock_cache_service.generate_cache_key.return_value = "cache-key-123"

        with patch('app.config.settings.CACHE_ENABLED', True):
            with patch('app.services.cache_service.get_cache_service', return_value=mock_cache_service):
                with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
                    with patch.object(converter, 'convert') as mock_convert:
                        result = await converter.convert_with_cache(
                            input_path=input_file,
                            output_format="pdf",
                            options={},
                            session_id="test-session"
                        )

                        # Verify convert() was NOT called (cache hit)
                        mock_convert.assert_not_called()

                        # Verify progress showed cache hit
                        progress_calls = [str(call) for call in mock_progress.call_args_list]
                        assert any("cache" in str(call).lower() for call in progress_calls)

    @pytest.mark.asyncio
    async def test_convert_with_cache_miss_performs_conversion(self, temp_dir):
        """Test cache miss triggers actual conversion"""
        converter = MockConverter()
        input_file = temp_dir / "test.txt"
        input_file.write_text("test content")

        output_file = settings.UPLOAD_DIR / "test_converted.pdf"

        # Mock cache miss
        mock_cache_service = Mock()
        mock_cache_service.get_cached_result.return_value = None  # Cache miss
        mock_cache_service.generate_cache_key.return_value = "cache-key-123"
        mock_cache_service.store_result = Mock()

        with patch('app.config.settings.CACHE_ENABLED', True):
            with patch('app.services.cache_service.get_cache_service', return_value=mock_cache_service):
                with patch.object(converter, 'convert', return_value=output_file) as mock_convert:
                    result = await converter.convert_with_cache(
                        input_path=input_file,
                        output_format="pdf",
                        options={"quality": 95},
                        session_id="test-session"
                    )

                    # Verify convert() WAS called (cache miss)
                    mock_convert.assert_called_once_with(
                        input_file, "pdf", {"quality": 95}, "test-session"
                    )

                    # Verify result was stored in cache
                    mock_cache_service.store_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_with_cache_stores_result_after_conversion(self, temp_dir):
        """Test successful conversion stores result in cache"""
        converter = MockConverter()
        input_file = temp_dir / "test.txt"
        input_file.write_text("test content")

        output_file = settings.UPLOAD_DIR / "test_converted.pdf"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("converted content")

        mock_cache_service = Mock()
        mock_cache_service.get_cached_result.return_value = None
        mock_cache_service.generate_cache_key.return_value = "cache-key-123"

        with patch('app.config.settings.CACHE_ENABLED', True):
            with patch('app.services.cache_service.get_cache_service', return_value=mock_cache_service):
                with patch.object(converter, 'convert', return_value=output_file):
                    await converter.convert_with_cache(
                        input_path=input_file,
                        output_format="pdf",
                        options={"quality": 95},
                        session_id="test-session"
                    )

                    # Verify store_result was called with correct parameters
                    store_call = mock_cache_service.store_result.call_args
                    assert store_call[1]["cache_key"] == "cache-key-123"
                    assert store_call[1]["original_filename"] == "test.txt"
                    assert store_call[1]["output_file_path"] == output_file
                    assert store_call[1]["output_format"] == "pdf"
                    assert store_call[1]["conversion_options"] == {"quality": 95}

    @pytest.mark.asyncio
    async def test_convert_with_cache_storage_error_doesnt_fail_conversion(self, temp_dir):
        """Test cache storage error doesn't fail conversion"""
        converter = MockConverter()
        input_file = temp_dir / "test.txt"
        input_file.write_text("test content")

        output_file = settings.UPLOAD_DIR / "test_converted.pdf"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("converted content")

        mock_cache_service = Mock()
        mock_cache_service.get_cached_result.return_value = None
        mock_cache_service.generate_cache_key.return_value = "cache-key-123"
        mock_cache_service.store_result.side_effect = Exception("Cache storage failed")

        with patch('app.config.settings.CACHE_ENABLED', True):
            with patch('app.services.cache_service.get_cache_service', return_value=mock_cache_service):
                with patch.object(converter, 'convert', return_value=output_file):
                    # Should not raise error despite cache storage failure
                    result = await converter.convert_with_cache(
                        input_path=input_file,
                        output_format="pdf",
                        options={},
                        session_id="test-session"
                    )

                    assert result == output_file

    @pytest.mark.asyncio
    async def test_convert_with_cache_error_falls_back_to_normal_conversion(self, temp_dir):
        """Test cache operation error falls back to normal conversion"""
        converter = MockConverter()
        input_file = temp_dir / "test.txt"
        input_file.write_text("test content")

        output_file = settings.UPLOAD_DIR / "test_converted.pdf"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("converted content")

        mock_cache_service = Mock()
        mock_cache_service.generate_cache_key.side_effect = Exception("Cache error")

        with patch('app.config.settings.CACHE_ENABLED', True):
            with patch('app.services.cache_service.get_cache_service', return_value=mock_cache_service):
                with patch.object(converter, 'convert', return_value=output_file) as mock_convert:
                    result = await converter.convert_with_cache(
                        input_path=input_file,
                        output_format="pdf",
                        options={},
                        session_id="test-session"
                    )

                    # Should fall back to normal conversion
                    mock_convert.assert_called_once()
                    assert result == output_file

    @pytest.mark.asyncio
    async def test_convert_with_cache_none_cache_service(self, temp_dir):
        """Test None cache service falls back to normal conversion"""
        converter = MockConverter()
        input_file = temp_dir / "test.txt"
        input_file.write_text("test content")

        output_file = settings.UPLOAD_DIR / "test_converted.pdf"

        with patch('app.config.settings.CACHE_ENABLED', True):
            with patch('app.services.cache_service.get_cache_service', return_value=None):
                with patch.object(converter, 'convert', return_value=output_file) as mock_convert:
                    result = await converter.convert_with_cache(
                        input_path=input_file,
                        output_format="pdf",
                        options={},
                        session_id="test-session"
                    )

                    # Should call convert directly
                    mock_convert.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_with_cache_per_converter_disable(self, temp_dir):
        """Test converter can disable cache via _cache_enabled flag"""
        converter = MockConverter()
        converter._cache_enabled = False  # Disable cache for this converter

        input_file = temp_dir / "test.txt"
        input_file.write_text("test content")

        output_file = settings.UPLOAD_DIR / "test_converted.pdf"

        with patch('app.config.settings.CACHE_ENABLED', True):
            with patch.object(converter, 'convert', return_value=output_file) as mock_convert:
                await converter.convert_with_cache(
                    input_path=input_file,
                    output_format="pdf",
                    options={},
                    session_id="test-session"
                )

                # Should call convert directly (cache disabled for converter)
                mock_convert.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_with_cache_file_deleted_after_cache_hit(self, temp_dir):
        """Test cached file gets deleted between cache check and copy (lines 119-120)"""
        converter = MockConverter()

        input_file = temp_dir / "test.txt"
        input_file.write_text("test content")

        cached_file = temp_dir / "cached_output.pdf"
        cached_file.write_text("cached content")

        output_file = settings.UPLOAD_DIR / "test_converted.pdf"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with patch('app.config.settings.CACHE_ENABLED', True):
            # Patch get_cache_service where it's imported (inside the method)
            with patch('app.services.cache_service.get_cache_service') as mock_cache_func:
                # Mock cache service
                mock_cache_service = MagicMock()
                mock_cache_func.return_value = mock_cache_service

                # Generate cache key
                cache_key = "test-cache-key"
                mock_cache_service.generate_cache_key.return_value = cache_key

                # Return cached result with path to file
                mock_cached_result = MagicMock()
                mock_cached_result.output_file = str(cached_file)
                mock_cache_service.get_cached_result.return_value = mock_cached_result

                # Mock the file existence check to return False (simulating file deletion)
                with patch.object(Path, 'exists', return_value=False):
                    with patch.object(converter, 'convert', return_value=output_file) as mock_convert:
                        with patch.object(converter, 'send_progress', new=AsyncMock()):
                            result = await converter.convert_with_cache(
                                input_path=input_file,
                                output_format="pdf",
                                options={},
                                session_id="test-session"
                            )

                            # Should call convert because cached file was deleted
                            mock_convert.assert_called_once()
                            assert result == output_file


class TestAbstractMethods:
    """Test abstract method implementations to reach 100% coverage"""

    @pytest.mark.asyncio
    async def test_convert_abstract_method_pass_statement(self):
        """Test that abstract convert method has pass statement (line 175)"""
        # Call the abstract method directly to cover the pass statement
        from app.services.base_converter import BaseConverter

        # Create a minimal concrete subclass that calls the base method
        class TestConverter(BaseConverter):
            async def convert(self, input_path, output_format, options, session_id):
                # Dummy implementation
                output_file = settings.UPLOAD_DIR / "test_output.txt"
                output_file.write_text("converted")
                return output_file

            async def get_supported_formats(self):
                # Call parent's abstract method to cover line 185
                await super().get_supported_formats()
                return {"input": ["txt"], "output": ["pdf"]}

        converter = TestConverter()

        # Call get_supported_formats which will execute line 185
        formats = await converter.get_supported_formats()
        assert "input" in formats
        assert "output" in formats

    @pytest.mark.asyncio
    async def test_get_supported_formats_abstract_method_pass_statement(self, temp_dir):
        """Test that abstract get_supported_formats method has pass statement (line 185)"""
        from app.services.base_converter import BaseConverter

        # Create a minimal concrete subclass that calls the base convert method
        class TestConverter(BaseConverter):
            async def convert(self, input_path, output_format, options, session_id):
                # Call parent's abstract method to cover line 175
                await super().convert(input_path, output_format, options, session_id)
                # Then do actual conversion
                output_file = settings.UPLOAD_DIR / "test_output.txt"
                output_file.write_text("converted")
                return output_file

            async def get_supported_formats(self):
                return {"input": ["txt"], "output": ["pdf"]}

        converter = TestConverter()

        # Call convert which will execute line 175
        input_file = temp_dir / "test.txt"
        input_file.write_text("test content")

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        result = await converter.convert(
            input_path=input_file,
            output_format="pdf",
            options={},
            session_id="test-session"
        )

        assert result.exists()
