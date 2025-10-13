from enum import Enum

class NSFWOption(Enum):
    SHOW_EVERYTHING = "Show everything"
    ONLY_NSFW = "Only NSFW"
    BLOCK_NSFW = "Block NSFW"