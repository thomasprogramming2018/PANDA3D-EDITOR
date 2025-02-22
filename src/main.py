from QPanda3D.Panda3DWorld import Panda3DWorld
from QPanda3D.QPanda3DWidget import QPanda3DWidget
from QPanda3D.Helpers.Env_Grid_Maker import *
# import PyQt5 stuff
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys
from panda3d.core import *
from direct.interval.LerpInterval import LerpHprInterval
from direct.interval.IntervalGlobal import *
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.DirectObject import DirectObject
import ui_editor
#from camera import FlyingCamera
import node
from shader_editor import ShaderEditor
from file_explorer import FileExplorer
import terrainEditor
import importlib
import os
import entity_editor
#import node_system
from PyQt5.QtCore import pyqtSignal
from scirpt_inspector import ScriptInspector
import scirpt_inspector
#import qdarktheme
from direct.gui.DirectGui import DirectButton, DirectLabel, DirectFrame
from direct.gui import DirectGuiGlobals as DGG
import input_manager
from input_manager import NetworkManager, InputManager
import uuid
import sequence_editor as sequenceEditorTab
import raycasting
import Preview_build
from terrain_control_widget import TerrainControlWidget
import gizmos

class PandaTest(Panda3DWorld):
    def __init__(self, width=1024, height=768, script_inspector=None):
        Panda3DWorld.__init__(self, width=width, height=height)
        
        self.setupRender2d()
        global network_manager
        global input_manager_c
        self.network_manager = network_manager
        self.input_manager = input_manager_c
        
        self.animator_tab = sequenceEditorTab.SequenceEditorTab(self)
        
        self.gizmos = gizmos.GizmoDemo(self)
        
        
        #self.raycasting.set_gizmos(self.animator_tab.gizmo_parent)
        

        
        self.canvas = NodePath("UI-Canvas")
        self.canvas.reparent_to(self.render2d)
        
        self.canvas.set_python_tag("isCanvas", True)
        self.canvas.set_python_tag("isLabel", False)
        
        self.canvas.setPythonTag("widget_type", "c")
        
        self.canvas.setPos(0, 0, 255)
        # Set up the orthographic camera
        self.ortho_cam = self.makeCamera(self.win)
        lens = OrthographicLens()
        lens.setFilmSize(20, 15)  # Adjust the size as needed
        self.ortho_cam.node().setLens(lens)
        self.ortho_cam.reparentTo(self.render)
        self.ortho_cam.setPos(0, 0, 0)
        
        self.script_inspector = script_inspector
        self.loader = self.loader
        #self.camera_controls = FlyingCamera(self)
        self.cam.setPos(0, -58, 30)
        self.cam.setHpr(0, -30, 0)
        self.win.setClearColorActive(True)
        self.win.setClearColor(VBase4(0, 0, 0, 1))
        self.cam.node().getDisplayRegion(0).setSort(20)
        # Create a panda        
        self.panda = loader.loadModel("panda")
        self.panda.set_python_tag("model_path", "panda")
        
        self.assign_id(self.panda)
        self.panda.reparentTo(render)
        self.panda.setPos(0, 0, 0)

        self.grid_maker = Env_Grid_Maker()
        self.grid = self.grid_maker.create()
        self.grid.reparentTo(render)
        self.grid.setLightOff()  # THE GRID SHOULD NOT BE LIT
        
        self.selected_node = None

        # Now create some lights to apply to everything in the scene.

        # Create Ambient Light
        ambientLight = AmbientLight('ambientLight')
        ambientLight.setColor(Vec4(0.1, 0.1, 0.1, 1))
        ambientLightNP = render.attachNewNode(ambientLight)
        render.setLight(ambientLightNP)

        # Directional light 01
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setColor(Vec4(0.8, 0.1, 0.1, 1))
        directionalLightNP = render.attachNewNode(directionalLight)
        # This light is facing backwards, towards the camera.
        directionalLightNP.setHpr(180, -20, 0)
        directionalLightNP.setPos(10, -100, 10)
        render.setLight(directionalLightNP)

        # If we did not call setLightOff() first, the green light would add to
        # the total set of lights on this object.  Since we do call
        # setLightOff(), we are turning off all the other lights on this
        # object first, and then turning on only the green light.
        self.panda.setLightOff()
        self.jump_up = self.panda.posInterval(1.0, Point3(0, 0, 5), blendType="easeOut")
        self.jump_down = self.panda.posInterval(1.0, Point3(0, 0, 0), blendType="easeIn")
        self.jump_seq = Sequence(self.jump_up, self.jump_down)
 
        self.jump_up2 = self.panda.posInterval(1.0, Point3(10, 0, 15))
        self.jump_down2 = self.panda.posInterval(1.0, Point3(0, 0, 0))
        self.roll_left = self.panda.hprInterval(1.0, Point3(0, 0, 180))
        self.roll_right = self.panda.hprInterval(1.0, Point3(0, 0, 0))
        self.roll_seq = Sequence(Parallel(self.jump_up2, self.roll_left), Parallel(self.jump_down2, self.roll_right))
    
    def recreate_widget(self, text, frameColor, text_fg, scale, pos, parent):
        return uiEditor_inst.label(text, scale, pos, parent, frameColor, text_fg)
    def recreate_button(self, text, frameColor, text_fg, scale, pos, parent):
        return uiEditor_inst.button(text, scale, pos, parent, frameColor, text_fg)
    def make_hierarchy(self):
        self.hierarchy_tree = QTreeWidget()
        self.hierarchy_tree1 = QTreeWidget()
        
    
    def make_ray_caster(self):
        self.raycasting = raycasting.Picker(self)
    
    def assign_id(self, nodepath: NodePath):
        nodepath.set_python_tag("scripts", {})
        nodepath.set_python_tag("script_paths", [])
        nodepath.set_python_tag("script_properties", [])
        nodepath.set_python_tag("id", str(uuid.uuid4())[:8])

    def jump(self):
        self.jump_seq.start()

    def roll(self):
        self.roll_seq.start()
        
    def refresh(self):
        self.hierarchy_tree.clear()
        self.populate_hierarchy(self.hierarchy_tree, render)
        self.hierarchy_tree1.clear()
        self.populate_hierarchy(self.hierarchy_tree1, self.render2d)

    def add_model(self, model):


        self.hierarchy_tree.clear()
        self.populate_hierarchy(self.hierarchy_tree, render)
        self.hierarchy_tree1.clear()
        self.populate_hierarchy(self.hierarchy_tree1, self.render2d)
        world.selected_node = model
        self.assign_id(model)

    def make_terrain(self):


        self.hierarchy_tree.clear()
        self.hierarchy_tree1.clear()

        self.terrain_generate = terrainEditor.TerrainPainterApp(world, pandaWidget)

        world.selected_node = self.terrain_generate.terrain_node
        
        self.populate_hierarchy(self.hierarchy_tree, render)
        self.populate_hierarchy(self.hierarchy_tree1, self.render2d)

        selected_node = self.terrain_generate.terrain_node
    #def ui_editor_script_to_canvas(self):
    #    inspector.set_script(os.path.relpath("D:/000PANDA3d-EDITOR/PANDA3D-EDITOR/ui_editor_properties.py"), self.canvas, inspector.prop)
    def reset_render(self):
        """
        Resets the render node to a new NodePath.
        """
        global render  # Make the new NodePath the global render
        old_render = render

        # Create a new root node
        render = NodePath("render")
        base.render = render  # Update ShowBase's render reference

        # Reparent global elements like the camera
        base.camera.reparent_to(render)

        # Detach the old render node (optional)
        old_render.detach_node()

        #self.camera_controls = FlyingCamera(self)
        self.cam.setPos(0, -58, 30)
        self.cam.setHpr(0, -30, 0)
        self.win.setClearColorActive(True)
        self.win.setClearColor(VBase4(0, 0, 0, 1))
        self.cam.node().getDisplayRegion(0).setSort(20)

        self.hierarchy_tree.clear()
        self.hierarchy_tree1.clear()
        
        self.populate_hierarchy(self.hierarchy_tree, self.render)
        self.populate_hierarchy(self.hierarchy_tree1, self.render2d)
    #TODO make each object from toml load up with a function that runs on load


    def populate_hierarchy(self, hierarchy_widget, node, parent_item=None):

        # Create a new item for the current node
        item = QTreeWidgetItem(parent_item or hierarchy_widget, [node.getName()])
        item.setData(0, Qt.UserRole, node)  # Store the NodePath in the item data
        # Recursively add child nodes
        for child in node.getChildren():
            self.populate_hierarchy(hierarchy_widget, child, item)



