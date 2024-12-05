DEVKIT_VER = (0, 5, 0)

import os
import bpy   
import time
import random
import addon_utils

from importlib     import reload
from pathlib       import Path
from functools     import partial
from itertools     import combinations
from bpy.types     import Operator, Panel, PropertyGroup 
from bpy.props     import StringProperty, EnumProperty, BoolProperty, PointerProperty, FloatProperty, IntProperty


#       Shapes:         (Name,          Slot/Misc,      Category, Description,                                           Body,             Shape Key)
ALL_SHAPES = {
        "Large":        ("Large",       "Chest",        "Large",  "Standard Large",                                      "",               ""),
        "Omoi":         ("Omoi",        "Chest",        "Large",  "Large, but saggier",                                  "",               ""),
        "Sugoi Omoi":   ("Sugoi Omoi",  "Chest",        "Large",  "Omoi, but saggier",                                   "",               ""),
        "Medium":       ("Medium",      "Chest",        "Medium", "Standard Medium",                                     "",               "MEDIUM ----------------------------"),
        "Sayonara":     ("Sayonara",    "Chest",        "Medium", "Medium with more separation",                         "",               ""),
        "Tsukareta":    ("Tsukareta",   "Chest",        "Medium", "Medium, but saggier",                                 "",               ""),
        "Tsukareta+":   ("Tsukareta+",  "Chest",        "Medium", "Tsukareta, but saggier",                              "",               ""),
        "Mini":         ("Mini",        "Chest",        "Medium", "Medium, but smaller",                                 "",               ""),
        "Small":        ("Small",       "Chest",        "Small",  "Standard Small",                                      "",               "SMALL ------------------------------"),
        "Rue":          ("Rue",         "Chest",        "",       "Adds tummy",                                          "",               "Rue"),
        "Buff":         ("Buff",        "Chest",        "",       "Adds muscle",                                         "",               "Buff"),
        "Piercings":    ("Piercings",   "Chest",        "",       "Adds piercings",                                      "",               ""),
        "Rue Legs":     ("Rue",         "Legs",         "",       "Adds tummy and hip dips.",                            "",               "Rue"),
        "Melon":        ("Melon",       "Legs",         "Legs",   "For crushing melons",                                 "",               ""),
        "Skull":        ("Skull",       "Legs",         "Legs",   "For crushing skulls",                                 "",               "Skull Crushers"),
        "Small Butt":   ("Small Butt",  "Legs",         "Butt",   "Not actually small",                                  "",               "Small Butt"),
        "Mini Legs":    ("Mini",        "Legs",         "Legs",   "Smaller legs",                                        "",               "Mini"),
        "Soft Butt":    ("Soft Butt",   "Legs",         "Butt",   "Less perky butt",                                     "",               "Soft Butt"),
        "Hip Dips":     ("Hip Dips",    "Legs",         "Hip",    "Removes hip dips on Rue, adds them on YAB",           "",               ""),
        "Gen A":        ("Gen A",       "Legs",         "Vagina", "Labia majora",                                        "",               ""),
        "Gen B":        ("Gen B",       "Legs",         "Vagina", "Visible labia minora",                                "",               "Gen B"),
        "Gen C":        ("Gen C",       "Legs",         "Vagina", "Open vagina",                                         "",               "Gen C"),
        "Gen SFW":      ("Gen SFW",     "Legs",         "Vagina", "Barbie doll",                                         "",               "Gen SFW"), 
        "Pubes":        ("Pubes",       "Legs",         "Pubes",  "Adds pubes",                                          "",               ""),
        "YAB Hands":    ("YAB",         "Hands",        "Hands",  "YAB hands",                                           "",               ""),
        "Rue Hands":    ("Rue",         "Hands",        "Hands",  "Changes hand shape to Rue",                           "",               "Rue"),
        "Long":         ("Long",        "Hands",        "Nails",  "They're long",                                        "",               ""),
        "Short":        ("Short",       "Hands",        "Nails",  "They're short",                                       "",               "Short Nails"),
        "Ballerina":    ("Ballerina",   "Hands",        "Nails",  "Some think they look like shoes",                     "",               "Ballerina"),
        "Stabbies":     ("Stabbies",    "Hands",        "Nails",  "You can stab someone's eyes with these",              "",               "Stabbies"),
        "Straight":     ("Straight",    "Hands",        "Nails",  "When you want to murder instead",                     "",               ""),
        "Curved":       ("Curved",      "Hands",        "Nails",  "If you want to murder them a bit more curved",        "",               "Curved"),
        "YAB Feet":     ("YAB",         "Feet",         "Feet",   "YAB feet",                                            "",               ""),
        "Rue Feet":     ("Rue",         "Feet",         "Feet",   "Changes foot shape to Rue",                           "",               "Rue"),
        "Clawsies":     ("Clawsies",    "Feet",         "Claws",  "Good for kicking",                                    "",               ""),
        }


# Global variable for making sure all functions can properly track the current export.
is_exporting: bool      = False

devkit_registered: bool = False


def visible_meshobj():
    visible_meshobj = []
    for obj in bpy.context.scene.objects:
        if obj.visible_get(view_layer=bpy.context.view_layer) and obj.type == "MESH":
            visible_meshobj.append(obj)
    return visible_meshobj

def get_object_from_mesh(mesh_name:str):
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and obj.data.name == mesh_name:
            return obj
    return None

def get_chest_size_keys(chest_subsize:str):
    """category, sizekey"""
    chest_category = get_chest_category(chest_subsize)
    
    size_key = {
        "Large": "LARGE -------------------------------",
        "Medium": "MEDIUM ----------------------------",
        "Small": "SMALL ------------------------------"
    }
    return size_key[chest_category]

def get_chest_category(size:str):
    """subsize, category"""
    if ALL_SHAPES[size][1] == "Chest":
        return ALL_SHAPES[size][2]
    else:
        return None

def get_shape_presets(size:str):
        """subsize, [shapekey, value]"""
        shape_presets = {
        "Large":        {"Squeeze" : 0.3,    "Squish" : 0.0,  "Push-Up" : 0.0, "Omoi" : 0.0, "Sag" : 0.0, "Nip Nops" : 0.0},
        "Omoi":         {"Omoi" : 1.0, "Sag" : 0.0},
        "Sugoi Omoi":   {"Omoi" : 1.0, "Sag" : 1.0},
        "Medium":       {"Squeeze" : 0.0,  "Squish" : 0.0, "Push-Up" : 0.0, "Mini" : 0.0, "Sayonara" : 0.0, "Sag" : 0.0, "Nip Nops" : 0.0},
        "Sayonara":     {"Sayonara" : 1.0, "Sag" : 0.0},
        "Tsukareta":    {"Sag" : 0.6},
        "Tsukareta+":   {"Sag" : 1.0},
        "Mini":         {"Mini" : 1.0},
        "Small":        {"Squeeze" : 0.0, "Nip Nops" : 0.0}
        }
        return shape_presets[size]

def has_shape_keys(obj):
        if obj and obj.type == "MESH":
            if obj.data.shape_keys is not None:
                return True
        return False

def get_filtered_shape_keys(obj, key_filter:list):
        shape_keys = obj.shape_keys.key_blocks
        key_list = []
        to_exclude = ["Mini"]
        
        for key in shape_keys:
            norm_key = key.name.lower().replace("-","").replace(" ","")
            if any(f_key == norm_key for f_key in key_filter):
                key_name = key.name
                category = key.relative_key.name
                category_lower = category.lower().replace("-","").replace(" ","")

                if any(key_name in to_exclude for keys in to_exclude):
                    break

                key_list.append((norm_key, category_lower, key_name))
        
        return key_list

def update_directory(category:str):
    prop = bpy.context.scene.devkit_props
    actual_prop = f"{category}_directory"
    display_prop = f"{category}_display_directory"

    display_directory = getattr(prop, display_prop, "")

    if os.path.exists(display_directory):  
        setattr(prop, actual_prop, display_directory)
        print (getattr(prop, actual_prop, ""))


class CollectionState(PropertyGroup):
    name: bpy.props.StringProperty() # type: ignore


class ObjectState(PropertyGroup):
    name: bpy.props.StringProperty() # type: ignore
    hide: bpy.props.BoolProperty() # type: ignore


