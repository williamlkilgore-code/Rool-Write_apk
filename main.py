"""
PRNG Dice Game - A random number generator based dice rolling game
Supports both horizontal and vertical orientations with responsive layout
"""

import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.properties import (
    StringProperty, NumericProperty, ListProperty,
    BooleanProperty, ObjectProperty
)
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Line
from kivy.lang import Builder


class PRNG:
    """Linear Congruential Generator - Custom PRNG implementation"""

    def __init__(self, seed=None):
        self.modulus = 2**31 - 1  # Mersenne prime
        self.multiplier = 48271
        self.increment = 0
        if seed is None:
            seed = random.randint(1, self.modulus - 1)
        self.state = seed % self.modulus
        if self.state == 0:
            self.state = 1

    def next(self):
        """Generate next random number"""
        self.state = (self.multiplier * self.state + self.increment) % self.modulus
        return self.state

    def random(self):
        """Return a random float between 0 and 1"""
        return self.next() / self.modulus

    def randint(self, a, b):
        """Return a random integer between a and b inclusive"""
        return a + int(self.random() * (b - a + 1))

    def reseed(self, seed=None):
        """Reseed the generator"""
        if seed is None:
            seed = random.randint(1, self.modulus - 1)
        self.state = seed % self.modulus
        if self.state == 0:
            self.state = 1


class DiceWidget(Widget):
    """Widget to display a single die with dots"""
    value = NumericProperty(1)
    rolling = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas, value=self.update_canvas)
        Clock.schedule_once(lambda dt: self.update_canvas(), 0)

    def update_canvas(self, *args):
        """Redraw the dice"""
        self.canvas.clear()

        with self.canvas:
            # Dice background
            if self.rolling:
                Color(0.9, 0.85, 0.7, 1)
            else:
                Color(0.98, 0.98, 0.95, 1)

            # Draw rounded rectangle for dice
            dice_size = min(self.width, self.height) * 0.95
            x_offset = self.x + (self.width - dice_size) / 2
            y_offset = self.y + (self.height - dice_size) / 2

            RoundedRectangle(
                pos=(x_offset, y_offset),
                size=(dice_size, dice_size),
                radius=[dp(12)]
            )

            # Dice border
            Color(0.3, 0.3, 0.35, 1)
            Line(
                rounded_rectangle=(x_offset, y_offset, dice_size, dice_size, dp(12)),
                width=dp(2)
            )

            # Draw dots
            Color(0.15, 0.15, 0.2, 1)
            dot_positions = self.get_dot_positions()
            dot_size = dice_size * 0.18

            for px, py in dot_positions:
                dot_x = x_offset + (px * dice_size) - (dot_size / 2)
                dot_y = y_offset + (py * dice_size) - (dot_size / 2)
                Ellipse(pos=(dot_x, dot_y), size=(dot_size, dot_size))

    def get_dot_positions(self):
        """Return dot positions based on dice value (relative 0-1 coordinates)"""
        positions = {
            1: [(0.5, 0.5)],
            2: [(0.28, 0.72), (0.72, 0.28)],
            3: [(0.28, 0.72), (0.5, 0.5), (0.72, 0.28)],
            4: [(0.28, 0.28), (0.28, 0.72), (0.72, 0.28), (0.72, 0.72)],
            5: [(0.28, 0.28), (0.28, 0.72), (0.5, 0.5), (0.72, 0.28), (0.72, 0.72)],
            6: [(0.28, 0.25), (0.28, 0.5), (0.28, 0.75),
                (0.72, 0.25), (0.72, 0.5), (0.72, 0.75)],
        }
        return positions.get(self.value, [(0.5, 0.5)])


