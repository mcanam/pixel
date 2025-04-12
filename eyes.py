"""
Eyes class is responsible for rendering animated eyes on an SH1106 OLED display using the luma.oled library.
it handles eye movements, blinking, eyelid expressions, and mood-based animations such as angry, sad, tired, and happy.
the eyes can also move randomly when idle, simulating a more natural and lifelike behavior.

this implementation is inspired by the RoboEyes library (https://github.com/FluxGarage/RoboEyes), originally written in C++.
"""

from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas
from threading import Thread
from time import time, sleep
from enum import Enum
from random import uniform
from dataclasses import dataclass

class EyesPosition(Enum):
    CENTER = 0
    TOP = 1
    LEFT = 2
    BOTTOM = 3
    RIGHT  = 4
    TOP_LEFT = 5
    TOP_RIGHT = 6
    BOTTOM_LEFT = 7
    BOTTOM_RIGHT = 8
    
class EyesMood(Enum):
    NEUTRAL = 0
    ANGRY = 1
    TIRED = 2
    HAPPY = 3
    SAD = 4
    
@dataclass
class Eye:
    x: float
    y: float
    w: float
    h: float
    x_next: float
    y_next: float
    w_next: float
    h_next: float
    eyelid_h_l: float
    eyelid_h_r: float
    eyelid_h_l_next: float
    eyelid_h_r_next: float
    