class DevkitProps(PropertyGroup):
    ui_buttons_list = [
    ("export",   "expand",   "Opens the category"),
    ("import",   "expand",   "Opens the category"),
    ("chest",    "shapes",   "Opens the category"),
    ("leg",      "shapes",   "Opens the category"),
    ("other",    "shapes",   "Opens the category"),
    ("chest",    "category", "Opens the category"),
    ("yas",      "expand",   "Opens the category"),
    ("export",   "options",  "Opens the category"),
    ("import",   "options",  "Opens the category"),
    ("dynamic",  "view",     "Changes between a shape key view that focuses on the main controller in a collection or the active object"),
    ("force",    "yas",      "This force enables YAS on any exported model and appends 'Yiggle' to their file name. Use this if you already exported regular models and want YAS alternatives"),
   
    ]
    
    extra_buttons_list = [
        ("check",    "tris",       True,   "Verify that the meshes have an active triangulation modifier"),
        ("force",    "yas",        False,  "This force enables YAS on any exported model and appends 'Yiggle' to their file name. Use this if you already exported regular models and want YAS alternatives"),
        ("fix",      "parent",     True,   "Parents the meshes to the devkit skeleton and removes non-mesh objects"),
        ("update",   "material",   True,   "Changes material rendering and enables backface culling"),
        ("keep",     "shapekeys",  True,   "Preserves vanilla clothing shape keys"),
        ("create",   "subfolder",  True,   "Creates a folder in your export directory for your exported body part"),
        ]
   
    mesh_list = [
        "Torso",
        "Waist",
        "Hands",
        "Feet",
        "Mannequin",
    ]

    controller_modifiers = [
            ("UV Transfers",       False,   "Toggles UV transfers for various breast sizes. Toggling it off makes shape sliders operate more smoothly. Off by default, exporting automatically turns it on"),
            ("Triangulation",      True,    "Toggles triangulation of the body meshes"),
            ("YAS Chest",          False,   "Toggles YAS"),
            ("YAS Legs",           False,   "Toggles YAS"),
            ("YAS Hands",          False,   "Toggles YAS"),
            ("YAS Feet",           False,   "Toggles YAS"),
            ("YAS Mannequin",      False,   "Toggles YAS"),
            ("YAS Legs Gen",       False,   "Toggles Genitalia"),
            ("YAS Mannequin Gen",  False,   "Toggles Genitalia"),
            ]
        
    @staticmethod
    def export_bools():
        for shape, (name, slot, shape_category, description, body, key) in ALL_SHAPES.items():
            slot_lower = slot.lower().replace("/", " ")
            name_lower = name.lower().replace(" ", "_")
            
            prop_name = f"export_{name_lower}_{slot_lower}_bool"
            prop = BoolProperty(
                name="", 
                description=description,
                default=False, 
                )
            setattr(DevkitProps, prop_name, prop)

    @staticmethod
    def extra_options():
        for (name, category, default, description) in DevkitProps.extra_buttons_list:
            category_lower = category.lower()
            name_lower = name.lower()
            
            prop_name = f"{name_lower}_{category_lower}"
            prop = BoolProperty(
                name="", 
                description=description,
                default=default, 
                )
            setattr(DevkitProps, prop_name, prop)

    @staticmethod
    def ui_buttons():
        for (name, category, description) in DevkitProps.ui_buttons_list:
            category_lower = category.lower()
            name_lower = name.lower()

            default = False
            if name_lower == "advanced":
                default = True
            
            prop_name = f"button_{name_lower}_{category_lower}"
            prop = BoolProperty(
                name="", 
                description=description,
                default=default, 
                )
            setattr(DevkitProps, prop_name, prop)

    @staticmethod
    def chest_key_floats():
        # Creates float properties for chest shape keys controlled by values.
        # Automatically assigns drivers to the models to be controlled by the UI.
        key_filter = ["squeeze", "squish", "pushup", "omoi", "sag", "nipnops", "sayonara", "mini"]
        torso = bpy.data.meshes["Torso"]
        mq = bpy.data.meshes["Mannequin"]
        
        targets = {
             "torso": torso,
             "mq":    mq,
        }
        
        for name, obj in targets.items():
            key_list = get_filtered_shape_keys(obj, key_filter)

            for key, category, key_name in key_list:
                default = 0
                if key == "squeeze" and category != "small":
                    min = -50
                    if category == "large":
                        default = 30
                else:
                    min = 0
                
                prop_name = f"key_{key}_{category}_{name}"
                
                prop = FloatProperty(
                    name="",
                    default=default,
                    min=min,
                    max=100,
                    soft_min=0,
                    precision=0,
                    subtype="PERCENTAGE"    
                )
                if hasattr(DevkitProps, prop_name):
                    return None
                else:
                    setattr(DevkitProps, prop_name, prop)
                DevkitProps.add_shape_key_drivers(obj, key_name, prop_name)

    @staticmethod
    def feet_key_floats():
        # Creates float properties for feet shape keys controlled by values.
        # Automatically assigns drivers to the models to be controlled by the UI.
        key_filter = ["heels", "cinderella", "miniheels"]
        feet = bpy.data.meshes["Feet"]
        mq = bpy.data.meshes["Mannequin"]
        
        targets = {
             "feet": feet,
             "mq":    mq,
        }
        
        
        for name, obj in targets.items():
            
            key_list = get_filtered_shape_keys(obj, key_filter)
            for key, category, key_name in key_list:      
                
                prop_name = f"key_{key}_{name}"
                
                prop = FloatProperty(
                    name="",
                    default=0,
                    min=0,
                    max=100,
                    precision=0,
                    subtype="PERCENTAGE"    
                )
                if hasattr(DevkitProps, prop_name):
                    return None
                else:
                    setattr(DevkitProps, prop_name, prop)
                DevkitProps.add_shape_key_drivers(obj, key_name, prop_name)

    def add_shape_key_drivers(obj, key_name, prop_name):
        
        if key_name in obj.shape_keys.key_blocks:
            shape_key = obj.shape_keys.key_blocks[key_name]
          
            shape_key.driver_remove("value")
            driver = shape_key.driver_add("value").driver

            driver.type = "SCRIPTED"
            driver.expression = "round(key_value/100, 2)"

            var = driver.variables.new()
            var.name = "key_value"
            var.type = "SINGLE_PROP"
            
            var.targets[0].id_type = "SCENE"
            var.targets[0].id = bpy.data.scenes["Scene"]
            var.targets[0].data_path = f"devkit_props.{prop_name}"  

    @staticmethod
    def controller_drivers():  
        obj = get_object_from_mesh("Controller")
        
        for (name, default, description) in DevkitProps.controller_modifiers:
            name_norm = name.lower().replace(" ", "_") 
            prop_name = f"controller_{name_norm}"

            prop = BoolProperty(
                name="", 
                description=description,
                default=default, 
                )
            
            if hasattr(DevkitProps, prop_name):
                    return None
            else:
                setattr(DevkitProps, prop_name, prop)

            modifier = obj.modifiers[name]
            modifier.driver_remove("show_viewport")
            driver = modifier.driver_add("show_viewport").driver
            
            driver.type = 'AVERAGE'
            var = driver.variables.new()
            var.name = "devkit_toggle"
            var.type
            var.targets[0].id_type = "SCENE"
            var.targets[0].id = bpy.data.scenes["Scene"]
            var.targets[0].data_path = f"devkit_props.{prop_name}"  

    def get_listable_shapes(body_slot):
        items = []

        for shape, (name, slot, shape_category, description, body, key) in ALL_SHAPES.items():
            if body_slot.lower() == slot.lower() and description != "" and shape_category !="":
                items.append((name, name, description))
        return items

    chest_shape_enum: EnumProperty(
        name= "",
        description= "Select a size",
        items=lambda self, context: DevkitProps.get_listable_shapes("Chest")
        )   # type: ignore
    
    shape_mq_chest_bool: BoolProperty(
        name="",
        description="Switches to the mannequin", 
        default=False, 
        ) # type: ignore
    
    shape_mq_legs_bool: BoolProperty(
        name="",
        description="Switches to the mannequin", 
        default=False, 
        )  # type: ignore

    shape_mq_other_bool: BoolProperty(
        name="",
        description="Switches to the mannequin",  
        default=False, 
        )   # type: ignore

    collection_state: bpy.props.CollectionProperty(type=CollectionState) # type: ignore

    object_state: bpy.props.CollectionProperty(type=ObjectState) # type: ignore

    overview_ui: EnumProperty(
        name= "",
        description= "Select a body slot",
        items= [
            ("Body", "Shape", "Body Overview."),
            ("Shape Keys", "View", "Shape Key Overview."),
            ("Settings", "Settings", "Devkit Settings."),
            ("Info", "Info", "Useful info."),
        ]
        )  # type: ignore
    
    export_body_slot: EnumProperty(
        name= "",
        description= "Select a body slot",
        items= [
            ("Chest", "Chest", "Chest export options."),
            ("Legs", "Legs", "Leg export options."),
            ("Hands", "Hands", "Hand export options."),
            ("Feet", "Feet", "Feet export options."),
            ("Chest & Legs", "Chest & Legs", "When you want to export Chest with Leg models.")]
        )  # type: ignore

    export_display_directory: StringProperty(
        name="Export Folder",
        default="Select Export Directory",  
        maxlen=255,
        update=lambda self, context: update_directory('export'),
        ) # type: ignore
    
    export_directory: StringProperty(
        default="Select Export Directory",
        subtype="DIR_PATH", 
        maxlen=255,
        )  # type: ignore
    
    export_total: IntProperty(default=0) # type: ignore

    export_progress: FloatProperty(default=0) # type: ignore

    export_step: IntProperty(default=0) # type: ignore

    export_time: FloatProperty(default=0) # type: ignore

    export_file_name: StringProperty(name="",
        default="",  
        maxlen=255,
        ) # type: ignore

    import_display_directory: StringProperty(
        name="Export Folder",
        default="Select Export Directory",  
        maxlen=255,
        update=lambda self, context: update_directory('import'),
        ) # type: ignore
    
    rename_import: StringProperty(
        name="",
        description="Renames the prefix of the selected meshes",
        default="",
        maxlen=255,
        )  # type: ignore

    file_gltf: BoolProperty(
        name="",
        description="Switch file format", 
        default=False,
        ) # type: ignore
    
    ui_size_category: StringProperty(
        name="",
        subtype="DIR_PATH", 
        maxlen=255,
        )  # type: ignore


class CollectionManager(Operator):
    bl_idname = "ya.collection_manager"
    bl_label = "Export"
    bl_description = "Combines chest options and exports them"

    preset: StringProperty() # type: ignore

    def __init__(self):
        self.props = bpy.context.scene.devkit_props
        self.view_layer = bpy.context.view_layer.layer_collection
        self.collections_state = bpy.context.scene.devkit_props.collection_state
        self.object_state = bpy.context.scene.devkit_props.object_state
        self.coll = bpy.data.collections
        self.export_collections = [
            self.coll["Skeleton"],
            self.coll["Resources"],
            self.coll["Data Sources"],
            self.coll["UV/Weights"],
            self.coll["Nail UVs"],
            self.coll["Rue"],
            self.coll["YAS"],
            self.coll["Piercings"]
        ]
        self.restore = []
        self.obj_visibility = {}
    
    def execute(self, context): 
        if self.preset == "Export":
            self.get_obj_visibility()
            for state in self.collections_state:
                name = state.name
                collection = self.coll[name]
                self.export_collections.append(collection)
            self.restore = self.export_collections
            self.save_current_state()
            bpy.context.view_layer.layer_collection.children['Resources'].hide_viewport = True
            self.props.controller_uv_transfers = True
        elif self.preset == "Restore":
            for state in self.collections_state:
                    name = state.name
                    collection = self.coll[name]
                    self.restore.append(collection)
            self.props.controller_uv_transfers = False
        else:
            self.save_current_state()
            for state in self.collections_state:
                    name = state.name
                    collection = self.coll[name]
                    self.restore.append(collection)

        self.exclude_collections()
        self.restore_obj_visibility()
        
        return {"FINISHED"}

    def save_current_state(self):
        self.collections_state.clear()
        for layer_collection in bpy.context.view_layer.layer_collection.children:
            if not layer_collection.exclude:
                state = self.collections_state.add()
                state.name = layer_collection.name
            for children in layer_collection.children:
                if not children.exclude:
                    state = self.collections_state.add()
                    state.name = children.name
    
    def get_obj_visibility(self):
        self.object_state.clear()
        for obj in bpy.context.scene.objects:
            if obj.visible_get(view_layer=bpy.context.view_layer):
                state = self.object_state.add()
                state.name = obj.name
                state.hide = False
            if obj.hide_get(view_layer=bpy.context.view_layer):
                state = self.object_state.add()
                state.name = obj.name
                state.hide = True
        
    def restore_obj_visibility(self):
        for obj in bpy.context.view_layer.objects:
            for state in self.object_state:
                if obj.name == state.name:
                    obj.hide_set(state.hide)
                    
    def exclude_collections(self):
        all_collections = self.coll
        
        for collection in self.restore:
            self.toggle_collection_exclude(collection, exclude=False)

        for collection in all_collections:
            if collection not in self.restore:
                self.toggle_collection_exclude(collection, exclude=True)
    
    def toggle_collection_exclude(self, collection, exclude=True):
            for layer_collection in bpy.context.view_layer.layer_collection.children:
                self.recursively_toggle_exclude(layer_collection, collection, exclude)

    def recursively_toggle_exclude(self, layer_collection, collection, exclude):
        if layer_collection.collection == collection:
            layer_collection.exclude = exclude
        
        for child in layer_collection.children:
            self.recursively_toggle_exclude(child, collection, exclude)


