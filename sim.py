from enum import Enum
from typing import Match
from rich import print
from rich import inspect
import csv


class Capabilities(Enum):
    CORAL_1 = 1
    CORAL_2 = 2
    CORAL_3 = 3
    CORAL_4 = 4
    CORAL_HP = 5
    CORAL_FLOOR = 6

    ALGAE_2 = 7
    ALGAE_3 = 8
    ALGAE_FLOOR = 9
    ALGAE_NET = 10
    ALGAE_PROC = 11

    CLIMB_LOW = 12
    CLIMB_HIGH = 11


# Place estimates here
timemap = {
    Capabilities.CORAL_1: 2,
    Capabilities.CORAL_2: 3,
    Capabilities.CORAL_3: 3,
    Capabilities.CORAL_4: 4,
    Capabilities.CORAL_HP: 2,
    Capabilities.CORAL_FLOOR: 2,
    Capabilities.ALGAE_2: 1,
    Capabilities.ALGAE_3: 1,
    Capabilities.ALGAE_FLOOR: 1,
    Capabilities.ALGAE_NET: 2,
    Capabilities.ALGAE_PROC: 2,
    Capabilities.CLIMB_LOW: 10,
    Capabilities.CLIMB_HIGH: 8,
}

r1_abilties = [Capabilities.CORAL_FLOOR, Capabilities.CORAL_1]
r2_abilties = [Capabilities.ALGAE_PROC, Capabilities.ALGAE_2, Capabilities.ALGAE_3]
r3_abilties = []
HP_ACCURACY = 0.5  # must be <1


class Level:
    def __init__(self, height):
        self.height = height
        if height == 1:
            self.coral_slots = 3 * 8
            self.algae_slots = 0
        elif height == 2:
            self.algae_slots = 3
            self.coral_slots = 6
        elif height == 3:
            self.algae_slots = 3
            self.coral_slots = 6
        elif height == 4:
            self.algae_slots = 0
            self.coral_slots = 12

    def take_algae(self) -> bool:  # returns if an algae was drawn
        if self.algae_slots > 0:
            self.algae_slots -= 1
            return True
        else:
            return False

    def score_coral(self) -> bool:
        if self.coral_slots > 0:
            self.coral_slots -= 1
            return True
        else:
            return False


class Reef(object):
    def __init__(self):
        self.L1 = Level(1)
        self.L2 = Level(2)
        self.L3 = Level(3)
        self.L4 = Level(4)
        self.levels = [self.L1, self.L2, self.L3, self.L4]

    def take_algae(self, level):
        if self.levels[level - 1].take_algae():
            if level == 2:
                # taking an algae on l2 frees up 2 slots on l3
                self.levels[level].coral_slots += 2
                self.levels[level - 1].coral_slots += 2
            elif level == 3:
                # l3 frees up level and level below
                self.levels[level - 2].coral_slots += 2
                self.levels[level - 1].coral_slots += 2
            return True
        else:
            return False

    def place_coral(self, level):
        return self.levels[level - 1].score_coral()


reef = Reef()