class Eyes:
    def __init__(self):
        # screen setup
        self.screen_width = 128
        self.screen_height = 64
        self.frame_rate = 0.02
        self.device = sh1106(i2c(port=1, address=0x3C), width=self.screen_width, height=self.screen_height)
        
        # default eye properties
        self.default_eye_w = 36
        self.default_eye_h = 36
        self.default_eye_radius = 8
        self.default_eye_gap = 10
        
        # initialize left and right eyes
        eye_x = (self.screen_width - ((self.default_eye_w * 2) + self.default_eye_gap)) / 2
        eye_y = (self.screen_height - self.default_eye_h) / 2

        self.eye_l = Eye(
            x=eye_x,
            y=eye_y,
            w=self.default_eye_w,
            h=1,
            x_next=eye_x,
            y_next=eye_y,
            w_next=self.default_eye_w,
            h_next=1,
            eyelid_h_l=eye_y,
            eyelid_h_r=eye_y,
            eyelid_h_l_next=eye_y,
            eyelid_h_r_next=eye_y
        )

        self.eye_r = Eye(
            x=eye_x + self.default_eye_w + self.default_eye_gap,
            y=eye_y,
            w=self.default_eye_w,
            h=1,
            x_next=eye_x + self.default_eye_w + self.default_eye_gap,
            y_next=eye_y,
            w_next=self.default_eye_w,
            h_next=1,
            eyelid_h_l=eye_y,
            eyelid_h_r=eye_y,
            eyelid_h_l_next=eye_y,
            eyelid_h_r_next=eye_y
        )
        
        # happy eyelid
        self.eyelid_happy_h = 1
        self.eyelid_happy_h_next = 1
        
        # state
        self.is_open = False
        self.is_idle = False
        self.mood = EyesMood.NEUTRAL
        self.idle_timer = 0
        self.blink_timer = 0
        
        # start drawing thread
        self.thread = Thread(target=self.draw, daemon=True)
        self.thread.start()
    
    def interpolate(self, current, target):
        # use averging interpolation for smooth transitions
        return (current + target) / 2
    
    def get_max_x_limit(self):
        return self.screen_width - self.eye_l.w - self.default_eye_gap - self.eye_r.w

    def get_max_y_limit(self):
        return self.screen_height - self.default_eye_h

    def set_idle(self, value):
        self.is_idle = value
        if not value: self.set_position(EyesPosition.CENTER)

    def set_mood(self, value):
        self.mood = value

    def set_position(self, value):
        max_x = self.get_max_x_limit()
        max_y = self.get_max_y_limit()

        positions = {
            EyesPosition.CENTER: (max_x / 2, max_y / 2),
            EyesPosition.TOP: (max_x / 2, 0),
            EyesPosition.LEFT: (0, max_y / 2),
            EyesPosition.BOTTOM: (max_x / 2, max_y),
            EyesPosition.RIGHT: (max_x, max_y / 2),
            EyesPosition.TOP_LEFT: (0, 0),
            EyesPosition.TOP_RIGHT: (max_x, 0),
            EyesPosition.BOTTOM_LEFT: (0, max_y),
            EyesPosition.BOTTOM_RIGHT: (max_x, max_y)
        }

        self.eye_l.x_next, self.eye_l.y_next = positions.get(value)

    def open(self):
        self.eye_l.h_next = self.default_eye_h
        self.eye_r.h_next = self.default_eye_h
        self.is_open = True

    def close(self):
        self.eye_l.h_next = 1
        self.eye_r.h_next = 1
        self.is_open = False
        self.set_position(EyesPosition.CENTER)
    
    def update_eye_position(self):
        # size
        self.eye_l.w = self.interpolate(self.eye_l.w, self.eye_l.w_next)
        self.eye_l.h = self.interpolate(self.eye_l.h, self.eye_l.h_next)
        self.eye_r.w = self.interpolate(self.eye_r.w, self.eye_r.w_next)
        self.eye_r.h = self.interpolate(self.eye_r.h, self.eye_r.h_next)

        # centering
        self.eye_l.x += (self.default_eye_w - self.eye_l.w) / 2
        self.eye_l.y += (self.default_eye_h - self.eye_l.h) / 2
        self.eye_r.x += (self.default_eye_w - self.eye_r.w) / 2
        self.eye_r.y += (self.default_eye_h - self.eye_r.h) / 2

        # position
        self.eye_l.x = self.interpolate(self.eye_l.x, self.eye_l.x_next)
        self.eye_l.y = self.interpolate(self.eye_l.y, self.eye_l.y_next)

        # position of the right eye relative to the left eye
        self.eye_r.x_next = self.eye_l.x_next + self.eye_l.w + self.default_eye_gap
        self.eye_r.y_next = self.eye_l.y_next
        self.eye_r.x = self.interpolate(self.eye_r.x, self.eye_r.x_next)
        self.eye_r.y = self.interpolate(self.eye_r.y, self.eye_r.y_next)
        
    def update_eye_state(self):
        # open eyes afterblinking
        if self.is_open:
            if self.eye_l.h <= 1.1: self.eye_l.h_next = self.default_eye_h
            if self.eye_r.h <= 1.1: self.eye_r.h_next = self.default_eye_h

        # blink
        if time() >= self.blink_timer and self.is_open:
            self.eye_l.h_next = 1
            self.eye_r.h_next = 1
            self.blink_timer = time() + uniform(3, 6)

        # idle movement
        if self.is_idle and self.is_open and time() >= self.idle_timer:
            self.eye_l.x_next = uniform(0, self.get_max_x_limit())
            self.eye_l.y_next = uniform(0, self.get_max_y_limit())
            self.idle_timer = time() + uniform(3, 6)
    
    def update_eyelids(self):
        # neutral
        if self.mood in (EyesMood.NEUTRAL, EyesMood.HAPPY):
            self.eye_l.eyelid_h_l_next = self.eye_l.y
            self.eye_l.eyelid_h_r_next = self.eye_l.y
            self.eye_r.eyelid_h_l_next = self.eye_r.y
            self.eye_r.eyelid_h_r_next = self.eye_r.y

        # angry
        if self.mood == EyesMood.ANGRY:
            self.eye_l.eyelid_h_l_next = self.eye_l.y + (self.eye_l.h / 4)
            self.eye_l.eyelid_h_r_next = self.eye_l.y + (self.eye_l.h / 2)
            self.eye_r.eyelid_h_l_next = self.eye_r.y + (self.eye_r.h / 2)
            self.eye_r.eyelid_h_r_next = self.eye_r.y + (self.eye_r.h / 4)

        # sad
        if self.mood == EyesMood.SAD:
            self.eye_l.eyelid_h_l_next = self.eye_l.y + (self.eye_l.h / 2)
            self.eye_l.eyelid_h_r_next = self.eye_l.y + (self.eye_l.h / 4)
            self.eye_r.eyelid_h_l_next = self.eye_r.y + (self.eye_r.h / 4)
            self.eye_r.eyelid_h_r_next = self.eye_r.y + (self.eye_r.h / 2)

        # tired
        if self.mood == EyesMood.TIRED:
            self.eye_l.eyelid_h_l_next = self.eye_l.y + (self.eye_l.h / 1.2)
            self.eye_l.eyelid_h_r_next = self.eye_l.y + (self.eye_l.h / 1.4)
            self.eye_r.eyelid_h_l_next = self.eye_r.y + (self.eye_r.h / 1.4)
            self.eye_r.eyelid_h_r_next = self.eye_r.y + (self.eye_r.h / 1.2)

        # happy
        self.eyelid_happy_h_next = 3 if self.mood == EyesMood.HAPPY else 1
        self.eyelid_happy_h = self.interpolate(self.eyelid_happy_h, self.eyelid_happy_h_next)

        self.eye_l.eyelid_h_l = self.interpolate(self.eye_l.eyelid_h_l, self.eye_l.eyelid_h_l_next)
        self.eye_l.eyelid_h_r = self.interpolate(self.eye_l.eyelid_h_r, self.eye_l.eyelid_h_r_next)
        self.eye_r.eyelid_h_l = self.interpolate(self.eye_r.eyelid_h_l, self.eye_r.eyelid_h_l_next)
        self.eye_r.eyelid_h_r = self.interpolate(self.eye_r.eyelid_h_r, self.eye_r.eyelid_h_r_next)
    
    def draw(self):
        while True:
            self.update_eye_position()
            self.update_eye_state()
            self.update_eyelids()

            with canvas(self.device) as draw:
                # draw eyes
                draw.rounded_rectangle(((self.eye_l.x, self.eye_l.y), (self.eye_l.x + self.eye_l.w, self.eye_l.y + self.eye_l.h)), radius=self.default_eye_radius, fill="white")
                draw.rounded_rectangle(((self.eye_r.x, self.eye_r.y), (self.eye_r.x + self.eye_r.w, self.eye_r.y + self.eye_r.h)), radius=self.default_eye_radius, fill="white")

                # draw eyelids
                draw.polygon(((self.eye_l.x - 2, self.eye_l.y - 2), (self.eye_l.x + self.eye_l.w + 2, self.eye_l.y - 2), (self.eye_l.x + self.eye_l.w + 2, self.eye_l.eyelid_h_r - 1), (self.eye_l.x - 2, self.eye_l.eyelid_h_l - 1)), fill="black")
                draw.polygon(((self.eye_r.x - 2, self.eye_r.y - 2), (self.eye_r.x + self.eye_r.w + 2, self.eye_r.y - 2), (self.eye_r.x + self.eye_r.w + 2, self.eye_r.eyelid_h_r - 1), (self.eye_r.x - 2, self.eye_r.eyelid_h_l - 1)), fill="black")

                # happy eyelids
                draw.rounded_rectangle(((self.eye_l.x, self.eye_l.y + (self.eye_l.h / self.eyelid_happy_h) + 2), (self.eye_l.x + self.eye_l.w, self.eye_l.y + self.eye_l.h + 2)), radius=self.default_eye_radius, fill="black")
                draw.rounded_rectangle(((self.eye_r.x, self.eye_r.y + (self.eye_r.h / self.eyelid_happy_h) + 2), (self.eye_r.x + self.eye_r.w, self.eye_r.y + self.eye_r.h + 2)), radius=self.default_eye_radius, fill="black")

            sleep(self.frame_rate)