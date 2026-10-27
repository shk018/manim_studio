from manim import *


class QuickTest(Scene):
    """A short, simple scene just for testing narration + music.
    Should render in well under a minute at draft quality."""

    def construct(self):
        self.intro_section()
        self.shapes_section()
        self.outro_section()

    # ---------- 1. Intro ----------
    def intro_section(self):
        title = Text("Testing 1, 2, 3", font_size=54, color=YELLOW)
        self.play(Write(title))
        self.wait(2)
        self.play(FadeOut(title))

    # ---------- 2. Shapes ----------
    def shapes_section(self):
        circle = Circle(color=BLUE, fill_color=BLUE, fill_opacity=0.3)
        square = Square(color=GREEN, fill_color=GREEN, fill_opacity=0.3)
        triangle = Triangle(color=ORANGE, fill_color=ORANGE, fill_opacity=0.3)

        shapes = VGroup(circle, square, triangle).arrange(RIGHT, buff=1.2)

        self.play(Create(circle))
        self.wait(0.5)
        self.play(Create(square))
        self.wait(0.5)
        self.play(Create(triangle))
        self.wait(1)
        self.play(shapes.animate.arrange(RIGHT, buff=0.5).scale(1.3))
        self.wait(2)
        self.play(FadeOut(shapes))

    # ---------- 3. Outro ----------
    def outro_section(self):
        done = Text("All done!", font_size=48, color=GREEN)
        self.play(FadeIn(done, scale=1.3))
        self.wait(2)
        self.play(FadeOut(done))
