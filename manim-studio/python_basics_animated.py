from manim import *


class PythonBasicsAnimated(Scene):
    """
    A ~3 minute, animation-heavy walkthrough of Python fundamentals using
    visual metaphors (memory boxes, decision diamonds, an iteration pointer,
    a "function machine") instead of plain code-and-text slides.

    Sections: title -> variables -> data types -> operators ->
    conditionals -> loops -> functions -> outro.
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

    # ---------- helper ----------
    def section_heading(self, text):
        heading = Text(text, font_size=44, color=YELLOW, weight=BOLD)
        heading.to_edge(UP)
        return heading

    # ---------- 1. Title ----------
    def title_section(self):
        title = Text("Python Basics", font_size=64, color=YELLOW)
        subtitle = Text("visualized", font_size=28, color=GRAY_B)
        subtitle.next_to(title, DOWN, buff=0.4)

        # A few floating shapes for visual interest on the title card.
        deco = VGroup(
            Square(side_length=0.5, color=BLUE).shift(LEFT * 4 + UP * 1.5),
            Circle(radius=0.3, color=GREEN).shift(RIGHT * 4 + UP * 2),
            Triangle(color=ORANGE).scale(0.4).shift(RIGHT * 4.5 + DOWN * 1.8),
            RegularPolygon(n=6, color=PURPLE).scale(0.35).shift(LEFT * 4.5 + DOWN * 2),
        )

        self.play(LaggedStart(*[FadeIn(s, scale=0.5) for s in deco], lag_ratio=0.2), run_time=1.5)
        self.play(Write(title), run_time=1.5)
        self.play(FadeIn(subtitle, shift=UP))
        self.wait(8.97)
        self.play(FadeOut(title), FadeOut(subtitle), FadeOut(deco))

    # ---------- 2. Variables (memory boxes) ----------
    def variables_section(self):
        heading = self.section_heading("Variables")
        self.play(FadeIn(heading))

        # A "box" represents a variable in memory.
        box = Rectangle(width=2.2, height=1.4, color=BLUE, fill_color=BLUE, fill_opacity=0.15)
        box.shift(UP * 0.5)
        label = Text("age", font_size=28, color=BLUE).next_to(box, UP, buff=0.2)
        value = Text("25", font_size=40).move_to(box)

        assign_text = Text("age = 25", font_size=32, font="monospace").to_edge(DOWN, buff=1.2)

        self.play(Create(box), Write(label))
        self.play(FadeIn(value, scale=1.3))
        self.play(Write(assign_text))
        self.wait(4.89)

        # Reassigning the variable: the box's contents change, the box doesn't move.
        new_value = Text("26", font_size=40).move_to(box)
        new_assign = Text("age = 26", font_size=32, font="monospace").move_to(assign_text)

        self.play(Indicate(box, color=YELLOW))
        self.play(
            ReplacementTransform(value, new_value),
            ReplacementTransform(assign_text, new_assign),
        )
        self.wait(6.11)

        explain = Text("The box stays the same — only what's inside changes.", font_size=24, color=GRAY_B)
        explain.next_to(box, DOWN, buff=1.6)
        self.play(FadeIn(explain, shift=UP))
        self.wait(8.15)

        self.play(FadeOut(box), FadeOut(label), FadeOut(new_value), FadeOut(new_assign),
                   FadeOut(explain), FadeOut(heading))

    # ---------- 3. Data types ----------
    def data_types_section(self):
        heading = self.section_heading("Data Types")
        self.play(FadeIn(heading))

        def type_card(shape, label_text, example_text, color):
            shape.set_color(color)
            shape.set_fill(color, opacity=0.2)
            label = Text(label_text, font_size=24, color=color, weight=BOLD).next_to(shape, UP, buff=0.15)
            example = Text(example_text, font_size=20, font="monospace").next_to(shape, DOWN, buff=0.15)
            return VGroup(shape, label, example)

        cards = VGroup(
            type_card(Rectangle(width=1.4, height=1.0), "str", '"hi"', BLUE),
            type_card(Circle(radius=0.55), "int", "42", GREEN),
            type_card(Triangle(), "float", "3.14", TEAL),
            type_card(RegularPolygon(n=6), "bool", "True", ORANGE),
            type_card(RegularPolygon(n=5), "list", "[1,2,3]", PURPLE),
        ).arrange(RIGHT, buff=0.8)
        cards.move_to(ORIGIN).shift(DOWN * 0.2)

        for card in cards:
            self.play(GrowFromCenter(card[0]), FadeIn(card[1]), FadeIn(card[2]), run_time=0.7)
            self.wait(1.64)

        self.play(LaggedStart(*[Indicate(c, scale_factor=1.15) for c in cards], lag_ratio=0.2), run_time=1.8)
        self.wait(6.11)
        self.play(FadeOut(cards), FadeOut(heading))

    # ---------- 4. Operators (numbers combining) ----------
    def operators_section(self):
        heading = self.section_heading("Operators")
        self.play(FadeIn(heading))

        def op_demo(a_val, b_val, symbol, result_val, color):
            a = Circle(radius=0.6, color=color, fill_color=color, fill_opacity=0.25)
            a_text = Text(str(a_val), font_size=32).move_to(a)
            b = Circle(radius=0.6, color=color, fill_color=color, fill_opacity=0.25)
            b_text = Text(str(b_val), font_size=32).move_to(b)
            op = Text(symbol, font_size=40)
            group_a = VGroup(a, a_text)
            group_b = VGroup(b, b_text)
            row = VGroup(group_a, op, group_b).arrange(RIGHT, buff=0.5)
            row.move_to(UP * 0.3)

            result_circle = Circle(radius=0.7, color=YELLOW, fill_color=YELLOW, fill_opacity=0.3)
            result_text = Text(str(result_val), font_size=36)
            result_group = VGroup(result_circle, result_text).move_to(DOWN * 1.6)

            return row, result_group

        row, result_group = op_demo(10, 5, "+", 15, BLUE)
        self.play(FadeIn(row, shift=UP))
        self.wait(2.44)
        arrow = Arrow(row.get_bottom(), result_group.get_top(), buff=0.15, color=GRAY_B)
        self.play(Create(arrow))
        self.play(
            ReplacementTransform(row.copy(), result_group),
        )
        self.wait(6.11)
        self.play(FadeOut(row), FadeOut(arrow), FadeOut(result_group))

        row2, result_group2 = op_demo(10, 3, "*", 30, GREEN)
        self.play(FadeIn(row2, shift=UP))
        self.wait(2.44)
        arrow2 = Arrow(row2.get_bottom(), result_group2.get_top(), buff=0.15, color=GRAY_B)
        self.play(Create(arrow2))
        self.play(ReplacementTransform(row2.copy(), result_group2))
        self.wait(7.34)
        self.play(FadeOut(row2), FadeOut(arrow2), FadeOut(result_group2), FadeOut(heading))

    # ---------- 5. Conditionals (decision diamond) ----------
    def conditionals_section(self):
        heading = self.section_heading("Conditionals")
        self.play(FadeIn(heading))

        diamond = RegularPolygon(n=4, color=ORANGE, fill_color=ORANGE, fill_opacity=0.2)
        diamond.stretch(1.6, 0).stretch(0.9, 1)
        diamond.move_to(UP * 1.2)
        condition_text = Text("age >= 18 ?", font_size=26).move_to(diamond)

        true_box = RoundedRectangle(width=2.6, height=1.0, corner_radius=0.2,
                                     color=GREEN, fill_color=GREEN, fill_opacity=0.2)
        true_box.shift(LEFT * 2.8 + DOWN * 1.3)
        true_label = Text('"Adult"', font_size=26, color=GREEN).move_to(true_box)

        false_box = RoundedRectangle(width=2.6, height=1.0, corner_radius=0.2,
                                      color=RED, fill_color=RED, fill_opacity=0.2)
        false_box.shift(RIGHT * 2.8 + DOWN * 1.3)
        false_label = Text('"Minor"', font_size=26, color=RED).move_to(false_box)

        arrow_true = Arrow(diamond.get_bottom(), true_box.get_top(), color=GREEN, buff=0.1)
        arrow_false = Arrow(diamond.get_bottom(), false_box.get_top(), color=RED, buff=0.1)
        true_word = Text("True", font_size=20, color=GREEN).next_to(arrow_true, LEFT, buff=0.1)
        false_word = Text("False", font_size=20, color=RED).next_to(arrow_false, RIGHT, buff=0.1)

        self.play(Create(diamond), Write(condition_text))
        self.wait(3.26)
        self.play(
            Create(arrow_true), Create(arrow_false),
            FadeIn(true_word), FadeIn(false_word),
        )
        self.play(Create(true_box), Write(true_label), Create(false_box), Write(false_label))
        self.wait(4.08)

        # Show age=20 taking the "True" path.
        traveler = Circle(radius=0.15, color=YELLOW, fill_color=YELLOW, fill_opacity=1)
        traveler.move_to(diamond)
        self.play(FadeIn(traveler, scale=0.5))
        self.play(MoveAlongPath(traveler, arrow_true), run_time=1)
        self.play(Circumscribe(true_box, color=YELLOW))
        self.wait(8.15)

        self.play(FadeOut(VGroup(diamond, condition_text, arrow_true, arrow_false,
                                  true_word, false_word, true_box, true_label,
                                  false_box, false_label, traveler, heading)))

    # ---------- 6. Loops (iteration pointer over a list) ----------
    def loops_section(self):
        heading = self.section_heading("Loops")
        self.play(FadeIn(heading))

        values = [4, 8, 15, 16, 23]
        boxes = VGroup(*[
            Square(side_length=1.0, color=BLUE, fill_color=BLUE, fill_opacity=0.15)
            for _ in values
        ]).arrange(RIGHT, buff=0.3)
        numbers = VGroup(*[
            Text(str(v), font_size=30).move_to(box)
            for v, box in zip(values, boxes)
        ])
        boxes.move_to(UP * 0.3)
        for n, box in zip(numbers, boxes):
            n.move_to(box)

        pointer = Triangle(color=YELLOW, fill_color=YELLOW, fill_opacity=1).scale(0.25)
        pointer.rotate(PI)
        pointer.next_to(boxes[0], UP, buff=0.15)

        counter_label = Text("sum = 0", font_size=30, font="monospace").to_edge(DOWN, buff=1.3)

        self.play(Create(boxes), Write(numbers))
        self.play(FadeIn(pointer))
        self.play(Write(counter_label))
        self.wait(2.04)

        running_total = 0
        for i, v in enumerate(values):
            self.play(box_indicate := Indicate(boxes[i], color=YELLOW), run_time=0.5)
            running_total += v
            new_counter = Text(f"sum = {running_total}", font_size=30, font="monospace")
            new_counter.move_to(counter_label)
            self.play(ReplacementTransform(counter_label, new_counter), run_time=0.5)
            counter_label = new_counter
            if i < len(values) - 1:
                self.play(pointer.animate.next_to(boxes[i + 1], UP, buff=0.15), run_time=0.5)
            self.wait(1.22)

        self.wait(4.89)
        self.play(FadeOut(boxes), FadeOut(numbers), FadeOut(pointer),
                   FadeOut(counter_label), FadeOut(heading))

    # ---------- 7. Functions (input -> machine -> output) ----------
    def functions_section(self):
        heading = self.section_heading("Functions")
        self.play(FadeIn(heading))

        machine = RoundedRectangle(width=3.2, height=1.8, corner_radius=0.25,
                                    color=PURPLE, fill_color=PURPLE, fill_opacity=0.2)
        machine_label = Text("greet(name)", font_size=26, color=PURPLE).move_to(machine)

        input_box = Rectangle(width=1.8, height=0.9, color=BLUE, fill_color=BLUE, fill_opacity=0.2)
        input_box.next_to(machine, LEFT, buff=1.4)
        input_text = Text('"Alice"', font_size=24, font="monospace").move_to(input_box)

        output_box = Rectangle(width=2.6, height=0.9, color=GREEN, fill_color=GREEN, fill_opacity=0.2)
        output_box.next_to(machine, RIGHT, buff=1.4)
        output_text = Text('"Hello, Alice!"', font_size=22, font="monospace").move_to(output_box)

        arrow_in = Arrow(input_box.get_right(), machine.get_left(), buff=0.1)
        arrow_out = Arrow(machine.get_right(), output_box.get_left(), buff=0.1)

        self.play(Create(machine), Write(machine_label))
        self.play(Create(input_box), Write(input_text))
        self.wait(2.44)
        self.play(Create(arrow_in))
        moving_input = input_text.copy()
        self.play(moving_input.animate.move_to(machine.get_center()), run_time=0.8)
        self.play(FadeOut(moving_input), Indicate(machine, color=YELLOW))
        self.play(Create(arrow_out))
        self.play(Create(output_box), Write(output_text))
        self.wait(8.97)

        self.play(FadeOut(VGroup(machine, machine_label, input_box, input_text,
                                  output_box, output_text, arrow_in, arrow_out, heading)))

    # ---------- 8. Outro ----------
    def outro_section(self):
        outro_title = Text("You now know Python basics!", font_size=40, color=WHITE)
        outro_title.to_edge(UP)

        recap_items = ["Variables", "Data Types", "Operators", "Conditionals", "Loops", "Functions"]
        colors = [BLUE, GREEN, TEAL, ORANGE, YELLOW, PURPLE]
        recap = VGroup(*[
            VGroup(
                Square(side_length=0.4, color=c, fill_color=c, fill_opacity=0.4),
                Text(name, font_size=28, color=c),
            ).arrange(RIGHT, buff=0.3)
            for name, c in zip(recap_items, colors)
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.3)

        self.play(Write(outro_title), run_time=1.5)
        self.play(LaggedStart(*[FadeIn(item, shift=RIGHT * 0.3) for item in recap], lag_ratio=0.3), run_time=3)
        self.wait(10.19)
        self.play(FadeOut(recap), FadeOut(outro_title))