class ApplyShapes(Operator):
    bl_idname = "ya.apply_shapes"
    bl_label = ""
    bl_description = "Applies the selected option"
    bl_options = {'UNDO'}
    
    key: StringProperty() # type: ignore
    target: StringProperty() # type: ignore
    preset: StringProperty() # type: ignore # shapes, chest_category, leg_size, gen, nails, other

    def execute(self, context):
        apply_mq = self.get_mannequin_category(context)
        preset_target = "torso"

        if apply_mq:
            obj = get_object_from_mesh("Mannequin").data.shape_keys.key_blocks
            preset_target = "mq"
        else:
            obj = self.get_obj() 

        self.get_function(context, obj, preset_target)
        return {"FINISHED"}

    def get_obj(self):
        match self.target:  
            case "Legs":
                return get_object_from_mesh("Waist").data.shape_keys.key_blocks

            case "Hands":
                return get_object_from_mesh("Hands").data.shape_keys.key_blocks

            case "Feet":
                return get_object_from_mesh("Feet").data.shape_keys.key_blocks
            case _:
                return get_object_from_mesh("Torso").data.shape_keys.key_blocks

    def get_mannequin_category(self, context):
        match self.target:   
            case "Legs":
                return context.scene.devkit_props.shape_mq_legs_bool

            case "Hands" | "Feet":
                return context.scene.devkit_props.shape_mq_other_bool
            
            case _:
                return context.scene.devkit_props.shape_mq_chest_bool

    def get_function(self, context, obj, preset_target):
        match self.preset:
            case "chest_category":
                ApplyShapes.mute_chest_shapes(obj, self.key)

            case "leg_size":
                ApplyShapes.mute_leg_shapes(obj, self.key)
            
            case "gen":
                ApplyShapes.mute_gen_shapes(obj, self.key)

            case "nails":
                ApplyShapes.mute_nail_shapes(obj, self.key)

            case "other":   
                if self.key == "Alt Hips" and self.target == "Legs" and not obj["Mini"].mute:
                    self.report({"ERROR"}, "Mini not compatible with alternate hips!")
                    return {"CANCELLED"}
                ApplyShapes.toggle_other(obj, self.key)
            
            case _:
                size = context.scene.devkit_props.chest_shape_enum
                category = get_chest_category(size)
                shape_presets = get_shape_presets(size)
                ApplyShapes.reset_shape_values(preset_target, category)
                ApplyShapes.apply_shape_values(preset_target, category, shape_presets)
                ApplyShapes.mute_chest_shapes(obj, category)
            
                if preset_target == "torso":
                    bpy.context.view_layer.objects.active = get_object_from_mesh("Torso")
                else:
                    bpy.context.view_layer.objects.active = get_object_from_mesh("Mannequin")
                bpy.context.view_layer.update()

    def apply_shape_values(apply_target, category, shape_presets):
        dev_props = bpy.context.scene.devkit_props
        for shape_key in shape_presets:
            norm_key = shape_key.lower().replace(" ","").replace("-","")
            category_lower = category.lower()

            if norm_key == "sag" and category_lower == "large":
                category_lower = "omoi"
            
            prop = f"key_{norm_key}_{category_lower}_{apply_target}"
            if hasattr(dev_props, prop):
                setattr(dev_props, prop, 100 * shape_presets[shape_key])
            
    def reset_shape_values(apply_target, category):
        reset = get_shape_presets(category)
        dev_props = bpy.context.scene.devkit_props

        for reset_key in reset:
            norm_key = reset_key.lower().replace(" ","").replace("-","")
            category_lower = category.lower()

            if norm_key == "sag" and category_lower == "large":
                category_lower = "omoi"
            
            prop = f"key_{norm_key}_{category_lower}_{apply_target}"
            if hasattr(dev_props, prop):
                setattr(dev_props, prop, 100 * reset[reset_key])
                             
    def mute_chest_shapes(apply_target, category):
        category_mute_mapping = {
            "Large": (True, True), 
            "Medium": (False, True), 
            "Small": (True, False),   
        }

        # Gets category and its bools
        mute_medium, mute_small = category_mute_mapping.get(category, (True, True))

        # Apply the mute states to the target
        apply_target[get_chest_size_keys("Medium")].mute = mute_medium
        apply_target[get_chest_size_keys("Small")].mute = mute_small

    def mute_gen_shapes(apply_target, gen: str):
        gen_mute_mapping = {
            "Gen A": (True, True, True), 
            "Gen B": (False, True, True), 
            "Gen C": (True, False, True),   
            "Gen SFW": (True, True, False),   
        }

        # Gets category and its bools
        mute_b, mute_c, mute_sfw = gen_mute_mapping.get(gen, (True, True, True))

        # Apply the mute states to the target
        apply_target["Gen B"].mute = mute_b
        apply_target["Gen C"].mute = mute_c
        apply_target["Gen SFW"].mute = mute_sfw

    def mute_leg_shapes(apply_target, size: str):
        size_mute_mapping = {
            "Melon": (True, True), 
            "Skull": (False, True), 
            "Mini": (True, False),   
        }

        # Gets category and its bools
        mute_skull, mute_mini = size_mute_mapping.get(size, (True, True))

        # Apply the mute states to the target
        apply_target["Skull Crushers"].mute = mute_skull
        apply_target["Mini"].mute = mute_mini

        if not mute_mini:
            apply_target["Hip Dips (for YAB)"].mute = True
            apply_target["Less Hip Dips (for Rue)"].mute = True

    def mute_nail_shapes(apply_target, nails: str):
        nails_mute_mapping = {
            "Long": (True, True, True), 
            "Short": (False, True, True), 
            "Ballerina": (True, False, True), 
            "Stabbies": (True, True, False), 
             
        }
        # Gets category and its bools
        mute_short, mute_ballerina, mute_stabbies = nails_mute_mapping.get(nails, (True, True, True))

        # Apply the mute states to the target
        apply_target["Short Nails"].mute = mute_short
        apply_target["Ballerina"].mute = mute_ballerina
        apply_target["Stabbies"].mute = mute_stabbies
    
    def toggle_other(apply_target, key: str):
        if key == "Rue Other":
            key = "Rue"
       
        if apply_target[key].mute:
            apply_target[key].mute = False
        else:
            apply_target[key].mute = True


class ApplyVisibility(Operator):
    bl_idname = "ya.apply_visibility"
    bl_label = ""
    bl_description = "Toggles the visibility of the collection"
    bl_options = {'UNDO'}

    key: StringProperty() # type: ignore
    target: StringProperty() # type: ignore

    def execute(self, context):
        collection = bpy.context.view_layer.layer_collection.children

        match self.target:
            case "Feet":
                self.feet_visibility(collection)
            case "Hands":
                self.hand_visibility(collection)
            case "Chest":
                self.chest_visibility(collection)
            case "Legs":
                self.legs_visibility(collection)
        return {"FINISHED"}
    
    def chest_visibility(self, collection):
        if collection["Chest"].exclude:
            collection["Chest"].exclude = False
        else:
            collection["Chest"].exclude = True

    def legs_visibility(self, collection):
        if collection["Legs"].exclude:
            collection["Legs"].exclude = False
        else:
            collection["Legs"].exclude = True

    def feet_visibility(self, collection):
        if self.key == "Nails": 
                if collection["Feet"].children["Toenails"].exclude:
                    collection["Feet"].children["Toenails"].exclude = False
                else:
                    collection["Feet"].children["Toenails"].exclude = True

        elif self.key == "Clawsies":
            if collection["Feet"].children["Toe Clawsies"].exclude:
                collection["Feet"].children["Toe Clawsies"].exclude = False
            else:
                collection["Feet"].children["Toe Clawsies"].exclude = True
                
        else:
            if collection["Feet"].exclude:
                collection["Feet"].exclude = False
            else:
                collection["Feet"].exclude = True
    
    def hand_visibility(self, collection):
        if self.key == "Nails": 
                if collection["Hands"].children["Nails"].exclude:
                    collection["Hands"].children["Nails"].exclude = False
                else:
                    collection["Hands"].children["Nails"].exclude = True

        elif self.key == "Clawsies":
            if collection["Hands"].children["Clawsies"].exclude:
                collection["Hands"].children["Clawsies"].exclude = False
            else:
                collection["Hands"].children["Clawsies"].exclude = True

        else:
            if collection["Hands"].exclude:
                collection["Hands"].exclude = False
            else:
                collection["Hands"].exclude = True


def check_triangulation():
    not_triangulated = []

    for obj in bpy.context.scene.objects:
        if obj.visible_get(view_layer=bpy.context.view_layer) and obj.type == "MESH":
            triangulated = False
            for modifier in reversed(obj.modifiers):
                if modifier.type == "TRIANGULATE" and modifier.show_viewport:
                    triangulated = True
                    break
            if not triangulated:
                not_triangulated.append(obj.name)
    
    if not_triangulated:
        return False, not_triangulated
    else:
        return True, ""

def force_yas():
    devkit = bpy.context.scene.devkit_props
    for obj in bpy.context.scene.objects:
        if obj.visible_get(view_layer=bpy.context.view_layer) and obj.type == "MESH":
            if obj.data.name == "Torso":
                devkit.controller_yas_chest = True
            if obj.data.name == "Waist":
                devkit.controller_yas_legs = True
            if obj.data.name == "Hands":
                devkit.controller_yas_hands = True
            if obj.data.name == "Feet":
                devkit.controller_yas_feet = True

def shape_key_keeper():
    bpy.ops.object.select_all(action="DESELECT")
    visible_obj = visible_meshobj()
    mesh_modifiers = ["MIRROR", "SUBSURF", "MASK", "WELD"]
    to_reset = []
    to_delete = []
    to_join = []
    
    for original_obj in visible_obj:
        old_name = original_obj.name
        split = old_name.split()
        split[0] = "ShapeKey"
        new_name = " ".join(split)
        xiv_key = [key for key in original_obj.data.shape_keys.key_blocks if key.name.startswith("shp")]

        if xiv_key:
            original_obj.select_set(state=True)
            bpy.context.view_layer.objects.active = original_obj

            bpy.ops.object.duplicate()
            original_obj.hide_set(state=True)
            shapekey_obj = bpy.context.selected_objects[0]
            shapekey_obj.name = new_name
            to_reset.append(original_obj)
            to_delete.append(shapekey_obj)

        for key in xiv_key:
            shapekey_obj.select_set(state=True)
            bpy.context.view_layer.objects.active = shapekey_obj

            bpy.ops.object.duplicate()
            shapekey_dupe = bpy.context.selected_objects[0]
            shapekey_dupe.data.shape_keys.key_blocks[key.name].value = 1.0
            bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
            shapekey_dupe.name = key.name

            shapekey_dupe.select_set(state=True)
            bpy.context.view_layer.objects.active = shapekey_dupe
            for modifier in shapekey_dupe.modifiers:
                if any(modifier.type in mesh_modifiers for m in mesh_modifiers):
                    try:
                        bpy.ops.object.modifier_apply(modifier=modifier.name)
                    except:
                        bpy.ops.object.modifier_remove(modifier=modifier.name)
                elif modifier.type != "ARMATURE":
                    bpy.ops.object.modifier_remove(modifier=modifier.name)
            
            to_join.append(shapekey_dupe)
            bpy.ops.object.select_all(action="DESELECT")

        if to_join:
            shapekey_obj.select_set(state=True)
            bpy.context.view_layer.objects.active = shapekey_obj
            bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
            for modifier in shapekey_obj.modifiers:
                if modifier.type != "ARMATURE" and modifier.show_viewport:
                    try:
                        bpy.ops.object.modifier_apply(modifier=modifier.name)
                    except:
                        bpy.ops.object.modifier_remove(modifier=modifier.name)
                elif modifier.type != "ARMATURE":
                    bpy.ops.object.modifier_remove(modifier=modifier.name)
            for dupe in to_join:
                dupe.select_set(state=True)
                bpy.ops.object.join_shapes()
                bpy.data.objects.remove(dupe, do_unlink=True, do_id_user=True, do_ui_user=True)
            to_join = []
        bpy.ops.object.select_all(action="DESELECT")

    return to_reset, to_delete

def restore_pre_shape_key(to_reset, to_delete):
    for obj in to_delete:
        bpy.data.objects.remove(obj, do_unlink=True, do_id_user=True, do_ui_user=True)
    
    for obj in to_reset:
        obj.hide_set(state=False)

def ivcs_mune(visible_obj, yas=False):
    for obj in visible_obj:
        for group in obj.vertex_groups:
            try:
                if yas:
                    if group.name == "j_mune_r":
                        group.name = "iv_c_mune_r"
                    if group.name == "j_mune_l":
                        group.name = "iv_c_mune_l"
                else:
                    if group.name == "iv_c_mune_r":
                            group.name = "j_mune_r"
                    if group.name == "iv_c_mune_l":
                        group.name = "j_mune_l"
            except:
                continue
      
    
class SimpleExport(Operator):
    bl_idname = "ya.simple_export"
    bl_label = "Simple Export"
    bl_description = "Exports single model based on visible objects"
    bl_options = {'REGISTER'}

    user_input: StringProperty(name="File Name", default="") # type: ignore

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"
    
    def __init__(self):
        self.props = bpy.context.scene.devkit_props
        self.check_tris = self.props.check_tris
        self.force_yas = self.props.force_yas
        self.keep_shapekeys = self.props.keep_shapekeys
        self.gltf = self.props.file_gltf 

    def invoke(self, context, event):
        if self.check_tris:
            triangulated, obj = check_triangulation()
            if not triangulated:
                self.report({'ERROR'}, f"Not Triangulated: {', '.join(obj)}")
                return {'CANCELLED'} 
            
        bpy.context.window_manager.invoke_props_dialog(self, confirm_text="Export")
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if self.force_yas:
            force_yas()
        
        self.props.controller_uv_transfers = True

        directory = context.scene.devkit_props.export_directory
        export_path = os.path.join(directory, self.user_input)
        export_settings = FileExport.get_export_settings(self.gltf)

        obj = get_object_from_mesh("Controller")
        yas = obj.modifiers["YAS Chest"].show_viewport
        visible_obj = visible_meshobj()
        ivcs_mune(visible_obj, yas)

        if self.keep_shapekeys:
            to_reset, to_delete = shape_key_keeper()
        
        if self.gltf:
            bpy.ops.export_scene.gltf(filepath=export_path + ".gltf", **export_settings)
        else:
            bpy.ops.export_scene.fbx(filepath=export_path + ".fbx", **export_settings)

        if self.keep_shapekeys:
            restore_pre_shape_key(to_reset, to_delete)

        ivcs_mune(visible_obj)
        self.props.controller_uv_transfers = False
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "user_input")

