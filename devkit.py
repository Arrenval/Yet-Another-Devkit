import os
import bpy   

from functools     import partial
from itertools     import combinations
from bpy.types     import Operator, Panel, PropertyGroup
from bpy.props     import StringProperty, EnumProperty, BoolProperty, PointerProperty, FloatProperty

# Global variable for making sure all functions can properly track the current export.
is_exporting: bool = False


addon_installed = "Yet Another Addon" in bpy.context.preferences.addons

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


def yas_state(self, context):
    show_modifier = self.toggle_yas
    
    modifier = self.modifiers.get("YAS Toggle")
    
    if modifier:
        modifier.show_viewport = show_modifier
        
def yas_gen_state(self, context):
    show_modifier = self.toggle_yas_gen
    
    modifier = self.modifiers.get("YAS Genitalia Toggle")
    
    if modifier:
        modifier.show_viewport = show_modifier

def force_yas(context):
    force_yas = context.scene.devkit_props.button_force_yas

    if force_yas:
        for obj in bpy.context.scene.objects:
            if obj.visible_get(view_layer=bpy.context.view_layer) and obj.type == "MESH":
                try:
                    obj.toggle_yas = True
                except:
                    continue

def get_object_from_mesh(mesh_name):
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and obj.data.name == mesh_name:
            return obj
    return None

def get_chest_size_keys(chest_subsize):
    """category, sizekey"""
    chest_category = get_chest_category(chest_subsize)
    
    size_key = {
        "Large": "LARGE -------------------------------",
        "Medium": "MEDIUM ----------------------------",
        "Small": "SMALL ------------------------------"
    }
    return size_key[chest_category]

def get_chest_category(size):
    """subsize, category"""
    if ALL_SHAPES[size][1] == "Chest":
        return ALL_SHAPES[size][2]
    else:
        return None

def get_shape_presets(size):
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

def has_shape_keys(ob):
        if ob and ob.type == "MESH":
            if ob.data.shape_keys is not None:
                return True
        return False

def get_filtered_shape_keys(obj, key_filter: list):
        shape_keys = obj.shape_keys.key_blocks
        key_list = []
        to_exclude = ["Mini", "Mini Heels", "Heels", "Cinderella"]
        
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

def check_triangulation(context):
    check_tris = context.scene.devkit_props.button_check_tris
    not_triangulated = []

    if check_tris:
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

def update_directory(category):
    prop = bpy.context.scene.devkit_props
    actual_prop = f"{category}_directory"
    display_prop = f"{category}_display_directory"

    display_directory = getattr(prop, display_prop, "")

    if os.path.exists(display_directory):  
        setattr(prop, actual_prop, display_directory)
        print (getattr(prop, actual_prop, ""))


class CollectionState(PropertyGroup):
    collection_name: bpy.props.StringProperty() # type: ignore


