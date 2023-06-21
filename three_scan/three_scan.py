from .lib import Context
from .lib import Mesh
from .lib import Animation
import glob
import json


class MeshEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Mesh):
            return obj.to_json()
        return json.JSONEncoder.default(self, obj)


def scan_and_compare(input_paths, output_path):
    # init context first
    Context.init()

    # scan inputs
    scan(input_paths[0], None)
    scan(input_paths[1], None)

    context = Context.get_instance().get_context()
    # begin compare
    with open(output_path + ".csv", "w") as out_file:
        out_file.write("animation_a,animation_b,correlation_coefficient\n")
        compare_list = list(context["GComp"].values())
        print(len(compare_list))
        for i in range(len(compare_list)):
            for j in range(i, len(compare_list)):
                out_file.write(f"{compare_list[i].name},{compare_list[j].name},{Animation.compare(compare_list[i], compare_list[j])}\n")
            out_file.flush()
    # dump output
    with open(output_path, "w") as outfile:
        del context["GComp"]
        json.dump(context, outfile, cls=MeshEncoder)


def scan(input_path, output_path):
    # init context instance first
    if not Context.is_initialized():
        Context.init()

    for path in glob.glob(input_path + "/mesh.*"):
        with open(path) as f:
            json_string = f.read()
            Context.on_mesh_string(json_string)

    for path in glob.glob(input_path + "/animator.*"):
        with open(path) as f:
            json_string = f.read()
            Context.on_animator_string(json_string)

    # write output
    if output_path == None:
        # don't do anything
        return
    context = Context.get_instance().get_context()
    with open(output_path, "w") as outfile:
        del context["GComp"]
        json.dump(context, outfile, cls=MeshEncoder)

