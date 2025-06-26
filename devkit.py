DEVKIT_VER = (0, 15, 0)

import bpy   

from typing    import TYPE_CHECKING, Iterable
from bpy.props import StringProperty, EnumProperty, BoolProperty, PointerProperty, FloatProperty, CollectionProperty
from bpy.types import Operator, Panel, PropertyGroup, Object, Mesh, Context, UILayout, ShapeKey, Collection, LayerCollection

devkit_registered: bool = False

def assign_controller_meshes():
    props = get_devkit_props()
    mesh_names = ["Torso", "Waist", "Hands", "Feet", "Mannequin"]
    
    for mesh_name in mesh_names:
        obj = None

        for scene_obj in bpy.context.scene.objects:
            if scene_obj.type == "MESH" and scene_obj.data.name == mesh_name:
                obj = scene_obj
                break
        
        if obj:
            if mesh_name == "Waist":
                mesh_name = "Legs"
            prop_name = f"yam_{mesh_name.lower()}"
            setattr(props, prop_name, obj)

def get_object_from_mesh(mesh_name:str) -> Object | None:
    props = get_devkit_props()
    controllers = {
        "Torso": props.yam_torso,
        "Waist": props.yam_legs,
        "Hands": props.yam_hands,
        "Feet":  props.yam_feet,
        "Mannequin": props.yam_mannequin,
    }

    if controllers[mesh_name] is None:
        assign_controller_meshes()


    return controllers[mesh_name]

def has_shape_keys(obj:Object) -> bool:
        if obj and obj.type == "MESH":
            if obj.data.shape_keys:
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

class DevkitWindowProps(PropertyGroup):
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
        ]

    @staticmethod
    def ui_buttons() -> None:
        for (name, category, description) in DevkitWindowProps.ui_buttons_list:
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
            setattr(DevkitWindowProps, prop_name, prop)

    @staticmethod
    def export_bools() -> None:
        """These are used in Yet Another Addon's batch export menu to very which shapes are available in the current kit."""
        for shape, (name, slot, shape_category, description, body, key) in DevkitProps.ALL_SHAPES.items():
            slot_lower = slot.lower().replace("/", " ")
            name_lower = name.lower().replace(" ", "_")
            
            prop_name = f"export_{name_lower}_{slot_lower}_bool"
            prop = BoolProperty(
                name="", 
                description=description,
                default=False, 
                )
            setattr(DevkitWindowProps, prop_name, prop)

    @staticmethod
    def shpk_bools() -> None:
        """These are used in Yet Another Addon's shape key menu to very which shapes are available in the current kit."""
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

    devkit_triangulation: BoolProperty(
        default=True,
        name="Triangulation",
        description="Toggles triangulation of the devkit",
        update=lambda self, context: bpy.context.view_layer.update()) # type: ignore
    
    if TYPE_CHECKING:
        overview_ui: str
        devkit_triangulation: bool

class CollectionState(PropertyGroup):
    name: StringProperty() # type: ignore
    
    if TYPE_CHECKING:
        name: str

class ObjectState(PropertyGroup):
    name: StringProperty() # type: ignore
    hide: BoolProperty() # type: ignore

    if TYPE_CHECKING:
        name: str
        hide: bool

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
            "Flat":         ("Flat",         "Chest",        "Masc",   "Yet Another Masc",                                    True,               "MASC"),
            "Pecs":         ("Pecs",         "Chest",        "Masc",   "Defined Pecs for Masc",                               False,               ""),
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
            "Yanilla":      ("Yanilla",      "Legs",         "Legs",   "As Yoshi-P intended",                                 False,               "Yanilla"),
            "Small Butt":   ("Small Butt",   "Legs",         "Butt",   "Not actually small, except when it is",               False,               "Small Butt"),
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
        "Large" : {"- Squeeze": 0.3, "- Squish": 0.0,  "- Push-Up": 0.0,  "- Omoi": 0.0, "- Uranus Redux": 0.0, "- Sag": 0.0, "- Nip Nops": 0.0},
        "Medium": {"-- Squeeze": 0.0, "-- Squish": 0.0,  "-- Push-Up": 0.0,  "-- Mini": 0.0, "-- Sayonara": 0.0,     "-- Sag": 0.0, "-- Nip Nops": 0.0},
        "Small" : {"--- Squeeze": 0.0,                                                                                "--- Nip Nops": 0.0}},
        #Lava
        {
        "Large" : {"- Squeeze": 0.0, "- Squish": 0.0,  "- Push-Up": 0.0,  "- Omoi": 0.0, "- Uranus Redux": 0.0, "- Sag": 0.0, "- Nip Nops": 0.0},
        "Medium": {"-- Squeeze": 0.0, "-- Squish": 0.0,  "-- Push-Up": 0.0,  "-- Mini": 0.0, "-- Sayonara": 0.0,     "-- Sag": 0.0, "-- Nip Nops": 0.0},
        "Small" : {"--- Squeeze": 0.0,  "--- Sugar": 0.0,                                                                 "--- Nip Nops": 0.0}}]
    
    mq_floats = [{
        #YAB
        "Large" : {"- Squeeze": 0.3, "- Squish": 0.0,  "- Push-Up": 0.0,  "- Omoi": 0.0, "- Uranus Redux": 0.0, "- Sag": 0.0, "- Nip Nops": 0.0},
        "Medium": {"-- Squeeze": 0.0, "-- Squish": 0.0,  "-- Push-Up": 0.0,  "-- Mini": 0.0, "-- Sayonara": 0.0,     "-- Sag": 0.0, "-- Nip Nops": 0.0},
        "Small" : {"--- Squeeze": 0.0,                                                                                "--- Nip Nops": 0.0}},
        #Lava
        {
        "Large" : {"- Squeeze": 0.0, "- Squish": 0.0,  "- Push-Up": 0.0,  "- Omoi": 0.0, "- Uranus Redux": 0.0, "- Sag": 0.0, "- Nip Nops": 0.0},
        "Medium": {"-- Squeeze": 0.0, "-- Squish": 0.0,  "-- Push-Up": 0.0,  "-- Mini": 0.0, "-- Sayonara": 0.0,     "-- Sag": 0.0, "-- Nip Nops": 0.0},
        "Small" : {"--- Squeeze": 0.0,  "--- Sugar": 0.0,                                                                 "--- Nip Nops": 0.0}}]
    
    mesh_list = [
        "Torso",
        "Waist",
        "Hands",
        "Feet",
        "Mannequin",
    ]

    yam_torso: PointerProperty(
        type=Object,
        name="",
        description="Essential for devkit functionality",
        poll=lambda self, obj: obj.type == "MESH" and "Torso" in obj.data.name
    ) # type: ignore
    
    yam_legs: PointerProperty(
        type=Object,
        name="",
        description="Essential for devkit functionality",
        poll=lambda self, obj: obj.type == "MESH" and "Waist" in obj.data.name
    ) # type: ignore

    yam_hands: PointerProperty(
        type=Object,
        name="",
        description="Essential for devkit functionality",
        poll=lambda self, obj: obj.type == "MESH" and "Hands" in obj.data.name
    ) # type: ignore

    yam_feet: PointerProperty(
        type=Object,
        name="",
        description="Essential for devkit functionality",
        poll=lambda self, obj: obj.type == "MESH" and "Feet" in obj.data.name
    ) # type: ignore

    yam_mannequin: PointerProperty(
        type=Object,
        name="",
        description="Essential for devkit functionality",
        poll=lambda self, obj: obj.type == "MESH" and "Mannequin" in obj.data.name
    ) # type: ignore

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
            var.targets[0].data_path = f"ya_devkit_props.{prop_name}"  

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

    if TYPE_CHECKING:
        chest_shape_enum   : str
        shape_mq_chest_bool: bool
        shape_mq_legs_bool : bool
        shape_mq_other_bool: bool
        collection_state   : Iterable[CollectionState]
        object_state       : Iterable[ObjectState]

        yam_torso          : Object
        yam_legs           : Object
        yam_hands          : Object
        yam_feet           : Object
        yam_mannequin      : Object

