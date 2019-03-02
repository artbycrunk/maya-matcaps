import os
import maya.cmds as cmds
import glob


class MapcapShader(object):
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.shader, self.filenode = self.create()

    def create_node(self, nodetype, name):
        if nodetype in ["surfaceShader"]:
            return cmds.shadingNode(nodetype, n=name, asShader=True)
        if nodetype in ["envBall", "file"]:
            return cmds.shadingNode(nodetype, n=name, asTexture=True)
        if nodetype in ["place2dTexture", "place3dTexture"]:
            return cmds.shadingNode(nodetype, n=name, asUtility=True)
        return False

    def connect_attr(self, conn):
        if self.verbose:
            print conn
        cmds.connectAttr("%s.%s" % (conn[0], conn[2]),
                         "%s.%s" % (conn[1], conn[3]), force=True)

    def create(self):
        shader = self.create_node("surfaceShader", "matCapShader")
        envball = self.create_node("envBall", "matCapBall")
        texture3D = self.create_node("place3dTexture", "matCapTexturePlacer3d")
        texture2D = self.create_node("place2dTexture", "matCapTexturePlacer2d")
        filenode = self.create_node("file", "matCapFile")

        connections = [
            [texture3D, envball, 'worldInverseMatrix', 'placementMatrix'],
            [envball, shader, 'outColor'],
            [[texture2D, filenode], [
                'coverage', 'translateFrame', 'rotateFrame', 'mirrorU',
                'mirrorV', 'stagger', 'wrapU', 'wrapV', 'repeatUV', 'offset',
                'rotateUV', 'noiseUV', 'uv', 'uvFilterSize']],
            [filenode, envball, 'outColor', 'image'],
        ]

        for conn in connections:
            if isinstance(conn[0], list):
                for attr in conn[1]:
                    _conn = [conn[0][0], conn[0][1], attr, attr]
                    self.connect_attr(_conn)
            else:
                if not len(conn) == 4:
                    conn.append(conn[2])
                self.connect_attr(conn)

        cmds.setAttr("%s.filterType" % filenode, 0)
        cmds.setAttr("%s.eyeSpace" % envball, 1)
        return shader, filenode

    def set_texture(self, imagename):
        cmds.setAttr("%s.fileTextureName" % self.filenode,
                     str(imagename), type="string")

    def assign(self):
        meshes = cmds.ls(sl=True)
        for mesh in meshes:
            cmds.hyperShade(a=self.shader)


class MatcapBroswer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.window = None
        self.shader = MapcapShader(verbose=self.verbose)
        self.inputpath = None
        self.matcap_textScrollList = None
        self.matcap_iconTextButton = None

    def getpath(self):
        return cmds.textField(self.inputpath, q=True, text=True)

    def fetch_files(self):
        path = self.getpath()

        if not path:
            print "Please select a path to browse matcaps"
            return False

        files = [os.path.basename(x)
                 for x in glob.glob(os.path.join(path, "*.*"))]
        cmds.textScrollList(self.matcap_textScrollList,
                            e=True, append=files)

    def change_preview(self):
        path = self.getpath()
        selectedIndex = cmds.textScrollList(
            self.matcap_textScrollList, q=True, si=1)
        if selectedIndex:
            fullpath = os.path.join(path, selectedIndex[0])
            self.shader.set_texture(fullpath)
            cmds.iconTextButton(self.matcap_iconTextButton,
                                e=True, image1=fullpath)

    def show(self):
        if not self.window:
            self.build()
        cmds.showWindow(self.window)

    def build(self):
        self.window = cmds.window(title="Matcaps for Maya",
                                  iconName='Short Name',
                                  widthHeight=(505, 315),
                                  tlb=True, sizeable=False,
                                  bgc=(0.3, 0.3, 0.3))

        cmds.columnLayout(adjustableColumn=True)
        cmds.iconTextStaticLabel(st='textOnly', l='MATCAPS FOR MAYA', h=30)
        cmds.separator(h=10)
        cmds.rowColumnLayout(nc=3)
        cmds.iconTextStaticLabel(st='textOnly', l='Path', w=50)
        self.inputpath = cmds.textField(w=350, bgc=(0.5, 0.5, 0.5))
        cmds.button("Fetch Matcaps", w=100, c=lambda x: self.fetch_files())
        cmds.setParent("..")
        cmds.separator(h=10)
        cmds.rowColumnLayout(nc=2)

        self.matcap_textScrollList = cmds.textScrollList(
            w=300, sc=lambda: self.change_preview())
        self.matcap_iconTextButton = cmds.iconTextButton(
            style='iconOnly', image1=None, w=200, h=200)
        cmds.setParent('..')
        cmds.separator(h=10)
        cmds.button("Assign Shader", w=250, c=lambda x: self.shader.assign())
