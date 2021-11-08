from copy import deepcopy

data = { "plot" : [] }

class Object:
    pass

class Colorbar:
    def __init__(self):
        self.ax = Object()
        self.ax.set_title = self.set_title
        self.title = ""
    def set_title(self,title):
        self.title = title
    def __str__(self):
        return f"title : {self.title}"

def plot(x,y):
    data["plot"].append( ("plot",list(x),list(y),[]) )

def scatter(x,y,s=None,c=None):
    if c is not None:
        data["plot"].append( ("scatter",list(x),list(y),list(c)) )
    else:
        data["plot"].append( ("scatter",list(x),list(y),[]) )

def xlabel(label):
    data["xlabel"] = label

def ylabel(label):
    data["ylabel"] = label

def grid(grid):
    data["grid"] = grid

def colorbar():
    cb = Colorbar()
    data["colorbar"] = cb
    return cb

def set_cmap(cmap):
    data["colormap"] = cmap

def imshow(img):
    data["imshow"] = deepcopy(img)

def show():
    if "imshow" in data:
        img = data["imshow"]
        for r in img:
            print(",".join(f"{x:.2f}" for x in r))

    for p,x,y,c in data["plot"]:
        print(p,":")
        print(" x :", ",".join(f"{xi:.2f}" for xi in x))
        print(" y :", ",".join(f"{yi:.2f}" for yi in y))
        print(" c :", ",".join(f"{ci:.2f}" for ci in c))

    for k in sorted(data.keys()):
        if k in ["plot","imshow"]: continue
        print(k,":",data[k])