class CollectionManager(Operator):
    bl_idname = "yakit.collection_manager"
    bl_label = "Export"
    bl_description = "Combines chest options and exports them"

    preset: StringProperty() # type: ignore

    def execute(self, context:Context):
        self.props             :DevkitProps     = get_devkit_props()
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
        ]
        self.restore = []
        self.obj_visibility = {}

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

        def save_current_state_recursive(layer_collection:LayerCollection):
            if not layer_collection.exclude:
                    state = self.collections_state.add()
                    state.name = layer_collection.name
            for child in layer_collection.children:
                save_current_state_recursive(child)

        self.collections_state.clear()
        for layer_collection in context.view_layer.layer_collection.children:
            save_current_state_recursive(layer_collection)
      
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

        def recursively_toggle_exclude(layer_collection:LayerCollection, collection:Collection, exclude):
            if layer_collection.collection.name == collection.name:
                layer_collection.exclude = exclude
        
            for child in layer_collection.children:
                recursively_toggle_exclude(child, collection, exclude)

        for layer_collection in context.view_layer.layer_collection.children:
            recursively_toggle_exclude(layer_collection, collection, exclude)

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
        "Large":        {"- Squeeze": 0.3, "- Squish": 0.0,  "- Push-Up": 0.0,  "- Omoi": 0.0, "- Uranus Redux": 0.0, "- Sag": 0.0, "- Nip Nops": 0.0},
        "Omoi":         {"- Squeeze": 0.3, "- Squish": 0.0,  "- Push-Up": 0.0,  "- Omoi": 1.0, "- Uranus Redux": 0.0, "- Sag": 0.0, "- Nip Nops": 0.0},
        "Sugoi Omoi":   {"- Squeeze": 0.3, "- Squish": 0.0,  "- Push-Up": 0.0,  "- Omoi": 1.0, "- Uranus Redux": 0.0, "- Sag": 1.0, "- Nip Nops": 0.0},
        "Uranus":       {"- Squeeze": 0.0, "- Squish": 0.0,  "- Push-Up": 0.0,  "- Omoi": 0.0, "- Uranus Redux": 1.0, "- Sag": 0.0, "- Nip Nops": 0.0},
        "Lava Omoi":    {"- Squeeze": 0.0, "- Squish": 0.0,  "- Push-Up": 0.0,  "- Omoi": 0.0, "- Uranus Redux": 0.0, "- Sag": 0.0, "- Nip Nops": 0.0},
        
        "Medium":       {"-- Squeeze": 0.0, "-- Squish": 0.0,  "-- Push-Up": 0.0,  "-- Mini": 0.0, "-- Sayonara": 0.0, "-- Sag": 0.0, "-- Nip Nops": 0.0},
        "Sayonara":     {"-- Squeeze": 0.0, "-- Squish": 0.0,  "-- Push-Up": 0.0,  "-- Mini": 0.0, "-- Sayonara": 1.0, "-- Sag": 0.0, "-- Nip Nops": 0.0},
        "Tsukareta":    {"-- Squeeze": 0.0, "-- Squish": 0.0,  "-- Push-Up": 0.0,  "-- Mini": 0.0, "-- Sayonara": 0.0, "-- Sag": 0.6, "-- Nip Nops": 0.0},
        "Tsukareta+":   {"-- Squeeze": 0.0, "-- Squish": 0.0,  "-- Push-Up": 0.0,  "-- Mini": 0.0, "-- Sayonara": 0.0, "-- Sag": 1.0, "-- Nip Nops": 0.0},
        "Mini":         {"-- Squeeze": 0.0, "-- Squish": 0.0,  "-- Push-Up": 0.0,  "-- Mini": 1.0, "-- Sayonara": 0.0, "-- Sag": 0.0, "-- Nip Nops": 0.0},
        "Teardrop":     {"-- Squeeze": 0.0, "-- Squish": 0.0,  "-- Push-Up": 0.0,  "-- Mini": 0.0, "-- Sayonara": 0.0, "-- Sag": 0.0, "-- Nip Nops": 0.0},

        "Small":        {"--- Squeeze": 0.0,                                                                                "--- Nip Nops": 0.0},
        "Cupcake":      {"--- Squeeze": 0.0,  "--- Sugar": 0.0,                                                             "--- Nip Nops": 0.0},
        "Sugar":        {"--- Squeeze": 0.0,  "--- Sugar": 1.0,                                                             "--- Nip Nops": 0.0},

        "Flat":         {"---- Pecs": 0.0,                                                                                  "---- Nip Nops": 0.0},
        "Pecs":         {"---- Pecs": 1.0,                                                                                  "---- Nip Nops": 0.0}
        }
        return shape_presets[size]

