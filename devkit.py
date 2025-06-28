import bpy   

from typing           import TYPE_CHECKING, Iterable
from bpy.props        import StringProperty, EnumProperty, BoolProperty, PointerProperty, FloatProperty, CollectionProperty
from bpy.types        import Operator, Panel, PropertyGroup, Object, Mesh, Context, UILayout, ShapeKey, Collection, LayerCollection, Driver, Key
from bpy.app.handlers import persistent

devkit_registered = False

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

def get_object_from_mesh(mesh_name: str) -> Object | None:
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

def create_scene_driver(target: Driver, prop: str, path_vars: list[tuple[str, str]], expression: str):
    try:
        target.driver_remove(prop)
    except:
        pass
    
    driver = target.driver_add(prop).driver
    driver.type = 'SCRIPTED' 
    driver.expression = expression
    
    # Add variable for the control property
    for var_name, data_path in path_vars:
        var = driver.variables.new()
        var.name = var_name
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = 'SCENE'
        var.targets[0].id = bpy.context.scene
        var.targets[0].data_path = data_path

def create_key_link_driver(target: Driver, source: Key, prop: str, data_path: str):
    try:
        target.driver_remove(prop)
    except:
        pass
    
    driver = target.driver_add(prop).driver
    driver.type = 'AVERAGE' 
    
    var = driver.variables.new()
    var.name = prop
    var.type = 'SINGLE_PROP'
    var.targets[0].id_type = 'KEY'
    var.targets[0].id = source
    var.targets[0].data_path = data_path

class AssignControllers(Operator):
    bl_idname = "yakit.assign_controllers"
    bl_label = "Assign Controller Meshes"
    bl_description = "Automatically find and assign controller meshes"
    
    def execute(self, context):
        assign_controller_meshes()
        self.report({'INFO'}, "Controller meshes updated!")
        return {'FINISHED'}

