"""Test hash-based file matching for renamed files."""
import os
import tempfile
from pathlib import Path

import pytest

from isisdl.backend.database_helper import DatabaseHelper


def test_find_file_by_checksum_returns_none_when_not_found():
    """Test that find_file_by_checksum returns None when no file is found."""
    db = DatabaseHelper()
    result = db.find_file_by_checksum('nonexistent_checksum', 999)
    assert result is None


def test_find_file_by_checksum_basic_functionality():
    """Test the basic functionality of find_file_by_checksum method.
    
    This test verifies that the new find_file_by_checksum method can be called
    without errors, which is essential for hash-based file matching.
    """
    db = DatabaseHelper()
    
    # Test with non-existent checksum
    result = db.find_file_by_checksum('test_checksum_123', 999)
    assert result is None
    
    # Test with different course IDs
    result = db.find_file_by_checksum('another_checksum', 123)
    assert result is None

