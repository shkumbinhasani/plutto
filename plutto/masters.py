import math
from dataclasses import dataclass

FAMILY = "Plutto"
UNITS = 1000
XH = 540
CAP = 712
ASC = 775
DESC = -210
OV = 10
CAP_OV = 14
ARCH_OV = 7
OVERSHOOT = (OV, 11, OV, 13)
CAP_OVERSHOOT = (CAP_OV, 17, CAP_OV, 19)
ARCH_OVERSHOOT = (ARCH_OV, 8, ARCH_OV, 10)
TOP_OV = max(OVERSHOOT)
LINE_ASCENT = 950
LINE_DESCENT = -250
REGULAR_WEIGHT = 400
BOLD_WEIGHT = 700
SLANT = 9
ITALIC_WIDTH = 0.965
ITALIC = "Italic"
UPRIGHT_DEFAULT = "Regular"


def mix_at(weight):
    return (weight - REGULAR_WEIGHT) / (BOLD_WEIGHT - REGULAR_WEIGHT)


LIGHT_MIX = mix_at(300)
BLACK_MIX = mix_at(900)


def interpolate(mix, regular, bold, light=None, black=None):
    step = bold - regular
    if mix < 0:
        if light is None:
            return regular + step * mix
        return regular + (regular - light) * mix / -LIGHT_MIX
    if mix <= 1 or black is None:
        return regular + step * mix
    return bold + (black - bold) * (mix - 1) / (BLACK_MIX - 1)


@dataclass(frozen=True)
class Master:
    name: str
    weight: int
    mix: float
    italic: bool = False
    slant: float = 0.0

    @property
    def slope(self):
        return math.tan(math.radians(self.slant))

    @property
    def narrowing(self):
        return ITALIC_WIDTH if self.italic else 1.0

    def v(self, regular, bold, light=None, black=None):
        return interpolate(self.mix, regular, bold, light, black)

    @property
    def ov(self):
        return interpolate(self.mix, *OVERSHOOT)

    @property
    def cap_ov(self):
        return interpolate(self.mix, *CAP_OVERSHOOT)

    @property
    def arch_ov(self):
        return interpolate(self.mix, *ARCH_OVERSHOOT)

    @property
    def stem(self):
        return self.v(84, 150, light=56, black=204)

    @property
    def round(self):
        return self.v(88, 156, light=59, black=208)

    @property
    def thin(self):
        return self.v(74, 118, light=52, black=148)

    @property
    def bar(self):
        return self.v(72, 118, light=51, black=140)

    @property
    def diag(self):
        return self.v(80, 138, light=54, black=188)

    @property
    def cap_stem(self):
        return self.v(90, 158, light=60, black=214)

    @property
    def cap_round(self):
        return self.v(94, 164, light=63, black=218)

    @property
    def cap_thin(self):
        return self.v(78, 124, light=55, black=164)

    @property
    def cap_bar(self):
        return self.v(76, 130, light=54, black=172)

    @property
    def cap_diag(self):
        return self.v(86, 146, light=58, black=198)

    @property
    def k_out(self):
        return self.v(0.61, 0.62, light=0.60, black=0.63)

    @property
    def k_in(self):
        return self.v(0.60, 0.57, light=0.61, black=0.54)

    @property
    def track(self):
        return self.v(0, 2, light=0, black=6)

    def bearing(self, side):
        if side == "straight":
            return self.v(70, 54, light=74, black=44)
        if side == "round":
            return self.v(38, 28, light=40, black=21)
        if side == "diagonal":
            return self.v(12, 8, light=14, black=5)
        if side == "cap":
            return self.v(78, 62, light=82, black=52)
        if side == "cap_round":
            return self.v(44, 32, light=46, black=25)
        if side == "cap_diagonal":
            return self.v(10, 6, light=12, black=3)
        return side


def line_heights(master):
    ov, cap_ov, arch_ov = (math.floor(value + 0.5) for value in (master.ov, master.cap_ov, master.arch_ov))
    return {0, XH, CAP, ASC, DESC, -ov, XH + ov, CAP + ov, CAP + cap_ov, -cap_ov, ASC + ov, DESC - ov, XH + arch_ov, -arch_ov}


def style_name(weight_name, italic):
    if not italic:
        return weight_name
    if weight_name == UPRIGHT_DEFAULT:
        return ITALIC
    return f"{weight_name} {ITALIC}"


def weight_name(master):
    if master.name == ITALIC:
        return UPRIGHT_DEFAULT
    return master.name.removesuffix(f" {ITALIC}")


def italic_of(master):
    return Master(style_name(master.name, True), master.weight, master.mix, italic=True, slant=SLANT)


LIGHT = Master("Light", 300, LIGHT_MIX)
REGULAR = Master("Regular", REGULAR_WEIGHT, mix_at(REGULAR_WEIGHT))
BOLD = Master("Bold", BOLD_WEIGHT, mix_at(BOLD_WEIGHT))
BLACK = Master("Black", 900, BLACK_MIX)
MASTERS = [LIGHT, REGULAR, BOLD, BLACK]
DEFAULT = REGULAR
LIGHT_ITALIC, ITALIC_REGULAR, BOLD_ITALIC, BLACK_ITALIC = ITALIC_MASTERS = [italic_of(master) for master in MASTERS]
ITALIC_DEFAULT = ITALIC_REGULAR
DESIGN_SPACES = [MASTERS, ITALIC_MASTERS]
ALL_MASTERS = MASTERS + ITALIC_MASTERS


def family(master):
    return ITALIC_MASTERS if master.italic else MASTERS


def roman_of(master):
    return next(roman for roman in MASTERS if roman.weight == master.weight)


def default_of(masters):
    return ITALIC_DEFAULT if masters[0].italic else DEFAULT


INSTANCES = [
    ("Light", 300),
    ("Regular", 400),
    ("Medium", 500),
    ("SemiBold", 600),
    ("Bold", 700),
    ("ExtraBold", 800),
    ("Black", 900),
]

BETWEEN_STATICS = [Master("Medium", 500, mix_at(500)), Master("SemiBold", 600, mix_at(600)), Master("ExtraBold", 800, mix_at(800))]
ITALIC_BETWEEN_STATICS = [italic_of(master) for master in BETWEEN_STATICS]
DRAWN_HEIGHTS = tuple(sorted({height for master in ALL_MASTERS for height in line_heights(master)}))