class DevkitProps(PropertyGroup):
    
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

    extra_buttons_list = [
        ("check",    "tris",     True, "Verify that the meshes have an active triangulation modifier"),
        ("force",    "yas",      False, "This force enables YAS on any exported model and appends 'Yiggle' to their file name. Use this if you already exported regular models and want YAS alternatives"),
        ]
   
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

    ui_buttons_list = [
    ("export",   "expand",   "Opens the category"),
    ("import",   "expand",   "Opens the category"),
    ("chest",    "shapes",   "Opens the category"),
    ("leg",      "shapes",   "Opens the category"),
    ("other",    "shapes",   "Opens the category"),
    ("chest",    "category", "Opens the category"),
    ("yas",      "expand",   "Opens the category"),
    ("modpack",  "expand",   "Opens the category"),
    ("export",   "options",  "Opens the category"),
    ("check",    "tris",     "Verify that the meshes have an active triangulation modifier"),
    ("force",    "yas",      "This force enables YAS on any exported model and appends 'Yiggle' to their file name. Use this if you already exported regular models and want YAS alternatives"),
    ("advanced", "expand",   "Switches between a simplified and full view of the shape keys"),
    ("dynamic",  "view",     "Toggles between a dynamic collection viewer and one constrained to the active object"),
    ("modpack",  "replace",  "Make new or update existing mod")
    ]
   
    mesh_list = [
        "Torso",
        "Waist",
        "Hands",
        "Feet",
        "Mannequin",
    ]

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

    bpy.types.Object.toggle_yas = bpy.props.BoolProperty(
    name="",
    description="Enable yiggle weights",
    default=False,
    update=yas_state
    )

    bpy.types.Object.toggle_yas_gen = bpy.props.BoolProperty(
    name="",
    description="Enable IVCS weights for the genitalia. YAS needs to be enabled",
    default=False,
    update=yas_gen_state
    )

    collection_state: bpy.props.CollectionProperty(type=CollectionState) # type: ignore

    export_body_slot: EnumProperty(
        name= "",
        description= "Select a body slot",
        items= [
            ("Chest", "Chest", "Chest export options."),
            ("Legs", "Legs", "Leg export options."),
            ("Hands", "Hands", "Hand export options."),
            ("Feet", "Feet", "Feet export options."),
            ("Chest/Legs", "Chest/Legs", "When you want to export Chest with Leg models.")]
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

    export_gltf: BoolProperty(
        name="",
        description="Switch export format", 
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
    bl_options = {'UNDO'}

    def __init__(self):
        self.coll = bpy.data.collections
        self.collections_to_keep = [
            self.coll["Skeleton"],
            self.coll["Resources"],
            self.coll["Data Sources"],
            self.coll["UV/Weights"],
            self.coll["Nail UVs"],
            self.coll["Rue"],
            self.coll["YAS"],
            self.coll["Piercings"]
        ]
   
    def execute(self, context): 
        collections = bpy.context.scene.devkit_props.collection_state
        
        for state in collections:
            name = state.collection_name
            new_collection = self.coll[name]
            self.collections_to_keep.append(new_collection)
        
        self.collections_to_keep = set(self.collections_to_keep)

        self.exclude_collections()
        bpy.context.view_layer.layer_collection.children['Resources'].hide_viewport = True
        return {"FINISHED"}

    def exclude_collections(self):
        # Eclude all collections except those to keep
        all_collections = bpy.data.collections
        
        # First set visible to avoid children being enabled
        for collection in self.collections_to_keep:
            self.toggle_collection_exclude(collection, exclude=False)

        # Exclude remaining collections
        for collection in all_collections:
            if collection not in self.collections_to_keep:
                self.toggle_collection_exclude(collection, exclude=True)
    
    def toggle_collection_exclude(self, collection, exclude=True):
            # Get the layer collections for the current scene and context
            for layer_collection in bpy.context.view_layer.layer_collection.children:
                self.recursively_toggle_exclude(layer_collection, collection, exclude)

    def recursively_toggle_exclude(self, layer_collection, collection, exclude):
        # check all layers for children and apply exclude state
        if layer_collection.collection == collection:
            layer_collection.exclude = exclude
        
        # Recursive check for child collections
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
    bl_description = "Hides selected nails/claws"
    bl_options = {'UNDO'}

    key: StringProperty() # type: ignore
    target: StringProperty() # type: ignore

    def execute(self, context):
        collection = bpy.context.view_layer.layer_collection.children
        if self.key == "Nails" and self.target == "Feet":
            
            if collection["Feet"].children["Toenails"].exclude:
                collection["Feet"].children["Toenails"].exclude = False
            else:
                collection["Feet"].children["Toenails"].exclude = True
        
        elif self.target == "Feet":

            if collection["Feet"].children["Toe Clawsies"].exclude:
                collection["Feet"].children["Toe Clawsies"].exclude = False
            else:
                collection["Feet"].children["Toe Clawsies"].exclude = True
    
        elif self.key == "Nails" and self.target == "Hands":

            if collection["Hands"].children["Nails"].exclude:
                collection["Hands"].children["Nails"].exclude = False
                collection["Hands"].children["Nails"].children["Practical Uses"].exclude = False
            else:
                collection["Hands"].children["Nails"].exclude = True

        elif self.target == "Hands" and self.key == "Clawsies":

            if collection["Hands"].children["Clawsies"].exclude:
                collection["Hands"].children["Clawsies"].exclude = False
            else:
                collection["Hands"].children["Clawsies"].exclude = True


        return {"FINISHED"}


class SimpleExport(Operator):
    bl_idname = "ya.simple_export"
    bl_label = "Open Export Window"
    bl_description = "Exports single model"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"
    
    def execute(self, context):
        triangulated, obj = check_triangulation(context)
        if not triangulated:
            self.report({'ERROR'}, f"Not Triangulated: {', '.join(obj)}")
            return {'CANCELLED'} 
        
        gltf = context.scene.devkit_props.export_gltf 
        directory = context.scene.devkit_props.export_directory
        export_path = os.path.join(directory, "untitled")
        export_settings = FileExport.get_export_settings(gltf)

        force_yas(context)

        if gltf:
            bpy.ops.export_scene.gltf('INVOKE_DEFAULT', filepath=export_path + ".gltf", **export_settings)
        else:
            bpy.ops.export_scene.fbx('INVOKE_DEFAULT', filepath=export_path + ".fbx", **export_settings)
        
        return {'FINISHED'}


class BatchQueue(Operator):
    bl_idname = "ya.batch_queue"
    bl_label = "Export"
    bl_description = "Exports your files based on your selections"
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
        self.queue = []
        self.leg_queue = []
        
    def execute(self, context):
        triangulated, obj = check_triangulation(context)
        if not triangulated:
            self.report({'ERROR'}, f"Not Triangulated: {', '.join(obj)}")
            return {'CANCELLED'} 
        
        prop = context.scene.devkit_props
        selected_directory = prop.export_directory
        self.gltf = prop.export_gltf
        self.body_slot = prop.export_body_slot
        
        if not os.path.exists(selected_directory):
            self.report({'ERROR'}, "No directory selected for export!")
            return {'CANCELLED'} 

        self.size_options = self.get_size_options(context)

        if self.body_slot == "Chest/Legs":
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
        
        if self.body_slot == "Chest/Legs":
            if self.leg_queue == []:
                self.report({'ERROR'}, "No valid combinations!")
                return {'CANCELLED'} 
            
        self.collection_state(context)
        bpy.ops.ya.collection_manager()

        force_yas(context)
        if "Chest" in self.body_slot:
            obj = get_object_from_mesh("Torso")
            yas = obj.modifiers["YAS Toggle"].show_viewport
            BatchQueue.ivcs_mune(context, yas)

        BatchQueue.process_queue(context, self.queue, self.leg_queue, self.body_slot, gen_options)
        return {'FINISHED'}
    
    # The following functions is executed to establish the queue and valid options 
    # before handing all variables over to queue processing

    def collection_state(self, context):
        context.scene.devkit_props.collection_state.clear()
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

            case "Chest/Legs":
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
            collection_state = context.scene.devkit_props.collection_state.add()
            collection_state.collection_name = name

    def get_size_options(self, context):
        options = {}
        prop = context.scene.devkit_props

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

        leg_sizes = {
            "Melon": self.size_options["Melon"],
            "Skull": self.size_options["Skull"], 
            "Mini Legs": self.size_options["Mini Legs"]
            }

        if body_slot != "Legs":
            gen = None             
            for size, options_groups in self.actual_combinations.items(): 
                for options in options_groups:
                    self.queue.append((options, size, gen, target))
            return "Main queue finished."

        # Legs need different handling due to genitalia combos     
        for size, enabled in leg_sizes.items():
            if enabled:
                for gen, options_groups in self.actual_combinations.items(): 
                    for options in options_groups:
                        if self.body_slot == "Chest/Legs":
                            self.leg_queue.append((options, size, gen, target))
                        else:
                            self.queue.append((options, size, gen, target))
        if self.leg_queue != []:
            return "No leg options selected."
        
        return "Leg queue finished."
 
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

    # These functions are responsible for processing the queue.
    # Export queue is running on a timer interval until the queue is empty.

    def process_queue(context, queue, leg_queue, body_slot, gen_options):
        global is_exporting
        is_exporting = False

        callback = partial(BatchQueue.export_queue, context, queue, leg_queue, body_slot, gen_options)
        
        bpy.app.timers.register(callback, first_interval=0.5) 

    def export_queue(context, queue, leg_queue, body_slot, gen_options):
        collection = bpy.context.view_layer.layer_collection.children
        global is_exporting

        if is_exporting:
            return 0.1
        
        second_queue = leg_queue

        is_exporting = True
        options, size, gen, target = queue.pop()
        
        BatchQueue.reset_model_state(body_slot, target)

        main_name = BatchQueue.name_generator(options, size, gen, gen_options, body_slot)
        BatchQueue.apply_model_state(options, size, gen, body_slot, target)

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
        
        if body_slot == "Chest/Legs":
            for leg_task in second_queue:
                options, size, gen, leg_target = leg_task
                if BatchQueue.check_rue_match(options, main_name):
                    body_slot = "Legs"
                    
                    BatchQueue.reset_model_state(body_slot, leg_target)
                    BatchQueue.apply_model_state(options, size, gen, body_slot, leg_target)

                    leg_name = BatchQueue.name_generator(options, size, gen, gen_options, body_slot)
                    main_name = leg_name + " - " + main_name
                    main_name = BatchQueue.clean_file_name(main_name)

                    FileExport.export_template(context, file_name=main_name)
        
        else:
            FileExport.export_template(context, file_name=main_name)

        is_exporting = False

        if queue:
            return 0.1
        else:
            if "Chest" in body_slot:
                obj = get_object_from_mesh("Torso")
                BatchQueue.ivcs_mune(context, obj)
            return None

    # These functions are responsible for applying the correct model state and appropriate file name.
    # They are called from the export_queue function.

    def check_rue_match (options, file_name):
        
        if "Rue" in file_name:
            if any("Rue" in option for option in options):
                return True
            else:
                return False
    
        return True

    def clean_file_name (file_name):
        first = file_name.find("Rue - ")

        second = file_name.find("Rue - ", first + len("Rue - "))

        if second == -1:
            return file_name
        
        return file_name[:second] + file_name[second + len("Rue - "):]

    def apply_model_state(options, size, gen, body_slot, ob):
        if body_slot == "Chest/Legs":
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
                        
    def name_generator(options, size, gen, gen_options, body_slot):
        yiggle = bpy.context.scene.devkit_props.button_force_yas

        if body_slot == "Chest/Legs":
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
    
    def reset_model_state(body_slot, ob):
        if body_slot == "Chest/Legs":
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

    def ivcs_mune(context, yas=False):
        for obj in bpy.context.scene.objects:
            if obj.visible_get(view_layer=bpy.context.view_layer) and obj.type == "MESH":
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
      
    
class FileExport(Operator):
    bl_idname = "ya.file_export"
    bl_label = "Export"
    bl_description = ""
    bl_options = {'UNDO'}

    file_name: StringProperty() # type: ignore

    def execute(self, context):
            FileExport.export_template(context, self.file_name)

    def export_template(context, file_name):
        gltf = context.scene.devkit_props.export_gltf
        selected_directory = context.scene.devkit_props.export_directory

        export_path = os.path.join(selected_directory, file_name)
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


class BodyPartSlot(Operator):
    bl_idname = "ya.set_body_part"
    bl_label = "Select body slot to export."
    bl_description = "The icons almost make sense"

    body_part: StringProperty() # type: ignore

    def execute(self, context):
        # Update the export_body_part with the selected body part
        context.scene.devkit_props.export_body_slot = self.body_part
        return {'FINISHED'}


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
        selected_file = self.directory  

        if os.path.isdir(selected_file):
            setattr(context.scene.devkit_props, actual_dir_prop, selected_file)
            display_dir = self.directory_short(selected_file, 3) 

            setattr(context.scene.devkit_props, display_dir_prop, display_dir)
            self.report({"INFO"}, f"Directory selected: {selected_file}")
        
        else:
            self.report({"ERROR"}, "Not a valid path!")
        
        return {'FINISHED'}
    
    def directory_short(directory, amount):
        if os.path.exists(directory):
            try:
                full_path = os.path.normpath(directory)

                path_parts = full_path.split(os.sep)

                last_folders = os.sep.join(path_parts[-amount:])

                return last_folders
            except:
                full_path = os.path.normpath(directory)

                path_parts = full_path.split(os.sep)

                last_folders = os.sep.join(path_parts[-1:])

                return last_folders

        else:
            return None

    
class Overview(Panel):
    bl_idname = "VIEW3D_PT_YA_Overview"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Devkit"
    bl_label = "Yet Another Overview"

    def draw(self, context):
        mq = get_object_from_mesh("Mannequin")
        torso = get_object_from_mesh("Torso")
        legs = get_object_from_mesh("Waist")
        hands = get_object_from_mesh("Hands")
        feet = get_object_from_mesh("Feet")

        ob = self.collection_context(context)
        key = ob.data.shape_keys
        layout = self.layout
        label_name = ob.data.name
        scene = context.scene
        section_prop = scene.devkit_props
        section_props = scene.devkit_props

        button_adv = section_props.button_advanced_expand

        # SHAPE MENUS
        
        if button_adv:
            box = layout.box()
            row = box.row(align=True)
            row.label(text=f"{label_name}:")
            text = "Collection" if section_prop.button_dynamic_view else "Active"
            row.prop(section_prop, "button_dynamic_view", text=text, icon="HIDE_OFF")
        
            row.alignment = "RIGHT"
            row.prop(section_props, "button_advanced_expand", text="", icon="TOOL_SETTINGS")
            

            row = layout.row()
            row.template_list(
                "MESH_UL_shape_keys", 
                "", 
                key, 
                "key_blocks", 
                ob, 
                "active_shape_key_index", 
                rows=10)
        
        if not button_adv:
            
            # CHEST

            button = section_prop.button_chest_shapes

            box = layout.box()
            row = box.row(align=True)
            
            icon = 'TRIA_DOWN' if button else 'TRIA_RIGHT'
            row.prop(section_prop, "button_chest_shapes", text="", icon=icon, emboss=False)
            row.label(text="CHEST")
            
            button_row = row.row(align=True)
            button_row.prop(section_prop, "shape_mq_chest_bool", text="", icon="ARMATURE_DATA")
            button_row.prop(section_prop, "button_advanced_expand", text="", icon="TOOL_SETTINGS")

            if button:
                box.separator(factor=0.5,type="LINE")
                self.chest_shapes(box, section_prop, mq, torso)

            layout.separator(factor=0.1)

            # LEGS

            button = section_prop.button_leg_shapes

            box = layout.box()
            row = box.row(align=True)
            
            icon = 'TRIA_DOWN' if button else 'TRIA_RIGHT'
            row.prop(section_prop, "button_leg_shapes", text="", icon=icon, emboss=False)
            row.label(text="LEGS")
            
            button_row = row.row(align=True)
            button_row.prop(section_prop, "shape_mq_legs_bool", text="", icon="ARMATURE_DATA")

            if button:
                box.separator(factor=0.5,type="LINE")
                self.leg_shapes(box, section_prop, mq, legs)

            layout.separator(factor=0.1)
            
            # OTHER

            button = section_prop.button_other_shapes

            box = layout.box()
            row = box.row(align=True)
            icon = 'TRIA_DOWN' if button else 'TRIA_RIGHT'
            row.prop(section_prop, "button_other_shapes", text="", icon=icon, emboss=False)
            row.label(text="HANDS/FEET")
            
            button_row = row.row(align=True)
            button_row.prop(section_prop, "shape_mq_other_bool", text="", icon="ARMATURE_DATA")

            if button:
                box.separator(factor=0.5,type="LINE")
                self.other_shapes(box, section_prop, mq, hands, feet)

        layout.separator(factor=0.1)

        # YAS MENU

        button = section_props.button_yas_expand                          

        box = layout.box()
        row = box.row(align=True)
        row.alignment = 'LEFT'
        
        icon = 'TRIA_DOWN' if button else 'TRIA_RIGHT'
        row.prop(section_prop, "button_yas_expand", text="", icon=icon, emboss=False)
        row.label(text="YET ANOTHER SKELETON")

        if button:
            box.separator(factor=0.5,type="LINE")
            row = box.row(align=True)
            icon = 'CHECKMARK' if torso.toggle_yas else 'PANEL_CLOSE'
            row.prop(torso, "toggle_yas", text="Chest", icon=icon)
            icon = 'CHECKMARK' if hands.toggle_yas else 'PANEL_CLOSE'
            row.prop(hands, "toggle_yas", text="Hands", icon=icon)
            icon = 'CHECKMARK' if feet.toggle_yas else 'PANEL_CLOSE'
            row.prop(feet, "toggle_yas", text="Feet", icon=icon)

            box.separator(factor=0.5,type="LINE")

            row = box.row(align=True)
            col2 = row.column(align=True)
            col2.label(text="Legs:")
            icon = 'CHECKMARK' if legs.toggle_yas else 'PANEL_CLOSE'
            col2.prop(legs, "toggle_yas", text="YAS", icon=icon)
            icon = 'CHECKMARK' if legs.toggle_yas_gen else 'PANEL_CLOSE'
            col2.prop(legs, "toggle_yas_gen", text="Genitalia", icon=icon)

            col = row.column(align=True)
            col.label(text="Mannequin:")
            icon = 'CHECKMARK' if mq.toggle_yas else 'PANEL_CLOSE'
            col.prop(mq, "toggle_yas", text="YAS", icon=icon)
            icon = 'CHECKMARK' if mq.toggle_yas_gen else 'PANEL_CLOSE'
            col.prop(mq, "toggle_yas_gen", text="Genitalia", icon=icon) 

            box.separator(factor=0.1)
            
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

        layout.separator(factor=0.5,type="LINE")

        row = layout.row()
        
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

        layout.separator(factor=0.5,type="LINE")
        
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
        nails_col = bpy.context.view_layer.layer_collection.children["Hands"].children["Nails"].exclude
        toenails_col = bpy.context.view_layer.layer_collection.children["Feet"].children["Toenails"].exclude

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Hands:")
        button_row = split.row(align=True)
        operator = button_row.operator("ya.apply_shapes", text= "Rue", depress=rue_depress)
        operator.key = "Rue"
        operator.target = "Hands"
        operator.preset = "other"

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Nails:")
        button_row = split.row(align=True)
        icon = "HIDE_ON" if nails_col else "HIDE_OFF"
        if not section_prop.shape_mq_other_bool:
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
        operator = button_row.operator("ya.apply_shapes", text= "Rue", depress=rue_f_depress)
        operator.key = "Rue"
        operator.target = "Feet"

        if not section_prop.shape_mq_other_bool:
            row = layout.row(align=True)
            col = row.column(align=True)
            row = col.row(align=True)
            split = row.split(factor=0.25, align=True)
            split.alignment = 'RIGHT'  # Align label to the right
            split.label(text="Nails/Claws:")
            icon = "HIDE_ON" if nails_col else "HIDE_OFF"
            operator = split.operator("ya.apply_visibility", text="", icon=icon, depress=not toenails_col)
            operator.key = "Nails"
            operator.target = "Feet"
            split.operator("ya.apply_visibility", text="", icon=icon, depress=not toeclawsies_col).target = "Feet"
        
        row = layout.row(align=True)
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


class FileManager(Panel):
    bl_idname = "VIEW3D_PT_YA_FileManager"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Devkit"
    bl_label = "File Manager"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2

    def draw(self, context):
        layout = self.layout
        section_prop = context.scene.devkit_props

        # EXPORT
        button = section_prop.button_export_expand
        box = self.dropdown_header(button, section_prop, "button_export_expand", "EXPORT", "EXPORT")
        if button:
            box.separator(factor=0.5,type="LINE")
            self.draw_export(box, section_prop)

        layout.separator(factor=0.1)

        # IMPORT
        button = section_prop.button_import_expand
        box = self.dropdown_header(button, section_prop, "button_import_expand", "IMPORT", "IMPORT")

        layout.separator(factor=0.1)

        if addon_installed:
            section_prop = context.scene.ya_props
            # MODPACKER
            button = section_prop.button_modpack_expand
            box = self.dropdown_header(button, section_prop, "button_modpack_expand", "MODPACK", "NEWFOLDER")

            if button :
                
                self.draw_modpack(layout, section_prop)
            
    def draw_export(self, layout, section_prop):
        row = layout.row(align=True)
        row.prop(section_prop, "export_display_directory", text="")
        row.operator("ya.dir_selector", icon="FILE_FOLDER", text="").category = "export"

        row = layout.row(align=True)
        col = row.column(align=True)
        col.operator("ya.simple_export", text="Simple Export")
        col2 = row.column(align=True)
        col2.operator("ya.batch_queue", text="Batch Export")
        
        export_text = "GLTF" if section_prop.export_gltf else "FBX"
        icon = "BLENDER" if section_prop.export_gltf else "VIEW3D"
        col3 = row.column(align=True)
        col3.alignment = "RIGHT"
        col3.prop(section_prop, "export_gltf", text=export_text, icon=icon, invert_checkbox=True)


        layout.separator(factor=1, type='LINE')


        row = layout.row(align=True)
        if section_prop.export_body_slot == "Chest/Legs":
            row.label(text=f"Body Part: Chest")
        else:
            row.label(text=f"Body Part: {section_prop.export_body_slot}")

        options =[
            ("Chest", "MOD_CLOTH"),
            ("Legs", "BONE_DATA"),
            ("Hands", "VIEW_PAN"),
            ("Feet", "VIEW_PERSPECTIVE"),
            ("Chest/Legs", "ARMATURE_DATA")
            ]
        
        self.body_category_buttons(row, section_prop, options)
    
            
        # CHEST EXPORT  
        
        button_type = "export"
        if section_prop.export_body_slot == "Chest" or section_prop.export_body_slot == "Chest/Legs":

            category = "Chest"
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

            layout.separator(factor=1)

            labels = {"Buff": "Buff", "Rue": "Rue", "Piercings": "Piercings"}
    
            self.dynamic_column_buttons(3, layout, section_prop, labels, category, button_type)

            if section_prop.export_body_slot == "Chest/Legs":
                layout.separator(factor=1, type="LINE")
                row = layout.row(align=True)
                row.label(text=f"Body Part: Legs")
            
        # LEG EXPORT  
        
        if section_prop.export_body_slot == "Legs" or section_prop.export_body_slot == "Chest/Legs":
            
            category = "Legs"
            labels = {
                "Melon": "Melon",
                "Skull": "Skull",  
                "Mini": "Mini",
                "Small Butt": "Small Butt",
                "Rue": "Rue",
                "Soft Butt": "Soft Butt", 
                    
                }
    
            self.dynamic_column_buttons(3, layout, section_prop, labels, category, button_type)

            row = layout.row(align=True)
            row.alignment = "CENTER"
            row.label(text="One leg and gen shape is required.")

            labels = {
                "Gen A":  "Gen A",
                "Gen B":  "Gen B", 
                "Gen C":  "Gen C",
                "Hip Dips":  "Hip Dips", 
                "Gen SFW":  "Gen SFW",
                "Pubes":  "Pubes"
            }
    
            self.dynamic_column_buttons(3, layout, section_prop, labels, category, button_type)  

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

            labels = { 
                "Clawsies": "Clawsies"
                }

            self.dynamic_column_buttons(2, layout, section_prop, labels, category, button_type)
       
        layout.separator(factor=0.5, type="LINE")

        button = section_prop.button_export_options
        
        row = layout.row(align=True)
        split = row.split(factor=1)
        sub = split.row(align=True)
        sub.alignment = 'LEFT'

        icon = 'TRIA_DOWN' if button else 'TRIA_RIGHT'
        sub.prop(section_prop, "button_export_options", text="", icon=icon, emboss=False)
        sub.label(text="Advanced Options")
        if button:
            row = layout.row(align=True)
            col = row.column(align=True)
            icon = 'CHECKMARK' if section_prop.force_yas else 'PANEL_CLOSE'
            col.prop(section_prop, "force_yas", text="Force YAS", icon=icon)
            col2 = row.column(align=True)
            icon = 'CHECKMARK' if section_prop.check_tris else 'PANEL_CLOSE'
            col2.prop(section_prop, "check_tris", text="Check Triangulation", icon=icon)

            

        layout.separator(factor=0.5)

    def draw_modpack(self, layout, section_prop):
        layout.separator(factor=0.5,type="LINE")
        row = layout.row(align=True)
        split = row.split(factor=0.65, align=True)
        icon = "CHECKMARK" if section_prop.consoletools_status == "ConsoleTools Ready!" else "X"
        split.label(text=section_prop.consoletools_status, icon=icon)
        split.operator("ya.file_console_tools", text="Check")
        row.operator("ya.consoletools_dir", icon="FILE_FOLDER", text="")

        layout.separator(factor=0.5,type="LINE")

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Model:")
        split.prop(section_prop, "game_model_path", text="")
        model_path = section_prop.game_model_path
        icon = "CHECKMARK" if model_path.startswith("chara") or model_path.endswith("mdl") else "X"
        row.label(icon=icon)
        
        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="FBX:")
        split.prop(section_prop, "savemodpack_display_directory", text="")
        
        row.operator("ya.dir_selector", icon="FILE_FOLDER", text="").category = "savemodpack"

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.label(text="")
        split.operator("ya.directory_copy", text="Copy from Export") 

        row = layout.row(align=True)
        row.prop(section_prop, "button_modpack_replace", text="New", icon="FILE_NEW", invert_checkbox=True)
        row.prop(section_prop, "button_modpack_replace", text="Update", icon="CURRENT_FILE",)

        if section_prop.button_modpack_replace:

            row = layout.row()
            split = row.split(factor=0.33)
            col2 = split.column(align=True)
            col2.label(text="Ver.")
            col2.prop(section_prop, "loadmodpack_version", text="")
            col = split.column(align=True)
            col.label(text="Modpack:")
            col.prop(section_prop, "loadmodpack_display_directory", text="", emboss=False)
            split2 = row.split(factor=0.8)
            col3 = split2.column(align=True)
            col3.alignment = "CENTER"
            col3.label(text="")
            col3.prop(section_prop, "loadmodpack_author", text="by", emboss=False)

        
            row = layout.row(align=True)
            split = row.split(factor=0.25, align=True)
            split.label(text="")
            split.operator("ya.pmp_selector", icon="FILE_FOLDER", text="Choose Modpack")
            
            
            row = layout.row(align=True)
            split = row.split(factor=0.25, align=True)
            split.alignment = "RIGHT"
            split.label(text="Replace:")
            split.prop(section_prop, "modpack_groups", text="")

            row = layout.row()
            split = row.split(factor=0.25)
            col2 = split.column(align=True)
            if section_prop.modpack_groups == "0":
                col2.prop(section_prop, "mod_group_type", text="")
            else:
                text = "" if section_prop.modpack_groups == "0" else "Rename:"
                col2.alignment = "RIGHT"
                col2.label(text=text)
            col = split.column(align=True)
            col.prop(section_prop, "modpack_rename_group", text="")
        
        else:
            

            row = layout.row()
            split = row.split(factor=0.25)
            col2 = split.column(align=True)
            col2.label(text="Ver.")
            col2.prop(section_prop, "new_mod_version", text="")
            col = split.column(align=True)
            col.label(text="Mod Name:")
            col.prop(section_prop, "new_mod_name", text="")

            row = layout.row()
            split = row.split(factor=0.25)
            col2 = split.column(align=True)
            col2.label(text="Type:")
            col2.prop(section_prop, "mod_group_type", text="")
            col = split.column(align=True)
            col.label(text="Group Name:")
            col.prop(section_prop, "modpack_rename_group", text="")

            row = layout.row(align=True)
            split = row.split(factor=0.25, align=True)
            split.alignment = "RIGHT"
            split.label(text="Author:")
            split.prop(section_prop, "author_name", text="")



        row = layout.row(align=True)
        row.operator("ya.file_modpacker", text="Convert & Pack").preset = "convert_pack"
        row.operator("ya.file_modpacker", text="Convert").preset = "convert"
        row.operator("ya.file_modpacker", text="Pack").preset = "pack"

        layout.separator(factor=0.5, type="LINE")

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Status:")
        split.prop(section_prop, "modpack_progress", text="", emboss=False)

        layout.separator(factor=0.1)
        
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
    DevkitProps,
    CollectionManager,
    ApplyShapes,
    ApplyVisibility,
    SimpleExport,
    BatchQueue,
    FileExport,
    BodyPartSlot,
    DirSelector
]

UI_CLASSES = [
    Overview,
    FileManager
]


def delayed_setup():
    DevkitProps.chest_key_floats()
    DevkitProps.feet_key_floats()

def set_devkit_properties():
    bpy.types.Scene.devkit_props = PointerProperty(
        type=DevkitProps)
    
    bpy.types.Scene.collection_state = bpy.props.CollectionProperty(
        type=CollectionState)

    DevkitProps.ui_buttons()
    bpy.app.timers.register(delayed_setup, first_interval=1.0)
    
    DevkitProps.export_bools()
    DevkitProps.extra_options()


def register():

    for cls in CLASSES:
        bpy.utils.register_class(cls)

    set_devkit_properties()

    for cls in UI_CLASSES:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(CLASSES + UI_CLASSES):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.devkit_props
    del bpy.types.Scene.collection_state

if __name__ == "__main__":
    register()