class ModelDrivers():

    def __init__(self):
        self.props = get_devkit_props()
        self.data_path = "ya_devkit_props"

        self.torso_drivers()
        self.torso_drivers(mq=True)

        self.leg_drivers()
        self.leg_drivers(mq=True)

        self.hand_drivers()
        self.hand_drivers(mq=True)

        self.feet_drivers()
        self.feet_drivers(mq=True)

    def torso_drivers(self, mq=False) -> None:
        if mq:
            obj     = self.props.yam_mannequin
            obj_str = 'mannequin_state'
        else:
            obj     = self.props.yam_torso
            obj_str = "torso_state"

        target_keys = obj.data.shape_keys.key_blocks
        chest_path  = self._get_data_path(obj_str, "chest_size")
        lava_path   = self._get_data_path(obj_str, "lavabod")

        chest_keys = {
            "LARGE":  0,
            "MEDIUM": 1, 
            "SMALL":  2,
            "MASC":   3
        }
        option_keys = ["Buff", "Rue", "Lavabod"]
        lava_keys   = ["- Soft Nips", "-- Soft Nips", "-- Teardrop", "--- Soft Nips", "--- Cupcake"]
        lava_skip   = ["Omoi", "Uranus", "Nops", "Mini", "Sayonara"]

        var_paths  = [("size", chest_path)]

        for size, value in chest_keys.items():
            expression = f"size == {value}"
            if size in ("SMALL", "MEDIUM"):
                expression = f"size == {value} and lava == 0"
                var_paths.append(("lava", lava_path))

            target = target_keys[size]
            create_scene_driver(
                target, 
                'value', 
                var_paths,
                expression)

            for sub_key in target_keys:
                if not sub_key.name.startswith("-" * (value + 1)):
                    continue

                sub_var_paths = [("size", chest_path)]
                if any(skip in sub_key.name for skip in lava_skip):
                    expression = f"size != {value} or lava == 1"
                    sub_var_paths.append(("lava", lava_path))
                else:
                    expression = f"size != {value}"

                create_scene_driver(
                    sub_key, 
                    'mute', 
                    sub_var_paths, 
                    expression)

        for key in option_keys:
            target = target_keys[key]
            expression = f"option == 1"
            create_scene_driver(
                target, 
                'value', 
                [("option", self._get_data_path(obj_str, key.lower()))], 
                expression)

        for key in lava_keys:
            count = key.count("-")
            if key in ("-- Teardrop", "--- Cupcake"):
                prop = 'value'
                expression = f"lava == 1 and size == {count - 1}"
            else:
                prop = 'mute'
                expression = f"lava == 0 and size != {count - 1}"
            target = target_keys[key]
            
            create_scene_driver(
                target, 
                prop, 
                [("lava", lava_path), 
                ("size", chest_path)], 
                expression
                )
            
            create_scene_driver(
                target_keys["Rue/Buff"],
                'value',
                [("buff", self._get_data_path(obj_str, "buff")), 
                ("rue", self._get_data_path(obj_str, "rue"))],
                "buff == 1 and rue == 1"
            )

            create_scene_driver(
                target_keys["Rue/Lava"],
                'value',
                [("lava", lava_path), 
                ("rue", self._get_data_path(obj_str, "rue"))],
                "lava == 1 and rue == 1"
            )

    def leg_drivers(self, mq=False) -> None:
        if mq:
            obj      = self.props.yam_mannequin
            obj_str  = 'mannequin_state'
            base_key = "LARGE"
            lava_key = "Lava Legs"
        else:
            obj      = self.props.yam_legs
            obj_str  = "leg_state"
            base_key = "Gen A/Watermelon Crushers"
            lava_key = "Lavabod"

        target_keys = obj.data.shape_keys.key_blocks
        legs_path   = self._get_data_path(obj_str, "leg_size")
        gen_path    = self._get_data_path(obj_str, "gen")
        hip_path    = self._get_data_path(obj_str, "alt_hips")
        rue_path    = self._get_data_path(obj_str, "rue")

        gen_keys = {
            0: base_key, 
            1: "Gen B", 
            2: "Gen C", 
            3: "Gen SFW",
        }

        for value, key in gen_keys.items():
            target = target_keys[key]
            expression = f"gen == {value}"

            create_scene_driver(
                target,
                'value',
                [("gen", gen_path)],
                expression
                )
        
        leg_keys = {
            0: base_key, 
            1: "Skull Crushers", 
            2: "Yanilla",
            3: "Masc", 
            4: lava_key,
            5: "Mini", 
        }

        for value, key in leg_keys.items():
            if key == "Lavabod" and mq:
                continue
            target = target_keys[key]
            expression = f"legs == {value}"

            create_scene_driver(
                target,
                'value',
                [("legs", legs_path)],
                expression
                )
            
        option_keys = ["Rue", "Small Butt", "Soft Butt", "Alt Hips"]
        for key in option_keys:
            if key == "Rue" and mq:
                continue
            target = target_keys[key]
            var = key.lower().replace(" ", "_")
            expression = f"{var} == 1"

            create_scene_driver(
                target,
                'value',
                [(var, self._get_data_path(obj_str, var))],
                expression
                )
        
        squish_keys = {
            0: base_key,  
            1: "Squish", 
            2: "Squimsh", 
        }

        for value, key in squish_keys.items():
            target = target_keys[key]
            expression = f"squish == {value}"

            create_scene_driver(
                target,
                'value',
                [("squish", self._get_data_path(obj_str, "squish"))],
                expression
            )

        create_scene_driver(
            target_keys["Hip Dips (for YAB)"],
            'value',
            [("legs", legs_path), 
            ("alt_hips", hip_path),
            ("rue", rue_path)],
            "legs <= 2 and alt_hips == 1 and rue == 0"
            )
        
        create_scene_driver(
            target_keys["Less Hip Dips (for Rue)"],
            'value',
            [("legs", legs_path), 
            ("alt_hips", hip_path),
            ("rue", rue_path)],
            "legs <= 2 and alt_hips == 1 and rue == 1"
            )
        
        create_scene_driver(
            target_keys["Rue/Mini"],
            'value',
            [("legs", legs_path), 
            ("rue", rue_path)],
            "legs == 5 and rue == 1"
            )
        
        if mq:
            create_scene_driver(
                target_keys["Rue/Lava Legs"],
                'value',
                [("legs", legs_path), 
                ("rue", rue_path)],
                "legs == 4 and rue == 1"
                )
        
        create_scene_driver(
            target_keys["Rue/Lava"],
            'value',
            [("lavabod", self._get_data_path(obj_str, "lavabod")), 
            ("rue", rue_path)],
            "lavabod == 1 and rue == 1"
            )

    def hand_drivers(self, mq=False) -> None:
        if mq:
            obj      = self.props.yam_mannequin
            obj_str  = 'mannequin_state'
            base_key = "LARGE"
            rue_key  = "Rue Hands"
        else:
            obj      = self.props.yam_hands
            obj_str  = 'hand_state'
            base_key = "NAILS"
            rue_key  = "Rue"

        target_keys = obj.data.shape_keys.key_blocks
        nail_path  = self._get_data_path(obj_str, "nails")
        body_path  = self._get_data_path(obj_str, "hand_size")

        nail_keys = {
            base_key: 0, 
            "Short Nails": 1, 
            "Ballerina": 2, 
            "Stabbies": 3,
        }

        for key, value in nail_keys.items():
            target = target_keys[key]
            expression = f"nails == {value}"

            create_scene_driver(
                target,
                'value',
                [("nails", nail_path)],
                expression
                )
            
        lava_key = "Lava Hands" if mq else "Lavabod"
        body_keys = {
            base_key: 0, 
            rue_key: 1, 
            lava_key: 2, 
        }

        for key, value in body_keys.items():
            target = target_keys[key]
            expression = f"hand_size == {value}"

            create_scene_driver(
                target_keys[key],
                'value',
                [("hand_size", body_path)],
                expression
                    )
        
        if not mq:
            body_keys = {
            base_key: 0, 
            "Curved": 1, 
        }

            for key, value in body_keys.items():
                target = target_keys[key]
                expression = f"clawsies == {value}"

                create_scene_driver(
                    target_keys[key],
                    'value',
                    [("clawsies", body_path)],
                    expression
                    )

    def feet_drivers(self, mq=False) -> None:
        if mq:
            obj      = self.props.yam_mannequin
            obj_str  = 'mannequin_state'
            rue_key  = "Rue Feet"
        else:
            obj      = self.props.yam_feet
            obj_str  = 'feet_state'
            rue_key  = "Rue"

        target_keys = obj.data.shape_keys.key_blocks
        rue_path    = self._get_data_path(obj_str, 'rue_feet')

        create_scene_driver(
            target_keys[rue_key],
            'value',
            [('rue_feet', rue_path)],
            "rue_feet == 1"
        )
        
        create_scene_driver(
                target_keys["Rue/Cinderella"],
                'mute',
                [("rue", rue_path)],
                "rue != 1"
            )

        create_key_link_driver(
            target_keys["Rue/Cinderella"],
            obj.data.shape_keys,
            'value',
            'key_blocks["Cinderella"].value'
        )
               
    def _get_data_path(self, obj_str: str, prop: str) -> str:
        return f"{self.data_path}.{obj_str}.{prop}"
    

