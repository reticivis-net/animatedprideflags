import copy
import math
import typing
from typing import List, Tuple
import bezier
import numpy as np
import pyglet
import sympy
import webcolors

# pyglet.gl.glEnable(pyglet.gl.GL_LINE_SMOOTH)
pyglet.gl.glHint(pyglet.gl.GL_LINE_SMOOTH_HINT, pyglet.gl.GL_NICEST)
config = pyglet.gl.Config(sample_buffers=1, samples=4)  #
window = pyglet.window.Window(vsync=1, config=config, width=500, height=500, visible=False, resizable=True)


class FlagStripe:
    def __str__(self):
        return f"<FlagStripe color={self.color} size={self.size}>"

    def __init__(self, color, size):
        self.color: Tuple[int, int, int] = color
        self.size: float = size

    def split(self, times=2):
        return [FlagStripe(self.color, self.size / times)] * times


class Flag:
    def __str__(self):
        return f"<Flag stripes={len(self)} name={self.name} images={len(self.images)}>"

    def __len__(self):
        return len(self.stripes)

    def __init__(self, stripes: List[typing.Union[FlagStripe, tuple, str]],
                 images: List[typing.Union[pyglet.sprite.Sprite, str]] = [], name: str = "unnamed", reverse=False):
        self.stripes: List[FlagStripe] = []
        for s in stripes:
            if isinstance(s, FlagStripe):
                self.stripes.append(s)
            elif isinstance(s, tuple):
                self.stripes.append(FlagStripe(s, 1 / len(stripes)))
            elif isinstance(s, str):
                if not s.startswith("#"):
                    s = "#" + s
                self.stripes.append(FlagStripe(webcolors.hex_to_rgb(s), 1 / len(stripes)))
            else:
                raise Exception("what")
        if reverse:
            self.stripes.reverse()
        self.images: List[pyglet.sprite.Sprite] = []
        for im in images:
            if isinstance(im, pyglet.sprite.Sprite):
                self.images.append(im)
            else:
                pic = pyglet.image.load(im)
                self.images.append(pyglet.sprite.Sprite(pic))
        self.name: str = name

    def draw(self):
        background = pyglet.graphics.OrderedGroup(0)
        foreground = pyglet.graphics.OrderedGroup(1)
        batch = pyglet.graphics.Batch()
        shapes = []
        current_height = 0
        for fs in self.stripes:
            shapes.append(pyglet.shapes.Rectangle(0, current_height, window.width, window.height * fs.size,
                                                  color=(int(fs.color[0]), int(fs.color[1]), int(fs.color[2])),
                                                  batch=batch, group=background))
            current_height += window.height * fs.size
        sprites = []
        for im in self.images:
            im2 = pyglet.sprite.Sprite(im.image, batch=batch, group=foreground)
            im2.opacity = im.opacity
            im2.scale = window.height / im.height
            im2.x = (window.width - im2.width) // 2
            sprites.append(im2)
        # print(self.images)
        batch.draw()
        # batch.invalidate()

    def split(self, num_of_stripes: int):
        assert num_of_stripes > len(self.stripes)
        split_by = math.ceil(num_of_stripes / len(self.stripes))
        new_stripes_to_add = num_of_stripes - len(self.stripes)
        output = []
        for stripe in self.stripes:
            if new_stripes_to_add >= split_by:
                output += stripe.split(split_by)
                new_stripes_to_add -= split_by - 1
            elif new_stripes_to_add > 0:
                output += stripe.split(new_stripes_to_add + 1)
                new_stripes_to_add = 0
            else:
                output.append(stripe)
        return Flag(output, images=self.images, name=self.name)


def transition(start: float, end: float, percent: float) -> float:
    percent = max(min(percent, 1), 0)
    # beizerify
    if beizer:
        percent = beizerexpr.subs(sympy.Symbol("x"), percent)
    # linear
    return start * (1 - percent) + end * percent


