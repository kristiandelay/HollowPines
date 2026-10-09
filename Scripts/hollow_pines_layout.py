"""Blackwater Reach prototype layout in metres; +X east, +Y north, +Z up.

Shared by terrain, PCG seed points, trails, caves and validation. Change the seed
or coordinates here and run Build-BlackwaterReach.py in the editor to regenerate.
"""
import math
import random

SEED=731905
EXTENT=500.0
POIS={
    'Start Camp':(55,-5,32), 'Abandoned Cabin':(-220,235,22),
    'River Crossing':(-135,-230,20), 'Radio Tower':(245,-165,23),
    'Logging Site':(-265,-15,35), 'Old Mine':(255,120,26),
    'North Lake':(-120,365,16), 'Cliff Lookout':(255,320,22),
    'Swamp':(260,-315,28), 'South Exit':(-240,-430,18),
}
TRAILS=[
    ('Camp to Mine',[(55,-5),(115,35),(185,55),(255,120)]),
    ('Camp to Radio',[(55,-5),(100,-65),(160,-135),(245,-165)]),
    ('Camp to Crossing',[(55,-5),(60,-110),(0,-200),(-135,-230)]),
    ('West Logging Trail',[(-135,-230),(-225,-180),(-300,-90),(-265,-15)]),
    ('Cabin Trail',[(-265,-15),(-300,90),(-220,235)]),
    ('Cabin to Lake',[(-220,235),(-140,285),(-135,340),(-120,365)]),
    ('North Camp Trail',[(55,-5),(95,100),(60,205),(120,275),(155,365)]),
    ('Cliff Ascent',[(255,120),(190,160),(235,215),(180,260),(255,320)]),
    ('Lake to Lookout',[(-120,365),(-120,400),(-95,440),(65,435),(155,365),(255,320)]),
    ('Swamp Trail',[(245,-165),(315,-220),(300,-280),(260,-315)]),
    ('South Exit Trail',[(-135,-230),(-230,-300),(-280,-365),(-240,-430)]),
    ('West Ford',[(-265,-15),(-175,-55),(-75,-70),(55,-5)]),
]

def smooth(x):
    x=max(0,min(1,x));return x*x*(3-2*x)

def river_x(y):
    return -75 + 26*math.sin((y+70)/90) - max(0,-y-80)*.17

def river_water_z(y):
    return 8+(y+500)*.055

def lake_distance(x,y):
    return math.sqrt(((x-0)/84)**2+((y-348)/67)**2)

def swamp_distance(x,y):
    return math.sqrt(((x-275)/65)**2+((y+325)/75)**2)

def base_height(x,y):
    h=26+(y+500)*.04
    h+=70*math.exp(-((x-310)**2/125**2+(y-260)**2/190**2))
    h+=42*math.exp(-((x+335)**2/145**2+(y-220)**2/270**2))
    h+=65*(smooth((abs(x)-380)/120)+smooth((abs(y)-415)/100))
    h+=5*math.sin(x/47)*math.cos(y/61)+2.2*math.sin(x/16+y/31)
    distance=abs(x-river_x(y))
    if y<322:
        factor=1-smooth((distance-9)/29)
        h=h*(1-factor)+(river_water_z(y)-2.5)*factor
    ld=lake_distance(x,y)
    if ld<1.38:
        factor=1-smooth((ld-.88)/.5)
        h=h*(1-factor)+(river_water_z(320)-4)*factor
    sd=swamp_distance(x,y)
    if sd<1.3:
        factor=1-smooth((sd-.85)/.45)
        h=h*(1-factor)+18*factor
    return h

def segment(x,y,a,b):
    dx=b[0]-a[0];dy=b[1]-a[1]
    t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/max(.0001,dx*dx+dy*dy)))
    return math.hypot(x-a[0]-t*dx,y-a[1]-t*dy),t

POI_HEIGHTS={name:base_height(x,y) for name,(x,y,r) in POIS.items()}
POI_HEIGHTS['River Crossing']=max(base_height(river_x(-230)+32,-230),base_height(river_x(-230)-32,-230))+.6

def trail_height(point):
    for name,(x,y,r) in POIS.items():
        if point==(x,y):return POI_HEIGHTS[name]
    return base_height(*point)