class EnabledCollection(PropertyGroup):
    name: StringProperty() # type: ignore
    
    if TYPE_CHECKING:
        name: str

class CollectionState(PropertyGroup):

    def update_skeleton(self, context: Context):
        context.view_layer.layer_collection.children["Skeleton"].exclude = not self.skeleton
    
    def update_chest(self, context: Context):
        context.view_layer.layer_collection.children["Chest"].exclude = not self.chest
    
    def update_nipple_piercings(self, context: Context):
        context.view_layer.layer_collection.children["Chest"].children["Nipple Piercings"].exclude = not self.nipple_piercings
    
    def update_legs(self, context: Context):
        context.view_layer.layer_collection.children["Legs"].exclude = not self.legs

    def update_pubes(self, context: Context):
        context.view_layer.layer_collection.children["Legs"].children["Pubes"].exclude = not self.pubes
    
    def update_nails(self, context: Context):
        context.view_layer.layer_collection.children["Hands"].children["Nails"].exclude = not self.nails
    
    def update_clawsies(self, context: Context):
        context.view_layer.layer_collection.children["Hands"].children["Clawsies"].exclude = not self.clawsies
    
    def update_practical(self, context: Context):
        context.view_layer.layer_collection.children["Hands"].children["Nails"].children["Practical Uses"].exclude = not self.practical
    
    def update_feet(self, context: Context):
        context.view_layer.layer_collection.children["Feet"].exclude = not self.feet
    
    def update_mannequin(self, context: Context):
        context.view_layer.layer_collection.children["Mannequin"].exclude = not self.mannequin
    
    def update_export(self, context: Context):
        resources    = context.view_layer.layer_collection.children["Resources"]
        data_sources = resources.children["Data Sources"]

        # Order matters for consistency
        if self.export:
            resources.hide_viewport = self.export
            resources.exclude       = not self.export
            data_sources.exclude    = not self.export

            data_sources.children["UV/Weights"].exclude                      = not self.export
            data_sources.children["UV/Weights"].children["Rue"].exclude      = not self.export
            data_sources.children["UV/Weights"].children["Nail UVs"].exclude = not self.export
        else:
            data_sources.children["UV/Weights"].children["Nail UVs"].exclude = not self.export
            data_sources.children["UV/Weights"].children["Rue"].exclude      = not self.export
            data_sources.children["UV/Weights"].exclude                      = not self.export
            
            data_sources.exclude    = not self.export
            resources.exclude       = not self.export
            resources.hide_viewport = self.export

    def update_toe_clawsies(self, context: Context):
        context.view_layer.layer_collection.children["Feet"].children["Toe Clawsies"].exclude = not self.toe_clawsies
    
    def update_toenails(self, context: Context):
        context.view_layer.layer_collection.children["Feet"].children["Toenails"].exclude = not self.toenails
    
    def update_hands(self, context: Context):
        if not self.hands:
            self.nails    = False
            self.clawsies = False
            context.view_layer.layer_collection.children["Hands"].children["Clawsies"].exclude = True
            context.view_layer.layer_collection.children["Hands"].children["Nails"].exclude = True
        else:
            self.nails = True

        context.view_layer.layer_collection.children["Hands"].exclude = not self.hands


    skeleton: BoolProperty(
        name="",
        description="Skeletons reside here",
        default=True,
        update=update_skeleton
    ) # type: ignore

    chest: BoolProperty(
        name="",
        description="bob",
        default=True,
        update=update_chest
    ) # type: ignore

    nipple_piercings: BoolProperty(
        name="",
        description="Ouchies",
        default=False,
        update=update_nipple_piercings
    ) # type: ignore

    legs: BoolProperty(
        name="",
        description="Leggies",
        default=False,
        update=update_legs
    ) # type: ignore
    
    pubes: BoolProperty(
        name="",
        description="pubs",
        default=False,
        update=update_pubes
    ) # type: ignore

    hands: BoolProperty(
        name="",
        description="jazz",
        default=False,
        update=lambda self, context: self.update_hands(context)
    ) # type: ignore

    nails: BoolProperty(
        name="",
        description="stabbies",
        default=False,
        update=update_nails
    ) # type: ignore

    clawsies: BoolProperty(
        name="",
        description="most stabbies",
        default=False,
        update=update_clawsies
    ) # type: ignore

    practical: BoolProperty(
        name="",
        description="stabbies",
        default=False,
        update=update_practical
    ) # type: ignore

    feet: BoolProperty(
        name="",
        description="toesies",
        default=False,
        update=update_feet
    ) # type: ignore

    toenails: BoolProperty(
        name="",
        description="just nails",
        default=False,
        update=update_toenails
    ) # type: ignore

    toe_clawsies: BoolProperty(
        name="",
        description="more clawsies",
        default=False,
        update=update_toe_clawsies
    ) # type: ignore

    mannequin: BoolProperty(
        name="",
        description="toesies",
        default=False,
        update=update_mannequin
    ) # type: ignore

    export: BoolProperty(
        name="",
        description="when you need to get the files out",
        default=False,
        update=update_export
    ) # type: ignore

    if TYPE_CHECKING:
        skeleton        : bool
        chest           : bool
        nipple_piercings: bool
        legs            : bool
        pubes           : bool
        hands           : bool
        nails           : bool
        clawsies        : bool
        practical       : bool
        feet            : bool
        toenails        : bool
        toe_clawsies    : bool
        mannequin       : bool
        export          : bool


