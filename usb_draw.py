
import time
from turtle import pos
import pygame
import struct 
import io
from pcapng import FileScanner, blocks






CMDS = {
  3 : 'CMD_SERVO_MOVE',
}

BTN_STATE  = {
  2400 : 1,
  2300 : 0, 
}

MIDDLE_VALUE=1500


def convert_value(n):
  return n - MIDDLE_VALUE 
  # return ((n - MIDDLE_VALUE)/MIDDLE_VALUE) * 3.14 / 2

def read_fmt(stream, fmt="", into=None):
  sz = struct.calcsize(fmt)
  d = stream.read(sz)
  assert len(d) == sz, "Invalid read size"
  vals = struct.unpack(fmt, d)
  if len(vals) == 1:
    return vals[0]
  return vals


def _fade_pixel(px):
  rv = px
  for i in range(3):
    if px[i] > 20:
      px[i] -= 20
  return rv

def _fade_all():
  for i in range(500):
    for j in range(500):
      px = surface.get_at((i,j))
      if px[0] > 0:
        px = _fade_pixel(px)
        #print(px)
        surface.set_at((i,j),px)

def _draw_line(p1, p2):
  if p1 == p2:
    return
  #print('DRAW', p1, p2)
  pygame.draw.line(surface, color, p1, p2, 5 )
  pygame.display.flip()


SCREEN_OFFSET_X = 100
SCREEN_OFFSET_Y = 100

class LeArm:
  STATES = None
  prev_btn = None
  prev_point = [0,0]
  skip = 4

  def __init__(self):
    self.STATES = {}
    for i in range(1,7):
      self.STATES[i] = 0
  
  def update(self, servo, pos):
    self.STATES[servo] = pos
    self.draw_state()

  def draw_state(self):

    button = BTN_STATE[ self.STATES[1] ]  
    a1 = SCREEN_OFFSET_X +  -convert_value( self.STATES[2])
    a2 = SCREEN_OFFSET_Y + 200 - convert_value( self.STATES[3])
    was_switch = button != self.prev_btn
    self.prev_btn = button
    
    p1 = [a1,a2]
    p2 = self.prev_point

    draw = True

    if self.skip > 0:
      self.skip -=1 
      draw = False
    else:
      draw = button or was_switch

      
    if draw:
      _draw_line(p1, p2)
      print("DRAW")
    else:
      print("SKIP")

    self.prev_point = p1 

    _fade_all()
    #time.sleep(0.1)



ROBOT = LeArm()

def process_data(buf):
  
  direction = "i" if (buf[21]>1) else "o"
  data_size = struct.unpack("I",buf[23:27])[0]
  # print(direction, data_size)
  if direction != 'o' or data_size < 2:
    # print("SKIP 1")
    return
  stream = io.BytesIO(buf[27:])
  header = read_fmt(stream,"H")
  if header != 0x5555:
    # print("SKIP 2")
    return
  #print("WORK")
  size = read_fmt(stream, "b")
  cmd, num, time = read_fmt(stream, "bbh")
  print(f" > {CMDS.get(cmd)} x {num}  Time:{time}")

  for i in range(num):
    servo =  read_fmt(stream,"b")
    position =  read_fmt(stream,"h")
    print(f"  ID:{servo} POS:{position}")
    #STATES[servo] = position
    ROBOT.update(servo, position)
  
  #process_state(ts)


  
# Initializing Pygame
pygame.init()
surface = pygame.display.set_mode((600, 600))
color = (255,0,0)

with open(r'engraver.pcapng', 'rb') as fp:
  scanner = FileScanner(fp)
  for block in scanner:
    #print(block)
    #print(block.__class__)
    if type(block) == blocks.EnhancedPacket:
      process_data(block.packet_data)

