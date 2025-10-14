import sublime
import sublime_plugin
import re


class ToggleFrameCommand(sublime_plugin.TextCommand):
    """Команда для добавления/удаления ASCII рамки вокруг выделенного текста"""

    def run(self, edit):
        for region in self.view.sel():
            if region.empty():
                # Курсор без выделения - проверяем, находимся ли внутри рамки
                row, col = self.view.rowcol(region.begin())
                line = self.get_line_text(row)

                if self.is_inside_frame(region.begin()):
                    sublime.status_message("Удаление рамки... (строка {}, колонка {})".format(row, col))
                    self.remove_frame(edit, region.begin())
                else:
                    sublime.status_message("Рамка не найдена. Строка: '{}'".format(line[:50]))
            else:
                # Есть выделение - добавляем рамку
                self.add_frame(edit, region)

    def is_inside_frame(self, position):
        """Проверяет, находится ли позиция внутри рамки"""
        row, col = self.view.rowcol(position)
        line = self.get_line_text(row)

        if not line:
            return False

        # Ищем символ │ слева от курсора (включая позицию курсора)
        left_border_pos = -1
        for i in range(min(col, len(line) - 1), -1, -1):
            if line[i] == '│':
                left_border_pos = i
                break

        # Ищем символ │ справа от курсора
        right_border_pos = -1
        for i in range(col, len(line)):
            if line[i] == '│':
                right_border_pos = i
                break

        # Если есть границы с обеих сторон - мы внутри рамки
        # left_border_pos должен быть левее курсора или на той же позиции
        # right_border_pos должен быть правее курсора
        return 0 <= left_border_pos <= col < right_border_pos

    def remove_frame(self, edit, position):
        """Удаляет рамку вокруг позиции"""
        row, col = self.view.rowcol(position)
        current_line = self.get_line_text(row)

        # Определяем левую и правую границы на текущей строке
        left_border_col = -1
        right_border_col = -1

        # Ищем левую границу (ближайший │ слева от курсора)
        for i in range(min(col, len(current_line) - 1), -1, -1):
            if current_line[i] == '│':
                left_border_col = i
                break

        # Ищем правую границу (ближайший │ справа от курсора)
        for i in range(col, len(current_line)):
            if current_line[i] == '│':
                right_border_col = i
                break

        if left_border_col == -1 or right_border_col == -1:
            sublime.status_message("Курсор не находится внутри рамки")
            return

        # Ищем САМУЮ ВНЕШНЮЮ верхнюю границу, расширяя поиск
        top_row = None
        final_left = left_border_col
        final_right = right_border_col

        for r in range(row - 1, max(row - 100, -1), -1):
            line = self.get_line_text(r)

            # Проверяем, есть ли на этой строке верхняя граница для текущих границ
            if len(line) > final_left and len(line) > final_right:
                if line[final_left] == '┌' and line[final_right] == '┐':
                    # Нашли верхнюю границу, запоминаем её
                    top_row = r

                    # Пробуем найти еще более внешнюю рамку
                    # Ищем │ слева от текущей левой границы
                    new_left = -1
                    for i in range(final_left - 1, -1, -1):
                        if i < len(line) and line[i] == '│':
                            new_left = i
                            break

                    # Ищем │ справа от текущей правой границы
                    new_right = -1
                    for i in range(final_right + 1, len(line)):
                        if line[i] == '│':
                            new_right = i
                            break

                    # Если нашли более внешние границы, расширяем поиск
                    if new_left >= 0 and new_right > new_left:
                        final_left = new_left
                        final_right = new_right
                        # Продолжаем искать еще более внешние рамки
                        continue
                    else:
                        # Больше нет внешних рамок
                        break

            # Проверяем, что вертикальные границы продолжаются
            if len(line) <= final_left or line[final_left] != '│':
                break
            if len(line) <= final_right or line[final_right] != '│':
                break

        # Ищем САМУЮ ВНЕШНЮЮ нижнюю границу для найденных границ
        bottom_row = None
        last_row, _ = self.view.rowcol(self.view.size())

        for r in range(row + 1, min(row + 100, last_row + 1)):
            line = self.get_line_text(r)

            # Проверяем, есть ли на этой строке нижняя граница
            if len(line) > final_left and len(line) > final_right:
                if line[final_left] == '└' and line[final_right] == '┘':
                    bottom_row = r
                    break

            # Проверяем, что вертикальные границы продолжаются
            if len(line) <= final_left or line[final_left] != '│':
                break
            if len(line) <= final_right or line[final_right] != '│':
                break

        # Обновляем границы на найденные
        left_border_col = final_left
        right_border_col = final_right

        if top_row is None or bottom_row is None:
            sublime.status_message("Не удалось найти границы рамки (top={}, bottom={})".format(top_row, bottom_row))
            return

        # Извлекаем содержимое из рамки
        result_lines = []

        # Обрабатываем верхнюю строку рамки
        top_line = self.get_line_text(top_row)
        before_top = top_line[:left_border_col] if left_border_col > 0 else ""
        after_top = top_line[right_border_col + 1:] if right_border_col + 1 < len(top_line) else ""

        # Если есть текст до или после верхней границы, сохраняем его
        if before_top.strip() or after_top.strip():
            combined = before_top.rstrip()
            if after_top.strip():
                combined += " " + after_top.lstrip() if combined else after_top.lstrip()
            if combined.strip():
                result_lines.append(combined)

        # Извлекаем содержимое между верхней и нижней границами
        for r in range(top_row + 1, bottom_row):
            line = self.get_line_text(r)
            # Извлекаем текст между конкретными позициями │ ... │
            if len(line) > right_border_col and line[left_border_col] == '│' and line[right_border_col] == '│':
                # Извлекаем содержимое между левой и правой границей
                content_start = left_border_col + 1
                content_end = right_border_col

                # Пропускаем пробелы после левой границы
                if content_start < len(line) and line[content_start] == ' ':
                    content_start += 1

                # Пропускаем пробел перед правой границей
                if content_end > 0 and line[content_end - 1] == ' ':
                    content_end -= 1

                if content_start <= content_end:
                    content = line[content_start:content_end]
                    result_lines.append(' ' * left_border_col + content.rstrip())
                else:
                    result_lines.append("")

        # Обрабатываем нижнюю строку рамки
        bottom_line = self.get_line_text(bottom_row)
        before_bottom = bottom_line[:left_border_col] if left_border_col > 0 else ""
        after_bottom = bottom_line[right_border_col + 1:] if right_border_col + 1 < len(bottom_line) else ""

        # Если есть текст до или после нижней границы, сохраняем его
        if before_bottom.strip() or after_bottom.strip():
            combined = before_bottom.rstrip()
            if after_bottom.strip():
                combined += " " + after_bottom.lstrip() if combined else after_bottom.lstrip()
            if combined.strip():
                result_lines.append(combined)

        # Формируем результат
        result = '\n'.join(result_lines) if result_lines else ""

        # Заменяем рамку на содержимое
        start_point = self.view.text_point(top_row, 0)
        end_point = self.view.line(self.view.text_point(bottom_row, 0)).end()
        replace_region = sublime.Region(start_point, end_point)

        self.view.replace(edit, replace_region, result)
        sublime.status_message("Рамка удалена")

    def add_frame(self, edit, region):
        """Добавляет рамку вокруг выделения"""
        begin_row, begin_col = self.view.rowcol(region.begin())
        end_row, end_col = self.view.rowcol(region.end())

        selected_text = self.view.substr(region)

        if begin_row == end_row:
            # Однострочное выделение
            self.add_single_line_frame(edit, region, selected_text, begin_col)
        else:
            # Многострочное выделение
            self.add_multiline_frame(edit, region, selected_text, begin_col)

    def add_single_line_frame(self, edit, region, text, indent_col):
        """Добавляет рамку для однострочного текста"""
        width = len(text)
        top_border = "┌" + "─" * (width + 2) + "┐"
        middle_line = "│ " + text + " │"
        bottom_border = "└" + "─" * (width + 2) + "┘"

        indent = " " * indent_col
        framed_text = indent + top_border + "\n" + indent + middle_line + "\n" + indent + bottom_border

        self.view.replace(edit, region, framed_text)
        sublime.status_message("Рамка добавлена")

    def add_multiline_frame(self, edit, region, text, indent_col):
        """Добавляет рамку для многострочного текста"""
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
        sublime.status_message("Рамка добавлена")

    def get_line_text(self, row):
        """Получает текст строки по номеру"""
        # Получаем общее количество строк через последнюю точку файла
        last_row, _ = self.view.rowcol(self.view.size())

        if row < 0 or row > last_row:
            return ""
        line_region = self.view.line(self.view.text_point(row, 0))
        return self.view.substr(line_region)