class SubKeyValues(PropertyGroup):
    name: StringProperty() # type: ignore
    value: FloatProperty(default=0.0) # type: ignore

    if TYPE_CHECKING:
        name : str
        value: float

class TorsoState(PropertyGroup):

    MANNEQUIN: BoolProperty(
        name="Mannequin",
        default=False,
        options={'HIDDEN', 'SKIP_SAVE'}  
    ) # type: ignore
    
    def _masc_lavabod(self, context) -> None:
        if self.lavabod and self.chest_size == "3":
            self.lavabod = False
    
    def _save_sub_keys(self, context) -> None:
        if self.lavabod and self.chest_size == "3":
            self.chest_size = "2"

        sizes = {}
        if self.MANNEQUIN:
            key_blocks = get_devkit_props().yam_mannequin.data.shape_keys.key_blocks
        else:
            key_blocks = get_devkit_props().yam_torso.data.shape_keys.key_blocks

        if self.lavabod:
            stored_keys = self.lava_keys
            new_values  = self.yab_keys
        else:
            stored_keys = self.yab_keys
            new_values  = self.lava_keys

        if stored_keys:
            for key in stored_keys:
                sizes[key.name] = key.value

        new_values.clear()
        for key in key_blocks:
            if not key.name.startswith("-"):
                continue
            count = key.name[:4].count("-")
            if count == 4:
                continue
            
            new = new_values.add()
            new.name = key.name
            new.value = key.value

            if key.name in sizes:
                # print(key.value)
                key.value = sizes[key.name]
                # print(key.value)

        if self.lavabod and not sizes:
            key_blocks["- Squeeze"].value = 0.0

    chest_size: EnumProperty(
        name="",
        description="Choose a chest size",
        default="0",
        items=[
            ("0", "Large", "Standard Large"),
            ("1", "Medium", "Standard Medium"),
            ("2", "Small", "Standard Small"),
            ("3", "Masc", "Yet Another Masc"),
        ],
        update=_masc_lavabod
        ) # type: ignore

    buff: BoolProperty(
        name="",
        description="Adds muscle",
        default=False,
    ) # type: ignore

    rue: BoolProperty(
        name="",
        description="Adds tummy",
        default=False,
    ) # type: ignore

    lavabod: BoolProperty(
        name="",
        description="Lavabod",
        default=False,
        update=_save_sub_keys
    ) # type: ignore
    
    yab_keys: CollectionProperty(type=SubKeyValues) # type: ignore

    lava_keys: CollectionProperty(type=SubKeyValues) # type: ignore

    if TYPE_CHECKING:
        sizes  : str
        buff   : bool
        rue    : bool
        lavabod: bool

        yab_keys : Iterable[SubKeyValues]
        lava_keys: Iterable[SubKeyValues]

