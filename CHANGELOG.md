# Changelog

All notable changes to this project will be documented in this file.

## [1.0.1] - 2025-01-15

### Changed
- Improved code formatting following PEP 8 standards
- Updated README with MIT license badge and acknowledgments
- Added demo GIF with border styling
- Enhanced project description as starting point for plugin development
- Optimized demo GIF size (50% smaller, 1.5x faster playback)

### Fixed
- Removed unused import (re module)
- Cleaned up status messages for consistency

## [1.0.0] - 2025-01-15

### Added
- Initial release of SublimeFrame
- Add ASCII frames around selected text (single-line and multi-line)
- Remove frames by placing cursor inside the frame
- Smart detection for nested frames (removes outermost frame)
- Preserves text indentation and formatting
- Support for rectangular selections
- Keyboard shortcuts for all platforms (Cmd+Shift+F on macOS, Ctrl+Shift+F on Windows/Linux)
- Command Palette integration

### Features
- Box-drawing characters for clean, professional-looking frames
- Automatic width adjustment based on content
- Status messages for user feedback