class ApplyShapes(Operator):
    """This class is a mess"""

    bl_idname = "yakit.apply_shapes"
    bl_label = ""
    bl_description = "Applies the selected option"
    bl_options = {'UNDO'}
    
    key: StringProperty() # type: ignore
    target: StringProperty() # type: ignore
    preset: StringProperty() # type: ignore # shapes, chest_category, leg_size, gen, nails, other
    desc: StringProperty() # type: ignore # shapes, chest_category, leg_size, gen, nails, other

    @classmethod
    def description(cls, context, properties):
        if properties.desc in DevkitProps.ALL_SHAPES:
            return DevkitProps.ALL_SHAPES[properties.desc][3]
        else:
            return "Applies the selected option"
        
    def execute(self, context):
        self.props = get_devkit_props()
        apply_mq = self.get_mannequin_category()
        apply_target = "torso"

        if apply_mq:
            key_blocks = self.props.yam_mannequin.data.shape_keys.key_blocks
            apply_target = "mq"
        else:
            key_blocks = self.get_key_blocks() 

        self.get_function(key_blocks, apply_target)
        return {"FINISHED"}

    def get_key_blocks(self) -> ShapeKey:
        match self.target:  
            case "Legs":
                return self.props.yam_legs.data.shape_keys.key_blocks

            case "Hands":
                return self.props.yam_hands.data.shape_keys.key_blocks

            case "Feet":
                return self.props.yam_feet.data.shape_keys.key_blocks
            case _:
                return self.props.yam_torso.data.shape_keys.key_blocks

    def get_mannequin_category(self) -> bool:
        props = get_devkit_props()
        match self.target:   
            case "Legs":
                return props.shape_mq_legs_bool

            case "Hands" | "Feet":
                return props.shape_mq_other_bool
            
            case _:
                return props.shape_mq_chest_bool

    def get_function(self, key_blocks, apply_target:str) -> None:
        match self.preset:
            case "chest_category":
                ApplyShapes.mute_chest_shapes(key_blocks, self.key)

            case "leg_size":
                ApplyShapes.mute_leg_shapes(key_blocks, self.key)
            
            case "gen":
                ApplyShapes.mute_gen_shapes(key_blocks, self.key)

            case "nails":
                ApplyShapes.mute_nail_shapes(key_blocks, self.key)

            case "other":   
                if self.key == "Alt Hips" and self.target == "Legs" and not key_blocks["Mini"].mute:
                    self.report({"ERROR"}, "Mini not compatible with alternate hips!")
                    return {"CANCELLED"}
                if self.key == "Alt Hips" and self.target == "Legs" and not key_blocks["Lavabod"].mute:
                    self.report({"ERROR"}, "Lavabod not compatible with alternate hips!")
                    return {"CANCELLED"}
                if self.key == "Alt Hips" and self.target == "Legs" and not key_blocks["Masc"].mute:
                    self.report({"ERROR"}, "Masc not compatible with alternate hips!")
                    return {"CANCELLED"}
                if self.target == "Torso" and self.key == "Lavabod":
                    self.save_chest_sizes(key_blocks, apply_target)
                self.toggle_other(key_blocks, self.key)
            
            case _:
                size = self.props.chest_shape_enum
                lava_sizes = ["Lava Omoi", "Teardrop", "Cupcake", "Sugar"]
                
                if size in lava_sizes and key_blocks["Lavabod"].mute:
                    bpy.ops.yakit.apply_shapes(key="Lavabod", target="Torso", preset="other")
                elif size not in lava_sizes and not key_blocks["Lavabod"].mute:
                    bpy.ops.yakit.apply_shapes(key="Lavabod", target="Torso", preset="other")

                category = get_chest_category(size)
                shape_presets = get_shape_presets(size)

                ApplyShapes.apply_shape_values(key_blocks, shape_presets)
                ApplyShapes.mute_chest_shapes(key_blocks, category)
            
                self.force_update(apply_target)

    def apply_shape_values(key_blocks: Object, shape_presets:dict[str, float]) -> None:
        for key_name, value in shape_presets.items():
            key_blocks[key_name].value = value
            
    def reset_shape_values(key_blocks: Object, category) -> None:
        reset = get_shape_presets(category)
        for key_name, value in reset.items():
            key_blocks[key_name].value = value
                             
    def mute_chest_shapes(key_blocks, category) -> None:
        category_mute_mapping = {
            "Large": (True, True, True), 
            "Medium": (False, True, True), 
            "Small": (True, False, True),   
            "Masc": (True, True, False),   
        }

        # Gets category and its bools
        mute_medium, mute_small, mute_masc = category_mute_mapping.get(category, (True, True, True))

        # Apply the mute states to the target
        key_blocks["MEDIUM"].mute = mute_medium
        key_blocks["SMALL"].mute = mute_small
        key_blocks["MASC"].mute = mute_masc

        if category == "Masc" and not key_blocks["Lavabod"].mute:
            bpy.ops.yakit.apply_shapes(key="Lavabod", target="Torso", preset="other")

    def mute_gen_shapes(key_blocks, gen: str) -> None:
        gen_mute_mapping = {
            "Gen A": (True, True, True), 
            "Gen B": (False, True, True), 
            "Gen C": (True, False, True),   
            "Gen SFW": (True, True, False),   
        }
        # Gets category and its bools
        mute_b, mute_c, mute_sfw = gen_mute_mapping.get(gen, (True, True, True))

        # Apply the mute states to the target
        key_blocks["Gen B"].mute = mute_b
        key_blocks["Gen C"].mute = mute_c
        key_blocks["Gen SFW"].mute = mute_sfw

    def mute_leg_shapes(key_blocks, size: str) -> None:
        size_mute_mapping = {
            "Melon": (True, True, True, True, True), 
            "Skull": (False, True, True, True, True), 
            "Mini": (True, False, True, True, True),   
            "Lava": (True, True, False, True, True),   
            "Masc": (True, True, True, False, True),   
            "Yanilla": (True, True, True, True, False),   
        }

        # Gets category and its bools
        mute_skull, mute_mini, mute_lava, mute_masc, mute_yanilla= size_mute_mapping.get(size, (True, True, True, True, True))

        # Apply the mute states to the target
        key_blocks["Skull Crushers"].mute = mute_skull
        key_blocks["Mini"].mute = mute_mini
        key_blocks["Lavabod"].mute = mute_lava
        key_blocks["Masc"].mute = mute_masc
        key_blocks["Yanilla"].mute = mute_yanilla

        # if not mute_mini:
        #     key_blocks["Hip Dips (for YAB)"].mute = True
        #     key_blocks["Less Hip Dips (for Rue)"].mute = True

    def mute_nail_shapes(key_blocks, nails: str) -> None:
        nails_mute_mapping = {
            "Long": (True, True, True), 
            "Short": (False, True, True), 
            "Ballerina": (True, False, True), 
            "Stabbies": (True, True, False), 
             
        }
        # Gets category and its bools
        mute_short, mute_ballerina, mute_stabbies = nails_mute_mapping.get(nails, (True, True, True))

        # Apply the mute states to the target
        key_blocks["Short Nails"].mute = mute_short
        key_blocks["Ballerina"].mute = mute_ballerina
        key_blocks["Stabbies"].mute = mute_stabbies
    
    def toggle_other(self, key_blocks, key: str) -> None:
        if key_blocks[key].mute:
            if self.target == "Hands" and key == "Rue":
                key_blocks["Lavabod"].mute = True
            if self.target == "Hands" and key == "Lavabod":
                key_blocks["Rue"].mute = True
            if self.target == "Torso" and key == "Lavabod":
                key_blocks["MASC"].mute = True
            if self.target in ("Legs", "Mannequin") and key == "Squish":
                key_blocks["Squimsh"].mute = True
            if self.target in ("Legs", "Mannequin") and key == "Squimsh":
                key_blocks["Squish"].mute = True

            key_blocks[key].mute = False
        else:
            key_blocks[key].mute = True

    def save_chest_sizes(self, key_blocks, apply_target:str):
        apply_mq = self.get_mannequin_category()
        if key_blocks["Lavabod"].mute:
            index  = 1
            backup = 0
        else:
            index  = 0
            backup = 1

        if apply_mq:
            presets = DevkitProps.mq_floats
        else:
            presets = DevkitProps.torso_floats

        for key in key_blocks:
            key_name = key.name
        
            for category in ["Large", "Medium", "Small"]:
                if key_name in presets[backup][category]:
                    presets[backup][category][key_name] = round(key.value, 2)
                    break

        for size in presets[index].keys():
            preset = presets[index][size]
            ApplyShapes.apply_shape_values(key_blocks, preset)
        
        self.force_update(apply_target)
        
    def force_update(self, apply_target:str):
        if apply_target == "torso":
            try:
                bpy.context.view_layer.objects.active = self.props.yam_torso
            except:
                pass
        else:
            try:
                bpy.context.view_layer.objects.active = self.props.yam_mannequin
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

