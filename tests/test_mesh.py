import numpy as np

from src.image_to_3d import MeshOptions, _grid_stride_for_target, mesh_from_depth


def test_stride_increases_for_lower_face_budget():
    s1 = _grid_stride_for_target(512, 512, 100000)
    s2 = _grid_stride_for_target(512, 512, 10000)
    assert s2 > s1


def test_mesh_face_count_respects_budget_approximately():
    depth = np.random.rand(256, 256).astype(np.float32)
    mesh = mesh_from_depth(depth, None, MeshOptions(target_faces=8000, textured=False))
    assert len(mesh.faces) <= 9000
    assert len(mesh.vertices) > 0
