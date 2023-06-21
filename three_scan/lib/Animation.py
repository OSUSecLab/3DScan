import base64
import copy
import hashlib
from scipy.interpolate import CubicSpline
from scipy.stats import pearsonr
import math


class Animator:
    def __init__(self, json_string):
        self.name = json_string['name']
        self.bone_path_hash = json_string['bonePathHash']
        self.root_frame = json_string['RootFrame']
        self.mesh_list = json_string['MeshList']
        self.material_list = json_string['MaterialList']
        self.texture_list = json_string['TextureList']
        self.animation_list = json_string['AnimationList']
        self.mesh_to_materials = dict()

        self.textures = dict()
        self.materials = dict()

        self.meshes = list()
        self.animations = list()

        self.init_material_texture()

    def init_material_texture(self):
        for i in self.texture_list:
            texture = dict()
            texture["name"] = i["Name"]
            texture["wd"] = i["m_Width"]
            texture["ht"] = i["m_Height"]
            texture["mc"] = i["m_MipCount"]

            data = base64.b64decode(i["Data"])
            texture["hash"] = hashlib.blake2s(data).hexdigest()
            texture["size"] = len(data)
            self.textures[i["Name"]] = texture

        for i in self.material_list:
            if len(i.get("Textures",[])) > 0:
                material = list()
                for textr in i["Textures"]:
                    if textr["Name"] in self.textures:
                        material.append(self.textures[textr["Name"]])
                self.materials[i["Name"]] = material

    def match_bones_and_animations(self, meshes):
        for jsmesh in self.mesh_list:
            uid = "%s--%s" % (jsmesh["Mesh_AssetFileName"], jsmesh["Mesh_PathID"])
            mesh = meshes[uid]
            mesh.set_bones(self.bone_path_hash, jsmesh["BoneList"])
            mates = mesh.set_material(self.materials, jsmesh["SubmeshList"])

            if mesh not in self.mesh_to_materials: self.mesh_to_materials[mesh] = set()
            self.mesh_to_materials[mesh].update(mates)
            self.meshes.append(mesh)

        for animation_js in self.animation_list:
            for mesh in self.meshes:
                animation = try_it(mesh, animation_js, self.name, self.mesh_to_materials)
                if animation:
                    self.animations.append(animation)