def transition_flags(flag1: Flag, flag2: Flag, percent: float) -> Flag:
    outflag = []
    for i, stripe1 in enumerate(flag1.stripes):
        stripe2 = flag2.stripes[i]
        newcolors = (
            transition(stripe1.color[0], stripe2.color[0], percent),
            transition(stripe1.color[1], stripe2.color[1], percent),
            transition(stripe1.color[2], stripe2.color[2], percent)
        )
        newsize = transition(stripe1.size, stripe2.size, percent)
        outflag.append(FlagStripe(newcolors, newsize))
    images = []
    if flag1.images:
        for image in flag1.images:
            image.opacity = int(255 * (1 - percent))
            images.append(image)
    if flag2.images:
        for image in flag2.images:
            image.opacity = int(255 * percent)
            images.append(image)
    return Flag(outflag, images=images, name=f"{flag1.name}->{flag2.name} {round(percent * 100)}%")


def update(frame_delta):
    global current_time
    global draw_flag
    current_index = math.floor(current_time / time_to_transition)
    next_index = current_index + 1
    while current_index >= len(flags):
        if render:
            pyglet.app.exit()
        current_index -= len(flags)
    while next_index >= len(flags):
        next_index -= len(flags)
    # print(current_index)
    current_flag = flags[current_index]
    next_flag = flags[next_index]
    percent_between_flags = current_time / time_to_transition % 1
    if len(current_flag) > len(next_flag):
        next_flag = next_flag.split(len(current_flag))
    elif len(current_flag) < len(next_flag):
        current_flag = current_flag.split(len(next_flag))
    draw_flag = transition_flags(current_flag, next_flag, percent_between_flags)
    if render:
        current_time += 1.0 / 60
    else:
        current_time += frame_delta


@window.event
def on_draw():
    global frame
    global draw_flag
    # window.clear()
    draw_flag.draw()
    if render:
        pyglet.image.get_buffer_manager().get_color_buffer().save(f"render/frame{frame}.png")
        print(f"saving render/frame{frame}.png")
    frame += 1


beizer = True
render = True
if beizer:
    nodes1 = np.asfortranarray([
        [0, .5, .5, 1],
        [0, 0, 1, 1],
    ])
    curve1 = bezier.Curve.from_nodes(nodes1)
    beizerexpr = curve1.implicitize()
    beizerexpr = sympy.solve(beizerexpr, sympy.Symbol("y"))[0]
flags = [
    Flag(["#e40303", "#ff8c00", "#ffed00", "008026", "004dff", "750787"], name="gay", reverse=True),  # gay
    Flag(["55cdfc", "f7a8b8", "ffffff", "f7a8b8", "55cdfc"], name="trans", reverse=True),  # trans
    Flag(["#FE218B", "fed700", "21b0fe"], name="pan", reverse=True),  # pan
    Flag(["#CD0067", "#CD0067", "#993399", "#003399", "#003399"], name="bi", reverse=True),  # bi
    Flag(["#FDF433", "#ffffff", "#9A5ACF", "#2D2E2C"], name="NB", reverse=True),  # NB
    Flag(["#018E70", "#9AE9C3", "#ffffff", "#7CAFE4", "#3C1379"], name="vincian", reverse=True),  # vincian
    Flag(["#000000", "#A3A3A3", "#ffffff", "#800080"], name="ace", reverse=True),  # ace
    Flag(["d42c00", "fd9855", "ffffff", "d161a2", "a20161"], name="lesbiab", reverse=True),  # lesbiab
    Flag(["fe8ca9", "ffffff", "fe8ca9"], name="sapphic", reverse=True, images=["sapphic-flower.png"]),
    Flag(["3ca542", "a8d377", "fefefe", "a9a9a9", "000000"], name="aro", reverse=True),  # aro
    Flag(["99c6e9", "ffffff", "99c6e9"], name="achillean", reverse=True, images=["achillean-flower.png"]),
    Flag(["ff76ae", "ffafd0", "c876ff", "b0d5ff", "77bcff"], name="xenogender", reverse=True),  # xenogender
    Flag(["ffffff", "ffffff", "6c016e", "d2d2d2", "d2d2d2"], name="demisexual", reverse=True,
         images=["demisexual-triangle.png"]),

]
current_time = 0
frame = 0
print([str(f) for f in flags])
time_to_transition = 1
draw_flag = flags[0]
# pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
window.set_visible()
pyglet.clock.schedule(update)
pyglet.app.run()