class BatchQueue(Operator):
    bl_idname = "ya.batch_queue"
    bl_label = "Export"
    bl_description = "Exports your scene based on your selections"
    bl_options = {'UNDO'}

    ob_mesh_dict = {
            "Chest": "Torso", 
            "Legs": "Waist", 
            "Hands": "Hands",
            "Feet": "Feet"
            }
    
    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def __init__(self):
        props = bpy.context.scene.devkit_props
        self.check_tris = props.check_tris
        self.force_yas = props.force_yas
        self.subfolder = props.create_subfolder
        self.export_directory = Path(props.export_directory)
        self.body_slot = props.export_body_slot
        self.selected_directory = props.export_directory
        self.size_options = self.get_size_options()

        self.leg_sizes = {
            "Melon": self.size_options["Melon"],
            "Skull": self.size_options["Skull"], 
            "Mini Legs": self.size_options["Mini Legs"]
            }

        self.queue = []
        self.leg_queue = []
        
    def execute(self, context):
        props = bpy.context.scene.devkit_props
        props.controller_uv_transfers = True
        if self.check_tris:
            triangulated, obj = check_triangulation()
            if not triangulated:
                self.report({'ERROR'}, f"Not Triangulated: {', '.join(obj)}")
                return {'CANCELLED'} 
        if self.force_yas:
            force_yas()
        
        if self.subfolder:
            Path.mkdir(self.export_directory / self.body_slot, exist_ok=True)
        
        if not os.path.exists(self.selected_directory):
            self.report({'ERROR'}, "No directory selected for export!")
            return {'CANCELLED'} 

        if self.body_slot == "Chest & Legs":
            self.actual_combinations = self.shape_combinations("Chest")
            self.calculate_queue("Chest")
            self.actual_combinations = self.shape_combinations("Legs")
            self.calculate_queue("Legs")
        else:
            self.actual_combinations = self.shape_combinations(self.body_slot)
            self.calculate_queue(self.body_slot)

        if "Legs" in self.body_slot:
            gen_options = len(self.actual_combinations.keys())
        else:
            gen_options = 0

        if self.queue == []:
            self.report({'ERROR'}, "No valid combinations!")
            return {'CANCELLED'} 
        
        if self.body_slot == "Chest & Legs":
            if self.leg_queue == []:
                self.report({'ERROR'}, "No valid combinations!")
                return {'CANCELLED'} 
            
        self.collection_state()
        bpy.ops.ya.collection_manager(preset="Export")

        if "Chest" in self.body_slot:
            obj = get_object_from_mesh("Controller")
            yas = obj.modifiers["YAS Chest"].show_viewport
            visible_obj = visible_meshobj()
            ivcs_mune(visible_obj, yas)

        props.export_total = len(self.queue)
        BatchQueue.process_queue(context, self.queue, self.leg_queue, self.body_slot)
        return {'RUNNING_MODAL'}
    
    # The following functions is executed to establish the queue and valid options 
    # before handing all variables over to queue processing

    def collection_state(self):
        collection_state = bpy.context.scene.devkit_props.collection_state
        collection_state.clear()
        collections = []
        match self.body_slot:
            case "Chest":
                collections = ["Chest"]
                if self.size_options["Piercings"]:
                    collections.append("Nipple Piercings")

            case "Legs":
                collections = ["Legs"]
                if self.size_options["Pubes"]:
                    collections.append("Pubes")

            case "Chest & Legs":
                collections = ["Chest", "Legs"]
                if self.size_options["Piercings"]:
                    collections.append("Nipple Piercings")
                if self.size_options["Pubes"]:
                    collections.append("Pubes")

            case "Hands":
                collections = ["Hands"]

            case "Feet":
                collections = ["Feet"]

        for name in collections:
            state = collection_state.add()
            state.name = name

    def get_size_options(self):
        options = {}
        prop = bpy.context.scene.devkit_props

        for shape, (name, slot, shape_category, description, body, key) in ALL_SHAPES.items():
            slot_lower = slot.lower().replace("/", " ")
            name_lower = name.lower().replace(" ", "_")

            prop_name = f"export_{name_lower}_{slot_lower}_bool"

            if hasattr(prop, prop_name):
                options[shape] = getattr(prop, prop_name)

        return options

    def calculate_queue(self, body_slot):
        mesh = self.ob_mesh_dict[body_slot]
        target = get_object_from_mesh(mesh).data.shape_keys.key_blocks

        leg_sizes = [key for key in self.leg_sizes.keys() if self.leg_sizes[key]]

        if body_slot != "Legs":
            for size, options_groups in self.actual_combinations.items(): 
                for options in options_groups:
                    name = BatchQueue.name_generator(options, size, "", 0, body_slot)
                    self.queue.append((name, options, size, "", target))
        else:
            # Legs need different handling due to genitalia combos     
            for size in leg_sizes:
                gen_options = len(self.actual_combinations.keys())
                for gen, options_groups in self.actual_combinations.items(): 
                    for options in options_groups:
                        if size == "Mini Legs" and any("Hip Dips" in option for option in options):
                            continue
                        name = BatchQueue.name_generator(options, size, gen, gen_options, body_slot) 
                        
                        if self.body_slot == "Chest & Legs":
                            self.leg_queue.append((name, options, size, gen, target))
                        else:
                            self.queue.append((name, options, size, gen, target))
        
    def shape_combinations(self, body_slot):
        possible_parts  = [
            "Rue Legs", "Small Butt", "Soft Butt", "Hip Dips",
            "Buff", "Rue", 
            "Rue Hands", "YAB Hands", 
            "Clawsies"
            ]
        actual_parts = []
        all_combinations = set()
        actual_combinations = {}

        
        #Excludes possible parts based on which body slot they belong to
        for shape, (name, slot, category, description, body, key) in ALL_SHAPES.items():
            if any(shape in possible_parts for parts in possible_parts) and body_slot == slot and self.size_options[shape]:
                actual_parts.append(shape)  

        for r in range(0, len(actual_parts) + 1):
            if body_slot == "Hands":
                r = 1
            all_combinations.update(combinations(actual_parts, r))

        all_combinations = tuple(all_combinations)  

        for shape, (name, slot, category, description, body, key) in ALL_SHAPES.items():
            if body_slot == "Legs":
                if self.size_options[shape] and category == "Vagina":
                    actual_combinations[shape] = all_combinations

            elif body_slot == "Chest" and slot == "Chest":
                if self.size_options[shape] and category != "":
                    actual_combinations[shape] = all_combinations

            elif body_slot == "Hands":
                if self.size_options[shape] and category == "Nails":
                    actual_combinations[shape] = all_combinations

            elif body_slot == "Feet":
                if self.size_options[shape] and category == "Feet":
                    actual_combinations[shape] = all_combinations

        return actual_combinations
                       
    def name_generator(options, size, gen, gen_options, body_slot):
        yiggle = bpy.context.scene.devkit_props.force_yas

        if body_slot == "Chest & Legs":
            body_slot = "Chest"
        if yiggle:
            file_names = ["Yiggle"]
        else:
            file_names = []
        
        gen_name = None

        #Loops over the options and applies the shapes name to file_names
        for shape, (name, slot, category, description, body, key) in ALL_SHAPES.items():
            if any(shape in options for option in options) and not shape.startswith("Gen") and name != "YAB":
                if name == "Hip Dips":
                    name = "Alt Hip" 
                file_names.append(name)
        
        # Checks if any Genitalia shapes and applies the shortened name 
        # Ignores gen_name if only one option is selected
        if gen != None and gen.startswith("Gen") and gen_options > 1:
            gen_name = gen.replace("Gen ","")       
        
        # Tweaks name output for the sizes
        size_name = size.replace(" Legs", "").replace("YAB ", "")
        if size == "Skull":
            size_name = "Skull Crushers"
        if size == "Melon":
            size_name = "Watermelon Crushers"
        if size == "Short" or size == "Long":
            size_name = size + " Nails"

        file_names.append(size_name)

        if body_slot == "Feet":
            file_names = reversed(file_names)

        if gen_name != None:
            file_names.append(gen_name)
        
        return " - ".join(list(file_names))
    
    # These functions are responsible for processing the queue.
    # Export queue is running on a timer interval until the queue is empty.

    def process_queue(context, queue, leg_queue, body_slot):
        global is_exporting
        is_exporting = False
        start_time = time.time()

        # randomising the list gives a much better time estimate
        random.shuffle(queue)
        BatchQueue.progress_tracker(queue)
        callback = partial(BatchQueue.export_queue, context, queue, leg_queue, body_slot, start_time)
       
        bpy.app.timers.register(callback, first_interval=0.5) 
        
    def export_queue(context, queue, leg_queue, body_slot, start_time):
        props = context.scene.devkit_props
        collection = context.view_layer.layer_collection.children
        global is_exporting

        if is_exporting:
            return 0.1
        is_exporting = True

        main_name, options, size, gen, target = queue.pop()
       
        BatchQueue.reset_model_state(body_slot, target)
        BatchQueue.apply_model_state(options, size, gen, body_slot, target)
        props.export_file_name = main_name

        if body_slot == "Hands":

            if size == "Straight" or size == "Curved":
                collection["Hands"].children["Clawsies"].exclude = False
                collection["Hands"].children["Nails"].exclude = True
                collection["Hands"].children["Nails"].exclude = True
    
            else:
                collection["Hands"].children["Clawsies"].exclude = True
                collection["Hands"].children["Nails"].exclude = False
                collection["Hands"].children["Nails"].children["Practical Uses"].exclude = False
        
        if body_slot == "Feet":

            if "Clawsies" in options:
                collection["Feet"].children["Toe Clawsies"].exclude = False
                collection["Feet"].children["Toenails"].exclude = True
                
    
            else:
                collection["Feet"].children["Toe Clawsies"].exclude = True
                collection["Feet"].children["Toenails"].exclude = False
        
        if body_slot == "Chest & Legs":
            exported = []
            for leg_task in leg_queue:
                leg_name, options, size, gen, leg_target = leg_task
                # rue_match stops non-rue tops to be used with rue legs and vice versa
                if BatchQueue.check_rue_match(options, main_name):
                    body_slot = "Legs"
                    
                    BatchQueue.reset_model_state(body_slot, leg_target)
                    BatchQueue.apply_model_state(options, size, gen, body_slot, leg_target)

                    combined_name = main_name + " - " + leg_name
                    final_name = BatchQueue.clean_file_name(combined_name)
                    if props.keep_shapekeys:
                        to_reset, to_delete = shape_key_keeper()
                    if not any(final_name in name for name in exported):
                        exported.append(final_name)
                        bpy.ops.ya.file_export(file_name=final_name, body_slot="Chest & Legs")
        
        else:
            if props.keep_shapekeys:
                to_reset, to_delete = shape_key_keeper()
            bpy.ops.ya.file_export(file_name=main_name, body_slot=body_slot)

        is_exporting = False

        if queue:
            end_time = time.time()
            duration = end_time - start_time
            props.export_time = duration
            BatchQueue.progress_tracker(queue)
            if props.keep_shapekeys:
                restore_pre_shape_key(to_reset, to_delete)
            return 0.1
        else:
            if props.keep_shapekeys:
                restore_pre_shape_key(to_reset, to_delete)
            if body_slot == "Chest":
                visible_obj = visible_meshobj()
                ivcs_mune(visible_obj)
            bpy.ops.ya.collection_manager(preset="Restore")
            props.controller_uv_transfers = False
            BatchQueue.progress_reset(props)
            return None

    # These functions are responsible for applying the correct model state and appropriate file name.
    # They are called from the export_queue function.

    def check_rue_match (options, file_name):
        '''This function checks the name of the leg export vs the chest export and makes sure only 
        rue tops and bottoms are combined'''
        if "Rue" in file_name:
            if any("Rue Legs" in option for option in options):
                return True
            else:
                return False
        elif any("Rue Legs" in option for option in options):
            return False
    
        return True

    def clean_file_name (file_name:str):
        parts = file_name.split(" - ")
        rue_match = False
        new_parts = []

        for part in parts:
            if part == "Rue":
                if rue_match:
                    continue
                rue_match = True
            new_parts.append(part)
            
        
        file_name = " - ".join(new_parts)

        return file_name

        # first = file_name.find("Rue - ")

        # second = file_name.find("Rue - ", first + len("Rue - "))

        # if second == -1:
        #     return file_name
            
        
        # return file_name[:second] + file_name[second + len("Rue - "):]

    def apply_model_state(options, size, gen, body_slot, ob):
        if body_slot == "Chest & Legs":
            body_slot = "Chest"

        for shape, (name, slot, category, description, body, key) in ALL_SHAPES.items():

            if shape == size and key != "":
                ob[key].mute = False

            if any(shape in options for option in options):
                if key != "":
                    ob[key].mute = False

        # Adds the shape value presets alongside size toggles
        if body_slot == "Chest":
            keys_to_filter = ["Squeeze", "Squish", "Push-Up", "Nip Nops"]
            preset = get_shape_presets(size)
            filtered_preset = {}
           

            for key in preset.keys():
                if not any(key.endswith(sub) for sub in keys_to_filter):
                    filtered_preset[key] = preset[key]

            category = ALL_SHAPES[size][2]
            ApplyShapes.mute_chest_shapes(ob, category)
            ApplyShapes.apply_shape_values("torso", category, filtered_preset)
            bpy.context.view_layer.objects.active = get_object_from_mesh("Torso")
            bpy.context.view_layer.update()
                
        
        if gen != None and gen.startswith("Gen") and gen != "Gen A":
            ob[gen].mute = False

    def reset_model_state(body_slot, ob):
        if body_slot == "Chest & Legs":
            body_slot = "Chest"

        reset_shape_keys = []

        for shape, (name, slot, shape_category, description, body, key) in ALL_SHAPES.items():
            if key != "" and slot == body_slot:
                if shape == "Hip Dips":
                    reset_shape_keys.append("Hip Dips (for YAB)")
                    reset_shape_keys.append("Less Hip Dips (for Rue)")
                else:
                    reset_shape_keys.append(key)

        for key in reset_shape_keys:   
            ob[key].mute = True

    def progress_tracker(queue):
        props = bpy.context.scene.devkit_props
        props.export_progress = (props.export_total - len(queue)) / props.export_total
        props.export_step = (props.export_total - len(queue)) 
        props.export_file_name = queue[-1][0]

    def progress_reset(props):
        props.export_total = 0
        props.export_progress = 0
        props.export_step = 0
        props.export_time = 0
        props.export_file_name = ""