class Animation:
    def __init__(self, mesh, json_string, animator_name, materials):
        self.name = json_string["Name"]
        self.sample_rate = json_string.get("SampleRate", -1)
        self.timings = set()
        self.mesh = mesh
        self.mesh_name = mesh.name
        self.animator_name = animator_name
        self.animationjs = json_string
        self.materials = list(materials)
        self.bones = copy.deepcopy(mesh.bones)
        self.bones_id = copy.deepcopy(mesh.bones_id)
        self.bones_interpolate_functions = dict()

        self.anim_hash = None
        self.type = "anim"
        self.add_tracks()
        self.chash()

    def add_tracks(self):
        def interpolate(track, channle, track_interpolation, resname):
            sorted_x = sorted(track[channle], key=lambda kv: kv["time"])
            if len(sorted_x) > 0:
                track_interpolation[resname] = (
                    # X
                    CubicSpline(range(len(sorted_x)), [i["value"]["X"] for i in sorted_x]),
                    # Y
                    CubicSpline(range(len(sorted_x)), [i["value"]["Y"] for i in sorted_x]),
                    # Z
                    CubicSpline(range(len(sorted_x)), [i["value"]["Z"] for i in sorted_x])
                )

        def ttt(track, channle, res, resname):
            sorted_x = sorted(track[channle], key=lambda kv: kv["time"])
            if len(sorted_x) > 0:
                res[resname] = (
                    round(sorted_x[0 ]["value"]["X"]),
                    round(sorted_x[0 ]["value"]["Y"]),
                    round(sorted_x[0 ]["value"]["Z"]),

                    round(sorted_x[-1]["value"]["X"]),
                    round(sorted_x[-1]["value"]["Y"]),
                    round(sorted_x[-1]["value"]["Z"]),
                )

        for track in self.animationjs["TrackList"]:
            if track["Path"] == None:
                continue
            if track["sPath"] not in self.bones:
                continue

            my_track = {"s": None, "r": None, "t": None}
            track_interpolation = {"s": None, "r": None, "t": None}
            for channle, resname  in [("Scalings", "s"), ("Rotations", "r"), ("Translations", "t")]:
                ttt(track, channle, my_track, resname)
                interpolate(track, channle, track_interpolation, resname)
                self.timings.update([one_item.get("time", 0) for one_item in track[channle]])
            self.bones[track["sPath"]]["tk"] = str(my_track["s"]) + str(my_track["r"]) + str(my_track["t"])
            self.bones_interpolate_functions[track["sPath"]] = track_interpolation

    def compare(self, animation):
        return Animation.compare(self, animation)

    @staticmethod
    def compare(animation_a, animation_b):
        if len(animation_a.bones_interpolate_functions) == 0 or len(animation_b.bones_interpolate_functions) == 0:
            print("[-] animations have zero bones_interpolate_functions")
            return 0
        results = list()
        # only compare the same bones
        for s_path in animation_a.bones_interpolate_functions:
            if s_path not in animation_b.bones_interpolate_functions:
                continue
            # generate 100 values for each dimesion and channel
            generated_range = range(100)
            # let's do Scalings first
            scaling_func_A = animation_a.bones_interpolate_functions[s_path]["s"]
            scaling_func_B = animation_b.bones_interpolate_functions[s_path]["s"]
            if scaling_func_A != None and scaling_func_B != None:
                scaling_generated_A = (
                    scaling_func_A[0](generated_range),
                    scaling_func_A[1](generated_range),
                    scaling_func_A[2](generated_range)
                )
                scaling_generated_B = (
                    scaling_func_B[0](generated_range),
                    scaling_func_B[1](generated_range),
                    scaling_func_B[2](generated_range)
                )
            else:
                scaling_generated_A = None
                scaling_generated_B = None
            # then Rotations
            rotation_func_A = animation_a.bones_interpolate_functions[s_path]["r"]
            rotation_func_B = animation_b.bones_interpolate_functions[s_path]["r"]
            if rotation_func_A != None and rotation_func_B != None:
                rotation_generated_A = (
                    rotation_func_A[0](generated_range),
                    rotation_func_A[1](generated_range),
                    rotation_func_A[2](generated_range)
                )
                rotation_generated_B = (
                    rotation_func_B[0](generated_range),
                    rotation_func_B[1](generated_range),
                    rotation_func_B[2](generated_range)
                )
            else:
                rotation_generated_A = None
                rotation_generated_B = None
            # finally Translations
            translation_func_A = animation_a.bones_interpolate_functions[s_path]["t"]
            translation_func_B = animation_b.bones_interpolate_functions[s_path]["t"]
            if translation_func_A != None and translation_func_B != None:
                translation_generated_A = (
                    translation_func_A[0](generated_range),
                    translation_func_A[1](generated_range),
                    translation_func_A[2](generated_range)
                )
                translation_generated_B = (
                    translation_func_B[0](generated_range),
                    translation_func_B[1](generated_range),
                    translation_func_B[2](generated_range)
                )
            else:
                translation_generated_A = None
                translation_generated_B = None
            # now we can calculate the Pearson correlation coefficient
            # let's do Scalings first
            if scaling_generated_A != None and scaling_generated_B != None:
                scaling_correlation_X = pearsonr(scaling_generated_A[0], scaling_generated_B[0]).statistic
                scaling_correlation_Y = pearsonr(scaling_generated_A[1], scaling_generated_B[1]).statistic
                scaling_correlation_Z = pearsonr(scaling_generated_A[2], scaling_generated_B[2]).statistic
                scaling_correlations = (
                    0 if math.isnan(scaling_correlation_X) else scaling_correlation_X,
                    0 if math.isnan(scaling_correlation_Y) else scaling_correlation_Y,
                    0 if math.isnan(scaling_correlation_Z) else scaling_correlation_Z,
                )
            else:
                scaling_correlations = tuple()
            # then, Rotations
            if rotation_generated_A != None and rotation_generated_B != None:
                rotation_correlation_X = pearsonr(rotation_generated_A[0], rotation_generated_B[0]).statistic
                rotation_correlation_Y = pearsonr(rotation_generated_A[1], rotation_generated_B[1]).statistic
                rotation_correlation_Z = pearsonr(rotation_generated_A[2], rotation_generated_B[2]).statistic
                rotation_correlations = (
                    0 if math.isnan(rotation_correlation_X) else rotation_correlation_X,
                    0 if math.isnan(rotation_correlation_Y) else rotation_correlation_Y,
                    0 if math.isnan(rotation_correlation_Z) else rotation_correlation_Z,
                )
            else:
                rotation_correlations = tuple()
            # finally, Translations
            if translation_generated_A != None and translation_generated_B != None:
                translation_correlation_X = pearsonr(translation_generated_A[0], translation_generated_B[0]).statistic 
                translation_correlation_Y = pearsonr(translation_generated_A[1], translation_generated_B[1]).statistic 
                translation_correlation_Z = pearsonr(translation_generated_A[2], translation_generated_B[2]).statistic 
                translation_correlations = (
                    0 if math.isnan(translation_correlation_X) else translation_correlation_X,
                    0 if math.isnan(translation_correlation_Y) else translation_correlation_Y,
                    0 if math.isnan(translation_correlation_Z) else translation_correlation_Z,
                )
            else:
                translation_correlations = tuple()
            # summarize them
            for i in scaling_correlations + rotation_correlations + translation_correlations:
                # drop the invalid data point
                if i == 0:
                    continue
                results.append(abs(i))
        
        return sum(results) / len(results) if len(results) else 0

    def chash(self):
        def visit_bone(bid):
            bname = self.bones_id[bid]
            subs = list()
            for i in self.bones[bname]["chdr"]:
                subs.append(visit_bone(i))
            return "(%s):%s" % (self.bones[bname].get("tk", "x"), ",".join(sorted(subs)))

        heads = list()
        for bn in self.bones:
            if self.bones[bn]["fath"] == None:
                heads.append(visit_bone(self.bones[bn]["id"]))

        bhstr = ",".join(sorted(heads))
        self.anim_hash = hashlib.blake2s(bhstr.encode('utf-8')).hexdigest()
        self.mesh_bones_animation_hash = hashlib.blake2s((self.mesh.mesh_bones_hash + bhstr).encode('utf-8')).hexdigest()

    def to_json(self):
        ret = dict()
        ret["type"] = self.type

        if self.anim_hash != None:
            ret['ah'] = self.anim_hash

        if self.mesh.bones_hash != None:
            ret['bh'] = self.mesh.bones_hash

        if self.mesh.mesh_hash != None:
            ret['mh'] = self.mesh.mesh_hash

        if self.mesh.mesh_bones_hash != None:
            ret['mbh'] = self.mesh.mesh_bones_hash

        if self.mesh_bones_animation_hash != None:
            ret['mbah'] = self.mesh_bones_animation_hash

        ret['n'] = self.name
        ret['sr'] = self.sample_rate
        ret['timings'] = list(self.timings)
        ret['m'] = self.mesh.uid + " " + self.mesh.name
        ret['ator'] = self.animator_name
        ret['matrl'] = self.materials
        return ret


