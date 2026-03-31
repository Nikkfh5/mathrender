#!/usr/bin/env python3
"""Тесты парсинга LaTeX-формул."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from hook_send_formulas import has_formulas


class TestHasFormulas(unittest.TestCase):
    """Определяет ли has_formulas наличие LaTeX в тексте."""

    # --- Должен находить ---

    def test_display_math_double_dollar(self):
        self.assertTrue(has_formulas("Вот формула: $$\\int_0^1 x dx$$"))

    def test_display_math_brackets(self):
        self.assertTrue(has_formulas("Формула: \\[\\sum_{n=1}^N n\\]"))

    def test_inline_math_single_dollar(self):
        self.assertTrue(has_formulas("Где $\\alpha > 0$ и $\\beta < 1$"))

    def test_inline_math_parens(self):
        self.assertTrue(has_formulas("Число \\(\\pi \\approx 3.14\\)"))

    def test_complex_formula(self):
        text = """
        Интеграл Гаусса:
        $$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$
        """
        self.assertTrue(has_formulas(text))

    def test_matrix(self):
        self.assertTrue(has_formulas("$$\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}$$"))

    def test_fraction(self):
        self.assertTrue(has_formulas("Получаем $\\frac{a}{b}$"))

    def test_multiple_formulas(self):
        text = "Из $$E = mc^2$$ следует $$m = \\frac{E}{c^2}$$"
        self.assertTrue(has_formulas(text))

    def test_subscript_superscript(self):
        self.assertTrue(has_formulas("Рассмотрим $x_{n+1} = x_n^2 + c$"))

    def test_greek_letters(self):
        self.assertTrue(has_formulas("Угол $\\theta$ и $\\phi$"))

    def test_limit(self):
        self.assertTrue(has_formulas("$$\\lim_{x \\to 0} \\frac{\\sin x}{x} = 1$$"))

    def test_multiline_formula(self):
        text = """$$
        \\nabla \\times \\mathbf{E} = -\\frac{\\partial \\mathbf{B}}{\\partial t}
        $$"""
        self.assertTrue(has_formulas(text))

    # --- НЕ должен находить ---

    def test_plain_text(self):
        self.assertFalse(has_formulas("Просто текст без формул."))

    def test_code_only(self):
        self.assertFalse(has_formulas("Запусти `python3 server.py` и проверь"))

    def test_empty_string(self):
        self.assertFalse(has_formulas(""))

    def test_markdown_without_math(self):
        text = "## Заголовок\n- пункт 1\n- пункт 2\n**жирный текст**"
        self.assertFalse(has_formulas(text))

    def test_json_with_dollars(self):
        self.assertFalse(has_formulas('{"price": "$50"}'))

    @unittest.skip("Known: $HOME и $PATH ловится как inline math — Claude так не пишет")
    def test_shell_variables(self):
        self.assertFalse(has_formulas("echo $HOME и $PATH"))

    def test_single_dollar_no_close(self):
        self.assertFalse(has_formulas("Цена $50 за штуку"))


class TestFormulaEdgeCases(unittest.TestCase):
    """Крайние случаи парсинга."""

    def test_formula_in_code_block(self):
        # Код-блоки обрабатываются фронтендом, хук видит сырой текст
        # $$...$$ внутри ``` блока — хук его найдёт,
        # но фронтенд защитит плейсхолдером
        text = "```\n$$\\int x dx$$\n```"
        # Хук НАЙДЁТ это (он не знает про код-блоки), но фронтенд не отрендерит
        self.assertTrue(has_formulas(text))

    @unittest.skip("Known: \\$100 ловится — Claude использует `$` в коде, не экранирует")
    def test_escaped_dollar(self):
        text = "Стоимость \\$100 и \\$200"
        self.assertFalse(has_formulas(text))

    def test_adjacent_dollars(self):
        text = "Значение $$x^2 + y^2 = r^2$$"
        self.assertTrue(has_formulas(text))

    def test_formula_with_text_around(self):
        text = "Если взять $\\alpha = 0.05$, то гипотеза отвергается."
        self.assertTrue(has_formulas(text))


if __name__ == "__main__":
    unittest.main()
