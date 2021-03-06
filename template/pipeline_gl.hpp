/**
 * This file was auto-generated with OGL_Pipeline generator
 */
#pragma once
#include <functional>
#include <fstream>
#include <sstream>
#include <memory>

#include <GL/glew.h>

#include <glm/vec3.hpp>
#include <glm/gtx/quaternion.hpp>

namespace lit::voxels {

template<typename T>
class ValueHolder {
public:
    ValueHolder() {
        value = std::make_shared<T>();
    }

    static ValueHolder Create() {
        return ValueHolder();
    }

    T & Get() {
        return *value;
    }

    const T & Get() const {
        return *value;
    }

private:
    std::shared_ptr<T> value;
};

class Pipeline {
public:
    void Init(int width, int height);

    void UpdateResolution(int width, int height);

    void Redraw();

    ValueHolder<glm::dvec3> CameraTranslation();

    ValueHolder<glm::dquat> CameraRotation();

/*BIND_QUEUE*/

/*BIND_VALUE*/

private:

    void UpdateProjectionMatrix();

    void CreateFrameBuffers();

    void CreatePrograms();

    void DestroyFrameBuffers();

    void CompileAndAttachShader(GLuint program, std::string path, GLenum type);

    void UniformMat3(GLint location, const glm::dmat3 & mat);

    void UniformMat4(GLint location, const glm::dmat4 & mat);

    int current_width;
    int current_height;

    ValueHolder<glm::dquat> camera_rotation = ValueHolder<glm::dquat>::Create();
    ValueHolder<glm::dvec3> camera_translation = ValueHolder<glm::dvec3>::Create();

    const double Z_NEAR = /*Z_NEAR*/;
    const double Z_FAR = /*Z_FAR*/;
    const double FOV = /*FOV*/;

/*MEMBERS*/
};

} // namespace LiteEngine::VoxelWorld
