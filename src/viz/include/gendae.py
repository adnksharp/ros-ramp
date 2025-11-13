from collada import *
from collada.material import CImage
import numpy as np
import os


MARKER_SIDE = 0.1
THICKNESS = 0.01
OUTPUT_DIR = 'aruco_patterns'
IMAGE_DIR = 'aruco_patterns'
NUM_MARKERS = 1000 

def create_aruco_mesh(marker_id):
    mesh = Collada()
    marker_id_str = f"{marker_id:04d}"
    image_name = f"{marker_id_str}.png"
    
    image = CImage(
        id=f"image_{marker_id_str}", 
        path=image_name
    )
    mesh.images.append(image)
    
    effect = material.Effect(f"effect_{marker_id_str}", [], "lambert", 
                             ambient=(1.0, 1.0, 1.0),
                             diffuse=material.Map(image, texcoord="0"),
                             emission=(1.0, 1.0, 1.0),
                             specular=(0.5, 0.5, 0.5)) 

    mat = material.Material(f"material_{marker_id_str}", f"aruco_mat_{marker_id_str}", effect)

    mesh.effects.append(effect)
    mesh.materials.append(mat)

    half_side = MARKER_SIDE / 2.0
    half_thickness = THICKNESS / 2.0

    vert_floats = [
        half_side, -half_side, half_thickness,
        half_side, half_side, half_thickness,
        -half_side, -half_side, half_thickness,
        -half_side, half_side, half_thickness,
        
        half_side, -half_side, -half_thickness,
        half_side, half_side, -half_thickness,
        -half_side, -half_side, -half_thickness,
        -half_side, half_side, -half_thickness
    ]

    normal_floats = [
        0, 0, 1,
        0, 0, -1,
        1, 0, 0,
        -1, 0, 0,
        0, 1, 0,
        0, -1, 0
    ]

    tex_floats = [1.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0]

    vert_src = source.FloatSource("cube-verts", np.array(vert_floats), ('X', 'Y', 'Z'))
    normal_src = source.FloatSource("cube-normals", np.array(normal_floats), ('X', 'Y', 'Z'))
    tex_src = source.FloatSource("cube-tex", np.array(tex_floats), ('S', 'T'))

    geom = geometry.Geometry(mesh, f"geometry_{marker_id_str}", f"aruco_cube_{marker_id_str}", 
                             [vert_src, normal_src, tex_src])

    indices = np.array([
        1, 0, 1,   0, 0, 0,   2, 0, 2,
        1, 0, 1,   2, 0, 2,   3, 0, 3,
        
        6, 1, 0,   4, 1, 0,   5, 1, 0,
        6, 1, 0,   5, 1, 0,   7, 1, 0,

        4, 2, 0,   0, 2, 0,   1, 2, 0,
        4, 2, 0,   1, 2, 0,   5, 2, 0,
        
        2, 3, 0,   6, 3, 0,   7, 3, 0,
        2, 3, 0,   7, 3, 0,   3, 3, 0,

        0, 5, 0,   4, 5, 0,   6, 5, 0,
        0, 5, 0,   6, 5, 0,   2, 5, 0,

        5, 4, 0,   1, 4, 0,   3, 4, 0,
        5, 4, 0,   3, 4, 0,   7, 4, 0

    ])

    input_list = source.InputList()
    input_list.addInput(0, 'VERTEX', "#cube-verts")
    input_list.addInput(1, 'NORMAL', "#cube-normals")
    input_list.addInput(2, 'TEXCOORD', "#cube-tex", set="0")

    triset = geom.createTriangleSet(indices, input_list, "materialref")
    geom.primitives.append(triset)
    mesh.geometries.append(geom)

    matnode = scene.MaterialNode("materialref", mat, inputs=[])
    geomnode = scene.GeometryNode(geom, [matnode])

    node = scene.Node(f"aruco_node_{marker_id_str}", children=[geomnode])

    myscene = scene.Scene("myscene", [node])
    mesh.scenes.append(myscene)
    mesh.scene = myscene

    output_filepath = os.path.join(OUTPUT_DIR, f"{marker_id_str}.dae")
    mesh.write(output_filepath)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for i in range(NUM_MARKERS):
        try:
            create_aruco_mesh(i)
        except Exception as e:
            print(f"ERROR fatal al generar el marcador {i}: {e}")

if __name__ == '__main__':
    main()