class FileExport(Operator):
    bl_idname = "ya.file_export"
    bl_label = "Export"
    bl_description = ""

    file_name: StringProperty() # type: ignore
    body_slot: StringProperty() # type: ignore

    def execute(self, context):
            FileExport.export_template(context, self.file_name, self.body_slot)
            return {'FINISHED'}

    def export_template(context, file_name, body_slot):
        gltf = context.scene.devkit_props.file_gltf
        subfolder = bpy.context.scene.devkit_props.create_subfolder
        selected_directory = Path(context.scene.devkit_props.export_directory)

        if subfolder:
            export_path = str(selected_directory / body_slot / file_name)
        else:
            export_path = str(selected_directory / file_name)
        export_settings = FileExport.get_export_settings(gltf)

        if gltf:
            bpy.ops.export_scene.gltf(filepath=export_path + ".gltf", **export_settings)
        else:
            bpy.ops.export_scene.fbx(filepath=export_path + ".fbx", **export_settings)
        
    def get_export_settings(gltf):
        if gltf:
            return {
                "export_format": "GLTF_SEPARATE", 
                "export_texture_dir": "GLTF Textures",
                "use_selection": False,
                "use_active_collection": False,
                "export_animations": False,
                "export_extras": True,
                "export_leaf_bone": False,
                "export_apply": True,
                "use_visible": True,
                "export_try_sparse_sk": False,
                "export_attributes": True,
                "export_tangents": True,
                "export_influence_nb": 8,
                "export_active_vertex_color_when_no_material": True,
                "export_all_vertex_colors": True,
                "export_image_format": "NONE"
            }
        
        else:
            return {
                "use_selection": False,
                "use_active_collection": False,
                "bake_anim": False,
                "use_custom_props": True,
                "use_triangles": False,
                "add_leaf_bones": False,
                "use_mesh_modifiers": True,
                "use_visible": True,
            }


class SimpleImport(Operator):
    bl_idname = "ya.simple_import"
    bl_label = "Open Import Window"
    bl_description = "Import a file in the selected format"
    bl_options = {'UNDO'}

    preset: StringProperty() # type: ignore

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"
    
    def execute(self, context):
        gltf = context.scene.devkit_props.file_gltf
        if gltf:
            bpy.ops.import_scene.gltf('INVOKE_DEFAULT')
        else:
            bpy.ops.import_scene.fbx('INVOKE_DEFAULT', ignore_leaf_bones=True)

        return {"FINISHED"}
    

class SimpleCleanUp(Operator):
    bl_idname = "ya.simple_cleanup"
    bl_label = "Open Import Window"
    bl_description = "Cleanup the selected files"
    bl_options = {'UNDO'}

    preset: StringProperty() # type: ignore

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"
    
    def execute(self, context):
        props = context.scene.devkit_props
        if props.fix_parent:
            self.fix_parent()
        if props.update_material:
            self.update_material()
        if props.rename_import != "":
            self.rename_import()
        
        return {"FINISHED"}

    def update_material(self):
        selected = bpy.context.selected_objects
        for obj in selected:
            bpy.context.view_layer.objects.active = obj
            if obj.type == "MESH":
                material = obj.active_material
                material.surface_render_method = "DITHERED"
                material.use_backface_culling = True

    def fix_parent(self):
        selected = bpy.context.selected_objects
        for obj in selected:
            bpy.context.view_layer.objects.active = obj
            old_transform = obj.matrix_world.copy()
            obj.parent = bpy.data.objects["Skeleton"]
            obj.matrix_world = old_transform
            bpy.ops.object.transform_apply(location=True, scale=True, rotation=True)
            if obj.type != "MESH":
                bpy.data.objects.remove(obj, do_unlink=True, do_id_user=True, do_ui_user=True)

    def rename_import(self):
        selected = bpy.context.selected_objects
        for obj  in selected:
            bpy.context.view_layer.objects.active = obj
            if obj.type == "MESH":
                split = obj.name.split()
                split[0] = bpy.context.scene.devkit_props.rename_import
                obj.name = " ".join(split)


class DirSelector(Operator):
    bl_idname = "ya.dir_selector"
    bl_label = "Select Folder"
    bl_description = "Select file or directory. Hold Alt to open the folder"
    
    directory: StringProperty() # type: ignore
    category: StringProperty() # type: ignore

    def invoke(self, context, event):
        actual_dir = getattr(context.scene.devkit_props, f"{self.category}_directory", "")     

        if event.alt and event.type == "LEFTMOUSE" and os.path.isdir(actual_dir):
            os.startfile(actual_dir)
        elif event.type == "LEFTMOUSE":
            context.window_manager.fileselect_add(self)


        else:
             self.report({"ERROR"}, "Not a directory!")
    
        return {"RUNNING_MODAL"}
    

    def execute(self, context):
        actual_dir_prop = f"{self.category}_directory"
        display_dir_prop = f"{self.category}_display_directory"
        selected_file = Path(self.directory)  

        if selected_file.is_dir():
            setattr(context.scene.devkit_props, actual_dir_prop, str(selected_file))
            setattr(context.scene.devkit_props, display_dir_prop, str(Path(*selected_file.parts[-3:])))
            self.report({"INFO"}, f"Directory selected: {selected_file}")
        
        else:
            self.report({"ERROR"}, "Not a valid path!")
        
        return {'FINISHED'}
    

class BodyPartSlot(Operator):
    bl_idname = "ya.set_body_part"
    bl_label = "Select body slot to export."
    bl_description = "The icons almost make sense"

    body_part: StringProperty() # type: ignore

    def execute(self, context):
        # Update the export_body_part with the selected body part
        context.scene.devkit_props.export_body_slot = self.body_part
        return {'FINISHED'}
    
    
class UISelector(Operator):
    bl_idname = "ya.set_ui"
    bl_label = "Choose your main menu."
    bl_description = "Gives different overviews of the devkit"

    overview: StringProperty() # type: ignore

    def execute(self, context):
        # Update the export_body_part with the selected body part
        context.scene.devkit_props.overview_ui = self.overview
        return {'FINISHED'}