def link_tri_modifier():
    for obj in bpy.data.objects:
        tri_mod = [modifier for modifier in obj.modifiers if modifier.type == 'TRIANGULATE']
        for modifier in tri_mod:
            _add_tri_driver(modifier)

def _add_tri_driver(modifier:ShapeKey) -> None:
        modifier.driver_remove("show_viewport")
        driver = modifier.driver_add("show_viewport").driver

        driver.type = "AVERAGE"
        driver_var  = driver.variables.new()
        driver_var.name = "show_viewport"
        driver_var.type = "SINGLE_PROP"

        driver_var.targets[0].id_type   = "WINDOWMANAGER"
        driver_var.targets[0].id        = bpy.context.window_manager
        driver_var.targets[0].data_path = "ya_devkit_window.devkit_triangulation"
        
class TriangulateLink(Operator):
    bl_idname = "yakit.triangulate_link"
    bl_label = "Triangulate"
    bl_description = "Links all Triangulate modifiers to this toggle"

    def execute(self, context):
        link_tri_modifier()
        return {'FINISHED'}

class AssignControllers(Operator):
    bl_idname = "yakit.assign_controllers"
    bl_label = "Assign Controller Meshes"
    bl_description = "Automatically find and assign controller meshes"
    
    def execute(self, context):
        assign_controller_meshes()
        self.report({'INFO'}, "Controller meshes updated!")
        return {'FINISHED'}

class ResetQueue(Operator):
    bl_idname = "yakit.reset_queue"
    bl_label = "Export"
    bl_description = "Resets Export UI if it ran into an error"

    @classmethod
    def poll(cls, context):
        return hasattr(context.scene, "ya_file_props")

    def execute(self, context):
        bpy.context.scene.ya_file_props.export_total = 0
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
                get_window_props().overview_ui = self.overview
        return {'FINISHED'}

def get_conditional_icon(condition: bool, invert: bool=False, if_true: str="CHECKMARK", if_false: str="X"):
    if invert:
        return if_true if not condition else if_false
    else:
        return if_true if condition else if_false

def aligned_row(layout: UILayout, label: str, attr: str, prop=None, prop_str: str="", label_icon: str="NONE", attr_icon: str="NONE", factor:float=0.25, emboss: bool=True, alignment: str="RIGHT") -> UILayout:
    """
    Create a row with a label in the main split and a prop or text label in the second split. Returns the row if you want to append extra items.
    Args:
        label: Row name.
        prop: Prop referenced, if an object is not passed, the prop is just treated as a label with text
        container: Object that contains the necessary props.
        factor: Split row ratio.
        alignment: Right aligned by default.
    """
    row = layout.row(align=True)
    split = row.split(factor=factor, align=True)
    split.alignment = alignment
    split.label(text=label, icon=label_icon)

    if prop is None:
        row = split.row(align=True)
        row.label(text=attr)
    else:
        row = split.row(align=True)
        row.prop(prop, attr, text=prop_str, emboss=emboss, icon=attr_icon)
    
    return row