class LegState(PropertyGroup):

    def _no_hips_dips(self, context) -> None:
        if int(self.leg_size) > 2 and self.alt_hips:
            self.alt_hips = False
    
    def _change_legs(self, context) -> None:
        if self.alt_hips and int(self.leg_size) > 2:
            self.leg_size = "0"

    gen: EnumProperty(
        name="",
        description="Choose a genitalia type",
        default="0",
        items=[
            ("0", "Gen A", "Labia majora"),
            ("1", "Gen B", "Visible labia minora"),
            ("2", "Gen C", "Open vagina"),
            ("3", "Gen SFW", "Barbie doll"),
        ]
        ) # type: ignore
    
    leg_size: EnumProperty(
        name="",
        description="Choose a leg size",
        default="0",
        items=[
            ("0", "Melon", "For crushing melons"),
            ("1", "Skull", "For crushing skulls"),
            ("2", "Yanilla", "As Yoshi-P intended"),
            ("3", "Masc", "Yet Another Masc"),
            ("4", "Lavabod", "Bigger hips, butt and hip dips"),
            ("5", "Mini", "Smaller legs"),
        ],
        update=_no_hips_dips
        ) # type: ignore
    
    rue: BoolProperty(
        name="",
        description="Adds tummy",
        default=False,
    ) # type: ignore

    small_butt: BoolProperty(
        name="",
        description="Not actually small, except when it is",
        default=False,
    ) # type: ignore

    soft_butt: BoolProperty(
        name="",
        description="Less perky butt",
        default=False,
    ) # type: ignore

    alt_hips: BoolProperty(
        name="",
        description="Removes hip dips on Rue, adds them on YAB",
        default=False,
        update=_change_legs 
    ) # type: ignore

    squish: EnumProperty(
        name="",
        description="Constrict your thighs",
        default="0",
        items=[
            ("0", "None", "No squish"),
            ("1", "Squish", "Thick band"),
            ("2", "Squimsh", "Thin band"),
        ]
        ) # type: ignore
    
    if TYPE_CHECKING:
        gen       : str
        leg_size  : str
        rue       : bool
        small_butt: bool
        soft_butt : bool
        alt_hips  : bool
        squish    : str

class HandState(PropertyGroup):

    nails: EnumProperty(
        name="",
        description="Choose a nail type",
        default="0",
        items=[
            ("0", "Long", "They're long"),
            ("1", "Short", "They're short"),
            ("2", "Ballerina", "Some think they look like shoes"),
            ("3", "Stabbies", "You can stab someone's eyes with these"),
        ]
        ) # type: ignore
    
    hand_size: EnumProperty(
        name="",
        description="Choose a body",
        default="0",
        items=[
            ("0", "YAB", "YAB hands"),
            ("1", "Rue", "Rue hands"),
            ("3", "Lavabod", "Lava hands"),
        ]
        ) # type: ignore

    clawsies: EnumProperty(
        name="",
        description="Choose a clawsies type",
        default="0",
        items=[
            ("0", "Straight", "When you want to murder instead"),
            ("1", "Curved", "Less straight murdering"),
        ]
        ) # type: ignore

    if TYPE_CHECKING:
        nails    : str
        hand_size: str
        clawsies : bool

class FeetState(PropertyGroup):

    rue_feet: BoolProperty(
        name="",
        description="Rue feetsies",
        default=False,
    ) # type: ignore

    if TYPE_CHECKING:
        rue_feet: bool

class MannequinState(TorsoState, LegState, HandState, FeetState):

    MANNEQUIN: BoolProperty(
        name="Mannequin",
        default=True,
        options={'HIDDEN', 'SKIP_SAVE'}
    ) # type: ignore
    pass
    

