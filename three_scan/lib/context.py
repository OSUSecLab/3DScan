import json
from .Animation import Animator
from .Mesh import Mesh


class Context:
    instance = None
    context = None

    def __init__(self):
        self.context = dict()
        self.context["GMesh"] = dict()
        self.context["GBone"] = dict()
        self.context["GAnim"] = dict()
        self.context["GComp"] = dict()

    def get_context(self):
        return self.context
    
    def set_context(self, _context):
        self.context = _context

    @staticmethod
    def init():
        Context.instance = Context()

    @staticmethod
    def get_instance():
        if not Context.is_initialized():
            raise ValueError("[context] init before get instance")
        return Context.instance

    @staticmethod
    def is_initialized():
        if Context.instance == None:
            return False
        return True

    @staticmethod
    def check_and_add(container, mhash, value):
        if mhash not in container:
            container[mhash] = value

    @staticmethod
    def mesh_from_json_array(json_string, context):
        mesh_str, asset_name, path_id, name, skin, bone_hashes = json.loads(json_string)
        uid = "%s--%s" % (asset_name, path_id)

        if uid in context["GMesh"]:
            print("[context mesh_from_json_array] already has this mesh")
            return context["GMesh"][uid]

        if mesh_str == None or len(mesh_str) == 0:
            print("[context mesh_from_json_array] none mesh str", uid)
            mesh_str = ""

        mesh = Mesh(mesh_str.split("\n"), name)
        mesh.asset_name = asset_name
        mesh.path_id = path_id
        mesh.skin = skin
        mesh.bone_hashes = bone_hashes
        mesh.uid = uid
        context["GMesh"][uid] = mesh
        return mesh

    @staticmethod
    def on_mesh_string(json_string):
        if not Context.is_initialized():
            Context.init()
        context = Context.get_instance().get_context()
        mesh = Context.mesh_from_json_array(json_string, context)
        if mesh == None:
            print("[context on_mesh_string] unable to create Mesh object from JSON string")
            return

        mesh.sort()
        mhash = mesh.get_hash()
        Context.check_and_add(context["GMesh"], mhash, mesh)

    @staticmethod
    def anim_from_json_string(json_string, context):
        anim_json = json.loads(json_string)
        animator = Animator(anim_json)
        return animator

    @staticmethod
    def on_animator_string(json_string):
        if not Context.is_initialized():
            Context.init()
        context = Context.get_instance().get_context()
        animator = Context.anim_from_json_string(json_string, context)
        if animator == None:
            print("[context on_animator_string] unable to create Animator object from JSON string")
            return

        animator.match_bones_and_animations(context["GMesh"])

        for mesh in animator.meshes:
            if hasattr(mesh, 'mesh_bones_hash'):
                Context.check_and_add(context["GBone"], mesh.mesh_bones_hash, mesh.to_json(include_bone=True))

        for animation in animator.animations:
            Context.check_and_add(context["GAnim"], animation.mesh_bones_animation_hash, animation.to_json())
            Context.check_and_add(context["GComp"], animation.mesh_bones_animation_hash, animation)

