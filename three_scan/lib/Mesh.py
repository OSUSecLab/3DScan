import json
import hashlib


class Mesh:
    def __init__(self, lines, name):
        self.name = name
        self.verts = dict()
        self.sorted_verts = dict()

        self.vertsT = dict()
        self.faces = list()
        self.type = "mesh"
        self.materials = dict()

        self.file_hash = hashlib.blake2s(("\n".join(lines)).encode('utf-8')).hexdigest()
        self.mesh_hash = None
        self.bones_hash = None
        self.mesh_bones_hash = None

        for i in lines:
            i = i.strip()
            if i.startswith("v "):
                _, x, y, z = i.split(" ")
                x, y, z = float(x), float(y), float(z)
                x, y, z = x * 10000, y * 10000, z * 10000
                self.verts[len(self.verts) + 1] = (x, y, z)

            if i.startswith("vt "):
                _, x, y = i.split(" ")
                x, y = float(x), float(y)
                x, y = x * 10000, y * 10000
                self.vertsT[len(self.vertsT) + 1] = (x, y)

            if i.startswith("f "):
                _, x, y, z = i.split(" ")
                x, y, z = x.split("/")[0], y.split("/")[0], z.split("/")[0]
                x, y, z = int(x), int(y), int(z)
                self.faces.append(sorted([x, y, z]))

        self.verts_count = len(self.verts)
        self.faces_count = len(self.faces)

    def set_material(self, materials, submesh_list):
        new_materials = list()
        for sub in submesh_list:
            if sub["Material"] in materials:
                mat = materials[sub["Material"]]
                for textr in mat:
                    if textr["hash"] not in self.materials:
                        self.materials[textr["hash"]] = textr
                    new_materials.append(textr["hash"])
        return new_materials

    def set_bones(self, bone_path_hash, bone_list):
        self.bones = dict()
        self.bones_id = dict()

        if bone_list == None:
            print("[mesh] mesh has no bones", self.name)
            return

        for i, bone in enumerate(bone_list):
            bone_name = bone["Path"]
            if bone_name != None:
                self.bones[bone_name] = {"id": i, "chdr": [], "fath": None}
                self.bones_id[i] = bone_name

        for bone_name in self.bones:
            father = None
            for bn in self.bones:
                if bn != bone_name:
                    if bone_name.startswith(bn) and bone_name[len(bn)] == '/':
                        if father == None or len(bn) > len(father):
                            father = bn
            if father != None:
                self.bones[bone_name]["fath"] = self.bones[father]["id"]
                self.bones[father]["chdr"].append(self.bones[bone_name]["id"])

        self.calc_bones_hash()

    def print_bones(self):
        def print_bone(bid, dent="  "):
            bname = self.bones_id[bid]
            print(dent + bname, len(self.bones[bname]["vs"]))
            for i in self.bones[bname]["chdr"]:
                print_bone(i, dent + "  ")

        print("[*] ===> bones of meshes", self.name)
        for bn in self.bones:
            if self.bones[bn]["fath"] == None:
                print_bone(self.bones[bn]["id"])
        print("[*] ===> end of bones of meshes")

    def calc_bones_hash(self):
        def visit_bone(bid):
            bname = self.bones_id[bid]
            subs = list()
            for i in self.bones[bname]["chdr"]:
                subs.append(visit_bone(i))
            return "(%s)" % ",".join(sorted(subs))

        heads = list()
        for bn in self.bones:
            if self.bones[bn]["fath"] == None:
                heads.append(visit_bone(self.bones[bn]["id"]))

        bhstr = ",".join(sorted(heads))
        self.bones_hash = hashlib.blake2s(bhstr.encode('utf-8')).hexdigest()
        self.mesh_bones_hash = hashlib.blake2s((self.mesh_hash + bhstr).encode('utf-8')).hexdigest()
        self.type = "bmesh"

    def to_json(self, include_bone=False):
        ret = dict()
        ret["type"] = self.type
        ret["matrl"] = self.materials
        ret["fh"] = self.file_hash

        if self.mesh_hash != None:
            ret['mh'] = self.mesh_hash

        if self.bones_hash != None:
            ret['bh'] = self.bones_hash

        if self.mesh_bones_hash != None:
            ret['mbh'] = self.mesh_bones_hash
            if include_bone:
                ret['bones_str'] = json.dumps(self.bones)

        ret['v'] = self.verts_count
        ret['f'] = self.faces_count
        ret['n'] = self.uid + " " + self.name
        return ret

    def sort(self):
        if getattr(self, "sorted_verts", False):
            return

        tverts = sorted(set(self.verts.values()))
        for i in tverts:
            self.sorted_verts[i] = len(self.sorted_verts)

        tfaces = list()
        for face in self.faces:
            nface = list()
            for i in face:
                nface.append(self.sorted_verts[self.verts[i]])
            tfaces.append(sorted(nface))

        self.sorted_faces = sorted(tfaces)
        return self

    def get_hash(self):
        mhash = hashlib.blake2s()
        result = ""
        for face in self.sorted_faces:
            for i in face:
                mhash.update(("%s," % i).encode('utf-8'))
                result += str(i) + ","
            mhash.update("|".encode('utf-8'))
            result += "|"
        self.mesh_hash = mhash.hexdigest()
        return self.mesh_hash

