from manim import *


class PythonBasics(Scene):
    """
    A ~3 minute walkthrough of Python fundamentals:
    title -> variables -> data types -> operators -> conditionals -> loops -> functions -> outro.

    Timing is controlled by self.wait() calls between animations.
    Total runtime is roughly 175-185 seconds at normal Manim animation speeds.
    Render with the "medium" or "final" quality preset for a smooth result;
    use "draft" first while you're checking pacing, since it's much faster.
    """

    def construct(self):
        self.title_section()
        self.variables_section()
        self.data_types_section()
        self.operators_section()
        self.conditionals_section()
        self.loops_section()
        self.functions_section()
        self.outro_section()

    # ---------- 1. Title (0:00 - 0:10) ----------
    def title_section(self):
        title = Text("Python Basics", font_size=64, color=YELLOW)
        subtitle = Text("A 3-minute crash course", font_size=28, color=GRAY_B)
        subtitle.next_to(title, DOWN, buff=0.4)

        self.play(Write(title), run_time=1.5)
        self.play(FadeIn(subtitle, shift=UP))
        self.wait(11.27)
        self.play(FadeOut(title), FadeOut(subtitle))

    # ---------- 2. Variables (0:10 - 0:35) ----------
    def variables_section(self):
        heading = self.section_heading("Variables")

        code = Code(
            code_string='name = "Alice"\nage = 30\nheight = 5.6',
            language="python",
            background="window",
        ).scale(0.9)
        code.next_to(heading, DOWN, buff=0.6)

        explain = Text(
            "Variables store data using a simple name = value syntax.",
            font_size=26,
        ).next_to(code, DOWN, buff=0.6)

        self.play(Write(code), run_time=2.5)
        self.wait(4.82)
        self.play(FadeIn(explain, shift=UP))
        self.wait(12.87)
        self.play(FadeOut(code), FadeOut(explain), FadeOut(heading))

    # ---------- 3. Data types (0:35 - 1:05) ----------
    def data_types_section(self):
        heading = self.section_heading("Data Types")

        types_table = VGroup(
            self.type_row("str", '"hello"', BLUE),
            self.type_row("int", "42", GREEN),
            self.type_row("float", "3.14", TEAL),
            self.type_row("bool", "True / False", ORANGE),
            self.type_row("list", "[1, 2, 3]", PURPLE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        types_table.next_to(heading, DOWN, buff=0.6)

        self.play(FadeIn(heading))
        for row in types_table:
            self.play(FadeIn(row, shift=RIGHT * 0.3), run_time=0.6)
            self.wait(2.58)
        self.wait(8.05)
        self.play(FadeOut(types_table), FadeOut(heading))

    def type_row(self, type_name, example, color):
        label = Text(type_name, font_size=28, color=color, weight=BOLD)
        arrow = Text("→", font_size=28)
        value = Text(example, font_size=28, font="monospace")
        row = VGroup(label, arrow, value).arrange(RIGHT, buff=0.4)
        return row

    # ---------- 4. Operators (1:05 - 1:30) ----------
    def operators_section(self):
        heading = self.section_heading("Operators")

        code = Code(
            code_string="total = 10 + 5      # addition\n"
                        "diff  = 10 - 5      # subtraction\n"
                        "prod  = 10 * 5      # multiplication\n"
                        "quot  = 10 / 5      # division\n"
                        "is_eq = 10 == 5     # comparison",
            language="python",
            background="window",
        ).scale(0.75)
        code.next_to(heading, DOWN, buff=0.6)

        self.play(FadeIn(heading))
        self.play(Write(code), run_time=3.5)
        self.wait(16.09)
        self.play(FadeOut(code), FadeOut(heading))

    # ---------- 5. Conditionals (1:30 - 2:00) ----------
    def conditionals_section(self):
        heading = self.section_heading("Conditionals")

        code = Code(
            code_string='age = 20\n\n'
                        'if age >= 18:\n'
                        '    print("You are an adult")\n'
                        'else:\n'
                        '    print("You are a minor")',
            language="python",
            background="window",
        ).scale(0.85)
        code.next_to(heading, DOWN, buff=0.6)

        output = Text('"You are an adult"', font_size=26, color=GREEN)
        output.next_to(code, DOWN, buff=0.5)

        self.play(FadeIn(heading))
        self.play(Write(code), run_time=3)
        self.wait(6.43)
        self.play(FadeIn(output, shift=UP))
        self.wait(11.27)
        self.play(FadeOut(code), FadeOut(output), FadeOut(heading))

    # ---------- 6. Loops (2:00 - 2:30) ----------
    def loops_section(self):
        heading = self.section_heading("Loops")

        code = Code(
            code_string='for i in range(3):\n    print(i)',
            language="python",
            background="window",
        ).scale(0.9)
        code.next_to(heading, DOWN, buff=0.6)

        outputs = VGroup(*[
            Text(str(i), font_size=32, font="monospace", color=YELLOW)
            for i in range(3)
        ]).arrange(RIGHT, buff=0.8)
        outputs.next_to(code, DOWN, buff=0.6)

        self.play(FadeIn(heading))
        self.play(Write(code), run_time=2)
        self.wait(3.22)
        for num in outputs:
            self.play(FadeIn(num, scale=1.3), run_time=0.6)
            self.wait(2.26)
        self.wait(8.05)
        self.play(FadeOut(code), FadeOut(outputs), FadeOut(heading))

    # ---------- 7. Functions (2:30 - 2:55) ----------
    def functions_section(self):
        heading = self.section_heading("Functions")

        code = Code(
            code_string='def greet(name):\n'
                        '    return f"Hello, {name}!"\n\n'
                        'greet("Alice")',
            language="python",
            background="window",
        ).scale(0.85)
        code.next_to(heading, DOWN, buff=0.6)

        result = Text('"Hello, Alice!"', font_size=26, color=GREEN)
        result.next_to(code, DOWN, buff=0.5)

        self.play(FadeIn(heading))
        self.play(Write(code), run_time=3)
        self.wait(6.43)
        self.play(FadeIn(result, shift=UP))
        self.wait(11.27)
        self.play(FadeOut(code), FadeOut(result), FadeOut(heading))

    # ---------- 8. Outro (2:55 - 3:05) ----------
    def outro_section(self):
        recap = VGroup(
            Text("Variables", font_size=32, color=BLUE),
            Text("Data Types", font_size=32, color=GREEN),
            Text("Operators", font_size=32, color=TEAL),
            Text("Conditionals", font_size=32, color=ORANGE),
            Text("Loops", font_size=32, color=PURPLE),
            Text("Functions", font_size=32, color=YELLOW),
        ).arrange(DOWN, buff=0.3)

        outro_title = Text("You now know Python basics!", font_size=40, color=WHITE)
        outro_title.to_edge(UP)

        self.play(Write(outro_title), run_time=1.5)
        self.play(LaggedStart(*[FadeIn(item, shift=RIGHT * 0.3) for item in recap], lag_ratio=0.3), run_time=3)
        self.wait(16.09)
        self.play(FadeOut(recap), FadeOut(outro_title))

    # ---------- helper ----------
    def section_heading(self, text):
        heading = Text(text, font_size=44, color=YELLOW, weight=BOLD)
        heading.to_edge(UP)
        return heading
