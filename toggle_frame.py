import sublime
import sublime_plugin


class ToggleFrameCommand(sublime_plugin.TextCommand):
    """Command to add or remove ASCII frames around selected text."""

    def run(self, edit):
        for region in self.view.sel():
            if region.empty():
                # No selection - check if cursor is inside a frame
                row, col = self.view.rowcol(region.begin())
                line = self.get_line_text(row)

                if self.is_inside_frame(region.begin()):
                    sublime.status_message("Removing frame... (row {}, col {})".format(row, col))
                    self.remove_frame(edit, region.begin())
                else:
                    sublime.status_message("Frame not found. Line: '{}'".format(line[:50]))
            else:
                # Has selection - add frame
                self.add_frame(edit, region)

    def is_inside_frame(self, position):
        """Check if position is inside a frame."""
        row, col = self.view.rowcol(position)
        line = self.get_line_text(row)

        if not line:
            return False

        # Find │ character to the left of cursor (including cursor position)
        left_border_pos = -1
        for i in range(min(col, len(line) - 1), -1, -1):
            if line[i] == '│':
                left_border_pos = i
                break

        # Find │ character to the right of cursor
        right_border_pos = -1
        for i in range(col, len(line)):
            if line[i] == '│':
                right_border_pos = i
                break

        # If there are borders on both sides - we're inside a frame
        # left_border_pos should be to the left or at cursor position
        # right_border_pos should be to the right of cursor
        return 0 <= left_border_pos <= col < right_border_pos

    def remove_frame(self, edit, position):
        """Remove frame around position."""
        row, col = self.view.rowcol(position)
        current_line = self.get_line_text(row)

        # Determine left and right borders on current line
        left_border_col = -1
        right_border_col = -1

        # Find left border (nearest │ to the left of cursor)
        for i in range(min(col, len(current_line) - 1), -1, -1):
            if current_line[i] == '│':
                left_border_col = i
                break

        # Find right border (nearest │ to the right of cursor)
        for i in range(col, len(current_line)):
            if current_line[i] == '│':
                right_border_col = i
                break

        if left_border_col == -1 or right_border_col == -1:
            sublime.status_message("Cursor is not inside a frame")
            return

        # Find the OUTERMOST top border, expanding search
        top_row = None
        final_left = left_border_col
        final_right = right_border_col

        for r in range(row - 1, max(row - 100, -1), -1):
            line = self.get_line_text(r)

            # Check if this line has top border for current borders
            if len(line) > final_left and len(line) > final_right:
                if line[final_left] == '┌' and line[final_right] == '┐':
                    # Found top border, remember it
                    top_row = r

                    # Try to find even more outer frame
                    # Look for │ to the left of current left border
                    new_left = -1
                    for i in range(final_left - 1, -1, -1):
                        if i < len(line) and line[i] == '│':
                            new_left = i
                            break

                    # Look for │ to the right of current right border
                    new_right = -1
                    for i in range(final_right + 1, len(line)):
                        if line[i] == '│':
                            new_right = i
                            break

                    # If found more outer borders, expand search
                    if new_left >= 0 and new_right > new_left:
                        final_left = new_left
                        final_right = new_right
                        # Continue looking for even more outer frames
                        continue
                    else:
                        # No more outer frames
                        break

            # Check that vertical borders continue
            if len(line) <= final_left or line[final_left] != '│':
                break
            if len(line) <= final_right or line[final_right] != '│':
                break

        # Find the OUTERMOST bottom border for found borders
        bottom_row = None
        last_row, _ = self.view.rowcol(self.view.size())

        for r in range(row + 1, min(row + 100, last_row + 1)):
            line = self.get_line_text(r)

            # Check if this line has bottom border
            if len(line) > final_left and len(line) > final_right:
                if line[final_left] == '└' and line[final_right] == '┘':
                    bottom_row = r
                    break

            # Check that vertical borders continue
            if len(line) <= final_left or line[final_left] != '│':
                break
            if len(line) <= final_right or line[final_right] != '│':
                break

        # Update borders to found ones
        left_border_col = final_left
        right_border_col = final_right

        if top_row is None or bottom_row is None:
            sublime.status_message("Could not find frame borders (top={}, bottom={})".format(top_row, bottom_row))
            return

        # Extract content from frame
        result_lines = []

        # Process top frame line
        top_line = self.get_line_text(top_row)
        before_top = top_line[:left_border_col] if left_border_col > 0 else ""
        after_top = top_line[right_border_col + 1:] if right_border_col + 1 < len(top_line) else ""

        # If there's text before or after top border, save it
        if before_top.strip() or after_top.strip():
            combined = before_top.rstrip()
            if after_top.strip():
                combined += " " + after_top.lstrip() if combined else after_top.lstrip()
            if combined.strip():
                result_lines.append(combined)

        # Extract content between top and bottom borders
        for r in range(top_row + 1, bottom_row):
            line = self.get_line_text(r)
            # Extract text between specific positions │ ... │
            if len(line) > right_border_col and line[left_border_col] == '│' and line[right_border_col] == '│':
                # Extract content between left and right border
                content_start = left_border_col + 1
                content_end = right_border_col

                # Skip spaces after left border
                if content_start < len(line) and line[content_start] == ' ':
                    content_start += 1

                # Skip space before right border
                if content_end > 0 and line[content_end - 1] == ' ':
                    content_end -= 1

                if content_start <= content_end:
                    content = line[content_start:content_end]
                    result_lines.append(' ' * left_border_col + content.rstrip())
                else:
                    result_lines.append("")

        # Process bottom frame line
        bottom_line = self.get_line_text(bottom_row)
        before_bottom = bottom_line[:left_border_col] if left_border_col > 0 else ""
        after_bottom = bottom_line[right_border_col + 1:] if right_border_col + 1 < len(bottom_line) else ""

        # If there's text before or after bottom border, save it
        if before_bottom.strip() or after_bottom.strip():
            combined = before_bottom.rstrip()
            if after_bottom.strip():
                combined += " " + after_bottom.lstrip() if combined else after_bottom.lstrip()
            if combined.strip():
                result_lines.append(combined)

        # Form result
        result = '\n'.join(result_lines) if result_lines else ""

        # Replace frame with content
        start_point = self.view.text_point(top_row, 0)
        end_point = self.view.line(self.view.text_point(bottom_row, 0)).end()
        replace_region = sublime.Region(start_point, end_point)

        self.view.replace(edit, replace_region, result)
        sublime.status_message("Frame removed")

    def add_frame(self, edit, region):
        """Add frame around selection."""
        begin_row, begin_col = self.view.rowcol(region.begin())
        end_row, end_col = self.view.rowcol(region.end())

        selected_text = self.view.substr(region)

        if begin_row == end_row:
            # Single line selection
            self.add_single_line_frame(edit, region, selected_text, begin_col)
        else:
            # Multiline selection
            self.add_multiline_frame(edit, region, selected_text, begin_col)

    def add_single_line_frame(self, edit, region, text, indent_col):
        """Add frame for single line text."""
        width = len(text)
        top_border = "┌" + "─" * (width + 2) + "┐"
        middle_line = "│ " + text + " │"
        bottom_border = "└" + "─" * (width + 2) + "┘"

        indent = " " * indent_col
        framed_text = indent + top_border + "\n" + indent + middle_line + "\n" + indent + bottom_border

        self.view.replace(edit, region, framed_text)
        sublime.status_message("Frame added")

    def add_multiline_frame(self, edit, region, text, indent_col):
        """Add frame for multiline text."""
        lines = text.split('\n')
        max_width = max(len(line) for line in lines) if lines else 0

        top_border = "┌" + "─" * (max_width + 2) + "┐"
        bottom_border = "└" + "─" * (max_width + 2) + "┘"

        framed_lines = [top_border]
        for line in lines:
            padded_line = line.ljust(max_width)
            framed_lines.append("│ " + padded_line + " │")
        framed_lines.append(bottom_border)

        indent = " " * indent_col
        framed_text = '\n'.join(indent + line for line in framed_lines)

        self.view.replace(edit, region, framed_text)
        sublime.status_message("Frame added")

    def get_line_text(self, row):
        """Get text of line by row number."""
        # Get total number of lines via last point in file
        last_row, _ = self.view.rowcol(self.view.size())

        if row < 0 or row > last_row:
            return ""
        line_region = self.view.line(self.view.text_point(row, 0))
        return self.view.substr(line_region)