class Overview(Panel):
    bl_idname = "VIEW3D_PT_YA_Overview"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Devkit"
    bl_label = "Yet Another Overview"
    bl_order = 0

    def draw(self, context):
        mq = get_object_from_mesh("Mannequin")
        torso = get_object_from_mesh("Torso")
        legs = get_object_from_mesh("Waist")
        hands = get_object_from_mesh("Hands")
        feet = get_object_from_mesh("Feet")
        controller = get_object_from_mesh("Controller")

        ob = self.collection_context(context)
        key = ob.data.shape_keys
        layout = self.layout
        label_name = ob.data.name
        scene = context.scene
        section_prop = scene.devkit_props

        box = layout.box()
        row = box.row(align=True)
        
        row.label(text=f"Menu: {section_prop.overview_ui}")
        button_row = row.row(align=True)

        options =[
            ("Body", "OUTLINER_OB_ARMATURE"),
            ("Shape Keys", "MESH_DATA"),
            ("Settings", "SETTINGS"),
            ("Info", "INFO"),
            ]
        
        self.ui_category_buttons(button_row, section_prop, options)
        
        layout.separator(factor=1, type="LINE")

        # SHAPE MENUS
        
        if section_prop.overview_ui == "Shape Keys":
            box = layout.box()
            row = box.row(align=True)
            row.label(text=f"{label_name}:")
            text = "Collection" if section_prop.button_dynamic_view else "Active"
            row.prop(section_prop, "button_dynamic_view", text=text, icon="HIDE_OFF")
          
            row = layout.row()
            row.template_list(
                "MESH_UL_shape_keys", 
                "", 
                key, 
                "key_blocks", 
                ob, 
                "active_shape_key_index", 
                rows=10)
        
        # BODY
        
        if section_prop.overview_ui == "Body":
            
            # CHEST

            button = section_prop.button_chest_shapes
            chest_col = bpy.context.view_layer.layer_collection.children["Chest"].exclude

            box = layout.box()
            row = box.row(align=True)
            
            icon = 'TRIA_DOWN' if button else 'TRIA_RIGHT'
            row.prop(section_prop, "button_chest_shapes", text="", icon=icon, emboss=False)
            row.label(text="Chest")
            
            button_row = row.row(align=True)
            if not section_prop.shape_mq_other_bool:
                icon = "HIDE_ON" if chest_col else "HIDE_OFF"
                chest_op = button_row.operator("ya.apply_visibility", text="", icon=icon, depress=not chest_col)
                chest_op.target = "Chest"
                chest_op.key = ""
            button_row.prop(section_prop, "shape_mq_chest_bool", text="", icon="ARMATURE_DATA")
            

            if button:
                self.chest_shapes(layout, section_prop, mq, torso)

            # LEGS

            button = section_prop.button_leg_shapes
            leg_col = bpy.context.view_layer.layer_collection.children["Legs"].exclude

            box = layout.box()
            row = box.row(align=True)
            
            icon = 'TRIA_DOWN' if button else 'TRIA_RIGHT'
            row.prop(section_prop, "button_leg_shapes", text="", icon=icon, emboss=False)
            row.label(text="Legs")
            
            button_row = row.row(align=True)
            if not section_prop.shape_mq_other_bool:
                icon = "HIDE_ON" if leg_col else "HIDE_OFF"
                leg_op = button_row.operator("ya.apply_visibility", text="", icon=icon, depress=not leg_col)
                leg_op.target = "Legs"
                leg_op.key = ""
            button_row.prop(section_prop, "shape_mq_legs_bool", text="", icon="ARMATURE_DATA")

            if button:
                self.leg_shapes(layout, section_prop, mq, legs)
            
            # OTHER

            button = section_prop.button_other_shapes

            box = layout.box()
            row = box.row(align=True)
            icon = 'TRIA_DOWN' if button else 'TRIA_RIGHT'
            row.prop(section_prop, "button_other_shapes", text="", icon=icon, emboss=False)
            row.label(text="Hands/Feet")
            
            button_row = row.row(align=True)
            button_row.prop(section_prop, "shape_mq_other_bool", text="", icon="ARMATURE_DATA")

            if button:
                self.other_shapes(layout, section_prop, mq, hands, feet)

        # YAS MENU
        if section_prop.overview_ui == "Body" or section_prop.overview_ui == "Shape Keys":
            button = section_prop.button_yas_expand                          

            box = layout.box()
            row = box.row(align=True)
            row.alignment = 'LEFT'
            
            icon = 'TRIA_DOWN' if button else 'TRIA_RIGHT'
            row.prop(section_prop, "button_yas_expand", text="", icon=icon, emboss=False)
            row.label(text="Yet Another Skeleton")

            if button:
                self.yas_menu(layout, section_prop)

        # SETTINGS

        if section_prop.overview_ui == "Settings":
            row = layout.row(align=True)
            row.alignment = "CENTER"
            row.prop(section_prop, "controller_uv_transfers", text="UV Transfers")
            row.prop(section_prop, "controller_triangulation", text="Triangulation")

            layout.separator(factor=1, type="LINE")

            row = layout.row(align=True)
            row.alignment = "CENTER"
            col = row.column(align=True)
            col.operator("outliner.orphans_purge", text="Delete Unused Data")
            col.operator("script.reload", text="Reload Scripts")
        
        #INFO

        if section_prop.overview_ui == "Info":
            box = layout.box()
            row = box.row(align=True)
            row.alignment = "CENTER"
            row.label(text="My Links:")
            box = layout.box()
            row = box.row(align=True)
            col = row.column()
            col.operator("wm.url_open", text="Devkit Guide").url = "https://docs.google.com/document/d/1WRKKUZZsAzDOTpt6F7iJkN8TDvwDBm0s0Z4DHdWqT_o/edit?usp=sharing"
            col.separator(factor=1, type="LINE")
            col.operator("wm.url_open", text="Discord").url = "https://discord.gg/bnuuybooty"
            col.operator("wm.url_open", text="Ko-Fi").url = "https://ko-fi.com/yetanothermodder"
            col.operator("wm.url_open", text="Bluesky").url = "https://bsky.app/profile/kejabnuuy.bsky.social"
            col.separator(factor=1, type="LINE")
            col.operator("wm.url_open", text="Heliosphere").url = "https://heliosphere.app/user/Aleks"
            col.operator("wm.url_open", text="XMA").url = "https://www.xivmodarchive.com/user/26481"

        if section_prop.overview_ui == "Info" or section_prop.overview_ui == "Settings":
            row = layout.row(align=True)
            col = row.column(align=True)
            col.alignment = "CENTER"
            row = col.row(align=True)
            row.alignment = "CENTER"
            if hasattr(context.scene, "ya_addon_ver"):
                addon_ver = context.scene.ya_addon_ver
                row.label(text=f"Addon Ver: {addon_ver[0]}.{addon_ver[1]}.{addon_ver[2]}")
            else: row.label(text=f"Addon Not Installed")
            row = col.row(align=True)
            row.alignment = "CENTER"
            row.label(text=f"Devkit Script Ver: {DEVKIT_VER[0]}.{DEVKIT_VER[1]}.{DEVKIT_VER[2]}")
                 
          
    def collection_context(self, context):
        # Links mesh name to the standard collections)
        body_part_collections = {
            "Torso": ['Chest', 'Nipple Piercings'],
            "Waist": ['Legs', 'Pubes'],
            "Hands": ['Hands', 'Nails', 'Practical Uses', 'Clawsies'],
            "Feet": ['Feet', 'Toenails', 'Toe Clawsies'] 
            }

        # Get the active object
        active_ob = bpy.context.active_object

        if active_ob and has_shape_keys(active_ob):
            if not context.scene.devkit_props.button_dynamic_view:
                return active_ob
            else:
                active_collection = active_ob.users_collection
                for body_part, collections in body_part_collections.items():
                    if any(bpy.data.collections[coll_name] in active_collection for coll_name in collections):
                        return get_object_from_mesh(body_part) 
                return active_ob
        else:
            return get_object_from_mesh("Mannequin")

    def chest_shapes(self, layout, section_prop, mq, torso):
        layout.separator(factor=0.1)  
        if section_prop.shape_mq_chest_bool:
            target = mq
            key_target = "mq"
        else:
            target = torso
            key_target = "torso"

        medium_mute = target.data.shape_keys.key_blocks["MEDIUM ----------------------------"].mute
        small_mute = target.data.shape_keys.key_blocks["SMALL ------------------------------"].mute
        buff_mute = target.data.shape_keys.key_blocks["Buff"].mute
        rue_mute = target.data.shape_keys.key_blocks["Rue"].mute
        
        large_depress = True if small_mute and medium_mute else False
        medium_depress = True if not medium_mute and small_mute else False
        small_depress = True if not small_mute and medium_mute else False
        buff_depress = True if not buff_mute else False
        rue_depress = True if not rue_mute else False
        
        row = layout.row(align=True)
        operator = row.operator("ya.apply_shapes", text= "Large", depress=large_depress)
        operator.key = "Large"
        operator.target = "Torso"
        operator.preset = "chest_category"
        operator = row.operator("ya.apply_shapes", text= "Medium", depress=medium_depress)
        operator.key = "Medium"
        operator.target = "Torso"
        operator.preset = "chest_category"
        operator = row.operator("ya.apply_shapes", text= "Small", depress=small_depress)
        operator.key = "Small"
        operator.target = "Torso"
        operator.preset = "chest_category"

        row = layout.row(align=True)
        operator = row.operator("ya.apply_shapes", text= "Buff", depress=buff_depress)
        operator.key = "Buff"
        operator.target = "Torso"
        operator.preset = "other"

        operator = row.operator("ya.apply_shapes", text= "Rue", depress=rue_depress)
        operator.key = "Rue"
        operator.target = "Torso"
        operator.preset = "other"

        box = layout.box()
        row = box.row()
        
        if not small_mute and not medium_mute:
            row.alignment = "CENTER"
            row.label(text="Select a chest size.")
        else:
            split = row.split(factor=0.25)
            col = split.column(align=True)
            col.alignment = "RIGHT"
            col.label(text="Squeeze:")
            if large_depress or medium_depress:
                col.label(text="Squish:")
                col.label(text="Push-Up:")
            if medium_depress:
                col.label(text="Sayonara:")
                col.label(text="Mini:")
            if large_depress:
                col.label(text="Omoi:")
            if large_depress or medium_depress:
                col.label(text="Sag:")
            col.label(text="Nip Nops:")

            if large_depress:
                col2 = split.column(align=True)
                col2.prop(section_prop, f"key_squeeze_large_{key_target}")
                col2.prop(section_prop, f"key_squish_large_{key_target}")
                col2.prop(section_prop, f"key_pushup_large_{key_target}")
                col2.prop(section_prop, f"key_omoi_large_{key_target}")
                col2.prop(section_prop, f"key_sag_omoi_{key_target}")
                col2.prop(section_prop, f"key_nipnops_large_{key_target}")
            
            elif medium_depress:
                col2 = split.column(align=True)
                col2.prop(section_prop, f"key_squeeze_medium_{key_target}")
                col2.prop(section_prop, f"key_squish_medium_{key_target}")
                col2.prop(section_prop, f"key_pushup_medium_{key_target}")
                col2.prop(section_prop, f"key_sayonara_medium_{key_target}")
                col2.prop(section_prop, f"key_mini_medium_{key_target}")
                col2.prop(section_prop, f"key_sag_medium_{key_target}")
                col2.prop(section_prop, f"key_nipnops_medium_{key_target}")

            elif small_depress:
                col2 = split.column(align=True)
                col2.prop(section_prop, f"key_squeeze_small_{key_target}")
                col2.prop(section_prop, f"key_nipnops_small_{key_target}")
        
        layout.separator(factor=0.1)

        row = layout.row()
        split = row.split(factor=0.25, align=True) 
        col = split.column(align=True)
        col.alignment = "RIGHT"
        col.label(text="Preset:")
        
        col2 = split.column(align=True)
        col2.prop(section_prop, "chest_shape_enum")

        col3 = split.column(align=True)
        col3.operator("ya.apply_shapes", text= "Apply").preset = "shapes"

        layout.separator(factor=0.1)

    def leg_shapes(self, layout, section_prop, mq, legs):
        layout.separator(factor=0.1)
        if section_prop.shape_mq_legs_bool:
            target = mq
        else:
            target = legs

        skull_mute = target.data.shape_keys.key_blocks["Skull Crushers"].mute
        mini_mute = target.data.shape_keys.key_blocks["Mini"].mute
        rue_mute = target.data.shape_keys.key_blocks["Rue"].mute

        genb_mute = target.data.shape_keys.key_blocks["Gen B"].mute
        genc_mute = target.data.shape_keys.key_blocks["Gen C"].mute
        gensfw_mute = target.data.shape_keys.key_blocks["Gen SFW"].mute

        small_mute = target.data.shape_keys.key_blocks["Small Butt"].mute
        soft_mute = target.data.shape_keys.key_blocks["Soft Butt"].mute

        hip_yab_mute = target.data.shape_keys.key_blocks["Hip Dips (for YAB)"].mute
        hip_rue_mute = target.data.shape_keys.key_blocks["Less Hip Dips (for Rue)"].mute

        melon_depress = True if skull_mute and mini_mute else False
        skull_depress = True if not skull_mute else False
        mini_depress = True if not mini_mute else False
        rue_depress = True if not rue_mute else False

        gena_depress = True if genb_mute and gensfw_mute and genc_mute else False
        genb_depress = True if not genb_mute else False
        genc_depress = True if not genc_mute else False
        gensfw_depress = True if not gensfw_mute else False

        small_depress = True if not small_mute else False
        soft_depress = True if not soft_mute else False
        hip_depress = True if not hip_yab_mute or not hip_rue_mute else False
        
        row = layout.row(align=True) 
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Genitalia:")
        button_row = split.row(align=True)

        operator = button_row.operator("ya.apply_shapes", text= "A", depress=gena_depress)
        operator.key = "Gen A"
        operator.target = "Legs"
        operator.preset = "gen"

        operator = button_row.operator("ya.apply_shapes", text= "B", depress=genb_depress)
        operator.key = "Gen B"
        operator.target = "Legs"
        operator.preset = "gen"

        operator = button_row.operator("ya.apply_shapes", text= "C", depress=genc_depress)
        operator.key = "Gen C"
        operator.target = "Legs"
        operator.preset = "gen"

        operator = button_row.operator("ya.apply_shapes", text= "SFW", depress=gensfw_depress)
        operator.key = "Gen SFW"
        operator.target = "Legs"
        operator.preset = "gen"
        
        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Leg sizes:")
        button_row = split.row(align=True)
        operator = button_row.operator("ya.apply_shapes", text= "Melon", depress=melon_depress)
        operator.key = "Melon"
        operator.target = "Legs"
        operator.preset = "leg_size"

        operator = button_row.operator("ya.apply_shapes", text= "Skull", depress=skull_depress)
        operator.key = "Skull"
        operator.target = "Legs"
        operator.preset = "leg_size"

        operator = button_row.operator("ya.apply_shapes", text= "Mini", depress=mini_depress)
        operator.key = "Mini"
        operator.target = "Legs"
        operator.preset = "leg_size"

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Butt options:")
        button_row = split.row(align=True)
        operator = button_row.operator("ya.apply_shapes", text= "Small", depress=small_depress)
        operator.key = "Small Butt"
        operator.target = "Legs"
        operator.preset = "other"
        operator = button_row.operator("ya.apply_shapes", text= "Soft", depress=soft_depress)
        operator.key = "Soft Butt"
        operator.target = "Legs"
        operator.preset = "other"

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        operator = split.operator("ya.apply_shapes", text= "Alt Hips", depress=hip_depress)
        operator.key = "Alt Hips"
        operator.target = "Legs"
        operator.preset = "other"
        button_row = split.row(align=True)
        operator = button_row.operator("ya.apply_shapes", text= "Rue", depress=rue_depress)
        operator.key = "Rue"
        operator.target = "Legs"
        operator.preset = "other"
        
        layout.separator(factor=0.1)

    def yas_menu(self, layout, section_prop):
        layout.separator(factor=0.1)
        row = layout.row(align=True)
        icon = 'CHECKMARK' if section_prop.controller_yas_chest else 'PANEL_CLOSE'
        row.prop(section_prop, "controller_yas_chest", text="Chest", icon=icon)
        icon = 'CHECKMARK' if section_prop.controller_yas_hands else 'PANEL_CLOSE'
        row.prop(section_prop, "controller_yas_hands", text="Hands", icon=icon)
        icon = 'CHECKMARK' if section_prop.controller_yas_feet else 'PANEL_CLOSE'
        row.prop(section_prop, "controller_yas_feet", text="Feet", icon=icon)

        layout.separator(factor=0.5,type="LINE")

        row = layout.row(align=True)
        col2 = row.column(align=True)
        col2.label(text="Legs:")
        icon = 'CHECKMARK' if section_prop.controller_yas_legs else 'PANEL_CLOSE'
        col2.prop(section_prop, "controller_yas_legs", text="YAS", icon=icon)
        icon = 'CHECKMARK' if section_prop.controller_yas_legs_gen else 'PANEL_CLOSE'
        col2.prop(section_prop, "controller_yas_legs_gen", text="Genitalia", icon=icon)

        col = row.column(align=True)
        col.label(text="Mannequin:")
        icon = 'CHECKMARK' if section_prop.controller_yas_mannequin else 'PANEL_CLOSE'
        col.prop(section_prop, "controller_yas_mannequin", text="YAS", icon=icon)
        icon = 'CHECKMARK' if section_prop.controller_yas_mannequin_gen else 'PANEL_CLOSE'
        col.prop(section_prop, "controller_yas_mannequin_gen", text="Genitalia", icon=icon) 

        layout.separator(factor=0.1)

    def other_shapes(self, layout, section_prop, mq, hands, feet):
        if section_prop.shape_mq_other_bool:
                        target = mq
                        target_f = mq
                        key_target = "mq"
        else:
            target = hands
            target_f = feet
            key_target = "feet"
            clawsies_mute = target.data.shape_keys.key_blocks["Curved"].mute
            clawsies_depress = True if clawsies_mute else False
            clawsies_col = bpy.context.view_layer.layer_collection.children["Hands"].children["Clawsies"].exclude
            toeclawsies_col = bpy.context.view_layer.layer_collection.children["Feet"].children["Toe Clawsies"].exclude

        short_mute = target.data.shape_keys.key_blocks["Short Nails"].mute
        ballerina_mute = target.data.shape_keys.key_blocks["Ballerina"].mute
        stabbies_mute = target.data.shape_keys.key_blocks["Stabbies"].mute
        rue_mute = target.data.shape_keys.key_blocks["Rue"].mute
        rue_f_mute = target_f.data.shape_keys.key_blocks["Rue"].mute

        long_depress = True if short_mute and ballerina_mute and stabbies_mute else False
        short_depress = True if not short_mute else False
        ballerina_depress = True if not ballerina_mute else False
        stabbies_depress = True if not stabbies_mute else False
        rue_depress = True if not rue_mute else False
        rue_f_depress = True if not rue_f_mute else False
        hands_col = bpy.context.view_layer.layer_collection.children["Hands"].exclude
        feet_col = bpy.context.view_layer.layer_collection.children["Feet"].exclude
        nails_col = bpy.context.view_layer.layer_collection.children["Hands"].children["Nails"].exclude
        toenails_col = bpy.context.view_layer.layer_collection.children["Feet"].children["Toenails"].exclude

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Hands:")
        button_row = split.row(align=True)
        if not section_prop.shape_mq_other_bool:
            icon = "HIDE_ON" if hands_col else "HIDE_OFF"
            hands_op = button_row.operator("ya.apply_visibility", text="", icon=icon, depress=not hands_col)
            hands_op.target = "Hands"
            hands_op.key = ""

        operator = button_row.operator("ya.apply_shapes", text= "Rue", depress=rue_depress)
        operator.key = "Rue Other"
        operator.target = "Hands"
        operator.preset = "other"

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Nails:")
        button_row = split.row(align=True)
        if not section_prop.shape_mq_other_bool:
            icon = "HIDE_ON" if nails_col else "HIDE_OFF"
            operator = button_row.operator("ya.apply_visibility", text="", icon=icon, depress=not nails_col)
            operator.key = "Nails"
            operator.target = "Hands"

        operator = button_row.operator("ya.apply_shapes", text= "Long", depress=long_depress)
        operator.key = "Long"
        operator.target = "Hands"
        operator.preset = "nails"
        
        operator = button_row.operator("ya.apply_shapes", text= "Short", depress=short_depress)
        operator.key = "Short"
        operator.target = "Hands"
        operator.preset = "nails"

        operator = button_row.operator("ya.apply_shapes", text= "Ballerina", depress=ballerina_depress)
        operator.key = "Ballerina"
        operator.target = "Hands"
        operator.preset = "nails"

        operator = button_row.operator("ya.apply_shapes", text= "Stabbies", depress=stabbies_depress)
        operator.key = "Stabbies"
        operator.target = "Hands"
        operator.preset = "nails"

        if not section_prop.shape_mq_other_bool:
            row = layout.row(align=True)
            split = row.split(factor=0.25, align=True)
            split.alignment = "RIGHT"
            split.label(text="Clawsies:")
            button_row = split.row(align=True)
            icon = "HIDE_ON" if clawsies_col else "HIDE_OFF"
            operator = button_row.operator("ya.apply_visibility", text="", icon=icon, depress=not clawsies_col)
            operator.key = "Clawsies"
            operator.target = "Hands"
            operator = button_row.operator("ya.apply_shapes", text= "Straight", depress=clawsies_depress)
            operator.key = "Curved"
            operator.target = "Hands"
            operator.preset = "other"
            operator = button_row.operator("ya.apply_shapes", text= "Curved", depress=not clawsies_depress)
            operator.key = "Curved"
            operator.target = "Hands"
            operator.preset = "other"
    
        layout.separator(type="LINE")

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Feet:")
        button_row = split.row(align=True)
        if not section_prop.shape_mq_other_bool:
            icon = "HIDE_ON" if feet_col else "HIDE_OFF"
            feet_op = button_row.operator("ya.apply_visibility", text="", icon=icon, depress=not feet_col)
            feet_op.target = "Feet"
            feet_op.key = ""
        operator = button_row.operator("ya.apply_shapes", text= "Rue", depress=rue_f_depress)
        operator.key = "Rue Other"
        operator.target = "Feet"
        operator.preset = "other"

        if not section_prop.shape_mq_other_bool:
            row = layout.row(align=True)
            col = row.column(align=True)
            row = col.row(align=True)
            split = row.split(factor=0.25, align=True)
            split.alignment = 'RIGHT'  # Align label to the right
            split.label(text="Nails/Claws:")
            icon = "HIDE_ON" if toenails_col else "HIDE_OFF"
            nail_op = split.operator("ya.apply_visibility", text="", icon=icon, depress=not toenails_col)
            nail_op.key = "Nails"
            nail_op.target = "Feet"
            icon = "HIDE_ON" if toeclawsies_col else "HIDE_OFF"
            claw_op = split.operator("ya.apply_visibility", text="", icon=icon, depress=not toeclawsies_col)
            claw_op.key = "Clawsies"
            claw_op.target = "Feet"

        box = layout.box()
        row = box.row(align=True)
        split = row.split(factor=0.25)
        col = split.column(align=True)
        col.alignment = "RIGHT"
        col.label(text="Heels:")
        col.label(text="Cinderella:")
        col.label(text="Mini Heels:")
        
        col2 = split.column(align=True)
        col2.prop(section_prop, f"key_heels_{key_target}")
        col2.prop(section_prop, f"key_cinderella_{key_target}")
        col2.prop(section_prop, f"key_miniheels_{key_target}")

        layout.separator(factor=0.1)

    def ui_category_buttons(self, layout, section_prop, options):
        row = layout

        for slot, icon in options:
            depress = True if section_prop.overview_ui == slot else False
            row.operator("ya.set_ui", text="", icon=icon, depress=depress).overview = slot