class Robot:
    def __init__(self, abilties):
        self.abilties = abilties
        self.cargo_coral = 1
        self.cargo_algae = 0
        # Actions are instant, so after an action occurs, the bot is in a "time debt" where they do nothing until the action is finished
        self.time_debt = 0

    def teleop(self, time_left):
        if self.time_debt > 0:
            self.time_debt -= 1
            return

        # Priority 1: Climb
        if (
            Capabilities.CLIMB_LOW in self.abilties
            and (time_left + self.time_debt) < 20
            and (time_left + self.time_debt) > timemap[Capabilities.CLIMB_LOW]
        ):
            self.time_debt += timemap[Capabilities.CLIMB_LOW]
            return "Climbed low"

        elif (
            Capabilities.CLIMB_HIGH in self.abilties
            and (time_left + self.time_debt) < 20
            and (time_left + self.time_debt) > timemap[Capabilities.CLIMB_HIGH]
        ):
            self.time_debt += timemap[Capabilities.CLIMB_HIGH]
            return "Climbed high"

        # Priority 2: Score algae

        elif (
            self.cargo_algae == 1
            and Capabilities.ALGAE_NET in self.abilties
            and (time_left + self.time_debt) > timemap[Capabilities.ALGAE_NET]
        ):
            self.time_debt += timemap[Capabilities.ALGAE_NET]
            self.cargo_algae = 0
            return "Algae net"
        elif (
            self.cargo_algae == 1
            and Capabilities.ALGAE_PROC in self.abilties
            and (time_left + self.time_debt) > timemap[Capabilities.ALGAE_PROC]
        ):
            self.time_debt += timemap[Capabilities.ALGAE_PROC]
            self.cargo_algae = 0
            return "Algae proc"

        elif (
            self.cargo_algae == 0
            and Capabilities.ALGAE_2 in self.abilties
            and (time_left + self.time_debt) > timemap[Capabilities.ALGAE_2]
            and reef.take_algae(2)
        ):
            self.time_debt += timemap[Capabilities.ALGAE_2]
            self.cargo_algae = 1
            return "Algae 2"

        elif (
            self.cargo_algae == 0
            and Capabilities.ALGAE_3 in self.abilties
            and (time_left + self.time_debt) > timemap[Capabilities.ALGAE_3]
            and reef.take_algae(3)
        ):
            self.time_debt += timemap[Capabilities.ALGAE_3]
            self.cargo_algae = 1
            return "Algae 1"

        # Priority 3: Score coral
        elif (
            self.cargo_coral == 1
            and Capabilities.CORAL_4 in self.abilties
            and (time_left + self.time_debt) > timemap[Capabilities.CORAL_4]
            and reef.place_coral(4)
        ):
            self.time_debt += timemap[Capabilities.CORAL_4]
            self.cargo_coral = 0
            return "Coral 4"
        elif (
            self.cargo_coral == 1
            and Capabilities.CORAL_3 in self.abilties
            and (time_left + self.time_debt) > timemap[Capabilities.CORAL_3]
            and reef.place_coral(3)
        ):
            self.time_debt += timemap[Capabilities.CORAL_3]
            self.cargo_coral = 0
            return "Coral 3"
        elif (
            self.cargo_coral == 1
            and Capabilities.CORAL_2 in self.abilties
            and (time_left + self.time_debt) > timemap[Capabilities.CORAL_2]
            and reef.place_coral(2)
        ):
            self.time_debt += timemap[Capabilities.CORAL_2]
            self.cargo_coral = 0
            return "Coral 2"
            return
        elif (
            self.cargo_coral == 1
            and Capabilities.CORAL_1 in self.abilties
            and (time_left + self.time_debt) > timemap[Capabilities.CORAL_1]
            and reef.place_coral(1)
        ):
            self.time_debt += timemap[Capabilities.CORAL_1]
            self.cargo_coral = 0
            return "Coral 1"
            return

        # Intake coral

        elif (
            self.cargo_coral == 0
            and Capabilities.CORAL_FLOOR in self.abilties
            and (time_left + self.time_debt) > timemap[Capabilities.CORAL_FLOOR]
        ):
            self.time_debt += timemap[Capabilities.CORAL_FLOOR]
            self.cargo_coral = 1
            return "Coral floor"
        elif (
            self.cargo_coral == 0
            and Capabilities.CORAL_HP in self.abilties
            and (time_left + self.time_debt) > timemap[Capabilities.CORAL_HP]
        ):
            self.time_debt += timemap[Capabilities.CORAL_HP]
            self.cargo_coral = 1
            return "Coral HP"
        # Do nothing if all else fails
        else:
            return "passed"


def str_to_pts(str) -> float:
    match str:
        case "Coral 4":
            return 5
        case "Coral 3":
            return 4
        case "Coral 2":
            return 3
        case "Coral 1":
            return 2
        case "Algae net":
            return 4
        case "Algae proc":
            return 6 - (4 * HP_ACCURACY)
        case "Climbed low":
            return 12
        case "Climbed high":
            return 6
        case _:
            return 0


