DEVKIT_VER = (0, 10, 0)

import bpy   

from bpy.props     import StringProperty, EnumProperty, BoolProperty, PointerProperty, FloatProperty, CollectionProperty
from bpy.types     import Operator, Panel, PropertyGroup, Object, Mesh, Context, UILayout, ShapeKey, Collection, LayerCollection

devkit_registered: bool = False

def get_object_from_mesh(mesh_name:str) -> Object | None:
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and obj.data.name == mesh_name:
            return obj
    return None

def has_shape_keys(obj:Object) -> bool:
        if obj and obj.type == "MESH":
            if obj.data.shape_keys is not None:
                return True
        return False

def get_filtered_shape_keys(obj:Mesh, key_filter:list) -> list:
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

class CollectionState(PropertyGroup):
    name: StringProperty() # type: ignore

class ObjectState(PropertyGroup):
    name: StringProperty() # type: ignore
    hide: BoolProperty() # type: ignore

class DevkitProps(PropertyGroup):

    #       Shapes:         (Name,           Slot/Misc,      Category, Description,                                           Body,             Shape Key)
    ALL_SHAPES = { 
            "Large":        ("Large",        "Chest",        "Large",  "Standard Large",                                      False,               "LARGE"),
            "Omoi":         ("Omoi",         "Chest",        "Large",  "Large, but saggier",                                  False,               ""),
            "Sugoi Omoi":   ("Sugoi Omoi",   "Chest",        "Large",  "Omoi, but saggier",                                   False,               ""),
            "Uranus":       ("Uranus",       "Chest",        "Large",  "Uranus Redux",                                        False,               ""),
            "Medium":       ("Medium",       "Chest",        "Medium", "Standard Medium",                                     False,               "MEDIUM"),
            "Sayonara":     ("Sayonara",     "Chest",        "Medium", "Medium with more separation",                         False,               ""),
            "Tsukareta":    ("Tsukareta",    "Chest",        "Medium", "Medium, but saggier",                                 False,               ""),
            "Tsukareta+":   ("Tsukareta+",   "Chest",        "Medium", "Tsukareta, but saggier",                              False,               ""),
            "Mini":         ("Mini",         "Chest",        "Medium", "Medium, but smaller",                                 False,               ""),
            "Small":        ("Small",        "Chest",        "Small",  "Standard Small",                                      False,               "SMALL"),
            "Flat":         ("Flat",         "Chest",        "Masc",   "Yet Another Masc",                                    False,                "MASC"),
            "Pecs":         ("Pecs",         "Chest",        "Masc",   "Defined Pecs for Masc",                               False,               "MASC"),
            "Lava Omoi":    ("Lava Omoi",    "Chest",        "Large",  "Biggest Lavatiddy",                                   False,               ""),
            "Teardrop":     ("Teardrop",     "Chest",        "Medium", "Medium Lavatiddy",                                    False,               ""),
            "Cupcake":      ("Cupcake",      "Chest",        "Small",  "Small Lavatiddy",                                     False,               ""),
            "Sugar":        ("Sugar",        "Chest",        "Small",  "Smallest Lavatiddy",                                  False,               ""),
            "YAB":          ("YAB",          "Chest",        "",       "Base size",                                           True,                "Rue"),
            "Rue":          ("Rue",          "Chest",        "",       "Adds tummy",                                          True,                "Rue"),
            "Lava":         ("Lava",         "Chest",        "",       "Lavabod",                                             True,                "Lavabod"),
            "Buff":         ("Buff",         "Chest",        "",       "Adds muscle",                                         False,               "Buff"),
            "Piercings":    ("Piercings",    "Chest",        "",       "Adds piercings",                                      False,               ""),
            "YAB Legs":     ("YAB",          "Legs",         "",       "Base size",                                           True,                ""),
            "Rue Legs":     ("Rue",          "Legs",         "",       "Adds tummy and hip dips",                             True,                "Rue"),
            "Lava Legs":    ("Lava",         "Legs",         "",       "Bigger hips, butt and hip dips",                      True,                "Lavabod"),
            "Masc Legs":    ("Masc",         "Legs",         "",       "Yet Another Masc",                                    True,                "Masc"),
            "Melon":        ("Melon",        "Legs",         "Legs",   "For crushing melons",                                 False,               "Gen A/Watermelon Crushers"),
            "Skull":        ("Skull",        "Legs",         "Legs",   "For crushing skulls",                                 False,               "Skull Crushers"),
            "Small Butt":   ("Small Butt",   "Legs",         "Butt",   "Not actually small",                                  False,               "Small Butt"),
            "Mini Legs":    ("Mini",         "Legs",         "Legs",   "Smaller legs",                                        False,               "Mini"),
            "Soft Butt":    ("Soft Butt",    "Legs",         "Butt",   "Less perky butt",                                     False,               "Soft Butt"),
            "Hip Dips":     ("Hip Dips",     "Legs",         "Hip",    "Removes hip dips on Rue, adds them on YAB",           False,               "Alt Hips"),
            "Gen A":        ("Gen A",        "Legs",         "Vagina", "Labia majora",                                        False,               ""),
            "Gen B":        ("Gen B",        "Legs",         "Vagina", "Visible labia minora",                                False,               "Gen B"),
            "Gen C":        ("Gen C",        "Legs",         "Vagina", "Open vagina",                                         False,               "Gen C"),
            "Gen SFW":      ("Gen SFW",      "Legs",         "Vagina", "Barbie doll",                                         False,               "Gen SFW"), 
            "Pubes":        ("Pubes",        "Legs",         "Pubes",  "Adds pubes",                                          False,               ""),
            "YAB Hands":    ("YAB",          "Hands",        "Hands",  "YAB hands",                                           True,                ""),
            "Rue Hands":    ("Rue",          "Hands",        "Hands",  "Changes hand shape to Rue",                           True,                "Rue"),
            "Lava Hands":   ("Lava",         "Hands",        "Hands",  "Changes hand shape to Lavabod",                       True,                "Lavabod"),
            "Long":         ("Long",         "Hands",        "Nails",  "They're long",                                        False,               ""),
            "Short":        ("Short",        "Hands",        "Nails",  "They're short",                                       False,               "Short Nails"),
            "Ballerina":    ("Ballerina",    "Hands",        "Nails",  "Some think they look like shoes",                     False,               "Ballerina"),
            "Stabbies":     ("Stabbies",     "Hands",        "Nails",  "You can stab someone's eyes with these",              False,               "Stabbies"),
            "Straight":     ("Straight",     "Hands",        "Nails",  "When you want to murder instead",                     False,               ""),
            "Curved":       ("Curved",       "Hands",        "Nails",  "If you want to murder them a bit more curved",        False,               "Curved"),
            "YAB Feet":     ("YAB",          "Feet",         "Feet",   "YAB feet",                                            True,                ""),
            "Rue Feet":     ("Rue",          "Feet",         "Feet",   "Changes foot shape to Rue",                           True,                "Rue"),
            "Clawsies":     ("Clawsies",     "Feet",         "Claws",  "Good for kicking",                                    False,               ""),
            }

    torso_floats = [{
        #YAB
        "Large" : {"Squeeze": 0.3, "Squish": 0.0,  "Push-Up": 0.0,  "Omoi": 0.0, "Uranus Redux": 0.0, "Sag": 0.0, "Nip Nops": 0.0},
        "Medium": {"Squeeze": 0.0, "Squish": 0.0,  "Push-Up": 0.0,  "Mini": 0.0, "Sayonara": 0.0,     "Sag": 0.0, "Nip Nops": 0.0},
        "Small" : {"Squeeze": 0.0,                                                                                "Nip Nops": 0.0}},
        #Lava
        {
        "Large" : {"Squeeze": 0.0, "Squish": 0.0,  "Push-Up": 0.0,  "Omoi": 0.0, "Uranus Redux": 0.0, "Sag": 0.0, "Nip Nops": 0.0},
        "Medium": {"Squeeze": 0.0, "Squish": 0.0,  "Push-Up": 0.0,  "Mini": 0.0, "Sayonara": 0.0,     "Sag": 0.0, "Nip Nops": 0.0},
        "Small" : {"Squeeze": 0.0,  "Sugar": 0.0,                                                                 "Nip Nops": 0.0}}]
    
    mq_floats = [{
        #YAB
        "Large" : {"Squeeze": 0.3, "Squish": 0.0,  "Push-Up": 0.0,  "Omoi": 0.0, "Uranus Redux": 0.0, "Sag": 0.0, "Nip Nops": 0.0},
        "Medium": {"Squeeze": 0.0, "Squish": 0.0,  "Push-Up": 0.0,  "Mini": 0.0, "Sayonara": 0.0,     "Sag": 0.0, "Nip Nops": 0.0},
        "Small" : {"Squeeze": 0.0,                                                                                "Nip Nops": 0.0}},
        #Lava
        {
        "Large" : {"Squeeze": 0.0, "Squish": 0.0,  "Push-Up": 0.0,  "Omoi": 0.0, "Uranus Redux": 0.0, "Sag": 0.0, "Nip Nops": 0.0},
        "Medium": {"Squeeze": 0.0, "Squish": 0.0,  "Push-Up": 0.0,  "Mini": 0.0, "Sayonara": 0.0,     "Sag": 0.0, "Nip Nops": 0.0},
        "Small" : {"Squeeze": 0.0,  "Sugar": 0.0,                                                                 "Nip Nops": 0.0}}]

    is_exporting: bool = False

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

    mesh_list = [
        "Torso",
        "Waist",
        "Hands",
        "Feet",
        "Mannequin",
    ]

    controller_modifiers = [
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
    def shpk_bools() -> None:
        for shape, (name, slot, shape_category, description, body, key) in DevkitProps.ALL_SHAPES.items():
            if key == "":
                continue
            if slot == "Hands" or slot == "Feet":
                continue
            if shape_category == "Vagina":
                continue
            slot_lower = slot.lower().replace("/", " ")
            key_lower = key.lower().replace(" ", "_")
            
            prop_name = f"shpk_{slot_lower}_{key_lower}"
            prop = BoolProperty(
                name="", 
                description=description,
                default=False, 
                )
            setattr(DevkitProps, prop_name, prop)

    @staticmethod
    def export_bools() -> None:
        for shape, (name, slot, shape_category, description, body, key) in DevkitProps.ALL_SHAPES.items():
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
    def ui_buttons() -> None:
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
    def chest_key_floats() -> None:
        # Creates float properties for chest shape keys controlled by values.
        # Automatically assigns drivers to the models to be controlled by the UI.
        key_filter = ["squeeze", "squish", "pushup", "omoi", "sag", "nipnops", "sayonara", "mini", "softnips", "uranusredux", "sugar", "pecs"]
        torso = bpy.data.meshes["Torso"]
        mq = bpy.data.meshes["Mannequin"]
        control = bpy.data.meshes["Chest Controller"]
        
        targets = {
             "torso": torso,
             "mq":    mq,
             "ctrl":  control,
        }
        
        for name, obj in targets.items():
            key_list = get_filtered_shape_keys(obj, key_filter)

            for key, category, key_name in key_list:
                default = 0
                if key == "squeeze" and category != "small":
                    min = -50
                    if category == "large" and name != "ctrl":
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
    def feet_key_floats() -> None:
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
    
    def add_shape_key_drivers(obj, key_name, prop_name) -> None:
        
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
    def controller_drivers() -> None:  
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

    def get_listable_shapes(body_slot) -> list:
        items = []

        for shape, (name, slot, shape_category, description, body, key) in DevkitProps.ALL_SHAPES.items():
            if body_slot.lower() == slot.lower() and description != "" and shape_category !="":
                if name == "Medium":
                    items.append(None)
                if name == "Small":
                    items.append(None)
                if name == "Lava Omoi":
                    items.append(None)
                    items.append((name, "Omoi", description))
                    continue
                if name == "Flat":
                    items.append(None)
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

    collection_state: CollectionProperty(type=CollectionState) # type: ignore

    object_state: CollectionProperty(type=ObjectState) # type: ignore

    overview_ui: EnumProperty(
        name= "",
        description= "Select an overview",
        items= [
            ("Body", "Shape", "Body Overview"),
            ("Shape Keys", "View", "Shape Key Overview"),
            ("Settings", "Settings", "Devkit Settings"),
            ("Info", "Info", "Useful info"),
        ]
        )  # type: ignore
    
class CollectionManager(Operator):
    bl_idname = "yakit.collection_manager"
    bl_label = "Export"
    bl_description = "Combines chest options and exports them"

    preset: StringProperty() # type: ignore

    def __init__(self):
        self.props             :DevkitProps     = bpy.context.scene.devkit_props
        self.view_layer                         = bpy.context.view_layer.layer_collection
        self.collections_state :CollectionState = self.props.collection_state
        self.object_state      :ObjectState     = self.props.object_state
        self.coll                               = bpy.data.collections
        self.export_collections = [
            self.coll["Skeleton"],
            self.coll["Resources"],
            self.coll["Data Sources"],
            self.coll["UV/Weights"],
            self.coll["Nail UVs"],
            self.coll["Rue"],
            self.coll["YAS"]
        ]
        self.restore = []
        self.obj_visibility = {}
    
    def execute(self, context:Context):
        if self.preset == "Export": 
            self.get_obj_visibility(context)
            for state in self.collections_state:
                name = state.name
                collection = self.coll[name]
                self.export_collections.append(collection)
            self.restore = self.export_collections
            context.view_layer.layer_collection.children['Resources'].children['Data Sources'].hide_viewport = True
            # Export state has been set by now, this saves pre-export scene to be restored after export
            self.save_current_state(context)
            self.exclude_collections(context)
            self.restore_obj_visibility()
        
        elif self.preset == "Restore": 
            for state in self.collections_state:
                    name = state.name
                    collection = self.coll[name]
                    self.restore.append(collection)
            self.exclude_collections(context)
            self.restore_obj_visibility()
        
        elif self.preset == "Animation":
            self.get_obj_visibility(context)
            self.save_current_state(context)
            context.view_layer.layer_collection.children['Resources'].children['Data Sources'].exclude = True
            context.view_layer.layer_collection.children['Resources'].children['Connectors'].exclude = True
            context.view_layer.layer_collection.children['Resources'].children['Nail Kit'].exclude = True
            context.view_layer.layer_collection.children['Resources'].children['Controller'].exclude = True

        else:
            self.save_current_state(context)
            self.get_obj_visibility(context)
        return {"FINISHED"}

    def save_current_state(self, context:Context):
        self.collections_state.clear()
        for layer_collection in context.view_layer.layer_collection.children:
            self.save_current_state_recursive(layer_collection)
    
    def save_current_state_recursive(self, layer_collection:LayerCollection):
        if not layer_collection.exclude:
                state = self.collections_state.add()
                state.name = layer_collection.name
        for child in layer_collection.children:
            self.save_current_state_recursive(child)
    
    def get_obj_visibility(self, context:Context):
        self.object_state.clear()
        for obj in context.scene.objects:
            if obj.visible_get(view_layer=context.view_layer):
                state = self.object_state.add()
                state.name = obj.name
                state.hide = False
            if obj.hide_get(view_layer=context.view_layer):
                state = self.object_state.add()
                state.name = obj.name
                state.hide = True
        
    def restore_obj_visibility(self):
        for obj in bpy.context.view_layer.objects:
            for state in self.object_state:
                if obj.name == state.name:
                    obj.hide_set(state.hide)
                    
    def exclude_collections(self, context:Context):
        collection_sort: dict[Collection, int] = {}

        def sort_collections(coll:Collection, priority):
                collection_sort[coll] = priority
                for child in coll.children:
                    sort_collections(child, priority + 1)
        
        for coll in context.view_layer.layer_collection.children:
            sort_collections(coll, 0)

        to_restore = [coll.name for coll in self.restore]
        sorted_collections = sorted(collection_sort.keys(), key=lambda x: collection_sort[x], reverse=True)
   
        for collection in self.restore:
            self.toggle_collection_exclude(context, collection, exclude=False)

        for collection in sorted_collections:
            if collection.name not in to_restore:
                self.toggle_collection_exclude(context, collection, exclude=True)
    
    def toggle_collection_exclude(self, context:Context, collection:Collection, exclude=True):
            for layer_collection in context.view_layer.layer_collection.children:
                self.recursively_toggle_exclude(layer_collection, collection, exclude)

    def recursively_toggle_exclude(self, layer_collection:LayerCollection, collection:Collection, exclude):
        if layer_collection.collection.name == collection.name:
            layer_collection.exclude = exclude
        
        for child in layer_collection.children:
            self.recursively_toggle_exclude(child, collection, exclude)


def get_chest_size_keys(chest_subsize:str) -> str:
    """category, sizekey"""
    chest_category = get_chest_category(chest_subsize)
    
    size_key = {
        "Large": "LARGE",
        "Medium": "MEDIUM",
        "Small": "SMALL"
    }
    return size_key[chest_category]

def get_chest_category(size:str) -> str | None:
    """subsize, category"""
    if DevkitProps.ALL_SHAPES[size][1] == "Chest":
        return DevkitProps.ALL_SHAPES[size][2]
    else:
        return None

def get_shape_presets(size:str) -> dict:
        shape_presets = {
        "Large":        {"Squeeze": 0.3, "Squish": 0.0,  "Push-Up": 0.0,  "Omoi": 0.0, "Uranus Redux": 0.0, "Sag": 0.0, "Nip Nops": 0.0},
        "Omoi":         {"Squeeze": 0.3, "Squish": 0.0,  "Push-Up": 0.0,  "Omoi": 1.0, "Uranus Redux": 0.0, "Sag": 0.0, "Nip Nops": 0.0},
        "Sugoi Omoi":   {"Squeeze": 0.3, "Squish": 0.0,  "Push-Up": 0.0,  "Omoi": 1.0, "Uranus Redux": 0.0, "Sag": 1.0, "Nip Nops": 0.0},
        "Uranus":       {"Squeeze": 0.0, "Squish": 0.0,  "Push-Up": 0.0,  "Omoi": 0.0, "Uranus Redux": 1.0, "Sag": 0.0, "Nip Nops": 0.0},
        "Lava Omoi":    {"Squeeze": 0.0, "Squish": 0.0,  "Push-Up": 0.0,  "Omoi": 0.0, "Uranus Redux": 0.0, "Sag": 0.0, "Nip Nops": 0.0},
        
        "Medium":       {"Squeeze": 0.0, "Squish": 0.0,  "Push-Up": 0.0,  "Mini": 0.0, "Sayonara": 0.0, "Sag": 0.0, "Nip Nops": 0.0},
        "Sayonara":     {"Squeeze": 0.0, "Squish": 0.0,  "Push-Up": 0.0,  "Mini": 0.0, "Sayonara": 1.0, "Sag": 0.0, "Nip Nops": 0.0},
        "Tsukareta":    {"Squeeze": 0.0, "Squish": 0.0,  "Push-Up": 0.0,  "Mini": 0.0, "Sayonara": 0.0, "Sag": 0.6, "Nip Nops": 0.0},
        "Tsukareta+":   {"Squeeze": 0.0, "Squish": 0.0,  "Push-Up": 0.0,  "Mini": 0.0, "Sayonara": 0.0, "Sag": 1.0, "Nip Nops": 0.0},
        "Mini":         {"Squeeze": 0.0, "Squish": 0.0,  "Push-Up": 0.0,  "Mini": 1.0, "Sayonara": 0.0, "Sag": 0.0, "Nip Nops": 0.0},
        "Teardrop":     {"Squeeze": 0.0, "Squish": 0.0,  "Push-Up": 0.0,  "Mini": 0.0, "Sayonara": 0.0, "Sag": 0.0, "Nip Nops": 0.0},

        "Small":        {"Squeeze": 0.0,                                                                            "Nip Nops": 0.0},
        "Cupcake":      {"Squeeze": 0.0,  "Sugar": 0.0,                                                             "Nip Nops": 0.0},
        "Sugar":        {"Squeeze": 0.0,  "Sugar": 1.0,                                                             "Nip Nops": 0.0},

        "Flat":         {"Pecs": 0.0,                                                                               "Nip Nops": 0.0},
        "Pecs":         {"Pecs": 1.0,                                                                               "Nip Nops": 0.0}
        }
        return shape_presets[size]

class ApplyShapes(Operator):
    bl_idname = "yakit.apply_shapes"
    bl_label = ""
    bl_description = "Applies the selected option"
    bl_options = {'UNDO'}
    
    key: StringProperty() # type: ignore
    target: StringProperty() # type: ignore
    preset: StringProperty() # type: ignore # shapes, chest_category, leg_size, gen, nails, other

    def execute(self, context):
        apply_mq = self.get_mannequin_category(context)
        apply_target = "torso"

        if apply_mq:
            obj = get_object_from_mesh("Mannequin").data.shape_keys.key_blocks
            apply_target = "mq"
        else:
            obj = self.get_obj() 

        self.get_function(context, obj, apply_target)
        return {"FINISHED"}

    def get_obj(self) -> ShapeKey:
        match self.target:  
            case "Legs":
                return get_object_from_mesh("Waist").data.shape_keys.key_blocks

            case "Hands":
                return get_object_from_mesh("Hands").data.shape_keys.key_blocks

            case "Feet":
                return get_object_from_mesh("Feet").data.shape_keys.key_blocks
            case _:
                return get_object_from_mesh("Torso").data.shape_keys.key_blocks

    def get_mannequin_category(self, context:Context) -> bool:
        match self.target:   
            case "Legs":
                return context.scene.devkit_props.shape_mq_legs_bool

            case "Hands" | "Feet":
                return context.scene.devkit_props.shape_mq_other_bool
            
            case _:
                return context.scene.devkit_props.shape_mq_chest_bool

    def get_function(self, context:Context, obj, apply_target:str) -> None:
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
                if self.key == "Alt Hips" and self.target == "Legs" and not obj["Lavabod"].mute:
                    self.report({"ERROR"}, "Lavabod not compatible with alternate hips!")
                    return {"CANCELLED"}
                if self.key == "Alt Hips" and self.target == "Legs" and not obj["Masc"].mute:
                    self.report({"ERROR"}, "Masc not compatible with alternate hips!")
                    return {"CANCELLED"}
                if self.target == "Torso" and self.key == "Lavabod":
                    self.save_chest_sizes(context, obj, apply_target)
                self.toggle_other(obj, self.key)
            
            case _:
                size = context.scene.devkit_props.chest_shape_enum
                lava_sizes = ["Lava Omoi", "Teardrop", "Cupcake", "Sugar"]
                
                if size in lava_sizes and obj["Lavabod"].mute:
                    bpy.ops.yakit.apply_shapes(key="Lavabod", target="Torso", preset="other")
                elif size not in lava_sizes and not obj["Lavabod"].mute:
                    bpy.ops.yakit.apply_shapes(key="Lavabod", target="Torso", preset="other")

                category = get_chest_category(size)
                shape_presets = get_shape_presets(size)

                # ApplyShapes.reset_shape_values(apply_target, category)
                ApplyShapes.apply_shape_values(apply_target, category, shape_presets)
                ApplyShapes.mute_chest_shapes(obj, category)
            
                self.force_update(apply_target)

    def apply_shape_values(apply_target:str, category:str, shape_presets:dict[str, float]) -> None:
        dev_props = bpy.context.scene.devkit_props
        for shape_key in shape_presets:
            norm_key = shape_key.lower().replace(" ","").replace("-","")
            category_lower = category.lower()

            if norm_key == "sag" and category_lower == "large":
                category_lower = "omoi"
            if norm_key == "sugar":
                category_lower = "cupcake"
            
            prop = f"key_{norm_key}_{category_lower}_{apply_target}"
            if hasattr(dev_props, prop):
                setattr(dev_props, prop, 100 * shape_presets[shape_key])
            
    def reset_shape_values(apply_target:str, category) -> None:
        reset = get_shape_presets(category)
        dev_props = bpy.context.scene.devkit_props

        for reset_key in reset:
            norm_key = reset_key.lower().replace(" ","").replace("-","")
            category_lower = category.lower()

            if norm_key == "sag" and category_lower == "large":
                category_lower = "omoi"
            if norm_key == "sugar":
                category_lower = "cupcake"
            
            prop = f"key_{norm_key}_{category_lower}_{apply_target}"
            if hasattr(dev_props, prop):
                setattr(dev_props, prop, 100 * reset[reset_key])
                             
    def mute_chest_shapes(obj, category) -> None:
        category_mute_mapping = {
            "Large": (True, True, True), 
            "Medium": (False, True, True), 
            "Small": (True, False, True),   
            "Masc": (True, True, False),   
        }

        # Gets category and its bools
        mute_medium, mute_small, mute_masc = category_mute_mapping.get(category, (True, True, True))

        # Apply the mute states to the target
        obj["MEDIUM"].mute = mute_medium
        obj["SMALL"].mute = mute_small
        obj["MASC"].mute = mute_masc

        if category == "Masc" and not obj["Lavabod"].mute:
            bpy.ops.yakit.apply_shapes(key="Lavabod", target="Torso", preset="other")

    def mute_gen_shapes(obj, gen: str) -> None:
        gen_mute_mapping = {
            "Gen A": (True, True, True), 
            "Gen B": (False, True, True), 
            "Gen C": (True, False, True),   
            "Gen SFW": (True, True, False),   
        }
        # Gets category and its bools
        mute_b, mute_c, mute_sfw = gen_mute_mapping.get(gen, (True, True, True))

        # Apply the mute states to the target
        obj["Gen B"].mute = mute_b
        obj["Gen C"].mute = mute_c
        obj["Gen SFW"].mute = mute_sfw

    def mute_leg_shapes(obj, size: str) -> None:
        size_mute_mapping = {
            "Melon": (True, True, True, True), 
            "Skull": (False, True, True, True), 
            "Mini": (True, False, True, True),   
            "Lava": (True, True, False, True),   
            "Masc": (True, True, True, False),   
        }

        # Gets category and its bools
        mute_skull, mute_mini, mute_lava, mute_masc = size_mute_mapping.get(size, (True, True, True, True))

        # Apply the mute states to the target
        obj["Skull Crushers"].mute = mute_skull
        obj["Mini"].mute = mute_mini
        obj["Lavabod"].mute = mute_lava
        obj["Masc"].mute = mute_masc

        # if not mute_mini:
        #     obj["Hip Dips (for YAB)"].mute = True
        #     obj["Less Hip Dips (for Rue)"].mute = True

    def mute_nail_shapes(obj, nails: str) -> None:
        nails_mute_mapping = {
            "Long": (True, True, True), 
            "Short": (False, True, True), 
            "Ballerina": (True, False, True), 
            "Stabbies": (True, True, False), 
             
        }
        # Gets category and its bools
        mute_short, mute_ballerina, mute_stabbies = nails_mute_mapping.get(nails, (True, True, True))

        # Apply the mute states to the target
        obj["Short Nails"].mute = mute_short
        obj["Ballerina"].mute = mute_ballerina
        obj["Stabbies"].mute = mute_stabbies
    
    def toggle_other(self, obj, key: str) -> None:
        if obj[key].mute:
            if self.target == "Hands" and key == "Rue":
                obj["Lavabod"].mute = True
            if self.target == "Hands" and key == "Lavabod":
                obj["Rue"].mute = True
            if self.target == "Torso" and key == "Lavabod":
                obj["MASC"].mute = True

            obj[key].mute = False
        else:
            obj[key].mute = True

    def save_chest_sizes(self, context:Context, obj, apply_target:str):
        apply_mq = self.get_mannequin_category(context)
        if obj["Lavabod"].mute:
            index  = 1
            backup = 0
        else:
            index  = 0
            backup = 1

        if apply_mq:
            presets = DevkitProps.mq_floats
        else:
            presets = DevkitProps.torso_floats

        for key in obj:
            if key.name.startswith("- "):
                name = key.name[2:]
                presets[backup]["Large"][name] = round(key.value, 2)
            if key.name.startswith("-- "):
                name = key.name[3:]
                presets[backup]["Medium"][name] = round(key.value, 2)
            if key.name.startswith("--- "):
                name = name = key.name[4:]
                presets[backup]["Small"][name] = round(key.value, 2)

        for size in presets[index].keys():
            preset = presets[index][size]
            ApplyShapes.apply_shape_values(apply_target, size, preset)
        
        self.force_update(apply_target)
        
    def force_update(self, apply_target:str):
        if apply_target == "torso":
            try:
                bpy.context.view_layer.objects.active = get_object_from_mesh("Torso")
            except:
                pass
        else:
            try:
                bpy.context.view_layer.objects.active = get_object_from_mesh("Mannequin")
            except:
                pass
        bpy.context.view_layer.update()

class ApplyVisibility(Operator):
    bl_idname = "yakit.apply_visibility"
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
            case "Shape":
                self.shape_visibility(collection)

        return {"FINISHED"}
    
    def chest_visibility(self, collection) -> None:
        if collection["Chest"].exclude:
            collection["Chest"].exclude = False
        else:
            collection["Chest"].exclude = True

    def legs_visibility(self, collection) -> None:
        if collection["Legs"].exclude:
            collection["Legs"].exclude = False
        else:
            collection["Legs"].exclude = True

    def feet_visibility(self, collection) -> None:
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
    
    def hand_visibility(self, collection) -> None:
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

    def shape_visibility(self, collection) -> None:
        if collection["Resources"].children["Controller"].children["Shape"].exclude:
            collection["Resources"].children["Controller"].children["Shape"].exclude = False
        else:
            collection["Resources"].children["Controller"].children["Shape"].exclude = True

class TriangulateLink(Operator):
    bl_idname = "yakit.triangulate_link"
    bl_label = "Overview"
    bl_description = "Links all Triangulate modifiers to this toggle"

    def execute(self, context):
        for obj in bpy.data.objects:
            tri_mod = [modifier for modifier in obj.modifiers if modifier.type == 'TRIANGULATE']
            for modifier in tri_mod:
                self.add_driver(modifier)
        return {'FINISHED'}

    def add_driver(self, modifier:ShapeKey) -> None:
            modifier.driver_remove("show_viewport")
            driver = modifier.driver_add("show_viewport").driver

            driver.type = "AVERAGE"
            driver_var  = driver.variables.new()
            driver_var.name = "show_viewport"
            driver_var.type = "SINGLE_PROP"

            driver_var.targets[0].id_type = 'OBJECT'
            driver_var.targets[0].id = get_object_from_mesh("Controller")
            driver_var.targets[0].data_path = f'modifiers["Triangulation"].show_viewport'

class ResetQueue(Operator):
    bl_idname = "yakit.reset_queue"
    bl_label = "Export"
    bl_description = "Resets Export UI if it ran into an error"

    @classmethod
    def poll(cls, context):
        return hasattr(context.scene, "file_props")

    def execute(self, context):
        bpy.context.scene.file_props.export_total = 0
        return {'FINISHED'}
        
class PanelCategory(Operator):
    bl_idname = "yakit.set_ui"
    bl_label = "Select the menu."
    bl_description = "Changes the panel menu"

    overview: StringProperty() # type: ignore
    panel: StringProperty() # type: ignore

    def execute(self, context):
        match self.panel:
            case "overview":
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

        obj = self.collection_context(context)
        key = obj.data.shape_keys
        layout = self.layout
        label_name = obj.name
        scene = context.scene
        section_prop = scene.devkit_props

        options ={
            "Body": "OUTLINER_OB_ARMATURE",
            "Shape Keys": "MESH_DATA",
            "Settings": "SETTINGS",
            "Info": "INFO",
            }

        box = layout.box()
        row = box.row(align=True)
        
        row.label(icon=options[section_prop.overview_ui])
        row.label(text=f"  {section_prop.overview_ui}")
        button_row = row.row(align=True)
        
        self.ui_category_buttons(button_row, section_prop, "overview_ui", options, "overview")
        
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
                obj, 
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
            icon = "HIDE_ON" if chest_col else "HIDE_OFF"
            chest_op = button_row.operator("yakit.apply_visibility", text="", icon=icon, depress=not chest_col)
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
            icon = "HIDE_ON" if leg_col else "HIDE_OFF"
            leg_op = button_row.operator("yakit.apply_visibility", text="", icon=icon, depress=not leg_col)
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
        if (section_prop.overview_ui == "Body" or section_prop.overview_ui == "Shape Keys") and hasattr(section_prop, "controller_yas_chest"):
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
            row.prop(section_prop, "controller_triangulation", text="Triangulation")
            row = layout.row(align=True)
            row.alignment = "CENTER"
            col = row.column(align=True)
            col.operator("yakit.triangulate_link", text=("Link Triangulation"))

            layout.separator(factor=1, type="LINE")

            row = layout.row(align=True)
            row.alignment = "CENTER"
            col = row.column(align=True)
            col.operator("yakit.reset_queue", text=("Reset Export"))
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
                       
    def collection_context(self, context:Context):
        # Links mesh name to the standard collections)
        body_part_collections = {
            "Torso": ['Chest', 'Nipple Piercings'],
            "Waist": ['Legs', 'Pubes'],
            "Hands": ['Hands', 'Nails', 'Practical Uses', 'Clawsies'],
            "Feet": ['Feet', 'Toenails', 'Toe Clawsies'] 
            }

        # Get the active object
        active_obj = bpy.context.active_object

        if active_obj and has_shape_keys(active_obj):
            if not context.scene.devkit_props.button_dynamic_view:
                return active_obj
            else:
                active_collection = active_obj.users_collection
                for body_part, collections in body_part_collections.items():
                    if any(bpy.data.collections[coll_name] in active_collection for coll_name in collections):
                        return get_object_from_mesh(body_part) 
                return active_obj
        else:
            return get_object_from_mesh("Mannequin")

    def chest_shapes(self, layout:UILayout, section_prop, mq:Object, torso:Object):
        layout.separator(factor=0.1)  
        if section_prop.shape_mq_chest_bool:
            target = mq
            key_target = "mq"
        else:
            target = torso
            key_target = "torso"

        medium_mute = target.data.shape_keys.key_blocks["MEDIUM"].mute
        small_mute = target.data.shape_keys.key_blocks["SMALL"].mute
        masc_mute = target.data.shape_keys.key_blocks["MASC"].mute
        buff_mute = target.data.shape_keys.key_blocks["Buff"].mute
        rue_mute = target.data.shape_keys.key_blocks["Rue"].mute
        lava_mute = target.data.shape_keys.key_blocks["Lavabod"].mute
        
        large_depress = True if small_mute and medium_mute and masc_mute else False
        medium_depress = True if not medium_mute and small_mute and masc_mute else False
        small_depress = True if not small_mute and medium_mute and masc_mute else False
        masc_depress = True if not masc_mute and medium_mute and small_mute else False
        buff_depress = True if not buff_mute else False
        rue_depress = True if not rue_mute else False
        lava_depress = True if not lava_mute else False
        
        row = layout.row(align=True)
        text = "Omoi" if lava_depress else "Large"
        operator = row.operator("yakit.apply_shapes", text=text, depress=large_depress)
        operator.key = "Large"
        operator.target = "Torso"
        operator.preset = "chest_category"
        text = "Teardrop" if lava_depress else "Medium"
        operator = row.operator("yakit.apply_shapes", text= text, depress=medium_depress)
        operator.key = "Medium"
        operator.target = "Torso"
        operator.preset = "chest_category"
        text = "Cupcake" if lava_depress else "Small"
        operator = row.operator("yakit.apply_shapes", text= text, depress=small_depress)
        operator.key = "Small"
        operator.target = "Torso"
        operator.preset = "chest_category"

        operator = row.operator("yakit.apply_shapes", text= "Masc", depress=masc_depress)
        operator.key = "Masc"
        operator.target = "Torso"
        operator.preset = "chest_category"

        row = layout.row(align=True)
        operator = row.operator("yakit.apply_shapes", text= "Buff", depress=buff_depress)
        operator.key = "Buff"
        operator.target = "Torso"
        operator.preset = "other"

        operator = row.operator("yakit.apply_shapes", text= "Rue", depress=rue_depress)
        operator.key = "Rue"
        operator.target = "Torso"
        operator.preset = "other"

        operator = row.operator("yakit.apply_shapes", text= "Lava", depress=lava_depress)
        operator.key = "Lavabod"
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
            if not masc_depress:
                col.label(text="Squeeze:")
            else:
                col.label(text="Pecs:")
            if large_depress or medium_depress:
                col.label(text="Squish:")
                col.label(text="Push-Up:")
            if medium_depress and not lava_depress:
                col.label(text="Sayonara:")
                col.label(text="Mini:")
            if large_depress and not lava_depress:
                col.label(text="Omoi:")
            if large_depress or medium_depress:
                col.label(text="Sag:")
            if large_depress and not lava_depress:
                col.label(text="Uranus:")
            if not lava_depress:
                col.label(text="Nip Nops:")
            else:
                if small_depress:
                    col.label(text="Sugar:")
                col.label(text="Soft Nips:")

            if large_depress:
                col2 = split.column(align=True)
                col2.prop(section_prop, f"key_squeeze_large_{key_target}")
                col2.prop(section_prop, f"key_squish_large_{key_target}")
                col2.prop(section_prop, f"key_pushup_large_{key_target}")
                if not lava_depress:
                    col2.prop(section_prop, f"key_omoi_large_{key_target}")
                col2.prop(section_prop, f"key_sag_omoi_{key_target}")
                if not lava_depress:
                    col2.prop(section_prop, f"key_uranusredux_large_{key_target}")
                    col2.prop(section_prop, f"key_nipnops_large_{key_target}")
                else:
                    col2.prop(section_prop, f"key_softnips_lavabod_{key_target}")
            elif medium_depress:
                col2 = split.column(align=True)
                col2.prop(section_prop, f"key_squeeze_medium_{key_target}")
                col2.prop(section_prop, f"key_squish_medium_{key_target}")
                col2.prop(section_prop, f"key_pushup_medium_{key_target}")
                if not lava_depress:
                    col2.prop(section_prop, f"key_sayonara_medium_{key_target}")
                    col2.prop(section_prop, f"key_mini_medium_{key_target}")
                col2.prop(section_prop, f"key_sag_medium_{key_target}")
                if not lava_depress:
                    col2.prop(section_prop, f"key_nipnops_medium_{key_target}")
                else:
                    col2.prop(section_prop, f"key_softnips_teardrop_{key_target}")

            elif small_depress:
                col2 = split.column(align=True)
                col2.prop(section_prop, f"key_squeeze_small_{key_target}")
                if not lava_depress:
                    col2.prop(section_prop, f"key_nipnops_small_{key_target}")
                else:
                    col2.prop(section_prop, f"key_sugar_cupcake_{key_target}")
                    col2.prop(section_prop, f"key_softnips_cupcake_{key_target}")
            
            elif masc_depress:
                col2 = split.column(align=True)
                col2.prop(section_prop, f"key_pecs_masc_{key_target}")
                col2.prop(section_prop, f"key_nipnops_masc_{key_target}")
     
        
        layout.separator(factor=0.1)

        row = layout.row()
        split = row.split(factor=0.25, align=True) 
        col = split.column(align=True)
        col.alignment = "RIGHT"
        col.label(text="Preset:")
        
        col2 = split.column(align=True)
        col2.prop(section_prop, "chest_shape_enum")

        col3 = split.column(align=True)
        operator = col3.operator("yakit.apply_shapes", text= "Apply")
        operator.preset = "SHAPES"
        operator.target = "Chest"

        layout.separator(factor=0.1)

    def leg_shapes(self, layout:UILayout, section_prop, mq:Object, legs:Object):
        layout.separator(factor=0.1)
        if section_prop.shape_mq_legs_bool:
            target = mq
        else:
            target = legs

        skull_mute = target.data.shape_keys.key_blocks["Skull Crushers"].mute
        mini_mute = target.data.shape_keys.key_blocks["Mini"].mute
        rue_mute = target.data.shape_keys.key_blocks["Rue"].mute
        lava_mute = target.data.shape_keys.key_blocks["Lavabod"].mute
        masc_mute = target.data.shape_keys.key_blocks["Masc"].mute

        genb_mute = target.data.shape_keys.key_blocks["Gen B"].mute
        genc_mute = target.data.shape_keys.key_blocks["Gen C"].mute
        gensfw_mute = target.data.shape_keys.key_blocks["Gen SFW"].mute

        small_mute = target.data.shape_keys.key_blocks["Small Butt"].mute
        soft_mute = target.data.shape_keys.key_blocks["Soft Butt"].mute

        hip_yab_mute = target.data.shape_keys.key_blocks["Hip Dips (for YAB)"].mute
        hip_rue_mute = target.data.shape_keys.key_blocks["Less Hip Dips (for Rue)"].mute

        melon_depress = True if skull_mute and mini_mute and lava_mute and masc_mute else False
        skull_depress = True if not skull_mute else False
        mini_depress = True if not mini_mute else False
        rue_depress = True if not rue_mute else False
        lava_depress = True if not lava_mute else False
        masc_depress = True if not masc_mute else False

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

        operator = button_row.operator("yakit.apply_shapes", text= "A", depress=gena_depress)
        operator.key = "Gen A"
        operator.target = "Legs"
        operator.preset = "gen"

        operator = button_row.operator("yakit.apply_shapes", text= "B", depress=genb_depress)
        operator.key = "Gen B"
        operator.target = "Legs"
        operator.preset = "gen"

        operator = button_row.operator("yakit.apply_shapes", text= "C", depress=genc_depress)
        operator.key = "Gen C"
        operator.target = "Legs"
        operator.preset = "gen"

        operator = button_row.operator("yakit.apply_shapes", text= "SFW", depress=gensfw_depress)
        operator.key = "Gen SFW"
        operator.target = "Legs"
        operator.preset = "gen"
        
        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Leg sizes:")
        button_row = split.row(align=True)
        operator = button_row.operator("yakit.apply_shapes", text= "Melon", depress=melon_depress)
        operator.key = "Melon"
        operator.target = "Legs"
        operator.preset = "leg_size"

        operator = button_row.operator("yakit.apply_shapes", text= "Skull", depress=skull_depress)
        operator.key = "Skull"
        operator.target = "Legs"
        operator.preset = "leg_size"

        operator = button_row.operator("yakit.apply_shapes", text= "Lava", depress=lava_depress)
        operator.key = "Lava"
        operator.target = "Legs"
        operator.preset = "leg_size"

        operator = button_row.operator("yakit.apply_shapes", text= "Masc", depress=masc_depress)
        operator.key = "Masc"
        operator.target = "Legs"
        operator.preset = "leg_size"

        operator = button_row.operator("yakit.apply_shapes", text= "Mini", depress=mini_depress)
        operator.key = "Mini"
        operator.target = "Legs"
        operator.preset = "leg_size"

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Butt options:")
        button_row = split.row(align=True)
        operator = button_row.operator("yakit.apply_shapes", text= "Small", depress=small_depress)
        operator.key = "Small Butt"
        operator.target = "Legs"
        operator.preset = "other"
        operator = button_row.operator("yakit.apply_shapes", text= "Soft", depress=soft_depress)
        operator.key = "Soft Butt"
        operator.target = "Legs"
        operator.preset = "other"

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        operator = split.operator("yakit.apply_shapes", text= "Alt Hips", depress=hip_depress)
        operator.key = "Alt Hips"
        operator.target = "Legs"
        operator.preset = "other"
        button_row = split.row(align=True)
        operator = button_row.operator("yakit.apply_shapes", text= "Rue", depress=rue_depress)
        operator.key = "Rue"
        operator.target = "Legs"
        operator.preset = "other"
        
        layout.separator(factor=0.1)

    def yas_menu(self, layout:UILayout, section_prop):
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

    def other_shapes(self, layout:UILayout, section_prop, mq:Object, hands:Object, feet:Object):
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
        lava_mute = target.data.shape_keys.key_blocks["Lavabod"].mute
        rue_f_mute = target_f.data.shape_keys.key_blocks["Rue"].mute

        long_depress = True if short_mute and ballerina_mute and stabbies_mute else False
        short_depress = True if not short_mute else False
        ballerina_depress = True if not ballerina_mute else False
        stabbies_depress = True if not stabbies_mute else False
        rue_depress = True if not rue_mute else False
        lava_depress = True if not lava_mute else False
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
            hands_op = button_row.operator("yakit.apply_visibility", text="", icon=icon, depress=not hands_col)
            hands_op.target = "Hands"
            hands_op.key = ""

        operator = button_row.operator("yakit.apply_shapes", text= "Rue", depress=rue_depress)
        operator.key = "Rue"
        operator.target = "Hands"
        operator.preset = "other"

        operator = button_row.operator("yakit.apply_shapes", text= "Lava", depress=lava_depress)
        operator.key = "Lavabod"
        operator.target = "Hands"
        operator.preset = "other"

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Nails:")
        button_row = split.row(align=True)
        if not section_prop.shape_mq_other_bool:
            icon = "HIDE_ON" if nails_col else "HIDE_OFF"
            operator = button_row.operator("yakit.apply_visibility", text="", icon=icon, depress=not nails_col)
            operator.key = "Nails"
            operator.target = "Hands"

        operator = button_row.operator("yakit.apply_shapes", text= "Long", depress=long_depress)
        operator.key = "Long"
        operator.target = "Hands"
        operator.preset = "nails"
        
        operator = button_row.operator("yakit.apply_shapes", text= "Short", depress=short_depress)
        operator.key = "Short"
        operator.target = "Hands"
        operator.preset = "nails"

        operator = button_row.operator("yakit.apply_shapes", text= "Ballerina", depress=ballerina_depress)
        operator.key = "Ballerina"
        operator.target = "Hands"
        operator.preset = "nails"

        operator = button_row.operator("yakit.apply_shapes", text= "Stabbies", depress=stabbies_depress)
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
            operator = button_row.operator("yakit.apply_visibility", text="", icon=icon, depress=not clawsies_col)
            operator.key = "Clawsies"
            operator.target = "Hands"
            operator = button_row.operator("yakit.apply_shapes", text= "Straight", depress=clawsies_depress)
            operator.key = "Curved"
            operator.target = "Hands"
            operator.preset = "other"
            operator = button_row.operator("yakit.apply_shapes", text= "Curved", depress=not clawsies_depress)
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
            feet_op = button_row.operator("yakit.apply_visibility", text="", icon=icon, depress=not feet_col)
            feet_op.target = "Feet"
            feet_op.key = ""
        operator = button_row.operator("yakit.apply_shapes", text= "Rue", depress=rue_f_depress)
        operator.key = "Rue"
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
            nail_op = split.operator("yakit.apply_visibility", text="", icon=icon, depress=not toenails_col)
            nail_op.key = "Nails"
            nail_op.target = "Feet"
            icon = "HIDE_ON" if toeclawsies_col else "HIDE_OFF"
            claw_op = split.operator("yakit.apply_visibility", text="", icon=icon, depress=not toeclawsies_col)
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
   
    def ui_category_buttons(self, layout:UILayout, section_prop, prop, options, panel:str):
        row = layout
        ui_selector = getattr(section_prop, prop)

        for slot, icon in options.items():
            depress = True if ui_selector == slot else False
            operator = row.operator("yakit.set_ui", text="", icon=icon, depress=depress)
            operator.overview = slot
            operator.panel = panel

CLASSES = [
    CollectionState,
    ObjectState,
    DevkitProps,
    CollectionManager,
    ApplyShapes,
    ApplyVisibility,
    TriangulateLink,
    ResetQueue,
    PanelCategory,
    Overview
]

def delayed_setup(dummy=None) -> None:
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
    
    devkit_registered = True
    return None

def cleanup_props(dummy=None) -> None:
    global devkit_registered  
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except:
            continue
    
    try:
        del bpy.types.Scene.devkit_props
    except:
        pass
    try:
        del bpy.types.Scene.collection_state
    except:
        pass
    try:
        del bpy.types.Scene.object_state
    except:
        pass
    
    bpy.app.handlers.load_post.remove(delayed_setup)
    bpy.app.handlers.load_pre.remove(cleanup_props)
    devkit_registered = False

def set_devkit_properties() -> None:
    bpy.types.Scene.devkit_props = PointerProperty(
        type=DevkitProps)
    
    bpy.types.Scene.collection_state = bpy.props.CollectionProperty(
        type=CollectionState)
    
    bpy.types.Scene.object_state = bpy.props.CollectionProperty(
        type=ObjectState)

    DevkitProps.ui_buttons()
    DevkitProps.shpk_bools()
    DevkitProps.export_bools()
 
def register():

    for cls in CLASSES:
        bpy.utils.register_class(cls)
        if cls == DevkitProps:
            set_devkit_properties()

    bpy.app.timers.register(delayed_setup, first_interval=1)
    bpy.app.handlers.load_post.append(delayed_setup)
    bpy.app.handlers.load_pre.append(cleanup_props)

if __name__ == "__main__":
    register()