class DevkitWindowProps(PropertyGroup):
    overview_ui: EnumProperty(
        name= "",
        description= "Select an overview",
        items= [
            ("Body", "Shape", "Body Overview", "OUTLINER_OB_ARMATURE", 0),
            ("Shape Keys", "View", "Shape Key Overview", "MESH_DATA", 1),
            ("Settings", "Settings", "Devkit Settings", "SETTINGS", 2),
            ("Info", "Info", "Useful info", "INFO", 3),
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

def get_shape_presets(size: str) -> dict[str, float]:
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
    
    mesh_list = [
        "Torso",
        "Waist",
        "Hands",
        "Feet",
        "Mannequin",
    ]

    collection_state: PointerProperty(type=CollectionState) # type: ignore

    torso_state: PointerProperty(type=TorsoState) # type: ignore

    leg_state: PointerProperty(type=LegState) # type: ignore

    hand_state: PointerProperty(type=HandState) # type: ignore

    feet_state: PointerProperty(type=FeetState) # type: ignore

    mannequin_state: PointerProperty(type=MannequinState) # type: ignore

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

    def _get_listable_shapes(self, context) -> list:
        items = []

        for shape, (name, slot, shape_category, description, body, key) in self.ALL_SHAPES.items():
            if slot.lower() == "chest" and description != "" and shape_category !="":
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

    def _apply_preset(self, context) -> None:
        size       = self.chest_shape_enum
        preset     = get_shape_presets(size)
        lava_sizes = ("Lava Omoi", "Teardrop", "Cupcake", "Sugar")
        category   = self.ALL_SHAPES[size][2]

        category_to_enum = {
            "Large":  "0",
            "Medium": "1",
            "Small":  "2",
            "Masc":   "3"
        }

        if self.shape_mq_chest_bool:
            key_blocks = self.yam_mannequin.data.shape_keys.key_blocks
            state = self.mannequin_state
        else:
            key_blocks = self.yam_torso.data.shape_keys.key_blocks
            state = self.torso_state
        
        if size in lava_sizes:
            state.lavabod = True
        else:
            state.lavabod = False
        
        state.chest_size = category_to_enum[category]
        for key_name, value in preset.items():
            key_blocks[key_name].value = value

    chest_shape_enum: EnumProperty(
        name= "",
        description= "Select a size",
        items=_get_listable_shapes,
        update=_apply_preset
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

    enabled_collection: CollectionProperty(type=EnabledCollection) # type: ignore

    if TYPE_CHECKING:
        chest_shape_enum   : str
        shape_mq_chest_bool: bool
        shape_mq_legs_bool : bool
        shape_mq_other_bool: bool
        enabled_collection : Iterable[EnabledCollection]
        
        collection_state   : CollectionState
        torso_state        : TorsoState
        leg_state          : LegState
        hand_state         : HandState
        feet_state         : FeetState
        yam_torso          : Object
        yam_legs           : Object
        yam_hands          : Object
        yam_feet           : Object
        yam_mannequin      : Object

        mannequin_state: MannequinState

class CollectionManager(Operator):
    bl_idname = "yakit.collection_manager"
    bl_label = "Export"
    bl_description = "Combines chest options and exports them"

    preset: StringProperty() # type: ignore

    def execute(self, context:Context):
        self.props       :DevkitProps        = get_devkit_props()
        self.export                          = self.props.collection_state.export
        self.view_layer                      = bpy.context.view_layer.layer_collection
        self.enabled_coll: EnabledCollection = self.props.enabled_collection
        self.coll                            = bpy.data.collections
        self.restore = []
        self.obj_visibility = {}

        if self.preset == "Export": 
            self.get_obj_visibility(context)
            for state in self.enabled_coll:
                name = state.name
                collection = self.coll[name]
                self.restore.append(collection)

            self.export = True
            # Export state has been set by now, this saves pre-export scene to be restored after export
            self.save_current_state(context)
            self.exclude_collections(context)
            self.restore_obj_visibility()
        
        elif self.preset == "Restore": 
            for state in self.enabled_coll:
                    name = state.name
                    collection = self.coll[name]
                    self.restore.append(collection)

            self.export = False
            self.exclude_collections(context)
            self.restore_obj_visibility()
        
        elif self.preset == "Animation":
            self.get_obj_visibility(context)
            self.save_current_state(context)
            self.export = False

        else:
            self.save_current_state(context)
            self.get_obj_visibility(context)
        return {"FINISHED"}

    def save_current_state(self, context:Context):

        def save_current_state_recursive(layer_collection:LayerCollection):
            if not layer_collection.exclude:
                    state = self.enabled_coll.add()
                    state.name = layer_collection.name
            for child in layer_collection.children:
                save_current_state_recursive(child)

        self.enabled_coll.clear()
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


def link_tri_modifier():
    for obj in bpy.data.objects:
        tri_mod = [modifier for modifier in obj.modifiers if modifier.type == 'TRIANGULATE']
        for modifier in tri_mod:
            _add_tri_driver(modifier)

def unlink_tri_modifier():
    for obj in bpy.data.objects:
        tri_mod = [modifier for modifier in obj.modifiers if modifier.type == 'TRIANGULATE']
        for modifier in tri_mod:
            modifier.driver_remove("show_viewport")

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

class DeactivateKit(Operator):
    bl_idname = "yakit.deactivate"
    bl_label = "Deactivate Devkit"
    bl_description = "Resets all model drivers and deactivates devkit"

    def execute(self, context):
        global devkit_registered
        props = get_devkit_props()

        unlink_tri_modifier()
        props.yam_torso.data.shape_keys.animation_data_clear()
        props.yam_legs.data.shape_keys.animation_data_clear()
        props.yam_hands.data.shape_keys.animation_data_clear()
        props.yam_feet.data.shape_keys.animation_data_clear()
        props.yam_mannequin.data.shape_keys.animation_data_clear()
        unregister()
        devkit_registered = False
        return {'FINISHED'}


def get_conditional_icon(condition: bool, invert: bool=False, if_true: str='CHECKMARK', if_false: str='X'):
    if invert:
        return if_true if not condition else if_false
    else:
        return if_true if condition else if_false

def aligned_row(layout: UILayout, label: str, attr: str, prop=None, prop_str: str="", label_icon: str='NONE', attr_icon: str='NONE', factor:float=0.25, emboss: bool=True, alignment: str="RIGHT") -> UILayout:
    '''
    Create a row with a label in the main split and a prop or text label in the second split. Returns the row if you want to append extra items.
    Args:
        label: Row name.
        prop: Prop referenced, if an object is not passed, the prop is just treated as a label with text
        container: Object that contains the necessary props.
        factor: Split row ratio.
        alignment: Right aligned by default.
    '''
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

        self.collection = self.props.collection_state

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
        
        button_row.prop(self.window, "overview_ui", text="", expand=True)
        
        layout.separator(factor=1, type="LINE")

        # SHAPE MENUS
        
        if self.window.overview_ui == "Shape Keys":
            box = layout.box()

            obj = self.collection_context()
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

            box = layout.box()
            row = box.row(align=True)
            
            icon = 'TRIA_DOWN' if button else 'TRIA_RIGHT'
            row.prop(self.window, "button_chest_shapes", text="", icon=icon, emboss=False)
            row.label(text="Chest")
            
            button_row = row.row(align=True)
            icon = "HIDE_OFF" if self.collection.chest else "HIDE_ON"
            button_row.prop(self.collection, "chest", text="", icon=icon)
            button_row.prop(self.props, "shape_mq_chest_bool", text="", icon="ARMATURE_DATA")
            

            if button:
                self.chest_shapes(layout)

            # LEGS

            button = self.window.button_leg_shapes

            box = layout.box()
            row = box.row(align=True)
            
            icon = 'TRIA_DOWN' if button else 'TRIA_RIGHT'
            row.prop(self.window, "button_leg_shapes", text="", icon=icon, emboss=False)
            row.label(text="Legs")
            
            button_row = row.row(align=True)
            icon = "HIDE_OFF" if self.collection.legs else "HIDE_ON"
            button_row.prop(self.collection, "legs", text="", icon=icon)
            button_row.prop(self.props, "shape_mq_legs_bool", text="", icon="ARMATURE_DATA")

            if button:
                self.leg_shapes(layout)
            
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
                self.other_shapes(layout)

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
            col.operator("outliner.orphans_purge", text="Delete Unused Data")
            col.operator("yakit.deactivate", text="Deactivate Devkit")

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
            devkit_ver = context.scene.ya_devkit_ver 
            col = layout.column(align=True)
            row = col.row(align=True)
            row.alignment = "CENTER"
            if hasattr(context.scene, "ya_addon_ver"):
                addon_ver = context.scene.ya_addon_ver
                row.label(text=f"Addon Ver: {addon_ver[0]}.{addon_ver[1]}.{addon_ver[2]}")
            else: row.label(text=f"Addon Not Installed")
            row = col.row(align=True)
            row.alignment = "CENTER"
            row.label(text=f"Devkit Script Ver: {'.'.join(map(str, devkit_ver))}")
                       
    def collection_context(self) -> Object | None:
        # Links mesh name to the standard collections)
        body_part_collections = {
            "Torso": ['Chest', 'Nipple Piercings'],
            "Waist": ['Legs', 'Pubes'],
            "Hands": ['Hands', 'Nails', 'Practical Uses', 'Clawsies'],
            "Feet": ['Feet', 'Toenails', 'Toe Clawsies'] 
            }

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

    def chest_shapes(self, layout: UILayout):
        layout.separator(factor=0.1)  
        if self.props.shape_mq_chest_bool:
            target      = self.props.mannequin_state
            target_keys = self.props.yam_mannequin.data.shape_keys.key_blocks
        else:
            target      = self.props.torso_state
            target_keys = self.props.yam_torso.data.shape_keys.key_blocks

        chest_size = target.chest_size
        lavabod    = target.lavabod
        row = layout.row(align=True)
        row.prop(target, "chest_size", expand=True, text="Size")

        row = layout.row(align=True)
        row.prop(target, "buff", text=f"{'Buff':<8}", icon="BLANK1")
        row.prop(target, "rue", text=f"{'Rue':<9}", icon="BLANK1")
        row.prop(target, "lavabod", text=f"{'Lavabod':<13}", icon="BLANK1")

        box = layout.box()
        col = box.column(align=True)

        skip      = {"-- Teardrop", "--- Cupcake"}
        lava_skip = ["Omoi", "Uranus", "Nops", "Mini", "Sayonara"]
        prefix_conditions = [
            (chest_size == "3",   "---- ", 5),
            (chest_size == "2",  "--- ", 4),
            (chest_size == "1", "-- ", 3),
            (chest_size == "0",  "- ", 2),
        ]

        name_idx = 0
        for key in target_keys[1:]:
            for condition, prefix, idx in prefix_conditions:
                if condition and key.name.startswith(prefix):
                    name_idx = idx
                    break
            else:
                continue
            if lavabod and any(skip in key.name for skip in lava_skip):
                continue
            if not lavabod and "Soft" in key.name:
                continue
            if key.name in skip:
                continue
            
            aligned_row(col, f"{key.name[name_idx:]}:", 'value', prop=key, prop_str=f"{key.value*100:.0f}%")
        
        layout.separator(factor=0.1)

        aligned_row(layout, "Preset:", "chest_shape_enum", self.props)

        layout.separator(factor=0.1)

    def leg_shapes(self, layout: UILayout):
        layout.separator(factor=0.1)
        if self.props.shape_mq_chest_bool:
            target = self.props.mannequin_state
        else:
            target = self.props.leg_state
        
        options: list[tuple[str, str]] = [
            ("Genitalia", "gen"),
            ("Leg Sizes", "leg_size"),
            ("Squish", "squish"),
            ]
        
        for name, attr in options:
            row = layout.row(align=True)
            split = row.split(factor=0.25, align=True)
            split.alignment = "RIGHT"
            split.label(text=f"{name}:")
            subrow = split.row(align=True)
            subrow.prop(target, attr, text="Size", expand=True)

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text="Butt options:")
        split.prop(target, "small_butt", text=f"{'Small Butt':<14}", icon="BLANK1")
        split.prop(target, "soft_butt", text=f"{'Soft Butt':<14}", icon="BLANK1")

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.prop(target, "alt_hips", text=f"{'Alt Hips':<13}", icon="BLANK1")
        split.prop(target, "rue", text=f"{'Rue':<9}", icon="BLANK1")
        
        layout.separator(factor=0.1)

    def yas_menu(self, layout: UILayout):
        layout.separator(factor=0.1)
 
    def other_shapes(self, layout: UILayout):
        layout.separator(factor=0.1)  
        if self.props.shape_mq_other_bool:
            target      = self.props.mannequin_state
        else:
            target      = self.props.hand_state
            
        options: list[tuple[str, str]] = [
            ("Hands", "hand_size"),
            ("Nails", "nails"),
            ("Clawsies", "clawsies"),
            ]
        
        for name, attr in options:
            if name == "Clawsies" and self.props.shape_mq_other_bool:
                continue
            row = layout.row(align=True)
            split = row.split(factor=0.25, align=True)
            split.alignment = "RIGHT"
            split.label(text=f"{name}:")
            subrow = split.row(align=True)
            if not self.props.shape_mq_other_bool:
                icon = "HIDE_OFF" if getattr(self.collection, name.lower()) else "HIDE_ON"
                subrow.prop(self.collection, name.lower(), text="", icon=icon)

            subrow.prop(target, attr, text="Size", expand=True)
    
        layout.separator(type="LINE")

        if self.props.shape_mq_other_bool:
            target      = self.props.mannequin_state
            target_keys = self.props.yam_mannequin.data.shape_keys.key_blocks
        else:
            target      = self.props.feet_state
            target_keys = self.props.yam_feet.data.shape_keys.key_blocks

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text=f"Rue:")
        subrow = split.row(align=True)
        if not self.props.shape_mq_other_bool:
            icon = "HIDE_OFF" if self.collection.feet else "HIDE_ON"
            subrow.prop(self.collection, "feet", text="", icon=icon)

        subrow.prop(target, "rue_feet", text=f"{'Rue':<9}", icon="BLANK1")

        row = layout.row(align=True)
        split = row.split(factor=0.25, align=True)
        split.alignment = "RIGHT"
        split.label(text=f"")
        subrow = split.row(align=True)

        icon = "HIDE_OFF" if self.collection.toenails else "HIDE_ON"
        subrow.prop(self.collection, "toenails", icon=icon, text="Nails")

        icon = "HIDE_OFF" if self.collection.toe_clawsies else "HIDE_ON"
        subrow.prop(self.collection, "toe_clawsies", icon=icon, text="Clawsies")

        box = layout.box()
        row = box.row()
        
        split = row.split(factor=0.25)
        col = split.column(align=True)
        col.alignment = "RIGHT"
        col2 = split.column(align=True)

        heel_keys = ["Heels", "Cinderella", "Mini Heels"]
        for key in target_keys[1:]:
            if key.name not in heel_keys:
                continue
            col.label(text=f"{key.name}:")
            col2.prop(key, 'value', text=f"{key.value*100:.0f}%")

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
    EnabledCollection,
    AssignControllers,
    DevkitWindowProps,
    CollectionState,
    SubKeyValues,
    TorsoState,
    LegState,
    HandState,
    FeetState,
    MannequinState,
    DevkitProps,
    CollectionManager,
    TriangulateLink,
    DeactivateKit,
    Overview
]


def delayed_setup(dummy=None) -> None:
    global devkit_registered  
    if devkit_registered:
        return None
    context = bpy.context
    link_tri_modifier()
    assign_controller_meshes()
    ModelDrivers()
    DevkitWindowProps.shpk_bools()

    try:
        area = [area for area in context.screen.areas if area.type == 'VIEW_3D'][0]
        view3d = [space for space in area.spaces if space.type == 'VIEW_3D'][0]

        with context.temp_override(area=area, space=view3d):
            view3d.show_region_ui = True
            region = [region for region in area.regions if region.type == 'UI'][0]
            region.active_panel_category = "XIV Kit"
    except:
        pass
    
    devkit_registered = True
    return None

@persistent
def cleanup_props(dummy=None) -> None:
    global devkit_registered
    if not bpy.data.texts.get("devkit.py"):
        unregister()
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

    bpy.app.timers.register(delayed_setup, first_interval=1.5)
    bpy.app.handlers.load_post.append(cleanup_props)

def unregister() -> None: 
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
    
    try:
        bpy.app.handlers.load_post.remove(cleanup_props)
    except:
        pass

if __name__ == "__main__":
    register()