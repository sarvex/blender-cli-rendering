# blender --background --python 12_cloth.py --render-anim -- </path/to/output/directory>/<name> <resolution_percentage> <num_samples>
# ffmpeg -r 24 -i </path/to/output/directory>/<name>%04d.png -pix_fmt yuv420p out.mp4

import bpy
import sys
import math
import os

working_dir_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(working_dir_path)

import utils

# Define paths for the PBR textures used in this scene
texture_paths = {
    "Fabric02": {
        "ambient_occlusion": "",
        "color": os.path.join(working_dir_path, "assets/cc0textures.com/[2K]Fabric02/Fabric02_col.jpg"),
        "displacement": os.path.join(working_dir_path, "assets/cc0textures.com/[2K]Fabric02/Fabric02_disp.jpg"),
        "metallic": "",
        "normal": os.path.join(working_dir_path, "assets/cc0textures.com/[2K]Fabric02/Fabric02_nrm.jpg"),
        "roughness": os.path.join(working_dir_path, "assets/cc0textures.com/[2K]Fabric02/Fabric02_rgh.jpg"),
    },
    "Fabric03": {
        "ambient_occlusion": "",
        "color": os.path.join(working_dir_path, "assets/cc0textures.com/[2K]Fabric03/Fabric03_col.jpg"),
        "displacement": os.path.join(working_dir_path, "assets/cc0textures.com/[2K]Fabric03/Fabric03_disp.jpg"),
        "metallic": "",
        "normal": os.path.join(working_dir_path, "assets/cc0textures.com/[2K]Fabric03/Fabric03_nrm.jpg"),
        "roughness": os.path.join(working_dir_path, "assets/cc0textures.com/[2K]Fabric03/Fabric03_rgh.jpg"),
    },
}


def add_named_material(name: str, scale=(1.0, 1.0, 1.0), displacement_scale: float = 1.0) -> bpy.types.Material:
    mat = utils.add_material(name, use_nodes=True, make_node_tree_empty=True)
    utils.build_pbr_textured_nodes(mat.node_tree,
                                   color_texture_path=texture_paths[name]["color"],
                                   roughness_texture_path=texture_paths[name]["roughness"],
                                   normal_texture_path=texture_paths[name]["normal"],
                                   metallic_texture_path=texture_paths[name]["metallic"],
                                   displacement_texture_path=texture_paths[name]["displacement"],
                                   ambient_occlusion_texture_path=texture_paths[name]["ambient_occlusion"],
                                   scale=scale,
                                   displacement_scale=displacement_scale)
    return mat


def set_floor_and_lights() -> None:
    size = 200.0
    current_object = utils.create_plane(size=size, name="Floor")
    floor_mat = utils.add_material("Material_Plane", use_nodes=True, make_node_tree_empty=True)
    utils.build_checker_board_nodes(floor_mat.node_tree, size)
    current_object.data.materials.append(floor_mat)

    utils.create_area_light(location=(6.0, 0.0, 4.0),
                            rotation=(0.0, math.pi * 60.0 / 180.0, 0.0),
                            size=5.0,
                            color=(1.00, 0.70, 0.60, 1.00),
                            strength=1500.0,
                            name="Main Light")
    utils.create_area_light(location=(-6.0, 0.0, 2.0),
                            rotation=(0.0, -math.pi * 80.0 / 180.0, 0.0),
                            size=5.0,
                            color=(0.30, 0.42, 1.00, 1.00),
                            strength=1000.0,
                            name="Sub Light")


def set_scene_objects() -> bpy.types.Object:
    add_named_material("Fabric02")
    add_named_material("Fabric03")
    bpy.data.materials["Fabric02"].node_tree.nodes["Principled BSDF"].inputs["Sheen"].default_value = 4.0
    bpy.data.materials["Fabric03"].node_tree.nodes["Principled BSDF"].inputs["Sheen"].default_value = 4.0

    set_floor_and_lights()

    current_object = utils.create_smooth_monkey(location=(0.0, 0.0, 1.0))
    current_object.data.materials.append(bpy.data.materials["Fabric03"])
    bpy.ops.object.modifier_add(type='COLLISION')

    if bpy.app.version >= (2, 80, 0):
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=75, y_subdivisions=75, size=3.0, location=(0.0, 0.0, 2.75))
    else:
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=75,
                                        y_subdivisions=75,
                                        radius=1.5,
                                        calc_uvs=True,
                                        location=(0.0, 0.0, 2.75))
    cloth_object = bpy.context.object
    cloth_object.name = "Cloth"
    bpy.ops.object.modifier_add(type='CLOTH')
    cloth_object.modifiers["Cloth"].collision_settings.use_collision = True
    cloth_object.modifiers["Cloth"].collision_settings.use_self_collision = True
    cloth_object.modifiers["Cloth"].settings.quality = 10
    utils.set_smooth_shading(cloth_object.data)
    utils.add_subdivision_surface_modifier(cloth_object, 2)
    cloth_object.data.materials.append(bpy.data.materials["Fabric02"])

    bpy.ops.object.empty_add(location=(0.0, -0.75, 1.05))
    return bpy.context.object


# Args
output_file_path = bpy.path.relpath(str(sys.argv[sys.argv.index('--') + 1]))
resolution_percentage = int(sys.argv[sys.argv.index('--') + 2])
num_samples = int(sys.argv[sys.argv.index('--') + 3])

# Scene Building
scene = bpy.data.scenes["Scene"]
world = scene.world

## Reset
utils.clean_objects()

## Animation
utils.set_animation(scene, fps=24, frame_start=1, frame_end=48)

## Object
focus_target_object = set_scene_objects()

## Camera
camera_object = utils.create_camera(location=(0.0, -12.5, 2.2))

utils.add_track_to_constraint(camera_object, focus_target_object)
utils.set_camera_params(camera_object.data, focus_target_object)

## Background
utils.build_rgb_background(world, rgb=(0.0, 0.0, 0.0, 1.0))

## Composition
utils.build_scene_composition(scene, dispersion=0.0)

# Render Setting
utils.set_output_properties(scene, resolution_percentage, output_file_path)
utils.set_cycles_renderer(scene, camera_object, num_samples, use_motion_blur=True)