class properties:
    def __init__():
        pass
    def update_node_property(self, coord):
        print(f"update_node_property called with coord: {coord}")
        if coord not in input_boxes:
            print(f"Error: {coord} not found in input_boxes. Current keys: {list(input_boxes.keys())}")
            return
        value = float(input_boxes[coord].text())
        if not world.selected_node:
            return
        try:
            value = float(input_boxes[coord].text())
        except ValueError:
            return  # Ignore invalid inputs

        if coord[0] == 0:  # Translation
            pos = list(world.selected_node.getPos())
            pos[coord[1]] = value
            world.selected_node.setPos(*pos)
        elif coord[0] == 1:  # Rotation
            hpr = list(world.selected_node.getHpr())
            hpr[coord[1]] = value
            world.selected_node.setHpr(*hpr)
        elif coord[0] == 2:  # Scale
            scale = list(world.selected_node.getScale())
            scale[coord[1]] = value
            world.selected_node.setScale(*scale)
class properties_ui_editor:
    def __init__():
        pass
    def update_node_property(self, coord):
        print(f"update_node_property called with coord: {coord}")
        if coord not in uiEditor_inst.input_boxes:
            print(f"Error: {coord} not found in input_boxes. Current keys: {list(uiEditor_inst.input_boxes.keys())}")
            return
        value = float(uiEditor_inst.input_boxes[coord].text())
        if not world.selected_node:
            return
        try:
            value = float(uiEditor_inst.input_boxes[coord].text())
        except ValueError:
            return  # Ignore invalid inputs

        if coord[0] == 0:  # Translation
            pos = list(world.selected_node.getPos())
            pos[coord[1]] = value
            world.selected_node.setPos(*pos)
        elif coord[0] == 1:  # Rotation
            hpr = list(world.selected_node.getHpr())
            hpr[coord[1]] = value
            world.selected_node.setHpr(*hpr)
        elif coord[0] == 2:  # Scale
            scale = list(world.selected_node.getScale())
            scale[coord[1]] = value
            world.selected_node.setScale(*scale)