def lists_similar_rate(listA, listB):
    listA, listB = set(listA), set(listB)

    count = 0
    for i in listA:
        if i in listB:
            count += 1

    return count * 1.0 / min(len(listB), len(listA)), count


def try_it(mesh, js, animator_name, mesh2materials):
    bones = [track["Path"] for track in js["TrackList"] if track["Path"] != None]
    if len(bones) == 0 or len(mesh.bones.keys()) == 0:
        return None

    rate, count = lists_similar_rate(bones, mesh.bones.keys())

    if count > 0 : #rate > 0.9 or count < 3:
        for i in js["TrackList"]:
            if i["Path"] == None:
                continue

            if "sPath" not in i:
                #if i["Path"].startswith(animator_name+"/"):
                #   i["sPath"] = i["Path"][len(animator_name)+1:]
                #else:
                #   i["sPath"] = i["Path"]
                i["sPath"] = i["Path"]

            #if i["sPath"] not in mesh.bones:
                #print("[-] animation not match", mesh.name, i["sPath"], i["Path"])
            #   return None
        #print("[*] mesh & animation matches!", mesh.name, js["Name"])
        return Animation(mesh, js, animator_name, mesh2materials.get(mesh, set()))
    else:
        print("[-] animation not match", mesh.name, animator_name, rate, count)
        return None