class DiceContainer(GridLayout):
    """Container that holds and arranges dice"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dice_widgets = []
        self.spacing = dp(15)
        self.padding = dp(15)

    def update_dice(self, values, rolling=False):
        """Update dice display with given values"""
        # Clear existing dice
        self.clear_widgets()
        self.dice_widgets = []

        num_dice = len(values)

        # Adjust columns based on dice count
        if num_dice <= 2:
            self.cols = num_dice
        elif num_dice <= 4:
            self.cols = 2
        else:
            self.cols = 3

        # Create dice widgets
        for val in values:
            dice = DiceWidget(value=val, rolling=rolling)
            dice.size_hint = (1, 1)
            self.dice_widgets.append(dice)
            self.add_widget(dice)


class PRNGDiceGame(BoxLayout):
    """Main game widget with responsive layout"""

    dice_values = ListProperty([1, 1])
    total = NumericProperty(2)
    roll_count = NumericProperty(0)
    high_score = NumericProperty(0)
    status_text = StringProperty("Tap 'ROLL DICE' to play!")
    is_rolling = BooleanProperty(False)
    is_portrait = BooleanProperty(True)
    num_dice = NumericProperty(2)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prng = PRNG()
        self.roll_history = []
        self.dice_container = None
        self.animation_step = 0
        self.max_animation_steps = 15

        # Bind to window size changes for responsive layout
        Window.bind(on_resize=self.on_window_resize)

        # Build UI after initialization
        Clock.schedule_once(self.build_ui, 0)

    def build_ui(self, dt):
        """Build the user interface"""
        self.check_orientation()
        self.rebuild_layout()

    def on_window_resize(self, instance, width, height):
        """Handle window resize for orientation changes"""
        old_orientation = self.is_portrait
        self.check_orientation()
        if old_orientation != self.is_portrait:
            self.rebuild_layout()

    def check_orientation(self, *args):
        """Check and update orientation"""
        self.is_portrait = Window.height >= Window.width

    def rebuild_layout(self, *args):
        """Rebuild layout based on orientation"""
        self.clear_widgets()

        # Set main orientation
        self.orientation = 'vertical' if self.is_portrait else 'horizontal'
        self.padding = dp(15)
        self.spacing = dp(15)

        # Create sections
        header = self.create_header()
        dice_area = self.create_dice_area()
        controls = self.create_controls()

        if self.is_portrait:
            # Portrait: header, dice, controls (top to bottom)
            header.size_hint = (1, 0.12)
            dice_area.size_hint = (1, 0.48)
            controls.size_hint = (1, 0.40)
        else:
            # Landscape: controls | dice | header (left to right)
            controls.size_hint = (0.28, 1)
            dice_area.size_hint = (0.44, 1)
            header.size_hint = (0.28, 1)

        if self.is_portrait:
            self.add_widget(header)
            self.add_widget(dice_area)
            self.add_widget(controls)
        else:
            self.add_widget(controls)
            self.add_widget(dice_area)
            self.add_widget(header)

        # Update dice display
        self.update_dice_display()

    def create_header(self):
        """Create header section with title and status"""
        header = BoxLayout(orientation='vertical', spacing=dp(5))

        # Background
        with header.canvas.before:
            Color(0.18, 0.18, 0.25, 1)
            self.header_bg = RoundedRectangle(radius=[dp(15)])
        header.bind(pos=lambda i, v: setattr(self.header_bg, 'pos', v),
                   size=lambda i, v: setattr(self.header_bg, 'size', v))

        # Title
        title = Label(
            text="[b]PRNG DICE[/b]",
            markup=True,
            font_size=sp(32) if self.is_portrait else sp(26),
            color=(1, 0.85, 0.2, 1),
            size_hint_y=0.5
        )

        # Status
        self.status_label = Label(
            text=self.status_text,
            font_size=sp(16) if self.is_portrait else sp(14),
            color=(0.9, 0.9, 0.9, 1),
            size_hint_y=0.3,
            text_size=(None, None),
            halign='center'
        )

        # High score
        self.highscore_label = Label(
            text=f"High: {self.high_score}",
            font_size=sp(14),
            color=(0.7, 0.9, 0.7, 1),
            size_hint_y=0.2
        )

        header.add_widget(title)
        header.add_widget(self.status_label)
        header.add_widget(self.highscore_label)

        return header

    def create_dice_area(self):
        """Create dice display area"""
        dice_area = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))

        # Background
        with dice_area.canvas.before:
            Color(0.12, 0.35, 0.18, 1)
            self.dice_area_bg = RoundedRectangle(radius=[dp(20)])
        dice_area.bind(pos=lambda i, v: setattr(self.dice_area_bg, 'pos', v),
                      size=lambda i, v: setattr(self.dice_area_bg, 'size', v))

        # Dice container
        self.dice_container = DiceContainer()
        self.dice_container.size_hint = (1, 0.75)

        # Total display
        total_box = BoxLayout(size_hint=(1, 0.25), padding=dp(5))

        with total_box.canvas.before:
            Color(0.08, 0.25, 0.12, 1)
            self.total_bg = RoundedRectangle(radius=[dp(12)])
        total_box.bind(pos=lambda i, v: setattr(self.total_bg, 'pos', v),
                      size=lambda i, v: setattr(self.total_bg, 'size', v))

        self.total_label = Label(
            text=f"Total: {self.total}",
            font_size=sp(36) if self.is_portrait else sp(30),
            bold=True,
            color=(1, 1, 1, 1)
        )
        total_box.add_widget(self.total_label)

        dice_area.add_widget(self.dice_container)
        dice_area.add_widget(total_box)

        return dice_area

    def create_controls(self):
        """Create control buttons"""
        controls = BoxLayout(orientation='vertical', spacing=dp(12), padding=dp(10))

        # Background
        with controls.canvas.before:
            Color(0.15, 0.15, 0.22, 1)
            self.controls_bg = RoundedRectangle(radius=[dp(15)])
        controls.bind(pos=lambda i, v: setattr(self.controls_bg, 'pos', v),
                     size=lambda i, v: setattr(self.controls_bg, 'size', v))

        # Roll button
        roll_btn = Button(
            text="ROLL DICE",
            font_size=sp(26) if self.is_portrait else sp(22),
            bold=True,
            size_hint_y=0.3,
            background_color=(0, 0, 0, 0)
        )
        self.roll_btn = roll_btn

        with roll_btn.canvas.before:
            Color(0.2, 0.55, 0.85, 1)
            self.roll_btn_bg = RoundedRectangle(radius=[dp(18)])
        roll_btn.bind(pos=lambda i, v: setattr(self.roll_btn_bg, 'pos', v),
                     size=lambda i, v: setattr(self.roll_btn_bg, 'size', v))
        roll_btn.bind(on_release=lambda x: self.roll_dice())

        # Dice count controls
        dice_ctrl = BoxLayout(spacing=dp(15), size_hint_y=0.18)

        minus_btn = Button(
            text="-",
            font_size=sp(32),
            bold=True,
            background_color=(0, 0, 0, 0)
        )
        with minus_btn.canvas.before:
            Color(0.7, 0.25, 0.25, 1)
            self.minus_bg = RoundedRectangle(radius=[dp(12)])
        minus_btn.bind(pos=lambda i, v: setattr(self.minus_bg, 'pos', v),
                      size=lambda i, v: setattr(self.minus_bg, 'size', v))
        minus_btn.bind(on_release=lambda x: self.remove_dice())

        self.dice_count_label = Label(
            text=f"{self.num_dice} Dice",
            font_size=sp(20),
            color=(0.95, 0.95, 0.95, 1),
            size_hint_x=1.5
        )

        plus_btn = Button(
            text="+",
            font_size=sp(32),
            bold=True,
            background_color=(0, 0, 0, 0)
        )
        with plus_btn.canvas.before:
            Color(0.25, 0.6, 0.25, 1)
            self.plus_bg = RoundedRectangle(radius=[dp(12)])
        plus_btn.bind(pos=lambda i, v: setattr(self.plus_bg, 'pos', v),
                     size=lambda i, v: setattr(self.plus_bg, 'size', v))
        plus_btn.bind(on_release=lambda x: self.add_dice())

        dice_ctrl.add_widget(minus_btn)
        dice_ctrl.add_widget(self.dice_count_label)
        dice_ctrl.add_widget(plus_btn)

        # Stats display
        stats_box = BoxLayout(size_hint_y=0.15, padding=dp(8))

        with stats_box.canvas.before:
            Color(0.22, 0.22, 0.28, 1)
            self.stats_bg = RoundedRectangle(radius=[dp(10)])
        stats_box.bind(pos=lambda i, v: setattr(self.stats_bg, 'pos', v),
                      size=lambda i, v: setattr(self.stats_bg, 'size', v))

        self.stats_label = Label(
            text="No rolls yet",
            font_size=sp(13),
            color=(0.8, 0.8, 0.8, 1)
        )
        stats_box.add_widget(self.stats_label)

        # Reset button
        reset_btn = Button(
            text="Reset Game",
            font_size=sp(17),
            size_hint_y=0.15,
            background_color=(0, 0, 0, 0)
        )
        with reset_btn.canvas.before:
            Color(0.45, 0.45, 0.5, 1)
            self.reset_bg = RoundedRectangle(radius=[dp(10)])
        reset_btn.bind(pos=lambda i, v: setattr(self.reset_bg, 'pos', v),
                      size=lambda i, v: setattr(self.reset_bg, 'size', v))
        reset_btn.bind(on_release=lambda x: self.reset_game())

        # Spacer
        spacer = Widget(size_hint_y=0.22)

        controls.add_widget(roll_btn)
        controls.add_widget(dice_ctrl)
        controls.add_widget(stats_box)
        controls.add_widget(reset_btn)
        controls.add_widget(spacer)

        return controls

    def update_dice_display(self, rolling=False):
        """Update the dice container with current values"""
        if self.dice_container:
            self.dice_container.update_dice(self.dice_values, rolling)

    def roll_dice(self):
        """Roll all dice with animation"""
        if self.is_rolling:
            return

        self.is_rolling = True
        self.roll_btn.text = "Rolling..."
        self.status_text = "Rolling..."
        if hasattr(self, 'status_label'):
            self.status_label.text = self.status_text
        self.roll_count += 1

        # Start rolling animation
        self.animation_step = 0
        Clock.schedule_interval(self.animate_roll, 0.06)

    def animate_roll(self, dt):
        """Animate the dice rolling"""
        self.animation_step += 1

        # Generate random values during animation
        new_values = [self.prng.randint(1, 6) for _ in range(self.num_dice)]
        self.dice_values = new_values
        self.update_dice_display(rolling=True)

        if self.animation_step >= self.max_animation_steps:
            # Final values
            self.finalize_roll()
            return False
        return True

    def finalize_roll(self):
        """Finalize the roll and update stats"""
        self.is_rolling = False
        self.roll_btn.text = "ROLL DICE"
        self.total = sum(self.dice_values)
        self.roll_history.append(self.total)

        if hasattr(self, 'total_label'):
            self.total_label.text = f"Total: {self.total}"

        # Update high score
        if self.total > self.high_score:
            self.high_score = self.total
            self.status_text = f"NEW HIGH: {self.total}!"
            if hasattr(self, 'highscore_label'):
                self.highscore_label.text = f"High: {self.high_score}"
        else:
            self.status_text = f"You rolled {self.total}!"

        # Check for special rolls
        if len(set(self.dice_values)) == 1 and self.num_dice > 1:
            if self.dice_values[0] == 6:
                self.status_text = "JACKPOT! All sixes!"
            else:
                self.status_text = f"DOUBLES! All {self.dice_values[0]}s!"

        if hasattr(self, 'status_label'):
            self.status_label.text = self.status_text

        # Update stats
        self.update_stats()
        self.update_dice_display(rolling=False)

    def update_stats(self):
        """Update statistics display"""
        if hasattr(self, 'stats_label') and self.roll_history:
            avg = sum(self.roll_history) / len(self.roll_history)
            self.stats_label.text = f"Avg: {avg:.1f} | Rolls: {self.roll_count}"

    def add_dice(self):
        """Add a die (max 6)"""
        if self.num_dice < 6:
            self.num_dice += 1
            self.dice_values = list(self.dice_values) + [1]
            self.total = sum(self.dice_values)
            if hasattr(self, 'dice_count_label'):
                self.dice_count_label.text = f"{self.num_dice} Dice"
            if hasattr(self, 'total_label'):
                self.total_label.text = f"Total: {self.total}"
            self.status_text = f"Now rolling {self.num_dice} dice"
            if hasattr(self, 'status_label'):
                self.status_label.text = self.status_text
            self.update_dice_display()

    def remove_dice(self):
        """Remove a die (min 1)"""
        if self.num_dice > 1:
            self.num_dice -= 1
            self.dice_values = list(self.dice_values)[:-1]
            self.total = sum(self.dice_values)
            if hasattr(self, 'dice_count_label'):
                self.dice_count_label.text = f"{self.num_dice} Dice"
            if hasattr(self, 'total_label'):
                self.total_label.text = f"Total: {self.total}"
            self.status_text = f"Now rolling {self.num_dice} dice"
            if hasattr(self, 'status_label'):
                self.status_label.text = self.status_text
            self.update_dice_display()

    def reset_game(self):
        """Reset game stats"""
        self.roll_count = 0
        self.high_score = 0
        self.roll_history = []
        self.dice_values = [1] * self.num_dice
        self.total = self.num_dice
        self.status_text = "Game reset! Tap 'ROLL DICE'!"
        self.prng.reseed()

        if hasattr(self, 'status_label'):
            self.status_label.text = self.status_text
        if hasattr(self, 'highscore_label'):
            self.highscore_label.text = f"High: {self.high_score}"
        if hasattr(self, 'total_label'):
            self.total_label.text = f"Total: {self.total}"
        if hasattr(self, 'stats_label'):
            self.stats_label.text = "No rolls yet"

        self.update_dice_display()


class PRNGDiceApp(App):
    """Main application class"""

    def build(self):
        """Build the application"""
        self.title = "PRNG Dice Game"

        # Set window size for desktop testing
        if platform not in ('android', 'ios'):
            Window.size = (420, 750)
            Window.minimum_width = 320
            Window.minimum_height = 480

        # Set background color
        Window.clearcolor = (0.1, 0.1, 0.15, 1)

        return PRNGDiceGame()

    def on_start(self):
        """Called when the application starts"""
        pass

    def on_pause(self):
        """Called when the application is paused (Android)"""
        return True

    def on_resume(self):
        """Called when the application resumes (Android)"""
        pass


if __name__ == '__main__':
    PRNGDiceApp().run()
