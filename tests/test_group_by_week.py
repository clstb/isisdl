"""Tests for the group by week feature."""
import os
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from isisdl.backend.request_helper import PreMediaContainer, Course
from isisdl.utils import MediaType, config, path, sanitize_name


@pytest.fixture
def mock_course() -> Course:
    """Create a mock course for testing."""
    course = MagicMock(spec=Course)
    course.course_id = "12345"
    course.name = "Test Course"
    course.path = lambda *args: path(sanitize_name("Test Course", True), *args)
    return course


@pytest.fixture(autouse=True)
def setup_config():
    """Setup and teardown for config state."""
    original_make_subdirs = config.make_subdirs
    yield
    config.make_subdirs = original_make_subdirs


class TestPreMediaContainerWeekFeature:
    """Tests for PreMediaContainer with week_name parameter."""

    def test_week_name_with_subdirs_enabled(self, mock_course: Course) -> None:
        """Test that week_name creates correct path when subdirs are enabled."""
        config.make_subdirs = True
        
        container = PreMediaContainer(
            url="https://example.com/file.pdf",
            course=mock_course,
            media_type=MediaType.document,
            name="test_file.pdf",
            week_name="Week 1 - Introduction"
        )
        
        # Week name should be sanitized and used as parent path
        expected_path = path(sanitize_name("Test Course", True), sanitize_name("Week 1 - Introduction", True))
        assert container.parent_path == expected_path
        assert container.parent_path.exists()

    def test_week_name_with_subdirs_disabled(self, mock_course: Course) -> None:
        """Test that week_name is ignored when subdirs are disabled."""
        config.make_subdirs = False
        
        container = PreMediaContainer(
            url="https://example.com/file.pdf",
            course=mock_course,
            media_type=MediaType.document,
            name="test_file.pdf",
            week_name="Week 1 - Introduction"
        )
        
        # With subdirs disabled, files should go directly in course root
        expected_path = path(sanitize_name("Test Course", True))
        assert container.parent_path == expected_path

    def test_no_week_name_uses_media_type_dir(self, mock_course: Course) -> None:
        """Test that without week_name, media type directory is used."""
        config.make_subdirs = True
        
        container = PreMediaContainer(
            url="https://example.com/file.pdf",
            course=mock_course,
            media_type=MediaType.document,
            name="test_file.pdf",
            week_name=None
        )
        
        # Should use media type directory when no week is provided
        expected_path = path(sanitize_name("Test Course", True), sanitize_name(MediaType.document.dir_name, True))
        assert container.parent_path == expected_path

    def test_empty_week_name_uses_media_type_dir(self, mock_course: Course) -> None:
        """Test that empty week_name falls back to media type directory."""
        config.make_subdirs = True
        
        container = PreMediaContainer(
            url="https://example.com/file.pdf",
            course=mock_course,
            media_type=MediaType.document,
            name="test_file.pdf",
            week_name=""
        )
        
        # Empty string should be treated as no week
        expected_path = path(sanitize_name("Test Course", True), sanitize_name(MediaType.document.dir_name, True))
        assert container.parent_path == expected_path

    def test_week_name_with_video_media_type(self, mock_course: Course) -> None:
        """Test week grouping with video media type."""
        config.make_subdirs = True
        
        container = PreMediaContainer(
            url="https://example.com/video.mp4",
            course=mock_course,
            media_type=MediaType.video,
            name="lecture.mp4",
            week_name="Week 2 - Data Structures"
        )
        
        expected_path = path(sanitize_name("Test Course", True), sanitize_name("Week 2 - Data Structures", True))
        assert container.parent_path == expected_path

    def test_week_name_with_extern_media_type(self, mock_course: Course) -> None:
        """Test week grouping with external links."""
        config.make_subdirs = True
        
        container = PreMediaContainer(
            url="https://external-site.com/resource",
            course=mock_course,
            media_type=MediaType.extern,
            week_name="Week 3 - Algorithms"
        )
        
        expected_path = path(sanitize_name("Test Course", True), sanitize_name("Week 3 - Algorithms", True))
        assert container.parent_path == expected_path

    def test_week_name_sanitization(self, mock_course: Course) -> None:
        """Test that week names with special characters are sanitized."""
        config.make_subdirs = True
        
        container = PreMediaContainer(
            url="https://example.com/file.pdf",
            course=mock_course,
            media_type=MediaType.document,
            name="test.pdf",
            week_name="Week 1: Introduction / Overview"
        )
        
        # Week name should be sanitized (special chars removed/replaced)
        expected_path = path(sanitize_name("Test Course", True), sanitize_name("Week 1: Introduction / Overview", True))
        assert container.parent_path == expected_path
        # Verify the path was created
        assert container.parent_path.exists()

    def test_week_name_with_relative_location(self, mock_course: Course) -> None:
        """Test that week_name takes precedence over relative_location."""
        config.make_subdirs = True
        
        container = PreMediaContainer(
            url="https://example.com/file.pdf",
            course=mock_course,
            media_type=MediaType.document,
            name="test.pdf",
            relative_location="custom/path",
            week_name="Week 4 - Testing"
        )
        
        # Week name should take precedence
        expected_path = path(sanitize_name("Test Course", True), sanitize_name("Week 4 - Testing", True))
        assert container.parent_path == expected_path

    def test_multiple_files_same_week(self, mock_course: Course) -> None:
        """Test that multiple files in the same week share parent path."""
        config.make_subdirs = True
        week_name = "Week 5 - Final Project"
        
        container1 = PreMediaContainer(
            url="https://example.com/lecture.pdf",
            course=mock_course,
            media_type=MediaType.document,
            name="lecture.pdf",
            week_name=week_name
        )
        
        container2 = PreMediaContainer(
            url="https://example.com/video.mp4",
            course=mock_course,
            media_type=MediaType.video,
            name="lecture.mp4",
            week_name=week_name
        )
        
        # Both should have the same parent path
        assert container1.parent_path == container2.parent_path
        expected_path = path(sanitize_name("Test Course", True), sanitize_name(week_name, True))
        assert container1.parent_path == expected_path

    def test_different_weeks_different_paths(self, mock_course: Course) -> None:
        """Test that files from different weeks have different parent paths."""
        config.make_subdirs = True
        
        container1 = PreMediaContainer(
            url="https://example.com/file1.pdf",
            course=mock_course,
            media_type=MediaType.document,
            week_name="Week 1"
        )
        
        container2 = PreMediaContainer(
            url="https://example.com/file2.pdf",
            course=mock_course,
            media_type=MediaType.document,
            week_name="Week 2"
        )
        
        # Different weeks should have different parent paths
        assert container1.parent_path != container2.parent_path

    def test_parent_path_directory_creation(self, mock_course: Course) -> None:
        """Test that parent_path directories are created automatically."""
        config.make_subdirs = True
        week_name = "Week 6 - New Topic"
        
        container = PreMediaContainer(
            url="https://example.com/file.pdf",
            course=mock_course,
            media_type=MediaType.document,
            week_name=week_name
        )
        
        # The directory should exist after container creation
        assert container.parent_path.exists()
        assert container.parent_path.is_dir()
