import json
import re
from typing import Dict, List

header_template = open('template/pipeline_gl.hpp', 'r').read()
source_template = open('template/pipeline_gl.cpp', 'r').read()


def to_camel_case(snake_str):
    return ''.join(x[0].upper() + x[1:] for x in snake_str.split('_'))


class Input:
    def get_id(self, program_name):
        return ''


class UInput(Input):
    def __init__(self, name, type_):
        self.name = name
        self.type = type_

    def get_id(self, program_name):
        return f'{program_name}_{self.name}_inp'

    def get_cpp_type(self):
        if self.type == 'int':
            return 'int'
        if self.type == 'int[]':
            return 'std::vector<int>'
        if self.type == 'int3[]':
            return 'std::vector<std::tuple<int,int,int>>'
        if self.type == 'float':
            return 'float'
        if self.type == 'vec3':
            return 'Vec3'
        if self.type == 'int3':
            return 'std::tuple<int,int,int>'
        if self.type == 'mat3':
            return 'Mat3'
        if self.type == 'mat4':
            return 'Mat4'
        return 'void'


class FBInput(Input):
    def __init__(self, name, value):
        self.name = name
        self.value = tuple(value.split('/'))

    def get_id(self, program_name):
        return f'{program_name}_{self.name}_inp'


class Subprogram:
    def __init__(self, json_obj):
        self.name = json_obj["name"]
        self.vert_path = json_obj["vert_path"]
        self.frag_path = json_obj["frag_path"]
        self.use_depth = json_obj["use_depth"]
        self.outputs = list(map(lambda p: tuple(p.split('/')), json_obj["outputs"]))
        self.fb_inputs = list(map(lambda nv: FBInput(nv["name"], nv["value"]), json_obj["fb_inputs"]))
        self.inputs = list(map(lambda nv: UInput(nv["name"], nv["type"]), json_obj["inputs"]))
        self.execute_before = json_obj["execute_before"]
        self.frame_buffer = self.outputs[0][0]

    def get_id(self):
        return f'{self.name}_p'

    def get_func_id(self):
        return f'{self.name}_func'


class FrameBuffer:
    def __init__(self, json_obj):
        self.name = json_obj["name"]
        self.depth = json_obj["depth"]
        self.textures = list(map(lambda v: (v["name"], v["format"]), json_obj["textures"]))

    def get_id(self):
        return f'{self.name}_fb'

    def get_depth_id(self):
        return f'{self.name}_depth_rb'

    def get_texture_ids(self):
        return [f'{self.name}_{t[0]}_t' for t in self.textures]

    def get_texture_id(self, texture_name):
        return f'{self.name}_{texture_name}_t'


class Params:
    def __init__(self, json_obj):
        self.z_near = json_obj['z_near']
        self.z_far = json_obj['z_far']
        self.fov = json_obj['fov']


def is_next(a: Subprogram, b: Subprogram):
    for inp in b.fb_inputs:
        if inp.value in a.outputs:
            return True
    return False


def sort_to_pipeline(subprograms: List[Subprogram]):
    for iteration in range(50):
        for a_id in range(len(subprograms)):
            for b_id in range(a_id + 1, len(subprograms)):
                if is_next(subprograms[b_id], subprograms[a_id]):
                    subprograms[a_id], subprograms[b_id] = subprograms[b_id], subprograms[a_id]