class Overview(Panel):
    bl_idname = "VIEW3D_PT_YA_Overview"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "XIV Kit"
    bl_label = "Devkit"
    bl_order = 0

    def draw(self, context):
        global devkit_registered
        layout = self.layout

        if not devkit_registered:
            row = layout.row(align=True)
            row.alignment = "CENTER"
            row.label(text="Devkit is setting up...", icon="INFO")
            return
        
        self.props  = get_devkit_props()
        self.window = get_window_props()

        self.mq    = self.props.yam_mannequin
        self.torso = self.props.yam_torso
        self.legs  = self.props.yam_legs
        self.hands = self.props.yam_hands
        self.feet  = self.props.yam_feet

        layout     = self.layout

        options ={
            "Body": "OUTLINER_OB_ARMATURE",
            "Shape Keys": "MESH_DATA",
            "Settings": "SETTINGS",
            "Info": "INFO",
            }

        box = layout.box()
        row = box.row(align=True)
        
        row.label(icon=options[self.window.overview_ui])
        row.label(text=f"  {self.window.overview_ui}")
        button_row = row.row(align=True)
        
        self.ui_category_buttons(button_row, "overview_ui", options, "overview")
        
        layout.separator(factor=1, type="LINE")

        # SHAPE MENUS
        
        if self.window.overview_ui == "Shape Keys":
            box = layout.box()

            obj = self.collection_context(context)
            if obj is None or not obj.data.shape_keys:
                row = box.row(align=True)
                row.label(text="Object has no shape keys:", icon="ERROR")
            else:
                key = obj.data.shape_keys
                row = box.row(align=True)
                row.label(text=f"{obj.name}:")
                text = "Collection" if self.window.button_dynamic_view else "Active"
                row.prop(self.window, "button_dynamic_view", text=text, icon="HIDE_OFF")
            
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
        
        if self.window.overview_ui == "Body":
            
            # CHEST

            button = self.window.button_chest_shapes
            chest_col = bpy.context.view_layer.layer_collection.children["Chest"].exclude

            box = layout.box()
            row = box.row(align=True)
            
            icon = 'TRIA_DOWN' if button else 'TRIA_RIGHT'
            row.prop(self.window, "button_chest_shapes", text="", icon=icon, emboss=False)
            row.label(text="Chest")
            
            button_row = row.row(align=True)
            icon = "HIDE_ON" if chest_col else "HIDE_OFF"
            chest_op = button_row.operator("yakit.apply_visibility", text="", icon=icon, depress=not chest_col)
            chest_op.target = "Chest"
            chest_op.key = ""
            button_row.prop(self.props, "shape_mq_chest_bool", text="", icon="ARMATURE_DATA")
            

            if button:
                self.chest_shapes(layout, self.mq, self.torso)

            # LEGS

            button = self.window.button_leg_shapes
            leg_col = bpy.context.view_layer.layer_collection.children["Legs"].exclude

            box = layout.box()
            row = box.row(align=True)
            
            icon = 'TRIA_DOWN' if button else 'TRIA_RIGHT'
            row.prop(self.window, "button_leg_shapes", text="", icon=icon, emboss=False)
            row.label(text="Legs")
            
            button_row = row.row(align=True)
            icon = "HIDE_ON" if leg_col else "HIDE_OFF"
            leg_op = button_row.operator("yakit.apply_visibility", text="", icon=icon, depress=not leg_col)
            leg_op.target = "Legs"
            leg_op.key = ""
            button_row.prop(self.props, "shape_mq_legs_bool", text="", icon="ARMATURE_DATA")

            if button:
                self.leg_shapes(layout, self.mq, self.legs)
            
            # OTHER

            button = self.window.button_other_shapes

            box = layout.box()
            row = box.row(align=True)
            icon = 'TRIA_DOWN' if button else 'TRIA_RIGHT'
            row.prop(self.window, "button_other_shapes", text="", icon=icon, emboss=False)
            row.label(text="Hands/Feet")
            
            button_row = row.row(align=True)
            button_row.prop(self.props, "shape_mq_other_bool", text="", icon="ARMATURE_DATA")

            if button:
                self.other_shapes(layout, self.mq, self.hands, self.feet)

        # YAS MENU
        if (self.window.overview_ui == "Body" or self.window.overview_ui == "Shape Keys"):
            button = self.window.button_yas_expand                          

            box = layout.box()
            row = box.row(align=True)
            row.alignment = 'LEFT'
            
            icon = 'TRIA_DOWN' if button else 'TRIA_RIGHT'
            row.prop(self.window, "button_yas_expand", text="", icon=icon, emboss=False)
            row.label(text="Yet Another Skeleton")

            if button:
                self.yas_menu(layout)

        # SETTINGS

        if self.window.overview_ui == "Settings":

            box = layout.box()
            col = box.column(align=True)
            row = col.row(align=True)
            row.alignment = "CENTER"
            row.label(text="Controller Meshes:")

            col.separator(factor=0.5, type="LINE")

            row = aligned_row(col, "Torso:", "yam_torso", self.props)
            row.label(text="", icon=get_conditional_icon(self.props.yam_torso, if_false="ERROR"))

            row = aligned_row(col, "Legs:", "yam_legs", self.props)
            row.label(text="", icon=get_conditional_icon(self.props.yam_legs, if_false="ERROR"))

            row = aligned_row(col, "Hands:", "yam_hands", self.props)
            row.label(text="", icon=get_conditional_icon(self.props.yam_hands, if_false="ERROR"))

            row = aligned_row(col, "Feet:", "yam_feet", self.props)
            row.label(text="", icon=get_conditional_icon(self.props.yam_feet, if_false="ERROR"))

            row = aligned_row(col, "Mannequin:", "yam_mannequin", self.props)
            row.label(text="", icon=get_conditional_icon(self.props.yam_mannequin, if_false="ERROR"))

            row = box.row(align=True)
            row.alignment = "CENTER"
            row.scale_x = 1.9
            row.operator("yakit.assign_controllers", text="Reassign")

            layout.separator(factor=1, type="LINE")

            row = layout.row(align=True)
            row.alignment = "CENTER"
            row.prop(self.window, "devkit_triangulation", text="Triangulation")
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

            layout.separator(factor=1, type="LINE")

        #INFO

        if self.window.overview_ui == "Info":
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

        if self.window.overview_ui == "Info" or self.window.overview_ui == "Settings":
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
                       
    def collection_context(self, context:Context) -> Object | None:
        # Links mesh name to the standard collections)
        body_part_collections = {
            "Torso": ['Chest', 'Nipple Piercings'],
            "Waist": ['Legs', 'Pubes'],
            "Hands": ['Hands', 'Nails', 'Practical Uses', 'Clawsies'],
            "Feet": ['Feet', 'Toenails', 'Toe Clawsies'] 
            }

        # Get the active object
        active_obj = bpy.context.active_object

        if active_obj and active_obj.data.shape_keys:
            if not self.window.button_dynamic_view:
                return active_obj
            else:
                active_collection = active_obj.users_collection
                for body_part, collections in body_part_collections.items():
                    if any(bpy.data.collections[coll_name] in active_collection for coll_name in collections):
                        return get_object_from_mesh(body_part) 
                return active_obj
        else:
            return None

    def chest_shapes(self, layout: UILayout, mq: Object, torso: Object):
        layout.separator(factor=0.1)  
        if self.props.shape_mq_chest_bool:
            target = mq
        else:
            target = torso

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
        operator.desc   = "Lava Omoi" if lava_depress else "Large"

        text = "Teardrop" if lava_depress else "Medium"
        operator = row.operator("yakit.apply_shapes", text= text, depress=medium_depress)
        operator.key = "Medium"
        operator.target = "Torso"
        operator.preset = "chest_category"
        operator.desc   = "Teardrop" if lava_depress else "Medium"

        text = "Cupcake" if lava_depress else "Small"
        operator = row.operator("yakit.apply_shapes", text= text, depress=small_depress)
        operator.key = "Small"
        operator.target = "Torso"
        operator.preset = "chest_category"
        operator.desc   = "Cupcake" if lava_depress else "Small"

        operator = row.operator("yakit.apply_shapes", text= "Masc", depress=masc_depress)
        operator.key = "Masc"
        operator.target = "Torso"
        operator.preset = "chest_category"
        operator.desc   = "Flat"

        row = layout.row(align=True)
        operator = row.operator("yakit.apply_shapes", text= "Buff", depress=buff_depress)
        operator.key = "Buff"
        operator.target = "Torso"
        operator.preset = "other"
        operator.desc   = "Buff"

        operator = row.operator("yakit.apply_shapes", text= "Rue", depress=rue_depress)
        operator.key = "Rue"
        operator.target = "Torso"
        operator.preset = "other"
        operator.desc   = "Rue"

        operator = row.operator("yakit.apply_shapes", text= "Lava", depress=lava_depress)
        operator.key = "Lavabod"
        operator.target = "Torso"
        operator.preset = "other"
        operator.desc   = "Lava"

        box = layout.box()
        row = box.row()
        
        if not small_mute and not medium_mute:
            row.alignment = "CENTER"
            row.label(text="Select a chest size.")
        else:
            split = row.split(factor=0.25)
            col = split.column(align=True)
            col.alignment = "RIGHT"
            col2 = split.column(align=True)

            skip      = {"-- Teardrop", "--- Cupcake"}
            lava_skip = ["Omoi", "Uranus", "Nops", "Mini", "Sayonara"]
            prefix_conditions = [
                (masc_depress,   "---- ", 5),
                (small_depress,  "--- ", 4),
                (medium_depress, "-- ", 3),
                (large_depress,  "- ", 2),
            ]

            name_idx = 0
            for key in target.data.shape_keys.key_blocks[1:]:
                for condition, prefix, idx in prefix_conditions:
                    if condition and key.name.startswith(prefix):
                        name_idx = idx
                        break
                else:
                    continue
                if lava_depress and any(skip in key.name for skip in lava_skip):
                    continue
                if not lava_depress and "Soft" in key.name:
                    continue
                if key.name in skip:
                    continue
    
                col.label(text=f"{key.name[name_idx:]}:")
                col2.prop(key, "value", text=f"{key.value*100:.0f}%")
     
        
        layout.separator(factor=0.1)

        row = layout.row()
        split = row.split(factor=0.25, align=True) 
        col = split.column(align=True)
        col.alignment = "RIGHT"
        col.label(text="Preset:")
        
        col2 = split.column(align=True)
        col2.prop(self.props, "chest_shape_enum")

        col3 = split.column(align=True)
        operator = col3.operator("yakit.apply_shapes", text= "Apply")
        operator.preset = "SHAPES"
        operator.target = "Chest"

        layout.separator(factor=0.1)

    def leg_shapes(self, layout: UILayout, mq: Object, legs: Object):
        layout.separator(factor=0.1)
        if self.props.shape_mq_legs_bool:
            target = mq
        else:
            target = legs

        skull_mute = target.data.shape_keys.key_blocks["Skull Crushers"].mute
        mini_mute = target.data.shape_keys.key_blocks["Mini"].mute
        rue_mute = target.data.shape_keys.key_blocks["Rue"].mute
        lava_mute = target.data.shape_keys.key_blocks["Lavabod"].mute
        masc_mute = target.data.shape_keys.key_blocks["Masc"].mute
        yanilla_mute = target.data.shape_keys.key_blocks["Yanilla"].mute

        genb_mute = target.data.shape_keys.key_blocks["Gen B"].mute
        genc_mute = target.data.shape_keys.key_blocks["Gen C"].mute
        gensfw_mute = target.data.shape_keys.key_blocks["Gen SFW"].mute

        small_mute = target.data.shape_keys.key_blocks["Small Butt"].mute
        soft_mute = target.data.shape_keys.key_blocks["Soft Butt"].mute

        hip_yab_mute = target.data.shape_keys.key_blocks["Hip Dips (for YAB)"].mute
        hip_rue_mute = target.data.shape_keys.key_blocks["Less Hip Dips (for Rue)"].mute

        squish_mute = target.data.shape_keys.key_blocks["Squish"].mute
        squimsh_mute = target.data.shape_keys.key_blocks["Squimsh"].mute

        melon_depress = True if skull_mute and mini_mute and lava_mute and masc_mute and yanilla_mute else False
        skull_depress = True if not skull_mute else False
        mini_depress = True if not mini_mute else False
        rue_depress = True if not rue_mute else False
        lava_depress = True if not lava_mute else False
        masc_depress = True if not masc_mute else False
        yanilla_depress = True if not yanilla_mute else False
        

        gena_depress = True if genb_mute and gensfw_mute and genc_mute else False
        genb_depress = True if not genb_mute else False
        genc_depress = True if not genc_mute else False
        gensfw_depress = True if not gensfw_mute else False

        small_depress = True if not small_mute else False
        soft_depress = True if not soft_mute else False
        hip_depress = True if not hip_yab_mute or not hip_rue_mute else False

        squish_depress = True if not squish_mute else False
        squimsh_depress = True if not squimsh_mute else False
        
        row = layout.row(align=True) 
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Genitalia:")
        button_row = split.row(align=True)

        operator = button_row.operator("yakit.apply_shapes", text= "A", depress=gena_depress)
        operator.key = "Gen A"
        operator.target = "Legs"
        operator.preset = "gen"
        operator.desc = "Gen A"

        operator = button_row.operator("yakit.apply_shapes", text= "B", depress=genb_depress)
        operator.key = "Gen B"
        operator.target = "Legs"
        operator.preset = "gen"
        operator.desc = "Gen B"

        operator = button_row.operator("yakit.apply_shapes", text= "C", depress=genc_depress)
        operator.key = "Gen C"
        operator.target = "Legs"
        operator.preset = "gen"
        operator.desc = "Gen C"

        operator = button_row.operator("yakit.apply_shapes", text= "SFW", depress=gensfw_depress)
        operator.key = "Gen SFW"
        operator.target = "Legs"
        operator.preset = "gen"
        operator.desc = "Gen SFW"
        
        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Leg sizes:")
        button_row = split.row(align=True)
        operator = button_row.operator("yakit.apply_shapes", text= "Melon", depress=melon_depress)
        operator.key = "Melon"
        operator.target = "Legs"
        operator.preset = "leg_size"
        operator.desc = "Melon"

        operator = button_row.operator("yakit.apply_shapes", text= "Skull", depress=skull_depress)
        operator.key = "Skull"
        operator.target = "Legs"
        operator.preset = "leg_size"
        operator.desc = "Skull"

        operator = button_row.operator("yakit.apply_shapes", text= "Yanilla", depress=yanilla_depress)
        operator.key = "Yanilla"
        operator.target = "Legs"
        operator.preset = "leg_size"
        operator.desc = "Yanilla"

        operator = button_row.operator("yakit.apply_shapes", text= "Lava", depress=lava_depress)
        operator.key = "Lava"
        operator.target = "Legs"
        operator.preset = "leg_size"
        operator.desc = "Lava Legs"

        operator = button_row.operator("yakit.apply_shapes", text= "Masc", depress=masc_depress)
        operator.key = "Masc"
        operator.target = "Legs"
        operator.preset = "leg_size"
        operator.desc = "Masc Legs"

        operator = button_row.operator("yakit.apply_shapes", text= "Mini", depress=mini_depress)
        operator.key = "Mini"
        operator.target = "Legs"
        operator.preset = "leg_size"
        operator.desc = "Mini Legs"

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Butt options:")
        button_row = split.row(align=True)
        operator = button_row.operator("yakit.apply_shapes", text= "Small", depress=small_depress)
        operator.key = "Small Butt"
        operator.target = "Legs"
        operator.preset = "other"
        operator.desc = "Small Butt"
        
        operator = button_row.operator("yakit.apply_shapes", text= "Soft", depress=soft_depress)
        operator.key = "Soft Butt"
        operator.target = "Legs"
        operator.preset = "other"
        operator.desc = "Soft Butt"

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Squish:")
        button_row = split.row(align=True)
        operator = button_row.operator("yakit.apply_shapes", text= "Squish", depress=squish_depress)
        operator.key = "Squish"
        operator.target = "Legs"
        operator.preset = "other"
        operator.desc = "Squish"
        
        operator = button_row.operator("yakit.apply_shapes", text= "Squimsh", depress=squimsh_depress)
        operator.key = "Squimsh"
        operator.target = "Legs"
        operator.preset = "other"
        operator.desc = "Squimsh"

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        operator = split.operator("yakit.apply_shapes", text= "Alt Hips", depress=hip_depress)
        operator.key = "Alt Hips"
        operator.target = "Legs"
        operator.preset = "other"
        operator.desc = "Hip Dips"

        button_row = split.row(align=True)
        operator = button_row.operator("yakit.apply_shapes", text= "Rue", depress=rue_depress)
        operator.key = "Rue"
        operator.target = "Legs"
        operator.preset = "other"
        operator.desc = "Rue Legs"
        
        layout.separator(factor=0.1)

    def yas_menu(self, layout: UILayout):
        layout.separator(factor=0.1)
 
    def other_shapes(self, layout: UILayout, mq: Object, hands: Object, feet: Object):
        if self.props.shape_mq_other_bool:
            target = mq
            target_f = mq
        else:
            target = hands
            target_f = feet
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
        if not self.props.shape_mq_other_bool:
            icon = "HIDE_ON" if hands_col else "HIDE_OFF"
            hands_op = button_row.operator("yakit.apply_visibility", text="", icon=icon, depress=not hands_col)
            hands_op.target = "Hands"
            hands_op.key = ""

        operator = button_row.operator("yakit.apply_shapes", text= "Rue", depress=rue_depress)
        operator.key = "Rue"
        operator.target = "Hands"
        operator.preset = "other"
        operator.desc = "Rue Hands"

        operator = button_row.operator("yakit.apply_shapes", text= "Lava", depress=lava_depress)
        operator.key = "Lavabod"
        operator.target = "Hands"
        operator.preset = "other"
        operator.desc = "Lava Hands"

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Nails:")
        button_row = split.row(align=True)
        if not self.props.shape_mq_other_bool:
            icon = "HIDE_ON" if nails_col else "HIDE_OFF"
            operator = button_row.operator("yakit.apply_visibility", text="", icon=icon, depress=not nails_col)
            operator.key = "Nails"
            operator.target = "Hands"

        operator = button_row.operator("yakit.apply_shapes", text= "Long", depress=long_depress)
        operator.key = "Long"
        operator.target = "Hands"
        operator.preset = "nails"
        operator.desc = "Long"
        
        operator = button_row.operator("yakit.apply_shapes", text= "Short", depress=short_depress)
        operator.key = "Short"
        operator.target = "Hands"
        operator.preset = "nails"
        operator.desc = "Short"

        operator = button_row.operator("yakit.apply_shapes", text= "Ballerina", depress=ballerina_depress)
        operator.key = "Ballerina"
        operator.target = "Hands"
        operator.preset = "nails"
        operator.desc = "Ballerina"

        operator = button_row.operator("yakit.apply_shapes", text= "Stabbies", depress=stabbies_depress)
        operator.key = "Stabbies"
        operator.target = "Hands"
        operator.preset = "nails"
        operator.desc = "Stabbies"

        if not self.props.shape_mq_other_bool:
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
            operator.desc = "Straight"

            operator = button_row.operator("yakit.apply_shapes", text= "Curved", depress=not clawsies_depress)
            operator.key = "Curved"
            operator.target = "Hands"
            operator.preset = "other"
            operator.desc = "Curved"
    
        layout.separator(type="LINE")

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Feet:")
        button_row = split.row(align=True)
        if not self.props.shape_mq_other_bool:
            icon = "HIDE_ON" if feet_col else "HIDE_OFF"
            feet_op = button_row.operator("yakit.apply_visibility", text="", icon=icon, depress=not feet_col)
            feet_op.target = "Feet"
            feet_op.key = ""

        operator = button_row.operator("yakit.apply_shapes", text= "Rue", depress=rue_f_depress)
        operator.key = "Rue"
        operator.target = "Feet"
        operator.preset = "other"
        operator.desc = "Rue Feet"

        if not self.props.shape_mq_other_bool:
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

        feet_keys = target_f.data.shape_keys.key_blocks
        box = layout.box()
        row = box.row(align=True)
        split = row.split(factor=0.25)
        col = split.column(align=True)
        col.alignment = "RIGHT"
        col.label(text="Heels:")
        col.label(text="Cinderella:")
        col.label(text="Mini Heels:")
        
        col2 = split.column(align=True)
        col2.prop(feet_keys["Heels"], "value", text=f"{feet_keys['Heels'].value*100:.0f}%")
        col2.prop(feet_keys["Cinderella"], "value", text=f"{feet_keys['Cinderella'].value*100:.0f}%")
        col2.prop(feet_keys["Mini Heels"], "value", text=f"{feet_keys['Mini Heels'].value*100:.0f}%")


        layout.separator(factor=0.1)
   
    def ui_category_buttons(self, layout:UILayout, prop, options, panel:str):
        row = layout
        ui_selector = getattr(self.window, prop)

        for slot, icon in options.items():
            depress = True if ui_selector == slot else False
            operator = row.operator("yakit.set_ui", text="", icon=icon, depress=depress)
            operator.overview = slot
            operator.panel = panel

