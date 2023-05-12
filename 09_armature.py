# blender --background --python 09_armature.py --render-anim -- </path/to/output/directory>/<name> <resolution_percentage> <num_samples>
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
    "Metal07": {
        "ambient_occlusion": "",
        "color": os.path.join(working_dir_path, "assets/cc0textures.com/[2K]Metal07/Metal07_col.jpg"),
        "displacement": os.path.join(working_dir_path, "assets/cc0textures.com/[2K]Metal07/Metal07_disp.jpg"),
        "metallic": os.path.join(working_dir_path, "assets/cc0textures.com/[2K]Metal07/Metal07_met.jpg"),
        "normal": os.path.join(working_dir_path, "assets/cc0textures.com/[2K]Metal07/Metal07_nrm.jpg"),
        "roughness": os.path.join(working_dir_path, "assets/cc0textures.com/[2K]Metal07/Metal07_rgh.jpg"),
    },
    "Marble01": {
        "ambient_occlusion": "",
        "color": os.path.join(working_dir_path, "assets/cc0textures.com/[2K]Marble01/Marble01_col.jpg"),
        "displacement": os.path.join(working_dir_path, "assets/cc0textures.com/[2K]Marble01/Marble01_disp.jpg"),
        "metallic": "",
        "normal": os.path.join(working_dir_path, "assets/cc0textures.com/[2K]Marble01/Marble01_nrm.jpg"),
        "roughness": os.path.join(working_dir_path, "assets/cc0textures.com/[2K]Marble01/Marble01_rgh.jpg"),
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


def create_skinned_object():
    # Edit mode
    bpy.ops.object.add(type='ARMATURE', enter_editmode=True, location=(0.0, 0.0, 0.0))
    armature = bpy.context.object
    bone1 = armature.data.edit_bones.new('Bone1')
    bone1.head = (0.0, 0.0, 0.0)
    bone1.tail = (0.0, 0.0, 1.0)
    bone2 = armature.data.edit_bones.new('Bone2')
    bone2.parent = bone1
    bone2.use_connect = True
    bone2.tail = (0.0, 0.0, 2.0)

    # Pose mode
    bpy.ops.object.mode_set(mode='POSE')
    bone2 = armature.pose.bones['Bone2']
    bone2.rotation_mode = 'XYZ'
    bone2.rotation_euler = (0.0, 0.0, 0.0)
    bone2.keyframe_insert(data_path='rotation_euler', frame=4)
    bone2.rotation_euler = (+math.pi * 30.0 / 180.0, 0.0, 0.0)
    bone2.keyframe_insert(data_path='rotation_euler', frame=12)
    bone2.rotation_euler = (-math.pi * 30.0 / 180.0, 0.0, 0.0)
    bone2.keyframe_insert(data_path='rotation_euler', frame=20)
    bone2.rotation_euler = (+math.pi * 30.0 / 180.0, 0.0, 0.0)
    bone2.keyframe_insert(data_path='rotation_euler', frame=28)
    bone2.rotation_euler = (0.0, 0.0, 0.0)
    bone2.keyframe_insert(data_path='rotation_euler', frame=36)

    # Object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Material
    add_named_material("Metal07")

    # Mesh
    bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 1.0), calc_uvs=True)
    cube = bpy.context.object
    cube.name = "Cuboid"
    cube.scale = (0.5, 0.5, 1.0)
    utils.add_subdivision_surface_modifier(cube, 3, is_simple=True)
    utils.add_subdivision_surface_modifier(cube, 3, is_simple=False)
    utils.set_smooth_shading(cube.data)
    cube.data.materials.append(bpy.data.materials["Metal07"])

    # Set the armature as the parent of the cube using the "Automatic Weight" armature option
    bpy.ops.object.select_all(action='DESELECT')
    if bpy.app.version >= (2, 80, 0):
        cube.select_set(True)
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
    else:
        cube.select = True
        armature.select = True
        bpy.context.scene.objects.active = armature
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    return armature


def set_scene_objects():
    add_named_material("Marble01", displacement_scale=0.02)

    current_object = create_skinned_object()
    current_object.rotation_euler = (0.0, 0.0, math.pi * 60.0 / 180.0)

    current_object = utils.create_plane(size=12.0, name="Floor")
    current_object.data.materials.append(bpy.data.materials["Marble01"])

    bpy.ops.object.empty_add(location=(0.0, 0.0, 1.0))
    return bpy.context.object


# Args
output_file_path = bpy.path.relpath(str(sys.argv[sys.argv.index('--') + 1]))
resolution_percentage = int(sys.argv[sys.argv.index('--') + 2])
num_samples = int(sys.argv[sys.argv.index('--') + 3])

# Parameters
hdri_path = os.path.join(working_dir_path, "assets/HDRIs/green_point_park_2k.hdr")

# Scene Building
scene = bpy.data.scenes["Scene"]
world = scene.world

## Reset
utils.clean_objects()

## Suzannes
focus_target = set_scene_objects()

## Camera
bpy.ops.object.camera_add(location=(0.0, -16.0, 2.0))
camera_object = bpy.context.object

utils.add_track_to_constraint(camera_object, focus_target)
utils.set_camera_params(camera_object.data, focus_target, lens=85, fstop=0.5)

## Lights
utils.build_environment_texture_background(world, hdri_path)

## Composition
utils.build_scene_composition(scene)

# Animation Setting
utils.set_animation(scene, fps=24, frame_start=1, frame_end=40)

# Render Setting
utils.set_output_properties(scene, resolution_percentage, output_file_path)
utils.set_cycles_renderer(scene, camera_object, num_samples, use_motion_blur=True)
