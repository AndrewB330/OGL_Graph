/**
 * This file was auto-generated with OGL_Pipeline generator
 */
#include "pipeline_gl.hpp"

#include <common/logging.hpp>

using namespace lit::voxels;
using LiteEngine::Common::Logger;

void Pipeline::Init(int width, int height) {
    current_width = std::min(std::max(width, 128), 4096);
    current_height = std::min(std::max(height, 128), 4096);

    glClearColor(0, 0, 0, 1);
    glDepthFunc(GL_LESS);
    glEnable(GL_DEPTH_TEST);
    UpdateProjectionMatrix();

    CreateFrameBuffers();
    CreatePrograms();
}

void Pipeline::UpdateResolution(int width, int height) {
    width = std::min(std::max(width, 128), 4096);
    height = std::min(std::max(height, 128), 4096);
    if (width == current_width && height == current_height) {
        return;
    }
    current_width = width;
    current_height = height;
    UpdateProjectionMatrix();

    DestroyFrameBuffers();
    CreateFrameBuffers();
}

void Pipeline::UpdateProjectionMatrix() {
    glViewport(0, 0, current_width, current_height);
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    double h = tan(FOV / 360 * M_PI) * Z_NEAR;
    double w = h * (current_width * 1.0 / current_height);
    glFrustum(-w, w, -h, h, Z_NEAR, Z_FAR);
}

void Pipeline::Redraw() {
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
/*REDRAW*/
}

void Pipeline::CreateFrameBuffers() {
/*CREATE_FRAME_BUFFERS*/
}

void Pipeline::CreatePrograms() {
/*CREATE_PROGRAMS*/
}

void Pipeline::DestroyFrameBuffers() {
/*DESTROY_FRAME_BUFFERS*/
}

void Pipeline::CompileAndAttachShader(GLuint program, std::string path, GLenum type) {
    std::ifstream fin(("D:\\Dev\\Cpp\\LiteEngine.VoxelWorld\\shaders\\" + path).c_str());
    std::stringstream ss;
    ss << fin.rdbuf();
    std::string code_str = ss.str();
    const char *code_c_str = code_str.c_str();
    GLuint shader = glCreateShader(type);
    glShaderSource(shader, 1, &code_c_str, NULL);
    glCompileShader(shader);
    glAttachShader(program, shader);

    int success;
    char infoLog[512];
    glGetShaderiv(shader, GL_COMPILE_STATUS, &success);
    if (!success) {
        glGetShaderInfoLog(shader, 512, NULL, infoLog);
        Logger::LogError("Shader compilation error %s", infoLog);
    }
}


ValueHolder<glm::dvec3> Pipeline::CameraTranslation() {
    return camera_translation;
}

ValueHolder<glm::dquat> Pipeline::CameraRotation() {
    return camera_rotation;
}

void Pipeline::UniformMat3(GLint location, const glm::dmat3 &mat) {
    float data[9];
    for(int i = 0; i < 9; i++) data[i] = mat[i / 3][i % 3];
    glUniformMatrix3fv(location, 1, GL_FALSE, data);
}

void Pipeline::UniformMat4(GLint location, const glm::dmat4 &mat) {
    float data[16];
    for(int i = 0; i < 16; i++) data[i] = mat[i / 4][i % 4];
    glUniformMatrix4fv(location, 1, GL_FALSE, data);
}