CLASSES = [
    CollectionState,
    ObjectState,
    DevkitWindowProps,
    DevkitProps,
    CollectionManager,
    ApplyShapes,
    ApplyVisibility,
    TriangulateLink,
    AssignControllers,
    ResetQueue,
    PanelCategory,
    Overview
]


def delayed_setup(dummy=None) -> None:
    global devkit_registered  
    if devkit_registered:
        return None
    context = bpy.context
    link_tri_modifier()
    assign_controller_meshes()
    DevkitWindowProps.shpk_bools()

    try:
        area = [area for area in context.screen.areas if area.type == 'VIEW_3D'][0]
        view3d = [space for space in area.spaces if space.type == 'VIEW_3D'][0]

        with context.temp_override(area=area, space=view3d):
            view3d.show_region_ui = True
            region = [region for region in area.regions if region.type == 'UI'][0]
            region.active_panel_category = 'XIV Kit'
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
        del bpy.types.Scene.ya_devkit_props
    except:
        pass
    try:
        del bpy.types.WindowManager.ya_devkit_window
    except:
        pass
    
    bpy.app.handlers.load_post.remove(delayed_setup)
    bpy.app.handlers.load_pre.remove(cleanup_props)
    devkit_registered = False

def get_devkit_props() -> DevkitProps:
    return bpy.context.scene.ya_devkit_props