idiot_vec = [
    [
        Capabilities.CORAL_1,
        Capabilities.CORAL_2,
        Capabilities.CORAL_3,
        Capabilities.CORAL_4,
        Capabilities.ALGAE_PROC,
        Capabilities.ALGAE_NET,
        Capabilities.CLIMB_LOW,
        Capabilities.CLIMB_HIGH,
        Capabilities.CORAL_FLOOR,
        Capabilities.CORAL_HP,
        Capabilities.ALGAE_3,
        Capabilities.ALGAE_2,
    ],
    [Capabilities.CLIMB_LOW, Capabilities.CLIMB_HIGH],
    [
        Capabilities.ALGAE_NET,
        Capabilities.ALGAE_PROC,
        Capabilities.ALGAE_FLOOR,
        Capabilities.ALGAE_2,
        Capabilities.ALGAE_3,
    ],
    [Capabilities.CORAL_1, Capabilities.CLIMB_HIGH, Capabilities.CORAL_HP],
    [
        Capabilities.CORAL_1,
        Capabilities.CORAL_2,
        Capabilities.CORAL_3,
        Capabilities.CORAL_4,
        Capabilities.ALGAE_2,
        Capabilities.ALGAE_3,
        Capabilities.CORAL_HP,
    ],
    [
        Capabilities.CORAL_2,
        Capabilities.CORAL_3,
        Capabilities.CORAL_HP,
        Capabilities.ALGAE_3,
        Capabilities.ALGAE_2,
        Capabilities.ALGAE_PROC,
    ],
    [
        Capabilities.ALGAE_FLOOR,
        Capabilities.ALGAE_2,
        Capabilities.ALGAE_3,
        Capabilities.ALGAE_PROC,
        Capabilities.ALGAE_NET,
    ],
    [
        Capabilities.CORAL_3,
        Capabilities.CORAL_2,
        Capabilities.CORAL_4,
        Capabilities.CORAL_1,
        Capabilities.ALGAE_3,
        Capabilities.ALGAE_2,
        Capabilities.ALGAE_PROC,
        Capabilities.CORAL_HP,
    ],
    [
        Capabilities.CORAL_3,
        Capabilities.CORAL_2,
        Capabilities.CORAL_4,
        Capabilities.CORAL_1,
        Capabilities.ALGAE_3,
        Capabilities.ALGAE_2,
        Capabilities.ALGAE_NET,
    ],
    [
        Capabilities.CORAL_2,
        Capabilities.CORAL_1,
        Capabilities.ALGAE_3,
        Capabilities.ALGAE_2,
        Capabilities.ALGAE_PROC,
        Capabilities.ALGAE_NET,
    ],
    [
        Capabilities.CORAL_2,
        Capabilities.CORAL_4,
        Capabilities.CORAL_3,
        Capabilities.CORAL_1,
        Capabilities.CORAL_HP,
        Capabilities.CLIMB_HIGH,
    ],
    [
        Capabilities.CORAL_2,
        Capabilities.CORAL_4,
        Capabilities.CORAL_3,
        Capabilities.CORAL_1,
        Capabilities.CORAL_FLOOR,
        Capabilities.CLIMB_HIGH,
    ],
    [
        Capabilities.CORAL_2,
        Capabilities.CORAL_3,
        Capabilities.CORAL_HP,
    ],
    [
        Capabilities.CORAL_2,
        Capabilities.CORAL_1,
        Capabilities.ALGAE_2,
        Capabilities.ALGAE_PROC,
        Capabilities.CORAL_FLOOR,
    ],
]


retbuf = [[(137, "building the robot...", 0)]]


def sim():
    for i in idiot_vec:
        r1_abilties = i
        r2_abilties = []
        r3_abilties = []
        r1 = Robot(r1_abilties)
        r2 = Robot(r2_abilties)
        r3 = Robot(r3_abilties)

        time_left = 135
        r1_buf = [(136, "Connecting to FMS...", 0)]
        r2_buf = [(136, "Connecting to FMS...", 0)]
        r3_buf = [(136, "Connecting to FMS...", 0)]
        while time_left > 0:
            time_left -= 1
            r1out = r1.teleop(time_left)
            r1_buf.append((time_left, r1out, str_to_pts(r1out)))
        print("====================================")
        print(
            "Robot (",
            r1_abilties,
            ") scored ",
            sum(list(map(str_to_pts, r1_buf[1]))),
            " points",
        )
        print("====================================")
        retbuf.append(r1_buf)


sim()
inspect(retbuf)
with open("out.csv", "w", newline="") as csvfile:
    outwriter = csv.writer(
        csvfile, delimiter=" ", quotechar="|", quoting=csv.QUOTE_MINIMAL
    )
    num = 0
    for i in retbuf:
        outwriter.writerow(i)