class OutfitStudio(Panel):
    bl_idname = "VIEW3D_PT_YA_OutfitStudio"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Devkit"
    bl_label = "Outfit Studio"
    bl_order = 1

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)


class FileManager(Panel):
    bl_idname = "VIEW3D_PT_YA_FileManager"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Devkit"
    bl_label = "File Manager"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 3

    def draw(self, context):
        layout = self.layout
        section_prop = context.scene.devkit_props

        # EXPORT
        button = section_prop.button_export_expand
        box = self.dropdown_header(button, section_prop, "button_export_expand", "Export", "EXPORT")
        if button:
            self.draw_export(context, layout, section_prop)

        # IMPORT
        button = section_prop.button_import_expand
        box = self.dropdown_header(button, section_prop, "button_import_expand", "Import", "IMPORT")
        if button:
            self.draw_import(layout, section_prop)

        if hasattr(context.scene, "pmp_props"):
                from modpack.panel import draw_modpack
                section_prop = context.scene.pmp_props
                # MODPACKER
                button = section_prop.button_modpack_expand
                box = self.dropdown_header(button, section_prop, "button_modpack_expand", "Modpack", "NEWFOLDER")

                if button :
                    try:
                        reload(draw_modpack)
                    except:
                        pass
                    draw_modpack(self, layout, section_prop, devkit=True)
      
    def draw_export(self, context, layout, section_prop):
        global is_exporting

        if section_prop.export_total > 0:
            layout.separator(factor=0.5)

            total = section_prop.export_total
            step = section_prop.export_step
            total_time = section_prop.export_time
            if step < 1:
                time_left = "Estimating duration..."
            else:
                average_time = total_time / step
                estimate = int((total - step) * average_time)

                if estimate < 0:
                    time_left = f"~{estimate} seconds"
                else:
                    minutes = estimate / 60
                    seconds = estimate % 60
                    time_left = f"~{int(minutes)} min {int(seconds)} seconds"

            row = layout.row(align=True)
            row.alignment = "CENTER"
            row.progress(
                factor=section_prop.export_progress, 
                text=f"Exporting: {step + 1}/{total}",
                type="RING")
            row.label(text=f"{time_left}")
            row = layout.row(align=True)
            row.alignment = "CENTER"
            row.label(text=f"{section_prop.export_file_name}")

            layout.separator(factor=0.5)
        else:
            row = layout.row(align=True)
            row.prop(section_prop, "export_display_directory", text="")
            row.operator("ya.dir_selector", icon="FILE_FOLDER", text="").category = "export"

            row = layout.row(align=True)
            col = row.column(align=True)
            col.operator("ya.simple_export", text="Simple Export")
            col2 = row.column(align=True)
            col2.operator("ya.batch_queue", text="Batch Export")
            
            export_text = "GLTF" if section_prop.file_gltf else "FBX"
            icon = "BLENDER" if section_prop.file_gltf else "VIEW3D"
            col3 = row.column(align=True)
            col3.alignment = "RIGHT"
            col3.prop(section_prop, "file_gltf", text=export_text, icon=icon, invert_checkbox=True)

        box = layout.box()
        row = box.row(align=True)
        if section_prop.export_body_slot == "Chest & Legs":
            row.label(text=f"Body Part: Chest")
        else:
            row.label(text=f"Body Part: {section_prop.export_body_slot}")

        options =[
            ("Chest", "MOD_CLOTH"),
            ("Legs", "BONE_DATA"),
            ("Hands", "VIEW_PAN"),
            ("Feet", "VIEW_PERSPECTIVE"),
            ("Chest & Legs", "ARMATURE_DATA")
            ]
        
        self.body_category_buttons(row, section_prop, options)
    
            
        # CHEST EXPORT  
        
        button_type = "export"
        if section_prop.export_body_slot == "Chest" or section_prop.export_body_slot == "Chest & Legs":

            category = "Chest"

            labels = {"Buff": "Buff", "Rue": "Rue", "Piercings": "Piercings"}
    
            self.dynamic_column_buttons(3, layout, section_prop, labels, category, button_type)


            layout.separator(factor=0.5, type="LINE")
            
            labels = {
                "Large":      "Large",    
                "Medium":     "Medium",   
                "Small":      "Small",    
                "Omoi":       "Omoi",     
                "Sayonara":   "Sayonara", 
                "Mini":       "Mini",     
                "Sugoi Omoi": "Sugoi Omoi", 
                "Tsukareta":  "Tsukareta", 
                "Tsukareta+": "Tsukareta+"
            }
    
            self.dynamic_column_buttons(3, layout, section_prop, labels, category, button_type)
            
        # LEG EXPORT  
        
        if section_prop.export_body_slot == "Legs" or section_prop.export_body_slot == "Chest & Legs":
            category = "Legs"

            if section_prop.export_body_slot == "Chest & Legs":
                layout.separator(factor=1, type="LINE")
                row = layout.row(align=True)
                row.label(text=f"Body Part: Legs")

            labels = {
                "Gen A":  "Gen A",
                "Gen B":  "Gen B", 
                "Gen C":  "Gen C",
                "Gen SFW":  "Gen SFW",
                "Melon": "Melon",
                "Skull": "Skull",  
                "Mini": "Mini",
                "Pubes":  "Pubes"
            }
            
            self.dynamic_column_buttons(4, layout, section_prop, labels, category, button_type)

            layout.separator(factor=0.5, type="LINE")

            labels = {
                "Small Butt": "Small Butt",
                "Rue": "Rue",
                "Soft Butt": "Soft Butt", 
                "Hip Dips":  "Hip Dips",
            }
    
            self.dynamic_column_buttons(2, layout, section_prop, labels, category, button_type) 

        # HAND EXPORT  
        
        if section_prop.export_body_slot == "Hands":
            
            category = "Hands"
            labels = {
                "YAB": "YAB", 
                "Rue": "Rue"
                }
    
            self.dynamic_column_buttons(2, layout, section_prop, labels, category, button_type)
            
            layout.separator(factor=0.5, type="LINE")

            labels = {
                "Long": "Long", 
                "Short": "Short", 
                "Ballerina": "Ballerina", 
                "Stabbies": "Stabbies" 
                }

            self.dynamic_column_buttons(2, layout, section_prop, labels, category, button_type)

            row = layout.row(align=True)
            row.label(text="Clawsies:")

            labels = { 
                "Straight": "Straight", 
                "Curved": "Curved"
                }

            self.dynamic_column_buttons(2, layout, section_prop, labels, category, button_type)

            row = layout.row(align=True)

        # FEET EXPORT  
        
        if section_prop.export_body_slot == "Feet":
            
            category = "Feet"
            labels = {
                "YAB": "YAB", 
                "Rue": "Rue", 
                }
    
            self.dynamic_column_buttons(2, layout, section_prop, labels, category, button_type)

            layout.separator(factor=0.5, type="LINE")

            labels = { 
                "Clawsies": "Clawsies"
                }

            self.dynamic_column_buttons(2, layout, section_prop, labels, category, button_type)
       
        layout.separator(factor=0.5, type="LINE")

        box = layout.box()
        row = box.row(align=True)
        row.alignment = "CENTER"
        row.label(text="Advanced Options")

        layout.separator(factor=0.1) 

        row = layout.row(align=True)
        split = row.split(factor=0.33)
        col = split.column(align=True)
        col.alignment = "RIGHT"
        col.label(text="Force YAS:")
        col.label(text="Check Tris:")
        col.label(text="Shape Keys:")
        col.label(text="Subfolder:")
        
        col2 = split.column(align=True)
        col2.alignment = "RIGHT"
        icon = 'CHECKMARK' if section_prop.force_yas else 'PANEL_CLOSE'
        text = 'Enabled' if section_prop.force_yas else 'Disabled'
        col2.prop(section_prop, "force_yas", text=text, icon=icon)
        icon = 'CHECKMARK' if section_prop.check_tris else 'PANEL_CLOSE'
        text = 'Enabled' if section_prop.check_tris else 'Disabled'
        col2.prop(section_prop, "check_tris", text=text, icon=icon)
        icon = 'CHECKMARK' if section_prop.keep_shapekeys else 'PANEL_CLOSE'
        text = 'Keep' if section_prop.keep_shapekeys else 'Remove'
        col2.prop(section_prop, "keep_shapekeys", text=text, icon=icon)
        icon = 'CHECKMARK' if section_prop.keep_shapekeys else 'PANEL_CLOSE'
        text = 'Create' if section_prop.create_subfolder else 'Ignore'
        col2.prop(section_prop, "create_subfolder", text=text, icon=icon)

        layout.separator(factor=0.5)
    
    def draw_import(self, layout, section_prop):
        layout = self.layout
        row = layout.row(align=True)
        col = row.column(align=True)
        col.operator("ya.simple_import", text="Import")

        col2 = row.column(align=True)
        col2.operator("ya.simple_cleanup", text="Cleanup")
        
        export_text = "GLTF" if section_prop.file_gltf else "FBX"
        icon = "BLENDER" if section_prop.file_gltf else "VIEW3D"
        col3 = row.column(align=True)
        col3.alignment = "RIGHT"
        col3.prop(section_prop, "file_gltf", text=export_text, icon=icon, invert_checkbox=True)

        box = layout.box()
        row = box.row(align=True)
        row.alignment = "CENTER"
        row.label(text="Cleanup Options") 

        layout.separator(factor=0.1)  

        row = layout.row(align=True)
        split = row.split(factor=0.33)
        col = split.column(align=True)
        col.alignment = "RIGHT"
        col.label(text="Fix Parenting:")
        col.label(text="Update Material:")
        col.label(text="Rename:")
        
        col2 = split.column(align=True)
        col2.alignment = "RIGHT"
        icon = 'CHECKMARK' if section_prop.fix_parent else 'PANEL_CLOSE'
        text = 'Enabled' if section_prop.fix_parent else 'Disabled'
        col2.prop(section_prop, "fix_parent", text=text, icon=icon)
        icon = 'CHECKMARK' if section_prop.update_material else 'PANEL_CLOSE'
        text = 'Enabled' if section_prop.update_material else 'Disabled'
        col2.prop(section_prop, "update_material", text=text, icon=icon)
        col2.prop(section_prop, "rename_import", text="")

        layout.separator(factor=0.5)

    def dynamic_column_buttons(self, columns, box, section_prop, labels, category, button_type):
        row = box.row(align=True)

        columns_list = [row.column(align=True) for _ in range(columns)]

        for index, (size, name) in enumerate(labels.items()):
            size_lower = size.lower().replace(' ', "_")
            category_lower = category.lower()

            prop_name = f"{button_type}_{size_lower}_{category_lower}_bool"

            if hasattr(section_prop, prop_name):
                icon = 'CHECKMARK' if getattr(section_prop, prop_name) else 'PANEL_CLOSE'
                
                col_index = index % columns 
                
                columns_list[col_index].prop(section_prop, prop_name, text=name, icon=icon)
            else:
                print(f"{name} has no assigned property!")
        return box  

    def dropdown_header(self, button, section_prop, prop_str=str, label=str, extra_icon=""):
        layout = self.layout
        row = layout.row(align=True)
        split = row.split(factor=1)
        box = split.box()
        sub = box.row(align=True)
        sub.alignment = 'LEFT'

        icon = 'TRIA_DOWN' if button else 'TRIA_RIGHT'
        sub.prop(section_prop, prop_str, text="", icon=icon, emboss=False)
        sub.label(text=label)
        if extra_icon != "":
            sub.label(icon=extra_icon)
        
        return box

    def body_category_buttons(self, layout, section_prop, options):
        row = layout

        for slot, icon in options:
            depress = True if section_prop.export_body_slot == slot else False
            row.operator("ya.set_body_part", text="", icon=icon, depress=depress).body_part = slot