class Pipeline:
    def __init__(self, subprograms, framebuffers, params):
        self.subprograms = list(subprograms)
        self.framebuffers = dict(framebuffers)
        self.params = params
        sort_to_pipeline(self.subprograms)

    def validate(self):
        pass

    def generate_create_fb(self, fb: FrameBuffer):
        gen = ''
        gen += f'\tglGenFramebuffers(1, &{fb.get_id()});\n'
        gen += f'\tglBindFramebuffer(GL_FRAMEBUFFER, {fb.get_id()});\n\n'
        if fb.depth:
            gen += f'\tglGenRenderbuffers(1, &{fb.get_depth_id()});\n'
            gen += f'\tglBindRenderbuffer(GL_RENDERBUFFER, {fb.get_depth_id()});\n'
            gen += '\tglRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT32, current_width, current_height);\n'
            gen += '\tglBindRenderbuffer(GL_RENDERBUFFER, 0);\n\n'
            gen += f'\tglFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, ' \
                   f'{fb.get_depth_id()});\n\n'
        for i, (t, t_id) in enumerate(zip(fb.textures, fb.get_texture_ids())):
            gen += '\tglActiveTexture(GL_TEXTURE0);\n'
            gen += f'\tglGenTextures(1, &{t_id});\n'
            gen += f'\tglBindTexture(GL_TEXTURE_2D, {t_id});\n'
            gen += '\tglTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);\n'
            gen += '\tglTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);\n'
            gen += '\tglTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);\n'
            gen += '\tglTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);\n'
            gen += f'\tglTexImage2D(GL_TEXTURE_2D, 0, GL_{t[1]}, ' \
                   f'current_width, current_height, 0, GL_RGB, GL_UNSIGNED_BYTE, NULL);\n'
            gen += '\tglBindTexture(GL_TEXTURE_2D, 0);\n\n'
            gen += f'\tglFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0 + {i}, GL_TEXTURE_2D,' \
                   f'{t_id}, 0);\n\n'
        gen += '\tglBindFramebuffer(GL_FRAMEBUFFER, 0);\n'
        return gen

    def generate_destroy_fb(self, fb: FrameBuffer):
        gen = ''
        if fb.depth:
            gen += f'\tglDeleteRenderbuffers(1, &{fb.get_depth_id()});\n'
        for t_id in fb.get_texture_ids():
            gen += f'\tglDeleteTextures(1, &{t_id});\n'
        gen += f'\tglDeleteFramebuffers(1, &{fb.get_id()});'
        return gen

    def generate_program(self, p: Subprogram):
        gen = ''
        gen += f'\t{p.get_id()} = glCreateProgram();\n'

        gen += f'\tCompileAndAttachShader({p.get_id()}, "{p.vert_path}", GL_VERTEX_SHADER);\n'
        gen += f'\tCompileAndAttachShader({p.get_id()}, "{p.frag_path}", GL_FRAGMENT_SHADER);\n'

        gen += f'\tglLinkProgram({p.get_id()});\n\n'

        for inp in p.inputs + p.fb_inputs:
            gen += f'\t{inp.get_id(p.name)} = ' \
                   f'glGetUniformLocation({p.get_id()}, "{inp.name + ("[0]" if "[]" in inp.type else "")}");\n'
            gen += f'\tif ({inp.get_id(p.name)} == -1) \n' + \
                   f'\t\tLogger::LogError("Uniform location \\"{inp.name}\\" not found");\n\n'

        return gen + '\n'

    def generate_redraw_step(self, p: Subprogram):
        gen = ''
        if p.frame_buffer == 'SCREEN':
            gen += '\tglBindFramebuffer(GL_FRAMEBUFFER, 0);\n'
            gen += f'\tglDrawBuffer(GL_COLOR_ATTACHMENT0);\n'
            gen += '\tglClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT);\n'
        else:
            fb = self.framebuffers[p.frame_buffer]
            gen += f'\tglBindFramebuffer(GL_FRAMEBUFFER, {fb.get_id()});\n'
            if fb.depth:
                gen += '\tglClear(GL_DEPTH_BUFFER_BIT);\n'
                gen += '\tglEnable(GL_DEPTH_TEST);\n'
            else:
                gen += '\tglDisable(GL_DEPTH_TEST);\n'
            for i, t in enumerate(fb.textures):
                gen += f'\tglDrawBuffer(GL_COLOR_ATTACHMENT0 + {i});\n'
                gen += '\tglClear(GL_COLOR_BUFFER_BIT);\n'
            tmp = [f'GL_COLOR_ATTACHMENT0 + {i}' for i in range(len(fb.textures))]
            gen += f'\tGLenum {p.name}_buffers[] = {{{",".join(tmp)}}};\n'
            gen += f'\tglDrawBuffers({len(fb.textures)}, {p.name}_buffers);\n'

        gen += f'\tglUseProgram({p.get_id()});\n'

        for i, inp in enumerate(p.fb_inputs):
            fb_name, texture = inp.value
            gen += f'\tglActiveTexture(GL_TEXTURE0 + {i});\n'
            tex_id = self.framebuffers[fb_name].get_texture_id(texture)
            gen += f'\tglBindTexture(GL_TEXTURE_2D, {tex_id});\n'
            gen += f'\tglUniform1i({inp.get_id(p.name)}, {i});\n'

        gen += f'''
    if ({p.get_func_id()}) {{
        {p.get_func_id()}();
    }}\n'''

        return gen

    def generate_set_uniform(self):
        gen_cpp = ''
        gen_hpp = ''
        for p in self.subprograms:
            for inp in p.inputs:
                if len(inp.type) > 8:
                    # SPECIAL TYPES
                    gen_hpp += f'\tvoid UpdateUniform{to_camel_case(p.name)}{to_camel_case(inp.name)}();\n'
                    gen_cpp += f'void Pipeline::UpdateUniform{to_camel_case(p.name)}{to_camel_case(inp.name)}()'
                    if inp.type == 'GL_PROJECTION_MATRIX':
                        gen_cpp += f'{{ UniformProjection({inp.get_id(p.name)}); }}\n'
                    elif inp.type == 'GL_MODELVIEW_MATRIX':
                        gen_cpp += f'{{ UniformModelView({inp.get_id(p.name)}); }}\n'
                else:
                    # STANDARD TYPES
                    gen_hpp += f'\tvoid UpdateUniform{to_camel_case(p.name)}{to_camel_case(inp.name)}' \
                               f'(const {inp.get_cpp_type()} & value);\n'
                    gen_cpp += f'void Pipeline::UpdateUniform{to_camel_case(p.name)}{to_camel_case(inp.name)}' \
                               f'(const {inp.get_cpp_type()} & value)'
                    if inp.type == 'int':
                        gen_cpp += f'{{ glUniform1i({inp.get_id(p.name)}, value);}}\n'
                    elif inp.type == 'int[]':
                        gen_cpp += f'{{for (int i = 0; i < value.size(); i++) ' \
                                   f'glUniform1i({inp.get_id(p.name)} + i, value[i]);}}'
                    elif inp.type == 'int3[]':
                        gen_cpp += f'{{for (int i = 0; i < value.size(); i++) {{ auto [x,y,z] = value[i];' \
                                   f'glUniform3i({inp.get_id(p.name)} + i, x, y, z);}}}}'
                    elif inp.type == 'float':
                        gen_cpp += f'{{glUniform1f({inp.get_id(p.name)}, value);}}\n'
                    elif inp.type == 'vec3':
                        gen_cpp += f'{{glUniform3f({inp.get_id(p.name)}, value.x, value.y, value.z);}}\n'
                    elif inp.type == 'int3':
                        gen_cpp += f'{{auto [x,y,z] = value;'
                        gen_cpp += f'glUniform3i({inp.get_id(p.name)}, x, y, z);}}\n'
                    elif inp.type == 'mat3':
                        gen_cpp += f'{{UniformMat3({inp.get_id(p.name)}, value);}}\n'
                    elif inp.type == 'mat4':
                        gen_cpp += f'{{UniformMat4({inp.get_id(p.name)}, value);}}\n'
        return gen_hpp, gen_cpp

    def generate_cpp_class(self):
        members = ''
        queue_binders_h = ''
        queue_binders_c = ''
        value_binders_h = ''
        value_binders_c = ''

        members += '// FrameBuffers(fb) | RenderBuffers(rb) | OutTextures(t)\n'
        for fb in self.framebuffers.values():
            members += f'GLuint {fb.get_id()};\n'
            if fb.depth:
                members += f'GLuint {fb.get_depth_id()};\n'
            for t_id in fb.get_texture_ids():
                members += f'GLuint {t_id};\n'
        members += '\n// Subprograms(p) | RenderFunctions(func) | Inputs(inp)\n'
        for p in self.subprograms:
            members += f'\n// == {p.name} ==\n'
            members += f'GLuint {p.get_id()};\n'
            members += f'std::function<void(void)> {p.get_func_id()} = nullptr;\n'
            queue_binders_h += f'\tvoid Set{to_camel_case(p.name)}Func(std::function<void(void)> func);\n'
            queue_binders_c += f'void Pipeline::Set{to_camel_case(p.name)}Func(std::function<void(void)> func) ' \
                               f'{{ {p.get_func_id()} = std::move(func); }}\n'
            for inp in p.inputs + p.fb_inputs:
                members += f'GLint {inp.get_id(p.name)};\n'
        members += '\n// Uniforms(uni)\n'

        create_fb = ''
        for fb in self.framebuffers.values():
            create_fb += self.generate_create_fb(fb)
        destroy_fb = ''
        for fb in self.framebuffers.values():
            destroy_fb += self.generate_destroy_fb(fb)
        create_programs = ''
        for p in self.subprograms:
            create_programs += self.generate_program(p)
        redraw = ''

        redraw += '\tglMatrixMode(GL_MODELVIEW);\n'
        redraw += '\tglLoadIdentity();\n'
        r = 'camera_rotation.Get()'
        t = 'camera_translation.Get()'
        angle = f'acos(std::min(std::max(-1.0, {r}.s), 1.0)) * 2 / PI * 180'
        redraw += f'\tglRotatef(180, 0, 1, 0);\n'
        redraw += f'\tglRotatef(-{angle}, {r}.v.x, {r}.v.y, {r}.v.z);\n'
        redraw += f'\tglTranslatef(-{t}.x, -{t}.y, -{t}.z);\n'

        for p in self.subprograms:
            redraw += self.generate_redraw_step(p)
        redraw += '\tglUseProgram(0);\n'

        uniforms_hpp, uniforms_cpp = self.generate_set_uniform()

        header = header_template
        source = source_template
        header = header.replace('/*Z_NEAR*/', str(self.params.z_near))
        header = header.replace('/*Z_FAR*/', str(self.params.z_far))
        header = header.replace('/*FOV*/', str(self.params.fov))
        header = header.replace('/*MEMBERS*/', re.sub(r'(^|\n)(\S)', r'\g<1>\t\g<2>', members))
        header = header.replace('/*BIND_QUEUE*/', '/*BIND_QUEUE*/\n' + queue_binders_h)
        header = header.replace('/*BIND_VALUE*/', '/*BIND_VALUE*/\n' + uniforms_hpp)

        source = source.replace('/*DESTROY_FRAME_BUFFERS*/', '/*DESTROY_FRAME_BUFFERS*/\n' + destroy_fb)
        source = source.replace('/*CREATE_FRAME_BUFFERS*/', '/*CREATE_FRAME_BUFFERS*/\n' + create_fb)
        source = source.replace('/*CREATE_PROGRAMS*/', '/*CREATE_PROGRAMS*/\n' + create_programs)
        source = source.replace('/*REDRAW*/', '/*REDRAW*/\n' + redraw)
        source += queue_binders_c
        source += uniforms_cpp

        source = source.replace('\n\n}', '\n}')
        source = source.replace('\n\n}', '\n}')
        source = source.replace('\n\n}', '\n}')

        header = header.replace('\t', '    ')
        source = source.replace('\t', '    ')

        return header, source


def parse(path):
    with open(path, 'r') as file:
        json_obj = json.load(file)
        framebuffers = {fb.name: fb for fb in map(FrameBuffer, json_obj["framebuffers"])}
        subprograms: List[Subprogram] = list(map(Subprogram, json_obj["subprograms"]))
        params = Params(json_obj['params'])

        pipeline = Pipeline(subprograms, framebuffers, params)
        pipeline.validate()

        h, s = pipeline.generate_cpp_class()
        open(r'D:\Dev\Cpp\Physics3D\preview\src\pipeline_gl\pipeline_gl.hpp', 'w').write(h)
        open(r'D:\Dev\Cpp\Physics3D\preview\src\pipeline_gl\pipeline_gl.cpp', 'w').write(s)


if __name__ == '__main__':
    parse('graph2.json')
