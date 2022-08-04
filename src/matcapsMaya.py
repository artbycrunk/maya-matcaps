import os
import maya.cmds as cmds
import glob

def load_path_from_file():
    script_path = os.path.dirname(os.path.abspath(__file__))
    try:
        with open('{0}/__matcaps_previous_dir__.txt'.format(script_path), 'r') as f:
            path = f.readlines()[0]
            if(os.path.isdir(path)):
                return path
        return ""
    except:
        print("No previous paths found")
        return ""
        
        
def write_path_to_file(path):
    script_path = os.path.dirname(os.path.abspath(__file__))
    try:
        with open('{0}/__matcaps_previous_dir__.txt'.format(script_path), 'w') as f:
            f.write(path)
    except:
        raise IOError("Unable to write to file {0}/__matcaps_previous_dir__.txt".format(script_path))


class MatcapShader():
    
    
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
            print(conn)
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


class MatcapBrowser():
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.window_name = "MatcapsForMaya"
        self.shader = MatcapShader(verbose=self.verbose)
        self.inputpath_textFieldButtonGrp = None
        self.matcap_textScrollList = None
        self.matcap_iconTextButton = None
        self.path = load_path_from_file()

        
    def change_preview(self):
        selectedIndex = cmds.textScrollList(
            self.matcap_textScrollList, q=True, si=1)
        if selectedIndex:
            fullpath = os.path.join(self.path, selectedIndex[0])
            self.shader.set_texture(fullpath)
            cmds.iconTextButton(self.matcap_iconTextButton,
                                e=True, image1=fullpath)        
        
    
    def write_icon_list(self, path):
        files = [os.path.basename(x) for x in glob.glob(
                os.path.join(path, "*.*")
                )]
        cmds.textScrollList(self.matcap_textScrollList,
                                e=True, append=files)
        return files
    
    
    def launch_filedialog(self):
        path = cmds.fileDialog2(fm=3)[0]
        if(path):
            self.write_icon_list(path)
            cmds.textFieldButtonGrp(self.inputpath_textFieldButtonGrp, e=True, text=path)
            self.path = path
            write_path_to_file(path)
            

    def show(self):
        if(cmds.window(self.window_name, q=True, ex=True)):
            cmds.delete(self.window_name)
            
        window = cmds.window(title="Matcaps for Maya",
                             iconName='Short Name',
                             widthHeight=(505, 315),
                             tlb=True, sizeable=False,
                             bgc=(0.3, 0.3, 0.3))

        cmds.columnLayout(adjustableColumn=True)
        cmds.text(l='MATCAPS FOR MAYA', h=30)
        cmds.separator(h=10)
        self.inputpath_textFieldButtonGrp = cmds.textFieldButtonGrp(l='Path', bl='...', text=self.path,
                                                                    bc=lambda: self.launch_filedialog())
        cmds.separator(h=10)
        cmds.rowColumnLayout(nc=2)

        self.matcap_textScrollList = cmds.textScrollList(
            w=300, sc=lambda: self.change_preview())
        self.matcap_iconTextButton = cmds.iconTextButton(
            style='iconOnly', image1=None, w=200, h=200)
        cmds.setParent('..')
        cmds.separator(h=10)
        cmds.button("Assign Shader", w=250, c=lambda x: self.shader.assign())
        
        if(self.path !=""):
            self.write_icon_list(self.path)
            
        cmds.showWindow(window)