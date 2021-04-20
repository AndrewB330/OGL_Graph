/**
 * This file was auto-generated with OGL_Pipeline generator
 */
#include "pipeline_gl.hpp"

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
    double h = tan(FOV / 360 * PI) * Z_NEAR;
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
    std::ifstream fin(("D:\\Dev\\Cpp\\Physics3D\\preview\\shaders\\" + path).c_str());
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


ValueHolder<Vec3> Pipeline::CameraTranslation() {
    return camera_translation;
}

ValueHolder<Quat> Pipeline::CameraRotation() {
    return camera_rotation;
}

void Pipeline::UniformMat3(GLint location, const Mat3 &mat) {
    float data[9];
    for(int i = 0; i < 9; i++) data[i] = *(*mat.val + i);
    glUniformMatrix3fv(location, 1, GL_TRUE, data);
}

void Pipeline::UniformMat4(GLint location, const Mat4 &mat) {
    float data[16];
    for(int i = 0; i < 16; i++) data[i] = *(*mat.val + i);
    glUniformMatrix4fv(location, 1, GL_TRUE, data);
}