def on_item_clicked(item, column):
    #global selected_node
    node = item.data(0, Qt.UserRole)  # Retrieve the NodePath stored in the item

    if node:
        world.selected_node = node
        # Update input boxes with node's properties
        input_boxes[(0, 0)].setText(str(node.getX()))
        input_boxes[(0, 1)].setText(str(node.getY()))
        input_boxes[(0, 2)].setText(str(node.getZ()))
        input_boxes[(1, 0)].setText(str(node.getH()))
        input_boxes[(1, 1)].setText(str(node.getP()))
        input_boxes[(1, 2)].setText(str(node.getR()))
        input_boxes[(2, 0)].setText(str(node.getScale().x))
        input_boxes[(2, 1)].setText(str(node.getScale().y))
        input_boxes[(2, 2)].setText(str(node.getScale().z))

        # Clear existing widgets in the ScriptInspector
        for i in reversed(range(inspector.scroll_layout.count())):
            widget = inspector.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                
<<<<<<< Updated upstream
        if node.get_python_tag("isTerrain"):
            control_widget.show()
        else:
            control_widget.hide()
                
        
=======
        if node.get_python_tag("isTerrain") == True:
            control_widget.show()
        else:
            control_widget.hide()
>>>>>>> Stashed changes
        
        world.gizmos.gizmo_root.set_pos(node.get_pos())

        
        inspector.recreate_property_box_for_node(node)
        
        ## Load scripts associated with the node
        #if node in inspector.scripts:
        #    for path, script_instance in inspector.scripts[node].items():
        #        if inspector.prop:
        #            
        #            inspector.set_script(path, node, inspector.prop)
        #else:
        #    inspector.scripts = {}  # Initialize script storage for the node
    else:
        print("No node selected.")
def on_item_clicked1(item, column):
    #global selected_node
    node = item.data(0, Qt.UserRole)  # Retrieve the NodePath stored in the item

    if node:
        world.selected_node = node
        # Update input boxes with node's properties
        uiEditor_inst.input_boxes[(0, 0)].setText(str(node.getX()))
        uiEditor_inst.input_boxes[(0, 1)].setText(str(node.getY()))
        uiEditor_inst.input_boxes[(0, 2)].setText(str(node.getZ()))
        uiEditor_inst.input_boxes[(1, 0)].setText(str(node.getH()))
        uiEditor_inst.input_boxes[(1, 1)].setText(str(node.getP()))
        uiEditor_inst.input_boxes[(1, 2)].setText(str(node.getR()))
        uiEditor_inst.input_boxes[(2, 0)].setText(str(node.getScale().x))
        uiEditor_inst.input_boxes[(2, 1)].setText(str(node.getScale().y))
        uiEditor_inst.input_boxes[(2, 2)].setText(str(node.getScale().z))

        # Clear existing widgets in the ScriptInspector
        for i in reversed(range(uiEditor_inst.inspector_ui_tab.scroll_layout.count())):
            widget = uiEditor_inst.inspector_ui_tab.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                
        
        world.gizmos.gizmo_root.set_pos(node.get_pos())
        
        uiEditor_inst.inspector_ui_tab.recreate_property_box_for_node(node)

        # Load scripts associated with the node
        #if node in inspector.scripts:
        #    for path, script_instance in inspector.scripts[node].items():
        #        if inspector.prop:
        #            
        #            inspector.set_script(path, node, inspector.prop)
        #else:
        #    inspector.scripts = {}  # Initialize script storage for the node
        uiEditor_inst.inspector_ui_tab.set_ui_editor(node, node.get_python_tag("isCanvas"), node.get_python_tag("isLabel"), instance=uiEditor_inst, w=world)
    else:
        print("No node selected.")


def new_tab(index):
    if index == 1:
        shader_editor.show_nodes()
        pandaWidget.resizeEvent(pandaWidget)
        pandaWidget1.resizeEvent(pandaWidget1)
        world.cam.setPos(0, -55, 30)
        world.cam.lookAt(0, 0, 0)
    elif index == 2:
        shader_editor.hide_nodes()
        panda_widget_2.resizeEvent(panda_widget_2)
        world.cam.setPos(0, -55, 30)
        world.cam.lookAt(0, 0, 0)

    elif index == 3:
        print("!")
        shader_editor.show_nodes()
        pandaWidget.resizeEvent(pandaWidget)
        pandaWidget1.resizeEvent(pandaWidget1)
        panda_widget_2.resizeEvent(panda_widget_2)
        world.cam.setPos(0,-3, 255)
        world.cam.lookAt(world.canvas)
class Node:
    def __init__(self, ref, path):
        self.ref = ref
        self.paths = [path]

    def update(self, path):
        if path not in self.paths:
            self.paths.append(path)

