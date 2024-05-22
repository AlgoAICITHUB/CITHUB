from manim import *

class CITHUBIntro(Scene):
    def construct(self):
        self.camera.background_color = "#ece6e2"  # 設定背景顏色

        # 開場標題
        title = Text("Welcome to CITHUB", font_size=56, color=BLUE_B)
        self.play(Write(title))
        self.wait(1)
        self.play(FadeOut(title, shift=DOWN))
        
        # 介紹CITHUB
        description = Text(
            "CITHUB is a vibrant academic community where dreams and knowledge converge.\n "
            "In this welcoming space, you are invited to explore and discuss a wide array\n"
            "of subjects including mathematics, coding, science, and more. Engage in stimulating\n",

            font_size=25,  color = BLACK# 增加字體大小

        )
        self.play(Write(description), run_time=3)
        self.wait(2)
        self.play(FadeOut(description, shift=DOWN))
        descriptions = Text(
            "conversations and exchange ideas within a structured framework designed to foster\n"
            "intellectual growth and creativity. Dive into the world of CITHUB, where rules pave\n "
            "the way to limitless discovery!",
            font_size=25, color = BLACK,
            line_spacing=1.5
        )
        self.play(Write(descriptions), run_time=3)
        self.wait(2)
        self.play(FadeOut(descriptions, shift=DOWN))
        # 主要特色
        features = VGroup(
            Text("Markdown&Latex", color=BLUE_D).scale(0.9),
            Text("Various Topics", color=GREEN_B).scale(0.9),
            Text("Free to talk", color=YELLOW_D).scale(0.9)
        ).arrange(DOWN, buff=1)
        
        self.play(LaggedStart(*[FadeIn(feature, shift=UP) for feature in features], lag_ratio=0.5))
        self.wait(2)
        self.play(FadeOut(features, shift=DOWN))
        
        # 成員名單
        member_title = Text("Committee members:", font_size=36, color=RED_A)
        members = Text(
            "General call: TudoHuang\n"
            "Debugger&In_out: A1u\n"
            "Decorator&IN_out: Chenya\n"
            "Technical Support: ChatGPT\n"
            "Platform Provider: CKCSC,IZCC\n"
            "Cooperation Platform Provider: Github\n",
            font_size=25,color=LOGO_BLUE  # 增加名單字體大小
        )
        member_group = VGroup(member_title, members).arrange(DOWN, center=True, aligned_edge=LEFT)
        self.play(Write(member_group, run_times=6))
        self.wait(2)
        self.play(FadeOut(member_group, shift=DOWN))
        
        # 結束畫面
        ending = Text("Join us to start your knowledge journey with CITHUB!", font_size=40, color=LOGO_BLUE)
        self.play(Write(ending))
        self.wait(2)

        # Transform to highlight CITHUB
        cithub_highlight = Text("CITHUB", font_size=64, color=ORANGE)  # 增加字體大小和顏色
        self.play(Transform(ending, cithub_highlight))
        self.wait(2)

        self.play(FadeOut(ending, shift=DOWN))
        self.wait(1)