def get_window_props() -> DevkitWindowProps:
    return bpy.context.window_manager.ya_devkit_window

def set_devkit_properties() -> None:
    bpy.types.Scene.ya_devkit_props = PointerProperty(
        type=DevkitProps)
    
    bpy.types.WindowManager.ya_devkit_window = PointerProperty(
        type=DevkitWindowProps)
    
    bpy.types.Scene.ya_devkit_ver = (0, 15, 0)

    DevkitWindowProps.ui_buttons()
    DevkitWindowProps.export_bools()
 
def register() -> None:

    for cls in CLASSES:
        bpy.utils.register_class(cls)
        if cls == DevkitProps:
            set_devkit_properties()

    bpy.app.timers.register(delayed_setup, first_interval=1)
    bpy.app.handlers.load_post.append(delayed_setup)
    bpy.app.handlers.load_post.append(cleanup_props)

def unregister() -> None:
    global devkit_registered  
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except:
            continue
    
    try:
        del bpy.types.Scene.ya_devkit_props
    except:
        pass

    try:
        del bpy.types.WindowManager.ya_devkit_window
    except:
        pass

    try:
        del bpy.types.Scene.ya_devkit_ver
    except:
        pass
    
    bpy.app.handlers.load_post.remove(delayed_setup)
    bpy.app.handlers.load_pre.remove(cleanup_props)
    devkit_registered = False

if __name__ == "__main__":
    register()