project_name = None

main_map = None


class StartupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select a Project")
        self.setGeometry(200, 200, 400, 300)
        layout = QVBoxLayout()
        self.label = QLabel("Select or Create a Project:")
        layout.addWidget(self.label)
        self.project_list = QListWidget()

        # InZane84 2/11/2025: Let's be sure the cwd is '/src' =========================
        editor_program_path = os.path.abspath(sys.argv[0])
        if not os.path.samefile(os.getcwd(), os.path.dirname(editor_program_path)):
            print("StartupWindow: init - cwd is different from the editor program directory!")
            os.chdir(os.path.dirname(editor_program_path))
            print("StartupWindow: init - Changed cwd to the editor program directory.")
        # =============================================================================

        self.fill_project_list(os.path.abspath("./saves"))
        layout.addWidget(self.project_list)
        self.select_button = QPushButton("Open Project")
        self.select_button.clicked.connect(self.load_projects)
        self.select_button.setEnabled(False)  # Initially disabled
        layout.addWidget(self.select_button)
        self.new_project_input = QLineEdit()
        self.new_project_input.setPlaceholderText("Enter new project name...")
        layout.addWidget(self.new_project_input)
        self.create_button = QPushButton("Create New Project")
        self.create_button.clicked.connect(self.create_project)
        self.project_list.itemSelectionChanged.connect(self.update_button_state)
        self.project_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.create_button)
        self.setLayout(layout)

    def on_item_double_clicked(self, item):
        """Handle double-click on project list item"""
        project_path = item.data(Qt.UserRole)
        self.load_projects(select=project_path)

    def update_button_state(self):
        """Enables/disables Open Project button based on selection"""
        has_selection = bool(self.project_list.selectedItems())
        self.select_button.setEnabled(has_selection)

    def fill_project_list(self, folder_path):
        self.project_list.clear()
        if not os.path.isdir(folder_path):
            print(f"Provided path {folder_path} is not a valid directory.")
            return
        try:
            entries = os.listdir(folder_path)
        except Exception as e:
            print(f"Error reading directory {folder_path}: {e}")
            return
        if entries:
            self.project_list.setCurrentRow(0)
        for entry in entries:
            full_path = os.path.join(folder_path, entry)
            if os.path.isdir(full_path):
                item = QListWidgetItem(os.path.basename(entry))
                item.setData(Qt.UserRole, full_path)
                self.project_list.addItem(item)

    def load_projects(self, select=None):
        """
        Loads the selected project by reading its preferences.toml to get the main_map path,
        then uses MapLoader to load the map.
        """
        global project_name, opened_map, world, appw
        if not select:
            selected_item = self.project_list.currentItem()
            # Use the full project folder path stored in the item.
            project_path = selected_item.data(Qt.UserRole)
            project_name = os.path.basename(project_path)  # Store full path for later use.
        else:
            selected_item = select
            project_path = select
            project_name = select
        if not selected_item:
            QMessageBox.warning(self, "No Project Selected", "Please select a project to open.")
            return
        
        print(f"Opening project: {project_path}")

        # Read the preferences file (assumed to be at PROJECT_PATH/preferences.toml)
        pref_file = os.path.join(project_path, "preferences.toml")
        if not os.path.exists(pref_file):
            QMessageBox.warning(self, "Error", f"Preferences file not found in {project_path}")
            return

        with open(pref_file, "r") as pref:
            prefs = toml.load(pref)
        map_path = prefs.get("main_map", None)
        if not map_path:
            QMessageBox.warning(self, "Error", "No main_map entry found in preferences.")
            return
        appw.show()

        # Ensure the map_path is absolute.
        map_path = os.path.abspath(map_path)
        print(f"Opening map file: {map_path}")
        self.hide()
        ml = entity_editor.MapLoader(world)
        ml.load_map(map_path)
        opened_map = os.path.basename(map_path)
        QMessageBox.information(self, "Project Loaded", f"Project loaded from {map_path}")

    def create_project(self):
        """
        Creates a new project folder (inside ./saves) and initializes it with a basic scene.
        """
        global project_name, world
        world.refresh()
        world.reset_render()
        project_name = self.new_project_input.text().strip()
        if not project_name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a valid project name.")
            return
        base_dir = os.path.abspath(os.path.join(os.getcwd(), "saves"))
        base1_dir = os.path.abspath(os.path.join(os.getcwd(), "toml_loader"))
        project_path = os.path.join(base_dir, project_name)
        if os.path.exists(project_path):
            QMessageBox.warning(self, "Project Exists", "A project with this name already exists.")
            return
        os.makedirs(project_path)
        print(f"📂 Created new project: {project_path}")
        # Save scene data into a folder inside the project.
        output_toml = os.path.join(base1_dir, project_name)  # e.g., ./saves/tttttt/tttttt
        output_map = os.path.join(project_path, f"{project_name}.map")  # e.g., ./saves/tttttt/tttttt.map
        saver = entity_editor.Save(world)
        saver.save_scene_to_toml(world.render, output_toml)
        saver.save_scene_to_map(output_toml, output_map)
        # Save preferences indicating the map file location.
        main_map = {"main_map": output_map}
        with open(os.path.join(project_path, "preferences.toml"), "w") as pref:
            pref.write(toml.dumps(main_map))
        self.load_projects(select=project_path)
        QMessageBox.information(self, "Project Created", f"Project '{project_name}' created and initialized!")



    def launch_main_app(self, project_path):
        """Launches the main application with the selected project."""
        print(f"Launching main application with project: {project_path}")
        global appw
        self.close()
        appw.show()
        # Replace with your main application launch (e.g., main.py)
        #os.system(f"python main.py {project_path}")