def trail_edges(a,b):
    length=math.dist(a,b)
    radii={point[:2]:point[2] for point in POIS.values()}
    # Hold the trail level inside a clearing, then grade the remaining distance.
    ra=radii.get(a,0);rb=radii.get(b,0)
    edge_a=tuple(a[k]+(b[k]-a[k])*ra/length for k in range(2))
    edge_b=tuple(b[k]+(a[k]-b[k])*rb/length for k in range(2))
    za,zb=trail_height(a),trail_height(b)
    return [(a,edge_a,za,za),(edge_a,edge_b,za,zb),(edge_b,b,zb,zb)]

TRAIL_SEGMENTS=[s for _,points in TRAILS for a,b in zip(points,points[1:]) for s in trail_edges(a,b) if math.dist(s[0],s[1])>.01]

def trail_distance(x,y):
    return min(segment(x,y,a,b)[0] for a,b,_,_ in TRAIL_SEGMENTS)

def height(x,y):
    h=base_height(x,y)
    for name,(px,py,radius) in POIS.items():
        if name in ['Swamp','River Crossing']:continue
        d=math.hypot(x-px,y-py)
        if d<radius+12:
            weight=1-smooth((d-radius)/12)
            h=h*(1-weight)+POI_HEIGHTS[name]*weight
    # Gentle authored trail beds preserve grades across the ridges.
    closest=None
    for a,b,za,zb in TRAIL_SEGMENTS:
        d,t=segment(x,y,a,b)
        if closest is None or d<closest[0]:closest=(d,za+(zb-za)*t)
    d,z=closest
    if d<7 and (abs(x-river_x(y))>12 or y>322):
        weight=1-smooth((d-2.8)/4.2)
        h=h*(1-weight)+z*weight
    return h

MINE_Z=height(255,120)
EXIT_Z=height(305,-260)
CAVES=[
    ('Mine Descent',[(248,114,MINE_Z),(270,128,MINE_Z-3),(295,110,MINE_Z-10),(325,72,MINE_Z-23),(330,18,MINE_Z-40)],5.5,7),
    ('Lake Passage',[(330,18,MINE_Z-40),(312,-35,MINE_Z-55),(310,-90,MINE_Z-70),(333,-135,MINE_Z-65)],6.5,8),
    ('Swamp Escape',[(333,-135,MINE_Z-65),(365,-175,EXIT_Z-12),(345,-222,EXIT_Z-4),(305,-260,EXIT_Z)],5,6),
    ('Collapsed Branch',[(312,-35,MINE_Z-55),(365,-40,MINE_Z-52),(390,-8,MINE_Z-48)],4,5.5),
]

def near_cave_opening(x,y,z):
    for points,width,roof in [(CAVES[0][1][:2],6.8,9),(CAVES[2][1][-2:],6.8,9)]:
        a,b=points
        d,t=segment(x,y,a,b);floor=a[2]+(b[2]-a[2])*t
        if d<width and floor-2<z<floor+roof:return True
    return False

def vegetation_allowed(x,y,clearance=0):
    if abs(x)>EXTENT-12 or abs(y)>EXTENT-12:return False
    if y<322 and abs(x-river_x(y))<18+clearance:return False
    if lake_distance(x,y)<1.13 or swamp_distance(x,y)<1.12:return False
    if trail_distance(x,y)<4+clearance:return False
    for px,py,r in POIS.values():
        if math.hypot(x-px,y-py)<r+clearance:return False
    z=height(x,y)
    if near_cave_opening(x,y,z):return False
    slope=math.hypot(height(x+1,y)-height(x-1,y),height(x,y+1)-height(x,y-1))/2
    return slope<.65

def scatter(spacing,clearance,seed=SEED):
    rng=random.Random(seed)
    result=[]
    steps=int(2*EXTENT/spacing)
    for i in range(steps):
        for j in range(steps):
            x=-EXTENT+(i+.5+rng.uniform(-.34,.34))*spacing
            y=-EXTENT+(j+.5+rng.uniform(-.34,.34))*spacing
            yaw=rng.uniform(0,360);scale=rng.uniform(.78,1.22)
            if vegetation_allowed(x,y,clearance):result.append((x,y,height(x,y),yaw,scale))
    return result
