# OGL_Graph
Generate **OpenGL C++** code by **json** description of a rendering pipeline (graph)!

**SOON**

## Graph example
```json
{
  "params": {
    "z_near": 0.1,
    "z_far": 100.0,
    "fov": 90
  },
  "framebuffers": [],
  "subprograms": [
    {
      "name": "main",
      "vert_path": "main_vert.glsl",
      "frag_path": "main_frag.glsl",
      "use_depth": true,
      "outputs": [
        "SCREEN"
      ],
      "fb_inputs": [
      ],
      "inputs": [
        {
          "name": "projectionMat_u",
          "type": "GL_PROJECTION_MATRIX"
        },
        {
          "name": "gridDims_u",
          "type": "int3"
        },
        {
          "name": "voxels_u",
          "type": "int[]"
        }
      ],
      "execute_before": []
    }
  ]
}
```