class Save_ui(QInputDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Second Window")
        self.setGeometry(150, 150, 300, 200)
        
        # Layout for the second window
        layout = QVBoxLayout()
        
        # Input field
        self.input_field = QLineEdit(self)
        self.input_field.setText("untitled.ui")
        self.input_field.setPlaceholderText("untitled.ui")
        layout.addWidget(self.input_field)
        
        # Button to process the input
        self.submit_button = QPushButton("Save", self)
        self.submit_button.clicked.connect(self.process_input)
        layout.addWidget(self.submit_button)
        
        self.setLayout(layout)
    
    def process_input(self):
        global world
        global project_name
        # Get the input text and display it in the label
        user_input = self.input_field.text()
        ent_editor = entity_editor.Save(world)
        ent_editor.save_scene_ui_to_toml(world.render2d, project_name + "/saves/ui/", user_input)
        
class Save_map(QInputDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Second Window")
        self.setGeometry(150, 150, 300, 200)
        
        global project_name
        
        if project_name != None:
        
        
            # Layout for the second window
            layout = QVBoxLayout()

            # Input field
            self.input_field = QLineEdit(self)
            self.input_field.setText("untitled.map")
            self.input_field.setPlaceholderText("untitled.map")
            layout.addWidget(self.input_field)

            # Button to process the input
            self.submit_button = QPushButton("Save", self)
            self.submit_button.clicked.connect(self.process_input)
            layout.addWidget(self.submit_button)

            self.setLayout(layout)
            
        else:
            pass
    
    def process_input(self):
        global world
        # Get the input text and display it in the label
        user_input = self.input_field.text()
        save_map(user_input)
        

class Load_ui(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Second Window")
        self.setGeometry(150, 150, 300, 200)

        self.mesh_select = QComboBox(self)
        self.mesh_select.currentIndexChanged.connect(self.set_selected)
        
        matching_files = []
        for root, _, files in os.walk("./"):#FIXME this will be the project folder
            for file in files:
                if file.endswith(".ui"):  # Check file extension
                    matching_files.append(os.path.join(root, file))
                    self.mesh_select.addItem(file)
        
        
        
        # Layout for the second window
        layout = QVBoxLayout()

        
        # Button to process the input
        self.submit_button = QPushButton("Load", self)
        self.submit_button.clicked.connect(self.process_input)
        layout.addWidget(self.submit_button)
        
        self.setLayout(layout)
        
    def set_selected(self):
        self.selected_text = self.mesh_select.currentText()

    
    def process_input(self):
        global world
        # Get the input text and display it in the label
        #user_input = self.input_field.text()
        entity_editor.Load(world).load_ui_from_folder_toml(self.selected_text, world.render2d)
        
#Toolbar functions
def new_project():
    print("Open file triggered")
    global sw
    
    sw.show()
    appw.hide()

opened_map = None
def save_file():
    global opened_map
    #world.messenger.send("save")
    save_map(os.path.basename(os.path.splitext(opened_map)[0]))
    print("Save file triggered")


save_ui_instance = None
load_ui_instance = None

def save_ui_func():
    global save_ui_instance
    save_ui_instance = Save_ui()
    save_ui_instance.show()
    
def load_ui_func():
    global load_ui_instance
    load_ui_instance = Load_ui()
    load_ui_instance.show()

save_map_instance = None

def save_map_func():
    global save_map_instance
    save_map_instance = Save_map()
    save_map_instance.show()

import toml

def load_project(world):
    global sw
    
    sw.show()
    appw.hide()

    # Iterate through entities


    
    
def close(): #TODO when saving is introduced make a window pop up with save option(save don't save and don't exist(canel))
    """closing the editor"""
    exit()

input_settings = None
net_settings = None
def show_input_manager():
    global input_settings
    input_settings = input_manager.InputSettingsWindow(input_manager_c)
    input_settings.show()

def show_net_manager():
    global net_settings
    net_settings = input_manager.NetworkSettingsWindow()
    net_settings.show()
    
from multiprocessing import Process

# Top-level function for multiprocessing
def run_game_preview(network_manager):
    app = Preview_build.GamePreviewApp(network_manager)
    app.run()

def play_mode():
    """Launch game preview in a separate process as a client"""
    server_ip = "127.0.0.1"
    server_port = 9000

    # Ensure the game process uses the client NetworkManager
    from multiprocessing import get_context
    ctx = get_context('spawn')
    game_process = ctx.Process(
        target=run_game_preview,
        args=(server_ip, server_port)
    )
    game_process.start()

def run_game_preview(server_ip, server_port):
    """Target function for the game preview process (client)"""
    network_manager = NetworkManager(
        server_address=(server_ip, server_port),
        is_client=True  # Force client mode
    )
    network_manager.connect_to_server()
    app = Preview_build.GamePreviewApp(network_manager)
    app.run()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Panda3D Editor")

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Hierarchy tree widget
        self.hierarchy_tree = QTreeWidget()
        self.hierarchy_tree.setHeaderLabel("Hierarchy")
        self.hierarchy_tree.itemClicked.connect(self.on_item_clicked)
        main_layout.addWidget(self.hierarchy_tree)

        # Terrain control widget
        self.terrain_control_widget = TerrainControlWidget(terrain_painter_app)
        terrain_painter_app.terrain_np.set_python_tag("isTerrain", True)
        main_layout.addWidget(self.terrain_control_widget)

        # Populate the hierarchy tree with example data
        self.populate_hierarchy_tree()

    def populate_hierarchy_tree(self):
        # Example data for the hierarchy tree
        root_item = QTreeWidgetItem(self.hierarchy_tree, ["Root"])
        child_item = QTreeWidgetItem(root_item, ["Child"])
        root_item.setExpanded(True)

        # Store NodePath in the item for demonstration purposes
        root_node = NodePath("Root")
        child_node = root_node.attachNewNode("Child")
        root_item.setData(0, Qt.UserRole, root_node)
        child_item.setData(0, Qt.UserRole, child_node)

    def on_item_clicked(self, item, column):
        node = item.data(0, Qt.UserRole)  # Retrieve the NodePath stored in the item

        if node:
            world.selected_node = node
            # Update input boxes with node's properties
            input_boxes[(0, 0)].setText(str(node.getX()))
            input_boxes[(0, 1)].setText(str(node.getY()))
            input_boxes[(0, 2)].setText(str(node.getZ()))
            input_boxes[(1, 0)].setText(str(node.getH()))
            input_boxes[(1, 1)].setText(str(node.getP()))
            input_boxes[(1, 2)].setText(str(node.getR()))
            input_boxes[(2, 0)].setText(str(node.getScale().x))
            input_boxes[(2, 1)].setText(str(node.getScale().y))
            input_boxes[(2, 2)].setText(str(node.getScale().z()))

#-------------------
#Terrain Generation
terrain_generate = None


def gen_terrain():
    global world
    global terrain_generate
    world.make_terrain()


#-------------------

sw = None

def startup_w():
    global sw
    sw = StartupWindow()
    sw.show()




def save_map(map_name):
    global world, project_name
    
    world.refresh()
    world.reset_render()
    # Define the base directories for the TOML and MAP files.
    # (Here we use os.getcwd() to get the current working directory.
    #  Adjust this as needed for your project structure.)
    toml_base_dir = os.path.join(os.getcwd(), "toml_loader", project_name)
    map_base_dir  = os.path.join(os.getcwd(), "saves", project_name)
    
    # Ensure these directories exist
    os.makedirs(toml_base_dir, exist_ok=True)
    os.makedirs(map_base_dir, exist_ok=True)
    
    # Build the full file paths.
    # For example, if map_name is "Level1", the paths become:
    #   .../toml_loader/MyProject/Level1.toml
    #   .../saves/MyProject/Level1.map
    toml_file_path = os.path.join(toml_base_dir, map_name)
    map_file_path  = os.path.join(map_base_dir, map_name + ".map")
    
    # Save the scene.
    # (Note: In your create_project function you used the toml path as the first
    #  parameter for save_scene_to_map; we follow that pattern here.)
    saver = entity_editor.Save(world)
    saver.save_scene_to_toml(world.render, toml_file_path)
    saver.save_scene_to_map(toml_file_path, map_file_path)

def delete_selection():
    global world
    selected_items = world.hierarchy_tree.selectedItems()
    if not selected_items:
        print("No item selected.")
        return

    item = selected_items[0]
    node = item.data(0, Qt.UserRole)
    
    if not node:
        print("Selected item has no associated node.")
        return

    # Prevent deletion of the main render node
    if node == world.render:
        QMessageBox.warning(appw, "Cannot Delete", "The main render node cannot be deleted.")
        return

    # Store the node name before removal
    node_name = node.getName()

    # Proceed with deletion if not the main render
    node.removeNode()
    world.selected_node = None
    del node
    
    world.refresh()
    print(f"Node '{node_name}' deleted successfully.")


def build_project():
    os.system("python build.py")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    appw = QMainWindow()
    
    # Initialize NetworkManager and InputManager inside the main block
    network_manager = NetworkManager()  # Server mode
    input_manager_c = InputManager(network_manager)
    
    world = PandaTest()
    appw.setGeometry(50, 50, 1024, 768)

    world.make_hierarchy()
    
    # Main Widget
    main_widget = QWidget()
    main_layout = QVBoxLayout(main_widget)  # Use vertical layout for tabs
    
    
    
    # Create the toolbar
    toolbar = QToolBar("Main Toolbar")

    appw.addToolBar(toolbar)
    
    delete_shortcut = QShortcut(QKeySequence("Delete"), world.hierarchy_tree)
    delete_shortcut.activated.connect(delete_selection)
    

    # Create the menu
    edit_tool_type_menu = QMenu("File", appw)
    terrain_3d = QMenu("Terrain 3D", appw)

    # Create an action for the Edit menu
    action = QAction("New Project", appw)
    action.triggered.connect(new_project)
    edit_tool_type_menu.addAction(action)

    action1 = QAction("Save Project", appw)
    action1.triggered.connect(save_file)
    action1.setShortcut(QKeySequence("Ctrl+S"))
    edit_tool_type_menu.addAction(action1)

    action3 = QAction("play game", appw)
    action3.triggered.connect(play_mode)
    action3.setShortcut(QKeySequence("F5"))
    edit_tool_type_menu.addAction(action3)
    
    actionI = QAction("input manager", appw)
    actionI.triggered.connect(show_input_manager)
    edit_tool_type_menu.addAction(actionI)
    
    actionN = QAction("network manager", appw)
    actionN.triggered.connect(show_net_manager)
    edit_tool_type_menu.addAction(actionN)
    
    action2 = QAction("Load Project", appw)
    action2.triggered.connect(lambda: load_project(world))
    edit_tool_type_menu.addAction(action2)

    save_ui = QAction("save ui", appw)
    save_ui.triggered.connect(lambda: save_ui_func())
    edit_tool_type_menu.addAction(save_ui)
    
    load_ui = QAction("load ui", appw)
    load_ui.triggered.connect(lambda: load_ui_func())
    edit_tool_type_menu.addAction(load_ui)
    
    save_map_w = QAction("save map", appw)
    save_map_w.triggered.connect(lambda: save_map_func())
    edit_tool_type_menu.addAction(save_map_w)
    
    action3 = QAction("Exit", appw)
    action3.triggered.connect(exit)
    edit_tool_type_menu.addAction(action3)

    #--------------------------
    #actions for Terrain3D menu
    action = QAction("Generate Terrain", appw)
    action.triggered.connect(gen_terrain)
    terrain_3d.addAction(action)
    #--------------------------

    # Create a tool button for the menu
    tool_button = QToolButton()
    tool_button.setText("File")
    tool_button.setMenu(edit_tool_type_menu)
    tool_button.setPopupMode(QToolButton.InstantPopup)
    toolbar.addWidget(tool_button)

    # Create a tool button for the menu
    tool_button1 = QToolButton()
    tool_button1.setText("Terrain 3D")
    tool_button1.setMenu(terrain_3d)
    tool_button1.setPopupMode(QToolButton.InstantPopup)
    toolbar.addWidget(tool_button1)

    build_btn = QPushButton("build")
    build_btn.clicked.connect(lambda: build_project())
    # Tabs
    tab_widget = QTabWidget()
    main_layout.addWidget(tab_widget)

    # Node Editor Tab
    node_editor_tab = QWidget()
    node_editor_layout = QVBoxLayout(node_editor_tab)
    node_editor = node.MainWindow()
    node_editor_layout.addWidget(node_editor)
    tab_widget.addTab(node_editor_tab, "Node Editor")

    # 3D Viewport Tab
    viewport_tab = QWidget()
    viewport_layout = QVBoxLayout(viewport_tab)

    # Splitter for left panel, viewport, and right panel
    viewport_splitter = QSplitter(Qt.Horizontal)
    viewport_layout.addWidget(viewport_splitter)

    # Empty Left Panel
    left_panel = QWidget()
    left_panel_layout = QVBoxLayout()
    left_panel.setLayout(left_panel_layout)


    # Example node and script
    class DummyNode:
        def __init__(self, name):
            self.name = name
            self.tags = {}

        def get_name(self):
            return self.name

        def set_python_tag(self, key, value):
            self.tags[key] = value

        def get_python_tag(self, key):
            return self.tags.get(key)

    inspector = scirpt_inspector.ScriptInspector(world, entity_editor, node, left_panel)
    world.script_inspector = inspector

    node = DummyNode("Cube")

    #inspector.show()
    left_panel_layout.addWidget(inspector)
    viewport_splitter.addWidget(left_panel)

    # Splitter for 3D Viewport and File System
    viewport_inner_splitter = QSplitter(Qt.Vertical)
    viewport_splitter.addWidget(viewport_inner_splitter)

    # 3D Viewport
    pandaWidget = QPanda3DWidget(world)
    viewport_inner_splitter.addWidget(pandaWidget)
 
    
    # Drag-and-Drop File System
    file_system_panel = FileExplorer()
    #file_system_panel.setHeaderLabel("File System")
    viewport_inner_splitter.addWidget(file_system_panel)

    # Hierarchy Viewer (Right Panel)
    right_panel = QWidget()
    right_panel.setLayout(QVBoxLayout())
    
    #world.make_hierarchy()
    
    world.hierarchy_tree.setHeaderLabel("Scene Hierarchy")
    world.hierarchy_tree.setDragEnabled(True)
    world.hierarchy_tree.setAcceptDrops(True)
    
    right_panel.layout().addWidget(world.hierarchy_tree)
    terrain_painter_app = terrainEditor.TerrainPainterApp(world, pandaWidget)
    terrain_painter_app.terrain_np.set_python_tag("isTerrain", True)
    control_widget = TerrainControlWidget(terrain_painter_app)
    right_panel.layout().addWidget(control_widget)
    # Create a QWidget to hold the grid layout
    grid_widget = QWidget()
    # Create a grid layout for the input boxes (3x3)
    grid_layout = QGridLayout(grid_widget)

    # Create 3x3 QLineEdit input boxes
    input_boxes = {}
    for i in range(3):
        for j in range(3):
            if i == 0 and j == 0:
                label = QLabel("transforms x y z: ")
            if i == 1 and j == 0:
                label = QLabel("rotation x y z: ")
            if i == 2 and j == 0:
                label = QLabel("scale x y z: ")
            input_box = QLineEdit(grid_widget)
            input_boxes[(i, j)] = input_box
            grid_layout.addWidget(label, i * 2, j)  # Add label in a separate row
            grid_layout.addWidget(input_box, i * 2 + 1, j)  # Add input box below the label

    # Add the grid widget to the main layout
    right_panel.layout().addWidget(grid_widget)

    viewport_splitter.addWidget(right_panel)

    # Add the 3D Viewport Tab to Tabs
    tab_widget.addTab(viewport_tab, "3D Viewport")

    # Add Shader Editor
    viewport_tab = QWidget()
    viewport_layout = QVBoxLayout(viewport_tab)

    # Add UI Editor
    viewport_tab1 = QWidget()
    viewport_layout1 = QVBoxLayout(viewport_tab1)
    
    # Splitter for left panel, viewport, and right panel
    viewport_splitter = QSplitter(Qt.Horizontal)
    viewport_layout.addWidget(viewport_splitter)

    viewport_splitter1 = QSplitter(Qt.Horizontal)
    viewport_layout1.addWidget(viewport_splitter1)
    
    panda_widget_2 = QPanda3DWidget(world)
    viewport_splitter.addWidget(panda_widget_2)

    shader_editor = ShaderEditor()
    viewport_splitter.addWidget(shader_editor)

    # 2D Viewport
    pandaWidget1 = QPanda3DWidget(world)
    uiEditor_inst = ui_editor.Drag_and_drop_ui_editor(world, world.render2d)
    viewport_splitter1.addWidget(uiEditor_inst.tab_content(viewport_tab1, world))
    world.uiEditor = uiEditor_inst
    
    tab_widget.addTab(viewport_tab, "Shader Editor")
    tab_widget.currentChanged.connect(new_tab)
    
    tab_widget.addTab(viewport_tab1, "UI Editor")
    tab_widget.currentChanged.connect(new_tab)

    # Set the main widget as the central widget
    appw.setCentralWidget(main_widget)

    # Populate the hierarchy tree with actual scene data
    world.populate_hierarchy(world.hierarchy_tree, render)  # This will populate the hierarchy panel
    world.populate_hierarchy(world.hierarchy_tree1, world.render2d)  # This will populate the hierarchy panel

    world.hierarchy_tree.itemClicked.connect(lambda item, column: on_item_clicked(item, column))
    world.hierarchy_tree1.itemClicked.connect(lambda item, column: on_item_clicked1(item, column))
    
    #world.ui_editor_script_to_canvas()
    
    
    tab_widget.addTab(world.animator_tab, "Animator") 

    prop = properties
    prop_ui_e = properties_ui_editor
    for coord, box in input_boxes.items():
        # Use a default argument to capture the value of coord correctly
        box.textChanged.connect(lambda box=box, coord=coord: prop.update_node_property(box, coord))
    for coord, box in uiEditor_inst.input_boxes.items():
        # Use a default argument to capture the value of coord correctly
        box.textChanged.connect(lambda box=box, coord=coord: prop_ui_e.update_node_property(box, coord))

    # Set the background color of the widget to gray
    #qdarktheme.setup_theme()
    #apply_stylesheet(appw, theme="light_blue.xml")

    # Replace qdarktheme with this
    app.setStyle("Fusion")
    
    # Create dark palette
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    dark_palette.setColor(QPalette.Disabled, QPalette.Button, QColor(42, 42, 42))
    dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(128, 128, 128))
    dark_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(128, 128, 128))

    app.setPalette(dark_palette)
    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")
    app.setStyleSheet("""
        /* Style for tool buttons with menus */
        QToolButton {
            padding-right: 15px;
            background-color: #353535;
            border: 1px solid #454545;
            border-radius: 3px;
            min-width: 60px;
        }
        
        QToolButton::menu-indicator {
            subcontrol-origin: padding;
            subcontrol-position: right center;
            width: 12px;
            right: 2px;
        }

        /* Style for dropdown menus */
        QMenu {
            background-color: #404040;
            border: 1px solid #505050;
            color: white;
        }
        
        QMenu::item {
            padding: 5px 25px 5px 20px;
        }
        
        QMenu::item:selected {
            background-color: #505050;
        }
        
        QMenu::separator {
            height: 1px;
            background: #505050;
            margin: 4px 8px;
        }
    """)

    # Show the application window
    startup_w()
    world.make_ray_caster()
    
    appw.hide()

    
    sys.exit(app.exec_())