"""Tests for validate_subprocess_path security function."""

import pytest
from app.utils.validation import validate_subprocess_path
from fastapi import HTTPException


class TestValidateSubprocessPath:
    """Test validate_subprocess_path prevents arbitrary file access."""

    def test_path_within_allowed_dir(self, tmp_path):
        """Path inside allowed dir should return resolved path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("data")
        result = validate_subprocess_path(test_file, [tmp_path])
        assert result == test_file.resolve()

    def test_path_outside_allowed_dir(self, tmp_path):
        """Path outside all allowed dirs should raise 403."""
        other_dir = tmp_path / "allowed"
        other_dir.mkdir()
        test_file = tmp_path / "outside.txt"
        test_file.write_text("data")
        with pytest.raises(HTTPException) as exc_info:
            validate_subprocess_path(test_file, [other_dir])
        assert exc_info.value.status_code == 403

    def test_empty_allowed_dirs(self, tmp_path):
        """Empty allowed_dirs list should reject all paths."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("data")
        with pytest.raises(HTTPException) as exc_info:
            validate_subprocess_path(test_file, [])
        assert exc_info.value.status_code == 403

    def test_path_traversal_attempt(self, tmp_path):
        """Path with .. traversal should be resolved and checked."""
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        # Even with .., resolve() normalizes. Path outside will fail.
        traversal_path = allowed / ".." / "outside.txt"
        (tmp_path / "outside.txt").write_text("data")
        with pytest.raises(HTTPException) as exc_info:
            validate_subprocess_path(traversal_path, [allowed])
        assert exc_info.value.status_code == 403

    def test_multiple_allowed_dirs_second_match(self, tmp_path):
        """Path in second allowed dir should pass."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        test_file = dir2 / "test.txt"
        test_file.write_text("data")
        result = validate_subprocess_path(test_file, [dir1, dir2])
        assert result == test_file.resolve()

    def test_nonexistent_path(self, tmp_path):
        """Nonexistent path should raise (resolve with strict may differ by OS)."""
        fake_path = tmp_path / "nonexistent.txt"
        # validate_subprocess_path doesn't use strict=True on resolve,
        # so it resolves without error but then checks against allowed dirs
        result = validate_subprocess_path(fake_path, [tmp_path])
        assert result == fake_path.resolve()

    def test_subdirectory_allowed(self, tmp_path):
        """File in subdirectory of allowed dir should pass."""
        sub = tmp_path / "sub" / "deep"
        sub.mkdir(parents=True)
        test_file = sub / "test.txt"
        test_file.write_text("data")
        result = validate_subprocess_path(test_file, [tmp_path])
        assert result == test_file.resolve()

    @pytest.mark.skipif(
        not hasattr(__import__("os"), "symlink"),
        reason="Symlinks not supported on this platform",
    )
    def test_symlink_escaping_allowed_dir(self, tmp_path):
        """Symlink pointing outside allowed dir should be rejected."""
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        target_file = outside / "secret.txt"
        target_file.write_text("secret")
        link = allowed / "link.txt"
        try:
            link.symlink_to(target_file)
        except OSError:
            pytest.skip("Cannot create symlinks")
        # resolve() follows symlink, so resolved path is outside allowed
        with pytest.raises(HTTPException) as exc_info:
            validate_subprocess_path(link, [allowed])
        assert exc_info.value.status_code == 403
