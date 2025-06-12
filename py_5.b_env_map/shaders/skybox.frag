#version 460 core

out vec4 frag_color;

in vec4 frag_world_pos;

uniform samplerCube u_cube_map;

struct Light {
    vec3 position;
    vec3 direction;
    vec3 color;
    float strength;
};

struct PointLight {
    vec3 position;
    vec3 color;
    float strength;
};

struct SpotLight {
    vec3 position;
    vec3 direction;
    vec3 color;
    float strength;
    float cutoff;
    float softness;
};

struct Material {
    vec3 a;
    float d;
    float s;
};

uniform vec3 cam_pos;
uniform Light global_light;
uniform Material material;

const float PI = 3.14159265359;
const vec3 gamma = vec3(2.2);
const vec3 i_gamma = vec3(1 / 2.2);

// const vec3 fog_albedo = vec3(0.333);
// const float fog_scale = 0.15 / 10; // Higher is stronger rescale [0.0 to 1.0] to [0.0 to 0.1] i.e 0.015;

vec3 fresnelSchlick(float cosTheta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}

vec3 skybox_colors(vec3 tex_color) {
    const vec3 frag_pos = vec3(frag_world_pos);
    const vec3 V = normalize(cam_pos - frag_pos);

    // Precompute the surface response at normal incidence
    const vec3 F0 = mix(vec3(0.04), material.a, material.s);

    // Direction vector
    const vec3 D = normalize(global_light.position - global_light.direction);
    const vec3 H = normalize(V + D);

    // Radiance for directional lights is the color of the light times its strength
    const vec3 radiance = global_light.color * global_light.strength;

    // Calculate Fresnel term for direct lighting.
    const vec3 F = fresnelSchlick(max(dot(H, V), 0.0), F0);

    // Diffuse scattering
    const vec3 kD = (vec3(1.0) - F) * (1.0 - material.s); 

    // Only using the global light
    const vec3 Lo = (((kD * material.a / (PI + material.d))) * radiance);

    // Blend texture color with the combined illumination (if 0 there is none)
    return Lo * tex_color;
}

void main() {
    const vec3 skybox_coord = normalize(frag_world_pos.xyz / frag_world_pos.w);
    vec3 color = texture(u_cube_map, skybox_coord).rgb;
    color = pow(color, gamma);
    color = skybox_colors(color);

    // Fog
    // const float fog = gl_FragCoord.z / gl_FragCoord.w; // Strength higher when far away from frag
    // color = mix(color, fog_albedo, (1.0 - exp2(-fog_scale * fog)));

    color = pow(color, i_gamma);
    frag_color = vec4(color, 1.0);
}