CLASSES = [
    CollectionState,
    ObjectState,
    DevkitProps,
    CollectionManager,
    ApplyShapes,
    ApplyVisibility,
    SimpleExport,
    SimpleCleanUp,
    BatchQueue,
    FileExport,
    SimpleImport,
    BodyPartSlot,
    DirSelector,
    UISelector,
]

UI_CLASSES = [
    Overview,
    OutfitStudio,
    FileManager
]


def delayed_setup(dummy=None):
    global devkit_registered  
    if devkit_registered:
        return None
    DevkitProps.chest_key_floats()
    DevkitProps.feet_key_floats()
    DevkitProps.controller_drivers()
    context = bpy.context

    try:
        area = [area for area in context.screen.areas if area.type == 'VIEW_3D'][0]
        view3d = [space for space in area.spaces if space.type == 'VIEW_3D'][0]

        with context.temp_override(area=area, space=view3d):
            view3d.show_region_ui = True
            region = [region for region in area.regions if region.type == 'UI'][0]
            region.active_panel_category = 'Devkit'
    except:
        pass

    addon_status = addon_utils.check("Yet Another Addon")
    if addon_status:
        addon_utils.disable("Yet Another Addon")
        addon_utils.enable("Yet Another Addon")
    
    devkit_registered = True
    return None

def set_devkit_properties():
    bpy.types.Scene.devkit_props = PointerProperty(
        type=DevkitProps)
    
    bpy.types.Scene.collection_state = bpy.props.CollectionProperty(
        type=CollectionState)
    
    bpy.types.Scene.object_state = bpy.props.CollectionProperty(
        type=ObjectState)

    DevkitProps.ui_buttons()
    
    DevkitProps.export_bools()
    DevkitProps.extra_options()
 
def register():

    for cls in CLASSES:
        bpy.utils.register_class(cls)

    set_devkit_properties()
    bpy.app.timers.register(delayed_setup, first_interval=1)
    bpy.app.handlers.load_post.append(delayed_setup)

    for cls in UI_CLASSES:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(CLASSES + UI_CLASSES):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.devkit_props
    del bpy.types.Scene.collection_state
    del bpy.types.Scene.object_state
    bpy.app.handlers.load_post.remove(delayed_setup)

if __name__ == "__main__":
    register()