"""
MIT License

Copyright (c) 2020-2023 thatsOven

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame, numpy
from libs.sort   import sort
from libs.Vector import Vector
from pathlib     import Path

__circle_cache = {}
def __circlepoints(r):
    r = int(round(r))
    if r in __circle_cache:
        return __circle_cache[r]
    x, y, e = r, 0, 1 - r
    __circle_cache[r] = points = []
    while x >= y:
        points.append((x, y))
        y += 1
        if e < 0:
            e += 2 * y - 1
        else:
            x -= 1
            e += 2 * (y - x) - 1
    points += [(y, x) for x, y in points if x > y]
    points += [(-x, y) for x, y in points if x]
    points += [(x, -y) for x, y in points if y]
    sort(points)
    return points

def _renderOutlineText(text, font, color, outlineColor, opx):
    textsurface = font.render(text, True, color).convert_alpha()
    w = textsurface.get_width() + 2 * opx
    h = font.get_height()

    osurf = pygame.Surface((w, h + 2 * opx)).convert_alpha()
    osurf.fill((0, 0, 0, 0))

    surf = osurf.copy()

    osurf.blit(font.render(text, True, outlineColor).convert_alpha(), (0, 0))

    for dx, dy in __circlepoints(opx):
        surf.blit(osurf, (dx + opx, dy + opx))

    surf.blit(textsurface, (opx, opx))
    return surf


class Graphics:
    def __init__(self, resolution : Vector, framerate = 60, translated = Vector(0, 0), caption = "opal Graphics Window", backgroundColor = (0, 0, 0), showFps = False, fixedSize = True, font = pygame.font.get_default_font(), fontSize = 36, frequencySample = 48000, audioChannels = 1):
        pygame.mixer.pre_init(frequencySample, size = -16, channels = audioChannels)
        pygame.init()
        pygame.font.init()
        pygame.mixer.init(frequencySample, size = -16, channels = audioChannels)

        pygame.display.set_icon(
            pygame.image.load(
                os.path.join(str(Path(__file__).parent.absolute()), "icon.png")
            )
        )

        pygame.display.set_caption(caption)

        self.frequencySample = frequencySample

        self.resolution = resolution
        if fixedSize:
            self.screen = pygame.display.set_mode(self.resolution.toList(2))
        else:
            self.screen = pygame.display.set_mode(self.resolution.toList(2), pygame.RESIZABLE)

        self.font = pygame.font.SysFont(font, fontSize)
        self.__font = font

        self.caption = caption
        self.backgroundColor = backgroundColor

        self.center       = translated
        self.framerate    = framerate
        self.__clock      = pygame.time.Clock()
        self.__showFps    = showFps
        self.__updateSize = not fixedSize
        self.stopped    = False

        self.eventActions = {}

    def loopOnly(self):
        self.stopped = True

    def restore(self):
        self.stopped = False

    def getSysFont(self, font = None, size = 36):
        if font is None:
            return pygame.font.SysFont(self.__font, size)
        else: return pygame.font.SysFont(font, size)

    def getFont(self, font, size = 36):
        return pygame.font.Font(font, size)

    def getAudioChs(self):
        return pygame.mixer.get_init()

    def loadAudioFile(self, file):
        return pygame.mixer.Sound(file)

    def setResolution(self, resolution : Vector):
        self.resolution = resolution
        self.screen     = pygame.display.set_mode(self.resolution.toList(2))
        return self.screen

    def setCaption(self, caption, update=True):
        if update:
            self.caption = caption
        pygame.display.set_caption(caption)

    def translate(self, point : Vector):
        self.center += point

    def resetCenter(self):
        self.center = Vector(0, 0)

    def drawLoop(self): pass

    def update(self, func):
        self.drawLoop = func

    def run(self, draw = None, handleQuit = True, drawBackground = True, autoUpdate = True):
        if draw is not None:
            self.drawLoop = draw

        if handleQuit:
            def handle(ev):
                quit()
            self.eventActions[pygame.QUIT] = handle

        while True:
            if self.framerate is not None:
                self.__clock.tick(self.framerate)
            else:
                self.__clock.tick()

            if self.__updateSize:
                self.screen     = pygame.display.get_surface()
                self.resolution = Vector().fromList(self.screen.get_size())

            if self.__showFps:
                self.setCaption(self.caption + " - FPS: " + str(round(self.__clock.get_fps(), 3)), False)

            if drawBackground:
                self.screen.fill(self.backgroundColor)

            self.drawLoop()

            while self.stopped:
                self.drawLoop()
                
                for event in pygame.event.get():
                    if event.type in self.eventActions:
                        self.eventActions[event.type](event)

            for event in pygame.event.get():
                if event.type in self.eventActions:
                    self.eventActions[event.type](event)

            if autoUpdate:
                pygame.display.update()

    def getFps(self):
        return self.__clock.get_fps()

    def event(self, evType):
        def dec(func):
            self.eventActions[evType] = func
        return dec

    def getMousePos(self):
        return Vector().fromList(pygame.mouse.get_pos())

    def rawUpdate(self):
        pygame.display.update()

    def updateEvents(self):
        for event in pygame.event.get():
            if event.type in self.eventActions:
                self.eventActions[event.type](event)

    def forceDraw(self, handleQuit = True, drawBackground = True):
        if handleQuit:
            def handle(ev):
                quit()
            self.eventActions[pygame.QUIT] = handle

        self.updateEvents()

        pygame.display.update()

        if drawBackground:
            self.screen.fill(self.backgroundColor)

    def tick(self):
        if self.framerate is not None:
            self.__clock.tick(self.framerate)
        else:
            self.__clock.tick()

    def getEvents(self):
        return pygame.event.get()

    def hasQuit(self, returner = False):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if returner: return True
                quit()
        return False

    def setAt(self, pos : Vector, color, surf = None):
        if surf is None:
            surf = self.screen

        surf.set_at(pos.toList(2), color)

    def getAt(self, pos : Vector, surf = None):
        if surf is None:
            surf = self.screen

        return surf.get_at(pos.toList(2))

    def fill(self, color, surf = None):
        if surf is None:
            surf = self.screen

        surf.fill(color)

    def fillAlpha(self, color, alpha, surf = None):
        if surf is None:
            surf = self.screen

        alphaSurf = pygame.Surface(self.resolution.toList(2), pygame.SRCALPHA).convert_alpha()
        alphaSurf.fill(list(color) + [alpha])
        surf.blit(alphaSurf, (0, 0))

    def loadImage(self, imagePath, resolution = None):
        img = pygame.image.load(imagePath).convert_alpha()
        if resolution is not None:
            img = pygame.transform.scale(img, resolution.toList(2))
        return img

    def setIcon(self, surf):
        pygame.display.set_icon(pygame.transform.scale(surf, (32, 32)))

    def blitSurf(self, toBlit, position, surf = None):
        if surf is None:
            surf = self.screen

        surf.blit(toBlit, (position + self.center).toList(2))

    def line(self, pointA : Vector, pointB : Vector, color = (255, 255, 255), thickness = 1, surf = None):
        if surf is None:
            surf = self.screen

        pygame.draw.line(surf, color, (pointA + self.center).toList(2), (pointB + self.center).toList(2), thickness)

    def lines(self, points, color = (255, 255, 255), closed = True, thickness = 1, surf = None):
        if surf is None:
            surf = self.screen

        ptsCopy = []
        for i in range(len(points)):
            ptsCopy.append((points[i] + self.center).toList(2))

        pygame.draw.lines(surf, color, closed, ptsCopy, thickness)

    def rectangle(self, position : Vector, size : Vector, color = (255, 255, 255), thickness = 0, alpha = 255, fromCenter = False, surf = None):
        if surf is None:
            surf = self.screen
        
        lSize = size.toList(2)
        rectSurf = pygame.Surface(lSize)
        pygame.draw.rect(rectSurf, color, [0, 0] + lSize, thickness)
        rectSurf.set_alpha(alpha)

        if fromCenter:
            surf.blit(rectSurf, (position - (size // 2) + self.center).toList(2))
        else:
            surf.blit(rectSurf, (position + self.center).toList(2))

    def fastRectangle(self, position : Vector, size : Vector, color = (255, 255, 255), thickness = 0, fromCenter = False, surf = None):
        if surf is None:
            surf = self.screen

        if fromCenter:
            pygame.draw.rect(surf, color, (position - (size // 2) + self.center).toList(2) + size.toList(2), thickness)
        else:
            pygame.draw.rect(surf, color, (position + self.center).toList(2) + size.toList(2), thickness)

    def circle(self, center : Vector, radius, color = (255, 255, 255), alpha = 255, thickness = 0, surf = None):
        if surf is None:
            surf = self.screen

        circleSurf = pygame.Surface((radius * 2, radius * 2))
        pygame.draw.circle(circleSurf, color, (radius, radius), radius, thickness)
        circleSurf.set_alpha(alpha)
        surf.blit(circleSurf, (center - radius + self.center).toList(2))

    def fastCircle(self, center : Vector, radius, color = (255, 255, 255), thickness = 0, surf = None):
        if surf is None:
            surf = self.screen

        pygame.draw.circle(surf, color, (center + self.center).toList(2), radius, thickness)

    def polygon(self, points, color = (255, 255, 255), thickness = 0, surf = None):
        if surf is None:
            surf = self.screen

        ptsCopy = []
        for i in range(len(points)):
            ptsCopy.append((points[i] + self.center).toList(2))

        pygame.draw.polygon(surf, color, ptsCopy, thickness)

    def simpleText(self, text : str, pos : Vector, color = (255, 255, 255), centerX = False, centerY = False, font = None, surf = None):
        if surf is None:
            surf = self.screen

        if font is None:
            font = self.font

        cPos = pos.copy()

        s = font.render(text, True, color)
        r = s.get_rect()

        if centerX:
            cPos.x -= r.width // 2
        if centerY:
            cPos.y -= r.height // 2

        surf.blit(s, (cPos + self.center).toList(2))


    def drawText(self, text : list, pos : Vector, shadow = False, color = (255, 255, 255), shadowOffset = 4, font = None, surf = None):
        if surf is None:
            surf = self.screen

        if font is None:
            font = self.font

        origColor = color
        origPos   = pos.copy()

        if not shadow:
            shadowOffset = 0
        else:
            color = (0, 0, 0)

        intPos = pos.copy() + self.center

        for _ in range(2 if shadow else 1):
            for i in range(len(text)):
                surf.blit(font.render(text[i], True, color), (intPos + shadowOffset).toList(2))
                intPos.y += font.get_height()

            color        = origColor
            pos          = origPos.copy()
            shadowOffset = 0

    def drawOutlineText(self, text : list, pos : Vector, color = (255, 255, 255), outlineColor = (0, 0, 0), outlineSize = 2, font = None, surf = None):
        if surf is None:
            surf = self.screen
        
        if font is None:
            font = self.font

        intPos = pos.copy() + self.center

        for line in text:
            surf.blit(_renderOutlineText(line, font, color, outlineColor, outlineSize), intPos.toList(2))
            intPos.y += font.get_height()

    def playWaveforms(self, waveforms):
        for waveform in waveforms:
            pygame.sndarray.make_sound(waveform.astype(numpy.int16)).play()

    def stopSounds(self):
        pygame.mixer.stop()

    def stopPlay(self, waveforms):
        toPlay = []
        for waveform in waveforms:
            toPlay.append(pygame.sndarray.make_sound(waveform.astype(numpy.int16)))

        pygame.mixer.stop()

        for waveform in toPlay:
            waveform.play()

    def quit(self):
        pygame.quit()
